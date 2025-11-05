from fastapi import FastAPI
from pydantic import BaseModel
from src.rag.retriever import Retriever
from src.rag.generator import Generator
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# Initialisation des composants RAG
print("Initialisation du Retriever et du Generator...")
retriever = Retriever()
generator = Generator() # Utilise flan-t5-base
print("✅ API RAG prête à l'emploi.")

# Création de l'application FastAPI
app = FastAPI(title="API RAG Administration BF")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint racine pour vérifier que l'API est en ligne
@app.get("/")
def read_root():
    """Endpoint racine pour vérifier que l'API est en ligne."""
    return {"message": "Bonjour ! C'est l'API RAG. Je suis prêt à travailler. \n Pour acceder à mon GUI ici: https://huggingface.co/spaces/Dayende/frontend-rag"}

# Modèle pour la requête de l'utilisateur
class Query(BaseModel):
    question: str
    top_k: int = 2 

# Modèle pour les sources de la réponse
class Source(BaseModel):
    titre: str | None
    url: str | None

# Modèle pour la réponse de l'API
class Response(BaseModel):
    answer: str
    sources: List[Source]

# Endpoint pour générer une réponse à une question
@app.post("/generate", response_model=Response)
def ask_rag_endpoint(query: Query):
    """
    Endpoint pour générer une réponse à une question en utilisant le système RAG.
    
    Args:
        query: Objet contenant la question et le nombre de documents à récupérer
        
    Returns:
        Réponse générée avec les sources
    """
    # Vérifie si la question est vide
    if not query.question:
        return {"answer": "Veuillez poser une question.", "sources": []}
    
    # Récupère les documents pertinents
    docs = retriever.retrieve(query.question, top_k=1)
    # Génère la réponse
    (answer_text, source_doc) = generator.generate(query.question, docs)
    
    # Prépare la liste des sources
    sources_list = []
    if source_doc:
        sources_list.append(Source(
            titre=source_doc.get("titre", "Source inconnue"),
            url=source_doc.get("url", "#")
        ))

    # Retourne la réponse avec les sources
    return Response(answer=answer_text, sources=sources_list)