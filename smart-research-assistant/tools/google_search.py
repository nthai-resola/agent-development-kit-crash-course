"""
Google Search Tool for the Smart Research Assistant.
"""

import logging
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

    async def search(self, query: str, num_results: int = 20) -> list:
        """
        Perform a Google search.
        """
        logger.info(f"Performing Google search for: {query[:100]}...")
        try:
            result = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=num_results
            ).execute()

            return result.get('items', [])
        except HttpError as e:
            logger.error(f"An HTTP error occurred during Google search: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Google search: {e}")
            return [] 