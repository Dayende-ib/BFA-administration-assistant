from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(":memory:")
        self.collection_name = "procedures_bf"

    def create_collection(self, vector_size=768):
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def upsert(self, embeddings, documents):
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "titre": doc["Titre"],
                    "description": doc["Description"],
                    "url": doc["Adresse web"],
                    "Espace": doc.get("Espace", ""),
                    "Thème": doc.get("Thème", "")
                }
            )
            for emb, doc in zip(embeddings, documents)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"{len(points)} documents ont été ajoutés à l'index.")

    def search(self, query_embedding, top_k=5, espace_filter=None, theme_filter=None):
        must = []
        if espace_filter:
            must.append(FieldCondition(key="Espace", match=MatchValue(value=espace_filter)))
        if theme_filter:
            must.append(FieldCondition(key="Thème", match=MatchValue(value=theme_filter)))
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(must=must) if must else None
        )
        return [hit.payload for hit in hits]