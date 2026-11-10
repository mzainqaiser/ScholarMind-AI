"""Semantic retrieval + context construction."""
import re

# Phrases that try to give orders to the model. Retrieved text is DATA; matches are flagged and neutralised.
_INJECTION = re.compile(r"(ignore|disregard|forget)\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts?)"
                        r"|you\s+are\s+now\s+|system\s+prompt|reveal\s+your\s+(prompt|instructions)", re.I)


def retrieve(embedder, store, query, top_k, min_score=0.0, doc_ids=None):
    hits = store.query(embedder.embed([query])[0], top_k, doc_ids)
    return [h for h in hits if h["score"] >= min_score]


def build_context(hits, char_budget):
    """Number chunks S1..Sn within a character budget. Returns (context_text, citations)."""
    parts, citations, used = [], [], 0
    for h in hits:
        text = h["text"]
        flagged = bool(_INJECTION.search(text))
        if flagged:
            text = _INJECTION.sub("[removed instruction-like text]", text)
        if used + len(text) > char_budget and citations:
            break
        text = text[: max(char_budget - used, 200)]
        sid = f"S{len(citations) + 1}"
        where = f"{h['filename']}" + (f", page {h['page']}" if h["page"] else "")
        parts.append(f"[{sid}] ({where})\n{text}")
        used += len(text)
        citations.append({"id": sid, "chunk_id": h["chunk_id"], "doc_id": h["doc_id"], "filename": h["filename"],
                          "page": h["page"], "section": h["section"], "score": h["score"],
                          "excerpt": text[:300], "injection_suspected": flagged})
    return "\n\n".join(parts), citations
