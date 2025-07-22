#!/usr/bin/env python3
"""
Google Search API Diagnostic Tool

This script helps diagnose issues with the Google Custom Search API configuration.
It attempts several test queries with different parameters to identify problems.
"""

import asyncio
import logging
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_search(query, api_key, cse_id, num=1):
    """Test a search query with given parameters."""
    print(f"\n===== Testing search for '{query}' =====")
    try:
        # Create service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Execute search
        print(f"Calling API with: query='{query}', cse_id='{cse_id}', num={num}")
        result = service.cse().list(
            q=query,
            cx=cse_id,
            num=num
        ).execute()
        
        # Process results
        items = result.get('items', [])
        print(f"✅ SUCCESS: API returned {len(items)} results")
        if items:
            print(f"First result: '{items[0]['title']}'")
            print(f"Link: {items[0]['link']}")
        return True
        
    except HttpError as e:
        print(f"❌ ERROR: HTTP error occurred: {e}")
        if hasattr(e, 'resp') and hasattr(e.resp, 'status'):
            print(f"Status code: {e.resp.status}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {str(e)}")
        return False


async def diagnose():
    """Run a series of diagnostic tests."""
    print("Google Search API Diagnostic Tool")
    print("================================\n")
    
    # Get credentials from environment or prompt
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key:
        api_key = input("Enter your Google API Key: ").strip()
    if not cse_id:
        cse_id = input("Enter your Google Custom Search Engine ID: ").strip()
    
    if not api_key or not cse_id:
        print("Error: API Key and CSE ID are required")
        return
    
    print(f"Using API Key: {api_key[:5]}...{api_key[-4:] if len(api_key) > 8 else ''}")
    print(f"Using CSE ID: {cse_id}")
    
    # Test 1: Simple query
    await test_search("python programming", api_key, cse_id)
    
    # Test 2: Query with spaces
    await test_search("artificial intelligence", api_key, cse_id)
    
    # Test 3: PascalCase query - the problematic one
    await test_search("PydanticAI", api_key, cse_id)
    
    # Test 4: Same query with space
    await test_search("Pydantic AI", api_key, cse_id)
    
    print("\n=== Diagnostic Tests Complete ===")
    print("If any tests succeeded, your API key and CSE ID are working correctly.")
    print("If all tests failed with 400 errors:")
    print("1. Check that your Custom Search Engine is properly configured in the Google Cloud Console")
    print("2. Verify that the CSE ID is correct")
    print("3. Ensure your API key has the Custom Search API enabled")
    print("4. Check for any API key restrictions (IP, referrer, etc.)")
    print("\nFor more information, visit: https://developers.google.com/custom-search/v1/introduction")


if __name__ == "__main__":
    asyncio.run(diagnose()) 