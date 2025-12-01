"""Integration tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from unittest.mock import Mock, patch
from app.core.config import Config
from app.core.dependencies import initialize_dependencies, reset_dependencies
from app.core.gemini_client import MockGeminiClient


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client for testing"""
    client = MockGeminiClient()
    return client


@pytest.fixture
def test_app(mock_gemini_client):
    """Create test FastAPI application with mocked dependencies"""
    # Reset dependencies before each test
    reset_dependencies()
    
    # Create test config
    config = Config(
        api_title="Test API",
        api_version="1.0.0",
        host="0.0.0.0",
        port=8000,
        max_image_size=10 * 1024 * 1024,
        max_audio_size=20 * 1024 * 1024,
        google_api_key="test-api-key",
        ai_model="gemini-2.0-flash-exp",
        enable_rate_limiting=False,
        enable_structured_logging=False,
        log_level="ERROR"
    )
    
    # Initialize dependencies with mock client
    deps = initialize_dependencies(config=config, gemini_client=mock_gemini_client)
    
    # Import the FastAPI app from app.py (not the app package)
    import sys
    import importlib.util
    import os
    
    # Get the path to app.py
    app_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
    
    # Load the module from the file
    spec = importlib.util.spec_from_file_location("app_module", app_py_path)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    # Manually set up error handlers for testing (since startup event may not fire)
    from app.core.error_handlers import setup_error_handlers
    setup_error_handlers(app_module.app, deps.get_logger())
    
    yield app_module.app
    
    # Cleanup
    reset_dependencies()


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def valid_image_bytes():
    """Return valid JPEG image bytes"""
    # Minimal valid JPEG
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9'


@pytest.fixture
def valid_audio_bytes():
    """Return valid WAV audio bytes"""
    # Minimal valid WAV
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


class TestGenerateEndpoint:
    """Integration tests for /generate endpoint"""
    
    def test_successful_generation_with_valid_inputs(
        self,
        client,
        valid_image_bytes,
        valid_audio_bytes
    ):
        """Test successful generation with valid inputs"""
        # Prepare multipart form data
        files = {
            'image': ('test.jpg', BytesIO(valid_image_bytes), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(valid_audio_bytes), 'audio/wav')
        }
        data = {
            'text': 'I want to build something creative'
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
        assert 'idea' in json_data
        assert len(json_data['idea']) > 0
        assert 'request_id' in json_data
        assert 'inputs' in json_data
        assert json_data['inputs']['text'] == 'I want to build something creative'
    
    def test_validation_error_with_invalid_image_type(
        self,
        client,
        valid_audio_bytes
    ):
        """Test validation errors with invalid image file"""
        # Prepare invalid image (text file pretending to be image)
        invalid_image = b'This is not an image file'
        
        files = {
            'image': ('test.jpg', BytesIO(invalid_image), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(valid_audio_bytes), 'audio/wav')
        }
        data = {
            'text': 'I want to build something creative'
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code == 400
        json_data = response.json()
        assert json_data['success'] is False
        assert 'error' in json_data
        assert 'image' in json_data['error'].lower() or 'image' in str(json_data.get('details', {})).lower()
    
    def test_validation_error_with_invalid_audio_type(
        self,
        client,
        valid_image_bytes
    ):
        """Test validation errors with invalid audio file"""
        # Prepare invalid audio (text file pretending to be audio)
        invalid_audio = b'This is not an audio file'
        
        files = {
            'image': ('test.jpg', BytesIO(valid_image_bytes), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(invalid_audio), 'audio/wav')
        }
        data = {
            'text': 'I want to build something creative'
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code == 400
        json_data = response.json()
        assert json_data['success'] is False
        assert 'error' in json_data
        assert 'audio' in json_data['error'].lower() or 'audio' in str(json_data.get('details', {})).lower()
    
    def test_validation_error_with_empty_text(
        self,
        client,
        valid_image_bytes,
        valid_audio_bytes
    ):
        """Test validation errors with empty text input"""
        files = {
            'image': ('test.jpg', BytesIO(valid_image_bytes), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(valid_audio_bytes), 'audio/wav')
        }
        data = {
            'text': '   '  # Only whitespace
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # 400 or 422 for validation error
        json_data = response.json()
        assert json_data['success'] is False
    
    def test_validation_error_with_oversized_image(
        self,
        client,
        valid_audio_bytes
    ):
        """Test validation errors with oversized image file"""
        # Create image larger than 10MB
        oversized_image = b'\xff\xd8\xff\xe0' + (b'x' * (11 * 1024 * 1024))
        
        files = {
            'image': ('test.jpg', BytesIO(oversized_image), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(valid_audio_bytes), 'audio/wav')
        }
        data = {
            'text': 'I want to build something creative'
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code == 400
        json_data = response.json()
        assert json_data['success'] is False
        assert 'error' in json_data
        assert 'size' in json_data['error'].lower() or 'size' in str(json_data.get('details', {})).lower()
    
    def test_error_handling_with_mocked_api_failure(
        self,
        client,
        valid_image_bytes,
        valid_audio_bytes,
        mock_gemini_client
    ):
        """Test error handling with mocked API failures"""
        # Configure mock to raise an exception
        mock_gemini_client.configure_failure(
            should_fail=True,
            fail_count=10,  # Fail all attempts
            failure_type="service_unavailable"
        )
        
        files = {
            'image': ('test.jpg', BytesIO(valid_image_bytes), 'image/jpeg'),
            'audio': ('test.wav', BytesIO(valid_audio_bytes), 'audio/wav')
        }
        data = {
            'text': 'I want to build something creative'
        }
        
        # Make request
        response = client.post('/generate', files=files, data=data)
        
        # Assert response
        assert response.status_code in [500, 502]  # Internal or bad gateway error
        json_data = response.json()
        assert json_data['success'] is False
        assert 'error' in json_data
        
        # Reset mock
        mock_gemini_client.reset()



class TestGenerateStepsEndpoint:
    """Integration tests for /generate-steps endpoint"""
    
    def test_successful_step_generation(self, client):
        """Test successful step generation"""
        data = {
            'idea': 'Build a mobile app for tracking daily water intake'
        }
        
        # Make request
        response = client.post('/generate-steps', json=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
        assert 'steps' in json_data
        assert len(json_data['steps']) > 0
        assert 'request_id' in json_data
    
    def test_validation_error_with_empty_idea(self, client):
        """Test validation errors with empty idea"""
        data = {
            'idea': '   '  # Only whitespace
        }
        
        # Make request
        response = client.post('/generate-steps', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False
    
    def test_validation_error_with_missing_idea(self, client):
        """Test validation errors with missing idea field"""
        data = {}
        
        # Make request
        response = client.post('/generate-steps', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False
    
    def test_validation_error_with_oversized_idea(self, client):
        """Test validation errors with idea exceeding max length"""
        data = {
            'idea': 'x' * 2001  # Exceeds 2000 character limit
        }
        
        # Make request
        response = client.post('/generate-steps', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False



class TestRefineIdeaEndpoint:
    """Integration tests for /refine-idea endpoint"""
    
    def test_successful_refinement_variation(self, client):
        """Test successful idea refinement with variation type"""
        data = {
            'idea': 'Build a mobile app for tracking daily water intake',
            'type': 'variation'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
        assert 'refined_idea' in json_data
        assert len(json_data['refined_idea']) > 0
        assert 'request_id' in json_data
    
    def test_successful_refinement_simpler(self, client):
        """Test successful idea refinement with simpler type"""
        data = {
            'idea': 'Build a complex AI-powered recommendation system',
            'type': 'simpler'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
        assert 'refined_idea' in json_data
        assert len(json_data['refined_idea']) > 0
    
    def test_successful_refinement_more_ambitious(self, client):
        """Test successful idea refinement with more_ambitious type"""
        data = {
            'idea': 'Make a simple todo list app',
            'type': 'more_ambitious'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
        assert 'refined_idea' in json_data
        assert len(json_data['refined_idea']) > 0
    
    def test_default_refinement_type(self, client):
        """Test that default refinement type is 'variation'"""
        data = {
            'idea': 'Build a mobile app for tracking daily water intake'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['success'] is True
    
    def test_validation_error_with_empty_idea(self, client):
        """Test validation errors with empty idea"""
        data = {
            'idea': '   ',  # Only whitespace
            'type': 'variation'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False
    
    def test_validation_error_with_invalid_type(self, client):
        """Test validation errors with invalid refinement type"""
        data = {
            'idea': 'Build a mobile app',
            'type': 'invalid_type'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False
    
    def test_validation_error_with_oversized_idea(self, client):
        """Test validation errors with idea exceeding max length"""
        data = {
            'idea': 'x' * 2001,  # Exceeds 2000 character limit
            'type': 'variation'
        }
        
        # Make request
        response = client.post('/refine-idea', json=data)
        
        # Assert response
        assert response.status_code in [400, 422]  # Validation error
        json_data = response.json()
        assert json_data['success'] is False
