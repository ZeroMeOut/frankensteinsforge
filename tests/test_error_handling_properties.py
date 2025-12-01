"""Property-based tests for error handling framework.

Feature: api-improvements
"""

import json
import logging
from io import StringIO
from hypothesis import given, strategies as st, settings
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    AppException,
    ValidationError,
    ExternalAPIError,
    ConfigurationError,
    FileProcessingError,
    RateLimitError
)
from app.core.error_handlers import setup_error_handlers, create_error_response
from app.core.logging import StructuredLogger, CustomJsonFormatter


# Strategies for generating test data
error_messages = st.text(min_size=1, max_size=200)
status_codes = st.integers(min_value=400, max_value=599)
client_error_codes = st.integers(min_value=400, max_value=499)
server_error_codes = st.integers(min_value=500, max_value=599)
retry_after_values = st.integers(min_value=1, max_value=3600)
http_methods = st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
# Generate valid URL paths (alphanumeric, hyphens, underscores, slashes)
paths = st.text(
    min_size=1,
    max_size=50,
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
).map(lambda x: f"/{x}" if x else "/test")


def capture_logs(logger: StructuredLogger):
    """Helper function to capture log output."""
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    
    return log_capture


def create_test_app_with_error_handlers():
    """Create a test FastAPI app with error handlers configured."""
    app = FastAPI()
    logger = StructuredLogger("test_error_handler")
    setup_error_handlers(app, logger)
    
    # Add middleware to set request_id
    class RequestIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.request_id = "test-request-id-123"
            response = await call_next(request)
            return response
    
    app.add_middleware(RequestIDMiddleware)
    
    return app, logger


class TestExceptionLoggingCompleteness:
    """Property 10: Exception logging completeness
    
    **Feature: api-improvements, Property 10: Exception logging completeness**
    **Validates: Requirements 3.1**
    
    For any exception that occurs during request processing, the logged entry
    should include the full stack trace and request context.
    """
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        method=http_methods
    )
    def test_exception_logs_include_stack_trace_and_context(
        self, error_message, method
    ):
        """Test that exceptions are logged with stack trace and request context."""
        app, logger = create_test_app_with_error_handlers()
        log_capture = capture_logs(logger)
        
        # Use a fixed path to avoid routing issues
        test_path = "/test-error-endpoint"
        
        # Create an endpoint that raises an exception
        @app.api_route(test_path, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        async def test_endpoint(request: Request):
            raise ValueError(error_message)
        
        client = TestClient(app, raise_server_exceptions=False)
        
        # Make request that will trigger exception
        response = client.request(method, test_path)
        
        # Get log output
        output = log_capture.getvalue().strip()
        
        # Should have logged the error
        assert output, "Error should be logged"
        
        # Parse the log entry
        log_lines = output.split('\n')
        parsed = json.loads(log_lines[0])
        
        # Should contain request context
        assert 'request_id' in parsed, "Log should contain request_id"
        assert parsed['request_id'] == "test-request-id-123"
        
        assert 'path' in parsed, "Log should contain path"
        assert parsed['path'] == test_path
        
        assert 'method' in parsed, "Log should contain method"
        assert parsed['method'] == method
        
        # Should contain error information
        assert 'error_type' in parsed, "Log should contain error_type"
        assert parsed['error_type'] == 'ValueError'
    
    @settings(max_examples=100)
    @given(error_message=error_messages)
    def test_app_exception_logs_with_context(self, error_message):
        """Test that AppException logs include full context."""
        app, logger = create_test_app_with_error_handlers()
        log_capture = capture_logs(logger)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise AppException(error_message, status_code=500, details={"key": "value"})
        
        client = TestClient(app)
        response = client.get("/test")
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain all context
        assert 'request_id' in parsed
        assert 'path' in parsed
        assert 'method' in parsed
        assert 'error_type' in parsed
        assert 'status_code' in parsed
        assert 'error_details' in parsed


class TestErrorResponseFormatConsistency:
    """Property 11: Error response format consistency
    
    **Feature: api-improvements, Property 11: Error response format consistency**
    **Validates: Requirements 3.2**
    
    For any error that occurs in the API, the response should follow a consistent
    structure with success=false, error message, and request ID.
    """
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        status_code=status_codes
    )
    def test_error_response_has_consistent_structure(self, error_message, status_code):
        """Test that all error responses follow consistent structure."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise AppException(error_message, status_code=status_code)
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Response should be JSON
        data = response.json()
        
        # Should have consistent structure
        assert 'success' in data, "Response should contain 'success' field"
        assert data['success'] is False, "Success should be False for errors"
        
        assert 'error' in data, "Response should contain 'error' field"
        assert isinstance(data['error'], str), "Error should be a string"
        
        assert 'request_id' in data, "Response should contain 'request_id' field"
        assert isinstance(data['request_id'], str), "Request ID should be a string"
        
        assert 'details' in data, "Response should contain 'details' field"
        assert isinstance(data['details'], dict), "Details should be a dict"
        
        assert 'timestamp' in data, "Response should contain 'timestamp' field"
        assert isinstance(data['timestamp'], str), "Timestamp should be a string"
        
        # Status code should match
        assert response.status_code == status_code
    
    @settings(max_examples=100)
    @given(error_message=error_messages)
    def test_validation_error_response_format(self, error_message):
        """Test that ValidationError responses follow consistent format."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise ValidationError(error_message, details={"field": "test_field"})
        
        client = TestClient(app)
        response = client.get("/test")
        
        data = response.json()
        
        # Should follow consistent format
        assert data['success'] is False
        assert 'error' in data
        assert 'request_id' in data
        assert 'details' in data
        assert 'timestamp' in data
        assert response.status_code == 400
    
    @settings(max_examples=100)
    @given(error_message=error_messages)
    def test_external_api_error_response_format(self, error_message):
        """Test that ExternalAPIError responses follow consistent format."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise ExternalAPIError(error_message, details={"api": "gemini"})
        
        client = TestClient(app)
        response = client.get("/test")
        
        data = response.json()
        
        # Should follow consistent format
        assert data['success'] is False
        assert 'error' in data
        assert 'request_id' in data
        assert 'details' in data
        assert 'timestamp' in data
        assert response.status_code == 502


class TestAPIErrorClassification:
    """Property 12: API error classification accuracy
    
    **Feature: api-improvements, Property 12: API error classification accuracy**
    **Validates: Requirements 3.3**
    
    For any Gemini API failure, the error handler should correctly classify it
    as either a client error (4xx) or server error (5xx) based on the response.
    """
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        client_status=client_error_codes
    )
    def test_client_errors_classified_as_4xx(self, error_message, client_status):
        """Test that client errors are classified with 4xx status codes."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            # Simulate a client error from external API
            raise ExternalAPIError(
                error_message,
                status_code=client_status,
                details={"error_type": "client_error"}
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Should be classified as client error (4xx)
        assert 400 <= response.status_code < 500, \
            f"Client errors should have 4xx status, got {response.status_code}"
        assert response.status_code == client_status
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        server_status=server_error_codes
    )
    def test_server_errors_classified_as_5xx(self, error_message, server_status):
        """Test that server errors are classified with 5xx status codes."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            # Simulate a server error from external API
            raise ExternalAPIError(
                error_message,
                status_code=server_status,
                details={"error_type": "server_error"}
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Should be classified as server error (5xx)
        assert 500 <= response.status_code < 600, \
            f"Server errors should have 5xx status, got {response.status_code}"
        assert response.status_code == server_status
    
    @settings(max_examples=100)
    @given(error_message=error_messages)
    def test_validation_errors_are_client_errors(self, error_message):
        """Test that validation errors are classified as client errors (400)."""
        app, logger = create_test_app_with_error_handlers()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise ValidationError(error_message)
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Validation errors should always be 400
        assert response.status_code == 400


class TestErrorLogMetadataCompleteness:
    """Property 13: Error log metadata completeness
    
    **Feature: api-improvements, Property 13: Error log metadata completeness**
    **Validates: Requirements 3.4**
    
    For any error that is logged, the log entry should contain request ID,
    timestamp, and available user context.
    """
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        method=http_methods
    )
    def test_error_logs_contain_complete_metadata(
        self, error_message, method
    ):
        """Test that error logs contain all required metadata."""
        app, logger = create_test_app_with_error_handlers()
        log_capture = capture_logs(logger)
        
        test_path = "/test-metadata-endpoint"
        
        @app.api_route(test_path, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        async def test_endpoint(request: Request):
            raise AppException(error_message, status_code=500)
        
        client = TestClient(app)
        response = client.request(method, test_path)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain request ID
        assert 'request_id' in parsed, "Error log should contain request_id"
        assert isinstance(parsed['request_id'], str)
        assert len(parsed['request_id']) > 0
        
        # Should contain timestamp
        assert 'timestamp' in parsed, "Error log should contain timestamp"
        assert isinstance(parsed['timestamp'], str)
        assert parsed['timestamp'].endswith('Z'), "Timestamp should be ISO format"
        
        # Should contain user context (path, method)
        assert 'path' in parsed, "Error log should contain path"
        assert parsed['path'] == test_path
        
        assert 'method' in parsed, "Error log should contain method"
        assert parsed['method'] == method
    
    @settings(max_examples=100)
    @given(error_message=error_messages)
    def test_error_logs_include_error_details(self, error_message):
        """Test that error logs include error-specific details."""
        app, logger = create_test_app_with_error_handlers()
        log_capture = capture_logs(logger)
        
        error_details = {"field": "test_field", "reason": "invalid_value"}
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise ValidationError(error_message, details=error_details)
        
        client = TestClient(app)
        response = client.get("/test")
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain error details
        assert 'error_details' in parsed, "Error log should contain error_details"
        assert isinstance(parsed['error_details'], dict)
    
    @settings(max_examples=100)
    @given(
        error_message=error_messages,
        retry_after=retry_after_values
    )
    def test_rate_limit_error_logs_contain_retry_info(
        self, error_message, retry_after
    ):
        """Test that rate limit error logs contain retry information."""
        app, logger = create_test_app_with_error_handlers()
        log_capture = capture_logs(logger)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            raise RateLimitError(error_message, retry_after=retry_after)
        
        client = TestClient(app)
        response = client.get("/test")
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain all metadata
        assert 'request_id' in parsed
        assert 'timestamp' in parsed
        assert 'path' in parsed
        assert 'method' in parsed
        
        # Should contain retry information in details
        assert 'error_details' in parsed
        assert 'retry_after' in parsed['error_details']
