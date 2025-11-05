from fastapi import FastAPI
from pydantic import BaseModel
from src.rag.retriever import Retriever
from src.rag.generator import Generator
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# ... (Vérification 'qdrant_data' et chargement des modèles) ...
print("Initialisation du Retriever et du Generator...")
retriever = Retriever()
generator = Generator() # Utilise flan-t5-base
print("✅ API RAG prête à l'emploi.")

app = FastAPI(title="API RAG Administration BF")

# ... (Configuration CORS - C'est très important, gardez-le) ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Un endpoint "hello world" à la racine (/)
@app.get("/")
def read_root():
    """Endpoint racine pour vérifier que l'API est en ligne."""
    return {"message": "Bonjour ! C'est l'API RAG. Je suis prêt à travailler. \n Pour acceder à mon GUI ici: https://huggingface.co/spaces/Dayende/frontend-rag"}
# --------------------

class Query(BaseModel):
    question: str
    top_k: int = 2 

class Source(BaseModel):
    titre: str | None
    url: str | None

class Response(BaseModel):
    answer: str
    sources: List[Source]


@app.post("/generate", response_model=Response)
def ask_rag_endpoint(query: Query):
    if not query.question:
        return {"answer": "Veuillez poser une question.", "sources": []}
    
    docs = retriever.retrieve(query.question, top_k=1)
    (answer_text, source_doc) = generator.generate(query.question, docs)
    
    sources_list = []
    if source_doc:
        sources_list.append(Source(
            titre=source_doc.get("titre", "Source inconnue"),
            url=source_doc.get("url", "#")
        ))

    return Response(answer=answer_text, sources=sources_list)