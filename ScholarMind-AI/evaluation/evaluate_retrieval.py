"""Retrieval evaluation: Precision@K, Recall@K, MRR on evaluation_dataset.json. Fully automatic and deterministic;
needs NO LLM. Uses whatever embedder the configuration selects (auto -> MiniLM if available, else the
lexical fallback) and RECORDS which one was used, so scores are never mislabeled.

Definitions (K in {1,3,5}); a retrieved chunk is RELEVANT if its (document, page|section) equals the expected unit:
  Precision@K = relevant chunks in top-K / K
  Recall@K    = |expected units found in top-K| / |expected units|   (one expected unit per question -> hit rate)
  MRR         = mean over questions of 1 / rank of the first relevant chunk (0 if none in top-10)
Out-of-scope questions are excluded from these metrics and reported separately (score vs. MIN_SCORE threshold).
Usage: python evaluation/evaluate_retrieval.py [--embedding auto|hashing|sentence-transformers]"""
import argparse
import json
import statistics

from common import RESULTS, build_services, expected_unit, load_questions, stamp, unit_of

KS = (1, 3, 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedding", default=None, help="override EMBEDDING_PROVIDER")
    args = ap.parse_args()
    s = build_services(args.embedding)
    from backend.app.retrieval.retriever import retrieve
    threshold = s.settings.min_score
    rows, oos = [], []
    for q in load_questions():
        hits = retrieve(s.embedder, s.store, q["question"], 10, 0.0)
        units = [unit_of(h) for h in hits]
        exp = expected_unit(q)
        if exp is None:
            top = hits[0]["score"] if hits else 0.0
            oos.append({"id": q["id"], "question": q["question"], "top_score": top, "passes_threshold": top >= threshold,
                        "top_source": f"{hits[0]['filename']} p.{hits[0]['page']}" if hits else None})
            continue
        rank = next((i + 1 for i, u in enumerate(units) if u == exp), None)
        row = {"id": q["id"], "question": q["question"], "expected": f"{exp[0]} {exp[1]}", "first_relevant_rank": rank,
               "top_score": hits[0]["score"] if hits else 0.0,
               "retrieved": [f"{u[0]} {u[1]} ({h['score']:.2f})" for u, h in zip(units[:5], hits[:5])]}
        for k in KS:
            row[f"precision@{k}"] = sum(u == exp for u in units[:k]) / k
            row[f"recall@{k}"] = 1.0 if exp in units[:k] else 0.0
        row["rr"] = 1.0 / rank if rank else 0.0
        rows.append(row)
    summary = {f"{m}@{k}": round(statistics.mean(r[f"{m}@{k}"] for r in rows), 3) for k in KS for m in ("precision", "recall")}
    summary["MRR"] = round(statistics.mean(r["rr"] for r in rows), 3)
    # Operational metrics: how the agent's relevance threshold (MIN_SCORE) behaves on this question set.
    false_refusals = [r["id"] for r in rows if r["top_score"] < threshold]
    summary["false_refusal_rate"] = round(len(false_refusals) / len(rows), 3)          # in-scope but below threshold
    summary["out_of_scope_correctly_refused"] = f"{sum(not o['passes_threshold'] for o in oos)}/{len(oos)}"
    result = {"timestamp": stamp(), "embedder": s.embedder.name, "semantic_embedder": not s.embedder.name.startswith("hashing"),
              "chunk_size": s.settings.chunk_size, "chunk_overlap": s.settings.chunk_overlap, "min_score_threshold": threshold,
              "in_scope_questions": len(rows), "out_of_scope_questions": len(oos), "false_refusal_ids": false_refusals, "summary": summary, "per_question": rows, "out_of_scope": oos}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Embedder: {s.embedder.name} (semantic={result['semantic_embedder']}) | {len(rows)} in-scope, {len(oos)} out-of-scope questions")
    for k, v in summary.items():
        print(f"  {k:14s} {v}")
    for r in rows:
        print(f"  {r['id']} rank={r['first_relevant_rank']} top={r['top_score']:.2f}  {r['question']}")
    print(f"  In-scope questions the agent would WRONGLY refuse at threshold {threshold}: {false_refusals or 'none'}")
    for o in oos:
        print(f"  {o['id']} OUT-OF-SCOPE top_score={o['top_score']:.2f} -> {'WRONGLY passes' if o['passes_threshold'] else 'correctly below'} threshold {threshold}")


if __name__ == "__main__":
    main()
