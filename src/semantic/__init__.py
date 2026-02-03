"""
Semantic processing module for Otto.AI
Provides vehicle data processing, embedding generation, and semantic search capabilities
"""

from .vehicle_processing_service import (
    VehicleProcessingService,
    VehicleData,
    VehicleProcessingResult,
    BatchProcessingResult,
    VehicleImageType
)

__all__ = [
    "VehicleProcessingService",
    "VehicleData",
    "VehicleProcessingResult",
    "BatchProcessingResult",
    "VehicleImageType"
]