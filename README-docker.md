# Docker / Docker Compose — BFA-administration-assistant

Petit guide pour builder et lancer le projet en local avec Docker.

Pré-requis
- Docker
- (Optionnel) Docker Compose

Builder l'image

PowerShell:

```powershell
docker build -t bfa-admin-assistant:latest .
```

Lancer avec Docker Compose

```powershell
docker compose up --build
```

Notes importantes
- Les modèles GGUF (gros fichiers dans `src/models`) ne sont pas inclus dans l'image. Montez-les en tant que volume : `- ./src/models:/app/src/models` (c'est déjà configuré dans `docker-compose.yml`).
- Si vous utilisez le module `gpt4all`, installez le modèle GGUF attendu sous `src/models` et adaptez le nom si nécessaire.
- `requirements.txt` contient déjà `fastapi` et `uvicorn`; l'image démarre `uvicorn src.api.main:app` par défaut.
- Pour débogage, vous pouvez lancer le conteneur et ouvrir un shell :

```powershell
docker run --rm -it -p 8000:8000 -v ${PWD}/src/models:/app/src/models bfa-admin-assistant:latest sh
```

Endpoints exposés
- GET /health — vérifie si l'API répond
- POST /generate — payload JSON: { "question": "...", "top_k": 5 }

Prochaines étapes recommandées
- Monter un stockage persistant pour Qdrant (déjà configuré via volume `qdrant_storage`).
- Ajuster `MODEL_DIR` si vos modèles sont ailleurs.
