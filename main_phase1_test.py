"""
Phase 1 Test Runner: Interactive & Diagnostic Script for the Research Agent.

This script demonstrates:
1. Secure loading of environment variables via python-dotenv.
2. Instantiation of the Research Agent using OpenAI Agents SDK.
3. Execution lifecycle using Runner.run (Live API or Official Scripted Simulation).
4. Diagnostic checks for API keys and configuration.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

from agents import Runner, Agent
from agents.testing import ScriptedModel, assistant_message
from src.agents.research_agent import create_research_agent, RESEARCH_AGENT_INSTRUCTIONS


MOCK_RESEARCH_OUTPUT = """### 1. Topic Overview & Background
Recent advancements in Multi-Agent AI Systems (2024–2026) mark a transition from monolithic large language models toward collaborative, specialized agent collectives. These systems leverage hierarchical orchestration, specialized tool use, and structured communication protocols.

### 2. Key Research Findings
- **Hierarchical & Orchestrated Swarms**: Systems employing supervisor-worker topologies demonstrate significantly higher task-completion rates on complex reasoning benchmarks compared to single-agent prompts.
- **Formalized Communication & Tool Calling**: Frameworks like the OpenAI Agents SDK and MCP (Model Context Protocol) have standardized tool exposure, streaming events, and agent-to-agent handoffs.
- **Verification & Self-Correction**: Integrating explicit Verification Agents reduces hallucination rates by up to 40% through iterative cross-examination against retrieved sources.

### 3. Observed Trends & Practical Implications
- Autonomous workflows are increasingly integrated into enterprise software stacks (FastAPI microservices, vector search with ChromaDB/pgvector).
- Dynamic handoffs allow smooth transitions between specialized domains (e.g., Researcher -> Analyst -> Verifier -> Reporter).

### 4. Unresolved Challenges
- Cascading error propagation when an upstream agent generates subtle factual errors.
- Token consumption and latency trade-offs in multi-turn multi-agent loops.

### 5. Sources and Reference Pointers
- OpenAI Agents SDK Documentation (2025)
- Anthropic Model Context Protocol (MCP) Standards (2024-2025)
- Multi-Agent Systems in Healthcare & Enterprise Workflows (IEEE / ACM Surveys, 2024-2026)
"""


async def run_research_query(query: str) -> None:
    """Execute a research query using the Research Agent and the Runner."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    print("=" * 70)
    print("Multi-Agent AI System - Phase 1: Research Agent Verification")
    print("=" * 70)
    print(f"Target Model: {model_name}")
    has_api_key = len(api_key) > 10 and not api_key.startswith("your_")
    print(f"API Key Status: {'Configured (Live OpenAI API)' if has_api_key else 'Not Configured (Running SDK Offline Simulation)'}")
    print("-" * 70)

    if has_api_key:
        research_agent = create_research_agent(model=model_name)
        print(f"[✓] Initialized Live Agent: '{research_agent.name}' (Model: {research_agent.model})")
    else:
        # Use official OpenAI Agents SDK ScriptedModel for offline execution
        simulated_model = ScriptedModel(
            steps=[{"output": [assistant_message(MOCK_RESEARCH_OUTPUT)]}]
        )
        research_agent = Agent(
            name="Research_Agent",
            instructions=RESEARCH_AGENT_INSTRUCTIONS,
            model=simulated_model,
        )
        print(f"[✓] Initialized SDK Simulation Agent: '{research_agent.name}'")

    print(f"[✓] Instructions Length: {len(research_agent.instructions)} characters")
    print("-" * 70)
    print(f"Executing Research Query:\n\"{query}\"\n")
    print("Running agent via Runner.run()...")

    try:
        result = await Runner.run(
            starting_agent=research_agent,
            input=query,
        )
        print("\n" + "=" * 70)
        print("RESEARCH AGENT OUTPUT:")
        print("=" * 70)
        print(result.final_output)
        print("=" * 70)
        print("[✓] Agent run completed successfully via Runner.run().")
        if not has_api_key:
            print("\n[TIP] To switch to live OpenAI API execution, add your actual API key")
            print("      to the .env file: OPENAI_API_KEY=sk-proj-...")
    except Exception as e:
        print(f"\n[✗] Execution Error: {type(e).__name__}: {e}")


def main() -> None:
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What are the key advancements in Multi-Agent AI systems in 2024-2026?"
    )
    asyncio.run(run_research_query(query))


if __name__ == "__main__":
    main()
