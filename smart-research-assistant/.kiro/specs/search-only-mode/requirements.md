# Requirements Document

## Introduction

This feature modifies the Smart Research Assistant to return only search results by default, while keeping all specialized agents (analysis, summary, verification) available for invocation when specifically needed. The system should be more efficient by avoiding unnecessary processing while maintaining full functionality when required.

## Requirements

### Requirement 1

**User Story:** As a user, I want to receive only search results by default, so that I get faster responses without unnecessary processing overhead.

#### Acceptance Criteria

1. WHEN a user submits a research query THEN the system SHALL return only search results unless other agents are explicitly requested
2. WHEN the query does not contain specific keywords for other agents THEN the system SHALL invoke only the search agent
3. WHEN search results are returned THEN they SHALL maintain the same format and quality as the current implementation
4. WHEN only search is performed THEN the response time SHALL be faster than the current multi-agent approach

### Requirement 2

**User Story:** As a user, I want to explicitly request analysis, summary, or verification when needed, so that I can get comprehensive results when required.

#### Acceptance Criteria

1. WHEN a user includes analysis keywords (analyze, visualize, chart, translate, compare) THEN the system SHALL invoke both search and analysis agents
2. WHEN a user includes summary keywords (summarize, key points, overview, brief) THEN the system SHALL invoke both search and summary agents
3. WHEN a user includes verification keywords (verify, fact-check, accurate, reliable) THEN the system SHALL invoke both search and verification agents
4. WHEN multiple agent types are requested THEN the system SHALL invoke all relevant agents in the appropriate order
5. WHEN specialized agents are invoked THEN they SHALL receive search results as context for their processing

### Requirement 3

**User Story:** As a user, I want the system to intelligently detect when multiple agents are needed, so that I don't have to explicitly request every type of processing.

#### Acceptance Criteria

1. WHEN a query contains multiple intent indicators THEN the system SHALL invoke all relevant agents
2. WHEN a query asks for comprehensive research THEN the system SHALL invoke search, verification, and summary agents
3. WHEN a query involves data analysis and verification THEN the system SHALL invoke search, analysis, and verification agents
4. WHEN the session context suggests additional processing is needed THEN the system SHALL recommend or invoke appropriate agents

### Requirement 4

**User Story:** As a developer, I want the orchestrator to be configurable for agent selection, so that the system can be tuned for different use cases.

#### Acceptance Criteria

1. WHEN the system is configured THEN it SHALL support a "search-only" mode as the default
2. WHEN the system is configured THEN it SHALL support an "auto-detect" mode for intelligent agent selection
3. WHEN the system is configured THEN it SHALL support a "full-processing" mode for comprehensive analysis
4. WHEN the mode is changed THEN the system SHALL apply the new behavior to subsequent queries
5. WHEN in search-only mode THEN users SHALL still be able to override with explicit keywords

### Requirement 5

**User Story:** As a user, I want clear feedback about which agents were used, so that I understand what processing was performed on my query.

#### Acceptance Criteria

1. WHEN a query is processed THEN the response SHALL indicate which agents were invoked
2. WHEN only search is performed THEN the response SHALL clearly indicate "search-only" mode
3. WHEN multiple agents are used THEN the response SHALL list all agents that contributed to the result
4. WHEN an agent fails THEN the response SHALL indicate which agents succeeded and which failed
5. WHEN agents are skipped due to configuration THEN the response SHALL explain why they were not used