
import pytest
from unittest.mock import AsyncMock, patch
import os
import shutil
from models.data_models import ResearchSession
from session_manager import SessionManager
from storage.file_storage_provider import FileStorageProvider

TEST_STORAGE_PATH = "./test_sessions"

@pytest.fixture
def session_manager():
    storage_provider = FileStorageProvider(base_path=TEST_STORAGE_PATH)
    manager = SessionManager(storage_provider=storage_provider)
    yield manager
    # Teardown: remove the test sessions directory
    if os.path.exists(TEST_STORAGE_PATH):
        shutil.rmtree(TEST_STORAGE_PATH)

@pytest.mark.asyncio
async def test_create_and_load_session(session_manager):
    # Arrange
    topic = "Test Topic"

    # Act
    created_session = await session_manager.create_session(topic)
    loaded_session = await session_manager.load_session(created_session.session_id)

    # Assert
    assert created_session is not None
    assert loaded_session is not None
    assert created_session.session_id == loaded_session.session_id
    assert loaded_session.topic == topic

@pytest.mark.asyncio
async def test_list_sessions(session_manager):
    # Arrange
    await session_manager.create_session("Topic 1")
    await session_manager.create_session("Topic 2")

    # Act
    sessions = await session_manager.list_sessions()

    # Assert
    assert len(sessions) == 2

@pytest.mark.asyncio
async def test_export_session_markdown(session_manager):
    # Arrange
    session = await session_manager.create_session("Export Test")
    
    # Act
    markdown_export = await session_manager.export_session(session.session_id, "markdown")

    # Assert
    assert b"# Research Session: Export Test" in markdown_export
    assert f"**Session ID:** {session.session_id}".encode('utf-8') in markdown_export

@pytest.mark.asyncio
async def test_export_session_json(session_manager):
    # Arrange
    session = await session_manager.create_session("Export Test")
    
    # Act
    json_export = await session_manager.export_session(session.session_id, "json")

    # Assert
    import json
    data = json.loads(json_export)
    assert data["topic"] == "Export Test"
    assert data["session_id"] == session.session_id 