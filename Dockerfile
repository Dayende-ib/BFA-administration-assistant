# Dockerfile pour le projet BFA-administration-assistant (runtime Python 3.12)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# Aucune dépendance système lourde requise pour le RAG CPU-only (torch/transformers ont des wheels)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Copier le projet (ne pas copier les modèles volumineux, on doit les monter en volume)
COPY . .

# Crée un point de montage recommandé pour les modèles GGUF (ne pas les inclure dans l'image)
VOLUME ["/app/src/models"]

EXPOSE 8000

# Commande par défaut : lance l'API
CMD ["sh", "-c", "python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]