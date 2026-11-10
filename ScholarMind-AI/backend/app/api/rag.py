from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..llm.base import LLMUnavailable
from ..retrieval.retriever import build_context, retrieve
from ..services.rag_service import answer_question

router = APIRouter(prefix="/api/rag", tags=["rag"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    document_ids: Optional[List[str]] = None


@router.post("/search")
def search(request: Request, body: SearchRequest):
    s = request.app.state.services
    hits = retrieve(s.embedder, s.store, body.query, body.top_k, 0.0, body.document_ids)
    _, citations = build_context(hits, s.settings.context_char_budget)
    return {"query": body.query, "results": citations, "embedder": s.embedder.name}


@router.post("/query")
def query(request: Request, body: SearchRequest):
    s = request.app.state.services
    try:
        return answer_question(s, body.query, body.document_ids, body.top_k)
    except LLMUnavailable as exc:
        raise HTTPException(503, detail={"error": "llm_unavailable", "message": str(exc)})
