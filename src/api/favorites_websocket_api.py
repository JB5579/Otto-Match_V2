"""
Otto.AI Favorites WebSocket API Endpoints

Implements Story 1.6: Vehicle Favorites and Notifications
WebSocket endpoints for real-time price monitoring and notifications

Endpoints:
- WebSocket /ws/favorites/{user_id} - Real-time favorites updates
- GET /api/favorites/websocket/stats - WebSocket connection statistics
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Path
from fastapi.responses import JSONResponse
import sys
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.realtime_services.favorites_websocket_service import FavoritesWebSocketService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API Router Setup
# ============================================================================

# Create router for WebSocket endpoints
websocket_router = APIRouter(
    tags=["Favorites WebSocket"],
    responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
)

# Global WebSocket service instance
websocket_service: Optional[FavoritesWebSocketService] = None

async def get_websocket_service() -> FavoritesWebSocketService:
    """Get WebSocket service instance"""
    global websocket_service
    if websocket_service is None:
        websocket_service = FavoritesWebSocketService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=500,
                detail="Missing Supabase configuration"
            )

        success = await websocket_service.initialize(supabase_url, supabase_key)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize WebSocket service"
            )

    return websocket_service

# ============================================================================
# Helper Functions
# ============================================================================

def _get_user_from_websocket(websocket: WebSocket) -> str:
    """
    Extract user ID from WebSocket headers or query parameters
    In production, this would validate WebSocket authentication token
    """
    # TODO: Implement proper WebSocket authentication
    # For now, use query parameter or header
    user_id = websocket.query_params.get('user_id')
    if not user_id:
        # Try headers
        user_id = websocket.headers.get('x-user-id')

    if not user_id:
        # For development, use a default
        user_id = "test_user_123"

    return user_id

async def _handle_websocket_message(
    websocket: WebSocket,
    connection_id: str,
    message: Dict[str, Any],
    service: FavoritesWebSocketService
) -> None:
    """
    Handle incoming WebSocket message

    Args:
        websocket: WebSocket connection
        connection_id: Connection identifier
        message: Parsed message
        service: WebSocket service instance
    """
    try:
        message_type = message.get('type')

        if message_type == 'subscribe':
            vehicle_id = message.get('vehicle_id')
            if vehicle_id:
                success = await service.subscribe_to_vehicle(connection_id, vehicle_id)
                response = {
                    'type': 'subscription_response',
                    'vehicle_id': vehicle_id,
                    'success': success,
                    'message': 'Subscribed successfully' if success else 'Failed to subscribe'
                }
                await websocket.send_text(json.dumps(response))

        elif message_type == 'unsubscribe':
            vehicle_id = message.get('vehicle_id')
            if vehicle_id:
                success = await service.unsubscribe_from_vehicle(connection_id, vehicle_id)
                response = {
                    'type': 'unsubscription_response',
                    'vehicle_id': vehicle_id,
                    'success': success,
                    'message': 'Unsubscribed successfully' if success else 'Failed to unsubscribe'
                }
                await websocket.send_text(json.dumps(response))

        elif message_type == 'ping':
            # Echo ping back as pong
            response = {
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(response))

        elif message_type == 'get_subscriptions':
            # Get current subscriptions for this connection
            if connection_id in service.active_connections:
                subscriptions = list(service.active_connections[connection_id].subscribed_vehicles)
                response = {
                    'type': 'subscriptions_response',
                    'subscriptions': subscriptions,
                    'count': len(subscriptions)
                }
                await websocket.send_text(json.dumps(response))

        else:
            # Unknown message type
            response = {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }
            await websocket.send_text(json.dumps(response))

    except Exception as e:
        logger.error(f"❌ Error handling WebSocket message: {e}")
        error_response = {
            'type': 'error',
            'message': 'Internal server error'
        }
        try:
            await websocket.send_text(json.dumps(error_response))
        except:
            pass

# ============================================================================
# WebSocket Endpoints
# ============================================================================

@websocket_router.websocket("/ws/favorites")
async def websocket_favorites_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time favorites updates

    Query Parameters:
    - user_id: User identifier (for development, in production use auth)

    Message Types (Client to Server):
    - subscribe: Subscribe to vehicle price updates
      {"type": "subscribe", "vehicle_id": "vehicle_123"}
    - unsubscribe: Unsubscribe from vehicle price updates
      {"type": "unsubscribe", "vehicle_id": "vehicle_123"}
    - ping: Ping connection
      {"type": "ping"}
    - get_subscriptions: Get current subscriptions
      {"type": "get_subscriptions"}

    Message Types (Server to Client):
    - price_change: Vehicle price change notification
      {"type": "price_change", "vehicle_id": "vehicle_123", "old_price": 30000, "new_price": 27000, "price_drop_percentage": 10.0}
    - subscription_response: Response to subscribe/unsubscribe request
      {"type": "subscription_response", "vehicle_id": "vehicle_123", "success": true}
    - pong: Response to ping
      {"type": "pong", "timestamp": "2025-12-12T10:30:00Z"}
    - connection_status: Connection status updates
      {"type": "connection_status", "status": "connected", "message": "Successfully connected"}
    """
    try:
        # Get WebSocket service
        service = await get_websocket_service()

        # Accept WebSocket connection
        await websocket.accept()

        # Get user ID
        user_id = _get_user_from_websocket(websocket)

        # Register connection
        connection_id = await service.register_connection(user_id, websocket)

        # Send welcome message
        await service.send_connection_status(
            connection_id,
            "connected",
            f"Successfully connected to favorites updates (Connection ID: {connection_id[:8]}...)"
        )

        logger.info(f"🔗 WebSocket connection established for user {user_id}, connection {connection_id}")

        # Handle message loop
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()

                # Parse JSON
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    error_response = {
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue

                # Handle message
                await _handle_websocket_message(websocket, connection_id, message, service)

        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected for user {user_id}, connection {connection_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket error for connection {connection_id}: {e}")
        finally:
            # Unregister connection
            await service.unregister_connection(connection_id)

    except Exception as e:
        logger.error(f"❌ Failed to handle WebSocket connection: {e}")

# ============================================================================
# HTTP API Endpoints for WebSocket Management
# ============================================================================

@websocket_router.get("/stats")
async def get_websocket_stats() -> Dict[str, Any]:
    """
    Get WebSocket connection statistics

    Returns statistics about active connections and monitoring status
    """
    try:
        service = await get_websocket_service()
        stats = await service.get_connection_stats()

        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting WebSocket stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving WebSocket statistics"
        )

@websocket_router.post("/ping")
async def ping_all_connections() -> Dict[str, Any]:
    """
    Ping all active WebSocket connections

    This endpoint triggers a ping to all active connections to check connectivity
    and cleanup dead connections.
    """
    try:
        service = await get_websocket_service()

        # Get stats before ping
        before_stats = await service.get_connection_stats()

        # Ping all connections
        await service.ping_connections()

        # Get stats after ping (to see cleanup effects)
        await asyncio.sleep(1)  # Brief pause for cleanup
        after_stats = await service.get_connection_stats()

        return {
            "status": "success",
            "message": "Ping sent to all active connections",
            "data": {
                "connections_before": before_stats.get("total_connections", 0),
                "connections_after": after_stats.get("total_connections", 0),
                "cleaned_up": before_stats.get("total_connections", 0) - after_stats.get("total_connections", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error pinging connections: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while pinging connections"
        )

@websocket_router.get("/monitoring/{vehicle_id}")
async def get_vehicle_monitoring_status(
    vehicle_id: str = Path(..., description="Vehicle ID to check monitoring status")
) -> Dict[str, Any]:
    """
    Get monitoring status for a specific vehicle

    Returns information about price monitoring for the specified vehicle
    """
    try:
        service = await get_websocket_service()

        # Check if vehicle is being monitored
        is_monitored = vehicle_id in service.vehicle_subscribers
        subscriber_count = len(service.vehicle_subscribers.get(vehicle_id, set()))

        # Get recent price changes for this vehicle
        recent_alerts = [
            alert for alert in service.price_change_history
            if alert.vehicle_id == vehicle_id and
            alert.created_at >= datetime.utcnow() - timedelta(hours=24)
        ]

        return {
            "status": "success",
            "data": {
                "vehicle_id": vehicle_id,
                "is_monitored": is_monitored,
                "subscriber_count": subscriber_count,
                "recent_price_changes": len(recent_alerts),
                "latest_change": recent_alerts[0].created_at.isoformat() if recent_alerts else None,
                "monitoring_active": service.monitoring_active
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting vehicle monitoring status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving vehicle monitoring status"
        )

@websocket_router.get("/alerts")
async def get_recent_price_alerts(
    limit: int = 10,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Get recent price change alerts

    Args:
        limit: Maximum number of alerts to return
        hours: Number of hours to look back for alerts
    """
    try:
        service = await get_websocket_service()

        # Filter recent alerts
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in service.price_change_history
            if alert.created_at >= cutoff_time
        ]

        # Sort by most recent
        recent_alerts.sort(key=lambda x: x.created_at, reverse=True)

        # Limit results
        limited_alerts = recent_alerts[:limit]

        # Format for response
        formatted_alerts = [
            {
                "vehicle_id": alert.vehicle_id,
                "old_price": alert.old_price,
                "new_price": alert.new_price,
                "price_drop_percentage": alert.price_drop_percentage,
                "users_notified_count": len(alert.users_notified),
                "created_at": alert.created_at.isoformat()
            }
            for alert in limited_alerts
        ]

        return {
            "status": "success",
            "data": {
                "alerts": formatted_alerts,
                "total_count": len(recent_alerts),
                "hours_covered": hours
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting recent price alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving price alerts"
        )