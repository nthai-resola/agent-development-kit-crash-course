"""
Main entry point for the Smart Research Assistant.
"""

import asyncio
import logging
import argparse
import os
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
from rich.text import Text
from tools.agent_logger import AgentLogLevel


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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Smart Research Assistant')
    
    # Agent logging options
    parser.add_argument('--agent-log', choices=['none', 'basic', 'info', 'debug'], 
                      default=os.environ.get('AGENT_LOG_LEVEL', 'info').lower(),
                      help='Agent logging level (default: info)')
    
    parser.add_argument('--hide-agent-logs', action='store_true',
                      help='Hide agent logs from terminal output')
    
    # Processing mode options
    parser.add_argument('--mode', choices=['search-only', 'auto-detect', 'full-processing'],
                      default=os.environ.get('PROCESSING_MODE', 'search-only'),
                      help='Processing mode (default: search-only)')
    
    # Non-interactive mode
    parser.add_argument('--topic', type=str, help='Topic for a new research session in non-interactive mode')
    parser.add_argument('--query', type=str, help='Query to process in non-interactive mode')

    return parser.parse_args()


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
    # Parse command line arguments
    args = parse_args()
    
    # Update configuration based on command line arguments
    Config.AGENT_LOG_LEVEL = args.agent_log.upper()
    Config.AGENT_LOG_TO_TERMINAL = not args.hide_agent_logs
    Config.PROCESSING_MODE = args.mode
    
    # Setup logging
    setup_logging()
    console = Console()
    
    try:
        # Display banner with mode information
        title_style = "bold green"
        console.print(Panel(
            Text("Smart Research Assistant", style=title_style),
            subtitle=f"Processing Mode: {Config.PROCESSING_MODE} | Agent Logs: {'HIDDEN' if args.hide_agent_logs else args.agent_log.upper()}"
        ))
        
        assistant = SmartResearchAssistant()

        # Non-interactive mode
        if args.query:
            topic = args.topic or "Non-interactive Session"
            await assistant.start_session(topic)
            console.print(f"Started new session: {topic}")

            with console.status("[bold green]Researching...[/bold green]"):
                result = await assistant.process_query(args.query)

            if result["success"]:
                console.print(Panel(result["response"], title="[bold blue]Research Results[/bold blue]"))
                
                # Display summary of agents used
                if not args.hide_agent_logs:
                    agents_text = ", ".join(result.get("agents_used", []))
                    console.print(Text(f"Agents used: {agents_text}", style="dim"))
            else:
                # Enhanced error display for non-interactive mode
                error_message = result.get("error", "Unknown error")
                console.print(Panel(f"I apologize, but I wasn't able to process your query successfully. Error: {error_message}", title="[bold red]Research Results[/bold red]"))
            return

        # Interactive mode
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
                
                # Display summary of agents used
                if not args.hide_agent_logs:
                    agents_text = ", ".join(result.get("agents_used", []))
                    console.print(Text(f"Agents used: {agents_text}", style="dim"))
            else:
                # Enhanced error display with more specific messages
                error_message = result.get("error", "Unknown error")
                suggestion = ""
                
                # Add helpful suggestions based on error patterns
                if "HttpError" in error_message and "400" in error_message:
                    suggestion = "\nTry rephrasing your query or checking for typos."
                elif "HttpError" in error_message and "429" in error_message:
                    suggestion = "\nAPI rate limit reached. Please try again later."
                elif "HttpError" in error_message and ("401" in error_message or "403" in error_message):
                    suggestion = "\nAPI authentication issue. Please check your API keys."
                
                console.print(Panel(f"I apologize, but I wasn't able to process your query successfully. Please try rephrasing your question or check if all required services are available.{suggestion}", title="[bold red]Research Results[/bold red]"))
    
    except Exception as e:
        console.print(Panel(f"An unexpected error occurred: {e}", title="[bold red]Fatal Error[/bold red]"))
        logging.error(f"Error running Smart Research Assistant: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main_cli())