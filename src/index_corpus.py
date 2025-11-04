import json
import os
import time
from rag.embedder import Embedder
from rag.vector_store import VectorStore
import torch

def index_corpus():
    # Resolve project root and data path robustly
    base_dir = os.path.dirname(os.path.dirname(__file__))
    corpus_path = os.path.join(base_dir, "data", "corpus.json")

    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"corpus.json introuvable à l'emplacement attendu: {corpus_path}")

    with open(corpus_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    embedder = Embedder()
    vector_store = VectorStore()
    
    # Wait for Qdrant to be ready (up to ~30s)
    for _ in range(30):
        try:
            if vector_store.ping():
                break
        except Exception:
            pass
        time.sleep(1)

    # Skip reindex if collection already has points unless FORCE_REINDEX=1
    force = os.environ.get("FORCE_REINDEX", "0") == "1"
    try:
        # If collection exists and has points, skip
        info = vector_store.client.get_collection(vector_store.collection_name)
        count = vector_store.client.count(vector_store.collection_name, exact=True).count
        if (count or 0) > 0 and not force:
            print(f"Collection '{vector_store.collection_name}' contient déjà {count} points. Saut de l'indexation (FORCE_REINDEX=1 pour forcer).")
            return
    except Exception:
        # If collection doesn't exist yet, we'll create it below
        pass

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