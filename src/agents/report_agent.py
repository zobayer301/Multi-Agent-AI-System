"""
Report Agent implementation using the OpenAI Agents SDK.

The Report Agent serves as the principal synthesizer and publication editor.
It receives the cumulative outputs from the Research, Analysis, and Verification agents,
resolves any conflicting perspectives using the verification audit, and produces a
polished, comprehensive, publication-grade research report.
"""

import os
from typing import Optional, Any
from agents import Agent
from src.agents.schemas import ReportOutput

REPORT_AGENT_INSTRUCTIONS = """You are a specialized Report Agent in a Multi-Agent AI system.

Your primary mission:
1. Ingest findings from the Research Agent, insights from the Analysis Agent, and integrity audits from the Verification Agent.
2. Structure the combined intelligence into a professional, cohesive, publication-quality research report.
3. Integrate verification feedback: ensure unsupported assertions are flagged with appropriate caveats and contradictions are reconciled transparently.
4. Formulate an authoritative Executive Summary that provides an immediate overview of high-impact takeaways.
5. Elaborate findings into logical thematic chapters with clear Markdown headings, comparative tables, and data bullet points.
6. Provide actionable strategic recommendations and a forward-looking conclusion.
7. Include a rigorous Bibliography / References section listing all sources and citations.

Output Structure:
# [Comprehensive Report Title]
- **Executive Summary**: Core synthesis and high-level briefing.
- **Key Takeaways**: High-density summary bullet points.
- **1. Background & Foundational Context**
- **2. Core Findings & Technological Advancements**
- **3. Deep Analysis & Comparative Evaluation**
- **4. Verification & Reliability Audit** (Noting caveats, confidence metrics, and confirmed facts)
- **5. Strategic Implications & Forward Recommendations**
- **6. Conclusion & Future Outlook**
- **References & Citations**

Maintain a clear, polished, authoritative, and professional tone suited for executive briefings, technical leadership, and academic publishing.
"""


def create_report_agent(
    model: Optional[str] = None,
    name: str = "Report_Agent",
    output_type: Optional[Any] = None,
) -> Agent:
    """
    Factory function to initialize and return a configured Report Agent instance.

    Args:
        model: Optional model name (e.g., 'gpt-4o-mini', 'gpt-4o').
               Defaults to OPENAI_MODEL environment variable or 'gpt-4o-mini'.
        name: The identifying name for this agent.
        output_type: Optional Pydantic model class for structured schema enforcement.

    Returns:
        Agent: A configured instance of the OpenAI Agents SDK Agent class.
    """
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    kwargs = {
        "name": name,
        "instructions": REPORT_AGENT_INSTRUCTIONS,
        "model": resolved_model,
        "tools": [],  # Document export / compilation tools will be attached in Phase 4
    }
    if output_type is not None:
        kwargs["output_type"] = output_type

    return Agent(**kwargs)
