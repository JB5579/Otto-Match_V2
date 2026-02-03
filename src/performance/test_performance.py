"""
Performance tests for Otto.AI Conversation System
Validates < 2 second response time requirement under load
"""

import asyncio
import json
import pytest
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.websocket_endpoints import (
    ConnectionManager,
    process_conversation_message,
    circuit_breaker,
    enforce_response_timeout
)
from src.conversation.conversation_agent import ConversationAgent, ConversationResponse
from src.memory.zep_client import ZepClient
from src.conversation.groq_client import GroqClient
from src.config.conversation_config import ConversationConfig

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWebSocketPerformance:
    """Performance tests for WebSocket communication"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time_under_2_seconds_single_message(self):
        """Test that single message response is under 2 seconds"""
        # Create mock conversation agent with controlled response time
        mock_agent = AsyncMock(spec=ConversationAgent)
        mock_agent.process_message.return_value = ConversationResponse(
            message="Quick response",
            response_type="text",
            processing_time_ms=1500
        )

        with patch('src.api.websocket_endpoints.conversation_agent', mock_agent):
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                message = {
                    "type": "text",
                    "content": "Find me a vehicle",
                    "timestamp": datetime.now().isoformat()
                }

                start_time = time.time()
                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )
                end_time = time.time()

                processing_time_ms = (end_time - start_time) * 1000

                # Verify performance requirement
                assert processing_time_ms < 2000, f"Response took {processing_time_ms:.2f}ms, expected < 2000ms"
                logger.info(f"Single message response time: {processing_time_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time_enforcement_timeout(self):
        """Test that responses exceeding 2 seconds are timed out"""
        # Create mock agent with slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(3)  # 3 second delay
            return ConversationResponse(
                message="Too slow response",
                response_type="text",
                processing_time_ms=3000
            )

        mock_agent = AsyncMock(spec=ConversationAgent)
        mock_agent.process_message = slow_response

        with patch('src.api.websocket_endpoints.conversation_agent', mock_agent):
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                message = {
                    "type": "text",
                    "content": "Find me a vehicle",
                    "timestamp": datetime.now().isoformat()
                }

                start_time = time.time()
                await process_conversation_message(
                    connection_id="test_conn",
                    user_id="test_user",
                    session_id="test_session",
                    message=message
                )
                end_time = time.time()

                processing_time_ms = (end_time - start_time) * 1000

                # Should timeout before 3 seconds
                assert processing_time_ms < 3000, f"Response not properly timed out: {processing_time_ms:.2f}ms"
                logger.info(f"Timed out response time: {processing_time_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_connections_performance(self):
        """Test performance with multiple concurrent connections"""
        num_connections = 50
        messages_per_connection = 5

        # Create mock agent
        mock_agent = AsyncMock(spec=ConversationAgent)
        mock_agent.process_message.return_value = ConversationResponse(
            message="Concurrent response",
            response_type="text",
            processing_time_ms=500
        )

        with patch('src.api.websocket_endpoints.conversation_agent', mock_agent):
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                # Create tasks for concurrent processing
                tasks = []
                start_time = time.time()

                for conn_id in range(num_connections):
                    for msg_id in range(messages_per_connection):
                        task = process_conversation_message(
                            connection_id=f"conn_{conn_id}",
                            user_id=f"user_{conn_id}",
                            session_id=f"session_{conn_id}",
                            message={
                                "type": "text",
                                "content": f"Message {msg_id}",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        tasks.append(task)

                # Execute all tasks concurrently
                await asyncio.gather(*tasks)
                end_time = time.time()

                total_time = (end_time - start_time) * 1000
                total_messages = num_connections * messages_per_connection
                avg_time_per_message = total_time / total_messages
                messages_per_second = total_messages / (total_time / 1000)

                # Performance assertions
                assert avg_time_per_message < 2000, f"Average time per message: {avg_time_per_message:.2f}ms"
                assert messages_per_second > 10, f"Messages per second: {messages_per_second:.2f}"

                logger.info(f"Processed {total_messages} messages in {total_time:.2f}ms")
                logger.info(f"Average time per message: {avg_time_per_message:.2f}ms")
                logger.info(f"Messages per second: {messages_per_second:.2f}")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_connection_manager_scalability(self):
        """Test ConnectionManager performance with many connections"""
        manager = ConnectionManager()
        num_connections = 1000

        # Mock WebSockets
        mock_websockets = [AsyncMock() for _ in range(num_connections)]

        start_time = time.time()

        # Connect all mock WebSockets
        connection_ids = []
        for i, websocket in enumerate(mock_websockets):
            conn_id = await manager.connect(websocket, f"user_{i % 100}")  # 100 unique users
            connection_ids.append(conn_id)

        connect_time = time.time() - start_time

        # Test broadcasting
        start_time = time.time()
        sent_count = await manager.broadcast_to_user(
            "user_1",
            {"type": "test", "data": "broadcast message"}
        )
        broadcast_time = time.time() - start_time

        # Get stats
        start_time = time.time()
        stats = await manager.get_connection_stats()
        stats_time = time.time() - start_time

        # Performance assertions
        assert connect_time < 5.0, f"Connecting {num_connections} took {connect_time:.2f}s"
        assert broadcast_time < 0.1, f"Broadcast took {broadcast_time:.3f}s"
        assert stats_time < 0.1, f"Getting stats took {stats_time:.3f}s"
        assert stats["total_connections"] == num_connections

        logger.info(f"Connected {num_connections} connections in {connect_time:.2f}s")
        logger.info(f"Broadcast to user in {broadcast_time:.3f}s")
        logger.info(f"Retrieved stats in {stats_time:.3f}s")

        # Cleanup
        for conn_id in connection_ids:
            await manager.disconnect(conn_id)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_circuit_breaker_performance_impact(self):
        """Test circuit breaker doesn't significantly impact performance"""
        # Reset circuit breaker
        circuit_breaker.state = "CLOSED"
        circuit_breaker.failure_count = 0

        # Create fast mock function
        async def fast_function():
            return {"result": "success"}

        # Measure performance with circuit breaker
        times = []
        for _ in range(100):
            start_time = time.time()
            await circuit_breaker.call(fast_function)
            times.append((time.time() - start_time) * 1000)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Circuit breaker should add minimal overhead
        assert avg_time < 10, f"Circuit breaker adds too much overhead: {avg_time:.2f}ms avg"
        assert max_time < 50, f"Circuit breaker max time too high: {max_time:.2f}ms"

        logger.info(f"Circuit breaker avg overhead: {avg_time:.3f}ms")
        logger.info(f"Circuit breaker max overhead: {max_time:.3f}ms")


class TestMemoryUsagePerformance:
    """Test memory usage and leaks under load"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_conversation_state_memory(self):
        """Test conversation state doesn't grow unbounded"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create conversation agent
        mock_agent = ConversationAgent()

        # Simulate many conversations
        for user_id in range(1000):
            await mock_agent._get_dialogue_state(f"user_{user_id}")
            # Simulate some conversation
            mock_agent.dialogue_states[f"user_{user_id}"].collected_info = {
                "vehicle_type": "SUV",
                "budget": 30000,
                "features": ["Bluetooth", "Backup Camera"]
            }

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Memory increase should be reasonable (< 100MB for 1000 users)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"

        # Clear states
        for user_id in range(1000):
            await mock_agent.reset_conversation(f"user_{user_id}")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_recovered = peak_memory - final_memory

        # Most memory should be recovered
        assert memory_recovered > memory_increase * 0.8, f"Only recovered {memory_recovered:.2f}MB of {memory_increase:.2f}MB"

        logger.info(f"Memory increase: {memory_increase:.2f}MB")
        logger.info(f"Memory recovered: {memory_recovered:.2f}MB")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_websocket_message_buffering(self):
        """Test WebSocket message buffering doesn't cause memory issues"""
        manager = ConnectionManager()

        # Create many connections
        connections = []
        for i in range(100):
            websocket = AsyncMock()
            conn_id = await manager.connect(websocket, f"user_{i}")
            connections.append(conn_id)

        # Send many messages rapidly
        message = {"type": "test", "data": "x" * 1000}  # 1KB message
        num_messages = 10000

        start_time = time.time()
        for conn_id in connections:
            for _ in range(num_messages // len(connections)):
                await manager.send_message(conn_id, message)
        end_time = time.time()

        total_time = end_time - start_time
        messages_per_second = num_messages / total_time

        # Should handle high message throughput
        assert messages_per_second > 1000, f"Low message throughput: {messages_per_second:.2f} msg/s"

        logger.info(f"Sent {num_messages} messages in {total_time:.2f}s")
        logger.info(f"Message throughput: {messages_per_second:.2f} msg/s")

        # Cleanup
        for conn_id in connections:
            await manager.disconnect(conn_id)


class TestTimeoutEnforcementPerformance:
    """Test timeout enforcement mechanisms"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_enforce_response_timeout_accuracy(self):
        """Test timeout enforcement accuracy"""
        timeout_ms = 2000

        # Test with fast function
        async def fast_function():
            await asyncio.sleep(0.1)
            return {"result": "fast"}

        result = await enforce_response_timeout(fast_function(), timeout_ms)
        assert result is not None
        assert result["result"] == "fast"

        # Test with slow function
        async def slow_function():
            await asyncio.sleep(3)
            return {"result": "slow"}

        result = await enforce_response_timeout(slow_function(), timeout_ms)
        assert result is None

        # Test timeout accuracy
        timeouts = []
        for _ in range(10):
            start_time = time.time()
            await enforce_response_timeout(slow_function(), timeout_ms)
            timeouts.append((time.time() - start_time) * 1000)

        avg_timeout = sum(timeouts) / len(timeouts)
        max_timeout = max(timeouts)

        # Should timeout close to specified time (with some tolerance)
        assert timeout_ms * 0.9 <= avg_timeout <= timeout_ms * 1.1, f"Inaccurate timeout: {avg_timeout:.2f}ms"
        assert max_timeout < timeout_ms * 1.2, f"Timeout too slow: {max_timeout:.2f}ms"

        logger.info(f"Average timeout: {avg_timeout:.2f}ms (target: {timeout_ms}ms)")
        logger.info(f"Max timeout: {max_timeout:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_timeout_overhead(self):
        """Test timeout enforcement overhead"""
        timeout_ms = 2000

        # Measure overhead of timeout wrapper
        async def fast_function():
            return {"result": "success"}

        # Without timeout
        times_no_timeout = []
        for _ in range(100):
            start_time = time.time()
            await fast_function()
            times_no_timeout.append((time.time() - start_time) * 1000)

        # With timeout
        times_with_timeout = []
        for _ in range(100):
            start_time = time.time()
            await enforce_response_timeout(fast_function(), timeout_ms)
            times_with_timeout.append((time.time() - start_time) * 1000)

        avg_no_timeout = sum(times_no_timeout) / len(times_no_timeout)
        avg_with_timeout = sum(times_with_timeout) / len(times_with_timeout)
        overhead = avg_with_timeout - avg_no_timeout

        # Timeout overhead should be minimal (< 1ms)
        assert overhead < 1, f"Timeout overhead too high: {overhead:.2f}ms"

        logger.info(f"Function time without timeout: {avg_no_timeout:.3f}ms")
        logger.info(f"Function time with timeout: {avg_with_timeout:.3f}ms")
        logger.info(f"Timeout overhead: {overhead:.3f}ms")


class TestLoadTesting:
    """Comprehensive load testing scenarios"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_sustained_load_performance(self):
        """Test system performance under sustained load"""
        duration_seconds = 30
        target_rps = 50  # requests per second

        mock_agent = AsyncMock(spec=ConversationAgent)
        mock_agent.process_message.return_value = ConversationResponse(
            message="Load test response",
            response_type="text",
            processing_time_ms=500
        )

        with patch('src.api.websocket_endpoints.conversation_agent', mock_agent):
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                # Track performance metrics
                response_times = []
                error_count = 0
                success_count = 0

                async def send_request():
                    nonlocal error_count, success_count
                    try:
                        start_time = time.time()
                        await process_conversation_message(
                            connection_id=f"conn_{success_count}",
                            user_id=f"user_{success_count % 10}",
                            session_id=f"session_{success_count}",
                            message={
                                "type": "text",
                                "content": "Load test message",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        response_time = (time.time() - start_time) * 1000
                        response_times.append(response_time)
                        success_count += 1
                    except Exception:
                        error_count += 1

                # Generate sustained load
                start_time = time.time()
                tasks = []

                while time.time() - start_time < duration_seconds:
                    # Create burst of requests
                    for _ in range(target_rps):
                        tasks.append(send_request())

                    # Wait for 1 second before next burst
                    await asyncio.gather(*tasks)
                    tasks = []
                    await asyncio.sleep(1)

                total_time = time.time() - start_time

                # Calculate metrics
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
                p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0
                actual_rps = success_count / total_time
                error_rate = error_count / (success_count + error_count) if (success_count + error_count) > 0 else 0

                # Performance assertions
                assert avg_response_time < 2000, f"Average response time too high: {avg_response_time:.2f}ms"
                assert p95_response_time < 2000, f"P95 response time too high: {p95_response_time:.2f}ms"
                assert actual_rps >= target_rps * 0.9, f"RPS too low: {actual_rps:.2f} (target: {target_rps})"
                assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"

                logger.info(f"Sustained load test results:")
                logger.info(f"  Duration: {total_time:.2f}s")
                logger.info(f"  Requests: {success_count}")
                logger.info(f"  Errors: {error_count}")
                logger.info(f"  Actual RPS: {actual_rps:.2f}")
                logger.info(f"  Avg response time: {avg_response_time:.2f}ms")
                logger.info(f"  P95 response time: {p95_response_time:.2f}ms")
                logger.info(f"  P99 response time: {p99_response_time:.2f}ms")
                logger.info(f"  Error rate: {error_rate:.2%}")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_burst_load_performance(self):
        """Test system performance under burst load"""
        burst_size = 500  # requests at once
        num_bursts = 5
        delay_between_bursts = 2  # seconds

        mock_agent = AsyncMock(spec=ConversationAgent)
        mock_agent.process_message.return_value = ConversationResponse(
            message="Burst test response",
            response_type="text",
            processing_time_ms=300
        )

        with patch('src.api.websocket_endpoints.conversation_agent', mock_agent):
            mock_connection_manager = AsyncMock()
            mock_connection_manager.send_message.return_value = True

            with patch('src.api.websocket_endpoints.connection_manager', mock_connection_manager):
                all_response_times = []

                for burst_num in range(num_bursts):
                    logger.info(f"Starting burst {burst_num + 1}/{num_bursts}")

                    # Create burst of requests
                    tasks = []
                    for i in range(burst_size):
                        task = process_conversation_message(
                            connection_id=f"conn_{burst_num}_{i}",
                            user_id=f"user_{i % 50}",
                            session_id=f"session_{burst_num}",
                            message={
                                "type": "text",
                                "content": f"Burst message {i}",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        tasks.append(task)

                    # Measure burst performance
                    start_time = time.time()
                    await asyncio.gather(*tasks)
                    burst_time = time.time() - start_time

                    # Calculate burst metrics
                    burst_rps = burst_size / burst_time
                    logger.info(f"Burst {burst_num + 1}: {burst_size} requests in {burst_time:.2f}s ({burst_rps:.2f} RPS)")

                    # Wait between bursts
                    if burst_num < num_bursts - 1:
                        await asyncio.sleep(delay_between_bursts)

                # System should handle bursts without degradation
                assert burst_time < 10, f"Burst took too long: {burst_time:.2f}s"
                assert burst_rps > 50, f"Burst throughput too low: {burst_rps:.2f} RPS"

                logger.info(f"Burst load test completed successfully")


# Performance test runner
if __name__ == "__main__":
    # Run performance tests with markers
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short"
    ])