"""LangGraph nodes. Pipeline: classify -> select_tool -> plan -> retrieve -> validate -> generate -> format.
Every node is step-counted; exceeding the budget ends the run with status 'iteration_limit'."""
import re

from ..llm.provider_factory import get_llm
from ..retrieval.retriever import build_context, retrieve as semantic_retrieve
from .routing import build_search_query, classify_intent, parse_options, resolve_docs, topic_query
from .tools.registry import SYSTEM, TOOLS, ToolOutputError, render_instructions

HELP_TEXT = ("Hi! I'm ScholarMind. I can **search**, **summarise**, **compare**, make **study notes**, **quizzes**, "
             "**flashcards**, a **study plan**, run **research** on a topic, or answer questions — all from your uploaded documents.")
INSUFFICIENT = {
    "default": "I couldn't find enough relevant material in the selected documents to answer this. "
               "Try rephrasing, selecting different documents, or uploading the missing source.",
    "compare": "I need evidence for every subject being compared, and the documents don't provide it. "
               "Select at least two documents or name concepts that appear in your notes.",
}


def _step(state, label, detail=""):
    return [*state.get("trace", []), {"step": label, "detail": detail}]


def build_nodes(s):
    max_steps = s.settings.agent_max_steps

    def guarded(fn):
        def wrapper(state):
            if state.get("status") == "iteration_limit":
                return {}
            steps = state.get("steps", 0) + 1
            if steps > max_steps:
                return {"steps": steps, "status": "iteration_limit",
                        "error": f"Stopped after {max_steps} steps to avoid an endless loop.",
                        "trace": _step(state, "Stopped", "Step limit reached")}
            return {**fn(state), "steps": steps}
        return wrapper

    @guarded
    def classify(state):
        intent = state.get("forced_tool") or classify_intent(state["question"], bool(state.get("history")))
        out = {"intent": intent, "trace": _step(state, "Understanding your question", f"Intent: {intent}")}
        if intent == "chitchat":
            out.update(status="chitchat", answer=HELP_TEXT, citations=[])
        return out

    @guarded
    def select_tool(state):
        name = "document_search" if state["intent"] == "verify_missing" else state["intent"]
        if name not in TOOLS:                                # allow-list: unknown tools can never run
            return {"status": "tool_failed", "error": f"Unknown tool '{name}'.", "trace": _step(state, "Tool selection failed")}
        docs = resolve_docs(state["question"], state.get("doc_ids") or [], s.db.list_documents())
        opts = parse_options(state["question"], state.get("options"))
        scope = f"{len(docs)} selected document(s)" if docs else "all documents"
        return {"tool": name, "scoped_docs": docs, "options": opts,
                "trace": _step(state, f"Selected tool: {TOOLS[name].title}", f"Scope: {scope}")}

    @guarded
    def plan(state):
        history, q = state.get("history", []), state["question"]
        if state["intent"] == "verify_missing":
            prev = [m["content"] for m in history if m["role"] == "user"]
            query = topic_query(prev[-1]) or prev[-1]
        else:
            base = build_search_query(q, history)
            topic = topic_query(base)
            query = topic if TOOLS[state["tool"]].retrieval == "coverage" else (topic or base)
        return {"search_query": query, "trace": _step(state, "Planning retrieval", f"Search query: “{query}”" if query else "Whole-document coverage")}

    @guarded
    def retrieve(state):
        tool, docs, query = TOOLS[state["tool"]], state.get("scoped_docs", []), state.get("search_query", "")
        top_k = max(tool.top_k, s.settings.top_k) if tool.top_k > 5 else s.settings.top_k
        min_score, hits = s.settings.min_score, []
        if tool.retrieval == "compare" and len(docs) >= 2:
            for d in docs:
                hits += semantic_retrieve(s.embedder, s.store, query, 4, min_score, [d])
        elif tool.retrieval == "coverage":
            file_tokens = {t for d in docs for t in re.findall(r"[a-z0-9]+", (s.db.get_document(d) or {}).get("filename", "").lower())}
            residual = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in file_tokens]
            if not residual:                                   # no specific topic -> cover whole documents
                targets = docs or [d["id"] for d in s.db.list_documents() if d["status"] == "indexed"][:5]
                budget = s.settings.context_char_budget // max(len(targets), 1)
                for d in targets:
                    chunks = s.store.get_chunks(d)
                    total = sum(len(c["text"]) for c in chunks) or 1
                    n = len(chunks) if total <= budget else max(1, int(len(chunks) * budget / total))
                    hits += [chunks[int(i * len(chunks) / n)] for i in range(n)] if chunks else []
            else:
                hits = semantic_retrieve(s.embedder, s.store, query, 8, min_score, docs or None)
        else:
            hits = semantic_retrieve(s.embedder, s.store, query, top_k, min_score, docs or None)
        context, citations = build_context(hits, s.settings.context_char_budget)
        warnings = list(state.get("warnings", []))
        flagged = sorted({c["filename"] for c in citations if c["injection_suspected"]})
        if flagged:
            warnings.append(f"Instruction-like text found in {', '.join(flagged)} was treated as data and ignored.")
        n_docs = len({c["doc_id"] for c in citations})
        return {"hits": hits, "context": context, "citations": citations, "warnings": warnings,
                "trace": _step(state, "Retrieving documents", f"{len(citations)} passage(s) from {n_docs} document(s)")}

    @guarded
    def validate(state):
        cites, docs = state.get("citations", []), state.get("scoped_docs", [])
        ok = bool(cites)
        reason = "sufficient evidence" if ok else "no relevant passages above the relevance threshold"
        if ok and state["tool"] == "compare" and len(docs) >= 2 and len({c["doc_id"] for c in cites}) < 2:
            ok, reason = False, "evidence found for only one document"
        out = {"trace": _step(state, "Analyzing evidence", reason)}
        if not ok:
            out.update(status="insufficient_evidence", answer=INSUFFICIENT.get(state["tool"], INSUFFICIENT["default"]))
        return out

    @guarded
    def generate(state):
        tool, opts, cites = TOOLS[state["tool"]], state["options"], state["citations"]
        if not tool.needs_llm:                                 # document_search: ranked passages, no model call
            lines = [f"**{i}. {c['filename']}" + (f" — page {c['page']}" if c["page"] else "") +
                     f"** (relevance {c['score']:.2f})\n> {c['excerpt']}" for i, c in enumerate(cites, 1)]
            return {"status": "answered", "answer": "\n\n".join(lines), "error": None,
                    "trace": _step(state, "Generating response", "Ranked passages (no LLM needed)")}
        hist = "".join(f"{m['role'].upper()}: {m['content'][:300]}\n" for m in state.get("history", [])[-4:])
        prompt = (f"TOOL: {tool.name}\n\nCONVERSATION HISTORY (context only, not evidence):\n{hist or '(none)'}\n"
                  f"CONTEXT:\n{state['context']}\n\nTASK: {render_instructions(tool, opts)}\nUSER REQUEST: {state['question']}")
        if state.get("error"):
            prompt += f"\nIMPORTANT: your previous output was rejected ({state['error']}). Follow the required format exactly."
        raw = get_llm(s.settings).generate(SYSTEM, prompt)     # LLMUnavailable propagates -> HTTP 503
        try:
            answer, structured, warns = tool.parser(raw, {c["id"] for c in cites}, opts)
        except ToolOutputError as exc:
            return {"attempts": state.get("attempts", 0) + 1, "error": str(exc),
                    "trace": _step(state, "Generating response", f"Output rejected ({exc}); retrying")}
        return {"answer": answer, "structured": structured, "status": "answered", "error": None,
                "warnings": [*state.get("warnings", []), *warns],
                "trace": _step(state, "Generating response", f"{tool.title} complete")}

    def format_response(state):
        status = state.get("status") or "tool_failed"          # generation never succeeded -> tool_failed
        out = {"status": status, "trace": state.get("trace", [])}
        if status == "answered":
            valid = {c["id"] for c in state["citations"]}
            used = set(re.findall(r"\[(S\d+)\]", state["answer"]))
            if state.get("structured"):
                items = state["structured"].get("items") or state["structured"].get("cards") or []
                used |= {i["source"] for i in items}
            bad = used - valid
            answer = re.sub(r"\s?\[(S\d+)\]", lambda m: m.group(0) if m.group(1) in valid else "", state["answer"])
            for c in state["citations"]:
                c["cited_in_answer"] = c["id"] in used
            warns = list(state.get("warnings", []))
            if bad:
                warns.append(f"Removed unsupported citation markers: {', '.join(sorted(bad))}.")
            if state["tool"] in ("document_qa", "research", "summarize", "compare") and not (used & valid):
                warns.append("The model did not cite any source; verify this answer against the documents.")
            out.update(answer=answer, warnings=warns, citations=state["citations"])
        elif status == "tool_failed":
            out.update(answer="I couldn't produce a valid result after retrying. Please try again or rephrase.",
                       citations=state.get("citations", []))
        elif status == "iteration_limit":
            out.update(answer="I stopped because the request needed too many steps. Please simplify it.", citations=[])
        else:
            out.setdefault("citations", state.get("citations", []))
        return out

    return {"classify": classify, "select_tool": select_tool, "plan": plan, "retrieve": retrieve,
            "validate": validate, "generate": generate, "format": format_response}
