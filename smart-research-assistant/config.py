"""
Configuration management for the Smart Research Assistant.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from models.enums import ProcessingMode

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Smart Research Assistant."""
    
    # Default model configurations
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai:gpt-4")
    ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)
    SEARCH_MODEL = os.getenv("SEARCH_MODEL", DEFAULT_MODEL)
    VERIFICATION_MODEL = os.getenv("VERIFICATION_MODEL", DEFAULT_MODEL)
    SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", DEFAULT_MODEL)
    ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", DEFAULT_MODEL)

    # Processing mode configuration
    PROCESSING_MODE = os.getenv("PROCESSING_MODE", "search-only")  # search-only, auto-detect, full-processing
    ENABLE_SMART_DETECTION = bool(os.getenv("ENABLE_SMART_DETECTION", "true"))
    SEARCH_ONLY_KEYWORDS = os.getenv("SEARCH_ONLY_KEYWORDS", "find,search,look up,information")
    
    # Processing mode descriptions:
    # - search-only: Only use the search agent unless other agents are explicitly requested.
    #   This is the fastest mode and uses fewer resources.
    # - auto-detect: Use query analysis to determine which agents to invoke based on
    #   intent detection. More adaptive but still efficient.
    # - full-processing: Use all available agents for every query to provide the most
    #   comprehensive results. Highest resource usage but most thorough.
    
    # Agent logging configuration
    AGENT_LOG_LEVEL = os.getenv("AGENT_LOG_LEVEL", "INFO")  # Options: NONE, BASIC, INFO, DEBUG
    AGENT_LOG_TO_TERMINAL = os.getenv("AGENT_LOG_TO_TERMINAL", "true").lower() == "true"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")  # SerpAPI key for search
    
    # Storage configuration
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file")
    STORAGE_PATH = os.getenv("STORAGE_PATH", "./data/sessions")
    
    # Application settings
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "smart_research_assistant.log")
    
    @classmethod
    def get_model_config(cls) -> Dict[str, str]:
        """Get model configuration for all agents."""
        return {
            "orchestrator": cls.ORCHESTRATOR_MODEL,
            "search": cls.SEARCH_MODEL,
            "verification": cls.VERIFICATION_MODEL,
            "summary": cls.SUMMARY_MODEL,
            "analysis": cls.ANALYSIS_MODEL,
        }
    
    @classmethod
    def validate_processing_mode(cls) -> bool:
        """Validate the processing mode configuration."""
        valid_modes = [mode.value for mode in ProcessingMode]
        if cls.PROCESSING_MODE not in valid_modes:
            print(f"Invalid PROCESSING_MODE: {cls.PROCESSING_MODE}. Must be one of {valid_modes}")
            return False
        return True

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        required_keys = [
            "OPENAI_API_KEY",
            "SERPAPI_API_KEY",
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"Missing required configuration: {', '.join(missing_keys)}")
            return False
        
        if not cls.validate_processing_mode():
            return False

        return True