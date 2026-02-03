"""
Otto.AI Listing Persistence Service
Bridges PDF ingestion to database storage.

This service takes VehicleListingArtifact from the PDF ingestion pipeline
and persists it to the vehicle_listings, vehicle_images, and vehicle_condition_issues tables.

This completes the end-to-end flow:
PDF → VehicleListingArtifact → Database → Search → Grid Display
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from ..services.pdf_ingestion_service import VehicleListingArtifact
from ..repositories.listing_repository import (
    ListingRepository,
    ListingCreate
)
from ..repositories.image_repository import (
    ImageRepository,
    ImageCreate
)
from ..services.storage_service import get_storage_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ListingPersistenceService:
    """
    Service for persisting vehicle listings from PDF processing to the database.

    This is the critical missing piece that completes the PDF → Database pipeline.
    """

    def __init__(self):
        self.listing_repo = ListingRepository()
        self.image_repo = ImageRepository()
        self.storage_service = None  # Lazy loaded

    async def _get_storage_service(self):
        """Lazy load storage service"""
        if self.storage_service is None:
            self.storage_service = await get_storage_service()
        return self.storage_service

    async def persist_listing(
        self,
        artifact: VehicleListingArtifact,
        text_embedding: Optional[List[float]] = None,
        seller_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Persist a complete vehicle listing from PDF processing to the database.

        This method:
        1. Creates the vehicle_listings record
        2. Uploads images to Supabase Storage
        3. Creates vehicle_images records
        4. Creates vehicle_condition_issues records

        Args:
            artifact: VehicleListingArtifact from PDF ingestion
            text_embedding: Optional text embedding for semantic search
            seller_id: Optional seller/user ID who owns this listing

        Returns:
            Dict with listing_id, vin, image_count, and issue_count
        """
        try:
            logger.info(f"Persisting listing for VIN: {artifact.vehicle.vin}")

            # Step 1: Create the vehicle listing record
            listing_create = ListingCreate(
                vin=artifact.vehicle.vin,
                year=artifact.vehicle.year,
                make=artifact.vehicle.make,
                model=artifact.vehicle.model,
                trim=artifact.vehicle.trim,
                odometer=artifact.vehicle.odometer,
                drivetrain=artifact.vehicle.drivetrain,
                transmission=artifact.vehicle.transmission,
                engine=artifact.vehicle.engine,
                exterior_color=artifact.vehicle.exterior_color,
                interior_color=artifact.vehicle.interior_color,
                condition_score=artifact.condition.score,
                condition_grade=artifact.condition.grade,
                description_text=self._generate_description(artifact),
                text_embedding=text_embedding,
                status='active',
                listing_source='pdf_upload',
                processing_metadata={
                    'pdf_filename': artifact.processing_metadata.get('filename'),
                    'processing_time': artifact.processing_metadata.get('processing_time'),
                    'gemini_images_found': artifact.processing_metadata.get('gemini_images_found', 0),
                    'pymupdf_images_extracted': artifact.processing_metadata.get('pymupdf_images_extracted', 0),
                    'final_merged_images': artifact.processing_metadata.get('final_merged_images', 0)
                },
                seller_id=seller_id
            )

            # Use upsert to handle existing VINs gracefully
            listing = await self.listing_repo.upsert(listing_create, update_metadata=True)
            listing_id = listing['id']

            # Determine if this was a create or update
            action = "Updated" if listing.get('updated_at') and listing['updated_at'] > listing['created_at'] else "Created"
            logger.info(f"✅ {action} listing {listing_id} for VIN: {artifact.vehicle.vin}")

            # Step 2: Upload images and create image records
            image_count = await self._persist_images(
                listing_id=listing_id,
                vin=artifact.vehicle.vin,
                images=artifact.images
            )

            # Step 3: Create condition issue records
            issue_count = await self._persist_condition_issues(
                listing_id=listing_id,
                vin=artifact.vehicle.vin,
                condition=artifact.condition
            )

            # Step 4: Update listing with summary metadata
            # This could trigger search indexing in the future
            logger.info(f"✅ Successfully persisted listing {listing_id}")

            return {
                'listing_id': listing_id,
                'vin': artifact.vehicle.vin,
                'image_count': image_count,
                'issue_count': issue_count,
                'status': 'active'
            }

        except Exception as e:
            logger.error(f"❌ Failed to persist listing for VIN {artifact.vehicle.vin}: {e}")
            raise

    async def _persist_images(
        self,
        listing_id: str,
        vin: str,
        images: List[Any]
    ) -> int:
        """Upload images to storage and create database records"""
        if not images:
            logger.warning(f"No images to persist for listing {listing_id}")
            return 0

        try:
            storage_service = await self._get_storage_service()
            image_creates = []

            for idx, enriched_image in enumerate(images):
                try:
                    # Generate unique filename
                    ext = enriched_image.format or 'jpg'
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"{vin}_{timestamp}_{idx}.{ext}"

                    # Upload image to Supabase Storage
                    upload_result = await storage_service.upload_vehicle_image(
                        image_bytes=enriched_image.image_bytes,
                        filename=filename,
                        optimize=True,
                        create_variants=True
                    )

                    # Create image record
                    image_create = ImageCreate(
                        listing_id=listing_id,
                        vin=vin,
                        category=enriched_image.category,
                        vehicle_angle=enriched_image.vehicle_angle,
                        description=enriched_image.description,
                        suggested_alt=enriched_image.suggested_alt,
                        quality_score=enriched_image.quality_score,
                        visible_damage=enriched_image.visible_damage or [],
                        original_filename=filename,
                        file_format=enriched_image.format or 'jpeg',
                        file_size_bytes=len(enriched_image.image_bytes),
                        width=enriched_image.width,
                        height=enriched_image.height,
                        original_url=upload_result.get('original_url'),
                        web_url=upload_result.get('web_url'),
                        thumbnail_url=upload_result.get('thumbnail_url'),
                        detail_url=upload_result.get('detail_url'),
                        page_number=enriched_image.page_number,
                        display_order=idx  # Use array index for display order
                    )
                    image_creates.append(image_create)

                except Exception as e:
                    logger.error(f"Failed to process image {idx} for listing {listing_id}: {e}")
                    # Continue with other images

            # Batch create image records
            if image_creates:
                created_images = await self.image_repo.create_batch(image_creates)
                logger.info(f"✅ Created {len(created_images)} image records for listing {listing_id}")
                return len(created_images)

            return 0

        except Exception as e:
            logger.error(f"❌ Failed to persist images for listing {listing_id}: {e}")
            # Don't fail the entire listing if images fail
            return 0

    async def _persist_condition_issues(
        self,
        listing_id: str,
        vin: str,
        condition: Any
    ) -> int:
        """Create condition issue records from condition data"""
        if not condition or not condition.issues:
            logger.info(f"No condition issues to persist for listing {listing_id}")
            return 0

        try:
            issue_count = 0

            # Process each issue category
            for category, issues in condition.issues.items():
                if not isinstance(issues, list):
                    continue

                for issue in issues:
                    try:
                        # Handle both string and dict issue formats
                        if isinstance(issue, str):
                            # Parse "LOCATION: Issue description" format
                            if ':' in issue:
                                location, description = issue.split(':', 1)
                                location = location.strip()
                                description = description.strip()
                            else:
                                location = None
                                description = issue
                        elif isinstance(issue, dict):
                            location = issue.get('location')
                            description = issue.get('description', issue.get('issue', ''))
                        else:
                            continue

                        # Determine severity based on condition score
                        if condition.score >= 4.5:
                            severity = 'minor'
                        elif condition.score >= 3.5:
                            severity = 'moderate'
                        else:
                            severity = 'major'

                        # Create issue record (direct insert via client for now)
                        # TODO: Create IssueRepository for this
                        issue_data = {
                            'listing_id': listing_id,
                            'vin': vin,
                            'issue_category': category,
                            'issue_type': 'condition_issue',
                            'severity': severity,
                            'description': description,
                            'location': location
                        }

                        # Direct insert for condition issues (no repository yet)
                        from ..services.supabase_client import get_supabase_client_singleton
                        client = get_supabase_client_singleton()
                        result = client.table('vehicle_condition_issues').insert(issue_data).execute()

                        if result.data:
                            issue_count += 1

                    except Exception as e:
                        logger.error(f"Failed to persist issue for listing {listing_id}: {e}")
                        # Continue with other issues

            logger.info(f"✅ Created {issue_count} condition issue records for listing {listing_id}")
            return issue_count

        except Exception as e:
            logger.error(f"❌ Failed to persist condition issues for listing {listing_id}: {e}")
            # Don't fail the entire listing if issues fail
            return 0

    def _generate_description(self, artifact: VehicleListingArtifact) -> str:
        """Generate a natural language description from the artifact"""
        try:
            parts = [
                f"{artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}",
            ]

            if artifact.vehicle.trim:
                parts.append(artifact.vehicle.trim)

            parts.append(f"with {artifact.vehicle.odometer:,} miles")

            if artifact.vehicle.drivetrain and artifact.vehicle.drivetrain != 'Unknown':
                parts.append(f"{artifact.vehicle.drivetrain} drivetrain")

            if artifact.vehicle.transmission and artifact.vehicle.transmission != 'Unknown':
                parts.append(f"{artifact.vehicle.transmission} transmission")

            condition_desc = f"Condition grade: {artifact.condition.grade} ({artifact.condition.score}/5)"
            parts.append(condition_desc)

            # Add notable features from condition
            if artifact.condition.issues:
                total_issues = sum(len(issues) for issues in artifact.condition.issues.values())
                if total_issues == 0:
                    parts.append("Excellent condition with no noted issues")
                elif total_issues <= 3:
                    parts.append(f"{total_issues} minor noted issues")
                else:
                    parts.append(f"{total_issues} noted issues - see details")

            return ". ".join(parts) + "."

        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            # Fallback to basic description
            return (f"{artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model} "
                   f"with {artifact.vehicle.odometer:,} miles. "
                   f"Condition: {artifact.condition.grade} ({artifact.condition.score}/5).")

    async def persist_batch(
        self,
        artifacts: List[VehicleListingArtifact],
        text_embeddings: Optional[List[List[float]]] = None,
        seller_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Persist multiple listings in batch.

        Args:
            artifacts: List of VehicleListingArtifact objects
            text_embeddings: Optional list of embeddings (must match artifacts length)
            seller_id: Optional seller/user ID

        Returns:
            List of result dicts for each artifact
        """
        if not artifacts:
            return []

        results = []

        for idx, artifact in enumerate(artifacts):
            try:
                embedding = text_embeddings[idx] if text_embeddings and idx < len(text_embeddings) else None

                result = await self.persist_listing(
                    artifact=artifact,
                    text_embedding=embedding,
                    seller_id=seller_id
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to persist artifact {idx}: {e}")
                results.append({
                    'error': str(e),
                    'vin': artifact.vehicle.vin if hasattr(artifact, 'vehicle') else 'unknown'
                })

        return results

    async def close(self):
        """Clean up resources"""
        if self.storage_service:
            await self.storage_service.close()


# Singleton instance
_listing_persistence_service: Optional[ListingPersistenceService] = None


def get_listing_persistence_service() -> ListingPersistenceService:
    """Get singleton ListingPersistenceService instance"""
    global _listing_persistence_service
    if _listing_persistence_service is None:
        _listing_persistence_service = ListingPersistenceService()
    return _listing_persistence_service
