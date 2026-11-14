"""Phase 7: FastAPI Request and Response Pydantic Schemas."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "healthy"
    version: str = "1.0.0"
    service: str = "Multi-Agent AI Research Assistant API"
    timestamp: str = Field(default_factory=_utc_now_str)
    database_connected: bool = True
    rag_ready: bool = True


class ResearchRequest(BaseModel):
    """Payload to initiate a multi-agent research workflow."""
    topic: str = Field(
        ...,
        min_length=3,
        description="The research question or topic (e.g., 'Impact of AI on Healthcare in Developing Countries')"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional unique session identifier. If omitted, one is automatically generated."
    )
    verification_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum integrity score required from the Verification Agent."
    )
    use_simulation: Optional[bool] = Field(
        default=None,
        description="Force offline simulation (ScriptedModel) if True. If None, auto-detected from API key."
    )
    run_async: bool = Field(
        default=True,
        description="If True, dispatches workflow in background and returns 202 immediately. If False, awaits completion."
    )


class ResearchResponse(BaseModel):
    """Immediate acknowledgement returned when a research task is initiated."""
    session_id: str
    status: str = "PROCESSING"
    message: str
    created_at: str = Field(default_factory=_utc_now_str)


class ResearchStatusResponse(BaseModel):
    """Comprehensive status of an ongoing or completed research session."""
    session_id: str
    title: str
    status: str
    execution_logs: List[str] = Field(default_factory=list)
    has_final_report: bool = False
    report: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class DocumentIngestRequest(BaseModel):
    """Payload to ingest raw text or document content into ChromaDB."""
    content: str = Field(..., min_length=10, description="Raw text or markdown document content to chunk and index.")
    source_name: str = Field(..., min_length=2, description="Identifier or filename of the document source.")
    category: str = Field(default="research", description="Category tag for metadata filtering.")


class DocumentIngestResponse(BaseModel):
    """Response returned after ingesting a document into ChromaDB."""
    source_name: str
    chunks_indexed: int
    message: str
    created_at: str = Field(default_factory=_utc_now_str)


class KnowledgeQueryRequest(BaseModel):
    """Payload to semantically search the RAG vector store."""
    query: str = Field(..., min_length=2, description="Semantic search query.")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of relevant chunks to retrieve.")


class KnowledgeQueryResponse(BaseModel):
    """Response containing semantically matched passages from ChromaDB."""
    query: str
    total_matches: int
    matches: List[Dict[str, Any]]
