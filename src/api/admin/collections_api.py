"""
Otto.AI Admin Collections API Endpoints

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Admin-only API endpoints for managing vehicle collections

Endpoints:
- POST /api/admin/collections/create - Create new collection
- PUT /api/admin/collections/{id}/update - Update collection
- DELETE /api/admin/collections/{id}/delete - Delete collection
- GET /api/admin/collections/list - List all collections
- POST /api/admin/collections/{id}/refresh - Refresh collection vehicles
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.collections.collection_engine import (
    CollectionEngine,
    Collection,
    CollectionCriteria,
    CollectionType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Admin Collections API
# ============================================================================

class CollectionCriteriaRequest(BaseModel):
    """Request model for collection criteria"""
    vehicle_type: Optional[str] = Field(None, description="Vehicle type (e.g., SUV, Sedan)")
    fuel_type: Optional[Union[str, List[str]]] = Field(None, description="Fuel type(s)")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    year_min: Optional[int] = Field(None, ge=1900, le=2030, description="Minimum year")
    year_max: Optional[int] = Field(None, ge=1900, le=2030, description="Maximum year")
    mileage_max: Optional[int] = Field(None, ge=0, description="Maximum mileage")
    make: Optional[Union[str, List[str]]] = Field(None, description="Vehicle make(s)")
    model: Optional[str] = Field(None, description="Vehicle model")
    features: Optional[List[str]] = Field(None, description="Required features")
    location: Optional[str] = Field(None, description="Location filter")
    seats_min: Optional[int] = Field(None, ge=1, le=9, description="Minimum seats")
    safety_rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum safety rating")
    fuel_efficiency_min: Optional[float] = Field(None, ge=0, description="Minimum fuel efficiency (mpg)")
    horsepower_min: Optional[int] = Field(None, ge=0, description="Minimum horsepower")
    drive_type: Optional[str] = Field(None, description="Drive type (e.g., AWD, FWD)")
    custom_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom rules")

    @validator('year_max')
    def validate_year_range(cls, v, values):
        if v is not None and 'year_min' in values and values['year_min'] is not None:
            if v < values['year_min']:
                raise ValueError('year_max must be greater than or equal to year_min')
        return v

    @validator('price_max')
    def validate_price_range(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v < values['price_min']:
                raise ValueError('price_max must be greater than or equal to price_min')
        return v

class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection"""
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    collection_type: str = Field(..., description="Collection type (curated, trending, dynamic, template)")
    criteria: CollectionCriteriaRequest = Field(..., description="Collection criteria")
    sort_order: Optional[int] = Field(0, description="Display order")
    is_featured: bool = Field(False, description="Featured collection")

    @validator('collection_type')
    def validate_collection_type(cls, v):
        valid_types = ['curated', 'trending', 'dynamic', 'template']
        if v not in valid_types:
            raise ValueError(f'collection_type must be one of: {valid_types}')
        return v

class UpdateCollectionRequest(BaseModel):
    """Request model for updating a collection"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    criteria: Optional[CollectionCriteriaRequest] = Field(None, description="Collection criteria")
    sort_order: Optional[int] = Field(None, description="Display order")
    is_featured: Optional[bool] = Field(None, description="Featured collection")

class GenerateFromTemplateRequest(BaseModel):
    """Request model for generating collection from template"""
    template_name: str = Field(..., description="Template name")
    collection_name: str = Field(..., description="New collection name")
    description: Optional[str] = Field(None, description="Collection description")
    template_variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Template variables")

class CollectionResponse(BaseModel):
    """Response model for collection"""
    id: str = Field(..., description="Collection ID")
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    type: str = Field(..., description="Collection type")
    criteria: Dict[str, Any] = Field(..., description="Collection criteria")
    vehicle_count: int = Field(..., description="Number of vehicles in collection")
    sort_order: int = Field(..., description="Display order")
    is_featured: bool = Field(..., description="Featured status")
    is_active: bool = Field(..., description="Active status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_refreshed_at: Optional[str] = Field(None, description="Last refresh timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for admin collection endpoints
admin_collections_router = APIRouter(
    prefix="/api/admin/collections",
    tags=["Admin Collections"],
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}}
)

# Global collection engine instance
collection_engine: Optional[CollectionEngine] = None

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

def _user_id_from_header(request) -> str:
    """
    Extract user ID from request headers
    In production, this would validate JWT token and check admin role
    """
    # TODO: Implement proper JWT authentication and role checking
    # For now, return a test admin user ID
    user_id = request.headers.get('x-user-id')
    if not user_id:
        # In production, this would be an error
        # For development, use a default admin user
        user_id = "admin_user_123"
    return user_id

# ============================================================================
# API Endpoints
# ============================================================================

@admin_collections_router.post("/create", response_model=CollectionResponse)
async def create_collection(
    request: CreateCollectionRequest,
    req: Any = Depends(lambda: None)
) -> CollectionResponse:
    """
    Create a new vehicle collection

    This endpoint creates a new collection with specified criteria.
    The collection will automatically populate with matching vehicles.
    """
    try:
        # Get user ID (for audit trail)
        user_id = _user_id_from_header(req)

        # Get collection engine
        engine = await get_collection_engine()

        # Convert request criteria to engine criteria
        criteria = CollectionCriteria(**request.criteria.dict(exclude_unset=True))

        # Create collection
        collection_id = await engine.create_collection(
            name=request.name,
            description=request.description,
            collection_type=CollectionType(request.collection_type),
            criteria=criteria,
            created_by=user_id
        )

        # Get created collection
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve created collection"
            )

        # Convert to response model
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            type=collection.type.value,
            criteria=collection.criteria.__dict__,
            vehicle_count=len(collection.vehicle_ids),
            sort_order=request.sort_order,
            is_featured=request.is_featured,
            is_active=True,
            created_at=collection.created_at.isoformat(),
            updated_at=collection.updated_at.isoformat(),
            last_refreshed_at=collection.updated_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating collection"
        )

@admin_collections_router.put("/{collection_id}/update", response_model=CollectionResponse)
async def update_collection(
    collection_id: str = Path(..., description="Collection ID"),
    request: UpdateCollectionRequest = ...,
    req: Any = Depends(lambda: None)
) -> CollectionResponse:
    """
    Update an existing collection

    Updates collection details and/or criteria. If criteria are updated,
    the vehicle mappings will be regenerated.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Prepare update parameters
        update_params = {}
        criteria = None

        if request.name:
            update_params['name'] = request.name
        if request.description is not None:
            update_params['description'] = request.description
        if request.criteria:
            criteria = CollectionCriteria(**request.criteria.dict(exclude_unset=True))
            update_params['criteria'] = criteria
        if request.sort_order is not None:
            update_params['sort_order'] = request.sort_order
        if request.is_featured is not None:
            update_params['is_featured'] = request.is_featured

        # Update collection
        success = await engine.update_collection(collection_id, **update_params)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Collection not found"
            )

        # Get updated collection
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=404,
                detail="Collection not found after update"
            )

        # Convert to response model
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            type=collection.type.value,
            criteria=collection.criteria.__dict__,
            vehicle_count=len(collection.vehicle_ids),
            sort_order=collection.metadata.get('sort_order', 0),
            is_featured=collection.metadata.get('is_featured', False),
            is_active=True,
            created_at=collection.created_at.isoformat(),
            updated_at=collection.updated_at.isoformat(),
            last_refreshed_at=collection.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection {collection_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating collection"
        )

@admin_collections_router.delete("/{collection_id}/delete")
async def delete_collection(
    collection_id: str = Path(..., description="Collection ID"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Delete a collection (soft delete)

    Marks the collection as inactive. Collections are not permanently deleted
    for audit purposes.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Delete collection (soft delete)
        success = await engine.delete_collection(collection_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Collection not found"
            )

        return {
            "success": True,
            "message": f"Collection {collection_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection {collection_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting collection"
        )

@admin_collections_router.get("/list", response_model=List[CollectionResponse])
async def list_collections(
    collection_type: Optional[str] = Query(None, description="Filter by collection type"),
    featured_only: bool = Query(False, description="Show only featured collections"),
    include_inactive: bool = Query(False, description="Include inactive collections"),
    limit: int = Query(50, ge=1, le=200, description="Number of collections to return"),
    req: Any = Depends(lambda: None)
) -> List[CollectionResponse]:
    """
    List collections with optional filtering

    Returns all collections that match the specified filters.
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
            limit=limit
        )

        # Convert to response models
        response = []
        for collection in collections:
            response.append(CollectionResponse(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                type=collection.type.value,
                criteria=collection.criteria.__dict__,
                vehicle_count=len(collection.vehicle_ids),
                sort_order=collection.metadata.get('sort_order', 0),
                is_featured=collection.metadata.get('is_featured', False),
                is_active=True,
                created_at=collection.created_at.isoformat(),
                updated_at=collection.updated_at.isoformat(),
                last_refreshed_at=collection.updated_at.isoformat()
            ))

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing collections"
        )

@admin_collections_router.post("/{collection_id}/refresh")
async def refresh_collection(
    collection_id: str = Path(..., description="Collection ID"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Refresh a collection's vehicles

    Regenerates the vehicle mappings for a collection based on its criteria.
    Useful for dynamic collections or when inventory changes.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Get collection details
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=404,
                detail="Collection not found"
            )

        # Clear existing mappings
        with engine.db_conn.cursor() as cur:
            cur.execute("""
                DELETE FROM collection_vehicle_mappings
                WHERE collection_id = %s
            """, (collection_id,))

        # Regenerate mappings
        await engine._generate_collection_vehicles(collection_id, collection.criteria)

        # Update refresh timestamp
        with engine.db_conn.cursor() as cur:
            cur.execute("""
                UPDATE vehicle_collections
                SET last_refreshed_at = NOW()
                WHERE id = %s
            """, (collection_id,))

        # Get updated collection
        updated_collection = await engine.get_collection(collection_id)

        return {
            "success": True,
            "message": f"Collection {collection_id} refreshed successfully",
            "vehicle_count": len(updated_collection.vehicle_ids) if updated_collection else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing collection {collection_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while refreshing collection"
        )

@admin_collections_router.post("/generate-from-template", response_model=CollectionResponse)
async def generate_from_template(
    request: GenerateFromTemplateRequest,
    req: Any = Depends(lambda: None)
) -> CollectionResponse:
    """
    Generate a collection from a predefined template

    Creates a new collection based on a predefined template with variable substitution.
    Templates provide common collection patterns (e.g., "Electric Vehicles", "Family SUVs").
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Generate collection from template
        collection_id = await engine.generate_collection_from_template(
            template_name=request.template_name,
            collection_name=request.collection_name,
            description=request.description,
            template_variables=request.template_variables
        )

        if not collection_id:
            raise HTTPException(
                status_code=400,
                detail=f"Template not found: {request.template_name}"
            )

        # Get created collection
        collection = await engine.get_collection(collection_id)
        if not collection:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve generated collection"
            )

        # Convert to response model
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            type=collection.type.value,
            criteria=collection.criteria.__dict__,
            vehicle_count=len(collection.vehicle_ids),
            sort_order=0,
            is_featured=False,
            is_active=True,
            created_at=collection.created_at.isoformat(),
            updated_at=collection.updated_at.isoformat(),
            last_refreshed_at=collection.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating collection from template: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating collection from template"
        )

@admin_collections_router.post("/refresh-all-dynamic")
async def refresh_all_dynamic_collections(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Refresh all dynamic and template-based collections

    Regenerates all collections that are marked as dynamic or template-based.
    This is useful for automated daily updates or when inventory changes significantly.
    """
    try:
        # Get collection engine
        engine = await get_collection_engine()

        # Refresh all dynamic collections
        await engine.refresh_all_dynamic_collections()

        return {
            "success": True,
            "message": "All dynamic collections refreshed successfully"
        }

    except Exception as e:
        logger.error(f"Error refreshing dynamic collections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while refreshing collections"
        )