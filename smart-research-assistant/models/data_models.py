"""
Core data models for the Smart Research Assistant.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class QueryResult:
    """Represents a single result from a research query."""
    result_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = ""
    content: str = ""
    confidence: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResearchQuery:
    """Represents a research query made by the user."""
    query_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    text: str = ""
    agent: str = ""
    results: List[QueryResult] = field(default_factory=list)


@dataclass
class ResearchFinding:
    """Represents a key finding from research."""
    finding_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    title: str = ""
    content: str = ""
    sources: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)


@dataclass
class UserNote:
    """Represents a user-added note."""
    note_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    related_findings: List[str] = field(default_factory=list)


@dataclass
class ResearchSession:
    """Represents a complete research session."""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    topic: str = ""
    queries: List[ResearchQuery] = field(default_factory=list)
    findings: List[ResearchFinding] = field(default_factory=list)
    notes: List[UserNote] = field(default_factory=list)
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()