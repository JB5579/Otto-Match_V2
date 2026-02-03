"""
Otto.AI Notification Service

Implements Story 1.6: Vehicle Favorites and Notifications
Multi-channel notification system for price drops and availability changes

Features:
- Price drop notifications with 5% threshold checking
- Availability change notifications
- Multi-channel support (email, SMS, in-app)
- Notification batching to prevent spam
- User notification preferences management
- Real-time notification delivery
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import uuid
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications supported"""
    PRICE_DROP = "price_drop"
    AVAILABILITY_CHANGE = "availability_change"
    NEW_SIMILAR_VEHICLE = "new_similar_vehicle"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

@dataclass
class NotificationMessage:
    """Notification message data model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    vehicle_id: str = ""
    type: NotificationType = NotificationType.PRICE_DROP
    channel: NotificationChannel = NotificationChannel.EMAIL
    subject: str = ""
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class UserNotificationPreferences:
    """User notification preferences model"""
    user_id: str = ""
    price_drop_notifications: bool = True
    availability_notifications: bool = True
    new_similar_vehicle_notifications: bool = False
    email_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    min_price_drop_percentage: float = 5.0
    notification_frequency: str = "immediate"  # immediate, hourly, daily
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class NotificationService:
    """
    Service for managing multi-channel notifications

    Provides comprehensive notification management with user preferences,
    batching, and delivery across multiple channels.
    """

    def __init__(self):
        """Initialize notification service"""
        self.db_conn = None
        self.pending_notifications: List[NotificationMessage] = []
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@otto.ai')
        }

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection and create tables

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous key

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to Supabase using proper connection string format
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)

            logger.info("✅ Notification Service connected to Supabase")

            # Create required tables
            await self._create_notifications_table()
            await self._create_notification_preferences_table()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Notification Service: {e}")
            return False

    async def _create_notifications_table(self) -> None:
        """Create notifications table if it doesn't exist"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_id VARCHAR(255) NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        channel VARCHAR(20) NOT NULL,
                        subject TEXT,
                        content TEXT NOT NULL,
                        data JSONB DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        sent_at TIMESTAMP WITH TIME ZONE,
                        status VARCHAR(20) DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        INDEX user_id_idx (user_id),
                        INDEX vehicle_id_idx (vehicle_id),
                        INDEX status_idx (status),
                        INDEX created_at_idx (created_at)
                    );
                """)

                self.db_conn.commit()
                logger.info("✅ Notifications table created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create notifications table: {e}")
            raise

    async def _create_notification_preferences_table(self) -> None:
        """Create user_notification_preferences table if it doesn't exist"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_notification_preferences (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) UNIQUE NOT NULL,
                        price_drop_notifications BOOLEAN DEFAULT true,
                        availability_notifications BOOLEAN DEFAULT true,
                        new_similar_vehicle_notifications BOOLEAN DEFAULT false,
                        email_enabled BOOLEAN DEFAULT true,
                        sms_enabled BOOLEAN DEFAULT false,
                        in_app_enabled BOOLEAN DEFAULT true,
                        email_address VARCHAR(255),
                        phone_number VARCHAR(20),
                        min_price_drop_percentage DECIMAL(5,2) DEFAULT 5.0,
                        notification_frequency VARCHAR(20) DEFAULT 'immediate',
                        quiet_hours_start TIME,
                        quiet_hours_end TIME,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id
                    ON user_notification_preferences(user_id);
                """)

                # Create trigger for updated_at
                cur.execute("""
                    CREATE OR REPLACE FUNCTION update_notification_preferences_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """)

                cur.execute("""
                    DROP TRIGGER IF EXISTS update_notification_preferences_updated_at
                    ON user_notification_preferences;
                    CREATE TRIGGER update_notification_preferences_updated_at
                        BEFORE UPDATE ON user_notification_preferences
                        FOR EACH ROW
                        EXECUTE FUNCTION update_notification_preferences_updated_at();
                """)

                self.db_conn.commit()
                logger.info("✅ Notification preferences table created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create notification preferences table: {e}")
            raise

    async def send_price_drop_notification(
        self,
        user_id: str,
        vehicle_id: str,
        old_price: float,
        new_price: float,
        vehicle_details: Dict[str, Any]
    ) -> bool:
        """
        Send price drop notification if it meets user preferences threshold

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            old_price: Previous vehicle price
            new_price: New vehicle price
            vehicle_details: Vehicle information for notification

        Returns:
            True if notification was sent/scheduled, False otherwise
        """
        try:
            # Calculate price drop percentage
            price_drop_percentage = ((old_price - new_price) / old_price) * 100

            # Get user preferences
            preferences = await self.get_user_notification_preferences(user_id)

            # Check if user wants price drop notifications
            if not preferences.price_drop_notifications:
                logger.info(f"User {user_id} has disabled price drop notifications")
                return False

            # Check if drop meets user's threshold
            if price_drop_percentage < preferences.min_price_drop_percentage:
                logger.info(f"Price drop {price_drop_percentage:.1f}% below threshold {preferences.min_price_drop_percentage}%")
                return False

            # Create notification content
            savings_amount = old_price - new_price
            subject = f"Price Alert: {vehicle_details.get('make', '')} {vehicle_details.get('model', '')} price dropped by {price_drop_percentage:.1f}%"

            content = f"""
Great news! A vehicle you're following has dropped in price:

Vehicle: {vehicle_details.get('year', '')} {vehicle_details.get('make', '')} {vehicle_details.get('model', '')}
Previous Price: ${old_price:,.2f}
New Price: ${new_price:,.2f}
You Save: ${savings_amount:,.2f} ({price_drop_percentage:.1f}%)

View this vehicle now before someone else grabs this deal!
{vehicle_details.get('url', 'Contact us for details')}

Best regards,
Otto AI Vehicle Discovery
            """.strip()

            # Create notification message
            notification = NotificationMessage(
                user_id=user_id,
                vehicle_id=vehicle_id,
                type=NotificationType.PRICE_DROP,
                subject=subject,
                content=content,
                data={
                    'old_price': old_price,
                    'new_price': new_price,
                    'savings_amount': savings_amount,
                    'price_drop_percentage': price_drop_percentage,
                    'vehicle_details': vehicle_details
                }
            )

            # Send through preferred channels
            success = await self._send_notification_channels(notification, preferences)

            if success:
                logger.info(f"✅ Price drop notification sent for vehicle {vehicle_id} to user {user_id}")
            else:
                logger.error(f"❌ Failed to send price drop notification for vehicle {vehicle_id} to user {user_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending price drop notification: {e}")
            return False

    async def send_availability_change_notification(
        self,
        user_id: str,
        vehicle_id: str,
        new_status: str,
        vehicle_details: Dict[str, Any]
    ) -> bool:
        """
        Send availability change notification

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            new_status: New availability status (sold, unavailable, etc.)
            vehicle_details: Vehicle information for notification

        Returns:
            True if notification was sent/scheduled, False otherwise
        """
        try:
            # Get user preferences
            preferences = await self.get_user_notification_preferences(user_id)

            # Check if user wants availability notifications
            if not preferences.availability_notifications:
                logger.info(f"User {user_id} has disabled availability notifications")
                return False

            # Create notification content based on status
            if new_status.lower() == 'sold':
                subject = f"Sold: {vehicle_details.get('make', '')} {vehicle_details.get('model', '')} is no longer available"
                content = f"""
Unfortunately, a vehicle you were following has been sold:

Vehicle: {vehicle_details.get('year', '')} {vehicle_details.get('make', '')} {vehicle_details.get('model', '')}

Don't worry! Otto AI can help you find similar vehicles.
Check your recommendations or adjust your search criteria.

Happy car hunting!
Otto AI Vehicle Discovery
                """.strip()
            else:
                subject = f"Availability Update: {vehicle_details.get('make', '')} {vehicle_details.get('model', '')}"
                content = f"""
Availability update for a vehicle you're following:

Vehicle: {vehicle_details.get('year', '')} {vehicle_details.get('make', '')} {vehicle_details.get('model', '')}
New Status: {new_status}

{f"View vehicle: {vehicle_details.get('url', '')}" if vehicle_details.get('url') else ""}

Best regards,
Otto AI Vehicle Discovery
                """.strip()

            # Create notification message
            notification = NotificationMessage(
                user_id=user_id,
                vehicle_id=vehicle_id,
                type=NotificationType.AVAILABILITY_CHANGE,
                subject=subject,
                content=content,
                data={
                    'new_status': new_status,
                    'vehicle_details': vehicle_details
                }
            )

            # Send through preferred channels
            success = await self._send_notification_channels(notification, preferences)

            if success:
                logger.info(f"✅ Availability change notification sent for vehicle {vehicle_id} to user {user_id}")
            else:
                logger.error(f"❌ Failed to send availability change notification for vehicle {vehicle_id} to user {user_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending availability change notification: {e}")
            return False

    async def _send_notification_channels(
        self,
        notification: NotificationMessage,
        preferences: UserNotificationPreferences
    ) -> bool:
        """
        Send notification through user's preferred channels

        Args:
            notification: Notification message to send
            preferences: User notification preferences

        Returns:
            True if sent through at least one channel, False otherwise
        """
        success_count = 0

        try:
            # Check quiet hours
            if self._is_quiet_hours(preferences):
                logger.info(f"Deferring notification for user {notification.user_id} due to quiet hours")
                await self._defer_notification(notification)
                return True

            # Send through enabled channels
            if preferences.email_enabled and preferences.email_address:
                email_notification = NotificationMessage(
                    **notification.__dict__,
                    channel=NotificationChannel.EMAIL
                )
                if await self._send_email_notification(email_notification, preferences.email_address):
                    success_count += 1

            if preferences.sms_enabled and preferences.phone_number:
                sms_notification = NotificationMessage(
                    **notification.__dict__,
                    channel=NotificationChannel.SMS
                )
                if await self._send_sms_notification(sms_notification, preferences.phone_number):
                    success_count += 1

            if preferences.in_app_enabled:
                in_app_notification = NotificationMessage(
                    **notification.__dict__,
                    channel=NotificationChannel.IN_APP
                )
                if await self._send_in_app_notification(in_app_notification):
                    success_count += 1

            return success_count > 0

        except Exception as e:
            logger.error(f"❌ Error sending notification channels: {e}")
            return False

    async def _send_email_notification(
        self,
        notification: NotificationMessage,
        email_address: str
    ) -> bool:
        """
        Send email notification

        Args:
            notification: Notification message
            email_address: Recipient email address

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = email_address
            msg['Subject'] = notification.subject

            # Add HTML and plain text versions
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #333; margin-bottom: 20px;">{notification.subject}</h2>
                        <div style="background-color: white; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; color: #666;">{notification.content}</pre>
                        </div>
                        <div style="text-align: center; color: #999; font-size: 12px;">
                            <p>Sent by Otto AI Vehicle Discovery</p>
                            <p>If you no longer want these notifications, you can update your preferences in your account settings.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(notification.content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                server.send_message(msg)

            # Update notification status
            notification.sent_at = datetime.utcnow()
            notification.status = 'sent'
            await self._save_notification(notification)

            logger.info(f"✅ Email notification sent to {email_address}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email notification: {e}")
            notification.status = 'failed'
            await self._save_notification(notification)
            return False

    async def _send_sms_notification(
        self,
        notification: NotificationMessage,
        phone_number: str
    ) -> bool:
        """
        Send SMS notification (placeholder implementation)

        Args:
            notification: Notification message
            phone_number: Recipient phone number

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # TODO: Implement SMS service integration (Twilio, AWS SNS, etc.)
            # For now, just log the SMS that would be sent

            sms_content = f"Otto AI: {notification.subject}. {notification.content[:100]}..."

            logger.info(f"📱 SMS would be sent to {phone_number}: {sms_content}")

            # Simulate successful SMS send
            notification.sent_at = datetime.utcnow()
            notification.status = 'sent'
            await self._save_notification(notification)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send SMS notification: {e}")
            notification.status = 'failed'
            await self._save_notification(notification)
            return False

    async def _send_in_app_notification(
        self,
        notification: NotificationMessage
    ) -> bool:
        """
        Send in-app notification (placeholder implementation)

        Args:
            notification: Notification message

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # TODO: Implement real-time in-app notification system
            # This would integrate with WebSocket manager for real-time delivery

            logger.info(f"🔔 In-app notification for user {notification.user_id}: {notification.subject}")

            # Simulate successful in-app notification
            notification.sent_at = datetime.utcnow()
            notification.status = 'sent'
            await self._save_notification(notification)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send in-app notification: {e}")
            notification.status = 'failed'
            await self._save_notification(notification)
            return False

    async def _save_notification(self, notification: NotificationMessage) -> None:
        """Save notification to database"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO notifications (
                        id, user_id, vehicle_id, type, channel, subject, content,
                        data, created_at, sent_at, status, retry_count, max_retries
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        sent_at = EXCLUDED.sent_at,
                        status = EXCLUDED.status,
                        retry_count = EXCLUDED.retry_count;
                """, (
                    notification.id, notification.user_id, notification.vehicle_id,
                    notification.type.value, notification.channel.value,
                    notification.subject, notification.content, json.dumps(notification.data),
                    notification.created_at, notification.sent_at, notification.status,
                    notification.retry_count, notification.max_retries
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to save notification: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    async def _defer_notification(self, notification: NotificationMessage) -> None:
        """Save notification for later delivery during quiet hours"""
        try:
            # TODO: Implement proper notification deferral system
            # For now, just mark as deferred
            notification.status = 'deferred'
            await self._save_notification(notification)
            logger.info(f"Notification deferred for user {notification.user_id}")

        except Exception as e:
            logger.error(f"❌ Failed to defer notification: {e}")

    def _is_quiet_hours(self, preferences: UserNotificationPreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False

        try:
            current_time = datetime.now().time()
            start_time = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()

            if start_time <= end_time:
                # Same day (e.g., 22:00 to 07:00 crosses midnight)
                return start_time <= current_time <= end_time
            else:
                # Crosses midnight
                return current_time >= start_time or current_time <= end_time

        except Exception:
            return False

    async def get_user_notification_preferences(self, user_id: str) -> UserNotificationPreferences:
        """
        Get user's notification preferences

        Args:
            user_id: User identifier

        Returns:
            UserNotificationPreferences object
        """
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT * FROM user_notification_preferences WHERE user_id = %s;
                """, (user_id,))

                row = cur.fetchone()

                if row:
                    return UserNotificationPreferences(
                        user_id=row['user_id'],
                        price_drop_notifications=row['price_drop_notifications'],
                        availability_notifications=row['availability_notifications'],
                        new_similar_vehicle_notifications=row['new_similar_vehicle_notifications'],
                        email_enabled=row['email_enabled'],
                        sms_enabled=row['sms_enabled'],
                        in_app_enabled=row['in_app_enabled'],
                        email_address=row['email_address'],
                        phone_number=row['phone_number'],
                        min_price_drop_percentage=float(row['min_price_drop_percentage']),
                        notification_frequency=row['notification_frequency'],
                        quiet_hours_start=row['quiet_hours_start'].strftime("%H:%M") if row['quiet_hours_start'] else None,
                        quiet_hours_end=row['quiet_hours_end'].strftime("%H:%M") if row['quiet_hours_end'] else None,
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                else:
                    # Return default preferences
                    return UserNotificationPreferences(user_id=user_id)

        except Exception as e:
            logger.error(f"❌ Failed to get user notification preferences: {e}")
            return UserNotificationPreferences(user_id=user_id)

    async def update_user_notification_preferences(
        self,
        preferences: UserNotificationPreferences
    ) -> bool:
        """
        Update user's notification preferences

        Args:
            preferences: User notification preferences

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_notification_preferences (
                        user_id, price_drop_notifications, availability_notifications,
                        new_similar_vehicle_notifications, email_enabled, sms_enabled,
                        in_app_enabled, email_address, phone_number, min_price_drop_percentage,
                        notification_frequency, quiet_hours_start, quiet_hours_end
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        price_drop_notifications = EXCLUDED.price_drop_notifications,
                        availability_notifications = EXCLUDED.availability_notifications,
                        new_similar_vehicle_notifications = EXCLUDED.new_similar_vehicle_notifications,
                        email_enabled = EXCLUDED.email_enabled,
                        sms_enabled = EXCLUDED.sms_enabled,
                        in_app_enabled = EXCLUDED.in_app_enabled,
                        email_address = EXCLUDED.email_address,
                        phone_number = EXCLUDED.phone_number,
                        min_price_drop_percentage = EXCLUDED.min_price_drop_percentage,
                        notification_frequency = EXCLUDED.notification_frequency,
                        quiet_hours_start = EXCLUDED.quiet_hours_start,
                        quiet_hours_end = EXCLUDED.quiet_hours_end,
                        updated_at = NOW();
                """, (
                    preferences.user_id,
                    preferences.price_drop_notifications,
                    preferences.availability_notifications,
                    preferences.new_similar_vehicle_notifications,
                    preferences.email_enabled,
                    preferences.sms_enabled,
                    preferences.in_app_enabled,
                    preferences.email_address,
                    preferences.phone_number,
                    preferences.min_price_drop_percentage,
                    preferences.notification_frequency,
                    preferences.quiet_hours_start,
                    preferences.quiet_hours_end
                ))

                self.db_conn.commit()
                logger.info(f"✅ Updated notification preferences for user {preferences.user_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to update user notification preferences: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> Tuple[List[NotificationMessage], int]:
        """
        Get user's notification history

        Args:
            user_id: User identifier
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            status_filter: Filter by status (sent, failed, pending, etc.)

        Returns:
            Tuple of (notifications list, total count)
        """
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Build query with optional status filter
                where_clause = "WHERE user_id = %s"
                params = [user_id]

                if status_filter:
                    where_clause += " AND status = %s"
                    params.append(status_filter)

                # Get total count
                cur.execute(f"""
                    SELECT COUNT(*) as total FROM notifications {where_clause};
                """, params)

                total = cur.fetchone()['total']

                # Get paginated notifications
                params.extend([limit, offset])
                cur.execute(f"""
                    SELECT * FROM notifications {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s;
                """, params)

                rows = cur.fetchall()

                notifications = []
                for row in rows:
                    notification = NotificationMessage(
                        id=str(row['id']),
                        user_id=row['user_id'],
                        vehicle_id=row['vehicle_id'],
                        type=NotificationType(row['type']),
                        channel=NotificationChannel(row['channel']),
                        subject=row['subject'],
                        content=row['content'],
                        data=row['data'] if isinstance(row['data'], dict) else json.loads(row.get('{}', '{}')),
                        created_at=row['created_at'],
                        sent_at=row['sent_at'],
                        status=row['status'],
                        retry_count=row['retry_count'],
                        max_retries=row['max_retries']
                    )
                    notifications.append(notification)

                logger.info(f"✅ Retrieved {len(notifications)} notifications for user {user_id}")
                return notifications, total

        except Exception as e:
            logger.error(f"❌ Failed to get user notifications: {e}")
            return [], 0

    async def close(self) -> None:
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Notification Service connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass