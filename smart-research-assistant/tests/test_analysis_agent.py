
import pytest
from unittest.mock import AsyncMock, patch
from models.data_models import AnalysisResult, DataInsight, TranslationResult, EntityExtractionResult, Entity, VersionComparisonResult
from agents.analysis_agent import AnalysisAgent

@pytest.fixture
def analysis_agent():
    with patch('agents.analysis_agent.Agent') as MockAgent, \
         patch('agents.analysis_agent.plt') as MockPlot:
        mock_analyzer = MockAgent.return_value
        agent = AnalysisAgent(model="test_model")
        agent.analyzer = mock_analyzer
        return agent

@pytest.mark.asyncio
async def test_analysis_agent_process_analysis_success(analysis_agent):
    # Arrange
    query = "Analyze this data."
    context = {"other_agent_results": {"search": {"content": "Some data to analyze."}}}
    
    analysis_result = AnalysisResult(
        query=query,
        analysis_summary="The data is interesting.",
        insights=[DataInsight(insight="Insight 1", supporting_data="Data point A", confidence=0.9)],
        visualization=None
    )

    analysis_agent.analyzer.run = AsyncMock(return_value=analysis_result)

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Analysis for 'Analyze this data.'" in result["content"]
    assert "Insight 1" in result["content"]

@pytest.mark.asyncio
async def test_analysis_agent_process_translation_success(analysis_agent):
    # Arrange
    query = "translate this"
    context = {"other_agent_results": {"search": {"content": "Hello"}}}
    
    translation_result = TranslationResult(
        original_text="Hello",
        translated_text="Hola",
        source_language="English",
        target_language="Spanish"
    )

    analysis_agent.analyzer.run = AsyncMock(return_value=translation_result)

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Translation to Spanish" in result["content"]
    assert "Hola" in result["content"]

@pytest.mark.asyncio
async def test_analysis_agent_process_entity_extraction_success(analysis_agent):
    # Arrange
    query = "extract entities from this text"
    context = {"other_agent_results": {"search": {"content": "Apple is a company."}}}
    
    extraction_result = EntityExtractionResult(
        entities=[Entity(text="Apple", type="Organization", relevance=0.95)]
    )

    analysis_agent.analyzer.run = AsyncMock(return_value=extraction_result)

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Extracted Entities" in result["content"]
    assert "Apple (Organization)" in result["content"]

@pytest.mark.asyncio
async def test_analysis_agent_process_version_comparison_success(analysis_agent):
    # Arrange
    query = "compare versions: this is v1 vs this is v2"
    context = {}
    
    comparison_result = VersionComparisonResult(
        query=query,
        summary="v2 has new items.",
        added=["new item"],
        removed=[],
        changed=["this is v1"]
    )

    analysis_agent.analyzer.run = AsyncMock(return_value=comparison_result)

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is True
    assert "Version Comparison" in result["content"]
    assert "new item" in result["content"]

@pytest.mark.asyncio
async def test_analysis_agent_process_version_comparison_invalid_format(analysis_agent):
    # Arrange
    query = "compare versions: this is v1"
    context = {}

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is False
    assert "Failed to perform version comparison" in result["content"]

@pytest.mark.asyncio
async def test_analysis_agent_handles_exception(analysis_agent):
    # Arrange
    query = "a query that will raise an exception"
    context = {}
    analysis_agent.analyzer.run = AsyncMock(side_effect=Exception("Test exception"))

    # Act
    result = await analysis_agent.process(query, context)

    # Assert
    assert result["success"] is False
    assert "An error occurred during analysis" in result["content"] 