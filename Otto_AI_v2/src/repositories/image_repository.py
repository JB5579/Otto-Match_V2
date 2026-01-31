"""
Otto.AI Image Repository
Data access layer for vehicle_images table operations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..services.supabase_client import get_supabase_client_singleton

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageCreate(BaseModel):
    """Data model for creating a new vehicle image"""
    listing_id: str
    vin: str
    category: str  # hero, carousel, detail, documentation
    vehicle_angle: str
    description: str
    suggested_alt: str
    quality_score: int
    visible_damage: List[str] = []
    original_filename: Optional[str] = None
    file_format: str
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    original_url: Optional[str] = None
    web_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    detail_url: Optional[str] = None
    image_embedding: Optional[List[float]] = None
    page_number: Optional[int] = None
    processing_metadata: Dict[str, Any] = {}
    display_order: int = 0


class ImageUpdate(BaseModel):
    """Data model for updating an image"""
    category: Optional[str] = None
    quality_score: Optional[int] = None
    visible_damage: Optional[List[str]] = None
    original_url: Optional[str] = None
    web_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    detail_url: Optional[str] = None
    image_embedding: Optional[List[float]] = None


class ImageSummary(BaseModel):
    """Summary model for image results"""
    id: str
    listing_id: str
    vin: str
    category: str
    vehicle_angle: str
    description: str
    suggested_alt: str
    quality_score: int
    thumbnail_url: Optional[str] = None
    web_url: Optional[str] = None


class ImageDetail(BaseModel):
    """Full image detail model"""
    id: str
    listing_id: str
    vin: str
    category: str
    vehicle_angle: str
    description: str
    suggested_alt: str
    quality_score: int
    visible_damage: List[str] = []
    original_filename: Optional[str] = None
    file_format: str
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    original_url: Optional[str] = None
    web_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    detail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ImageRepository:
    """
    Repository for vehicle_images table CRUD operations.
    Uses Supabase client for database access.
    """

    def __init__(self):
        self.client = get_supabase_client_singleton()
        self.table_name = 'vehicle_images'

    async def create(self, image: ImageCreate) -> Dict[str, Any]:
        """
        Create a new vehicle image record.

        Args:
            image: ImageCreate model with image data

        Returns:
            Dict with created image data including generated id
        """
        try:
            data = image.model_dump(exclude_none=True)

            # Handle embedding as string for pgvector
            if data.get('image_embedding'):
                data['image_embedding'] = str(data['image_embedding'])

            logger.info(f"Creating image for listing: {image.listing_id}, category: {image.category}")

            result = self.client.table(self.table_name).insert(data).execute()

            if result.data and len(result.data) > 0:
                created = result.data[0]
                logger.info(f"✅ Created image {created['id']} for listing: {image.listing_id}")
                return created
            else:
                raise ValueError("Insert returned no data")

        except Exception as e:
            logger.error(f"❌ Failed to create image for listing {image.listing_id}: {e}")
            raise

    async def create_batch(self, images: List[ImageCreate]) -> List[Dict[str, Any]]:
        """
        Create multiple vehicle image records in a single batch.

        Args:
            images: List of ImageCreate models

        Returns:
            List of created image data dicts
        """
        try:
            if not images:
                return []

            data_list = []
            for img in images:
                data = img.model_dump(exclude_none=True)
                if data.get('image_embedding'):
                    data['image_embedding'] = str(data['image_embedding'])
                data_list.append(data)

            logger.info(f"Batch creating {len(images)} images")

            result = self.client.table(self.table_name).insert(data_list).execute()

            if result.data:
                logger.info(f"✅ Batch created {len(result.data)} images")
                return result.data
            return []

        except Exception as e:
            logger.error(f"❌ Failed to batch create images: {e}")
            raise

    async def get_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an image by its ID.

        Args:
            image_id: UUID string of the image

        Returns:
            Image data dict or None if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('id', image_id) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get image {image_id}: {e}")
            raise

    async def get_by_listing(self, listing_id: str) -> List[Dict[str, Any]]:
        """
        Get all images for a specific listing.

        Args:
            listing_id: UUID string of the listing

        Returns:
            List of image data dicts
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('listing_id', listing_id) \
                .order('category') \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to get images for listing {listing_id}: {e}")
            raise

    async def get_by_vin(self, vin: str) -> List[Dict[str, Any]]:
        """
        Get all images for a specific VIN.

        Args:
            vin: Vehicle Identification Number

        Returns:
            List of image data dicts
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('vin', vin) \
                .order('category') \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to get images for VIN {vin}: {e}")
            raise

    async def get_hero_image(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the hero (primary) image for a listing.

        Args:
            listing_id: UUID string of the listing

        Returns:
            Hero image data or None if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('listing_id', listing_id) \
                .eq('category', 'hero') \
                .limit(1) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get hero image for listing {listing_id}: {e}")
            raise

    async def update(self, image_id: str, updates: ImageUpdate) -> Optional[Dict[str, Any]]:
        """
        Update an image by ID.

        Args:
            image_id: UUID string of the image
            updates: ImageUpdate model with fields to update

        Returns:
            Updated image data or None if not found
        """
        try:
            data = updates.model_dump(exclude_none=True)

            if not data:
                logger.warning(f"No updates provided for image {image_id}")
                return await self.get_by_id(image_id)

            # Handle embedding as string for pgvector
            if data.get('image_embedding'):
                data['image_embedding'] = str(data['image_embedding'])

            result = self.client.table(self.table_name) \
                .update(data) \
                .eq('id', image_id) \
                .execute()

            if result.data and len(result.data) > 0:
                logger.info(f"✅ Updated image {image_id}")
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to update image {image_id}: {e}")
            raise

    async def delete(self, image_id: str) -> bool:
        """
        Delete an image by ID.

        Args:
            image_id: UUID string of the image

        Returns:
            True if deleted, False if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .delete() \
                .eq('id', image_id) \
                .execute()

            if result.data and len(result.data) > 0:
                logger.info(f"✅ Deleted image {image_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Failed to delete image {image_id}: {e}")
            raise

    async def delete_by_listing(self, listing_id: str) -> int:
        """
        Delete all images for a listing.

        Args:
            listing_id: UUID string of the listing

        Returns:
            Number of images deleted
        """
        try:
            result = self.client.table(self.table_name) \
                .delete() \
                .eq('listing_id', listing_id) \
                .execute()

            count = len(result.data) if result.data else 0
            logger.info(f"✅ Deleted {count} images for listing {listing_id}")
            return count

        except Exception as e:
            logger.error(f"❌ Failed to delete images for listing {listing_id}: {e}")
            raise

    async def find_similar(
        self,
        embedding: List[float],
        limit: int = 5,
        exclude_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar images using pgvector similarity search.

        Args:
            embedding: Query embedding vector
            limit: Max number of results
            exclude_id: Image ID to exclude from results

        Returns:
            List of similar images with similarity scores
        """
        try:
            # Use Supabase RPC for vector similarity search
            params = {
                'query_embedding': str(embedding),
                'match_count': limit
            }

            if exclude_id:
                params['exclude_id'] = exclude_id

            result = self.client.rpc('match_vehicle_images', params).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to find similar images: {e}")
            # Fallback: return empty list if RPC not available
            logger.warning("Falling back to empty results - ensure match_vehicle_images RPC is created")
            return []

    async def count_by_listing(self, listing_id: str) -> int:
        """
        Count images for a listing.

        Args:
            listing_id: UUID string of the listing

        Returns:
            Count of images
        """
        try:
            result = self.client.table(self.table_name) \
                .select('id', count='exact') \
                .eq('listing_id', listing_id) \
                .execute()

            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"❌ Failed to count images for listing {listing_id}: {e}")
            raise


# Singleton instance
_image_repository: Optional[ImageRepository] = None


def get_image_repository() -> ImageRepository:
    """Get singleton ImageRepository instance"""
    global _image_repository
    if _image_repository is None:
        _image_repository = ImageRepository()
    return _image_repository
