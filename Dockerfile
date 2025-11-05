FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Pré-télécharge les modèles
RUN python -c "from transformers import pipeline; pipeline('text2text-generation', model='google/flan-t5-base', device=-1)"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base', device='cpu')"

COPY . .

# Exécute l'indexation une fois
RUN python index_db.py

# Expose le port 7860
EXPOSE 7860

# Lance le serveur API Uvicorn sur le bon port
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]