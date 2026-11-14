"""
Comprehensive Unit & Integration Tests for Phase 5:
Retrieval-Augmented Generation (RAG) with ChromaDB and Embeddings.
"""

import math
import pytest
from src.rag import (
    EmbeddingEngine,
    EMBEDDING_DIM,
    VectorStore,
    KnowledgeRetriever,
    chunk_text,
    retrieve_knowledge_fn,
)


def test_embedding_generation():
    """Verify EmbeddingEngine generates unit-normalized vectors of expected dimensions."""
    engine = EmbeddingEngine()
    vec = engine.embed_text("Artificial Intelligence in Global Health")

    assert isinstance(vec, list)
    assert len(vec) == EMBEDDING_DIM
    # Verify vector is unit normalized (Euclidean norm ≈ 1.0)
    norm = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)


def test_batch_embedding_generation():
    """Verify batch embedding generation for multiple texts."""
    engine = EmbeddingEngine()
    texts = [
        "Clinical trials for edge computing neural networks.",
        "Rural electrification and healthcare infrastructure deficits.",
    ]
    batch_vecs = engine.embed_batch(texts)

    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == EMBEDDING_DIM
    assert len(batch_vecs[1]) == EMBEDDING_DIM


def test_text_chunking():
    """Verify text chunking logic with sentence boundary awareness."""
    short_text = "This is a brief summary of a medical study."
    chunks_short = chunk_text(short_text, chunk_size=200)
    assert len(chunks_short) == 1
    assert chunks_short[0] == short_text

    long_text = (
        "Paragraph 1: Point-of-care mobile radiography classifiers have compressed pulmonary tuberculosis "
        "turnaround times from 14 days down to under 15 minutes, dramatically curbing community transmission.\n\n"
        "Paragraph 2: Healthcare environments in developing nations exhibit stark infrastructural realities: "
        "over 62% of primary clinics experience frequent power intermittency and lack broadband connectivity.\n\n"
        "Paragraph 3: An adversarial verification audit established a 0.91 data integrity rating. "
        "Core clinical diagnostic sensitivity and electrical infrastructure metrics are verified against peer-reviewed datasets."
    )
    chunks_long = chunk_text(long_text, chunk_size=250, chunk_overlap=50)

    assert len(chunks_long) >= 2
    for c in chunks_long:
        assert len(c) > 0


def test_vector_store_in_memory():
    """Verify ChromaDB in-memory store operations (add, query, count, reset)."""
    store = VectorStore(collection_name="test_collection", in_memory=True)
    engine = EmbeddingEngine()

    docs = [
        "Retinal imaging algorithms achieved 93.2% sensitivity in rural clinics.",
        "Grid power failure affects 62% of district dispensaries.",
    ]
    embeddings = engine.embed_batch(docs)
    metadatas = [{"source": "study_a.pdf"}, {"source": "report_b.pdf"}]

    store.add_chunks(texts=docs, embeddings=embeddings, metadatas=metadatas)

    assert store.count() == 2

    # Query for retinal diagnostics
    query_vec = engine.embed_text("ophthalmic retinal screening accuracy")
    results = store.query(query_embedding=query_vec, n_results=1)

    assert len(results) == 1
    assert "Retinal" in results[0]["content"]
    assert results[0]["metadata"]["source"] == "study_a.pdf"

    store.reset()
    assert store.count() == 0


def test_knowledge_retriever_pipeline():
    """Verify end-to-end RAG ingestion and retrieval through KnowledgeRetriever."""
    store = VectorStore(collection_name="test_pipeline", in_memory=True)
    retriever = KnowledgeRetriever(vector_store=store)

    knowledge_doc = (
        "Solid-state battery electrolytes utilize sulfide and oxide ceramic matrices. "
        "These solid matrices prevent lithium dendrite penetration and improve thermal stability up to 180 degrees Celsius. "
        "However, commercial production yields remain constrained by interface impedance and high-pressure packaging requirements."
    )
    ingested_count = retriever.ingest_text(
        text=knowledge_doc,
        source_name="battery_review_2025.txt",
        chunk_size=150,
        chunk_overlap=30,
    )

    assert ingested_count >= 2

    # Query for battery dendrites
    context = retriever.format_retrieval_context("How do solid-state electrolytes stop dendrites?")

    assert "Retrieved" in context
    assert "battery_review_2025.txt" in context
    assert "dendrite" in context.lower()


def test_retrieve_knowledge_function_tool():
    """Verify retrieve_knowledge tool execution."""
    result = retrieve_knowledge_fn("healthcare in low-income regions")
    assert isinstance(result, str)
    assert len(result) > 10

    # Test empty query guard
    empty_result = retrieve_knowledge_fn("   ")
    assert "Error: Retrieval query cannot be empty." in empty_result
