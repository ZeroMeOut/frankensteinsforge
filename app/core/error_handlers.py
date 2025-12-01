"""FastAPI exception handlers with structured logging integration."""

import traceback
from typing import Union
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AppException,
    ValidationError,
    ExternalAPIError,
    ConfigurationError,
    FileProcessingError,
    RateLimitError
)
from app.core.logging import StructuredLogger


def create_error_response(
    success: bool,
    error: str,
    details: dict,
    request_id: str,
    status_code: int
) -> JSONResponse:
    """Create consistent error response.
    
    Args:
        success: Success flag (always False for errors)
        error: Error message
        details: Additional error details
        request_id: Request ID for tracing
        status_code: HTTP status code
        
    Returns:
        JSONResponse with consistent error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "error": error,
            "details": details,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    )


def setup_error_handlers(app: FastAPI, logger: StructuredLogger) -> None:
    """Register error handlers with FastAPI application.
    
    Args:
        app: FastAPI application instance
        logger: StructuredLogger instance for logging errors
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle custom application exceptions.
        
        Args:
            request: FastAPI request object
            exc: AppException instance
            
        Returns:
            JSONResponse with error details
        """
        # Get request ID from state or generate new one
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Log the error with full context
        logger.error(
            f"Application error: {exc.message}",
            exc_info=exc,
            request_id=request_id,
            status_code=exc.status_code,
            error_type=type(exc).__name__,
            error_details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        return create_error_response(
            success=False,
            error=exc.message,
            details=exc.details,
            request_id=request_id,
            status_code=exc.status_code
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors.
        
        Args:
            request: FastAPI request object
            exc: ValidationError instance
            
        Returns:
            JSONResponse with validation error details
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.warning(
            f"Validation error: {exc.message}",
            request_id=request_id,
            error_details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        return create_error_response(
            success=False,
            error=exc.message,
            details=exc.details,
            request_id=request_id,
            status_code=400
        )
    
    @app.exception_handler(ExternalAPIError)
    async def external_api_error_handler(request: Request, exc: ExternalAPIError) -> JSONResponse:
        """Handle external API errors.
        
        Args:
            request: FastAPI request object
            exc: ExternalAPIError instance
            
        Returns:
            JSONResponse with API error details
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            f"External API error: {exc.message}",
            exc_info=exc,
            request_id=request_id,
            status_code=exc.status_code,
            error_details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        return create_error_response(
            success=False,
            error=exc.message,
            details=exc.details,
            request_id=request_id,
            status_code=exc.status_code
        )
    
    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
        """Handle rate limit errors.
        
        Args:
            request: FastAPI request object
            exc: RateLimitError instance
            
        Returns:
            JSONResponse with rate limit error and retry-after header
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.warning(
            f"Rate limit exceeded: {exc.message}",
            request_id=request_id,
            error_details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        response = create_error_response(
            success=False,
            error=exc.message,
            details=exc.details,
            request_id=request_id,
            status_code=429
        )
        
        # Add retry-after header if available
        if 'retry_after' in exc.details:
            response.headers['Retry-After'] = str(exc.details['retry_after'])
        
        return response
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI request validation errors.
        
        Args:
            request: FastAPI request object
            exc: RequestValidationError instance
            
        Returns:
            JSONResponse with validation error details
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Extract validation error details
        errors = exc.errors()
        details = {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                }
                for error in errors
            ]
        }
        
        logger.warning(
            "Request validation failed",
            request_id=request_id,
            error_details=details,
            path=request.url.path,
            method=request.method
        )
        
        return create_error_response(
            success=False,
            error="Request validation failed",
            details=details,
            request_id=request_id,
            status_code=400  # Changed from 422 to 400 for consistency
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions.
        
        Args:
            request: FastAPI request object
            exc: StarletteHTTPException instance
            
        Returns:
            JSONResponse with HTTP error details
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.warning(
            f"HTTP error: {exc.detail}",
            request_id=request_id,
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method
        )
        
        return create_error_response(
            success=False,
            error=str(exc.detail),
            details={},
            request_id=request_id,
            status_code=exc.status_code
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions.
        
        Args:
            request: FastAPI request object
            exc: Exception instance
            
        Returns:
            JSONResponse with generic error message
        """
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Get full stack trace
        stack_trace = traceback.format_exc()
        
        # Log the error with full stack trace
        logger.error(
            f"Unexpected error: {str(exc)}",
            exc_info=exc,
            request_id=request_id,
            error_type=type(exc).__name__,
            stack_trace=stack_trace,
            path=request.url.path,
            method=request.method
        )
        
        # Return generic error message to client (don't expose internal details)
        return create_error_response(
            success=False,
            error="An unexpected error occurred. Please try again later.",
            details={"error_type": type(exc).__name__},
            request_id=request_id,
            status_code=500
        )
