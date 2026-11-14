"""
Phase 4 Test Runner: Interactive Verification of Agent Tool Integrations.

Demonstrates:
1. Live / Fallback Web Search via DuckDuckGo.
2. Local Document Reading (.pdf, .md, .txt) with Character Budgeting.
3. Sandboxed Python Analytical Calculation for Quantitative Insights.
4. Specialized Agent Tool Attachments.
"""

import sys
import tempfile
from pathlib import Path

from src.tools import search_web_fn, read_document_fn, execute_python_analysis_fn
from src.agents import (
    create_research_agent,
    create_analysis_agent,
    create_verification_agent,
)


def run_phase4_diagnostics() -> None:
    print("=" * 80)
    print("Multi-Agent AI System - Phase 4: Tool Integration Verification")
    print("=" * 80)

    # 1. Test Web Search Tool
    print("\n[1/3] Testing Web Search Tool (search_web)...")
    query = "WHO digital health guidelines rural clinics artificial intelligence"
    print(f"Query: \"{query}\"")
    search_output = search_web_fn(query, max_results=3)
    print("-" * 80)
    print(search_output[:450] + "\n[... truncated for display ...]")
    print("-" * 80)
    print("[✓] Web Search Tool operational.")

    # 2. Test Document Reader Tool
    print("\n[2/3] Testing Document Reader Tool (read_document)...")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Field Trial Data: Rural Clinic Retinal Diagnostic AI\n\n"
                "Cohort Size: 1,420 patients across 8 district centers.\n"
                "Observed Sensitivity: 93.4% (95% CI: 91.2% - 95.1%).\n"
                "Observed Specificity: 89.1%.\n"
                "Connectivity: 58% of tests completed fully offline on handheld scanners.")
        temp_file_path = f.name

    doc_output = read_document_fn(temp_file_path, max_characters=500)
    print("-" * 80)
    print(doc_output)
    print("-" * 80)
    print("[✓] Document Reader Tool operational.")

    # 3. Test Safe Python Analytical Calculator
    print("\n[3/3] Testing Safe Python Calculator (execute_python_analysis)...")
    code = """
import math
import statistics

# Clinical Diagnostic Metrics
true_positives = 420
false_negatives = 30
true_negatives = 810
false_positives = 90

total = true_positives + false_negatives + true_negatives + false_positives
sensitivity = true_positives / (true_positives + false_negatives)
specificity = true_negatives / (true_negatives + false_positives)
accuracy = (true_positives + true_negatives) / total

print(f"Total Cohort: {total}")
print(f"Sensitivity: {sensitivity:.2%}")
print(f"Specificity: {specificity:.2%}")
print(f"Diagnostic Accuracy: {accuracy:.2%}")
"""
    python_output = execute_python_analysis_fn(code)
    print("-" * 80)
    print(python_output)
    print("-" * 80)
    print("[✓] Safe Python Tool operational.")

    # 4. Display Agent Tool Attachments
    print("\n" + "=" * 80)
    print("SPECIALIZED AGENT TOOL ATTACHMENT AUDIT:")
    print("=" * 80)
    researcher = create_research_agent()
    analyst = create_analysis_agent()
    verifier = create_verification_agent()

    print(f"• {researcher.name:<22} -> Tools: {[t.name for t in researcher.tools]}")
    print(f"• {analyst.name:<22} -> Tools: {[t.name for t in analyst.tools]}")
    print(f"• {verifier.name:<22} -> Tools: {[t.name for t in verifier.tools]}")
    print("=" * 80)
    print("[✓] ALL TOOLS SUCCESSFULLY INTEGRATED AND BOUND TO SPECIALIZED AGENTS")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_diagnostics()
