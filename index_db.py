import json
import os
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

CORPUS_PATH = os.path.join("data", "corpus.json")

def main():
    print("Démarrage de l'indexation (Mode Extraction)...")
    
    if not os.path.exists(CORPUS_PATH):
        print(f"ERREUR: Fichier '{CORPUS_PATH}' non trouvé.")
        return

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    print(f"Chargement de {len(docs)} documents (Corpus COMPLET) depuis '{CORPUS_PATH}'.")

    embedder = Embedder()
    vector_store = VectorStore()
    vector_store.create_collection(vector_size=embedder.dim)

    # Nous créons l'embedding à partir du Titre ET de la Description
    texts_to_embed = []
    for doc in docs:
        titre = doc.get("Titre", "")
        description = doc.get("Description", "")
        # Combine Titre et Description pour une recherche plus pertinente
        combined_text = f"Titre: {titre}. Description: {description}"
        texts_to_embed.append(combined_text)

    print(f"Génération des embeddings pour {len(texts_to_embed)} textes...")
    embeddings = embedder.embed_documents(texts_to_embed) # Utilise la fonction 'passage:'

    print("Insertion des données (avec tous les champs) dans Qdrant...")
    # 'docs' contient la liste complète des documents JSON
    vector_store.upsert(embeddings, docs)

    print("✅ Indexation (Mode Extraction) terminée !")
    print(f"La base de données est sauvegardée dans le dossier 'qdrant_data'.")

if __name__ == "__main__":
    main()