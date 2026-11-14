"""
Comprehensive Unit & Integration Tests for Phase 2:
Individual Agent Development & Pydantic Schema Validation.
"""

import pytest
import asyncio
from agents import Agent, Runner
from agents.testing import ScriptedModel, assistant_message

from src.agents import (
    create_research_agent,
    create_analysis_agent,
    create_verification_agent,
    create_report_agent,
    RESEARCH_AGENT_INSTRUCTIONS,
    ANALYSIS_AGENT_INSTRUCTIONS,
    VERIFICATION_AGENT_INSTRUCTIONS,
    REPORT_AGENT_INSTRUCTIONS,
    ResearchOutput,
    AnalysisOutput,
    ClaimVerification,
    VerificationOutput,
    ReportSection,
    ReportOutput,
)


def test_agent_instantiations():
    """Verify all 4 specialized agents instantiate with correct defaults."""
    researcher = create_research_agent()
    analyst = create_analysis_agent()
    verifier = create_verification_agent()
    reporter = create_report_agent()

    assert researcher.name == "Research_Agent"
    assert analyst.name == "Analysis_Agent"
    assert verifier.name == "Verification_Agent"
    assert reporter.name == "Report_Agent"

    assert researcher.instructions == RESEARCH_AGENT_INSTRUCTIONS
    assert analyst.instructions == ANALYSIS_AGENT_INSTRUCTIONS
    assert verifier.instructions == VERIFICATION_AGENT_INSTRUCTIONS
    assert reporter.instructions == REPORT_AGENT_INSTRUCTIONS


def test_agent_custom_models():
    """Verify custom model assignments for all agents."""
    custom_model = "gpt-4o"
    researcher = create_research_agent(model=custom_model, name="Custom_Research")
    analyst = create_analysis_agent(model=custom_model, name="Custom_Analysis")
    verifier = create_verification_agent(model=custom_model, name="Custom_Verification")
    reporter = create_report_agent(model=custom_model, name="Custom_Report")

    for agent, expected_name in [
        (researcher, "Custom_Research"),
        (analyst, "Custom_Analysis"),
        (verifier, "Custom_Verification"),
        (reporter, "Custom_Report"),
    ]:
        assert agent.model == custom_model
        assert agent.name == expected_name


def test_agent_structured_output_configuration():
    """Verify output_type parameter attaches correctly to each Agent instance."""
    researcher = create_research_agent(output_type=ResearchOutput)
    analyst = create_analysis_agent(output_type=AnalysisOutput)
    verifier = create_verification_agent(output_type=VerificationOutput)
    reporter = create_report_agent(output_type=ReportOutput)

    assert researcher.output_type is ResearchOutput
    assert analyst.output_type is AnalysisOutput
    assert verifier.output_type is VerificationOutput
    assert reporter.output_type is ReportOutput


def test_pydantic_schemas_validation():
    """Test data contract validation across all Pydantic schemas."""
    # 1. ResearchOutput
    res = ResearchOutput(
        topic="AI in Oncology",
        overview="Overview of neural net diagnostic tools",
        key_findings=["CNNs achieved 94% accuracy in melanoma detection"],
        observed_trends=["Edge AI in handheld scanners"],
        unresolved_questions=["Bias in non-Caucasian datasets"],
        sources=["https://pubmed.ncbi.nlm.nih.gov/example"],
    )
    assert res.topic == "AI in Oncology"
    assert len(res.key_findings) == 1

    # 2. AnalysisOutput
    ana = AnalysisOutput(
        topic="AI in Oncology",
        thematic_patterns=["Rapid clinical translation from academic labs"],
        contrasting_perspectives=["Radiologist pushback vs hospital cost savings"],
        opportunities=["Early cancer detection reducing treatment expenses"],
        limitations_and_risks=["High false-positive rate causing patient anxiety"],
        strategic_insights=["FDA cleared algorithms require localized validation"],
    )
    assert len(ana.thematic_patterns) == 1

    # 3. VerificationOutput
    ver = VerificationOutput(
        overall_integrity_score=0.92,
        evaluations=[
            ClaimVerification(
                claim="CNNs achieved 94% accuracy",
                status="VERIFIED",
                confidence_score=0.95,
                evidence_notes="Verified against clinical trial dataset.",
                source_citation="Nature Medicine 2024",
            )
        ],
        contradictions_flagged=[],
        unsupported_statements=["Cost savings estimate was modeled, not observed"],
        verdict_summary="High empirical rigor; add caveats on cost projections.",
    )
    assert ver.overall_integrity_score == 0.92
    assert ver.evaluations[0].status == "VERIFIED"

    # 4. ReportOutput
    rep = ReportOutput(
        title="Comprehensive Evaluation of AI in Oncology",
        executive_summary="Executive briefing on oncology imaging advancements.",
        sections=[
            ReportSection(
                heading="Diagnostic Performance",
                content="Deep learning architectures continue to outperform legacy baselines.",
            )
        ],
        key_takeaways=["Diagnostic accuracy reaches 94%", "Clinical adoption bottleneck is FDA approval"],
        conclusion="AI demonstrates decisive diagnostic advantages.",
        references=["Nature Medicine (2024)"],
    )
    assert rep.title == "Comprehensive Evaluation of AI in Oncology"
    assert len(rep.sections) == 1


@pytest.mark.anyio
async def test_all_agents_runner_execution():
    """Test that all 4 agents execute successfully through the official Runner using ScriptedModel."""
    agents_and_outputs = [
        ("Research_Agent", RESEARCH_AGENT_INSTRUCTIONS, "Research findings summary"),
        ("Analysis_Agent", ANALYSIS_AGENT_INSTRUCTIONS, "Analytical insights report"),
        ("Verification_Agent", VERIFICATION_AGENT_INSTRUCTIONS, "Verification audit: VERIFIED"),
        ("Report_Agent", REPORT_AGENT_INSTRUCTIONS, "# Final Research Report"),
    ]

    for name, instructions, simulated_text in agents_and_outputs:
        model = ScriptedModel(steps=[{"output": [assistant_message(simulated_text)]}])
        agent = Agent(name=name, instructions=instructions, model=model)

        result = await Runner.run(starting_agent=agent, input="Analyze test topic")
        assert result.final_output == simulated_text
