"""Custom exception classes for the application."""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception for application errors.
    
    All application-specific exceptions should inherit from this class.
    Provides consistent error handling with status codes and additional details.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize application exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code for the error
            details: Additional error details (field names, reasons, etc.)
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """String representation of the exception."""
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format.
        
        Returns:
            Dictionary with error information
        """
        return {
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


class ValidationError(AppException):
    """Raised when input validation fails.
    
    Used for invalid file types, malformed data, missing required fields,
    or any other input validation failures.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error.
        
        Args:
            message: Human-readable error message
            details: Additional validation error details
        """
        super().__init__(message, status_code=400, details=details)


class ExternalAPIError(AppException):
    """Raised when external API calls fail.
    
    Used for Gemini API failures, network timeouts, or any other
    external service errors.
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 502
    ):
        """Initialize external API error.
        
        Args:
            message: Human-readable error message
            details: Additional API error details
            status_code: HTTP status code (default 502 Bad Gateway)
        """
        super().__init__(message, status_code=status_code, details=details)


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing.
    
    Used for missing required configuration, invalid configuration values,
    or configuration validation failures.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize configuration error.
        
        Args:
            message: Human-readable error message
            details: Additional configuration error details
        """
        super().__init__(message, status_code=500, details=details)


class FileProcessingError(AppException):
    """Raised when file processing fails.
    
    Used for file read/write errors, temporary file cleanup failures,
    or any other file processing issues.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize file processing error.
        
        Args:
            message: Human-readable error message
            details: Additional file processing error details
        """
        super().__init__(message, status_code=500, details=details)


class RateLimitError(AppException):
    """Raised when rate limits are exceeded.
    
    Used when a client exceeds the configured rate limit.
    """
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize rate limit error.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds until the client can retry
            details: Additional rate limit error details
        """
        details = details or {}
        if retry_after is not None:
            details['retry_after'] = retry_after
        super().__init__(message, status_code=429, details=details)
