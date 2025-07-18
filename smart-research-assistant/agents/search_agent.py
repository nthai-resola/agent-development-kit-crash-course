"""
Search Agent for the Smart Research Assistant.
"""

import logging
from typing import Dict, Any, List
from pydantic import ValidationError
from pydantic_ai import pydantic_ai
from ..models.data_models import SearchResult, StructuredSearchResult

try:
    from .specialized_agent import SpecializedAgent
    from ..tools.google_search import GoogleSearchTool
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.specialized_agent import SpecializedAgent
    from tools.google_search import GoogleSearchTool
    from models.data_models import SearchResult, StructuredSearchResult

logger = logging.getLogger(__name__)


class SearchAgent(SpecializedAgent):
    """
    A specialized agent for performing web searches.
    """

    def __init__(self, model: str, name: str = "SearchAgent"):
        """
        Initialize the Search Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
        """
        super().__init__(model, name, agent_type="search")
        self.search_tool = GoogleSearchTool()
        self.structured_data_extractor = pydantic_ai.PydanticAI(model=self.model)

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a search query and return the results.
        """
        logger.info(f"{self.name} processing query: {query[:100]}...")
        context = context or {}

        try:
            advanced_query = self._prepare_advanced_query(query, context)
            search_results = await self.search_tool.search(advanced_query)
            
            if not search_results:
                return {
                    "success": False,
                    "content": "No search results found.",
                    "confidence": 0.5,
                    "metadata": {}
                }

            structured_data = await self._extract_structured_data(query, search_results)
            
            if not structured_data:
                return {
                    "success": False,
                    "content": "Failed to extract structured data from search results.",
                    "confidence": 0.4,
                    "metadata": {}
                }

            return {
                "success": True,
                "content": self._format_results(structured_data),
                "confidence": 0.9,
                "metadata": {"sources": [res.link for res in structured_data.results]}
            }
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return {
                "success": False,
                "content": f"An error occurred during the search: {e}",
                "confidence": 0.1,
                "metadata": {}
            }

    def _prepare_advanced_query(self, query: str, context: Dict[str, Any]) -> str:
        """
        Prepare an advanced search query based on context.
        """
        if "research_focus" in context and context["research_focus"]:
            return f"{context['research_focus']} {query}"
        return query

    async def _extract_structured_data(self, query: str, results: List[Dict[str, Any]]) -> StructuredSearchResult:
        """
        Extract structured data from search results using an LLM.
        """
        try:
            return await self.structured_data_extractor.run(
                input_text=f"Query: {query}\n\nResults:\n" + "\n".join([str(r) for r in results]),
                pydantic_model=StructuredSearchResult
            )
        except (ValueError, ValidationError) as e:
            logger.error(f"Pydantic AI validation error: {e}")
            return None

    def _prioritize_results(self, results: list, context: Dict[str, Any]) -> list:
        """
        Prioritize search results based on preferred sources.
        """
        preferred_sources = context.get("user_preferences", {}).get("preferred_sources", [])
        if not preferred_sources:
            return results

        prioritized = sorted(results, key=lambda r: any(pref in r.get('link', '') for pref in preferred_sources), reverse=True)
        return prioritized

    def _detect_paywall(self, result: dict) -> (bool, str):
        """
        Detect if a search result is behind a paywall.
        This is a basic placeholder implementation.
        """
        paywall_keywords = ["subscribe", "premium", "for subscribers", "log in"]
        snippet = result.get('snippet', '').lower()
        if any(keyword in snippet for keyword in paywall_keywords):
            return True, "Paywall detected based on snippet keywords."

        known_paywall_domains = ["wsj.com", "ft.com", "theathletic.com"]
        if any(domain in result.get('link', '') for domain in known_paywall_domains):
            return True, "Source is a known paywalled domain."

        return False, ""

    def _format_results(self, data: StructuredSearchResult) -> str:
        """
        Format the structured search results into a readable string.
        """
        if not data:
            return "No structured data available."

        formatted_string = f"Key Takeaways:\n" + "\n".join(f"- {takeaway}" for takeaway in data.key_takeaways)
        formatted_string += "\n\nResults:\n"

        for item in data.results:
            formatted_string += f"Title: {item.title}\n"
            formatted_string += f"Link: {item.link}\n"
            formatted_string += f"Snippet: {item.snippet}\n"
            if item.is_paywalled:
                formatted_string += f"Paywall: {item.paywall_reason}\n"
            formatted_string += "\n"

        formatted_string += f"Related Topics:\n" + "\n".join(f"- {topic}" for topic in data.related_topics)
        return formatted_string 