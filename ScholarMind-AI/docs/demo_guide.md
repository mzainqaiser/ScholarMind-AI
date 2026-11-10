# Instructor Demonstration Guide (≈ 8 minutes)

**Before the demo:** run `scripts\setup.ps1` once; `ollama pull qwen2.5:3b-instruct`; start `scripts\start_backend.ps1` and `scripts\start_frontend.ps1`; open http://localhost:5173.
Check the top bar shows a green **LLM: qwen2.5…** badge (and no amber *Fallback embeddings* badge). If LLM is amber, demo Document Search only and show Settings → setup instructions.
CPU answers can take 20–60 s – ask the first question while you talk.

| Min | Step | What to do | What to point out |
|---|---|---|---|
| 0:00 | Dashboard | Show the empty dashboard | Real statistics, empty states, LLM/vector DB status |
| 0:45 | **Upload a PDF** | My Documents → upload `sample_data/ml_fundamentals.pdf` and `neural_networks.pdf`, category "Course" | Progress bar, status *indexed*, pages and chunk counts, **Preview** drawer, duplicate re-upload is rejected |
| 2:00 | **Ask + cited evidence** | AI Assistant → *"What is overfitting?"* | Answer with `[S1]` markers; open **Sources**: file, **page number**, excerpt, relevance; **Agent activity** shows tool = Document Q&A |
| 3:00 | **Follow-up** | *"Why does it happen?"* | Conversation memory: query is resolved from the previous turn; other chats stay separate |
| 3:45 | **Tool selection** | *"Find where K-means is discussed"* then *"Summarize ml_fundamentals"* | Different tools chosen (Document Search needs no LLM; Summarization covers the whole document) – visible in the badge and activity list |
| 4:45 | **Compare two documents** | Research Workspace → Compare → select both PDFs, text "learning" (or ask in chat: *"Compare supervised and unsupervised learning"*) | Evidence retrieved from each document, table of similarities/differences |
| 5:45 | **Notes / MCQs / flashcards** | Study Tools → Quizzes → select `ml_fundamentals.pdf`, count 5 → Generate; answer a question; then Flashcards and Notes | Interactive quiz scoring; every item carries a source; invalid items are dropped with a warning |
| 7:00 | **Honesty / safety** | Ask *"Who won the 1966 World Cup?"* | "Insufficient evidence" – the LLM was not even called. Mention prompt-injection filter, step limit |
| 7:30 | **Persistence + delete** | Restart the backend, reload: documents and chats remain. Delete a document | Metadata **and** vectors removed (Dashboard chunk count drops) |
| 8:00 | Evidence of testing | Show `submission/test_reports/` and `evaluation/evaluation_report.md` | 62 + 24 tests, 22-check end-to-end, retrieval metrics and the stated limitations |

**Be ready to explain:** why rules route intents (3B models are unreliable classifiers); why the LLM is skipped when evidence is missing; why page numbers can be trusted
(they come from the extractor, not the model); what the *Fallback embeddings* badge means; which parts were verified only with a mock LLM (see README "Verification status").
