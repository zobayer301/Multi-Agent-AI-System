"""
Phase 9 Standalone Verification Script: Multi-Agent AI System Evaluation & Benchmarking.

Demonstrates:
1. End-to-end evaluation with quantitative performance metrics.
2. Individual agent structural schema compliance auditing.
3. Verification integrity, claim classification ratios, and citation density.
4. Token estimation modeling and stage latency breakdown.
5. Multi-topic automated benchmark suite execution with aggregated metrics.
"""

import asyncio
import json
from src.evaluation import AgentEvaluator
from src.workflows import ResearchWorkflow


async def main():
    print("=" * 80)
    print("   PHASE 9 VERIFICATION: MULTI-AGENT TESTING & EVALUATION FRAMEWORK")
    print("=" * 80)

    evaluator = AgentEvaluator()
    workflow = ResearchWorkflow(use_simulation=True, verification_threshold=0.75)

    # -------------------------------------------------------------
    # 1. Single Workflow Evaluation
    # -------------------------------------------------------------
    query = "Artificial Intelligence in Clinical Diagnostics Across Developing Nations"
    print("\n[1/3] Executing Evaluator on Target Topic:")
    print(f"      Query: '{query}'")

    state, report = await evaluator.evaluate_workflow(workflow=workflow, query=query)

    print("\n--- EVALUATION SUMMARY ---")
    print(f"  Session ID             : {report.session_id}")
    print(f"  Workflow Status        : {report.status}")
    print(f"  Total Latency          : {report.metrics.execution_time_seconds:.3f} s")
    print(f"  Estimated Input Tokens : {report.metrics.estimated_input_tokens}")
    print(f"  Estimated Output Tokens: {report.metrics.estimated_output_tokens}")
    print(f"  Total Estimated Tokens : {report.metrics.total_tokens}")

    print("\n--- AGENT SCHEMA CONFORMANCE AUDIT ---")
    for agent_name, validation in report.agent_validations.items():
        status_sym = "[OK]" if validation.is_valid and validation.completeness_score >= 0.95 else "[WARN]"
        print(f"  {status_sym} {agent_name:<20} | Completeness: {validation.completeness_score * 100:>5.1f}% | Missing: {len(validation.missing_or_empty_fields)}")

    print("\n--- VERIFICATION & EVIDENCE INTEGRITY ---")
    print(f"  Overall Integrity Score: {report.metrics.overall_integrity_score:.2f} (Threshold: {workflow.verification_threshold:.2f})")
    print(f"  Verified Claims Ratio  : {report.metrics.verified_claims_ratio * 100:.1f}%")
    print(f"  Unsupported Claims     : {report.metrics.unsupported_count}")
    print(f"  Contradictions Flagged : {report.metrics.contradiction_count}")
    print(f"  Unique Citations       : {report.metrics.citation_count}")
    print(f"  Quality Gate Result    : {'PASSED' if report.metrics.quality_gate_passed else 'FAILED'}")

    print("\n--- ESTIMATED STAGE LATENCIES ---")
    for stage, lat in report.metrics.stage_latencies.items():
        print(f"  - {stage:<25}: {lat:.3f} s")

    print("\n--- SYSTEM QUALITY RECOMMENDATIONS ---")
    for idx, rec in enumerate(report.recommendations, 1):
        print(f"  {idx}. {rec}")

    # -------------------------------------------------------------
    # 2. Multi-Topic Benchmark Suite
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[2/3] Executing Multi-Domain Benchmark Suite (3 Diverse Research Queries)...")
    benchmark_queries = [
        "Quantum Computing Impact on Post-Quantum Cryptography Architectures",
        "Perovskite Tandem Solar Cells Commercialization and Degradation Bottlenecks",
        "CRISPR In-Vivo Gene Editing Clinical Safety and Regulatory Pathways",
    ]

    summary = await evaluator.run_benchmark(workflow=workflow, queries=benchmark_queries)

    print("\n--- BENCHMARK AGGREGATED METRICS ---")
    print(f"  Total Runs Evaluated   : {summary.total_runs}")
    print(f"  Successful Runs        : {summary.successful_runs}")
    print(f"  Benchmark Success Rate : {summary.success_rate * 100:.1f}%")
    print(f"  Average Latency        : {summary.average_latency_seconds:.3f} s")
    print(f"  Min / Max Latency      : {summary.min_latency_seconds:.3f} s / {summary.max_latency_seconds:.3f} s")
    print(f"  Mean Integrity Score   : {summary.average_integrity_score:.2f}")
    print(f"  Mean Verified Ratio    : {summary.average_verified_ratio * 100:.1f}%")
    print(f"  Total Estimated Tokens : {summary.total_estimated_tokens}")

    # -------------------------------------------------------------
    # 3. Validation Assertions
    # -------------------------------------------------------------
    print("\n[3/3] Validating Phase 9 Integrity Gates:")
    assert report.status == "COMPLETED", "Workflow failed to complete."
    assert report.metrics.schema_completeness_score >= 0.90, "Schema completeness fell below 90%."
    assert report.metrics.quality_gate_passed is True, "Quality gate unexpectedly failed."
    assert summary.success_rate == 1.0, "Benchmark success rate did not achieve 100%."
    assert summary.total_runs == 3, "Benchmark did not execute all 3 test runs."
    print("  [SUCCESS] All Phase 9 assertions and quality criteria satisfied!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
