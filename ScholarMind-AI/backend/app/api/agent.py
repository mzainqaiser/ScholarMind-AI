from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..agent.graph import run_agent
from ..agent.tools.registry import TOOLS
from ..llm.base import LLMUnavailable
from ..llm.provider_factory import get_llm

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None     # None = keep the conversation's current selection


def payload(state):
    return {k: state.get(k) for k in ("answer", "status", "tool", "intent", "citations", "trace", "structured", "warnings")}


def run_and_handle(services, **inputs):
    """Run the graph; translate an unreachable LLM into a clear 503 (never a fake answer)."""
    try:
        return run_agent(services, **inputs)
    except LLMUnavailable as exc:
        raise HTTPException(503, detail={"error": "llm_unavailable", "message": str(exc)})


@router.post("/chat")
def chat(request: Request, body: ChatRequest):
    s = request.app.state.services
    if body.conversation_id:
        conv = s.db.get_conversation(body.conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found.")
    else:
        conv = s.db.get_conversation(s.db.create_conversation(body.message.strip()[:60], body.document_ids or []))
    doc_ids = body.document_ids if body.document_ids is not None else conv["doc_ids"]
    # history is read strictly by conversation id -> no cross-conversation leakage
    history = [{"role": m["role"], "content": m["content"]} for m in s.db.get_messages(conv["id"], limit=8)]
    state = run_and_handle(s, question=body.message.strip(), doc_ids=doc_ids, history=history)
    meta = {k: state.get(k) for k in ("tool", "intent", "status", "citations", "trace", "structured", "warnings")}
    s.db.add_message(conv["id"], "user", body.message.strip())
    s.db.add_message(conv["id"], "assistant", state["answer"], meta)
    s.db.update_conversation(conv["id"], doc_ids=doc_ids)
    return {"conversation_id": conv["id"], **payload(state)}


@router.get("/tools")
def tools():
    return {"tools": [{"name": t.name, "title": t.title, "description": t.description, "uses_llm": t.needs_llm}
                      for t in TOOLS.values()]}


@router.get("/status")
def status(request: Request):
    s = request.app.state.services
    try:
        llm = get_llm(s.settings).status()
    except LLMUnavailable as exc:
        llm = {"available": False, "detail": str(exc)}
    return {"llm": llm, "tools": len(TOOLS), "max_steps": s.settings.agent_max_steps, "framework": "langgraph"}
