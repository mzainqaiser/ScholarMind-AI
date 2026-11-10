# ScholarMind AI — Technical Report
**Agentic Academic Research & Learning Assistant (RAG + LangGraph)**
Muhammad Zain Qaiser · NIAI–NAVTTC AI Program, NETSOL Lahore

> Honesty note: this report describes what was *built and executed*. Where something could not be run in the build environment
> (real LLM, MiniLM embeddings, browser, PowerShell) it is stated explicitly in §15–16 and no result is invented.

## 1. Introduction
ScholarMind AI is a full-stack application that turns a student's own documents into a searchable, citable knowledge base and
adds an AI agent that performs study tasks over it. It combines Retrieval-Augmented Generation (RAG), a persistent vector database,
local embeddings, a locally hosted language model and an agent workflow, behind a React interface.

## 2. Problem statement
Language models answer fluently from parametric memory, so wrong statements are indistinguishable from right ones, and answers
cannot be traced to course material. Students need answers that come from *their* sources, are checkable, and admit ignorance.

## 3. Project objectives
(1) End-to-end RAG pipeline; (2) a genuine tool-using agent with ≥ 9 tools; (3) professional light-theme UI on real data; (4) no paid
services; (5) honest testing and evaluation; (6) safe handling of untrusted documents.

## 4. RAG fundamentals
RAG (Lewis et al., 2020) augments a generator with a non-parametric memory: passages are retrieved for the query and supplied as
context, so knowledge can be updated by changing the corpus and answers can cite evidence. The pipeline here: ingest → extract →
clean → chunk → embed → index → retrieve → build context → generate → attribute. Typical failure modes addressed: irrelevant retrieval
(threshold), context overflow (budget), unsupported generation (prompt rules + citation validation), and corpus text that attacks the
model (injection filter).

## 5. Agentic AI fundamentals
An agent wraps a model in a controller that decides *what to do* (choose a tool, gather evidence, check it, retry or stop) rather than
sending every input to the model once. LangGraph models this as a state graph with conditional edges. Here the controller is
deliberately simple and deterministic (rules for routing, validators for outputs), with the LLM used only to write.

## 6. System architecture
React/TypeScript SPA → FastAPI (7 routers, 27 endpoints) → services: ingestion, embeddings, ChromaDB, retrieval, LLM provider, LangGraph
agent → SQLite + ChromaDB on disk. Full diagram and decisions: `docs/architecture.md`.

## 7. Dataset / document processing
Supported: PDF, DOCX, TXT, MD (20 MB default cap, magic-byte check, SHA-256 duplicate rejection). PDFs are read page by page with
PyMuPDF so every chunk keeps its page number; DOCX and Markdown keep the nearest heading. Cleaning removes control characters,
re-joins hyphenated line breaks and collapses whitespace while preserving paragraphs. Scanned PDFs are rejected with an explanation (no OCR).
The project ships three original sample documents (`sample_data/`, 7 PDF pages in two files + 1 Markdown file) used for tests, demo and evaluation.

## 8. Chunking and embedding methodology
Character windows of 800 with 120 overlap, ending at a paragraph/sentence boundary when one exists in the last 30 % of the window,
never crossing a page/section boundary. These defaults are conventional starting values, **not tuned**; they are configurable.
Embeddings: `all-MiniLM-L6-v2` (Wang et al., 2020 – MiniLM; Reimers & Gurevych, 2019 – Sentence-BERT), 384 dimensions, L2-normalised,
computed locally on CPU. An offline fallback (`HashingEmbedder`: signed hashed unigram+bigram term frequencies, 384-d) keeps the system
runnable without the model download; it matches words, not meaning, and is labelled everywhere it is used.

## 9. Vector database implementation
ChromaDB `PersistentClient`, cosine space. The collection name embeds the embedder name so incompatible vectors cannot mix. Each vector stores
doc_id, filename, page (−1 when absent), section and chunk index. Deleting a document removes vectors, metadata row and file in that order;
re-indexing removes old vectors first. Persistence across restart is covered by tests (unit and HTTP end-to-end).

## 10. Semantic retrieval
Query → embedding → top-k nearest chunks (optionally restricted to selected document ids) → score = 1 − cosine distance → discard below
`MIN_SCORE` → number passages `[S1]…` within a character budget. Result objects carry filename, page, section, score and excerpt, which
the UI shows verbatim; page numbers are never produced by the model.

## 11. Agent architecture
LangGraph graph: classify → select_tool → plan → retrieve → validate → generate (retry ≤ 1) → format, with conditional exits for chit-chat,
unknown tool, insufficient evidence and step-limit. State is a plain dict. Routing is rule-based (11 intents), follow-up questions are
resolved with the previous user turn of the same conversation, and retrieval strategy depends on the tool (top-k, whole-document coverage, per-document for comparison).
Details: `docs/agent_workflow.md`.

## 12. Tool integration
Nine tools in one registry (Document Search, Summarization, Comparison, Study Notes, Quiz, Flashcards, Research Assistant, Document Q&A, Learning Plan).
Each defines retrieval mode, LLM instructions and a strict output parser. Quiz and flashcard outputs must be valid JSON whose every item cites a real
excerpt; MCQ answers must match an option; invalid items are dropped and reported. Document Search needs no LLM. Study buttons call the same graph with the tool forced.

## 13. Frontend and backend integration
Vite dev proxy forwards `/api` to FastAPI. A typed API client normalises every FastAPI error shape into a readable message; uploads use XHR to show
real progress; React context shares documents and system status. Pages: Dashboard, AI Assistant (history, scope picker, sources panel, agent activity),
My Documents, Research Workspace, Study Tools (interactive quiz and flashcards), Analytics, Settings. Statistics come from `/api/analytics/*`; nothing is hard-coded.

## 14. Testing methodology
| Level | Tool | Count | Notes |
|---|---|---|---|
| Backend unit + API + agent + analytics | pytest, FastAPI TestClient | **62** | real SQLite, ChromaDB, PyMuPDF, python-docx; offline embedder; **scripted mock LLM** |
| Frontend components | Vitest + Testing Library | **24** | API client mocked; one assertion mutation-checked (breaking scope passing made its test fail) |
| Build | `tsc --noEmit`, `vite build` | – | clean |
| HTTP end-to-end | real backend + Vite proxy | **22 checks** | upload → index → search → chat → follow-up → 4 study tools → analytics → **backend restart** → persistence → delete (metadata and vectors) |
Mock-LLM tests prove routing, validation, safety and persistence; they do **not** prove answer quality. Recorded outputs: `submission/test_reports/`.
Defects found and fixed during development and review included: command-word stripping that removed "learning" from "supervised learning" and caused false refusals; a dead UI control; and `.env` being documented but never loaded.

## 15. Actual evaluation results
Retrieval (automatic, 14 answerable questions, **lexical fallback embedder, not MiniLM**, chunk 800/120, threshold 0.12):

| Metric | K=1 | K=3 | K=5 |
|---|---|---|---|
| Precision@K | 0.500 | 0.310 | 0.186 |
| Recall@K (hit rate) | 0.500 | 0.929 | 0.929 |

MRR = **0.687**. Four of 14 answerable questions (Q04, Q06, Q07, Q09 – 28.6 %) score below the 0.12 threshold, so the agent would wrongly answer
"insufficient evidence"; both out-of-scope questions were correctly refused (2/2). Precision@K falls with K because each question has a single relevant page.
Interpretation: with a purely lexical embedder, ranking is mediocre and the threshold is too strict; these numbers are a *lower bound* and say nothing about MiniLM.
**Generation evaluation was not run** (no LLM available); `evaluate_generation.py` and the report template are provided, and human-review columns are left blank.
The dataset is small (16 questions, 3 documents, one relevant unit each) so differences of a few points are not meaningful. Full table: `evaluation/evaluation_report.md`.

## 16. Limitations
No real-LLM or MiniLM execution in the build environment; single-user; no OCR; heuristic injection defence; rule-based routing; uncalibrated threshold for MiniLM;
no re-ranking; no streaming; no browser-level (Playwright) tests or screenshots; PowerShell scripts unexecuted; small evaluation set; a 3B model can still
paraphrase evidence wrongly, which the app can flag (uncited answers, removed markers) but not detect semantically.

## 17. Future improvements
Hybrid BM25 + vector retrieval and cross-encoder re-ranking; threshold calibration on MiniLM; streaming; OCR; verified free-tier API provider; LLM-assisted routing with rule fallback;
larger human-labelled evaluation (optionally RAGAS with a local judge); authentication and multi-user storage; Playwright tests.

## 18. Conclusion
The project delivers a working, tested Agentic RAG system whose design priorities are traceability and honesty: evidence is checked before the model is called, citations come from
metadata rather than model output, failures are reported as failures, and every reported number comes from a script run. The main remaining work is to execute it with the real
embedding model and a local LLM on the target machine and to record those results.

## 19. References
1. Lewis, P., Perez, E., Piktus, A., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 33. arXiv:2005.11401.
2. Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP-IJCNLP. arXiv:1908.10084.
3. Wang, W., Wei, F., Dong, L., et al. (2020). *MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers.* NeurIPS 33. arXiv:2002.10957.
4. Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2023). *RAGAS: Automated Evaluation of Retrieval Augmented Generation.* arXiv:2309.15217 (considered; not used).
5. LangGraph documentation — https://langchain-ai.github.io/langgraph/
6. ChromaDB documentation — https://docs.trychroma.com/
7. Sentence Transformers documentation — https://www.sbert.net/
8. FastAPI documentation — https://fastapi.tiangolo.com/
9. Ollama — https://ollama.com/ ; Qwen2.5 model card — https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
10. PyMuPDF documentation — https://pymupdf.readthedocs.io/
