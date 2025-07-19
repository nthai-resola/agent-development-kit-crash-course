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

## Development Environment

- A `.env` file is required to store API keys and other configuration variables.
- The project uses `pip` and a `requirements.txt` file for dependency management.

## Technical Constraints

- The system relies on external APIs (e.g., Google Search), so it requires a stable internet connection.
- API keys must be configured correctly for the application to function. 