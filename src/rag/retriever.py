from .embedder import Embedder
from .vector_store import VectorStore
from typing import List, Dict
import math

class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def retrieve(self, question, top_k=5, espace_filter=None, theme_filter=None):
        q_emb = self.embedder.embed([question])[0]
        # initial vector search (limiter le pré-filtrage)
        prefetch = max(top_k * 2, 10)
        results = self.vector_store.search(q_emb, prefetch, espace_filter, theme_filter)
        # ne re-ranker qu'un petit sous-ensemble
        candidates = results[:20]
        texts = [r.get("description", "") for r in candidates]
        doc_embs = self.embedder.embed(texts) if texts else []

        def cosine(a, b):
            if not a or not b:
                return -1.0
            s = sum(x*y for x, y in zip(a, b))
            return s  # embeddings are normalized -> dot = cosine

        scored: List[Dict] = []
        for doc, emb in zip(candidates, doc_embs):
            score = cosine(q_emb, emb)
            doc = dict(doc)
            doc["_score"] = score
            scored.append(doc)

        scored.sort(key=lambda d: d.get("_score", -1.0), reverse=True)
        return scored[:top_k]