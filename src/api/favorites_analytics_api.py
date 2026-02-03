"""
Otto.AI Favorites Analytics API Endpoints

Implements Story 1.6: Vehicle Favorites and Notifications (Technical Notes)
REST API endpoints for favorites analytics and conversion tracking

Endpoints:
- GET /api/favorites/analytics - Get comprehensive favorites analytics
- GET /api/favorites/analytics/journey/{user_id}/{vehicle_id} - Get user's journey with a vehicle
- POST /api/favorites/analytics/track - Track favorite events
- GET /api/favorites/analytics/performance - Get performance metrics
- GET /api/favorites/analytics/ab-test/{test_name} - Get A/B test results
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analytics.favorites_analytics_service import FavoritesAnalyticsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Analytics API
# ============================================================================

class TrackEventRequest(BaseModel):
    """Request model for tracking events"""
    user_id: str = Field(..., description="User identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    event_type: str = Field(..., description="Event type (favorited, unfavorited, viewed, converted, etc.)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    session_id: Optional[str] = Field(None, description="Optional session identifier")

class TrackEventResponse(BaseModel):
    """Response model for event tracking"""
    success: bool = Field(..., description="Whether event was tracked successfully")
    message: str = Field(..., description="Response message")
    event_id: Optional[str] = Field(None, description="Event identifier")

class AnalyticsResponse(BaseModel):
    """Response model for analytics data"""
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    event_breakdown: List[Dict[str, Any]] = Field(..., description="Event type breakdown")
    daily_trends: List[Dict[str, Any]] = Field(..., description="Daily trend data")
    top_vehicles: List[Dict[str, Any]] = Field(..., description="Top performing vehicles")
    generated_at: str = Field(..., description="When analytics were generated")

class JourneyResponse(BaseModel):
    """Response model for user journey data"""
    user_id: str = Field(..., description="User identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    events: List[Dict[str, Any]] = Field(..., description="Timeline of events")
    conversion: Optional[Dict[str, Any]] = Field(None, description="Conversion information")
    journey_metrics: Dict[str, Any] = Field(..., description="Journey statistics")
    generated_at: str = Field(..., description="When journey was generated")

class ABTestReportResponse(BaseModel):
    """Response model for A/B test report"""
    test_name: str = Field(..., description="Name of the A/B test")
    period_days: int = Field(..., description="Period covered by the report")
    metrics: Dict[str, Any] = Field(..., description="Test metrics and results")
    generated_at: str = Field(..., description="When report was generated")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for analytics endpoints
analytics_router = APIRouter(
    prefix="/api/favorites/analytics",
    tags=["Favorites Analytics"],
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
)

# Global analytics service instance
analytics_service: Optional[FavoritesAnalyticsService] = None

async def get_analytics_service() -> FavoritesAnalyticsService:
    """Get analytics service instance"""
    global analytics_service
    if analytics_service is None:
        analytics_service = FavoritesAnalyticsService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await analytics_service.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize analytics service"
            )

    return analytics_service

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

def _parse_date_filter(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string filter"""
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Use ISO format."
        )

# ============================================================================
# API Endpoints
# ============================================================================

@analytics_router.get("/", response_model=AnalyticsResponse)
async def get_favorites_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    req: Any = Depends(lambda: None)
) -> AnalyticsResponse:
    """
    Get comprehensive favorites analytics

    Query Parameters:
    - user_id: Optional filter by specific user
    - vehicle_id: Optional filter by specific vehicle
    - start_date: Optional start date for analysis period
    - end_date: Optional end date for analysis period
    """
    try:
        # Parse date filters
        start_date_parsed = _parse_date_filter(start_date)
        end_date_parsed = _parse_date_filter(end_date)

        # Get analytics service
        service = await get_analytics_service()

        # Get analytics data
        analytics = await service.get_favorites_analytics(
            user_id=user_id,
            vehicle_id=vehicle_id,
            start_date=start_date_parsed,
            end_date=end_date_parsed
        )

        if not analytics:
            return AnalyticsResponse(
                summary={},
                event_breakdown=[],
                daily_trends=[],
                top_vehicles=[],
                generated_at=datetime.utcnow().isoformat()
            )

        return AnalyticsResponse(**analytics)

    except Exception as e:
        logger.error(f"Error getting favorites analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving analytics"
        )

@analytics_router.post("/track", response_model=TrackEventResponse)
async def track_favorite_event(
    request: TrackEventRequest,
    req: Any = Depends(lambda: None)
) -> TrackEventResponse:
    """
    Track a favorite-related event

    This endpoint allows tracking various user interactions with favorites,
    such as favoriting, unfavoriting, viewing from favorites, converting, etc.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Track the event
        success = await service.track_favorite_event(
            user_id=request.user_id,
            vehicle_id=request.vehicle_id,
            event_type=request.event_type,
            data=request.data,
            session_id=request.session_id
        )

        if success:
            return TrackEventResponse(
                success=True,
                message=f"Event {request.event_type} tracked successfully",
                event_id=request.session_id or "generated"
            )
        else:
            return TrackEventResponse(
                success=False,
                message="Failed to track event"
            )

    except Exception as e:
        logger.error(f"Error tracking favorite event: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while tracking event"
        )

@analytics_router.get("/journey/{user_id}/{vehicle_id}", response_model=JourneyResponse)
async def get_user_favorite_journey(
    user_id: str = Path(..., description="User identifier"),
    vehicle_id: str = Path(..., description="Vehicle identifier"),
    req: Any = Depends(lambda: None)
) -> JourneyResponse:
    """
    Get the complete journey of a user's interaction with a favorited vehicle

    This provides a timeline of all events related to a specific user-vehicle pair,
    showing how the user discovered, favorited, and potentially converted on the vehicle.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Get journey data
        journey = await service.get_user_favorite_journey(user_id, vehicle_id)

        if not journey:
            raise HTTPException(
                status_code=404,
                detail="No journey found for this user and vehicle"
            )

        return JourneyResponse(**journey)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user favorite journey: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving journey"
        )

@analytics_router.get("/performance")
async def get_vehicle_performance_metrics(
    limit: int = Query(20, ge=1, le=100, description="Number of vehicles to return"),
    sort_by: str = Query("favorites", description="Sort by: favorites, conversions, conversion_rate"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get performance metrics for vehicles based on favorites data

    This endpoint provides ranking of vehicles by various performance metrics
    related to favorites and conversions.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Get general analytics (this will include top vehicles)
        analytics = await service.get_favorites_analytics()

        # Extract and sort vehicle performance data
        top_vehicles = analytics.get('top_vehicles', [])

        # Sort based on requested criteria
        if sort_by == "conversions":
            top_vehicles.sort(key=lambda x: x.get('conversions', 0), reverse=True)
        elif sort_by == "conversion_rate":
            top_vehicles.sort(key=lambda x: x.get('conversion_rate', 0), reverse=True)
        else:  # favorites (default)
            top_vehicles.sort(key=lambda x: x.get('favorites', 0), reverse=True)

        # Limit results
        limited_vehicles = top_vehicles[:limit]

        return {
            "status": "success",
            "data": {
                "vehicles": limited_vehicles,
                "sort_by": sort_by,
                "total_analyzed": len(top_vehicles)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting vehicle performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving performance metrics"
        )

@analytics_router.get("/ab-test/{test_name}", response_model=ABTestReportResponse)
async def get_ab_test_report(
    test_name: str = Path(..., description="Name of the A/B test"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back for data"),
    req: Any = Depends(lambda: None)
) -> ABTestReportResponse:
    """
    Get A/B test effectiveness report for notification experiments

    This provides statistical analysis of different notification strategies
    to determine their effectiveness in driving conversions.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Get A/B test report
        report = await service.get_notification_effectiveness_report(test_name, days_back)

        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"No A/B test data found for test: {test_name}"
            )

        return ABTestReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving A/B test report"
        )

@analytics_router.get("/dashboard")
async def get_analytics_dashboard(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get analytics dashboard data with multiple views

    This endpoint provides a comprehensive dashboard view with multiple
    analytics perspectives for favorites and conversions.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Get data for different time periods
        end_date = datetime.utcnow()

        # Last 7 days
        week_analytics = await service.get_favorites_analytics(
            start_date=end_date - timedelta(days=7),
            end_date=end_date
        )

        # Last 30 days
        month_analytics = await service.get_favorites_analytics(
            start_date=end_date - timedelta(days=30),
            end_date=end_date
        )

        # Last 90 days
        quarter_analytics = await service.get_favorites_analytics(
            start_date=end_date - timedelta(days=90),
            end_date=end_date
        )

        dashboard_data = {
            "status": "success",
            "data": {
                "periods": {
                    "last_7_days": week_analytics.get('summary', {}),
                    "last_30_days": month_analytics.get('summary', {}),
                    "last_90_days": quarter_analytics.get('summary', {})
                },
                "trends": {
                    "daily_trends": month_analytics.get('daily_trends', [])[-30:],  # Last 30 days
                    "top_vehicles": month_analytics.get('top_vehicles', [])[:10]     # Top 10 vehicles
                },
                "insights": {
                    "most_common_events": month_analytics.get('event_breakdown', [])[:5],
                    "conversion_rate_change": self._calculate_conversion_rate_change(
                        week_analytics.get('summary', {}),
                        month_analytics.get('summary', {})
                    )
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving dashboard data"
        )

    def _calculate_conversion_rate_change(
        self,
        week_summary: Dict[str, Any],
        month_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate conversion rate change between periods"""
        try:
            week_rate = week_summary.get('overall_conversion_rate', 0)
            month_rate = month_summary.get('overall_conversion_rate', 0)

            if week_rate > 0 and month_rate > 0:
                change_percentage = ((week_rate - month_rate) / month_rate) * 100
                return {
                    "current_period": week_rate,
                    "previous_period": month_rate,
                    "change_percentage": round(change_percentage, 2),
                    "trend": "improving" if change_percentage > 0 else "declining"
                }
            else:
                return {
                    "current_period": week_rate,
                    "previous_period": month_rate,
                    "change_percentage": 0,
                    "trend": "stable"
                }

        except Exception:
            return {"error": "Unable to calculate conversion rate change"}

@analytics_router.get("/stats")
async def get_analytics_stats(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get basic analytics statistics

    This provides a quick overview of key analytics metrics.
    """
    try:
        # Get analytics service
        service = await get_analytics_service()

        # Get recent analytics (last 7 days)
        end_date = datetime.utcnow()
        analytics = await service.get_favorites_analytics(
            start_date=end_date - timedelta(days=7),
            end_date=end_date
        )

        summary = analytics.get('summary', {})

        stats = {
            "status": "success",
            "data": {
                "last_7_days": {
                    "total_favorites": summary.get('total_favorites', 0),
                    "total_conversions": summary.get('total_conversions', 0),
                    "conversion_rate": summary.get('overall_conversion_rate', 0),
                    "unique_users": summary.get('unique_users', 0)
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving analytics stats"
        )