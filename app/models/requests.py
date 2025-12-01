"""Pydantic request models for API endpoints"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class GenerateRequest(BaseModel):
    """Request model for idea generation from text input
    
    Note: Image and audio files are handled separately as multipart form data
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User text input describing what they want to create"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Text input cannot be empty or only whitespace")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I want to build something creative with AI"
                }
            ]
        }
    }


class StepsRequest(BaseModel):
    """Request model for step generation"""
    idea: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The idea for which to generate implementation steps"
    )
    
    @field_validator('idea')
    @classmethod
    def validate_idea_not_empty(cls, v: str) -> str:
        """Ensure idea is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Idea cannot be empty or only whitespace")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "idea": "Build a mobile app that helps users track their daily water intake"
                }
            ]
        }
    }


class RefineRequest(BaseModel):
    """Request model for idea refinement"""
    idea: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The idea to refine or create variations of"
    )
    type: Literal["variation", "simpler", "more_ambitious"] = Field(
        default="variation",
        description="Type of refinement: variation (different approach), simpler (reduce scope), or more_ambitious (expand scope)"
    )
    
    @field_validator('idea')
    @classmethod
    def validate_idea_not_empty(cls, v: str) -> str:
        """Ensure idea is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Idea cannot be empty or only whitespace")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "idea": "Build a mobile app that helps users track their daily water intake",
                    "type": "variation"
                },
                {
                    "idea": "Create a complex AI-powered recommendation system",
                    "type": "simpler"
                },
                {
                    "idea": "Make a simple todo list app",
                    "type": "more_ambitious"
                }
            ]
        }
    }
