from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore
from typing import List, Dict, Any

class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    # La signature de la fonction est simplifiée
    def retrieve(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        
        # 1. Utilise 'embed_query' (correction de notre étape précédente)
        q_emb = self.embedder.embed_query(question)
        
        # 2. Appelle la recherche SANS les filtres
        return self.vector_store.search(q_emb, top_k)