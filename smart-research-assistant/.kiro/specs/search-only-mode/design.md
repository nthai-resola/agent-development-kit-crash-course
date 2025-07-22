# Design Document

## Overview

This design implements a search-only mode for the Smart Research Assistant that returns only search results by default while maintaining the ability to invoke specialized agents (analysis, summary, verification) when explicitly requested or automatically detected based on query intent.

The solution modifies the orchestrator's agent selection logic to be more selective and introduces configuration options for different processing modes. This approach reduces response time and computational overhead for simple queries while preserving full functionality when needed.

## Architecture

### Current Architecture
The current system uses an "invoke all relevant agents" approach where the orchestrator analyzes queries and typically invokes multiple agents (search + verification/summary/analysis) based on keyword detection.

### New Architecture
The new architecture introduces three processing modes:

1. **Search-Only Mode (Default)**: Only invokes the search agent unless other agents are explicitly requested
2. **Auto-Detect Mode**: Uses enhanced query analysis to selectively invoke agents based on clear intent indicators
3. **Full-Processing Mode**: Maintains current behavior of invoking multiple agents

### Key Changes

#### 1. Enhanced Query Analysis
- More restrictive keyword matching for non-search agents
- Context-aware agent selection based on session history
- Explicit intent detection for multi-agent processing

#### 2. Processing Mode Configuration
- New configuration options in `Config` class
- Runtime mode switching capability
- Per-session mode preferences

#### 3. Agent Coordination Strategy
- Modified execution order with search-first approach
- Conditional agent invocation based on search results
- Fallback mechanisms for failed agents

## Components and Interfaces

### 1. Configuration Extensions

```python
class Config:
    # New configuration options
    PROCESSING_MODE = os.getenv("PROCESSING_MODE", "search-only")  # search-only, auto-detect, full-processing
    ENABLE_SMART_DETECTION = bool(os.getenv("ENABLE_SMART_DETECTION", "true"))
    SEARCH_ONLY_KEYWORDS = os.getenv("SEARCH_ONLY_KEYWORDS", "find,search,look up,information")
```

### 2. Enhanced Orchestrator Agent

#### New Methods:
- `_determine_processing_mode(query, context)`: Determines which mode to use for a specific query
- `_analyze_query_intent(query)`: Enhanced query analysis with stricter criteria
- `_should_invoke_agent(agent_type, query, context)`: Decides whether to invoke a specific agent
- `_get_explicit_agent_requests(query)`: Extracts explicit agent requests from query

#### Modified Methods:
- `_analyze_query_requirements()`: Updated with more restrictive logic
- `_coordinate_agents()`: Enhanced with conditional execution
- `process_query()`: Added mode-specific processing paths

### 3. Agent Selection Logic

#### Search-Only Mode
```python
def _get_required_agents_search_only(self, query: str) -> List[str]:
    """Return only search agent unless explicitly requested otherwise."""
    explicit_requests = self._get_explicit_agent_requests(query)
    if explicit_requests:
        return ["search"] + explicit_requests
    return ["search"]
```

#### Auto-Detect Mode
```python
def _get_required_agents_auto_detect(self, query: str, context: Dict) -> List[str]:
    """Use enhanced detection with stricter criteria."""
    required_agents = ["search"]
    
    # More restrictive keyword matching
    if self._has_strong_verification_intent(query):
        required_agents.append("verification")
    if self._has_strong_summary_intent(query):
        required_agents.append("summary")
    if self._has_strong_analysis_intent(query):
        required_agents.append("analysis")
    
    return required_agents
```

### 4. Response Format Extensions

#### Enhanced Response Metadata
```python
response_data = {
    "success": True,
    "response": response,
    "processing_mode": current_mode,
    "agents_used": list(required_agents),
    "agents_available": list(self.specialized_agents.keys()),
    "agents_skipped": skipped_agents,
    "execution_time": execution_time,
    "session_id": session_id,
    "query_id": research_query.query_id,
    "timestamp": datetime.now().isoformat()
}
```

## Data Models

### 1. Processing Mode Enum
```python
from enum import Enum

class ProcessingMode(Enum):
    SEARCH_ONLY = "search-only"
    AUTO_DETECT = "auto-detect"
    FULL_PROCESSING = "full-processing"
```

### 2. Enhanced Query Result
```python
class QueryResult(BaseModel):
    # Existing fields...
    processing_mode: str = ""
    agents_invoked: List[str] = Field(default_factory=list)
    execution_time_ms: int = 0
    agent_execution_order: List[str] = Field(default_factory=list)
```

### 3. Agent Intent Detection
```python
class AgentIntent(BaseModel):
    agent_type: str
    confidence: float
    keywords_matched: List[str]
    explicit_request: bool
```

## Error Handling

### 1. Agent Failure Handling
- When search agent fails, return error immediately in search-only mode
- In other modes, attempt to continue with available agents
- Provide clear error messages indicating which agents failed

### 2. Configuration Validation
- Validate processing mode values at startup
- Provide fallback to search-only mode for invalid configurations
- Log configuration warnings and errors

### 3. Graceful Degradation
- If specialized agents are unavailable, fall back to search-only
- Inform users when agents are skipped due to failures
- Maintain session continuity despite agent failures

## Testing Strategy

### 1. Unit Tests

#### Query Analysis Tests
- Test keyword detection accuracy for each agent type
- Verify processing mode selection logic
- Test explicit request parsing

#### Agent Coordination Tests
- Test agent execution order in different modes
- Verify conditional agent invocation
- Test error handling and fallback mechanisms

### 2. Integration Tests

#### End-to-End Processing Tests
- Test complete query processing in each mode
- Verify response format and metadata
- Test mode switching during sessions

#### Performance Tests
- Measure response time improvements in search-only mode
- Compare processing times across different modes
- Test system behavior under load

### 3. User Acceptance Tests

#### Functionality Tests
- Verify search-only mode returns appropriate results
- Test explicit agent requests work correctly
- Confirm auto-detection accuracy

#### User Experience Tests
- Test clarity of agent usage feedback
- Verify mode switching is intuitive
- Test error messages are helpful

### 4. Test Data and Scenarios

#### Query Types for Testing
```python
TEST_QUERIES = {
    "search_only": [
        "What is machine learning?",
        "Find information about Python programming",
        "Look up recent news about AI"
    ],
    "explicit_analysis": [
        "Analyze the performance of different ML algorithms",
        "Create a chart showing AI adoption trends",
        "Translate this text to Spanish"
    ],
    "explicit_summary": [
        "Summarize the key points about blockchain",
        "Give me an overview of climate change research",
        "Brief me on the latest tech developments"
    ],
    "explicit_verification": [
        "Verify the accuracy of this climate data",
        "Fact-check this news article",
        "Is this information reliable?"
    ],
    "multi_agent": [
        "Research and analyze renewable energy trends, then summarize the findings",
        "Find information about AI ethics and verify the claims",
        "Compare different programming languages and create a summary"
    ]
}
```

## Implementation Phases

### Phase 1: Core Infrastructure
1. Add configuration options for processing modes
2. Implement enhanced query analysis methods
3. Create agent intent detection logic
4. Add response metadata extensions

### Phase 2: Orchestrator Modifications
1. Modify `_analyze_query_requirements()` method
2. Implement mode-specific agent selection
3. Update `_coordinate_agents()` for conditional execution
4. Add explicit request parsing

### Phase 3: Error Handling and Fallbacks
1. Implement graceful degradation mechanisms
2. Add comprehensive error handling
3. Create fallback strategies for agent failures
4. Add configuration validation

### Phase 4: Testing and Optimization
1. Implement comprehensive test suite
2. Performance testing and optimization
3. User acceptance testing
4. Documentation and examples

This design maintains backward compatibility while introducing the requested search-only functionality with intelligent agent selection when needed.