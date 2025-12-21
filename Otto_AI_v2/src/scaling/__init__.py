"""
Scaling Module for Otto.AI
Connection pooling and horizontal scaling utilities
"""

from .connection_pool import (
    DatabaseConfig,
    ConnectionMetrics,
    PoolStatistics,
    PooledConnection,
    ConnectionPool,
    LoadBalancedPoolManager,
    pool_manager
)

__all__ = [
    'DatabaseConfig',
    'ConnectionMetrics',
    'PoolStatistics',
    'PooledConnection',
    'ConnectionPool',
    'LoadBalancedPoolManager',
    'pool_manager'
]