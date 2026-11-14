"""
Comprehensive Unit & Integration Tests for Phase 4:
Tool Integration (Web Search, Document Reader, Python Analytical Engine).
"""

import os
import pytest
from pathlib import Path

from src.tools import (
    search_web,
    search_web_fn,
    read_document,
    read_document_fn,
    execute_python_analysis,
    execute_python_analysis_fn,
)
from src.agents import (
    create_research_agent,
    create_analysis_agent,
    create_verification_agent,
)


def test_web_search_tool_execution():
    """Verify web_search function returns structured search results."""
    result = search_web_fn("artificial intelligence healthcare WHO")

    assert isinstance(result, str)
    assert len(result) > 50
    assert "Title:" in result
    assert "URL:" in result


def test_web_search_empty_query():
    """Verify web_search handles empty queries cleanly."""
    result = search_web_fn("   ")
    assert "Error: Search query cannot be empty." in result


def test_document_reader_text_file(tmp_path: Path):
    """Verify read_document correctly extracts content from a text/markdown file."""
    sample_file = tmp_path / "sample_research.md"
    sample_content = "# Clinical Trials 2025\n\nAI model achieved 94.2% diagnostic sensitivity."
    sample_file.write_text(sample_content, encoding="utf-8")

    result = read_document_fn(str(sample_file))

    assert "sample_research.md" in result
    assert "94.2% diagnostic sensitivity" in result


def test_document_reader_truncation(tmp_path: Path):
    """Verify read_document enforces character budget."""
    sample_file = tmp_path / "long_document.txt"
    sample_file.write_text("A" * 500, encoding="utf-8")

    result = read_document_fn(str(sample_file), max_characters=100)

    assert "[... Remaining content truncated for token efficiency ...]" in result
    assert "Truncated to 100 characters" in result


def test_document_reader_file_not_found():
    """Verify read_document handles non-existent paths gracefully."""
    result = read_document_fn("non_existent_file_xyz.pdf")
    assert "Error: File not found" in result


def test_document_reader_unsupported_format(tmp_path: Path):
    """Verify read_document flags unsupported binary extensions."""
    unsupported = tmp_path / "binary_data.exe"
    unsupported.write_bytes(b"\x00\x01\x02")

    result = read_document_fn(str(unsupported))
    assert "Unsupported file format '.exe'" in result


def test_python_tool_arithmetic_calculation():
    """Verify execute_python_analysis executes mathematical expressions."""
    code = """
rates = [0.12, 0.15, 0.18, 0.22]
avg_rate = sum(rates) / len(rates)
print(f"Average Growth: {avg_rate:.2%}")
"""
    result = execute_python_analysis_fn(code)

    assert "Execution Output:" in result
    assert "Average Growth: 16.75%" in result


def test_python_tool_math_and_statistics():
    """Verify execute_python_analysis can use math and statistics packages."""
    code = """
import math
import statistics

values = [10, 20, 30, 40, 50]
stdev = statistics.stdev(values)
sqrt_val = math.sqrt(256)
print(f"StDev: {stdev:.2f}, Sqrt: {sqrt_val}")
"""
    result = execute_python_analysis_fn(code)

    assert "StDev: 15.81" in result
    assert "Sqrt: 16.0" in result


def test_python_tool_restricted_module_rejection():
    """Verify execute_python_analysis blocks dangerous un-whitelisted modules."""
    code = "import os\nprint(os.name)"
    result = execute_python_analysis_fn(code)

    assert "ImportError: Import of module 'os' is restricted" in result


def test_python_tool_error_handling():
    """Verify execute_python_analysis catches runtime exceptions safely."""
    code = "print(100 / 0)"
    result = execute_python_analysis_fn(code)

    assert "Python Execution Error: ZeroDivisionError" in result


def test_agent_tool_bindings():
    """Verify tools are attached to their specialized agents by default."""
    researcher = create_research_agent()
    analyst = create_analysis_agent()
    verifier = create_verification_agent()

    researcher_tool_names = [getattr(t, "name", str(t)) for t in researcher.tools]
    analyst_tool_names = [getattr(t, "name", str(t)) for t in analyst.tools]
    verifier_tool_names = [getattr(t, "name", str(t)) for t in verifier.tools]

    assert "search_web_fn" in researcher_tool_names or "search_web" in researcher_tool_names
    assert "read_document_fn" in researcher_tool_names or "read_document" in researcher_tool_names
    assert "retrieve_knowledge_fn" in researcher_tool_names or "retrieve_knowledge" in researcher_tool_names

    assert "execute_python_analysis_fn" in analyst_tool_names or "execute_python_analysis" in analyst_tool_names

    assert "search_web_fn" in verifier_tool_names or "search_web" in verifier_tool_names
    assert "read_document_fn" in verifier_tool_names or "read_document" in verifier_tool_names
    assert "retrieve_knowledge_fn" in verifier_tool_names or "retrieve_knowledge" in verifier_tool_names
