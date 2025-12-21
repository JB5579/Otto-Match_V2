"""
Otto.AI Services Module

Contains business logic services for:
- PDF ingestion and processing
- Image management and optimization
- Storage and caching
- External API integrations
"""

from .pdf_ingestion_service import PDFIngestionService, VehicleListingArtifact, EnrichedImage

__all__ = [
    'PDFIngestionService',
    'VehicleListingArtifact',
    'EnrichedImage'
]