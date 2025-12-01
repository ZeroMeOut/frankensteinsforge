"""Test to verify testing infrastructure is properly set up"""
import pytest
from pathlib import Path
from hypothesis import given, strategies as st


@pytest.mark.unit
def test_fixtures_directory_exists(fixtures_dir):
    """Verify fixtures directory exists"""
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


@pytest.mark.unit
def test_sample_files_exist(sample_image_path, sample_audio_path):
    """Verify sample test files exist"""
    assert sample_image_path.exists()
    assert sample_audio_path.exists()


@pytest.mark.unit
def test_sample_image_bytes(sample_image_bytes):
    """Verify sample image bytes are loaded"""
    assert isinstance(sample_image_bytes, bytes)
    assert len(sample_image_bytes) > 0
    # Check JPEG magic bytes
    assert sample_image_bytes[:2] == b'\xff\xd8'


@pytest.mark.unit
def test_sample_audio_bytes(sample_audio_bytes):
    """Verify sample audio bytes are loaded"""
    assert isinstance(sample_audio_bytes, bytes)
    assert len(sample_audio_bytes) > 0
    # Check WAV magic bytes
    assert sample_audio_bytes[:4] == b'RIFF'


@pytest.mark.unit
def test_sample_text_fixture(sample_text):
    """Verify sample text fixture"""
    assert isinstance(sample_text, str)
    assert len(sample_text) > 0


@pytest.mark.unit
def test_config_fixture(test_config):
    """Verify test configuration fixture"""
    assert isinstance(test_config, dict)
    assert "api_title" in test_config
    assert "google_api_key" in test_config
    assert test_config["max_image_size"] > 0


@pytest.mark.property
@given(st.text(min_size=1, max_size=100))
def test_hypothesis_integration(text):
    """Verify Hypothesis property-based testing works"""
    assert isinstance(text, str)
    assert len(text) >= 1
    assert len(text) <= 100


@pytest.mark.unit
def test_project_structure():
    """Verify project directory structure exists"""
    base_dir = Path(__file__).parent.parent
    
    # Check app directories
    assert (base_dir / "app").exists()
    assert (base_dir / "app" / "core").exists()
    assert (base_dir / "app" / "services").exists()
    assert (base_dir / "app" / "validators").exists()
    assert (base_dir / "app" / "models").exists()
    
    # Check tests directory
    assert (base_dir / "tests").exists()
    assert (base_dir / "tests" / "fixtures").exists()
    
    # Check configuration files
    assert (base_dir / "pytest.ini").exists()
    assert (base_dir / "requirements.txt").exists()
