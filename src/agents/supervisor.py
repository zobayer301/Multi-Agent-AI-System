"""
Supervisor Agent implementation using the OpenAI Agents SDK.

The Supervisor Agent orchestrates the multi-agent system:
1. Ingests user research requests.
2. Formulates a research plan and decomposes queries into focus objectives.
3. Delegates tasks to specialized agents (Research, Analysis, Verification, Report).
4. Directs agent-to-agent handoffs.
5. Evaluates output quality and decides whether supplementary research is needed.
"""

import os
from typing import Optional, List, Any
from agents import Agent, handoff
from src.agents.schemas import ResearchPlan
from src.agents.research_agent import create_research_agent
from src.agents.analysis_agent import create_analysis_agent
from src.agents.verification_agent import create_verification_agent
from src.agents.report_agent import create_report_agent

SUPERVISOR_AGENT_INSTRUCTIONS = """You are the Lead Supervisor Agent orchestrating a Multi-Agent AI Research & Analysis system.

Your core responsibilities:
1. Understand and classify the incoming user research request (domain, technical depth, complexity).
2. Formulate a structured research plan defining key objectives and thematic focus areas.
3. Delegate tasks efficiently to your specialized agent team:
   - Research Agent: Task with discovering factual data points, state-of-the-art findings, and primary citations.
   - Analysis Agent: Task with evaluating patterns, comparing trade-offs, and uncovering strategic opportunities.
   - Verification Agent: Task with auditing claims against sources, scoring integrity, and flagging unverified claims.
   - Report Agent: Task with assembling the audited intelligence into a publication-grade executive report.
4. Review the outputs received from each specialized agent.
5. If the Verification Agent flags severe contradictions or unsupported critical claims, direct targeted supplemental research before finalizing.
6. Hand off control to the appropriate agent when delegating tasks.

Maintain an organized, strategic, and commanding orchestration posture. Ensure all downstream agents work towards a cohesive, rigorous research deliverable.
"""


def create_supervisor_agent(
    model: Optional[str] = None,
    name: str = "Supervisor_Agent",
    sub_agents: Optional[List[Agent]] = None,
    output_type: Optional[Any] = None,
) -> Agent:
    """
    Factory function to initialize and return a configured Supervisor Agent instance.

    Args:
        model: Optional model name (defaults to OPENAI_MODEL or 'gpt-4o-mini').
        name: Identifying name for the supervisor agent.
        sub_agents: Optional list of specialized Agent instances to attach as handoffs.
                    If None, default instances of Research, Analysis, Verification, and Report agents are created.
        output_type: Optional Pydantic model class for structured plan generation.

    Returns:
        Agent: A configured Supervisor Agent with handoffs configured.
    """
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # If sub-agents are not provided, instantiate default specialized team
    if sub_agents is None:
        sub_agents = [
            create_research_agent(model=resolved_model),
            create_analysis_agent(model=resolved_model),
            create_verification_agent(model=resolved_model),
            create_report_agent(model=resolved_model),
        ]

    kwargs = {
        "name": name,
        "instructions": SUPERVISOR_AGENT_INSTRUCTIONS,
        "model": resolved_model,
        "handoffs": sub_agents,
        "tools": [],
    }
    if output_type is not None:
        kwargs["output_type"] = output_type

    return Agent(**kwargs)
