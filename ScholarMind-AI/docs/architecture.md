# Architecture

```
 Browser (React + TypeScript + Tailwind, light theme)
   Dashboard | AI Assistant | My Documents | Research | Study Tools | Analytics | Settings
        │   /api/*  (Vite dev proxy → no CORS problems; CORS also configured)
        ▼
 FastAPI (backend/app/main.py)  ── routers: health, documents, rag, agent, conversations, study, analytics
        │
        ├── ingestion/      extractors (PyMuPDF, python-docx, text/MD) → chunker → processor
        ├── embeddings/     SentenceTransformer (all-MiniLM-L6-v2)  |  HashingEmbedder (offline fallback)
        ├── vectorstore/    ChromaDB PersistentClient (cosine) – collection name includes the embedder name
        ├── retrieval/      top-k search, relevance threshold, context budget, prompt-injection neutralisation
        ├── llm/            provider interface + Ollama provider + factory (single swap point)
        ├── agent/          LangGraph: state, routing (rules), nodes, 9-tool registry, graph
        ├── services/       container (wires everything), rag_service (plain RAG answer)
        └── database.py     SQLite: documents, conversations, messages
 Storage: storage/data/{scholarmind.db, chroma/, uploads/}
```

## Key design decisions

| Decision | Reason |
|---|---|
| **Rules for intent routing**, LLM only for generation | 3B local models classify intent unreliably; rules are deterministic, instant and unit-testable. Trade-off: unusual phrasing falls back to plain document Q&A. |
| **One agent graph for chat and study buttons** | `/api/study/*` calls the same graph with the tool forced, so UI buttons and chat cannot diverge. |
| **Embedder name is part of the Chroma collection name** | Vectors from different models/dimensions can never be mixed; switching embedders needs a re-index (the UI has a Re-index button). |
| **Evidence checked before generation** | If no passage clears the relevance threshold the agent answers "insufficient evidence" **without calling the LLM** – the cheapest and most reliable hallucination guard. |
| **LLM failure → HTTP 503, never a canned answer** | The UI shows the setup instructions instead of pretending. |
| **SQLite + Chroma kept consistent by ordering** | Delete removes vectors first, then the metadata row, then the file; re-index deletes the old vectors before inserting the new ones. |
| **Uploaded files get server-generated names** | The user-supplied filename is only a sanitised display label and never part of a filesystem path (path-traversal protection). |

## Security & reliability controls

File type allow-list + magic-byte check · size limit (`MAX_UPLOAD_MB`) · duplicate detection by SHA-256 · sanitised display names ·
parameterised SQL · Pydantic validation on every request body · CORS allow-list · secrets only via environment (none are required) ·
LLM timeout (`LLM_TIMEOUT_S`) · agent step limit (`AGENT_MAX_STEPS`) + one bounded format-retry · tool allow-list ·
documents treated as untrusted data (see `agent_workflow.md`) · React Markdown renderer with raw HTML disabled.

## Known architectural limits

Single user, no authentication (the avatar in the top bar is a placeholder) · no OCR for scanned PDFs · SQLite connection per transaction
(fine for one user, not for heavy concurrency) · no streaming of LLM tokens · no cross-encoder re-ranking.
