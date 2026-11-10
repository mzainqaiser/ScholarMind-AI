from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class NewConversation(BaseModel):
    title: str = Field("New conversation", max_length=80)
    document_ids: Optional[List[str]] = None


def _get(s, cid):
    c = s.db.get_conversation(cid)
    if not c:
        raise HTTPException(404, "Conversation not found.")
    return c


@router.get("")
def list_conversations(request: Request):
    return {"conversations": request.app.state.services.db.list_conversations()}


@router.post("")
def create(request: Request, body: NewConversation):
    s = request.app.state.services
    return s.db.get_conversation(s.db.create_conversation(body.title, body.document_ids))


@router.get("/{conversation_id}")
def get(request: Request, conversation_id: str):
    s = request.app.state.services
    return {**_get(s, conversation_id), "messages": s.db.get_messages(conversation_id)}


@router.delete("/{conversation_id}")
def delete(request: Request, conversation_id: str):
    s = request.app.state.services
    _get(s, conversation_id)
    s.db.delete_conversation(conversation_id)
    return {"deleted": conversation_id}


@router.delete("/{conversation_id}/messages")
def clear(request: Request, conversation_id: str):
    s = request.app.state.services
    _get(s, conversation_id)
    s.db.clear_messages(conversation_id)
    return {"cleared": conversation_id}
