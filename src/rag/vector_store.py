from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import json
import uuid
import os


class VectorStore:
    def __init__(self, host=None, port=None):
        # Reading environment variables if present (Docker/.env compatibility)
        host = host or os.environ.get("QDRANT_HOST", "localhost")
        port = port or int(os.environ.get("QDRANT_PORT", 6333))

        self.collection_name = "procedures_bf"

        try:
            self.client = QdrantClient(host=host, port=port)
        except Exception as e:
            # Don't crash initialization: log and leave client as None
            print(f"Warning: unable to connect to Qdrant ({host}:{port}) : {e}")
            self.client = None

    def create_collection(self, vector_size=768):
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized. Start Qdrant or check QDRANT_HOST/QDRANT_PORT.")

        # Create collection with hybrid search support (both vector and keyword search)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            # Enable hybrid search with keyword indexing
        )

        # Create payload index for filtering
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="Espace"
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="Thème"
            )
        except Exception as e:
            print(f"Warning: unable to create payload indexes: {e}")

    def upsert(self, embeddings, documents):
        points = []
        for emb, doc in zip(embeddings, documents):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "titre": doc["Titre"],
                    "description": doc["Description"],
                    "url": doc["Adresse web"],
                    "source": doc.get("source", "ServicePublic.gov.bf"),
                    "Espace": doc.get("Espace", "Particuliers"),
                    "Thème": doc.get("Thème", "Non spécifié"),
                    "Coût(s)": doc.get("Coût(s)", "Non spécifié")
                }
            )
            points.append(point)
        
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized. Unable to upsert points.")

        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_embedding, top_k=5, espace_filter=None, theme_filter=None):
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized. Unable to perform search.")

        # Build filter conditions
        must_conditions = []
        if espace_filter:
            must_conditions.append(FieldCondition(
                key="Espace",
                match=MatchValue(value=espace_filter)
            ))
        if theme_filter:
            must_conditions.append(FieldCondition(
                key="Thème",
                match=MatchValue(value=theme_filter)
            ))

        search_filter = Filter(must=must_conditions) if must_conditions else None

        # Perform vector search with optional filters
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter
        )
        return [hit.payload for hit in hits]