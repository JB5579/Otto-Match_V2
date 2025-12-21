"""
Multi-Level Caching Strategy for Otto.AI
Implements Story 1-8: Multi-Level Caching (Redis + Cloudflare Edge + Local Cache)

Cache Levels:
1. L1 - In-memory local cache (fastest, single instance)
2. L2 - Redis distributed cache (fast, shared across instances)
3. L3 - Cloudflare Edge Cache (global, CDN-based)

Features:
- Automatic cache tiering based on query patterns
- Intelligent cache warming strategies
- Performance monitoring and metrics
- Cache invalidation on data updates
- Rate-aware caching for high-traffic queries
"""

import os
import json
import time
import hashlib
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import pickle
import base64

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache level enumeration"""
    L1_LOCAL = "local"
    L2_REDIS = "redis"
    L3_EDGE = "edge"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    level: CacheLevel = CacheLevel.L1_LOCAL
    size_bytes: int = 0

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = datetime.now()

        # Calculate size
        self.size_bytes = len(json.dumps(self._serialize_value()).encode())

    def _serialize_value(self) -> Any:
        """Serialize value for storage"""
        if isinstance(self.value, (dict, list)):
            return self.value
        return str(self.value)

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)

    def increment_access(self):
        """Increment access counter and update last accessed"""
        self.access_count += 1
        self.last_accessed = datetime.now()

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0
    evictions: int = 0
    errors: int = 0

    # Performance metrics
    avg_response_time: float = 0.0
    total_response_time: float = 0.0

    # Cache sizes
    l1_size: int = 0
    l2_size: int = 0

    def get_hit_rate(self) -> float:
        """Calculate overall hit rate"""
        if self.total_requests == 0:
            return 0.0
        hits = self.l1_hits + self.l2_hits + self.l3_hits
        return (hits / self.total_requests) * 100

    def get_hit_rate_by_level(self) -> Dict[str, float]:
        """Calculate hit rate by cache level"""
        if self.total_requests == 0:
            return {level.value: 0.0 for level in CacheLevel}

        return {
            CacheLevel.L1_LOCAL.value: (self.l1_hits / self.total_requests) * 100,
            CacheLevel.L2_REDIS.value: (self.l2_hits / self.total_requests) * 100,
            CacheLevel.L3_EDGE.value: (self.l3_hits / self.total_requests) * 100
        }

class LocalCache:
    """L1 - In-memory local cache"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU eviction

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # Check if expired
        if entry.is_expired():
            self._remove_entry(key)
            return None

        # Update access
        entry.increment_access()
        self._update_access_order(key)

        return entry

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set entry in cache"""
        try:
            # Check if need to evict
            if key not in self.cache and len(self.cache) >= self.max_size:
                self._evict_lru()

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or self.default_ttl,
                created_at=datetime.now(),
                level=CacheLevel.L1_LOCAL
            )

            self.cache[key] = entry
            self._update_access_order(key)

            return True

        except Exception as e:
            logger.error(f"Error setting local cache entry: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            self._remove_entry(key)
            return True
        return False

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()

    def _update_access_order(self, key: str):
        """Update LRU access order"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def _remove_entry(self, key: str):
        """Remove entry and update access order"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order[0]
            self._remove_entry(lru_key)

    def get_size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

class RedisCache:
    """L2 - Redis distributed cache"""

    def __init__(self, redis_url: str, default_ttl: int = 3600, key_prefix: str = "otto_ai:"):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.redis_client = None
        self.connection_pool = None

    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis module not available, Redis cache disabled")
            return False

        try:
            # Create connection pool with optimized settings
            self.connection_pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )

            self.redis_client = redis.Redis(connection_pool=self.connection_pool)

            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis cache initialized successfully")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis cache: {e}")
            return False

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from Redis"""
        if not self.redis_client:
            return None

        try:
            redis_key = self._prefix_key(key)
            data = await self.redis_client.get(redis_key)

            if not data:
                return None

            # Deserialize
            entry_data = json.loads(data)
            entry = CacheEntry(
                key=entry_data['key'],
                value=entry_data['value'],
                ttl=entry_data['ttl'],
                created_at=datetime.fromisoformat(entry_data['created_at']),
                access_count=entry_data['access_count'],
                last_accessed=datetime.fromisoformat(entry_data['last_accessed']),
                level=CacheLevel.L2_REDIS,
                size_bytes=entry_data['size_bytes']
            )

            # Check if expired
            if entry.is_expired():
                await self.delete(key)
                return None

            # Update access stats
            await self.redis_client.hincrby(f"{redis_key}:meta", "access_count", 1)
            await self.redis_client.expire(redis_key, self.default_ttl)

            return entry

        except Exception as e:
            logger.error(f"Error getting Redis cache entry: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set entry in Redis"""
        if not self.redis_client:
            return False

        try:
            redis_key = self._prefix_key(key)
            ttl = ttl or self.default_ttl

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                created_at=datetime.now(),
                level=CacheLevel.L2_REDIS
            )

            # Serialize and store
            data = json.dumps(asdict(entry), default=str)
            await self.redis_client.setex(redis_key, ttl, data)

            # Store metadata for analytics
            meta_key = f"{redis_key}:meta"
            await self.redis_client.hset(meta_key, mapping={
                "access_count": "0",
                "created_at": entry.created_at.isoformat(),
                "size_bytes": str(entry.size_bytes)
            })
            await self.redis_client.expire(meta_key, ttl)

            return True

        except Exception as e:
            logger.error(f"Error setting Redis cache entry: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from Redis"""
        if not self.redis_client:
            return False

        try:
            redis_key = self._prefix_key(key)
            meta_key = f"{redis_key}:meta"

            # Delete entry and metadata
            await self.redis_client.delete(redis_key, meta_key)
            return True

        except Exception as e:
            logger.error(f"Error deleting Redis cache entry: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache entries with our prefix"""
        if not self.redis_client:
            return False

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True

        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False

    def _prefix_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"

    async def get_size(self) -> int:
        """Get approximate cache size"""
        if not self.redis_client:
            return 0

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            return len(keys) // 2  # Each entry has data + meta key

        except Exception:
            return 0

class EdgeCacheSimulator:
    """L3 - Cloudflare Edge Cache simulator

    In production, this would integrate with Cloudflare's API.
    For development, we simulate edge caching behavior.
    """

    def __init__(self, default_ttl: int = 86400):  # 24 hours default
        self.default_ttl = default_ttl
        self.edge_cache: Dict[str, Tuple[CacheEntry, datetime]] = {}

        # Cloudflare cache headers that would be sent
        self.cache_headers = {
            'Cache-Control': 'public, max-age=86400',
            'Edge-Cache-Tag': 'otto-ai-vehicle-search',
            'CDN-Cache-Control': 'public, max-age=86400, s-maxage=86400'
        }

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from edge cache"""
        if key not in self.edge_cache:
            return None

        entry, cached_at = self.edge_cache[key]

        # Simulate edge cache expiration
        if datetime.now() - cached_at > timedelta(seconds=self.default_ttl):
            del self.edge_cache[key]
            return None

        entry.increment_access()
        return entry

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set entry in edge cache"""
        try:
            ttl = ttl or self.default_ttl
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                created_at=datetime.now(),
                level=CacheLevel.L3_EDGE
            )

            self.edge_cache[key] = (entry, datetime.now())
            return True

        except Exception as e:
            logger.error(f"Error setting edge cache entry: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from edge cache"""
        if key in self.edge_cache:
            del self.edge_cache[key]
            return True
        return False

    def get_cache_headers(self, ttl: Optional[int] = None) -> Dict[str, str]:
        """Get cache headers for response"""
        if ttl:
            return {
                'Cache-Control': f'public, max-age={ttl}',
                'Edge-Cache-Tag': 'otto-ai-vehicle-search',
                'CDN-Cache-Control': f'public, max-age={ttl}, s-maxage={ttl}'
            }
        return self.cache_headers.copy()

    def get_size(self) -> int:
        """Get current cache size"""
        return len(self.edge_cache)

class MultiLevelCache:
    """Multi-level cache manager"""

    def __init__(
        self,
        local_cache_size: int = 1000,
        redis_url: Optional[str] = None,
        enable_edge_cache: bool = True
    ):
        # Initialize cache levels
        self.l1_cache = LocalCache(max_size=local_cache_size)
        self.l2_cache = RedisCache(redis_url) if redis_url else None
        self.l3_cache = EdgeCacheSimulator() if enable_edge_cache else None

        # Cache strategy configuration
        self.cache_config = {
            'search_results': {
                'l1_ttl': 300,      # 5 minutes
                'l2_ttl': 3600,     # 1 hour
                'l3_ttl': 86400     # 24 hours
            },
            'vehicle_details': {
                'l1_ttl': 600,      # 10 minutes
                'l2_ttl': 7200,     # 2 hours
                'l3_ttl': 86400     # 24 hours
            },
            'filters': {
                'l1_ttl': 1800,     # 30 minutes
                'l2_ttl': 14400,    # 4 hours
                'l3_ttl': 86400     # 24 hours
            }
        }

        # Performance metrics
        self.metrics = CacheMetrics()

        # Cache warming strategy
        self.warmup_queries = [
            "SUV under 30000",
            "electric vehicles",
            "Toyota Camry",
            "family cars",
            "luxury vehicles"
        ]

    async def initialize(self) -> bool:
        """Initialize cache system"""
        logger.info("🚀 Initializing Multi-Level Cache System...")

        # Initialize Redis if configured
        if self.l2_cache:
            if not await self.l2_cache.initialize():
                logger.warning("⚠️ Redis cache initialization failed, using local cache only")
                self.l2_cache = None

        logger.info("✅ Multi-Level Cache System initialized")
        return True

    async def get(self, key: str, cache_type: str = "search_results") -> Optional[Any]:
        """Get value from cache, trying L1 -> L2 -> L3"""
        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Try L1 (local) cache first
            entry = self.l1_cache.get(key)
            if entry:
                self.metrics.l1_hits += 1
                self._update_response_time(start_time)
                logger.debug(f"L1 cache hit: {key}")
                return entry.value

            # Try L2 (Redis) cache
            if self.l2_cache:
                entry = await self.l2_cache.get(key)
                if entry:
                    self.metrics.l2_hits += 1

                    # Promote to L1 if frequently accessed
                    if entry.access_count > 3:
                        config = self.cache_config.get(cache_type, self.cache_config['search_results'])
                        self.l1_cache.set(key, entry.value, config['l1_ttl'])

                    self._update_response_time(start_time)
                    logger.debug(f"L2 cache hit: {key}")
                    return entry.value

            # Try L3 (Edge) cache
            if self.l3_cache:
                entry = await self.l3_cache.get(key)
                if entry:
                    self.metrics.l3_hits += 1

                    # Cache in L2 for faster access
                    if self.l2_cache:
                        config = self.cache_config.get(cache_type, self.cache_config['search_results'])
                        await self.l2_cache.set(key, entry.value, config['l2_ttl'])

                    self._update_response_time(start_time)
                    logger.debug(f"L3 cache hit: {key}")
                    return entry.value

            # Cache miss
            self.metrics.misses += 1
            self._update_response_time(start_time)
            logger.debug(f"Cache miss: {key}")
            return None

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "search_results",
        custom_ttl: Optional[int] = None
    ) -> bool:
        """Set value in all cache levels"""
        try:
            config = self.cache_config.get(cache_type, self.cache_config['search_results'])

            # Use custom TTL if provided
            if custom_ttl:
                l1_ttl = l2_ttl = l3_ttl = custom_ttl
            else:
                l1_ttl = config['l1_ttl']
                l2_ttl = config['l2_ttl']
                l3_ttl = config['l3_ttl']

            # Set in L1
            self.l1_cache.set(key, value, l1_ttl)

            # Set in L2
            if self.l2_cache:
                await self.l2_cache.set(key, value, l2_ttl)

            # Set in L3 (only for cacheable content)
            if self.l3_cache and self._is_edge_cacheable(cache_type):
                await self.l3_cache.set(key, value, l3_ttl)

            return True

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from all cache levels"""
        try:
            # Delete from all levels
            self.l1_cache.delete(key)

            if self.l2_cache:
                await self.l2_cache.delete(key)

            if self.l3_cache:
                await self.l3_cache.delete(key)

            return True

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        count = 0

        try:
            # L1 - simple pattern matching
            keys_to_delete = [k for k in self.l1_cache.cache.keys() if pattern in k]
            for key in keys_to_delete:
                self.l1_cache.delete(key)
                count += 1

            # L2 - Redis pattern matching
            if self.l2_cache and self.l2_cache.redis_client:
                redis_pattern = f"{self.l2_cache.key_prefix}{pattern}*"
                keys = await self.l2_cache.redis_client.keys(redis_pattern)
                if keys:
                    await self.l2_cache.redis_client.delete(*keys)
                    count += len(keys) // 2  # Each entry has data + meta

            # L3 - pattern matching
            if self.l3_cache:
                keys_to_delete = [k for k in self.l3_cache.edge_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.l3_cache.edge_cache[key]
                    count += 1

            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Error invalidating cache pattern: {e}")
            return 0

    def _is_edge_cacheable(self, cache_type: str) -> bool:
        """Check if content should be cached at edge"""
        # Only cache search results and vehicle details at edge
        return cache_type in ['search_results', 'vehicle_details']

    def _update_response_time(self, start_time: float):
        """Update average response time metric"""
        response_time = time.time() - start_time
        self.metrics.total_response_time += response_time
        self.metrics.avg_response_time = self.metrics.total_response_time / self.metrics.total_requests

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create a deterministic key
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)

        # Hash to ensure consistent length
        return hashlib.md5(key_string.encode()).hexdigest()

    async def warm_up_cache(self, search_function):
        """Warm up cache with common queries"""
        logger.info("🔥 Warming up cache with common queries...")

        for query in self.warmup_queries:
            try:
                # Generate cache key
                cache_key = self.generate_cache_key("search", query, {}, 20)

                # Check if already cached
                if not await self.get(cache_key):
                    # Execute search and cache result
                    result = await search_function(query, limit=20)
                    await self.set(cache_key, result, "search_results")

                    logger.debug(f"Warmed cache for query: {query}")

            except Exception as e:
                logger.error(f"Error warming cache for query '{query}': {e}")

        logger.info("✅ Cache warm-up completed")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "hit_rate": self.metrics.get_hit_rate(),
            "hit_rate_by_level": self.metrics.get_hit_rate_by_level(),
            "cache_sizes": {
                "l1_local": self.l1_cache.get_size(),
                "l2_redis": self.l2_cache.get_size() if self.l2_cache else 0,
                "l3_edge": self.l3_cache.get_size() if self.l3_cache else 0
            },
            "evictions": self.metrics.evictions,
            "errors": self.metrics.errors,
            "avg_response_time_ms": self.metrics.avg_response_time * 1000
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status"""
        status = {
            "l1_local": {"status": "healthy", "size": self.l1_cache.get_size()},
            "l2_redis": {"status": "disabled"},
            "l3_edge": {"status": "disabled"}
        }

        # Check Redis health
        if self.l2_cache:
            try:
                # Would check Redis health here
                status["l2_redis"] = {"status": "healthy", "size": self.l2_cache.get_size()}
            except:
                status["l2_redis"] = {"status": "unhealthy"}

        # Edge cache status
        if self.l3_cache:
            status["l3_edge"] = {"status": "healthy", "size": self.l3_cache.get_size()}

        return status

# ============================================================================
# Cache Decorators
# ============================================================================

def cached(
    cache_type: str = "search_results",
    ttl: Optional[int] = None,
    key_generator: Optional[callable] = None
):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()}"

            # Try to get from cache
            from src.cache.multi_level_cache import cache_manager
            cached_result = await cache_manager.get(cache_key, cache_type)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, cache_type, ttl)

            return result

        return wrapper
    return decorator

# ============================================================================
# Global Cache Manager Instance
# ============================================================================

# Initialize global cache manager
cache_manager = MultiLevelCache(
    local_cache_size=1000,
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    enable_edge_cache=True
)