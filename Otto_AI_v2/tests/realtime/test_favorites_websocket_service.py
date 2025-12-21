"""
Tests for Otto.AI Favorites WebSocket Service

Implements Story 1.6: Vehicle Favorites and Notifications
Comprehensive test suite for real-time WebSocket functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.realtime.favorites_websocket_service import (
    FavoritesWebSocketService,
    WebSocketConnection,
    PriceChangeAlert
)

class TestFavoritesWebSocketService:
    """Test suite for FavoritesWebSocketService"""

    @pytest.fixture
    async def websocket_service(self):
        """Create WebSocket service fixture"""
        service = FavoritesWebSocketService()

        # Mock database connection
        service.db_conn = Mock()
        service.db_conn.cursor = Mock()
        service.db_conn.commit = Mock()
        service.db_conn.rollback = Mock()

        yield service

        await service.close()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        websocket = Mock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization"""
        service = FavoritesWebSocketService()

        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_DB_PASSWORD': 'test_password'
        }):
            with patch('src.realtime.favorites_websocket_service.psycopg.connect') as mock_connect:
                mock_conn = Mock()
                mock_connect.return_value = mock_conn

                result = await service.initialize('https://test.supabase.co', 'test_key')

                assert result is True
                mock_connect.assert_called_once()
                assert service.db_conn == mock_conn
                assert service.monitoring_active is True

    @pytest.mark.asyncio
    async def test_register_connection(self, websocket_service, mock_websocket):
        """Test WebSocket connection registration"""
        user_id = "test_user_123"

        # Mock database operations
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        connection_id = await websocket_service.register_connection(user_id, mock_websocket)

        assert connection_id is not None
        assert connection_id in websocket_service.active_connections
        assert user_id in websocket_service.user_connections
        assert connection_id in websocket_service.user_connections[user_id]

        connection = websocket_service.active_connections[connection_id]
        assert connection.user_id == user_id
        assert connection.websocket == mock_websocket

    @pytest.mark.asyncio
    async def test_unregister_connection(self, websocket_service, mock_websocket):
        """Test WebSocket connection unregistration"""
        user_id = "test_user_123"

        # First register a connection
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        connection_id = await websocket_service.register_connection(user_id, mock_websocket)

        # Mock database operations for unregistration
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        await websocket_service.unregister_connection(connection_id)

        assert connection_id not in websocket_service.active_connections
        assert user_id not in websocket_service.user_connections

    @pytest.mark.asyncio
    async def test_subscribe_to_vehicle(self, websocket_service, mock_websocket):
        """Test subscribing to vehicle updates"""
        user_id = "test_user_123"
        vehicle_id = "vehicle_123"

        # Register connection first
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        connection_id = await websocket_service.register_connection(user_id, mock_websocket)

        # Mock database operations for subscription
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        result = await websocket_service.subscribe_to_vehicle(connection_id, vehicle_id)

        assert result is True

        connection = websocket_service.active_connections[connection_id]
        assert vehicle_id in connection.subscribed_vehicles
        assert vehicle_id in websocket_service.vehicle_subscribers
        assert user_id in websocket_service.vehicle_subscribers[vehicle_id]

    @pytest.mark.asyncio
    async def test_unsubscribe_from_vehicle(self, websocket_service, mock_websocket):
        """Test unsubscribing from vehicle updates"""
        user_id = "test_user_123"
        vehicle_id = "vehicle_123"

        # Register and subscribe first
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        connection_id = await websocket_service.register_connection(user_id, mock_websocket)
        await websocket_service.subscribe_to_vehicle(connection_id, vehicle_id)

        # Mock database operations for unsubscription
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        result = await websocket_service.unsubscribe_from_vehicle(connection_id, vehicle_id)

        assert result is True

        connection = websocket_service.active_connections[connection_id]
        assert vehicle_id not in connection.subscribed_vehicles
        assert vehicle_id not in websocket_service.vehicle_subscribers

    @pytest.mark.asyncio
    async def test_subscribe_nonexistent_connection(self, websocket_service):
        """Test subscribing with nonexistent connection"""
        result = await websocket_service.subscribe_to_vehicle("invalid_id", "vehicle_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_price_changes(self, websocket_service):
        """Test fetching price changes from database"""
        vehicle_ids = ["vehicle_1", "vehicle_2"]

        # Mock database response with price changes
        mock_rows = [
            {
                'vehicle_id': 'vehicle_1',
                'old_price': 30000.0,
                'new_price': 27000.0,
                'price_change_threshold': 5.0
            },
            {
                'vehicle_id': 'vehicle_2',
                'old_price': 25000.0,
                'new_price': 24500.0,
                'price_change_threshold': 3.0
            }
        ]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_rows
        websocket_service.db_conn.cursor.return_value.__enter__.return_value = mock_cursor

        price_changes = await websocket_service._fetch_price_changes(vehicle_ids)

        assert len(price_changes) == 2
        assert price_changes[0]['vehicle_id'] == 'vehicle_1'
        assert price_changes[0]['price_drop_percentage'] == 10.0  # (30000-27000)/30000*100
        assert price_changes[1]['vehicle_id'] == 'vehicle_2'
        assert price_changes[1]['price_drop_percentage'] == 2.0  # (25000-24500)/25000*100

    @pytest.mark.asyncio
    async def test_fetch_price_changes_filters_by_threshold(self, websocket_service):
        """Test that price changes are filtered by threshold"""
        vehicle_ids = ["vehicle_1"]

        # Mock database response with small price change (below threshold)
        mock_rows = [
            {
                'vehicle_id': 'vehicle_1',
                'old_price': 30000.0,
                'new_price': 29500.0,  # Only 1.67% drop
                'price_change_threshold': 5.0
            }
        ]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_rows
        websocket_service.db_conn.cursor.return_value.__enter__.return_value = mock_cursor

        price_changes = await websocket_service._fetch_price_changes(vehicle_ids)

        # Should be filtered out as it's below 5% threshold
        assert len(price_changes) == 0

    @pytest.mark.asyncio
    async def test_handle_price_change(self, websocket_service, mock_websocket):
        """Test handling price change and broadcasting to subscribers"""
        user_id = "test_user_123"
        vehicle_id = "vehicle_123"

        # Set up connection and subscription
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        connection_id = await websocket_service.register_connection(user_id, mock_websocket)
        await websocket_service.subscribe_to_vehicle(connection_id, vehicle_id)

        # Mock database update for price
        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        price_change = {
            'vehicle_id': vehicle_id,
            'old_price': 30000.0,
            'new_price': 27000.0,
            'price_drop_percentage': 10.0
        }

        await websocket_service._handle_price_change(price_change)

        # Verify WebSocket message was sent
        mock_websocket.send_text.assert_called_once()

        # Verify message content
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message['type'] == 'price_change'
        assert message['vehicle_id'] == vehicle_id
        assert message['old_price'] == 30000.0
        assert message['new_price'] == 27000.0
        assert message['price_drop_percentage'] == 10.0
        assert message['is_price_drop'] is True

    @pytest.mark.asyncio
    async def test_send_connection_status(self, websocket_service, mock_websocket):
        """Test sending connection status"""
        connection_id = "test_connection_123"

        # Add connection to service
        websocket_service.active_connections[connection_id] = WebSocketConnection(
            connection_id=connection_id,
            user_id="test_user",
            websocket=mock_websocket,
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            subscribed_vehicles=set()
        )

        await websocket_service.send_connection_status(connection_id, "connected", "Test message")

        mock_websocket.send_text.assert_called_once()

        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message['type'] == 'connection_status'
        assert message['status'] == 'connected'
        assert message['message'] == 'Test message'

    @pytest.mark.asyncio
    async def test_ping_connections(self, websocket_service):
        """Test pinging all connections"""
        # Create multiple mock connections
        mock_websockets = []
        for i in range(3):
            mock_websocket = Mock()
            mock_websocket.send_text = AsyncMock()
            mock_websockets.append(mock_websocket)

            websocket_service.active_connections[f"conn_{i}"] = WebSocketConnection(
                connection_id=f"conn_{i}",
                user_id=f"user_{i}",
                websocket=mock_websocket,
                connected_at=datetime.utcnow(),
                last_ping=datetime.utcnow(),
                subscribed_vehicles=set()
            )

        await websocket_service.ping_connections()

        # Verify all connections received ping
        for mock_websocket in mock_websockets:
            mock_websocket.send_text.assert_called_once()
            call_args = mock_websocket.send_text.call_args[0][0]
            message = json.loads(call_args)
            assert message['type'] == 'ping'

    @pytest.mark.asyncio
    async def test_get_connection_stats(self, websocket_service):
        """Test getting connection statistics"""
        # Set up some test data
        websocket_service.active_connections = {
            "conn_1": WebSocketConnection("conn_1", "user_1", Mock(), datetime.utcnow(), datetime.utcnow(), {"vehicle_1"}),
            "conn_2": WebSocketConnection("conn_2", "user_1", Mock(), datetime.utcnow(), datetime.utcnow(), {"vehicle_2"}),
            "conn_3": WebSocketConnection("conn_3", "user_2", Mock(), datetime.utcnow(), datetime.utcnow(), {"vehicle_1", "vehicle_3"})
        }

        websocket_service.user_connections = {
            "user_1": {"conn_1", "conn_2"},
            "user_2": {"conn_3"}
        }

        websocket_service.vehicle_subscribers = {
            "vehicle_1": {"user_1", "user_2"},
            "vehicle_2": {"user_1"},
            "vehicle_3": {"user_2"}
        }

        websocket_service.price_change_history = [
            PriceChangeAlert("vehicle_1", 30000, 27000, 10.0, {"user_1"}, datetime.utcnow())
        ]

        stats = await websocket_service.get_connection_stats()

        assert stats['total_connections'] == 3
        assert stats['unique_users'] == 2
        assert stats['monitored_vehicles'] == 3
        assert stats['total_subscriptions'] == 4  # vehicle_1 appears twice, vehicle_2 once, vehicle_3 once
        assert stats['monitoring_active'] is True
        assert stats['price_alerts_today'] == 1

    @pytest.mark.asyncio
    async def test_price_monitoring_loop(self, websocket_service):
        """Test price monitoring loop with mocked operations"""
        # Mock the price checking method
        websocket_service.monitoring_active = True

        with patch.object(websocket_service, '_check_vehicle_prices', new_callable=AsyncMock) as mock_check:
            # Mock asyncio.sleep to avoid actual waiting
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # Run a single iteration then stop
                mock_sleep.side_effect = [None, Exception("Stop loop")]

                with pytest.raises(Exception, match="Stop loop"):
                    await websocket_service._price_monitoring_loop()

                mock_check.assert_called_once()
                mock_sleep.assert_called_once()

    def test_websocket_connection_model(self):
        """Test WebSocketConnection data model"""
        now = datetime.utcnow()
        connection = WebSocketConnection(
            connection_id="test_conn",
            user_id="test_user",
            websocket=Mock(),
            connected_at=now,
            last_ping=now,
            subscribed_vehicles={"vehicle_1", "vehicle_2"}
        )

        assert connection.connection_id == "test_conn"
        assert connection.user_id == "test_user"
        assert connection.connected_at == now
        assert connection.last_ping == now
        assert len(connection.subscribed_vehicles) == 2
        assert "vehicle_1" in connection.subscribed_vehicles
        assert "vehicle_2" in connection.subscribed_vehicles

    def test_price_change_alert_model(self):
        """Test PriceChangeAlert data model"""
        now = datetime.utcnow()
        alert = PriceChangeAlert(
            vehicle_id="vehicle_123",
            old_price=30000.0,
            new_price=27000.0,
            price_drop_percentage=10.0,
            users_notified={"user_1", "user_2"},
            created_at=now
        )

        assert alert.vehicle_id == "vehicle_123"
        assert alert.old_price == 30000.0
        assert alert.new_price == 27000.0
        assert alert.price_drop_percentage == 10.0
        assert len(alert.users_notified) == 2
        assert "user_1" in alert.users_notified
        assert alert.created_at == now

    @pytest.mark.asyncio
    async def test_broadcast_to_subscribers_no_subscribers(self, websocket_service):
        """Test broadcasting when no subscribers exist"""
        message = {"test": "message"}

        # Should not raise any errors
        await websocket_service._broadcast_to_subscribers("vehicle_123", message)

    @pytest.mark.asyncio
    async def test_start_monitoring_vehicle(self, websocket_service):
        """Test starting vehicle monitoring"""
        vehicle_id = "vehicle_123"

        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        await websocket_service._start_monitoring_vehicle(vehicle_id)

        # Verify database insert was called
        websocket_service.db_conn.cursor.assert_called()

    @pytest.mark.asyncio
    async def test_update_last_known_price(self, websocket_service):
        """Test updating last known price"""
        vehicle_id = "vehicle_123"
        new_price = 27000.0

        websocket_service.db_conn.cursor.return_value.__enter__ = Mock()
        websocket_service.db_conn.cursor.return_value.__exit__ = Mock()

        await websocket_service._update_last_known_price(vehicle_id, new_price)

        # Verify database update was called
        websocket_service.db_conn.cursor.assert_called()

    @pytest.mark.asyncio
    async def test_close_service(self, websocket_service, mock_websocket):
        """Test closing WebSocket service"""
        # Set up some active connections
        websocket_service.active_connections = {
            "conn_1": WebSocketConnection("conn_1", "user_1", mock_websocket, datetime.utcnow(), datetime.utcnow(), set())
        }
        websocket_service.monitoring_active = True

        await websocket_service.close()

        # Verify cleanup
        assert websocket_service.monitoring_active is False
        assert len(websocket_service.active_connections) == 0

    @pytest.mark.asyncio
    async def test_initialize_missing_password(self):
        """Test initialization failure with missing database password"""
        service = FavoritesWebSocketService()

        with patch.dict(os.environ, {}, clear=True):
            result = await service.initialize('https://test.supabase.co', 'test_key')

            assert result is False
            assert service.monitoring_active is False

    @pytest.mark.asyncio
    async def test_register_connection_database_error(self, websocket_service, mock_websocket):
        """Test handling database error during connection registration"""
        user_id = "test_user_123"

        # Mock database error
        websocket_service.db_conn.cursor.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await websocket_service.register_connection(user_id, mock_websocket)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])