from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    """Classe pour créer des embeddings de texte à partir de documents et de requêtes."""
    
    def __init__(self):
        # Initialisation du modèle multilingue pour les embeddings
        self.model = SentenceTransformer("intfloat/multilingual-e5-base", device="cpu")
        # Dimension des vecteurs d'embedding
        self.dim = 768

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Crée des embeddings pour les DOCUMENTS (passages) à stocker dans Qdrant.
        """
        # Ajoute le préfixe 'passage:' pour différencier les documents des requêtes
        prefixed_texts = [f"passage: {text}" for text in texts]
        print(f"Embedding de {len(prefixed_texts)} documents...")
        
        # Génère les embeddings pour tous les documents
        return self.model.encode(
            prefixed_texts, 
            normalize_embeddings=True, 
            show_progress_bar=True
        ).tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Crée un embedding pour la QUESTION (query) de l'utilisateur.
        """
        # Ajoute le préfixe 'query:' pour différencier les requêtes des documents
        prefixed_query = f"query: {query}"
        print(f"Embedding de la requête: '{prefixed_query}'")
        
        # Génère l'embedding pour la requête
        return self.model.encode(
            prefixed_query, 
            normalize_embeddings=True
        ).tolist()