"""
Otto.AI Collections API Endpoints

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Public API endpoints for browsing vehicle collections

Endpoints:
- GET /api/collections - Get all collections
- GET /api/collections/{id} - Get collection details
- GET /api/collections/{id}/vehicles - Get vehicles in collection
- GET /api/collections/trending - Get trending collections
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.collections.collection_engine import CollectionEngine, CollectionType
from src.semantic.vehicle_database_service import VehicleDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Collections API
# ============================================================================

class VehicleSummary(BaseModel):
    """Simplified vehicle model for collection listings"""
    id: str = Field(..., description="Vehicle ID")
    vin: str = Field(..., description="Vehicle VIN")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Model year")
    trim: Optional[str] = Field(None, description="Trim level")
    price: float = Field(..., description="Vehicle price")
    mileage: Optional[int] = Field(None, description="Mileage")
    vehicle_type: str = Field(..., description="Vehicle type")
    fuel_type: str = Field(..., description="Fuel type")
    transmission: Optional[str] = Field(None, description="Transmission")
    exterior_color: Optional[str] = Field(None, description="Exterior color")
    interior_color: Optional[str] = Field(None, description="Interior color")
    images: List[str] = Field(default_factory=list, description="Vehicle images")
    location: Optional[Dict[str, str]] = Field(None, description="Location (city, state)")
    score: float = Field(..., description="Collection relevance score")

class CollectionSummary(BaseModel):
    """Summary model for collection listings"""
    id: str = Field(..., description="Collection ID")
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    type: str = Field(..., description="Collection type")
    vehicle_count: int = Field(..., description="Number of vehicles")
    image_url: Optional[str] = Field(None, description="Collection preview image")
    is_featured: bool = Field(..., description="Featured status")
    created_at: str = Field(..., description="Creation timestamp")

class CollectionDetails(BaseModel):
    """Detailed collection model"""
    id: str = Field(..., description="Collection ID")
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    type: str = Field(..., description="Collection type")
    criteria: Dict[str, Any] = Field(..., description="Collection criteria")
    vehicle_count: int = Field(..., description="Number of vehicles")
    vehicles: List[VehicleSummary] = Field(..., description="Vehicles in collection")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    related_collections: List[CollectionSummary] = Field(default_factory=list, description="Similar collections")

class CollectionsListResponse(BaseModel):
    """Response model for collections list"""
    collections: List[CollectionSummary] = Field(..., description="List of collections")
    total_count: int = Field(..., description="Total number of collections")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for collections endpoints
collections_router = APIRouter(
    prefix="/api/collections",
    tags=["Collections"],
    responses={404: {"description": "Not found"}}
)

# Global instances
collection_engine: Optional[CollectionEngine] = None
vehicle_db_service: Optional[VehicleDatabaseService] = None

async def get_collection_engine() -> CollectionEngine:
    """Get collection engine instance"""
    global collection_engine
    if collection_engine is None:
        collection_engine = CollectionEngine()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await collection_engine.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize collection engine"
            )

    return collection_engine

async def get_vehicle_db_service() -> VehicleDatabaseService:
    """Get vehicle database service instance"""
    global vehicle_db_service
    if vehicle_db_service is None:
        vehicle_db_service = VehicleDatabaseService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        success = await vehicle_db_service.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize vehicle database service"
            )

    return vehicle_db_service

# ============================================================================
# API Endpoints
# ============================================================================

@collections_router.get("/", response_model=CollectionsListResponse)
async def get_collections(
    collection_type: Optional[str] = Query(None, description="Filter by collection type"),
    featured_only: bool = Query(False, description="Show only featured collections"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    req: Any = Depends(lambda: None)
) -> CollectionsListResponse:
    """
    Get all curated and trending collections

    Returns paginated list of collections with optional filtering.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Parse collection type
        collection_type_enum = None
        if collection_type:
            try:
                collection_type_enum = CollectionType(collection_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid collection type: {collection_type}"
                )

        # Get collections
        collections = await engine.get_collections(
            collection_type=collection_type_enum,
            featured_only=featured_only,
            limit=per_page
        )

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_collections = collections[start_idx:end_idx]

        # Convert to response models
        response_collections = []
        for collection in paginated_collections:
            # Get preview image from first vehicle
            preview_image = None
            if collection.vehicle_ids:
                vehicle_db = await get_vehicle_db_service()
                first_vehicle = await vehicle_db.get_vehicle(collection.vehicle_ids[0])
                if first_vehicle and first_vehicle.get('images'):
                    preview_image = first_vehicle['images'][0]

            response_collections.append(CollectionSummary(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                type=collection.type.value,
                vehicle_count=len(collection.vehicle_ids),
                image_url=preview_image,
                is_featured=collection.metadata.get('is_featured', False),
                created_at=collection.created_at.isoformat()
            ))

        return CollectionsListResponse(
            collections=response_collections,
            total_count=len(collections),
            page=page,
            per_page=per_page
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving collections"
        )

@collections_router.get("/{collection_id}", response_model=CollectionDetails)
async def get_collection_details(
    collection_id: str = Path(..., description="Collection ID"),
    req: Any = Depends(lambda: None)
) -> CollectionDetails:
    """
    Get detailed collection information

    Returns collection details with a sample of vehicles and related collections.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Get collection
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=404,
                detail="Collection not found"
            )

        # Get vehicle database service
        vehicle_db = await get_vehicle_db_service()

        # Get vehicles in collection (limited to 20 for preview)
        vehicles = []
        vehicle_ids = collection.vehicle_ids[:20]  # Limit for performance

        for vehicle_id in vehicle_ids:
            vehicle = await vehicle_db.get_vehicle(vehicle_id)
            if vehicle:
                # Get score from collection
                score = collection.scores.get(vehicle_id, 1.0)

                vehicles.append(VehicleSummary(
                    id=vehicle['id'],
                    vin=vehicle['vin'],
                    make=vehicle['make'],
                    model=vehicle['model'],
                    year=vehicle['year'],
                    trim=vehicle.get('trim'),
                    price=vehicle.get('price', 0),
                    mileage=vehicle.get('mileage'),
                    vehicle_type=vehicle['vehicle_type'],
                    fuel_type=vehicle['fuel_type'],
                    transmission=vehicle.get('transmission'),
                    exterior_color=vehicle.get('exterior_color'),
                    interior_color=vehicle.get('interior_color'),
                    images=vehicle.get('images', []),
                    location={
                        'city': vehicle.get('city'),
                        'state': vehicle.get('state')
                    } if vehicle.get('city') else None,
                    score=score
                ))

        # Get related collections (same type, featured)
        related_collections = []
        if collection.type != CollectionType.TRENDING:
            related = await engine.get_collections(
                collection_type=collection.type,
                featured_only=True,
                limit=5
            )

            for related_collection in related:
                if related_collection.id != collection.id:
                    related_collections.append(CollectionSummary(
                        id=related_collection.id,
                        name=related_collection.name,
                        description=related_collection.description,
                        type=related_collection.type.value,
                        vehicle_count=len(related_collection.vehicle_ids),
                        image_url=None,  # Skip images for related collections
                        is_featured=True,
                        created_at=related_collection.created_at.isoformat()
                    ))

        # Build response
        return CollectionDetails(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            type=collection.type.value,
            criteria=collection.criteria.__dict__,
            vehicle_count=len(collection.vehicle_ids),
            vehicles=vehicles,
            created_at=collection.created_at.isoformat(),
            updated_at=collection.updated_at.isoformat(),
            related_collections=related_collections
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection details {collection_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving collection details"
        )

@collections_router.get("/{collection_id}/vehicles")
async def get_collection_vehicles(
    collection_id: str = Path(..., description="Collection ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("rank", description="Sort by: rank, price, year, mileage"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get all vehicles in a collection

    Returns paginated list of vehicles belonging to a collection
    with sorting options.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Get collection
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=404,
                detail="Collection not found"
            )

        # Get vehicle database service
        vehicle_db = await get_vehicle_db_service()

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_vehicle_ids = collection.vehicle_ids[start_idx:end_idx]

        # Get vehicles
        vehicles = []
        for vehicle_id in paginated_vehicle_ids:
            vehicle = await vehicle_db.get_vehicle(vehicle_id)
            if vehicle:
                # Get score from collection
                score = collection.scores.get(vehicle_id, 1.0)

                vehicles.append({
                    **vehicle,
                    'collection_score': score
                })

        # Apply sorting if needed
        if sort_by != "rank":
            reverse = sort_order == "desc"
            if sort_by == "price":
                vehicles.sort(key=lambda x: x.get('price', 0), reverse=reverse)
            elif sort_by == "year":
                vehicles.sort(key=lambda x: x.get('year', 0), reverse=reverse)
            elif sort_by == "mileage":
                vehicles.sort(key=lambda x: x.get('mileage', 0), reverse=reverse)

        return {
            "vehicles": vehicles,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": len(collection.vehicle_ids),
                "total_pages": (len(collection.vehicle_ids) + per_page - 1) // per_page
            },
            "collection_info": {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "type": collection.type.value
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection vehicles {collection_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving collection vehicles"
        )

@collections_router.get("/trending", response_model=CollectionsListResponse)
async def get_trending_collections(
    limit: int = Query(10, ge=1, le=50, description="Number of trending collections"),
    req: Any = Depends(lambda: None)
) -> CollectionsListResponse:
    """
    Get trending collections

    Returns collections with highest engagement in the recent period.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Get trending collections
        collections = await engine.get_trending_collections(limit=limit)

        # Convert to response models
        response_collections = []
        for collection in collections:
            response_collections.append(CollectionSummary(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                type=collection.type.value,
                vehicle_count=len(collection.vehicle_ids),
                image_url=None,  # Add trending badge in UI instead
                is_featured=True,
                created_at=collection.created_at.isoformat()
            ))

        return CollectionsListResponse(
            collections=response_collections,
            total_count=len(response_collections),
            page=1,
            per_page=limit
        )

    except Exception as e:
        logger.error(f"Error getting trending collections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving trending collections"
        )

@collections_router.get("/categories")
async def get_collection_categories(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get available collection categories

    Returns predefined categories and templates that users can explore.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Get templates from cache
        categories = {
            "use_case": {
                "name": "Use Case",
                "description": "Collections for specific needs and lifestyles",
                "templates": []
            },
            "price_range": {
                "name": "Price Range",
                "description": "Budget-friendly to luxury collections",
                "templates": []
            },
            "feature_based": {
                "name": "Features",
                "description": "Collections based on specific features",
                "templates": []
            },
            "seasonal": {
                "name": "Seasonal",
                "description": "Timely collections for different seasons",
                "templates": []
            }
        }

        # Group templates by type
        for template_name, template in engine._templates_cache.items():
            if template.template_type in categories:
                categories[template.template_type]["templates"].append({
                    "name": template.name,
                    "description": template.description,
                    "template_name": template_name
                })

        return {
            "categories": categories,
            "featured_categories": [
                {
                    "name": "Electric Vehicles",
                    "description": "All electric and plug-in hybrid vehicles",
                    "collection_type": "feature_based",
                    "icon": "ev"
                },
                {
                    "name": "Family SUVs",
                    "description": "Spacious SUVs perfect for families",
                    "collection_type": "use_case",
                    "icon": "family"
                },
                {
                    "name": "Budget Friendly",
                    "description": "Affordable vehicles under $30k",
                    "collection_type": "price_range",
                    "icon": "budget"
                },
                {
                    "name": "Performance Cars",
                    "description": "Sports cars and high-performance vehicles",
                    "collection_type": "feature_based",
                    "icon": "performance"
                }
            ]
        }

    except Exception as e:
        logger.error(f"Error getting collection categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving categories"
        )