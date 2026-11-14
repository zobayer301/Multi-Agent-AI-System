"""
Phase 3 Test Runner: Interactive Multi-Agent Orchestration & Workflow Execution.

Demonstrates the end-to-end multi-agent orchestration pipeline:
Supervisor Agent -> Research Agent -> Analysis Agent -> Verification Agent -> Report Agent

Supports both live OpenAI API execution and offline SDK simulation mode.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

from src.workflows import ResearchWorkflow


async def run_orchestration(topic: str) -> None:
    """Execute the full multi-agent orchestration workflow and display formatted outputs."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    has_api_key = len(api_key) > 10 and not api_key.startswith("your_")

    print("=" * 80)
    print("Multi-Agent AI System - Phase 3: Multi-Agent Orchestration Pipeline")
    print("=" * 80)
    print(f"Target Query: \"{topic}\"")
    print(f"Target Model: {model_name}")
    print(f"Execution Engine: {'Live OpenAI API' if has_api_key else 'SDK ScriptedModel Simulation'}")
    print("=" * 80 + "\n")

    workflow = ResearchWorkflow(model=model_name, verification_threshold=0.70)
    state = await workflow.run(user_query=topic)

    # 1. Display Supervisor Plan
    print("\n" + "=" * 80)
    print("STAGE 1: SUPERVISOR AGENT RESEARCH PLAN")
    print("=" * 80)
    print(f"Domain: {state.plan.domain} | Complexity: {state.plan.complexity_level}")
    print("\nKey Objectives:")
    for i, obj in enumerate(state.plan.key_objectives, 1):
        print(f"  {i}. {obj}")
    print("\nFocus Areas:")
    for area in state.plan.focus_areas:
        print(f"  • {area}")
    print("\nDelegation Strategy:")
    print(f"  • Research Agent:     {state.plan.delegation_strategy.research_agent}")
    print(f"  • Analysis Agent:     {state.plan.delegation_strategy.analysis_agent}")
    print(f"  • Verification Agent: {state.plan.delegation_strategy.verification_agent}")
    print(f"  • Report Agent:       {state.plan.delegation_strategy.report_agent}")

    # 2. Display Research Output
    print("\n" + "=" * 80)
    print("STAGE 2: RESEARCH AGENT FINDINGS & CITATIONS")
    print("=" * 80)
    print(f"Overview: {state.research.overview}\n")
    print("Key Findings:")
    for finding in state.research.key_findings:
        print(f"  [+] {finding}")
    print("\nSources & References:")
    for src in state.research.sources:
        print(f"  - {src}")

    # 3. Display Analysis Output
    print("\n" + "=" * 80)
    print("STAGE 3: ANALYSIS AGENT SYNTHESIS & INSIGHTS")
    print("=" * 80)
    print("Thematic Patterns:")
    for pattern in state.analysis.thematic_patterns:
        print(f"  [*] {pattern}")
    print("\nStrategic Insights:")
    for insight in state.analysis.strategic_insights:
        print(f"  [>] {insight}")

    # 4. Display Verification Output
    print("\n" + "=" * 80)
    print("STAGE 4: VERIFICATION AGENT AUDIT & QUALITY GATE")
    print("=" * 80)
    print(f"Overall Data Integrity Score: {state.verification.overall_integrity_score:.2f} / 1.00")
    print(f"Audit Verdict: {state.verification.verdict_summary}\n")
    print("Claim Evaluations:")
    for ev in state.verification.evaluations:
        status_tag = f"[{ev.status}]"
        print(f"  {status_tag:<15} Confidence: {ev.confidence_score:.2f} | Claim: \"{ev.claim}\"")
        if ev.source_citation:
            print(f"                  Citation: {ev.source_citation}")

    # 5. Display Final Report
    print("\n" + "=" * 80)
    print("STAGE 5: REPORT AGENT FINAL SYNTHESIZED DELIVERABLE")
    print("=" * 80)
    print(f"TITLE: {state.report.title}\n")
    print("EXECUTIVE SUMMARY:")
    print(state.report.executive_summary + "\n")
    for section in state.report.sections:
        print(f"\n--- {section.heading} ---")
        print(section.content)
    print("\nKEY TAKEAWAYS:")
    for takeaway in state.report.key_takeaways:
        print(f"  ✔ {takeaway}")
    print("\nREFERENCES:")
    for ref in state.report.references:
        print(f"  [Ref] {ref}")

    # Workflow Logs Summary
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTION LOGS AUDIT TRAIL:")
    print("=" * 80)
    for log in state.execution_logs:
        print(f"  {log}")
    print("=" * 80)
    print(f"Workflow Status: {state.status} | Total Iterations: {state.iteration_count}")
    print("=" * 80)


def main() -> None:
    topic = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Analyze the impact of artificial intelligence on the healthcare industry in developing countries."
    )
    asyncio.run(run_orchestration(topic))


if __name__ == "__main__":
    main()
