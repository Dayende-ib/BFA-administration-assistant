# Assistant IA pour l'Administration du Burkina Faso

**Équipe : FASO DEME**

**Membres :**
- DIALLO Djeneba
- OUGDA Ibrahim
- SILGA Patricia

Ce projet est un assistant basé sur une architecture RAG (Retrieval-Augmented Generation) pour répondre aux questions des usagers sur les démarches administratives au Burkina Faso.

## 🎯 Sujet choisi et justification

Le sujet choisi est "Administration (procédures)" du Burkina Faso. Ce choix est pertinent car:
- Il répond à un besoin concret des citoyens burkinabè qui ont souvent des difficultés à naviguer dans les procédures administratives
- Les informations sont accessibles en ligne via les sites gouvernementaux
- Cela permet de démontrer l'application des technologies open source à un problème local important

## 🏗️ Architecture technique

L'application suit une architecture RAG (Retrieval-Augmented Generation) :

1.  **Indexation ([index_db.py](file:///e:/BFA-administration-assistant/index_db.py))**:
    -   Les documents du [corpus.json](file:///e:/BFA-administration-assistant/data/corpus.json) sont chargés.
    -   Pour chaque document, un embedding est créé en utilisant le modèle `intfloat/multilingual-e5-base`.
    -   Les embeddings et les métadonnées des documents sont stockés dans une base de données vectorielle Qdrant.

2.  **Requête de l'utilisateur**:
    -   L'utilisateur pose une question via l'interface web ou l'API.
    -   La question est transformée en embedding avec le même modèle `intfloat/multilingual-e5-base`.
    -   Cet embedding est utilisé pour rechercher les documents les plus similaires dans Qdrant ([retriever.py](file:///e:/BFA-administration-assistant/src/rag/retriever.py)).
    -   Les documents pertinents sont récupérés et servent de contexte.
    -   Le modèle `google/flan-t5-base` génère une réponse en se basant sur la question de l'utilisateur et le contexte fourni ([generator.py](file:///e:/BFA-administration-assistant/src/rag/generator.py)).
    -   La réponse est renvoyée via l'API ou affichée dans l'interface.

## 🚀 Technologies open source utilisées

- **Python** : Langage de programmation principal
- **FastAPI** : Pour l'API web ([Licence MIT](https://github.com/tiangolo/fastapi/blob/master/LICENSE))
- **Transformers (Hugging Face)** : Pour le modèle de génération de texte ([google/flan-t5-base](https://huggingface.co/google/flan-t5-base)) ([Licence Apache 2.0](https://github.com/huggingface/transformers/blob/main/LICENSE))
- **Sentence-Transformers** : Pour la création des embeddings ([intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base)) ([Licence Apache 2.0](https://github.com/UKPLab/sentence-transformers/blob/master/LICENSE))
- **Qdrant** : Comme base de données vectorielle ([Licence Apache 2.0](https://github.com/qdrant/qdrant/blob/master/LICENSE))
- **Docker** : Pour la conteneurisation de l'application ([Licence Apache 2.0](https://github.com/docker/docker-ce/blob/master/LICENSE))

## ⚙️ Instructions d'installation

1.  **Clonez le dépôt :**
    ```bash
    git clone <url_du_depot>
    cd BFA-administration-assistant
    ```

2.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ Utilisation

1.  **Indexez les données :**
    Avant de lancer l'application, vous devez créer la base de données vectorielle en exécutant le script suivant :
    ```bash
    python index_db.py
    ```
    Ce script va lire les documents dans [data/corpus.json](file:///e:/BFA-administration-assistant/data/corpus.json), générer les embeddings et les stocker dans Qdrant. Le tout sera sauvegardé dans le dossier `qdrant_data`.

2.  **Lancez l'application :**
    ```bash
    python api.py
    ```

3.  **Accédez à l'interface :**
    Vous pouvez accéder à l'interface en ligne à cette adresse : https://huggingface.co/spaces/Dayende/frontend-rag
    
    Ou ouvrez le fichier [frontend/index.html](file:///e:/BFA-administration-assistant/frontend/index.html) dans votre navigateur pour utiliser l'interface locale.
    
    Ou accédez directement à l'API via `http://localhost:8000`.

## 🐳 Utilisation avec Docker

Vous pouvez également construire et lancer l'application avec Docker :

```bash
docker build -t bfa-admin-assistant .
docker run -p 8000:8000 bfa-admin-assistant
```

## 📁 Structure du projet

-   [api.py](file:///e:/BFA-administration-assistant/api.py): Point d'entrée de l'API FastAPI.
-   [index_db.py](file:///e:/BFA-administration-assistant/index_db.py): Script pour l'indexation des données dans Qdrant.
-   [requirements.txt](file:///e:/BFA-administration-assistant/requirements.txt): Liste des dépendances Python.
-   [Dockerfile](file:///e:/BFA-administration-assistant/Dockerfile): Pour construire l'image Docker de l'application.
-   `data/`: Contient les données brutes.
    -   [corpus.json](file:///e:/BFA-administration-assistant/data/corpus.json): Le corpus de documents sur les démarches administratives.
-   `src/rag/`: Contient le coeur de l'architecture RAG.
    -   [embedder.py](file:///e:/BFA-administration-assistant/src/rag/embedder.py): Gère la création des embeddings pour les documents et les requêtes.
    -   [generator.py](file:///e:/BFA-administration-assistant/src/rag/generator.py): Gère la génération de la réponse à partir du contexte et de la question.
    -   [retriever.py](file:///e:/BFA-administration-assistant/src/rag/retriever.py): Gère la recherche des documents pertinents dans la base de données vectorielle.
    -   [vector_store.py](file:///e:/BFA-administration-assistant/src/rag/vector_store.py): Gère les interactions avec la base de données vectorielle Qdrant.
-   `frontend/`: Contient l'interface utilisateur web.
    -   [index.html](file:///e:/BFA-administration-assistant/frontend/index.html): Page principale de l'interface.
    -   [script.js](file:///e:/BFA-administration-assistant/frontend/script.js): Logique frontend et communication avec l'API.
    -   [style.css](file:///e:/BFA-administration-assistant/frontend/style.css): Styles de l'interface.
-   `evaluation/`: Contient les tests d'évaluation.
    -   [test_question.json](file:///e:/BFA-administration-assistant/evaluation/test_question.json): Jeu de test de 20 questions avec réponses attendues.

## 🧪 Résultats d'évaluation

L'évaluation du système a été effectuée avec un jeu de 23 questions présentes dans [evaluation/test_question.json](file:///e:/BFA-administration-assistant/evaluation/test_question.json). Les métriques utilisées sont :

- **Précision du Retrieval** : 100.0% (23/23) - Toutes les requêtes ont trouvé un document pertinent
- **Pertinence de la Réponse** : Variable selon la question (certaines réponses sont très précises, d'autres nécessitent des améliorations)
- **Temps de Réponse** : Moyenne de 11.87 secondes par requête

Vous pouvez exécuter le script d'évaluation avec :
```bash
python test_system.py
```

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus d'informations.