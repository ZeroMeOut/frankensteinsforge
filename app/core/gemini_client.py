"""Gemini API client abstraction with retry logic and rate limiting support"""
import time
import logging
from typing import Protocol, Any, Optional
from google import genai
from google.genai import types


logger = logging.getLogger(__name__)


class GeminiClientProtocol(Protocol):
    """Protocol for Gemini API clients"""
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate content from multimodal inputs
        
        Args:
            model: The model name to use (e.g., 'gemini-2.0-flash-exp')
            contents: List of content parts (text, images, audio)
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If content generation fails
        """
        ...


class GeminiClient:
    """Production Gemini API client with retry logic and rate limiting"""
    
    def __init__(self, api_key: str, max_retries: int = 3):
        """Initialize Gemini client
        
        Args:
            api_key: Google API key for Gemini
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self._client = genai.Client(api_key=api_key)
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate content with retry logic and rate limiting
        
        Args:
            model: The model name to use
            contents: List of content parts
            **kwargs: Additional arguments
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If all retry attempts fail
        """
        return self._retry_with_backoff(
            self._generate_content_internal,
            model,
            contents,
            **kwargs
        )
    
    def _generate_content_internal(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Internal method to generate content
        
        Args:
            model: The model name to use
            contents: List of content parts
            **kwargs: Additional arguments
            
        Returns:
            Generated text content
        """
        response = self._client.models.generate_content(
            model=model,
            contents=contents,
            **kwargs
        )
        return response.text
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Retry function with exponential backoff
        
        Implements exponential backoff strategy:
        - Attempt 1: Immediate
        - Attempt 2: 1 second delay
        - Attempt 3: 2 seconds delay
        - Attempt 4: 4 seconds delay (if max_retries > 3)
        
        Args:
            func: Function to retry
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from successful function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"API call attempt {attempt + 1}/{self.max_retries}")
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"API call succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_message = str(e).lower()
                
                # Check if this is a rate limit error
                if "429" in error_message or "rate limit" in error_message or "quota" in error_message:
                    retry_after = self._extract_retry_after(e)
                    if retry_after:
                        logger.warning(
                            f"Rate limit exceeded. Waiting {retry_after} seconds before retry. "
                            f"Attempt {attempt + 1}/{self.max_retries}"
                        )
                        time.sleep(retry_after)
                        continue
                
                # Check if this is a retryable error (5xx errors, timeouts, etc.)
                is_retryable = (
                    "503" in error_message or
                    "504" in error_message or
                    "timeout" in error_message or
                    "temporarily unavailable" in error_message or
                    "429" in error_message
                )
                
                if not is_retryable:
                    logger.error(f"Non-retryable error: {e}")
                    raise
                
                # Don't retry on the last attempt
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    delay = 2 ** attempt
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"API call failed after {self.max_retries} attempts: {e}"
                    )
        
        # If we get here, all retries failed
        raise last_exception
    
    def _extract_retry_after(self, exception: Exception) -> Optional[int]:
        """Extract retry-after value from exception
        
        Args:
            exception: The exception to extract retry-after from
            
        Returns:
            Number of seconds to wait, or None if not found
        """
        # Try to extract retry-after from exception message or headers
        error_str = str(exception)
        
        # Look for "retry after X seconds" pattern
        import re
        match = re.search(r'retry[- ]after[:\s]+(\d+)', error_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Check if exception has response attribute with headers
        if hasattr(exception, 'response') and hasattr(exception.response, 'headers'):
            retry_after = exception.response.headers.get('Retry-After')
            if retry_after:
                try:
                    return int(retry_after)
                except ValueError:
                    pass
        
        # Default to exponential backoff if no retry-after found
        return None


class MockGeminiClient:
    """Mock Gemini client for testing"""
    
    def __init__(self, api_key: str = "mock-api-key", max_retries: int = 3):
        """Initialize mock client
        
        Args:
            api_key: Mock API key (not used)
            max_retries: Maximum retries (not used in mock)
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.call_count = 0
        self.mock_response = "Mock generated content"
        self.should_fail = False
        self.fail_count = 0
        self.failure_type = "generic"
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate mock content
        
        Args:
            model: The model name (ignored in mock)
            contents: List of content parts (ignored in mock)
            **kwargs: Additional arguments (ignored in mock)
            
        Returns:
            Mock generated text
            
        Raises:
            Exception: If configured to fail
        """
        self.call_count += 1
        
        # Simulate failures if configured
        if self.should_fail and self.call_count <= self.fail_count:
            if self.failure_type == "rate_limit":
                raise Exception("429 Rate limit exceeded. Retry after 2 seconds")
            elif self.failure_type == "timeout":
                raise Exception("504 Gateway timeout")
            elif self.failure_type == "service_unavailable":
                raise Exception("503 Service temporarily unavailable")
            else:
                raise Exception("API call failed")
        
        return self.mock_response
    
    def configure_failure(
        self,
        should_fail: bool = True,
        fail_count: int = 1,
        failure_type: str = "generic"
    ):
        """Configure mock to simulate failures
        
        Args:
            should_fail: Whether to fail
            fail_count: Number of times to fail before succeeding
            failure_type: Type of failure ('rate_limit', 'timeout', 'service_unavailable', 'generic')
        """
        self.should_fail = should_fail
        self.fail_count = fail_count
        self.failure_type = failure_type
        self.call_count = 0
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.should_fail = False
        self.fail_count = 0
        self.failure_type = "generic"
