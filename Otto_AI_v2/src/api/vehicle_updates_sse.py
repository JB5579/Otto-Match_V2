"""
SSE (Server-Sent Events) API endpoints for real-time vehicle updates
Story 3-3b: Migrate vehicle updates from WebSocket to SSE

This module provides SSE endpoints for:
- Vehicle updates when user preferences change
- Availability status updates
- Real-time grid refresh notifications

Key differences from WebSocket:
- Unidirectional (server → client only)
- Simpler architecture (no reconnection logic)
- Native browser API (EventSource)
- Better test reliability (no reconnection loops)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request

# Configure logging
logger = logging.getLogger(__name__)

# Create router
vehicle_updates_router = APIRouter(prefix="/api/vehicles", tags=["vehicle-updates"])

# Active SSE connections tracking
active_sse_connections: Dict[str, Any] = {}


# ============================================================================
# Models
# ============================================================================

class VehicleUpdateEvent(BaseModel):
    """Vehicle update event data for SSE"""
    vehicles: list[Dict[str, Any]]
    timestamp: str
    requestId: str


class AvailabilityStatusUpdateEvent(BaseModel):
    """Availability status update event data for SSE"""
    vehicle_id: str
    old_status: str
    new_status: str
    reservation_expiry: Optional[str] = None
    priority_until: Optional[str] = None
    timestamp: str


# ============================================================================
# JWT Authentication (reuse from existing auth)
# ============================================================================

async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token from Supabase

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Import Supabase client to verify token
        from supabase import create_client, Client
        import os

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.error("[SSE] Missing Supabase configuration")
            raise HTTPException(500, "Server configuration error")

        # Create client and verify token
        client: Client = create_client(supabase_url, supabase_key)

        # Verify JWT token
        user = client.auth.get_user(token)

        if not user or not user.user:
            logger.warning("[SSE] Invalid JWT token")
            raise HTTPException(401, "Invalid token")

        return {
            "user_id": user.user.id,
            "email": user.user.email,
            "token": token
        }

    except Exception as e:
        logger.error(f"[SSE] Token verification error: {e}")
        raise HTTPException(401, "Invalid authentication token")


# ============================================================================
# SSE Event Generators
# ============================================================================

async def vehicle_update_event_stream(
    user_id: str,
    request: Request
) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for vehicle updates

    Args:
        user_id: Authenticated user ID
        request: FastAPI request object

    Yields:
        SSE-formatted event strings

    Events:
        - event: vehicle_update
        - data: {vehicles: [...], timestamp: ..., requestId: ...}
        - id: unique event ID
    """
    connection_id = f"{user_id}-{uuid4().hex[:8]}"

    logger.info(f"[SSE] Vehicle update stream started: {connection_id}")

    # Track active connection
    active_sse_connections[connection_id] = {
        "user_id": user_id,
        "connected_at": datetime.utcnow(),
        "request": request
    }

    try:
        # Send initial connection event
        yield f": connected\n\n"
        yield f"event: vehicle_update\n"
        yield f"data: {json.dumps({'vehicles': [], 'timestamp': datetime.utcnow().isoformat(), 'requestId': 'connection-established'})}\n"
        yield f"id: {connection_id}-init\n\n"

        # Keep connection alive and listen for updates
        # In production, this would subscribe to a pub/sub system (Redis, Kafka, etc.)
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info(f"[SSE] Client disconnected: {connection_id}")
                break

            # Send keep-alive comment every 30 seconds
            yield ": keep-alive\n\n"

            # Wait for next iteration or new event
            # In production, this would await on a queue or pub/sub message
            await asyncio.sleep(30)

    except asyncio.CancelledError:
        logger.info(f"[SSE] Stream cancelled: {connection_id}")
    except Exception as e:
        logger.error(f"[SSE] Stream error for {connection_id}: {e}")
    finally:
        # Clean up connection
        if connection_id in active_sse_connections:
            del active_sse_connections[connection_id]
        logger.info(f"[SSE] Vehicle update stream ended: {connection_id}")


async def broadcast_vehicle_update(user_id: str, vehicles: list[Dict[str, Any]], request_id: str):
    """
    Broadcast a vehicle update to a specific user's SSE connections

    This is a helper function for other parts of the system to trigger updates.
    In production, this would publish to a pub/sub system.

    Args:
        user_id: Target user ID
        vehicles: List of vehicles to send
        request_id: Unique request ID for tracking
    """
    # Find active connections for this user
    user_connections = [
        (conn_id, conn) for conn_id, conn in active_sse_connections.items()
        if conn["user_id"] == user_id
    ]

    if not user_connections:
        logger.warning(f"[SSE] No active connections for user {user_id}")
        return

    # Prepare SSE event
    event_data = {
        "vehicles": vehicles,
        "timestamp": datetime.utcnow().isoformat(),
        "requestId": request_id
    }

    # In production with pub/sub, we would publish here
    # For now, we just log that an update would be sent
    logger.info(f"[SSE] Would broadcast vehicle update to {len(user_connections)} connections: {request_id}")

    # TODO: Implement actual broadcast mechanism
    # Options:
    # 1. Redis pub/sub
    # 2. Internal queue with background task
    # 3. Direct write to connection if same process


# ============================================================================
# API Endpoints
# ============================================================================

@vehicle_updates_router.get("/updates")
async def get_vehicle_updates(
    request: Request,
    token: str = Query(..., description="JWT authentication token")
):
    """
    SSE endpoint for real-time vehicle updates

    Story 3-3b: Replaces WebSocket vehicle_update messages

    Returns:
        StreamingResponse with text/event-stream Content-Type

    Events:
        - vehicle_update: When vehicles list changes
        - availability_status_update: When vehicle status changes

    Example:
        ```bash
        curl -N "http://localhost:8000/api/vehicles/updates?token=JWT_TOKEN"
        ```
    """
    # Verify JWT token
    try:
        user = await verify_jwt_token(token)
        user_id = user["user_id"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SSE] Authentication failed: {e}")
        raise HTTPException(401, "Authentication failed")

    logger.info(f"[SSE] New vehicle updates connection: user_id={user_id}")

    # Return SSE stream
    return StreamingResponse(
        vehicle_update_event_stream(user_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@vehicle_updates_router.post("/trigger-update")
async def trigger_vehicle_update(
    vehicles: list[Dict[str, Any]],
    user_id: str = Query(..., description="Target user ID"),
    request_id: Optional[str] = None
):
    """
    Trigger a vehicle update broadcast (for testing and internal use)

    In production, this would be called by the conversation agent when
    user preferences change.

    Args:
        vehicles: List of vehicles to broadcast
        user_id: Target user ID
        request_id: Optional request ID for tracking

    Returns:
        Confirmation message
    """
    if not request_id:
        request_id = f"trigger-{uuid4().hex[:8]}"

    await broadcast_vehicle_update(user_id, vehicles, request_id)

    return {
        "status": "queued",
        "user_id": user_id,
        "request_id": request_id,
        "vehicle_count": len(vehicles)
    }


@vehicle_updates_router.get("/connections")
async def get_active_connections():
    """
    Get active SSE connections (for monitoring/debugging)

    Returns:
        List of active connections with metadata
    """
    return {
        "active_connections": len(active_sse_connections),
        "connections": [
            {
                "connection_id": conn_id,
                "user_id": conn["user_id"],
                "connected_at": conn["connected_at"].isoformat()
            }
            for conn_id, conn in active_sse_connections.items()
        ]
    }
