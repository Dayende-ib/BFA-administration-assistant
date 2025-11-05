from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Any, Tuple

class Generator:
    """Classe pour générer des réponses à partir d'une question et de documents contextuels."""
    
    def __init__(self):
        # Nom du modèle de génération de texte
        MODEL_NAME = "google/flan-t5-base"
        print(f"Chargement du générateur ({MODEL_NAME}) sur CPU...")
        
        # Initialisation du pipeline de génération de texte
        self.pipe = pipeline("text2text-generation", model=MODEL_NAME, device=-1, max_length=256)
        # Initialisation du tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        # Longueur maximale du modèle
        self.model_max_length = 512
        print(f"Générateur ({MODEL_NAME}) chargé.")

    def generate(self, question: str, context_docs: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any] | None]:
        """
        Génère une réponse à partir d'une question et de documents contextuels.
        
        Args:
            question: La question de l'utilisateur
            context_docs: Liste des documents contextuels pertinents
            
        Returns:
            Tuple contenant la réponse générée et le document source
        """
        # Vérifie s'il y a des documents contextuels
        if not context_docs:
            return ("Aucune information pertinente n'a été trouvée.", None)

        # Utilise le premier document comme contexte principal
        doc = context_docs[0]
        
        # Construit le contexte pour le prompt
        context_str = (
            f"Titre: {doc.get('titre', 'N/A')}\n"
            f"Description: {doc.get('description', 'N/A')}\n"
            f"Pièces: {doc.get('pieces', 'N/A')}\n"
            f"Coût: {doc.get('cout', 'N/A')}\n"
            f"Conditions: {doc.get('conditions', 'N/A')}\n"
            f"Infos: {doc.get('infos', 'N/A')}\n"
        )
        
        # Template du prompt avec le contexte et la question
        prompt_template = f"""Contexte:
[CONTEXTE_PLACEHOLDER]

Question:
{question}

En te basant uniquement sur le contexte ci-dessus, réponds à la question:
"""

        # Calcule la longueur maximale du contexte
        prompt_instructions = prompt_template.replace("[CONTEXTE_PLACEHOLDER]", "")
        instruction_tokens = self.tokenizer(prompt_instructions, return_tensors="pt").input_ids.size(1)
        safety_margin = 20 
        max_context_tokens = self.model_max_length - instruction_tokens - safety_margin
        
        # Vérifie si la question est trop longue
        if max_context_tokens <= 0:
             return ("Erreur : La question est trop longue pour le modèle.", None)

        # Vérifie si le contexte doit être tronqué
        context_tokens = self.tokenizer(context_str, return_tensors="pt", truncation=False).input_ids
        if context_tokens.size(1) > max_context_tokens:
            print(f"AVERTISSEMENT: Contexte tronqué. {context_tokens.size(1)} > {max_context_tokens}")
            truncated_context_tokens = context_tokens[:, :max_context_tokens]
            context_str = self.tokenizer.decode(truncated_context_tokens[0], skip_special_tokens=True)

        # Remplace le placeholder par le contexte réel
        final_prompt = prompt_template.replace("[CONTEXTE_PLACEHOLDER]", context_str)

        # Génère la réponse
        try:
            result_text = self.pipe(final_prompt, max_new_tokens=256)[0]['generated_text']
        except Exception as e:
            print(f"Erreur lors de la génération : {e}")
            return ("Désolé, une erreur est survenue lors de la génération.", None)
        
        # Renvoie la réponse et le document source
        return (result_text, doc)