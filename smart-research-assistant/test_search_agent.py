#!/usr/bin/env python3
"""
Test script to verify the fixed SearchAgent functionality
"""

import asyncio
import logging
from agents.search_agent import SearchAgent
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def test_search_agent():
    """Test the SearchAgent with a simple query"""
    try:
        # Initialize the search agent with the default model
        agent = SearchAgent(Config.SEARCH_MODEL)
        
        # Simple query for testing
        query = "Python programming language features"
        
        logger.info(f"Testing SearchAgent with query: {query}")
        
        # Process the query
        result = await agent.process(query)
        
        # Log the result
        if result["success"]:
            logger.info("Search successful!")
            logger.info(f"Confidence: {result['confidence']}")
            logger.info(f"Sources: {result['metadata']['sources']}")
            logger.info("\nContent preview:")
            
            # Print the first 500 characters of the content
            content_preview = result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"]
            print(content_preview)
        else:
            logger.error(f"Search failed: {result['content']}")
        
        return result["success"]
    except Exception as e:
        logger.error(f"Error in test_search_agent: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(test_search_agent()) 