import os
from gpt4all import GPT4All
from typing import List, Dict, Any

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

    def generate(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate a response to a question using the provided context documents.
        
        This method uses a Retrieval-Augmented Generation (RAG) approach where:
        1. Context documents are formatted and provided to the LLM
        2. A structured prompt guides the LLM to produce a coherent, cited response
        3. The LLM generates a response based on both its knowledge and the provided context
        
        Args:
            question (str): The user's question to answer
            context_docs (List[Dict[str, Any]]): List of relevant documents containing:
                - 'titre': Document title
                - 'description': Document content/description
                - 'url': Source URL for citation
                - Other metadata fields as available
                
        Returns:
            str: A formatted answer with citations to the source documents
            
        Example:
            >>> generator = Generator()
            >>> context = [{'titre': 'Passeport', 'description': 'Document de voyage', 'url': 'https://example.com'}]
            >>> response = generator.generate("Comment obtenir un passeport?", context)
        """
        # Check if model was properly loaded
        if not hasattr(self, 'model') or self.model is None:
            return "Modèle indisponible. Montez un modèle GGUF dans /app/src/models."
            
        def _truncate(text: str, max_len: int = 1024) -> str:
            """Truncate text to maximum length while preserving word boundaries."""
            t = (text or "").strip()
            if len(t) <= max_len:
                return t
            # Try to truncate at last space within limit
            truncated = t[:max_len]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space] + "..."
            return truncated[:max_len] + "..."

        # Enhanced context formatting with better structure and metadata
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            title = doc.get('titre', 'Document sans titre')
            description = _truncate(doc.get('description', ''))
            url = doc.get('url', 'Source inconnue')
            source = doc.get('source', '')
            theme = doc.get('Thème', '')
            espace = doc.get('Espace', '')
            
            # Build context entry with all available metadata
            context_entry = f"Document {i}:\n"
            context_entry += f"  Titre: {title}\n"
            if description:
                context_entry += f"  Description: {description}\n"
            context_entry += f"  Source: {url}\n"
            if source:
                context_entry += f"  Publication: {source}\n"
            if theme:
                context_entry += f"  Thème: {theme}\n"
            if espace:
                context_entry += f"  Espace: {espace}\n"
                
            context_parts.append(context_entry)

        # Join all context parts
        context = "\n".join(context_parts)

        # Enhanced prompt with clearer structure and instructions
        prompt = f"""Vous êtes un assistant administratif burkinabè expert en droit et procédures administratives du Burkina Faso.
Votre rôle est de répondre aux questions des citoyens en vous basant sur les documents fournis.

Question du citoyen:
{question}

Documents de référence (à utiliser pour votre réponse):
{context}

Consignes pour votre réponse:
1. Répondez uniquement en français avec des phrases complètes et cohérentes
2. Basez votre réponse sur les informations des documents fournis
3. Si les documents ne contiennent pas suffisamment d'informations, dites-le clairement
4. Structurez votre réponse en 3 à 10 phrases (paragraphes courts)
5. Utilisez un ton clair, professionnel et pédagogique
6. À la fin, citez les sources pertinentes sous la forme "Sources: [Titre](URL)"

Réponse:"""

        # Generate response with tuned parameters for better quality
        response = self.model.generate(
            prompt,
            max_tokens=512,
            temp=0.2,          # Low temperature for more deterministic responses
            top_p=0.95,        # Nucleus sampling
            repeat_penalty=1.1 # Slight penalty for repetition
        )
        return self._format_answer(response)