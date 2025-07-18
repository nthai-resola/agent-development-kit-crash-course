"""
Main entry point for the Smart Research Assistant.
"""

import asyncio
import logging
from typing import Optional

from config import Config
from models.data_models import ResearchSession
from agents.orchestrator_agent import OrchestratorAgent
from agents.search_agent import SearchAgent
from agents.verification_agent import VerificationAgent
from agents.summary_agent import SummaryAgent
from agents.analysis_agent import AnalysisAgent
from agents.specialized_agent import SpecializedAgent
from storage.file_storage_provider import FileStorageProvider
from session_manager import SessionManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


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
        self.storage_provider = FileStorageProvider(base_path=Config.STORAGE_PATH)
        
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


async def main_cli():
    """Main function for running the Smart Research Assistant CLI."""
    setup_logging()
    
    try:
        assistant = SmartResearchAssistant()
        console = Console()
        console.print(Panel("Welcome to the Smart Research Assistant!", title="[bold green]SRA[/bold green]"))

        sessions = await assistant.session_manager.list_sessions()
        if sessions:
            console.print("Available sessions:")
            for i, session in enumerate(sessions):
                console.print(f"  {i+1}. {session['topic']} ({session['session_id']})")
            
            choice = Prompt.ask("Select a session to load (number) or press Enter for a new session", default="")
            if choice.isdigit() and 0 < int(choice) <= len(sessions):
                await assistant.session_manager.load_session(sessions[int(choice)-1]['session_id'])
                console.print(f"Loaded session: {assistant.session_manager.current_session.topic}")
        
        if not assistant.session_manager.current_session:
            topic = Prompt.ask("Enter a topic for your new research session")
            await assistant.start_session(topic)
            console.print(f"Started new session: {topic}")
            
        while True:
            query = Prompt.ask("\nWhat would you like to research? (type 'exit' to end)")
            if query.lower() == 'exit':
                break
            
            with console.status("[bold green]Researching...[/bold green]"):
                result = await assistant.process_query(query)

            if result["success"]:
                console.print(Panel(result["response"], title="[bold blue]Research Results[/bold blue]"))
            else:
                console.print(Panel(f"An error occurred: {result.get('error', 'Unknown error')}", title="[bold red]Error[/bold red]"))
    
    except Exception as e:
        console.print(Panel(f"An unexpected error occurred: {e}", title="[bold red]Fatal Error[/bold red]"))
        logging.error(f"Error running Smart Research Assistant: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main_cli())