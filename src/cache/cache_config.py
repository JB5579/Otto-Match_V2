"""
Cache Configuration for Otto.AI
Production-ready cache settings and optimization parameters
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    TTL = "time_based"
    ADAPTIVE = "adaptive_hybrid"

@dataclass
class CacheTierConfig:
    """Configuration for a cache tier"""
    enabled: bool
    ttl_seconds: int
    max_size: int
    eviction_strategy: CacheStrategy
    compression: bool = False
    encryption: bool = False
    persistence: bool = False

@dataclass
class CacheConfig:
    """Complete cache configuration"""

    # Tier configurations
    l1_local: CacheTierConfig
    l2_redis: CacheTierConfig
    l3_edge: CacheTierConfig

    # Global settings
    enable_cache_warmup: bool = True
    enable_cache_metrics: bool = True
    enable_adaptive_ttl: bool = True
    cache_key_prefix: str = "otto_ai_v1"

    # Performance settings
    batch_size: int = 100
    max_concurrent_operations: int = 50
    connection_pool_size: int = 20

    # Cache invalidation
    invalidate_on_update: bool = True
    invalidation_delay_seconds: int = 5

    # Warm-up settings
    warmup_concurrency: int = 5
    warmup_timeout_seconds: int = 30

    # Rate limiting for cache operations
    max_ops_per_second: int = 1000

    # Content-specific settings
    content_types: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.content_types is None:
            self.content_types = {
                "search_results": {
                    "l1_ttl": 300,      # 5 minutes
                    "l2_ttl": 3600,     # 1 hour
                    "l3_ttl": 86400,     # 24 hours
                    "compress": True,
                    "edge_cache": True
                },
                "vehicle_details": {
                    "l1_ttl": 600,      # 10 minutes
                    "l2_ttl": 7200,     # 2 hours
                    "l3_ttl": 86400,     # 24 hours
                    "compress": True,
                    "edge_cache": True
                },
                "filters": {
                    "l1_ttl": 1800,     # 30 minutes
                    "l2_ttl": 14400,    # 4 hours
                    "l3_ttl": 86400,     # 24 hours
                    "compress": False,
                    "edge_cache": False
                },
                "recommendations": {
                    "l1_ttl": 900,      # 15 minutes
                    "l2_ttl": 3600,     # 1 hour
                    "l3_ttl": 43200,     # 12 hours
                    "compress": True,
                    "edge_cache": True
                },
                "analytics": {
                    "l1_ttl": 60,       # 1 minute
                    "l2_ttl": 300,      # 5 minutes
                    "l3_ttl": 0,        # No edge caching
                    "compress": True,
                    "edge_cache": False
                }
            }

# Default production configuration
DEFAULT_CACHE_CONFIG = CacheConfig(
    l1_local=CacheTierConfig(
        enabled=True,
        ttl_seconds=300,
        max_size=1000,
        eviction_strategy=CacheStrategy.LRU,
        compression=False,
        encryption=False,
        persistence=False
    ),
    l2_redis=CacheTierConfig(
        enabled=True,
        ttl_seconds=3600,
        max_size=10000,
        eviction_strategy=CacheStrategy.LRU,
        compression=True,
        encryption=False,
        persistence=True
    ),
    l3_edge=CacheTierConfig(
        enabled=True,
        ttl_seconds=86400,
        max_size=100000,
        eviction_strategy=CacheStrategy.TTL,
        compression=True,
        encryption=False,
        persistence=False
    )
)

# Development configuration
DEV_CACHE_CONFIG = CacheConfig(
    l1_local=CacheTierConfig(
        enabled=True,
        ttl_seconds=60,
        max_size=100,
        eviction_strategy=CacheStrategy.LRU
    ),
    l2_redis=CacheTierConfig(
        enabled=False,
        ttl_seconds=300,
        max_size=1000,
        eviction_strategy=CacheStrategy.LRU
    ),
    l3_edge=CacheTierConfig(
        enabled=False,
        ttl_seconds=0,
        max_size=0,
        eviction_strategy=CacheStrategy.TTL
    ),
    enable_cache_warmup=False,
    warmup_concurrency=1
)

# High-traffic configuration
HIGH_TRAFFIC_CACHE_CONFIG = CacheConfig(
    l1_local=CacheTierConfig(
        enabled=True,
        ttl_seconds=180,
        max_size=5000,
        eviction_strategy=CacheStrategy.ADAPTIVE,
        compression=True
    ),
    l2_redis=CacheTierConfig(
        enabled=True,
        ttl_seconds=7200,
        max_size=50000,
        eviction_strategy=CacheStrategy.LFU,
        compression=True,
        persistence=True
    ),
    l3_edge=CacheTierConfig(
        enabled=True,
        ttl_seconds=86400,
        max_size=1000000,
        eviction_strategy=CacheStrategy.TTL,
        compression=True
    ),
    max_concurrent_operations=100,
    max_ops_per_second=5000
)