import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str, model: str = "gemma3:4b") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # ← CRUCIAL : désactive le stream
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        # Vérifie la structure
        if "response" in data:
            return data["response"]
        else:
            print("Réponse brute :", data)
            return "[ERREUR: réponse incomplète]"
            
    except Exception as e:
        return f"[ERREUR: {e}]"

# Test
if __name__ == "__main__":
    test_prompt = "Bonjour, qui es-tu ?"
    print("Réponse :", query_ollama(test_prompt))