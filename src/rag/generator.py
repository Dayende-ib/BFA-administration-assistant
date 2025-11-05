from transformers import pipeline
from typing import List, Dict

class Generator:
    def __init__(self):
        self.pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-small",
            device=-1,
            max_length=256
        )

    def generate(self, question: str, context_docs: List[Dict]) -> str:
        if not context_docs:
            return "Aucune information trouvée."

        context = "\n".join([
            f"{d.get('titre', '')}: {d.get('description', '')[:400]}"
            for d in context_docs
        ])

        prompt = f"""Réponds en français, en 3 phrases max, en te basant sur ces documents.

Question: {question}
Documents: {context}

Réponse:"""

        result = self.pipe(prompt)[0]['generated_text']
        sources = "; ".join([f"[{d['titre']}]({d['url']})" for d in context_docs])
        return f"{result}\n\n**Sources:** {sources}"