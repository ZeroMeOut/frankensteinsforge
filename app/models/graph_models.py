"""Pydantic request models for graph-based API endpoints"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from enum import Enum


class NodeType(str, Enum):
    """Node type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class GraphNodeData(BaseModel):
    """Data for a single node in the graph"""
    id: str = Field(
        ...,
        description="Unique identifier for the node"
    )
    type: NodeType = Field(
        ...,
        description="Type of node (text, image, or audio)"
    )
    content: Optional[str] = Field(
        None,
        description="Text content (for text nodes)"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str], info) -> Optional[str]:
        """Validate content based on node type"""
        node_type = info.data.get('type')
        
        if node_type == NodeType.TEXT:
            if not v or not v.strip():
                raise ValueError("Text nodes must have content")
            return v.strip()
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "node-123",
                    "type": "text",
                    "content": "I want to build a mobile app"
                },
                {
                    "id": "node-456",
                    "type": "image",
                    "content": None
                }
            ]
        }
    }


class GraphConnection(BaseModel):
    """Connection between two nodes with weight"""
    source: str = Field(
        ...,
        description="Source node ID"
    )
    target: str = Field(
        ...,
        description="Target node ID"
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Connection weight (0.0 to 1.0)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "node-123",
                    "target": "node-456",
                    "weight": 0.7
                }
            ]
        }
    }


class GraphMetadata(BaseModel):
    """Metadata about the graph structure"""
    node_data: List[GraphNodeData] = Field(
        ...,
        description="List of nodes with their data"
    )
    connections: List[GraphConnection] = Field(
        ...,
        description="List of connections between nodes"
    )
    
    @field_validator('node_data')
    @classmethod
    def validate_nodes(cls, v: List[GraphNodeData]) -> List[GraphNodeData]:
        """Ensure at least one node"""
        if not v or len(v) == 0:
            raise ValueError("Graph must contain at least one node")
        if len(v) > 10:
            raise ValueError("Graph cannot contain more than 10 nodes")
        return v
    
    @field_validator('connections')
    @classmethod
    def validate_connections(cls, v: List[GraphConnection]) -> List[GraphConnection]:
        """Ensure at least one connection"""
        if not v or len(v) == 0:
            raise ValueError("Graph must contain at least one connection")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "node_data": [
                        {"id": "n1", "type": "text", "content": "Build an app"},
                        {"id": "n2", "type": "image", "content": None}
                    ],
                    "connections": [
                        {"source": "n1", "target": "n2", "weight": 0.7}
                    ]
                }
            ]
        }
    }
