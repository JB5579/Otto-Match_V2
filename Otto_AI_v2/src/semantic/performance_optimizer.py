"""
Performance Optimizer for Vehicle Processing Service
Provides intelligent caching, async processing patterns, and performance monitoring
to achieve <2 second processing time per vehicle
"""

import asyncio
import time
import logging
import hashlib
import pickle
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for processing operations"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl_seconds

    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            self._cleanup_expired()
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, value: Any):
        """Put value in cache"""
        with self.lock:
            self._cleanup_expired()
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove oldest item
                    oldest_key = next(iter(self.cache))
                    self.cache.pop(oldest_key)
                    self.timestamps.pop(oldest_key, None)
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            self._cleanup_expired()
            return len(self.cache)

class PerformanceOptimizer:
    """
    Optimizes vehicle processing performance through intelligent caching,
    async processing patterns, and comprehensive monitoring
    """

    def __init__(self, embedding_dim: int = 3072):
        self.embedding_dim = embedding_dim

        # Performance caches
        self.text_cache = LRUCache(max_size=500, ttl_seconds=1800)  # 30 minutes
        self.metadata_cache = LRUCache(max_size=1000, ttl_seconds=3600)  # 1 hour
        self.tag_cache = LRUCache(max_size=200, ttl_seconds=900)  # 15 minutes

        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        self.metrics_lock = threading.RLock()

        # Thread pool for CPU-intensive operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vehicle_perf")

        # Performance thresholds
        self.WARNING_THRESHOLD = 1.5  # seconds
        self.CRITICAL_THRESHOLD = 2.0  # seconds

    def generate_cache_key(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Generate consistent cache key from data"""
        # Sort keys for consistent hashing
        sorted_data = {k: data[k] for k in sorted(data.keys()) if data[k] is not None}
        data_str = str(sorted_data).encode('utf-8')
        hash_key = hashlib.sha256(data_str).hexdigest()[:16]
        return f"{prefix}_{hash_key}" if prefix else hash_key

    async def cached_text_processing(
        self,
        vehicle_data: Dict[str, Any],
        processing_func: Callable
    ) -> Any:
        """Cached text processing with performance monitoring"""
        cache_key = self.generate_cache_key({
            "make": vehicle_data.get("make"),
            "model": vehicle_data.get("model"),
            "year": vehicle_data.get("year"),
            "description": vehicle_data.get("description"),
            "features": vehicle_data.get("features")
        }, prefix="text")

        # Check cache first
        cached_result = self.text_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for text processing: {vehicle_data.get('vehicle_id')}")
            return cached_result

        # Process with monitoring
        start_time = time.time()
        try:
            result = await processing_func(vehicle_data)
            duration = time.time() - start_time

            # Cache successful results
            self.text_cache.put(cache_key, result)

            # Record metrics
            self._record_metric("text_processing", start_time, time.time(), True)

            if duration > self.WARNING_THRESHOLD:
                logger.warning(f"Slow text processing: {duration:.2f}s for vehicle {vehicle_data.get('vehicle_id')}")

            return result

        except Exception as e:
            duration = time.time() - start_time
            self._record_metric("text_processing", start_time, time.time(), False, str(e))
            logger.error(f"Text processing failed after {duration:.2f}s: {e}")
            raise

    async def cached_metadata_processing(
        self,
        vehicle_data: Dict[str, Any],
        processing_func: Callable
    ) -> Any:
        """Cached metadata processing with performance monitoring"""
        cache_key = self.generate_cache_key({
            "make": vehicle_data.get("make"),
            "model": vehicle_data.get("model"),
            "year": vehicle_data.get("year"),
            "mileage": vehicle_data.get("mileage"),
            "price": vehicle_data.get("price")
        }, prefix="metadata")

        # Check cache first
        cached_result = self.metadata_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for metadata processing: {vehicle_data.get('vehicle_id')}")
            return cached_result

        # Process with monitoring
        start_time = time.time()
        try:
            result = await processing_func(vehicle_data)
            duration = time.time() - start_time

            # Cache successful results
            self.metadata_cache.put(cache_key, result)

            # Record metrics
            self._record_metric("metadata_processing", start_time, time.time(), True)

            if duration > self.WARNING_THRESHOLD:
                logger.warning(f"Slow metadata processing: {duration:.2f}s for vehicle {vehicle_data.get('vehicle_id')}")

            return result

        except Exception as e:
            duration = time.time() - start_time
            self._record_metric("metadata_processing", start_time, time.time(), False, str(e))
            logger.error(f"Metadata processing failed after {duration:.2f}s: {e}")
            raise

    async def cached_tag_extraction(
        self,
        vehicle_data: Dict[str, Any],
        image_descriptions: List[str],
        processing_func: Callable
    ) -> List[str]:
        """Cached semantic tag extraction with performance monitoring"""
        cache_key = self.generate_cache_key({
            "make": vehicle_data.get("make"),
            "model": vehicle_data.get("model"),
            "year": vehicle_data.get("year"),
            "price": vehicle_data.get("price"),
            "image_count": len(image_descriptions),
            "image_desc_hash": hashlib.sha256("|".join(image_descriptions).encode()).hexdigest()[:8]
        }, prefix="tags")

        # Check cache first
        cached_result = self.tag_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for tag extraction: {vehicle_data.get('vehicle_id')}")
            return cached_result

        # Process with monitoring
        start_time = time.time()
        try:
            result = await processing_func(vehicle_data, image_descriptions)
            duration = time.time() - start_time

            # Cache successful results
            self.tag_cache.put(cache_key, result)

            # Record metrics
            self._record_metric("tag_extraction", start_time, time.time(), True)

            if duration > self.WARNING_THRESHOLD:
                logger.warning(f"Slow tag extraction: {duration:.2f}s for vehicle {vehicle_data.get('vehicle_id')}")

            return result

        except Exception as e:
            duration = time.time() - start_time
            self._record_metric("tag_extraction", start_time, time.time(), False, str(e))
            logger.error(f"Tag extraction failed after {duration:.2f}s: {e}")
            raise

    async def parallel_image_processing(
        self,
        images: List[Dict[str, Any]],
        processing_func: Callable,
        max_concurrent: int = 4
    ) -> List[Any]:
        """Process images in parallel with concurrency control"""
        if not images:
            return []

        start_time = time.time()
        logger.debug(f"Processing {len(images)} images with max concurrency {max_concurrent}")

        try:
            # Create semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single_image(image_data):
                async with semaphore:
                    image_start = time.time()
                    try:
                        result = await processing_func(image_data)
                        image_duration = time.time() - image_start
                        logger.debug(f"Image processed in {image_duration:.2f}s: {image_data.get('path', 'unknown')}")
                        return result
                    except Exception as e:
                        image_duration = time.time() - image_start
                        logger.error(f"Image processing failed after {image_duration:.2f}s: {e}")
                        raise

            # Process images in parallel with limited concurrency
            tasks = [process_single_image(image) for image in images]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and log errors
            successful_results = []
            failed_count = 0
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"Image processing failed: {result}")
                else:
                    successful_results.append(result)

            duration = time.time() - start_time
            success_rate = (len(successful_results) / len(images)) * 100 if images else 0

            # Record metrics
            self._record_metric("parallel_image_processing", start_time, time.time(), True, metadata={
                "total_images": len(images),
                "successful_images": len(successful_results),
                "failed_images": failed_count,
                "success_rate": success_rate,
                "max_concurrent": max_concurrent
            })

            logger.info(f"Parallel image processing: {len(successful_results)}/{len(images)} images in {duration:.2f}s ({success_rate:.1f}% success)")

            if duration > self.WARNING_THRESHOLD:
                logger.warning(f"Slow parallel image processing: {duration:.2f}s for {len(images)} images")

            return successful_results

        except Exception as e:
            duration = time.time() - start_time
            self._record_metric("parallel_image_processing", start_time, time.time(), False, str(e))
            logger.error(f"Parallel image processing failed after {duration:.2f}s: {e}")
            raise

    def _record_metric(
        self,
        operation_name: str,
        start_time: float,
        end_time: float,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record performance metric"""
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=success,
            error_message=error_message,
            metadata=metadata
        )

        with self.metrics_lock:
            self.metrics.append(metric)

            # Keep only last 1000 metrics to prevent memory bloat
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.metrics_lock:
            if not self.metrics:
                return {
                    "total_operations": 0,
                    "average_duration": 0,
                    "success_rate": 0,
                    "operations_per_second": 0
                }

        # Calculate metrics
        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics if m.success)
        total_duration = sum(m.duration for m in self.metrics)
        average_duration = total_duration / total_operations
        success_rate = (successful_operations / total_operations) * 100

        # Calculate operations per second (last 10 operations)
        recent_metrics = self.metrics[-10:] if len(self.metrics) >= 10 else self.metrics
        if recent_metrics:
            recent_duration = sum(m.duration for m in recent_metrics)
            ops_per_second = len(recent_metrics) / recent_duration if recent_duration > 0 else 0
        else:
            ops_per_second = 0

        # Performance by operation type
        operation_stats = {}
        for metric in self.metrics:
            op_name = metric.operation_name
            if op_name not in operation_stats:
                operation_stats[op_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0,
                    "avg_duration": 0,
                    "success_rate": 0
                }

            operation_stats[op_name]["count"] += 1
            operation_stats[op_name]["total_duration"] += metric.duration
            if metric.success:
                operation_stats[op_name]["success_count"] += 1

        # Calculate averages for each operation type
        for op_name, stats in operation_stats.items():
            stats["avg_duration"] = stats["total_duration"] / stats["count"]
            stats["success_rate"] = (stats["success_count"] / stats["count"]) * 100

        # Cache statistics
        cache_stats = {
            "text_cache_size": self.text_cache.size(),
            "metadata_cache_size": self.metadata_cache.size(),
            "tag_cache_size": self.tag_cache.size()
        }

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "average_duration": average_duration,
            "success_rate": success_rate,
            "operations_per_second": ops_per_second,
            "operation_stats": operation_stats,
            "cache_stats": cache_stats,
            "performance_health": self._get_performance_health(average_duration, success_rate)
        }

    def _get_performance_health(self, avg_duration: float, success_rate: float) -> str:
        """Determine overall performance health"""
        if avg_duration < 1.0 and success_rate > 95:
            return "excellent"
        elif avg_duration < 1.5 and success_rate > 90:
            return "good"
        elif avg_duration < 2.0 and success_rate > 85:
            return "acceptable"
        else:
            return "needs_improvement"

    def get_slow_operations(self, threshold: float = None) -> List[PerformanceMetrics]:
        """Get operations that exceeded performance threshold"""
        if threshold is None:
            threshold = self.WARNING_THRESHOLD

        with self.metrics_lock:
            return [m for m in self.metrics if m.duration > threshold]

    def clear_caches(self):
        """Clear all performance caches"""
        self.text_cache.clear()
        self.metadata_cache.clear()
        self.tag_cache.clear()
        logger.info("Performance caches cleared")

    def clear_metrics(self):
        """Clear all performance metrics"""
        with self.metrics_lock:
            self.metrics.clear()
        logger.info("Performance metrics cleared")

    def shutdown(self):
        """Cleanup resources"""
        self.clear_caches()
        self.clear_metrics()
        self.thread_pool.shutdown(wait=True)
        logger.info("Performance optimizer shutdown complete")

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.shutdown()
        except:
            pass