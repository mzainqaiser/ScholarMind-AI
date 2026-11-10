"""Configurable character-window chunker with overlap. Chunks never cross a page/section boundary,
so every chunk keeps exact page and heading metadata for citations."""
import re
from typing import List

_BREAKS = ("\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ")


def _split_text(text: str, size: int, overlap: int) -> List[str]:
    if overlap >= size:
        raise ValueError("chunk overlap must be smaller than chunk size")
    out, start, n = [], 0, len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            floor = start + int(size * 0.7)          # prefer a natural boundary in the last 30% of the window
            for sep in _BREAKS:
                idx = text.rfind(sep, floor, end)
                if idx != -1:
                    end = idx + len(sep)
                    break
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return out


def chunk_sections(sections, doc_id: str, size: int = 800, overlap: int = 120):
    """Return chunk dicts: id, text, page, section, chunk_index. Exact duplicate chunks are dropped."""
    chunks, seen = [], set()
    for sec in sections:
        for piece in _split_text(sec.text, size, overlap):
            key = re.sub(r"\s+", " ", piece.lower())
            if key in seen:
                continue
            seen.add(key)
            idx = len(chunks)
            chunks.append({"id": f"{doc_id}:{idx}", "text": piece, "page": sec.page,
                           "section": sec.heading, "chunk_index": idx})
    return chunks
