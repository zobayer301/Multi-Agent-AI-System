"""
RAG Ingestion and Semantic Retrieval Engine.

Features:
- Sentence & paragraph-aware text chunking with sliding overlap.
- Document ingestion pipeline (raw text and local files).
- Semantic similarity retrieval against ChromaDB.
- `retrieve_knowledge` FunctionTool for OpenAI Agents SDK integration.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from agents import function_tool

from src.rag.embeddings import EmbeddingEngine
from src.rag.vector_store import VectorStore
from src.tools.document_reader import read_document_fn

logger = logging.getLogger("rag.retriever")


def chunk_text(text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks respecting paragraph and sentence boundaries.

    Args:
        text: The source text to segment.
        chunk_size: Target character length per chunk (default 600).
        chunk_overlap: Overlapping character count between consecutive chunks (default 100).

    Returns:
        List of text chunk strings.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks = []
    start = 0
    stride = max(1, chunk_size - chunk_overlap)

    while start < len(cleaned):
        end = start + chunk_size
        chunk = cleaned[start:end]

        # If not at the very end, try to break cleanly at paragraph or sentence boundary
        if end < len(cleaned):
            last_newline = chunk.rfind("\n\n")
            last_period = chunk.rfind(". ")
            if last_newline != -1 and last_newline > chunk_size * 0.5:
                chunk = chunk[: last_newline + 2]
                end = start + len(chunk)
            elif last_period != -1 and last_period > chunk_size * 0.5:
                chunk = chunk[: last_period + 2]
                end = start + len(chunk)

        final_chunk = chunk.strip()
        if final_chunk:
            chunks.append(final_chunk)

        start = start + stride if (end - start) < stride else end - chunk_overlap

    return chunks


class KnowledgeRetriever:
    """Manages document chunking, vector indexing, and semantic retrieval."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore()

    def ingest_text(
        self,
        text: str,
        source_name: str = "manual_entry",
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> int:
        """
        Segment text into chunks, generate embeddings, and index in ChromaDB.

        Returns:
            Number of chunks successfully indexed.
        """
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return 0

        embeddings = self.embedding_engine.embed_batch(chunks)
        base_meta = metadata or {}

        metadatas = []
        ids = []
        doc_id = str(uuid.uuid4())[:8]

        for i, chunk in enumerate(chunks):
            meta = {
                **base_meta,
                "source": source_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": doc_id,
            }
            metadatas.append(meta)
            ids.append(f"{source_name}_{doc_id}_chk_{i}")

        self.vector_store.add_chunks(
            texts=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Ingested {len(chunks)} chunks from '{source_name}'.")
        return len(chunks)

    def ingest_document(
        self,
        content: str,
        source_name: str = "document",
        doc_category: str = "research"
    ) -> int:
        """Convenience method to ingest text content with category tag."""
        return self.ingest_text(
            text=content,
            source_name=source_name,
            metadata={"category": doc_category}
        )

    def ingest_file(self, file_path: str) -> int:
        """Extract text from a file and index its chunks into the vector store."""
        content = read_document_fn(file_path, max_characters=50000)
        if content.startswith("Error:"):
            logger.error(f"Cannot ingest '{file_path}': {content}")
            return 0

        path_obj = Path(file_path)
        return self.ingest_text(
            text=content,
            source_name=path_obj.name,
            metadata={"file_path": str(path_obj.resolve()), "extension": path_obj.suffix},
        )

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a search query using semantic similarity."""
        query_embedding = self.embedding_engine.embed_text(query)
        return self.vector_store.query(query_embedding=query_embedding, n_results=top_k)

    def format_retrieval_context(self, query: str, top_k: int = 4) -> str:
        """Format retrieved chunks into an LLM-ready context block."""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return f"No relevant context found in local knowledge base for query: '{query}'."

        formatted = [f"Retrieved {len(results)} relevant passages for '{query}':\n"]
        for i, item in enumerate(results, 1):
            source = item.get("metadata", {}).get("source", "Unknown Source")
            score = item.get("similarity_score", 0.0)
            content = item.get("content", "").strip()
            formatted.append(f"[{i}] Source: {source} (Relevance: {score:.2f})\n{content}\n")

        return "\n".join(formatted)


# Default singleton instance for tool invocation
_global_retriever = KnowledgeRetriever()


def get_default_retriever() -> KnowledgeRetriever:
    """Access the global KnowledgeRetriever singleton."""
    return _global_retriever


def retrieve_knowledge_fn(query: str, top_k: int = 3) -> str:
    """
    Search the local vector knowledge base for relevant research passages and excerpts.

    Args:
        query: Specific semantic topic or question to retrieve.
        top_k: Number of relevant passages to retrieve (default 3).

    Returns:
        Structured excerpts from the internal knowledge base with source citations.
    """
    cleaned = query.strip()
    if not cleaned:
        return "Error: Retrieval query cannot be empty."

    return _global_retriever.format_retrieval_context(cleaned, top_k=min(max(1, top_k), 8))


# Decorated OpenAI Agents SDK FunctionTool
retrieve_knowledge = function_tool(retrieve_knowledge_fn)
