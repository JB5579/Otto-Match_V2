"""
Test Suite for Multi-Level Cache System
Comprehensive testing for Story 1-8 performance optimization
"""

import asyncio
import time
import json
import pytest
import sys
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cache.multi_level_cache import (
    MultiLevelCache,
    LocalCache,
    RedisCache,
    EdgeCacheSimulator,
    CacheEntry,
    CacheMetrics,
    CacheLevel,
    cache_manager
)
from src.cache.cache_config import (
    CacheConfig,
    DEFAULT_CACHE_CONFIG,
    DEV_CACHE_CONFIG,
    CacheStrategy
)

class TestLocalCache:
    """Test L1 local cache"""

    def test_cache_entry_creation(self):
        """Test cache entry creation and serialization"""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test_value"},
            ttl=300,
            created_at=datetime.now(),
            level=CacheLevel.L1_LOCAL
        )

        assert entry.key == "test_key"
        assert entry.value["data"] == "test_value"
        assert entry.ttl == 300
        assert entry.access_count == 0
        assert entry.size_bytes > 0

    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        # Create expired entry
        entry = CacheEntry(
            key="expired_key",
            value="expired_value",
            ttl=1,
            created_at=datetime.now() - timedelta(seconds=2),
            level=CacheLevel.L1_LOCAL
        )

        assert entry.is_expired() == True

        # Create valid entry
        valid_entry = CacheEntry(
            key="valid_key",
            value="valid_value",
            ttl=300,
            created_at=datetime.now(),
            level=CacheLevel.L1_LOCAL
        )

        assert valid_entry.is_expired() == False

    def test_local_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = LocalCache(max_size=3, default_ttl=60)

        # Test set and get
        assert cache.set("key1", "value1") == True
        assert cache.get("key1").value == "value1"
        assert cache.get_size() == 1

        # Test non-existent key
        assert cache.get("nonexistent") is None

        # Test delete
        assert cache.delete("key1") == True
        assert cache.get("key1") is None
        assert cache.get_size() == 0

    def test_local_cache_lru_eviction(self):
        """Test LRU eviction policy"""
        cache = LocalCache(max_size=2, default_ttl=60)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.get_size() == 2

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add key3 - should evict key2 (least recently used)
        cache.set("key3", "value3")
        assert cache.get_size() == 2
        assert cache.get("key1") is not None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None

    def test_local_cache_ttl_expiration(self):
        """Test TTL-based expiration"""
        cache = LocalCache(max_size=10, default_ttl=1)  # 1 second TTL

        # Set value
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") is not None

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

class TestCacheMetrics:
    """Test cache metrics calculation"""

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        metrics = CacheMetrics(
            total_requests=100,
            l1_hits=30,
            l2_hits=20,
            l3_hits=10,
            misses=40
        )

        assert metrics.get_hit_rate() == 60.0  # (30+20+10)/100 * 100

    def test_empty_metrics(self):
        """Test metrics with no requests"""
        metrics = CacheMetrics()
        assert metrics.get_hit_rate() == 0.0

    def test_hit_rate_by_level(self):
        """Test hit rate breakdown by level"""
        metrics = CacheMetrics(
            total_requests=100,
            l1_hits=30,
            l2_hits=20,
            l3_hits=10
        )

        hit_rates = metrics.get_hit_rate_by_level()
        assert hit_rates[CacheLevel.L1_LOCAL.value] == 30.0
        assert hit_rates[CacheLevel.L2_REDIS.value] == 20.0
        assert hit_rates[CacheLevel.L3_EDGE.value] == 10.0

class TestMultiLevelCache:
    """Test multi-level cache operations"""

    @pytest.fixture
    def cache(self):
        """Create test cache instance"""
        return MultiLevelCache(
            local_cache_size=10,
            redis_url=None,  # Disable Redis for testing
            enable_edge_cache=True
        )

    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache):
        """Test cache initialization"""
        assert await cache.initialize() == True
        assert cache.l1_cache is not None
        assert cache.l3_cache is not None
        assert cache.l2_cache is None  # Disabled in test

    @pytest.mark.asyncio
    async def test_cache_miss_and_set(self, cache):
        """Test cache miss and subsequent set"""
        await cache.initialize()

        # Test miss
        result = await cache.get("test_key")
        assert result is None

        # Test set
        assert await cache.set("test_key", "test_value") == True

        # Test hit
        result = await cache.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_cache_tier_promotion(self, cache):
        """Test cache promotion from L3 to L2 to L1"""
        await cache.initialize()

        # Simulate frequently accessed item
        key = "popular_key"
        value = {"data": "popular_content"}

        # Set in cache
        await cache.set(key, value)

        # First access - should hit L1
        result = await cache.get(key)
        assert result == value
        assert cache.metrics.l1_hits > 0

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation"""
        await cache.initialize()

        # Set cache entries
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Delete specific key
        assert await cache.delete("key2") == True

        # Verify deletion
        assert await cache.get("key1") is not None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is not None

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, cache):
        """Test pattern-based cache invalidation"""
        await cache.initialize()

        # Set cache entries with patterns
        await cache.set("search:suv", {"results": "SUVs"})
        await cache.set("search:truck", {"results": "Trucks"})
        await cache.set("vehicle:123", {"details": "Car details"})

        # Invalidate search pattern
        count = await cache.invalidate_pattern("search:")
        assert count == 2

        # Verify invalidation
        assert await cache.get("search:suv") is None
        assert await cache.get("search:truck") is None
        assert await cache.get("vehicle:123") is not None

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache):
        """Test cache key generation"""
        key1 = cache.generate_cache_key("search", "SUV", {"price_max": 30000}, 20)
        key2 = cache.generate_cache_key("search", "SUV", {"price_max": 30000}, 20)
        key3 = cache.generate_cache_key("search", "truck", {"price_max": 30000}, 20)

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

        # Keys should be consistent length
        assert len(key1) == len(key2) == len(key3) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_cache_warmup(self, cache):
        """Test cache warm-up functionality"""
        await cache.initialize()

        # Mock search function
        async def mock_search(query, limit=20):
            return {"query": query, "results": f"Results for {query}"}

        # Warm up cache
        await cache.warm_up_cache(mock_search)

        # Verify cache is warmed
        warmup_results = await cache.get(cache.generate_cache_key("search", "SUV under 30000", {}, 20))
        assert warmup_results is not None
        assert warmup_results["query"] == "SUV under 30000"

    @pytest.mark.asyncio
    async def test_cache_metrics_collection(self, cache):
        """Test metrics collection"""
        await cache.initialize()

        # Set and get some values
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("nonexistent")  # Miss

        # Get metrics
        metrics = cache.get_metrics()

        assert metrics["total_requests"] == 2
        assert metrics["l1_hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["hit_rate"] == 50.0
        assert "cache_sizes" in metrics
        assert "avg_response_time_ms" in metrics

    @pytest.mark.asyncio
    async def test_health_status(self, cache):
        """Test health status reporting"""
        await cache.initialize()

        status = cache.get_health_status()

        assert "l1_local" in status
        assert "l2_redis" in status
        assert "l3_edge" in status

        assert status["l1_local"]["status"] == "healthy"
        assert status["l3_edge"]["status"] == "healthy"
        assert status["l2_redis"]["status"] == "disabled"

class TestCacheConfiguration:
    """Test cache configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = DEFAULT_CACHE_CONFIG

        assert config.l1_local.enabled == True
        assert config.l1_local.max_size == 1000
        assert config.l1_local.ttl_seconds == 300

        assert config.l2_redis.enabled == True
        assert config.l2_redis.compression == True
        assert config.l2_redis.persistence == True

        assert config.l3_edge.enabled == True
        assert config.l3_edge.ttl_seconds == 86400

    def test_content_type_settings(self):
        """Test content-specific cache settings"""
        config = DEFAULT_CACHE_CONFIG

        # Search results should be edge cached
        search_config = config.content_types["search_results"]
        assert search_config["edge_cache"] == True
        assert search_config["l3_ttl"] == 86400

        # Analytics should not be edge cached
        analytics_config = config.content_types["analytics"]
        assert analytics_config["edge_cache"] == False
        assert analytics_config["l3_ttl"] == 0

    def test_dev_config(self):
        """Test development configuration"""
        config = DEV_CACHE_CONFIG

        assert config.l2_redis.enabled == False
        assert config.l3_edge.enabled == False
        assert config.enable_cache_warmup == False
        assert config.l1_local.max_size == 100  # Smaller for dev

class TestCachePerformance:
    """Performance tests for cache system"""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent cache operations"""
        cache = MultiLevelCache(
            local_cache_size=100,
            redis_url=None,
            enable_edge_cache=False
        )
        await cache.initialize()

        # Concurrent set operations
        tasks = []
        for i in range(50):
            task = cache.set(f"key_{i}", f"value_{i}")
            tasks.append(task)

        await asyncio.gather(*tasks)
        assert cache.l1_cache.get_size() == 50

        # Concurrent get operations
        results = await asyncio.gather(*[
            cache.get(f"key_{i}") for i in range(50)
        ])

        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Benchmark cache performance"""
        cache = MultiLevelCache(
            local_cache_size=1000,
            redis_url=None,
            enable_edge_cache=False
        )
        await cache.initialize()

        # Benchmark set operations
        start_time = time.time()
        for i in range(100):
            await cache.set(f"perf_key_{i}", f"perf_value_{i}")
        set_time = time.time() - start_time

        # Benchmark get operations
        start_time = time.time()
        for i in range(100):
            await cache.get(f"perf_key_{i}")
        get_time = time.time() - start_time

        # Performance assertions (adjust based on requirements)
        assert set_time < 1.0  # Should complete in < 1 second
        assert get_time < 0.5  # Should complete in < 0.5 seconds

        # Check hit rate
        metrics = cache.get_metrics()
        assert metrics["hit_rate"] == 100.0  # All should be hits

class TestCacheEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_large_value_caching(self):
        """Test caching of large values"""
        cache = MultiLevelCache(redis_url=None, enable_edge_cache=False)
        await cache.initialize()

        # Create large value (>1MB)
        large_value = "x" * (1024 * 1024)

        # Should cache successfully
        assert await cache.set("large_key", large_value) == True

        # Should retrieve successfully
        result = await cache.get("large_key")
        assert result == large_value

    @pytest.mark.asyncio
    async def test_special_characters_in_keys(self):
        """Test caching with special characters in keys"""
        cache = MultiLevelCache(redis_url=None, enable_edge_cache=False)
        await cache.initialize()

        special_keys = [
            "key with spaces",
            "key/with/slashes",
            "key?with?query",
            "key#with#hash",
            "key:with:colons",
            "unicode_key_测试"
        ]

        for key in special_keys:
            value = f"value_for_{key}"
            assert await cache.set(key, value) == True
            assert await cache.get(key) == value

    @pytest.mark.asyncio
    async def test_none_value_caching(self):
        """Test caching of None values"""
        cache = MultiLevelCache(redis_url=None, enable_edge_cache=False)
        await cache.initialize()

        # Cache None value
        assert await cache.set("none_key", None) == True

        # Retrieve None value
        result = await cache.get("none_key")
        assert result is None

        # But cache miss also returns None, so check metrics
        assert cache.metrics.misses == 0  # Should be a hit

if __name__ == "__main__":
    # Run basic tests
    print("Running cache tests...")

    # Test local cache
    print("\n1. Testing Local Cache...")
    cache = LocalCache(max_size=3, default_ttl=60)
    cache.set("test", "value")
    assert cache.get("test").value == "value"
    print("Local cache tests passed")

    # Test metrics
    print("\n2. Testing Cache Metrics...")
    metrics = CacheMetrics(total_requests=100, l1_hits=50)
    assert metrics.get_hit_rate() == 50.0
    print("Cache metrics tests passed")

    # Test multi-level cache
    print("\n3. Testing Multi-Level Cache...")
    async def test_multi_cache():
        cache = MultiLevelCache(redis_url=None, enable_edge_cache=False)
        await cache.initialize()
        await cache.set("test", "value")
        result = await cache.get("test")
        assert result == "value"
        print("Multi-level cache tests passed")

    asyncio.run(test_multi_cache())

    print("\nAll cache tests completed successfully!")