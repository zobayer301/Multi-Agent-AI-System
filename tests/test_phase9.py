"""
Comprehensive Unit & Integration Tests for Phase 9:
Testing, Evaluation, Benchmarking, Latency Profiling, and Edge Case Handling.
"""

import pytest
import asyncio
from src.evaluation import (
    AgentEvaluator,
    EvaluationMetrics,
    EvaluationReport,
    BenchmarkSummary,
    FieldValidationResult,
    estimate_tokens,
)
from src.agents.schemas import (
    ResearchPlan,
    AgentDelegation,
    ResearchOutput,
    AnalysisOutput,
    VerificationOutput,
    ReportOutput,
    ClaimVerification,
)
from src.workflows import ResearchWorkflow


def test_token_estimator():
    """Verify heuristic token counting handles various lengths and empty inputs."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0
    short_text = "Multi-agent systems using OpenAI Agents SDK."
    tokens = estimate_tokens(short_text)
    assert tokens > 5
    assert tokens < 25


def test_field_completeness_auditor():
    """Verify recursive field audit distinguishes full vs incomplete Pydantic models."""
    evaluator = AgentEvaluator()

    # Fully populated model
    valid_plan = ResearchPlan(
        topic="Solid State Electrolytes",
        domain="Materials Science",
        complexity_level="HIGH",
        key_objectives=["Measure conductivity", "Prevent dendrites"],
        focus_areas=["Sulfide-based", "Oxide-based"],
        delegation_strategy=AgentDelegation(
            research_agent="Find lab test papers",
            analysis_agent="Compare degradation rates",
            verification_agent="Audit cycle life claims",
            report_agent="Draft executive overview",
        ),
    )
    score, missing = evaluator.audit_model_completeness(valid_plan)
    assert score == 1.0
    assert len(missing) == 0

    # Incomplete model with empty strings and empty lists
    incomplete_plan = ResearchPlan(
        topic=" ",
        domain="",
        complexity_level="LOW",
        key_objectives=[],
        focus_areas=[],
        delegation_strategy=AgentDelegation(
            research_agent="",
            analysis_agent="Some task",
            verification_agent="",
            report_agent="",
        ),
    )
    incomplete_score, incomplete_missing = evaluator.audit_model_completeness(incomplete_plan)
    assert incomplete_score < 0.5
    assert "topic" in incomplete_missing
    assert "domain" in incomplete_missing
    assert "key_objectives" in incomplete_missing


def test_agent_artifact_validation():
    """Verify evaluate_agent_artifact audits individual agent outputs."""
    evaluator = AgentEvaluator()

    # Valid research output
    research = ResearchOutput(
        topic="Neuromorphic Computing",
        overview="Overview of spinnaker and memristive architectures.",
        key_findings=["Sub-milliwatt power consumption in spiking neural nets."],
        observed_trends=["Integration with CMOS edge chips."],
        unresolved_questions=["Thermal stability under sustained spike trains."],
        sources=["Nature Electronics (2024)"],
    )
    res = evaluator.evaluate_agent_artifact("Research_Agent", research)
    assert res.is_valid is True
    assert res.completeness_score == 1.0
    assert len(res.missing_or_empty_fields) == 0

    # Invalid artifact (None)
    res_none = evaluator.evaluate_agent_artifact("Research_Agent", None)
    assert res_none.is_valid is False
    assert res_none.completeness_score == 0.0

    # Unknown agent
    res_unknown = evaluator.evaluate_agent_artifact("Ghost_Agent", research)
    assert res_unknown.is_valid is False
    assert "No registered schema found" in res_unknown.error_message


@pytest.mark.anyio
async def test_workflow_evaluation_pipeline():
    """Verify AgentEvaluator executes a workflow and returns a comprehensive EvaluationReport."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.75)
    query = "Autonomous driving safety standards in North America and the EU."

    state, report = await evaluator.evaluate_workflow(workflow=workflow, query=query)

    assert state.status == "COMPLETED"
    assert report.query == query
    assert report.status == "COMPLETED"
    assert report.metrics.execution_time_seconds > 0.0
    assert report.metrics.total_tokens > 100
    assert report.metrics.schema_completeness_score >= 0.90
    assert report.metrics.overall_integrity_score >= 0.75
    assert report.metrics.quality_gate_passed is True
    assert len(report.agent_validations) == 5
    for name, val in report.agent_validations.items():
        assert val.is_valid is True


@pytest.mark.anyio
async def test_verification_accuracy_and_citation_metrics():
    """Verify evaluation metrics accurately capture claim ratios and citations."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.70)
    query = "Next-generation solar photovoltaic perovskite cell efficiencies."

    _, report = await evaluator.evaluate_workflow(workflow=workflow, query=query)

    # In the default simulation, 2 of 3 claims are VERIFIED, 1 is UNSUPPORTED
    assert report.metrics.verified_claims_ratio > 0.50
    assert report.metrics.unsupported_count >= 1
    assert report.metrics.contradiction_count == 0
    assert report.metrics.citation_count >= 3
    assert len(report.recommendations) >= 1


@pytest.mark.anyio
async def test_benchmark_suite():
    """Verify benchmark runs across multiple topics and produces aggregated statistics."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.70)
    test_queries = [
        "Quantum computing impact on post-quantum cryptography.",
        "Precision fermentation in scalable alternative protein synthesis.",
    ]

    summary = await evaluator.run_benchmark(workflow=workflow, queries=test_queries)

    assert summary.total_runs == 2
    assert summary.successful_runs == 2
    assert summary.success_rate == 1.0
    assert summary.average_latency_seconds > 0.0
    assert summary.average_integrity_score > 0.80
    assert summary.total_estimated_tokens > 200
    assert len(summary.reports) == 2


@pytest.mark.anyio
async def test_quality_gate_strict_threshold():
    """Verify high verification threshold triggers quality gate warning in metrics."""
    evaluator = AgentEvaluator()
    # Require 0.99 integrity (simulation yields 0.91)
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.99)
    query = "Fusion energy net positive power breakeven timeline."

    _, report = await evaluator.evaluate_workflow(workflow=workflow, query=query)

    assert report.metrics.quality_gate_passed is False
    assert any("failed the verification threshold" in rec for rec in report.recommendations)


@pytest.mark.anyio
async def test_edge_case_empty_and_whitespace_query():
    """Verify workflow and evaluator handle empty or whitespace query gracefully."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True)
    empty_query = "   "

    state, report = await evaluator.evaluate_workflow(workflow=workflow, query=empty_query)

    assert state.status == "COMPLETED"
    assert report.metrics.execution_time_seconds > 0.0
    assert report.metrics.schema_completeness_score > 0.80


@pytest.mark.anyio
async def test_edge_case_extremely_long_query():
    """Verify handling of an abnormally long query (5,000+ characters)."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True)
    long_query = "Assess AI scalability challenges in distributed networks. " * 100
    assert len(long_query) > 5000

    state, report = await evaluator.evaluate_workflow(workflow=workflow, query=long_query)

    assert state.status == "COMPLETED"
    assert report.metrics.estimated_input_tokens > 1000
    assert report.metrics.quality_gate_passed is True


@pytest.mark.anyio
async def test_edge_case_unicode_and_special_characters():
    """Verify queries containing Unicode, emojis, math symbols, and multilingual text."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True)
    special_query = "🔬 Quantum AI & Genomics 🧬: 日本語, العربية, Math: ∫e^(x^2)dx & Trade-offs (100% vs 50%)?!"

    state, report = await evaluator.evaluate_workflow(workflow=workflow, query=special_query)

    assert state.status == "COMPLETED"
    assert report.status == "COMPLETED"
    assert "🔬" in state.user_query or "Quantum AI" in state.user_query


@pytest.mark.anyio
async def test_concurrent_workflow_evaluation():
    """Verify multiple concurrent evaluation runs execute safely without SQLite collisions."""
    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True)

    queries = [
        "Concurrent Task Alpha: Microplastics filtration",
        "Concurrent Task Beta: Solid-state battery pack thermal design",
    ]

    tasks = [evaluator.evaluate_workflow(workflow=workflow, query=q) for q in queries]
    results = await asyncio.gather(*tasks)

    assert len(results) == 2
    for state, report in results:
        assert state.status == "COMPLETED"
        assert report.metrics.quality_gate_passed is True
