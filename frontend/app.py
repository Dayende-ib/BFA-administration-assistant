#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio frontend for the BFA Administration Assistant.
Provides a simple web interface for asking questions and getting answers with sources.
"""

import gradio as gr
import requests
import os
from urllib.parse import urljoin

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def ask_question(question, top_k=5):
    """
    Ask a question to the BFA Administration Assistant API.
    
    Args:
        question (str): The question to ask
        top_k (int): Number of context documents to retrieve
        
    Returns:
        tuple: (answer, sources)
    """
    try:
        # Call the API
        response = requests.post(
            urljoin(API_BASE_URL, "/generate"),
            json={"question": question, "top_k": top_k},
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        answer = data.get("answer", "Désolé, je n'ai pas pu générer de réponse.")
        sources = data.get("sources", [])
        
        # Format sources for display
        sources_text = "\n\n".join([
            f"**{source.get('titre', 'Document sans titre')}**\n"
            f"Description: {source.get('description', 'Aucune description')[:200]}...\n"
            f"Source: {source.get('url', 'URL non spécifiée')}"
            for source in sources
        ]) if sources else "Aucune source trouvée."
        
        return answer, sources_text
    except Exception as e:
        error_msg = f"Erreur lors de la requête à l'API: {str(e)}"
        return error_msg, "Impossible de récupérer les sources."

# Create the Gradio interface
with gr.Blocks(title="Assistant Administratif Burkina Faso") as demo:
    gr.Markdown("""
    # 🇧🇫 Assistant Administratif Burkina Faso
    
    Posez vos questions sur les procédures administratives du Burkina Faso.
    """)
    
    with gr.Row():
        with gr.Column():
            question = gr.Textbox(
                label="Question",
                placeholder="Ex: Comment demander un passeport au Burkina Faso ?",
                lines=3
            )
            top_k = gr.Slider(
                minimum=1,
                maximum=10,
                value=5,
                step=1,
                label="Nombre de documents de contexte"
            )
            submit_btn = gr.Button("Poser la question", variant="primary")
        
        with gr.Column():
            answer = gr.Textbox(label="Réponse", interactive=False, lines=10)
            sources = gr.Textbox(label="Sources", interactive=False, lines=10)
    
    # Examples
    gr.Examples(
        examples=[
            "Comment demander un acte de naissance ?",
            "Quels sont les documents nécessaires pour un visa ?",
            "Comment s'inscrire aux concours de la fonction publique ?",
            "Quels sont les frais pour un casier judiciaire ?",
            "Comment obtenir une carte d'identité biométrique ?"
        ],
        inputs=[question]
    )
    
    # Event handling
    submit_btn.click(
        fn=ask_question,
        inputs=[question, top_k],
        outputs=[answer, sources]
    )
    
    # Allow Enter key to submit
    question.submit(
        fn=ask_question,
        inputs=[question, top_k],
        outputs=[answer, sources]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)