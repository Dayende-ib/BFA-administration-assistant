from transformers import pipeline, AutoTokenizer
from typing import List, Dict, Any, Tuple

class Generator:
    def __init__(self):
        MODEL_NAME = "google/flan-t5-base"
        print(f"Chargement du générateur ({MODEL_NAME}) sur CPU...")
        
        self.pipe = pipeline("text2text-generation", model=MODEL_NAME, device=-1, max_length=256)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model_max_length = 512 # Limite de flan-t5
        print(f"Générateur ({MODEL_NAME}) chargé.")

    # MODIFICATION : La fonction renvoie maintenant un Tuple (réponse_brute, document_source)
    def generate(self, question: str, context_docs: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any] | None]:
        
        if not context_docs:
            return ("Aucune information pertinente n'a été trouvée.", None)

        doc = context_docs[0]
        
        # Contexte pour le prompt (sans l'URL)
        context_str = (
            f"Titre: {doc.get('titre', 'N/A')}\n"
            f"Description: {doc.get('description', 'N/A')}\n"
            f"Pièces: {doc.get('pieces', 'N/A')}\n"
            f"Coût: {doc.get('cout', 'N/A')}\n"
            f"Conditions: {doc.get('conditions', 'N/A')}\n"
            f"Infos: {doc.get('infos', 'N/A')}\n"
        )
        
        prompt_template = f"""Contexte:
[CONTEXTE_PLACEHOLDER]

Question:
{question}

En te basant uniquement sur le contexte ci-dessus, réponds à la question:
"""

        # --- Logique de troncature (inchangée) ---
        prompt_instructions = prompt_template.replace("[CONTEXTE_PLACEHOLDER]", "")
        instruction_tokens = self.tokenizer(prompt_instructions, return_tensors="pt").input_ids.size(1)
        safety_margin = 20 
        max_context_tokens = self.model_max_length - instruction_tokens - safety_margin
        
        if max_context_tokens <= 0:
             return ("Erreur : La question est trop longue pour le modèle.", None)

        context_tokens = self.tokenizer(context_str, return_tensors="pt", truncation=False).input_ids

        if context_tokens.size(1) > max_context_tokens:
            print(f"AVERTISSEMENT: Contexte tronqué. {context_tokens.size(1)} > {max_context_tokens}")
            truncated_context_tokens = context_tokens[:, :max_context_tokens]
            context_str = self.tokenizer.decode(truncated_context_tokens[0], skip_special_tokens=True)

        final_prompt = prompt_template.replace("[CONTEXTE_PLACEHOLDER]", context_str)
        # --- Fin de la troncature ---

        try:
            result_text = self.pipe(final_prompt, max_new_tokens=256)[0]['generated_text']
        except Exception as e:
            print(f"Erreur lors de la génération : {e}")
            return ("Désolé, une erreur est survenue lors de la génération.", None)
        
        # MODIFICATION : Renvoie le texte ET le document source
        return (result_text, doc)