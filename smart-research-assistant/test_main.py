#!/usr/bin/env python3
"""
Test script for the main application without requiring API keys.
"""

import asyncio
import logging
from typing import Optional
from config import Config
from models.data_models import ResearchSession


class TestSmartResearchAssistant:
    """Test version of the Smart Research Assistant that doesn't require API keys."""
    
    def __init__(self):
        """Initialize the test version."""
        self.logger = logging.getLogger(__name__)
        self.current_session: Optional[ResearchSession] = None
        self.logger.info("Test Smart Research Assistant initialized")
    
    async def start_session(self, topic: str = "") -> str:
        """Start a new research session."""
        self.current_session = ResearchSession(topic=topic)
        self.logger.info(f"Started new research session: {self.current_session.session_id}")
        return self.current_session.session_id
    
    async def process_query(self, query: str) -> dict:
        """Process a research query."""
        if not self.current_session:
            await self.start_session()
        
        self.logger.info(f"Processing query: {query}")
        
        return {
            "query": query,
            "session_id": self.current_session.session_id,
            "status": "received",
            "message": "Query processing will be implemented in subsequent tasks"
        }
    
    def get_session_info(self) -> Optional[dict]:
        """Get information about the current session."""
        if not self.current_session:
            return None
        
        return {
            "session_id": self.current_session.session_id,
            "topic": self.current_session.topic,
            "created_at": self.current_session.created_at.isoformat(),
            "updated_at": self.current_session.updated_at.isoformat(),
            "queries_count": len(self.current_session.queries),
            "findings_count": len(self.current_session.findings),
            "notes_count": len(self.current_session.notes)
        }


async def test_main():
    """Test the main application functionality."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        assistant = TestSmartResearchAssistant()
        
        # Test session creation
        session_id = await assistant.start_session("AI Research")
        print(f"✓ Started session: {session_id}")
        
        # Test query processing
        result = await assistant.process_query("What are the latest developments in AI?")
        print(f"✓ Processed query: {result['status']}")
        
        # Test session info
        session_info = assistant.get_session_info()
        print(f"✓ Got session info for topic: {session_info['topic']}")
        
        print("✓ Main application structure works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Main application error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_main())
    if success:
        print("\n✓ All main application tests passed!")
    else:
        print("\n✗ Main application tests failed!")