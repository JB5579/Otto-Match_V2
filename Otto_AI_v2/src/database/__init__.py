"""
Database Module for Otto.AI
Database optimization and performance tuning utilities
"""

from .pgvector_optimizer import (
    PGVectorOptimizer,
    IndexConfiguration,
    IndexStatistics,
    QueryPerformanceMetrics,
    pgvector_optimizer
)

__all__ = [
    'PGVectorOptimizer',
    'IndexConfiguration',
    'IndexStatistics',
    'QueryPerformanceMetrics',
    'pgvector_optimizer'
]