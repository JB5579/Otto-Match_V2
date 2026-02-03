"""
Test Suite for WebSocket Endpoints
Tests for the Otto AI conversation WebSocket functionality
"""

import pytest
import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient
from fastapi import FastAPI
import websockets
from src.api.websocket_endpoints import (
    ConnectionManager,
    conversation_router,
    initialize_conversation_services,
    process_conversation_message
)
from src.conversation.conversation_agent import ConversationAgent, ConversationResponse


class TestConnectionManager:
    """Test WebSocket connection manager"""

    @pytest.fixture
    def connection_manager(self):
        """Create connection manager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connection_limits(self, connection_manager):
        """Test per-user connection limits"""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        mock_websocket3 = AsyncMock()
        mock_websocket1.accept = AsyncMock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket3.accept = AsyncMock()

        # Connect first two users (should succeed)
        conn1 = await connection_manager.connect(mock_websocket1, "user1")
        conn2 = await connection_manager.connect(mock_websocket2, "user1")

        assert conn1 is not None
        assert conn2 is not None
        assert len([c for c in connection_manager.connections.values() if c["user_id"] == "user1"]) == 2

        # Third connection for same user should fail
        mock_websocket3.close = AsyncMock()
        with pytest.raises(Exception):  # HTTPException for too many connections
            await connection_manager.connect(mock_websocket3, "user1")

    @pytest.mark.asyncio
    async def test_send_message(self, connection_manager):
        """Test sending messages to connections"""
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        # Connect
        conn_id = await connection_manager.connect(mock_websocket, "test_user")

        # Send message
        message = {"type": "test", "content": "Hello"}
        result = await connection_manager.send_message(conn_id, message)

        assert result == True
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, connection_manager):
        """Test broadcasting to all user connections"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        # Connect multiple for same user
        conn1 = await connection_manager.connect(mock_ws1, "test_user")
        conn2 = await connection_manager.connect(mock_ws2, "test_user")

        # Broadcast message
        message = {"type": "broadcast", "content": "Hello all"}
        sent_count = await connection_manager.broadcast_to_user("test_user", message)

        assert sent_count == 2
        mock_ws1.send_text.assert_called_with(json.dumps(message))
        mock_ws2.send_text.assert_called_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager):
        """Test connection disconnection"""
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Connect
        conn_id = await connection_manager.connect(mock_websocket, "test_user")
        assert conn_id in connection_manager.connections

        # Disconnect
        await connection_manager.disconnect(conn_id)
        assert conn_id not in connection_manager.connections
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_stats(self, connection_manager):
        """Test connection statistics"""
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()

        # Connect two different users
        await connection_manager.connect(mock_ws1, "user1")
        await connection_manager.connect(mock_ws2, "user2")

        # Get stats
        stats = await connection_manager.get_connection_stats()

        assert stats["total_connections"] == 2
        assert stats["unique_users"] == 2
        assert stats["max_connections_per_user"] == 5  # Default value


class TestWebSocketEndpoints:
    """Test WebSocket endpoint functionality"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with conversation router"""
        app = FastAPI()
        app.include_router(conversation_router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, app):
        """Test WebSocket stats endpoint"""
        from fastapi.testclient import TestClient
        client = TestClient(app)

        response = client.get("/ws/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_connections" in data
        assert "unique_users" in data

    @pytest.mark.asyncio
    async def test_conversation_processing(self):
        """Test conversation message processing"""
        # Mock dependencies
        with patch('src.api.websocket_endpoints.conversation_agent') as mock_agent:
            # Setup mock response
            mock_agent.process_message.return_value = ConversationResponse(
                message="Test response",
                response_type="text",
                processing_time_ms=100.0
            )

            # Create test message
            message = {
                "type": "text",
                "content": "Test message",
                "timestamp": datetime.now().isoformat()
            }

            # Mock connection manager
            with patch('src.api.websocket_endpoints.connection_manager') as mock_cm:
                mock_cm.send_message = AsyncMock()

                # Process message
                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )

                # Verify agent was called
                mock_agent.process_message.assert_called_once_with(
                    user_id="test_user",
                    message="Test message",
                    session_id="test_session"
                )

                # Verify response was sent
                mock_cm.send_message.assert_called_once()
                sent_data = mock_cm.send_message.call_args[0][1]
                assert sent_data["type"] == "text"
                assert sent_data["data"]["message"] == "Test response"
                assert sent_data["data"]["processing_time_ms"] == 100.0

    @pytest.mark.asyncio
    async def test_heartbeat_processing(self):
        """Test heartbeat message processing"""
        with patch('src.api.websocket_endpoints.connection_manager') as mock_cm:
            mock_cm.send_message = AsyncMock()

            # Create heartbeat message
            message = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }

            # Process heartbeat
            await process_conversation_message(
                connection_id="test_conn",
                user_id="test_user",
                session_id="test_session",
                message=message
            )

            # Verify pong response
            mock_cm.send_message.assert_called_once()
            sent_data = mock_cm.send_message.call_args[0][1]
            assert sent_data["type"] == "heartbeat"
            assert sent_data["event"] == "pong"

    @pytest.mark.asyncio
    async def test_invalid_message_format(self):
        """Test handling of invalid message formats"""
        with patch('src.api.websocket_endpoints.connection_manager') as mock_cm:
            mock_cm.send_message = AsyncMock()

            # Process invalid JSON (simulated)
            # Note: In actual implementation, JSON parsing happens before this function

            # Create message with unknown type
            message = {
                "type": "unknown_type",
                "content": "Test",
                "timestamp": datetime.now().isoformat()
            }

            # Process unknown type
            await process_conversation_message(
                connection_id="test_conn",
                user_id="test_user",
                session_id="test_session",
                message=message
            )

            # Verify error response
            mock_cm.send_message.assert_called_once()
            sent_data = mock_cm.send_message.call_args[0][1]
            assert sent_data["type"] == "error"
            assert sent_data["event"] == "unknown_message_type"

    @pytest.mark.asyncio
    async def test_service_unavailable_fallback(self):
        """Test fallback when conversation agent is unavailable"""
        with patch('src.api.websocket_endpoints.conversation_agent', None):
            with patch('src.api.websocket_endpoints.connection_manager') as mock_cm:
                mock_cm.send_message = AsyncMock()

                # Create message
                message = {
                    "type": "text",
                    "content": "Test message",
                    "timestamp": datetime.now().isoformat()
                }

                # Process without agent
                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )

                # Verify service unavailable response
                mock_cm.send_message.assert_called_once()
                sent_data = mock_cm.send_message.call_args[0][1]
                assert sent_data["type"] == "error"
                assert sent_data["event"] == "service_unavailable"

    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring integration"""
        with patch('src.api.websocket_endpoints.conversation_agent') as mock_agent:
            with patch('src.api.websocket_endpoints.performance_monitor') as mock_monitor:
                with patch('src.api.websocket_endpoints.connection_manager') as mock_cm:
                    # Setup mocks
                    mock_agent.process_message.return_value = ConversationResponse(
                        message="Test response",
                        response_type="text",
                        processing_time_ms=1500.0  # Over 2 second threshold
                    )

                    mock_monitor.record_query = AsyncMock()
                    mock_monitor.update_query_time = AsyncMock()
                    mock_cm.send_message = AsyncMock()

                    # Process message
                    message = {
                        "type": "text",
                        "content": "Test message",
                        "timestamp": datetime.now().isoformat()
                    }

                    await process_conversation_message(
                        connection_id="test_conn",
                        user_id="test_user",
                        session_id="test_session",
                        message=message
                    )

                    # Verify performance monitoring
                    mock_monitor.record_query.assert_called_once()
                    mock_monitor.update_query_time.assert_called_once_with(
                        query_text="conversation:test_user:Test message",
                        execution_time_ms=1500.0
                    )


class TestServiceInitialization:
    """Test conversation services initialization"""

    @pytest.mark.asyncio
    async def test_initialize_services_success(self):
        """Test successful service initialization"""
        # Mock all dependencies
        with patch('src.api.websocket_endpoints.get_conversation_config') as mock_config:
            with patch('src.api.websocket_endpoints.MultiLevelCache') as mock_cache:
                with patch('src.api.websocket_endpoints.QueryOptimizer') as mock_monitor:
                    with patch('src.api.websocket_endpoints.ZepClient') as mock_zep:
                        with patch('src.api.websocket_endpoints.GroqClient') as mock_groq:
                            with patch('src.api.websocket_endpoints.ConversationAgent') as mock_agent:

                                # Setup config mock
                                mock_config.return_value = MagicMock()
                                mock_config.return_value.zep_api_key = "test_key"
                                mock_config.return_value.groq_api_key = "test_groq_key"
                                mock_config.return_value.openrouter_api_key = None
                                mock_config.return_value.openrouter_base_url = None

                                # Setup cache mock
                                mock_cache_instance = AsyncMock()
                                mock_cache_instance.initialize = AsyncMock()
                                mock_cache.return_value = mock_cache_instance

                                # Setup monitor mock
                                mock_monitor.return_value = MagicMock()

                                # Setup agent mock
                                mock_agent_instance = AsyncMock()
                                mock_agent_instance.initialize = AsyncMock(return_value=True)
                                mock_agent.return_value = mock_agent_instance

                                # Initialize services
                                await initialize_conversation_services()

                                # Verify agent was created and initialized
                                mock_agent.assert_called_once()
                                mock_agent_instance.initialize.assert_called_once()


# Run tests if executed directly
if __name__ == "__main__":
    print("Running WebSocket Endpoint Tests...")
    pytest.main([__file__, "-v"])