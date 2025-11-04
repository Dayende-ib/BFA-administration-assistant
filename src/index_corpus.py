import json
from rag.embedder import Embedder
from rag.vector_store import VectorStore
import torch

def index_corpus():
    with open("data/corpus.json", "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    embedder = Embedder()
    vector_store = VectorStore()
    
    # Create collection with the correct vector size for multilingual-e5-base (768 dimensions)
    vector_store.create_collection(vector_size=768)
    
    # Embed the descriptions
    texts = [doc["Description"] for doc in docs]
    embeddings = embedder.embed(texts)
    
    # Upsert with metadata (Thème, Espace, Coût)
    vector_store.upsert(embeddings, docs)
    print(f"Indexé {len(docs)} documents dans Qdrant")

if __name__ == "__main__":
    index_corpus()