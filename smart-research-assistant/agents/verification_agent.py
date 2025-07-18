"""
Verification Agent for the Smart Research Assistant.
"""

import logging
from typing import Dict, Any, List
from pydantic import ValidationError
from pydantic_ai import Agent
from models.data_models import VerificationResult
from agents.specialized_agent import SpecializedAgent

logger = logging.getLogger(__name__)


class VerificationAgent(SpecializedAgent):
    """
    A specialized agent for verifying claims and fact-checking.
    """

    def __init__(self, model: str, name: str = "VerificationAgent"):
        """
        Initialize the Verification Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
        """
        super().__init__(model, name, agent_type="verification")
        self.fact_checker = Agent(model=self.model)

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a verification query and return the results.
        """
        logger.info(f"{self.name} processing query: {query[:100]}...")
        context = context or {}

        try:
            verification_result = await self._fact_check(query, context)
            
            if not verification_result:
                return {
                    "success": False,
                    "content": "Failed to perform verification.",
                    "confidence": 0.3,
                    "metadata": {}
                }

            return {
                "success": True,
                "content": self._format_results(verification_result),
                "confidence": verification_result.overall_confidence,
                "metadata": {"fact_checks": [fc.model_dump() for fc in verification_result.fact_checks]}
            }
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return {
                "success": False,
                "content": f"An error occurred during verification: {e}",
                "confidence": 0.1,
                "metadata": {}
            }

    def _get_source_credibility(self, source: str) -> float:
        """
        Assess the credibility of a source based on predefined lists.
        """
        high_credibility_domains = ["reuters.com", "apnews.com", "bbc.com", "nature.com", "sciencemag.org"]
        low_credibility_domains = ["dailymail.co.uk", "infowars.com", "breitbart.com"]

        if any(domain in source for domain in high_credibility_domains):
            return 0.9
        if any(domain in source for domain in low_credibility_domains):
            return 0.2
        return 0.6  # Neutral score for other sources

    async def _fact_check(self, query: str, context: Dict[str, Any]) -> VerificationResult:
        """
        Perform fact-checking using an LLM.
        """
        search_results = context.get("other_agent_results", {}).get("search", {}).get("content", "")
        sources = context.get("other_agent_results", {}).get("search", {}).get("metadata", {}).get("sources", [])
        
        source_credibility = {source: self._get_source_credibility(source) for source in sources}

        prompt = f"""
        Please verify the following query: "{query}"

        Here are the search results to use for verification:
        {search_results}

        Here is the credibility score for each source (0.0 to 1.0):
        {source_credibility}

        Perform the following tasks:
        1. Identify the key claims in the query.
        2. For each claim, cross-reference the information across the provided search results, taking into account the credibility of the sources.
        3. Identify any conflicting information between sources.
        4. Determine if each claim is verified, not verified, or disputed.
        5. Provide a confidence score for each claim based on the consistency and credibility of the evidence.
        6. List the sources that support each claim and those that conflict with it.
        7. Provide an overall confidence score for the entire verification.
        """

        try:
            return await self.fact_checker.run(
                input_text=prompt,
                pydantic_model=VerificationResult
            )
        except (ValueError, ValidationError) as e:
            logger.error(f"Pydantic AI validation error during fact-checking: {e}")
            return None

    def _format_results(self, data: VerificationResult) -> str:
        """
        Format the verification results into a readable string.
        """
        if not data:
            return "No verification data available."

        formatted_string = f"Verification for '{data.query}':\n\n"
        for check in data.fact_checks:
            formatted_string += f"Claim: {check.claim}\n"
            formatted_string += f"Verified: {'Yes' if check.is_verified else 'No'}\n"
            formatted_string += f"Supporting Sources: {', '.join(check.supporting_sources)}\n"
            formatted_string += f"Conflicting Sources: {', '.join(check.conflicting_sources)}\n"
            formatted_string += f"Confidence: {check.confidence_score:.2f}\n\n"
            
        formatted_string += f"Overall Confidence: {data.overall_confidence:.2f}"
        return formatted_string 