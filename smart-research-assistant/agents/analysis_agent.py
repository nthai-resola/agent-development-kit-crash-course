"""
Analysis Agent for the Smart Research Assistant.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import ValidationError, BaseModel, Field
from pydantic_ai import Agent
from models.data_models import AnalysisResult, TranslationResult, EntityExtractionResult, DataInsight, VersionComparisonResult
import matplotlib.pyplot as plt
from agents.specialized_agent import SpecializedAgent

logger = logging.getLogger(__name__)


class AnalysisAgent(SpecializedAgent):
    """
    A specialized agent for analyzing data and extracting insights.
    """

    def __init__(self, model: str, name: str = "AnalysisAgent"):
        """
        Initialize the Analysis Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
        """
        super().__init__(model, name, agent_type="analysis")
        self.analyzer = Agent(model=self.model, result_type=AnalysisResult)
        self.translator = Agent(model=self.model, result_type=TranslationResult)
        self.entity_extractor = Agent(model=self.model, result_type=EntityExtractionResult)
        self.version_comparer = Agent(model=self.model, result_type=VersionComparisonResult)

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process an analysis query and return the results.
        """
        logger.info(f"{self.name} processing query: {query[:100]}...")
        context = context or {}

        if self._is_translation_query(query):
            return await self._handle_translation(query, context)
        if self._is_entity_extraction_query(query):
            return await self._handle_entity_extraction(query, context)
        if self._is_version_comparison_query(query):
            return await self._handle_version_comparison(query, context)

        try:
            analysis_run_result = await self._analyze_data(query, context)
            
            if not analysis_run_result or not hasattr(analysis_run_result, 'data'):
                return {
                    "success": False,
                    "content": "Failed to perform analysis.",
                    "confidence": 0.3,
                    "metadata": {}
                }

            analysis_result = analysis_run_result.data
            if self._is_visualization_query(query):
                chart_path = self._generate_chart(analysis_result)
                analysis_result.visualization = chart_path

            return {
                "success": True,
                "content": self._format_results(analysis_result),
                "confidence": 0.9,
                "metadata": {"analysis": analysis_result.model_dump()}
            }
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return {
                "success": False,
                "content": f"An error occurred during analysis: {e}",
                "confidence": 0.1,
                "metadata": {}
            }

    def _is_translation_query(self, query: str) -> bool:
        """
        Check if a query is a translation query.
        """
        return "translate" in query.lower()

    def _is_entity_extraction_query(self, query: str) -> bool:
        """
        Check if a query is an entity extraction query.
        """
        return "extract entities" in query.lower()

    def _is_version_comparison_query(self, query: str) -> bool:
        """
        Check if a query is a version comparison query.
        """
        return query.lower().startswith("compare versions:")

    async def _handle_translation(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle translation queries.
        """
        try:
            translation_run_result = await self._translate_text(query, context)
            if not translation_run_result or not hasattr(translation_run_result, 'data'):
                return {"success": False, "content": "Failed to perform translation."}
            
            translation_result = translation_run_result.data
            return {"success": True, "content": self._format_translation_results(translation_result)}
        except Exception as e:
            logger.error(f"Error during translation: {e}")
            return {"success": False, "content": "An error occurred during translation."}

    async def _handle_entity_extraction(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle entity extraction queries.
        """
        try:
            extraction_run_result = await self._extract_entities(query, context)
            if not extraction_run_result or not hasattr(extraction_run_result, 'data'):
                return {"success": False, "content": "Failed to extract entities."}
            
            extraction_result = extraction_run_result.data
            return {"success": True, "content": self._format_entity_extraction_results(extraction_result)}
        except Exception as e:
            logger.error(f"Error during entity extraction: {e}")
            return {"success": False, "content": "An error occurred during entity extraction."}

    async def _handle_version_comparison(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle version comparison queries.
        """
        try:
            comparison_run_result = await self._compare_versions(query, context)
            if not comparison_run_result or not hasattr(comparison_run_result, 'data'):
                return {"success": False, "content": "Failed to perform version comparison."}
            
            comparison_result = comparison_run_result.data
            return {"success": True, "content": self._format_version_comparison_results(comparison_result)}
        except Exception as e:
            logger.error(f"Error during version comparison: {e}")
            return {"success": False, "content": "An error occurred during version comparison."}

    async def _translate_text(self, query: str, context: Dict[str, Any]) -> TranslationResult:
        """
        Perform text translation using an LLM.
        """
        text_to_translate = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        prompt = f"Translate the following text based on the query: '{query}'\n\nText: {text_to_translate}"
        self.analyzer.result_type = TranslationResult
        return await self.analyzer.run(prompt)

    async def _extract_entities(self, query: str, context: Dict[str, Any]) -> EntityExtractionResult:
        """
        Perform entity extraction using an LLM.
        """
        text_to_extract = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        prompt = f"Extract entities from the following text based on the query: '{query}'\n\nText: {text_to_extract}"
        self.analyzer.result_type = EntityExtractionResult
        return await self.analyzer.run(prompt)

    async def _compare_versions(self, query: str, context: Dict[str, Any]) -> VersionComparisonResult:
        """
        Perform version comparison using an LLM.
        """
        try:
            _, texts = query.split(":", 1)
            text_v1, text_v2 = texts.split(" vs ", 1)
        except ValueError:
            return None

        prompt = f"""
        Please compare the following two versions of text based on the query: '{query}'

        Version 1:
        {text_v1.strip()}

        Version 2:
        {text_v2.strip()}

        Perform the following tasks:
        1. Identify what has been added, removed, or changed between the two versions.
        2. Provide a summary of the differences.
        """
        self.analyzer.result_type = VersionComparisonResult
        return await self.analyzer.run(prompt)

    def _is_visualization_query(self, query: str) -> bool:
        """
        Check if a query is a visualization query.
        """
        visualization_keywords = ["visualize", "chart", "graph", "plot"]
        return any(keyword in query.lower() for keyword in visualization_keywords)

    def _generate_chart(self, data: AnalysisResult) -> str:
        """
        Generate a bar chart from the analysis results.
        """
        if not data.insights:
            return ""

        labels = [insight.insight for insight in data.insights]
        values = [insight.confidence for insight in data.insights]

        plt.figure(figsize=(10, 6))
        plt.barh(labels, values, color='skyblue')
        plt.xlabel('Confidence')
        plt.title('Data Analysis Insights')
        plt.tight_layout()

        chart_path = f"data/charts/{data.query.replace(' ', '_')}.png"
        plt.savefig(chart_path)
        plt.close()
        return chart_path

    async def _analyze_data(self, query: str, context: Dict[str, Any]) -> AnalysisResult:
        """
        Perform data analysis using an LLM.
        """
        search_results = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        
        prompt = f"""
        Please analyze the following data based on the query: "{query}"

        Here is the data to analyze:
        {search_results}

        Perform the following tasks:
        1. Identify key insights from the data.
        2. For each insight, provide the supporting data or evidence.
        3. Assign a confidence level to each insight.
        4. Generate a high-level summary of the analysis.
        """

        try:
            self.analyzer.result_type = AnalysisResult
            return await self.analyzer.run(prompt)
        except (ValueError, ValidationError) as e:
            logger.error(f"Pydantic AI validation error during analysis: {e}")
            return None

    def _format_translation_results(self, data: TranslationResult) -> str:
        """
        Format the translation results into a readable string.
        """
        return f"Translation to {data.target_language}:\n\nOriginal:\n{data.original_text}\n\nTranslated:\n{data.translated_text}"

    def _format_entity_extraction_results(self, data: EntityExtractionResult) -> str:
        """
        Format the entity extraction results into a readable string.
        """
        formatted_string = "Extracted Entities:\n\n"
        for entity in data.entities:
            formatted_string += f"- {entity.text} ({entity.type}) - Relevance: {entity.relevance:.2f}\n"
        return formatted_string

    def _format_version_comparison_results(self, data: VersionComparisonResult) -> str:
        """
        Format the version comparison results into a readable string.
        """
        formatted_string = f"Version Comparison for '{data.query}':\n\n{data.summary}\n\n"
        if data.added:
            formatted_string += "Added:\n"
            for item in data.added:
                formatted_string += f"- {item}\n"
        if data.removed:
            formatted_string += "\nRemoved:\n"
            for item in data.removed:
                formatted_string += f"- {item}\n"
        if data.changed:
            formatted_string += "\nChanged:\n"
            for item in data.changed:
                formatted_string += f"- {item}\n"
        return formatted_string

    def _format_results(self, data: AnalysisResult) -> str:
        """
        Format the analysis results into a readable string.
        """
        if not data:
            return "No analysis data available."

        formatted_string = f"Analysis for '{data.query}':\n\n{data.analysis_summary}\n\n"
        formatted_string += "Insights:\n"
        for insight in data.insights:
            formatted_string += f"- {insight.insight} (Confidence: {insight.confidence:.2f})\n"
            formatted_string += f"  Supporting Data: {insight.supporting_data}\n"
        
        if data.visualization:
            formatted_string += f"\nVisualization: {data.visualization}"
            
        return formatted_string 