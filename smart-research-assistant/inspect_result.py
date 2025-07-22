#!/usr/bin/env python3
"""
Script to inspect the pydantic-ai result object
"""

import asyncio
from pydantic_ai import Agent

async def main():
    agent = Agent('openai:gpt-4o')
    result = await agent.run('Hello')
    print("Result dir:", dir(result))
    print("\nResult type:", type(result))
    
    # Try to access various attributes that might exist
    try:
        print("\nResult.__dict__:", result.__dict__)
    except Exception as e:
        print(f"Could not access __dict__: {e}")
    
    for attr in dir(result):
        if not attr.startswith('_'):
            try:
                print(f"\nResult.{attr}: {getattr(result, attr)}")
            except Exception as e:
                print(f"Could not access {attr}: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 