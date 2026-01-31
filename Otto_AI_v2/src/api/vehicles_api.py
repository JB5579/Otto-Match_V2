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
class Vehicle(BaseModel):
    """Vehicle model matching frontend expectations"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: Optional[int] = None
    drivetrain: Optional[str] = None
    transmission: Optional[str] = None
    engine: Optional[str] = None
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    body_style: Optional[str] = None
    fuel_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    condition_score: Optional[float] = None
    condition_grade: Optional[str] = None
    description_text: Optional[str] = None
    status: Optional[str] = None
    listing_source: Optional[str] = None
    asking_price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Frontend-specific fields
    isFavorited: bool = False
    isComparing: bool = False
    images: List[str] = []


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
        sort_order_bool = sort_order.lower() == 'desc' if sort_order else True
        if sort_by == 'year':
            query = query.order('year', desc=sort_order_bool)
        elif sort_by == 'price':
            # Sort by effective_price (asking_price is the primary field)
            # Note: NULL values will be sorted first in PostgreSQL (ASC) or last (DESC)
            query = query.order('asking_price', desc=sort_order_bool)
        elif sort_by == 'mileage':
            query = query.order('odometer', desc=sort_order_bool)
        else:
            # Default: sort by created_at (newest first)
            query = query.order('created_at', desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute query
        result = query.execute()

        # Get total count from response
        total = result.count if result.count is not None else len(result.data)

        # Convert database rows to Vehicle models
        vehicles = []
        for row in result.data:
            vehicle = Vehicle(
                id=row.get('id', ''),
                vin=row.get('vin', ''),
                year=row.get('year', 0),
                make=row.get('make', ''),
                model=row.get('model', ''),
                trim=row.get('trim'),
                odometer=row.get('odometer'),
                drivetrain=row.get('drivetrain'),
                transmission=row.get('transmission'),
                engine=row.get('engine'),
                exterior_color=row.get('exterior_color'),
                interior_color=row.get('interior_color'),
                body_style=row.get('body_style'),
                fuel_type=row.get('fuel_type'),
                vehicle_type=row.get('vehicle_type'),
                condition_score=row.get('condition_score'),
                condition_grade=row.get('condition_grade'),
                description_text=row.get('description_text'),
                status=row.get('status'),
                listing_source=row.get('listing_source'),
                asking_price=row.get('asking_price'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                isFavorited=False,
                isComparing=False,
                images=[]  # Will be populated with actual images in future
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


@vehicles_router.get("/", response_model=VehicleSearchResponse)
async def list_vehicles(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all vehicles (simplified endpoint for basic listing).

    This is a simpler version of /search that returns all active vehicles.
    """
    return await search_vehicles(limit=limit, offset=offset)


@vehicles_router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str):
    """Get detailed information for a specific vehicle."""
    try:
        supabase = get_supabase_client()

        result = supabase.table('vehicle_listings').select('*').eq('id', vehicle_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        row = result.data[0]

        vehicle = Vehicle(
            id=row.get('id', ''),
            vin=row.get('vin', ''),
            year=row.get('year', 0),
            make=row.get('make', ''),
            model=row.get('model', ''),
            trim=row.get('trim'),
            odometer=row.get('odometer'),
            drivetrain=row.get('drivetrain'),
            transmission=row.get('transmission'),
            engine=row.get('engine'),
            exterior_color=row.get('exterior_color'),
            interior_color=row.get('interior_color'),
            body_style=row.get('body_style'),
            fuel_type=row.get('fuel_type'),
            vehicle_type=row.get('vehicle_type'),
            condition_score=row.get('condition_score'),
            condition_grade=row.get('condition_grade'),
            description_text=row.get('description_text'),
            status=row.get('status'),
            listing_source=row.get('listing_source'),
            asking_price=row.get('asking_price'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            isFavorited=False,
            isComparing=False,
            images=[]
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
