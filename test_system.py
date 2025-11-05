import json
import time
from api import retriever, generator

def evaluate_system():
    """Teste le système avec les questions d'évaluation"""
    
    # Charger les questions de test
    with open("evaluation/test_question.json", "r", encoding="utf-8") as f:
        test_questions = json.load(f)
    
    print(f"Nombre de questions de test : {len(test_questions)}")
    
    # Métriques
    total_questions = len(test_questions)
    retrieval_success = 0
    total_time = 0
    
    print("\n=== RÉSULTATS D'ÉVALUATION ===\n")
    
    for i, item in enumerate(test_questions):
        question = item["question"]
        expected_answer = item["reponse_attendue"]
        
        print(f"{i+1}. Question : {question}")
        
        # Mesurer le temps de réponse
        start_time = time.time()
        
        # Récupérer les documents pertinents
        docs = retriever.retrieve(question, top_k=1)
        
        # Générer la réponse
        (answer_text, source_doc) = generator.generate(question, docs)
        
        end_time = time.time()
        response_time = end_time - start_time
        total_time += response_time
        
        # Vérifier si un document a été trouvé
        if docs:
            retrieval_success += 1
            doc_title = docs[0].get("titre", "Titre inconnu")
            print(f"   Document trouvé : {doc_title}")
        else:
            print("   Aucun document pertinent trouvé")
        
        print(f"   Réponse générée : {answer_text}")
        print(f"   Temps de réponse : {response_time:.2f} secondes")
        print("-" * 50)
    
    # Calculer les métriques finales
    retrieval_precision = (retrieval_success / total_questions) * 100
    avg_response_time = total_time / total_questions
    
    print("\n=== MÉTRIQUES FINALES ===")
    print(f"Précision du Retrieval : {retrieval_precision:.1f}% ({retrieval_success}/{total_questions})")
    print(f"Temps de réponse moyen : {avg_response_time:.2f} secondes")

if __name__ == "__main__":
    evaluate_system()