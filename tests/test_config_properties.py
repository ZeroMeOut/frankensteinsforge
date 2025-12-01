"""
Property-based tests for configuration system.

These tests verify universal properties that should hold across all valid
configurations using Hypothesis for property-based testing.
"""
import os
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from pydantic import ValidationError
from contextlib import contextmanager

from app.core.config import Config, reset_config


# Hypothesis strategies for generating test data
config_keys = st.sampled_from([
    "api_title",
    "api_version",
    "host",
    "port",
    "max_image_size",
    "max_audio_size",
    "ai_model",
    "enable_rate_limiting",
    "log_level",
])

# String values that can be used in environment variables (no null bytes)
string_values = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(blacklist_characters='\x00', blacklist_categories=('Cs',))
)
positive_integers = st.integers(min_value=1, max_value=1000000)
port_numbers = st.integers(min_value=1, max_value=65535)
boolean_values = st.booleans()
log_levels = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])


@contextmanager
def clean_env():
    """Context manager to clean environment and disable .env loading."""
    original_env = os.environ.copy()
    
    # Clear all environment variables to ensure clean state
    os.environ.clear()
    
    # Set a marker to prevent .env loading (we'll check this in Config)
    os.environ["_TEST_MODE"] = "1"
    
    try:
        yield
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
        reset_config()


def create_test_config(**kwargs):
    """Create a Config instance without loading .env file."""
    # Temporarily modify the model config to not load .env
    from app.core.config import Config as OrigConfig
    
    class TestConfig(OrigConfig):
        model_config = OrigConfig.model_config.copy()
    
    # Disable .env file loading for test
    TestConfig.model_config["env_file"] = None
    
    return TestConfig(**kwargs)


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    reset_config()


class TestEnvironmentVariableOverride:
    """
    **Feature: api-improvements, Property 1: Environment variable override consistency**
    **Validates: Requirements 1.2**
    
    For any configuration key that exists in both file and environment variables,
    the environment variable value should always take precedence.
    """
    
    @settings(max_examples=100)
    @given(
        api_title=string_values,
        api_version=string_values,
        host=string_values,
    )
    def test_string_config_env_override(self, api_title: str, api_version: str, host: str):
        """Test that environment variables override default string values."""
        with clean_env():
            # Set required field
            os.environ["GOOGLE_API_KEY"] = "test-key-123"
            
            # Set environment variables for string fields
            os.environ["API_TITLE"] = api_title
            os.environ["API_VERSION"] = api_version
            os.environ["HOST"] = host
            
            # Create config
            config = create_test_config()
            
            # Verify environment values take precedence
            assert config.api_title == api_title
            assert config.api_version == api_version
            assert config.host == host
    
    @settings(max_examples=100)
    @given(
        port=port_numbers,
        max_image_size=positive_integers,
        max_audio_size=positive_integers,
    )
    def test_integer_config_env_override(
        self, port: int, max_image_size: int, max_audio_size: int
    ):
        """Test that environment variables override default integer values."""
        with clean_env():
            # Set required field
            os.environ["GOOGLE_API_KEY"] = "test-key-456"
            
            # Set environment variables for integer fields
            os.environ["PORT"] = str(port)
            os.environ["MAX_IMAGE_SIZE"] = str(max_image_size)
            os.environ["MAX_AUDIO_SIZE"] = str(max_audio_size)
            
            # Create config
            config = create_test_config()
            
            # Verify environment values take precedence
            assert config.port == port
            assert config.max_image_size == max_image_size
            assert config.max_audio_size == max_audio_size
    
    @settings(max_examples=100)
    @given(
        enable_rate_limiting=boolean_values,
        enable_structured_logging=boolean_values,
        debug=boolean_values,
    )
    def test_boolean_config_env_override(
        self, enable_rate_limiting: bool, enable_structured_logging: bool, debug: bool
    ):
        """Test that environment variables override default boolean values."""
        with clean_env():
            # Set required field
            os.environ["GOOGLE_API_KEY"] = "test-key-789"
            
            # Set environment variables for boolean fields
            os.environ["ENABLE_RATE_LIMITING"] = str(enable_rate_limiting).lower()
            os.environ["ENABLE_STRUCTURED_LOGGING"] = str(enable_structured_logging).lower()
            os.environ["DEBUG"] = str(debug).lower()
            
            # Create config
            config = create_test_config()
            
            # Verify environment values take precedence
            assert config.enable_rate_limiting == enable_rate_limiting
            assert config.enable_structured_logging == enable_structured_logging
            assert config.debug == debug


class TestConfigurationTypeSafety:
    """
    **Feature: api-improvements, Property 2: Configuration type safety**
    **Validates: Requirements 1.3**
    
    For any configuration value accessed, the returned value should match
    the declared type in the configuration schema.
    """
    
    @settings(max_examples=100)
    @given(
        api_title=string_values,
        port=port_numbers,
        enable_rate_limiting=boolean_values,
    )
    def test_config_type_safety(
        self, api_title: str, port: int, enable_rate_limiting: bool
    ):
        """Test that configuration values maintain their declared types."""
        with clean_env():
            # Set required field and test values
            os.environ["GOOGLE_API_KEY"] = "test-key-type-safety"
            os.environ["API_TITLE"] = api_title
            os.environ["PORT"] = str(port)
            os.environ["ENABLE_RATE_LIMITING"] = str(enable_rate_limiting).lower()
            
            # Create config
            config = create_test_config()
            
            # Verify types match declarations
            assert isinstance(config.api_title, str)
            assert isinstance(config.port, int)
            assert isinstance(config.enable_rate_limiting, bool)
            
            # Verify values are correct
            assert config.api_title == api_title
            assert config.port == port
            assert config.enable_rate_limiting == enable_rate_limiting
    
    @settings(max_examples=100)
    @given(
        max_image_size=positive_integers,
        max_audio_size=positive_integers,
    )
    def test_integer_fields_are_integers(
        self, max_image_size: int, max_audio_size: int
    ):
        """Test that integer configuration fields return actual integers."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-int-type"
            os.environ["MAX_IMAGE_SIZE"] = str(max_image_size)
            os.environ["MAX_AUDIO_SIZE"] = str(max_audio_size)
            
            config = create_test_config()
            
            # Verify integer types
            assert isinstance(config.max_image_size, int)
            assert isinstance(config.max_audio_size, int)
            assert type(config.max_image_size) is int
            assert type(config.max_audio_size) is int


class TestMissingConfigurationErrors:
    """
    **Feature: api-improvements, Property 3: Missing configuration error clarity**
    **Validates: Requirements 1.4**
    
    For any required configuration field that is missing, the system should raise
    an error message that explicitly names the missing field.
    """
    
    def test_missing_google_api_key_error_message(self):
        """Test that missing GOOGLE_API_KEY produces a clear error message."""
        with clean_env():
            # Attempt to create config should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                create_test_config()
            
            # Verify error message mentions the missing field
            error_str = str(exc_info.value)
            assert "google_api_key" in error_str.lower()
    
    def test_from_env_missing_field_error_clarity(self):
        """Test that from_env() provides clear error for missing required fields."""
        with clean_env():
            # Attempt to load config without .env file
            with pytest.raises((ValidationError, ValueError)) as exc_info:
                Config.from_env(_env_file=None)
            
            # Verify error message is clear about what's missing
            error_str = str(exc_info.value)
            assert "google_api_key" in error_str.lower() or "missing" in error_str.lower()
    
    @settings(max_examples=100)
    @given(field_name=st.sampled_from(["google_api_key"]))
    def test_missing_required_field_names_field(self, field_name: str):
        """Test that error messages explicitly name the missing required field."""
        with clean_env():
            # Attempt to create config
            with pytest.raises(ValidationError) as exc_info:
                create_test_config()
            
            # Verify the field name appears in the error
            error_str = str(exc_info.value).lower()
            assert field_name.lower() in error_str


class TestConfigurationValidation:
    """
    **Feature: api-improvements, Property 4: Configuration validation completeness**
    **Validates: Requirements 1.5**
    
    For any invalid configuration value, validation at startup should detect
    and report the invalidity before the application starts processing requests.
    """
    
    @settings(max_examples=100)
    @given(port=st.integers(min_value=-1000, max_value=0))
    def test_invalid_port_rejected(self, port: int):
        """Test that invalid port numbers are rejected during validation."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-validation"
            os.environ["PORT"] = str(port)
            
            # Config creation should fail with invalid port
            with pytest.raises(ValidationError):
                create_test_config()
    
    @settings(max_examples=100)
    @given(port=st.integers(min_value=65536, max_value=100000))
    def test_port_above_max_rejected(self, port: int):
        """Test that port numbers above 65535 are rejected."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-validation"
            os.environ["PORT"] = str(port)
            
            with pytest.raises(ValidationError):
                create_test_config()
    
    @settings(max_examples=100)
    @given(size=st.integers(max_value=0))
    def test_non_positive_file_sizes_rejected(self, size: int):
        """Test that non-positive file sizes are rejected."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-validation"
            os.environ["MAX_IMAGE_SIZE"] = str(size)
            
            with pytest.raises(ValidationError):
                create_test_config()
    
    @settings(max_examples=100)
    @given(log_level=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(blacklist_characters='\x00', blacklist_categories=('Cs',))
    ))
    def test_invalid_log_level_rejected(self, log_level: str):
        """Test that invalid log levels are rejected."""
        # Only test invalid log levels
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assume(log_level.upper() not in valid_levels)
        
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-validation"
            os.environ["LOG_LEVEL"] = log_level
            
            with pytest.raises(ValidationError):
                create_test_config()
    
    def test_empty_api_key_rejected(self):
        """Test that empty API key is rejected."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = ""
            
            with pytest.raises(ValidationError):
                create_test_config()
    
    def test_whitespace_only_api_key_rejected(self):
        """Test that whitespace-only API key is rejected."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "   "
            
            # Create config (Pydantic will accept it initially)
            config = create_test_config()
            
            # But validate() should catch it
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            
            assert "google_api_key" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        rate_limit_requests=st.integers(min_value=-1000, max_value=-1),
    )
    def test_invalid_rate_limit_with_feature_enabled(self, rate_limit_requests: int):
        """Test that invalid rate limit values are caught when feature is enabled."""
        with clean_env():
            os.environ["GOOGLE_API_KEY"] = "test-key-validation"
            os.environ["ENABLE_RATE_LIMITING"] = "true"
            os.environ["RATE_LIMIT_REQUESTS"] = str(rate_limit_requests)
            
            # Config creation should fail with invalid rate limit (Pydantic validates gt=0)
            with pytest.raises(ValidationError):
                create_test_config()
