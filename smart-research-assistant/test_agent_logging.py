#!/usr/bin/env python3
"""
Test script for agent logging functionality.
"""

import asyncio
import logging
import os
from rich.console import Console

from config import Config
from tools.agent_logger import AgentLogger, AgentLogLevel
from agents.orchestrator_agent import OrchestratorAgent
from agents.search_agent import SearchAgent
from storage.file_storage_provider import FileStorageProvider


# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Set up Rich console
console = Console()


async def test_agent_logging():
    """Test the agent logging functionality with different levels."""
    console.print("[bold]Agent Logging Test[/bold]")
    
    # Override config for testing
    Config.AGENT_LOG_TO_TERMINAL = True
    
    # Create test loggers
    test_logger = AgentLogger("TestAgent", "test")
    console.print("\n[bold]Testing Basic level:[/bold]")
    
    # Set to BASIC level
    Config.AGENT_LOG_LEVEL = "BASIC"
    test_logger._get_log_level()  # Refresh log level
    
    test_logger.start("basic level test")
    await asyncio.sleep(0.5)  # Simulate some work
    test_logger.complete("basic level test", "completed")
    
    # This should not be displayed at BASIC level
    test_logger.info("This is additional info that shouldn't appear at BASIC level")
    test_logger.debug("This is debug info that shouldn't appear at BASIC level")
    
    console.print("\n[bold]Testing INFO level:[/bold]")
    
    # Set to INFO level
    Config.AGENT_LOG_LEVEL = "INFO"
    test_logger._get_log_level()  # Refresh log level
    
    test_logger.start("info level test")
    await asyncio.sleep(0.5)  # Simulate some work
    test_logger.info("Processing information...")
    test_logger.info("Making a decision...")
    test_logger.decision("chose option A", "it was the best match for the criteria")
    await asyncio.sleep(0.5)  # Simulate more work
    test_logger.complete("info level test", "completed with INFO messages")
    
    console.print("\n[bold]Testing DEBUG level:[/bold]")
    
    # Set to DEBUG level
    Config.AGENT_LOG_LEVEL = "DEBUG"
    test_logger._get_log_level()  # Refresh log level
    
    test_logger.start("debug level test")
    test_logger.debug("Initializing components...")
    await asyncio.sleep(0.3)
    test_logger.debug("Setting up parameters: x=10, y=20")
    test_logger.info("Main process started")
    await asyncio.sleep(0.3)
    test_logger.debug("Processing step 1/3 complete")
    test_logger.debug("Processing step 2/3 complete")
    test_logger.debug("Processing step 3/3 complete")
    test_logger.info("Processing complete")
    test_logger.complete("debug level test", "completed with DEBUG messages")
    
    console.print("\n[bold]Testing Error handling:[/bold]")
    try:
        raise ValueError("Test error")
    except ValueError as e:
        test_logger.error("An error occurred during processing", e)
    
    console.print("\n[bold]Testing NONE level (should show no agent logs):[/bold]")
    
    # Set to NONE level
    Config.AGENT_LOG_LEVEL = "NONE"
    test_logger._get_log_level()  # Refresh log level
    
    test_logger.start("none level test")
    test_logger.info("This should not appear")
    test_logger.complete("none level test", "completed silently")
    
    console.print("\n[bold green]✓[/bold green] Agent logging tests completed")


async def test_with_real_agents():
    """Test logging with actual agent interactions."""
    console.print("\n[bold]Testing with real agents:[/bold]")
    
    # Set to INFO level for real agent test
    Config.AGENT_LOG_LEVEL = "INFO"
    Config.AGENT_LOG_TO_TERMINAL = True
    
    # Initialize storage provider
    storage_provider = FileStorageProvider(base_path="./data/sessions")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(storage_provider=storage_provider)
    
    # Register a search agent with the orchestrator
    search_agent = SearchAgent(model="openai:gpt-4")
    orchestrator.register_agent(search_agent, "search")
    
    # Process a simple query
    console.print("\n[bold]Processing query with agents:[/bold]")
    
    # This will only work if you have valid API keys set up
    # Otherwise, it will show the error handling capabilities of the logger
    try:
        result = await orchestrator.process_query("What is Python programming language?")
        
        if result["success"]:
            console.print("\n[bold green]✓[/bold green] Query processed successfully")
        else:
            console.print(f"\n[bold red]✗[/bold red] Query processing failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] Error during agent test: {str(e)}")


async def main():
    """Run the tests."""
    try:
        # Test the basic logger functionality
        await test_agent_logging()
        
        # Only run real agent test if API keys are available
        if Config.OPENAI_API_KEY and Config.SERPAPI_API_KEY:
            await test_with_real_agents()
        else:
            console.print("\n[yellow]Skipping real agent test - API keys not configured[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]Error in test: {e}[/bold red]")
        logger.error(f"Test error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 