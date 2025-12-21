"""
Otto.AI Notifications API Endpoints

Implements Story 1.6: Vehicle Favorites and Notifications
REST API endpoints for managing user notifications and preferences

Endpoints:
- GET /api/notifications/preferences - Get user notification preferences
- PUT /api/notifications/preferences - Update user notification preferences
- GET /api/notifications/history - Get user notification history
- POST /api/notifications/test - Send test notification
"""

import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.notifications.notification_service import (
    NotificationService,
    NotificationType,
    NotificationChannel,
    UserNotificationPreferences
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for Notifications API
# ============================================================================

class NotificationPreferencesRequest(BaseModel):
    """Request model for updating notification preferences"""
    price_drop_notifications: bool = Field(True, description="Enable price drop notifications")
    availability_notifications: bool = Field(True, description="Enable availability change notifications")
    new_similar_vehicle_notifications: bool = Field(False, description="Enable new similar vehicle notifications")
    email_enabled: bool = Field(True, description="Enable email notifications")
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")
    email_address: Optional[EmailStr] = Field(None, description="Email address for notifications")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS notifications", regex=r"^\+?[\d\s\-\(\)]+$")
    min_price_drop_percentage: float = Field(5.0, ge=0, le=100, description="Minimum price drop percentage to trigger notification")
    notification_frequency: str = Field("immediate", description="Notification frequency", regex="^(immediate|hourly|daily)$")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences"""
    user_id: str = Field(..., description="User identifier")
    price_drop_notifications: bool = Field(..., description="Enable price drop notifications")
    availability_notifications: bool = Field(..., description="Enable availability change notifications")
    new_similar_vehicle_notifications: bool = Field(..., description="Enable new similar vehicle notifications")
    email_enabled: bool = Field(..., description="Enable email notifications")
    sms_enabled: bool = Field(..., description="Enable SMS notifications")
    in_app_enabled: bool = Field(..., description="Enable in-app notifications")
    email_address: Optional[str] = Field(None, description="Email address for notifications")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS notifications")
    min_price_drop_percentage: float = Field(..., description="Minimum price drop percentage to trigger notification")
    notification_frequency: str = Field(..., description="Notification frequency")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)")
    created_at: datetime = Field(..., description="When preferences were created")
    updated_at: datetime = Field(..., description="When preferences were last updated")

class NotificationHistoryResponse(BaseModel):
    """Response model for notification history"""
    id: str = Field(..., description="Notification ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    type: str = Field(..., description="Notification type")
    channel: str = Field(..., description="Delivery channel")
    subject: str = Field(..., description="Notification subject")
    content: str = Field(..., description="Notification content")
    created_at: datetime = Field(..., description="When notification was created")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    status: str = Field(..., description="Notification status")
    retry_count: int = Field(..., description="Number of retry attempts")

class NotificationHistoryListResponse(BaseModel):
    """Response model for notification history list"""
    notifications: List[NotificationHistoryResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total number of notifications")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

class TestNotificationRequest(BaseModel):
    """Request model for sending test notification"""
    type: str = Field(..., description="Notification type to test", regex="^(price_drop|availability_change|new_similar_vehicle)$")
    channel: str = Field(..., description="Channel to test", regex="^(email|sms|in_app)$")

class TestNotificationResponse(BaseModel):
    """Response model for test notification"""
    success: bool = Field(..., description="Whether test notification was sent")
    message: str = Field(..., description="Response message")
    notification_id: Optional[str] = Field(None, description="Test notification ID")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for notifications endpoints
notifications_router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications Management"],
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
)

# Global notification service instance
notification_service: Optional[NotificationService] = None

async def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    global notification_service
    if notification_service is None:
        notification_service = NotificationService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await notification_service.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize notification service"
            )

    return notification_service

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

def _preferences_to_response(preferences: UserNotificationPreferences) -> NotificationPreferencesResponse:
    """Convert UserNotificationPreferences to response model"""
    return NotificationPreferencesResponse(
        user_id=preferences.user_id,
        price_drop_notifications=preferences.price_drop_notifications,
        availability_notifications=preferences.availability_notifications,
        new_similar_vehicle_notifications=preferences.new_similar_vehicle_notifications,
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        in_app_enabled=preferences.in_app_enabled,
        email_address=preferences.email_address,
        phone_number=preferences.phone_number,
        min_price_drop_percentage=preferences.min_price_drop_percentage,
        notification_frequency=preferences.notification_frequency,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )

# ============================================================================
# API Endpoints
# ============================================================================

@notifications_router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    req: Any = Depends(lambda: None)
) -> NotificationPreferencesResponse:
    """
    Get user's notification preferences
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get notification service
        service = await get_notification_service()

        # Get preferences
        preferences = await service.get_user_notification_preferences(user_id)

        logger.info(f"Retrieved notification preferences for user {user_id}")

        return _preferences_to_response(preferences)

    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving notification preferences"
        )

@notifications_router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_request: NotificationPreferencesRequest,
    req: Any = Depends(lambda: None)
) -> NotificationPreferencesResponse:
    """
    Update user's notification preferences
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get notification service
        service = await get_notification_service()

        # Create preferences object
        preferences = UserNotificationPreferences(
            user_id=user_id,
            price_drop_notifications=preferences_request.price_drop_notifications,
            availability_notifications=preferences_request.availability_notifications,
            new_similar_vehicle_notifications=preferences_request.new_similar_vehicle_notifications,
            email_enabled=preferences_request.email_enabled,
            sms_enabled=preferences_request.sms_enabled,
            in_app_enabled=preferences_request.in_app_enabled,
            email_address=preferences_request.email_address,
            phone_number=preferences_request.phone_number,
            min_price_drop_percentage=preferences_request.min_price_drop_percentage,
            notification_frequency=preferences_request.notification_frequency,
            quiet_hours_start=preferences_request.quiet_hours_start,
            quiet_hours_end=preferences_request.quiet_hours_end
        )

        # Update preferences
        success = await service.update_user_notification_preferences(preferences)

        if success:
            logger.info(f"Updated notification preferences for user {user_id}")
            return _preferences_to_response(preferences)
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update notification preferences"
            )

    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating notification preferences"
        )

@notifications_router.get("/history", response_model=NotificationHistoryListResponse)
async def get_notification_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (sent, failed, pending)"),
    req: Any = Depends(lambda: None)
) -> NotificationHistoryListResponse:
    """
    Get user's notification history
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get notification service
        service = await get_notification_service()

        # Calculate pagination
        offset = (page - 1) * per_page

        # Get notifications
        notifications, total = await service.get_user_notifications(
            user_id=user_id,
            limit=per_page,
            offset=offset,
            status_filter=status
        )

        # Convert to response format
        notification_responses = [
            NotificationHistoryResponse(
                id=notification.id,
                vehicle_id=notification.vehicle_id,
                type=notification.type.value,
                channel=notification.channel.value,
                subject=notification.subject,
                content=notification.content,
                created_at=notification.created_at,
                sent_at=notification.sent_at,
                status=notification.status,
                retry_count=notification.retry_count
            )
            for notification in notifications
        ]

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        logger.info(f"Retrieved {len(notifications)} notifications for user {user_id}")

        return NotificationHistoryListResponse(
            notifications=notification_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving notification history"
        )

@notifications_router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    test_request: TestNotificationRequest,
    req: Any = Depends(lambda: None)
) -> TestNotificationResponse:
    """
    Send a test notification to verify configuration
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get notification service
        service = await get_notification_service()

        # Get user preferences to ensure we have a delivery method
        preferences = await service.get_user_notification_preferences(user_id)

        # Validate that the requested channel is enabled
        if test_request.channel == "email" and not preferences.email_enabled:
            return TestNotificationResponse(
                success=False,
                message="Email notifications are disabled in your preferences"
            )
        elif test_request.channel == "sms" and not preferences.sms_enabled:
            return TestNotificationResponse(
                success=False,
                message="SMS notifications are disabled in your preferences"
            )
        elif test_request.channel == "in_app" and not preferences.in_app_enabled:
            return TestNotificationResponse(
                success=False,
                message="In-app notifications are disabled in your preferences"
            )

        # Create test notification content
        if test_request.type == "price_drop":
            subject = "Test: Price Drop Notification"
            content = """
This is a test price drop notification from Otto AI.

If you receive this, your notification preferences are working correctly!
You would normally see details about a vehicle's price drop here.

Best regards,
Otto AI Vehicle Discovery
            """.strip()
        elif test_request.type == "availability_change":
            subject = "Test: Availability Change Notification"
            content = """
This is a test availability change notification from Otto AI.

If you receive this, your notification preferences are working correctly!
You would normally see details about a vehicle's availability change here.

Best regards,
Otto AI Vehicle Discovery
            """.strip()
        else:  # new_similar_vehicle
            subject = "Test: New Similar Vehicle Notification"
            content = """
This is a test new similar vehicle notification from Otto AI.

If you receive this, your notification preferences are working correctly!
You would normally see details about a new vehicle that matches your preferences here.

Best regards,
Otto AI Vehicle Discovery
            """.strip()

        # Import NotificationMessage and NotificationType locally to avoid circular imports
        from src.notifications.notification_service import NotificationMessage, NotificationChannel

        # Create test notification
        test_notification = NotificationMessage(
            user_id=user_id,
            vehicle_id="test_vehicle_123",
            type=NotificationType(test_request.type),
            channel=NotificationChannel(test_request.channel),
            subject=subject,
            content=content,
            data={"test": True}
        )

        # Send test notification
        if test_request.channel == "email":
            success = await service._send_email_notification(test_notification, preferences.email_address)
        elif test_request.channel == "sms":
            success = await service._send_sms_notification(test_notification, preferences.phone_number)
        else:  # in_app
            success = await service._send_in_app_notification(test_notification)

        if success:
            logger.info(f"✅ Test notification sent to user {user_id} via {test_request.channel}")
            return TestNotificationResponse(
                success=True,
                message=f"Test notification sent successfully via {test_request.channel}",
                notification_id=test_notification.id
            )
        else:
            return TestNotificationResponse(
                success=False,
                message=f"Failed to send test notification via {test_request.channel}"
            )

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while sending test notification"
        )

@notifications_router.get("/stats")
async def get_notification_stats(
    req: Any = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    Get notification statistics for the user
    """
    try:
        # Get user ID from request
        user_id = _user_id_from_header(req)

        # Get notification service
        service = await get_notification_service()

        # Get counts by status
        sent_notifications, _ = await service.get_user_notifications(user_id, status_filter="sent", limit=1, offset=0)
        failed_notifications, _ = await service.get_user_notifications(user_id, status_filter="failed", limit=1, offset=0)
        pending_notifications, _ = await service.get_user_notifications(user_id, status_filter="pending", limit=1, offset=0)

        # Get recent notifications (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        all_recent, _ = await service.get_user_notifications(user_id, limit=1000, offset=0)

        recent_count = len([n for n in all_recent if n.created_at >= thirty_days_ago])

        # Get user preferences
        preferences = await service.get_user_notification_preferences(user_id)

        return {
            "user_id": user_id,
            "stats": {
                "sent_count": len(sent_notifications),
                "failed_count": len(failed_notifications),
                "pending_count": len(pending_notifications),
                "last_30_days_count": recent_count
            },
            "preferences": {
                "email_enabled": preferences.email_enabled,
                "sms_enabled": preferences.sms_enabled,
                "in_app_enabled": preferences.in_app_enabled,
                "price_drop_notifications": preferences.price_drop_notifications,
                "availability_notifications": preferences.availability_notifications
            }
        }

    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving notification statistics"
        )