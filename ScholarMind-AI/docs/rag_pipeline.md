# RAG Pipeline

| # | Stage | Implementation | Notes |
|---|---|---|---|
| 1 | Ingestion | `api/documents.py` | Extension allow-list, size cap, empty-file check, SHA-256 duplicate rejection, safe stored name |
| 2 | Extraction | `ingestion/extractors.py` | PDF: PyMuPDF **per page** (page numbers kept). DOCX: python-docx, headings tracked. TXT/MD: UTF-8 (latin-1 fallback), Markdown headings tracked. Magic-byte validation. Scanned PDFs → clear error (no OCR) |
| 3 | Cleaning | `clean_text` | Removes control characters, re-joins words hyphenated across lines, collapses spaces, keeps paragraph breaks; exact duplicate chunks dropped |
| 4 | Chunking | `ingestion/chunker.py` | Character window (default **800**, overlap **120**), prefers paragraph/sentence boundaries in the last 30 % of the window; never crosses a page/section boundary; chunk id `docid:index` |
| 5 | Embedding | `embeddings/embedding_service.py` | `sentence-transformers/all-MiniLM-L6-v2` (384-d, normalised). Offline fallback `HashingEmbedder` (384-d signed hashed uni+bigrams) – **lexical, not semantic**; its name is shown in the UI and in every report |
| 6 | Storage | `vectorstore/chroma_service.py` | ChromaDB persistent, cosine space; metadata: doc_id, filename, page (‑1 if none), section, chunk_index |
| 7 | Retrieval | `retrieval/retriever.py` | Top-k by cosine similarity, optional `doc_id` filter (single or `$in`), score = 1 − distance, results below `MIN_SCORE` (0.12) discarded |
| 8 | Context | `build_context` | Passages numbered `[S1]…[Sn]` inside a character budget (`CONTEXT_CHAR_BUDGET`, 6000); instruction-like phrases are replaced and the citation is flagged |
| 9 | Generation | `agent/nodes.py`, `services/rag_service.py` | System prompt: answer only from excerpts, cite `[S#]`, say when insufficient, treat excerpts as data, label general knowledge |
| 10 | Attribution | `format` node | Every citation carries filename, page, section, relevance, 300-char excerpt, `cited_in_answer`. Markers the model invented are **removed** and a warning is added; uncited answers get a warning. Page numbers come only from the extractor – the model never supplies them |

## Three different "no answer" situations (kept distinct)

1. **System error** – LLM/Ollama unreachable → HTTP 503 `llm_unavailable` with setup guidance.
2. **Retrieval failure** – nothing in the knowledge base is above the threshold → `insufficient_evidence`, LLM not called.
3. **Insufficient evidence in generation** – the model itself states the excerpts do not answer; this appears as normal answer text.

## Tuning

`CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `MIN_SCORE`, `CONTEXT_CHAR_BUDGET` (see `.env.example`). After changing chunking or the embedder,
use **Re-index** on each document. `MIN_SCORE=0.12` was chosen for the fallback embedder's score range and has **not** been
calibrated for MiniLM – see `evaluation/evaluation_report.md` for the false-refusal measurement and re-evaluate with the real model.
