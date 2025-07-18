"""
Storage provider interface for the Smart Research Assistant.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from models.data_models import ResearchSession


class StorageProvider(ABC):
    """Abstract base class for storage providers."""
    
    @abstractmethod
    async def save_session(self, session: ResearchSession) -> bool:
        """
        Save a research session.
        
        Args:
            session: The research session to save
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Load a research session by ID.
        
        Args:
            session_id: The ID of the session to load
            
        Returns:
            The research session if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a research session.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session metadata dictionaries
        """
        pass
    
    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: The ID of the session to check
            
        Returns:
            True if the session exists, False otherwise
        """
        pass