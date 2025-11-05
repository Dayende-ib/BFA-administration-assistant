import json
import os
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

# Chemin vers le fichier de corpus
CORPUS_PATH = os.path.join("data", "corpus.json")

def main():
    """Fonction principale pour indexer les documents dans la base vectorielle."""
    print("Démarrage de l'indexation (Mode Extraction)...")
    
    # Vérifie si le fichier de corpus existe
    if not os.path.exists(CORPUS_PATH):
        print(f"ERREUR: Fichier '{CORPUS_PATH}' non trouvé.")
        return

    # Charge les documents depuis le fichier JSON
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    print(f"Chargement de {len(docs)} documents (Corpus COMPLET) depuis '{CORPUS_PATH}'.")

    # Initialise les composants pour l'indexation
    embedder = Embedder()
    vector_store = VectorStore()
    vector_store.create_collection(vector_size=embedder.dim)

    # Prépare les textes à encoder (titre + description)
    texts_to_embed = []
    for doc in docs:
        titre = doc.get("Titre", "")
        description = doc.get("Description", "")
        # Combine Titre et Description pour une recherche plus pertinente
        combined_text = f"Titre: {titre}. Description: {description}"
        texts_to_embed.append(combined_text)

    print(f"Génération des embeddings pour {len(texts_to_embed)} textes...")
    # Génère les embeddings pour tous les documents
    embeddings = embedder.embed_documents(texts_to_embed)

    print("Insertion des données (avec tous les champs) dans Qdrant...")
    # Insère les documents et leurs embeddings dans la base vectorielle
    vector_store.upsert(embeddings, docs)

    print("✅ Indexation (Mode Extraction) terminée !")
    print(f"La base de données est sauvegardée dans le dossier 'qdrant_data'.")

if __name__ == "__main__":
    main()