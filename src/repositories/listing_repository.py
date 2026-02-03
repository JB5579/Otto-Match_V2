"""
Otto.AI Listing Repository
Data access layer for vehicle_listings table operations
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


class ListingCreate(BaseModel):
    """Data model for creating a new listing"""
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: int
    drivetrain: str
    transmission: str
    engine: str
    exterior_color: str
    interior_color: str
    body_style: Optional[str] = None
    fuel_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    condition_score: float
    condition_grade: str
    description_text: Optional[str] = None
    text_embedding: Optional[List[float]] = None
    status: str = 'active'
    listing_source: str = 'pdf_upload'
    processing_metadata: Dict[str, Any] = {}
    seller_id: Optional[str] = None


class ListingUpdate(BaseModel):
    """Data model for updating a listing"""
    status: Optional[str] = None
    odometer: Optional[int] = None
    description_text: Optional[str] = None
    text_embedding: Optional[List[float]] = None
    processing_metadata: Optional[Dict[str, Any]] = None


class ListingSummary(BaseModel):
    """Summary model for listing results"""
    listing_id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: int
    exterior_color: str
    interior_color: str
    condition_score: float
    condition_grade: str
    status: str
    created_at: datetime
    primary_image_url: Optional[str] = None
    image_count: int = 0


class ListingDetail(BaseModel):
    """Full listing detail model"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: int
    drivetrain: str
    transmission: str
    engine: str
    exterior_color: str
    interior_color: str
    condition_score: float
    condition_grade: str
    description_text: Optional[str] = None
    status: str
    listing_source: str
    processing_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    seller_id: Optional[str] = None


class ListingRepository:
    """
    Repository for vehicle_listings table CRUD operations.
    Uses Supabase client for database access.
    """

    def __init__(self):
        self.client = get_supabase_client_singleton()
        self.table_name = 'vehicle_listings'

    async def create(self, listing: ListingCreate) -> Dict[str, Any]:
        """
        Create a new vehicle listing.

        Args:
            listing: ListingCreate model with vehicle data

        Returns:
            Dict with created listing data including generated id
        """
        try:
            data = listing.model_dump(exclude_none=True)

            # Handle embedding as string for pgvector
            if data.get('text_embedding'):
                data['text_embedding'] = str(data['text_embedding'])

            logger.info(f"Creating listing for VIN: {listing.vin}")

            result = self.client.table(self.table_name).insert(data).execute()

            if result.data and len(result.data) > 0:
                created = result.data[0]
                logger.info(f"✅ Created listing {created['id']} for VIN: {listing.vin}")
                return created
            else:
                raise ValueError("Insert returned no data")

        except Exception as e:
            logger.error(f"❌ Failed to create listing for VIN {listing.vin}: {e}")
            raise

    async def upsert(
        self,
        listing: ListingCreate,
        update_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new listing or update existing one by VIN.

        Args:
            listing: ListingCreate model with vehicle data
            update_metadata: If True, merge processing_metadata when updating

        Returns:
            Dict with created/updated listing data including id

        Raises:
            ValueError: If upsert operation fails
        """
        try:
            # First, check if listing exists by VIN
            existing = await self.get_by_vin(listing.vin)

            data = listing.model_dump(exclude_none=True)

            # Handle embedding as string for pgvector
            if data.get('text_embedding'):
                data['text_embedding'] = str(data['text_embedding'])

            if existing:
                # Update existing listing
                logger.info(f"⚠️ VIN {listing.vin} exists, updating listing {existing['id']}")

                # Merge processing_metadata if requested
                if update_metadata and existing.get('processing_metadata'):
                    existing_meta = existing['processing_metadata']
                    new_meta = data.get('processing_metadata', {})
                    data['processing_metadata'] = {**existing_meta, **new_meta}

                result = self.client.table(self.table_name) \
                    .update(data) \
                    .eq('id', existing['id']) \
                    .execute()

                if result.data and len(result.data) > 0:
                    updated = result.data[0]
                    logger.info(f"✅ Updated listing {updated['id']} for VIN: {listing.vin}")
                    return updated
                else:
                    raise ValueError("Update returned no data")
            else:
                # Create new listing
                logger.info(f"Creating new listing for VIN: {listing.vin}")

                result = self.client.table(self.table_name).insert(data).execute()

                if result.data and len(result.data) > 0:
                    created = result.data[0]
                    logger.info(f"✅ Created listing {created['id']} for VIN: {listing.vin}")
                    return created
                else:
                    raise ValueError("Insert returned no data")

        except Exception as e:
            logger.error(f"❌ Failed to upsert listing for VIN {listing.vin}: {e}")
            raise

    async def get_by_id(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a listing by its ID.

        Args:
            listing_id: UUID string of the listing

        Returns:
            Listing data dict or None if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('id', listing_id) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get listing {listing_id}: {e}")
            raise

    async def get_by_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """
        Get a listing by VIN.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Listing data dict or None if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .select('*') \
                .eq('vin', vin) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get listing by VIN {vin}: {e}")
            raise

    async def list_all(
        self,
        limit: int = 20,
        offset: int = 0,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        Get paginated list of vehicle listings with filters.

        Args:
            limit: Max number of results
            offset: Number of results to skip
            make: Filter by vehicle make
            model: Filter by vehicle model
            year_min: Minimum year
            year_max: Maximum year
            status: Filter by status (default: active)

        Returns:
            List of listing dicts
        """
        try:
            query = self.client.table(self.table_name) \
                .select('id, vin, year, make, model, trim, odometer, exterior_color, interior_color, condition_score, condition_grade, status, created_at') \
                .eq('status', status) \
                .order('created_at', desc=True)

            if make:
                query = query.ilike('make', f'%{make}%')
            if model:
                query = query.ilike('model', f'%{model}%')
            if year_min:
                query = query.gte('year', year_min)
            if year_max:
                query = query.lte('year', year_max)

            result = query.range(offset, offset + limit - 1).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to list listings: {e}")
            raise

    async def update(self, listing_id: str, updates: ListingUpdate) -> Optional[Dict[str, Any]]:
        """
        Update a listing by ID.

        Args:
            listing_id: UUID string of the listing
            updates: ListingUpdate model with fields to update

        Returns:
            Updated listing data or None if not found
        """
        try:
            data = updates.model_dump(exclude_none=True)

            if not data:
                logger.warning(f"No updates provided for listing {listing_id}")
                return await self.get_by_id(listing_id)

            # Handle embedding as string for pgvector
            if data.get('text_embedding'):
                data['text_embedding'] = str(data['text_embedding'])

            result = self.client.table(self.table_name) \
                .update(data) \
                .eq('id', listing_id) \
                .execute()

            if result.data and len(result.data) > 0:
                logger.info(f"✅ Updated listing {listing_id}")
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Failed to update listing {listing_id}: {e}")
            raise

    async def delete(self, listing_id: str) -> bool:
        """
        Delete a listing by ID (soft delete by setting status to 'inactive').

        Args:
            listing_id: UUID string of the listing

        Returns:
            True if deleted, False if not found
        """
        try:
            result = self.client.table(self.table_name) \
                .update({'status': 'inactive'}) \
                .eq('id', listing_id) \
                .execute()

            if result.data and len(result.data) > 0:
                logger.info(f"✅ Soft-deleted listing {listing_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Failed to delete listing {listing_id}: {e}")
            raise

    async def find_similar(
        self,
        embedding: List[float],
        limit: int = 5,
        exclude_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar listings using pgvector similarity search.

        Args:
            embedding: Query embedding vector
            limit: Max number of results
            exclude_id: Listing ID to exclude from results

        Returns:
            List of similar listings with similarity scores
        """
        try:
            # Use Supabase RPC for vector similarity search
            # This requires a database function to be created
            params = {
                'query_embedding': str(embedding),
                'match_count': limit
            }

            if exclude_id:
                params['exclude_id'] = exclude_id

            result = self.client.rpc('match_vehicle_listings', params).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"❌ Failed to find similar listings: {e}")
            # Fallback: return empty list if RPC not available
            logger.warning("Falling back to empty results - ensure match_vehicle_listings RPC is created")
            return []

    async def count(self, status: str = 'active') -> int:
        """
        Count listings by status.

        Args:
            status: Filter by status

        Returns:
            Count of listings
        """
        try:
            result = self.client.table(self.table_name) \
                .select('id', count='exact') \
                .eq('status', status) \
                .execute()

            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"❌ Failed to count listings: {e}")
            raise


# Singleton instance
_listing_repository: Optional[ListingRepository] = None


def get_listing_repository() -> ListingRepository:
    """Get singleton ListingRepository instance"""
    global _listing_repository
    if _listing_repository is None:
        _listing_repository = ListingRepository()
    return _listing_repository
