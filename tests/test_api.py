from fastapi.testclient import TestClient


def test_health_ok():
    # Import tardif pour éviter d'exécuter le startup avant les autres tests
    from src.api.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_generate_with_mocks(monkeypatch):
    # Importer le module pour patcher ses variables globales retriever/generator
    import src.api.main as api
    client = TestClient(api.app)

    class _FakeRetriever:
        def retrieve(self, question, top_k=5, espace_filter=None, theme_filter=None):
            return [
                {"titre": "Doc A", "description": "Texte A", "url": "http://a"},
                {"titre": "Doc B", "description": "Texte B", "url": "http://b"},
            ]

    class _FakeGenerator:
        def generate(self, question, context_docs):
            return "Réponse factice. Sources: http://a, http://b."

    # Patcher les singletons du module
    monkeypatch.setattr(api, "retriever", _FakeRetriever(), raising=True)
    monkeypatch.setattr(api, "generator", _FakeGenerator(), raising=True)

    payload = {"question": "Test?", "top_k": 2}
    r = client.post("/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and isinstance(data["answer"], str)
    assert "sources" in data and isinstance(data["sources"], list)
    assert len(data["sources"]) == 2

