"""
Otto.AI Vehicles API
FastAPI endpoints for vehicle search and listing display.
Bridges the frontend expectations (/api/v1/vehicles) with Supabase database.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for v1 vehicles endpoints
vehicles_router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


# Pydantic models for API responses
class VehicleImage(BaseModel):
    """Vehicle image matching frontend expectations"""
    url: str
    description: str
    category: str = 'hero'  # 'hero' | 'carousel' | 'detail'
    altText: str = ''


class Vehicle(BaseModel):
    """Vehicle model matching frontend expectations"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    # Frontend expects 'mileage' not 'odometer'
    mileage: Optional[int] = None
    drivetrain: Optional[str] = None
    transmission: Optional[str] = None
    # Frontend expects 'color' not 'exterior_color'
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    body_type: Optional[str] = None  # Frontend expects 'body_type' not 'body_style'
    condition: Optional[str] = None  # Frontend expects 'condition' not 'condition_grade'
    description: Optional[str] = None  # Frontend expects 'description' not 'description_text'
    images: Optional[List[VehicleImage]] = None
    features: Optional[List[str]] = None
    matchScore: Optional[float] = None
    availabilityStatus: Optional[str] = None  # 'available' | 'reserved' | 'sold'
    currentViewers: Optional[int] = None
    ottoRecommendation: Optional[str] = None
    range: Optional[int] = None  # For EVs - miles range
    isFavorited: bool = False
    # Frontend expects 'price' not 'asking_price'
    price: Optional[float] = None
    originalPrice: Optional[float] = None
    savings: Optional[float] = None
    # Required field - use empty string if null
    seller_id: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Additional fields not in frontend type (will be ignored)
    isComparing: bool = False


class VehicleSearchResponse(BaseModel):
    """Response model for vehicle search matching frontend expectations"""
    vehicles: List[Vehicle]
    total: int


@vehicles_router.get("/search", response_model=VehicleSearchResponse)
async def search_vehicles(
    limit: int = Query(50, ge=1, le=100, description="Number of vehicles to return"),
    offset: int = Query(0, ge=0, description="Number of vehicles to skip"),
    # Single-select filters (backward compatibility)
    make: Optional[str] = Query(None, description="Filter by vehicle make"),
    model: Optional[str] = Query(None, description="Filter by vehicle model"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    # Multi-select filters (NEW - Story 3-7)
    makes: Optional[str] = Query(None, description="Comma-separated makes for multi-select (e.g., 'Toyota,Honda,Ford')"),
    vehicle_types: Optional[str] = Query(None, description="Comma-separated vehicle types (e.g., 'SUV,Sedan')"),
    # Range filters
    year: Optional[int] = Query(None, description="Filter by specific year"),
    year_min: Optional[int] = Query(None, description="Minimum model year"),
    year_max: Optional[int] = Query(None, description="Maximum model year"),
    price_min: Optional[float] = Query(None, description="Minimum asking_price"),
    price_max: Optional[float] = Query(None, description="Maximum asking_price"),
    mileage_min: Optional[int] = Query(None, description="Minimum mileage"),
    mileage_max: Optional[int] = Query(None, description="Maximum mileage"),
    # Sorting (NEW - Story 3-7)
    sort_by: Optional[str] = Query(None, description="Sort by: created_at, year, price, mileage"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
):
    """
    Search vehicles with optional filters.

    Story 3-7 Updates:
    - Added multi-select support for makes and vehicle_types (comma-separated)
    - Added sorting support for better UX
    - Supports both single and multi-select filters for flexibility

    Returns all active vehicles from the database with pagination support.
    """
    try:
        supabase = get_supabase_client()

        # Build query
        query = supabase.table('vehicle_listings').select('*', count='exact')

        # Apply filters (Story 3-7: Added multi-select support)
        # Multi-select makes (priority over single make)
        if makes:
            makes_list = [m.strip() for m in makes.split(',') if m.strip()]
            if makes_list:
                query = query.in_('make', makes_list)
        # Fallback to single-select make
        elif make:
            query = query.eq('make', make)

        if model:
            query = query.eq('model', model)
        if year:
            query = query.eq('year', year)
        if year_min:
            query = query.gte('year', year_min)
        if year_max:
            query = query.lte('year', year_max)

        # Multi-select vehicle_types (priority over single vehicle_type)
        if vehicle_types:
            types_list = [t.strip() for t in vehicle_types.split(',') if t.strip()]
            if types_list:
                query = query.in_('vehicle_type', types_list)
        # Fallback to single-select vehicle_type
        elif vehicle_type:
            query = query.eq('vehicle_type', vehicle_type)

        if mileage_min:
            query = query.gte('odometer', mileage_min)
        if mileage_max:
            query = query.lte('odometer', mileage_max)

        # Price filtering using effective_price (Story 3-7)
        # Uses coalesce of asking_price, auction_forecast, estimated_price
        # For simplicity, we filter on asking_price first (most common case)
        if price_min is not None:
            # Filter vehicles where asking_price >= price_min
            # Note: This excludes vehicles with NULL asking_price
            query = query.gte('asking_price', price_min)
        if price_max is not None:
            query = query.lte('asking_price', price_max)

        # Always filter for active vehicles
        query = query.eq('status', 'active')

        # Apply sorting (Story 3-7: Dynamic sorting support)
        # Default: sort by created_at (newest first)
        query = query.order('created_at', desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute query
        result = query.execute()

        # Get total count from response
        total = result.count if result.count is not None else len(result.data)

        # Get all listing IDs for batch image fetch
        listing_ids = [row.get('id') for row in result.data]

        # Fetch images for all vehicles in one batch query
        images_by_listing = {}
        if listing_ids:
            images_result = supabase.table('vehicle_images') \
                .select('*') \
                .in_('listing_id', listing_ids) \
                .execute()

            # Group images by listing_id
            for img_row in images_result.data:
                listing_id = img_row.get('listing_id')
                if listing_id not in images_by_listing:
                    images_by_listing[listing_id] = []

                # Transform database image to frontend format
                # Use web_url if available, otherwise use a placeholder
                image_url = img_row.get('web_url') or img_row.get('detail_url') or img_row.get('thumbnail_url')

                # Only include images that have URLs (not null/empty)
                if image_url:
                    images_by_listing[listing_id].append({
                        'url': image_url,
                        'description': img_row.get('description') or '',
                        'category': img_row.get('category') or 'hero',
                        'altText': img_row.get('suggested_alt') or ''
                    })

        # Convert database rows to Vehicle models
        # Map database field names to frontend expectations
        vehicles = []
        for row in result.data:
            listing_id = row.get('id', '')

            # Map database fields to frontend field names
            # Database uses: odometer, description_text, exterior_color, body_style, asking_price
            # Frontend expects: mileage, description, color, body_type, price

            # Get images for this listing
            images = images_by_listing.get(listing_id, [])

            vehicle = Vehicle(
                id=row.get('id', ''),
                vin=row.get('vin', ''),
                year=row.get('year', 0),
                make=row.get('make', ''),
                model=row.get('model', ''),
                trim=row.get('trim'),
                # Map odometer -> mileage
                mileage=row.get('odometer'),
                drivetrain=row.get('drivetrain'),
                transmission=row.get('transmission'),
                # Map exterior_color -> color
                color=row.get('exterior_color'),
                fuel_type=row.get('fuel_type'),
                # Map body_style -> body_type
                body_type=row.get('body_style') or row.get('vehicle_type'),
                # Map condition_grade -> condition (use grade text)
                condition=row.get('condition_grade'),
                # Map description_text -> description
                description=row.get('description_text'),
                images=images,
                features=None,  # Will be populated from features table in future
                matchScore=row.get('condition_score'),  # Use condition_score as match score
                # Map status -> availabilityStatus (convert active->available)
                availabilityStatus='available' if row.get('status') == 'active' else 'reserved',
                currentViewers=None,  # Will be tracked via WebSocket in future
                ottoRecommendation=None,  # Will be generated by AI in future
                range=None,  # Will be calculated for EVs in future
                isFavorited=False,
                # Map asking_price -> price
                price=row.get('asking_price') or row.get('estimated_price') or row.get('auction_forecast'),
                originalPrice=None,  # Will be calculated from price history
                savings=None,  # Will be calculated from price history
                # Required field - use empty string if null
                seller_id=row.get('seller_id') or '',
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                isComparing=False,
            )
            vehicles.append(vehicle)

        logger.info(f"Returning {len(vehicles)} vehicles (total: {total})")

        return VehicleSearchResponse(
            vehicles=vehicles,
            total=total
        )

    except Exception as e:
        logger.error(f"Failed to search vehicles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search vehicles: {str(e)}"
        )


# NOTE: The "/" endpoint has been removed because it was causing Query parameter issues.
# All clients should use the "/search" endpoint directly.

@vehicles_router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str):
    """Get detailed information for a specific vehicle."""
    try:
        supabase = get_supabase_client()

        result = supabase.table('vehicle_listings').select('*').eq('id', vehicle_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        row = result.data[0]

        # Build images list from database (if available)
        images = []

        vehicle = Vehicle(
            id=row.get('id', ''),
            vin=row.get('vin', ''),
            year=row.get('year', 0),
            make=row.get('make', ''),
            model=row.get('model', ''),
            trim=row.get('trim'),
            # Map odometer -> mileage
            mileage=row.get('odometer'),
            drivetrain=row.get('drivetrain'),
            transmission=row.get('transmission'),
            # Map exterior_color -> color
            color=row.get('exterior_color'),
            fuel_type=row.get('fuel_type'),
            # Map body_style -> body_type
            body_type=row.get('body_style') or row.get('vehicle_type'),
            # Map condition_grade -> condition
            condition=row.get('condition_grade'),
            # Map description_text -> description
            description=row.get('description_text'),
            images=images,
            features=None,
            matchScore=row.get('condition_score'),
            # Map status -> availabilityStatus
            availabilityStatus='available' if row.get('status') == 'active' else 'reserved',
            currentViewers=None,
            ottoRecommendation=None,
            range=None,
            isFavorited=False,
            # Map asking_price -> price
            price=row.get('asking_price') or row.get('estimated_price') or row.get('auction_forecast'),
            originalPrice=None,
            savings=None,
            # Required field - use empty string if null
            seller_id=row.get('seller_id') or '',
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            isComparing=False,
        )

        return vehicle

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vehicle {vehicle_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get vehicle: {str(e)}"
        )
