"""Structured logging system with JSON formatting and sensitive data redaction."""

import logging
import uuid
import re
from typing import Any, Optional
from datetime import datetime
from pythonjsonlogger import jsonlogger


class SensitiveDataRedactor:
    """Utility for redacting sensitive information from logs."""
    
    # Patterns for sensitive data (compiled once for performance)
    API_KEY_PATTERN = re.compile(r'(api[_-]?key|apikey|key)[\s:=]+(["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', re.IGNORECASE)
    STANDALONE_KEY_PATTERN = re.compile(r'\b([a-zA-Z0-9_\-]{20,})\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    
    # Track redacted keys with size limit to prevent memory leak
    _redacted_keys = set()
    _MAX_REDACTED_KEYS = 100
    
    @classmethod
    def _cleanup_redacted_keys(cls):
        """Keep only the most recent keys to prevent unbounded growth."""
        if len(cls._redacted_keys) > cls._MAX_REDACTED_KEYS:
            # Keep only the first MAX_REDACTED_KEYS items
            cls._redacted_keys = set(list(cls._redacted_keys)[:cls._MAX_REDACTED_KEYS])
    
    @classmethod
    def redact(cls, text: str) -> str:
        """Redact sensitive information from text.
        
        Args:
            text: Text that may contain sensitive information
            
        Returns:
            Text with sensitive information redacted
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Redact API keys and capture the key value
        def redact_and_track(match):
            key_value = match.group(3)
            cls._redacted_keys.add(key_value)
            cls._cleanup_redacted_keys()  # Prevent unbounded growth
            return f'{match.group(1)}{match.group(2)}[REDACTED]{match.group(4)}'
        
        text = cls.API_KEY_PATTERN.sub(redact_and_track, text)
        
        # Redact any previously seen keys that appear standalone
        for key in cls._redacted_keys:
            text = text.replace(key, '[REDACTED]')
        
        # Redact emails
        text = cls.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
        
        # Redact phone numbers
        text = cls.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
        
        # Redact SSNs
        text = cls.SSN_PATTERN.sub('[SSN_REDACTED]', text)
        
        # Redact credit cards
        text = cls.CREDIT_CARD_PATTERN.sub('[CARD_REDACTED]', text)
        
        return text
    
    @classmethod
    def redact_dict(cls, data: dict) -> dict:
        """Recursively redact sensitive information from dictionary.
        
        Args:
            data: Dictionary that may contain sensitive information
            
        Returns:
            Dictionary with sensitive information redacted
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = cls.redact(value)
            elif isinstance(value, dict):
                result[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                result[key] = [cls.redact(item) if isinstance(item, str) else item for item in value]
            else:
                result[key] = value
        return result


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields and redaction."""
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """Add custom fields to log record.
        
        Args:
            log_record: Dictionary to be logged as JSON
            record: LogRecord instance
            message_dict: Dictionary of message data
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Redact sensitive data from message
        if 'message' in log_record:
            log_record['message'] = SensitiveDataRedactor.redact(log_record['message'])
        
        # Redact sensitive data from all string fields
        for key, value in list(log_record.items()):
            if isinstance(value, str) and key != 'timestamp':
                log_record[key] = SensitiveDataRedactor.redact(value)
            elif isinstance(value, dict):
                log_record[key] = SensitiveDataRedactor.redact_dict(value)


class StructuredLogger:
    """Structured JSON logger with context management and sensitive data redaction."""
    
    def __init__(self, name: str, level: str = "INFO"):
        """Initialize structured logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self._configure_handler()
        self._context = {}
    
    def _configure_handler(self) -> None:
        """Configure JSON handler for the logger."""
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create console handler with JSON formatter
        handler = logging.StreamHandler()
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def set_context(self, **kwargs) -> None:
        """Set context fields that will be included in all log entries.
        
        Args:
            **kwargs: Context fields to add
        """
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context fields."""
        self._context.clear()
    
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal logging method with context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields to include
        """
        # Merge context with additional fields
        extra_fields = {**self._context, **kwargs}
        
        # Get the logging method
        log_method = getattr(self.logger, level.lower())
        
        # Log with extra fields
        log_method(message, extra=extra_fields)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self._log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self._log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self._log('WARNING', message, **kwargs)
    
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception info.
        
        Args:
            message: Log message
            exc_info: Exception instance to include
            **kwargs: Additional fields
        """
        if exc_info:
            kwargs['error_type'] = type(exc_info).__name__
            kwargs['error_message'] = str(exc_info)
            # Stack trace will be added by logging framework
        
        self.logger.error(message, exc_info=exc_info, extra={**self._context, **kwargs})
    
    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message with optional exception info.
        
        Args:
            message: Log message
            exc_info: Exception instance to include
            **kwargs: Additional fields
        """
        if exc_info:
            kwargs['error_type'] = type(exc_info).__name__
            kwargs['error_message'] = str(exc_info)
        
        self.logger.critical(message, exc_info=exc_info, extra={**self._context, **kwargs})
    
    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        duration: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log HTTP request with metadata.
        
        Args:
            request_id: Unique request identifier
            method: HTTP method
            path: Request path
            duration: Request duration in seconds
            **kwargs: Additional fields
        """
        log_data = {
            'request_id': request_id,
            'method': method,
            'path': path,
            **kwargs
        }
        
        if duration is not None:
            log_data['duration'] = duration
        
        self.info('Request processed', **log_data)


def generate_request_id() -> str:
    """Generate a unique request ID.
    
    Returns:
        UUID v4 string
    """
    return str(uuid.uuid4())


def setup_logging(level: str = "INFO") -> StructuredLogger:
    """Setup application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured StructuredLogger instance
    """
    return StructuredLogger("frankenstein_forge", level=level)