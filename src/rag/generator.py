import os
from gpt4all import GPT4All
from typing import List, Dict, Any

class Generator:
    def __init__(self, model_path="src/models/Llama-3.2-3B-Instruct-Q4_0.gguf"):
        # Convertir en chemin absolu pour garantir que GPT4All peut trouver le fichier
        if not os.path.isabs(model_path):
            model_path = os.path.join(os.getcwd(), model_path)
        
        # Stocker le chemin du modèle
        self.model_path = model_path
        
        # Vérifier si le fichier modèle existe avant d'essayer de le charger
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please mount a GGUF model file in /app/src/models.")
        
        # Charger le modèle uniquement s'il existe, et empêcher le téléchargement automatique
        self.model = GPT4All(model_path, device='cpu', allow_download=False, verbose=False)

    def _has_cuda(self):
        """Vérifier si CUDA est disponible."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _format_answer(self, text: str) -> str:
        """Normaliser les espaces et garantir la ponctuation de fin de phrase."""
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return cleaned
        if cleaned[-1] not in ".!?":
            cleaned += "."
        return cleaned

    def generate(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Générer une réponse à une question en utilisant les documents contextuels fournis.
        
        Cette méthode utilise une approche de génération augmentée par récupération (RAG) où :
        1. Les documents contextuels sont formatés et fournis au LLM
        2. Un prompt structuré guide le LLM pour produire une réponse cohérente et citée
        3. Le LLM génère une réponse basée sur ses connaissances et le contexte fourni
        
        Args:
            question (str): La question de l'utilisateur à répondre
            context_docs (List[Dict[str, Any]]): Liste des documents pertinents contenant :
                - 'titre': Titre du document
                - 'description': Contenu/description du document
                - 'url': URL source pour citation
                - Autres champs de métadonnées disponibles
                
        Returns:
            str: Une réponse formatée avec des citations aux documents sources
            
        Exemple:
            >>> generator = Generator()
            >>> context = [{'titre': 'Passeport', 'description': 'Document de voyage', 'url': 'https://example.com'}]
            >>> response = generator.generate("Comment obtenir un passeport?", context)
        """
        # Vérifier si le modèle a été correctement chargé
        if not hasattr(self, 'model') or self.model is None:
            return "Modèle indisponible. Montez un modèle GGUF dans /app/src/models."
            
        def _truncate(text: str, max_len: int = 1024) -> str:
            """Tronquer le texte à la longueur maximale tout en préservant les limites des mots."""
            t = (text or "").strip()
            if len(t) <= max_len:
                return t
            # Essayer de tronquer au dernier espace dans la limite
            truncated = t[:max_len]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space] + "..."
            return truncated[:max_len] + "..."

        # Formatage amélioré du contexte avec une meilleure structure et métadonnées
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            title = doc.get('titre', 'Document sans titre')
            description = _truncate(doc.get('description', ''))
            url = doc.get('url', 'Source inconnue')
            source = doc.get('source', '')
            theme = doc.get('Thème', '')
            espace = doc.get('Espace', '')
            
            # Construire l'entrée de contexte avec toutes les métadonnées disponibles
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

        # Joindre toutes les parties du contexte
        context = "\n".join(context_parts)

        # Prompt amélioré avec une structure et des instructions plus claires
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

        # Générer la réponse avec des paramètres ajustés pour une meilleure qualité
        response = self.model.generate(
            prompt,
            max_tokens=512,
            temp=0.2,          # Température basse pour des réponses plus déterministes
            top_p=0.95,        # Échantillonnage du noyau
            repeat_penalty=1.1 # Légère pénalité pour la répétition
        )
        return self._format_answer(response)