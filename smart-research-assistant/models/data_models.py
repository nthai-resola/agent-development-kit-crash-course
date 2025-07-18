"""
Core data models for the Smart Research Assistant.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4
from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    """Represents a single result from a research query."""
    result_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = ""
    content: str = ""
    confidence: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ResearchQuery(BaseModel):
    """Represents a research query made by the user."""
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    text: str = ""
    agent: str = ""
    results: List[QueryResult] = Field(default_factory=list)


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

class FactCheck(BaseModel):
    """Represents a single fact-checked claim."""
    claim: str = Field(..., description="The claim being verified.")
    is_verified: bool = Field(..., description="Indicates if the claim is verified.")
    supporting_sources: List[str] = Field(..., description="List of sources that support the claim.")
    conflicting_sources: List[str] = Field(..., description="List of sources that conflict with the claim.")
    confidence_score: float = Field(..., description="Confidence in the verification result.")

class VerificationResult(BaseModel):
    """Represents the result of a verification query."""
    query: str = Field(..., description="The original verification query.")
    fact_checks: List[FactCheck] = Field(..., description="List of fact-checked claims.")
    overall_confidence: float = Field(..., description="Overall confidence in the verification.")

class SummaryResult(BaseModel):
    """Represents the result of a summarization query."""
    query: str = Field(..., description="The original summary query.")
    summary: str = Field(..., description="The generated summary.")
    key_points: List[str] = Field(..., description="List of key points from the summary.")
    themes: List[str] = Field(..., description="List of main themes identified in the text.")
    categories: List[str] = Field(..., description="List of categories for the summarized content.")
    source_documents: List[str] = Field(..., description="List of source documents used for summarization.")

class ComparisonPoint(BaseModel):
    """Represents a single point of comparison between two or more items."""
    aspect: str = Field(..., description="The aspect being compared (e.g., 'performance', 'cost').")
    comparison: str = Field(..., description="A summary of the comparison for this aspect.")

class ComparativeAnalysisResult(BaseModel):
    """Represents the result of a comparative analysis query."""
    query: str = Field(..., description="The original comparison query.")
    analysis_summary: str = Field(..., description="A high-level summary of the comparative analysis.")
    comparison_points: List[ComparisonPoint] = Field(..., description="List of detailed comparison points.")

class DataInsight(BaseModel):
    """Represents a single insight derived from data analysis."""
    insight: str = Field(..., description="A key insight derived from the data.")
    supporting_data: str = Field(..., description="The specific data points or evidence supporting the insight.")
    confidence: float = Field(..., description="The confidence level of the insight (0.0 to 1.0).")

class AnalysisResult(BaseModel):
    """Represents the result of a data analysis query."""
    query: str = Field(..., description="The original analysis query.")
    analysis_summary: str = Field(..., description="A high-level summary of the analysis findings.")
    insights: List[DataInsight] = Field(..., description="A list of detailed insights from the data.")
    visualization: Optional[str] = Field(None, description="The path to a generated visualization, if applicable.")

class VersionComparisonResult(BaseModel):
    query: str = Field(..., description="The original comparison query.")
    summary: str = Field(..., description="A summary of the differences between the two versions.")
    added: List[str] = Field(..., description="A list of items added in the new version.")
    removed: List[str] = Field(..., description="A list of items removed from the old version.")
    changed: List[str] = Field(..., description="A list of items that have changed between versions.")

class TranslationResult(BaseModel):
    """Represents the result of a translation query."""
    original_text: str = Field(..., description="The original text to be translated.")
    translated_text: str = Field(..., description="The translated text.")
    target_language: str = Field(..., description="The target language for translation.")

class Entity(BaseModel):
    """Represents a single extracted entity."""
    text: str = Field(..., description="The text of the entity.")
    type: str = Field(..., description="The type of the entity (e.g., 'PERSON', 'ORGANIZATION').")
    relevance: float = Field(..., description="Relevance score of the entity.")

class EntityExtractionResult(BaseModel):
    """Represents the result of an entity extraction query."""
    entities: List[Entity] = Field(default_factory=list)


class ResearchFinding(BaseModel):
    """Represents a key finding from research."""
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str = ""
    content: str = ""
    sources: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class UserNote(BaseModel):
    """Represents a user-added note."""
    note_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str = ""
    related_findings: List[str] = Field(default_factory=list)


class ResearchSession(BaseModel):
    """Represents a complete research session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    topic: str = ""
    queries: List[ResearchQuery] = Field(default_factory=list)
    findings: List[ResearchFinding] = Field(default_factory=list)
    notes: List[UserNote] = Field(default_factory=list)
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()