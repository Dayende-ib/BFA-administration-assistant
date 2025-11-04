# Docker / Docker Compose — BFA-administration-assistant

Petit guide pour builder et lancer le projet en local avec Docker.

Pré-requis
- Docker
- (Optionnel) Docker Compose

## Téléchargement du modèle

Avant de lancer le conteneur, vous devez télécharger le modèle LLM requis:

1. Téléchargez le modèle `Llama-3.2-3B-Instruct-Q4_0.gguf` depuis:
   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
   
2. Placez le fichier dans le dossier `src/models/` du projet:
   ```
   BFA-administration-assistant/
   └── src/
       └── models/
           └── Llama-3.2-3B-Instruct-Q4_0.gguf
   ```

**Note:** Le modèle est automatiquement monté dans le conteneur via le volume défini dans `docker-compose.yml`.

## Builder l'image

PowerShell:

```powershell
docker build -t bfa-admin-assistant:latest .
```

## Lancer avec Docker Compose

```powershell
docker compose up --build
```

## Notes importantes

- Les modèles GGUF (gros fichiers) ne sont pas inclus dans l'image Docker et doivent être téléchargés séparément.
- Le dossier `src/models/` est automatiquement monté comme volume: `- ./src/models:/app/src/models`
- Si aucun modèle n'est trouvé, l'API retournera: "Modèle indisponible. Montez un modèle GGUF dans /app/src/models."
- `requirements.txt` contient déjà `fastapi` et `uvicorn`; l'image démarre `uvicorn src.api.main:app` par défaut.

## Débogage

Pour déboguer, vous pouvez lancer le conteneur et ouvrir un shell :

```powershell
docker run --rm -it -p 8000:8000 -v ${PWD}/src/models:/app/src/models bfa-admin-assistant:latest sh
```

## Endpoints exposés

- GET /health — vérifie si l'API répond
- POST /generate — payload JSON: { "question": "...", "top_k": 5 }
- GET /model/status — vérifie l'état du modèle

## Prochaines étapes recommandées

- Monter un stockage persistant pour Qdrant (déjà configuré via volume `qdrant_storage`).
- Ajuster `MODEL_DIR` si vos modèles sont ailleurs.