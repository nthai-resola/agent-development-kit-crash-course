"""
Agent Logger for the Smart Research Assistant.

This module provides tools for logging agent activities to the terminal with proper formatting.
"""

import logging
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

try:
    from ..config import Config
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import Config

# Set up the Rich console for terminal output
console = Console()


class AgentLogLevel(Enum):
    """Log levels for agent activities."""
    NONE = 0    # No agent logs
    BASIC = 1   # Only basic agent activations and completions
    INFO = 2    # Standard agent activities and decisions
    DEBUG = 3   # Detailed agent operations and internal decisions


class AgentLogger:
    """
    Logger for agent activities with rich formatting for the terminal.
    """
    
    def __init__(self, agent_name: str, agent_type: str = None):
        """
        Initialize the agent logger.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of the agent (e.g., 'search', 'verification')
        """
        self.agent_name = agent_name
        self.agent_type = agent_type or agent_name.replace('Agent', '').lower()
        self.logger = logging.getLogger(f"agent.{agent_type if agent_type else agent_name}")
        
        # Determine log level from config
        self.log_level = self._get_log_level()
        self.to_terminal = Config.AGENT_LOG_TO_TERMINAL
        
    def _get_log_level(self) -> AgentLogLevel:
        """Convert string log level to enum."""
        level_map = {
            "NONE": AgentLogLevel.NONE,
            "BASIC": AgentLogLevel.BASIC,
            "INFO": AgentLogLevel.INFO,
            "DEBUG": AgentLogLevel.DEBUG
        }
        return level_map.get(Config.AGENT_LOG_LEVEL.upper(), AgentLogLevel.INFO)
    
    def _get_style(self) -> str:
        """Get style for agent logs based on agent type."""
        styles = {
            "orchestrator": "bold blue",
            "search": "bold green",
            "verification": "bold yellow",
            "summary": "bold magenta",
            "analysis": "bold cyan"
        }
        return styles.get(self.agent_type.lower(), "bold")
    
    def _timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.now().strftime("%H:%M:%S")
    
    def _should_log(self, level: AgentLogLevel) -> bool:
        """Check if the given log level should be logged."""
        return self.log_level.value >= level.value and self.to_terminal
    
    def start(self, task: str, context: Optional[Dict[str, Any]] = None):
        """
        Log the start of an agent activity.
        
        Args:
            task: Description of the task
            context: Optional context for the task
        """
        # Always log to the Python logger
        self.logger.info(f"Starting: {task}")
        
        if self._should_log(AgentLogLevel.BASIC):
            style = self._get_style()
            msg = Text(f"[{self._timestamp()}] {self.agent_name} started: {task}")
            msg.stylize(style)
            console.print(msg)
    
    def complete(self, task: str, result: Optional[str] = None):
        """
        Log the completion of an agent activity.
        
        Args:
            task: Description of the task
            result: Optional brief result summary
        """
        self.logger.info(f"Completed: {task}")
        
        if self._should_log(AgentLogLevel.BASIC):
            style = self._get_style()
            msg = Text(f"[{self._timestamp()}] {self.agent_name} completed: {task}")
            if result:
                msg.append(f" → {result}")
            msg.stylize(style)
            console.print(msg)
    
    def info(self, message: str):
        """
        Log an informational message.
        
        Args:
            message: The message to log
        """
        self.logger.info(message)
        
        if self._should_log(AgentLogLevel.INFO):
            style = self._get_style()
            msg = Text(f"[{self._timestamp()}] {self.agent_name}: {message}")
            msg.stylize(style)
            console.print(msg)
    
    def debug(self, message: str):
        """
        Log a debug message.
        
        Args:
            message: The debug message to log
        """
        self.logger.debug(message)
        
        if self._should_log(AgentLogLevel.DEBUG):
            style = self._get_style()
            msg = Text(f"[{self._timestamp()}] {self.agent_name} (debug): {message}")
            msg.stylize(style)
            console.print(msg)
    
    def error(self, message: str, exception: Optional[Exception] = None):
        """
        Log an error message.
        
        Args:
            message: The error message
            exception: Optional exception that caused the error
        """
        if exception:
            self.logger.error(message, exc_info=exception)
        else:
            self.logger.error(message)
        
        if self.to_terminal and self.log_level != AgentLogLevel.NONE:
            msg = Text(f"[{self._timestamp()}] {self.agent_name} ERROR: {message}")
            msg.stylize("bold red")
            console.print(msg)
            
            if exception and self._should_log(AgentLogLevel.DEBUG):
                console.print(Text(f"Exception: {str(exception)}", style="red"))
    
    def decision(self, decision: str, reason: str = None):
        """
        Log an agent decision.
        
        Args:
            decision: The decision made by the agent
            reason: Optional reason for the decision
        """
        log_msg = f"Decision: {decision}"
        if reason:
            log_msg += f" (Reason: {reason})"
        self.logger.info(log_msg)
        
        if self._should_log(AgentLogLevel.INFO):
            style = self._get_style()
            msg = Text(f"[{self._timestamp()}] {self.agent_name} decided: {decision}")
            if reason:
                msg.append(f"\n└── Reason: {reason}")
            msg.stylize(style)
            console.print(msg)


# Create a global orchestrator logger instance for convenience
orchestrator_logger = AgentLogger("OrchestratorAgent", "orchestrator") 