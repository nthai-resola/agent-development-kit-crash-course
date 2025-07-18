"""
Session Manager for the Smart Research Assistant.
"""

import logging
from typing import Optional
from models.data_models import ResearchSession
from storage.storage_provider import StorageProvider

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

    async def list_sessions(self) -> list[str]:
        """
        List all available session IDs.
        """
        return await self.storage_provider.list_sessions()

    async def export_session(self, session_id: str, format: str) -> bytes:
        """
        Export a session to a specific format.
        """
        session = await self.load_session(session_id)
        if not session:
            raise ValueError("Session not found")

        if format == "markdown":
            return self._export_to_markdown(session)
        elif format == "json":
            return session.model_dump_json(indent=2).encode('utf-8')
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_to_markdown(self, session: ResearchSession) -> bytes:
        """
        Export the session to a markdown string.
        """
        md = f"# Research Session: {session.topic}\n\n"
        md += f"**Session ID:** {session.session_id}\n"
        md += f"**Created At:** {session.created_at}\n"
        md += f"**Last Updated:** {session.updated_at}\n\n"

        md += "## Queries\n"
        for query in session.queries:
            md += f"### Query: {query.text}\n"
            md += f"**Agent:** {query.agent}\n"
            for result in query.results:
                md += f"- **Source:** {result.source}\n"
                md += f"  - **Content:** {result.content}\n"
        
        md += "\n## Findings\n"
        for finding in session.findings:
            md += f"### {finding.title}\n"
            md += f"{finding.content}\n"
            md += f"**Sources:** {', '.join(finding.sources)}\n"

        md += "\n## Notes\n"
        for note in session.notes:
            md += f"- {note.content}\n"
            
        return md.encode('utf-8') 