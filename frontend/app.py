# frontend/app.py
import gradio as gr
import requests
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# API locale (FastAPI désactivé, on simule avec retriever)
from src.rag.retriever import Retriever
from src.rag.generator import Generator

retriever = Retriever()
generator = Generator()

def ask(question, espace=None, theme=None):
    try:
        docs = retriever.retrieve(question, top_k=5, espace_filter=espace, theme_filter=theme)
        answer = generator.generate(question, docs)
        sources = "\n".join([f"- [{d['titre']}]({d['url']})" for d in docs])
        return f"{answer}\n\n**Sources:**\n{sources}"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Interface
iface = gr.Interface(
    fn=ask,
    inputs=[
        gr.Textbox(label="Pose ta question", placeholder="Ex: Comment obtenir un acte de naissance ?"),
        gr.Dropdown(["Particuliers", "Entreprises"], label="Espace", value=None),
        gr.Textbox(label="Thème (optionnel)", placeholder="Ex: État civil")
    ],
    outputs=gr.Markdown(),
    title="Assistant IA Administration Burkina Faso",
    description="100% open source | RAG avec Qdrant + flan-t5-small",
    examples=[
        ["Comment obtenir un acte de naissance ?", "Particuliers", "État civil"],
        ["Comment créer une entreprise ?", "Entreprises", "Entrepreneuriat"]
    ]
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)