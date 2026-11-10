"""Analytics computed from real stored data - nothing is hard-coded."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _pub(d):
    return {k: v for k, v in d.items() if k not in ("text", "stored_name")}


@router.get("/overview")
def overview(request: Request):
    s = request.app.state.services
    docs, convs = s.db.list_documents(), s.db.list_conversations()
    msgs = s.db.message_rows()
    return {
        "documents": {"total": len(docs), **{k: sum(1 for d in docs if d["status"] == k) for k in ("indexed", "failed", "processing")}},
        "chunks": s.store.count(), "conversations": len(convs), "messages": len(msgs),
        "by_type": dict(Counter(d["file_type"] for d in docs)),
        "by_category": dict(Counter(d["category"] for d in docs)),
        "recent_documents": [_pub(d) for d in docs[:5]],
        "recent_conversations": [{k: c[k] for k in ("id", "title", "updated_at", "message_count")} for c in convs[:5]],
    }


@router.get("/documents")
def documents(request: Request):
    docs = request.app.state.services.db.list_documents()
    return {"documents": [{k: d[k] for k in ("id", "filename", "file_type", "category", "status", "chunk_count", "pages", "size_bytes")} for d in docs]}


@router.get("/usage")
def usage(request: Request, days: int = 14):
    rows = request.app.state.services.db.message_rows()
    today = datetime.now(timezone.utc).date()
    per_day = {(today - timedelta(days=i)).isoformat(): {"date": (today - timedelta(days=i)).isoformat(), "user": 0, "assistant": 0}
               for i in range(max(1, min(days, 90)) - 1, -1, -1)}
    tools, statuses = Counter(), Counter()
    for role, meta, created in rows:
        day = created[:10]
        if day in per_day:
            per_day[day][role] += 1
        if role == "assistant":
            if meta.get("tool"):
                tools[meta["tool"]] += 1
            if meta.get("status"):
                statuses[meta["status"]] += 1
    return {"messages_per_day": list(per_day.values()), "tools": dict(tools), "statuses": dict(statuses)}
