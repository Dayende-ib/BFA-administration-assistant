from sentence_transformers import SentenceTransformer
import torch

class Embedder:
    def __init__(self):
        # Use multilingual-e5-base for better French performance
        self.model = SentenceTransformer(
            "intfloat/multilingual-e5-base",
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def embed(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()