#!/usr/bin/env python3
"""
Google Custom Search Engine (CSE) Configuration Checker

This script verifies that your Google Custom Search Engine is properly configured.
"""

import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def check_cse_configuration():
    """Check the Google Custom Search Engine configuration."""
    print("Google CSE Configuration Checker")
    print("===============================")
    
    # Get API key and CSE ID from environment or prompt
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key:
        api_key = input("Enter your Google API Key: ").strip()
    if not cse_id:
        cse_id = input("Enter your Google Custom Search Engine ID: ").strip()
    
    if not api_key or not cse_id:
        print("Error: API Key and CSE ID are required")
        return
    
    # Construct a simple search URL
    url = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q=test"
    
    print(f"\nTesting CSE configuration...")
    print(f"API Key: {api_key[:5]}...{api_key[-4:] if len(api_key) > 8 else ''}")
    print(f"CSE ID: {cse_id}")
    
    try:
        # Make request directly using requests library instead of Google client
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4XX/5XX errors
        
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            print("\n✅ Success! Your CSE configuration is working correctly.")
            print(f"Found {len(data['items'])} search results.")
            return True
        else:
            print("\n⚠️ API request succeeded but returned no results.")
            if 'searchInformation' in data:
                print(f"Total results: {data['searchInformation'].get('totalResults', 0)}")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print("\nPossible issues:")
        if response.status_code == 400:
            print("- Invalid CSE ID format")
            print("- CSE not properly configured")
        elif response.status_code == 403:
            print("- API key doesn't have Custom Search API enabled")
            print("- API key has restrictions (IP, referrer, etc.)")
            print("- Billing not enabled for the project")
        
        try:
            error_data = response.json()
            if 'error' in error_data:
                print(f"\nError details: {error_data['error'].get('message', 'Unknown error')}")
        except:
            pass
            
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False
        
    print("\nTo fix CSE configuration issues:")
    print("1. Go to https://programmablesearchengine.google.com/")
    print("2. Verify your Custom Search Engine exists and is properly configured")
    print("3. Make sure 'Search the entire web' is enabled if you want general search results")
    print("4. Go to https://console.cloud.google.com/")
    print("5. Ensure the Custom Search API is enabled for your project")
    print("6. Verify your API key has no restrictions preventing its use")

if __name__ == "__main__":
    check_cse_configuration() 