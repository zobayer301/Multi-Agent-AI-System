"""
Unit tests for Phase 1: Research Agent Initialization and Architecture.
"""

import os
import pytest
from agents import Agent
from src.agents import create_research_agent, RESEARCH_AGENT_INSTRUCTIONS


def test_research_agent_creation():
    """Test that create_research_agent creates a valid Agent instance with correct properties."""
    agent = create_research_agent(model="gpt-4o-mini")

    assert isinstance(agent, Agent)
    assert agent.name == "Research_Agent"
    assert agent.model == "gpt-4o-mini"
    assert agent.instructions == RESEARCH_AGENT_INSTRUCTIONS
    assert len(agent.instructions) > 100
    assert "Research Agent" in agent.instructions


def test_research_agent_custom_name_and_model():
    """Test configuring the agent with custom parameters."""
    agent = create_research_agent(model="gpt-4o", name="Custom_Researcher")

    assert agent.name == "Custom_Researcher"
    assert agent.model == "gpt-4o"


def test_research_agent_env_model_fallback(monkeypatch):
    """Test that agent falls back to OPENAI_MODEL environment variable if not provided."""
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
    agent = create_research_agent()

    assert agent.model == "gpt-4o-2024-08-06"
