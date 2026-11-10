"""Shared helpers for the evaluation scripts: build an isolated service stack and ingest the sample corpus."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATASET = Path(__file__).with_name("evaluation_dataset.json")
SAMPLES = ROOT / "sample_data"
RESULTS = Path(__file__).with_name("results")


def load_questions():
    return json.loads(DATASET.read_text(encoding="utf-8"))["questions"]


def build_services(embedding_provider=None):
    """Fresh temporary storage (never touches the user's real data) + all sample documents indexed."""
    os.environ["SCHOLARMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="sm_eval_")
    if embedding_provider:
        os.environ["EMBEDDING_PROVIDER"] = embedding_provider
    from backend.app.database import now_iso
    from backend.app.ingestion.processor import index_document
    from backend.app.services.container import Services
    import hashlib
    s = Services()
    for path in sorted(SAMPLES.iterdir()):
        if path.suffix.lower() not in (".pdf", ".md") or path.name.lower() == "readme.md":
            continue
        data = path.read_bytes()
        doc_id = hashlib.sha1(path.name.encode()).hexdigest()[:12]
        stored = f"{doc_id}{path.suffix.lower()}"
        (s.settings.upload_dir / stored).write_bytes(data)
        s.db.insert_document(id=doc_id, filename=path.name, stored_name=stored, file_type=path.suffix.lower().lstrip("."),
                             category="Sample", sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data),
                             status="processing", uploaded_at=now_iso())
        index_document(s.db.get_document(doc_id), s.settings.upload_dir / stored, s)
    return s


def unit_of(item):
    """Evaluation unit of a retrieved chunk / citation: (filename, page) for PDFs, (filename, section) otherwise."""
    return (item["filename"], item["page"] if item.get("page") else item.get("section"))


def expected_unit(q):
    e = q["expected"]
    return (e["document"], e["page"] if "page" in e else e["section"]) if e else None


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")
