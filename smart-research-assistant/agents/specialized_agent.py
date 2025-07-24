"""
Specialized Agent for the Smart Research Assistant.
"""

import logging
from typing import Dict, Any, Optional
import asyncio

try:
    from .base_agent import BaseResearchAgent
    from tools.agent_logger import AgentLogger
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.base_agent import BaseResearchAgent
    from tools.agent_logger import AgentLogger

logger = logging.getLogger(__name__)


class SpecializedAgent(BaseResearchAgent):
    """
    A specialized agent that performs a specific task (e.g., search, verification).
    """

    def __init__(self, model: str, name: str, agent_type: str):
        """
        Initialize the Specialized Agent.

        Args:
            model: The model to use for this agent.
            name: The name of this agent.
            agent_type: The type of the agent (e.g., 'search', 'verification').
        """
        super().__init__(model, name)
        self.agent_type = agent_type
        self.agent_logger = AgentLogger(name, agent_type)
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the pydantic-ai agent for the specialized agent."""
        self.agent = {
            "model": self.model,
            "name": self.name,
            "type": self.agent_type,
            "initialized": True
        }
        logger.debug(f"Specialized agent '{self.name}' of type '{self.agent_type}' initialized")
        self.agent_logger.info(f"Initialized with model: {self.model}")
        
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query and return results.
        
        Args:
            query: The query to process
            context: Optional context information
            
        Returns:
            Dictionary containing the processing results
        """
        task_description = f"process query: '{query[:50]}{'...' if len(query) > 50 else ''}'"
        self.agent_logger.start(task_description)
        
        try:
            # This method should be implemented by subclasses
            # Default implementation returns a not-implemented error
            result = {
                "success": False,
                "error": f"{self.name} has not implemented processing logic",
                "content": ""
            }
            
            self.agent_logger.error(result["error"])
            return result
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.agent_logger.error(error_msg, e)
            return {
                "success": False,
                "error": error_msg,
                "content": ""
            }
        finally:
            success = result.get("success", False) if 'result' in locals() else False
            status = "completed successfully" if success else "failed"
            self.agent_logger.complete(task_description, status) 