
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
import aiofiles
from models.data_models import ResearchSession
from storage.storage_provider import StorageProvider
import logging

logger = logging.getLogger(__name__)

class FileStorageProvider(StorageProvider):
    """File-based storage provider for research sessions."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def save_session(self, session: ResearchSession) -> bool:
        file_path = os.path.join(self.base_path, f"{session.session_id}.json")
        try:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(session.model_dump_json(indent=2))
            logger.info(f"Saved session to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving session to {file_path}: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ResearchSession]:
        file_path = os.path.join(self.base_path, f"{session_id}.json")
        if not os.path.exists(file_path):
            logger.warning(f"Session file not found: {file_path}")
            return None
        try:
            async with aiofiles.open(file_path, 'r') as f:
                data = await f.read()
                session = ResearchSession.model_validate_json(data)
                logger.info(f"Loaded session from {file_path}")
                return session
        except Exception as e:
            logger.error(f"Error loading session from {file_path}: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        file_path = os.path.join(self.base_path, f"{session_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for filename in os.listdir(self.base_path):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                session = await self.load_session(session_id)
                if session:
                    sessions.append({"session_id": session_id, "topic": session.topic})
        return sessions

    async def session_exists(self, session_id: str) -> bool:
        file_path = os.path.join(self.base_path, f"{session_id}.json")
        return os.path.exists(file_path) 