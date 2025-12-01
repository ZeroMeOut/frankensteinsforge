"""Property-based tests for health check endpoint"""
import pytest
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient
from app.core.config import Config
from app.core.logging import setup_logging
from app.core.gemini_client import MockGeminiClient
from app.core.dependencies import initialize_dependencies, reset_dependencies
import sys
import importlib.util
import os


class TestHealthCheckProperties:
    """Property-based tests for health check endpoint"""
    
    def setup_method(self):
        """Setup test dependencies before each test"""
        reset_dependencies()
    
    def teardown_method(self):
        """Cleanup after each test"""
        reset_dependencies()
    
    def _get_app(self):
        """Load the FastAPI app from app.py"""
        # Get the path to app.py
        app_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
        
        # Load the module from the file
        spec = importlib.util.spec_from_file_location("app_module", app_py_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        return app_module.app
    
    @given(
        failure_type=st.sampled_from([
            "rate_limit",
            "timeout", 
            "service_unavailable",
            "generic"
        ])
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_31_unhealthy_dependency_response(self, failure_type):
        """
        **Feature: api-improvements, Property 31: Unhealthy dependency response**
        **Validates: Requirements 10.2**
        
        Property: For any dependency that is unhealthy during a health check, 
        the response should have status 503 and include specific details about 
        which dependency failed.
        """
        # Create a mock client that will fail
        mock_client = MockGeminiClient()
        mock_client.configure_failure(
            should_fail=True,
            fail_count=10,  # Fail all attempts
            failure_type=failure_type
        )
        
        # Initialize dependencies with failing mock client
        config = Config.from_env()
        logger = setup_logging(level=config.log_level)
        initialize_dependencies(
            config=config,
            gemini_client=mock_client,
            logger=logger
        )
        
        # Get the app and create test client
        app = self._get_app()
        client = TestClient(app)
        
        # Call health endpoint
        response = client.get("/health")
        
        # Property 1: Response should have status code 503 for unhealthy dependencies
        assert response.status_code == 503, (
            f"Expected status code 503 for unhealthy dependency, got {response.status_code}"
        )
        
        # Property 2: Response should be valid JSON
        data = response.json()
        assert isinstance(data, dict), "Response should be a JSON object"
        
        # Property 3: Response should have 'status' field set to 'unhealthy'
        assert "status" in data, "Response should include 'status' field"
        assert data["status"] == "unhealthy", (
            f"Expected status 'unhealthy', got '{data['status']}'"
        )
        
        # Property 4: Response should include 'dependencies' field with details
        assert "dependencies" in data, "Response should include 'dependencies' field"
        assert isinstance(data["dependencies"], dict), (
            "Dependencies should be a dictionary"
        )
        
        # Property 5: Dependencies should include gemini_api status
        assert "gemini_api" in data["dependencies"], (
            "Dependencies should include 'gemini_api' status"
        )
        
        gemini_status = data["dependencies"]["gemini_api"]
        assert isinstance(gemini_status, dict), (
            "Gemini API status should be a dictionary"
        )
        
        # Property 6: Gemini API status should indicate failure
        assert "status" in gemini_status, (
            "Gemini API status should include 'status' field"
        )
        assert gemini_status["status"] in ["error", "timeout"], (
            f"Gemini API status should be 'error' or 'timeout', got '{gemini_status['status']}'"
        )
        
        # Property 7: Gemini API status should include a message explaining the failure
        assert "message" in gemini_status, (
            "Gemini API status should include 'message' field with failure details"
        )
        assert isinstance(gemini_status["message"], str), (
            "Gemini API message should be a string"
        )
        assert len(gemini_status["message"]) > 0, (
            "Gemini API message should not be empty"
        )
        
        # Property 8: Response should include version
        assert "version" in data, "Response should include 'version' field"
        assert isinstance(data["version"], str), "Version should be a string"
        
        # Property 9: Response should include timestamp
        assert "timestamp" in data, "Response should include 'timestamp' field"
        assert isinstance(data["timestamp"], str), "Timestamp should be a string"
    
    def test_healthy_dependency_response(self):
        """
        Test that healthy dependencies return 200 status.
        This is a unit test to complement the property test.
        """
        # Create a mock client that will succeed
        mock_client = MockGeminiClient()
        mock_client.configure_failure(should_fail=False)
        
        # Initialize dependencies with working mock client
        config = Config.from_env()
        logger = setup_logging(level=config.log_level)
        initialize_dependencies(
            config=config,
            gemini_client=mock_client,
            logger=logger
        )
        
        # Get the app and create test client
        app = self._get_app()
        client = TestClient(app)
        
        # Call health endpoint
        response = client.get("/health")
        
        # Should return 200 for healthy dependencies
        assert response.status_code == 200, (
            f"Expected status code 200 for healthy dependencies, got {response.status_code}"
        )
        
        data = response.json()
        
        # Should have status 'healthy'
        assert data["status"] == "healthy", (
            f"Expected status 'healthy', got '{data['status']}'"
        )
        
        # Should include dependencies with accessible status
        assert "dependencies" in data
        assert "gemini_api" in data["dependencies"]
        assert data["dependencies"]["gemini_api"]["status"] == "accessible"
