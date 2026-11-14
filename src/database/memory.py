"""Phase 6: Multi-Agent Memory Manager (Short-Term, Persistent, and Context Windowing)."""
from typing import Dict, Any, List, Optional
from agents import function_tool
from src.database.db import DatabaseManager
from src.database.models import MessageRecord, MemoryEntry, SessionRecord


class MemoryManager:
    """Coordinates working short-term memory (in-memory scratchpad) and long-term SQLite persistence."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize MemoryManager with database backend and ephemeral working scratchpad."""
        self.db = db_manager or DatabaseManager()
        # Ephemeral short-term memory (session_id -> dict of key-value scratchpad items)
        self._scratchpads: Dict[str, Dict[str, Any]] = {}

    # =========================================================================
    # Short-Term Working Memory (Ephemeral / Scratchpad)
    # =========================================================================

    def set_scratchpad(self, session_id: str, key: str, value: Any) -> None:
        """Store an ephemeral value in the session's short-term scratchpad."""
        if session_id not in self._scratchpads:
            self._scratchpads[session_id] = {}
        self._scratchpads[session_id][key] = value

    def get_scratchpad(self, session_id: str, key: str, default: Any = None) -> Any:
        """Retrieve a value from the short-term scratchpad."""
        return self._scratchpads.get(session_id, {}).get(key, default)

    def get_all_scratchpad(self, session_id: str) -> Dict[str, Any]:
        """Return the entire scratchpad dictionary for a session."""
        return self._scratchpads.get(session_id, {}).copy()

    def clear_scratchpad(self, session_id: str) -> None:
        """Clear ephemeral scratchpad for a session."""
        if session_id in self._scratchpads:
            self._scratchpads[session_id].clear()

    # =========================================================================
    # Conversation History & Context Window Management
    # =========================================================================

    def record_user_message(self, session_id: str, content: str) -> int:
        """Record an incoming user message."""
        return self.db.add_message(session_id=session_id, role="user", content=content)

    def record_agent_message(
        self,
        session_id: str,
        agent_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Record an agent's reasoning, handoff, or final output message."""
        return self.db.add_message(
            session_id=session_id,
            role="agent",
            agent_name=agent_name,
            content=content,
            metadata=metadata
        )

    def get_recent_conversation(self, session_id: str, max_messages: int = 10) -> List[MessageRecord]:
        """Retrieve recent conversation messages, bounded by max_messages context window."""
        return self.db.get_messages(session_id=session_id, limit=max_messages)

    def format_history_for_prompt(self, session_id: str, max_messages: int = 6) -> str:
        """Format recent dialogue into a prompt-friendly string for agent context injection."""
        messages = self.get_recent_conversation(session_id, max_messages=max_messages)
        if not messages:
            return ""
        formatted = ["### Recent Conversation Context:"]
        for m in messages:
            sender = m.agent_name if m.role == "agent" and m.agent_name else m.role.capitalize()
            formatted.append(f"- **{sender}**: {m.content[:300]}...")
        return "\n".join(formatted)

    # =========================================================================
    # Persistent Memory (Facts, Constraints, Findings)
    # =========================================================================

    def remember(self, session_id: str, key: str, value: str, memory_type: str = "fact") -> int:
        """Save a persistent memory entry to the database."""
        return self.db.save_memory(session_id=session_id, memory_type=memory_type, key=key, value=value)

    def recall(self, session_id: str, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Retrieve all persistent memories for a session, optionally filtered by type."""
        return self.db.get_memories(session_id=session_id, memory_type=memory_type)

    def format_memories_for_prompt(self, session_id: str) -> str:
        """Format persistent facts and constraints into a markdown block for agent injection."""
        memories = self.recall(session_id)
        if not memories:
            return ""
        formatted = ["### Persistent Session Memory & Constraints:"]
        for mem in memories:
            formatted.append(f"- [{mem.memory_type.upper()}] {mem.key}: {mem.value}")
        return "\n".join(formatted)


# Global default instance for agent tools
_active_session_id: str = "default_session"
_default_memory_manager: Optional[MemoryManager] = None


def get_default_memory_manager() -> MemoryManager:
    """Get or create singleton MemoryManager."""
    global _default_memory_manager
    if _default_memory_manager is None:
        _default_memory_manager = MemoryManager()
    return _default_memory_manager


def set_active_session_id(session_id: str) -> None:
    """Set active session ID context for agent tools."""
    global _active_session_id
    _active_session_id = session_id


def get_active_session_id() -> str:
    """Get currently active session ID context."""
    global _active_session_id
    return _active_session_id


# =============================================================================
# Direct Functions and OpenAI Agents SDK Function Tools
# =============================================================================

def save_memory_fact_fn(key: str, value: str, memory_type: str = "fact") -> str:
    """Persist an important factual finding, user preference, or research constraint to memory."""
    mgr = get_default_memory_manager()
    sid = get_active_session_id()
    mem_id = mgr.remember(session_id=sid, key=key, value=value, memory_type=memory_type)
    return f"Successfully saved to persistent memory [ID: {mem_id}]: {key} -> {value}"


def recall_memory_facts_fn(memory_type: str = "") -> str:
    """Recall previously saved persistent facts and constraints for the current research session."""
    mgr = get_default_memory_manager()
    sid = get_active_session_id()
    m_type = memory_type.strip() if memory_type.strip() else None
    memories = mgr.recall(session_id=sid, memory_type=m_type)
    if not memories:
        return f"No persistent memories found for session '{sid}'."
    out = [f"Recalled {len(memories)} persistent memories for session '{sid}':"]
    for m in memories:
        out.append(f"- [{m.memory_type}] {m.key}: {m.value}")
    return "\n".join(out)


# Wrap into OpenAI Agents SDK FunctionTools for agent consumption
save_memory_fact = function_tool(save_memory_fact_fn)
recall_memory_facts = function_tool(recall_memory_facts_fn)
