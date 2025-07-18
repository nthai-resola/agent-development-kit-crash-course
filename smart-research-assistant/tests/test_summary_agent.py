
import pytest
from unittest.mock import AsyncMock, patch
from models.data_models import SummaryResult, ComparativeAnalysisResult, ComparisonPoint
from agents.summary_agent import SummaryAgent

@pytest.fixture
def summary_agent():
    with patch('agents.summary_agent.Agent') as MockAgent:
        mock_summarizer = MockAgent.return_value
        agent = SummaryAgent(model="test_model")
        agent.summarizer = mock_summarizer
        return agent

@pytest.mark.asyncio
async def test_summary_agent_process_summary_success(summary_agent):
    # Arrange
    query = "Summarize the following text."
    context = {"other_agent_results": {"search": {"content": "Some text to summarize."}}}
    
    summary_result = SummaryResult(
        query=query,
        summary="This is a summary.",
        key_points=["Point 1", "Point 2"],
        themes=["Theme A", "Theme B"],
        categories=["Category X", "Category Y"],
        source_documents=["doc1.txt", "doc2.txt"]
    )

    summary_agent.summarizer.run = AsyncMock(return_value=summary_result)

    # Act
    result = await summary_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Summary for 'Summarize the following text.'" in result["content"]
    assert "Point 1" in result["content"]
    assert "Theme A" in result["content"]

@pytest.mark.asyncio
async def test_summary_agent_process_comparison_success(summary_agent):
    # Arrange
    query = "Compare A vs B."
    context = {"other_agent_results": {"search": {"content": "Text about A and B."}}}
    
    comparison_result = ComparativeAnalysisResult(
        query=query,
        analysis_summary="A is better than B.",
        comparison_points=[
            ComparisonPoint(aspect="Cost", comparison="A is cheaper."),
            ComparisonPoint(aspect="Speed", comparison="B is faster.")
        ]
    )

    summary_agent.summarizer.run = AsyncMock(return_value=comparison_result)

    # Act
    result = await summary_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Comparative Analysis for 'Compare A vs B.'" in result["content"]
    assert "A is cheaper." in result["content"]
    assert "B is faster." in result["content"]

@pytest.mark.asyncio
async def test_summary_agent_handles_exception(summary_agent):
    # Arrange
    query = "a query that will raise an exception"
    context = {}
    summary_agent.summarizer.run = AsyncMock(side_effect=Exception("Test exception"))

    # Act
    result = await summary_agent.process(query, context)

    # Assert
    assert result["success"] is False
    assert "An error occurred during summarization" in result["content"] 