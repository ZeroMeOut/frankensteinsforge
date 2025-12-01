"""Property-based tests for Gemini client retry and rate limiting behavior"""
import time
import pytest
from hypothesis import given, strategies as st, settings
from app.core.gemini_client import GeminiClient, MockGeminiClient


class TestGeminiClientRetryProperties:
    """Property-based tests for Gemini client retry logic"""
    
    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        fail_count=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_15_api_retry_with_exponential_backoff(self, max_retries, fail_count):
        """
        **Feature: api-improvements, Property 15: API retry with exponential backoff**
        **Validates: Requirements 4.4**
        
        Property: For any API call that fails with a retryable error, the system should 
        retry up to max_retries times with exponentially increasing delays between attempts.
        
        The backoff pattern should be:
        - Attempt 1: Immediate (0 seconds)
        - Attempt 2: 1 second delay (2^0)
        - Attempt 3: 2 seconds delay (2^1)
        - Attempt 4: 4 seconds delay (2^2)
        """
        # Create mock client that will fail fail_count times then succeed
        mock_client = MockGeminiClient(max_retries=max_retries)
        
        # Only test cases where fail_count is less than max_retries
        # (otherwise it should raise an exception)
        if fail_count >= max_retries:
            # Configure to fail all attempts
            mock_client.configure_failure(
                should_fail=True,
                fail_count=max_retries,
                failure_type="service_unavailable"
            )
            
            # Wrap the mock to track timing
            client = GeminiClient(api_key="test-key", max_retries=max_retries)
            client._generate_content_internal = mock_client.generate_content
            
            # Should raise exception after all retries exhausted
            with pytest.raises(Exception):
                client.generate_content(
                    model="test-model",
                    contents=["test content"]
                )
            
            # Verify it tried max_retries times
            assert mock_client.call_count == max_retries
        else:
            # Configure to fail fail_count times then succeed
            mock_client.configure_failure(
                should_fail=True,
                fail_count=fail_count,
                failure_type="service_unavailable"
            )
            
            # Wrap the mock to track timing
            client = GeminiClient(api_key="test-key", max_retries=max_retries)
            client._generate_content_internal = mock_client.generate_content
            
            # Measure time taken
            start_time = time.time()
            result = client.generate_content(
                model="test-model",
                contents=["test content"]
            )
            elapsed_time = time.time() - start_time
            
            # Verify it succeeded
            assert result == "Mock generated content"
            
            # Verify it tried fail_count + 1 times (failures + success)
            assert mock_client.call_count == fail_count + 1
            
            # Verify exponential backoff timing
            # Expected delay: sum of 2^i for i in range(fail_count)
            # Attempt 1: immediate (0s)
            # Attempt 2: wait 1s (2^0)
            # Attempt 3: wait 2s (2^1)
            # Attempt 4: wait 4s (2^2)
            expected_delay = sum(2**i for i in range(fail_count))
            
            # Allow some tolerance for execution time (±0.5 seconds)
            # The actual delay should be at least the expected delay
            assert elapsed_time >= expected_delay - 0.5, (
                f"Expected at least {expected_delay}s delay for {fail_count} failures, "
                f"but got {elapsed_time}s"
            )


class TestGeminiClientRateLimitProperties:
    """Property-based tests for rate limit handling"""
    
    @given(
        retry_after=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_16_rate_limit_retry_behavior(self, retry_after):
        """
        **Feature: api-improvements, Property 16: Rate limit retry behavior**
        **Validates: Requirements 4.5**
        
        Property: For any API response indicating rate limit exceeded, the system should 
        wait according to the retry-after header before retrying.
        """
        # Create a custom mock that simulates rate limit with retry-after
        class RateLimitMockClient:
            def __init__(self):
                self.call_count = 0
                self.retry_after_value = retry_after
            
            def generate_content(self, model, contents, **kwargs):
                self.call_count += 1
                if self.call_count == 1:
                    # First call fails with rate limit
                    raise Exception(f"429 Rate limit exceeded. Retry after {self.retry_after_value} seconds")
                # Second call succeeds
                return "Success after rate limit"
        
        rate_limit_mock = RateLimitMockClient()
        
        # Create client with retry logic
        client = GeminiClient(api_key="test-key", max_retries=3)
        client._generate_content_internal = rate_limit_mock.generate_content
        
        # Measure time taken
        start_time = time.time()
        result = client.generate_content(
            model="test-model",
            contents=["test content"]
        )
        elapsed_time = time.time() - start_time
        
        # Verify it succeeded after retry
        assert result == "Success after rate limit"
        
        # Verify it made exactly 2 calls (1 failure + 1 success)
        assert rate_limit_mock.call_count == 2
        
        # Verify it waited at least retry_after seconds
        # Allow small tolerance for execution overhead
        assert elapsed_time >= retry_after - 0.5, (
            f"Expected to wait at least {retry_after}s for rate limit, "
            f"but only waited {elapsed_time}s"
        )
        
        # Verify it didn't wait too much longer (should be close to retry_after)
        # Allow up to 1 second extra for execution overhead
        assert elapsed_time <= retry_after + 1.0, (
            f"Expected to wait around {retry_after}s for rate limit, "
            f"but waited {elapsed_time}s"
        )
