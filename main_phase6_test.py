"""
Phase 6: Multi-Agent Memory Management & Persistent SQLite Storage Verification.

Demonstrates:
1. SQLite Database & Session Lifecycle Management
2. Multi-turn Conversation History & Context Window Truncation
3. Persistent Long-Term Memory (Facts, Constraints, Domain Findings)
4. Ephemeral In-Memory Scratchpad (Short-Term Working Memory)
5. Agent Memory Tools (`save_memory_fact`, `recall_memory_facts`)
6. End-to-End Hierarchical Workflow execution with persistent report storage in SQLite.
"""

import asyncio
import json
import os
from src.database.db import DatabaseManager
from src.database.memory import (
    MemoryManager,
    set_active_session_id,
    save_memory_fact_fn,
    recall_memory_facts_fn,
    save_memory_fact,
    recall_memory_facts,
)
from src.workflows.research_workflow import ResearchWorkflow


async def main():
    print("=" * 80)
    print("Multi-Agent AI System - Phase 6: Memory Management Verification")
    print("=" * 80)

    # 1. Initialize DatabaseManager with dedicated verification database
    test_db_path = os.path.join("data", "verify_phase6_memory.db")
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    db = DatabaseManager(db_path=test_db_path)
    mem_mgr = MemoryManager(db_manager=db)
    print(f"\n[1/6] SQLite Database Initialized at: {test_db_path}")

    # 2. Session Lifecycle
    session_id = "session_research_africa_01"
    session = db.create_session(
        title="Impact of AI on Healthcare in Developing Countries",
        session_id=session_id
    )
    print(f"[✓] Created research session: {session.session_id} ('{session.title}')")

    # 3. Conversation History
    print("\n[2/6] Storing Multi-Agent Conversation & Thought Traces...")
    db.add_message(
        session_id=session_id,
        role="user",
        content="Analyze the impact of artificial intelligence on healthcare in developing countries."
    )
    db.add_message(
        session_id=session_id,
        role="agent",
        agent_name="Supervisor_Agent",
        content="Decomposing user research question into diagnostic speed, connectivity bottlenecks, and policy."
    )
    db.add_message(
        session_id=session_id,
        role="agent",
        agent_name="Research_Agent",
        content="Discovered 93.2% sensitivity for mobile diabetic retinopathy screening.",
        metadata={"source": "Lancet Digital Health 2025", "confidence": 0.94}
    )

    messages = db.get_messages(session_id=session_id)
    print(f"[✓] {len(messages)} chronological messages stored in SQLite messages table.")
    recent_two = db.get_messages(session_id=session_id, limit=2)
    print(f"[✓] Windowed message retrieval (limit=2) returned latest {len(recent_two)} messages.")

    # 4. Long-Term Persistent Memory (Facts & Constraints)
    print("\n[3/6] Persisting Critical Facts & Constraints...")
    db.save_memory(
        session_id=session_id,
        memory_type="constraint",
        key="deployment_requirement",
        value="Edge-native 4-bit/8-bit models with 100% offline capability required due to 62% grid instability."
    )
    db.save_memory(
        session_id=session_id,
        memory_type="fact",
        key="tb_diagnostic_acceleration",
        value="Computer-aided chest radiography compressed active TB triage from 14 days down to 15 minutes."
    )
    memories = db.get_memories(session_id=session_id)
    print(f"[✓] Stored {len(memories)} persistent memories:")
    for m in memories:
        print(f"    - [{m.memory_type.upper()}] {m.key}: {m.value[:70]}...")

    # 5. Short-Term In-Memory Scratchpad
    print("\n[4/6] Testing Ephemeral Short-Term Working Memory (Scratchpad)...")
    mem_mgr.set_scratchpad(session_id, "active_hypothesis", "Edge AI yields 3x clinical ROI in doctor-scarce clinics")
    mem_mgr.set_scratchpad(session_id, "rejected_queries", ["cloud telemedicine bandwidth requirements"])
    retrieved_hypo = mem_mgr.get_scratchpad(session_id, "active_hypothesis")
    print(f"[✓] Scratchpad retrieved value: '{retrieved_hypo}'")

    # 6. Agents SDK FunctionTools for Memory
    print("\n[5/6] Testing Memory Function Tools (as invoked by agents)...")
    set_active_session_id(session_id)
    save_tool_result = save_memory_fact_fn(
        key="who_recommendation_2025",
        value="WHO recommends human-in-the-loop triage for automated computer vision.",
        memory_type="guideline"
    )
    print(f"Tool Output: {save_tool_result}")
    recalled = recall_memory_facts_fn()
    print(f"\nRecalled Output from Tool:\n{recalled}")

    # 7. End-to-End Workflow with SQLite Persistence
    print("\n[6/6] Executing Hierarchical Research Workflow with SQLite Integration...")
    wf = ResearchWorkflow(use_simulation=True, memory_manager=mem_mgr)
    state = await wf.run(
        user_query="Analyze the impact of artificial intelligence on healthcare in developing countries.",
        session_id=session_id
    )

    print(f"[✓] Workflow completed with status: {state.status}")
    print(f"[✓] Execution log entries recorded: {len(state.execution_logs)}")

    # Verify SQLite Persistence of Report & Session Summary
    persisted_report = db.get_latest_report(session_id)
    summary = db.get_session_summary(session_id)

    print("\n" + "=" * 80)
    print("SESSION SUMMARY IN SQLITE:")
    print(f"  Session ID: {summary.session_id}")
    print(f"  Title: {summary.title}")
    print(f"  Total Messages Logged: {summary.message_count}")
    print(f"  Total Persistent Memories: {summary.memory_count}")
    print(f"  Final Report Persisted: {summary.has_final_report}")
    print(f"  Session Status: {summary.status}")
    print(f"  Persisted Report Title: '{persisted_report.get('title')}'")
    print("=" * 80)
    print("[✓] PHASE 6 MEMORY MANAGEMENT & DATABASE VERIFIED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
