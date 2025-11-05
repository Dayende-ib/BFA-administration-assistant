from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
from typing import List, Dict, Any

COLLECTION_NAME = "procedures_bf"
QDRANT_PATH = "qdrant_data"

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(path=QDRANT_PATH)

    def create_collection(self, vector_size: int):
        try:
            self.client.get_collection(COLLECTION_NAME)
        except Exception:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def upsert(self, embeddings: list[list[float]], documents: list[dict]):
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                # --- MODIFICATION CLÉ ---
                # Nous sauvegardons TOUS les champs dont le générateur aura besoin
                payload={
                    "titre": doc.get("Titre"),
                    "description": doc.get("Description"),
                    "url": doc.get("Adresse web"),
                    # Clés normalisées pour une extraction plus facile
                    "pieces": doc.get("Pièce(s) à fournir"), 
                    "cout": doc.get("Coût(s)"),
                    "conditions": doc.get("Conditions d’accès"),
                    "infos": doc.get("Informations complémentaires")
                }
                # --- FIN MODIFICATION ---
            )
            for emb, doc in zip(embeddings, documents)
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    # (La recherche est simplifiée, sans filtres)
    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        hits = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=None
        )
        return [hit.payload for hit in hits if hit.payload is not None]