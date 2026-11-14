"""Phase 6: Memory & Database Pydantic Schemas."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessageRecord(BaseModel):
    """Pydantic representation of an individual conversation or agent trace message."""
    id: Optional[int] = None
    session_id: str
    role: str = Field(description="Role: 'user', 'agent', 'system', or 'tool'")
    agent_name: Optional[str] = Field(default=None, description="Name of the agent (e.g. 'Research_Agent')")
    content: str = Field(description="Body of the message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary execution metadata")
    created_at: str = Field(default_factory=_utc_now_str)


class SessionRecord(BaseModel):
    """Pydantic representation of a multi-agent research session."""
    session_id: str
    title: str
    status: str = Field(default="active", description="'active', 'completed', or 'failed'")
    created_at: str = Field(default_factory=_utc_now_str)
    updated_at: str = Field(default_factory=_utc_now_str)


class MemoryEntry(BaseModel):
    """Pydantic representation of a persistent memory fact or constraint."""
    id: Optional[int] = None
    session_id: str
    memory_type: str = Field(default="fact", description="'fact', 'constraint', 'finding', 'preference'")
    key: str = Field(description="Identifier or keyword for the memory entry")
    value: str = Field(description="Text content of the remembered entity")
    created_at: str = Field(default_factory=_utc_now_str)


class SessionSummary(BaseModel):
    """Summary of database records associated with a research session."""
    session_id: str
    title: str
    message_count: int
    memory_count: int
    has_final_report: bool
    status: str
