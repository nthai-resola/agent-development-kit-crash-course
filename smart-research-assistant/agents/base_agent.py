"""
Base agent interface for the Smart Research Assistant.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseResearchAgent(ABC):
    """Abstract base class for all research agents."""
    
    def __init__(self, model: str, name: str):
        """
        Initialize the base research agent.
        
        Args:
            model: The model to use for this agent
            name: The name of this agent
        """
        self.model = model
        self.name = name
        self.agent: Optional[Any] = None
    
    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query and return results.
        
        Args:
            query: The query to process
            context: Optional context information
            
        Returns:
            Dictionary containing the processing results
        """
        pass
    
    def get_agent_info(self) -> Dict[str, str]:
        """
        Get basic information about this agent.
        
        Returns:
            Dictionary with agent name and model information
        """
        return {
            "name": self.name,
            "model": self.model,
            "type": self.__class__.__name__
        }