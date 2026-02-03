"""
Otto.AI Collections Analytics API Endpoints

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Public API endpoints for collection analytics and insights

Endpoints:
- GET /api/analytics/dashboard - Get analytics dashboard data
- GET /api/analytics/collections/{id}/insights - Get collection insights
- GET /api/analytics/collections/top - Get top performing collections
- POST /api/analytics/track - Track analytics event
- GET /api/analytics/export - Export analytics report
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.collections.analytics_dashboard import (
    CollectionsAnalyticsDashboard,
    MetricType,
    TimePeriod,
    CollectionInsights
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Analytics API
# ============================================================================

class TrackEventRequest(BaseModel):
    """Request model for tracking analytics events"""
    event_type: str = Field(..., description="Event type (view, click, share, conversion)")
    collection_id: str = Field(..., description="Collection ID")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event metadata")

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = ['view', 'click', 'share', 'conversion']
        if v not in valid_types:
            raise ValueError(f'event_type must be one of: {valid_types}')
        return v

class DashboardRequest(BaseModel):
    """Request model for dashboard data"""
    time_period: Optional[str] = Field("day", description="Time period (hour, day, week, month, quarter, year)")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional filters")

    @validator('time_period')
    def validate_time_period(cls, v):
        valid_periods = ['hour', 'day', 'week', 'month', 'quarter', 'year']
        if v not in valid_periods:
            raise ValueError(f'time_period must be one of: {valid_periods}')
        return v

class TopCollectionsRequest(BaseModel):
    """Request model for top collections"""
    metric_type: Optional[str] = Field("views", description="Metric to sort by")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of collections")
    days_back: int = Field(7, ge=1, le=365, description="Number of days to analyze")

    @validator('metric_type')
    def validate_metric_type(cls, v):
        valid_metrics = ['views', 'clicks', 'shares', 'conversions', 'engagement_rate']
        if v not in valid_metrics:
            raise ValueError(f'metric_type must be one of: {valid_metrics}')
        return v

class ExportRequest(BaseModel):
    """Request model for exporting analytics"""
    format_type: str = Field("csv", description="Export format (csv, json, excel)")
    collection_ids: Optional[List[str]] = Field(None, description="Specific collections to include")
    days_back: int = Field(30, ge=1, le=365, description="Number of days to include")

    @validator('format_type')
    def validate_format_type(cls, v):
        valid_formats = ['csv', 'json', 'excel']
        if v not in valid_formats:
            raise ValueError(f'format_type must be one of: {valid_formats}')
        return v

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for analytics endpoints
analytics_router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
    responses={404: {"description": "Not found"}, 500: {"description": "Internal server error"}}
)

# Global analytics dashboard instance
analytics_dashboard: Optional[CollectionsAnalyticsDashboard] = None

async def get_analytics_dashboard() -> CollectionsAnalyticsDashboard:
    """Get analytics dashboard instance"""
    global analytics_dashboard
    if analytics_dashboard is None:
        analytics_dashboard = CollectionsAnalyticsDashboard()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await analytics_dashboard.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize analytics dashboard"
            )

    return analytics_dashboard

def _user_id_from_header(request) -> str:
    """
    Extract user ID from request headers
    In production, this would validate JWT token
    """
    # TODO: Implement proper JWT authentication
    user_id = request.headers.get('x-user-id')
    if not user_id:
        # Generate anonymous user ID for tracking
        user_id = f"anonymous_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return user_id

# ============================================================================
# API Endpoints
# ============================================================================

@analytics_router.post("/track")
async def track_event(
    request: TrackEventRequest,
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Track an analytics event

    Records user interactions with collections for analytics.
    Events include views, clicks, shares, and conversions.
    """
    try:
        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Enhance metadata
        metadata = request.metadata.copy()
        metadata['timestamp'] = datetime.utcnow().isoformat()
        metadata['user_agent'] = req.headers.get('user-agent')
        metadata['ip_address'] = req.client.host if req else None

        # Track event
        await dashboard.track_event(
            event_type=request.event_type,
            collection_id=request.collection_id,
            user_id=request.user_id,
            metadata=metadata
        )

        return {
            "success": True,
            "message": "Event tracked successfully"
        }

    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while tracking event"
        )

@analytics_router.get("/dashboard")
async def get_dashboard_data(
    time_period: str = Query("day", description="Time period (hour, day, week, month, quarter, year)"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get analytics dashboard data

    Returns comprehensive dashboard data with widgets for:
    - Overview metrics
    - Collection performance table
    - Engagement trends
    - Conversion funnel
    - A/B test results
    - User demographics
    """
    try:
        # Validate time period
        try:
            period = TimePeriod(time_period)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time period: {time_period}"
            )

        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Get dashboard data
        dashboard_data = await dashboard.get_dashboard_data(
            time_period=period,
            filters={}  # TODO: Implement filters based on user permissions
        )

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting dashboard data"
        )

@analytics_router.get("/collections/{collection_id}/insights")
async def get_collection_insights(
    collection_id: str = Path(..., description="Collection ID"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get detailed insights for a specific collection

    Returns comprehensive analytics including:
    - Engagement metrics
    - Performance trends
    - User demographics
    - Optimization recommendations
    - Trending score
    """
    try:
        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Get collection insights
        insights = await dashboard.get_collection_insights(
            collection_id=collection_id,
            days_back=days_back
        )

        if not insights:
            raise HTTPException(
                status_code=404,
                detail="Collection not found or no analytics data available"
            )

        # Convert to response format
        return {
            "collection_id": insights.collection_id,
            "collection_name": insights.collection_name,
            "metrics": {
                "total_views": insights.total_views,
                "total_clicks": insights.total_clicks,
                "total_shares": insights.total_shares,
                "total_conversions": insights.total_conversions,
                "engagement_rate": round(insights.engagement_rate * 100, 2),
                "click_through_rate": round(insights.click_through_rate * 100, 2),
                "conversion_rate": round(insights.conversion_rate * 100, 2),
                "average_time_viewed": round(insights.average_time_viewed, 2),
                "bounce_rate": round(insights.bounce_rate * 100, 2),
                "trending_score": round(insights.trending_score, 2)
            },
            "performance": {
                "trend": insights.performance_trend,
                "last_updated": insights.last_updated.isoformat()
            },
            "demographics": insights.user_demographics,
            "recommendations": insights.recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection insights: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting collection insights"
        )

@analytics_router.get("/collections/top")
async def get_top_collections(
    metric_type: str = Query("views", description="Metric to sort by"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of collections"),
    days_back: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get top performing collections by metric

    Returns a ranked list of collections based on the specified metric.
    Useful for identifying best-performing content.
    """
    try:
        # Validate metric type
        try:
            metric = MetricType(metric_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type: {metric_type}"
            )

        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Get top collections
        top_collections = await dashboard.get_top_collections(
            metric_type=metric,
            limit=limit,
            days_back=days_back
        )

        return {
            "metric": metric_type,
            "period_days": days_back,
            "collections": top_collections
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top collections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting top collections"
        )

@analytics_router.get("/export")
async def export_analytics_report(
    format_type: str = Query("csv", description="Export format (csv, json, excel)"),
    collection_ids: Optional[str] = Query(None, description="Comma-separated collection IDs"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to include"),
    req: Any = Depends(lambda: None)
) -> FileResponse:
    """
    Export analytics report

    Generates and downloads a comprehensive analytics report.
    Supports CSV, JSON, and Excel formats.
    """
    try:
        # Validate format type
        valid_formats = ['csv', 'json', 'excel']
        if format_type not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format type: {format_type}"
            )

        # Parse collection IDs
        collection_id_list = None
        if collection_ids:
            collection_id_list = [id.strip() for id in collection_ids.split(',') if id.strip()]

        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Export report
        export_result = await dashboard.export_analytics_report(
            format_type=format_type,
            collection_ids=collection_id_list,
            days_back=days_back
        )

        # Determine if it's a file path or data
        if format_type == "json":
            # Return JSON data directly
            return JSONResponse(
                content=export_result,
                headers={
                    "Content-Disposition": f"attachment; filename=collection_analytics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        else:
            # Return file
            return FileResponse(
                path=export_result,
                filename=os.path.basename(export_result),
                media_type='application/octet-stream'
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while exporting report"
        )

@analytics_router.get("/metrics/summary")
async def get_metrics_summary(
    days_back: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get metrics summary for all collections

    Returns aggregated metrics across all collections for the specified period.
    Useful for high-level overview and reporting.
    """
    try:
        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # Get summary metrics
        with dashboard.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    COUNT(DISTINCT vc.id) as total_collections,
                    COUNT(CASE WHEN ca.event_type = 'view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN ca.event_type = 'click' THEN 1 END) as total_clicks,
                    COUNT(CASE WHEN ca.event_type = 'conversion' THEN 1 END) as total_conversions,
                    COUNT(CASE WHEN ca.event_type = 'share' THEN 1 END) as total_shares,
                    COUNT(DISTINCT ca.user_id) as unique_users,
                    AVG(CASE WHEN ca.event_type = 'view' THEN 1 ELSE 0 END) as avg_views_per_collection
                FROM vehicle_collections vc
                LEFT JOIN collection_analytics ca ON vc.id = ca.collection_id
                WHERE vc.is_active = TRUE
                AND (ca.created_at >= %s OR ca.created_at IS NULL)
            """, (start_date,))

            summary = cur.fetchone() or {}

        # Calculate rates
        if summary.get('total_views', 0) > 0:
            summary['click_through_rate'] = round(
                (summary.get('total_clicks', 0) / summary['total_views']) * 100, 2
            )
            summary['conversion_rate'] = round(
                (summary.get('total_conversions', 0) / summary['total_views']) * 100, 2
            )
            summary['engagement_rate'] = round(
                ((summary.get('total_clicks', 0) + summary.get('total_shares', 0)) / summary['total_views']) * 100, 2
            )
        else:
            summary['click_through_rate'] = 0
            summary['conversion_rate'] = 0
            summary['engagement_rate'] = 0

        return {
            "period_days": days_back,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting metrics summary"
        )

@analytics_router.get("/realtime")
async def get_realtime_metrics(
    collection_id: Optional[str] = Query(None, description="Specific collection ID"),
    window_minutes: int = Query(5, ge=1, le=60, description="Time window in minutes"),
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get real-time metrics

    Returns live metrics for the recent time window.
    Useful for monitoring current activity and trends.
    """
    try:
        # Get analytics dashboard
        dashboard = await get_analytics_dashboard()

        # Calculate time window
        start_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Build query
        query = """
            SELECT
                DATE_TRUNC('minute', created_at) as minute,
                event_type,
                COUNT(*) as count
            FROM collection_analytics
            WHERE created_at >= %s
        """

        params = [start_time]

        if collection_id:
            query += " AND collection_id = %s"
            params.append(collection_id)

        query += " GROUP BY DATE_TRUNC('minute', created_at), event_type ORDER BY minute"

        # Get real-time data
        with dashboard.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            data = cur.fetchall()

        # Organize by minute
        metrics_by_minute = {}
        for row in data:
            minute = row['minute'].strftime('%Y-%m-%d %H:%M')
            if minute not in metrics_by_minute:
                metrics_by_minute[minute] = {"views": 0, "clicks": 0, "shares": 0, "conversions": 0}
            metrics_by_minute[minute][row['event_type'] + 's'] = row['count']

        return {
            "collection_id": collection_id,
            "window_minutes": window_minutes,
            "metrics": metrics_by_minute,
            "current_minute": datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting real-time metrics"
        )