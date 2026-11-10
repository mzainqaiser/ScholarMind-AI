# API Reference

Generated from the application's own OpenAPI schema (`app.openapi()`), so it matches the code. Interactive documentation is served by FastAPI at **http://127.0.0.1:8000/docs** (Swagger UI) and `/redoc`.

**Error conventions**

- `400` — every uploaded file was rejected (list of per-file errors) · `404` unknown id · `410` original file missing for re-index · `422` invalid input
- `503` with `{"detail": {"error": "llm_unavailable", "message": "..."}}` — the LLM provider is not reachable. The API never substitutes a fake answer.
- Insufficient evidence is **not** an error: it is a normal `200` response with `status: "insufficient_evidence"`.

## Health

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/health` | Health |
| `GET` | `/api/system/status` | System Status |


## Documents

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/documents` | List Documents |
| `POST` | `/api/documents/upload` | Upload |
| `DELETE` | `/api/documents/{document_id}` | Delete Document |
| `GET` | `/api/documents/{document_id}` | Get Document |
| `GET` | `/api/documents/{document_id}/preview` | Preview |
| `POST` | `/api/documents/{document_id}/reindex` | Reindex |

- **`POST /api/documents/upload`** — multipart form: `files` (one or more), `category`. Returns a per-file result list. If every file is rejected the status is 400 and `detail` is that same list.

## Rag

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/rag/query` | Query |
| `POST` | `/api/rag/search` | Search |

- **`POST /api/rag/query`** — Plain RAG answer. `status` is `answered` or `insufficient_evidence`. Returns HTTP 503 `{error: llm_unavailable, message}` when the LLM cannot be reached.
- **`POST /api/rag/search`** — Body `{query, top_k (1-20), document_ids?}`. Returns ranked passages with page, section, relevance score and excerpt. No LLM needed.

## Agent

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/agent/chat` | Chat |
| `GET` | `/api/agent/status` | Status |
| `GET` | `/api/agent/tools` | Tools |

- **`POST /api/agent/chat`** — Body `{message, conversation_id?, document_ids?}`. Runs the LangGraph agent. Response: `answer, status, tool, intent, citations[], trace[], structured, warnings[]`. `status` is one of `answered, insufficient_evidence, chitchat, tool_failed, iteration_limit`.
- **`GET /api/agent/tools`** — Lists the nine registered tools and whether each uses the LLM.

## Conversations

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/conversations` | List Conversations |
| `POST` | `/api/conversations` | Create |
| `DELETE` | `/api/conversations/{conversation_id}` | Delete |
| `GET` | `/api/conversations/{conversation_id}` | Get |
| `DELETE` | `/api/conversations/{conversation_id}/messages` | Clear |


## Study

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/study/compare` | Compare |
| `POST` | `/api/study/flashcards` | Flashcards |
| `POST` | `/api/study/notes` | Notes |
| `POST` | `/api/study/plan` | Plan |
| `POST` | `/api/study/quiz` | Quiz |
| `POST` | `/api/study/research` | Research |

- **`POST /api/study/quiz`** — Body `{document_ids[], topic?, count?, quiz_type: mcq|short}`. Needs at least one document or a topic (else 422). Runs the same agent graph with the tool forced.

## Analytics

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/analytics/documents` | Documents |
| `GET` | `/api/analytics/overview` | Overview |
| `GET` | `/api/analytics/usage` | Usage |


_Total endpoints: 27._
