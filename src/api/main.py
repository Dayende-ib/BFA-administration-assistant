from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys
import glob

# Add src directory to PYTHONPATH for rag.* imports to work
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from rag.retriever import Retriever
    from rag.generator import Generator
except Exception as e:
    # Import errors will be logged on startup; API will still expose health endpoint
    Retriever = None
    Generator = None
    print("Warning: impossible d'importer les modules RAG:", e)

try:
    # index_corpus is a utility to (re)create the index from data/corpus.json
    import index_corpus
except Exception as e:
    index_corpus = None
    print("Info: index_corpus non disponible:", e)

try:
    from utils.settings import settings
except Exception:
    # Fallback minimal settings
    class _Fallback:
        ALLOW_ORIGINS = ["*"]
        MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    settings = _Fallback()

app = FastAPI(title="BFA Administration Assistant API")
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "ALLOW_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# variable to store the loaded model path (if any)
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

    # Initialize the retriever if available
    try:
        if Retriever is not None:
            retriever = Retriever()
    except Exception as e:
        print("Warning: erreur initialisation Retriever:", e)

    # Initialize the generator if available and if a model is mounted
    try:
        if Generator is not None:
            model_dir = getattr(settings, "MODEL_DIR", os.path.join(BASE_DIR, "models"))
            # default filename used in src/rag/generator.py
            default_name = "Llama-3.2-3B-Instruct-Q4_0.gguf"
            # Prioritize the default file if it exists, otherwise search for any *.gguf
            model_path_default = os.path.join(model_dir, default_name)
            model_path = None
            if os.path.exists(model_path_default):
                model_path = model_path_default
            else:
                # Search for other .gguf files in the directory
                try:
                    candidates = glob.glob(os.path.join(model_dir, "*.gguf")) if os.path.isdir(model_dir) else []
                except Exception:
                    candidates = []
                if candidates:
                    model_path = candidates[0]

            if model_path and os.path.exists(model_path):
                print(f"Info: chargement du modèle depuis {model_path}")
                generator = Generator(model_path=model_path)
                # keep the path for reporting
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
    """Readiness probe: vérifie retriever, generator et présence du modèle."""
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

    # Retrieve contextual documents
    try:
        docs = retriever.retrieve(
            req.question, 
            top_k=req.top_k,
            espace_filter=req.espace_filter,
            theme_filter=req.theme_filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur retrieval: {e}")

    # Generation
    if generator is None:
        # Return just the docs if no model
        return {"answer": "Modèle indisponible. Montez un modèle GGUF dans /app/src/models.", "sources": docs}

    try:
        answer = generator.generate(req.question, docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération: {e}")

    return {"answer": answer, "sources": docs}


@app.post("/reindex")
def reindex(background_tasks: BackgroundTasks):
    """Starts a corpus reindexing in the background.

    This operation calls `index_corpus.index_corpus()` which reads `data/corpus.json`,
    computes embeddings and upserts to Qdrant. Launch in background to
    avoid blocking the HTTP request.
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
    """Returns the status of model-related components.

    - retriever: bool
    - generator: bool
    - model_path: path of loaded model (or None)
    - indexer_available: bool (if index_corpus utility is importable)
    """
    status = {
        "retriever_initialized": bool(retriever),
        "generator_initialized": bool(generator),
        "model_path": generator_model_path,
        "indexer_available": bool(index_corpus),
    }
    return status