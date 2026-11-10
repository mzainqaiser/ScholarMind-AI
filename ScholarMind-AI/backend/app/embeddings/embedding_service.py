"""Embedding providers behind one interface.
- SentenceTransformerEmbedder: the real semantic model (all-MiniLM-L6-v2, 384-d); needs a one-time model download.
- HashingEmbedder: deterministic lexical fallback (signed hashed uni+bigram TF, 384-d). It is NOT semantic; it exists
  so the pipeline and tests run offline. `name` is recorded so results are never mislabeled."""
import logging
import math
import re
import zlib
from typing import List

log = logging.getLogger("scholarmind.embeddings")
DIM = 384
_STOP = set("a an the of and or to in on for with is are was were be by as at it this that these those from "
            "what which who how why when does do did can about into than then".split())


class HashingEmbedder:
    name = "hashing-384"
    dim = DIM

    def _vec(self, text: str) -> List[float]:
        toks = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP]
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        v = [0.0] * self.dim
        for f in feats:
            h = zlib.crc32(f.encode())
            v[h % self.dim] += 1.0 if (h >> 16) & 1 else -1.0
        v = [math.copysign(math.log1p(abs(x)), x) for x in v]          # sublinear scaling, then L2 normalise
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]


class SentenceTransformerEmbedder:
    dim = DIM

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # heavy import, kept lazy
        self.model = SentenceTransformer(model_name)
        self.name = model_name.split("/")[-1]
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def get_embedder(provider: str, model_name: str):
    """'auto' tries the real model and falls back to hashing with a loud warning."""
    if provider == "hashing":
        return HashingEmbedder()
    try:
        return SentenceTransformerEmbedder(model_name)
    except Exception as exc:
        if provider == "sentence-transformers":
            raise RuntimeError(f"Embedding model '{model_name}' could not be loaded: {exc}") from exc
        log.warning("Falling back to non-semantic hashing embedder (%s). Install sentence-transformers "
                    "and allow the model download for real semantic search.", exc)
        return HashingEmbedder()
