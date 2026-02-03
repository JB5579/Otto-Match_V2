"""
Tests for Otto.AI Notification Service

Implements Story 1.6: Vehicle Favorites and Notifications
Comprehensive test suite for notification functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.notifications.notification_service import (
    NotificationService,
    NotificationType,
    NotificationChannel,
    NotificationMessage,
    UserNotificationPreferences
)

class TestNotificationService:
    """Test suite for NotificationService"""

    @pytest.fixture
    async def notification_service(self):
        """Create notification service fixture"""
        service = NotificationService()

        # Mock database connection
        service.db_conn = Mock()
        service.db_conn.cursor = Mock()
        service.db_conn.commit = Mock()
        service.db_conn.rollback = Mock()

        yield service

        await service.close()

    @pytest.fixture
    def sample_preferences(self):
        """Create sample user preferences"""
        return UserNotificationPreferences(
            user_id="test_user_123",
            price_drop_notifications=True,
            availability_notifications=True,
            new_similar_vehicle_notifications=False,
            email_enabled=True,
            sms_enabled=False,
            in_app_enabled=True,
            email_address="test@example.com",
            phone_number="+1234567890",
            min_price_drop_percentage=5.0,
            notification_frequency="immediate",
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )

    @pytest.fixture
    def sample_vehicle_details(self):
        """Create sample vehicle details"""
        return {
            "id": "vehicle_123",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "price": 25000.0,
            "url": "https://otto.ai/vehicles/123"
        }

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization"""
        service = NotificationService()

        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_DB_PASSWORD': 'test_password'
        }):
            with patch('src.notifications.notification_service.psycopg.connect') as mock_connect:
                mock_conn = Mock()
                mock_connect.return_value = mock_conn

                result = await service.initialize('https://test.supabase.co', 'test_key')

                assert result is True
                mock_connect.assert_called_once()
                assert service.db_conn == mock_conn

    @pytest.mark.asyncio
    async def test_send_price_drop_notification_success(
        self,
        notification_service,
        sample_preferences,
        sample_vehicle_details
    ):
        """Test successful price drop notification"""
        # Mock database operations
        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            sample_preferences.user_id,
            True,  # price_drop_notifications
            True,  # availability_notifications
            False, # new_similar_vehicle_notifications
            True,  # email_enabled
            False, # sms_enabled
            True,  # in_app_enabled
            sample_preferences.email_address,
            sample_preferences.phone_number,
            sample_preferences.min_price_drop_percentage,
            sample_preferences.notification_frequency,
            None,  # quiet_hours_start
            None   # quiet_hours_end
        )

        # Mock email sending
        with patch.object(notification_service, '_send_notification_channels', return_value=True):
            result = await notification_service.send_price_drop_notification(
                user_id=sample_preferences.user_id,
                vehicle_id="vehicle_123",
                old_price=30000.0,
                new_price=27000.0,  # 10% drop
                vehicle_details=sample_vehicle_details
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_price_drop_notification_below_threshold(
        self,
        notification_service,
        sample_preferences,
        sample_vehicle_details
    ):
        """Test price drop notification below user threshold"""
        # Mock database operations
        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            sample_preferences.user_id,
            True,  # price_drop_notifications
            True,  # availability_notifications
            False, # new_similar_vehicle_notifications
            True,  # email_enabled
            False, # sms_enabled
            True,  # in_app_enabled
            sample_preferences.email_address,
            sample_preferences.phone_number,
            sample_preferences.min_price_drop_percentage,
            sample_preferences.notification_frequency,
            None,  # quiet_hours_start
            None   # quiet_hours_end
        )

        result = await notification_service.send_price_drop_notification(
            user_id=sample_preferences.user_id,
            vehicle_id="vehicle_123",
            old_price=30000.0,
            new_price=28500.0,  # 5% drop (exactly threshold)
            vehicle_details=sample_vehicle_details
        )

        # Should be False because it's exactly at threshold, needs to be > threshold
        assert result is False

    @pytest.mark.asyncio
    async def test_send_price_drop_notification_disabled(
        self,
        notification_service,
        sample_preferences,
        sample_vehicle_details
    ):
        """Test price drop notification when user has disabled them"""
        # Mock preferences with price drop notifications disabled
        disabled_preferences = sample_preferences
        disabled_preferences.price_drop_notifications = False

        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            disabled_preferences.user_id,
            False, # price_drop_notifications disabled
            True,  # availability_notifications
            False, # new_similar_vehicle_notifications
            True,  # email_enabled
            False, # sms_enabled
            True,  # in_app_enabled
            disabled_preferences.email_address,
            disabled_preferences.phone_number,
            disabled_preferences.min_price_drop_percentage,
            disabled_preferences.notification_frequency,
            None,  # quiet_hours_start
            None   # quiet_hours_end
        )

        result = await notification_service.send_price_drop_notification(
            user_id=disabled_preferences.user_id,
            vehicle_id="vehicle_123",
            old_price=30000.0,
            new_price=27000.0,  # 10% drop
            vehicle_details=sample_vehicle_details
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_availability_change_notification_success(
        self,
        notification_service,
        sample_preferences,
        sample_vehicle_details
    ):
        """Test successful availability change notification"""
        # Mock database operations
        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            sample_preferences.user_id,
            True,  # price_drop_notifications
            True,  # availability_notifications
            False, # new_similar_vehicle_notifications
            True,  # email_enabled
            False, # sms_enabled
            True,  # in_app_enabled
            sample_preferences.email_address,
            sample_preferences.phone_number,
            sample_preferences.min_price_drop_percentage,
            sample_preferences.notification_frequency,
            None,  # quiet_hours_start
            None   # quiet_hours_end
        )

        # Mock email sending
        with patch.object(notification_service, '_send_notification_channels', return_value=True):
            result = await notification_service.send_availability_change_notification(
                user_id=sample_preferences.user_id,
                vehicle_id="vehicle_123",
                new_status="sold",
                vehicle_details=sample_vehicle_details
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_availability_change_notification_disabled(
        self,
        notification_service,
        sample_preferences,
        sample_vehicle_details
    ):
        """Test availability change notification when user has disabled them"""
        # Mock preferences with availability notifications disabled
        disabled_preferences = sample_preferences
        disabled_preferences.availability_notifications = False

        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
            disabled_preferences.user_id,
            True,  # price_drop_notifications
            False, # availability_notifications disabled
            False, # new_similar_vehicle_notifications
            True,  # email_enabled
            False, # sms_enabled
            True,  # in_app_enabled
            disabled_preferences.email_address,
            disabled_preferences.phone_number,
            disabled_preferences.min_price_drop_percentage,
            disabled_preferences.notification_frequency,
            None,  # quiet_hours_start
            None   # quiet_hours_end
        )

        result = await notification_service.send_availability_change_notification(
            user_id=disabled_preferences.user_id,
            vehicle_id="vehicle_123",
            new_status="sold",
            vehicle_details=sample_vehicle_details
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_notification_preferences_existing(
        self,
        notification_service,
        sample_preferences
    ):
        """Test getting existing user notification preferences"""
        # Mock database response
        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = {
            'user_id': sample_preferences.user_id,
            'price_drop_notifications': sample_preferences.price_drop_notifications,
            'availability_notifications': sample_preferences.availability_notifications,
            'new_similar_vehicle_notifications': sample_preferences.new_similar_vehicle_notifications,
            'email_enabled': sample_preferences.email_enabled,
            'sms_enabled': sample_preferences.sms_enabled,
            'in_app_enabled': sample_preferences.in_app_enabled,
            'email_address': sample_preferences.email_address,
            'phone_number': sample_preferences.phone_number,
            'min_price_drop_percentage': sample_preferences.min_price_drop_percentage,
            'notification_frequency': sample_preferences.notification_frequency,
            'quiet_hours_start': datetime.strptime(sample_preferences.quiet_hours_start, "%H:%M").time(),
            'quiet_hours_end': datetime.strptime(sample_preferences.quiet_hours_end, "%H:%M").time(),
            'created_at': sample_preferences.created_at,
            'updated_at': sample_preferences.updated_at
        }

        preferences = await notification_service.get_user_notification_preferences(sample_preferences.user_id)

        assert preferences.user_id == sample_preferences.user_id
        assert preferences.price_drop_notifications == sample_preferences.price_drop_notifications
        assert preferences.availability_notifications == sample_preferences.availability_notifications
        assert preferences.email_enabled == sample_preferences.email_enabled

    @pytest.mark.asyncio
    async def test_get_user_notification_preferences_default(
        self,
        notification_service
    ):
        """Test getting default user notification preferences when none exist"""
        # Mock empty database response
        notification_service.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None

        preferences = await notification_service.get_user_notification_preferences("new_user_456")

        assert preferences.user_id == "new_user_456"
        assert preferences.price_drop_notifications is True  # Default value
        assert preferences.availability_notifications is True  # Default value
        assert preferences.email_enabled is True  # Default value

    @pytest.mark.asyncio
    async def test_update_user_notification_preferences(
        self,
        notification_service,
        sample_preferences
    ):
        """Test updating user notification preferences"""
        # Mock successful database operation
        notification_service.db_conn.cursor.return_value.__enter__ = Mock()
        notification_service.db_conn.cursor.return_value.__exit__ = Mock()

        result = await notification_service.update_user_notification_preferences(sample_preferences)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_notifications(
        self,
        notification_service
    ):
        """Test getting user notifications"""
        # Mock database response
        mock_rows = [
            {
                'id': 'notif_1',
                'user_id': 'test_user_123',
                'vehicle_id': 'vehicle_1',
                'type': 'price_drop',
                'channel': 'email',
                'subject': 'Price Drop Alert',
                'content': 'Vehicle price dropped',
                'data': {},
                'created_at': datetime.utcnow(),
                'sent_at': datetime.utcnow(),
                'status': 'sent',
                'retry_count': 0,
                'max_retries': 3
            },
            {
                'id': 'notif_2',
                'user_id': 'test_user_123',
                'vehicle_id': 'vehicle_2',
                'type': 'availability_change',
                'channel': 'in_app',
                'subject': 'Vehicle Sold',
                'content': 'Vehicle is no longer available',
                'data': {},
                'created_at': datetime.utcnow(),
                'sent_at': datetime.utcnow(),
                'status': 'sent',
                'retry_count': 0,
                'max_retries': 3
            }
        ]

        # Mock total count query
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'total': len(mock_rows)}
        mock_cursor.fetchall.return_value = mock_rows

        notification_service.db_conn.cursor.return_value.__enter__.return_value = mock_cursor

        notifications, total = await notification_service.get_user_notifications(
            user_id="test_user_123",
            limit=20,
            offset=0
        )

        assert len(notifications) == 2
        assert total == 2
        assert notifications[0].type == NotificationType.PRICE_DROP
        assert notifications[1].type == NotificationType.AVAILABILITY_CHANGE

    def test_is_quiet_hours_active(self, notification_service):
        """Test quiet hours detection when active"""
        preferences = UserNotificationPreferences(
            user_id="test_user",
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )

        with patch('src.notifications.notification_service.datetime') as mock_datetime:
            # Mock current time as 23:00 (within quiet hours)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("23:00", "%H:%M").time()

            result = notification_service._is_quiet_hours(preferences)

            assert result is True

    def test_is_quiet_hours_inactive(self, notification_service):
        """Test quiet hours detection when inactive"""
        preferences = UserNotificationPreferences(
            user_id="test_user",
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )

        with patch('src.notifications.notification_service.datetime') as mock_datetime:
            # Mock current time as 10:00 (outside quiet hours)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("10:00", "%H:%M").time()

            result = notification_service._is_quiet_hours(preferences)

            assert result is False

    def test_is_quiet_hours_none(self, notification_service):
        """Test quiet hours detection when not set"""
        preferences = UserNotificationPreferences(
            user_id="test_user",
            quiet_hours_start=None,
            quiet_hours_end=None
        )

        result = notification_service._is_quiet_hours(preferences)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_notification_success(
        self,
        notification_service,
        sample_preferences
    ):
        """Test successful email notification sending"""
        notification = NotificationMessage(
            user_id=sample_preferences.user_id,
            vehicle_id="vehicle_123",
            type=NotificationType.PRICE_DROP,
            subject="Test Subject",
            content="Test content"
        )

        # Mock SMTP operations
        with patch('src.notifications.notification_service.smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_server.send_message = Mock()

            result = await notification_service._send_email_notification(
                notification,
                sample_preferences.email_address
            )

            assert result is True
            assert notification.status == 'sent'
            assert notification.sent_at is not None

    @pytest.mark.asyncio
    async def test_send_sms_notification_placeholder(
        self,
        notification_service,
        sample_preferences
    ):
        """Test SMS notification (placeholder implementation)"""
        notification = NotificationMessage(
            user_id=sample_preferences.user_id,
            vehicle_id="vehicle_123",
            type=NotificationType.PRICE_DROP,
            subject="Test Subject",
            content="Test content"
        )

        result = await notification_service._send_sms_notification(
            notification,
            sample_preferences.phone_number
        )

        # SMS is currently placeholder but should return True
        assert result is True
        assert notification.status == 'sent'

    @pytest.mark.asyncio
    async def test_send_in_app_notification_placeholder(
        self,
        notification_service
    ):
        """Test in-app notification (placeholder implementation)"""
        notification = NotificationMessage(
            user_id="test_user_123",
            vehicle_id="vehicle_123",
            type=NotificationType.PRICE_DROP,
            subject="Test Subject",
            content="Test content"
        )

        result = await notification_service._send_in_app_notification(notification)

        # In-app notification is currently placeholder but should return True
        assert result is True
        assert notification.status == 'sent'

    @pytest.mark.asyncio
    async def test_send_notification_channels_email_only(
        self,
        notification_service,
        sample_preferences
    ):
        """Test sending notification through email channel only"""
        notification = NotificationMessage(
            user_id=sample_preferences.user_id,
            vehicle_id="vehicle_123",
            type=NotificationType.PRICE_DROP,
            subject="Test Subject",
            content="Test content"
        )

        # Mock email sending
        with patch.object(notification_service, '_send_email_notification', return_value=True):
            result = await notification_service._send_notification_channels(notification, sample_preferences)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_notification_channels_during_quiet_hours(
        self,
        notification_service,
        sample_preferences
    ):
        """Test deferring notification during quiet hours"""
        notification = NotificationMessage(
            user_id=sample_preferences.user_id,
            vehicle_id="vehicle_123",
            type=NotificationType.PRICE_DROP,
            subject="Test Subject",
            content="Test content"
        )

        # Mock quiet hours as active
        with patch.object(notification_service, '_is_quiet_hours', return_value=True):
            with patch.object(notification_service, '_defer_notification', return_value=None):
                result = await notification_service._send_notification_channels(notification, sample_preferences)

                # Should return True as notification is deferred (not failed)
                assert result is True

    @pytest.mark.asyncio
    async def test_price_drop_calculation(self):
        """Test price drop percentage calculation"""
        # Test various price drop scenarios
        test_cases = [
            (1000.0, 900.0, 10.0),   # 10% drop
            (5000.0, 4750.0, 5.0),    # 5% drop
            (20000.0, 18000.0, 10.0), # 10% drop
            (1000.0, 999.0, 0.1),     # 0.1% drop
        ]

        for old_price, new_price, expected_percentage in test_cases:
            calculated_percentage = ((old_price - new_price) / old_price) * 100
            assert abs(calculated_percentage - expected_percentage) < 0.01

    @pytest.mark.asyncio
    async def test_notification_message_creation(self):
        """Test NotificationMessage data model"""
        notification = NotificationMessage(
            user_id="test_user",
            vehicle_id="test_vehicle",
            type=NotificationType.PRICE_DROP,
            channel=NotificationChannel.EMAIL,
            subject="Test",
            content="Test content"
        )

        assert notification.user_id == "test_user"
        assert notification.vehicle_id == "test_vehicle"
        assert notification.type == NotificationType.PRICE_DROP
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status == "pending"
        assert notification.retry_count == 0
        assert notification.max_retries == 3
        assert notification.id is not None
        assert notification.created_at is not None

    @pytest.mark.asyncio
    async def test_user_notification_preferences_defaults(self):
        """Test UserNotificationPreferences default values"""
        preferences = UserNotificationPreferences(user_id="test_user")

        assert preferences.user_id == "test_user"
        assert preferences.price_drop_notifications is True
        assert preferences.availability_notifications is True
        assert preferences.new_similar_vehicle_notifications is False
        assert preferences.email_enabled is True
        assert preferences.sms_enabled is False
        assert preferences.in_app_enabled is True
        assert preferences.min_price_drop_percentage == 5.0
        assert preferences.notification_frequency == "immediate"
        assert preferences.quiet_hours_start is None
        assert preferences.quiet_hours_end is None

    @pytest.mark.asyncio
    async def test_initialize_missing_password(self):
        """Test initialization failure with missing database password"""
        service = NotificationService()

        with patch.dict(os.environ, {}, clear=True):
            result = await service.initialize('https://test.supabase.co', 'test_key')

            assert result is False

    @pytest.mark.asyncio
    async def test_database_error_handling(self, notification_service):
        """Test handling of database errors"""
        # Mock database error
        notification_service.db_conn.cursor.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await notification_service.get_user_notification_preferences("test_user")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])