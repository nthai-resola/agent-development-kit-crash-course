"""
Configuration management for the Smart Research Assistant.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

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
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    
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
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        required_keys = [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY", 
            "GOOGLE_CSE_ID"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"Missing required configuration: {', '.join(missing_keys)}")
            return False
        
        return True