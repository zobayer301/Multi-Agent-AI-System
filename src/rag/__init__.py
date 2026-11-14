"""
RAG package exposing embeddings, vector storage, and semantic retrieval components.
"""

from .embeddings import EmbeddingEngine, EMBEDDING_DIM
from .vector_store import VectorStore
from .retriever import (
    KnowledgeRetriever,
    chunk_text,
    get_default_retriever,
    retrieve_knowledge,
    retrieve_knowledge_fn,
)

__all__ = [
    "EmbeddingEngine",
    "EMBEDDING_DIM",
    "VectorStore",
    "KnowledgeRetriever",
    "chunk_text",
    "get_default_retriever",
    "retrieve_knowledge",
    "retrieve_knowledge_fn",
]
