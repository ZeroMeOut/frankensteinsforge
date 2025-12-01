"""
Rate limiting middleware for Frankenstein's Forge API.

This module implements sliding window rate limiting to prevent API abuse
and ensure fair resource allocation across clients.

Usage:
    To add rate limiting to your FastAPI application:
    
    ```python
    from app.middleware.rate_limiter import RateLimiter
    from app.core.dependencies import get_config, get_logger
    
    # In your app startup:
    config = get_config()
    logger = get_logger()
    
    # Add the middleware
    app.add_middleware(RateLimiter, config=config, logger=logger)
    ```
    
    The rate limiter will automatically track requests per IP address
    (or per user if authentication is implemented) and enforce the
    configured rate limits.
"""
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import Config
from app.core.logging import StructuredLogger


class RateLimiter(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Tracks requests per IP address and per user (if authenticated),
    enforcing configurable rate limits with automatic window resets.
    """
    
    def __init__(self, app, config: Config, logger: StructuredLogger):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application instance
            config: Application configuration
            logger: Structured logger instance
        """
        super().__init__(app)
        self.config = config
        self.logger = logger
        
        # In-memory storage for request tracking
        # Structure: {identifier: [(timestamp1, timestamp2, ...)]}
        self._request_store: Dict[str, List[float]] = defaultdict(list)
        
        # Rate limit configuration
        self.max_requests = config.rate_limit_requests
        self.window_seconds = config.rate_limit_period
        
        self.logger.info(
            "Rate limiter initialized",
            max_requests=self.max_requests,
            window_seconds=self.window_seconds
        )
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Uses IP address for unauthenticated requests, or user ID
        for authenticated requests (if available).
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Unique client identifier
        """
        # Check for user authentication (future enhancement)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        # Handle X-Forwarded-For header for proxied requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _clean_old_requests(self, identifier: str, current_time: float) -> None:
        """
        Remove requests outside the current time window.
        
        Args:
            identifier: Client identifier
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_seconds
        
        # Keep only requests within the window
        self._request_store[identifier] = [
            timestamp for timestamp in self._request_store[identifier]
            if timestamp > cutoff_time
        ]
        
        # Clean up empty entries to prevent memory leaks
        if not self._request_store[identifier]:
            del self._request_store[identifier]
    
    def _check_rate_limit(
        self, identifier: str, current_time: float
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if the client has exceeded rate limits.
        
        Args:
            identifier: Client identifier
            current_time: Current timestamp
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
            - is_allowed: True if request should be allowed
            - retry_after_seconds: Seconds to wait before retry (if rate limited)
        """
        # Clean old requests first
        self._clean_old_requests(identifier, current_time)
        
        # Get request count in current window
        request_count = len(self._request_store[identifier])
        
        # Check if limit exceeded
        if request_count >= self.max_requests:
            # Calculate retry-after time
            oldest_request = min(self._request_store[identifier])
            retry_after = int(oldest_request + self.window_seconds - current_time) + 1
            return False, max(1, retry_after)
        
        return True, None
    
    def _record_request(self, identifier: str, current_time: float) -> None:
        """
        Record a new request for the client.
        
        Args:
            identifier: Client identifier
            current_time: Current timestamp
        """
        self._request_store[identifier].append(current_time)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request through rate limiting middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response
        """
        # Skip rate limiting if disabled
        if not self.config.enable_rate_limiting:
            return await call_next(request)
        
        # Get client identifier
        identifier = self._get_client_identifier(request)
        current_time = time.time()
        
        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(identifier, current_time)
        
        if not is_allowed:
            # Rate limit exceeded
            self.logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                retry_after=retry_after,
                path=request.url.path
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "details": {
                        "retry_after": retry_after,
                        "limit": self.max_requests,
                        "window": self.window_seconds
                    },
                    "request_id": getattr(request.state, "request_id", "unknown")
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Window": str(self.window_seconds)
                }
            )
        
        # Record the request
        self._record_request(identifier, current_time)
        
        # Log rate limit info
        request_count = len(self._request_store[identifier])
        self.logger.debug(
            "Request allowed",
            identifier=identifier,
            request_count=request_count,
            limit=self.max_requests,
            path=request.url.path
        )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - request_count)
        )
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        
        return response
    
    def reset(self) -> None:
        """
        Reset all rate limit counters.
        
        This is primarily useful for testing.
        """
        self._request_store.clear()
        self.logger.info("Rate limiter reset")
    
    def get_request_count(self, identifier: str) -> int:
        """
        Get current request count for an identifier.
        
        Args:
            identifier: Client identifier
            
        Returns:
            int: Number of requests in current window
        """
        current_time = time.time()
        self._clean_old_requests(identifier, current_time)
        return len(self._request_store[identifier])
