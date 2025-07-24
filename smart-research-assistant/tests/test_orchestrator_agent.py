"""
Tests for the Orchestrator Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
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
    
    def __init__(self, name: str, model: str = "test"):
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
    return OrchestratorAgent(model="test", storage_provider=mock_storage)


@pytest.fixture
def orchestrator_with_agents(orchestrator):
    # Register mock agents
    search_agent = MockAgent("SearchAgent")
    verification_agent = MockAgent("VerificationAgent")
    summary_agent = MockAgent("SummaryAgent")
    analysis_agent = MockAgent("AnalysisAgent")
    
    orchestrator.register_agent(search_agent, "search")
    orchestrator.register_agent(verification_agent, "verification")
    orchestrator.register_agent(summary_agent, "summary")
    orchestrator.register_agent(analysis_agent, "analysis")
    
    return orchestrator


class TestOrchestratorAgent:
    """Test cases for the Orchestrator Agent."""
    
    def test_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.name == "OrchestratorAgent"
        assert orchestrator.model == "test"
        assert orchestrator.current_session is None
        assert len(orchestrator.specialized_agents) == 0
        assert orchestrator.agent is not None
        
        # Test enhanced session management initialization
        assert orchestrator.session_context == {}
        assert orchestrator.interaction_history == []
        assert "active_topics" in orchestrator.session_state
        assert "research_focus" in orchestrator.session_state
        assert "last_query_type" in orchestrator.session_state
        assert "accumulated_findings" in orchestrator.session_state
        assert "user_preferences" in orchestrator.session_state
    
    def test_agent_registration(self, orchestrator):
        """Test agent registration functionality."""
        mock_agent = MockAgent("TestAgent")
        orchestrator.register_agent(mock_agent, "search")
        
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
        # Temporarily set the processing mode to full-processing for testing
        import config
        from models.enums import ProcessingMode
        original_mode = config.Config.PROCESSING_MODE
        config.Config.PROCESSING_MODE = ProcessingMode.FULL_PROCESSING.value
        
        try:
            # Test search-only query
            required_agents, _ = orchestrator._analyze_query_requirements("What is machine learning?")
            assert "search" in required_agents
            
            # Test query requiring verification
            required_agents, _ = orchestrator._analyze_query_requirements("Is this fact accurate?")
            assert "search" in required_agents
            assert "verification" in required_agents
            
            # Test query requiring summary
            required_agents, _ = orchestrator._analyze_query_requirements("Summarize the key points")
            assert "search" in required_agents
            assert "summary" in required_agents
            
            # Test query requiring analysis
            required_agents, _ = orchestrator._analyze_query_requirements("Analyze this data")
            assert "search" in required_agents
            assert "analysis" in required_agents
        finally:
            # Restore original mode
            config.Config.PROCESSING_MODE = original_mode
    
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
        assert "Verification Results" in response
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
    
    @pytest.mark.asyncio
    async def test_context_tracking_between_interactions(self, orchestrator_with_agents):
        """Test context tracking between interactions (Requirement 4.3)."""
        # Process first query
        result1 = await orchestrator_with_agents.process_query("search for AI information")
        
        assert result1["success"] is True
        assert len(orchestrator_with_agents.interaction_history) == 1
        assert orchestrator_with_agents.session_state["last_query_type"] == "search"
        
        # Process second query
        result2 = await orchestrator_with_agents.process_query("verify the AI facts")
        
        assert result2["success"] is True
        assert len(orchestrator_with_agents.interaction_history) == 2
        assert orchestrator_with_agents.session_state["last_query_type"] == "verification"
        
        # Check interaction history
        interactions = orchestrator_with_agents.interaction_history
        assert interactions[0]["query"] == "search for AI information"
        assert interactions[1]["query"] == "verify the AI facts"
        assert interactions[0]["success"] is True
        assert interactions[1]["success"] is True
    
    @pytest.mark.asyncio
    async def test_session_context_restoration(self, orchestrator, mock_storage):
        """Test session context restoration when loading (Requirement 4.2)."""
        from models.data_models import ResearchQuery, QueryResult, ResearchFinding
        
        # Create a session with some data
        session_id = await orchestrator.create_session("AI Research")
        
        # Add some queries and findings to simulate a session with history
        query = ResearchQuery(text="What is machine learning?", agent="OrchestratorAgent")
        query.results.append(QueryResult(source="search", content="ML is a subset of AI...", confidence=0.9))
        orchestrator.current_session.queries.append(query)
        
        finding = ResearchFinding(
            title="Key ML Concepts",
            content="Machine learning involves algorithms...",
            sources=["source1.com"],
            categories=["AI", "Technology"]
        )
        orchestrator.current_session.findings.append(finding)
        
        # Save the session
        await orchestrator.save_session()
        
        # Clear current session and context
        orchestrator.current_session = None
        orchestrator.session_context.clear()
        orchestrator.interaction_history.clear()
        
        # Load the session
        success = await orchestrator.load_session(session_id)
        
        assert success is True
        assert orchestrator.current_session is not None
        
        # Verify context restoration
        assert len(orchestrator.interaction_history) == 1
        assert orchestrator.session_state["research_focus"] == "AI Research"
        assert len(orchestrator.session_state["accumulated_findings"]) == 1
        assert orchestrator.session_context["session_id"] == session_id
        assert orchestrator.session_context["topic"] == "AI Research"
    
    @pytest.mark.asyncio
    async def test_add_finding_to_session(self, orchestrator):
        """Test adding findings to session (Requirement 4.3)."""
        # Create a session first
        await orchestrator.create_session("Test Research")
        
        # Add a finding
        success = await orchestrator.add_finding_to_session(
            title="Important Discovery",
            content="This is a significant finding about AI research...",
            sources=["source1.com", "source2.com"],
            categories=["AI", "Research"]
        )
        
        assert success is True
        assert len(orchestrator.current_session.findings) == 1
        assert orchestrator.current_session.findings[0].title == "Important Discovery"
        assert len(orchestrator.session_state["accumulated_findings"]) == 1
    
    @pytest.mark.asyncio
    async def test_add_note_to_session(self, orchestrator):
        """Test adding notes to session (Requirement 4.3)."""
        # Create a session first
        await orchestrator.create_session("Test Research")
        
        # Add a note
        success = await orchestrator.add_note_to_session(
            content="Remember to investigate this further",
            related_findings=["finding-123"]
        )
        
        assert success is True
        assert len(orchestrator.current_session.notes) == 1
        assert orchestrator.current_session.notes[0].content == "Remember to investigate this further"
    
    def test_get_session_context(self, orchestrator):
        """Test getting session context for continuity."""
        # Test with no session
        context = orchestrator.get_session_context()
        assert context["has_active_session"] is False
        assert context["session_context"] == {}
        
        # Create a session and test again
        orchestrator.current_session = ResearchSession(session_id="test", topic="Test")
        orchestrator.session_context = {"test": "data"}
        orchestrator.session_state = {"active_topics": ["AI"]}
        
        context = orchestrator.get_session_context()
        assert context["has_active_session"] is True
        assert context["session_context"]["test"] == "data"
        assert context["session_state"]["active_topics"] == ["AI"]
    
    @pytest.mark.asyncio
    async def test_session_state_management(self, orchestrator_with_agents):
        """Test comprehensive session state management."""
        # Process queries of different types
        await orchestrator_with_agents.process_query("Search for Machine Learning information")
        await orchestrator_with_agents.process_query("Summarize the key points about AI")
        await orchestrator_with_agents.process_query("Analyze the data trends")
        
        # Check session state updates
        state = orchestrator_with_agents.session_state
        assert state["last_query_type"] == "analysis"
        assert len(state["active_topics"]) > 0
        
        # Check interaction history
        assert len(orchestrator_with_agents.interaction_history) == 3
        
        # Verify context continuity
        context = orchestrator_with_agents.get_session_context()
        assert len(context["recent_interactions"]) == 3


class TestOrchestratorIntegration:
    """Integration tests for the Orchestrator Agent with real specialized agents."""

    @pytest.fixture
    def integrated_orchestrator(self, mock_storage):
        from agents.search_agent import SearchAgent
        from agents.verification_agent import VerificationAgent
        from agents.summary_agent import SummaryAgent
        from agents.analysis_agent import AnalysisAgent

        orchestrator = OrchestratorAgent(model="test", storage_provider=mock_storage)
        
        # Patch the underlying LLM calls for the specialized agents
        with patch('pydantic_ai.Agent') as MockLLMAgent:
            mock_llm_agent = MockLLMAgent.return_value
            mock_llm_agent.run = AsyncMock(return_value={"key": "mocked_value"}) # A simple mock response

            search_agent = SearchAgent(model="test")
            verification_agent = VerificationAgent(model="test")
            summary_agent = SummaryAgent(model="test")
            analysis_agent = AnalysisAgent(model="test")
            
            orchestrator.register_agent(search_agent, "search")
            orchestrator.register_agent(verification_agent, "verification")
            orchestrator.register_agent(summary_agent, "summary")
            orchestrator.register_agent(analysis_agent, "analysis")
            
            return orchestrator

    @pytest.mark.asyncio
    async def test_full_flow_integration(self, integrated_orchestrator):
        """Test a full end-to-end flow with multiple real agents."""
        query = "Search for information about Python, verify it, and then summarize it."
        
        # Mock the SearchTool to prevent real API calls
        with patch('agents.search_agent.SearchTool') as MockSearchTool:
            mock_search_tool_instance = MockSearchTool.return_value
            mock_search_tool_instance.search = AsyncMock(return_value=[
                {"title": "Python", "link": "https://python.org", "snippet": "Official site"}
            ])

            # Mock the structured data extraction for SearchAgent
            with patch.object(integrated_orchestrator.specialized_agents["search"].structured_data_extractor, 'run') as mock_search_run:
                from models.data_models import StructuredSearchResult, SearchResult
                mock_search_run.return_value = StructuredSearchResult(
                    query=query,
                    results=[SearchResult(title="Python", link="https://python.org", snippet="Official site", is_paywalled=False, paywall_reason="")],
                    key_takeaways=["Python is a programming language"],
                    related_topics=["programming"]
                )
                
                # Mock the fact checker for VerificationAgent
                with patch.object(integrated_orchestrator.specialized_agents["verification"].fact_checker, 'run') as mock_verify_run:
                    from models.data_models import VerificationResult, FactCheck
                    mock_verify_run.return_value = VerificationResult(
                        query=query,
                        fact_checks=[FactCheck(claim="Python is a language", is_verified=True, supporting_sources=[], conflicting_sources=[], confidence_score=0.9)],
                        overall_confidence=0.9
                    )

                    # Mock the summarizer for SummaryAgent
                    with patch.object(integrated_orchestrator.specialized_agents["summary"].summarizer, 'run') as mock_summary_run:
                        from models.data_models import SummaryResult
                        mock_summary_run.return_value = SummaryResult(
                            query=query,
                            summary="Python is a language.",
                            key_points=[], themes=[], categories=[], source_documents=[]
                        )

                        result = await integrated_orchestrator.process_query(query)

                        assert result["success"]
                        assert "search" in result["agents_used"]
                        assert "verification" in result["agents_used"]
                        assert "summary" in result["agents_used"]
                        assert "Python is a language" in result["response"]


if __name__ == "__main__":
    # Run a simple test
    async def simple_test():
        storage = MockStorageProvider()
        orchestrator = OrchestratorAgent(model="test", storage_provider=storage)
        
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