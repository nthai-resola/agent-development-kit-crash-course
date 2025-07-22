
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.data_models import SearchResult, StructuredSearchResult
from agents.search_agent import SearchAgent

@pytest.fixture
def search_agent():
    with patch('agents.search_agent.SearchTool') as MockSearchTool, \
         patch('agents.search_agent.Agent') as MockAgent:
        
        mock_search_tool = MockSearchTool.return_value
        mock_structured_data_extractor = MockAgent.return_value
        
        agent = SearchAgent(model="test_model")
        agent.search_tool = mock_search_tool
        agent.structured_data_extractor = mock_structured_data_extractor
        
        return agent

@pytest.mark.asyncio
async def test_search_agent_process_success(search_agent):
    # Arrange
    query = "test query"
    raw_search_results = [
        {"title": "Test Result 1", "link": "https://example.com", "snippet": "A test snippet."},
        {"title": "Test Result 2", "link": "https://anotherexample.com", "snippet": "Another test snippet."}
    ]
    
    structured_search_result = StructuredSearchResult(
        query=query,
        key_takeaways=["takeaway 1", "takeaway 2"],
        results=[
            SearchResult(title="Test Result 1", link="https://example.com", snippet="A test snippet.", is_paywalled=False, paywall_reason=""),
            SearchResult(title="Test Result 2", link="https://anotherexample.com", snippet="Another test snippet.", is_paywalled=False, paywall_reason="")
        ],
        related_topics=["topic 1", "topic 2"]
    )

    search_agent.search_tool.search = AsyncMock(return_value=raw_search_results)
    search_agent.structured_data_extractor.run = AsyncMock(return_value=structured_search_result)

    # Act
    result = await search_agent.process(query)

    # Assert
    assert result["success"] is True
    assert "Key Takeaways" in result["content"]
    assert "Test Result 1" in result["content"]
    assert result["metadata"]["sources"] == ["https://example.com", "https://anotherexample.com"]

@pytest.mark.asyncio
async def test_search_agent_no_results(search_agent):
    # Arrange
    query = "a query with no results"
    search_agent.search_tool.search = AsyncMock(return_value=[])

    # Act
    result = await search_agent.process(query)

    # Assert
    assert result["success"] is False
    assert result["content"] == "No search results found."

@pytest.mark.asyncio
async def test_search_agent_structured_data_extraction_fails(search_agent):
    # Arrange
    query = "a query that fails extraction"
    raw_search_results = [{"title": "Test", "link": "https://test.com", "snippet": "Test"}]
    
    search_agent.search_tool.search = AsyncMock(return_value=raw_search_results)
    search_agent.structured_data_extractor.run = AsyncMock(return_value=None)

    # Act
    result = await search_agent.process(query)

    # Assert
    assert result["success"] is False
    assert result["content"] == "Could not extract structured data from search results."

@pytest.mark.asyncio
async def test_search_agent_with_multiple_engines(search_agent):
    # Arrange
    query = "test query with multiple engines"
    raw_search_results = [
        {"title": "Google Result", "link": "https://example.com", "snippet": "A Google result."},
        {"title": "Bing Result", "link": "https://example.org", "snippet": "A Bing result."}
    ]
    
    structured_search_result = StructuredSearchResult(
        query=query,
        key_takeaways=["takeaway"],
        results=[
            SearchResult(title="Google Result", link="https://example.com", snippet="A Google result.", is_paywalled=False, paywall_reason=""),
            SearchResult(title="Bing Result", link="https://example.org", snippet="A Bing result.", is_paywalled=False, paywall_reason="")
        ],
        related_topics=["topic"]
    )
    
    context = {"use_multiple_engines": True}
    
    search_agent.search_tool.search_multiple_engines = AsyncMock(return_value=raw_search_results)
    search_agent.structured_data_extractor.run = AsyncMock(return_value=structured_search_result)
    
    # Act
    result = await search_agent.process(query, context)
    
    # Assert
    assert result["success"] is True
    assert search_agent.search_tool.search_multiple_engines.called
    assert not hasattr(search_agent.search_tool, 'search.called')

def test_prioritize_results(search_agent):
    # Arrange
    results = [
        SearchResult(title="A", link="https://c.com", snippet="s"),
        SearchResult(title="B", link="https://a.com", snippet="s"),
        SearchResult(title="C", link="https://b.com", snippet="s"),
    ]
    context = {"user_preferences": {"preferred_sources": ["a.com", "b.com"]}}

    # Act
    prioritized = search_agent._prioritize_results(results, context)

    # Assert
    assert prioritized[0].link == "https://a.com"
    assert prioritized[1].link == "https://b.com"
    assert prioritized[2].link == "https://c.com"

def test_detect_paywall(search_agent):
    # Arrange
    paywalled_result_keyword = SearchResult(title="Paywall", link="https://p.com", snippet="you must subscribe")
    paywalled_result_domain = SearchResult(title="Paywall", link="https://wsj.com", snippet="article")
    free_result = SearchResult(title="Free", link="https://free.com", snippet="free content")
    
    # Act
    is_paywalled_keyword, _ = search_agent._detect_paywall(paywalled_result_keyword)
    is_paywalled_domain, _ = search_agent._detect_paywall(paywalled_result_domain)
    is_free, _ = search_agent._detect_paywall(free_result)

    # Assert
    assert is_paywalled_keyword is True
    assert is_paywalled_domain is True
    assert is_free is False

@pytest.mark.asyncio
async def test_search_agent_process_with_paywall(search_agent):
    # Arrange
    query = "test query with paywall"
    raw_search_results = [{"title": "WSJ Article", "link": "https://wsj.com", "snippet": "A snippet from WSJ."}]
    
    structured_search_result = StructuredSearchResult(
        query=query,
        key_takeaways=["key info"],
        results=[SearchResult(title="WSJ Article", link="https://wsj.com", snippet="A snippet from WSJ.", is_paywalled=False, paywall_reason="")],
        related_topics=[]
    )

    search_agent.search_tool.search = AsyncMock(return_value=raw_search_results)
    search_agent.structured_data_extractor.run = AsyncMock(return_value=structured_search_result)

    # Act
    result = await search_agent.process(query)

    # Assert
    assert result["success"] is True
    assert "Paywall: Source is a known paywalled domain." in result["content"]
    assert structured_search_result.results[0].is_paywalled is True

@pytest.mark.asyncio
async def test_search_agent_handles_exception(search_agent):
    # Arrange
    query = "a query that will raise an exception"
    search_agent.search_tool.search = AsyncMock(side_effect=Exception("Test exception"))

    # Act
    result = await search_agent.process(query)

    # Assert
    assert result["success"] is False
    assert "An error occurred during the search" in result["content"] 