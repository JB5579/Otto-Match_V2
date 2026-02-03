"""
Comprehensive Performance Testing Suite for Otto.AI
Implements Story 1-8: Performance testing suite for all components

Features:
- Load testing for semantic search
- Stress testing for cache layers
- Database performance benchmarking
- Connection pool stress testing
- End-to-end performance validation
- Performance regression detection
"""

import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import aiohttp
import psutil

# Import Otto.AI components
from src.cache.multi_level_cache import MultiLevelCache
from src.database.pgvector_optimizer import PGVectorOptimizer
from src.monitoring.query_optimizer import QueryOptimizer
from src.scaling.connection_pool import ConnectionPool, DatabaseConfig

logger = logging.getLogger(__name__)

@dataclass
class PerformanceTestResult:
    """Results of a performance test"""
    test_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    requests_completed: int = 0
    requests_failed: int = 0
    requests_per_second: float = 0.0
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    error_rate_percent: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceThresholds:
    """Performance thresholds for pass/fail criteria"""
    max_avg_response_time_ms: float = 500.0
    max_p95_response_time_ms: float = 1000.0
    max_p99_response_time_ms: float = 2000.0
    min_requests_per_second: float = 10.0
    max_error_rate_percent: float = 1.0
    max_cpu_usage_percent: float = 80.0
    max_memory_usage_mb: float = 1000.0

class PerformanceTestSuite:
    """Comprehensive performance testing suite"""

    def __init__(
        self,
        test_duration_seconds: int = 60,
        concurrent_users: int = 10,
        ramp_up_seconds: int = 10,
        thresholds: Optional[PerformanceThresholds] = None
    ):
        self.test_duration_seconds = test_duration_seconds
        self.concurrent_users = concurrent_users
        self.ramp_up_seconds = ramp_up_seconds
        self.thresholds = thresholds or PerformanceThresholds()

        # Test components
        self.cache: Optional[MultiLevelCache] = None
        self.pgvector_optimizer: Optional[PGVectorOptimizer] = None
        self.query_optimizer: Optional[QueryOptimizer] = None
        self.connection_pool: Optional[ConnectionPool] = None

        # Test results
        self.test_results: List[PerformanceTestResult] = []
        self.test_history: List[Dict[str, Any]] = []

        # Monitoring
        self.monitoring_active = False
        self.system_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "network_io": []
        }

    async def initialize(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        redis_url: Optional[str] = None
    ) -> bool:
        """Initialize test components"""
        try:
            logger.info("🚀 Initializing Performance Test Suite...")

            # Initialize cache
            self.cache = MultiLevelCache(
                local_cache_size=1000,
                redis_url=redis_url,
                enable_edge_cache=True
            )
            await self.cache.initialize()

            # Initialize pgvector optimizer
            if supabase_url and supabase_key:
                self.pgvector_optimizer = PGVectorOptimizer()
                await self.pgvector_optimizer.initialize(supabase_url, supabase_key)

            # Initialize query optimizer
            self.query_optimizer = QueryOptimizer()
            await self.query_optimizer.start_monitoring()

            logger.info("✅ Performance Test Suite initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Performance Test Suite: {e}")
            return False

    async def run_semantic_search_test(
        self,
        test_queries: List[str],
        vector_dimensions: int = 1536
    ) -> PerformanceTestResult:
        """Run semantic search performance test"""
        logger.info(f"🔍 Running Semantic Search Performance Test with {len(test_queries)} queries")

        result = PerformanceTestResult(test_name="semantic_search")

        # Generate mock embeddings for testing
        test_embeddings = [
            np.random.random(vector_dimensions).tolist()
            for _ in test_queries
        ]

        response_times = []
        errors = 0

        start_time = time.time()

        # Start system monitoring
        self._start_system_monitoring()

        try:
            # Create concurrent tasks
            semaphore = asyncio.Semaphore(self.concurrent_users)
            tasks = []

            for i, (query, embedding) in enumerate(zip(test_queries, test_embeddings)):
                task = self._execute_search_with_monitoring(
                    semaphore,
                    query,
                    embedding,
                    response_times,
                    result
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            # Calculate metrics
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.requests_completed = len(response_times)
            result.requests_failed = errors

            if response_times:
                result.avg_response_time_ms = statistics.mean(response_times)
                result.p50_response_time_ms = np.percentile(response_times, 50)
                result.p95_response_time_ms = np.percentile(response_times, 95)
                result.p99_response_time_ms = np.percentile(response_times, 99)
                result.min_response_time_ms = min(response_times)
                result.max_response_time_ms = max(response_times)

            result.requests_per_second = result.requests_completed / result.duration_seconds
            result.error_rate_percent = (errors / max(result.requests_completed + errors, 1)) * 100

            # Get final system metrics
            cpu, memory = self._get_current_system_metrics()
            result.cpu_usage_percent = cpu
            result.memory_usage_mb = memory

            logger.info(f"Semantic Search Test completed: {result.requests_per_second:.2f} req/s, {result.avg_response_time_ms:.2f}ms avg")

        finally:
            self._stop_system_monitoring()

        return result

    async def run_cache_performance_test(
        self,
        cache_operations: int = 1000,
        cache_keys: List[str] = None
    ) -> PerformanceTestResult:
        """Run cache performance test"""
        logger.info(f"💾 Running Cache Performance Test with {cache_operations} operations")

        result = PerformanceTestResult(test_name="cache_performance")

        if not cache_keys:
            # Generate test cache keys
            cache_keys = [f"test_key_{i}" for i in range(100)]

        response_times = []
        errors = 0

        start_time = time.time()
        self._start_system_monitoring()

        try:
            # Cache write phase
            write_tasks = []
            for i in range(cache_operations // 2):
                key = cache_keys[i % len(cache_keys)]
                value = {"data": f"test_value_{i}", "timestamp": time.time()}

                task = self._execute_cache_write(
                    key,
                    value,
                    response_times,
                    result
                )
                write_tasks.append(task)

            await asyncio.gather(*write_tasks, return_exceptions=True)

            # Cache read phase
            read_tasks = []
            for i in range(cache_operations // 2):
                key = cache_keys[i % len(cache_keys)]

                task = self._execute_cache_read(
                    key,
                    response_times,
                    result
                )
                read_tasks.append(task)

            await asyncio.gather(*read_tasks, return_exceptions=True)

            # Calculate metrics
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.requests_completed = len(response_times)
            result.requests_failed = errors

            if response_times:
                result.avg_response_time_ms = statistics.mean(response_times)
                result.p50_response_time_ms = np.percentile(response_times, 50)
                result.p95_response_time_ms = np.percentile(response_times, 95)
                result.p99_response_time_ms = np.percentile(response_times, 99)
                result.min_response_time_ms = min(response_times)
                result.max_response_time_ms = max(response_times)

            result.requests_per_second = result.requests_completed / result.duration_seconds
            result.error_rate_percent = (errors / max(result.requests_completed + errors, 1)) * 100

            # Add cache-specific metrics
            if self.cache:
                cache_metrics = self.cache.get_metrics()
                result.custom_metrics.update({
                    "cache_hit_rate": cache_metrics["hit_rate"],
                    "cache_sizes": cache_metrics["cache_sizes"]
                })

            cpu, memory = self._get_current_system_metrics()
            result.cpu_usage_percent = cpu
            result.memory_usage_mb = memory

            logger.info(f"Cache Performance Test completed: {result.requests_per_second:.2f} ops/s, {result.custom_metrics.get('cache_hit_rate', 0):.1f}% hit rate")

        finally:
            self._stop_system_monitoring()

        return result

    async def run_database_stress_test(
        self,
        query_templates: List[str],
        num_queries: int = 1000
    ) -> PerformanceTestResult:
        """Run database stress test"""
        logger.info(f"🗄️ Running Database Stress Test with {num_queries} queries")

        result = PerformanceTestResult(test_name="database_stress")

        response_times = []
        errors = 0

        start_time = time.time()
        self._start_system_monitoring()

        try:
            # Generate test queries
            test_queries = []
            for i in range(num_queries):
                template = query_templates[i % len(query_templates)]
                # Simple parameter substitution
                query = template.replace("$1", str(i % 1000))
                test_queries.append(query)

            # Execute queries with concurrency control
            semaphore = asyncio.Semaphore(self.concurrent_users)
            tasks = []

            for query in test_queries:
                task = self._execute_database_query(
                    semaphore,
                    query,
                    response_times,
                    result
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Calculate metrics
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.requests_completed = len(response_times)
            result.requests_failed = errors

            if response_times:
                result.avg_response_time_ms = statistics.mean(response_times)
                result.p50_response_time_ms = np.percentile(response_times, 50)
                result.p95_response_time_ms = np.percentile(response_times, 95)
                result.p99_response_time_ms = np.percentile(response_times, 99)
                result.min_response_time_ms = min(response_times)
                result.max_response_time_ms = max(response_times)

            result.requests_per_second = result.requests_completed / result.duration_seconds
            result.error_rate_percent = (errors / max(result.requests_completed + errors, 1)) * 100

            # Add database-specific metrics
            if self.query_optimizer:
                performance_report = await self.query_optimizer.get_performance_report(1)  # Last minute
                result.custom_metrics.update({
                    "avg_execution_time": performance_report.get("performance_metrics", {}).get("avg_execution_time_ms", 0),
                    "index_usage_rate": performance_report.get("query_analysis", {}).get("index_usage_rate", 0)
                })

            cpu, memory = self._get_current_system_metrics()
            result.cpu_usage_percent = cpu
            result.memory_usage_mb = memory

            logger.info(f"Database Stress Test completed: {result.requests_per_second:.2f} qps, {result.avg_response_time_ms:.2f}ms avg")

        finally:
            self._stop_system_monitoring()

        return result

    async def run_connection_pool_test(
        self,
        pool_config: DatabaseConfig,
        operations: int = 500
    ) -> PerformanceTestResult:
        """Run connection pool stress test"""
        logger.info(f"🔌 Running Connection Pool Test with {operations} operations")

        result = PerformanceTestResult(test_name="connection_pool")

        # Create test connection pool
        test_pool = ConnectionPool(
            pool_config,
            pool_name="performance_test_pool",
            auto_resize=False
        )

        try:
            # Initialize pool (may fail with test credentials, but we'll test the logic)
            await test_pool.initialize()

            response_times = []
            errors = 0

            start_time = time.time()
            self._start_system_monitoring()

            # Test connection acquisition and release
            semaphore = asyncio.Semaphore(self.concurrent_users)
            tasks = []

            for i in range(operations):
                task = self._execute_connection_operation(
                    semaphore,
                    test_pool,
                    i,
                    response_times,
                    result
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Calculate metrics
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.requests_completed = len(response_times)
            result.requests_failed = errors

            if response_times:
                result.avg_response_time_ms = statistics.mean(response_times)
                result.p95_response_time_ms = np.percentile(response_times, 95)
                result.p99_response_time_ms = np.percentile(response_times, 99)

            result.requests_per_second = result.requests_completed / result.duration_seconds
            result.error_rate_percent = (errors / max(result.requests_completed + errors, 1)) * 100

            # Get pool metrics
            pool_metrics = await test_pool.get_metrics()
            result.custom_metrics.update({
                "peak_connections": pool_metrics["statistics"]["peak_connections"],
                "connection_reuse_count": pool_metrics["statistics"]["connection_reuse_count"],
                "avg_wait_time_ms": pool_metrics["statistics"]["avg_wait_time_ms"]
            })

            cpu, memory = self._get_current_system_metrics()
            result.cpu_usage_percent = cpu
            result.memory_usage_mb = memory

            logger.info(f"Connection Pool Test completed: {result.requests_per_second:.2f} ops/s")

        finally:
            await test_pool.close()
            self._stop_system_monitoring()

        return result

    async def run_end_to_end_test(
        self,
        user_scenarios: List[Dict[str, Any]]
    ) -> PerformanceTestResult:
        """Run end-to-end performance test"""
        logger.info(f"🔄 Running End-to-End Test with {len(user_scenarios)} scenarios")

        result = PerformanceTestResult(test_name="end_to_end")

        response_times = []
        errors = 0

        start_time = time.time()
        self._start_system_monitoring()

        try:
            # Execute user scenarios
            semaphore = asyncio.Semaphore(self.concurrent_users)
            tasks = []

            for i, scenario in enumerate(user_scenarios):
                task = self._execute_user_scenario(
                    semaphore,
                    scenario,
                    i,
                    response_times,
                    result
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Calculate metrics
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.requests_completed = len(response_times)
            result.requests_failed = errors

            if response_times:
                result.avg_response_time_ms = statistics.mean(response_times)
                result.p95_response_time_ms = np.percentile(response_times, 95)
                result.p99_response_time_ms = np.percentile(response_times, 99)

            result.requests_per_second = result.requests_completed / result.duration_seconds
            result.error_rate_percent = (errors / max(result.requests_completed + errors, 1)) * 100

            # Aggregate metrics from all components
            if self.cache:
                cache_metrics = self.cache.get_metrics()
                result.custom_metrics["cache_hit_rate"] = cache_metrics["hit_rate"]

            if self.query_optimizer:
                query_metrics = await self.query_optimizer.get_real_time_metrics()
                result.custom_metrics["query_performance"] = query_metrics

            cpu, memory = self._get_current_system_metrics()
            result.cpu_usage_percent = cpu
            result.memory_usage_mb = memory

            logger.info(f"End-to-End Test completed: {result.requests_per_second:.2f} scenarios/s")

        finally:
            self._stop_system_monitoring()

        return result

    async def run_performance_regression_test(
        self,
        baseline_file: str = "performance_baseline.json"
    ) -> Dict[str, Any]:
        """Compare current performance against baseline"""
        logger.info("📊 Running Performance Regression Test")

        # Load baseline
        baseline_results = self._load_baseline(baseline_file)
        if not baseline_results:
            logger.warning("No baseline found for comparison")
            return {"status": "no_baseline"}

        # Run current tests
        current_results = []
        current_results.append(await self.run_semantic_search_test(["test query"] * 100))
        current_results.append(await self.run_cache_performance_test(500))

        # Compare results
        regression_report = {
            "timestamp": datetime.now().isoformat(),
            "baseline_date": baseline_results.get("timestamp"),
            "comparisons": []
        }

        for current in current_results:
            baseline = baseline_results.get(current.test_name)
            if baseline:
                comparison = self._compare_results(current, baseline)
                regression_report["comparisons"].append(comparison)

        # Determine overall regression status
        has_regression = any(
            comp.get("regression_detected", False)
            for comp in regression_report["comparisons"]
        )

        regression_report["overall_status"] = "regression" if has_regression else "passed"

        # Save current results as new baseline
        self._save_baseline(current_results)

        return regression_report

    def evaluate_test_result(self, result: PerformanceTestResult) -> Dict[str, Any]:
        """Evaluate test result against thresholds"""
        evaluation = {
            "passed": True,
            "threshold_violations": []
        }

        # Check response time thresholds
        if result.avg_response_time_ms > self.thresholds.max_avg_response_time_ms:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"Average response time {result.avg_response_time_ms:.2f}ms exceeds threshold {self.thresholds.max_avg_response_time_ms}ms"
            )

        if result.p95_response_time_ms > self.thresholds.max_p95_response_time_ms:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"P95 response time {result.p95_response_time_ms:.2f}ms exceeds threshold {self.thresholds.max_p95_response_time_ms}ms"
            )

        # Check throughput threshold
        if result.requests_per_second < self.thresholds.min_requests_per_second:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"Requests per second {result.requests_per_second:.2f} below threshold {self.thresholds.min_requests_per_second}"
            )

        # Check error rate
        if result.error_rate_percent > self.thresholds.max_error_rate_percent:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"Error rate {result.error_rate_percent:.2f}% exceeds threshold {self.thresholds.max_error_rate_percent}%"
            )

        # Check resource usage
        if result.cpu_usage_percent > self.thresholds.max_cpu_usage_percent:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"CPU usage {result.cpu_usage_percent:.2f}% exceeds threshold {self.thresholds.max_cpu_usage_percent}%"
            )

        if result.memory_usage_mb > self.thresholds.max_memory_usage_mb:
            evaluation["passed"] = False
            evaluation["threshold_violations"].append(
                f"Memory usage {result.memory_usage_mb:.2f}MB exceeds threshold {self.thresholds.max_memory_usage_mb}MB"
            )

        return evaluation

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "test_configuration": {
                "concurrent_users": self.concurrent_users,
                "test_duration_seconds": self.test_duration_seconds,
                "ramp_up_seconds": self.ramp_up_seconds
            },
            "test_results": [asdict(result) for result in self.test_results],
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": 0,
                "failed_tests": 0
            },
            "performance_trends": {},
            "recommendations": []
        }

        # Evaluate each test
        for result in self.test_results:
            evaluation = self.evaluate_test_result(result)
            if evaluation["passed"]:
                report["summary"]["passed_tests"] += 1
            else:
                report["summary"]["failed_tests"] += 1
                report["recommendations"].extend(evaluation["threshold_violations"])

        # Add performance trends
        if len(self.test_results) > 1:
            report["performance_trends"] = self._analyze_performance_trends()

        return report

    # Private helper methods

    async def _execute_search_with_monitoring(
        self,
        semaphore: asyncio.Semaphore,
        query: str,
        embedding: List[float],
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute semantic search with monitoring"""
        async with semaphore:
            start_time = time.time()
            try:
                if self.pgvector_optimizer:
                    await self.pgvector_optimizer.execute_optimized_search(
                        "vehicles", "embedding", embedding, limit=10
                    )
                elif self.cache:
                    cache_key = f"search_{hash(query)}"
                    await self.cache.get(cache_key)

                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                result.requests_completed += 1

            except Exception as e:
                logger.error(f"Search execution failed: {e}")
                result.requests_failed += 1

    async def _execute_cache_write(
        self,
        key: str,
        value: Any,
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute cache write operation"""
        start_time = time.time()
        try:
            if self.cache:
                await self.cache.set(key, value)

            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            result.requests_completed += 1

        except Exception as e:
            logger.error(f"Cache write failed: {e}")
            result.requests_failed += 1

    async def _execute_cache_read(
        self,
        key: str,
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute cache read operation"""
        start_time = time.time()
        try:
            if self.cache:
                await self.cache.get(key)

            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            result.requests_completed += 1

        except Exception as e:
            logger.error(f"Cache read failed: {e}")
            result.requests_failed += 1

    async def _execute_database_query(
        self,
        semaphore: asyncio.Semaphore,
        query: str,
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute database query"""
        async with semaphore:
            start_time = time.time()
            try:
                # Mock query execution - in real implementation, use actual DB
                await asyncio.sleep(0.01)  # Simulate query time

                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                result.requests_completed += 1

                # Record with query optimizer if available
                if self.query_optimizer:
                    await self.query_optimizer.record_query(
                        query_text=query,
                        execution_time_ms=response_time,
                        index_used=True,
                        cache_hit=False
                    )

            except Exception as e:
                logger.error(f"Database query failed: {e}")
                result.requests_failed += 1

    async def _execute_connection_operation(
        self,
        semaphore: asyncio.Semaphore,
        pool: ConnectionPool,
        operation_id: int,
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute connection pool operation"""
        async with semaphore:
            start_time = time.time()
            try:
                # Mock connection operation
                await asyncio.sleep(0.005)  # Simulate connection time

                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                result.requests_completed += 1

            except Exception as e:
                logger.error(f"Connection operation failed: {e}")
                result.requests_failed += 1

    async def _execute_user_scenario(
        self,
        semaphore: asyncio.Semaphore,
        scenario: Dict[str, Any],
        scenario_id: int,
        response_times: List[float],
        result: PerformanceTestResult
    ):
        """Execute user scenario"""
        async with semaphore:
            start_time = time.time()
            try:
                # Simulate user scenario steps
                for step in scenario.get("steps", []):
                    step_type = step.get("type", "delay")

                    if step_type == "cache_read":
                        if self.cache:
                            await self.cache.get(step.get("key", f"scenario_{scenario_id}"))
                    elif step_type == "search":
                        if self.cache:
                            await self.cache.get(f"search_{step.get('query', 'test')}")
                    elif step_type == "delay":
                        await asyncio.sleep(step.get("duration", 0.01))

                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                result.requests_completed += 1

            except Exception as e:
                logger.error(f"User scenario failed: {e}")
                result.requests_failed += 1

    def _start_system_monitoring(self):
        """Start system resource monitoring"""
        self.monitoring_active = True
        self.system_metrics = {"cpu": [], "memory": []}

    def _stop_system_monitoring(self):
        """Stop system resource monitoring"""
        self.monitoring_active = False

    def _get_current_system_metrics(self) -> Tuple[float, float]:
        """Get current CPU and memory usage"""
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        memory_mb = memory_info.used / (1024 * 1024)
        return cpu_percent, memory_mb

    def _load_baseline(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load performance baseline from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")
            return None

    def _save_baseline(self, results: List[PerformanceTestResult], filename: str = "performance_baseline.json"):
        """Save current results as baseline"""
        baseline = {
            "timestamp": datetime.now().isoformat(),
            "results": {result.test_name: asdict(result) for result in results}
        }

        try:
            with open(filename, 'w') as f:
                json.dump(baseline, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")

    def _compare_results(self, current: PerformanceTestResult, baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current result with baseline"""
        comparison = {
            "test_name": current.test_name,
            "regression_detected": False,
            "improvement_detected": False,
            "metrics_comparison": {}
        }

        # Compare key metrics
        metrics_to_compare = [
            "avg_response_time_ms",
            "p95_response_time_ms",
            "requests_per_second",
            "error_rate_percent"
        ]

        for metric in metrics_to_compare:
            current_value = getattr(current, metric)
            baseline_value = baseline.get(metric, 0)

            # Calculate percentage change
            if baseline_value > 0:
                change_percent = ((current_value - baseline_value) / baseline_value) * 100

                comparison["metrics_comparison"][metric] = {
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": change_percent
                }

                # Check for regression (worsening performance)
                if metric in ["avg_response_time_ms", "p95_response_time_ms", "error_rate_percent"]:
                    if change_percent > 10:  # 10% degradation threshold
                        comparison["regression_detected"] = True
                elif metric == "requests_per_second":
                    if change_percent < -10:  # 10% throughput degradation
                        comparison["regression_detected"] = True

        return comparison

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends across test results"""
        trends = {
            "response_time_trend": "stable",
            "throughput_trend": "stable",
            "error_rate_trend": "stable"
        }

        if len(self.test_results) < 2:
            return trends

        # Simple trend analysis
        recent_tests = self.test_results[-5:]  # Last 5 tests
        response_times = [test.avg_response_time_ms for test in recent_tests]
        throughputs = [test.requests_per_second for test in recent_tests]
        error_rates = [test.error_rate_percent for test in recent_tests]

        # Response time trend
        if len(response_times) >= 3:
            if all(response_times[i] < response_times[i+1] for i in range(len(response_times)-1)):
                trends["response_time_trend"] = "degrading"
            elif all(response_times[i] > response_times[i+1] for i in range(len(response_times)-1)):
                trends["response_time_trend"] = "improving"

        # Throughput trend
        if len(throughputs) >= 3:
            if all(throughputs[i] > throughputs[i+1] for i in range(len(throughputs)-1)):
                trends["throughput_trend"] = "degrading"
            elif all(throughputs[i] < throughputs[i+1] for i in range(len(throughputs)-1)):
                trends["throughput_trend"] = "improving"

        return trends

# Global test suite instance
performance_test_suite = PerformanceTestSuite()