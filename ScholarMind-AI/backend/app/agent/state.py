"""LangGraph state. Plain dict (TypedDict) so every step is inspectable and JSON-serialisable."""
from typing import Any, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    doc_ids: List[str]            # documents the user selected in the UI (may be empty = all)
    history: List[dict]           # prior turns of THIS conversation only
    forced_tool: Optional[str]    # set by /api/study/* endpoints; validated against the registry
    options: dict                 # count / days / quiz_type
    intent: str
    tool: str
    search_query: str
    scoped_docs: List[str]
    hits: List[dict]
    context: str
    citations: List[dict]
    answer: str
    structured: Any
    status: str                   # answered | insufficient_evidence | tool_failed | iteration_limit | chitchat
    warnings: List[str]
    trace: List[dict]
    steps: int
    attempts: int
    error: Optional[str]
