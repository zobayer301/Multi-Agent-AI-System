"""
Embeddings Generation Engine for RAG.

Provides vector embeddings using:
1. Live OpenAI Embeddings API (`text-embedding-3-small`, 1536 dimensions).
2. Deterministic unit-normalized semantic pseudo-embeddings for offline testing and simulation.
"""

import os
import math
import hashlib
import logging
from typing import List

logger = logging.getLogger("rag.embeddings")

EMBEDDING_DIM = 1536
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _deterministic_offline_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generate a deterministic, unit-normalized vector for a text string.
    Ensures identical strings produce identical vectors, and similar strings share components.
    """
    cleaned = text.lower().strip()
    words = cleaned.split()
    vector = [0.0] * dim

    # Project words into vector coordinates using hash buckets
    for i, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        # Apply word position weight
        vector[idx] += 1.0 / (i + 1.0)
        # Bigram feature
        if i > 0:
            bi_word = f"{words[i-1]}_{word}"
            h_bi = int(hashlib.md5(bi_word.encode("utf-8")).hexdigest(), 16)
            vector[h_bi % dim] += 0.5

    # Compute Euclidean norm
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        # Uniform fallback for empty/neutral strings
        val = 1.0 / math.sqrt(dim)
        return [val] * dim

    return [x / norm for x in vector]


class EmbeddingEngine:
    """Handles text embedding generation across live API and offline modes."""

    def __init__(self, model: str = DEFAULT_EMBEDDING_MODEL):
        self.model = model
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.is_live = len(api_key) > 10 and not api_key.startswith("your_")
        self._client = None

        if self.is_live:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client ({e}); using offline embeddings.")
                self.is_live = False

    def embed_text(self, text: str) -> List[float]:
        """Generate a 1536-dimensional vector embedding for a single string."""
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * EMBEDDING_DIM

        if self.is_live and self._client:
            try:
                response = self._client.embeddings.create(
                    input=cleaned,
                    model=self.model,
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding call failed ({e}); falling back to offline generator.")

        return _deterministic_offline_embedding(cleaned, EMBEDDING_DIM)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of strings."""
        if not texts:
            return []

        if self.is_live and self._client:
            try:
                response = self._client.embeddings.create(
                    input=texts,
                    model=self.model,
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.warning(f"OpenAI batch embedding call failed ({e}); falling back to offline generator.")

        return [_deterministic_offline_embedding(t, EMBEDDING_DIM) for t in texts]
