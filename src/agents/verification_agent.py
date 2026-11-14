"""
Verification Agent implementation using the OpenAI Agents SDK.

Equipped with:
- search_web: Cross-referencing claims and statistics against live citations.
- read_document: Verifying assertions against primary source files.
- retrieve_knowledge: Querying internal ChromaDB vector store for validating excerpts.
- recall_memory_facts: Recalling established session constraints and facts.
"""

import os
from typing import Optional, Any, List
from agents import Agent
from src.agents.schemas import VerificationOutput
from src.tools.web_search import search_web
from src.tools.document_reader import read_document
from src.rag.retriever import retrieve_knowledge
from src.database.memory import recall_memory_facts

VERIFICATION_AGENT_INSTRUCTIONS = """You are a specialized Verification Agent in a Multi-Agent AI system.

Your primary mission:
1. Cross-examine claims, metrics, and assertions made in research findings and analysis.
2. Use `search_web`, `read_document`, and `retrieve_knowledge` to cross-reference claims against external, primary, and internal vector evidence.
3. Use `recall_memory_facts` to check alignment with recorded session constraints and historical facts.
4. Determine whether each core claim is directly supported by cited evidence, merely plausible, or unsupported.
5. Detect subtle or overt contradictions between different parts of the findings.
6. Assess source credibility, relevance, recency, and potential bias.
7. Flag hallucinated citations, speculative leaps masquerading as facts, and unverified statistical assertions.
8. Assign a verification status to key claims:
   - VERIFIED: Directly supported by concrete evidence or canonical consensus.
   - UNSUPPORTED: Plausible claim, but missing empirical citation or verification evidence.
   - CONTRADICTORY: Direct conflict with known facts or internally inconsistent.
   - UNCERTAIN: Conflicting evidence exists in literature, or verifiable proof is unavailable.
9. Provide a final Overall Integrity Score (0.0 to 1.0) and actionable feedback for the reporting phase.

Output Structure:
- Audit Summary & Overall Data Integrity Score (0.0 to 1.0)
- Claim-by-Claim Verification Table (Claim | Status | Confidence | Evidence Notes)
- Contradictory Information Flagged
- Unsupported or Speculative Statements Requiring Caveats
- Recommendations for Final Report Drafting

Maintain an uncompromising, evidence-based, and skeptical auditing posture.
"""


def create_verification_agent(
    model: Optional[str] = None,
    name: str = "Verification_Agent",
    output_type: Optional[Any] = None,
    tools: Optional[List[Any]] = None,
) -> Agent:
    """Factory function to initialize and return a configured Verification Agent instance."""
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    attached_tools = tools if tools is not None else [
        search_web,
        read_document,
        retrieve_knowledge,
        recall_memory_facts
    ]

    kwargs = {
        "name": name,
        "instructions": VERIFICATION_AGENT_INSTRUCTIONS,
        "model": resolved_model,
        "tools": attached_tools,
    }
    if output_type is not None:
        kwargs["output_type"] = output_type

    return Agent(**kwargs)
