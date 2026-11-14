"""Phase 7 Unit Tests: FastAPI Backend REST API Endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app, db_manager, knowledge_retriever


@pytest.fixture
async def client():
    """Async HTTP test client bound directly to the FastAPI ASGI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check_endpoint(client: AsyncClient):
    """Test GET /health returns operational readiness status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["database_connected"] is True


@pytest.mark.anyio
async def test_sessions_list_endpoint(client: AsyncClient):
    """Test GET /api/sessions returns a list of sessions."""
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_rag_ingest_and_query_endpoints(client: AsyncClient):
    """Test POST /api/rag/ingest and POST /api/rag/query."""
    # 1. Ingest document
    doc_payload = {
        "content": (
            "Point-of-care mobile deep learning algorithms achieved 94.1% sensitivity "
            "for malaria parasite detection in peripheral blood smears in field tests."
        ),
        "source_name": "Lancet_Infectious_Diseases_2025.md",
        "category": "malaria_diagnostics"
    }
    ingest_resp = await client.post("/api/rag/ingest", json=doc_payload)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert ingest_data["source_name"] == "Lancet_Infectious_Diseases_2025.md"
    assert ingest_data["chunks_indexed"] >= 1

    # 2. Query knowledge base
    query_payload = {
        "query": "What is the sensitivity for malaria parasite detection?",
        "top_k": 2
    }
    query_resp = await client.post("/api/rag/query", json=query_payload)
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total_matches"] >= 1


@pytest.mark.anyio
async def test_synchronous_research_endpoint(client: AsyncClient):
    """Test POST /api/research with run_async=False executes immediately and returns completed state."""
    payload = {
        "topic": "Evaluate edge AI for rural ultrasound diagnostics.",
        "session_id": "test_api_sync_sess_001",
        "verification_threshold": 0.70,
        "use_simulation": True,
        "run_async": False
    }
    response = await client.post("/api/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_api_sync_sess_001"
    assert data["status"] == "COMPLETED"
    assert data["has_final_report"] is True
    assert data["report"] is not None
    assert "title" in data["report"]


@pytest.mark.anyio
async def test_asynchronous_research_and_polling(client: AsyncClient):
    """Test POST /api/research with run_async=True returns 202 Accepted and allows status polling."""
    import asyncio
    payload = {
        "topic": "Assess telemedicine regulatory frameworks in West Africa.",
        "session_id": "test_api_async_sess_002",
        "verification_threshold": 0.70,
        "use_simulation": True,
        "run_async": True
    }
    resp = await client.post("/api/research", json=payload)
    assert resp.status_code == 202
    resp_data = resp.json()
    assert resp_data["session_id"] == "test_api_async_sess_002"
    assert resp_data["status"] == "PROCESSING"

    # Poll status until completed (simulation executes quickly)
    for _ in range(20):
        await asyncio.sleep(0.5)
        status_resp = await client.get("/api/research/test_api_async_sess_002")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] == "COMPLETED":
            break

    final_status = await client.get("/api/research/test_api_async_sess_002")
    final_data = final_status.json()
    assert final_data["status"] == "COMPLETED"
    assert final_data["has_final_report"] is True


@pytest.mark.anyio
async def test_session_messages_and_memories_endpoints(client: AsyncClient):
    """Test GET /api/sessions/{session_id}/messages and /memories."""
    # Using the completed session from previous test
    sid = "test_api_sync_sess_001"

    # Messages
    msg_resp = await client.get(f"/api/sessions/{sid}/messages")
    assert msg_resp.status_code == 200
    messages = msg_resp.json()
    assert len(messages) >= 5

    # Memories
    mem_resp = await client.get(f"/api/sessions/{sid}/memories")
    assert mem_resp.status_code == 200
    assert isinstance(mem_resp.json(), list)


@pytest.mark.anyio
async def test_not_found_handling(client: AsyncClient):
    """Test 404 responses for nonexistent sessions."""
    resp = await client.get("/api/research/non_existent_session_999999")
    assert resp.status_code == 404
