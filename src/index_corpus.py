# src/index_corpus.py
import json
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

def index_corpus():
    with open("data/corpus.json", "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    embedder = Embedder()
    vector_store = VectorStore()
    vector_store.create_collection()
    
    texts = [doc["Description"] for doc in docs]
    embeddings = embedder.embed(texts)
    vector_store.upsert(embeddings, docs)
    print(f"Indexé {len(docs)} documents")

if __name__ == "__main__":
    index_corpus()