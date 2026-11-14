"""
Phase 7: FastAPI Backend for Multi-Agent AI Research Assistant.

Provides RESTful endpoints for:
- Initiating asynchronous/synchronous multi-agent research workflows.
- Polling research progress, agent thought traces, and final reports.
- Inspecting persistent conversation history and session memories from SQLite.
- Ingesting technical documents and running semantic queries against ChromaDB RAG.
"""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database.db import DatabaseManager
from src.database.memory import MemoryManager, get_default_memory_manager
from src.database.models import SessionRecord, SessionSummary, MessageRecord, MemoryEntry
from src.rag.retriever import get_default_retriever, KnowledgeRetriever
from src.workflows.research_workflow import ResearchWorkflow
from src.api.schemas import (
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
    ResearchStatusResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api_main")

# Global subsystem managers
db_manager = DatabaseManager()
memory_manager = MemoryManager(db_manager=db_manager)
knowledge_retriever = get_default_retriever()

# Background task runner tracking
_active_tasks: Dict[str, asyncio.Task] = {}


async def _run_workflow_background(
    topic: str,
    session_id: str,
    verification_threshold: float,
    use_simulation: Optional[bool]
) -> None:
    """Asynchronous background worker for executing multi-agent research workflow."""
    logger.info(f"Starting background workflow for session: '{session_id}' | Topic: '{topic}'")
    workflow = ResearchWorkflow(
        verification_threshold=verification_threshold,
        use_simulation=use_simulation,
        memory_manager=memory_manager,
    )
    try:
        await workflow.run(user_query=topic, session_id=session_id)
        logger.info(f"Successfully finished workflow for session: '{session_id}'")
    except Exception as exc:
        logger.error(f"Workflow execution failed for session '{session_id}': {exc}", exc_info=True)
        db_manager.update_session_status(session_id, "FAILED")
        memory_manager.record_agent_message(
            session_id=session_id,
            agent_name="System",
            content=f"Workflow failed with error: {str(exc)}"
        )
    finally:
        _active_tasks.pop(session_id, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan manager for clean startup and shutdown."""
    logger.info("Initializing Multi-Agent AI Assistant API backend...")
    yield
    logger.info("Shutting down Multi-Agent AI Assistant API backend...")
    for sid, task in _active_tasks.items():
        if not task.done():
            task.cancel()


# Instantiate FastAPI application
app = FastAPI(
    title="Multi-Agent AI Research Assistant API",
    description="Production-grade asynchronous REST API orchestrating specialized OpenAI agents, RAG, and memory.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend applications (Streamlit, React, Vue, CLI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


# =============================================================================
# System & Health Endpoints
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Multi-Agent AI Research & Analysis Assistant API",
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "research": "/api/research",
            "history": "/api/history",
            "knowledge_ingest": "/api/knowledge/ingest",
            "knowledge_query": "/api/knowledge/query"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def get_health_status():
    """Verify health and operational readiness of API, database, and vector store."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="Multi-Agent AI Research Assistant API",
        database_connected=db_manager.db_path is not None,
        rag_ready=knowledge_retriever is not None,
    )


# =============================================================================
# Multi-Agent Research Endpoints
# =============================================================================

@app.post("/api/research", tags=["Research"])
async def start_research(request: ResearchRequest, response: Response):
    """
    Initiate a multi-agent research workflow.

    - If `run_async=True`: Spawns asynchronous background worker and returns 202 Accepted.
    - If `run_async=False`: Awaits full pipeline execution and returns 200 with complete report.
    """
    sid = request.session_id or f"session_{uuid.uuid4().hex[:8]}"

    # Ensure session record exists in SQLite
    if not db_manager.get_session(sid):
        db_manager.create_session(title=request.topic[:60], session_id=sid)

    if request.run_async:
        response.status_code = status.HTTP_202_ACCEPTED
        task = asyncio.create_task(
            _run_workflow_background(
                topic=request.topic,
                session_id=sid,
                verification_threshold=request.verification_threshold,
                use_simulation=request.use_simulation,
            )
        )
        _active_tasks[sid] = task
        return ResearchResponse(
            session_id=sid,
            status="PROCESSING",
            message=f"Research task dispatched in background for topic: '{request.topic}'."
        )
    else:
        response.status_code = status.HTTP_200_OK
        workflow = ResearchWorkflow(
            verification_threshold=request.verification_threshold,
            use_simulation=request.use_simulation,
            memory_manager=memory_manager,
        )
        state = await workflow.run(user_query=request.topic, session_id=sid)
        session = db_manager.get_session(sid)
        report = db_manager.get_latest_report(sid)
        return ResearchStatusResponse(
            session_id=sid,
            title=session.title if session else request.topic,
            status=state.status.upper(),
            execution_logs=state.execution_logs,
            has_final_report=report is not None,
            report=report,
            created_at=session.created_at if session else "",
            updated_at=session.updated_at if session else "",
        )


@app.get("/api/research/{session_id}", response_model=ResearchStatusResponse, tags=["Research"])
async def get_research_status(session_id: str):
    """Retrieve execution status, logs, and final report for a research session."""
    session = db_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found."
        )

    messages = db_manager.get_messages(session_id)
    logs = [f"[{m.agent_name or m.role}] {m.content}" for m in messages if m.role in ("agent", "system")]
    report = db_manager.get_latest_report(session_id)

    return ResearchStatusResponse(
        session_id=session.session_id,
        title=session.title,
        status=session.status.upper(),
        execution_logs=logs,
        has_final_report=report is not None,
        report=report,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# =============================================================================
# Session & Memory Inspection Endpoints
# =============================================================================

@app.get("/api/sessions", response_model=List[SessionSummary], tags=["Sessions"])
async def list_sessions():
    """List all past and active research sessions with summary metrics."""
    sessions = db_manager.list_sessions()
    summaries = []
    for s in sessions:
        summary = db_manager.get_session_summary(s.session_id)
        if summary:
            summaries.append(summary)
    return summaries


@app.get("/api/sessions/{session_id}/messages", response_model=List[MessageRecord], tags=["Sessions"])
async def get_session_messages(session_id: str, limit: Optional[int] = Query(default=None, ge=1, le=100)):
    """Retrieve chronological conversation and thought trace messages for a session."""
    if not db_manager.get_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    return db_manager.get_messages(session_id, limit=limit)


@app.get("/api/sessions/{session_id}/memories", response_model=List[MemoryEntry], tags=["Sessions"])
async def get_session_memories(session_id: str, memory_type: Optional[str] = None):
    """Retrieve persistent facts and constraints stored for a session."""
    if not db_manager.get_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    return db_manager.get_memories(session_id, memory_type=memory_type)


# =============================================================================
# RAG Knowledge Base Endpoints
# =============================================================================

@app.post("/api/rag/ingest", response_model=DocumentIngestResponse, tags=["RAG"])
async def ingest_document(request: DocumentIngestRequest):
    """Chunk and ingest technical document content into ChromaDB vector store."""
    chunks = knowledge_retriever.ingest_document(
        content=request.content,
        source_name=request.source_name,
        doc_category=request.category,
    )
    return DocumentIngestResponse(
        source_name=request.source_name,
        chunks_indexed=chunks,
        message=f"Indexed {chunks} semantic passages into vector store."
    )


@app.post("/api/rag/query", response_model=KnowledgeQueryResponse, tags=["RAG"])
async def query_knowledge_base(request: KnowledgeQueryRequest):
    """Perform direct cosine-similarity semantic retrieval against the ChromaDB vector store."""
    matches = knowledge_retriever.retrieve(query=request.query, top_k=request.top_k)
    return KnowledgeQueryResponse(
        query=request.query,
        total_matches=len(matches),
        matches=matches,
    )
