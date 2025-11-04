import os
from gpt4all import GPT4All

class Generator:
    def __init__(self, model_path="src/models/Llama-3.2-3B-Instruct-Q4_0.gguf"):
        # Convert to absolute path to ensure GPT4All can find the file
        if not os.path.isabs(model_path):
            model_path = os.path.join(os.getcwd(), model_path)
        
        # Store the model path
        self.model_path = model_path
        
        # Check if model file exists before trying to load it
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please mount a GGUF model file in /app/src/models.")
        
        # Load the model only if it exists, and prevent automatic download
        self.model = GPT4All(model_path, device='cpu', allow_download=False, verbose=False)

    def _has_cuda(self):
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _format_answer(self, text: str) -> str:
        """Normalize whitespace and ensure sentence-ending punctuation."""
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return cleaned
        if cleaned[-1] not in ".!?":
            cleaned += "."
        return cleaned

    def generate(self, question, context_docs):
        # Check if model was properly loaded
        if not hasattr(self, 'model') or self.model is None:
            return "Modèle indisponible. Montez un modèle GGUF dans /app/src/models."
            
        def _truncate(text: str, max_len: int = 1024) -> str:
            t = (text or "").strip()
            return t[:max_len]

        context = "\n\n".join([
            f"Titre: {d.get('titre','')}\nDescription: {_truncate(d.get('description',''))}\nSource: {d.get('url','')}"
            for d in context_docs
        ])

        # Prompt orienté phrases cohérentes, structurées et concises
        prompt = f"""Vous êtes un assistant administratif burkinabè.
Répondez uniquement en français avec des phrases complètes et cohérentes, en courts paragraphes.

Question:
{question}

Contexte (sources à citer):
{context}

Consignes:
1) Écrivez une réponse fluide en 2 à 6 phrases (paragraphes courts).
2) Utilisez un ton clair et professionnel, sans listes sauf si demandé.
3) À la fin, ajoutez une ligne "Sources:" suivie des liens/titres pertinents.
4) Si le contexte est insuffisant, dites-le explicitement.

Réponse:"""

        response = self.model.generate(
            prompt,
            max_tokens=512,
            temp=0.2,
            top_p=0.95,
            repeat_penalty=1.1
        )
        return self._format_answer(response)