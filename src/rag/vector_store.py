from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
from typing import List, Dict, Any

# Nom de la collection Qdrant
COLLECTION_NAME = "procedures_bf"
# Chemin de stockage des données Qdrant
QDRANT_PATH = "qdrant_data"

class VectorStore:
    """Classe pour gérer le stockage et la recherche vectorielle avec Qdrant."""
    
    def __init__(self):
        # Initialisation du client Qdrant avec le chemin local
        self.client = QdrantClient(path=QDRANT_PATH)

    def create_collection(self, vector_size: int):
        """
        Crée une collection dans Qdrant si elle n'existe pas déjà.
        
        Args:
            vector_size: Dimension des vecteurs d'embedding
        """
        try:
            # Vérifie si la collection existe déjà
            self.client.get_collection(COLLECTION_NAME)
        except Exception:
            # Crée la collection si elle n'existe pas
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def upsert(self, embeddings: list[list[float]], documents: list[dict]):
        """
        Insère ou met à jour des documents dans la collection Qdrant.
        
        Args:
            embeddings: Liste des embeddings vectoriels
            documents: Liste des documents correspondants
        """
        # Crée les points à insérer dans Qdrant
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                # Sauvegarde tous les champs nécessaires pour la génération de réponse
                payload={
                    "titre": doc.get("Titre"),
                    "description": doc.get("Description"),
                    "url": doc.get("Adresse web"),
                    # Clés normalisées pour une extraction plus facile
                    "pieces": doc.get("Pièce(s) à fournir"), 
                    "cout": doc.get("Coût(s)"),
                    "conditions": doc.get("Conditions d'accès"),
                    "infos": doc.get("Informations complémentaires")
                }
            )
            for emb, doc in zip(embeddings, documents)
        ]
        # Insère les points dans la collection
        self.client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """
        Recherche les documents les plus similaires à un embedding de requête.
        
        Args:
            query_embedding: Embedding vectoriel de la requête
            top_k: Nombre de documents à retourner
            
        Returns:
            Liste des documents pertinents
        """
        # Effectue la recherche vectorielle
        hits = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=None
        )
        # Retourne les données des documents trouvés
        return [hit.payload for hit in hits if hit.payload is not None]