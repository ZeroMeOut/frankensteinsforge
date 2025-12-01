"""Property-based tests for ForgeService response validation and sanitization"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.services.forge_service import ForgeService
from app.core.config import Config
from app.core.logging import StructuredLogger
from app.core.exceptions import ValidationError, ExternalAPIError


class MockGeminiClient:
    """Mock Gemini client for testing"""
    
    def __init__(self):
        self.response = "Mock generated content"
        self.should_fail = False
        self.failure_message = "API call failed"
    
    def generate_content(self, model: str, contents: list, **kwargs) -> str:
        """Generate mock content"""
        if self.should_fail:
            raise Exception(self.failure_message)
        return self.response
    
    def set_response(self, response: str):
        """Set the mock response"""
        self.response = response
    
    def set_failure(self, should_fail: bool, message: str = "API call failed"):
        """Configure mock to fail"""
        self.should_fail = should_fail
        self.failure_message = message


def create_forge_service():
    """Helper function to create a ForgeService instance with mocked dependencies"""
    mock_config = Config(
        google_api_key="test-api-key",
        ai_model="test-model"
    )
    mock_logger = StructuredLogger("test", level="INFO")
    mock_client = MockGeminiClient()
    
    forge_service = ForgeService(
        client=mock_client,
        config=mock_config,
        logger=mock_logger
    )
    
    return forge_service, mock_client


class TestResponseContentValidation:
    """Property-based tests for response content validation"""
    
    @given(
        response=st.one_of(
            st.none(),
            st.just(""),
            st.just("   "),
            st.just("\n\t  \n"),
            st.text(min_size=1, max_size=9).filter(lambda x: len(x.strip()) < 10)
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_17_response_content_validation(self, response):
        """
        **Feature: api-improvements, Property 17: Response content validation**
        **Validates: Requirements 5.1**
        
        Property: For any response from the Gemini API, the validation should verify 
        that the response contains non-empty text content.
        
        This test verifies that:
        1. None responses are rejected
        2. Empty string responses are rejected
        3. Whitespace-only responses are rejected
        4. Responses shorter than minimum length are rejected
        """
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Set the mock to return the test response
        mock_client.set_response(response)
        
        # All these responses should be rejected with ValidationError
        with pytest.raises(ValidationError) as exc_info:
            forge_service.generate_steps("test idea")
        
        # Verify the error indicates empty or insufficient response
        error = exc_info.value
        assert error.status_code == 400
        assert "empty" in error.message.lower() or "insufficient" in error.message.lower()
        
        # Verify fallback message is provided
        assert "fallback" in error.details
        assert isinstance(error.details["fallback"], str)
        assert len(error.details["fallback"]) > 0
    
    @given(
        response=st.text(
            min_size=10,
            max_size=1000,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
                whitelist_characters=' \n\t\r'
            )
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_17_valid_response_accepted(self, response):
        """
        Property: For any valid response (non-empty, sufficient length), 
        the validation should accept it.
        """
        # Filter out responses that are only whitespace
        assume(len(response.strip()) >= 10)
        
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Set the mock to return the test response
        mock_client.set_response(response)
        
        # This should succeed
        result = forge_service.generate_steps("test idea")
        
        # Result should be a string
        assert isinstance(result, str)
        
        # Result should have sufficient length
        assert len(result.strip()) >= 10


class TestResponseCharacterSanitization:
    """Property-based tests for response character sanitization"""
    
    @given(
        # Generate text with control characters mixed in
        base_text=st.text(min_size=20, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
            whitelist_characters=' \n\t'
        )),
        control_chars=st.lists(
            st.sampled_from(['\x00', '\x01', '\x02', '\x08', '\x0b', '\x0c', '\x0e', '\x1f', '\x7f']),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_18_response_character_sanitization(
        self, 
        base_text,
        control_chars
    ):
        """
        **Feature: api-improvements, Property 18: Response character sanitization**
        **Validates: Requirements 5.4**
        
        Property: For any response containing invalid or dangerous characters, 
        the sanitization should remove or escape those characters.
        
        This test verifies that control characters (0x00-0x08, 0x0b, 0x0c, 0x0e-0x1f, 0x7f-0x9f)
        are removed from responses while preserving valid content.
        """
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Insert control characters into the text
        text_with_control = base_text
        for char in control_chars:
            # Insert control character at random position
            pos = len(text_with_control) // 2
            text_with_control = text_with_control[:pos] + char + text_with_control[pos:]
        
        # Set the mock to return text with control characters
        mock_client.set_response(text_with_control)
        
        # Generate content
        result = forge_service.generate_steps("test idea")
        
        # Verify control characters are removed
        for char in control_chars:
            assert char not in result, f"Control character {repr(char)} was not sanitized"
        
        # Verify the base text content is preserved (at least most of it)
        # We check that the result contains significant portions of the original text
        # (allowing for some variation due to control character removal)
        assert len(result.strip()) >= len(base_text.strip()) * 0.8, (
            "Too much content was removed during sanitization"
        )
    
    @given(
        # Generate text with only valid characters
        valid_text=st.text(
            min_size=20,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
                whitelist_characters=' \n\t\r'
            )
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_18_valid_characters_preserved(
        self,
        valid_text
    ):
        """
        Property: For any response containing only valid characters,
        the sanitization should preserve the content unchanged.
        """
        # Ensure text has sufficient length
        assume(len(valid_text.strip()) >= 10)
        
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Set the mock to return valid text
        mock_client.set_response(valid_text)
        
        # Generate content
        result = forge_service.generate_steps("test idea")
        
        # Result should be identical to input (or truncated if too long)
        if len(valid_text) <= ForgeService.MAX_RESPONSE_LENGTH:
            assert result == valid_text
        else:
            # If truncated, should match up to max length
            assert result.startswith(valid_text[:ForgeService.MAX_RESPONSE_LENGTH])


class TestValidationFailureFallback:
    """Property-based tests for validation failure fallback messages"""
    
    @given(
        failure_type=st.sampled_from([
            "empty_response",
            "none_response",
            "whitespace_only",
            "too_short"
        ])
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_19_validation_failure_fallback(
        self,
        failure_type
    ):
        """
        **Feature: api-improvements, Property 19: Validation failure fallback**
        **Validates: Requirements 5.5**
        
        Property: For any response that fails validation, the system should provide 
        a user-friendly fallback error message instead of exposing internal errors.
        
        This test verifies that:
        1. Validation errors include a fallback message
        2. Fallback messages are user-friendly (not technical)
        3. Fallback messages don't expose internal implementation details
        """
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Configure mock based on failure type
        if failure_type == "empty_response":
            mock_client.set_response("")
        elif failure_type == "none_response":
            mock_client.set_response(None)
        elif failure_type == "whitespace_only":
            mock_client.set_response("   \n\t  ")
        elif failure_type == "too_short":
            mock_client.set_response("short")
        
        # Attempt to generate content
        with pytest.raises(ValidationError) as exc_info:
            forge_service.generate_steps("test idea")
        
        error = exc_info.value
        
        # Verify fallback message exists
        assert "fallback" in error.details, "Validation error should include fallback message"
        fallback = error.details["fallback"]
        
        # Verify fallback is a non-empty string
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        
        # Verify fallback is user-friendly (contains common user-facing words)
        user_friendly_words = ["try again", "unable", "please", "content", "generate"]
        assert any(word in fallback.lower() for word in user_friendly_words), (
            f"Fallback message should be user-friendly, got: {fallback}"
        )
        
        # Verify fallback doesn't expose technical details
        technical_terms = ["exception", "stack trace", "null", "none", "validation", "sanitize"]
        assert not any(term in fallback.lower() for term in technical_terms), (
            f"Fallback message should not expose technical details, got: {fallback}"
        )
    
    @given(
        api_error_message=st.text(min_size=10, max_size=100)
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_19_api_failure_fallback(
        self,
        api_error_message
    ):
        """
        Property: For any API failure, the system should wrap the error
        and provide appropriate error classification without exposing raw API errors.
        """
        # Create fresh instances for each test
        forge_service, mock_client = create_forge_service()
        
        # Configure mock to fail
        mock_client.set_failure(True, api_error_message)
        
        # Attempt to generate content
        with pytest.raises(ExternalAPIError) as exc_info:
            forge_service.generate_steps("test idea")
        
        error = exc_info.value
        
        # Verify error is properly wrapped
        assert error.status_code == 502
        assert "AI service" in error.message or "generate" in error.message
        
        # Verify error details are provided but sanitized
        assert "error" in error.details or "error_type" in error.details
        
        # The main error message should be user-friendly
        assert len(error.message) > 0
        assert not error.message.startswith("Exception:")
