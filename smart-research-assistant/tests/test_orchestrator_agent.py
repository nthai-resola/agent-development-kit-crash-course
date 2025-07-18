"""
Tests for the Orchestrator Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Import will be resolved at runtime when used as a package
try:
    from ..agents.orchestrator_agent import OrchestratorAgent
    from ..agents.base_agent import BaseResearchAgent
    from ..models.data_models import ResearchSession
    from ..storage.storage_provider import StorageProvider
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.base_agent import BaseResearchAgent
    from models.data_models import ResearchSession
    from storage.storage_provider import StorageProvider


class MockStorageProvider(StorageProvider):
    """Mock storage provider for testing."""
    
    def __init__(self):
        self.sessions = {}
    
    async def save_session(self, session: ResearchSession) -> bool:
        self.sessions[session.session_id] = session
        return True
    
    async def load_session(self, session_id: str) -> ResearchSession:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def list_sessions(self):
        return [{"session_id": sid, "topic": session.topic} 
                for sid, session in self.sessions.items()]
    
    async def session_exists(self, session_id: str) -> bool:
        return session_id in self.sessions


class MockAgent(BaseResearchAgent):
    """Mock specialized agent for testing."""
    
    def __init__(self, name: str, model: str = "test-model"):
        super().__init__(model, name)
        self.process_calls = []
    
    def _initialize_agent(self):
        self.agent = {"mock": True}
    
    async def process(self, query: str, context=None):
        self.process_calls.append(query)
        return {
            "success": True,
            "content": f"Mock {self.name} result for: {query}",
            "confidence": 0.8,
            "verified": True,
            "metadata": {"agent": self.name}
        }


@pytest.fixture
def mock_storage():
    return MockStorageProvider()


@pytest.fixture
def orchestrator(mock_storage):
    return OrchestratorAgent(model="test-model", storage_provider=mock_storage)


@pytest.fixture
def orchestrator_with_agents(orchestrator):
    # Register mock agents
    search_agent = MockAgent("SearchAgent")
    verification_agent = MockAgent("VerificationAgent")
    summary_agent = MockAgent("SummaryAgent")
    analysis_agent = MockAgent("AnalysisAgent")
    
    orchestrator.register_agent("search", search_agent)
    orchestrator.register_agent("verification", verification_agent)
    orchestrator.register_agent("summary", summary_agent)
    orchestrator.register_agent("analysis", analysis_agent)
    
    return orchestrator


class TestOrchestratorAgent:
    """Test cases for the Orchestrator Agent."""
    
    def test_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.name == "OrchestratorAgent"
        assert orchestrator.model == "test-model"
        assert orchestrator.current_session is None
        assert len(orchestrator.specialized_agents) == 0
        assert orchestrator.agent is not None
    
    def test_agent_registration(self, orchestrator):
        """Test agent registration functionality."""
        mock_agent = MockAgent("TestAgent")
        orchestrator.register_agent("search", mock_agent)
        
        assert "search" in orchestrator.specialized_agents
        assert orchestrator.specialized_agents["search"] == mock_agent
        
        registered = orchestrator.get_registered_agents()
        assert registered["search"] == "TestAgent"
    
    @pytest.mark.asyncio
    async def test_session_creation(self, orchestrator):
        """Test session creation."""
        session_id = await orchestrator.create_session("Test Topic")
        
        assert session_id is not None
        assert orchestrator.current_session is not None
        assert orchestrator.current_session.session_id == session_id
        assert orchestrator.current_session.topic == "Test Topic"
    
    @pytest.mark.asyncio
    async def test_session_loading(self, orchestrator, mock_storage):
        """Test session loading."""
        # Create a session first
        session_id = await orchestrator.create_session("Test Topic")
        
        # Clear current session
        orchestrator.current_session = None
        
        # Load the session
        success = await orchestrator.load_session(session_id)
        
        assert success is True
        assert orchestrator.current_session is not None
        assert orchestrator.current_session.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_session_saving(self, orchestrator):
        """Test session saving."""
        # Create a session
        await orchestrator.create_session("Test Topic")
        
        # Save the session
        success = await orchestrator.save_session()
        
        assert success is True
    
    def test_query_analysis(self, orchestrator):
        """Test query requirement analysis."""
        # Test search-only query
        agents = orchestrator._analyze_query_requirements("What is machine learning?")
        assert "search" in agents
        
        # Test query requiring verification
        agents = orchestrator._analyze_query_requirements("Is this fact accurate?")
        assert "search" in agents
        assert "verification" in agents
        
        # Test query requiring summary
        agents = orchestrator._analyze_query_requirements("Summarize the key points")
        assert "search" in agents
        assert "summary" in agents
        
        # Test query requiring analysis
        agents = orchestrator._analyze_query_requirements("Analyze this data")
        assert "search" in agents
        assert "analysis" in agents
    
    @pytest.mark.asyncio
    async def test_agent_coordination(self, orchestrator_with_agents):
        """Test coordination of specialized agents."""
        query = "Test query"
        required_agents = ["search", "verification"]
        
        results = await orchestrator_with_agents._coordinate_agents(query, required_agents)
        
        assert len(results) == 2
        assert "search" in results
        assert "verification" in results
        assert results["search"]["success"] is True
        assert results["verification"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_response_synthesis(self, orchestrator):
        """Test response synthesis from agent results."""
        agent_results = {
            "search": {
                "success": True,
                "content": "Search results content"
            },
            "verification": {
                "success": True,
                "content": "Verification results content"
            }
        }
        
        response = await orchestrator._synthesize_response("test query", agent_results)
        
        assert "Search Results:" in response
        assert "Verification Results:" in response
        assert "Search results content" in response
        assert "Verification results content" in response
    
    @pytest.mark.asyncio
    async def test_query_processing(self, orchestrator_with_agents):
        """Test end-to-end query processing."""
        query = "What is artificial intelligence? Please verify the information."
        
        result = await orchestrator_with_agents.process_query(query)
        
        assert result["success"] is True
        assert "response" in result
        assert "session_id" in result
        assert "query_id" in result
        assert "agents_used" in result
        assert "search" in result["agents_used"]
        assert "verification" in result["agents_used"]
    
    @pytest.mark.asyncio
    async def test_process_interface(self, orchestrator_with_agents):
        """Test the BaseResearchAgent process interface."""
        query = "Test query"
        context = {"session_id": None}
        
        result = await orchestrator_with_agents.process(query, context)
        
        assert result["success"] is True
        assert "response" in result
    
    def test_session_info(self, orchestrator):
        """Test session information retrieval."""
        # No current session
        info = orchestrator.get_session_info()
        assert info is None
        
        # With current session
        orchestrator.current_session = ResearchSession(
            session_id="test-id",
            topic="Test Topic"
        )
        
        info = orchestrator.get_session_info()
        assert info is not None
        assert info["session_id"] == "test-id"
        assert info["topic"] == "Test Topic"
        assert "created_at" in info
        assert "updated_at" in info


if __name__ == "__main__":
    # Run a simple test
    async def simple_test():
        storage = MockStorageProvider()
        orchestrator = OrchestratorAgent(model="test-model", storage_provider=storage)
        
        # Test basic functionality
        session_id = await orchestrator.create_session("Test Topic")
        print(f"Created session: {session_id}")
        
        # Test agent registration
        mock_agent = MockAgent("TestSearchAgent")
        orchestrator.register_agent("search", mock_agent)
        print(f"Registered agents: {orchestrator.get_registered_agents()}")
        
        # Test query processing
        result = await orchestrator.process_query("What is machine learning?")
        print(f"Query result: {result}")
        
        print("Simple test completed successfully!")
    
    asyncio.run(simple_test())