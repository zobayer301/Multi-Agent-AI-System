"""Phase 6: Multi-Agent Database & Memory Management Package."""
from src.database.models import MessageRecord, SessionRecord, MemoryEntry, SessionSummary
from src.database.db import DatabaseManager
from src.database.memory import (
    MemoryManager,
    get_default_memory_manager,
    set_active_session_id,
    get_active_session_id,
    save_memory_fact_fn,
    recall_memory_facts_fn,
    save_memory_fact,
    recall_memory_facts,
)

__all__ = [
    "MessageRecord",
    "SessionRecord",
    "MemoryEntry",
    "SessionSummary",
    "DatabaseManager",
    "MemoryManager",
    "get_default_memory_manager",
    "set_active_session_id",
    "get_active_session_id",
    "save_memory_fact_fn",
    "recall_memory_facts_fn",
    "save_memory_fact",
    "recall_memory_facts",
]
