"""
Comprehensive Unit & Integration Tests for Phase 3:
Multi-Agent Orchestration, Supervisor Agent, and Hierarchical Workflows.
"""

import pytest
import asyncio
from agents import Agent, Runner

from src.agents import (
    create_supervisor_agent,
    create_research_agent,
    create_analysis_agent,
    create_verification_agent,
    create_report_agent,
    SUPERVISOR_AGENT_INSTRUCTIONS,
    AgentDelegation,
    ResearchPlan,
    WorkflowState,
)
from src.workflows import ResearchWorkflow


def test_supervisor_agent_instantiation():
    """Verify Supervisor Agent initializes with appropriate instructions and 4 default handoffs."""
    supervisor = create_supervisor_agent()

    assert supervisor.name == "Supervisor_Agent"
    assert supervisor.instructions == SUPERVISOR_AGENT_INSTRUCTIONS
    assert supervisor.handoffs is not None
    assert len(supervisor.handoffs) == 4

    sub_agent_names = {agent.name for agent in supervisor.handoffs}
    assert "Research_Agent" in sub_agent_names
    assert "Analysis_Agent" in sub_agent_names
    assert "Verification_Agent" in sub_agent_names
    assert "Report_Agent" in sub_agent_names


def test_supervisor_custom_handoffs():
    """Verify custom sub-agents can be attached to Supervisor Agent."""
    custom_sub = [
        create_research_agent(name="Custom_Worker_1"),
        create_analysis_agent(name="Custom_Worker_2"),
    ]
    supervisor = create_supervisor_agent(name="Lead_Supervisor", sub_agents=custom_sub)

    assert supervisor.name == "Lead_Supervisor"
    assert len(supervisor.handoffs) == 2
    assert supervisor.handoffs[0].name == "Custom_Worker_1"
    assert supervisor.handoffs[1].name == "Custom_Worker_2"


def test_research_plan_schema():
    """Verify ResearchPlan Pydantic validation and delegation mapping."""
    plan = ResearchPlan(
        topic="Solid State Battery Chemistries",
        domain="Materials Science & Energy",
        complexity_level="HIGH",
        key_objectives=["Identify energy density limits", "Analyze dendrite suppression"],
        focus_areas=["Sulfide electrolytes", "Silicon anodes"],
        delegation_strategy=AgentDelegation(
            research_agent="Find peer-reviewed energy density numbers.",
            analysis_agent="Evaluate manufacturing cost bottlenecks.",
            verification_agent="Cross-examine cycle-life claims.",
            report_agent="Draft publication briefing.",
        ),
    )

    assert plan.complexity_level == "HIGH"
    assert len(plan.key_objectives) == 2
    assert plan.delegation_strategy.research_agent == "Find peer-reviewed energy density numbers."


def test_workflow_state_initialization_and_logging():
    """Verify WorkflowState lifecycle tracking and logging."""
    state = WorkflowState(user_query="Quantum Computing in Drug Discovery")

    assert state.status == "INITIALIZED"
    assert state.iteration_count == 0
    assert len(state.execution_logs) == 0

    state.execution_logs.append("Step 1 done")
    state.status = "PLANNED"
    assert state.status == "PLANNED"
    assert len(state.execution_logs) == 1


@pytest.mark.anyio
async def test_research_workflow_full_pipeline():
    """
    Test end-to-end execution of the hierarchical multi-agent workflow:
    Supervisor -> Research -> Analysis -> Verification -> Report.
    """
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.70)
    query = "Analyze the impact of artificial intelligence on healthcare in developing countries."

    state = await workflow.run(user_query=query)

    # 1. Verify pipeline completion
    assert state.status == "COMPLETED"
    assert len(state.execution_logs) >= 5

    # 2. Verify all intermediate artifacts are populated and strongly typed
    assert state.plan is not None
    assert isinstance(state.plan, ResearchPlan)
    assert len(state.plan.key_objectives) > 0

    assert state.research is not None
    assert len(state.research.key_findings) > 0
    assert len(state.research.sources) > 0

    assert state.analysis is not None
    assert len(state.analysis.thematic_patterns) > 0
    assert len(state.analysis.strategic_insights) > 0

    assert state.verification is not None
    assert 0.0 <= state.verification.overall_integrity_score <= 1.0
    assert len(state.verification.evaluations) > 0

    assert state.report is not None
    assert len(state.report.title) > 0
    assert len(state.report.sections) >= 3
    assert len(state.report.references) > 0


@pytest.mark.anyio
async def test_workflow_quality_gate_trigger():
    """Verify that quality gate identifies low integrity score and logs revision request."""
    # Setting threshold higher than the simulated score (0.91) triggers revision loop
    strict_workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.98, max_iterations=1)
    state = await strict_workflow.run("Test query for quality gate")

    # Verify quality gate was triggered in logs
    assert state.iteration_count == 1
    assert any("Quality Gate Triggered" in log for log in state.execution_logs)
