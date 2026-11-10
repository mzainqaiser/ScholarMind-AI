# ScholarMind AI — Agentic Academic Research & Learning Assistant

*Your Knowledge. Your Research. Your Intelligent AI Assistant.*

NIAI–NAVTTC AI Program (NETSOL Lahore) · Project: **RAG & Agentic AI** · Author: Muhammad Zain Qaiser

ScholarMind AI lets a student upload academic documents (PDF, DOCX, TXT, MD), then ask questions, summarise, compare, search,
and generate notes, quizzes, flashcards and study plans. Every answer is grounded in the uploaded documents and shows its
sources (file, page, excerpt). Everything runs locally and **no paid API is needed**.

## Problem statement
General chatbots answer from memory and can state wrong facts with confidence; students cannot tell which statement came from
their course material. ScholarMind AI retrieves evidence from the student's own documents first, answers only from that
evidence, shows exactly where it came from, and says so when the documents do not contain the answer.

## Objectives
1. A complete RAG pipeline: ingestion → cleaning → chunking → local embeddings → persistent vector store → retrieval → grounded generation → citations.
2. A real agent (LangGraph) that classifies intent, selects among **9 tools**, validates evidence and handles failure.
3. A professional light-theme React interface wired to real backend data.
4. Genuine testing and evaluation, with honest reporting of limits.

## Key features
- Upload one or many documents with progress, category, status, preview, re-index and delete; duplicate detection; type/size/content validation.
- Page-accurate citations for PDFs; heading-aware chunks for DOCX/Markdown.
- Chat with history, follow-up questions (conversation-scoped memory), document scope selection, Markdown/table rendering, copy, clear, delete.
- Agent tools: Document Search · Summarization · Academic Comparison · Study Notes · Quiz (MCQ/short answer) · Flashcards · Research Assistant · Document Q&A · Learning Plan.
- "Agent activity" panel (selected tool, scope, retrieval counts) – never the model's private reasoning.
- Dashboard and Analytics computed from real stored data; empty states everywhere; clear error messages.
- Safety: prompt-injection neutralisation, tool allow-list, step limit, citation validation, unsupported-claim warnings.

## Technology stack
| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite 6, Tailwind CSS 3, lucide-react, react-markdown + remark-gfm, React Router, Vitest + Testing Library |
| Backend | Python, FastAPI, Pydantic v2, Uvicorn, SQLite |
| RAG | PyMuPDF, python-docx, custom chunker, Sentence Transformers (`all-MiniLM-L6-v2`), ChromaDB |
| Agent | LangGraph |
| LLM | Ollama (local, free) – default model `qwen2.5:3b-instruct` (alternative: `llama3.2:3b`) |
| Tests | pytest, FastAPI TestClient, Vitest |

Tested with Python 3.13, Node 22. (Python ≥ 3.10 and Node ≥ 18 are expected to work.)

## Architecture, pipeline, agent
See [`docs/architecture.md`](docs/architecture.md), [`docs/rag_pipeline.md`](docs/rag_pipeline.md), [`docs/agent_workflow.md`](docs/agent_workflow.md),
[`docs/api_reference.md`](docs/api_reference.md) (27 endpoints) and the full [`docs/technical_report.md`](docs/technical_report.md).
Instructor demo: [`docs/demo_guide.md`](docs/demo_guide.md).

## Installation

### Windows (PowerShell)
```powershell
cd ScholarMind-AI
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1          # add -SkipEmbeddings for a quick, non-semantic try-out
```
### Linux / macOS
```bash
cd ScholarMind-AI
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
(cd frontend && npm install)
```
The first start downloads the embedding model (~90 MB) from Hugging Face once; `requirements.txt` pulls PyTorch (~2 GB).

## Configuration
Copy `.env.example` to `.env` (the backend reads it automatically; real environment variables take precedence). No key is required.
Main settings: `OLLAMA_MODEL`, `OLLAMA_URL`, `EMBEDDING_PROVIDER` (`auto` | `sentence-transformers` | `hashing`), `CHUNK_SIZE`, `CHUNK_OVERLAP`,
`TOP_K`, `MIN_SCORE`, `MAX_UPLOAD_MB`, `AGENT_MAX_STEPS`, `SCHOLARMIND_DATA_DIR`.

## Local LLM setup (Ollama)
```powershell
# 1. install Ollama from https://ollama.com
ollama pull qwen2.5:3b-instruct      # ~2 GB, 4-bit quantised, runs on CPU (slow but works; expect tens of seconds per answer)
ollama list                          # confirm it is installed
```
The app **detects** whether Ollama and the model are present (top-bar badge, Dashboard and Settings page) and shows exact instructions
if not. If `llama3.2:3b` is preferred: `ollama pull llama3.2:3b` and set `OLLAMA_MODEL=llama3.2:3b`. With no LLM, upload, search and Document
Search still work; everything that needs generation returns a clear error instead of a fake answer.

## Running
```powershell
scripts\start_backend.ps1      # terminal 1 → http://127.0.0.1:8000  (Swagger UI at /docs)
scripts\start_frontend.ps1     # terminal 2 → http://localhost:5173
```
```bash
python -m uvicorn backend.app.main:app --port 8000      # terminal 1 (from the project root, venv active)
cd frontend && npm run dev                              # terminal 2
```

## Using it
1. **My Documents** → upload `sample_data/ml_fundamentals.pdf` (and the other samples). Wait for status *indexed*.
2. **AI Assistant** → ask *"What is overfitting?"* – the answer shows `[S1]`-style markers; open **Sources** for file, page and excerpt; ask *"Why does it happen?"* as a follow-up.
3. Try *"Summarize ml_fundamentals"*, *"Create 5 MCQs from this document"*, *"Compare supervised and unsupervised learning"*, *"Find where K-means is discussed"*.
4. **Study Tools** / **Research Workspace** → notes, quizzes (interactive), flashcards, plans, research, comparison, passage search.

## Testing
```powershell
scripts\verify_project.ps1       # everything below in one go
```
```bash
python -m pytest backend/tests -q          # 62 backend tests
cd frontend && npm test                    # 24 component tests
cd frontend && npm run build               # TypeScript check + production build
python evaluation/evaluate_retrieval.py    # retrieval metrics
```
Tests need no internet and no LLM: they use a deterministic offline embedder and a **scripted mock LLM** (clearly named in the code and
reports). They verify routing, tool execution, validation, safety, persistence and API behaviour – **not** the writing quality of a real model.
The recorded outputs are in [`submission/test_reports/`](submission/test_reports/).

## Evaluation
`evaluation/evaluation_dataset.json` – 16 hand-written questions (14 answerable with a verified source page/section, 2 out of scope) over three original sample documents.
`evaluate_retrieval.py` computes Precision@K, Recall@K, MRR and the false-refusal rate. `evaluate_generation.py` needs a real LLM (it refuses to run
without one) and leaves human-review columns blank. Results: [`evaluation/evaluation_report.md`](evaluation/evaluation_report.md).

## Verification status (what was and was not actually run)
| Item | Status |
|---|---|
| Backend tests (62), frontend tests (24), TypeScript build, 22-check HTTP end-to-end incl. backend restart | **Run and passed** in the build environment (Linux, Python 3.13) |
| Retrieval evaluation | **Run**, but with the *lexical fallback embedder* (Hugging Face was unreachable) → a lower bound, not MiniLM results |
| `all-MiniLM-L6-v2` embeddings | Code path written; **never executed** in the build environment |
| Real LLM (Ollama/Qwen) | **Never executed** in the build environment. Generation evaluation **not run**; no scores exist |
| PowerShell scripts | Written for Windows; **not executed** (no PowerShell in the build environment) |
| Browser UI / Playwright | **Not run** (no browser available). The UI is verified by component tests, a clean TypeScript build and HTTP-level end-to-end; no screenshots exist |

Please run `scripts\verify_project.ps1`, start Ollama, and complete the checklist in `submission/SUBMISSION_CHECKLIST.md` before submitting.

## Deviations from the original brief (deliberate and documented)
- **LangChain is not used**; LangGraph provides the agent, and ingestion/chunking are custom (simpler and fully testable).
- **No separate re-ranker** (`reranker.py` omitted): ranking is cosine similarity + threshold.
- **Only the Ollama provider is implemented.** No free-API (e.g. Gemini) adapter was added because it could not be verified here; `llm/provider_factory.py` is the single extension point.
- **No token streaming** (the UI shows a progress indicator instead). **No docker-compose.**
- Tests live in `backend/tests/` and `frontend/src/test/` (no root-level `tests/` folder).
- PDF chunks carry page numbers but no section headings; DOCX/Markdown chunks carry headings.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Top bar: **Backend offline** | Start the backend; check port 8000 is free |
| **LLM offline** badge | Install/start Ollama and `ollama pull qwen2.5:3b-instruct`; check `OLLAMA_URL`; click *Re-check connections* in Settings |
| **Fallback embeddings** badge | `sentence-transformers` missing or the model could not be downloaded (needs internet once). Fix, restart, then **Re-index** every document |
| Answers say "insufficient evidence" for things that are in the document | Lower `MIN_SCORE` (e.g. 0.05) – especially with the fallback embedder – and re-test |
| Upload says "No extractable text" | The PDF is scanned images; OCR is not supported |
| Slow answers | CPU inference of a 3B model is slow; keep `TOP_K` small or use a smaller model |
| Start fresh | Stop the backend and delete `storage/data/` |

## Limitations
Single user, no login · no OCR · answer quality depends on the small local model (it can still misstate or ignore evidence; the app flags uncited answers but cannot prove correctness) ·
rule-based routing misses unusual phrasings · prompt-injection filtering is heuristic · `MIN_SCORE` is not calibrated for MiniLM · character-based chunking ignores sentence semantics.

## Future improvements
Cross-encoder re-ranking and hybrid (BM25 + vector) search · token streaming · OCR for scans · additional LLM providers (verified free-tier APIs) ·
LLM-assisted intent classification with the rules as fallback · RAGAS-style evaluation on a larger human-labelled set · multi-user accounts · Playwright browser tests.

## Sample documents & licence note
`sample_data/` contains original text written for this project and may be redistributed. Do not add copyrighted course material to submissions.
