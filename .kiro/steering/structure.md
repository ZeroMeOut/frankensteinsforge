# Project Structure

## Directory Organization

```
app/
├── core/              # Core infrastructure and utilities
│   ├── config.py      # Centralized configuration with Pydantic
│   ├── dependencies.py # Dependency injection setup
│   ├── error_handlers.py # Global error handling
│   ├── exceptions.py  # Custom exception classes
│   ├── file_handler.py # File processing utilities
│   ├── gemini_client.py # Gemini API client wrapper
│   ├── logging.py     # Structured logging setup
│   └── metrics.py     # Metrics collection and reporting
│
├── middleware/        # FastAPI middleware
│   └── rate_limiter.py # Rate limiting middleware
│
├── models/            # Pydantic models
│   ├── graph_models.py # Node graph data models
│   ├── requests.py    # API request models
│   └── responses.py   # API response models
│
├── services/          # Business logic layer
│   ├── forge_service.py # Core idea generation service
│   └── graph_service.py # Node graph processing service
│
└── validators/        # Input validation
    ├── file_validator.py # File type and size validation
    └── text_validator.py # Text sanitization and validation

tests/
├── conftest.py        # Shared pytest fixtures
├── fixtures/          # Test data files
├── test_*_properties.py # Property-based tests (Hypothesis)
├── test_api_integration.py # API integration tests
└── test_infrastructure.py # Infrastructure tests

static/                # Frontend assets
├── index-nodes.html   # Node graph interface
├── script-nodes.js    # Node graph JavaScript
└── style-nodes*.css   # Styling

main.py                # FastAPI application entry point
```

## Architecture Patterns

### Dependency Injection
- All services use constructor-based dependency injection
- Dependencies initialized in `app/core/dependencies.py`
- FastAPI's `Depends()` used for route-level injection
- Enables easy testing with mock implementations

### Protocol-Based Design
- Services depend on protocols (interfaces) not concrete implementations
- Example: `GeminiClientProtocol` allows swapping AI clients
- Facilitates testing and future extensibility

### Layered Architecture
1. **Routes** (`main.py`) - HTTP endpoints, request/response handling
2. **Services** (`app/services/`) - Business logic, orchestration
3. **Core** (`app/core/`) - Infrastructure, utilities, external APIs
4. **Models** (`app/models/`) - Data structures, validation
5. **Validators** (`app/validators/`) - Input validation and sanitization

### Error Handling
- Custom exception hierarchy in `app/core/exceptions.py`
- Base class: `AppException` with status codes and details
- Specific exceptions: `ValidationError`, `ExternalAPIError`, `ConfigurationError`, etc.
- Global error handlers in `app/core/error_handlers.py`
- All errors return consistent JSON structure

### Configuration Management
- Centralized in `app/core/config.py` using Pydantic
- Environment variables loaded from `.env` file
- Type-safe with validation
- Singleton pattern via `get_config()` function

### Logging
- Structured JSON logging via `StructuredLogger`
- Request IDs for tracing
- Context-aware logging with extra fields
- Configurable log levels

### Testing Strategy
- **Unit tests**: Individual component testing
- **Integration tests**: Component interaction testing
- **Property-based tests**: Hypothesis for invariant testing
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.property`
- Shared fixtures in `conftest.py`
- Mock implementations for external dependencies

## Code Conventions

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Documentation
- Module-level docstrings for all files
- Class and function docstrings with Args/Returns/Raises sections
- Type hints on all function signatures
- Inline comments for complex logic

### Imports
- Standard library imports first
- Third-party imports second
- Local application imports last
- Absolute imports preferred over relative

### Type Safety
- Type hints required on all public functions
- Pydantic models for data validation
- Protocol classes for interface definitions
- `typing` module for complex types
