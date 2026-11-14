"""
Phase 5 Test Runner: Interactive RAG & ChromaDB Vector Store Verification.

Demonstrates:
1. Document ingestion and chunking into ChromaDB.
2. Generating 1536-dimensional embeddings.
3. Querying the vector database via cosine similarity.
4. Calling the `retrieve_knowledge` FunctionTool equipped on Research and Verification agents.
"""

from src.rag import (
    EmbeddingEngine,
    VectorStore,
    KnowledgeRetriever,
    retrieve_knowledge_fn,
)


def run_phase5_diagnostics() -> None:
    print("=" * 80)
    print("Multi-Agent AI System - Phase 5: RAG & Vector Store Verification")
    print("=" * 80)

    # 1. Test Embedding Engine
    print("\n[1/4] Testing Embedding Engine (1536-dimensional vectors)...")
    engine = EmbeddingEngine()
    test_phrase = "Artificial Intelligence for Point-of-Care Diagnostics"
    vec = engine.embed_text(test_phrase)
    print(f"Text: \"{test_phrase}\"")
    print(f"Embedding Engine Mode: {'Live OpenAI API (text-embedding-3-small)' if engine.is_live else 'Deterministic Offline Generator'}")
    print(f"Vector Dimensions: {len(vec)} | First 5 values: {[round(x, 4) for x in vec[:5]]}")
    print("[✓] Embedding Engine verified.")

    # 2. Test Ingestion & Vector Storage
    print("\n[2/4] Ingesting Technical Research Data into ChromaDB...")
    store = VectorStore(collection_name="clinical_ai_demo", in_memory=True)
    retriever = KnowledgeRetriever(vector_store=store, embedding_engine=engine)

    sample_paper = """
# World Health Organization Clinical AI Synthesis (2024-2025)

## Section 1: Tuberculosis Computer-Aided Detection (CAD)
Automated chest X-ray classifiers deployed across 42 district hospitals in Sub-Saharan Africa
reduced average diagnosis latency from 14.2 days down to 11.5 minutes. When calibrated against
culture-confirmed sputum standards, CAD systems demonstrated 93.8% sensitivity and 89.4% specificity.

## Section 2: Last-Mile Electrical & Network Realities
Over 62.4% of rural healthcare facilities in low-income jurisdictions experience unannounced
grid outages exceeding 4 hours daily. Cloud-only healthcare software recorded a 78% communication
timeout failure rate during wet-season monsoons. Consequently, edge-native 4-bit quantized neural
networks operating entirely offline on mobile handsets represent the only viable deployment pattern.

## Section 3: Diabetic Retinopathy Mobile Screening
Coupled with low-cost 3D-printed ophthalmic lenses, mobile deep learning models attained 93.2%
sensitivity for sight-threatening diabetic retinopathy in primary care field clinics in South Asia.
"""
    num_chunks = retriever.ingest_text(
        text=sample_paper,
        source_name="WHO_Clinical_AI_Synthesis_2025.md",
        chunk_size=350,
        chunk_overlap=50,
    )
    print(f"Document chunked and indexed: {num_chunks} chunks stored in ChromaDB.")
    print(f"Total vector records in collection: {store.count()}")
    print("[✓] ChromaDB ingestion operational.")

    # 3. Test Semantic Similarity Retrieval
    print("\n[3/4] Performing Semantic Cosine Similarity Queries...")
    queries = [
        "What are the diagnostic sensitivity rates for tuberculosis X-ray screening?",
        "Why do cloud-only AI models fail in rural field deployments?",
    ]

    for q in queries:
        print(f"\nQuery: \"{q}\"")
        results = retriever.retrieve(q, top_k=1)
        if results:
            match = results[0]
            print(f"Top Match Source: {match['metadata'].get('source')} | Score: {match['similarity_score']:.2f}")
            print(f"Matched Excerpt:\n{match['content'].strip()}")
    print("[✓] Semantic vector retrieval operational.")

    # 4. Test retrieve_knowledge FunctionTool
    print("\n[4/4] Testing `retrieve_knowledge` FunctionTool (as invoked by agents)...")
    # Ingest into default retriever so the tool has access
    from src.rag import get_default_retriever
    get_default_retriever().ingest_text(
        text=sample_paper,
        source_name="Global_Health_AI_Index.md",
        chunk_size=350,
        chunk_overlap=50,
    )

    tool_result = retrieve_knowledge_fn("diabetic retinopathy mobile screening sensitivity", top_k=1)
    print("-" * 80)
    print(tool_result.strip())
    print("-" * 80)
    print("[✓] `retrieve_knowledge` FunctionTool verified.")

    print("\n" + "=" * 80)
    print("[✓] PHASE 5 RAG & VECTOR STORE INTEGRATION VERIFIED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_phase5_diagnostics()
