"""
WebSocket API endpoints for Otto.AI Conversational Interface
Handles real-time communication between users and Otto AI
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.routing import APIRouter
import websockets

from src.monitoring.query_optimizer import QueryOptimizer
from src.cache.multi_level_cache import MultiLevelCache
from src.conversation.conversation_agent import ConversationAgent
from src.services.voice_input_service import VoiceInputService, VoiceResult
from src.models.voice_models import VoiceCommand, parse_vehicle_command, VoiceState
from src.memory.zep_client import ZepClient
from src.conversation.groq_client import GroqClient
from src.config.conversation_config import get_conversation_config, start_config_hot_reload, stop_config_hot_reload

# Configure logging
logger = logging.getLogger(__name__)

# Create router
conversation_router = APIRouter(prefix="/ws", tags=["conversation"])

# Global stores for active connections
active_connections: Dict[str, Dict[str, Any]] = {}
connection_lock = asyncio.Lock()
max_connections_per_user = 5
connection_timeout = 300  # 5 minutes
heartbeat_interval = 30  # 30 seconds

# Circuit breaker state
circuit_breaker_state = {
    "failure_count": 0,
    "last_failure_time": None,
    "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
    "failure_threshold": 5,
    "recovery_timeout": 60  # seconds
}

# Service health status
service_health = {
    "conversation_agent": False,
    "zep_client": False,
    "groq_client": False,
    "last_check": None
}


class ConnectionManager:
    """Manages WebSocket connections with pooling and heartbeat"""

    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self.heartbeat_task = None

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept and track a new WebSocket connection"""
        await websocket.accept()

        # Generate unique connection ID
        connection_id = str(uuid4())

        async with self.lock:
            # Check per-user connection limit
            user_connections = [c for c in self.connections.values() if c["user_id"] == user_id]
            if len(user_connections) >= max_connections_per_user:
                await websocket.close(code=1008, reason="Too many connections")
                raise HTTPException(status_code=429, detail="Too many connections")

            # Store connection
            self.connections[connection_id] = {
                "websocket": websocket,
                "user_id": user_id,
                "connected_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "message_count": 0,
                "is_alive": True
            }

        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Remove a connection"""
        async with self.lock:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                connection["is_alive"] = False

                try:
                    await connection["websocket"].close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket {connection_id}: {e}")

                del self.connections[connection_id]
                logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send a message to a specific connection"""
        async with self.lock:
            if connection_id not in self.connections:
                logger.warning(f"Connection {connection_id} not found")
                return False

            connection = self.connections[connection_id]
            if not connection["is_alive"]:
                return False

            try:
                await connection["websocket"].send_text(json.dumps(message))
                connection["message_count"] += 1
                return True
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                connection["is_alive"] = False
                return False

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a user"""
        sent_count = 0
        async with self.lock:
            for conn_id, conn in list(self.connections.items()):
                if conn["user_id"] == user_id and conn["is_alive"]:
                    if await self.send_message(conn_id, message):
                        sent_count += 1

        return sent_count

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        async with self.lock:
            total_connections = len(self.connections)
            unique_users = len(set(c["user_id"] for c in self.connections.values()))

            # Calculate average message count
            avg_messages = 0
            if self.connections:
                avg_messages = sum(c["message_count"] for c in self.connections.values()) / total_connections

            return {
                "total_connections": total_connections,
                "unique_users": unique_users,
                "average_messages_per_connection": avg_messages,
                "max_connections_per_user": max_connections_per_user
            }

    async def start_heartbeat_monitor(self):
        """Start background task to monitor connection health"""
        async def heartbeat_loop():
            while True:
                await asyncio.sleep(heartbeat_interval)
                await self.check_heartbeats()

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info("Heartbeat monitor started")

    async def check_heartbeats(self):
        """Check connection health and send heartbeats"""
        now = datetime.now()
        dead_connections = []

        async with self.lock:
            for conn_id, conn in list(self.connections.items()):
                # Check if connection has timed out
                time_since_heartbeat = (now - conn["last_heartbeat"]).total_seconds()

                if time_since_heartbeat > connection_timeout:
                    dead_connections.append(conn_id)
                    continue

                # Send heartbeat ping
                try:
                    await conn["websocket"].ping()
                    conn["last_heartbeat"] = now
                except Exception as e:
                    logger.warning(f"Heartbeat failed for {conn_id}: {e}")
                    dead_connections.append(conn_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            await self.disconnect(conn_id)


# Initialize connection manager and services
connection_manager = ConnectionManager()
conversation_agent = None
voice_service = None
cache = None
performance_monitor = None
voice_sessions = {}  # Track active voice sessions per user


class CircuitBreaker:
    """Circuit breaker pattern for service resilience"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


# Initialize circuit breaker
circuit_breaker = CircuitBreaker()


async def check_service_health() -> Dict[str, bool]:
    """Check health of all conversation services"""
    health_status = {
        "conversation_agent": False,
        "zep_client": False,
        "groq_client": False
    }

    try:
        # Check conversation agent
        if conversation_agent:
            agent_health = await conversation_agent.health_check()
            health_status["conversation_agent"] = agent_health.get("initialized", False)

        # Check Zep client
        if conversation_agent and conversation_agent.zep_client:
            zep_health = await conversation_agent.zep_client.health_check()
            health_status["zep_client"] = zep_health.get("initialized", False)

        # Check Groq client
        if conversation_agent and conversation_agent.groq_client:
            groq_health = await conversation_agent.groq_client.health_check()
            health_status["groq_client"] = groq_health.get("initialized", False)

    except Exception as e:
        logger.error(f"Service health check failed: {e}")

    service_health.update(health_status)
    service_health["last_check"] = datetime.now()

    return health_status


async def get_fallback_response(message_type: str = "service_unavailable") -> Dict[str, Any]:
    """Get fallback response when services are unavailable"""
    fallback_responses = {
        "service_unavailable": {
            "type": "system",
            "event": "degraded_service",
            "data": {
                "message": "I'm experiencing some technical difficulties, but I'm still here to help! "
                          "You can ask me general questions about vehicles, and I'll do my best to assist.",
                "fallback_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        },
        "slow_response": {
            "type": "system",
            "event": "slow_response",
            "data": {
                "message": "I'm thinking... Please give me a moment to find the best information for you.",
                "fallback_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        },
        "timeout": {
            "type": "error",
            "event": "timeout",
            "data": {
                "message": "I'm taking longer than expected to respond. Let's try a simpler question or try again in a moment.",
                "fallback_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        }
    }

    return fallback_responses.get(message_type, fallback_responses["service_unavailable"])


async def enforce_response_timeout(coro, timeout_ms: float):
    """Enforce response timeout with circuit breaker"""
    try:
        # Add timeout to coroutine
        result = await asyncio.wait_for(coro, timeout=timeout_ms/1000)

        # Check if response meets performance requirement
        if hasattr(result, 'processing_time_ms') and result.processing_time_ms > timeout_ms:
            logger.warning(f"Response exceeded timeout: {result.processing_time_ms:.2f}ms > {timeout_ms}ms")
            circuit_breaker._on_failure()
            return None

        return result

    except asyncio.TimeoutError:
        logger.warning(f"Response timeout after {timeout_ms}ms")
        circuit_breaker._on_failure()
        return None
    except Exception as e:
        logger.error(f"Response enforcement failed: {e}")
        circuit_breaker._on_failure()
        return None


async def handle_voice_start(connection_id: str, user_id: str):
    """Handle voice input start request"""
    global voice_sessions

    # Check if user already has active voice session
    if user_id in voice_sessions:
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "session_exists",
            "data": {
                "message": "Voice session already active",
                "timestamp": datetime.now().isoformat()
            }
        })
        return

    # Check if voice service is available
    if not voice_service or not voice_service.is_browser_supported():
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "unsupported",
            "data": {
                "message": "Voice input not supported on this device/browser",
                "timestamp": datetime.now().isoformat()
            }
        })
        return

    # Define callbacks for voice recognition
    async def on_voice_result(voice_result: VoiceResult):
        # Send voice result to client
        await connection_manager.send_message(connection_id, {
            "type": "voice_result",
            "event": "interim_result" if not voice_result.is_final else "final_result",
            "data": {
                "transcript": voice_result.transcript,
                "confidence": voice_result.confidence,
                "is_final": voice_result.is_final,
                "timestamp": voice_result.timestamp
            }
        })

        # If final result, also process through conversation agent
        if voice_result.is_final and conversation_agent:
            voice_message = {
                "type": "voice_result",
                "content": voice_result.transcript,
                "data": {
                    "transcript": voice_result.transcript,
                    "confidence": voice_result.confidence,
                    "is_final": True,
                    "timestamp": voice_result.timestamp
                }
            }
            await process_conversation_message(connection_id, user_id, session_id, voice_message)

    async def on_voice_error(error: Dict):
        # Send error to client
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "recognition_error",
            "data": {
                "error": error.get("error", "unknown"),
                "message": error.get("message", "Voice recognition error"),
                "timestamp": error.get("timestamp", datetime.now().isoformat())
            }
        })

    # Start voice session
    success = await conversation_agent.start_voice_session(
        user_id=user_id,
        result_callback=on_voice_result,
        error_callback=on_voice_error
    )

    if success:
        voice_sessions[user_id] = {
            "connection_id": connection_id,
            "started_at": datetime.now()
        }
        await connection_manager.send_message(connection_id, {
            "type": "voice_started",
            "event": "listening_started",
            "data": {
                "message": "Listening... Speak now",
                "timestamp": datetime.now().isoformat()
            }
        })
    else:
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "start_failed",
            "data": {
                "message": "Failed to start voice recognition",
                "timestamp": datetime.now().isoformat()
            }
        })


async def handle_voice_stop(connection_id: str, user_id: str):
    """Handle voice input stop request"""
    global voice_sessions

    # Check if user has active voice session
    if user_id not in voice_sessions:
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "no_active_session",
            "data": {
                "message": "No active voice session",
                "timestamp": datetime.now().isoformat()
            }
        })
        return

    # Stop voice session
    success = await conversation_agent.stop_voice_session()

    if success:
        del voice_sessions[user_id]
        await connection_manager.send_message(connection_id, {
            "type": "voice_stopped",
            "event": "listening_stopped",
            "data": {
                "message": "Voice input stopped",
                "timestamp": datetime.now().isoformat()
            }
        })
    else:
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "stop_failed",
            "data": {
                "message": "Failed to stop voice recognition",
                "timestamp": datetime.now().isoformat()
            }
        })


async def handle_voice_abort(connection_id: str, user_id: str):
    """Handle voice input abort request"""
    global voice_sessions

    # Check if user has active voice session
    if user_id not in voice_sessions:
        await connection_manager.send_message(connection_id, {
            "type": "voice_error",
            "event": "no_active_session",
            "data": {
                "message": "No active voice session",
                "timestamp": datetime.now().isoformat()
            }
        })
        return

    # Abort voice session
    if voice_service:
        voice_service.abort_listening()

    # Clean up session
    del voice_sessions[user_id]

    await connection_manager.send_message(connection_id, {
        "type": "voice_aborted",
        "event": "listening_aborted",
        "data": {
            "message": "Voice input cancelled",
            "timestamp": datetime.now().isoformat()
        }
    })


async def initialize_conversation_services():
    """Initialize conversation services on startup"""
    global conversation_agent, voice_service, cache, performance_monitor

    try:
        # Get configuration
        config = get_conversation_config()

        # Initialize cache
        cache = MultiLevelCache(
            local_cache_size=1000,
            redis_url=os.getenv('REDIS_URL'),
            enable_edge_cache=True
        )
        await cache.initialize()

        # Initialize performance monitor
        performance_monitor = QueryOptimizer()

        # Initialize voice service
        voice_service = VoiceInputService()
        if voice_service.is_browser_supported():
            logger.info("Voice input service initialized with browser support")
        else:
            logger.warning("Voice input not supported in this environment")

        # Initialize conversation agent with voice service
        zep_client = ZepClient(api_key=config.zep_api_key, cache=cache)
        groq_client = GroqClient(
            api_key=config.groq_api_key or config.openrouter_api_key,
            base_url=config.openrouter_base_url if config.openrouter_api_key else None
        )

        conversation_agent = ConversationAgent(
            zep_client=zep_client,
            groq_client=groq_client,
            cache=cache,
            voice_service=voice_service
        )

        # Initialize the agent
        success = await conversation_agent.initialize()
        if success:
            logger.info("Conversation services initialized successfully")

            # Perform initial health check
            await check_service_health()

            # Log service status
            logger.info(f"Service health status: {service_health}")

            # Start configuration hot-reload if enabled
            await start_config_hot_reload()

        else:
            logger.error("Failed to initialize conversation services")
            # Don't raise exception - allow system to start in degraded mode

    except Exception as e:
        logger.error(f"Error initializing conversation services: {e}")
        # Continue without conversation services - will use fallback responses


@conversation_router.websocket("/conversation/{user_id}")
async def conversation_endpoint(websocket: WebSocket, user_id: str):
    """
    Main WebSocket endpoint for Otto AI conversations
    Handles real-time message exchange between users and Otto AI
    """
    connection_id = None
    session_id = f"ws_session_{uuid4()}"

    try:
        # Validate service health before accepting connection
        health_status = await check_service_health()

        # Check critical services
        if not health_status.get("conversation_agent", False):
            logger.error(f"Rejecting connection for user {user_id}: Conversation agent not healthy")
            await websocket.close(code=1013, reason="Service temporarily unavailable")
            return

        # Establish connection
        connection_id = await connection_manager.connect(websocket, user_id)

        # Send welcome message
        welcome_message = {
            "type": "system",
            "event": "connected",
            "data": {
                "message": "Welcome to Otto AI! How can I help you find your perfect vehicle today?",
                "connection_id": connection_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        await connection_manager.send_message(connection_id, welcome_message)

        # Handle incoming messages
        while True:
            # Receive message with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=connection_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Connection {connection_id} timed out")
                break

            # Parse message
            try:
                message = json.loads(data)
                message["timestamp"] = datetime.now().isoformat()

                # Add connection metadata
                if connection_id in connection_manager.connections:
                    connection_manager.connections[connection_id]["last_heartbeat"] = datetime.now()

                # Process message using conversation agent
                await process_conversation_message(connection_id, user_id, session_id, message)

            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "event": "invalid_format",
                    "data": {
                        "message": "Invalid JSON format. Please send valid JSON messages.",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await connection_manager.send_message(connection_id, error_message)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        error_message = {
            "type": "error",
            "event": "server_error",
            "data": {
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat()
            }
        }
        if connection_id:
            await connection_manager.send_message(connection_id, error_message)

    finally:
        # Cleanup
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def process_conversation_message(connection_id: str, user_id: str, session_id: str, message: Dict[str, Any]):
    """
    Process incoming conversation messages using the conversation agent
    """
    message_type = message.get("type", "text")
    content = message.get("content", "")

    if message_type == "heartbeat":
        # Respond to heartbeat
        response = {
            "type": "heartbeat",
            "event": "pong",
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        }
        await connection_manager.send_message(connection_id, response)
        return

    if message_type in ["text", "voice_result"] and content:
        # Get configuration for timeout
        config = get_conversation_config()
        response_timeout = config.response_timeout_ms

        # Handle voice input
        voice_result = None
        if message_type == "voice_result":
            # Extract voice data from message
            voice_data = message.get("data", {})
            transcript = voice_data.get("transcript", content)
            confidence = voice_data.get("confidence", 0.8)
            is_final = voice_data.get("is_final", True)

            # Create VoiceResult object
            voice_result = VoiceResult(
                transcript=transcript,
                confidence=confidence,
                is_final=is_final,
                timestamp=datetime.now().timestamp()
            )

        # Process with conversation agent with timeout enforcement
        try:
            # Record query start time for performance monitoring
            query_text = f"voice:{user_id}:{voice_result.transcript[:50]}" if voice_result else f"conversation:{user_id}:{content[:50]}"
            if performance_monitor:
                await performance_monitor.record_query(
                    query_text=query_text,
                    execution_time_ms=0,  # Will be updated after response
                    rows_examined=1,
                    rows_returned=1,
                    cache_hit=False,
                    query_type="voice" if voice_result else "conversation"
                )

            # Check circuit breaker state
            if circuit_breaker.state == "OPEN":
                logger.warning(f"Circuit breaker open for user {user_id}, using fallback")
                response = await get_fallback_response("service_unavailable")
                await connection_manager.send_message(connection_id, response)
                return

            # Get response from conversation agent with timeout
            if conversation_agent:
                # Send initial acknowledgment immediately
                ack_response = await get_fallback_response("slow_response")
                await connection_manager.send_message(connection_id, ack_response)

                # Process with timeout and circuit breaker
                agent_response = await enforce_response_timeout(
                    conversation_agent.process_message(
                        user_id=user_id,
                        message=voice_result.transcript if voice_result else content,
                        session_id=session_id,
                        voice_result=voice_result
                    ),
                    response_timeout
                )

                # If timeout or failure, return fallback
                if agent_response is None:
                    logger.warning(f"Response timeout for user {user_id}, using fallback")
                    response = await get_fallback_response("timeout")
                    await connection_manager.send_message(connection_id, response)
                    return

                # Format WebSocket response
                response = {
                    "type": agent_response.response_type,
                    "event": "message_processed",
                    "data": {
                        "message": agent_response.message,
                        "response_type": agent_response.response_type,
                        "suggestions": agent_response.suggestions,
                        "needs_follow_up": agent_response.needs_follow_up,
                        "processing_time_ms": agent_response.processing_time_ms,
                        "timestamp": datetime.now().isoformat(),
                        **(agent_response.metadata or {})
                    }
                }

                # Add vehicle results if available
                if agent_response.vehicle_results:
                    response["data"]["vehicle_results"] = agent_response.vehicle_results

                # Update performance monitoring
                if performance_monitor and agent_response.processing_time_ms:
                    await performance_monitor.update_query_time(
                        query_text=f"conversation:{user_id}:{content[:50]}",
                        execution_time_ms=agent_response.processing_time_ms
                    )

                # Check if response meets performance requirement
                if agent_response.processing_time_ms and agent_response.processing_time_ms > response_timeout:
                    logger.warning(f"Slow conversation response for user {user_id}: {agent_response.processing_time_ms:.2f}ms > {response_timeout}ms")
                    # Trigger circuit breaker on slow responses
                    circuit_breaker._on_failure()

            else:
                # Fallback if conversation agent not initialized
                response = await get_fallback_response("service_unavailable")

        except Exception as e:
            logger.error(f"Error processing conversation message: {e}")
            # Use circuit breaker on exceptions
            circuit_breaker._on_failure()
            response = await get_fallback_response("service_unavailable")

        # Send response
        await connection_manager.send_message(connection_id, response)

    elif message_type == "voice_request":
        # Handle voice control messages (start, stop, abort)
        voice_action = message.get("event", "").lower()

        if voice_action == "start":
            # Start voice input session
            await handle_voice_start(connection_id, user_id)
        elif voice_action == "stop":
            # Stop voice input session
            await handle_voice_stop(connection_id, user_id)
        elif voice_action == "abort":
            # Abort voice input session
            await handle_voice_abort(connection_id, user_id)
        else:
            # Unknown voice action
            error_message = {
                "type": "voice_error",
                "event": "unknown_action",
                "data": {
                    "message": f"Unknown voice action: {voice_action}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            await connection_manager.send_message(connection_id, error_message)

    else:
        # Handle unknown message types
        error_message = {
            "type": "error",
            "event": "unknown_message_type",
            "data": {
                "message": f"Unsupported message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
        }
        await connection_manager.send_message(connection_id, error_message)


@conversation_router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    stats = await connection_manager.get_connection_stats()

    # Add service health and circuit breaker status
    stats.update({
        "service_health": service_health,
        "circuit_breaker": {
            "state": circuit_breaker.state,
            "failure_count": circuit_breaker.failure_count,
            "failure_threshold": circuit_breaker.failure_threshold
        }
    })

    return stats


@conversation_router.get("/health")
async def get_service_health():
    """Get comprehensive service health status"""
    # Refresh health status
    await check_service_health()

    # Get circuit breaker status
    cb_status = {
        "state": circuit_breaker.state,
        "failure_count": circuit_breaker.failure_count,
        "failure_threshold": circuit_breaker.failure_threshold,
        "last_failure": circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None
    }

    return {
        "status": "healthy" if all(service_health.values()) else "degraded",
        "services": service_health,
        "circuit_breaker": cb_status,
        "last_check": service_health["last_check"].isoformat() if service_health["last_check"] else None
    }


# Startup and shutdown handlers
async def start_websocket_services():
    """Initialize WebSocket services"""
    # Start heartbeat monitoring
    await connection_manager.start_heartbeat_monitor()

    # Initialize performance monitoring
    # TODO: Initialize from Story 1.8 patterns
    logger.info("WebSocket services initialized")


async def stop_websocket_services():
    """Cleanup WebSocket services"""
    # Cancel heartbeat task
    if connection_manager.heartbeat_task:
        connection_manager.heartbeat_task.cancel()
        try:
            await connection_manager.heartbeat_task
        except asyncio.CancelledError:
            pass

    # Close all connections
    async with connection_lock:
        for conn_id in list(connection_manager.connections.keys()):
            await connection_manager.disconnect(conn_id)

    # Stop configuration hot-reload
    await stop_config_hot_reload()

    logger.info("WebSocket services stopped")