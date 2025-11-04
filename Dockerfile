# Dockerfile pour le projet BFA-administration-assistant
# Basé sur Python slim, installe les dépendances listées dans requirements.txt
# Installe aussi Playwright et ses navigateurs (Chromium) et expose le port 8000

FROM python:3.13.0-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# Dépendances système requises pour Playwright, lxml et divers parsers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       ca-certificates \
       git \
       libnss3 \
       libx11-6 \
       libx11-xcb1 \
       libxcomposite1 \
       libxdamage1 \
       libxrandr2 \
       libxss1 \
       libasound2 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libcups2 \
       libpangocairo-1.0-0 \
       fonts-liberation \
       libgbm1 \
       libxml2-dev \
       libxslt1-dev \
       zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright (Chromium) - si Playwright est présent
RUN if python -c "import importlib,sys\n;sys.exit(0 if importlib.util.find_spec('playwright') else 1)"; then \
      python -m playwright install --with-deps chromium || true; \
    fi

# Copier le projet (ne pas copier les modèles volumineux, on doit les monter en volume)
COPY . .

# Crée un point de montage recommandée pour les modèles GGUF (ne pas les inclure dans l'image)
VOLUME ["/app/src/models"]

# Script pour télécharger automatiquement le modèle si nécessaire
RUN echo '#!/bin/bash\n\
import os\n\
import requests\n\
import sys\n\
\n\
MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_0.gguf"\n\
MODEL_PATH = "src/models/Llama-3.2-3B-Instruct-Q4_0.gguf"\n\
\n\
if not os.path.exists(MODEL_PATH):\n\
    print("Téléchargement du modèle Llama-3.2-3B-Instruct-Q4_0.gguf...")\n\
    try:\n\
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)\n\
        response = requests.get(MODEL_URL, stream=True, timeout=30)\n\
        response.raise_for_status()\n\
        with open(MODEL_PATH, "wb") as f:\n\
            for chunk in response.iter_content(chunk_size=8192):\n\
                if chunk:\n\
                    f.write(chunk)\n\
        print("Téléchargement terminé.")\n\
    except Exception as e:\n\
        print(f"Erreur lors du téléchargement du modèle: {e}")\n\
        print("Le modèle doit être monté manuellement via un volume.")\n\
else:\n\
    print("Modèle déjà présent.")\n\
' > download_model.py

# Télécharger le modèle pendant le build (avec gestion d'erreurs)
RUN python download_model.py || echo "Le téléchargement du modèle a échoué, mais le build continue."

EXPOSE 8000

# Commande par défaut : lance l'API si elle existe, sinon exécute main.py
# Ajustez la commande en fonction de la manière dont votre projet démarre en production
CMD ["sh", "-c", "if [ -f ./src/api/main.py ]; then \
      python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}; \
    elif [ -f ./main.py ]; then \
      python main.py; \
    else \
      echo 'Aucune entrée API détectée (src/api/main.py ou main.py). Démarrage d\"un shell.'; exec sh; \
    fi"]