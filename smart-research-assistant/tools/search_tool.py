"""
Search Tool for the Smart Research Assistant using SerpAPI.

SerpAPI provides access to search results from various search engines including Google, Bing, and others.
"""

import logging
import re
import json
from typing import List, Dict, Any
import aiohttp

try:
    from ..config import Config
    from ..tools.agent_logger import AgentLogger
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import Config
    from tools.agent_logger import AgentLogger

logger = logging.getLogger(__name__)


class SearchTool:
    """
    A tool for performing web searches using SerpAPI.
    """

    def __init__(self):
        """
        Initialize the Search Tool.
        """
        self.api_key = Config.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.agent_logger = AgentLogger("SearchTool", "tool")

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize the search query to make it compatible with the search API.
        
        Args:
            query: The original search query
            
        Returns:
            A sanitized version of the query
        """
        if not query:
            return ""
            
        # Trim whitespace
        query = query.strip()
        
        # Add spaces between camelCase/PascalCase words (e.g., pydanticAI -> pydantic AI)
        query = re.sub(r'([a-z])([A-Z])', r'\1 \2', query)
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a web search using SerpAPI.
        
        Args:
            query: The search query
            num_results: Maximum number of results to return
            
        Returns:
            A list of search result dictionaries
        """
        sanitized_query = self._sanitize_query(query)
        self.agent_logger.info(f"Searching for: {sanitized_query}")
        
        try:
            params = {
                "q": sanitized_query,
                "api_key": self.api_key,
                "engine": "google",
                "num": num_results,
                "gl": "us",  # Google locale (country)
                "hl": "en"   # Host language
            }
            
            self.agent_logger.debug(f"Sending request to SerpAPI: {self.base_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.agent_logger.error(f"SerpAPI error: HTTP {response.status} - {error_text}")
                        return []
                    
                    data = await response.json()
                    
            if "error" in data:
                self.agent_logger.error(f"SerpAPI error: {data['error']}")
                return []
                
            organic_results = data.get("organic_results", [])
            self.agent_logger.info(f"Received {len(organic_results)} results from search API")
            
            # Include knowledge graph if available
            if "knowledge_graph" in data:
                kg = data["knowledge_graph"]
                if "title" in kg and "description" in kg:
                    kg_result = {
                        "title": kg["title"],
                        "snippet": kg["description"],
                        "link": kg.get("website", ""),
                        "is_knowledge_graph": True
                    }
                    organic_results.insert(0, kg_result)
                    self.agent_logger.info(f"Added knowledge graph result: {kg['title']}")
                
            return organic_results[:num_results]
            
        except aiohttp.ClientError as e:
            self.agent_logger.error(f"Request error: {str(e)}")
            return []
        except Exception as e:
            self.agent_logger.error(f"Unexpected error during search: {str(e)}")
            return []

    async def search_multiple_engines(self, query: str, num_results: int = 5) -> list:
        """
        Perform searches across multiple search engines for more comprehensive results.
        
        Args:
            query: The search query
            num_results: Number of results per search engine
            
        Returns:
            Combined list of results from multiple search engines
        """
        engines = ["google", "bing"]
        results = []
        
        for engine in engines:
            engine_results = await self.search(query, num_results, engine)
            results.extend(engine_results)
            
        return results


# For testing the tool directly
async def test_search(query="python programming"):
    """Test the search functionality."""
    search_tool = SearchTool()
    results = await search_tool.search(query)
    
    print(f"Search results for '{query}':")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Link: {result.get('link', 'N/A')}")
        print(f"Snippet: {result.get('snippet', 'N/A')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search()) 