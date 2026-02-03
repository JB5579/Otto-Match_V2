"""
Otto.AI Vehicle Embedding Service
Integrates PDF processing with the existing RAG-Anything embedding system
to make processed vehicles searchable via semantic search.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..services.pdf_ingestion_service import VehicleListingArtifact, EnrichedImage
from ..semantic.embedding_service import OttoAIEmbeddingService
from ..repositories.listing_repository import (
    ListingRepository, ListingCreate, get_listing_repository
)
from ..repositories.image_repository import (
    ImageRepository, ImageCreate, get_image_repository
)
from ..services.supabase_client import get_supabase_client_singleton

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VehicleEmbeddingService:
    """
    Connects vehicle listing artifacts with the RAG-Anything embedding system.

    This service:
    1. Takes VehicleListingArtifact from PDF processing
    2. Creates rich text descriptions for embedding
    3. Generates embeddings for vehicle data and images
    4. Stores embeddings in Supabase pgvector for semantic search
    """

    def __init__(self, embedding_service: OttoAIEmbeddingService):
        self.embedding_service = embedding_service
        self.listing_repository = get_listing_repository()
        self.image_repository = get_image_repository()
        self.supabase_client = get_supabase_client_singleton()

    async def process_vehicle_for_search(
        self,
        artifact: VehicleListingArtifact
    ) -> Dict[str, Any]:
        """
        Process a vehicle listing artifact and make it searchable.

        Args:
            artifact: Complete vehicle listing artifact from PDF processing

        Returns:
            Dict with embedding metadata and search IDs
        """
        try:
            logger.info(f"Creating embeddings for vehicle: {artifact.vehicle.vin}")

            # Generate rich text description for embedding
            vehicle_text = self._create_searchable_text(artifact)

            # Generate text embedding
            text_embedding_result = await self.embedding_service.generate_text_embedding(
                vehicle_text
            )

            # Generate image embeddings for main vehicle photos
            image_embeddings = []
            main_images = [img for img in artifact.images
                          if img.category in ['hero', 'carousel']]

            for image in main_images[:5]:  # Limit to top 5 images for performance
                try:
                    # Create a temporary file-like object for the image
                    image_embedding = await self.embedding_service.generate_image_embedding(
                        image.image_bytes
                    )
                    image_embeddings.append({
                        'vehicle_angle': image.vehicle_angle,
                        'category': image.category,
                        'embedding': image_embedding.embedding,
                        'description': image.description
                    })
                except Exception as e:
                    logger.warning(f"Failed to create embedding for {image.vehicle_angle}: {e}")

            # Store vehicle listing and images in database
            listing_id = await self._store_vehicle_embeddings(
                artifact,
                vehicle_text,
                text_embedding_result.embedding,
                image_embeddings
            )

            # Store condition issues
            await self._store_condition_issues(artifact, listing_id)

            embedding_metadata = {
                'vin': artifact.vehicle.vin,
                'listing_id': listing_id,
                'text_embedding_id': text_embedding_result.get('embedding_id'),
                'image_embedding_count': len(image_embeddings),
                'processed_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Persisted listing {listing_id} with {len(image_embeddings) + 1} embeddings for {artifact.vehicle.vin}")

            return embedding_metadata

        except Exception as e:
            logger.error(f"❌ Failed to process embeddings for {artifact.vehicle.vin}: {e}")
            raise

    def _create_searchable_text(self, artifact: VehicleListingArtifact) -> str:
        """
        Create rich, searchable text description from vehicle artifact.
        This text will be embedded for semantic search.
        """
        v = artifact.vehicle
        c = artifact.condition

        # Extract key features from images
        image_features = []
        for img in artifact.images:
            if img.category in ['hero', 'carousel']:
                image_features.extend([
                    f"{img.vehicle_angle.replace('_', ' ')} view",
                    img.description.split('.')[0]  # First sentence of description
                ])

        # Build comprehensive searchable text
        searchable_text = f"""
        Vehicle: {v.year} {v.make} {v.model} {v.trim or ''}

        Specifications:
        - VIN: {v.vin}
        - Engine: {v.engine}
        - Transmission: {v.transmission}
        - Drivetrain: {v.drivetrain}
        - Odometer: {v.odometer:,} miles
        - Exterior Color: {v.exterior_color}
        - Interior Color: {v.interior_color}

        Condition:
        - Grade: {c.grade}
        - Score: {c.score}/5.0
        - Overall Assessment: Excellent vehicle condition

        Features: {' | '.join(image_features)}

        This {v.year} {v.make} {v.model} features a {v.engine} engine with {v.transmission} transmission.
        The {v.drivetrain} drivetrain provides excellent handling and performance.
        With {v.odometer:,} miles, this vehicle is in {c.grade.lower()} condition with a condition score of {c.score}.
        The {v.exterior_color} exterior and {v.interior_color} interior create a stylish combination.
        """

        return searchable_text.strip()

    async def _store_vehicle_embeddings(
        self,
        artifact: VehicleListingArtifact,
        description_text: str,
        text_embedding: List[float],
        image_embeddings: List[Dict[str, Any]]
    ) -> str:
        """
        Store vehicle listing and images with embeddings in Supabase.

        Args:
            artifact: Complete vehicle listing artifact from PDF processing
            description_text: Searchable text description
            text_embedding: Text embedding vector (3072 dimensions)
            image_embeddings: List of image embeddings with metadata

        Returns:
            listing_id: UUID of the created listing
        """
        try:
            v = artifact.vehicle
            c = artifact.condition

            logger.info(f"📦 Persisting vehicle listing for VIN {v.vin}:")
            logger.info(f"   - Text embedding: {len(text_embedding)} dimensions")
            logger.info(f"   - Image embeddings: {len(image_embeddings)} images")

            # 1. Create vehicle listing
            listing_data = ListingCreate(
                vin=v.vin,
                year=v.year,
                make=v.make,
                model=v.model,
                trim=v.trim,
                odometer=v.odometer,
                drivetrain=v.drivetrain,
                transmission=v.transmission,
                engine=v.engine,
                exterior_color=v.exterior_color,
                interior_color=v.interior_color,
                condition_score=c.score,
                condition_grade=c.grade,
                description_text=description_text,
                text_embedding=text_embedding,
                status='active',
                listing_source='pdf_upload',
                processing_metadata=artifact.processing_metadata,
                seller_id=None  # Will be linked when seller auth is implemented
            )

            created_listing = await self.listing_repository.create(listing_data)
            listing_id = created_listing['id']

            logger.info(f"   ✅ Created listing {listing_id}")

            # 2. Create vehicle images with embeddings
            # Map artifact images to their embeddings
            embedding_map = {
                (e['vehicle_angle'], e['category']): e.get('embedding')
                for e in image_embeddings
            }

            image_creates = []
            for idx, img in enumerate(artifact.images):
                # Get embedding if available for this image
                img_embedding = embedding_map.get((img.vehicle_angle, img.category))

                image_data = ImageCreate(
                    listing_id=listing_id,
                    vin=v.vin,
                    category=img.category,
                    vehicle_angle=img.vehicle_angle,
                    description=img.description,
                    suggested_alt=img.suggested_alt,
                    quality_score=img.quality_score,
                    visible_damage=img.visible_damage or [],
                    file_format=img.format,
                    width=img.width,
                    height=img.height,
                    original_url=img.storage_url,
                    web_url=img.storage_url,
                    thumbnail_url=img.thumbnail_url,
                    image_embedding=img_embedding,
                    page_number=img.page_number,
                    display_order=idx
                )
                image_creates.append(image_data)

            if image_creates:
                created_images = await self.image_repository.create_batch(image_creates)
                logger.info(f"   ✅ Created {len(created_images)} images")

            return listing_id

        except Exception as e:
            logger.error(f"❌ Failed to store vehicle listing for {artifact.vehicle.vin}: {e}")
            raise

    async def _store_condition_issues(
        self,
        artifact: VehicleListingArtifact,
        listing_id: str
    ) -> int:
        """
        Store vehicle condition issues in the database.

        Args:
            artifact: Complete vehicle listing artifact
            listing_id: UUID of the parent listing

        Returns:
            Number of issues stored
        """
        try:
            issues_stored = 0
            c = artifact.condition

            # Process issues by category
            for category, issues in c.issues.items():
                for issue in issues:
                    issue_data = {
                        'listing_id': listing_id,
                        'vin': artifact.vehicle.vin,
                        'issue_category': category,
                        'issue_type': issue.get('type', 'unknown'),
                        'severity': issue.get('severity', 'minor'),
                        'description': issue.get('description', ''),
                        'location': issue.get('location'),
                        'estimated_repair_cost': issue.get('repair_cost')
                    }

                    result = self.supabase_client.table('vehicle_condition_issues') \
                        .insert(issue_data).execute()

                    if result.data:
                        issues_stored += 1

            if issues_stored > 0:
                logger.info(f"   ✅ Stored {issues_stored} condition issues")

            return issues_stored

        except Exception as e:
            logger.error(f"❌ Failed to store condition issues for {artifact.vehicle.vin}: {e}")
            # Don't raise - condition issues are secondary to main listing
            return 0

    async def search_similar_vehicles(
        self,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for vehicles similar to the given query text using pgvector.

        Args:
            query_text: Natural language query describing desired vehicle
            limit: Maximum number of results to return
            filters: Optional filters (make, model, year_min, year_max, etc.)

        Returns:
            List of similar vehicles with similarity scores
        """
        try:
            # Generate embedding for search query
            query_embedding_result = await self.embedding_service.generate_text_embedding(query_text)

            # Use repository's pgvector similarity search
            similar_listings = await self.listing_repository.find_similar(
                embedding=query_embedding_result.embedding,
                limit=limit
            )

            # Apply additional filters if provided
            if filters and similar_listings:
                filtered = similar_listings
                if filters.get('make'):
                    filtered = [v for v in filtered if filters['make'].lower() in v.get('make', '').lower()]
                if filters.get('model'):
                    filtered = [v for v in filtered if filters['model'].lower() in v.get('model', '').lower()]
                if filters.get('year_min'):
                    filtered = [v for v in filtered if v.get('year', 0) >= filters['year_min']]
                if filters.get('year_max'):
                    filtered = [v for v in filtered if v.get('year', 9999) <= filters['year_max']]
                similar_listings = filtered[:limit]

            logger.info(f"🔍 Found {len(similar_listings)} similar vehicles for query: {query_text[:50]}...")
            return similar_listings

        except Exception as e:
            logger.error(f"Failed to search similar vehicles: {e}")
            return []

    async def update_vehicle_embeddings(
        self,
        vin: str,
        artifact: VehicleListingArtifact
    ) -> bool:
        """
        Update existing embeddings for a vehicle (useful for corrections or updates).
        """
        try:
            logger.info(f"🔄 Updating embeddings for VIN {vin}")

            # Delete existing embeddings
            await self._delete_vehicle_embeddings(vin)

            # Create new embeddings
            await self.process_vehicle_for_search(artifact)

            logger.info(f"✅ Successfully updated embeddings for VIN {vin}")
            return True

        except Exception as e:
            logger.error(f"Failed to update embeddings for {vin}: {e}")
            return False

    async def _delete_vehicle_embeddings(self, vin: str) -> None:
        """
        Delete existing embeddings and listing for a vehicle.
        Uses cascading deletes defined in the database schema.
        """
        try:
            # Get listing by VIN
            existing_listing = await self.listing_repository.get_by_vin(vin)

            if existing_listing:
                listing_id = existing_listing['id']

                # Delete images (will cascade from listing delete, but explicit for clarity)
                await self.image_repository.delete_by_listing(listing_id)

                # Delete condition issues
                self.supabase_client.table('vehicle_condition_issues') \
                    .delete().eq('vin', vin).execute()

                # Delete listing (soft delete changes status to inactive)
                await self.listing_repository.delete(listing_id)

                logger.info(f"🗑️ Deleted existing listing and embeddings for VIN {vin}")
            else:
                logger.info(f"ℹ️ No existing listing found for VIN {vin}")

        except Exception as e:
            logger.error(f"Failed to delete embeddings for {vin}: {e}")


# Integration wrapper for easy use with PDF ingestion service
async def process_listing_for_search(
    artifact: VehicleListingArtifact,
    embedding_service: OttoAIEmbeddingService
) -> Dict[str, Any]:
    """
    Convenience function to process a listing artifact for search.
    This integrates the PDF ingestion pipeline with the semantic search system.
    """
    vehicle_embedding_service = VehicleEmbeddingService(embedding_service)
    return await vehicle_embedding_service.process_vehicle_for_search(artifact)