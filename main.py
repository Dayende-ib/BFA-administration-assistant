#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the BFA Administration Assistant.
This script can run the API server, the frontend, or perform other operations.
"""

import argparse
import sys
import os

def run_api():
    """Run the FastAPI server."""
    try:
        import uvicorn
        from src.api.main import app
        print("Démarrage du serveur API...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        print(f"Erreur: Impossible d'importer les modules nécessaires: {e}")
        print("Assurez-vous d'avoir installé toutes les dépendances avec:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur: {e}")
        sys.exit(1)

## Frontend/collect supprimés (hors périmètre RAG)

def run_index():
    """Run the indexing script."""
    try:
        from src.index_corpus import index_corpus
        print("Exécution du script d'indexation...")
        index_corpus()
    except ImportError as e:
        print(f"Erreur: Impossible d'importer les modules nécessaires: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de l'indexation: {e}")
        sys.exit(1)

## Evaluation supprimée (hors périmètre RAG)

def main():
    """Main function to parse arguments and run the appropriate component."""
    parser = argparse.ArgumentParser(description="BFA Administration Assistant")
    parser.add_argument(
        "command",
        choices=["api", "index"],
        help="Commande à exécuter"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        run_api()
    elif args.command == "index":
        run_index()
    else:
        print(f"Commande inconnue: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()