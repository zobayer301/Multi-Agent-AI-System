"""
Agents package exposing specialized multi-agent components and data contracts.
"""

from .schemas import (
    AgentDelegation,
    ResearchPlan,
    ResearchOutput,
    AnalysisOutput,
    ClaimVerification,
    MetricComparison,
    VerificationOutput,
    ReportSection,
    ReportOutput,
    WorkflowState,
)
from .supervisor import create_supervisor_agent, SUPERVISOR_AGENT_INSTRUCTIONS
from .research_agent import create_research_agent, RESEARCH_AGENT_INSTRUCTIONS
from .analysis_agent import create_analysis_agent, ANALYSIS_AGENT_INSTRUCTIONS
from .verification_agent import create_verification_agent, VERIFICATION_AGENT_INSTRUCTIONS
from .report_agent import create_report_agent, REPORT_AGENT_INSTRUCTIONS

__all__ = [
    # Schemas
    "AgentDelegation",
    "ResearchPlan",
    "ResearchOutput",
    "AnalysisOutput",
    "ClaimVerification",
    "VerificationOutput",
    "ReportSection",
    "ReportOutput",
    "WorkflowState",
    # Agents
    "create_supervisor_agent",
    "create_research_agent",
    "create_analysis_agent",
    "create_verification_agent",
    "create_report_agent",
    # Instructions
    "SUPERVISOR_AGENT_INSTRUCTIONS",
    "RESEARCH_AGENT_INSTRUCTIONS",
    "ANALYSIS_AGENT_INSTRUCTIONS",
    "VERIFICATION_AGENT_INSTRUCTIONS",
    "REPORT_AGENT_INSTRUCTIONS",
]
