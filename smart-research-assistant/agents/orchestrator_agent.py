"""
Orchestrator Agent for the Smart Research Assistant.

The Orchestrator Agent serves as the central coordinator that manages the overall
research workflow, delegates tasks to specialized agents, and maintains conversation context.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime

# Import will be resolved at runtime when used as a package
try:
    from .base_agent import BaseResearchAgent
    from ..models.data_models import ResearchSession, ResearchQuery, QueryResult
    from ..storage.storage_provider import StorageProvider
    from ..config import Config
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.base_agent import BaseResearchAgent
    from models.data_models import ResearchSession, ResearchQuery, QueryResult
    from storage.storage_provider import StorageProvider
    from config import Config

# Set up logging
logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseResearchAgent):
    """
    The central orchestrator agent that coordinates research workflows.
    
    This agent manages the overall research process by:
    - Processing user queries and determining appropriate actions
    - Delegating tasks to specialized agents
    - Maintaining session context and state
    - Synthesizing responses from multiple agents
    """
    
    def __init__(self, model: str = None, storage_provider: StorageProvider = None):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            model: The model to use for this agent (defaults to config value)
            storage_provider: Storage provider for session management
        """
        if model is None:
            model = Config.ORCHESTRATOR_MODEL
            
        super().__init__(model, "OrchestratorAgent")
        
        self.storage_provider = storage_provider
        self.current_session: Optional[ResearchSession] = None
        self.specialized_agents: Dict[str, BaseResearchAgent] = {}
        
        # Initialize agent registry for coordination
        self._agent_capabilities = {
            "search": ["web_search", "information_gathering", "source_finding"],
            "verification": ["fact_checking", "source_validation", "cross_reference"],
            "summary": ["content_summarization", "organization", "formatting"],
            "analysis": ["data_analysis", "visualization", "entity_extraction", "translation"]
        }
        
        logger.info(f"Orchestrator Agent initialized with model: {self.model}")
    
    def _initialize_agent(self):
        """Initialize the pydantic-ai agent for the orchestrator."""
        # For now, we'll use a simple implementation
        # This will be enhanced when we integrate with pydantic-ai
        self.agent = {
            "model": self.model,
            "name": self.name,
            "initialized": True
        }
        logger.debug("Orchestrator agent initialized")
    
    async def process_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a user research query.
        
        This method analyzes the query, determines which specialized agents to invoke,
        coordinates their execution, and synthesizes the final response.
        
        Args:
            query: The user's research query
            session_id: Optional session ID to continue existing session
            
        Returns:
            Dictionary containing the processed response and metadata
        """
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Load or create session
            if session_id:
                await self.load_session(session_id)
            elif not self.current_session:
                session_id = await self.create_session()
            
            # Create research query record
            research_query = ResearchQuery(
                text=query,
                agent=self.name,
                timestamp=datetime.now()
            )
            
            # Analyze query to determine required agents
            required_agents = self._analyze_query_requirements(query)
            
            # Coordinate agent execution
            agent_results = await self._coordinate_agents(query, required_agents)
            
            # Synthesize final response
            response = await self._synthesize_response(query, agent_results)
            
            # Update query with results
            for agent_name, result in agent_results.items():
                if result.get("success", False):
                    query_result = QueryResult(
                        source=agent_name,
                        content=str(result.get("content", "")),
                        confidence=result.get("confidence", 0.0),
                        verified=result.get("verified", False),
                        metadata=result.get("metadata", {})
                    )
                    research_query.results.append(query_result)
            
            # Add query to current session
            if self.current_session:
                self.current_session.queries.append(research_query)
                self.current_session.update_timestamp()
                
                # Save session if storage provider is available
                if self.storage_provider:
                    await self.storage_provider.save_session(self.current_session)
            
            return {
                "success": True,
                "response": response,
                "session_id": session_id,
                "query_id": research_query.query_id,
                "agents_used": list(required_agents),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_session(self, topic: str = "") -> str:
        """
        Create a new research session.
        
        Args:
            topic: Optional topic for the research session
            
        Returns:
            The session ID of the newly created session
        """
        try:
            session_id = str(uuid4())
            self.current_session = ResearchSession(
                session_id=session_id,
                topic=topic,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save session if storage provider is available
            if self.storage_provider:
                await self.storage_provider.save_session(self.current_session)
            
            logger.info(f"Created new research session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    async def load_session(self, session_id: str) -> bool:
        """
        Load an existing research session.
        
        Args:
            session_id: The ID of the session to load
            
        Returns:
            True if session was loaded successfully, False otherwise
        """
        try:
            if not self.storage_provider:
                logger.warning("No storage provider available for loading session")
                return False
            
            session = await self.storage_provider.load_session(session_id)
            if session:
                self.current_session = session
                logger.info(f"Loaded research session: {session_id}")
                return True
            else:
                logger.warning(f"Session not found: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            return False
    
    async def save_session(self, session_id: str = None) -> bool:
        """
        Save the current research session.
        
        Args:
            session_id: Optional session ID (uses current session if not provided)
            
        Returns:
            True if session was saved successfully, False otherwise
        """
        try:
            if not self.storage_provider:
                logger.warning("No storage provider available for saving session")
                return False
            
            if not self.current_session:
                logger.warning("No current session to save")
                return False
            
            # Update timestamp before saving
            self.current_session.update_timestamp()
            
            success = await self.storage_provider.save_session(self.current_session)
            if success:
                logger.info(f"Saved research session: {self.current_session.session_id}")
            else:
                logger.error(f"Failed to save session: {self.current_session.session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    
    def register_agent(self, agent_type: str, agent: BaseResearchAgent):
        """
        Register a specialized agent with the orchestrator.
        
        Args:
            agent_type: The type of agent (search, verification, summary, analysis)
            agent: The agent instance to register
        """
        if agent_type not in self._agent_capabilities:
            logger.warning(f"Unknown agent type: {agent_type}")
        
        self.specialized_agents[agent_type] = agent
        logger.info(f"Registered {agent_type} agent: {agent.name}")
    
    def get_registered_agents(self) -> Dict[str, str]:
        """
        Get information about registered specialized agents.
        
        Returns:
            Dictionary mapping agent types to agent names
        """
        return {
            agent_type: agent.name 
            for agent_type, agent in self.specialized_agents.items()
        }
    
    def _analyze_query_requirements(self, query: str) -> List[str]:
        """
        Analyze a query to determine which specialized agents are needed.
        
        Args:
            query: The user's research query
            
        Returns:
            List of agent types that should be involved in processing this query
        """
        # Simple keyword-based analysis for now
        # This will be enhanced with more sophisticated NLP analysis later
        query_lower = query.lower()
        required_agents = []
        
        # Always include search agent for information gathering
        required_agents.append("search")
        
        # Check for verification keywords
        verification_keywords = ["verify", "fact", "check", "accurate", "reliable", "source"]
        if any(keyword in query_lower for keyword in verification_keywords):
            required_agents.append("verification")
        
        # Check for summary keywords
        summary_keywords = ["summarize", "summary", "overview", "organize", "key points"]
        if any(keyword in query_lower for keyword in summary_keywords):
            required_agents.append("summary")
        
        # Check for analysis keywords
        analysis_keywords = ["analyze", "analysis", "data", "statistics", "chart", "graph", "translate"]
        if any(keyword in query_lower for keyword in analysis_keywords):
            required_agents.append("analysis")
        
        logger.debug(f"Query analysis determined required agents: {required_agents}")
        return required_agents
    
    async def _coordinate_agents(self, query: str, required_agents: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Coordinate execution of specialized agents.
        
        Args:
            query: The user's research query
            required_agents: List of agent types to coordinate
            
        Returns:
            Dictionary mapping agent types to their results
        """
        results = {}
        
        for agent_type in required_agents:
            try:
                if agent_type in self.specialized_agents:
                    agent = self.specialized_agents[agent_type]
                    logger.debug(f"Executing {agent_type} agent for query")
                    
                    # Execute the specialized agent
                    result = await agent.process(query)
                    results[agent_type] = result
                    
                else:
                    logger.warning(f"Required agent not registered: {agent_type}")
                    results[agent_type] = {
                        "success": False,
                        "error": f"Agent {agent_type} not available",
                        "content": ""
                    }
                    
            except Exception as e:
                logger.error(f"Error executing {agent_type} agent: {str(e)}")
                results[agent_type] = {
                    "success": False,
                    "error": str(e),
                    "content": ""
                }
        
        return results
    
    async def _synthesize_response(self, query: str, agent_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Synthesize a coherent response from multiple agent results.
        
        Args:
            query: The original user query
            agent_results: Results from specialized agents
            
        Returns:
            Synthesized response string
        """
        # Simple synthesis for now - this will be enhanced with LLM-based synthesis
        response_parts = []
        
        # Add successful results
        for agent_type, result in agent_results.items():
            if result.get("success", False):
                content = result.get("content", "")
                if content:
                    response_parts.append(f"**{agent_type.title()} Results:**\n{content}")
        
        # Add error information if needed
        errors = [
            f"{agent_type}: {result.get('error', 'Unknown error')}"
            for agent_type, result in agent_results.items()
            if not result.get("success", False)
        ]
        
        if errors:
            response_parts.append(f"**Errors encountered:**\n" + "\n".join(errors))
        
        if not response_parts:
            return "I apologize, but I wasn't able to process your query successfully. Please try rephrasing your question or check if all required services are available."
        
        return "\n\n".join(response_parts)
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query (implementation of BaseResearchAgent interface).
        
        Args:
            query: The query to process
            context: Optional context information
            
        Returns:
            Dictionary containing the processing results
        """
        session_id = context.get("session_id") if context else None
        return await self.process_query(query, session_id)
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session information or None if no current session
        """
        if not self.current_session:
            return None
        
        return {
            "session_id": self.current_session.session_id,
            "topic": self.current_session.topic,
            "created_at": self.current_session.created_at.isoformat(),
            "updated_at": self.current_session.updated_at.isoformat(),
            "num_queries": len(self.current_session.queries),
            "num_findings": len(self.current_session.findings),
            "num_notes": len(self.current_session.notes)
        }