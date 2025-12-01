"""
Dependency injection container for Frankenstein's Forge API.

This module provides centralized dependency management and injection
for the application, making components loosely coupled and testable.
"""
from typing import Optional
from app.core.config import Config
from app.core.logging import StructuredLogger, setup_logging
from app.core.gemini_client import GeminiClient, GeminiClientProtocol
from app.services.forge_service import ForgeService


class Dependencies:
    """Application dependencies container.
    
    This class manages the lifecycle and initialization of all application
    dependencies, providing a centralized location for dependency creation
    and configuration.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        gemini_client: Optional[GeminiClientProtocol] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """Initialize dependencies container.
        
        Args:
            config: Optional Config instance (creates new if not provided)
            gemini_client: Optional Gemini client (creates new if not provided)
            logger: Optional logger instance (creates new if not provided)
        """
        # Initialize configuration
        self.config = config if config is not None else Config.from_env()
        
        # Initialize logger
        self.logger = logger if logger is not None else setup_logging(
            level=self.config.log_level
        )
        
        # Initialize Gemini client
        self.gemini_client = gemini_client if gemini_client is not None else GeminiClient(
            api_key=self.config.google_api_key,
            max_retries=3
        )
        
        # Initialize ForgeService
        self.forge_service = ForgeService(
            client=self.gemini_client,
            config=self.config,
            logger=self.logger
        )
        
        self.logger.info(
            "Dependencies initialized",
            ai_model=self.config.ai_model,
            log_level=self.config.log_level
        )
    
    def get_config(self) -> Config:
        """Get Config instance.
        
        Returns:
            Config: Application configuration
        """
        return self.config
    
    def get_logger(self) -> StructuredLogger:
        """Get StructuredLogger instance.
        
        Returns:
            StructuredLogger: Application logger
        """
        return self.logger
    
    def get_gemini_client(self) -> GeminiClientProtocol:
        """Get Gemini client instance.
        
        Returns:
            GeminiClientProtocol: Gemini API client
        """
        return self.gemini_client
    
    def get_forge_service(self) -> ForgeService:
        """Get ForgeService instance.
        
        Returns:
            ForgeService: Forge service for idea generation
        """
        return self.forge_service


# Global dependencies instance
_dependencies: Optional[Dependencies] = None


def get_dependencies() -> Dependencies:
    """Get the global dependencies instance.
    
    This function is used as a FastAPI dependency to inject
    the dependencies container into endpoints.
    
    Returns:
        Dependencies: The global dependencies instance
        
    Raises:
        RuntimeError: If dependencies have not been initialized
    """
    global _dependencies
    if _dependencies is None:
        raise RuntimeError(
            "Dependencies not initialized. Call initialize_dependencies() first."
        )
    return _dependencies


def initialize_dependencies(
    config: Optional[Config] = None,
    gemini_client: Optional[GeminiClientProtocol] = None,
    logger: Optional[StructuredLogger] = None
) -> Dependencies:
    """Initialize the global dependencies instance.
    
    This should be called once at application startup.
    
    Args:
        config: Optional Config instance
        gemini_client: Optional Gemini client
        logger: Optional logger instance
        
    Returns:
        Dependencies: The initialized dependencies instance
    """
    global _dependencies
    _dependencies = Dependencies(
        config=config,
        gemini_client=gemini_client,
        logger=logger
    )
    return _dependencies


def reset_dependencies() -> None:
    """Reset the global dependencies instance.
    
    This is primarily useful for testing to ensure a clean state
    between test runs.
    """
    global _dependencies
    _dependencies = None


# FastAPI dependency functions for injection
def get_config() -> Config:
    """FastAPI dependency to inject Config.
    
    Returns:
        Config: Application configuration
    """
    return get_dependencies().get_config()


def get_logger() -> StructuredLogger:
    """FastAPI dependency to inject StructuredLogger.
    
    Returns:
        StructuredLogger: Application logger
    """
    return get_dependencies().get_logger()


def get_gemini_client() -> GeminiClientProtocol:
    """FastAPI dependency to inject Gemini client.
    
    Returns:
        GeminiClientProtocol: Gemini API client
    """
    return get_dependencies().get_gemini_client()


def get_forge_service() -> ForgeService:
    """FastAPI dependency to inject ForgeService.
    
    Returns:
        ForgeService: Forge service for idea generation
    """
    return get_dependencies().get_forge_service()
