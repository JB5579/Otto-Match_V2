"""
Cache Module for Otto.AI
Multi-level caching system for performance optimization
"""

from .multi_level_cache import (
    MultiLevelCache,
    LocalCache,
    RedisCache,
    EdgeCacheSimulator,
    CacheEntry,
    CacheMetrics,
    CacheLevel,
    cache_manager,
    cached
)

__all__ = [
    'MultiLevelCache',
    'LocalCache',
    'RedisCache',
    'EdgeCacheSimulator',
    'CacheEntry',
    'CacheMetrics',
    'CacheLevel',
    'cache_manager',
    'cached'
]