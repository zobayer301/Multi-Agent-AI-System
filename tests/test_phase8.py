"""Phase 8 Unit Tests: Streamlit Frontend Interface Testing using AppTest."""
import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "src" / "frontend" / "app.py")


def test_streamlit_app_initial_render():
    """Verify that Streamlit app initializes cleanly without throwing exceptions."""
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=15)
    assert len(at.exception) == 0, f"App threw unexpected exceptions: {at.exception}"

    # Verify key UI components rendered
    assert len(at.sidebar.radio) >= 1
    assert "🔬 Research Studio" in at.sidebar.radio[0].options
    assert len(at.text_area) >= 1
    assert len(at.button) >= 1


def test_navigation_switch_to_chat():
    """Test switching navigation to '💬 Interactive Chat' view."""
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=15)
    assert len(at.exception) == 0

    # Switch radio to chat
    at.sidebar.radio[0].set_value("💬 Interactive Chat").run(timeout=15)
    assert len(at.exception) == 0
    assert any("Multi-Agent Research Chat" in str(m.value) for m in at.markdown)


def test_navigation_switch_to_rag():
    """Test switching navigation to '📚 RAG Knowledge Base' view."""
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=15)
    assert len(at.exception) == 0

    # Switch radio to RAG view
    at.sidebar.radio[0].set_value("📚 RAG Knowledge Base").run(timeout=15)
    assert len(at.exception) == 0
    assert any("RAG Vector Knowledge Base Explorer" in str(m.value) for m in at.markdown)
    assert len(at.text_area) >= 1


def test_navigation_switch_to_history():
    """Test switching navigation to '🗄️ Session History' view."""
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=15)
    assert len(at.exception) == 0

    # Switch radio to Session History view
    at.sidebar.radio[0].set_value("🗄️ Session History").run(timeout=15)
    assert len(at.exception) == 0
    assert any("Session History & Memory Vault" in str(m.value) for m in at.markdown)
