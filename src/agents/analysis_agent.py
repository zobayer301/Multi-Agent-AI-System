"""
Analysis Agent implementation using the OpenAI Agents SDK.

Equipped with:
- execute_python_analysis: Quantitative calculations, CAGR, statistical metrics, and data computations.
"""

import os
from typing import Optional, Any, List
from agents import Agent
from src.agents.schemas import AnalysisOutput
from src.tools.python_tool import execute_python_analysis

ANALYSIS_AGENT_INSTRUCTIONS = """You are a specialized Analysis Agent in a Multi-Agent AI system.

Your primary mission:
1. Thoroughly examine research findings, raw data, or literature provided in the context.
2. Use `execute_python_analysis` to compute statistical metrics, growth rates, ratios, and percentages whenever evaluating numerical claims.
3. Uncover latent patterns, causal relationships, and structural correlations across different findings.
4. Contrast divergent perspectives, trade-offs, and competing technical or economic paradigms.
5. Pinpoint high-value strategic opportunities created by recent developments.
6. Rigorously critique systemic limitations, execution bottlenecks, safety vulnerabilities, and failure modes.
7. Synthesize clear, actionable analytical insights that bridge raw research with strategic decision-making.

Output Structure:
- Thematic Patterns & Structural Dynamics
- Comparative Analysis (Competing perspectives, methodologies, or paradigms)
- Strategic & Technological Opportunities
- Bottlenecks, Constraints & Risks
- Key Analytical Insights & Takeaways

Maintain a critical, analytical, and objective stance. Avoid surface-level repetition of facts—focus on "why it matters", "how components interact", and "what trade-offs exist".
"""


def create_analysis_agent(
    model: Optional[str] = None,
    name: str = "Analysis_Agent",
    output_type: Optional[Any] = None,
    tools: Optional[List[Any]] = None,
) -> Agent:
    """Factory function to initialize and return a configured Analysis Agent instance."""
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    attached_tools = tools if tools is not None else [execute_python_analysis]

    kwargs = {
        "name": name,
        "instructions": ANALYSIS_AGENT_INSTRUCTIONS,
        "model": resolved_model,
        "tools": attached_tools,
    }
    if output_type is not None:
        kwargs["output_type"] = output_type

    return Agent(**kwargs)
