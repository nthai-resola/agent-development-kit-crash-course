"""
Google Search Tool for the Smart Research Assistant.
"""

import logging
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from ..config import Config
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import Config

logger = logging.getLogger(__name__)


class GoogleSearchTool:
    """
    A tool for performing Google searches.
    """

    def __init__(self):
        """
        Initialize the Google Search Tool.
        """
        self.api_key = Config.GOOGLE_API_KEY
        self.cse_id = Config.GOOGLE_CSE_ID
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize the search query to make it compatible with the Google Search API.
        
        Args:
            query: The original search query
            
        Returns:
            A sanitized version of the query
        """
        if not query:
            return ""
            
        # Trim whitespace
        query = query.strip()
        
        # Add spaces between camelCase/PascalCase words (e.g., pydanticAI -> pydantic AI)
        query = re.sub(r'([a-z])([A-Z])', r'\1 \2', query)
        
        # Remove special characters that might cause issues
        query = re.sub(r'[^\w\s\-\.]', ' ', query)
        
        # Replace multiple spaces with a single space
        query = re.sub(r'\s+', ' ', query)
        
        return query

    async def search(self, query: str, num_results: int = 10) -> list:
        """
        Perform a Google search.
        
        Args:
            query: The search query
            num_results: The number of results to return (default: 10, max: 10 for free tier)
            
        Returns:
            A list of search result items
        """
        # Cap num_results to avoid API errors
        if num_results > 10:
            logger.warning(f"Requested {num_results} results but Google API free tier limits to 10. Capping to 10.")
            num_results = 10
            
        logger.info(f"Performing Google search for: {query[:100]}...")
        try:
            # Ensure the query is valid
            if not query or not query.strip():
                logger.error("Search query is empty or contains only whitespace")
                return []
            
            # Sanitize the query
            sanitized_query = self._sanitize_query(query)
            if not sanitized_query:
                logger.error(f"Query '{query}' was sanitized to an empty string")
                return []
                
            logger.info(f"Sanitized query: {sanitized_query[:100]}")
                
            result = self.service.cse().list(
                q=sanitized_query,
                cx=self.cse_id,
                num=num_results,
                safe='off'  # Disable SafeSearch filtering
            ).execute()

            items = result.get('items', [])
            logger.info(f"Search returned {len(items)} results")
            return items
            
        except HttpError as e:
            # More specific error handling based on HTTP error codes
            status_code = e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else None
            if status_code == 400:
                logger.error(f"Bad request error (400) in Google search. Check query format and API parameters: {e}")
                logger.error(f"Query was: '{sanitized_query}', CSE ID: '{self.cse_id}', num_results: {num_results}")
            elif status_code == 401 or status_code == 403:
                logger.error(f"Authentication error ({status_code}) in Google search. Check API key: {e}")
            elif status_code == 429:
                logger.error(f"Quota exceeded (429) in Google search. Check API usage limits: {e}")
            else:
                logger.error(f"An HTTP error ({status_code}) occurred during Google search: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Google search: {e}")
            return []


# Add a test function to help diagnose issues
async def test_search_api(query="python programming", api_key=None, cse_id=None):
    """
    Test the Google Custom Search API with a simple query.
    This can help diagnose API configuration issues.
    
    Args:
        query: Test query to use (default: "python programming")
        api_key: Optional API key to override the one in Config
        cse_id: Optional CSE ID to override the one in Config
    """
    try:
        # Use provided credentials or fall back to Config
        key = api_key or Config.GOOGLE_API_KEY
        cx = cse_id or Config.GOOGLE_CSE_ID
        
        print(f"Testing Google Custom Search API with:")
        print(f"- Query: {query}")
        print(f"- API Key: {key[:5]}...{key[-4:] if len(key) > 8 else ''}")
        print(f"- CSE ID: {cx}")
        
        # Create a service instance
        service = build("customsearch", "v1", developerKey=key)
        
        # Make the search request with minimal parameters
        result = service.cse().list(
            q=query,
            cx=cx,
            num=1  # Request just 1 result to minimize quota usage
        ).execute()
        
        # Check if the API returned results
        if 'items' in result and len(result['items']) > 0:
            print(f"✅ SUCCESS: API returned {len(result['items'])} results")
            print(f"First result title: {result['items'][0]['title']}")
            return True
        else:
            print("⚠️ API request succeeded but returned no results")
            return False
            
    except HttpError as e:
        print(f"❌ ERROR: HTTP error occurred: {e}")
        status_code = e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else "unknown"
        print(f"Status code: {status_code}")
        
        if status_code == 400:
            print("Possible causes:")
            print("- Invalid CSE ID")
            print("- Malformed query")
            print("- API restrictions in Google Cloud Console")
        elif status_code in [401, 403]:
            print("Possible causes:")
            print("- Invalid API key")
            print("- API key doesn't have Custom Search API enabled")
            print("- API key has restrictions (IP, referrer, etc.)")
        elif status_code == 429:
            print("Possible causes:")
            print("- Daily quota exceeded")
            print("- Rate limit exceeded")
            
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False


# If run directly as a script, test the API
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_api()) 