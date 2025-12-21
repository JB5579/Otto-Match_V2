"""
Otto.AI Realtime Module

Implements Story 1.6: Vehicle Favorites and Notifications
Real-time services for price monitoring and WebSocket connections
"""

from .favorites_websocket_service import (
    FavoritesWebSocketService,
    WebSocketConnection,
    PriceChangeAlert
)

__all__ = [
    'FavoritesWebSocketService',
    'WebSocketConnection',
    'PriceChangeAlert'
]