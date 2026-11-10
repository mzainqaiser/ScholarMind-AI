"""SQLite metadata store: documents, conversations, messages."""
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    sha256 TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    pages INTEGER,
    status TEXT NOT NULL,            -- processing | indexed | failed
    error TEXT,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    text TEXT,
    uploaded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,              -- user | assistant
    content TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}', -- JSON: tool, intent, citations, trace, status
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path):
        self.path = str(path)
        self._lock = threading.Lock()
        with self.tx() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        """One connection per transaction; commit on success, roll back on any error."""
        with self._lock:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    # ---- documents ----
    def insert_document(self, **f):
        cols = ", ".join(f)
        marks = ", ".join("?" for _ in f)
        with self.tx() as c:
            c.execute(f"INSERT INTO documents ({cols}) VALUES ({marks})", list(f.values()))

    def update_document(self, doc_id, **f):
        sets = ", ".join(f"{k}=?" for k in f)
        with self.tx() as c:
            c.execute(f"UPDATE documents SET {sets} WHERE id=?", [*f.values(), doc_id])

    def get_document(self, doc_id):
        with self.tx() as c:
            r = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        return dict(r) if r else None

    def find_by_hash(self, sha):
        with self.tx() as c:
            r = c.execute("SELECT * FROM documents WHERE sha256=?", (sha,)).fetchone()
        return dict(r) if r else None

    def list_documents(self):
        with self.tx() as c:
            rows = c.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [dict(r) for r in rows]

    def delete_document(self, doc_id):
        with self.tx() as c:
            c.execute("DELETE FROM documents WHERE id=?", (doc_id,))

    # ---- conversations (history is always read by conversation_id, so chats never leak into each other) ----
    def create_conversation(self, title="New conversation", doc_ids=None):
        cid, ts = uuid.uuid4().hex[:12], now_iso()
        with self.tx() as c:
            c.execute("INSERT INTO conversations VALUES (?,?,?,?,?)", (cid, title[:80], json.dumps(doc_ids or []), ts, ts))
        return cid

    def get_conversation(self, cid):
        with self.tx() as c:
            r = c.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["doc_ids"] = json.loads(d["doc_ids"])
        return d

    def list_conversations(self):
        with self.tx() as c:
            rows = c.execute("""SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id) AS message_count
                                FROM conversations c ORDER BY updated_at DESC""").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["doc_ids"] = json.loads(d["doc_ids"])
            out.append(d)
        return out

    def update_conversation(self, cid, **f):
        if "doc_ids" in f:
            f["doc_ids"] = json.dumps(f["doc_ids"])
        f["updated_at"] = now_iso()
        sets = ", ".join(f"{k}=?" for k in f)
        with self.tx() as c:
            c.execute(f"UPDATE conversations SET {sets} WHERE id=?", [*f.values(), cid])

    def add_message(self, cid, role, content, meta=None):
        with self.tx() as c:
            c.execute("INSERT INTO messages (conversation_id, role, content, meta, created_at) VALUES (?,?,?,?,?)",
                      (cid, role, content, json.dumps(meta or {}), now_iso()))

    def get_messages(self, cid, limit=None):
        with self.tx() as c:
            rows = c.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (cid,)).fetchall()
        out = [{**dict(r), "meta": json.loads(r["meta"])} for r in rows]
        return out[-limit:] if limit else out

    def delete_conversation(self, cid):
        with self.tx() as c:
            c.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
            c.execute("DELETE FROM conversations WHERE id=?", (cid,))

    def clear_messages(self, cid):
        with self.tx() as c:
            c.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
        self.update_conversation(cid)

    def message_rows(self):
        with self.tx() as c:
            rows = c.execute("SELECT role, meta, created_at FROM messages").fetchall()
        return [(r["role"], json.loads(r["meta"]), r["created_at"]) for r in rows]
