"""
Otto.AI Filter Management API Endpoints

Additional API endpoints for Story 1-4: Implement Intelligent Vehicle Filtering with Context

Endpoints:
- GET /api/filters/suggestions - Get intelligent filter suggestions
- POST /api/filters/save - Save filter combinations
- GET /api/filters/user/{user_id} - Get user's saved filters
- GET /api/filters/popular - Get popular filter combinations
- POST /api/filters/validate - Validate and sanitize filters
"""

import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from src.search.filter_service import (
    IntelligentFilterService, SavedFilter, FilterSuggestionResponse,
    SearchContext
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Filter API
# ============================================================================

class FilterSuggestionRequest(BaseModel):
    """Request model for filter suggestions"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query for context")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    search_history: Optional[List[str]] = Field(None, description="Recent search history")
    location_hint: Optional[str] = Field(None, description="Location context")

class SaveFilterRequest(BaseModel):
    """Request model for saving filters"""
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Filter name")
    description: Optional[str] = Field(None, max_length=500, description="Filter description")
    filters: Dict[str, Any] = Field(..., description="Filter combination to save")
    is_public: bool = Field(False, description="Whether to make filter public")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Filter name cannot be empty')
        return v.strip()

class FilterValidationRequest(BaseModel):
    """Request model for filter validation"""
    filters: Dict[str, Any] = Field(..., description="Filters to validate and sanitize")

class FilterValidationResponse(BaseModel):
    """Response model for filter validation"""
    original_filters: Dict[str, Any]
    sanitized_filters: Dict[str, Any]
    validation_errors: List[str] = []
    warnings: List[str] = []
    is_valid: bool = True

class PopularFiltersResponse(BaseModel):
    """Response model for popular filters"""
    popular_filters: List[Dict[str, Any]]
    total_filters: int
    last_updated: datetime

class UserFiltersResponse(BaseModel):
    """Response model for user saved filters"""
    user_id: str
    filters: List[Dict[str, Any]]
    total_count: int

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for filter management endpoints
filter_router = APIRouter(
    prefix="/api/filters",
    tags=["Filter Management"],
    responses={404: {"description": "Not found"}}
)

# Global filter service instance
filter_service: Optional[IntelligentFilterService] = None

async def get_filter_service() -> IntelligentFilterService:
    """Get filter service instance"""
    global filter_service
    if filter_service is None:
        raise HTTPException(
            status_code=503,
            detail="Filter service not initialized"
        )
    return filter_service

# ============================================================================
# API Endpoints
# ============================================================================

@filter_router.get("/suggestions", response_model=FilterSuggestionResponse)
async def get_filter_suggestions(
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    user_preferences: Optional[str] = Query(None, description="User preferences as JSON string"),
    search_history: Optional[str] = Query(None, description="Search history as JSON string"),
    location_hint: Optional[str] = Query(None, description="Location hint"),
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """
    Get intelligent filter suggestions based on search context

    - **query**: Natural language search query
    - **user_preferences**: User preferences (optional, JSON string)
    - **search_history**: Recent search history (optional, JSON string)
    - **location_hint**: Location context (optional)

    Returns intelligent filter suggestions with confidence scores and reasoning.
    """
    try:
        # Parse JSON parameters
        user_prefs_dict = {}
        if user_preferences:
            try:
                user_prefs_dict = json.loads(user_preferences)
            except json.JSONDecodeError:
                logger.warning(f"Invalid user preferences JSON: {user_preferences}")

        search_history_list = []
        if search_history:
            try:
                search_history_list = json.loads(search_history)
                if not isinstance(search_history_list, list):
                    search_history_list = []
            except json.JSONDecodeError:
                logger.warning(f"Invalid search history JSON: {search_history}")

        # Create search context
        search_context = SearchContext(
            query=query,
            user_preferences=user_prefs_dict,
            search_history=search_history_list,
            location_hint=location_hint
        )

        # Generate suggestions
        suggestions = await service.generate_filter_suggestions(search_context)

        logger.info(f"Generated {len(suggestions.suggestions)} filter suggestions for query: {query[:50]}...")
        return suggestions

    except Exception as e:
        logger.error(f"Failed to generate filter suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate filter suggestions: {str(e)}"
        )

@filter_router.post("/suggestions", response_model=FilterSuggestionResponse)
async def post_filter_suggestions(
    request: FilterSuggestionRequest,
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """POST endpoint for filter suggestions with detailed context"""
    try:
        # Create search context
        search_context = SearchContext(
            query=request.query,
            user_preferences=request.user_preferences or {},
            search_history=request.search_history or [],
            location_hint=request.location_hint
        )

        # Generate suggestions
        suggestions = await service.generate_filter_suggestions(search_context)

        logger.info(f"Generated {len(suggestions.suggestions)} filter suggestions via POST")
        return suggestions

    except Exception as e:
        logger.error(f"Failed to generate filter suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate filter suggestions: {str(e)}"
        )

@filter_router.post("/save", response_model=SavedFilter)
async def save_filter_combination(
    request: SaveFilterRequest,
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """
    Save a filter combination for later use

    - **user_id**: User identifier
    - **name**: Filter combination name
    - **description**: Optional description
    - **filters**: Filter combination data
    - **is_public**: Whether to make filter shareable
    """
    try:
        # Validate filters before saving
        sanitized_filters = await service.validate_and_sanitize_filters(request.filters)

        # Save filter combination
        saved_filter = await service.create_saved_filter(
            user_id=request.user_id,
            name=request.name,
            filters=sanitized_filters,
            description=request.description,
            is_public=request.is_public
        )

        logger.info(f"Saved filter '{request.name}' for user {request.user_id}")
        return saved_filter

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filter data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to save filter combination: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save filter combination: {str(e)}"
        )

@filter_router.get("/user/{user_id}", response_model=UserFiltersResponse)
async def get_user_saved_filters(
    user_id: str = Path(..., description="User identifier"),
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """
    Get all saved filter combinations for a user

    - **user_id**: User identifier
    """
    try:
        # Get user's saved filters
        user_filters = await service.get_user_saved_filters(user_id)

        # Convert to dict format for response
        filter_dicts = [filter.dict() for filter in user_filters]

        response = UserFiltersResponse(
            user_id=user_id,
            filters=filter_dicts,
            total_count=len(filter_dicts)
        )

        logger.info(f"Retrieved {len(filter_dicts)} saved filters for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to get user saved filters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user saved filters: {str(e)}"
        )

@filter_router.get("/popular", response_model=PopularFiltersResponse)
async def get_popular_filters(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of popular filters"),
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """
    Get popular filter combinations

    - **limit**: Maximum number of filters to return
    """
    try:
        # Get popular filters from service
        popular_filters_data = await service._get_popular_filters()

        # Limit results
        limited_filters = popular_filters_data[:limit]

        response = PopularFiltersResponse(
            popular_filters=limited_filters,
            total_filters=len(limited_filters),
            last_updated=datetime.now()
        )

        logger.info(f"Retrieved {len(limited_filters)} popular filters")
        return response

    except Exception as e:
        logger.error(f"Failed to get popular filters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get popular filters: {str(e)}"
        )

@filter_router.post("/validate", response_model=FilterValidationResponse)
async def validate_filters(
    request: FilterValidationRequest,
    service: IntelligentFilterService = Depends(get_filter_service)
):
    """
    Validate and sanitize filter parameters

    - **filters**: Filter parameters to validate
    """
    try:
        original_filters = request.filters.copy()

        # Validate and sanitize filters
        sanitized_filters = await service.validate_and_sanitize_filters(request.filters)

        # Compare original vs sanitized to identify changes
        validation_errors = []
        warnings = []

        # Check for specific validation issues
        if 'price_min' in original_filters and 'price_max' in original_filters:
            orig_min = float(original_filters['price_min'])
            orig_max = float(original_filters['price_max'])
            if orig_min > orig_max:
                warnings.append("Price range values were swapped (min > max)")

        if 'year_min' in original_filters and 'year_max' in original_filters:
            orig_min = int(original_filters['year_min'])
            orig_max = int(original_filters['year_max'])
            if orig_min > orig_max:
                warnings.append("Year range values were swapped (min > max)")

        # Check current year validation
        current_year = datetime.now().year
        if 'year_max' in sanitized_filters and sanitized_filters['year_max'] > current_year:
            warnings.append(f"Year maximum adjusted to current year ({current_year})")

        is_valid = len(validation_errors) == 0

        response = FilterValidationResponse(
            original_filters=original_filters,
            sanitized_filters=sanitized_filters,
            validation_errors=validation_errors,
            warnings=warnings,
            is_valid=is_valid
        )

        logger.info(f"Validated filters: {len(warnings)} warnings, {len(validation_errors)} errors")
        return response

    except ValueError as e:
        # Handle validation errors
        response = FilterValidationResponse(
            original_filters=request.filters,
            sanitized_filters={},
            validation_errors=[str(e)],
            warnings=[],
            is_valid=False
        )
        return response

    except Exception as e:
        logger.error(f"Failed to validate filters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate filters: {str(e)}"
        )

@filter_router.get("/sample")
async def get_sample_filters():
    """Get sample filter combinations for testing and demonstration"""
    return {
        "sample_filters": [
            {
                "name": "Family SUV Under $40k",
                "description": "Spacious SUVs for families on a budget",
                "filters": {
                    "vehicle_type": "SUV",
                    "price_max": 40000,
                    "features": ["third row seating", "cargo space"]
                }
            },
            {
                "name": "Luxury Executive",
                "description": "Premium vehicles for professionals",
                "filters": {
                    "make": ["BMW", "Mercedes-Benz", "Audi", "Lexus"],
                    "price_min": 50000,
                    "features": ["leather seats", "premium audio", "navigation"]
                }
            },
            {
                "name": "Eco-Friendly Commuter",
                "description": "Environmentally conscious daily driver",
                "filters": {
                    "fuel_type": ["Electric", "Hybrid"],
                    "price_max": 35000,
                    "vehicle_type": ["Sedan", "Hatchback"]
                }
            },
            {
                "name": "Work Truck",
                "description": "Capable truck for work and hauling",
                "filters": {
                    "vehicle_type": "Truck",
                    "features": ["towing capacity", "four-wheel drive"],
                    "year_min": 2015
                }
            },
            {
                "name": "Sports Car Enthusiast",
                "description": "High-performance driving experience",
                "filters": {
                    "vehicle_type": ["Coupe", "Convertible"],
                    "features": ["performance", "sport mode"],
                    "price_min": 30000
                }
            }
        ],
        "usage_notes": [
            "Use these filters with the semantic search API endpoints",
            "Combine with natural language queries for best results",
            "Save frequently used filter combinations for quick access",
            "Popular filters are automatically suggested based on usage patterns"
        ]
    }

@filter_router.get("/")
async def get_filter_info():
    """Get filter management API information"""
    return {
        "service": "Otto.AI Filter Management API",
        "version": "1.0.0",
        "features": [
            "Intelligent filter suggestions based on search context",
            "Save and manage personal filter combinations",
            "Popular filter recommendations",
            "Filter validation and sanitization",
            "A/B testing support for filter optimization"
        ],
        "endpoints": {
            "suggestions": "/api/filters/suggestions",
            "save": "/api/filters/save",
            "user_filters": "/api/filters/user/{user_id}",
            "popular": "/api/filters/popular",
            "validate": "/api/filters/validate",
            "sample": "/api/filters/sample"
        },
        "integration": {
            "semantic_search": "/api/search/semantic",
            "documentation": "/docs",
            "health_check": "/health"
        }
    }

# ============================================================================
# Error Handlers
# ============================================================================

@filter_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions in filter API"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@filter_router.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions in filter API"""
    logger.error(f"Unhandled exception in filter API: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred in filter service",
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# Initialization Function
# ============================================================================

async def initialize_filter_api(supabase_url: str, supabase_key: str, redis_url: Optional[str] = None) -> bool:
    """Initialize the filter management API"""
    global filter_service

    try:
        logger.info("🚀 Initializing Filter Management API...")

        filter_service = IntelligentFilterService()
        success = await filter_service.initialize(supabase_url, supabase_key, redis_url)

        if success:
            logger.info("✅ Filter Management API initialized successfully")
        else:
            logger.error("❌ Failed to initialize Filter Management API")

        return success

    except Exception as e:
        logger.error(f"❌ Filter API initialization failed: {e}")
        return False

def get_filter_router() -> APIRouter:
    """Get the filter router for FastAPI app inclusion"""
    return filter_router