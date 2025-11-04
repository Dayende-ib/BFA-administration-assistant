#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to automatically download the required LLM model.
"""

import os
import requests
from tqdm import tqdm

def download_model():
    """Download the Llama-3.2-3B-Instruct-Q4_0.gguf model."""
    MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_0.gguf"
    MODEL_PATH = "src/models/Llama-3.2-3B-Instruct-Q4_0.gguf"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Check if model already exists
    if os.path.exists(MODEL_PATH):
        print("Modèle déjà présent.")
        return
    
    print("Téléchargement du modèle Llama-3.2-3B-Instruct-Q4_0.gguf...")
    print("Cela peut prendre plusieurs minutes selon votre connexion.")
    
    try:
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        
        # Get total file size
        total_size = int(response.headers.get('content-length', 0))
        
        with open(MODEL_PATH, "wb") as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Téléchargement") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print("Téléchargement terminé avec succès!")
        
    except Exception as e:
        print(f"Erreur lors du téléchargement: {e}")
        # Remove partially downloaded file if it exists
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)

if __name__ == "__main__":
    download_model()