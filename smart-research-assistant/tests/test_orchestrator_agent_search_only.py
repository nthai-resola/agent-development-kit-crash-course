import pytest
from unittest.mock import MagicMock
from agents.orchestrator_agent import OrchestratorAgent
from models.enums import ProcessingMode
from config import Config

@pytest.fixture
def orchestrator():
    orc = OrchestratorAgent()
    # Register mock agents to test skipping logic
    orc.register_agent(MagicMock(), "search")
    orc.register_agent(MagicMock(), "verification")
    orc.register_agent(MagicMock(), "summary")
    orc.register_agent(MagicMock(), "analysis")
    return orc

def test_search_only_mode_simple_query(orchestrator, monkeypatch):
    monkeypatch.setattr(Config, "PROCESSING_MODE", "search-only")
    query = "What is the capital of France?"
    required_agents, skipped_agents = orchestrator._analyze_query_requirements(query)
    assert required_agents == ["search"]
    assert "verification" in skipped_agents
    assert "summary" in skipped_agents
    assert "analysis" in skipped_agents

def test_search_only_mode_explicit_analysis(orchestrator, monkeypatch):
    monkeypatch.setattr(Config, "PROCESSING_MODE", "search-only")
    query = "analyze the impact of climate change"
    required_agents, skipped_agents = orchestrator._analyze_query_requirements(query)
    assert "search" in required_agents
    assert "analysis" in required_agents
    assert "verification" in skipped_agents
    assert "summary" in skipped_agents

def test_auto_detect_mode_strong_summary_intent(orchestrator, monkeypatch):
    monkeypatch.setattr(Config, "PROCESSING_MODE", "auto-detect")
    query = "give me a summary of the latest AI research"
    required_agents, skipped_agents = orchestrator._analyze_query_requirements(query)
    assert "search" in required_agents
    assert "summary" in required_agents
    assert "verification" in skipped_agents
    assert "analysis" in skipped_agents

def test_full_processing_mode(orchestrator, monkeypatch):
    monkeypatch.setattr(Config, "PROCESSING_MODE", "full-processing")
    query = "tell me about space exploration"
    required_agents, skipped_agents = orchestrator._analyze_query_requirements(query)
    assert "search" in required_agents
    assert "verification" in required_agents
    assert "summary" in required_agents
    assert "analysis" in required_agents
    assert skipped_agents == [] 