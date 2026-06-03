"""
Vector Memory — Chapter 5: Memory Systems and Context Management

Long-term semantic memory using cosine similarity over embedding vectors.
Production: replace the in-process store with Pinecone, Weaviate, or pgvector.

Contract:
  store(key, text) → None
  retrieve(query, top_k) → list[str]
  forget(key) → None
"""
import math
import os
import time
from dataclasses import dataclass, field

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
EMBED_MODEL = "voyage-3"   # or any embeddings provider


def _embed(text: str) -> list[float]:
    """Get embedding vector for text."""
    # Stub — replace with real embeddings (Voyage AI, OpenAI, Cohere, etc.)
    # For demo purposes, return a fixed-length zero vector
    return [0.0] * 256


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class VectorMemory:
    similarity_threshold: float = 0.75
    _store: dict = field(default_factory=dict, repr=False)

    def store(self, key: str, text: str) -> None:
        """Embed and store a text entry."""
        self._store[key] = {
            "text": text,
            "vector": _embed(text),
            "stored_at": time.time(),
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Return top-k most similar entries above the similarity threshold."""
        if not self._store:
            return []
        query_vec = _embed(query)
        scored = [
            (key, _cosine(query_vec, entry["vector"]), entry["text"])
            for key, entry in self._store.items()
        ]
        filtered = [(k, s, t) for k, s, t in scored if s >= self.similarity_threshold]
        filtered.sort(key=lambda x: x[1], reverse=True)
        return [text for _, _, text in filtered[:top_k]]

    def forget(self, key: str) -> None:
        self._store.pop(key, None)

    def size(self) -> int:
        return len(self._store)
