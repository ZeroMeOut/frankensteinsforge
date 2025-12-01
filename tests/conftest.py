"""Shared test fixtures and configuration for pytest"""
import os
import pytest
from pathlib import Path
from hypothesis import settings

# Configure Hypothesis profiles
settings.register_profile("ci", max_examples=100, deadline=5000)
settings.register_profile("dev", max_examples=20, deadline=None)

# Load profile based on environment
profile = os.getenv("HYPOTHESIS_PROFILE", "dev")
settings.load_profile(profile)


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_image_path(fixtures_dir: Path) -> Path:
    """Return path to sample image file"""
    return fixtures_dir / "sample_image.jpg"


@pytest.fixture
def sample_audio_path(fixtures_dir: Path) -> Path:
    """Return path to sample audio file"""
    return fixtures_dir / "sample_audio.wav"


@pytest.fixture
def sample_image_bytes(sample_image_path: Path) -> bytes:
    """Return sample image file as bytes"""
    if sample_image_path.exists():
        return sample_image_path.read_bytes()
    # Return minimal valid JPEG if file doesn't exist
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9'


@pytest.fixture
def sample_audio_bytes(sample_audio_path: Path) -> bytes:
    """Return sample audio file as bytes"""
    if sample_audio_path.exists():
        return sample_audio_path.read_bytes()
    # Return minimal valid WAV header if file doesn't exist
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


@pytest.fixture
def sample_text() -> str:
    """Return sample text input"""
    return "I want to build something creative with AI"


@pytest.fixture
def test_config():
    """Return test configuration dictionary"""
    return {
        "api_title": "Test API",
        "api_version": "1.0.0",
        "host": "0.0.0.0",
        "port": 8000,
        "max_image_size": 10 * 1024 * 1024,  # 10MB
        "max_audio_size": 20 * 1024 * 1024,  # 20MB
        "google_api_key": "test-api-key",
        "ai_model": "gemini-2.0-flash-exp",
        "enable_rate_limiting": False,
        "enable_structured_logging": True,
    }
