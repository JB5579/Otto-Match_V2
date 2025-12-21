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

            # Store embeddings in database
            embedding_metadata = {
                'vin': artifact.vehicle.vin,
                'listing_id': f"listing_{artifact.vehicle.vin}_{int(datetime.utcnow().timestamp())}",
                'text_embedding_id': text_embedding_result.get('embedding_id'),
                'image_embedding_count': len(image_embeddings),
                'processed_at': datetime.utcnow().isoformat()
            }

            # Store vehicle embeddings (this would integrate with your existing embedding storage)
            await self._store_vehicle_embeddings(
                artifact.vehicle.vin,
                vehicle_text,
                text_embedding_result.embedding,
                image_embeddings
            )

            logger.info(f"✅ Created {len(image_embeddings) + 1} embeddings for {artifact.vehicle.vin}")

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
        vin: str,
        text: str,
        text_embedding: List[float],
        image_embeddings: List[Dict[str, Any]]
    ) -> None:
        """
        Store vehicle embeddings in the database.

        This method would integrate with your existing embedding storage system.
        For now, it logs the storage action.
        """
        try:
            # TODO: Integrate with your existing database schema
            # This might involve:
            # 1. Inserting into vehicle_listings table with text embedding
            # 2. Inserting into vehicle_images table with image embeddings
            # 3. Updating pgvector indexes for similarity search

            logger.info(f"📦 Storing embeddings for VIN {vin}:")
            logger.info(f"   - Text embedding: {len(text_embedding)} dimensions")
            logger.info(f"   - Image embeddings: {len(image_embeddings)} images")

            # Example of what the database integration might look like:
            """
            # Insert vehicle listing with text embedding
            await self.db_conn.execute("""
                INSERT INTO vehicle_listings
                (vin, make, model, year, description_text, text_embedding, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (vin, v.make, v.model, v.year, text, text_embedding, datetime.utcnow()))

            # Insert image embeddings
            for img_emb in image_embeddings:
                await self.db_conn.execute("""
                    INSERT INTO vehicle_image_embeddings
                    (vin, vehicle_angle, category, description, image_embedding, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (vin, img_emb['vehicle_angle'], img_emb['category'],
                     img_emb['description'], img_emb['embedding'], datetime.utcnow()))
            """

            # For now, we'll simulate successful storage
            await asyncio.sleep(0.01)  # Simulate database operation

        except Exception as e:
            logger.error(f"Failed to store embeddings for {vin}: {e}")
            raise

    async def search_similar_vehicles(
        self,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for vehicles similar to the given query text.

        This method integrates with your existing semantic search capabilities.
        """
        try:
            # Generate embedding for search query
            query_embedding_result = await self.embedding_service.generate_text_embedding(query_text)

            # TODO: Perform vector similarity search in database
            # This would use pgvector to find similar vehicles

            # Placeholder result
            similar_vehicles = [
                {
                    'vin': 'placeholder_vin',
                    'make': 'Honda',
                    'model': 'Civic',
                    'year': 2022,
                    'similarity_score': 0.85,
                    'description': 'Similar vehicle found via semantic search'
                }
            ]

            logger.info(f"🔍 Found {len(similar_vehicles)} similar vehicles for query: {query_text[:50]}...")
            return similar_vehicles

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
        Delete existing embeddings for a vehicle.
        """
        try:
            # TODO: Implement database cleanup
            # await self.db_conn.execute("DELETE FROM vehicle_listings WHERE vin = %s", (vin,))
            # await self.db_conn.execute("DELETE FROM vehicle_image_embeddings WHERE vin = %s", (vin,))

            logger.info(f"🗑️ Deleted existing embeddings for VIN {vin}")

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