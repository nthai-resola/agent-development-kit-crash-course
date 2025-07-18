"""
Session Manager for the Smart Research Assistant.
"""

import logging
from typing import Optional
from .models.data_models import ResearchSession
from .storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages research sessions, including creation, loading, and saving.
    """

    def __init__(self, storage_provider: StorageProvider):
        """
        Initialize the SessionManager.

        Args:
            storage_provider: The storage provider for session persistence.
        """
        self.storage_provider = storage_provider
        self.current_session: Optional[ResearchSession] = None

    async def create_session(self, topic: str = "") -> ResearchSession:
        """
        Create a new research session.
        """
        session = ResearchSession(topic=topic)
        await self.storage_provider.save_session(session)
        self.current_session = session
        logger.info(f"Created new session: {session.session_id}")
        return session

    async def load_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Load an existing research session.
        """
        session = await self.storage_provider.load_session(session_id)
        if session:
            self.current_session = session
            logger.info(f"Loaded session: {session.session_id}")
        return session

    async def save_current_session(self):
        """
        Save the current session.
        """
        if self.current_session:
            await self.storage_provider.save_session(self.current_session)
            logger.info(f"Saved session: {self.current_session.session_id}") 