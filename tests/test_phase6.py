"""Phase 6 Unit Tests: SQLite Database and Multi-Agent Memory Management."""
import pytest
from src.database.models import MessageRecord, SessionRecord, MemoryEntry
from src.database.db import DatabaseManager
from src.database.memory import (
    MemoryManager,
    set_active_session_id,
    save_memory_fact,
    recall_memory_facts,
)
from src.workflows.research_workflow import ResearchWorkflow


@pytest.fixture
def test_db():
    """Provide an isolated in-memory SQLite database manager for testing."""
    return DatabaseManager(db_path=":memory:")


@pytest.fixture
def test_memory_mgr(test_db):
    """Provide a MemoryManager instance backed by the in-memory database."""
    return MemoryManager(db_manager=test_db)


def test_session_lifecycle(test_db):
    """Test session creation, retrieval, listing, and status updates."""
    session = test_db.create_session(title="AI in Telemedicine", session_id="test_sess_001")
    assert session.session_id == "test_sess_001"
    assert session.title == "AI in Telemedicine"
    assert session.status == "active"

    fetched = test_db.get_session("test_sess_001")
    assert fetched is not None
    assert fetched.title == "AI in Telemedicine"

    test_db.update_session_status("test_sess_001", "completed")
    updated = test_db.get_session("test_sess_001")
    assert updated.status == "completed"

    sessions = test_db.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].session_id == "test_sess_001"


def test_message_history_persistence_and_windowing(test_db):
    """Test recording and windowed retrieval of multi-agent dialogue."""
    sid = "test_sess_002"
    test_db.create_session(title="Tuberculosis Screening", session_id=sid)

    msg_id1 = test_db.add_message(session_id=sid, role="user", content="Analyze diagnostic turnaround.")
    msg_id2 = test_db.add_message(
        session_id=sid,
        role="agent",
        agent_name="Research_Agent",
        content="Chest radiography AI reduced turnaround to 15 minutes.",
        metadata={"confidence": 0.95}
    )
    msg_id3 = test_db.add_message(
        session_id=sid,
        role="agent",
        agent_name="Verification_Agent",
        content="Verified against WHO 2024 guidance.",
        metadata={"status": "VERIFIED"}
    )

    all_messages = test_db.get_messages(session_id=sid)
    assert len(all_messages) == 3
    assert all_messages[0].role == "user"
    assert all_messages[1].agent_name == "Research_Agent"
    assert all_messages[1].metadata.get("confidence") == 0.95

    # Context window limit test
    recent_two = test_db.get_messages(session_id=sid, limit=2)
    assert len(recent_two) == 2
    assert recent_two[0].agent_name == "Research_Agent"
    assert recent_two[1].agent_name == "Verification_Agent"


def test_persistent_memory_storage_and_recall(test_db):
    """Test saving, retrieving, filtering, and deleting persistent memory facts."""
    sid = "test_sess_003"
    test_db.create_session(title="Edge Computing Constraints", session_id=sid)

    mem_id1 = test_db.save_memory(sid, memory_type="constraint", key="offline_mode", value="Required 100% offline")
    mem_id2 = test_db.save_memory(sid, memory_type="fact", key="sensitivity", value="93.2% retinal sensitivity")

    all_mems = test_db.get_memories(sid)
    assert len(all_mems) == 2

    # Filter by type
    constraints = test_db.get_memories(sid, memory_type="constraint")
    assert len(constraints) == 1
    assert constraints[0].key == "offline_mode"

    # Delete memory
    deleted = test_db.delete_memory(mem_id1)
    assert deleted is True
    remaining = test_db.get_memories(sid)
    assert len(remaining) == 1
    assert remaining[0].key == "sensitivity"


def test_short_term_scratchpad(test_memory_mgr):
    """Test ephemeral in-memory scratchpad storage."""
    sid = "test_sess_004"
    test_memory_mgr.set_scratchpad(sid, "current_hypothesis", "Edge AI cuts hospital readmissions by 30%")
    test_memory_mgr.set_scratchpad(sid, "rejected_sources", ["unverified_blog_post"])

    val = test_memory_mgr.get_scratchpad(sid, "current_hypothesis")
    assert val == "Edge AI cuts hospital readmissions by 30%"

    all_scratch = test_memory_mgr.get_all_scratchpad(sid)
    assert len(all_scratch) == 2

    test_memory_mgr.clear_scratchpad(sid)
    assert test_memory_mgr.get_all_scratchpad(sid) == {}


def test_prompt_formatting(test_memory_mgr):
    """Test formatting persistent memories and history into prompt markdown blocks."""
    sid = "test_sess_005"
    test_memory_mgr.db.create_session(title="Prompt Context Test", session_id=sid)
    test_memory_mgr.remember(sid, key="target_region", value="Sub-Saharan Africa", memory_type="constraint")
    test_memory_mgr.record_user_message(sid, "What are the primary hurdles?")

    mem_prompt = test_memory_mgr.format_memories_for_prompt(sid)
    assert "Persistent Session Memory & Constraints:" in mem_prompt
    assert "[CONSTRAINT] target_region: Sub-Saharan Africa" in mem_prompt

    hist_prompt = test_memory_mgr.format_history_for_prompt(sid)
    assert "Recent Conversation Context:" in hist_prompt
    assert "What are the primary hurdles?" in hist_prompt


def test_research_report_persistence(test_db):
    """Test saving and retrieving final structured research reports in SQLite."""
    sid = "test_sess_006"
    test_db.create_session(title="AI Diagnostics Report", session_id=sid)

    report_payload = {
        "title": "Clinical AI in Developing Markets",
        "executive_summary": "High diagnostic accuracy demonstrated in low-resource clinics.",
        "takeaways": ["Edge quantization required", "WHO funding expanding"]
    }
    rep_id = test_db.save_report(
        session_id=sid,
        topic="Clinical AI in Developing Markets",
        executive_summary=report_payload["executive_summary"],
        report_data=report_payload
    )
    assert rep_id > 0

    latest = test_db.get_latest_report(sid)
    assert latest is not None
    assert latest["title"] == "Clinical AI in Developing Markets"
    assert latest["takeaways"][0] == "Edge quantization required"

    summary = test_db.get_session_summary(sid)
    assert summary.has_final_report is True


@pytest.mark.anyio
async def test_workflow_end_to_end_with_memory(test_memory_mgr):
    """Test that ResearchWorkflow coordinates and populates SQLite memory during execution."""
    sid = "test_workflow_sess_001"
    wf = ResearchWorkflow(use_simulation=True, memory_manager=test_memory_mgr)

    state = await wf.run(user_query="Evaluate AI in rural maternal healthcare.", session_id=sid)
    assert state.status == "COMPLETED"

    # Verify session recorded in database
    session = test_memory_mgr.db.get_session(sid)
    assert session is not None
    assert session.status == "COMPLETED"

    # Verify messages logged
    messages = test_memory_mgr.db.get_messages(sid)
    assert len(messages) >= 5

    # Verify scratchpad captured stage outputs
    scratch = test_memory_mgr.get_all_scratchpad(sid)
    assert "plan" in scratch
    assert "research" in scratch
    assert "analysis" in scratch
    assert "verification" in scratch

    # Verify final report stored
    saved_report = test_memory_mgr.db.get_latest_report(sid)
    assert saved_report is not None
    assert "title" in saved_report

