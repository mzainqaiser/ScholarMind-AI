# Submission Checklist

## A. Verified in the build environment (re-runnable with `scripts\verify_project.ps1`)
- [x] Backend tests: 62 passed (`submission/test_reports/backend_pytest.txt`)
- [x] Frontend tests: 24 passed (`frontend_vitest.txt`) · TypeScript clean + production build (`frontend_build.txt`)
- [x] HTTP end-to-end through the frontend proxy: 22/22 checks, including backend restart persistence and delete consistency (`e2e_flow.txt`)
- [x] Retrieval evaluation executed (lexical fallback embedder) (`retrieval_evaluation.txt`, `evaluation/evaluation_report.md`)
- [x] Acceptance items 1–7, 11, 13, 14, 15 exercised by the HTTP-level end-to-end run. Items 8–10 and 12 (grounded answers, citations, tool execution, study material) were exercised **only with the mock LLM**; how citations *look* in the UI is covered by component tests, not by a real browser

## B. YOU must do on your own machine before submitting (not possible in the build environment)
- [ ] `scripts\setup.ps1` completes; `scripts\verify_project.ps1` shows all PASS on **Windows**
- [ ] `ollama pull qwen2.5:3b-instruct`; top bar shows green **LLM** badge and **no** *Fallback embeddings* badge (MiniLM downloaded)
- [ ] Upload the sample PDFs; ask real questions; confirm citations show correct pages; try quiz / flashcards / compare / notes with the **real** model
- [ ] Run `python evaluation/evaluate_retrieval.py` (now with MiniLM) and `python evaluation/evaluate_generation.py`, then `python evaluation/build_report.py`; fill the human-review columns
- [ ] If MiniLM scores differ, re-assess `MIN_SCORE` and update the report numbers (the report currently states fallback-embedder results)
- [ ] Capture the screenshots listed in `screenshots/README.md` (none are included)
- [ ] Practise the demo in `docs/demo_guide.md`

## C. Package contents (see README for details)
- [x] Backend source · frontend source · agent + RAG pipeline · requirements · `.env.example` · `.gitignore`
- [x] README, architecture, RAG pipeline, agent workflow, API reference, technical report, demo guide
- [x] Evaluation scripts, dataset, report · automated tests · sample documents (original text) · scripts · test reports
- [x] Excluded: virtualenv, `node_modules`, caches, model weights, uploaded/private documents, credentials

## D. Known gaps (also in README)
No real-LLM run · no MiniLM run · no browser/Playwright run and no screenshots · PowerShell scripts unexecuted · no LangChain, re-ranker, streaming, docker-compose or second LLM provider.
