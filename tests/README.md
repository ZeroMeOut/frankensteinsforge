# Test Suite

This directory contains the comprehensive test suite for Frankenstein's Forge API.

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── fixtures/             # Test data files (images, audio)
├── test_config.py        # Configuration system tests
├── test_validators.py    # Input validation tests
├── test_services.py      # Business logic tests
├── test_api.py          # API endpoint integration tests
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
source .venv/bin/activate
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Property-based tests only
pytest -m property

# Exclude slow tests
pytest -m "not slow"
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_validators.py
```

## Test Types

### Unit Tests
Test individual components in isolation with mocked dependencies.

### Integration Tests
Test component interactions and API endpoints using test clients.

### Property-Based Tests
Use Hypothesis to verify universal properties across many generated inputs.
- Configured to run 20 examples in dev mode
- Configured to run 100 examples in CI mode

## Hypothesis Profiles

Set the `HYPOTHESIS_PROFILE` environment variable to switch profiles:
- `dev`: Fast feedback with 20 examples (default)
- `ci`: Thorough testing with 100 examples

```bash
HYPOTHESIS_PROFILE=ci pytest
```

## Coverage Goals

- Minimum 80% overall code coverage
- 100% coverage for critical paths (validation, error handling)
- All property tests should run minimum 100 iterations in CI

## Test Fixtures

Sample files are provided in `tests/fixtures/`:
- `sample_image.jpg`: Valid JPEG image for testing
- `sample_audio.wav`: Valid WAV audio for testing

Additional fixtures are defined in `conftest.py` for easy reuse across tests.
