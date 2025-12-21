"""
Connection Pool Manager for Otto.AI
Implements Story 1-8: Horizontal scaling with connection pooling

Features:
- Async connection pooling for PostgreSQL
- Dynamic pool sizing based on load
- Connection health monitoring and recovery
- Load balancing across multiple database instances
- Connection metrics and performance monitoring
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque
import random
import hashlib
import os

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "require"
    application_name: str = "otto_ai_pool"
    max_connections: int = 20
    min_connections: int = 2
    connect_timeout: float = 10.0
    command_timeout: float = 30.0
    keepalives_idle: int = 30
    keepalives_interval: int = 10
    keepalives_count: int = 3

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_queries: int = 0
    avg_query_time_ms: float = 0.0
    max_query_time_ms: float = 0.0
    pool_utilization_percent: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

@dataclass
class PoolStatistics:
    """Pool-wide statistics"""
    created_at: datetime = field(default_factory=datetime.now)
    total_connections_created: int = 0
    total_connections_closed: int = 0
    peak_connections: int = 0
    avg_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    connection_reuse_count: int = 0

class PooledConnection:
    """Wrapper for a pooled database connection"""

    def __init__(self, connection: psycopg.AsyncConnection, pool: 'ConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.last_query_time = 0.0
        self.query_count = 0
        self.is_active = False
        self.is_healthy = True

    async def execute(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query with timing"""
        start_time = time.time()
        self.is_active = True
        self.last_used = datetime.now()

        try:
            result = await self.connection.execute(query, params)
            query_time = (time.time() - start_time) * 1000

            self.last_query_time = query_time
            self.query_count += 1
            self.pool.metrics.total_queries += 1

            # Update query time statistics
            self.pool._update_query_time_stats(query_time)

            return result

        except Exception as e:
            self.is_healthy = False
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            self.is_active = False

    async def fetch(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Fetch query results"""
        start_time = time.time()
        self.is_active = True
        self.last_used = datetime.now()

        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                result = await cur.fetchall()

            query_time = (time.time() - start_time) * 1000
            self.last_query_time = query_time
            self.query_count += 1
            self.pool.metrics.total_queries += 1

            self.pool._update_query_time_stats(query_time)
            return result

        except Exception as e:
            self.is_healthy = False
            logger.error(f"Query fetch failed: {e}")
            raise
        finally:
            self.is_active = False

    async def fetchone(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single query result"""
        start_time = time.time()
        self.is_active = True
        self.last_used = datetime.now()

        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                result = await cur.fetchone()

            query_time = (time.time() - start_time) * 1000
            self.last_query_time = query_time
            self.query_count += 1
            self.pool.metrics.total_queries += 1

            self.pool._update_query_time_stats(query_time)
            return result

        except Exception as e:
            self.is_healthy = False
            logger.error(f"Query fetchone failed: {e}")
            raise
        finally:
            self.is_active = False

    async def close(self):
        """Close the connection"""
        await self.connection.close()

class ConnectionPool:
    """Async connection pool for PostgreSQL"""

    def __init__(
        self,
        config: DatabaseConfig,
        pool_name: str = "default",
        auto_resize: bool = True,
        health_check_interval: float = 30.0
    ):
        self.config = config
        self.pool_name = pool_name
        self.auto_resize = auto_resize
        self.health_check_interval = health_check_interval

        # Connection management
        self.available_connections: deque[PooledConnection] = deque()
        self.active_connections: Set[PooledConnection] = set()
        self.all_connections: Set[PooledConnection] = set()

        # Metrics and statistics
        self.metrics = ConnectionMetrics()
        self.statistics = PoolStatistics()

        # Pool state
        self.is_initialized = False
        self.is_shutting_down = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.resize_task: Optional[asyncio.Task] = None

        # Synchronization
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)

    async def initialize(self) -> bool:
        """Initialize the connection pool"""
        try:
            if self.is_initialized:
                return True

            logger.info(f"🚀 Initializing connection pool '{self.pool_name}'...")

            # Create minimum connections
            await self._create_connections(self.config.min_connections)

            # Start background tasks
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            if self.auto_resize:
                self.resize_task = asyncio.create_task(self._auto_resize_loop())

            self.is_initialized = True
            logger.info(f"✅ Connection pool '{self.pool_name}' initialized with {len(self.all_connections)} connections")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool '{self.pool_name}': {e}")
            return False

    async def acquire(self, timeout: Optional[float] = None) -> PooledConnection:
        """Acquire a connection from the pool"""
        if not self.is_initialized:
            raise RuntimeError(f"Pool '{self.pool_name}' not initialized")

        if self.is_shutting_down:
            raise RuntimeError(f"Pool '{self.pool_name}' is shutting down")

        timeout = timeout or self.config.connect_timeout
        start_time = time.time()

        async with self._condition:
            while True:
                # Check for available connection
                if self.available_connections:
                    conn = self.available_connections.popleft()
                    if conn.is_healthy:
                        self.active_connections.add(conn)
                        conn.last_used = datetime.now()
                        self.statistics.connection_reuse_count += 1
                        logger.debug(f"Acquired connection from pool '{self.pool_name}'")
                        return conn
                    else:
                        # Remove unhealthy connection
                        self.all_connections.discard(conn)
                        await self._close_connection(conn)

                # Try to create new connection if under limit
                if len(self.all_connections) < self.config.max_connections:
                    try:
                        conn = await self._create_connection()
                        self.active_connections.add(conn)
                        return conn
                    except Exception as e:
                        logger.error(f"Failed to create new connection: {e}")

                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Timeout waiting for connection from pool '{self.pool_name}'")

                # Wait for connection to become available
                try:
                    await asyncio.wait_for(self._condition.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

    async def release(self, connection: PooledConnection):
        """Release a connection back to the pool"""
        if connection not in self.active_connections:
            logger.warning(f"Connection not found in active connections for pool '{self.pool_name}'")
            return

        async with self._condition:
            self.active_connections.remove(connection)

            if connection.is_healthy and not self.is_shutting_down:
                self.available_connections.append(connection)
                logger.debug(f"Released connection to pool '{self.pool_name}'")
            else:
                # Close unhealthy connection
                self.all_connections.discard(connection)
                await self._close_connection(connection)

            self._condition.notify()

    async def execute(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query using pool connection"""
        conn = await self.acquire()
        try:
            return await conn.execute(query, params)
        finally:
            await self.release(conn)

    async def fetch(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Fetch results using pool connection"""
        conn = await self.acquire()
        try:
            return await conn.fetch(query, params)
        finally:
            await self.release(conn)

    async def fetchone(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result using pool connection"""
        conn = await self.acquire()
        try:
            return await conn.fetchone(query, params)
        finally:
            await self.release(conn)

    async def close(self):
        """Close the connection pool"""
        logger.info(f"🔌 Closing connection pool '{self.pool_name}'...")

        self.is_shutting_down = True

        # Cancel background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.resize_task:
            self.resize_task.cancel()

        # Close all connections
        async with self._lock:
            for conn in list(self.all_connections):
                await self._close_connection(conn)

            self.all_connections.clear()
            self.available_connections.clear()
            self.active_connections.clear()

        self.is_initialized = False
        logger.info(f"✅ Connection pool '{self.pool_name}' closed")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get pool performance metrics"""
        async with self._lock:
            total = len(self.all_connections)
            active = len(self.active_connections)
            idle = len(self.available_connections)

            self.metrics.total_connections = total
            self.metrics.active_connections = active
            self.metrics.idle_connections = idle
            self.metrics.pool_utilization_percent = (active / max(total, 1)) * 100

            return {
                "pool_name": self.pool_name,
                "metrics": asdict(self.metrics),
                "statistics": asdict(self.statistics),
                "config": {
                    "min_connections": self.config.min_connections,
                    "max_connections": self.config.max_connections,
                    "auto_resize": self.auto_resize
                }
            }

    async def _create_connection(self) -> PooledConnection:
        """Create a new database connection"""
        connection_string = (
            f"postgresql://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
            f"?sslmode={self.config.ssl_mode}"
        )

        conn = await psycopg.AsyncConnection.connect(
            connection_string,
            autocommit=True,
            application_name=self.config.application_name,
            connect_timeout=self.config.connect_timeout,
            command_timeout=self.config.command_timeout,
            keepalives_idle=self.config.keepalives_idle,
            keepalives_interval=self.config.keepalives_interval,
            keepalives_count=self.config.keepalives_count
        )

        # Register pgvector extension
        register_vector(conn)

        pooled_conn = PooledConnection(conn, self)
        self.all_connections.add(pooled_conn)
        self.statistics.total_connections_created += 1

        # Update peak connections
        current_size = len(self.all_connections)
        if current_size > self.statistics.peak_connections:
            self.statistics.peak_connections = current_size

        return pooled_conn

    async def _create_connections(self, count: int):
        """Create multiple connections"""
        tasks = [self._create_connection() for _ in range(count)]
        connections = await asyncio.gather(*tasks, return_exceptions=True)

        for conn in connections:
            if isinstance(conn, Exception):
                logger.error(f"Failed to create connection: {conn}")
                self.metrics.failed_connections += 1
            else:
                self.available_connections.append(conn)

    async def _close_connection(self, connection: PooledConnection):
        """Close a connection"""
        try:
            await connection.close()
            self.statistics.total_connections_closed += 1
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    async def _health_check_loop(self):
        """Periodic health check for connections"""
        while not self.is_shutting_down:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self):
        """Perform health check on all connections"""
        async with self._lock:
            for conn in list(self.all_connections):
                if conn not in self.active_connections:
                    try:
                        # Simple health check
                        async with conn.connection.cursor() as cur:
                            await cur.execute("SELECT 1")
                        conn.is_healthy = True
                    except Exception as e:
                        logger.warning(f"Connection health check failed: {e}")
                        conn.is_healthy = False

                        # Remove unhealthy connection
                        if conn in self.available_connections:
                            self.available_connections.remove(conn)
                        self.all_connections.discard(conn)
                        await self._close_connection(conn)

    async def _auto_resize_loop(self):
        """Automatically resize pool based on load"""
        while not self.is_shutting_down:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._adjust_pool_size()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-resize error: {e}")

    async def _adjust_pool_size(self):
        """Adjust pool size based on current load"""
        async with self._lock:
            current_size = len(self.all_connections)
            active_count = len(self.active_connections)

            # Calculate desired size based on recent usage
            desired_size = max(
                self.config.min_connections,
                min(
                    self.config.max_connections,
                    active_count * 2 + self.config.min_connections
                )
            )

            # Scale up if needed
            if desired_size > current_size and current_size < self.config.max_connections:
                add_count = min(desired_size - current_size, 2)  # Add max 2 at a time
                await self._create_connections(add_count)
                logger.info(f"Scaled up pool '{self.pool_name}' by {add_count} connections")

            # Scale down if possible
            elif desired_size < current_size and current_size > self.config.min_connections:
                remove_count = min(current_size - desired_size, 2)  # Remove max 2 at a time
                removed = 0
                while removed < remove_count and self.available_connections:
                    conn = self.available_connections.popleft()
                    if not conn.is_active:
                        self.all_connections.discard(conn)
                        await self._close_connection(conn)
                        removed += 1

                if removed > 0:
                    logger.info(f"Scaled down pool '{self.pool_name}' by {removed} connections")

    def _update_query_time_stats(self, query_time: float):
        """Update query time statistics"""
        # Update max query time
        if query_time > self.metrics.max_query_time_ms:
            self.metrics.max_query_time_ms = query_time

        # Update average query time
        if self.metrics.total_queries > 0:
            total_time = self.metrics.avg_query_time_ms * (self.metrics.total_queries - 1) + query_time
            self.metrics.avg_query_time_ms = total_time / self.metrics.total_queries

class LoadBalancedPoolManager:
    """Manages multiple connection pools for load balancing"""

    def __init__(self, pool_configs: List[DatabaseConfig]):
        self.pool_configs = pool_configs
        self.pools: Dict[str, ConnectionPool] = {}
        self.round_robin_index = 0
        self.health_check_interval = 30.0

    async def initialize(self) -> bool:
        """Initialize all connection pools"""
        logger.info(f"🚀 Initializing load-balanced pool manager with {len(self.pool_configs)} pools...")

        for i, config in enumerate(self.pool_configs):
            pool_name = f"pool_{i}"
            pool = ConnectionPool(config, pool_name=pool_name)

            if await pool.initialize():
                self.pools[pool_name] = pool
                logger.info(f"✅ Initialized pool '{pool_name}'")
            else:
                logger.error(f"❌ Failed to initialize pool '{pool_name}'")

        success = len(self.pools) > 0
        logger.info(f"Load-balanced pool manager initialization: {'SUCCESS' if success else 'FAILED'}")
        return success

    async def acquire(self, pool_name: Optional[str] = None, strategy: str = "round_robin") -> Tuple[PooledConnection, str]:
        """Acquire connection using load balancing strategy"""
        if not self.pools:
            raise RuntimeError("No pools available")

        if pool_name:
            # Direct pool selection
            if pool_name not in self.pools:
                raise ValueError(f"Pool '{pool_name}' not found")
            selected_pool = pool_name
        else:
            # Load balancing strategy
            selected_pool = self._select_pool(strategy)

        if not selected_pool:
            raise RuntimeError("No healthy pool available")

        connection = await self.pools[selected_pool].acquire()
        return connection, selected_pool

    async def release(self, connection: PooledConnection, pool_name: str):
        """Release connection to specific pool"""
        if pool_name in self.pools:
            await self.pools[pool_name].release(connection)

    async def execute(self, query: str, params: Optional[Tuple] = None, pool_name: Optional[str] = None) -> Any:
        """Execute query with load balancing"""
        conn, used_pool = await self.acquire(pool_name)
        try:
            return await conn.execute(query, params)
        finally:
            await self.release(conn, used_pool)

    async def fetch(self, query: str, params: Optional[Tuple] = None, pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch results with load balancing"""
        conn, used_pool = await self.acquire(pool_name)
        try:
            return await conn.fetch(query, params)
        finally:
            await self.release(conn, used_pool)

    async def close(self):
        """Close all connection pools"""
        logger.info("🔌 Closing all connection pools...")

        for pool_name, pool in self.pools.items():
            await pool.close()

        self.pools.clear()
        logger.info("✅ All connection pools closed")

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all pools"""
        return {
            pool_name: pool.get_metrics()
            for pool_name, pool in self.pools.items()
        }

    def _select_pool(self, strategy: str) -> Optional[str]:
        """Select pool based on load balancing strategy"""
        healthy_pools = [
            (name, pool) for name, pool in self.pools.items()
            if pool.metrics.failed_connections == 0 or pool.metrics.total_connections > 0
        ]

        if not healthy_pools:
            return None

        if strategy == "round_robin":
            # Round-robin selection
            pool_names = [name for name, _ in healthy_pools]
            selected = pool_names[self.round_robin_index % len(pool_names)]
            self.round_robin_index += 1
            return selected

        elif strategy == "least_connections":
            # Select pool with least active connections
            return min(healthy_pools, key=lambda x: x[1].metrics.active_connections)[0]

        elif strategy == "random":
            # Random selection
            return random.choice([name for name, _ in healthy_pools])

        else:
            # Default to first healthy pool
            return healthy_pools[0][0]

# Global pool manager
pool_manager: Optional[LoadBalancedPoolManager] = None