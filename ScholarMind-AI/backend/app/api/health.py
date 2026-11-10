from fastapi import APIRouter, Request
from ..llm.base import LLMUnavailable
from ..llm.provider_factory import get_llm

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/system/status")
def system_status(request: Request):
    s = request.app.state.services
    try:
        llm = get_llm(s.settings).status()
    except LLMUnavailable as exc:
        llm = {"available": False, "detail": str(exc)}
    return {"vector_store": {"status": "ok", "chunks": s.store.count(), "embedder": s.embedder.name,
                             "semantic": not s.embedder.name.startswith("hashing")},
            "database": {"status": "ok", "documents": len(s.db.list_documents())}, "llm": llm,
            "config": {"chunk_size": s.settings.chunk_size, "chunk_overlap": s.settings.chunk_overlap,
                       "top_k": s.settings.top_k, "min_score": s.settings.min_score,
                       "max_upload_mb": s.settings.max_upload_mb, "embedding_model": s.settings.embedding_model,
                       "agent_max_steps": s.settings.agent_max_steps}}
