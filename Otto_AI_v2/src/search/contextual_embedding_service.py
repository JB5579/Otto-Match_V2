"""
Otto.AI Contextual Embedding Service

Generates category-aware embeddings by prepending vehicle type context
to improve semantic matching across vehicle categories.

Story: 1-12 Add Contextual Embeddings
"""

import os
import logging
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContextualEmbeddingConfig(BaseModel):
    """Configuration for contextual embeddings"""
    enable_context: bool = Field(True, description="Enable category context prefixes")
    enable_for_queries: bool = Field(False, description="Add context to query embeddings")


class ContextualEmbeddingService:
    """
    Generate embeddings with category context for improved semantic matching.

    Prepends vehicle category information to text before embedding:
    - Before: "2020 Ford F-250 Super Duty Lariat 4WD"
    - After: "AUTOMOTIVE VEHICLE - TRUCK: 2020 Ford F-250 Super Duty Lariat 4WD"

    This helps the embedding model understand vehicle purpose and category,
    improving matches like "family vehicle" -> SUVs, not sports cars.
    """

    # Context templates by vehicle type
    CATEGORY_TEMPLATES = {
        # Trucks
        "Truck": "AUTOMOTIVE VEHICLE - TRUCK/PICKUP",
        "Pickup": "AUTOMOTIVE VEHICLE - TRUCK/PICKUP",

        # SUVs and Crossovers
        "SUV": "AUTOMOTIVE VEHICLE - SUV/CROSSOVER",
        "Crossover": "AUTOMOTIVE VEHICLE - SUV/CROSSOVER",

        # Sedans and Cars
        "Sedan": "AUTOMOTIVE VEHICLE - SEDAN/CAR",
        "Car": "AUTOMOTIVE VEHICLE - SEDAN/CAR",

        # Sports and Performance
        "Coupe": "AUTOMOTIVE VEHICLE - SPORTS/COUPE",
        "Sports Car": "AUTOMOTIVE VEHICLE - SPORTS/PERFORMANCE",
        "Convertible": "AUTOMOTIVE VEHICLE - SPORTS/CONVERTIBLE",

        # Family and Utility
        "Minivan": "AUTOMOTIVE VEHICLE - FAMILY/MINIVAN",
        "Van": "AUTOMOTIVE VEHICLE - UTILITY/VAN",

        # Compact
        "Hatchback": "AUTOMOTIVE VEHICLE - COMPACT/HATCHBACK",
        "Compact": "AUTOMOTIVE VEHICLE - COMPACT/ECONOMY",

        # Wagon and Estate
        "Wagon": "AUTOMOTIVE VEHICLE - WAGON/ESTATE",
        "Station Wagon": "AUTOMOTIVE VEHICLE - WAGON/ESTATE",

        # Luxury
        "Luxury": "AUTOMOTIVE VEHICLE - LUXURY/PREMIUM",
    }

    DEFAULT_TEMPLATE = "AUTOMOTIVE VEHICLE"

    def __init__(
        self,
        embedding_service=None,
        config: Optional[ContextualEmbeddingConfig] = None
    ):
        """
        Initialize the contextual embedding service.

        Args:
            embedding_service: The base embedding service to use
            config: Optional configuration
        """
        self.embedding_service = embedding_service
        self.config = config or ContextualEmbeddingConfig()

        # Statistics
        self.stats = {
            "embeddings_generated": 0,
            "context_added": 0,
            "no_context": 0
        }

    def set_embedding_service(self, embedding_service):
        """Set the base embedding service"""
        self.embedding_service = embedding_service

    async def generate_vehicle_embedding(
        self,
        vehicle_text: str,
        vehicle_type: Optional[str] = None
    ) -> List[float]:
        """
        Generate contextual embedding for a vehicle.

        Args:
            vehicle_text: Text representation of the vehicle
            vehicle_type: Vehicle type for category context

        Returns:
            Embedding vector with category context
        """
        if self.embedding_service is None:
            raise ValueError("Embedding service not initialized")

        self.stats["embeddings_generated"] += 1

        # Add context if enabled and vehicle type is known
        if self.config.enable_context and vehicle_type:
            context = self.CATEGORY_TEMPLATES.get(
                vehicle_type,
                self.DEFAULT_TEMPLATE
            )
            contextual_text = f"{context}: {vehicle_text}"
            self.stats["context_added"] += 1
        else:
            contextual_text = vehicle_text
            self.stats["no_context"] += 1

        # Generate embedding using base service
        from src.semantic.embedding_service import EmbeddingRequest
        request = EmbeddingRequest(text=contextual_text)
        response = await self.embedding_service.generate_embedding(request)

        return response.embedding

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        By default, queries do NOT get category context so they can
        match across categories. This can be configured.

        Args:
            query: User search query

        Returns:
            Embedding vector
        """
        if self.embedding_service is None:
            raise ValueError("Embedding service not initialized")

        text = query
        if self.config.enable_for_queries:
            # Optionally add generic context for queries
            text = f"VEHICLE SEARCH: {query}"

        from src.semantic.embedding_service import EmbeddingRequest
        request = EmbeddingRequest(text=text)
        response = await self.embedding_service.generate_embedding(request)

        return response.embedding

    def create_vehicle_text(self, vehicle: Dict[str, Any]) -> str:
        """
        Create searchable text from vehicle data.

        Args:
            vehicle: Vehicle data dictionary

        Returns:
            Combined text for embedding
        """
        parts = [
            str(vehicle.get('year', '')),
            vehicle.get('make', ''),
            vehicle.get('model', ''),
            vehicle.get('trim', ''),
        ]

        # Add fuel type if notable (electric/hybrid)
        fuel_type = vehicle.get('fuel_type', '')
        if fuel_type and fuel_type.lower() in ['electric', 'hybrid', 'plug-in hybrid']:
            parts.append(fuel_type)

        # Add transmission if notable
        transmission = vehicle.get('transmission', '')
        if transmission:
            parts.append(transmission)

        # Add description (truncated)
        description = vehicle.get('description_text', '') or vehicle.get('description', '')
        if description:
            parts.append(description[:500])

        return " ".join(filter(None, parts))

    def get_context_template(self, vehicle_type: str) -> str:
        """
        Get the context template for a vehicle type.

        Args:
            vehicle_type: The vehicle type

        Returns:
            Context template string
        """
        return self.CATEGORY_TEMPLATES.get(vehicle_type, self.DEFAULT_TEMPLATE)

    def get_all_templates(self) -> Dict[str, str]:
        """Get all category templates"""
        return dict(self.CATEGORY_TEMPLATES)

    def add_template(self, vehicle_type: str, template: str):
        """
        Add or update a category template.

        Args:
            vehicle_type: The vehicle type key
            template: The context template
        """
        self.CATEGORY_TEMPLATES[vehicle_type] = template
        logger.info(f"Added template: {vehicle_type} -> {template}")

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "config": self.config.dict(),
            "template_count": len(self.CATEGORY_TEMPLATES)
        }
