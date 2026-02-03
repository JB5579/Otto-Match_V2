"""
Otto.AI Favorites WebSocket Service

Implements Story 1.6: Vehicle Favorites and Notifications
Real-time price monitoring and WebSocket updates for favorite vehicles

Features:
- Real-time price change monitoring for favorited vehicles
- WebSocket connections for live updates
- Price change detection with configurable thresholds
- Connection management for multiple users
- Broadcast notifications for price drops
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

@dataclass
class WebSocketConnection:
    """WebSocket connection data model"""
    connection_id: str
    user_id: str
    websocket: Any  # WebSocket instance
    connected_at: datetime
    last_ping: datetime
    subscribed_vehicles: Set[str]

@dataclass
class PriceChangeAlert:
    """Price change alert data model"""
    vehicle_id: str
    old_price: float
    new_price: float
    price_drop_percentage: float
    users_notified: Set[str]
    created_at: datetime

class FavoritesWebSocketService:
    """
    Service for managing WebSocket connections and real-time price monitoring
    """

    def __init__(self):
        """Initialize WebSocket service"""
        self.db_conn = None
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.vehicle_subscribers: Dict[str, Set[str]] = {}  # vehicle_id -> user_ids
        self.price_change_history: List[PriceChangeAlert] = []
        self.monitoring_active = False
        self.price_check_interval = 60  # Check prices every 60 seconds

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection and start price monitoring

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous key

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to Supabase
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)

            logger.info("✅ Favorites WebSocket Service connected to Supabase")

            # Create required tables
            await self._create_price_monitoring_table()
            await self._create_websocket_connections_table()

            # Start price monitoring background task
            if not self.monitoring_active:
                asyncio.create_task(self._price_monitoring_loop())
                self.monitoring_active = True

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Favorites WebSocket Service: {e}")
            return False

    async def _create_price_monitoring_table(self) -> None:
        """Create price monitoring table if it doesn't exist"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS price_monitoring (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        vehicle_id VARCHAR(255) UNIQUE NOT NULL,
                        last_known_price DECIMAL(10,2),
                        last_price_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        price_change_threshold DECIMAL(5,2) DEFAULT 5.0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_price_monitoring_vehicle_id
                    ON price_monitoring(vehicle_id);
                    CREATE INDEX IF NOT EXISTS idx_price_monitoring_last_check
                    ON price_monitoring(last_price_check);
                """)

                # Create trigger for updated_at
                cur.execute("""
                    CREATE OR REPLACE FUNCTION update_price_monitoring_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """)

                cur.execute("""
                    DROP TRIGGER IF EXISTS update_price_monitoring_updated_at
                    ON price_monitoring;
                    CREATE TRIGGER update_price_monitoring_updated_at
                        BEFORE UPDATE ON price_monitoring
                        FOR EACH ROW
                        EXECUTE FUNCTION update_price_monitoring_updated_at();
                """)

                self.db_conn.commit()
                logger.info("✅ Price monitoring table created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create price monitoring table: {e}")
            raise

    async def _create_websocket_connections_table(self) -> None:
        """Create websocket_connections table if it doesn't exist"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS websocket_connections (
                        connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_ids TEXT[] DEFAULT '{}',
                        connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_ping TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT true
                    );
                """)

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_websocket_connections_user_id
                    ON websocket_connections(user_id);
                """)

                self.db_conn.commit()
                logger.info("✅ WebSocket connections table created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create WebSocket connections table: {e}")
            raise

    async def register_connection(self, user_id: str, websocket: Any) -> str:
        """
        Register new WebSocket connection

        Args:
            user_id: User identifier
            websocket: WebSocket connection instance

        Returns:
            Connection ID
        """
        try:
            connection_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Create connection object
            connection = WebSocketConnection(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                connected_at=now,
                last_ping=now,
                subscribed_vehicles=set()
            )

            # Track in memory
            self.active_connections[connection_id] = connection

            # Track by user
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

            # Save to database
            await self._save_connection_to_db(connection)

            logger.info(f"✅ Registered WebSocket connection {connection_id} for user {user_id}")

            return connection_id

        except Exception as e:
            logger.error(f"❌ Failed to register WebSocket connection: {e}")
            raise

    async def unregister_connection(self, connection_id: str) -> None:
        """
        Unregister WebSocket connection

        Args:
            connection_id: Connection identifier
        """
        try:
            if connection_id not in self.active_connections:
                return

            connection = self.active_connections[connection_id]
            user_id = connection.user_id

            # Remove from memory
            del self.active_connections[connection_id]

            # Remove from user tracking
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from vehicle subscriptions
            for vehicle_id in connection.subscribed_vehicles:
                if vehicle_id in self.vehicle_subscribers:
                    self.vehicle_subscribers[vehicle_id].discard(user_id)
                    if not self.vehicle_subscribers[vehicle_id]:
                        del self.vehicle_subscribers[vehicle_id]

            # Mark as inactive in database
            await self._deactivate_connection_in_db(connection_id)

            logger.info(f"✅ Unregistered WebSocket connection {connection_id}")

        except Exception as e:
            logger.error(f"❌ Failed to unregister WebSocket connection: {e}")

    async def subscribe_to_vehicle(self, connection_id: str, vehicle_id: str) -> bool:
        """
        Subscribe connection to vehicle price updates

        Args:
            connection_id: Connection identifier
            vehicle_id: Vehicle identifier

        Returns:
            True if subscribed successfully, False otherwise
        """
        try:
            if connection_id not in self.active_connections:
                return False

            connection = self.active_connections[connection_id]
            user_id = connection.user_id

            # Add to connection subscriptions
            connection.subscribed_vehicles.add(vehicle_id)

            # Add to vehicle subscribers
            if vehicle_id not in self.vehicle_subscribers:
                self.vehicle_subscribers[vehicle_id] = set()
            self.vehicle_subscribers[vehicle_id].add(user_id)

            # Update database
            await self._update_connection_subscriptions(connection_id, connection.subscribed_vehicles)

            # Start monitoring vehicle if not already
            await self._start_monitoring_vehicle(vehicle_id)

            logger.info(f"✅ Connection {connection_id} subscribed to vehicle {vehicle_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to vehicle: {e}")
            return False

    async def unsubscribe_from_vehicle(self, connection_id: str, vehicle_id: str) -> bool:
        """
        Unsubscribe connection from vehicle price updates

        Args:
            connection_id: Connection identifier
            vehicle_id: Vehicle identifier

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            if connection_id not in self.active_connections:
                return False

            connection = self.active_connections[connection_id]
            user_id = connection.user_id

            # Remove from connection subscriptions
            connection.subscribed_vehicles.discard(vehicle_id)

            # Remove from vehicle subscribers
            if vehicle_id in self.vehicle_subscribers:
                self.vehicle_subscribers[vehicle_id].discard(user_id)
                if not self.vehicle_subscribers[vehicle_id]:
                    del self.vehicle_subscribers[vehicle_id]

            # Update database
            await self._update_connection_subscriptions(connection_id, connection.subscribed_vehicles)

            logger.info(f"✅ Connection {connection_id} unsubscribed from vehicle {vehicle_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe from vehicle: {e}")
            return False

    async def _save_connection_to_db(self, connection: WebSocketConnection) -> None:
        """Save connection to database"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO websocket_connections (
                        connection_id, user_id, vehicle_ids, connected_at, last_ping
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (connection_id) DO UPDATE SET
                        vehicle_ids = EXCLUDED.vehicle_ids,
                        last_ping = EXCLUDED.last_ping,
                        is_active = true;
                """, (
                    connection.connection_id,
                    connection.user_id,
                    list(connection.subscribed_vehicles),
                    connection.connected_at,
                    connection.last_ping
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to save connection to database: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    async def _deactivate_connection_in_db(self, connection_id: str) -> None:
        """Mark connection as inactive in database"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE websocket_connections
                    SET is_active = false
                    WHERE connection_id = %s;
                """, (connection_id,))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to deactivate connection in database: {e}")

    async def _update_connection_subscriptions(self, connection_id: str, vehicle_ids: Set[str]) -> None:
        """Update connection vehicle subscriptions in database"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE websocket_connections
                    SET vehicle_ids = %s
                    WHERE connection_id = %s;
                """, (list(vehicle_ids), connection_id))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update connection subscriptions: {e}")

    async def _start_monitoring_vehicle(self, vehicle_id: str) -> None:
        """Start monitoring vehicle for price changes"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO price_monitoring (vehicle_id, last_known_price)
                    VALUES (%s, NULL)
                    ON CONFLICT (vehicle_id) DO NOTHING;
                """, (vehicle_id,))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to start monitoring vehicle {vehicle_id}: {e}")

    async def _price_monitoring_loop(self) -> None:
        """Background task to monitor vehicle prices"""
        logger.info("🚀 Starting price monitoring loop")

        while self.monitoring_active:
            try:
                await self._check_vehicle_prices()
                await asyncio.sleep(self.price_check_interval)

            except Exception as e:
                logger.error(f"❌ Error in price monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _check_vehicle_prices(self) -> None:
        """Check for price changes on monitored vehicles"""
        try:
            # Get vehicles that have active subscribers
            monitored_vehicles = list(self.vehicle_subscribers.keys())
            if not monitored_vehicles:
                return

            # Get current prices from database
            price_changes = await self._fetch_price_changes(monitored_vehicles)

            # Process price changes and send notifications
            for price_change in price_changes:
                await self._handle_price_change(price_change)

        except Exception as e:
            logger.error(f"❌ Error checking vehicle prices: {e}")

    async def _fetch_price_changes(self, vehicle_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch price changes for monitored vehicles"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                placeholders = ','.join(['%s'] * len(vehicle_ids))

                cur.execute(f"""
                    SELECT
                        pm.vehicle_id,
                        pm.last_known_price as old_price,
                        v.price as new_price,
                        pm.price_change_threshold
                    FROM price_monitoring pm
                    JOIN vehicles v ON pm.vehicle_id = v.id
                    WHERE pm.vehicle_id IN ({placeholders})
                      AND v.price IS NOT NULL
                      AND (pm.last_known_price IS NULL
                           OR pm.last_known_price != v.price);
                """, vehicle_ids)

                price_changes = cur.fetchall()

                # Calculate price drop percentages
                for change in price_changes:
                    if change['old_price'] and change['new_price']:
                        price_drop_percentage = ((change['old_price'] - change['new_price']) / change['old_price']) * 100
                        change['price_drop_percentage'] = price_drop_percentage
                    else:
                        change['price_drop_percentage'] = 0

                # Filter for significant price drops (>= threshold)
                significant_changes = [
                    change for change in price_changes
                    if abs(change['price_drop_percentage']) >= change['price_change_threshold']
                ]

                return significant_changes

        except Exception as e:
            logger.error(f"❌ Error fetching price changes: {e}")
            return []

    async def _handle_price_change(self, price_change: Dict[str, Any]) -> None:
        """Handle price change and send notifications to subscribers"""
        try:
            vehicle_id = price_change['vehicle_id']
            old_price = price_change['old_price']
            new_price = price_change['new_price']
            price_drop_percentage = price_change['price_drop_percentage']

            # Update last known price
            await self._update_last_known_price(vehicle_id, new_price)

            # Get subscribers for this vehicle
            subscribers = self.vehicle_subscribers.get(vehicle_id, set())
            if not subscribers:
                return

            # Create price change alert
            alert = PriceChangeAlert(
                vehicle_id=vehicle_id,
                old_price=old_price,
                new_price=new_price,
                price_drop_percentage=price_drop_percentage,
                users_notified=subscribers.copy(),
                created_at=datetime.utcnow()
            )
            self.price_change_history.append(alert)

            # Prepare notification message
            notification_message = {
                "type": "price_change",
                "vehicle_id": vehicle_id,
                "old_price": old_price,
                "new_price": new_price,
                "price_drop_percentage": price_drop_percentage,
                "timestamp": alert.created_at.isoformat(),
                "is_price_drop": price_drop_percentage > 0
            }

            # Send to all active connections for subscribers
            await self._broadcast_to_subscribers(vehicle_id, notification_message)

            logger.info(f"📢 Price change detected for vehicle {vehicle_id}: {old_price} → {new_price} ({price_drop_percentage:.1f}%)")

        except Exception as e:
            logger.error(f"❌ Error handling price change: {e}")

    async def _update_last_known_price(self, vehicle_id: str, new_price: float) -> None:
        """Update last known price for vehicle"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE price_monitoring
                    SET last_known_price = %s, last_price_check = NOW()
                    WHERE vehicle_id = %s;
                """, (new_price, vehicle_id))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update last known price: {e}")

    async def _broadcast_to_subscribers(self, vehicle_id: str, message: Dict[str, Any]) -> None:
        """Broadcast message to all connections subscribed to vehicle"""
        try:
            subscribers = self.vehicle_subscribers.get(vehicle_id, set())
            sent_count = 0
            failed_count = 0

            for user_id in subscribers:
                user_connection_ids = self.user_connections.get(user_id, set())

                for connection_id in user_connection_ids:
                    if connection_id in self.active_connections:
                        connection = self.active_connections[connection_id]
                        try:
                            await connection.websocket.send_text(json.dumps(message))
                            sent_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to send to connection {connection_id}: {e}")
                            # Connection might be dead, schedule cleanup
                            asyncio.create_task(self.unregister_connection(connection_id))
                            failed_count += 1

            logger.info(f"📡 Price change broadcast: {sent_count} sent, {failed_count} failed")

        except Exception as e:
            logger.error(f"❌ Error broadcasting to subscribers: {e}")

    async def send_connection_status(self, connection_id: str, status: str, message: str = "") -> None:
        """Send connection status update"""
        try:
            if connection_id not in self.active_connections:
                return

            status_message = {
                "type": "connection_status",
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            connection = self.active_connections[connection_id]
            await connection.websocket.send_text(json.dumps(status_message))

        except Exception as e:
            logger.error(f"❌ Failed to send connection status: {e}")

    async def ping_connections(self) -> None:
        """Ping all active connections to check connectivity"""
        try:
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }

            for connection_id, connection in list(self.active_connections.items()):
                try:
                    await connection.websocket.send_text(json.dumps(ping_message))
                    connection.last_ping = datetime.utcnow()
                except Exception as e:
                    logger.warning(f"Ping failed for connection {connection_id}: {e}")
                    await self.unregister_connection(connection_id)

        except Exception as e:
            logger.error(f"❌ Error during connection ping: {e}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        try:
            stats = {
                "total_connections": len(self.active_connections),
                "unique_users": len(self.user_connections),
                "monitored_vehicles": len(self.vehicle_subscribers),
                "total_subscriptions": sum(len(conn.subscribed_vehicles) for conn in self.active_connections.values()),
                "monitoring_active": self.monitoring_active,
                "price_alerts_today": len([
                    alert for alert in self.price_change_history
                    if alert.created_at.date() == datetime.utcnow().date()
                ])
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting connection stats: {e}")
            return {}

    async def close(self) -> None:
        """Close WebSocket service and cleanup"""
        try:
            # Stop monitoring
            self.monitoring_active = False

            # Close all connections
            for connection_id in list(self.active_connections.keys()):
                await self.unregister_connection(connection_id)

            # Close database connection
            if self.db_conn:
                self.db_conn.close()
                logger.info("✅ Favorites WebSocket Service connection closed")

        except Exception as e:
            logger.error(f"❌ Error closing WebSocket service: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'monitoring_active'):
            self.monitoring_active = False
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass