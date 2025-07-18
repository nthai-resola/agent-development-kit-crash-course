"""
Orchestrator Agent for the Smart Research Assistant.

The Orchestrator Agent serves as the central coordinator that manages the overall
research workflow, delegates tasks to specialized agents, and maintains conversation context.
"""

import logging
import asyncio
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
        
        # Enhanced session context tracking
        self.session_context: Dict[str, Any] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        self.session_state: Dict[str, Any] = {
            "active_topics": [],
            "research_focus": "",
            "last_query_type": "",
            "accumulated_findings": [],
            "user_preferences": {}
        }
        
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
            
            # Prepare response data
            response_data = {
                "success": True,
                "response": response,
                "session_id": session_id,
                "query_id": research_query.query_id,
                "agents_used": list(required_agents),
                "timestamp": datetime.now().isoformat()
            }
            
            # Update session context after processing (Requirement 4.3)
            await self.update_session_context(query, response_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_session(self, topic: str = "", metadata: Dict[str, Any] = None) -> str:
        """
        Create a new research session.
        
        Args:
            topic: Optional topic for the research session
            metadata: Optional metadata to associate with the session
            
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
            
            # Initialize session context and state for the new session
            self._initialize_session_context(topic, metadata)
            
            # Save session if storage provider is available
            if self.storage_provider:
                await self.storage_provider.save_session(self.current_session)
            
            logger.info(f"Created new research session: {session_id} with topic: {topic}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def _initialize_session_context(self, topic: str = "", metadata: Dict[str, Any] = None):
        """
        Initialize session context and state for a new session.
        
        Args:
            topic: The research topic for the session
            metadata: Optional metadata for the session
        """
        # Initialize session context
        self.session_context = {
            "session_id": self.current_session.session_id,
            "topic": topic,
            "total_queries": 0,
            "total_findings": 0,
            "recent_queries": [],
            "key_findings": [],
            "session_duration": 0,  # hours
            "last_activity": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Initialize session state
        self.session_state = {
            "active_topics": [topic] if topic else [],
            "research_focus": topic,
            "last_query_type": "",
            "accumulated_findings": [],
            "user_preferences": {
                "preferred_sources": [],
                "output_format": "detailed",
                "verification_level": "standard"
            }
        }
        
        # Clear interaction history
        self.interaction_history = []
        
        logger.debug(f"Initialized context for new session with topic: {topic}")
    
    async def load_session(self, session_id: str) -> bool:
        """
        Load an existing research session and restore context.
        
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
                
                # Restore session context and state (Requirement 4.2)
                await self._restore_session_context(session)
                
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
            
            # If session_id is provided and different from current, load that session first
            if session_id and session_id != self.current_session.session_id:
                temp_session = self.current_session
                if await self.load_session(session_id):
                    self.current_session = temp_session
                    self.current_session.session_id = session_id
                else:
                    logger.error(f"Failed to load session {session_id} for saving")
                    return False
            
            success = await self.storage_provider.save_session(self.current_session)
            if success:
                logger.info(f"Saved research session: {self.current_session.session_id}")
            else:
                logger.error(f"Failed to save session: {self.current_session.session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available research sessions.
        
        Returns:
            List of session metadata dictionaries
        """
        try:
            if not self.storage_provider:
                logger.warning("No storage provider available for listing sessions")
                return []
            
            sessions = await self.storage_provider.list_sessions()
            logger.info(f"Listed {len(sessions)} research sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a research session.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if session was deleted successfully, False otherwise
        """
        try:
            if not self.storage_provider:
                logger.warning("No storage provider available for deleting session")
                return False
            
            success = await self.storage_provider.delete_session(session_id)
            
            # If we deleted the current session, clear it
            if success and self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                self._initialize_empty_context()
                logger.info(f"Deleted current session: {session_id}")
            elif success:
                logger.info(f"Deleted session: {session_id}")
            else:
                logger.warning(f"Failed to delete session: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def switch_session(self, session_id: str) -> bool:
        """
        Switch to a different research session.
        
        Args:
            session_id: The ID of the session to switch to
            
        Returns:
            True if session was switched successfully, False otherwise
        """
        try:
            # Save current session if it exists
            if self.current_session:
                await self.save_session()
            
            # Load the new session
            success = await self.load_session(session_id)
            if success:
                logger.info(f"Switched to session: {session_id}")
            else:
                logger.warning(f"Failed to switch to session: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error switching to session {session_id}: {str(e)}")
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
        # Enhanced query analysis with more sophisticated pattern matching
        query_lower = query.lower()
        required_agents = []
        
        # Context-aware agent selection based on query intent and session state
        
        # Search agent is needed for most queries, but not all
        search_keywords = [
            "find", "search", "look up", "information", "data", "research", 
            "gather", "collect", "discover", "locate", "sources"
        ]
        search_patterns = [
            "what is", "who is", "where is", "when did", "how does", 
            "tell me about", "find information", "learn about"
        ]
        
        # Default to including search unless it's clearly not needed
        needs_search = True
        
        # If we have an active session with accumulated findings and the query
        # is only about summarizing or analyzing existing information, we might not need search
        if self.current_session and self.current_session.findings:
            if "existing" in query_lower or "findings" in query_lower:
                if not any(keyword in query_lower for keyword in search_keywords):
                    needs_search = False
        
        if needs_search:
            required_agents.append("search")
        
        # Verification agent detection with enhanced patterns
        verification_keywords = [
            "verify", "fact", "check", "accurate", "reliable", "source", "credible",
            "trustworthy", "validate", "confirm", "authentic", "legitimate", "true",
            "false", "misleading", "accuracy", "correct", "incorrect", "wrong"
        ]
        verification_patterns = [
            "is it true", "is this accurate", "can you verify", "fact check", 
            "is this correct", "how reliable", "is this source", "can i trust"
        ]
        
        if any(keyword in query_lower for keyword in verification_keywords) or \
           any(pattern in query_lower for pattern in verification_patterns):
            required_agents.append("verification")
        
        # Summary agent detection with enhanced patterns
        summary_keywords = [
            "summarize", "summary", "overview", "organize", "key points", "brief",
            "digest", "condense", "shorten", "main ideas", "takeaways", "highlights",
            "outline", "recap", "tldr", "synopsis", "abstract", "extract"
        ]
        summary_patterns = [
            "give me a summary", "summarize this", "what are the key points",
            "main takeaways", "brief overview", "in summary", "to summarize",
            "can you condense", "highlight the important"
        ]
        
        if any(keyword in query_lower for keyword in summary_keywords) or \
           any(pattern in query_lower for pattern in summary_patterns):
            required_agents.append("summary")
        
        # Analysis agent detection with enhanced patterns
        analysis_keywords = [
            "analyze", "analysis", "data", "statistics", "chart", "graph", "translate",
            "compare", "contrast", "evaluate", "assess", "interpret", "examine",
            "investigate", "explore", "visualize", "visualization", "trend", "pattern",
            "correlation", "causation", "relationship", "insight", "metric"
        ]
        analysis_patterns = [
            "analyze this", "what does the data show", "create a chart", 
            "visualize this", "translate this", "compare these", "find patterns",
            "identify trends", "statistical analysis", "data interpretation"
        ]
        
        if any(keyword in query_lower for keyword in analysis_keywords) or \
           any(pattern in query_lower for pattern in analysis_patterns):
            required_agents.append("analysis")
        
        # Consider session context for agent selection
        if self.current_session:
            # If we have active research findings, we might need summary or analysis
            if self.current_session.findings and "summary" not in required_agents and \
               ("findings" in query_lower or "results" in query_lower):
                required_agents.append("summary")
            
            # If the query references previous information, we might need verification
            if "previous" in query_lower or "earlier" in query_lower or "before" in query_lower:
                if "verification" not in required_agents:
                    required_agents.append("verification")
        
        # Ensure we have at least one agent
        if not required_agents:
            required_agents.append("search")  # Default to search if no clear intent
        
        logger.debug(f"Enhanced query analysis determined required agents: {required_agents}")
        return required_agents
    
    async def _coordinate_agents(self, query: str, required_agents: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Coordinate execution of specialized agents with enhanced error handling and fallback mechanisms.
        
        This method orchestrates the execution of specialized agents based on the query requirements,
        handles errors gracefully, and implements fallback strategies when agents fail.
        
        Args:
            query: The user's research query
            required_agents: List of agent types to coordinate
            
        Returns:
            Dictionary mapping agent types to their results
        """
        results = {}
        retry_attempts = {}  # Track retry attempts for each agent
        max_retries = 1  # Maximum number of retries per agent
        
        # Determine execution order based on dependencies
        # For example, search should generally come before verification
        execution_order = self._determine_agent_execution_order(required_agents)
        
        # Execute agents in the determined order
        for agent_type in execution_order:
            try:
                if agent_type in self.specialized_agents:
                    agent = self.specialized_agents[agent_type]
                    logger.debug(f"Executing {agent_type} agent for query")
                    
                    # Prepare enhanced context for the specialized agent
                    agent_context = self._prepare_agent_context(query, agent_type, results)
                    
                    # Execute the specialized agent with timeout protection
                    try:
                        # In a real implementation, we would use asyncio.wait_for with a timeout
                        # For now, we'll just call the process method directly
                        result = await agent.process(query, agent_context)
                        
                        # Validate result structure
                        if not isinstance(result, dict) or "success" not in result:
                            logger.warning(f"{agent_type} agent returned invalid result structure")
                            result = {
                                "success": False,
                                "error": f"Invalid result structure from {agent_type} agent",
                                "content": str(result) if result else ""
                            }
                        
                        # Store the result
                        results[agent_type] = result
                        
                        # If the agent failed but we haven't reached max retries, try again with modified query
                        if not result.get("success", False) and retry_attempts.get(agent_type, 0) < max_retries:
                            retry_attempts[agent_type] = retry_attempts.get(agent_type, 0) + 1
                            logger.info(f"Retrying {agent_type} agent with modified query (attempt {retry_attempts[agent_type]})")
                            
                            # Simplify or modify the query for retry
                            modified_query = self._simplify_query_for_retry(query, agent_type)
                            
                            # Retry with modified query
                            retry_result = await agent.process(modified_query, agent_context)
                            
                            # If retry succeeded, use that result instead
                            if retry_result.get("success", False):
                                results[agent_type] = retry_result
                                logger.info(f"Retry for {agent_type} agent succeeded")
                    
                    except asyncio.TimeoutError:
                        logger.error(f"{agent_type} agent timed out")
                        results[agent_type] = {
                            "success": False,
                            "error": f"{agent_type} agent timed out",
                            "content": ""
                        }
                        
                else:
                    logger.warning(f"Required agent not registered: {agent_type}")
                    results[agent_type] = {
                        "success": False,
                        "error": f"Agent {agent_type} not available",
                        "content": ""
                    }
                    
                    # Try to use fallback if available
                    fallback_result = await self._try_agent_fallback(query, agent_type)
                    if fallback_result.get("success", False):
                        results[agent_type] = fallback_result
                        logger.info(f"Used fallback for {agent_type} agent")
                    
            except Exception as e:
                logger.error(f"Error executing {agent_type} agent: {str(e)}")
                results[agent_type] = {
                    "success": False,
                    "error": str(e),
                    "content": ""
                }
                
                # Record the exception for debugging
                import traceback
                logger.debug(f"Exception details for {agent_type} agent: {traceback.format_exc()}")
        
        # Check if we need to compensate for failed agents
        await self._compensate_for_failed_agents(query, results, required_agents)
        
        return results
        
    def _determine_agent_execution_order(self, required_agents: List[str]) -> List[str]:
        """
        Determine the optimal execution order for agents based on dependencies.
        
        Args:
            required_agents: List of agent types to coordinate
            
        Returns:
            Ordered list of agent types
        """
        # Define agent dependencies (which agents should run before others)
        dependencies = {
            "verification": ["search"],  # Verification typically needs search results first
            "summary": ["search"],       # Summary often needs search results
            "analysis": ["search"]       # Analysis may need search results
        }
        
        # Start with search if it's required
        ordered_agents = []
        remaining_agents = set(required_agents)
        
        # First add agents with no dependencies
        for agent in required_agents:
            if agent not in dependencies or not any(dep in required_agents for dep in dependencies.get(agent, [])):
                if agent in remaining_agents:
                    ordered_agents.append(agent)
                    remaining_agents.remove(agent)
        
        # Then add agents with dependencies
        while remaining_agents:
            for agent in list(remaining_agents):
                deps = dependencies.get(agent, [])
                if not deps or all(dep not in remaining_agents for dep in deps):
                    ordered_agents.append(agent)
                    remaining_agents.remove(agent)
                    break
            else:
                # If we can't satisfy all dependencies, just add the remaining agents
                # This can happen if there are circular dependencies
                ordered_agents.extend(list(remaining_agents))
                break
        
        logger.debug(f"Agent execution order: {ordered_agents}")
        return ordered_agents
    
    def _prepare_agent_context(self, query: str, agent_type: str, 
                              current_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare enhanced context for a specialized agent, including results from other agents.
        
        Args:
            query: The user's research query
            agent_type: The type of agent being executed
            current_results: Results from agents that have already executed
            
        Returns:
            Context dictionary for the agent
        """
        # Start with basic context
        context = {
            "session_id": self.current_session.session_id if self.current_session else None,
            "session_context": self.get_session_context(),
            "query_type": agent_type,
            "original_query": query
        }
        
        # Add results from other agents that have already executed
        other_agent_results = {}
        for other_agent, result in current_results.items():
            if result.get("success", False):
                other_agent_results[other_agent] = {
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {})
                }
        
        if other_agent_results:
            context["other_agent_results"] = other_agent_results
        
        # Add agent-specific context
        if agent_type == "verification" and "search" in current_results:
            # For verification, include search results directly
            search_result = current_results.get("search", {})
            if search_result.get("success", False):
                context["search_results"] = search_result.get("content", "")
                context["sources_to_verify"] = search_result.get("metadata", {}).get("sources", [])
        
        elif agent_type == "summary" and "search" in current_results:
            # For summary, include content to summarize
            search_result = current_results.get("search", {})
            if search_result.get("success", False):
                context["content_to_summarize"] = search_result.get("content", "")
        
        elif agent_type == "analysis":
            # For analysis, include any data that needs to be analyzed
            if "search" in current_results and current_results["search"].get("success", False):
                context["data_to_analyze"] = current_results["search"].get("content", "")
                context["data_sources"] = current_results["search"].get("metadata", {}).get("sources", [])
        
        # Add user preferences if available
        if self.current_session and "user_preferences" in self.session_state:
            context["user_preferences"] = self.session_state["user_preferences"]
        
        return context
    
    def _simplify_query_for_retry(self, query: str, agent_type: str) -> str:
        """
        Simplify or modify a query for retry when an agent fails.
        
        Args:
            query: The original query
            agent_type: The type of agent that failed
            
        Returns:
            Modified query for retry
        """
        # Simple implementation - in a real system, this would be more sophisticated
        query_lower = query.lower()
        
        # Remove complex parts of the query based on agent type
        if agent_type == "search":
            # For search, simplify by focusing on key nouns and removing qualifiers
            words = query_lower.split()
            # Keep only longer words that are likely important nouns
            important_words = [w for w in words if len(w) > 3 and w not in ["what", "when", "where", "which", "how", "why"]]
            if important_words:
                return " ".join(important_words)
        
        elif agent_type == "verification":
            # For verification, focus on the core fact to verify
            if "verify" in query_lower:
                # Extract what comes after "verify"
                parts = query_lower.split("verify", 1)
                if len(parts) > 1:
                    return f"Is it true that {parts[1].strip()}?"
            
        elif agent_type == "summary":
            # For summary, make the request more direct
            return f"Summarize the key points about {query}"
        
        elif agent_type == "analysis":
            # For analysis, simplify to basic analysis request
            return f"Analyze the data about {query}"
        
        # If no specific simplification, just return a shorter version
        if len(query) > 100:
            return query[:100]
        
        return query
    
    async def _try_agent_fallback(self, query: str, missing_agent_type: str) -> Dict[str, Any]:
        """
        Try to use a fallback mechanism when a specialized agent is not available.
        
        Args:
            query: The user's research query
            missing_agent_type: The type of agent that's missing
            
        Returns:
            Result dictionary from fallback mechanism
        """
        # This is a placeholder for a real fallback implementation
        # In a production system, this would implement actual fallback logic
        
        # For now, we'll just return a failure result
        return {
            "success": False,
            "error": f"No fallback available for {missing_agent_type} agent",
            "content": "",
            "fallback_attempted": True
        }
    
    async def _compensate_for_failed_agents(self, query: str, 
                                           results: Dict[str, Dict[str, Any]], 
                                           required_agents: List[str]) -> None:
        """
        Compensate for failed agents by adjusting results or using alternatives.
        
        Args:
            query: The user's research query
            results: Current results from agents
            required_agents: List of required agent types
        """
        # Check if any critical agents failed
        failed_agents = [
            agent_type for agent_type in required_agents
            if agent_type in results and not results[agent_type].get("success", False)
        ]
        
        if not failed_agents:
            return
        
        logger.info(f"Compensating for failed agents: {failed_agents}")
        
        # Try to compensate for specific agent failures
        for failed_agent in failed_agents:
            # If search failed but was required, this is critical
            if failed_agent == "search":
                # Add a note to the results explaining the limitation
                results["search"]["content"] = "I wasn't able to search for information on this topic. " \
                                             "Please try again later or rephrase your query."
                results["search"]["compensated"] = True
            
            # If verification failed but search succeeded, we can still provide unverified results
            elif failed_agent == "verification" and "search" in results and results["search"].get("success", False):
                results["verification"] = {
                    "success": True,
                    "content": "I couldn't verify this information, but here are the search results. " \
                              "Please consider these findings preliminary until they can be verified.",
                    "confidence": 0.3,
                    "verified": False,
                    "compensated": True
                }
            
            # If summary failed but search succeeded, we can provide raw results
            elif failed_agent == "summary" and "search" in results and results["search"].get("success", False):
                results["summary"] = {
                    "success": True,
                    "content": "I couldn't generate a summary, but here are the key points from the search results.",
                    "confidence": 0.4,
                    "compensated": True
                }
            
            # If analysis failed, we can suggest manual analysis
            elif failed_agent == "analysis":
                results["analysis"] = {
                    "success": True,
                    "content": "I couldn't perform the requested analysis. " \
                              "You may want to examine the raw data yourself or try a different analysis approach.",
                    "confidence": 0.2,
                    "compensated": True
                }
    
    async def _synthesize_response(self, query: str, agent_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Synthesize a coherent response from multiple agent results.
        
        This method combines results from different specialized agents into a unified,
        coherent response that addresses the user's query. It handles successful results,
        partial results, and errors in a user-friendly way.
        
        Args:
            query: The original user query
            agent_results: Results from specialized agents
            
        Returns:
            Synthesized response string
        """
        # Track which agents succeeded and failed
        successful_agents = [
            agent_type for agent_type, result in agent_results.items()
            if result.get("success", False)
        ]
        failed_agents = [
            agent_type for agent_type, result in agent_results.items()
            if not result.get("success", False)
        ]
        
        # If all agents failed, return a helpful error message
        if not successful_agents:
            return "I apologize, but I wasn't able to process your query successfully. " \
                   "Please try rephrasing your question or check if all required services are available."
        
        # Determine the response format based on user preferences
        response_format = "detailed"
        if self.current_session and "user_preferences" in self.session_state:
            response_format = self.session_state["user_preferences"].get("output_format", "detailed")
        
        # Start building the response
        response_parts = []
        
        # Add an introduction based on the query and successful agents
        intro = self._generate_response_introduction(query, successful_agents)
        if intro:
            response_parts.append(intro)
        
        # Process search results first if available
        if "search" in agent_results and agent_results["search"].get("success", False):
            search_content = agent_results["search"].get("content", "")
            if search_content:
                # For brief format, we might not show the search results directly
                if response_format != "brief":
                    search_section = self._format_search_results(search_content, response_format)
                    response_parts.append(search_section)
        
        # Add verification results if available
        if "verification" in agent_results and agent_results["verification"].get("success", False):
            verification_content = agent_results["verification"].get("content", "")
            if verification_content:
                verification_section = self._format_verification_results(
                    verification_content, 
                    agent_results["verification"].get("confidence", 0.0),
                    response_format
                )
                response_parts.append(verification_section)
        
        # Add summary results if available
        if "summary" in agent_results and agent_results["summary"].get("success", False):
            summary_content = agent_results["summary"].get("content", "")
            if summary_content:
                # For detailed format, we might show the summary at the beginning
                if response_format == "detailed":
                    # Move the summary to the beginning for better readability
                    summary_section = self._format_summary_results(summary_content, response_format)
                    # Insert after introduction
                    if len(response_parts) > 0:
                        response_parts.insert(1, summary_section)
                    else:
                        response_parts.append(summary_section)
                else:
                    summary_section = self._format_summary_results(summary_content, response_format)
                    response_parts.append(summary_section)
        
        # Add analysis results if available
        if "analysis" in agent_results and agent_results["analysis"].get("success", False):
            analysis_content = agent_results["analysis"].get("content", "")
            if analysis_content:
                analysis_section = self._format_analysis_results(analysis_content, response_format)
                response_parts.append(analysis_section)
        
        # Add information about compensated or fallback results
        compensated_agents = [
            agent_type for agent_type, result in agent_results.items()
            if result.get("success", False) and result.get("compensated", False)
        ]
        
        if compensated_agents:
            compensation_note = "Note: Some information could not be fully processed. " \
                               f"The following aspects were limited: {', '.join(compensated_agents)}."
            response_parts.append(compensation_note)
        
        # Add error information if needed (only in detailed format)
        if failed_agents and response_format == "detailed":
            errors = [
                f"{agent_type.title()}: {agent_results[agent_type].get('error', 'Unknown error')}"
                for agent_type in failed_agents
            ]
            
            error_section = "**Limitations:**\n" + "\n".join(errors)
            response_parts.append(error_section)
        
        # Add a conclusion or next steps suggestion
        conclusion = self._generate_response_conclusion(query, successful_agents, failed_agents)
        if conclusion:
            response_parts.append(conclusion)
        
        # Combine all parts into a coherent response
        return "\n\n".join(response_parts)
    
    def _generate_response_introduction(self, query: str, successful_agents: List[str]) -> str:
        """Generate an introduction for the response based on the query and successful agents."""
        # Simple implementation - in a real system, this would use an LLM
        
        # If we have a summary agent, we'll let it handle the introduction
        if "summary" in successful_agents:
            return ""
        
        # For search-only queries
        if successful_agents == ["search"]:
            return "Here's what I found about your query:"
        
        # For verification queries
        if "verification" in successful_agents:
            return "I've researched and verified information about your query:"
        
        # For analysis queries
        if "analysis" in successful_agents:
            return "I've analyzed the information related to your query:"
        
        # Default introduction
        return "Here's information about your query:"
    
    def _format_search_results(self, content: str, response_format: str) -> str:
        """Format search results based on the response format."""
        if response_format == "brief":
            # For brief format, just return the content without a header
            return content
        elif response_format == "bullet_points":
            # Convert to bullet points if not already
            if not content.strip().startswith("- ") and not content.strip().startswith("* "):
                lines = content.strip().split("\n")
                bullet_points = [f"- {line}" for line in lines if line.strip()]
                return "**Search Results:**\n" + "\n".join(bullet_points)
            else:
                return "**Search Results:**\n" + content
        else:  # detailed
            return "**Search Results:**\n" + content
    
    def _format_verification_results(self, content: str, confidence: float, response_format: str) -> str:
        """Format verification results based on the response format and confidence."""
        # Add confidence indicator
        confidence_indicator = ""
        if confidence > 0.8:
            confidence_indicator = "(High confidence)"
        elif confidence > 0.5:
            confidence_indicator = "(Medium confidence)"
        else:
            confidence_indicator = "(Low confidence)"
        
        if response_format == "brief":
            return f"**Verification {confidence_indicator}:**\n{content}"
        elif response_format == "bullet_points":
            # Convert to bullet points if not already
            if not content.strip().startswith("- ") and not content.strip().startswith("* "):
                lines = content.strip().split("\n")
                bullet_points = [f"- {line}" for line in lines if line.strip()]
                return f"**Verification {confidence_indicator}:**\n" + "\n".join(bullet_points)
            else:
                return f"**Verification {confidence_indicator}:**\n" + content
        else:  # detailed
            return f"**Verification {confidence_indicator}:**\n" + content
    
    def _format_summary_results(self, content: str, response_format: str) -> str:
        """Format summary results based on the response format."""
        if response_format == "brief":
            return content  # For brief format, the summary is the main content
        else:
            return "**Summary:**\n" + content
    
    def _format_analysis_results(self, content: str, response_format: str) -> str:
        """Format analysis results based on the response format."""
        if response_format == "brief":
            # For brief format, extract just the key findings
            if "key findings" in content.lower():
                parts = content.lower().split("key findings")
                if len(parts) > 1:
                    return "**Key Findings:**\n" + parts[1]
            return "**Analysis:**\n" + content
        else:
            return "**Analysis:**\n" + content
    
    def _generate_response_conclusion(self, query: str, successful_agents: List[str], 
                                     failed_agents: List[str]) -> str:
        """Generate a conclusion for the response based on the query and agent results."""
        # If all agents succeeded, no need for a conclusion
        if not failed_agents:
            return ""
        
        # If critical agents failed, suggest alternatives
        if "search" in failed_agents:
            return "I had difficulty finding information on this topic. " \
                   "You might want to try rephrasing your query or checking other sources."
        
        if "verification" in failed_agents and "search" in successful_agents:
            return "Note: I couldn't fully verify all the information provided. " \
                   "Please consider cross-checking important facts from other reliable sources."
        
        return ""
    
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
    
    async def _restore_session_context(self, session: ResearchSession):
        """
        Restore session context and state from a loaded session.
        
        Args:
            session: The loaded research session
        """
        try:
            # Clear current context
            self.session_context.clear()
            self.interaction_history.clear()
            
            # Restore interaction history from queries (Requirement 4.2)
            for query in session.queries:
                interaction = {
                    "timestamp": query.timestamp.isoformat(),
                    "query": query.text,
                    "agent": query.agent,
                    "results": [
                        {
                            "source": result.source,
                            "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                            "confidence": result.confidence,
                            "verified": result.verified
                        }
                        for result in query.results
                    ]
                }
                self.interaction_history.append(interaction)
            
            # Restore session state
            self.session_state = {
                "active_topics": self._extract_topics_from_session(session),
                "research_focus": session.topic,
                "last_query_type": self._get_last_query_type(session),
                "accumulated_findings": [
                    {
                        "title": finding.title,
                        "content": finding.content[:100] + "..." if len(finding.content) > 100 else finding.content,
                        "categories": finding.categories,
                        "sources": finding.sources
                    }
                    for finding in session.findings
                ],
                "user_preferences": self._extract_user_preferences(session)
            }
            
            # Build session context for continuity
            self.session_context = {
                "session_id": session.session_id,
                "topic": session.topic,
                "total_queries": len(session.queries),
                "total_findings": len(session.findings),
                "recent_queries": [q.text for q in session.queries[-5:]] if session.queries else [],
                "key_findings": [f.title for f in session.findings[-3:]] if session.findings else [],
                "session_duration": (datetime.now() - session.created_at).total_seconds() / 3600,  # hours
                "last_activity": session.updated_at.isoformat()
            }
            
            logger.info(f"Restored context for session {session.session_id}: "
                       f"{len(self.interaction_history)} interactions, "
                       f"{len(self.session_state['accumulated_findings'])} findings")
            
        except Exception as e:
            logger.error(f"Error restoring session context: {str(e)}")
            # Initialize with empty context if restoration fails
            self._initialize_empty_context()
    
    def _extract_topics_from_session(self, session: ResearchSession) -> List[str]:
        """Extract active topics from session queries and findings."""
        topics = set()
        
        # Add main topic
        if session.topic:
            topics.add(session.topic)
        
        # Extract topics from recent queries (simple keyword extraction)
        for query in session.queries[-10:]:  # Last 10 queries
            words = query.text.lower().split()
            # Simple heuristic: look for capitalized words or common research terms
            for word in words:
                if len(word) > 4 and (word.istitle() or word in ["research", "analysis", "study", "data"]):
                    topics.add(word.lower())
        
        # Extract topics from findings
        for finding in session.findings:
            # Add categories as topics
            for category in finding.categories:
                topics.add(category.lower())
            
            # Extract potential topics from titles
            words = finding.title.split()
            for word in words:
                if len(word) > 4 and word.istitle():
                    topics.add(word.lower())
        
        return list(topics)[:10]  # Limit to 10 topics
    
    def _get_last_query_type(self, session: ResearchSession) -> str:
        """Determine the type of the last query in the session."""
        if not session.queries:
            return ""
        
        last_query = session.queries[-1].text.lower()
        
        if any(word in last_query for word in ["summarize", "summary", "overview"]):
            return "summary"
        elif any(word in last_query for word in ["verify", "fact", "check", "accurate"]):
            return "verification"
        elif any(word in last_query for word in ["analyze", "analysis", "data", "statistics"]):
            return "analysis"
        else:
            return "search"
    
    def _extract_user_preferences(self, session: ResearchSession) -> Dict[str, Any]:
        """Extract user preferences from session history."""
        preferences = {
            "preferred_sources": [],
            "output_format": "detailed",
            "verification_level": "standard"
        }
        
        # Analyze query patterns to infer preferences
        query_texts = [q.text.lower() for q in session.queries]
        
        # Check for format preferences
        if any("bullet" in q or "list" in q for q in query_texts):
            preferences["output_format"] = "bullet_points"
        elif any("brief" in q or "short" in q for q in query_texts):
            preferences["output_format"] = "brief"
        elif any("detailed" in q or "comprehensive" in q for q in query_texts):
            preferences["output_format"] = "detailed"
        
        # Check for verification preferences
        if any("verify" in q or "fact" in q or "check" in q for q in query_texts):
            preferences["verification_level"] = "high"
        
        # Extract preferred sources
        source_indicators = ["from", "source", "website", "prefer"]
        for query in query_texts:
            if any(indicator in query for indicator in source_indicators):
                # Simple heuristic to extract domain names
                words = query.split()
                for word in words:
                    if "." in word and "/" in word:  # Likely a URL
                        domain = word.split("/")[0]
                        if domain not in preferences["preferred_sources"]:
                            preferences["preferred_sources"].append(domain)
        
        return preferences
    
    def _initialize_empty_context(self):
        """Initialize empty context when restoration fails."""
        self.session_context = {}
        self.interaction_history = []
        self.session_state = {
            "active_topics": [],
            "research_focus": "",
            "last_query_type": "",
            "accumulated_findings": [],
            "user_preferences": {}
        }
    
    async def update_session_context(self, query: str, results: Dict[str, Any]):
        """
        Update session context after processing a query.
        
        Args:
            query: The processed query
            results: The results from processing the query
        """
        try:
            # Add to interaction history (Requirement 4.3)
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "agent": self.name,
                "results": results.get("agents_used", []),
                "success": results.get("success", False)
            }
            self.interaction_history.append(interaction)
            
            # Keep only last 50 interactions to manage memory
            if len(self.interaction_history) > 50:
                self.interaction_history = self.interaction_history[-50:]
            
            # Update session state
            query_lower = query.lower()
            
            # Update last query type
            if any(word in query_lower for word in ["summarize", "summary", "overview"]):
                self.session_state["last_query_type"] = "summary"
            elif any(word in query_lower for word in ["verify", "fact", "check"]):
                self.session_state["last_query_type"] = "verification"
            elif any(word in query_lower for word in ["analyze", "analysis", "data"]):
                self.session_state["last_query_type"] = "analysis"
            else:
                self.session_state["last_query_type"] = "search"
            
            # Extract and add new topics
            words = query.split()
            new_topics = [word.lower() for word in words if len(word) > 4 and word.istitle()]
            for topic in new_topics:
                if topic not in self.session_state["active_topics"]:
                    self.session_state["active_topics"].append(topic)
            
            # Keep only last 10 topics
            self.session_state["active_topics"] = self.session_state["active_topics"][-10:]
            
            # Update user preferences based on query
            self._update_user_preferences(query)
            
            # Update session context
            if self.current_session:
                self.session_context.update({
                    "total_queries": len(self.current_session.queries),
                    "total_findings": len(self.current_session.findings),
                    "recent_queries": [q.text for q in self.current_session.queries[-5:]] if self.current_session.queries else [],
                    "last_activity": datetime.now().isoformat()
                })
            
            logger.debug(f"Updated session context: {len(self.interaction_history)} interactions")
            
        except Exception as e:
            logger.error(f"Error updating session context: {str(e)}")
    
    def _update_user_preferences(self, query: str):
        """
        Update user preferences based on the current query.
        
        Args:
            query: The user's query
        """
        query_lower = query.lower()
        
        # Update format preferences
        if "bullet" in query_lower or "list" in query_lower:
            self.session_state["user_preferences"]["output_format"] = "bullet_points"
        elif "brief" in query_lower or "short" in query_lower:
            self.session_state["user_preferences"]["output_format"] = "brief"
        elif "detailed" in query_lower or "comprehensive" in query_lower:
            self.session_state["user_preferences"]["output_format"] = "detailed"
        
        # Update verification preferences
        if "verify" in query_lower or "fact" in query_lower or "check" in query_lower:
            self.session_state["user_preferences"]["verification_level"] = "high"
        
        # Extract preferred sources
        source_indicators = ["from", "source", "website", "prefer"]
        if any(indicator in query_lower for indicator in source_indicators):
            # Simple heuristic to extract domain names
            words = query_lower.split()
            for word in words:
                if "." in word and "/" in word:  # Likely a URL
                    domain = word.split("/")[0]
                    if domain not in self.session_state["user_preferences"]["preferred_sources"]:
                        self.session_state["user_preferences"]["preferred_sources"].append(domain)
    
    async def add_finding_to_session(self, title: str, content: str, sources: List[str], categories: List[str] = None) -> bool:
        """
        Add a research finding to the current session.
        
        Args:
            title: Title of the finding
            content: Content of the finding
            sources: List of sources for the finding
            categories: Optional categories for the finding
            
        Returns:
            True if finding was added successfully, False otherwise
        """
        try:
            if not self.current_session:
                logger.warning("No current session to add finding to")
                return False
            
            from ..models.data_models import ResearchFinding
            
            finding = ResearchFinding(
                title=title,
                content=content,
                sources=sources,
                categories=categories or [],
                timestamp=datetime.now()
            )
            
            self.current_session.findings.append(finding)
            self.current_session.update_timestamp()
            
            # Update accumulated findings in session state
            self.session_state["accumulated_findings"].append({
                "title": title,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "categories": categories or [],
                "sources": sources
            })
            
            # Update session context
            self.session_context["total_findings"] = len(self.current_session.findings)
            self.session_context["key_findings"] = [f.title for f in self.current_session.findings[-3:]]
            
            # Save session if storage provider is available
            if self.storage_provider:
                await self.storage_provider.save_session(self.current_session)
            
            logger.info(f"Added finding '{title}' to session {self.current_session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding finding to session: {str(e)}")
            return False
    
    async def add_note_to_session(self, content: str, related_findings: List[str] = None) -> bool:
        """
        Add a user note to the current session.
        
        Args:
            content: Content of the note
            related_findings: Optional list of related finding IDs
            
        Returns:
            True if note was added successfully, False otherwise
        """
        try:
            if not self.current_session:
                logger.warning("No current session to add note to")
                return False
            
            from ..models.data_models import UserNote
            
            note = UserNote(
                content=content,
                related_findings=related_findings or [],
                timestamp=datetime.now()
            )
            
            self.current_session.notes.append(note)
            self.current_session.update_timestamp()
            
            # Save session if storage provider is available
            if self.storage_provider:
                await self.storage_provider.save_session(self.current_session)
            
            logger.info(f"Added note to session {self.current_session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding note to session: {str(e)}")
            return False
    
    def get_session_context(self) -> Dict[str, Any]:
        """
        Get the current session context for continuity between interactions.
        
        Returns:
            Dictionary containing session context information
        """
        return {
            "session_context": self.session_context.copy(),
            "session_state": self.session_state.copy(),
            "recent_interactions": self.interaction_history[-5:] if self.interaction_history else [],
            "has_active_session": self.current_session is not None
        }
    
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
            "num_notes": len(self.current_session.notes),
            "active_topics": self.session_state.get("active_topics", []),
            "research_focus": self.session_state.get("research_focus", ""),
            "last_query_type": self.session_state.get("last_query_type", "")
        }
    
    async def export_session(self, format_type: str = "markdown") -> Dict[str, Any]:
        """
        Export the current session in the specified format.
        
        Args:
            format_type: The format to export to (markdown, json, text)
            
        Returns:
            Dictionary with export data and metadata
        """
        try:
            if not self.current_session:
                logger.warning("No current session to export")
                return {
                    "success": False,
                    "error": "No active session to export",
                    "data": None
                }
            
            if format_type == "json":
                # Export as JSON (simplified for now)
                export_data = {
                    "session_id": self.current_session.session_id,
                    "topic": self.current_session.topic,
                    "created_at": self.current_session.created_at.isoformat(),
                    "updated_at": self.current_session.updated_at.isoformat(),
                    "queries": [
                        {
                            "query_id": q.query_id,
                            "text": q.text,
                            "timestamp": q.timestamp.isoformat(),
                            "results": [
                                {
                                    "source": r.source,
                                    "content": r.content,
                                    "confidence": r.confidence,
                                    "verified": r.verified
                                }
                                for r in q.results
                            ]
                        }
                        for q in self.current_session.queries
                    ],
                    "findings": [
                        {
                            "finding_id": f.finding_id,
                            "title": f.title,
                            "content": f.content,
                            "sources": f.sources,
                            "categories": f.categories,
                            "timestamp": f.timestamp.isoformat()
                        }
                        for f in self.current_session.findings
                    ],
                    "notes": [
                        {
                            "note_id": n.note_id,
                            "content": n.content,
                            "related_findings": n.related_findings,
                            "timestamp": n.timestamp.isoformat()
                        }
                        for n in self.current_session.notes
                    ]
                }
                
                return {
                    "success": True,
                    "format": "json",
                    "data": export_data,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif format_type == "markdown":
                # Export as Markdown
                md_lines = [
                    f"# Research Session: {self.current_session.topic or 'Untitled Research'}",
                    f"Session ID: {self.current_session.session_id}",
                    f"Created: {self.current_session.created_at.isoformat()}",
                    f"Last Updated: {self.current_session.updated_at.isoformat()}",
                    "",
                    "## Research Findings",
                    ""
                ]
                
                # Add findings
                if self.current_session.findings:
                    for finding in self.current_session.findings:
                        md_lines.extend([
                            f"### {finding.title}",
                            "",
                            finding.content,
                            "",
                            "**Sources:**",
                            ", ".join(finding.sources),
                            "",
                            "**Categories:**",
                            ", ".join(finding.categories),
                            "",
                            f"*Added on {finding.timestamp.isoformat()}*",
                            ""
                        ])
                else:
                    md_lines.append("*No findings recorded yet.*\n")
                
                # Add queries
                md_lines.extend([
                    "## Research Queries",
                    ""
                ])
                
                if self.current_session.queries:
                    for query in self.current_session.queries:
                        md_lines.extend([
                            f"### Query: {query.text}",
                            f"*{query.timestamp.isoformat()}*",
                            ""
                        ])
                        
                        if query.results:
                            for result in query.results:
                                md_lines.extend([
                                    f"**Source: {result.source}**",
                                    f"Confidence: {result.confidence}",
                                    f"Verified: {'Yes' if result.verified else 'No'}",
                                    "",
                                    result.content,
                                    ""
                                ])
                        else:
                            md_lines.append("*No results recorded for this query.*\n")
                else:
                    md_lines.append("*No queries recorded yet.*\n")
                
                # Add notes
                md_lines.extend([
                    "## Notes",
                    ""
                ])
                
                if self.current_session.notes:
                    for note in self.current_session.notes:
                        related = ", ".join(note.related_findings) if note.related_findings else "None"
                        md_lines.extend([
                            f"### Note ({note.timestamp.isoformat()})",
                            "",
                            note.content,
                            "",
                            f"*Related findings: {related}*",
                            ""
                        ])
                else:
                    md_lines.append("*No notes recorded yet.*\n")
                
                return {
                    "success": True,
                    "format": "markdown",
                    "data": "\n".join(md_lines),
                    "timestamp": datetime.now().isoformat()
                }
                
            elif format_type == "text":
                # Export as plain text
                text_lines = [
                    f"RESEARCH SESSION: {self.current_session.topic or 'Untitled Research'}",
                    f"Session ID: {self.current_session.session_id}",
                    f"Created: {self.current_session.created_at.isoformat()}",
                    f"Last Updated: {self.current_session.updated_at.isoformat()}",
                    "",
                    "RESEARCH FINDINGS",
                    "----------------",
                    ""
                ]
                
                # Add findings
                if self.current_session.findings:
                    for finding in self.current_session.findings:
                        text_lines.extend([
                            f"FINDING: {finding.title}",
                            "",
                            finding.content,
                            "",
                            f"Sources: {', '.join(finding.sources)}",
                            f"Categories: {', '.join(finding.categories)}",
                            f"Added on: {finding.timestamp.isoformat()}",
                            "",
                            "-" * 40,
                            ""
                        ])
                else:
                    text_lines.extend(["No findings recorded yet.", "", "-" * 40, ""])
                
                # Add queries
                text_lines.extend([
                    "RESEARCH QUERIES",
                    "----------------",
                    ""
                ])
                
                if self.current_session.queries:
                    for query in self.current_session.queries:
                        text_lines.extend([
                            f"QUERY: {query.text}",
                            f"Time: {query.timestamp.isoformat()}",
                            ""
                        ])
                        
                        if query.results:
                            for result in query.results:
                                text_lines.extend([
                                    f"Source: {result.source}",
                                    f"Confidence: {result.confidence}",
                                    f"Verified: {'Yes' if result.verified else 'No'}",
                                    "",
                                    result.content,
                                    "",
                                    "-" * 20,
                                    ""
                                ])
                        else:
                            text_lines.extend(["No results recorded for this query.", "", "-" * 20, ""])
                else:
                    text_lines.extend(["No queries recorded yet.", "", "-" * 40, ""])
                
                # Add notes
                text_lines.extend([
                    "NOTES",
                    "-----",
                    ""
                ])
                
                if self.current_session.notes:
                    for note in self.current_session.notes:
                        related = ", ".join(note.related_findings) if note.related_findings else "None"
                        text_lines.extend([
                            f"NOTE ({note.timestamp.isoformat()})",
                            "",
                            note.content,
                            "",
                            f"Related findings: {related}",
                            "",
                            "-" * 20,
                            ""
                        ])
                else:
                    text_lines.append("No notes recorded yet.")
                
                return {
                    "success": True,
                    "format": "text",
                    "data": "\n".join(text_lines),
                    "timestamp": datetime.now().isoformat()
                }
                
            else:
                logger.warning(f"Unsupported export format: {format_type}")
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format_type}",
                    "data": None
                }
                
        except Exception as e:
            logger.error(f"Error exporting session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }