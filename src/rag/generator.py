from gpt4all import GPT4All

class Generator:
    def __init__(self, model_path="src/models/Llama-3.2-3B-Instruct-Q4_0.gguf"):
        self.model = GPT4All(model_path, device='cpu')

    def _has_cuda(self):
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def generate(self, question, context_docs):
        context = "\n\n".join([
            f"Titre: {d['titre']}\nDescription: {d['description']}\nSource: {d['url']}"
            for d in context_docs
        ])

        # Enhanced prompt with citation requirement and concise response
        prompt = f"""Vous êtes un assistant administratif burkinabè. Répondez en français de manière claire et concise.
        
Question: {question}

Contexte:
{context}

Instructions:
1. Répondez uniquement en français
2. Citez obligatoirement les sources en les mentionnant à la fin de votre réponse
3. Soyez concis et direct dans votre réponse
4. Si le contexte ne contient pas d'informations pertinentes, indiquez-le clairement

Réponse:"""

        response = self.model.generate(
            prompt,
            max_tokens=512,
            temp=0.3,
            top_p=0.9,
            repeat_penalty=1.1
        )
        return response.strip()