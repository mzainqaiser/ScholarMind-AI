"""Study endpoints run the SAME agent graph with the tool forced, so UI buttons and chat share one code path."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .agent import payload, run_and_handle

router = APIRouter(prefix="/api/study", tags=["study"])


class StudyRequest(BaseModel):
    document_ids: List[str] = []
    topic: str = Field("", max_length=300)
    count: Optional[int] = Field(None, ge=1, le=20)
    days: Optional[int] = Field(None, ge=1, le=60)
    quiz_type: Optional[str] = Field(None, pattern="^(mcq|short)$")


def _run(request, tool, body, verb):
    s = request.app.state.services
    if not body.document_ids and not body.topic.strip():
        raise HTTPException(422, "Select at least one document or enter a topic.")
    # With a topic, search on the topic alone (a leading verb like "Research" would dilute the query).
    question = body.topic.strip() or f"{verb} the selected documents"
    state = run_and_handle(s, question=question, doc_ids=body.document_ids, forced_tool=tool,
                           options={"count": body.count, "days": body.days, "quiz_type": body.quiz_type})
    return payload(state)


@router.post("/notes")
def notes(request: Request, body: StudyRequest):
    return _run(request, "notes", body, "Create study notes on")


@router.post("/quiz")
def quiz(request: Request, body: StudyRequest):
    return _run(request, "quiz", body, "Create a quiz on")


@router.post("/flashcards")
def flashcards(request: Request, body: StudyRequest):
    return _run(request, "flashcards", body, "Create flashcards on")


@router.post("/plan")
def plan(request: Request, body: StudyRequest):
    return _run(request, "study_plan", body, "Create a study plan for")


@router.post("/research")
def research(request: Request, body: StudyRequest):
    if not body.topic.strip():
        raise HTTPException(422, "Enter a research topic or question.")
    return _run(request, "research", body, "Research")


@router.post("/compare")
def compare(request: Request, body: StudyRequest):
    if len(body.document_ids) < 2 and not body.topic.strip():
        raise HTTPException(422, "Select at least two documents, or enter the concepts to compare.")
    return _run(request, "compare", body, "Compare")
