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
    from .agents.search_agent import SearchAgent
    from .agents.verification_agent import VerificationAgent
    from .agents.summary_agent import SummaryAgent
    from .agents.analysis_agent import AnalysisAgent
    from .agents.specialized_agent import SpecializedAgent
    from .storage.storage_provider import StorageProvider
    from .session_manager import SessionManager
except ImportError:
    from config import Config
    from models.data_models import ResearchSession
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.search_agent import SearchAgent
    from agents.verification_agent import VerificationAgent
    from agents.summary_agent import SummaryAgent
    from agents.analysis_agent import AnalysisAgent
    from agents.specialized_agent import SpecializedAgent
    from storage.storage_provider import StorageProvider
    from session_manager import SessionManager


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
        
        # Validate configuration
        if not Config.validate_config():
            raise ValueError("Invalid configuration. Please check your environment variables.")

        # Initialize storage provider
        self.storage_provider = StorageProvider()
        
        # Initialize Session Manager
        self.session_manager = SessionManager(storage_provider=self.storage_provider)

        # Initialize Orchestrator Agent
        self.orchestrator = OrchestratorAgent(storage_provider=self.storage_provider)
        self._register_specialized_agents()
        
        self.logger.info("Smart Research Assistant initialized")

    def _register_specialized_agents(self):
        """Register specialized agents with the orchestrator."""
        # Create specialized agents
        search_agent = SearchAgent(model=Config.SEARCH_MODEL)
        verification_agent = VerificationAgent(model=Config.VERIFICATION_MODEL)
        summary_agent = SummaryAgent(model=Config.SUMMARY_MODEL)
        analysis_agent = AnalysisAgent(model=Config.ANALYSIS_MODEL)

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
        session = await self.session_manager.create_session(topic)
        self.logger.info(f"Started new research session: {session.session_id}")
        return session.session_id
    
    async def process_query(self, query: str) -> dict:
        """
        Process a research query.
        
        Args:
            query: The research query to process
            
        Returns:
            Dictionary containing the query results
        """
        if not self.session_manager.current_session:
            await self.start_session()
        
        self.logger.info(f"Processing query: {query}")
        
        # Delegate query processing to the orchestrator
        return await self.orchestrator.process_query(query, self.session_manager.current_session.session_id)
    
    def get_session_info(self) -> Optional[dict]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session information or None if no active session
        """
        if not self.session_manager.current_session:
            return None
        
        session = self.session_manager.current_session
        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "queries_count": len(session.queries),
            "findings_count": len(session.findings),
            "notes_count": len(session.notes)
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