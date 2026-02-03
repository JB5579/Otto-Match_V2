"""
Test Suite for Performance Testing Framework
Tests for the performance testing components themselves
"""

import asyncio
import pytest
import numpy as np
import sys
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.performance.performance_test_suite import (
    PerformanceTestSuite,
    PerformanceTestResult,
    PerformanceThresholds
)

class TestPerformanceTestResult:
    """Test performance test result data structure"""

    def test_result_initialization(self):
        """Test result initialization with defaults"""
        result = PerformanceTestResult(test_name="test")

        assert result.test_name == "test"
        assert result.duration_seconds == 0.0
        assert result.requests_completed == 0
        assert result.requests_failed == 0
        assert result.requests_per_second == 0.0
        assert result.avg_response_time_ms == 0.0
        assert result.custom_metrics == {}

    def test_result_with_values(self):
        """Test result with custom values"""
        now = datetime.now()
        result = PerformanceTestResult(
            test_name="search_test",
            duration_seconds=60.0,
            requests_completed=1000,
            requests_failed=5,
            avg_response_time_ms=150.5,
            p95_response_time_ms=300.0,
            p99_response_time_ms=500.0,
            cpu_usage_percent=45.2,
            memory_usage_mb=512.0,
            error_rate_percent=0.5,
            custom_metrics={"cache_hit_rate": 85.0}
        )

        assert result.test_name == "search_test"
        assert result.duration_seconds == 60.0
        assert result.requests_completed == 1000
        assert result.requests_failed == 5
        assert result.avg_response_time_ms == 150.5
        assert result.custom_metrics["cache_hit_rate"] == 85.0

class TestPerformanceThresholds:
    """Test performance thresholds configuration"""

    def test_default_thresholds(self):
        """Test default threshold values"""
        thresholds = PerformanceThresholds()

        assert thresholds.max_avg_response_time_ms == 500.0
        assert thresholds.max_p95_response_time_ms == 1000.0
        assert thresholds.max_p99_response_time_ms == 2000.0
        assert thresholds.min_requests_per_second == 10.0
        assert thresholds.max_error_rate_percent == 1.0
        assert thresholds.max_cpu_usage_percent == 80.0
        assert thresholds.max_memory_usage_mb == 1000.0

    def test_custom_thresholds(self):
        """Test custom threshold values"""
        thresholds = PerformanceThresholds(
            max_avg_response_time_ms=250.0,
            max_p95_response_time_ms=500.0,
            min_requests_per_second=20.0,
            max_cpu_usage_percent=70.0
        )

        assert thresholds.max_avg_response_time_ms == 250.0
        assert thresholds.max_p95_response_time_ms == 500.0
        assert thresholds.min_requests_per_second == 20.0
        assert thresholds.max_cpu_usage_percent == 70.0

class TestPerformanceTestSuite:
    """Test performance test suite functionality"""

    @pytest.fixture
    def suite(self):
        """Create test suite instance"""
        return PerformanceTestSuite(
            test_duration_seconds=10,
            concurrent_users=2,
            ramp_up_seconds=2
        )

    @pytest.fixture
    def thresholds(self):
        """Create custom thresholds"""
        return PerformanceThresholds(
            max_avg_response_time_ms=100.0,
            max_p95_response_time_ms=200.0,
            min_requests_per_second=5.0,
            max_error_rate_percent=5.0
        )

    def test_suite_initialization(self, suite):
        """Test suite initialization"""
        assert suite.test_duration_seconds == 10
        assert suite.concurrent_users == 2
        assert suite.ramp_up_seconds == 2
        assert suite.cache is None
        assert len(suite.test_results) == 0
        assert suite.monitoring_active == False

    def test_suite_with_custom_thresholds(self, thresholds):
        """Test suite with custom thresholds"""
        suite = PerformanceTestSuite(thresholds=thresholds)
        assert suite.thresholds == thresholds

    @pytest.mark.asyncio
    async def test_initialize_cache_only(self, suite):
        """Test initialization with cache only"""
        result = await suite.initialize(redis_url=None)  # No Redis for testing
        assert result == True
        assert suite.cache is not None
        assert suite.query_optimizer is not None

    @pytest.mark.asyncio
    async def test_semantic_search_test_mock(self, suite):
        """Test semantic search performance test with mock data"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Create test queries and embeddings
        queries = ["test query 1", "test query 2", "test query 3"] * 10
        embeddings = [np.random.random(1536).tolist() for _ in queries]

        # Run test (will use mock execution)
        result = await suite.run_semantic_search_test(queries, vector_dimensions=1536)

        assert result.test_name == "semantic_search"
        assert result.requests_completed > 0
        assert result.duration_seconds > 0
        assert result.requests_per_second > 0

    @pytest.mark.asyncio
    async def test_cache_performance_test(self, suite):
        """Test cache performance test"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Run cache test
        result = await suite.run_cache_performance_test(
            cache_operations=100,
            cache_keys=["test_key_1", "test_key_2", "test_key_3"]
        )

        assert result.test_name == "cache_performance"
        assert result.requests_completed > 0
        assert result.duration_seconds > 0
        assert "cache_hit_rate" in result.custom_metrics

    @pytest.mark.asyncio
    async def test_database_stress_test_mock(self, suite):
        """Test database stress test with mock queries"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Create test query templates
        query_templates = [
            "SELECT * FROM vehicles WHERE price < $1",
            "SELECT COUNT(*) FROM vehicles"
        ]

        # Run test
        result = await suite.run_database_stress_test(
            query_templates=query_templates,
            num_queries=50
        )

        assert result.test_name == "database_stress"
        assert result.requests_completed > 0
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_end_to_end_test(self, suite):
        """Test end-to-end performance test"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Create user scenarios
        scenarios = [
            {
                "name": "Simple Search",
                "steps": [
                    {"type": "search", "query": "test"},
                    {"type": "delay", "duration": 0.01}
                ]
            },
            {
                "name": "Cache Operation",
                "steps": [
                    {"type": "cache_read", "key": "test_key"}
                ]
            }
        ] * 10

        # Run test
        result = await suite.run_end_to_end_test(scenarios)

        assert result.test_name == "end_to_end"
        assert result.requests_completed > 0
        assert result.duration_seconds > 0

    def test_evaluate_test_result_pass(self, suite):
        """Test result evaluation - passing case"""
        result = PerformanceTestResult(
            test_name="test",
            avg_response_time_ms=100.0,
            p95_response_time_ms=200.0,
            p99_response_time_ms=300.0,
            requests_per_second=20.0,
            error_rate_percent=0.5,
            cpu_usage_percent=50.0,
            memory_usage_mb=500.0
        )

        evaluation = suite.evaluate_test_result(result)
        assert evaluation["passed"] == True
        assert len(evaluation["threshold_violations"]) == 0

    def test_evaluate_test_result_fail(self, suite):
        """Test result evaluation - failing case"""
        result = PerformanceTestResult(
            test_name="test",
            avg_response_time_ms=1000.0,  # Too high
            p95_response_time_ms=2000.0,  # Too high
            requests_per_second=5.0,  # Too low
            error_rate_percent=5.0,  # Too high
            cpu_usage_percent=90.0,  # Too high
            memory_usage_mb=1500.0  # Too high
        )

        evaluation = suite.evaluate_test_result(result)
        assert evaluation["passed"] == False
        assert len(evaluation["threshold_violations"]) > 0

    @pytest.mark.asyncio
    async def test_performance_regression_test_no_baseline(self, suite):
        """Test regression test without baseline"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Run regression test (no baseline file)
        result = await suite.run_performance_regression_test("nonexistent_baseline.json")
        assert result["status"] == "no_baseline"

    @pytest.mark.asyncio
    async def test_generate_performance_report(self, suite):
        """Test performance report generation"""
        # Initialize suite
        await suite.initialize(redis_url=None)

        # Add some test results
        result1 = PerformanceTestResult(
            test_name="test1",
            avg_response_time_ms=100.0,
            requests_per_second=20.0,
            error_rate_percent=0.0
        )
        result2 = PerformanceTestResult(
            test_name="test2",
            avg_response_time_ms=150.0,
            requests_per_second=15.0,
            error_rate_percent=1.0
        )

        suite.test_results = [result1, result2]

        # Generate report
        report = await suite.generate_performance_report()

        assert "generated_at" in report
        assert "test_configuration" in report
        assert "test_results" in report
        assert "summary" in report

        assert report["summary"]["total_tests"] == 2
        assert len(report["test_results"]) == 2

    def test_system_monitoring(self, suite):
        """Test system monitoring functionality"""
        # Test start monitoring
        suite._start_system_monitoring()
        assert suite.monitoring_active == True
        assert suite.system_metrics == {"cpu": [], "memory": []}

        # Test stop monitoring
        suite._stop_system_monitoring()
        assert suite.monitoring_active == False

    def test_system_metrics_collection(self, suite):
        """Test system metrics collection"""
        cpu, memory = suite._get_current_system_metrics()
        assert isinstance(cpu, float)
        assert isinstance(memory, float)
        assert cpu >= 0
        assert memory > 0

    def test_result_comparison(self, suite):
        """Test result comparison for regression detection"""
        current = PerformanceTestResult(
            test_name="test",
            avg_response_time_ms=550.0,  # 10% slower than baseline
            p95_response_time_ms=1100.0,  # 10% slower than baseline
            requests_per_second=9.0,  # 10% slower than baseline
            error_rate_percent=1.1  # Slightly higher
        )

        baseline = {
            "avg_response_time_ms": 500.0,
            "p95_response_time_ms": 1000.0,
            "requests_per_second": 10.0,
            "error_rate_percent": 1.0
        }

        comparison = suite._compare_results(current, baseline)
        assert comparison["test_name"] == "test"
        assert comparison["regression_detected"] == True
        assert "metrics_comparison" in comparison

        # Check specific metric comparisons
        assert comparison["metrics_comparison"]["avg_response_time_ms"]["change_percent"] == 10.0
        assert comparison["metrics_comparison"]["p95_response_time_ms"]["change_percent"] == 10.0
        assert comparison["metrics_comparison"]["requests_per_second"]["change_percent"] == -10.0

    def test_performance_trends_analysis(self, suite):
        """Test performance trends analysis"""
        # Create test results with improving trend
        improving_results = [
            PerformanceTestResult(
                test_name="test",
                avg_response_time_ms=500.0,
                requests_per_second=10.0,
                error_rate_percent=1.0
            ),
            PerformanceTestResult(
                test_name="test",
                avg_response_time_ms=400.0,
                requests_per_second=12.0,
                error_rate_percent=0.8
            ),
            PerformanceTestResult(
                test_name="test",
                avg_response_time_ms=300.0,
                requests_per_second=15.0,
                error_rate_percent=0.5
            )
        ]

        suite.test_results = improving_results
        trends = suite._analyze_performance_trends()

        assert trends["response_time_trend"] == "improving"
        assert trends["throughput_trend"] == "improving"

    def test_performance_trends_insufficient_data(self, suite):
        """Test trends analysis with insufficient data"""
        # Only one result
        suite.test_results = [
            PerformanceTestResult(
                test_name="test",
                avg_response_time_ms=400.0,
                requests_per_second=12.0,
                error_rate_percent=0.8
            )
        ]

        trends = suite._analyze_performance_trends()
        assert trends["response_time_trend"] == "stable"
        assert trends["throughput_trend"] == "stable"

class TestIntegration:
    """Integration tests for performance testing"""

    @pytest.mark.asyncio
    async def test_full_test_workflow(self):
        """Test complete performance test workflow"""
        # Create test suite
        suite = PerformanceTestSuite(
            test_duration_seconds=5,
            concurrent_users=2
        )

        # Initialize
        await suite.initialize(redis_url=None)

        # Run multiple tests
        cache_result = await suite.run_cache_performance_test(
            cache_operations=50,
            cache_keys=["key1", "key2", "key3"]
        )

        e2e_result = await suite.run_end_to_end_test([
            {"name": "test", "steps": [{"type": "delay", "duration": 0.01}]}
        ] * 10)

        # Verify results
        assert cache_result.test_name == "cache_performance"
        assert e2e_result.test_name == "end_to_end"

        # Generate report
        report = await suite.generate_performance_report()
        assert report["summary"]["total_tests"] == 2

        # Evaluate results
        cache_evaluation = suite.evaluate_test_result(cache_result)
        e2e_evaluation = suite.evaluate_test_result(e2e_result)

        assert "passed" in cache_evaluation
        assert "passed" in e2e_evaluation

if __name__ == "__main__":
    # Run basic tests
    print("Running Performance Test Suite tests...")

    # Test result initialization
    print("\n1. Testing Performance Test Result...")
    result = PerformanceTestResult(
        test_name="test",
        avg_response_time_ms=100.0,
        requests_per_second=20.0
    )
    assert result.test_name == "test"
    assert result.avg_response_time_ms == 100.0
    print("Performance test result tests passed")

    # Test thresholds
    print("\n2. Testing Performance Thresholds...")
    thresholds = PerformanceThresholds(
        max_avg_response_time_ms=250.0,
        min_requests_per_second=20.0
    )
    assert thresholds.max_avg_response_time_ms == 250.0
    assert thresholds.min_requests_per_second == 20.0
    print("Performance thresholds tests passed")

    # Test suite initialization
    print("\n3. Testing Performance Test Suite...")
    suite = PerformanceTestSuite(
        test_duration_seconds=30,
        concurrent_users=5
    )
    assert suite.test_duration_seconds == 30
    assert suite.concurrent_users == 5
    print("Performance test suite tests passed")

    # Test evaluation
    print("\n4. Testing Test Result Evaluation...")
    suite = PerformanceTestSuite()
    good_result = PerformanceTestResult(
        test_name="good_test",
        avg_response_time_ms=100.0,
        requests_per_second=20.0,
        error_rate_percent=0.0
    )
    evaluation = suite.evaluate_test_result(good_result)
    assert evaluation["passed"] == True
    print("Test evaluation tests passed")

    print("\nAll Performance Test Suite tests completed successfully!")