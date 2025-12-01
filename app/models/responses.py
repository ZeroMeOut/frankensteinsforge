"""Pydantic response models for API endpoints"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class GenerateResponse(BaseModel):
    """Response model for idea generation"""
    success: bool = Field(
        ...,
        description="Whether the request was successful"
    )
    idea: str = Field(
        ...,
        description="The generated creative idea"
    )
    inputs: Dict[str, str] = Field(
        ...,
        description="Echo of the input data provided"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this request"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "idea": "Create an AI-powered music composition tool that generates melodies based on visual art and spoken emotions",
                    "inputs": {
                        "text": "I want to build something creative",
                        "image_filename": "artwork.jpg",
                        "audio_filename": "voice.wav"
                    },
                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    }


class StepsResponse(BaseModel):
    """Response model for step generation"""
    success: bool = Field(
        ...,
        description="Whether the request was successful"
    )
    steps: str = Field(
        ...,
        description="The generated implementation steps"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this request"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "steps": "1. Design the user interface\n2. Set up the backend API\n3. Implement core features\n4. Test and deploy",
                    "request_id": "550e8400-e29b-41d4-a716-446655440001"
                }
            ]
        }
    }


class RefineResponse(BaseModel):
    """Response model for idea refinement"""
    success: bool = Field(
        ...,
        description="Whether the request was successful"
    )
    refined_idea: str = Field(
        ...,
        description="The refined or varied idea"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this request"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "refined_idea": "Build a gamified water tracking app with social challenges and achievement badges",
                    "request_id": "550e8400-e29b-41d4-a716-446655440002"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = Field(
        default=False,
        description="Always false for error responses"
    )
    error: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this request"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": "Invalid file type",
                    "details": {
                        "field": "image",
                        "reason": "File signature does not match declared MIME type"
                    },
                    "request_id": "550e8400-e29b-41d4-a716-446655440003"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(
        ...,
        description="Health status: 'healthy' or 'unhealthy'"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    dependencies: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Status of external dependencies"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp of the health check"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "dependencies": {
                        "gemini_api": "accessible"
                    },
                    "timestamp": "2024-01-15T10:30:00.000Z"
                }
            ]
        }
    }


class StatsResponse(BaseModel):
    """Response model for statistics endpoint"""
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    stats: Dict[str, Any] = Field(
        ...,
        description="API statistics and information"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "stats": {
                        "version": "1.0.0",
                        "model": "gemini-2.0-flash-exp",
                        "features": [
                            "multimodal_generation",
                            "step_generation",
                            "idea_refinement"
                        ]
                    }
                }
            ]
        }
    }


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint"""
    total_requests: int = Field(
        ...,
        description="Total number of requests processed"
    )
    total_errors: int = Field(
        ...,
        description="Total number of errors encountered"
    )
    error_rate: float = Field(
        ...,
        description="Error rate as a percentage"
    )
    latency_percentiles: Dict[str, float] = Field(
        ...,
        description="Latency percentiles (p50, p90, p95, p99, mean, min, max) in milliseconds"
    )
    endpoints: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Per-endpoint metrics including request counts, error rates, and latency"
    )
    timestamp: str = Field(
        ...,
        description="Timestamp when metrics were collected"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_requests": 150,
                    "total_errors": 5,
                    "error_rate": 3.33,
                    "latency_percentiles": {
                        "p50": 120.5,
                        "p90": 250.0,
                        "p95": 300.0,
                        "p99": 450.0,
                        "mean": 145.2,
                        "min": 50.0,
                        "max": 500.0
                    },
                    "endpoints": {
                        "POST /generate": {
                            "request_count": 100,
                            "error_count": 3,
                            "error_rate": 3.0,
                            "latency": {
                                "p50": 150.0,
                                "p90": 280.0,
                                "p95": 320.0,
                                "p99": 480.0,
                                "mean": 165.5
                            }
                        }
                    },
                    "timestamp": "2024-01-15T10:30:00.000Z"
                }
            ]
        }
    }
