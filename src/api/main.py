from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import sys
import glob

# Ajouter le répertoire src au PYTHONPATH pour que les imports rag.* fonctionnent
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from rag.retriever import Retriever
    from rag.generator import Generator
except Exception as e:
    # Les erreurs d'import seront enregistrées au démarrage ; l'API exposera toujours le point de terminaison de santé
    Retriever = None
    Generator = None
    print("Warning: impossible d'importer les modules RAG:", e)

try:
    # index_corpus est un utilitaire pour (re)créer l'index à partir de data/corpus.json
    import index_corpus
except Exception as e:
    index_corpus = None
    print("Info: index_corpus non disponible:", e)

try:
    from utils.settings import settings
except Exception:
    # Paramètres de secours minimaux
    class _Fallback:
        ALLOW_ORIGINS = ["*"]
        MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    settings = _Fallback()

app = FastAPI(title="API de l'assistant administratif BFA")
# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# variable pour stocker le chemin du modèle chargé (le cas échéant)
generator_model_path = None


class GenerateRequest(BaseModel):
    question: str
    top_k: int = 5
    espace_filter: Optional[str] = None
    theme_filter: Optional[str] = None


class GenerateResponse(BaseModel):
    answer: str
    sources: list[dict]


@app.on_event("startup")
def startup_event():
    global retriever, generator, generator_model_path
    retriever = None
    generator = None
    generator_model_path = None

    # Initialiser le récupérateur si disponible
    try:
        if Retriever is not None:
            retriever = Retriever()
            try:
                # préchauffage des embeddings (réduit la latence de la 1ère requête)
                retriever.embedder.embed(["warmup"])
            except Exception:
                pass
    except Exception as e:
        print("Warning: erreur initialisation Retriever:", e)

    # Initialiser le générateur si disponible et si un modèle est monté
    try:
        if Generator is not None:
            model_dir = getattr(settings, "MODEL_DIR", os.path.join(BASE_DIR, "models"))
            # nom de fichier par défaut utilisé dans src/rag/generator.py
            default_name = "Llama-3.2-3B-Instruct-Q4_0.gguf"
            # Prioriser le fichier par défaut s'il existe, sinon rechercher tout *.gguf
            model_path_default = os.path.join(model_dir, default_name)
            model_path = None
            if os.path.exists(model_path_default):
                model_path = model_path_default
            else:
                # Rechercher d'autres fichiers .gguf dans le répertoire
                try:
                    candidates = glob.glob(os.path.join(model_dir, "*.gguf")) if os.path.isdir(model_dir) else []
                except Exception:
                    candidates = []
                if candidates:
                    model_path = candidates[0]

            if model_path and os.path.exists(model_path):
                print(f"Info: chargement du modèle depuis {model_path}")
                generator = Generator(model_path=model_path)
                # conserver le chemin pour le rapport
                generator_model_path = model_path
            else:
                print(f"Info: aucun modèle .gguf trouvé dans {model_dir}. Le generator restera désactivé.")
    except Exception as e:
        print("Warning: erreur initialisation Generator:", e)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    """Sonde de disponibilité : vérifie retriever, generator et présence du modèle."""
    status = {
        "retriever": bool(retriever),
        "generator": bool(generator),
        "model_path": generator_model_path,
    }
    if not status["retriever"]:
        raise HTTPException(status_code=503, detail="Retriever non initialisé")
    # Generator peut être optionnel si on veut citations seules
    return status


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever non initialisé")

    # Récupérer les documents contextuels
    try:
        docs = retriever.retrieve(
            req.question, 
            top_k=req.top_k,
            espace_filter=req.espace_filter,
            theme_filter=req.theme_filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur retrieval: {e}")

    # Génération
    if generator is None:
        # Retourner juste les documents si aucun modèle
        return {"answer": "Modèle indisponible. Montez un modèle GGUF dans /app/src/models.", "sources": docs}

    try:
        answer = generator.generate(req.question, docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération: {e}")

    return {"answer": answer, "sources": docs}


@app.post("/reindex")
def reindex(background_tasks: BackgroundTasks):
    """Démarre une réindexation du corpus en arrière-plan.

    Cette opération appelle `index_corpus.index_corpus()` qui lit `data/corpus.json`,
    calcule les embeddings et les insère dans Qdrant. Lancer en arrière-plan pour
    éviter de bloquer la requête HTTP.
    """
    if index_corpus is None:
        raise HTTPException(status_code=503, detail="Indexeur non disponible dans le conteneur")

    try:
        background_tasks.add_task(index_corpus.index_corpus)
        return {"status": "reindex started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lancement reindex: {e}")


@app.get("/model/status")
def model_status():
    """Retourne l'état des composants liés au modèle.

    - retriever : bool
    - generator : bool
    - model_path : chemin du modèle chargé (ou None)
    - indexer_available : bool (si l'utilitaire index_corpus est importable)
    """
    status = {
        "retriever_initialized": bool(retriever),
        "generator_initialized": bool(generator),
        "model_path": generator_model_path,
        "indexer_available": bool(index_corpus),
    }
    return status

# Serve static files from frontend directory
# This should be at the end to avoid interfering with API routes
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")