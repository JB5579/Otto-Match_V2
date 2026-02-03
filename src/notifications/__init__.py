"""
Otto.AI Notifications Module

Implements Story 1.6: Vehicle Favorites and Notifications
Multi-channel notification system for price drops and availability changes
"""

from .notification_service import (
    NotificationService,
    NotificationType,
    NotificationChannel,
    NotificationMessage,
    UserNotificationPreferences
)

__all__ = [
    'NotificationService',
    'NotificationType',
    'NotificationChannel',
    'NotificationMessage',
    'UserNotificationPreferences'
]