"""
Integration tests for Otto.AI Conversation System
Tests end-to-end WebSocket communication with all services
"""

import asyncio
import json
import pytest
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.api.websocket_endpoints import (
    conversation_endpoint,
    process_conversation_message,
    check_service_health,
    get_fallback_response,
    initialize_conversation_services
)
from src.conversation.conversation_agent import ConversationAgent, ConversationResponse
from src.memory.zep_client import ZepClient
from src.conversation.groq_client import GroqClient
from src.config.conversation_config import ConversationConfig

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
async def test_config():
    """Get test configuration"""
    return ConversationConfig(
        zep_api_key="test_zep_key",
        groq_api_key="test_groq_key",
        response_timeout_ms=2000.0,
        websocket_timeout=30,
        websocket_heartbeat_interval=5
    )


@pytest.fixture
async def mock_clients():
    """Create mock clients for testing"""
    zep_client = AsyncMock(spec=ZepClient)
    zep_client.initialize.return_value = True
    zep_client.health_check.return_value = {"initialized": True}
    zep_client.store_conversation.return_value = None
    zep_client.get_contextual_memory.return_value = MagicMock(
        working_memory=[],
        episodic_memory=[],
        semantic_memory={},
        user_preferences={}
    )

    groq_client = AsyncMock(spec=GroqClient)
    groq_client.initialize.return_value = True
    groq_client.health_check.return_value = {"initialized": True}
    groq_client.analyze_message_intent.return_value = {
        "analysis": {
            "intent": "question",
            "entities": {"vehicle_types": ["SUV"]}
        }
    }
    groq_client.format_conversation_response.return_value = "I can help you find SUVs!"

    return zep_client, groq_client


@pytest.fixture
async def conversation_agent(mock_clients):
    """Create conversation agent with mock clients"""
    zep_client, groq_client = mock_clients
    agent = ConversationAgent(
        zep_client=zep_client,
        groq_client=groq_client,
        cache=None
    )
    await agent.initialize()
    return agent


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios"""

    @pytest.mark.asyncio
    async def test_service_health_check(self, conversation_agent):
        """Test service health validation"""
        # Patch the global conversation_agent
        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            health = await check_service_health()

            assert health["conversation_agent"] is True
            assert health["zep_client"] is True
            assert health["groq_client"] is True

    @pytest.mark.asyncio
    async def test_message_processing_with_timeout(self, conversation_agent):
        """Test message processing with timeout enforcement"""
        # Mock a slow response
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(3)  # Simulate 3 second delay
            return ConversationResponse(
                message="Slow response",
                response_type="text",
                processing_time_ms=3000
            )

        conversation_agent.process_message = slow_process

        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            # Mock connection manager
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                message = {
                    "type": "text",
                    "content": "Find me an SUV",
                    "timestamp": datetime.now().isoformat()
                }

                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )

                # Should have sent two messages: acknowledgment and timeout fallback
                assert mock_connection_manager.send_message.call_count == 2

                # Check that fallback response was sent
                last_call = mock_connection_manager.send_message.call_args_list[-1]
                response_data = last_call[0][1]  # Second argument (response dict)
                assert response_data["type"] == "error"
                assert response_data["event"] == "timeout"

    @pytest.mark.asyncio
    async def test_message_processing_success(self, conversation_agent):
        """Test successful message processing"""
        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            # Mock connection manager
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                message = {
                    "type": "text",
                    "content": "Find me an SUV",
                    "timestamp": datetime.now().isoformat()
                }

                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )

                # Should have sent two messages: acknowledgment and response
                assert mock_connection_manager.send_message.call_count == 2

                # Check the actual response
                response_call = mock_connection_manager.send_message.call_args_list[1]
                response_data = response_call[0][1]
                assert response_data["type"] == "text"
                assert response_data["event"] == "message_processed"

    @pytest.mark.asyncio
    async def test_fallback_responses(self):
        """Test fallback response generation"""
        # Test service unavailable fallback
        fallback = await get_fallback_response("service_unavailable")
        assert fallback["type"] == "system"
        assert fallback["event"] == "degraded_service"
        assert "technical difficulties" in fallback["data"]["message"]

        # Test timeout fallback
        fallback = await get_fallback_response("timeout")
        assert fallback["type"] == "error"
        assert fallback["event"] == "timeout"

        # Test slow response fallback
        fallback = await get_fallback_response("slow_response")
        assert fallback["type"] == "system"
        assert fallback["event"] == "slow_response"

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, conversation_agent):
        """Test circuit breaker behavior during failures"""
        from src.api.websocket_endpoints import circuit_breaker

        # Reset circuit breaker
        circuit_breaker.state = "CLOSED"
        circuit_breaker.failure_count = 0

        # Mock consecutive failures
        async def failing_process(*args, **kwargs):
            raise Exception("Service unavailable")

        conversation_agent.process_message = failing_process

        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            # Mock connection manager
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                message = {
                    "type": "text",
                    "content": "Test message",
                    "timestamp": datetime.now().isoformat()
                }

                # Trigger failures to open circuit breaker
                for _ in range(6):  # Exceed failure threshold
                    await process_conversation_message(
                        connection_id="test_conn",
                        user_id="test_user",
                        session_id="test_session",
                        message=message
                    )

                # Circuit breaker should be open now
                assert circuit_breaker.state == "OPEN"

                # Next message should be rejected immediately
                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )

                # Should only send one message (the service unavailable fallback)
                assert mock_connection_manager.send_message.call_count >= 1

                # Check that service unavailable response was sent
                last_call = mock_connection_manager.send_message.call_args_list[-1]
                response_data = last_call[0][1]
                assert response_data["event"] == "degraded_service"


class TestServiceInitialization:
    """Test service initialization scenarios"""

    @pytest.mark.asyncio
    async def test_full_initialization(self, mock_clients):
        """Test successful initialization of all services"""
        zep_client, groq_client = mock_clients

        with patch('src.api.websocket_endpoints.ZepClient', return_value=zep_client), \
             patch('src.api.websocket_endpoints.GroqClient', return_value=groq_client), \
             patch('src.api.websocket_endpoints.MultiLevelCache') as mock_cache, \
             patch('src.api.websocket_endpoints.QueryOptimizer') as mock_optimizer, \
             patch('src.api.websocket_endpoints.get_conversation_config') as mock_config:

            mock_config.return_value = ConversationConfig(
                zep_api_key="test_key",
                groq_api_key="test_key"
            )
            mock_cache.return_value.initialize.return_value = None

            await initialize_conversation_services()

            from src.api.websocket_endpoints import conversation_agent, service_health
            assert conversation_agent is not None
            assert conversation_agent.initialized is True

    @pytest.mark.asyncio
    async def test_partial_initialization_degraded_mode(self):
        """Test system starts in degraded mode when services fail"""
        with patch('src.api.websocket_endpoints.ZepClient') as mock_zep, \
             patch('src.api.websocket_endpoints.GroqClient') as mock_groq, \
             patch('src.api.websocket_endpoints.MultiLevelCache') as mock_cache, \
             patch('src.api.websocket_endpoints.QueryOptimizer') as mock_optimizer, \
             patch('src.api.websocket_endpoints.get_conversation_config') as mock_config:

            # Mock failed initialization
            mock_zep.return_value.initialize.return_value = False
            mock_groq.return_value.initialize.return_value = False
            mock_config.return_value = ConversationConfig()

            mock_cache.return_value.initialize.return_value = None

            # Should not raise exception
            await initialize_conversation_services()

            from src.api.websocket_endpoints import conversation_agent
            # Agent should still exist but not be initialized
            assert conversation_agent is not None


class TestWebSocketConnectionLifecycle:
    """Test WebSocket connection management"""

    @pytest.mark.asyncio
    async def test_connection_rejection_unhealthy_service(self):
        """Test connection rejection when service is unhealthy"""
        from src.api.websocket_endpoints import service_health

        # Set service as unhealthy
        service_health["conversation_agent"] = False

        mock_websocket = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Test endpoint with unhealthy service
        with patch('src.api.websocket_endpoints.connection_manager') as mock_manager:
            mock_manager.connect.return_value = "test_conn_id"

            # Should reject connection
            await conversation_endpoint(mock_websocket, "test_user")

            # Verify connection was closed with error code
            mock_websocket.close.assert_called_once_with(code=1013, reason="Service temporarily unavailable")

    @pytest.mark.asyncio
    async def test_heartbeat_handling(self):
        """Test WebSocket heartbeat message handling"""
        mock_connection_manager = AsyncMock()
        mock_connection_manager.send_message.return_value = True

        with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }

            await process_conversation_message(
                connection_id="test_conn",
                user_id="test_user",
                session_id="test_session",
                message=heartbeat_message
            )

            # Should send pong response
            mock_connection_manager.send_message.assert_called_once()
            response = mock_connection_manager.send_message.call_args[0][1]
            assert response["type"] == "heartbeat"
            assert response["event"] == "pong"

    @pytest.mark.asyncio
    async def test_unknown_message_type_handling(self):
        """Test handling of unknown message types"""
        mock_connection_manager = AsyncMock()
        mock_connection_manager.send_message.return_value = True

        with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
            unknown_message = {
                "type": "unknown_type",
                "content": "Test content",
                "timestamp": datetime.now().isoformat()
            }

            await process_conversation_message(
                connection_id="test_conn",
                user_id="test_user",
                session_id="test_session",
                message=unknown_message
            )

            # Should send error response
            mock_connection_manager.send_message.assert_called_once()
            response = mock_connection_manager.send_message.call_args[0][1]
            assert response["type"] == "error"
            assert response["event"] == "unknown_message_type"


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for conversation system"""

    @pytest.mark.asyncio
    async def test_response_time_under_2_seconds(self, conversation_agent):
        """Benchmark that responses are under 2 seconds"""
        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            start_time = datetime.now()

            # Process message
            response = await conversation_agent.process_message(
                user_id="test_user",
                message="Find me an SUV",
                session_id="test_session"
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify response time
            assert processing_time < 2000, f"Response took {processing_time:.2f}ms, expected < 2000ms"
            assert response.processing_time_ms < 2000

    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, conversation_agent):
        """Test concurrent message processing"""
        with patch('src.api.websocket_endpoints.conversation_agent', conversation_agent):
            # Create multiple concurrent tasks
            tasks = []
            for i in range(10):
                task = conversation_agent.process_message(
                    user_id=f"user_{i}",
                    message=f"Find me a vehicle {i}",
                    session_id=f"session_{i}"
                )
                tasks.append(task)

            # Process all concurrently
            start_time = datetime.now()
            responses = await asyncio.gather(*tasks)
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            # Verify all responses
            assert len(responses) == 10
            assert all(r.response_type == "text" for r in responses)

            # Concurrent processing should be faster than sequential
            avg_time_per_response = total_time / 10
            logger.info(f"Average response time for 10 concurrent requests: {avg_time_per_response:.2f}ms")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])