#!/usr/bin/env python3
"""
Simple verification script to test the basic project structure.
"""

import sys
import os
from datetime import datetime

def test_imports():
    """Test that all core modules can be imported."""
    try:
        from models.data_models import (
            ResearchSession, ResearchQuery, QueryResult, ResearchFinding, UserNote
        )
        from config import Config
        from agents.base_agent import BaseResearchAgent
        from storage.storage_provider import StorageProvider
        print("✓ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_data_models():
    """Test that data models work correctly."""
    try:
        from models.data_models import ResearchSession, ResearchQuery, QueryResult
        
        # Test ResearchSession
        session = ResearchSession(topic="Test Topic")
        assert session.session_id is not None
        assert session.topic == "Test Topic"
        assert isinstance(session.created_at, datetime)
        print("✓ ResearchSession works correctly")
        
        # Test QueryResult
        result = QueryResult(source="test.com", content="Test content", confidence=0.8)
        assert result.source == "test.com"
        assert result.content == "Test content"
        assert result.confidence == 0.8
        print("✓ QueryResult works correctly")
        
        # Test ResearchQuery
        query = ResearchQuery(text="What is AI?", agent="search")
        assert query.text == "What is AI?"
        assert query.agent == "search"
        print("✓ ResearchQuery works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Data model error: {e}")
        return False

def test_config():
    """Test that configuration works correctly."""
    try:
        from config import Config
        
        model_config = Config.get_model_config()
        assert isinstance(model_config, dict)
        assert "orchestrator" in model_config
        assert "search" in model_config
        print("✓ Config works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_base_classes():
    """Test that base classes are properly defined."""
    try:
        from agents.base_agent import BaseResearchAgent
        from storage.storage_provider import StorageProvider
        
        # Check that they are abstract classes
        assert hasattr(BaseResearchAgent, '_initialize_agent')
        assert hasattr(BaseResearchAgent, 'process')
        assert hasattr(StorageProvider, 'save_session')
        assert hasattr(StorageProvider, 'load_session')
        print("✓ Base classes are properly defined")
        
        return True
    except Exception as e:
        print(f"✗ Base class error: {e}")
        return False

def main():
    """Run all verification tests."""
    print("Smart Research Assistant - Structure Verification")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Data Models Test", test_data_models),
        ("Config Test", test_config),
        ("Base Classes Test", test_base_classes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name} failed")
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Project structure is correctly set up.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)