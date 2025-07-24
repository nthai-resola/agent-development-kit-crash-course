"""
Summary Agent for the Smart Research Assistant.
"""

import logging
from typing import Dict, Any
from pydantic import ValidationError
from pydantic_ai import Agent
from models.data_models import SummaryResult, ComparativeAnalysisResult
from agents.specialized_agent import SpecializedAgent

logger = logging.getLogger(__name__)


class SummaryAgent(SpecializedAgent):
    """
    A specialized agent for summarizing text.
    """

    def __init__(self, model: str, name: str = "SummaryAgent"):
        """
        Initialize the Summary Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
        """
        super().__init__(model, name, agent_type="summary")
        self.summarizer = Agent(model=self.model, result_type=SummaryResult)
        self.comparative_analyzer = Agent(model=self.model, result_type=ComparativeAnalysisResult)

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a summary query and return the results.
        """
        logger.info(f"{self.name} processing query: {query[:100]}...")
        context = context or {}

        if self._is_comparison_query(query):
            return await self._handle_comparative_analysis(query, context)

        try:
            summary_run_result = await self._summarize(query, context)
            
            if not summary_run_result or not hasattr(summary_run_result, 'data'):
                return {
                    "success": False,
                    "content": "Failed to generate summary.",
                    "confidence": 0.3,
                    "metadata": {}
                }

            summary_result = summary_run_result.data
            return {
                "success": True,
                "content": self._format_results(summary_result),
                "confidence": 0.9,
                "metadata": {"summary": summary_result.model_dump()}
            }
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            return {
                "success": False,
                "content": f"An error occurred during summarization: {e}",
                "confidence": 0.1,
                "metadata": {}
            }

    def _is_comparison_query(self, query: str) -> bool:
        """
        Check if a query is a comparison query.
        """
        comparison_keywords = ["compare", "vs", "versus", "difference", "similarity"]
        return any(keyword in query.lower() for keyword in comparison_keywords)

    async def _handle_comparative_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle comparative analysis queries.
        """
        try:
            analysis_run_result = await self._perform_comparative_analysis(query, context)
            if not analysis_run_result or not hasattr(analysis_run_result, 'data'):
                return {
                    "success": False,
                    "content": "Failed to perform comparative analysis.",
                    "confidence": 0.3,
                    "metadata": {}
                }
            
            analysis_result = analysis_run_result.data
            return {
                "success": True,
                "content": self._format_comparison_results(analysis_result),
                "confidence": 0.9,
                "metadata": {"comparison": analysis_result.model_dump()}
            }
        except Exception as e:
            logger.error(f"Error during comparative analysis: {e}")
            return {
                "success": False,
                "content": f"An error occurred during comparative analysis: {e}",
                "confidence": 0.1,
                "metadata": {}
            }

    async def _perform_comparative_analysis(self, query: str, context: Dict[str, Any]) -> ComparativeAnalysisResult:
        """
        Perform comparative analysis using an LLM.
        """
        search_results = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        
        prompt = f"""
        Please perform a comparative analysis based on the query: "{query}"

        Here is the text to analyze:
        {search_results}

        Perform the following tasks:
        1. Identify the key items being compared.
        2. For each item, identify the key aspects to compare (e.g., features, cost, performance).
        3. Provide a detailed comparison for each aspect, highlighting similarities and differences.
        4. Generate a high-level summary of the analysis.
        """
        try:
            return await self.comparative_analyzer.run(prompt)
        except (ValueError, ValidationError) as e:
            logger.error(f"Pydantic AI validation error during comparative analysis: {e}")
            return None

    async def _summarize(self, query: str, context: Dict[str, Any]) -> SummaryResult:
        """
        Perform summarization using an LLM.
        """
        search_results = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        
        prompt = f"""
        Please summarize the following text based on the query: "{query}"

        Here is the text to summarize:
        {search_results}

        Perform the following tasks:
        1. Generate a concise summary of the text.
        2. Extract the key points from the text.
        3. Identify the main themes in the text.
        4. Categorize the content into relevant topics.
        5. List the source documents that were used for summarization.
        """

        try:
            return await self.summarizer.run(prompt)
        except (ValueError, ValidationError) as e:
            logger.error(f"Pydantic AI validation error during summarization: {e}")
            return None

    def _format_comparison_results(self, data: ComparativeAnalysisResult) -> str:
        """
        Format the comparative analysis results into a readable string.
        """
        if not data:
            return "No comparative analysis data available."

        formatted_string = f"Comparative Analysis for '{data.query}':\n\n{data.analysis_summary}\n\n"
        formatted_string += "Comparison Points:\n"
        for point in data.comparison_points:
            formatted_string += f"- {point.aspect}: {point.comparison}\n"
        return formatted_string

    def _format_results(self, data: SummaryResult) -> str:
        """
        Format the summary results into a readable string.
        """
        if not data:
            return "No summary data available."

        formatted_string = f"Summary for '{data.query}':\n\n{data.summary}\n\n"
        formatted_string += "Key Points:\n"
        for point in data.key_points:
            formatted_string += f"- {point}\n"

        formatted_string += f"\nThemes: {', '.join(data.themes)}"
        formatted_string += f"\nCategories: {', '.join(data.categories)}"
        formatted_string += f"\nSources: {', '.join(data.source_documents)}"
        return formatted_string 