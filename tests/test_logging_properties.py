"""Property-based tests for structured logging system.

Feature: api-improvements
"""

import json
import logging
from io import StringIO
from hypothesis import given, strategies as st, settings
import pytest

from app.core.logging import (
    StructuredLogger,
    SensitiveDataRedactor,
    generate_request_id,
    setup_logging
)


# Strategies for generating test data
log_messages = st.text(min_size=1, max_size=200)
log_levels = st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
http_methods = st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
paths = st.text(min_size=1, max_size=100).map(lambda x: f"/{x.replace(' ', '_')}")
durations = st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False)


def capture_logs(logger: StructuredLogger):
    """Helper function to capture log output."""
    # Create a string buffer to capture output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    
    # Use the same formatter as the logger
    from app.core.logging import CustomJsonFormatter
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    
    # Replace the logger's handlers
    logger.logger.handlers.clear()
    logger.logger.addHandler(handler)
    
    return log_capture


class TestJSONLogFormat:
    """Property 38: JSON log format
    
    **Feature: api-improvements, Property 38: JSON log format**
    **Validates: Requirements 12.1**
    
    For any log entry written, the output should be valid JSON with structured fields.
    """
    
    @settings(max_examples=100)
    @given(message=log_messages, level=log_levels)
    def test_log_output_is_valid_json(self, message, level):
        """Test that all log entries are valid JSON."""
        logger = StructuredLogger("test_logger", level="DEBUG")
        log_capture = capture_logs(logger)
        
        # Log a message at the specified level
        log_method = getattr(logger, level.lower())
        log_method(message)
        
        # Get the output
        output = log_capture.getvalue().strip()
        
        # Should be valid JSON
        try:
            parsed = json.loads(output)
            assert isinstance(parsed, dict), "Log output should be a JSON object"
        except json.JSONDecodeError as e:
            pytest.fail(f"Log output is not valid JSON: {e}\nOutput: {output}")
    
    @settings(max_examples=100)
    @given(message=log_messages)
    def test_log_contains_structured_fields(self, message):
        """Test that log entries contain required structured fields."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should have structured fields
        assert 'message' in parsed, "Log should contain 'message' field"
        assert 'timestamp' in parsed, "Log should contain 'timestamp' field"
        assert 'level' in parsed, "Log should contain 'level' field"


class TestRequestLogMetadata:
    """Property 39: Request log metadata
    
    **Feature: api-improvements, Property 39: Request log metadata**
    **Validates: Requirements 12.2**
    
    For any request processed, the log should include request ID, HTTP method, path, and processing duration.
    """
    
    @settings(max_examples=100)
    @given(
        method=http_methods,
        path=paths,
        duration=durations
    )
    def test_request_log_contains_metadata(self, method, path, duration):
        """Test that request logs contain all required metadata."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        request_id = generate_request_id()
        logger.log_request(request_id, method, path, duration)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain all request metadata
        assert 'request_id' in parsed, "Request log should contain request_id"
        assert parsed['request_id'] == request_id, "Request ID should match"
        
        assert 'method' in parsed, "Request log should contain method"
        assert parsed['method'] == method, "Method should match"
        
        assert 'path' in parsed, "Request log should contain path"
        assert parsed['path'] == path, "Path should match"
        
        assert 'duration' in parsed, "Request log should contain duration"
        assert abs(parsed['duration'] - duration) < 0.001, "Duration should match"
    
    @settings(max_examples=100)
    @given(method=http_methods, path=paths)
    def test_request_log_without_duration(self, method, path):
        """Test that request logs work without duration."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        request_id = generate_request_id()
        logger.log_request(request_id, method, path)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain request metadata but not duration
        assert 'request_id' in parsed
        assert 'method' in parsed
        assert 'path' in parsed


class TestErrorLogStructure:
    """Property 40: Error log structure
    
    **Feature: api-improvements, Property 40: Error log structure**
    **Validates: Requirements 12.3**
    
    For any error logged, the entry should include error type, message, and stack trace as separate structured fields.
    """
    
    @settings(max_examples=100)
    @given(error_message=log_messages)
    def test_error_log_contains_exception_info(self, error_message):
        """Test that error logs contain exception information as structured fields."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        # Create an exception
        try:
            raise ValueError(error_message)
        except ValueError as e:
            logger.error("An error occurred", exc_info=e)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain error information as structured fields
        assert 'error_type' in parsed, "Error log should contain error_type"
        assert parsed['error_type'] == 'ValueError', "Error type should be ValueError"
        
        assert 'error_message' in parsed, "Error log should contain error_message"
        # The error message might be redacted, so just check it exists
        assert isinstance(parsed['error_message'], str)
    
    @settings(max_examples=100)
    @given(message=log_messages)
    def test_error_log_without_exception(self, message):
        """Test that error logs work without exception info."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        logger.error(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should still be valid JSON with message
        assert 'message' in parsed
        assert 'level' in parsed
        assert parsed['level'] == 'ERROR'


class TestLogEntryMetadata:
    """Property 41: Log entry metadata
    
    **Feature: api-improvements, Property 41: Log entry metadata**
    **Validates: Requirements 12.4**
    
    For any log entry, it should include timestamp, log level, and source location information.
    """
    
    @settings(max_examples=100)
    @given(message=log_messages, level=log_levels)
    def test_log_contains_metadata(self, message, level):
        """Test that all log entries contain required metadata."""
        logger = StructuredLogger("test_logger", level="DEBUG")
        log_capture = capture_logs(logger)
        
        log_method = getattr(logger, level.lower())
        log_method(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Should contain timestamp
        assert 'timestamp' in parsed, "Log should contain timestamp"
        assert isinstance(parsed['timestamp'], str), "Timestamp should be a string"
        assert parsed['timestamp'].endswith('Z'), "Timestamp should be in ISO format with Z"
        
        # Should contain log level
        assert 'level' in parsed, "Log should contain level"
        assert parsed['level'] == level, f"Level should be {level}"
        
        # Should contain source location
        assert 'source' in parsed, "Log should contain source location"
        assert isinstance(parsed['source'], dict), "Source should be a dict"
        assert 'file' in parsed['source'], "Source should contain file"
        assert 'line' in parsed['source'], "Source should contain line"
        assert 'function' in parsed['source'], "Source should contain function"


class TestSensitiveDataRedaction:
    """Property 14: Sensitive data redaction
    
    **Feature: api-improvements, Property 14: Sensitive data redaction**
    **Validates: Requirements 3.5**
    
    For any log entry containing API keys or personal identifiable information,
    the sensitive data should be redacted before writing to logs.
    """
    
    @settings(max_examples=100)
    @given(
        prefix=st.text(min_size=0, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz '),
        api_key=st.text(min_size=20, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'),
        suffix=st.text(min_size=0, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz ')
    )
    def test_api_keys_are_redacted(self, prefix, api_key, suffix):
        """Test that API keys are redacted from logs."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        # Create message with API key
        message = f"{prefix} api_key={api_key} {suffix}"
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # API key should be redacted
        assert api_key not in parsed['message'], "API key should be redacted from log message"
        assert '[REDACTED]' in parsed['message'], "Redaction marker should be present"
    
    @settings(max_examples=100)
    @given(
        # Generate valid email local parts (must start with alphanumeric)
        local_part=st.text(min_size=1, max_size=1, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').flatmap(
            lambda first: st.text(min_size=0, max_size=19, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-').map(
                lambda rest: first + rest
            )
        ),
        # Generate valid domain names (must start with alphanumeric)
        domain=st.text(min_size=1, max_size=1, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').flatmap(
            lambda first: st.text(min_size=0, max_size=19, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-').map(
                lambda rest: first + rest
            )
        ),
        tld=st.sampled_from(['com', 'org', 'net', 'edu'])
    )
    def test_emails_are_redacted(self, local_part, domain, tld):
        """Test that email addresses are redacted from logs."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        # Create message with email
        email = f"{local_part}@{domain}.{tld}"
        message = f"User email is {email}"
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Email should be redacted
        assert email not in parsed['message'], "Email should be redacted from log message"
        assert '[EMAIL_REDACTED]' in parsed['message'], "Email redaction marker should be present"
    
    def test_phone_numbers_are_redacted(self):
        """Test that phone numbers are redacted from logs."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        message = "Call me at 555-123-4567"
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Phone number should be redacted
        assert '555-123-4567' not in parsed['message'], "Phone number should be redacted"
        assert '[PHONE_REDACTED]' in parsed['message'], "Phone redaction marker should be present"
    
    def test_credit_cards_are_redacted(self):
        """Test that credit card numbers are redacted from logs."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        message = "Card number: 4532-1234-5678-9010"
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        parsed = json.loads(output)
        
        # Credit card should be redacted
        assert '4532-1234-5678-9010' not in parsed['message'], "Credit card should be redacted"
        assert '[CARD_REDACTED]' in parsed['message'], "Card redaction marker should be present"
    
    @settings(max_examples=100)
    @given(message=log_messages)
    def test_redaction_preserves_message_structure(self, message):
        """Test that redaction doesn't break the message structure."""
        logger = StructuredLogger("test_logger")
        log_capture = capture_logs(logger)
        
        logger.info(message)
        
        output = log_capture.getvalue().strip()
        
        # Should still be valid JSON
        try:
            parsed = json.loads(output)
            assert 'message' in parsed
            assert isinstance(parsed['message'], str)
        except json.JSONDecodeError as e:
            pytest.fail(f"Redaction broke JSON structure: {e}")
