"""
Property-based tests for dependency injection system.

These tests verify universal properties that should hold for the
dependency injection container using Hypothesis for property-based testing.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.core.dependencies import (
    Dependencies,
    initialize_dependencies,
    reset_dependencies,
    get_dependencies,
    get_config,
    get_logger,
    get_gemini_client,
    get_forge_service,
)
from app.core.config import Config
from app.core.logging import StructuredLogger
from app.core.gemini_client import MockGeminiClient, GeminiClientProtocol
from app.services.forge_service import ForgeService


# Hypothesis strategies
string_values = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(blacklist_characters='\x00', blacklist_categories=('Cs',))
).filter(lambda s: s.strip())  # Ensure non-whitespace strings
positive_integers = st.integers(min_value=1, max_value=1000000)
port_numbers = st.integers(min_value=1, max_value=65535)


@pytest.fixture(autouse=True)
def cleanup_dependencies():
    """Clean up dependencies after each test."""
    yield
    reset_dependencies()


def create_test_config(**overrides):
    """Create a test configuration with optional overrides."""
    defaults = {
        "api_title": "Test API",
        "api_version": "1.0.0",
        "host": "0.0.0.0",
        "port": 8000,
        "max_image_size": 10 * 1024 * 1024,
        "max_audio_size": 20 * 1024 * 1024,
        "google_api_key": "test-api-key",
        "ai_model": "gemini-2.0-flash-exp",
        "enable_rate_limiting": False,
        "enable_structured_logging": True,
        "log_level": "INFO",
    }
    defaults.update(overrides)
    
    # Create config without loading .env
    from app.core.config import Config as OrigConfig
    
    class TestConfig(OrigConfig):
        model_config = OrigConfig.model_config.copy()
    
    TestConfig.model_config["env_file"] = None
    return TestConfig(**defaults)


class TestDependencyInjectionConsistency:
    """
    **Feature: api-improvements, Property 25: Dependency injection consistency**
    **Validates: Requirements 8.2**
    
    For any API endpoint, dependencies should be injected through FastAPI's
    dependency system rather than being created within the endpoint.
    
    This test verifies that:
    1. Dependencies are properly initialized and accessible
    2. The same instance is returned for multiple calls (singleton pattern)
    3. All dependency getter functions return the correct types
    4. Dependencies can be overridden for testing
    """
    
    @settings(max_examples=100)
    @given(
        api_title=string_values,
        api_version=string_values,
        ai_model=string_values,
    )
    def test_dependencies_return_same_instances(
        self, api_title: str, api_version: str, ai_model: str
    ):
        """Test that dependency getters return the same instances (singleton pattern)."""
        # Create test config
        config = create_test_config(
            api_title=api_title,
            api_version=api_version,
            ai_model=ai_model,
        )
        
        # Initialize dependencies with test config
        deps = initialize_dependencies(config=config)
        
        # Get dependencies multiple times
        config1 = get_config()
        config2 = get_config()
        logger1 = get_logger()
        logger2 = get_logger()
        client1 = get_gemini_client()
        client2 = get_gemini_client()
        service1 = get_forge_service()
        service2 = get_forge_service()
        
        # Verify same instances are returned (singleton pattern)
        assert config1 is config2
        assert logger1 is logger2
        assert client1 is client2
        assert service1 is service2
        
        # Verify they match the initialized dependencies
        assert config1 is deps.get_config()
        assert logger1 is deps.get_logger()
        assert client1 is deps.get_gemini_client()
        assert service1 is deps.get_forge_service()
    
    @settings(max_examples=100)
    @given(
        api_title=string_values,
        port=port_numbers,
        max_image_size=positive_integers,
    )
    def test_dependencies_have_correct_types(
        self, api_title: str, port: int, max_image_size: int
    ):
        """Test that all dependency getters return correct types."""
        # Create test config
        config = create_test_config(
            api_title=api_title,
            port=port,
            max_image_size=max_image_size,
        )
        
        # Initialize dependencies
        initialize_dependencies(config=config)
        
        # Get all dependencies
        retrieved_config = get_config()
        retrieved_logger = get_logger()
        retrieved_client = get_gemini_client()
        retrieved_service = get_forge_service()
        
        # Verify types
        assert isinstance(retrieved_config, Config)
        assert isinstance(retrieved_logger, StructuredLogger)
        # Client should implement the protocol (duck typing)
        assert hasattr(retrieved_client, 'generate_content')
        assert callable(retrieved_client.generate_content)
        assert isinstance(retrieved_service, ForgeService)
        
        # Verify config values are preserved
        assert retrieved_config.api_title == api_title
        assert retrieved_config.port == port
        assert retrieved_config.max_image_size == max_image_size
    
    @settings(max_examples=100)
    @given(
        api_key=string_values,
        ai_model=string_values,
    )
    def test_dependencies_can_be_overridden_for_testing(
        self, api_key: str, ai_model: str
    ):
        """Test that dependencies can be overridden with mock implementations."""
        # Create test config
        config = create_test_config(
            google_api_key=api_key,
            ai_model=ai_model,
        )
        
        # Create mock client
        mock_client = MockGeminiClient(api_key=api_key)
        mock_client.mock_response = "Test response"
        
        # Initialize dependencies with mock client
        deps = initialize_dependencies(
            config=config,
            gemini_client=mock_client,
        )
        
        # Get the client through dependency injection
        retrieved_client = get_gemini_client()
        
        # Verify it's the mock client
        assert retrieved_client is mock_client
        
        # Verify the mock works
        response = retrieved_client.generate_content(
            model=ai_model,
            contents=["test"],
        )
        assert response == "Test response"
        assert mock_client.call_count == 1
    
    @settings(max_examples=100)
    @given(
        log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    )
    def test_forge_service_receives_injected_dependencies(self, log_level: str):
        """Test that ForgeService receives all its dependencies through injection."""
        # Create test config
        config = create_test_config(log_level=log_level)
        
        # Create mock client
        mock_client = MockGeminiClient()
        
        # Initialize dependencies
        deps = initialize_dependencies(
            config=config,
            gemini_client=mock_client,
        )
        
        # Get ForgeService
        service = get_forge_service()
        
        # Verify ForgeService has the injected dependencies
        assert service.client is mock_client
        assert service.config is config
        assert isinstance(service.logger, StructuredLogger)
        
        # Verify the service uses the injected config
        assert service.config.log_level == log_level
    
    def test_uninitialized_dependencies_raise_error(self):
        """Test that accessing dependencies before initialization raises an error."""
        # Reset to ensure clean state
        reset_dependencies()
        
        # Attempting to get dependencies should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            get_dependencies()
        
        assert "not initialized" in str(exc_info.value).lower()
    
    @settings(max_examples=100)
    @given(
        api_title=string_values,
        api_version=string_values,
    )
    def test_dependencies_container_provides_all_services(
        self, api_title: str, api_version: str
    ):
        """Test that Dependencies container provides access to all services."""
        # Create test config
        config = create_test_config(
            api_title=api_title,
            api_version=api_version,
        )
        
        # Create dependencies container directly
        deps = Dependencies(config=config)
        
        # Verify all getters work
        assert deps.get_config() is config
        assert isinstance(deps.get_logger(), StructuredLogger)
        assert hasattr(deps.get_gemini_client(), 'generate_content')
        assert isinstance(deps.get_forge_service(), ForgeService)
        
        # Verify ForgeService is properly wired
        service = deps.get_forge_service()
        assert service.config is config
        assert service.client is deps.get_gemini_client()
        assert service.logger is deps.get_logger()
    
    @settings(max_examples=100)
    @given(
        max_image_size=positive_integers,
        max_audio_size=positive_integers,
    )
    def test_reset_dependencies_clears_state(
        self, max_image_size: int, max_audio_size: int
    ):
        """Test that reset_dependencies() properly clears the global state."""
        # Initialize dependencies
        config1 = create_test_config(
            max_image_size=max_image_size,
            max_audio_size=max_audio_size,
        )
        deps1 = initialize_dependencies(config=config1)
        service1 = get_forge_service()
        
        # Reset dependencies
        reset_dependencies()
        
        # Verify accessing dependencies raises error
        with pytest.raises(RuntimeError):
            get_dependencies()
        
        # Initialize again with different config
        config2 = create_test_config(
            max_image_size=max_image_size * 2,
            max_audio_size=max_audio_size * 2,
        )
        deps2 = initialize_dependencies(config=config2)
        service2 = get_forge_service()
        
        # Verify new instances are created
        assert service1 is not service2
        assert deps1 is not deps2
        
        # Verify new config values
        assert get_config().max_image_size == max_image_size * 2
        assert get_config().max_audio_size == max_audio_size * 2
    
    @settings(max_examples=100)
    @given(
        api_key=string_values,
    )
    def test_custom_logger_can_be_injected(self, api_key: str):
        """Test that a custom logger can be injected into dependencies."""
        # Create test config
        config = create_test_config(google_api_key=api_key)
        
        # Create custom logger
        custom_logger = StructuredLogger("custom_test_logger", level="DEBUG")
        
        # Initialize dependencies with custom logger
        deps = initialize_dependencies(
            config=config,
            logger=custom_logger,
        )
        
        # Verify the custom logger is used
        retrieved_logger = get_logger()
        assert retrieved_logger is custom_logger
        
        # Verify ForgeService uses the custom logger
        service = get_forge_service()
        assert service.logger is custom_logger
