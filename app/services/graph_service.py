"""
Graph-based idea generation service with multi-modal fusion.

This module implements weighted graph processing where node influence
is calculated based on connection weights and graph structure.
"""
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from google.genai import types
from app.core.config import Config
from app.core.logging import StructuredLogger
from app.core.exceptions import ValidationError, ExternalAPIError
from app.core.gemini_client import GeminiClientProtocol


class GraphProcessor:
    """Processes node graphs with weighted connections for idea generation"""
    
    def __init__(
        self,
        client: GeminiClientProtocol,
        config: Config,
        logger: StructuredLogger
    ):
        """Initialize GraphProcessor with dependencies.
        
        Args:
            client: Gemini API client implementation
            config: Application configuration
            logger: Structured logger instance
        """
        self.client = client
        self.config = config
        self.logger = logger
    
    def calculate_node_influence(
        self,
        node_id: str,
        connections: List[Dict],
        all_node_ids: set
    ) -> float:
        """Calculate influence score for a node based on its connections.
        
        Influence is calculated as:
        - Sum of weights of all connections involving this node
        - Normalized by the number of nodes
        
        Args:
            node_id: ID of the node to calculate influence for
            connections: List of connection dictionaries
            all_node_ids: Set of all node IDs in the graph
            
        Returns:
            Influence score (0.0 to 1.0+)
        """
        total_weight = 0.0
        connection_count = 0
        
        for conn in connections:
            if conn['source'] == node_id or conn['target'] == node_id:
                total_weight += conn['weight']
                connection_count += 1
        
        # Normalize by potential connections
        if connection_count > 0:
            # Average weight * connection density
            avg_weight = total_weight / connection_count
            connection_density = connection_count / (len(all_node_ids) - 1) if len(all_node_ids) > 1 else 1.0
            return avg_weight * (0.5 + 0.5 * connection_density)
        
        return 0.1  # Minimum influence for isolated nodes
    
    def build_weighted_prompt(
        self,
        nodes: List[Dict],
        influence_scores: Dict[str, float],
        connections: List[Dict]
    ) -> str:
        """Build a sophisticated prompt that reflects graph structure and weights.
        
        Args:
            nodes: List of node dictionaries
            influence_scores: Dictionary mapping node IDs to influence scores
            connections: List of connection dictionaries
            
        Returns:
            Formatted prompt string
        """
        # Sort nodes by influence (highest first)
        sorted_nodes = sorted(
            nodes,
            key=lambda n: influence_scores.get(n['id'], 0),
            reverse=True
        )
        
        prompt_parts = []
        
        # Header
        prompt_parts.append("Create an innovative, achievable idea by synthesizing these multimodal inputs.")
        prompt_parts.append("Each input has been assigned an influence level based on its connections in the graph:\n")
        
        # Primary influences (top 70%)
        primary_threshold = 0.7
        primary_nodes = [n for n in sorted_nodes if influence_scores.get(n['id'], 0) >= primary_threshold]
        
        if primary_nodes:
            prompt_parts.append("PRIMARY INFLUENCES (highest priority):")
            for node in primary_nodes:
                score = influence_scores.get(node['id'], 0)
                if node['type'] == 'text':
                    prompt_parts.append(f"  [{score:.1%}] Text Input: {node.get('content', '')[:200]}")
                else:
                    prompt_parts.append(f"  [{score:.1%}] {node['type'].title()} Input: Visual/audio reference")
            prompt_parts.append("")
        
        # Secondary influences (40-70%)
        secondary_nodes = [
            n for n in sorted_nodes 
            if 0.4 <= influence_scores.get(n['id'], 0) < primary_threshold
        ]
        
        if secondary_nodes:
            prompt_parts.append("SECONDARY INFLUENCES (supporting elements):")
            for node in secondary_nodes:
                score = influence_scores.get(node['id'], 0)
                if node['type'] == 'text':
                    prompt_parts.append(f"  [{score:.1%}] {node.get('content', '')[:100]}")
                else:
                    prompt_parts.append(f"  [{score:.1%}] {node['type'].title()} reference")
            prompt_parts.append("")
        
        # Tertiary influences (below 40%)
        tertiary_nodes = [
            n for n in sorted_nodes 
            if influence_scores.get(n['id'], 0) < 0.4
        ]
        
        if tertiary_nodes:
            prompt_parts.append("SUBTLE INFLUENCES (background inspiration):")
            for node in tertiary_nodes:
                score = influence_scores.get(node['id'], 0)
                if node['type'] == 'text':
                    prompt_parts.append(f"  [{score:.1%}] {node.get('content', '')[:80]}")
                else:
                    prompt_parts.append(f"  [{score:.1%}] {node['type'].title()} element")
            prompt_parts.append("")
        
        # Relationship context
        prompt_parts.append("RELATIONSHIPS:")
        # Sort connections by weight
        sorted_connections = sorted(connections, key=lambda c: c['weight'], reverse=True)
        for conn in sorted_connections[:5]:  # Top 5 connections
            source_node = next((n for n in nodes if n['id'] == conn['source']), None)
            target_node = next((n for n in nodes if n['id'] == conn['target']), None)
            if source_node and target_node:
                prompt_parts.append(
                    f"  • {source_node['type'].title()} ←→ {target_node['type'].title()} "
                    f"(strength: {conn['weight']:.1f})"
                )
        
        prompt_parts.append("\nSYNTHESIS INSTRUCTION:")
        prompt_parts.append(
            "Generate a creative, actionable idea that primarily reflects the PRIMARY influences, "
            "incorporates SECONDARY influences as supporting elements, and uses SUBTLE influences "
            "for inspiration. Start your idea with 'Create' or 'Build' or 'Make' followed by a concrete concept."
        )
        
        return "\n".join(prompt_parts)
    
    def generate_from_graph(
        self,
        nodes: List[Dict],
        connections: List[Dict],
        image_files: Dict[str, bytes],
        audio_files: Dict[str, bytes]
    ) -> str:
        """Generate idea from complete graph with multi-modal fusion.
        
        Args:
            nodes: List of node data dictionaries
            connections: List of connection dictionaries
            image_files: Dictionary mapping node IDs to image bytes
            audio_files: Dictionary mapping node IDs to audio bytes
            
        Returns:
            Generated idea text
            
        Raises:
            ValidationError: If graph structure is invalid
            ExternalAPIError: If API call fails
        """
        self.logger.info(
            "Processing graph for idea generation",
            node_count=len(nodes),
            connection_count=len(connections)
        )
        
        # Validate inputs
        if not nodes:
            raise ValidationError(
                "Graph must contain at least one node",
                details={"reason": "empty_graph"}
            )
        
        if not connections:
            raise ValidationError(
                "Graph must contain at least one connection",
                details={"reason": "no_connections"}
            )
        
        # Calculate influence scores for all nodes
        all_node_ids = {node['id'] for node in nodes}
        influence_scores = {}
        
        for node in nodes:
            influence_scores[node['id']] = self.calculate_node_influence(
                node['id'],
                connections,
                all_node_ids
            )
        
        self.logger.info(
            "Calculated node influences",
            influence_scores={k: f"{v:.2f}" for k, v in influence_scores.items()}
        )
        
        # Build weighted prompt
        prompt = self.build_weighted_prompt(nodes, influence_scores, connections)
        
        # Prepare content parts for API
        content_parts = [prompt]
        
        # Add images (sorted by influence)
        image_nodes = [n for n in nodes if n['type'] == 'image']
        image_nodes.sort(key=lambda n: influence_scores.get(n['id'], 0), reverse=True)
        
        for node in image_nodes:
            if node['id'] in image_files:
                content_parts.append(
                    types.Part.from_bytes(
                        data=image_files[node['id']],
                        mime_type='image/jpeg'
                    )
                )
                self.logger.debug(
                    "Added image to generation",
                    node_id=node['id'],
                    influence=influence_scores.get(node['id'], 0)
                )
        
        # Add audio (sorted by influence)
        audio_nodes = [n for n in nodes if n['type'] == 'audio']
        audio_nodes.sort(key=lambda n: influence_scores.get(n['id'], 0), reverse=True)
        
        for node in audio_nodes:
            if node['id'] in audio_files:
                content_parts.append(
                    types.Part.from_bytes(
                        data=audio_files[node['id']],
                        mime_type='audio/wav'
                    )
                )
                self.logger.debug(
                    "Added audio to generation",
                    node_id=node['id'],
                    influence=influence_scores.get(node['id'], 0)
                )
        
        try:
            # Call API with all content
            response = self.client.generate_content(
                model=self.config.ai_model,
                contents=content_parts
            )
            
            # Validate response
            if not response or not response.strip():
                raise ValidationError(
                    "AI service returned empty response",
                    details={"reason": "empty_response"}
                )
            
            self.logger.info(
                "Successfully generated idea from graph",
                response_length=len(response),
                nodes_processed=len(nodes),
                images_used=len(image_nodes),
                audio_used=len(audio_nodes)
            )
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(
                "Failed to generate idea from graph",
                exc_info=e,
                error_type=type(e).__name__
            )
            
            if isinstance(e, (ValidationError, ExternalAPIError)):
                raise
            
            raise ExternalAPIError(
                "Failed to generate idea from graph",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ) from e
