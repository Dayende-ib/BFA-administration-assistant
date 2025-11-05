from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore
from typing import List, Dict, Any

class Retriever:
    """Classe pour récupérer les documents pertinents en fonction d'une question."""
    
    def __init__(self):
        # Initialisation de l'embedder et du stockage vectoriel
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def retrieve(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère les documents les plus pertinents pour une question donnée.
        
        Args:
            question: La question de l'utilisateur
            top_k: Nombre de documents à récupérer (par défaut 5)
            
        Returns:
            Liste des documents pertinents
        """
        # Crée un embedding pour la question
        q_emb = self.embedder.embed_query(question)
        
        # Recherche les documents similaires dans la base vectorielle
        return self.vector_store.search(q_emb, top_k)