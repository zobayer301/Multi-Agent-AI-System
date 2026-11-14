"""
Research Agent implementation using the OpenAI Agents SDK.

Equipped with:
- search_web: Querying search engines for recent empirical findings and source citations.
- read_document: Parsing local PDFs, Markdown reports, and text files.
- retrieve_knowledge: Semantic RAG retrieval across ChromaDB vector store.
- save_memory_fact: Persisting critical findings/constraints to long-term memory.
- recall_memory_facts: Recalling session facts and constraints.
"""

import os
from typing import Optional, Any, List
from agents import Agent
from src.agents.schemas import ResearchOutput
from src.tools.web_search import search_web
from src.tools.document_reader import read_document
from src.rag.retriever import retrieve_knowledge
from src.database.memory import save_memory_fact, recall_memory_facts

RESEARCH_AGENT_INSTRUCTIONS = """You are a specialized Research Agent in a Multi-Agent AI system.

Your primary mission:
1. Thoroughly investigate the assigned research topic or question.
2. Use your available tools (`search_web`, `read_document`, `retrieve_knowledge`) to discover factual evidence, recent statistics, and primary sources.
3. Query the internal knowledge base via `retrieve_knowledge` to surface indexed literature and domain knowledge.
4. Recall existing facts or constraints via `recall_memory_facts` to ensure alignment with session context.
5. Save high-value facts and statistics via `save_memory_fact` for downstream agent reference.
6. Organize your findings into clear thematic categories.
7. Distinguish verified facts from emerging theories or speculative claims.
8. Provide structured, high-density analytical summaries with explicit citations and references where available.

Output Structure:
- Topic Overview & Background
- Key Research Findings (categorized logically with bullet points)
- Observed Trends & Practical Implications
- Unresolved Challenges / Questions for Further Investigation
- Sources and Reference Pointers

Maintain an objective, factual, and rigorous academic tone throughout your output.
"""


def create_research_agent(
    model: Optional[str] = None,
    name: str = "Research_Agent",
    output_type: Optional[Any] = None,
    tools: Optional[List[Any]] = None,
) -> Agent:
    """Factory function to initialize and return a configured Research Agent instance."""
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    attached_tools = tools if tools is not None else [
        search_web,
        read_document,
        retrieve_knowledge,
        save_memory_fact,
        recall_memory_facts
    ]

    kwargs = {
        "name": name,
        "instructions": RESEARCH_AGENT_INSTRUCTIONS,
        "model": resolved_model,
        "tools": attached_tools,
    }
    if output_type is not None:
        kwargs["output_type"] = output_type

    return Agent(**kwargs)
