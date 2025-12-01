"""
Property-based tests for rate limiting middleware.

These tests verify universal properties that should hold across all valid
rate limiting scenarios using Hypothesis for property-based testing.
"""
import time
import pytest
from hypothesis import given, strategies as st, assume, settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient
from unittest.mock import Mock, MagicMock

from app.middleware.rate_limiter import RateLimiter
from app.core.config import Config
from app.core.logging import StructuredLogger


# Hypothesis strategies
# Generate valid IP addresses (0-255 for each octet)
ip_addresses = st.builds(
    lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
user_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(
    blacklist_characters='\x00:', blacklist_categories=('Cs',)
))
positive_integers = st.integers(min_value=1, max_value=100)
time_periods = st.integers(min_value=1, max_value=300)


def create_mock_config(
    enable_rate_limiting=True,
    rate_limit_requests=10,
    rate_limit_period=60
):
    """Create a mock config for testing."""
    config = Mock(spec=Config)
    config.enable_rate_limiting = enable_rate_limiting
    config.rate_limit_requests = rate_limit_requests
    config.rate_limit_period = rate_limit_period
    return config


def create_mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=StructuredLogger)
    return logger


class TestRequestTrackingPerIP:
    """
    **Feature: api-improvements, Property 26: Request tracking per IP**
    **Validates: Requirements 9.1**
    
    For any request received, the system should increment the request count
    for the source IP address.
    """
    
    @settings(max_examples=100)
    @given(
        ip_address=ip_addresses,
        request_count=st.integers(min_value=1, max_value=20)
    )
    def test_ip_request_tracking(self, ip_address: str, request_count: int):
        """Test that requests are tracked per IP address."""
        # Create rate limiter
        app = FastAPI()
        rate_limiter = RateLimiter(app, create_mock_config(), create_mock_logger())
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = ip_address
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None
        
        identifier = f"ip:{ip_address}"
        
        # Make multiple requests
        current_time = time.time()
        for i in range(request_count):
            rate_limiter._record_request(identifier, current_time + i * 0.1)
        
        # Verify request count matches
        tracked_count = rate_limiter.get_request_count(identifier)
        assert tracked_count == request_count
    
    @settings(max_examples=100)
    @given(
        ip1=ip_addresses,
        ip2=ip_addresses,
        count1=st.integers(min_value=1, max_value=10),
        count2=st.integers(min_value=1, max_value=10)
    )
    def test_different_ips_tracked_separately(
        self, ip1: str, ip2: str, count1: int, count2: int
    ):
        """Test that different IP addresses are tracked independently."""
        assume(ip1 != ip2)
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, create_mock_config(), create_mock_logger())
        
        identifier1 = f"ip:{ip1}"
        identifier2 = f"ip:{ip2}"
        
        current_time = time.time()
        
        # Record requests for first IP
        for i in range(count1):
            rate_limiter._record_request(identifier1, current_time + i * 0.1)
        
        # Record requests for second IP
        for i in range(count2):
            rate_limiter._record_request(identifier2, current_time + i * 0.1)
        
        # Verify counts are independent
        assert rate_limiter.get_request_count(identifier1) == count1
        assert rate_limiter.get_request_count(identifier2) == count2


class TestRateLimitResponseFormat:
    """
    **Feature: api-improvements, Property 27: Rate limit response format**
    **Validates: Requirements 9.2**
    
    For any request that exceeds rate limits, the response should have
    status code 429 and include a retry-after header.
    """
    
    @settings(max_examples=100)
    @given(
        ip_address=ip_addresses,
        max_requests=st.integers(min_value=1, max_value=10),
        window_seconds=st.integers(min_value=10, max_value=60)
    )
    def test_rate_limit_response_format(
        self, ip_address: str, max_requests: int, window_seconds: int
    ):
        """Test that rate limit exceeded responses have correct format."""
        # Create config with specific limits
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        identifier = f"ip:{ip_address}"
        current_time = time.time()
        
        # Fill up the rate limit
        for i in range(max_requests):
            rate_limiter._record_request(identifier, current_time + i * 0.1)
        
        # Check rate limit (should be exceeded)
        is_allowed, retry_after = rate_limiter._check_rate_limit(identifier, current_time + 1)
        
        # Verify response format
        assert is_allowed is False
        assert retry_after is not None
        assert isinstance(retry_after, int)
        assert retry_after > 0
    
    @settings(max_examples=50)
    @given(
        ip_address=ip_addresses,
        max_requests=st.integers(min_value=2, max_value=10)
    )
    def test_429_status_code_on_limit_exceeded(
        self, ip_address: str, max_requests: int
    ):
        """Test that 429 status code is returned when limit is exceeded."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=60
        )
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        # Add rate limiter middleware properly
        app.add_middleware(RateLimiter, config=config, logger=create_mock_logger())
        
        # Create test client
        client = TestClient(app)
        
        # Make requests up to the limit
        for i in range(max_requests):
            response = client.get("/test", headers={"X-Forwarded-For": ip_address})
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.get("/test", headers={"X-Forwarded-For": ip_address})
        assert response.status_code == 429
        
        # Verify response has retry-after header
        assert "Retry-After" in response.headers
        assert int(response.headers["Retry-After"]) > 0


class TestRateLimitWindowReset:
    """
    **Feature: api-improvements, Property 28: Rate limit window reset**
    **Validates: Requirements 9.3**
    
    For any client that was previously rate limited, once the rate limit
    window expires, new requests should be allowed.
    """
    
    @settings(max_examples=50, deadline=None)
    @given(
        ip_address=ip_addresses,
        max_requests=st.integers(min_value=2, max_value=5),
        window_seconds=st.integers(min_value=1, max_value=3)
    )
    def test_window_reset_allows_new_requests(
        self, ip_address: str, max_requests: int, window_seconds: int
    ):
        """Test that requests are allowed after window expires."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        identifier = f"ip:{ip_address}"
        start_time = time.time()
        
        # Fill up the rate limit
        for i in range(max_requests):
            rate_limiter._record_request(identifier, start_time + i * 0.1)
        
        # Verify limit is reached
        is_allowed, _ = rate_limiter._check_rate_limit(identifier, start_time + 0.5)
        assert is_allowed is False
        
        # Simulate time passing beyond the window
        time_after_window = start_time + window_seconds + 1
        
        # Check if requests are allowed after window expires
        is_allowed, _ = rate_limiter._check_rate_limit(identifier, time_after_window)
        assert is_allowed is True
    
    @settings(max_examples=50, deadline=None)
    @given(
        ip_address=ip_addresses,
        max_requests=st.integers(min_value=3, max_value=5),
        window_seconds=st.integers(min_value=2, max_value=5)
    )
    def test_old_requests_cleaned_from_window(
        self, ip_address: str, max_requests: int, window_seconds: int
    ):
        """Test that old requests outside the window are removed."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        identifier = f"ip:{ip_address}"
        start_time = time.time()
        
        # Record some old requests
        for i in range(max_requests - 1):
            rate_limiter._record_request(identifier, start_time + i * 0.1)
        
        # Move time forward past the window
        current_time = start_time + window_seconds + 1
        
        # Clean old requests
        rate_limiter._clean_old_requests(identifier, current_time)
        
        # Verify old requests were removed
        count = rate_limiter.get_request_count(identifier)
        assert count == 0


class TestPerUserRateLimiting:
    """
    **Feature: api-improvements, Property 29: Per-user rate limiting**
    **Validates: Requirements 9.4**
    
    For any authenticated user, rate limits should be tracked and enforced
    separately from other users.
    """
    
    @settings(max_examples=100)
    @given(
        user1=user_ids,
        user2=user_ids,
        count1=st.integers(min_value=1, max_value=10),
        count2=st.integers(min_value=1, max_value=10)
    )
    def test_different_users_tracked_separately(
        self, user1: str, user2: str, count1: int, count2: int
    ):
        """Test that different users are tracked independently."""
        assume(user1 != user2)
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, create_mock_config(), create_mock_logger())
        
        identifier1 = f"user:{user1}"
        identifier2 = f"user:{user2}"
        
        current_time = time.time()
        
        # Record requests for first user
        for i in range(count1):
            rate_limiter._record_request(identifier1, current_time + i * 0.1)
        
        # Record requests for second user
        for i in range(count2):
            rate_limiter._record_request(identifier2, current_time + i * 0.1)
        
        # Verify counts are independent
        assert rate_limiter.get_request_count(identifier1) == count1
        assert rate_limiter.get_request_count(identifier2) == count2
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        ip_address=ip_addresses,
        user_count=st.integers(min_value=1, max_value=10),
        ip_count=st.integers(min_value=1, max_value=10)
    )
    def test_user_and_ip_tracked_separately(
        self, user_id: str, ip_address: str, user_count: int, ip_count: int
    ):
        """Test that user-based and IP-based tracking are independent."""
        app = FastAPI()
        rate_limiter = RateLimiter(app, create_mock_config(), create_mock_logger())
        
        user_identifier = f"user:{user_id}"
        ip_identifier = f"ip:{ip_address}"
        
        current_time = time.time()
        
        # Record requests for user
        for i in range(user_count):
            rate_limiter._record_request(user_identifier, current_time + i * 0.1)
        
        # Record requests for IP
        for i in range(ip_count):
            rate_limiter._record_request(ip_identifier, current_time + i * 0.1)
        
        # Verify counts are independent
        assert rate_limiter.get_request_count(user_identifier) == user_count
        assert rate_limiter.get_request_count(ip_identifier) == ip_count
    
    @settings(max_examples=100)
    @given(
        user_id=user_ids,
        ip_address=ip_addresses
    )
    def test_user_identifier_takes_precedence_over_ip(
        self, user_id: str, ip_address: str
    ):
        """Test that authenticated users are tracked by user ID, not IP."""
        app = FastAPI()
        rate_limiter = RateLimiter(app, create_mock_config(), create_mock_logger())
        
        # Create mock request with both user_id and IP
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = ip_address
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = user_id
        
        # Get identifier
        identifier = rate_limiter._get_client_identifier(mock_request)
        
        # Verify user identifier is used, not IP
        assert identifier == f"user:{user_id}"
        assert identifier != f"ip:{ip_address}"


class TestRateLimitConfigurationCompliance:
    """
    **Feature: api-improvements, Property 30: Rate limit configuration compliance**
    **Validates: Requirements 9.5**
    
    For any configured rate limit setting, the system should enforce exactly
    that limit and time window.
    """
    
    @settings(max_examples=100)
    @given(
        max_requests=st.integers(min_value=1, max_value=20),
        window_seconds=st.integers(min_value=10, max_value=120),
        ip_address=ip_addresses
    )
    def test_configured_limit_enforced(
        self, max_requests: int, window_seconds: int, ip_address: str
    ):
        """Test that the configured request limit is enforced exactly."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        identifier = f"ip:{ip_address}"
        current_time = time.time()
        
        # Make requests up to the limit
        for i in range(max_requests):
            rate_limiter._record_request(identifier, current_time + i * 0.1)
            is_allowed, _ = rate_limiter._check_rate_limit(identifier, current_time + i * 0.1 + 0.05)
            # Should still be allowed at the limit
            if i < max_requests - 1:
                assert is_allowed is True
        
        # One more request should exceed the limit
        is_allowed, retry_after = rate_limiter._check_rate_limit(identifier, current_time + max_requests * 0.1)
        assert is_allowed is False
        assert retry_after is not None
    
    @settings(max_examples=100)
    @given(
        max_requests=st.integers(min_value=2, max_value=10),
        window_seconds=st.integers(min_value=5, max_value=30),
        ip_address=ip_addresses
    )
    def test_configured_window_enforced(
        self, max_requests: int, window_seconds: int, ip_address: str
    ):
        """Test that the configured time window is enforced exactly."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        identifier = f"ip:{ip_address}"
        start_time = time.time()
        
        # Record a request at the start
        rate_limiter._record_request(identifier, start_time)
        
        # Just before window expires, request should still be counted
        time_before_expiry = start_time + window_seconds - 0.5
        count_before = len([t for t in rate_limiter._request_store[identifier] if t > time_before_expiry - window_seconds])
        assert count_before == 1
        
        # After window expires, request should be cleaned
        time_after_expiry = start_time + window_seconds + 1
        rate_limiter._clean_old_requests(identifier, time_after_expiry)
        count_after = rate_limiter.get_request_count(identifier)
        assert count_after == 0
    
    @settings(max_examples=100)
    @given(
        max_requests=st.integers(min_value=1, max_value=10),
        window_seconds=st.integers(min_value=5, max_value=30)
    )
    def test_rate_limiter_uses_config_values(
        self, max_requests: int, window_seconds: int
    ):
        """Test that rate limiter initializes with configured values."""
        config = create_mock_config(
            rate_limit_requests=max_requests,
            rate_limit_period=window_seconds
        )
        
        app = FastAPI()
        rate_limiter = RateLimiter(app, config, create_mock_logger())
        
        # Verify rate limiter uses the configured values
        assert rate_limiter.max_requests == max_requests
        assert rate_limiter.window_seconds == window_seconds
