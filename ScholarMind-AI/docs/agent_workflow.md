# Agent Workflow (LangGraph)

```
START → classify → select_tool → plan → retrieve → validate → generate ─┐ (retry ≤ 1 if output format invalid)
           │            │                               │         ▲────┘
           ▼            ▼                               ▼
        chitchat    unknown tool                insufficient evidence      all paths end in → format → END
```

State (`agent/state.py`) is a plain dict: question, selected documents, conversation history (this conversation only),
intent, tool, search query, retrieved hits, context, citations, answer, status, warnings, trace, step counter.

| Node | What it does |
|---|---|
| **classify** | Rule-based intent (`agent/routing.py`): chitchat · study_plan · flashcards · quiz · document_search · summarize · notes · compare · research · verify_missing · default document_qa. A forced tool (study buttons) overrides it |
| **select_tool** | Allow-list lookup in `TOOLS`; resolves the document scope (UI selection, or a document named in the question); parses counts/days/quiz type ("10 MCQs", "7-day plan") |
| **plan** | Builds the search query: strips command words, and resolves short or pronoun follow-ups ("Why does it happen?") with the previous user turn of the **same** conversation |
| **retrieve** | Strategy per tool: *query* (top-k), *coverage* (whole-document sampling inside the context budget when no specific topic is given, otherwise topic search), *compare* (separate retrieval from each selected document) |
| **validate** | Needs ≥1 passage above the threshold (compare needs evidence from ≥2 documents); otherwise status `insufficient_evidence` and the LLM is never called |
| **generate** | Builds the prompt (tool instructions + context + last 4 turns marked as non-evidence) and calls the LLM; the tool's parser validates the output. Failure → one retry that tells the model why it was rejected, then `tool_failed` |
| **format** | Removes invented citation markers, computes `cited_in_answer`, adds warnings, returns trace |

## The nine tools (`agent/tools/registry.py`)

| Tool | Retrieval | LLM | Output validation |
|---|---|---|---|
| document_search | top-8 | no | ranked passages with page numbers |
| summarize | coverage | yes | non-empty Markdown |
| compare | per-document | yes | non-empty Markdown (table + similarities/differences/conflicts) |
| notes | coverage | yes | non-empty Markdown |
| quiz | coverage | yes | strict JSON; each item needs a real source marker; MCQ answer must be one of the options (a letter is mapped to its option); bad items dropped with a warning |
| flashcards | coverage | yes | strict JSON; each card needs a real source marker |
| research | top-8 | yes | Markdown split into *evidence*, *gaps*, *labelled general knowledge* |
| document_qa | top-k | yes | non-empty Markdown |
| study_plan | coverage | yes | Markdown table |

## Safety

- **Prompt injection:** retrieved text is data. Instruction-like phrases ("ignore all previous instructions", "reveal your system prompt", "you are now…") are replaced before they reach the model, the citation is flagged, and the user sees a warning. This is a heuristic filter, **not a guarantee** – the system prompt also tells the model never to follow excerpt instructions.
- **Arbitrary tool execution:** impossible – only keys of `TOOLS` run, and tools can only read the vector store.
- **Unauthorised file access:** the agent never receives file paths; documents are addressed by generated ids.
- **Infinite loops:** every node counts a step; exceeding `AGENT_MAX_STEPS` ends with `iteration_limit`; the retry loop is capped at one retry.
- **Unsupported claims:** invented `[S#]` markers are stripped, uncited answers are flagged, quiz/flashcard items without a valid source are discarded.
- **Transparency:** the UI shows tool name, scope, query, passage counts and citations ("Agent activity"). Model reasoning is never exposed.
