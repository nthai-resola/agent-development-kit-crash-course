"""
Tests for the agent delegation logic in the Orchestrator Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Import will be resolved at runtime when used as a package
try:
    from ..agents.orchestrator_agent import OrchestratorAgent
    from ..agents.base_agent import BaseResearchAgent
    from ..models.data_models import ResearchSession
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.base_agent import BaseResearchAgent
    from models.data_models import ResearchSession


class MockAgent(BaseResearchAgent):
    """Mock specialized agent for testing."""
    
    def __init__(self, name: str, model: str = "test-model", should_fail: bool = False):
        super().__init__(model, name)
        self.process_calls = []
        self.should_fail = should_fail
    
    def _initialize_agent(self):
        self.agent = {"mock": True}
    
    async def process(self, query: str, context=None):
        self.process_calls.append((query, context))
        
        if self.should_fail:
            return {
                "success": False,
                "error": f"Mock {self.name} failure",
                "content": ""
            }
        
        return {
            "success": True,
            "content": f"Mock {self.name} result for: {query}",
            "confidence": 0.8,
            "verified": True,
            "metadata": {"agent": self.name}
        }


@pytest.fixture
def orchestrator():
    return OrchestratorAgent(model="test-model")


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
    
    # Create a session for testing
    asyncio.run(orchestrator.create_session("Test Research"))
    
    return orchestrator


@pytest.fixture
def orchestrator_with_failing_agents(orchestrator):
    # Register mock agents with some failing
    search_agent = MockAgent("SearchAgent")
    verification_agent = MockAgent("VerificationAgent", should_fail=True)
    summary_agent = MockAgent("SummaryAgent")
    analysis_agent = MockAgent("AnalysisAgent", should_fail=True)
    
    orchestrator.register_agent("search", search_agent)
    orchestrator.register_agent("verification", verification_agent)
    orchestrator.register_agent("summary", summary_agent)
    orchestrator.register_agent("analysis", analysis_agent)
    
    # Create a session for testing
    asyncio.run(orchestrator.create_session("Test Research"))
    
    return orchestrator


class TestAgentDelegationLogic:
    """Test cases for the agent delegation logic."""
    
    @pytest.mark.asyncio
    async def test_enhanced_query_analysis(self, orchestrator):
        """Test the enhanced query analysis for agent selection."""
        # Test search query
        agents = orchestrator._analyze_query_requirements("Find information about machine learning")
        assert "search" in agents
        assert len(agents) == 1
        
        # Test verification query
        agents = orchestrator._analyze_query_requirements("Can you verify if this fact about AI is accurate?")
        assert "search" in agents
        assert "verification" in agents
        assert len(agents) == 2
        
        # Test summary query
        agents = orchestrator._analyze_query_requirements("Give me a summary of the key points about neural networks")
        assert "search" in agents
        assert "summary" in agents
        assert len(agents) == 2
        
        # Test analysis query
        agents = orchestrator._analyze_query_requirements("Analyze the trends in AI research over the past decade")
        assert "search" in agents
        assert "analysis" in agents
        assert len(agents) == 2
        
        # Test complex query requiring multiple agents
        agents = orchestrator._analyze_query_requirements(
            "Find information about deep learning, verify its accuracy, and summarize the key points"
        )
        assert "search" in agents
        assert "verification" in agents
        assert "summary" in agents
        assert len(agents) == 3
    
    @pytest.mark.asyncio
    async def test_agent_execution_order(self, orchestrator):
        """Test the determination of agent execution order."""
        # Test with search and verification
        order = orchestrator._determine_agent_execution_order(["search", "verification"])
        assert order[0] == "search"
        assert order[1] == "verification"
        
        # Test with search, verification, and summary
        order = orchestrator._determine_agent_execution_order(["verification", "search", "summary"])
        assert order[0] == "search"  # Search should come first
        assert "verification" in order
        assert "summary" in order
        
        # Test with only analysis
        order = orchestrator._determine_agent_execution_order(["analysis"])
        assert order[0] == "analysis"
        
        # Test with all agents
        order = orchestrator._determine_agent_execution_order(["verification", "search", "summary", "analysis"])
        assert order[0] == "search"  # Search should come first
        assert "verification" in order
        assert "summary" in order
        assert "analysis" in order
    
    @pytest.mark.asyncio
    async def test_agent_context_preparation(self, orchestrator_with_agents):
        """Test the preparation of context for specialized agents."""
        query = "What is machine learning?"
        
        # Test context for search agent (no previous results)
        context = orchestrator_with_agents._prepare_agent_context(query, "search", {})
        assert context["query_type"] == "search"
        assert context["original_query"] == query
        assert "session_id" in context
        assert "session_context" in context
        
        # Create mock results from search
        search_results = {
            "search": {
                "success": True,
                "content": "Machine learning is a field of AI...",
                "metadata": {"sources": ["source1.com", "source2.com"]}
            }
        }
        
        # Test context for verification agent with search results
        context = orchestrator_with_agents._prepare_agent_context(query, "verification", search_results)
        assert context["query_type"] == "verification"
        assert "search_results" in context
        assert context["search_results"] == "Machine learning is a field of AI..."
        assert "sources_to_verify" in context
        assert context["sources_to_verify"] == ["source1.com", "source2.com"]
        
        # Test context for summary agent with search results
        context = orchestrator_with_agents._prepare_agent_context(query, "summary", search_results)
        assert context["query_type"] == "summary"
        assert "content_to_summarize" in context
        assert context["content_to_summarize"] == "Machine learning is a field of AI..."
    
    @pytest.mark.asyncio
    async def test_agent_coordination(self, orchestrator_with_agents):
        """Test the coordination of multiple agents."""
        query = "What is machine learning? Verify the information and summarize it."
        
        # Analyze query to get required agents
        required_agents = orchestrator_with_agents._analyze_query_requirements(query)
        assert "search" in required_agents
        assert "verification" in required_agents
        assert "summary" in required_agents
        
        # Coordinate agents
        results = await orchestrator_with_agents._coordinate_agents(query, required_agents)
        
        # Check that all agents were executed
        assert "search" in results
        assert "verification" in results
        assert "summary" in results
        
        # Check that all results were successful
        assert results["search"]["success"] is True
        assert results["verification"]["success"] is True
        assert results["summary"]["success"] is True
        
        # Check that the content was generated
        assert "Mock SearchAgent result" in results["search"]["content"]
        assert "Mock VerificationAgent result" in results["verification"]["content"]
        assert "Mock SummaryAgent result" in results["summary"]["content"]
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, orchestrator_with_failing_agents):
        """Test handling of agent failures."""
        query = "What is machine learning? Verify the information and analyze the trends."
        
        # Analyze query to get required agents
        required_agents = orchestrator_with_failing_agents._analyze_query_requirements(query)
        assert "search" in required_agents
        assert "verification" in required_agents
        assert "analysis" in required_agents
        
        # Coordinate agents (some will fail)
        results = await orchestrator_with_failing_agents._coordinate_agents(query, required_agents)
        
        # Check that all agents were attempted
        assert "search" in results
        assert "verification" in results
        assert "analysis" in results
        
        # Check success/failure status
        assert results["search"]["success"] is True
        assert results["verification"]["success"] is False
        assert results["analysis"]["success"] is False
        
        # Check error messages
        assert "Mock VerificationAgent failure" in results["verification"]["error"]
        assert "Mock AnalysisAgent failure" in results["analysis"]["error"]
    
    @pytest.mark.asyncio
    async def test_response_synthesis(self, orchestrator_with_agents):
        """Test the synthesis of responses from multiple agents."""
        # Create mock agent results
        agent_results = {
            "search": {
                "success": True,
                "content": "Machine learning is a field of AI that uses statistical techniques to give computers the ability to learn.",
                "confidence": 0.9,
                "verified": False
            },
            "verification": {
                "success": True,
                "content": "The information about machine learning is accurate based on multiple reliable sources.",
                "confidence": 0.8,
                "verified": True
            },
            "summary": {
                "success": True,
                "content": "Machine learning is a subset of AI focused on developing systems that learn from data.",
                "confidence": 0.9,
                "verified": True
            }
        }
        
        # Synthesize response
        response = await orchestrator_with_agents._synthesize_response(
            "What is machine learning? Verify and summarize.", agent_results
        )
        
        # Check that the response contains content from all agents
        assert "Machine learning is a field of AI" in response
        assert "accurate based on multiple reliable sources" in response
        assert "subset of AI focused on developing systems" in response
    
    @pytest.mark.asyncio
    async def test_response_synthesis_with_failures(self, orchestrator_with_agents):
        """Test response synthesis when some agents fail."""
        # Create mock agent results with some failures
        agent_results = {
            "search": {
                "success": True,
                "content": "Machine learning is a field of AI that uses statistical techniques.",
                "confidence": 0.9,
                "verified": False
            },
            "verification": {
                "success": False,
                "error": "Verification service unavailable",
                "content": ""
            },
            "summary": {
                "success": True,
                "content": "Machine learning is a subset of AI focused on data-driven learning.",
                "confidence": 0.9,
                "verified": True
            }
        }
        
        # Synthesize response
        response = await orchestrator_with_agents._synthesize_response(
            "What is machine learning? Verify and summarize.", agent_results
        )
        
        # Check that the response contains content from successful agents
        assert "Machine learning is a field of AI" in response
        assert "subset of AI focused on data-driven learning" in response
        
        # Check that the response mentions the limitation
        assert "Limitations" in response
        assert "Verification" in response
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(self, orchestrator_with_agents):
        """Test end-to-end query processing with agent delegation."""
        # Process a complex query
        result = await orchestrator_with_agents.process_query(
            "What is deep learning? Verify the information and summarize the key points."
        )
        
        # Check that the query was processed successfully
        assert result["success"] is True
        assert "response" in result
        assert "agents_used" in result
        
        # Check that the required agents were used
        assert "search" in result["agents_used"]
        assert "verification" in result["agents_used"]
        assert "summary" in result["agents_used"]
        
        # Check that the response contains content from all agents
        assert "Search Results" in result["response"]
        assert "Verification" in result["response"]
        assert "Summary" in result["response"]


if __name__ == "__main__":
    # Run a simple test
    async def simple_test():
        orchestrator = OrchestratorAgent(model="test-model")
        
        # Register mock agents
        search_agent = MockAgent("SearchAgent")
        verification_agent = MockAgent("VerificationAgent")
        orchestrator.register_agent("search", search_agent)
        orchestrator.register_agent("verification", verification_agent)
        
        # Create a session
        await orchestrator.create_session("Test Research")
        
        # Test query analysis
        query = "Verify if machine learning can solve all AI problems"
        required_agents = orchestrator._analyze_query_requirements(query)
        print(f"Required agents for '{query}': {required_agents}")
        
        # Test agent coordination
        results = await orchestrator._coordinate_agents(query, required_agents)
        print(f"Agent results: {results}")
        
        # Test response synthesis
        response = await orchestrator._synthesize_response(query, results)
        print(f"Synthesized response: {response}")
        
        print("Simple test completed successfully!")
    
    asyncio.run(simple_test())