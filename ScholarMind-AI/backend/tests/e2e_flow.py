"""HTTP-level end-to-end check through the FRONTEND dev server's /api proxy (not a browser test).
Usage: python -m backend.tests.e2e_flow phase1|phase2   (restart the backend between phases to test persistence)."""
import sys
import tempfile
from pathlib import Path

import httpx

from backend.tests.conftest import PAGE1, PAGE2, PAGE3, make_pdf

BASE = "http://127.0.0.1:5173"
IDS = Path(tempfile.gettempdir()) / "sm_e2e_ids.txt"
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name} {extra}")


c = httpx.Client(base_url=BASE, timeout=30)
phase = sys.argv[1]
if phase == "phase1":
    html = httpx.get(BASE + "/", timeout=10)
    check("frontend serves the app shell", html.status_code == 200 and '<div id="root">' in html.text)
    check("backend reachable through frontend proxy", c.get("/api/health").json() == {"status": "ok"})
    pdf = Path(tempfile.mkdtemp()) / "ml_notes.pdf"
    make_pdf(pdf, [PAGE1, PAGE2, PAGE3])
    up = c.post("/api/documents/upload", files=[("files", ("ml_notes.pdf", pdf.read_bytes(), "application/pdf"))], data={"category": "Course"})
    doc = up.json()["results"][0]["document"]
    check("PDF uploaded, processed and indexed", up.status_code == 200 and doc["status"] == "indexed" and doc["pages"] == 3, f"(chunks={doc['chunk_count']})")
    check("document appears in library", [d["id"] for d in c.get("/api/documents").json()["documents"]] == [doc["id"]])
    bad = c.post("/api/documents/upload", files=[("files", ("x.exe", b"MZ", "application/octet-stream"))])
    check("invalid file rejected with readable error", bad.status_code == 400 and "Unsupported" in bad.json()["detail"][0]["error"])
    s = c.post("/api/rag/search", json={"query": "Which algorithm assigns points to the nearest centroid?"}).json()["results"][0]
    check("retrieval returns the correct page", s["page"] == 2 and s["filename"] == "ml_notes.pdf", f"(page={s['page']}, score={s['score']})")
    r1 = c.post("/api/agent/chat", json={"message": "What is overfitting in supervised learning?"}).json()
    check("agent answers with tool + valid citation", r1["status"] == "answered" and r1["tool"] == "document_qa" and r1["citations"][0]["page"] == 1)
    check("agent trace present", len(r1["trace"]) >= 5)
    cid = r1["conversation_id"]
    r2 = c.post("/api/agent/chat", json={"message": "Why does it happen?", "conversation_id": cid}).json()
    check("follow-up keeps conversation", r2["conversation_id"] == cid and len(c.get(f"/api/conversations/{cid}").json()["messages"]) == 4)
    for kind in ("notes", "quiz", "flashcards", "plan"):
        r = c.post(f"/api/study/{kind}", json={"document_ids": [doc["id"]]}).json()
        check(f"study/{kind} generated", r["status"] == "answered", f"(tool={r['tool']})")
    check("chitchat handled without LLM", c.post("/api/agent/chat", json={"message": "hello"}).json()["status"] == "chitchat")
    check("empty-evidence question reports insufficient evidence", c.post("/api/agent/chat", json={"message": "Who won the 1966 World Cup final?"}).json()["status"] == "insufficient_evidence")
    check("analytics reflects real usage", c.get("/api/analytics/overview").json()["documents"]["indexed"] == 1 and c.get("/api/analytics/usage").json()["tools"].get("document_qa", 0) >= 2)
    IDS.write_text(f"{doc['id']} {cid}")
else:
    doc_id, cid = IDS.read_text().split()
    check("document survived backend restart", c.get(f"/api/documents/{doc_id}").json()["status"] == "indexed")
    check("conversation survived backend restart", len(c.get(f"/api/conversations/{cid}").json()["messages"]) == 4)
    check("vector search works after restart", c.post("/api/rag/search", json={"query": "clustering centroid"}).json()["results"][0]["page"] == 2)
    check("delete succeeds", c.delete(f"/api/documents/{doc_id}").status_code == 200)
    st = c.get("/api/system/status").json()
    check("delete removed metadata AND vectors", st["vector_store"]["chunks"] == 0 and st["database"]["documents"] == 0)
    check("deleted document no longer retrievable", c.post("/api/rag/search", json={"query": "clustering centroid"}).json()["results"] == [])
failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
