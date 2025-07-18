
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.data_models import VerificationResult, FactCheck
from agents.verification_agent import VerificationAgent

@pytest.fixture
def verification_agent():
    with patch('agents.verification_agent.Agent') as MockAgent:
        mock_fact_checker = MockAgent.return_value
        agent = VerificationAgent(model="test_model")
        agent.fact_checker = mock_fact_checker
        return agent

@pytest.mark.asyncio
async def test_verification_agent_process_success(verification_agent):
    # Arrange
    query = "Is the sky blue?"
    context = {
        "other_agent_results": {
            "search": {
                "content": "The sky is blue due to Rayleigh scattering.",
                "metadata": {"sources": ["https://www.nasa.gov/science"]}
            }
        }
    }
    
    verification_result = VerificationResult(
        query=query,
        fact_checks=[
            FactCheck(
                claim="The sky is blue.",
                is_verified=True,
                supporting_sources=["https://www.nasa.gov/science"],
                conflicting_sources=[],
                confidence_score=0.95
            )
        ],
        overall_confidence=0.95
    )

    verification_agent.fact_checker.run = AsyncMock(return_value=verification_result)

    # Act
    result = await verification_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Claim: The sky is blue." in result["content"]
    assert result["confidence"] == 0.95
    assert len(result["metadata"]["fact_checks"]) == 1

@pytest.mark.asyncio
async def test_verification_agent_fact_check_fails(verification_agent):
    # Arrange
    query = "A query that fails fact-checking"
    context = {"other_agent_results": {"search": {"content": "Some content", "metadata": {"sources": []}}}}
    
    verification_agent.fact_checker.run = AsyncMock(return_value=None)

    # Act
    result = await verification_agent.process(query, context)

    # Assert
    assert result["success"] is False
    assert result["content"] == "Failed to perform verification."

def test_get_source_credibility(verification_agent):
    # Assert
    assert verification_agent._get_source_credibility("https://www.reuters.com") == 0.9
    assert verification_agent._get_source_credibility("https://www.dailymail.co.uk/news") == 0.2
    assert verification_agent._get_source_credibility("https://www.some-random-blog.com") == 0.6

@pytest.mark.asyncio
async def test_verification_agent_handles_exception(verification_agent):
    # Arrange
    query = "a query that will raise an exception"
    context = {}
    verification_agent.fact_checker.run = AsyncMock(side_effect=Exception("Test exception"))

    # Act
    result = await verification_agent.process(query, context)

    # Assert
    assert result["success"] is False
    assert "An error occurred during verification" in result["content"] 