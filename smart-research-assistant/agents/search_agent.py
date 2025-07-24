"""
Search Agent for the Smart Research Assistant.

The Search Agent is responsible for executing searches and extracting structured data from search results.
"""

import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from tools.search_tool import SearchTool
from agents.specialized_agent import SpecializedAgent

logger = logging.getLogger(__name__)


class SearchAgent(SpecializedAgent):
    """
    A specialized agent for executing web searches.
    """

    def __init__(self, model: str, name: str = "SearchAgent"):
        """
        Initialize the Search Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
        """
        super().__init__(model, name, agent_type="search")
        self.search_tool = SearchTool()
        
        # Define the extraction model
        class SearchSummary(BaseModel):
            content: str = Field(..., description="Comprehensive summary of the search results that directly addresses the query")
            sources: List[str] = Field(..., description="List of source URLs that contributed to the summary")
            key_facts: List[str] = Field(default_factory=list, description="List of key facts or figures mentioned in the search results")
            
        self.structured_data_extractor = Agent(model=self.model, result_type=SearchSummary)
        self.agent_logger.info(f"Initialized search agent with model {model} and SerpAPI search tool")

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a search query.

        Args:
            query: The query to process.
            context: Optional context information.

        Returns:
            Dictionary containing the search results.
        """
        task_description = f"search for: '{query[:50]}{'...' if len(query) > 50 else ''}'"
        self.agent_logger.start(task_description)
        
        try:
            self.agent_logger.info("Executing web search")
            # Perform the search
            search_results = await self._execute_search(query)
            
            if not search_results:
                self.agent_logger.error("Search returned no results")
                return {
                    "success": False,
                    "error": "No search results found",
                    "content": f"I couldn't find any information about '{query}'.",
                    "confidence": 0.0,
                    "metadata": {"sources": []}
                }
            
            # Extract structured data from search results
            self.agent_logger.info("Extracting structured data from search results")
            structured_data = await self._extract_structured_data(query, search_results)
            
            # Prepare response
            sources = []
            if structured_data and "sources" in structured_data:
                sources = structured_data.get("sources", [])
                self.agent_logger.info(f"Extracted {len(sources)} sources")
            
            content = ""
            if structured_data and "content" in structured_data:
                content = structured_data.get("content", "")
                self.agent_logger.info(f"Extracted content: {len(content)} characters")
            elif search_results:
                # Fallback if structured extraction failed
                self.agent_logger.info("Using raw search results as fallback")
                content = "Here's what I found in my search:\n\n"
                for i, result in enumerate(search_results[:5], 1):
                    content += f"{i}. {result.get('title', 'No title')}\n"
                    content += f"   {result.get('snippet', 'No description')}\n"
                    content += f"   Source: {result.get('link', 'No link')}\n\n"
                    sources.append(result.get('link', ''))
            
            result = {
                "success": True,
                "content": content,
                "confidence": 0.8 if structured_data else 0.5,
                "verified": False,  # Search results are not verified
                "metadata": {
                    "sources": sources,
                    "raw_results_count": len(search_results),
                    "query": query
                }
            }
            
            self.agent_logger.complete(task_description, f"found {len(sources)} sources")
            return result
            
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            self.agent_logger.error(error_msg, e)
            
            return {
                "success": False,
                "error": error_msg,
                "content": f"I encountered an error while searching for information about '{query}'.",
                "confidence": 0.0,
                "metadata": {"error_type": type(e).__name__}
            }

    async def _execute_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a search query using the search tool.

        Args:
            query: The search query.

        Returns:
            A list of search result dictionaries.
        """
        try:
            self.agent_logger.debug(f"Sending query to search API: {query}")
            results = await self.search_tool.search(query)
            
            if not results or not isinstance(results, list):
                self.agent_logger.error("Invalid search results structure")
                return []
                
            self.agent_logger.debug(f"Received {len(results)} search results")
            return results
            
        except Exception as e:
            self.agent_logger.error(f"Search API error: {str(e)}", e)
            raise

    async def _extract_structured_data(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract structured data from search results using pydantic-ai.

        Args:
            query: The original search query.
            search_results: The raw search results.

        Returns:
            A dictionary containing extracted structured data.
        """
        try:
            # Prepare search results for the extractor
            formatted_results = "\n\n".join(
                f"Title: {result.get('title', 'No title')}\n"
                f"Link: {result.get('link', 'No link')}\n"
                f"Snippet: {result.get('snippet', 'No description')}"
                for result in search_results[:10]  # Limit to first 10 results
            )
            
            # Create the prompt for the structured data extractor
            prompt = f"""
            Based on the following search results for the query "{query}", please extract the most relevant information.
            
            SEARCH RESULTS:
            {formatted_results}
            
            Please provide:
            1. A well-structured and coherent summary of the information found in these results
            2. A list of all sources (URLs) that contributed to this summary
            3. Any key facts or figures mentioned
            
            The information should be comprehensive but focused on answering the original query.
            """
            
            self.agent_logger.debug("Sending prompt to structured data extractor")
            
            # Extract structured data
            result = await self.structured_data_extractor.run(prompt)
            
            # Access the structured data from the result
            if not result or not hasattr(result, "data"):
                self.agent_logger.error("Structured data extraction failed - no result or data attribute")
                return {}
                
            structured_data = result.data.model_dump()
            self.agent_logger.debug(f"Successfully extracted structured data: {len(structured_data.get('content', ''))} chars")
            
            return structured_data
            
        except Exception as e:
            self.agent_logger.error(f"Error extracting structured data: {str(e)}", e)
            # Return empty dict on error, the caller will handle this gracefully
            return {} 