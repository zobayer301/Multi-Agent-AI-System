"""Phase 6: SQLite Persistent Database Manager."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.database.models import MessageRecord, SessionRecord, MemoryEntry, SessionSummary


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


class DatabaseManager:
    """Manages persistent SQLite storage for multi-agent conversations, memory, and reports."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to 'data/research_memory.db'.
                     Pass ':memory:' for isolated, in-memory testing.
        """
        self._mem_conn: Optional[sqlite3.Connection] = None
        if db_path is None:
            data_dir = os.path.join("data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "research_memory.db")
        else:
            self.db_path = db_path
            if self.db_path == ":memory:":
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._mem_conn.row_factory = sqlite3.Row
            else:
                os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create or return database connection with dictionary row access."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        """Create schema tables if they do not exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 2. Conversation & Agent messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                agent_name TEXT,
                content TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            );
        """)

        # 3. Persistent Agent memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                memory_type TEXT NOT NULL DEFAULT 'fact',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            );
        """)

        # 4. Final research reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                executive_summary TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            );
        """)

        # Create indexing for rapid query execution
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_session ON memories (session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_session ON reports (session_id);")
        conn.commit()
        if self._mem_conn is None:
            conn.close()

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(self, title: str, session_id: Optional[str] = None) -> SessionRecord:
        """Create a new research session."""
        import uuid
        sid = session_id or f"session_{uuid.uuid4().hex[:8]}"
        now = _utc_now_str()
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO sessions (session_id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (sid, title, "active", now, now)
            )
            conn.commit()
        finally:
            if self._mem_conn is None:
                conn.close()
        return SessionRecord(session_id=sid, title=title, status="active", created_at=now, updated_at=now)

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """Fetch session metadata by session ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                return SessionRecord(
                    session_id=row["session_id"],
                    title=row["title"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        finally:
            if self._mem_conn is None:
                conn.close()
        return None

    def list_sessions(self) -> List[SessionRecord]:
        """List all research sessions ordered by updated_at descending."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
            return [
                SessionRecord(
                    session_id=r["session_id"],
                    title=r["title"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                )
                for r in rows
            ]
        finally:
            if self._mem_conn is None:
                conn.close()

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status and updated_at timestamp."""
        now = _utc_now_str()
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, now, session_id)
            )
            conn.commit()
        finally:
            if self._mem_conn is None:
                conn.close()

    # =========================================================================
    # Message History Management
    # =========================================================================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Record a conversation or agent thought/trace message."""
        now = _utc_now_str()
        meta_str = json.dumps(metadata or {})
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO messages (session_id, role, agent_name, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, agent_name, content, meta_str, now)
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()
            return cursor.lastrowid
        finally:
            if self._mem_conn is None:
                conn.close()

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[MessageRecord]:
        """Retrieve chronological message history for a session."""
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC"
        params: list = [session_id]
        if limit:
            query = "SELECT * FROM (SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id ASC"
            params.append(limit)

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            messages = []
            for r in rows:
                meta = {}
                try:
                    meta = json.loads(r["metadata_json"])
                except Exception:
                    pass
                messages.append(MessageRecord(
                    id=r["id"],
                    session_id=r["session_id"],
                    role=r["role"],
                    agent_name=r["agent_name"],
                    content=r["content"],
                    metadata=meta,
                    created_at=r["created_at"]
                ))
            return messages
        finally:
            if self._mem_conn is None:
                conn.close()

    # =========================================================================
    # Persistent Memory (Key-Value Facts / Constraints)
    # =========================================================================

    def save_memory(self, session_id: str, memory_type: str, key: str, value: str) -> int:
        """Store an important fact, constraint, or finding into persistent memory."""
        now = _utc_now_str()
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO memories (session_id, memory_type, key, value, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, memory_type, key, value, now)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            if self._mem_conn is None:
                conn.close()

    def get_memories(self, session_id: str, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Fetch remembered entries for a session, optionally filtered by type."""
        query = "SELECT * FROM memories WHERE session_id = ?"
        params: list = [session_id]
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
        query += " ORDER BY id ASC"

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            return [
                MemoryEntry(
                    id=r["id"],
                    session_id=r["session_id"],
                    memory_type=r["memory_type"],
                    key=r["key"],
                    value=r["value"],
                    created_at=r["created_at"]
                )
                for r in rows
            ]
        finally:
            if self._mem_conn is None:
                conn.close()

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a persistent memory record by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if self._mem_conn is None:
                conn.close()

    # =========================================================================
    # Research Reports Storage
    # =========================================================================

    def save_report(self, session_id: str, topic: str, executive_summary: str, report_data: Dict[str, Any]) -> int:
        """Persist a completed final research report in JSON format."""
        now = _utc_now_str()
        rep_str = json.dumps(report_data)
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO reports (session_id, topic, executive_summary, report_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, topic, executive_summary, rep_str, now)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            if self._mem_conn is None:
                conn.close()

    def get_latest_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest research report for a given session."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM reports WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row["report_json"])
                except Exception:
                    return {"topic": row["topic"], "executive_summary": row["executive_summary"]}
        finally:
            if self._mem_conn is None:
                conn.close()
        return None

    def get_session_summary(self, session_id: str) -> Optional[SessionSummary]:
        """Get high-level summary of session activities."""
        session = self.get_session(session_id)
        if not session:
            return None
        conn = self._get_connection()
        try:
            msg_count = conn.execute("SELECT COUNT(*) as c FROM messages WHERE session_id = ?", (session_id,)).fetchone()["c"]
            mem_count = conn.execute("SELECT COUNT(*) as c FROM memories WHERE session_id = ?", (session_id,)).fetchone()["c"]
            rep_count = conn.execute("SELECT COUNT(*) as c FROM reports WHERE session_id = ?", (session_id,)).fetchone()["c"]

            return SessionSummary(
                session_id=session.session_id,
                title=session.title,
                message_count=msg_count,
                memory_count=mem_count,
                has_final_report=rep_count > 0,
                status=session.status
            )
        finally:
            if self._mem_conn is None:
                conn.close()
