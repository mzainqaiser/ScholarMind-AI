import hashlib
import re
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..database import now_iso
from ..ingestion.extractors import SUPPORTED_TYPES
from ..ingestion.processor import index_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _safe_display_name(name: str) -> str:
    name = Path((name or "document").replace("\\", "/")).name          # strips any directory part
    name = re.sub(r"[^\w.\- ()]", "_", name)[:150]
    return name or "document"


def _public(d, with_text=False):
    out = {k: v for k, v in d.items() if k not in ("text", "stored_name")}
    if with_text:
        out["text"] = d.get("text")
    return out


def _get_or_404(s, doc_id):
    doc = s.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc


@router.post("/upload")
async def upload(request: Request, files: List[UploadFile] = File(...), category: str = Form("General")):
    s = request.app.state.services
    limit = s.settings.max_upload_mb * 1024 * 1024
    category = re.sub(r"[^\w \-]", "", category).strip()[:50] or "General"
    results = []
    for f in files:
        display = _safe_display_name(f.filename)
        ext = display.rsplit(".", 1)[-1].lower() if "." in display else ""
        if ext not in SUPPORTED_TYPES:
            results.append({"filename": display, "ok": False, "error": f"Unsupported type '.{ext}'. Allowed: PDF, DOCX, TXT, MD."})
            continue
        data, too_big = bytearray(), False
        while chunk := await f.read(1024 * 1024):
            data += chunk
            if len(data) > limit:
                too_big = True
                break
        if too_big:
            results.append({"filename": display, "ok": False, "error": f"File exceeds {s.settings.max_upload_mb} MB limit."})
            continue
        if not data:
            results.append({"filename": display, "ok": False, "error": "File is empty."})
            continue
        sha = hashlib.sha256(data).hexdigest()
        existing = s.db.find_by_hash(sha)
        if existing:  # duplicate strategy: identical content is never ingested twice
            results.append({"filename": display, "ok": False, "duplicate_of": existing["id"],
                            "error": f"Duplicate of already uploaded '{existing['filename']}'."})
            continue
        doc_id = uuid.uuid4().hex[:12]
        stored = f"{doc_id}.{ext}"                      # server-generated name: no user input in the path
        path = s.settings.upload_dir / stored
        path.write_bytes(bytes(data))
        s.db.insert_document(id=doc_id, filename=display, stored_name=stored, file_type=ext, category=category,
                             sha256=sha, size_bytes=len(data), status="processing", uploaded_at=now_iso())
        index_document(s.db.get_document(doc_id), path, s)
        results.append({"filename": display, "ok": True, "document": _public(s.db.get_document(doc_id))})
    if results and not any(r["ok"] for r in results):
        raise HTTPException(400, detail=results)
    return {"results": results}


@router.get("")
def list_documents(request: Request, category: str = None, q: str = None):
    docs = request.app.state.services.db.list_documents()
    if category:
        docs = [d for d in docs if d["category"] == category]
    if q:
        docs = [d for d in docs if q.lower() in d["filename"].lower()]
    return {"documents": [_public(d) for d in docs]}


@router.get("/{document_id}")
def get_document(request: Request, document_id: str):
    return _public(_get_or_404(request.app.state.services, document_id))


@router.get("/{document_id}/preview")
def preview(request: Request, document_id: str, max_chars: int = 5000):
    d = _get_or_404(request.app.state.services, document_id)
    text = d.get("text") or ""
    return {"document_id": document_id, "text": text[:max_chars], "truncated": len(text) > max_chars}


@router.post("/{document_id}/reindex")
def reindex(request: Request, document_id: str):
    s = request.app.state.services
    doc = _get_or_404(s, document_id)
    path = s.settings.upload_dir / doc["stored_name"]
    if not path.exists():
        raise HTTPException(410, "Original file is missing; please upload it again.")
    index_document(doc, path, s)
    return _public(s.db.get_document(document_id))


@router.delete("/{document_id}")
def delete_document(request: Request, document_id: str):
    s = request.app.state.services
    doc = _get_or_404(s, document_id)
    s.store.delete_document(document_id)          # vectors first, so no orphan chunks stay searchable
    s.db.delete_document(document_id)
    (s.settings.upload_dir / doc["stored_name"]).unlink(missing_ok=True)
    return {"deleted": document_id}
