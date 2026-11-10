"""Generation evaluation through the real agent graph. REQUIRES A REAL LLM (Ollama) - it refuses to run without one,
because scores computed from a mock would be meaningless. Run it on a machine where `ollama pull qwen2.5:3b-instruct` is done.

Automatic metrics per in-scope question (all computed from the system's own outputs, no external judge):
  status_ok            agent returned status 'answered'
  retrieved_expected   a citation comes from the expected page/section
  cites_expected       a citation that the ANSWER actually uses [S#] comes from the expected page/section
  citation_valid       no unsupported citation markers had to be removed from the answer
  keyword_coverage     fraction of the question's expected keywords present in the answer
  context_utilization  fraction of retrieved passages the answer actually cites
  faithfulness_proxy   fraction of the answer's content words that occur in the retrieved context (LEXICAL PROXY, not a
                       semantic judgement; it cannot detect a fluent but unsupported sentence made of context words)
Out-of-scope questions: pass only if status == 'insufficient_evidence' (unsupported-claim detection).
Human review columns are left EMPTY on purpose; fill them by reading each answer.
Usage:  python evaluation/evaluate_generation.py
        python evaluation/evaluate_generation.py --mock   (pipeline smoke test only; writes *.MOCK.json, never used in the report)"""
import argparse
import json
import re
import statistics
import sys

from common import RESULTS, build_services, expected_unit, load_questions, stamp, unit_of

_STOP = set("the a an of and or to in on for with is are was were be by as at it this that these those from which who how why what when "
            "can not but their they them its also into than then such each other more most some any all use used using based".split())


def content_words(text):
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="smoke-test with a scripted mock LLM (results are NOT valid)")
    ap.add_argument("--embedding", default=None)
    args = ap.parse_args()
    s = build_services(args.embedding)
    from backend.app.llm.provider_factory import get_llm, set_llm_override
    if args.mock:
        from backend.tests.test_agent import ScriptedLLM
        set_llm_override(ScriptedLLM())
    llm = get_llm(s.settings)
    st = llm.status()
    if not st["available"]:
        print(f"ERROR: no LLM available - {st['detail']}\nThis evaluation needs a real model; it will not invent scores.", file=sys.stderr)
        sys.exit(2)
    from backend.app.agent.graph import run_agent
    rows = []
    for q in load_questions():
        state = run_agent(s, question=q["question"])
        cites = state.get("citations") or []
        answer = state.get("answer", "")
        exp = expected_unit(q)
        row = {"id": q["id"], "question": q["question"], "expected": f"{exp[0]} {exp[1]}" if exp else "NONE (out of scope)",
               "status": state["status"], "tool": state.get("tool"), "answer": answer,
               "retrieved": [f"{c['filename']} {c['page'] or c['section']} ({c['score']:.2f})" for c in cites],
               "human_faithful": "", "human_complete": "", "human_notes": ""}
        if exp is None:
            row["pass_out_of_scope"] = state["status"] == "insufficient_evidence"
        else:
            used = [c for c in cites if c.get("cited_in_answer")]
            ctx = " ".join(c["excerpt"] for c in cites)
            words = content_words(answer)
            row.update(
                status_ok=state["status"] == "answered",
                retrieved_expected=any(unit_of(c) == exp for c in cites),
                cites_expected=any(unit_of(c) == exp for c in used),
                citation_valid=not any("unsupported citation" in w for w in state.get("warnings", [])),
                keyword_coverage=round(sum(k.lower() in answer.lower() for k in q["keywords"]) / max(len(q["keywords"]), 1), 3),
                context_utilization=round(len(used) / len(cites), 3) if cites else 0.0,
                faithfulness_proxy=round(len(words & content_words(ctx)) / len(words), 3) if words else 0.0)
        rows.append(row)
    scored = [r for r in rows if "status_ok" in r]
    oos = [r for r in rows if "pass_out_of_scope" in r]
    mean = lambda key: round(statistics.mean(float(r[key]) for r in scored), 3) if scored else None
    summary = {k: mean(k) for k in ("status_ok", "retrieved_expected", "cites_expected", "citation_valid", "keyword_coverage",
                                    "context_utilization", "faithfulness_proxy")}
    summary["out_of_scope_correctly_refused"] = f"{sum(r['pass_out_of_scope'] for r in oos)}/{len(oos)}"
    result = {"timestamp": stamp(), "llm": "MOCK - INVALID" if args.mock else f"{st['provider']}:{st['model']}", "embedder": s.embedder.name,
              "semantic_embedder": not s.embedder.name.startswith("hashing"), "summary": summary, "per_question": rows}
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / ("generation_results.MOCK.json" if args.mock else "generation_results.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"LLM: {result['llm']} | embedder: {s.embedder.name}\n" + "\n".join(f"  {k:32s} {v}" for k, v in summary.items()) + f"\nWritten to {out}")
    if args.mock:
        print("NOTE: --mock results are for pipeline testing only and are NOT valid evaluation scores.")


if __name__ == "__main__":
    main()
