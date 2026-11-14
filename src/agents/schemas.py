"""
Pydantic Schemas for Multi-Agent Data Contracts & Workflow State.

Defines structured data models for:
- AgentDelegation: Concrete task assignments for all specialized agents.
- ResearchPlan: Task classification, scope decomposition, and delegation.
- ResearchOutput: Facts, findings, and initial sources.
- AnalysisOutput: Deep patterns, comparative viewpoints, and strategic insights.
- ClaimVerification: Claim-level assessment.
- VerificationOutput: Claim-level validation, contradictory checks, and confidence ratings.
- ReportSection & ReportOutput: Final synthesized research report.
- WorkflowState: End-to-end orchestration state across multi-agent pipelines.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AgentDelegation(BaseModel):
    """Task delegation mapping assigning specific responsibilities to specialized agents."""
    research_agent: str = Field(description="Task and focus assigned to Research Agent.")
    analysis_agent: str = Field(description="Task and focus assigned to Analysis Agent.")
    verification_agent: str = Field(description="Task and focus assigned to Verification Agent.")
    report_agent: str = Field(description="Task and focus assigned to Report Agent.")


class ResearchPlan(BaseModel):
    """Structured data contract for the Supervisor Agent's planning phase."""
    topic: str = Field(description="The primary research query or topic.")
    domain: str = Field(description="Domain classification (e.g., Healthcare, AI/ML, Economics, Energy).")
    complexity_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="MEDIUM", description="Assessed research complexity."
    )
    key_objectives: List[str] = Field(description="Core questions that the research workflow must answer.")
    focus_areas: List[str] = Field(description="Key technical or thematic focus areas to prioritize.")
    delegation_strategy: AgentDelegation = Field(
        description="Structured task delegation mapping assigning responsibilities to specialized agents."
    )


class ResearchOutput(BaseModel):
    """Structured data contract for the Research Agent."""
    topic: str = Field(description="The primary research topic investigated.")
    overview: str = Field(description="High-level summary of the topic and context.")
    key_findings: List[str] = Field(description="List of primary factual findings and data points.")
    observed_trends: List[str] = Field(description="Emerging developments and practical implications.")
    unresolved_questions: List[str] = Field(description="Gaps in current knowledge or areas needing deeper investigation.")
    sources: List[str] = Field(default_factory=list, description="References, studies, or source URLs identified.")


class MetricComparison(BaseModel):
    """Comparative quantitative evaluation for ML models, algorithms, or benchmarks."""
    algorithm_or_model: str = Field(description="Name of the algorithm or model compared.")
    accuracy: Optional[float] = Field(default=None, description="Reported classification accuracy (0.0 to 1.0).")
    precision: Optional[float] = Field(default=None, description="Reported precision score.")
    recall: Optional[float] = Field(default=None, description="Reported recall / sensitivity score.")
    f1_score: Optional[float] = Field(default=None, description="F1-score harmonic mean.")
    roc_auc: Optional[float] = Field(default=None, description="Area under the ROC curve.")
    dataset_characteristics: Optional[str] = Field(default=None, description="Dataset sample size, cohort balance, or benchmarks.")
    limitations: Optional[str] = Field(default=None, description="Specific analytical limitations or failure modes noted.")


class AnalysisOutput(BaseModel):
    """Structured data contract for the Analysis Agent."""
    topic: str = Field(description="The topic analyzed.")
    thematic_patterns: List[str] = Field(description="Underlying patterns and inter-relationships identified across findings.")
    contrasting_perspectives: List[str] = Field(description="Divergent viewpoints, trade-offs, or competing paradigms.")
    opportunities: List[str] = Field(description="Strategic, economic, or technological opportunities.")
    limitations_and_risks: List[str] = Field(description="Bottlenecks, challenges, and risk factors.")
    strategic_insights: List[str] = Field(description="Actionable analytical takeaways derived from the data.")
    performance_comparisons: List[MetricComparison] = Field(default_factory=list, description="Quantitative model and algorithmic metric benchmarks (Accuracy, Precision, Recall, F1, ROC-AUC).")


class ClaimVerification(BaseModel):
    """Verification assessment for an individual claim."""
    claim: str = Field(description="The specific assertion or factual claim being evaluated.")
    status: Literal["VERIFIED", "PARTIALLY_VERIFIED", "UNSUPPORTED", "CONTRADICTORY", "UNCERTAIN", "Verified", "Partially Verified", "Unsupported", "Contradicted"] = Field(
        description="The verification status of the claim."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence rating between 0.0 (no confidence) and 1.0 (absolute certainty)."
    )
    evidence_notes: str = Field(description="Reasoning and evidence supporting the assessment.")
    source_citation: Optional[str] = Field(default=None, description="Direct citation or source reference if available.")


class VerificationOutput(BaseModel):
    """Structured data contract for the Verification Agent."""
    overall_integrity_score: float = Field(
        ge=0.0, le=1.0, description="Composite trustworthiness score of the research data (0.0 to 1.0)."
    )
    evaluations: List[ClaimVerification] = Field(description="Individual claim assessments.")
    contradictions_flagged: List[str] = Field(description="Any conflicting statements or incompatible claims.")
    unsupported_statements: List[str] = Field(description="Assertions that lack empirical or citation support.")
    verdict_summary: str = Field(description="Concluding verification summary and recommendation for reporting.")


class ReportSection(BaseModel):
    """A single coherent section within the final report."""
    heading: str = Field(description="Section title.")
    content: str = Field(description="Section body formatted in structured Markdown.")


class ReportOutput(BaseModel):
    """Structured data contract for the Report Agent."""
    title: str = Field(description="Title of the research report.")
    executive_summary: str = Field(description="Concise executive briefing summarizing the core conclusions.")
    sections: List[ReportSection] = Field(description="Ordered topical sections of the report.")
    key_takeaways: List[str] = Field(description="High-impact bullet points summarizing essential outcomes.")
    conclusion: str = Field(description="Strategic conclusion and future outlook.")
    references: List[str] = Field(description="Formal bibliography and source references.")


class WorkflowState(BaseModel):
    """Shared execution state tracking multi-agent pipeline progress."""
    user_query: str = Field(description="Original user research request.")
    plan: Optional[ResearchPlan] = Field(default=None, description="Strategic plan generated by Supervisor Agent.")
    research: Optional[ResearchOutput] = Field(default=None, description="Output from Research Agent.")
    analysis: Optional[AnalysisOutput] = Field(default=None, description="Output from Analysis Agent.")
    verification: Optional[VerificationOutput] = Field(default=None, description="Output from Verification Agent.")
    report: Optional[ReportOutput] = Field(default=None, description="Final output from Report Agent.")
    iteration_count: int = Field(default=0, description="Number of feedback/refinement loops executed.")
    status: Literal["INITIALIZED", "PLANNED", "RESEARCHING", "ANALYZING", "VERIFYING", "REVISE_RESEARCH", "COMPLETED", "FAILED"] = Field(
        default="INITIALIZED", description="Current lifecycle state of the research workflow."
    )
    execution_logs: List[str] = Field(default_factory=list, description="Step-by-step audit logs of workflow operations.")
