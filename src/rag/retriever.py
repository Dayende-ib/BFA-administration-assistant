from .embedder import Embedder
from .vector_store import VectorStore

class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def retrieve(self, question, top_k=5, espace_filter=None, theme_filter=None):
        q_emb = self.embedder.embed([question])[0]
        results = self.vector_store.search(q_emb, top_k, espace_filter, theme_filter)
        return results