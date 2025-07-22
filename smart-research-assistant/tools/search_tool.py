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
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import Config

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

    async def search(self, query: str, num_results: int = 10, search_engine: str = "google") -> list:
        """
        Perform a web search using SerpAPI.
        
        Args:
            query: The search query
            num_results: The number of results to return (default: 10)
            search_engine: The search engine to use (default: "google")
            
        Returns:
            A list of search result items
        """
        logger.info(f"Performing {search_engine} search for: {query[:100]}...")
        
        try:
            # Ensure the query is valid
            if not query or not query.strip():
                logger.error("Search query is empty or contains only whitespace")
                return []
            
            # Sanitize the query
            sanitized_query = self._sanitize_query(query)
            if not sanitized_query:
                logger.error(f"Query '{query}' was sanitized to an empty string")
                return []
                
            logger.info(f"Sanitized query: {sanitized_query[:100]}")
            
            # Cap num_results to avoid unnecessary cost
            if num_results > 10:
                logger.warning(f"Capping requested results from {num_results} to 10")
                num_results = 10
                
            # Set up the request parameters
            params = {
                "api_key": self.api_key,
                "q": sanitized_query,
                "num": num_results,
                "engine": search_engine,
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"SerpAPI error ({response.status}): {error_text}")
                        return []
                        
                    data = await response.json()
            
            # Process the results
            organic_results = data.get("organic_results", [])
            logger.info(f"Search returned {len(organic_results)} results")
            
            # Transform the results to match the expected format
            transformed_results = []
            for result in organic_results:
                transformed_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": search_engine
                })
            
            return transformed_results
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error during search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
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