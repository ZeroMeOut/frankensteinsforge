"""
Configuration management for Frankenstein's Forge API.

This module provides centralized, type-safe configuration management
with environment variable support and validation.
"""
import os
from typing import Optional
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application configuration with validation.
    
    Configuration values can be set via:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values (lowest priority)
    """
    
    # API Settings
    api_title: str = Field(
        default="Frankenstein's Forge API",
        description="API title displayed in documentation"
    )
    api_description: str = Field(
        default="Multimodal AI API that processes images, audio, and text to generate creative ideas",
        description="API description"
    )
    api_version: str = Field(
        default="1.1.0",
        description="API version"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number"
    )
    reload: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    
    # File Upload Limits (in bytes)
    max_image_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        gt=0,
        description="Maximum image file size in bytes"
    )
    max_audio_size: int = Field(
        default=20 * 1024 * 1024,  # 20MB
        gt=0,
        description="Maximum audio file size in bytes"
    )
    
    # AI Model Configuration
    google_api_key: str = Field(
        ...,  # Required field
        min_length=1,
        description="Google API key for Gemini"
    )
    ai_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="AI model to use for generation"
    )
    
    # Feature Flags
    enable_rate_limiting: bool = Field(
        default=False,
        description="Enable rate limiting middleware"
    )
    enable_structured_logging: bool = Field(
        default=True,
        description="Enable structured JSON logging"
    )
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(
        default=10,
        gt=0,
        description="Maximum requests per time window"
    )
    rate_limit_period: int = Field(
        default=60,
        gt=0,
        description="Rate limit time window in seconds"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Development Settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    testing: bool = Field(
        default=False,
        description="Enable testing mode"
    )
    
    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Allow overriding env_file via environment variable for testing
        env_prefix=""
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{v}'"
            )
        return v_upper
    
    @field_validator("ai_model")
    @classmethod
    def validate_ai_model(cls, v: str) -> str:
        """Validate AI model name is not empty."""
        if not v or not v.strip():
            raise ValueError("ai_model cannot be empty")
        return v.strip()
    
    def validate(self) -> None:
        """
        Validate all configuration values.
        
        This method performs additional validation beyond field-level checks.
        Raises ValidationError if any validation fails.
        """
        # Port validation
        if not (1 <= self.port <= 65535):
            raise ValueError(
                f"port must be between 1 and 65535, got {self.port}"
            )
        
        # File size validation
        if self.max_image_size <= 0:
            raise ValueError(
                f"max_image_size must be positive, got {self.max_image_size}"
            )
        
        if self.max_audio_size <= 0:
            raise ValueError(
                f"max_audio_size must be positive, got {self.max_audio_size}"
            )
        
        # API key validation
        if not self.google_api_key or not self.google_api_key.strip():
            raise ValueError(
                "google_api_key is required and cannot be empty"
            )
        
        # Rate limiting validation
        if self.enable_rate_limiting:
            if self.rate_limit_requests <= 0:
                raise ValueError(
                    f"rate_limit_requests must be positive when rate limiting is enabled, "
                    f"got {self.rate_limit_requests}"
                )
            if self.rate_limit_period <= 0:
                raise ValueError(
                    f"rate_limit_period must be positive when rate limiting is enabled, "
                    f"got {self.rate_limit_period}"
                )
    
    @classmethod
    def from_env(cls, _env_file: Optional[str] = ".env") -> "Config":
        """
        Load configuration from environment variables and .env file.
        
        Args:
            _env_file: Path to .env file, or None to disable .env loading
        
        Returns:
            Config: Configured instance
            
        Raises:
            ValidationError: If required configuration is missing or invalid
        """
        try:
            # Temporarily override env_file setting
            if _env_file is None:
                # Create config without loading .env file
                original_env_file = cls.model_config.get("env_file")
                cls.model_config["env_file"] = None
                try:
                    config = cls()
                finally:
                    cls.model_config["env_file"] = original_env_file
            else:
                config = cls()
            
            config.validate()
            return config
        except ValidationError as e:
            # Re-raise with clearer error message
            missing_fields = []
            invalid_fields = []
            
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                error_type = error["type"]
                
                if error_type == "missing":
                    missing_fields.append(field)
                else:
                    invalid_fields.append(f"{field}: {error['msg']}")
            
            error_parts = []
            if missing_fields:
                error_parts.append(
                    f"Missing required configuration: {', '.join(missing_fields)}"
                )
            if invalid_fields:
                error_parts.append(
                    f"Invalid configuration: {'; '.join(invalid_fields)}"
                )
            
            raise ValueError(" | ".join(error_parts)) from e


# Global configuration instance (initialized on first import)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The global configuration instance
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """
    Reset the global configuration instance.
    
    This is primarily useful for testing.
    """
    global _config
    _config = None
