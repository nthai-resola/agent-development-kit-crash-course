"""
Basic tests to verify the project structure and core components.
"""

import pytest
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_models import (
    ResearchSession, ResearchQuery, QueryResult, ResearchFinding, UserNote
)
from config import Config


def test_research_session_creation():
    """Test that ResearchSession can be created with default values."""
    session = ResearchSession()
    
    assert session.session_id is not None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
    assert session.topic == ""
    assert len(session.queries) == 0
    assert len(session.findings) == 0
    assert len(session.notes) == 0


def test_research_session_with_topic():
    """Test that ResearchSession can be created with a topic."""
    topic = "AI Research"
    session = ResearchSession(topic=topic)
    
    assert session.topic == topic


def test_query_result_creation():
    """Test that QueryResult can be created with default values."""
    result = QueryResult()
    
    assert result.result_id is not None
    assert result.source == ""
    assert result.content == ""
    assert result.confidence == 0.0
    assert result.verified is False
    assert isinstance(result.metadata, dict)
    assert isinstance(result.timestamp, datetime)


def test_research_query_creation():
    """Test that ResearchQuery can be created with default values."""
    query = ResearchQuery()
    
    assert query.query_id is not None
    assert isinstance(query.timestamp, datetime)
    assert query.text == ""
    assert query.agent == ""
    assert len(query.results) == 0


def test_research_finding_creation():
    """Test that ResearchFinding can be created with default values."""
    finding = ResearchFinding()
    
    assert finding.finding_id is not None
    assert isinstance(finding.timestamp, datetime)
    assert finding.title == ""
    assert finding.content == ""
    assert len(finding.sources) == 0
    assert len(finding.categories) == 0


def test_user_note_creation():
    """Test that UserNote can be created with default values."""
    note = UserNote()
    
    assert note.note_id is not None
    assert isinstance(note.timestamp, datetime)
    assert note.content == ""
    assert len(note.related_findings) == 0


def test_config_model_config():
    """Test that Config returns model configuration."""
    model_config = Config.get_model_config()
    
    assert isinstance(model_config, dict)
    assert "orchestrator" in model_config
    assert "search" in model_config
    assert "verification" in model_config
    assert "summary" in model_config
    assert "analysis" in model_config


def test_session_update_timestamp():
    """Test that session timestamp can be updated."""
    session = ResearchSession()
    original_time = session.updated_at
    
    # Small delay to ensure timestamp difference
    import time
    time.sleep(0.01)
    
    session.update_timestamp()
    assert session.updated_at > original_time