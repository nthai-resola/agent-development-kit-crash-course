"""
Tests for session management in the Orchestrator Agent.
"""

import asyncio
from datetime import datetime

# Import will be resolved at runtime when used as a package
try:
    from ..agents.orchestrator_agent import OrchestratorAgent
    from ..models.data_models import ResearchSession, ResearchQuery, QueryResult, ResearchFinding
    from ..storage.storage_provider import StorageProvider
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from agents.orchestrator_agent import OrchestratorAgent
    from models.data_models import ResearchSession, ResearchQuery, QueryResult, ResearchFinding
    from storage.storage_provider import StorageProvider


class MockStorageProvider(StorageProvider):
    """Mock storage provider for testing."""
    
    def __init__(self):
        self.sessions = {}
    
    async def save_session(self, session: ResearchSession) -> bool:
        self.sessions[session.session_id] = session
        return True
    
    async def load_session(self, session_id: str) -> ResearchSession:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def list_sessions(self):
        return [{"session_id": sid, "topic": session.topic} 
                for sid, session in self.sessions.items()]
    
    async def session_exists(self, session_id: str) -> bool:
        return session_id in self.sessions


if __name__ == "__main__":
    # Run a simple test without pytest
    async def simple_test():
        storage = MockStorageProvider()
        orchestrator = OrchestratorAgent(model="test-model", storage_provider=storage)
        
        print("=== Testing Session Management ===")
        
        # Test session creation and context
        print("\n1. Testing session creation with metadata...")
        metadata = {"source": "web", "user_id": "test-user"}
        session_id = await orchestrator.create_session("Test Topic", metadata)
        print(f"Created session: {session_id}")
        print(f"Session context metadata: {orchestrator.session_context['metadata']}")
        assert orchestrator.session_context["metadata"] == metadata
        print("✓ Session creation with metadata successful")
        
        # Test session context initialization
        print("\n2. Testing session context initialization...")
        assert orchestrator.session_context["topic"] == "Test Topic"
        assert orchestrator.session_context["total_queries"] == 0
        assert "Test Topic" in orchestrator.session_state["active_topics"]
        print("✓ Session context initialization successful")
        
        # Test adding a finding
        print("\n3. Testing adding a finding...")
        await orchestrator.add_finding_to_session(
            title="Test Finding",
            content="This is a test finding.",
            sources=["test.com"],
            categories=["Test"]
        )
        assert len(orchestrator.current_session.findings) == 1
        assert orchestrator.current_session.findings[0].title == "Test Finding"
        assert len(orchestrator.session_state["accumulated_findings"]) == 1
        print("✓ Adding finding successful")
        
        # Test exporting
        print("\n4. Testing session export...")
        export = await orchestrator.export_session("markdown")
        print(f"Export success: {export['success']}")
        print(export["data"][:200] + "...")  # Print first 200 chars
        assert export["success"] is True
        assert "# Research Session: Test Topic" in export["data"]
        assert "Test Finding" in export["data"]
        print("✓ Session export successful")
        
        # Test creating another session
        print("\n5. Testing creating another session...")
        session_id2 = await orchestrator.create_session("Second Topic")
        assert orchestrator.current_session.topic == "Second Topic"
        print(f"Created second session: {session_id2}")
        print("✓ Creating second session successful")
        
        # Test switching sessions
        print("\n6. Testing switching sessions...")
        await orchestrator.switch_session(session_id)
        assert orchestrator.current_session.session_id == session_id
        assert orchestrator.current_session.topic == "Test Topic"
        print("✓ Switching sessions successful")
        
        # Test listing sessions
        print("\n7. Testing listing sessions...")
        sessions = await orchestrator.list_sessions()
        print(f"Found {len(sessions)} sessions")
        assert len(sessions) == 2
        print("✓ Listing sessions successful")
        
        # Test deleting a session
        print("\n8. Testing deleting a session...")
        await orchestrator.delete_session(session_id2)
        sessions = await orchestrator.list_sessions()
        assert len(sessions) == 1
        print("✓ Deleting session successful")
        
        # Test user preferences tracking
        print("\n9. Testing user preferences tracking...")
        await orchestrator.process_query("Give me a bullet point list of AI technologies")
        assert orchestrator.session_state["user_preferences"]["output_format"] == "bullet_points"
        print("✓ User preferences tracking successful")
        
        print("\nAll tests completed successfully!")
    
    asyncio.run(simple_test())