"""
Otto.AI Collections WebSocket Service

Implements Story 1.7: Add Curated Vehicles Collections and Categories
Real-time WebSocket service for collection updates and trending changes

Features:
- Real-time collection updates via WebSocket
- Live trending collection notifications
- Collection subscription management
- Connection pooling for multiple users
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
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
    subscribed_collections: Set[str] = field(default_factory=set)
    subscriptions: Set[str] = field(default_factory=set)  # 'trending', 'updates'

@dataclass
class CollectionUpdate:
    """Collection update data model"""
    collection_id: str
    update_type: str  # 'created', 'updated', 'deleted', 'trending'
    data: Dict[str, Any]
    timestamp: datetime

class CollectionsWebSocketService:
    """
    Service for managing WebSocket connections for collections
    """

    def __init__(self):
        """Initialize WebSocket service"""
        self.connections: Dict[str, WebSocketConnection] = {}
        self.collection_subscribers: Dict[str, Set[str]] = {}  # collection_id -> connection_ids
        self.global_subscribers: Set[str] = set()  # connection_ids subscribed to all updates
        self.db_conn = None
        self._running = False

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection

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

            logger.info("CollectionsWebSocketService initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CollectionsWebSocketService: {e}")
            return False

    async def add_connection(
        self,
        websocket: Any,
        user_id: str,
        connection_id: Optional[str] = None
    ) -> str:
        """
        Add a new WebSocket connection

        Args:
            websocket: WebSocket instance
            user_id: User identifier
            connection_id: Optional custom connection ID

        Returns:
            Connection ID
        """
        if not connection_id:
            connection_id = str(uuid.uuid4())

        connection = WebSocketConnection(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow()
        )

        self.connections[connection_id] = connection
        logger.info(f"Added WebSocket connection {connection_id} for user {user_id}")

        return connection_id

    async def remove_connection(self, connection_id: str):
        """
        Remove a WebSocket connection

        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # Remove from collection subscriptions
            for collection_id in connection.subscribed_collections:
                if collection_id in self.collection_subscribers:
                    self.collection_subscribers[collection_id].discard(connection_id)

            # Remove from global subscribers
            if connection_id in self.global_subscribers:
                self.global_subscribers.discard(connection_id)

            # Remove connection
            del self.connections[connection_id]
            logger.info(f"Removed WebSocket connection {connection_id}")

    async def subscribe_to_collection(
        self,
        connection_id: str,
        collection_id: str
    ):
        """
        Subscribe connection to collection updates

        Args:
            connection_id: Connection ID
            collection_id: Collection ID to subscribe to
        """
        if connection_id not in self.connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        connection = self.connections[connection_id]
        connection.subscribed_collections.add(collection_id)

        # Add to collection subscribers
        if collection_id not in self.collection_subscribers:
            self.collection_subscribers[collection_id] = set()
        self.collection_subscribers[collection_id].add(connection_id)

        logger.info(f"Connection {connection_id} subscribed to collection {collection_id}")

    async def unsubscribe_from_collection(
        self,
        connection_id: str,
        collection_id: str
    ):
        """
        Unsubscribe connection from collection updates

        Args:
            connection_id: Connection ID
            collection_id: Collection ID to unsubscribe from
        """
        if connection_id in self.connections:
            self.connections[connection_id].subscribed_collections.discard(collection_id)

        if collection_id in self.collection_subscribers:
            self.collection_subscribers[collection_id].discard(connection_id)

        logger.info(f"Connection {connection_id} unsubscribed from collection {collection_id}")

    async def subscribe_to_updates(
        self,
        connection_id: str,
        update_types: List[str]
    ):
        """
        Subscribe connection to global update types

        Args:
            connection_id: Connection ID
            update_types: List of update types ('trending', 'updates')
        """
        if connection_id not in self.connections:
            logger.warning(f"Connection {connection_id} not found")
            return

        connection = self.connections[connection_id]
        connection.subscriptions.update(update_types)

        # Add to global subscribers
        self.global_subscribers.add(connection_id)

        logger.info(f"Connection {connection_id} subscribed to updates: {update_types}")

    async def broadcast_collection_update(self, update: CollectionUpdate):
        """
        Broadcast collection update to subscribers

        Args:
            update: Collection update data
        """
        message = {
            "type": "collection_update",
            "data": {
                "collection_id": update.collection_id,
                "update_type": update.update_type,
                "timestamp": update.timestamp.isoformat(),
                **update.data
            }
        }

        # Send to collection-specific subscribers
        if update.collection_id in self.collection_subscribers:
            for connection_id in self.collection_subscribers[update.collection_id]:
                await self._send_to_connection(connection_id, message)

        # Send to global subscribers
        for connection_id in self.global_subscribers:
            connection = self.connections.get(connection_id)
            if connection and 'updates' in connection.subscriptions:
                await self._send_to_connection(connection_id, message)

    async def broadcast_trending_update(self, trending_collections: List[Dict[str, Any]]):
        """
        Broadcast trending collections update

        Args:
            trending_collections: List of trending collections
        """
        message = {
            "type": "trending_update",
            "data": {
                "collections": trending_collections,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Send to global subscribers
        for connection_id in self.global_subscribers:
            connection = self.connections.get(connection_id)
            if connection and 'trending' in connection.subscriptions:
                await self._send_to_connection(connection_id, message)

    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """
        Send message to specific connection

        Args:
            connection_id: Connection ID
            message: Message to send
        """
        try:
            connection = self.connections.get(connection_id)
            if connection and connection.websocket:
                await connection.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            # Remove broken connection
            await self.remove_connection(connection_id)

    async def ping_connections(self):
        """Ping all connections to check they're still alive"""
        current_time = datetime.utcnow()
        ping_timeout = timedelta(minutes=5)

        dead_connections = []
        for connection_id, connection in self.connections.items():
            if current_time - connection.last_ping > ping_timeout:
                dead_connections.append(connection_id)

        for connection_id in dead_connections:
            await self.remove_connection(connection_id)

    async def start_heartbeat(self):
        """Start heartbeat task to clean up dead connections"""
        self._running = True

        while self._running:
            try:
                await self.ping_connections()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(60)

    def stop_heartbeat(self):
        """Stop heartbeat task"""
        self._running = False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about WebSocket connections

        Returns:
            Dictionary with connection statistics
        """
        total_connections = len(self.connections)
        total_subscriptions = sum(
            len(conn.subscribed_collections)
            for conn in self.connections.values()
        )

        subscription_counts = {}
        for collection_id, subscribers in self.collection_subscribers.items():
            subscription_counts[collection_id] = len(subscribers)

        return {
            "total_connections": total_connections,
            "total_subscriptions": total_subscriptions,
            "collection_subscriptions": subscription_counts,
            "global_subscribers": len(self.global_subscribers),
            "active_connections": [
                {
                    "connection_id": conn.connection_id,
                    "user_id": conn.user_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": list(conn.subscribed_collections),
                    "global_subscriptions": list(conn.subscriptions)
                }
                for conn in self.connections.values()
            ]
        }

    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Handle incoming WebSocket message

        Args:
            connection_id: Connection ID
            message: WebSocket message
        """
        try:
            message_type = message.get('type')
            data = message.get('data', {})

            if message_type == 'subscribe':
                # Subscribe to specific collection
                collection_id = data.get('collection_id')
                if collection_id:
                    await self.subscribe_to_collection(connection_id, collection_id)

            elif message_type == 'unsubscribe':
                # Unsubscribe from collection
                collection_id = data.get('collection_id')
                if collection_id:
                    await self.unsubscribe_from_collection(connection_id, collection_id)

            elif message_type == 'subscribe_updates':
                # Subscribe to global updates
                update_types = data.get('types', [])
                await self.subscribe_to_updates(connection_id, update_types)

            elif message_type == 'ping':
                # Respond to ping
                await self._send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")

    async def close_all_connections(self):
        """Close all WebSocket connections"""
        for connection_id in list(self.connections.keys()):
            await self.remove_connection(connection_id)