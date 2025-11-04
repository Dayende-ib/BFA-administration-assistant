from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache

class Embedder:
    def __init__(self):
        # Use multilingual-e5-base for better French performance
        self.model = SentenceTransformer(
            "intfloat/multilingual-e5-base",
            device="cpu"
        )
        self._cache = {}
        self._batch_size = 32

    def embed(self, texts):
        # Simple in-memory cache per texte -> embedding
        missing = [t for t in texts if t not in self._cache]
        if missing:
            embeddings = self.model.encode(
                missing,
                batch_size=self._batch_size,
                normalize_embeddings=True
            ).tolist()
            for t, e in zip(missing, embeddings):
                self._cache[t] = e
        return [self._cache[t] for t in texts]