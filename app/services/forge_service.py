"""
Forge service for AI-powered idea generation with dependency injection.

This module provides the core business logic for generating creative ideas
from multimodal inputs (images, audio, text) using the Gemini API.
"""
import re
from typing import Protocol
from google.genai import types
from app.core.config import Config
from app.core.logging import StructuredLogger
from app.core.exceptions import ValidationError, ExternalAPIError


class GeminiClientProtocol(Protocol):
    """Protocol for Gemini API clients"""
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate content from multimodal inputs"""
        ...


class ForgeService:
    """Service for AI-powered idea generation with proper dependency injection"""
    
    # Maximum response length before truncation
    MAX_RESPONSE_LENGTH = 10000
    
    # Minimum response length to be considered valid
    MIN_RESPONSE_LENGTH = 10
    
    # Invalid characters that should be removed/sanitized
    INVALID_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
    
    def __init__(
        self,
        client: GeminiClientProtocol,
        config: Config,
        logger: StructuredLogger
    ):
        """Initialize ForgeService with dependencies.
        
        Args:
            client: Gemini API client implementation
            config: Application configuration
            logger: Structured logger instance
        """
        self.client = client
        self.config = config
        self.logger = logger
    
    def generate_idea(
        self,
        image_bytes: bytes,
        audio_bytes: bytes,
        text: str
    ) -> str:
        """Generate creative idea from multimodal inputs.
        
        Args:
            image_bytes: Image file bytes
            audio_bytes: Audio file bytes
            text: User text input
            
        Returns:
            Generated idea text
            
        Raises:
            ValidationError: If inputs are invalid
            ExternalAPIError: If API call fails
        """
        self.logger.info(
            "Generating idea from multimodal inputs",
            text_length=len(text)
        )
        
        # Validate inputs
        if not text or not text.strip():
            raise ValidationError(
                "Text input cannot be empty",
                details={"field": "text", "reason": "empty_input"}
            )
        
        if not image_bytes:
            raise ValidationError(
                "Image data cannot be empty",
                details={"field": "image", "reason": "empty_input"}
            )
        
        if not audio_bytes:
            raise ValidationError(
                "Audio data cannot be empty",
                details={"field": "audio", "reason": "empty_input"}
            )
        
        # Build prompt
        prompt = f"""Analyze these inputs and create an achievable idea. Start with 'create a' or 'make a':

User text: {text}

Consider the image content and audio sentiment to generate a creative, actionable idea."""
        
        # Prepare contents for API call
        contents = [
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg',
            ),
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/wav',
            )
        ]
        
        try:
            # Call API
            response = self.client.generate_content(
                model=self.config.ai_model,
                contents=contents
            )
            
            # Validate and sanitize response
            validated_response = self._validate_response(response)
            
            self.logger.info(
                "Successfully generated idea",
                response_length=len(validated_response)
            )
            
            return validated_response
            
        except Exception as e:
            self.logger.error(
                "Failed to generate idea",
                exc_info=e,
                error_type=type(e).__name__
            )
            
            # Check if this is already one of our custom exceptions
            if isinstance(e, (ValidationError, ExternalAPIError)):
                raise
            
            # Wrap other exceptions as ExternalAPIError
            raise ExternalAPIError(
                "Failed to generate idea from AI service",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ) from e
    
    def generate_steps(self, idea: str) -> str:
        """Generate implementation steps for an idea.
        
        Args:
            idea: The idea to generate steps for
            
        Returns:
            Generated implementation steps
            
        Raises:
            ValidationError: If idea is invalid
            ExternalAPIError: If API call fails
        """
        self.logger.info(
            "Generating implementation steps",
            idea_length=len(idea)
        )
        
        # Validate input
        if not idea or not idea.strip():
            raise ValidationError(
                "Idea cannot be empty",
                details={"field": "idea", "reason": "empty_input"}
            )
        
        if len(idea) > 2000:
            raise ValidationError(
                "Idea is too long (maximum 2000 characters)",
                details={
                    "field": "idea",
                    "reason": "exceeds_max_length",
                    "max_length": 2000,
                    "actual_length": len(idea)
                }
            )
        
        # Build prompt
        prompt = f"""Given this idea: "{idea}"

Generate a clear, actionable step-by-step implementation plan.

Format your response as a well-structured numbered list with:
- Main steps numbered (1, 2, 3, etc.)
- Sub-steps with letters (a, b, c, etc.) if needed
- Clear spacing between sections
- Concise but actionable descriptions

Keep each step clear and actionable."""
        
        try:
            # Call API
            response = self.client.generate_content(
                model=self.config.ai_model,
                contents=[prompt]
            )
            
            # Validate and sanitize response
            validated_response = self._validate_response(response)
            
            self.logger.info(
                "Successfully generated steps",
                response_length=len(validated_response)
            )
            
            return validated_response
            
        except Exception as e:
            self.logger.error(
                "Failed to generate steps",
                exc_info=e,
                error_type=type(e).__name__
            )
            
            # Check if this is already one of our custom exceptions
            if isinstance(e, (ValidationError, ExternalAPIError)):
                raise
            
            # Wrap other exceptions as ExternalAPIError
            raise ExternalAPIError(
                "Failed to generate steps from AI service",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ) from e
    
    def refine_idea(self, idea: str, refinement_type: str = "variation") -> str:
        """Refine or vary an existing idea.
        
        Args:
            idea: The idea to refine
            refinement_type: Type of refinement ('variation', 'simpler', 'more_ambitious')
            
        Returns:
            Refined idea text
            
        Raises:
            ValidationError: If inputs are invalid
            ExternalAPIError: If API call fails
        """
        self.logger.info(
            "Refining idea",
            idea_length=len(idea),
            refinement_type=refinement_type
        )
        
        # Validate input
        if not idea or not idea.strip():
            raise ValidationError(
                "Idea cannot be empty",
                details={"field": "idea", "reason": "empty_input"}
            )
        
        if len(idea) > 2000:
            raise ValidationError(
                "Idea is too long (maximum 2000 characters)",
                details={
                    "field": "idea",
                    "reason": "exceeds_max_length",
                    "max_length": 2000,
                    "actual_length": len(idea)
                }
            )
        
        # Validate refinement type
        valid_types = ["variation", "simpler", "more_ambitious"]
        if refinement_type not in valid_types:
            raise ValidationError(
                f"Invalid refinement type: {refinement_type}",
                details={
                    "field": "refinement_type",
                    "reason": "invalid_value",
                    "valid_values": valid_types,
                    "actual_value": refinement_type
                }
            )
        
        # Build prompt based on refinement type
        prompts = {
            "variation": f"Create a creative variation of this idea: '{idea}'. Keep the core concept but add a unique twist or different approach.",
            "simpler": f"Simplify this idea to make it more achievable: '{idea}'. Focus on the MVP (Minimum Viable Product) version.",
            "more_ambitious": f"Expand this idea to be more ambitious and impactful: '{idea}'. Think bigger scale and broader reach."
        }
        
        prompt = prompts[refinement_type]
        
        try:
            # Call API
            response = self.client.generate_content(
                model=self.config.ai_model,
                contents=[prompt]
            )
            
            # Validate and sanitize response
            validated_response = self._validate_response(response)
            
            self.logger.info(
                "Successfully refined idea",
                response_length=len(validated_response),
                refinement_type=refinement_type
            )
            
            return validated_response
            
        except Exception as e:
            self.logger.error(
                "Failed to refine idea",
                exc_info=e,
                error_type=type(e).__name__,
                refinement_type=refinement_type
            )
            
            # Check if this is already one of our custom exceptions
            if isinstance(e, (ValidationError, ExternalAPIError)):
                raise
            
            # Wrap other exceptions as ExternalAPIError
            raise ExternalAPIError(
                "Failed to refine idea from AI service",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "refinement_type": refinement_type
                }
            ) from e
    
    def _validate_response(self, response: str) -> str:
        """Validate and sanitize AI response.
        
        Args:
            response: Raw response from AI
            
        Returns:
            Validated and sanitized response
            
        Raises:
            ValidationError: If response is invalid
        """
        # Check if response is None or empty
        if response is None:
            self.logger.warning("Received None response from AI")
            raise ValidationError(
                "AI service returned empty response",
                details={
                    "reason": "empty_response",
                    "fallback": "Unable to generate content. Please try again."
                }
            )
        
        # Convert to string if needed
        if not isinstance(response, str):
            response = str(response)
        
        # Check if response is empty or only whitespace
        if not response.strip():
            self.logger.warning("Received empty response from AI")
            raise ValidationError(
                "AI service returned empty response",
                details={
                    "reason": "empty_response",
                    "fallback": "Unable to generate content. Please try again."
                }
            )
        
        # Check minimum length
        if len(response.strip()) < self.MIN_RESPONSE_LENGTH:
            self.logger.warning(
                "Response too short",
                response_length=len(response.strip()),
                min_length=self.MIN_RESPONSE_LENGTH
            )
            raise ValidationError(
                "AI service returned insufficient content",
                details={
                    "reason": "response_too_short",
                    "min_length": self.MIN_RESPONSE_LENGTH,
                    "actual_length": len(response.strip()),
                    "fallback": "Unable to generate sufficient content. Please try again."
                }
            )
        
        # Sanitize invalid characters
        sanitized = self._sanitize_response(response)
        
        # Check if sanitization removed too much content
        if len(sanitized.strip()) < self.MIN_RESPONSE_LENGTH:
            self.logger.warning(
                "Response too short after sanitization",
                original_length=len(response),
                sanitized_length=len(sanitized.strip())
            )
            raise ValidationError(
                "AI service returned content with too many invalid characters",
                details={
                    "reason": "invalid_content_after_sanitization",
                    "fallback": "Unable to generate valid content. Please try again."
                }
            )
        
        # Truncate if too long
        if len(sanitized) > self.MAX_RESPONSE_LENGTH:
            self.logger.warning(
                "Response exceeds maximum length, truncating",
                original_length=len(sanitized),
                max_length=self.MAX_RESPONSE_LENGTH
            )
            sanitized = sanitized[:self.MAX_RESPONSE_LENGTH] + "..."
        
        return sanitized
    
    def _sanitize_response(self, response: str) -> str:
        """Sanitize response by removing invalid characters.
        
        Args:
            response: Response text to sanitize
            
        Returns:
            Sanitized response text
        """
        # Remove control characters and other invalid characters
        # Keep newlines, tabs, and carriage returns
        sanitized = self.INVALID_CHAR_PATTERN.sub('', response)
        
        return sanitized
