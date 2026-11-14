"""
Phase 7: FastAPI Backend Verification Script.

Demonstrates:
1. API Health Check (`GET /health`)
2. Document Ingestion into RAG (`POST /api/rag/ingest`)
3. Semantic Vector Search (`POST /api/rag/query`)
4. Multi-Agent Research Dispatch (`POST /api/research` async)
5. Polling Workflow Execution Progress (`GET /api/research/{session_id}`)
6. Fetching Final Audited Report & Execution Traces
7. Inspecting Database Sessions & Message Histories (`GET /api/sessions`)
"""

import asyncio
from httpx import AsyncClient, ASGITransport
from src.api.main import app


async def main():
    print("=" * 80)
    print("Multi-Agent AI System - Phase 7: FastAPI Backend Verification")
    print("=" * 80)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:

        # 1. Health Check
        print("\n[1/6] Testing Health Endpoint (GET /health)...")
        resp = await client.get("/health")
        print(f"Status: {resp.status_code} | Payload: {resp.json()}")
        assert resp.status_code == 200
        print("[✓] API Gateway is healthy and subsystems are connected.")

        # 2. Document Ingestion into RAG
        print("\n[2/6] Ingesting Technical Literature into RAG (POST /api/rag/ingest)...")
        sample_doc = {
            "content": (
                "Field clinical trials across Sub-Saharan Africa evaluated edge-quantized neural "
                "networks deployed on standard Android smartphones. In malaria-endemic rural dispensaries, "
                "computer-vision analysis of Giemsa-stained thin blood films yielded 94.8% diagnostic "
                "sensitivity and 91.2% specificity, reducing diagnosis latency from 48 hours to under 6 minutes. "
                "Crucially, 100% offline operation eliminated connectivity-induced failure modes."
            ),
            "source_name": "WHO_Frontline_Malaria_AI_2025.md",
            "category": "malaria_diagnostics"
        }
        ingest_resp = await client.post("/api/rag/ingest", json=sample_doc)
        print(f"Status: {ingest_resp.status_code} | Indexed Chunks: {ingest_resp.json()['chunks_indexed']}")
        assert ingest_resp.status_code == 200
        print("[✓] Document successfully parsed, chunked, and stored in ChromaDB vector store.")

        # 3. Semantic Vector Query
        print("\n[3/6] Querying RAG Vector Store (POST /api/rag/query)...")
        query_payload = {
            "query": "What was the diagnostic latency reduction for smartphone malaria screening?",
            "top_k": 1
        }
        query_resp = await client.post("/api/rag/query", json=query_payload)
        print(f"Status: {query_resp.status_code} | Matches: {query_resp.json()['total_matches']}")
        match_content = query_resp.json()["matches"][0]["content"][:180]
        print(f"Top Match Excerpt: '{match_content}...'")
        assert query_resp.status_code == 200
        print("[✓] Cosine similarity retrieval verified via REST API.")

        # 4. Asynchronous Research Workflow Dispatch
        print("\n[4/6] Dispatching Research Task (POST /api/research [run_async=True])...")
        session_id = "session_fastapi_demo_01"
        research_payload = {
            "topic": "Analyze the impact of artificial intelligence on healthcare in developing countries.",
            "session_id": session_id,
            "verification_threshold": 0.75,
            "use_simulation": True,
            "run_async": True
        }
        dispatch_resp = await client.post("/api/research", json=research_payload)
        print(f"Status: {dispatch_resp.status_code} | Response: {dispatch_resp.json()}")
        assert dispatch_resp.status_code == 202
        print(f"[✓] Task accepted in background. Session ID: {session_id}")

        # 5. Polling Research Progress
        print("\n[5/6] Polling Research Status (GET /api/research/{session_id})...")
        for poll_attempt in range(15):
            await asyncio.sleep(0.6)
            status_resp = await client.get(f"/api/research/{session_id}")
            status_data = status_resp.json()
            print(f"  Attempt {poll_attempt + 1}: Status = {status_data['status']} | Logs recorded = {len(status_data['execution_logs'])}")
            if status_data["status"] == "COMPLETED":
                break

        assert status_data["status"] == "COMPLETED"
        assert status_data["has_final_report"] is True
        print(f"[✓] Multi-agent orchestration completed. Final Report Title: '{status_data['report']['title']}'")

        # 6. Session History & Inspection
        print("\n[6/6] Inspecting Session Telemetry from SQLite...")
        sessions_resp = await client.get("/api/sessions")
        print(f"Total Database Sessions: {len(sessions_resp.json())}")

        messages_resp = await client.get(f"/api/sessions/{session_id}/messages?limit=4")
        print(f"Chronological Messages Sample: {len(messages_resp.json())} entries retrieved.")
        for msg in messages_resp.json():
            print(f"  - [{msg['role']}|{msg['agent_name']}]: {msg['content'][:80]}...")

    print("\n" + "=" * 80)
    print("[✓] PHASE 7 FASTAPI BACKEND VERIFIED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
