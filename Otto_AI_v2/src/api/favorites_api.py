"""
Otto.AI Favorites API Endpoints

Implements Story 1.6: Vehicle Favorites and Notifications
REST API endpoints for managing user favorites

Endpoints:
- POST /api/favorites/add - Add vehicle to favorites
- DELETE /api/favorites/remove/{vehicle_id} - Remove vehicle from favorites
- GET /api/favorites/list - Get paginated user favorites
"""

import os
import time
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

from src.user.favorites_service import FavoritesService, FavoriteItem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Favorites API
# ============================================================================

class AddFavoriteRequest(BaseModel):
    """Request model for adding to favorites"""
    vehicle_id: str = Field(..., description="Vehicle identifier to add to favorites")

class AddFavoriteResponse(BaseModel):
    """Response model for add favorite"""
    success: bool = Field(..., description="Whether vehicle was added to favorites")
    message: str = Field(..., description="Response message")
    already_favorited: bool = Field(False, description="True if vehicle was already in favorites")

class FavoriteResponse(BaseModel):
    """Response model for favorite item"""
    id: str = Field(..., description="Favorite entry ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    created_at: datetime = Field(..., description="When vehicle was added to favorites")
    vehicle_make: Optional[str] = Field(None, description="Vehicle manufacturer")
    vehicle_model: Optional[str] = Field(None, description="Vehicle model")
    vehicle_year: Optional[int] = Field(None, description="Vehicle year")
    price: Optional[float] = Field(None, description="Vehicle price")
    vehicle_image: Optional[str] = Field(None, description="Vehicle image URL")
    vehicle_url: Optional[str] = Field(None, description="Vehicle details URL")

class FavoritesListResponse(BaseModel):
    """Response model for favorites list"""
    favorites: List[FavoriteResponse] = Field(..., description="List of favorite vehicles")
    total: int = Field(..., description="Total number of favorites")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

class RemoveFavoriteResponse(BaseModel):
    """Response model for remove favorite"""
    success: bool = Field(..., description="Whether vehicle was removed from favorites")
    message: str = Field(..., description="Response message")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for favorites endpoints
favorites_router = APIRouter(
    prefix="/api/favorites",
    tags=["Favorites Management"],
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
)

# Global favorites service instance
favorites_service: Optional[FavoritesService] = None

async def get_favorites_service() -> FavoritesService:
    """Get favorites service instance"""
    global favorites_service
    if favorites_service is None:
        favorites_service = FavoritesService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await favorites_service.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize favorites service"
            )

    return favorites_service

# ============================================================================
# Helper Functions
# ============================================================================

def _user_id_from_header(request) -> str:
    """
    Extract user ID from request headers
    In production, this would validate JWT token
    """
    # TODO: Implement proper JWT authentication
    # For now, return a test user ID
    user_id = request.headers.get('x-user-id')
    if not user_id:
        # In production, this would be an error
        # For development, use a default user
        user_id = "test_user_123"
    return user_id

def _favorite_item_to_response(item: FavoriteItem) -> FavoriteResponse:
    """Convert FavoriteItem to FavoriteResponse"""
    return FavoriteResponse(
        id=item.id,
        vehicle_id=item.vehicle_id,
        created_at=item.created_at,
        vehicle_make=item.vehicle_make,
        vehicle_model=item.vehicle_model,
        vehicle_year=item.vehicle_year,
        price=item.price,
        vehicle_image=item.vehicle_image,
        vehicle_url=item.vehicle_url
    )

# ============================================================================
# API Endpoints
# ============================================================================

@favorites_router.post("/add", response_model=AddFavoriteResponse)
async def add_to_favorites(
    request: AddFavoriteRequest,
    req: Any = Depends(lambda: None)
) -> AddFavoriteResponse:
    """
    Add vehicle to user favorites
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get favorites service
        service = await get_favorites_service()

        # Check if already favorited
        already_favorited = await service.favorite_exists(user_id, request.vehicle_id)

        # Add to favorites
        success = await service.add_to_favorites(user_id, request.vehicle_id)

        if success:
            logger.info(f"Added vehicle {request.vehicle_id} to favorites for user {user_id}")
            return AddFavoriteResponse(
                success=True,
                message="Vehicle added to favorites successfully",
                already_favorited=False
            )
        elif already_favorited:
            return AddFavoriteResponse(
                success=False,
                message="Vehicle is already in your favorites",
                already_favorited=True
            )
        else:
            return AddFavoriteResponse(
                success=False,
                message="Failed to add vehicle to favorites",
                already_favorited=False
            )

    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while adding to favorites"
        )

@favorites_router.delete("/remove/{vehicle_id}", response_model=RemoveFavoriteResponse)
async def remove_from_favorites(
    vehicle_id: str = Path(..., description="Vehicle ID to remove from favorites"),
    req: Any = Depends(lambda: None)
) -> RemoveFavoriteResponse:
    """
    Remove vehicle from user favorites
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get favorites service
        service = await get_favorites_service()

        # Remove from favorites
        success = await service.remove_from_favorites(user_id, vehicle_id)

        if success:
            logger.info(f"Removed vehicle {vehicle_id} from favorites for user {user_id}")
            return RemoveFavoriteResponse(
                success=True,
                message="Vehicle removed from favorites successfully"
            )
        else:
            return RemoveFavoriteResponse(
                success=False,
                message="Vehicle not found in your favorites"
            )

    except Exception as e:
        logger.error(f"Error removing from favorites: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while removing from favorites"
        )

@favorites_router.get("/list", response_model=FavoritesListResponse)
async def get_user_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    req: Any = Depends(lambda: None)
) -> FavoritesListResponse:
    """
    Get paginated list of user's favorite vehicles
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get favorites service
        service = await get_favorites_service()

        # Calculate pagination
        offset = (page - 1) * per_page

        # Get favorites
        favorites, total = await service.get_user_favorites(
            user_id=user_id,
            limit=per_page,
            offset=offset
        )

        # Convert to response format
        favorite_responses = [_favorite_item_to_response(f) for f in favorites]

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        logger.info(f"Retrieved {len(favorites)} favorites for user {user_id}")

        return FavoritesListResponse(
            favorites=favorite_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error getting favorites list: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving favorites"
        )

@favorites_router.get("/count")
async def get_favorites_count(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get total count of user's favorites
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get favorites service
        service = await get_favorites_service()

        # Get count
        count = await service.get_favorite_count(user_id)

        return {
            "count": count,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error getting favorites count: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving favorites count"
        )

@favorites_router.get("/check/{vehicle_id}")
async def check_favorite_status(
    vehicle_id: str = Path(..., description="Vehicle ID to check"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Check if a vehicle is in user's favorites
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get favorites service
        service = await get_favorites_service()

        # Check if favorited
        is_favorited = await service.favorite_exists(user_id, vehicle_id)

        return {
            "vehicle_id": vehicle_id,
            "user_id": user_id,
            "is_favorited": is_favorited
        }

    except Exception as e:
        logger.error(f"Error checking favorite status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking favorite status"
        )