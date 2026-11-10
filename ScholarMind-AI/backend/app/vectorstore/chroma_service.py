"""Persistent ChromaDB wrapper. The collection name includes the embedder name so vectors from different
models/dimensions never mix."""
import chromadb
from chromadb.config import Settings as ChromaSettings


class VectorStore:
    def __init__(self, path, embedder_name: str):
        self.client = chromadb.PersistentClient(path=str(path), settings=ChromaSettings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name=f"scholarmind_{embedder_name}".replace(".", "_")[:60], metadata={"hnsw:space": "cosine"})

    def add_chunks(self, doc_id, filename, chunks, embeddings):
        if not chunks:
            return
        self.collection.upsert(
            ids=[c["id"] for c in chunks], documents=[c["text"] for c in chunks], embeddings=embeddings,
            metadatas=[{"doc_id": doc_id, "filename": filename, "page": c["page"] if c["page"] is not None else -1,
                        "section": c["section"] or "", "chunk_index": c["chunk_index"]} for c in chunks])

    def delete_document(self, doc_id):
        self.collection.delete(where={"doc_id": doc_id})

    def count(self, doc_id=None) -> int:
        if doc_id is None:
            return self.collection.count()
        return len(self.collection.get(where={"doc_id": doc_id}, include=[])["ids"])

    def query(self, embedding, top_k, doc_ids=None):
        total = self.collection.count()
        if total == 0:
            return []
        where = None
        if doc_ids:
            where = {"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": list(doc_ids)}}
        res = self.collection.query(query_embeddings=[embedding], n_results=min(top_k, total), where=where,
                                    include=["documents", "metadatas", "distances"])
        hits = []
        for cid, text, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append({"chunk_id": cid, "text": text, "doc_id": meta["doc_id"], "filename": meta["filename"],
                         "page": meta["page"] if meta["page"] >= 0 else None,
                         "section": meta["section"] or None, "score": round(1.0 - dist, 4)})
        return hits

    def get_chunks(self, doc_id):
        """All chunks of one document in reading order (used for summaries / study material)."""
        res = self.collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
        rows = []
        for cid, text, m in zip(res["ids"], res["documents"], res["metadatas"]):
            rows.append({"chunk_id": cid, "text": text, "doc_id": m["doc_id"], "filename": m["filename"],
                         "page": m["page"] if m["page"] >= 0 else None, "section": m["section"] or None,
                         "score": 1.0, "_i": m["chunk_index"]})
        rows.sort(key=lambda r: r["_i"])
        return rows
