#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for the BFA Administration Assistant.
Calculates metrics like Recall@5, response time, and citation rate.
"""

import json
import time
import requests
from urllib.parse import urljoin
import os
from statistics import mean

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
EVAL_QUESTIONS_FILE = "evaluation/test_questions.json"
EVAL_RESULTS_FILE = "evaluation/eval_results.json"

def load_test_questions():
    """Load test questions from JSON file."""
    try:
        with open(EVAL_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create a sample file if it doesn't exist
        sample_questions = [
            {
                "question": "Comment demander un passeport au Burkina Faso ?",
                "expected_keywords": ["passeport", "demande", "pièces", "delai"]
            },
            {
                "question": "Quels sont les documents nécessaires pour un visa ?",
                "expected_keywords": ["visa", "documents", "formulaire", "timbre"]
            },
            {
                "question": "Comment s'inscrire aux concours de la fonction publique ?",
                "expected_keywords": ["concours", "fonction publique", "inscription", "econcours"]
            },
            {
                "question": "Quels sont les frais pour un casier judiciaire ?",
                "expected_keywords": ["casier judiciaire", "frais", "bulletin", "300 FCFA"]
            },
            {
                "question": "Comment obtenir une carte d'identité biométrique ?",
                "expected_keywords": ["carte d'identité", "biométrique", "CNI", "pièces"]
            }
        ]
        with open(EVAL_QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_questions, f, ensure_ascii=False, indent=2)
        return sample_questions

def ask_question(question):
    """Ask a question to the API and measure response time."""
    start_time = time.time()
    try:
        response = requests.post(
            urljoin(API_BASE_URL, "/generate"),
            json={"question": question, "top_k": 5},
            timeout=60
        )
        response.raise_for_status()
        end_time = time.time()
        
        data = response.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources,
            "response_time": end_time - start_time
        }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "error": str(e),
            "response_time": end_time - start_time
        }

def calculate_recall_at_k(answer, expected_keywords, k=5):
    """Calculate Recall@k based on expected keywords in the answer."""
    if not answer or not expected_keywords:
        return 0.0
    
    answer_lower = answer.lower()
    matched_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return matched_keywords / len(expected_keywords)

def calculate_citation_rate(sources):
    """Calculate citation rate (proportion of responses with sources)."""
    return 1.0 if sources else 0.0

def run_evaluation():
    """Run the full evaluation."""
    print("Chargement des questions de test...")
    test_questions = load_test_questions()
    print(f"Nombre de questions: {len(test_questions)}")
    
    results = []
    response_times = []
    recalls = []
    citation_rates = []
    
    print("\nExécution de l'évaluation...")
    for i, item in enumerate(test_questions):
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        
        print(f"Question {i+1}/{len(test_questions)}: {question}")
        
        result = ask_question(question)
        result["question"] = question
        result["expected_keywords"] = expected_keywords
        
        if result["success"]:
            # Calculate metrics
            recall = calculate_recall_at_k(result["answer"], expected_keywords)
            citation_rate = calculate_citation_rate(result["sources"])
            
            result["recall"] = recall
            result["citation_rate"] = citation_rate
            
            recalls.append(recall)
            citation_rates.append(citation_rate)
        
        response_times.append(result["response_time"])
        results.append(result)
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Calculate overall metrics
    successful_requests = [r for r in results if r["success"]]
    success_rate = len(successful_requests) / len(results)
    
    avg_response_time = mean(response_times) if response_times else 0
    avg_recall = mean(recalls) if recalls else 0
    avg_citation_rate = mean(citation_rates) if citation_rates else 0
    
    evaluation_summary = {
        "total_questions": len(test_questions),
        "successful_requests": len(successful_requests),
        "success_rate": success_rate,
        "average_response_time": avg_response_time,
        "average_recall_at_5": avg_recall,
        "average_citation_rate": avg_citation_rate,
        "detailed_results": results
    }
    
    # Save results
    with open(EVAL_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(evaluation_summary, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("RÉSULTATS DE L'ÉVALUATION")
    print("="*50)
    print(f"Nombre total de questions: {evaluation_summary['total_questions']}")
    print(f"Taux de succès: {evaluation_summary['success_rate']:.2%}")
    print(f"Temps de réponse moyen: {evaluation_summary['average_response_time']:.2f} secondes")
    print(f"Recall@5 moyen: {evaluation_summary['average_recall_at_5']:.2%}")
    print(f"Taux de citation moyen: {evaluation_summary['average_citation_rate']:.2%}")
    print("="*50)
    
    return evaluation_summary

if __name__ == "__main__":
    run_evaluation()