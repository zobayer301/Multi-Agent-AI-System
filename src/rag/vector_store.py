"""
Vector Store Management using ChromaDB.

Provides persistent and in-memory vector storage for research documents:
- Wraps ChromaDB collections.
- Stores text chunks, vector embeddings, and rich metadata.
- Executes cosine similarity nearest-neighbor queries.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb

logger = logging.getLogger("rag.vector_store")

DEFAULT_COLLECTION_NAME = "research_knowledge_base"


class VectorStore:
    """Manages collection lifecycle and vector operations with ChromaDB."""

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: Optional[str] = None,
        in_memory: bool = False,
    ):
        self.collection_name = collection_name
        self.in_memory = in_memory

        if in_memory:
            self.client = chromadb.Client()
        else:
            storage_path = persist_directory or os.path.join(os.getcwd(), "chroma_db")
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=storage_path)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add text chunks with precomputed vector embeddings to the vector store."""
        if not texts or not embeddings:
            return

        chunk_ids = ids or [f"chunk_{i}_{hash(text)}" for i, text in enumerate(texts)]
        chunk_metadatas = metadatas or [{} for _ in texts]

        # ChromaDB requires all metadata values to be primitives (str, int, float, bool)
        sanitized_metadatas = []
        for meta in chunk_metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            sanitized_metadatas.append(clean_meta)

        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=sanitized_metadatas,
            ids=chunk_ids,
        )

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Query vector collection using a query embedding vector.

        Returns:
            List of dictionaries containing matching chunk text, metadata, and distance.
        """
        count = self.collection.count()
        if count == 0:
            return []

        limit = min(n_results, count)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for i in range(len(documents)):
            output.append({
                "id": ids[i] if i < len(ids) else f"result_{i}",
                "content": documents[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "similarity_score": 1.0 - distances[i] if i < len(distances) else 1.0,
            })

        return output

    def count(self) -> int:
        """Return total number of vector chunks stored."""
        return self.collection.count()

    def reset(self) -> None:
        """Clear all records from the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
