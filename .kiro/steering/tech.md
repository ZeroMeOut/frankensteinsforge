# Technology Stack

## Core Framework

- **FastAPI** - Modern async web framework for building APIs
- **Uvicorn** - ASGI server with auto-reload support
- **Pydantic** - Data validation and settings management using Python type annotations
- **Python 3.x** - Primary programming language

## AI & External Services

- **Google Gemini API** (`google-genai`) - AI model for multimodal content generation
- **Model**: `gemini-2.0-flash-exp` (configurable)

## File Processing

- **python-multipart** - Multipart form data parsing for file uploads
- **filetype** - File type detection and validation

## Logging & Monitoring

- **python-json-logger** - Structured JSON logging
- **Custom metrics collector** - Request tracking, latency monitoring, error rates

## Testing

- **pytest** - Test framework with async support
- **pytest-asyncio** - Async test support
- **hypothesis** - Property-based testing framework
- **pytest-cov** - Code coverage reporting
- **pytest-mock** - Mocking utilities
- **httpx** - HTTP client for API testing

## Configuration

- **python-dotenv** - Environment variable management
- **pydantic-settings** - Type-safe configuration with validation

## Common Commands

### Development
First, remember to activate the venv.
```bash
# Start development server (auto-reload enabled)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m property      # Property-based tests only

# Run with Hypothesis profile
HYPOTHESIS_PROFILE=ci pytest  # CI profile (100 examples)
HYPOTHESIS_PROFILE=dev pytest # Dev profile (20 examples)
```

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration
- Copy `config.example.py` to `.env` and set required variables
- Required: `GOOGLE_API_KEY` for Gemini API access
- Optional: See `app/core/config.py` for all configuration options
