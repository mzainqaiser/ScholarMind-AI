"""Ingestion pipeline: validate -> extract -> clean -> chunk -> embed -> store."""
from .chunker import chunk_sections
from .extractors import ExtractionError, extract


def index_document(doc, path, services):
    """(Re)build the index for one document. Old vectors are removed first; any failure marks the
    document 'failed' with the reason instead of losing it."""
    s = services
    s.db.update_document(doc["id"], status="processing", error=None)
    try:
        sections, pages = extract(path, doc["file_type"])
        chunks = chunk_sections(sections, doc["id"], s.settings.chunk_size, s.settings.chunk_overlap)
        if not chunks:
            raise ExtractionError("Document produced no chunks.")
        vectors = s.embedder.embed([c["text"] for c in chunks])
        s.store.delete_document(doc["id"])
        s.store.add_chunks(doc["id"], doc["filename"], chunks, vectors)
        text = "\n\n".join((f"[Page {x.page}]\n" if x.page else "") + x.text for x in sections)
        s.db.update_document(doc["id"], status="indexed", chunk_count=len(chunks), pages=pages, text=text, error=None)
    except Exception as exc:
        s.store.delete_document(doc["id"])
        s.db.update_document(doc["id"], status="failed", chunk_count=0, error=str(exc)[:500])
