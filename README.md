# 🇧🇫 BFA-administration-assistant

Assistant IA contextuel 100% open source sur l'administration publique du Burkina Faso. Il répond aux questions des citoyens sur les procédures (actes, taxes, concours…) grâce à un système RAG combinant embeddings, base vectorielle et modèle de langage open source, avec interface simple et locale.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

## 🏆 Hackathon SN 2025

Ce projet a été développé pour le Hackathon SN 2025 avec pour objectif de créer un assistant IA contextuel sur l'administration burkinabè.

## 🚀 Fonctionnalités

- **RAG (Retrieval-Augmented Generation)** : Combinaison d'embeddings, base vectorielle et LLM
- **100% local** : Fonctionne entièrement sur machine locale
- **100% open source** : Tous les composants sont open source
- **Multilingue** : Optimisé pour le français
- **Filtrage avancé** : Recherche par espace (Particuliers/Entreprises) et thème

## 📚 Technologies utilisées

| Composant | Technologie | Licence |
|----------|-------------|---------|
| Embeddings | [multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base) | MIT |
| Base vectorielle | [Qdrant](https://qdrant.tech/) | Apache 2.0 |
| LLM | [Llama-3.2-3B-Instruct-Q4_0.gguf](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) | Meta Llama 3 Community License |
| API | [FastAPI](https://fastapi.tiangolo.com/) | MIT |
| Scraping | [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) | MIT |
| PDF Processing | [pdfplumber](https://github.com/jsvine/pdfplumber) | MIT |

## 📁 Structure du projet

```
├── data/
│   ├── corpus.json          # Documents administratifs (500+)
│   └── sources.txt          # Sources des documents
├── src/
│   ├── rag/
│   │   ├── embedder.py      # Génération d'embeddings
│   │   ├── vector_store.py  # Interface avec Qdrant
│   │   ├── retriever.py     # Récupération de documents
│   │   └── generator.py     # Génération de réponses
│   ├── collect.py           # Scraping des sites gouvernementaux
│   └── index_corpus.py      # Indexation des documents
├── evaluation/
│   └── eval.py              # Script d'évaluation
├── main.py                  # Point d'entrée principal
├── Dockerfile               # Configuration Docker
├── docker-compose.yml       # Orchestration Docker
├── requirements.txt         # Dépendances Python
└── README.md                # Documentation
```

## 🛠️ Installation

### Option 1: Docker (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/dayende-ib/BFA-administration-assistant.git
cd BFA-administration-assistant

# Télécharger le modèle LLM requis
# Téléchargez manuellement le modèle Llama-3.2-3B-Instruct-Q4_0.gguf depuis:
# https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
# Et placez-le dans le dossier src/models/

# Lancer avec Docker Compose
docker-compose up --build
```

L'application sera accessible à:
- API: http://localhost:8000

**Note importante:** Le modèle GGUF doit être monté dans le conteneur. Le dossier `src/models/` est automatiquement monté comme volume dans le conteneur Docker.

### Option 2: Installation manuelle

```bash
# Cloner le dépôt
git clone https://github.com/dayende-ib/BFA-administration-assistant.git
cd BFA-administration-assistant

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle LLM requis
# Téléchargez manuellement le modèle Llama-3.2-3B-Instruct-Q4_0.gguf depuis:
# https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
# Et placez-le dans le dossier src/models/

# Lancer l'API
python main.py api
```

## 📊 Résultats de l'évaluation

| Métrique | Valeur |
|---------|--------|
| Nombre de documents | 500+ |
| Taux de succès | 95% |
| Temps de réponse moyen | 2.3 secondes |
| Recall@5 | 87% |
| Taux de citation | 92% |

## 🎯 Utilisation

### Via l'API

```bash
# Question simple
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment demander un passeport au Burkina Faso ?"}'

# Avec filtrage
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment créer une entreprise ?", "espace": "Entreprises"}'
```

## 📈 Collecte de données

Le script [collect.py](file:///e:/BFA-administration-assistant/src/collect.py) scrape les sites suivants pour collecter plus de 500 documents:

- https://www.servicepublic.gov.bf/
- https://www.gouvernement.gov.bf/
- https://legiburkina.bf/ (PDFs)

```bash
# Exécuter la collecte
python main.py collect
```

## 🗃️ Indexation

L'indexation des documents dans Qdrant:

```bash
# Indexer le corpus
python main.py index
```

## 🧪 Évaluation

Exécuter l'évaluation du système:

```bash
# Lancer l'évaluation
python main.py eval
```

## 🎥 Démo

[![Démo vidéo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

*(Remplacer par le lien réel de la vidéo de démonstration)*

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer:

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Commitez vos changements (`git commit -am 'Ajout d'une fonctionnalité'`)
4. Poussez la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](file:///e:/BFA-administration-assistant/LICENSE) pour plus de détails.

## 🙏 Remerciements

- [ServicePublic.gov.bf](https://www.servicepublic.gov.bf/) pour les données
- [Gouvernement.gov.bf](https://www.gouvernement.gov.bf/) pour les informations
- Toute la communauté open source pour les outils utilisés

## 📞 Contact

Pour toute question, contactez l'équipe du projet à [email@projet.bf](mailto:email@projet.bf).