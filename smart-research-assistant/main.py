"""
Main entry point for the Smart Research Assistant.
"""

import asyncio
import logging
from typing import Optional

# Handle imports for both package and standalone usage
try:
    from .config import Config
    from .models.data_models import ResearchSession
    from .agents.orchestrator_agent import OrchestratorAgent
    from .agents.specialized_agent import SpecializedAgent
    from .storage.storage_provider import StorageProvider
except ImportError:
    from config import Config
    from models.data_models import ResearchSession
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.specialized_agent import SpecializedAgent
    from storage.storage_provider import StorageProvider


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


class SmartResearchAssistant:
    """Main application class for the Smart Research Assistant."""
    
    def __init__(self):
        """Initialize the Smart Research Assistant."""
        self.logger = logging.getLogger(__name__)
        self.current_session: Optional[ResearchSession] = None
        
        # Validate configuration
        if not Config.validate_config():
            raise ValueError("Invalid configuration. Please check your environment variables.")

        # Initialize storage provider
        self.storage_provider = StorageProvider()

        # Initialize Orchestrator Agent
        self.orchestrator = OrchestratorAgent(storage_provider=self.storage_provider)
        self._register_specialized_agents()
        
        self.logger.info("Smart Research Assistant initialized")

    def _register_specialized_agents(self):
        """Register specialized agents with the orchestrator."""
        # Create specialized agents
        search_agent = SpecializedAgent(model=Config.SEARCH_MODEL, name="SearchAgent", agent_type="search")
        verification_agent = SpecializedAgent(model=Config.VERIFICATION_MODEL, name="VerificationAgent", agent_type="verification")
        summary_agent = SpecializedAgent(model=Config.SUMMARY_MODEL, name="SummaryAgent", agent_type="summary")
        analysis_agent = SpecializedAgent(model=Config.ANALYSIS_MODEL, name="AnalysisAgent", agent_type="analysis")

        # Register agents with the orchestrator
        self.orchestrator.register_agent(search_agent, "search")
        self.orchestrator.register_agent(verification_agent, "verification")
        self.orchestrator.register_agent(summary_agent, "summary")
        self.orchestrator.register_agent(analysis_agent, "analysis")
    
    async def start_session(self, topic: str = "") -> str:
        """
        Start a new research session.
        
        Args:
            topic: Optional topic for the research session
            
        Returns:
            The session ID
        """
        self.current_session = ResearchSession(topic=topic)
        self.logger.info(f"Started new research session: {self.current_session.session_id}")
        return self.current_session.session_id
    
    async def process_query(self, query: str) -> dict:
        """
        Process a research query.
        
        Args:
            query: The research query to process
            
        Returns:
            Dictionary containing the query results
        """
        if not self.current_session:
            await self.start_session()
        
        self.logger.info(f"Processing query: {query}")
        
        # Delegate query processing to the orchestrator
        return await self.orchestrator.process_query(query, self.current_session.session_id)
    
    def get_session_info(self) -> Optional[dict]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session information or None if no active session
        """
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


async def main():
    """Main function for running the Smart Research Assistant."""
    setup_logging()
    
    try:
        assistant = SmartResearchAssistant()
        
        # Example usage
        session_id = await assistant.start_session("AI Research")
        print(f"Started session: {session_id}")
        
        result = await assistant.process_query("What are the latest developments in AI?")
        print(f"Query result: {result}")
        
        session_info = assistant.get_session_info()
        print(f"Session info: {session_info}")
        
    except Exception as e:
        logging.error(f"Error running Smart Research Assistant: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())