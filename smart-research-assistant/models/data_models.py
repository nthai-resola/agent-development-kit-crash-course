"""
Core data models for the Smart Research Assistant.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4
from pydantic import BaseModel, Field


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


class SearchResult(BaseModel):
    """Represents a single search result."""
    title: str = Field(..., description="Title of the search result.")
    link: str = Field(..., description="URL of the search result.")
    snippet: str = Field(..., description="A brief summary of the search result.")
    is_paywalled: bool = Field(False, description="Indicates if the content is behind a paywall.")
    paywall_reason: Optional[str] = Field(None, description="Reason for paywall detection.")
    relevance_score: float = Field(0.0, description="Score indicating relevance to the query.")

class StructuredSearchResult(BaseModel):
    """Represents a structured search result with metadata."""
    query: str = Field(..., description="The original search query.")
    results: List[SearchResult] = Field(..., description="List of individual search results.")
    key_takeaways: List[str] = Field(..., description="Key insights or summaries from the results.")
    related_topics: List[str] = Field(..., description="Related topics for further research.")

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