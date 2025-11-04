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

def run_frontend():
    """Run the Gradio frontend."""
    try:
        # Save current directory and change to frontend directory
        original_cwd = os.getcwd()
        frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
        if os.path.exists(frontend_path):
            os.chdir(frontend_path)
        
        # Dynamically import the frontend app using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        if spec is None:
            raise ImportError("Could not create module spec for frontend app")
        
        app_module = importlib.util.module_from_spec(spec)
        
        # Check that the spec has a loader before calling exec_module
        if spec.loader is None:
            raise ImportError("Module spec has no loader")
            
        spec.loader.exec_module(app_module)
        
        print("Démarrage de l'interface frontend...")
        app_module.demo.launch(server_name="0.0.0.0", server_port=7860)
        
        # Restore original working directory
        os.chdir(original_cwd)
    except ImportError as e:
        print(f"Erreur: Impossible d'importer les modules nécessaires: {e}")
        print("Assurez-vous d'avoir installé toutes les dépendances avec:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors du démarrage du frontend: {e}")
        sys.exit(1)

def run_collect():
    """Run the data collection script."""
    try:
        from src.collect import main as collect_main
        print("Exécution du script de collecte de données...")
        collect_main()
    except ImportError as e:
        print(f"Erreur: Impossible d'importer les modules nécessaires: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de la collecte de données: {e}")
        sys.exit(1)

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

def run_evaluation():
    """Run the evaluation script."""
    try:
        from evaluation.eval import run_evaluation
        print("Exécution de l'évaluation...")
        run_evaluation()
    except ImportError as e:
        print(f"Erreur: Impossible d'importer les modules nécessaires: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de l'évaluation: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and run the appropriate component."""
    parser = argparse.ArgumentParser(description="BFA Administration Assistant")
    parser.add_argument(
        "command",
        choices=["api", "frontend", "collect", "index", "eval"],
        help="Commande à exécuter"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        run_api()
    elif args.command == "frontend":
        run_frontend()
    elif args.command == "collect":
        run_collect()
    elif args.command == "index":
        run_index()
    elif args.command == "eval":
        run_evaluation()
    else:
        print(f"Commande inconnue: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()