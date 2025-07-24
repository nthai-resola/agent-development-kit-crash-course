# Tech Context

## Core Technologies

- **Python 3.9+**: The primary programming language for the application.
- **Agent Development Kit (ADK)**: The foundational framework for building the multi-agent system.
- **Pydantic**: Used for data validation and settings management.
- **Rich**: For creating a rich, interactive command-line interface.

## Key Libraries

- **`google-api-python-client`**: For integrating with Google Search and other Google APIs.
- **`python-dotenv`**: For managing environment variables and API keys.
- **`pytest`**: The framework for writing and running tests.
- **`flake8` and `mypy`**: For linting and static type checking to maintain code quality.
- **`uvicorn` and `fastapi`**: Used for serving the application, likely for a web-based interface or API.
- **`aiohttp`**: For making asynchronous HTTP requests in the search functionality.
- **`pydantic-ai`**: For integrating LLM-based structured data extraction.
- **`rich`**: Used for formatted terminal output and creating user interfaces with colors and styling.

## Technical Implementation Details

- **Processing Mode System**: 
  - Implemented as an enum (`ProcessingMode`) with three options: SEARCH_ONLY, AUTO_DETECT, and FULL_PROCESSING
  - Configurable via the PROCESSING_MODE environment variable
  - Affects which agents are invoked for a query and how query analysis is performed
  - Default mode is SEARCH_ONLY for optimal efficiency

- **Agent Coordination**:
  - Enhanced agent selection based on processing mode
  - Smart agent execution order based on dependencies
  - Improved error handling and compensation for agent failures
  - Context sharing between agents for improved results

- **Agent Logging System**:
  - Custom `AgentLogger` class with rich terminal formatting
  - Four logging levels: NONE, BASIC, INFO, and DEBUG for controlling verbosity
  - Color-coded output based on agent type for better visual differentiation
  - Command-line arguments for enabling/disabling agent logs and setting verbosity
  - Logs agent activities, decisions, errors, and task completions

## Development Environment

- A `.env` file is required to store API keys and other configuration variables.
- The project uses `pip` and a `requirements.txt` file for dependency management.

## Technical Constraints

- The system relies on external APIs (e.g., Google Search), so it requires a stable internet connection.
- API keys must be configured correctly for the application to function. 
- Different processing modes have different resource usage profiles and response time expectations. 
- Agent logs may significantly increase terminal output volume at higher verbosity levels, potentially making the interface more cluttered. 