"""
Test Suite for Query Optimizer
Comprehensive testing for Story 1-8 query optimization and monitoring
"""

import asyncio
import pytest
import numpy as np
import sys
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.query_optimizer import (
    QueryOptimizer,
    QueryMetrics,
    QueryPattern,
    PerformanceThresholds
)

class TestQueryMetrics:
    """Test query metrics data structure"""

    def test_query_metrics_creation(self):
        """Test query metrics creation"""
        metrics = QueryMetrics(
            query_id="test123",
            query_text="SELECT * FROM vehicles",
            execution_time_ms=150.5,
            cpu_usage_percent=25.3,
            memory_usage_mb=512.0,
            rows_examined=100,
            rows_returned=20,
            index_used=True,
            cache_hit=False,
            similarity_scores=[0.9, 0.8],
            query_type="select"
        )

        assert metrics.query_id == "test123"
        assert metrics.query_text == "SELECT * FROM vehicles"
        assert metrics.execution_time_ms == 150.5
        assert metrics.index_used == True
        assert len(metrics.similarity_scores) == 2

    def test_query_metrics_defaults(self):
        """Test query metrics with defaults"""
        metrics = QueryMetrics(
            query_id="test",
            query_text="SELECT 1",
            execution_time_ms=10.0,
            cpu_usage_percent=10.0,
            memory_usage_mb=100.0,
            rows_examined=0,
            rows_returned=0
        )

        assert metrics.index_used == False
        assert metrics.cache_hit == False
        assert metrics.similarity_scores == []
        assert metrics.query_type == "unknown"
        assert metrics.optimization_hints == []

class TestPerformanceThresholds:
    """Test performance thresholds configuration"""

    def test_default_thresholds(self):
        """Test default threshold values"""
        thresholds = PerformanceThresholds()

        assert thresholds.slow_query_threshold_ms == 1000.0
        assert thresholds.critical_query_threshold_ms == 5000.0
        assert thresholds.high_cpu_threshold_percent == 80.0
        assert thresholds.high_memory_threshold_mb == 1000.0
        assert thresholds.low_cache_hit_rate_percent == 50.0
        assert thresholds.low_similarity_threshold == 0.5

    def test_custom_thresholds(self):
        """Test custom threshold values"""
        thresholds = PerformanceThresholds(
            slow_query_threshold_ms=500.0,
            critical_query_threshold_ms=2000.0,
            high_cpu_threshold_percent=90.0
        )

        assert thresholds.slow_query_threshold_ms == 500.0
        assert thresholds.critical_query_threshold_ms == 2000.0
        assert thresholds.high_cpu_threshold_percent == 90.0

class TestQueryOptimizer:
    """Test query optimizer functionality"""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance for testing"""
        return QueryOptimizer(max_history_size=100)

    @pytest.fixture
    def sample_metrics(self):
        """Sample query metrics for testing"""
        return QueryMetrics(
            query_id="sample123",
            query_text="SELECT * FROM vehicles WHERE price < 30000",
            execution_time_ms=250.0,
            cpu_usage_percent=30.0,
            memory_usage_mb=600.0,
            rows_examined=500,
            rows_returned=50,
            index_used=True,
            cache_hit=False,
            query_type="select"
        )

    @pytest.fixture
    def slow_query_metrics(self):
        """Slow query metrics for testing"""
        return QueryMetrics(
            query_id="slow456",
            query_text="SELECT * FROM vehicles WHERE description LIKE '%test%'",
            execution_time_ms=1500.0,  # Slow query
            cpu_usage_percent=60.0,
            memory_usage_mb=800.0,
            rows_examined=10000,
            rows_returned=100,
            index_used=False,
            cache_hit=False,
            query_type="select"
        )

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.max_history_size == 100
        assert len(optimizer.query_history) == 0
        assert len(optimizer.query_patterns) == 0
        assert len(optimizer.slow_queries) == 0
        assert optimizer.is_monitoring == False

    def test_query_id_generation(self, optimizer):
        """Test query ID generation"""
        id1 = optimizer._generate_query_id("SELECT * FROM vehicles")
        id2 = optimizer._generate_query_id("SELECT * FROM vehicles")
        id3 = optimizer._generate_query_id("SELECT * FROM users")

        # Different queries should have different IDs
        assert id1 != id3

        # Same query at different times should have different IDs
        import time
        time.sleep(0.01)
        id4 = optimizer._generate_query_id("SELECT * FROM vehicles")
        assert id1 != id4

        # IDs should be consistent length
        assert len(id1) == len(id2) == len(id3) == len(id4) == 16

    def test_query_pattern_extraction(self, optimizer):
        """Test query pattern extraction"""
        query1 = "SELECT * FROM vehicles WHERE price = 30000"
        query2 = "SELECT * FROM vehicles WHERE price = 25000"
        query3 = "SELECT * FROM vehicles WHERE make = 'Toyota'"

        pattern1 = optimizer._extract_query_pattern(query1)
        pattern2 = optimizer._extract_query_pattern(query2)
        pattern3 = optimizer._extract_query_pattern(query3)

        # Queries with same structure should have same pattern
        assert pattern1 == pattern2

        # Different structure should have different pattern
        assert pattern1 != pattern3

    @pytest.mark.asyncio
    async def test_record_query(self, optimizer, sample_metrics):
        """Test recording query metrics"""
        await optimizer.record_query(
            query_text=sample_metrics.query_text,
            execution_time_ms=sample_metrics.execution_time_ms,
            rows_examined=sample_metrics.rows_examined,
            rows_returned=sample_metrics.rows_returned,
            index_used=sample_metrics.index_used,
            cache_hit=sample_metrics.cache_hit,
            query_type=sample_metrics.query_type
        )

        assert len(optimizer.query_history) == 1
        recorded = optimizer.query_history[0]

        assert recorded.query_text == sample_metrics.query_text
        assert recorded.execution_time_ms == sample_metrics.execution_time_ms
        assert recorded.index_used == sample_metrics.index_used

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, optimizer, slow_query_metrics):
        """Test slow query detection"""
        await optimizer.record_query(
            query_text=slow_query_metrics.query_text,
            execution_time_ms=slow_query_metrics.execution_time_ms,
            rows_examined=slow_query_metrics.rows_examined,
            rows_returned=slow_query_metrics.rows_returned,
            index_used=slow_query_metrics.index_used,
            cache_hit=slow_query_metrics.cache_hit,
            query_type=slow_query_metrics.query_type
        )

        assert len(optimizer.slow_queries) == 1
        assert optimizer.slow_queries[0].execution_time_ms == 1500.0

    @pytest.mark.asyncio
    async def test_query_patterns_update(self, optimizer):
        """Test query pattern statistics update"""
        # Record similar queries
        await optimizer.record_query("SELECT * FROM vehicles WHERE price = 30000", 100.0)
        await optimizer.record_query("SELECT * FROM vehicles WHERE price = 25000", 120.0)
        await optimizer.record_query("SELECT * FROM vehicles WHERE price = 20000", 90.0)

        # Should have one pattern
        assert len(optimizer.query_patterns) == 1

        pattern = list(optimizer.query_patterns.values())[0]
        assert pattern.total_executions == 3
        assert pattern.frequency == 3
        assert pattern.avg_execution_time_ms == 110.0  # (100 + 120 + 90) / 3

    @pytest.mark.asyncio
    async def test_query_optimization(self, optimizer):
        """Test query optimization"""
        query = "SELECT * FROM vehicles WHERE price > 30000 AND make = 'Toyota' ORDER BY year DESC"
        result = await optimizer.optimize_query(query)

        assert "original_query" in result
        assert "optimizations" in result
        assert "optimized_query" in result
        assert result["original_query"] == query

        # Should generate some optimizations
        assert len(result["optimizations"]) > 0

    @pytest.mark.asyncio
    async def test_similarity_query_optimization(self, optimizer):
        """Test similarity query optimization"""
        query = "SELECT *, embedding <=> query_embedding as distance FROM vehicles ORDER BY embedding <=> query_embedding LIMIT 10"
        result = await optimizer.optimize_query(query)

        # Should have similarity-specific optimizations
        optimizations = result.get("optimizations", [])
        similarity_opt_found = any("similarity" in opt.lower() for opt in optimizations)
        assert similarity_opt_found

    @pytest.mark.asyncio
    async def test_performance_report(self, optimizer):
        """Test performance report generation"""
        # Record some test queries
        queries_data = [
            ("SELECT * FROM vehicles", 50.0, True, False),
            ("SELECT * FROM vehicles WHERE price < 30000", 100.0, True, True),
            ("SELECT * FROM vehicles WHERE description LIKE '%test%'", 1500.0, False, False),
            ("SELECT * FROM users", 30.0, True, True)
        ]

        for query_text, exec_time, index_used, cache_hit in queries_data:
            await optimizer.record_query(
                query_text=query_text,
                execution_time_ms=exec_time,
                index_used=index_used,
                cache_hit=cache_hit,
                query_type="select"
            )

        # Generate report
        report = await optimizer.get_performance_report(time_window_minutes=60)

        assert "total_queries" in report
        assert report["total_queries"] == 4
        assert "performance_metrics" in report
        assert "query_analysis" in report
        assert "slow_queries" in report["query_analysis"]
        assert report["query_analysis"]["slow_queries"] == 1

    @pytest.mark.asyncio
    async def test_real_time_metrics(self, optimizer):
        """Test real-time metrics collection"""
        # Record a recent query
        await optimizer.record_query(
            query_text="SELECT * FROM vehicles LIMIT 10",
            execution_time_ms=75.0,
            index_used=True,
            cache_hit=True,
            query_type="select"
        )

        metrics = await optimizer.get_real_time_metrics()

        assert "timestamp" in metrics
        assert "query_performance" in metrics
        assert "system_resources" in metrics
        assert "cache_performance" in metrics
        assert "alerts" in metrics

        assert metrics["query_performance"]["total_queries"] >= 0

    def test_optimization_hints_generation(self, optimizer):
        """Test optimization hints generation"""
        # Create metrics for different scenarios
        slow_metrics = QueryMetrics(
            query_id="slow",
            query_text="SELECT * FROM vehicles",
            execution_time_ms=2000.0,  # Slow
            rows_examined=10000,
            rows_returned=10,  # Low selectivity
            index_used=False,
            cache_hit=False
        )

        # Generate hints
        asyncio.run(optimizer._generate_optimization_hints(slow_metrics))

        # Should have generated hints
        assert len(slow_metrics.optimization_hints) > 0

        # Check for expected hints
        hints_text = " ".join(slow_metrics.optimization_hints)
        assert "index" in hints_text.lower() or "filtering" in hints_text.lower()

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, optimizer):
        """Test monitoring start/stop"""
        # Start monitoring
        result = await optimizer.start_monitoring()
        assert result == True
        assert optimizer.is_monitoring == True

        # Wait a bit for monitoring to start
        await asyncio.sleep(0.1)

        # Stop monitoring
        await optimizer.stop_monitoring()
        assert optimizer.is_monitoring == False

    def test_apply_simple_optimizations(self, optimizer):
        """Test simple query optimizations"""
        # Query with extra whitespace
        query = "SELECT   *   FROM   vehicles   WHERE   price  >  30000"
        optimized = optimizer._apply_simple_optimizations(query)

        # Should normalize whitespace
        assert "SELECT * FROM vehicles WHERE price > 30000 LIMIT 1000" == optimized

        # Query without LIMIT
        query_no_limit = "SELECT * FROM vehicles WHERE price > 30000"
        optimized_with_limit = optimizer._apply_simple_optimizations(query_no_limit)

        # Should add LIMIT
        assert optimized_with_limit.endswith(" LIMIT 1000")

    def test_query_uses_index(self, optimizer):
        """Test index usage detection"""
        # Query with WHERE clause
        assert optimizer._query_uses_index("SELECT * FROM vehicles WHERE price > 30000") == True

        # Vector similarity query
        assert optimizer._query_uses_index("SELECT * FROM vehicles ORDER BY embedding <=> query_vec") == True

        # Simple query without conditions
        assert optimizer._query_uses_index("SELECT * FROM vehicles") == False

    @pytest.mark.asyncio
    async def test_optimization_callbacks(self, optimizer):
        """Test custom optimization callbacks"""
        callback_results = []

        async def custom_callback(query_text: str, query_type: str):
            callback_results.append((query_text, query_type))
            return {
                "optimizations": ["Custom optimization applied"]
            }

        # Add callback
        optimizer.add_optimization_callback(custom_callback)

        # Optimize query
        result = await optimizer.optimize_query("SELECT * FROM vehicles")

        # Check callback was called
        assert len(callback_results) == 1
        assert callback_results[0][0] == "SELECT * FROM vehicles"

        # Check custom optimization in result
        custom_opt_found = any("Custom optimization" in opt for opt in result["optimizations"])
        assert custom_opt_found

class TestIntegration:
    """Integration tests for query optimizer"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete query optimization workflow"""
        optimizer = QueryOptimizer()

        # Start monitoring
        await optimizer.start_monitoring()

        # Record various queries
        queries = [
            ("SELECT * FROM vehicles LIMIT 10", 25.0, True, True),
            ("SELECT * FROM vehicles WHERE price < 50000", 150.0, True, False),
            ("SELECT * FROM vehicles WHERE description LIKE '%luxury%'", 2000.0, False, False),
            ("SELECT embedding <=> query_vec FROM vehicles ORDER BY embedding <=> query_vec LIMIT 20", 100.0, True, True)
        ]

        for query_text, exec_time, index_used, cache_hit in queries:
            await optimizer.record_query(
                query_text=query_text,
                execution_time_ms=exec_time,
                index_used=index_used,
                cache_hit=cache_hit,
                query_type="similarity_search" if "<=>" in query_text else "select"
            )

        # Get performance report
        report = await optimizer.get_performance_report()

        # Verify report contents
        assert report["total_queries"] == 4
        assert report["query_analysis"]["slow_queries"] == 1
        assert report["query_analysis"]["similarity_queries"] == 1

        # Get real-time metrics
        metrics = await optimizer.get_real_time_metrics()
        assert metrics["query_performance"]["active_queries"] >= 0

        # Stop monitoring
        await optimizer.stop_monitoring()

if __name__ == "__main__":
    # Run basic tests
    print("Running Query Optimizer tests...")

    # Test metrics creation
    print("\n1. Testing Query Metrics...")
    metrics = QueryMetrics(
        query_id="test123",
        query_text="SELECT * FROM vehicles",
        execution_time_ms=150.5,
        cpu_usage_percent=25.3,
        memory_usage_mb=512.0,
        rows_examined=100,
        rows_returned=20,
        index_used=True,
        cache_hit=False
    )
    assert metrics.query_id == "test123"
    assert metrics.execution_time_ms == 150.5
    print("Query metrics tests passed")

    # Test optimizer
    print("\n2. Testing Query Optimizer...")
    optimizer = QueryOptimizer()
    assert len(optimizer.query_history) == 0
    print("Optimizer initialization tests passed")

    # Test query patterns
    print("\n3. Testing Query Pattern Extraction...")
    pattern1 = optimizer._extract_query_pattern("SELECT * FROM vehicles WHERE price = 30000")
    pattern2 = optimizer._extract_query_pattern("SELECT * FROM vehicles WHERE price = 25000")
    assert pattern1 == pattern2
    print("Query pattern tests passed")

    # Test simple optimizations
    print("\n4. Testing Simple Optimizations...")
    query = "SELECT   *   FROM   vehicles   WHERE   price  >  30000"
    optimized = optimizer._apply_simple_optimizations(query)
    assert "SELECT * FROM vehicles WHERE price > 30000 LIMIT 1000" == optimized
    print("Simple optimization tests passed")

    print("\nAll Query Optimizer tests completed successfully!")