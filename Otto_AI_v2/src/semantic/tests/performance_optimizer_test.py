"""
Test suite for Performance Optimizer
Tests caching, parallel processing, and performance monitoring
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from performance_optimizer import PerformanceOptimizer, LRUCache, PerformanceMetrics

class TestLRUCache:
    """Test class for LRU Cache implementation"""

    @pytest.fixture
    def cache(self):
        """Create LRU cache instance for testing"""
        return LRUCache(max_size=3, ttl_seconds=1)

    def test_cache_basic_operations(self, cache):
        """Test basic cache put and get operations"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("nonexistent") is None

    def test_cache_lru_eviction(self, cache):
        """Test LRU eviction when cache is full"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # Cache is now full
        assert cache.size() == 3

        # Add new item, should evict least recently used (key1)
        cache.put("key4", "value4")

        assert cache.get("key1") is None  # Should be evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        assert cache.size() == 3

    def test_cache_ttl_expiration(self, cache):
        """Test TTL-based expiration"""
        cache.put("key1", "value1")

        # Should be available immediately
        assert cache.get("key1") == "value1"

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_cache_move_to_end_on_access(self, cache):
        """Test that accessing items moves them to end (most recently used)"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new item, should evict key2 (now least recently used)
        cache.put("key4", "value4")

        assert cache.get("key1") == "value1"  # Should still exist
        assert cache.get("key2") is None  # Should be evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_clear(self, cache):
        """Test cache clearing functionality"""
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        assert cache.size() == 2

        cache.clear()

        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

class TestPerformanceOptimizer:
    """Test class for Performance Optimizer"""

    @pytest.fixture
    def optimizer(self):
        """Create performance optimizer instance for testing"""
        return PerformanceOptimizer(embedding_dim=3072)

    @pytest.mark.asyncio
    async def test_cached_text_processing_hit(self, optimizer):
        """Test text processing cache hit"""
        vehicle_data = {
            "vehicle_id": "test-001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "description": "Test description",
            "features": ["Bluetooth", "Backup Camera"]
        }

        # Mock processing function
        processing_func = AsyncMock(return_value=[0.1] * 3072)

        # First call should cache result
        result1 = await optimizer.cached_text_processing(vehicle_data, processing_func)
        assert result1 == [0.1] * 3072
        processing_func.assert_called_once()

        # Second call should use cache
        result2 = await optimizer.cached_text_processing(vehicle_data, processing_func)
        assert result2 == [0.1] * 3072
        processing_func.assert_called_once()  # Should not be called again

    @pytest.mark.asyncio
    async def test_cached_text_processing_miss(self, optimizer):
        """Test text processing cache miss with different data"""
        vehicle_data1 = {
            "vehicle_id": "test-001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "description": "Test description",
            "features": ["Bluetooth"]
        }

        vehicle_data2 = {
            "vehicle_id": "test-002",
            "make": "Honda",
            "model": "Civic",
            "year": 2023,
            "description": "Different description",
            "features": ["Backup Camera"]
        }

        # Mock processing function
        processing_func = AsyncMock(side_effect=[
            [0.1] * 3072,  # First call
            [0.2] * 3072   # Second call
        ])

        # Both calls should miss cache and call processing function
        result1 = await optimizer.cached_text_processing(vehicle_data1, processing_func)
        result2 = await optimizer.cached_text_processing(vehicle_data2, processing_func)

        assert result1 == [0.1] * 3072
        assert result2 == [0.2] * 3072
        assert processing_func.call_count == 2

    @pytest.mark.asyncio
    async def test_cached_metadata_processing(self, optimizer):
        """Test cached metadata processing"""
        vehicle_data = {
            "vehicle_id": "test-001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "mileage": 25000,
            "price": 25000,
            "features": ["Bluetooth"]
        }

        # Mock processing function
        processing_func = AsyncMock(return_value={"embedding": [0.3] * 3072, "processed": True})

        # First call
        result1 = await optimizer.cached_metadata_processing(vehicle_data, processing_func)
        assert result1["processed"] is True
        processing_func.assert_called_once()

        # Second call should use cache
        result2 = await optimizer.cached_metadata_processing(vehicle_data, processing_func)
        assert result2["processed"] is True
        processing_func.assert_called_once()  # Should not be called again

    @pytest.mark.asyncio
    async def test_cached_tag_extraction(self, optimizer):
        """Test cached tag extraction"""
        vehicle_data = {
            "vehicle_id": "test-001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "price": 25000,
            "features": ["Bluetooth"]
        }

        image_descriptions = ["Red exterior", "Clean interior"]

        # Mock processing function
        processing_func = AsyncMock(return_value=["toyota", "camry", "sedan", "red"])

        # First call
        result1 = await optimizer.cached_tag_extraction(vehicle_data, image_descriptions, processing_func)
        assert "toyota" in result1
        processing_func.assert_called_once()

        # Second call with same data should use cache
        result2 = await optimizer.cached_tag_extraction(vehicle_data, image_descriptions, processing_func)
        assert "toyota" in result2
        processing_func.assert_called_once()  # Should not be called again

    @pytest.mark.asyncio
    async def test_parallel_image_processing(self, optimizer):
        """Test parallel image processing"""
        images = [
            {"path": "image1.jpg", "type": "exterior"},
            {"path": "image2.jpg", "type": "interior"},
            {"path": "image3.jpg", "type": "detail"}
        ]

        # Mock processing function with different delays
        async def mock_process(image):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"description": f"Processed {image['path']}", "embedding": [0.5] * 3072}

        start_time = time.time()
        results = await optimizer.parallel_image_processing(images, mock_process, max_concurrent=2)
        duration = time.time() - start_time

        # Should process all images
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)

        # With parallel processing and max_concurrent=2, should be faster than sequential
        # Sequential would take ~0.3s, parallel should take ~0.2s
        assert duration < 0.25

    @pytest.mark.asyncio
    async def test_parallel_image_processing_with_errors(self, optimizer):
        """Test parallel image processing error handling"""
        images = [
            {"path": "image1.jpg", "type": "exterior"},
            {"path": "image2.jpg", "type": "interior"},
            {"path": "image3.jpg", "type": "detail"}
        ]

        # Mock processing function that fails on second image
        async def mock_process(image):
            if image["path"] == "image2.jpg":
                raise Exception("Processing failed")
            await asyncio.sleep(0.1)
            return {"description": f"Processed {image['path']}"}

        results = await optimizer.parallel_image_processing(images, mock_process, max_concurrent=3)

        # Should process successful images and handle errors gracefully
        assert len(results) == 2  # Only successful results
        assert all("image2.jpg" not in str(result) for result in results)

    def test_generate_cache_key_consistency(self, optimizer):
        """Test cache key generation consistency"""
        data1 = {"make": "Toyota", "model": "Camry", "year": 2022, "features": ["Bluetooth"]}
        data2 = {"year": 2022, "make": "Toyota", "features": ["Bluetooth"], "model": "Camry"}  # Different order

        key1 = optimizer.generate_cache_key(data1, "text")
        key2 = optimizer.generate_cache_key(data2, "text")

        # Same data in different order should generate same key
        assert key1 == key2
        assert key1.startswith("text_")

        # Different prefix should generate different key
        key3 = optimizer.generate_cache_key(data1, "metadata")
        assert key1 != key3

    def test_record_metric(self, optimizer):
        """Test performance metric recording"""
        start_time = time.time()
        time.sleep(0.01)  # Small delay
        end_time = time.time()

        optimizer._record_metric("test_operation", start_time, end_time, True)

        assert len(optimizer.metrics) == 1
        metric = optimizer.metrics[0]
        assert metric.operation_name == "test_operation"
        assert metric.success is True
        assert metric.duration > 0

    def test_get_performance_summary(self, optimizer):
        """Test performance summary calculation"""
        # Record some test metrics
        optimizer._record_metric("text_processing", time.time(), time.time() + 0.5, True)
        optimizer._record_metric("text_processing", time.time(), time.time() + 0.7, True)
        optimizer._record_metric("image_processing", time.time(), time.time() + 1.2, False, "Error occurred")

        summary = optimizer.get_performance_summary()

        assert summary["total_operations"] == 3
        assert summary["successful_operations"] == 2
        assert summary["success_rate"] == 66.66666666666666  # 2/3 * 100
        assert summary["average_duration"] > 0

        assert "text_processing" in summary["operation_stats"]
        assert "image_processing" in summary["operation_stats"]

        text_stats = summary["operation_stats"]["text_processing"]
        assert text_stats["count"] == 2
        assert text_stats["success_rate"] == 100.0

        image_stats = summary["operation_stats"]["image_processing"]
        assert image_stats["count"] == 1
        assert image_stats["success_rate"] == 0.0

    def test_get_slow_operations(self, optimizer):
        """Test retrieval of slow operations"""
        # Record metrics with different durations
        fast_time = 0.5
        slow_time = 2.5

        optimizer._record_metric("fast_op", time.time(), time.time() + fast_time, True)
        optimizer._record_metric("slow_op", time.time(), time.time() + slow_time, True)

        slow_operations = optimizer.get_slow_operations(threshold=1.0)

        assert len(slow_operations) == 1
        assert slow_operations[0].operation_name == "slow_op"
        assert slow_operations[0].duration > 1.0

    def test_clear_caches(self, optimizer):
        """Test cache clearing functionality"""
        # Add some items to caches
        optimizer.text_cache.put("key1", "value1")
        optimizer.metadata_cache.put("key2", "value2")
        optimizer.tag_cache.put("key3", "value3")

        assert optimizer.text_cache.size() > 0
        assert optimizer.metadata_cache.size() > 0
        assert optimizer.tag_cache.size() > 0

        optimizer.clear_caches()

        assert optimizer.text_cache.size() == 0
        assert optimizer.metadata_cache.size() == 0
        assert optimizer.tag_cache.size() == 0

    def test_clear_metrics(self, optimizer):
        """Test metrics clearing functionality"""
        # Record some metrics
        optimizer._record_metric("test_op", time.time(), time.time() + 0.1, True)
        assert len(optimizer.metrics) > 0

        optimizer.clear_metrics()

        assert len(optimizer.metrics) == 0

    def test_performance_health_assessment(self, optimizer):
        """Test performance health assessment"""
        # Test excellent health
        assert optimizer._get_performance_health(0.8, 98) == "excellent"

        # Test good health
        assert optimizer._get_performance_health(1.2, 92) == "good"

        # Test acceptable health
        assert optimizer._get_performance_health(1.8, 87) == "acceptable"

        # Test needs improvement
        assert optimizer._get_performance_health(2.5, 80) == "needs_improvement"

    def test_metrics_memory_management(self, optimizer):
        """Test that metrics list doesn't grow indefinitely"""
        # Record more than the limit (1000)
        for i in range(1100):
            optimizer._record_metric(f"op_{i}", time.time(), time.time() + 0.1, True)

        # Should only keep last 1000 metrics
        assert len(optimizer.metrics) == 1000
        assert optimizer.metrics[0].operation_name == "op_100"
        assert optimizer.metrics[-1].operation_name == "op_1099"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])