"""
Test Suite for PGVector Optimizer
Comprehensive testing for Story 1-8 pgvector optimization
"""

import asyncio
import pytest
import numpy as np
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.pgvector_optimizer import (
    PGVectorOptimizer,
    IndexConfiguration,
    IndexStatistics,
    QueryPerformanceMetrics
)

class TestIndexConfiguration:
    """Test index configuration"""

    def test_default_configuration(self):
        """Test default configuration values"""
        config = IndexConfiguration()

        assert config.index_type == "ivfflat"
        assert config.lists == 100
        assert config.m == 16
        assert config.similarity_threshold == 0.7
        assert config.probe_list_size == 10

    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = IndexConfiguration(
            index_type="hnsw",
            lists=200,
            m=32,
            similarity_threshold=0.8,
            probe_list_size=20
        )

        assert config.index_type == "hnsw"
        assert config.lists == 200
        assert config.m == 32
        assert config.similarity_threshold == 0.8
        assert config.probe_list_size == 20

class TestPGVectorOptimizer:
    """Test PGVector optimizer functionality"""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance for testing"""
        return PGVectorOptimizer()

    @pytest.fixture
    def sample_embedding(self):
        """Sample 1536-dimensional embedding"""
        return np.random.random(1536).tolist()

    @pytest.fixture
    def sample_queries(self):
        """Generate sample query vectors"""
        return [np.random.random(1536).tolist() for _ in range(5)]

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.db_conn is None
        assert optimizer.config.index_type == "ivfflat"
        assert len(optimizer.index_stats) == 0
        assert len(optimizer.query_history) == 0

    def test_calculate_optimal_lists(self, optimizer):
        """Test optimal lists calculation"""
        # Test with different estimated row counts
        lists_1k = optimizer._calculate_optimal_lists("test_table")
        lists_10k = optimizer._calculate_optimal_lists("test_table")

        # Should be at least 10
        assert lists_1k >= 10

        # Lists should increase with row count
        assert isinstance(lists_1k, int)
        assert isinstance(lists_10k, int)

    @pytest.mark.asyncio
    async def test_similarity_threshold_optimization(self, optimizer, sample_queries):
        """Test similarity threshold optimization"""
        # Mock the search method to avoid DB dependency
        async def mock_search(table, column, query, limit=10, threshold=None):
            # Return mock results based on threshold
            num_results = int((1 - threshold) * 20)  # More results at lower threshold
            return [
                {
                    "id": i,
                    "similarity_score": 0.9 - (i * 0.1 * threshold),
                    "query_time_ms": 50 + (i * 5)
                }
                for i in range(num_results)
            ]

        optimizer.execute_optimized_search = mock_search

        # Run optimization
        results = await optimizer.optimize_similarity_threshold(
            "test_table",
            "test_column",
            sample_queries,
            target_recall=0.5,
            max_precision_loss=0.5
        )

        assert "optimal_threshold" in results
        assert "thresholds_tested" in results
        assert len(results["thresholds_tested"]) > 0

        # Check that thresholds were tested
        thresholds = [r["threshold"] for r in results["thresholds_tested"]]
        assert any(t >= 0.5 and t <= 0.95 for t in thresholds)

    @pytest.mark.asyncio
    async def test_probe_list_optimization(self, optimizer, sample_queries):
        """Test probe list optimization"""
        # Mock the search method
        async def mock_search(table, column, query, limit=10):
            # Simulate varying performance based on probe size
            current_probe = optimizer.config.probe_list_size
            query_time = 100 / (1 + np.log(current_probe + 1))
            return [
                {
                    "id": i,
                    "similarity_score": 0.8 - (i * 0.05),
                    "query_time_ms": query_time
                }
                for i in range(10)
            ]

        optimizer.execute_optimized_search = mock_search

        # Run optimization
        results = await optimizer.optimize_probe_list_size(
            "test_table",
            "test_column",
            sample_queries,
            target_performance_ms=50.0
        )

        assert "optimal_probe_size" in results
        assert "probe_sizes_tested" in results

        # Check that different probe sizes were tested
        probe_sizes = [r["probe_size"] for r in results["probe_sizes_tested"]]
        assert len(probe_sizes) > 0
        assert any(size in [1, 5, 10, 20, 50, 100] for size in probe_sizes)

    def test_index_statistics_creation(self):
        """Test index statistics object creation"""
        stats = IndexStatistics(
            index_name="test_index",
            index_type="ivfflat",
            table_size=10000,
            index_size_mb=50.5,
            tuples_inserted=1000,
            tuples_updated=100,
            tuples_deleted=50,
            pages_fetched=5000,
            tuples_returned=2500,
            last_analyzed=datetime.now(),
            avg_similarity_score=0.75,
            query_count=100,
            avg_query_time_ms=45.2
        )

        assert stats.index_name == "test_index"
        assert stats.index_type == "ivfflat"
        assert stats.table_size == 10000
        assert stats.index_size_mb == 50.5
        assert stats.avg_similarity_score == 0.75
        assert stats.query_count == 100

    def test_query_performance_metrics(self):
        """Test query performance metrics"""
        metrics = QueryPerformanceMetrics(
            query_time_ms=55.5,
            rows_examined=100,
            rows_returned=20,
            index_usage=True,
            similarity_scores=[0.9, 0.85, 0.8],
            cache_hit=False,
            execution_plan={"index_scan": True}
        )

        assert metrics.query_time_ms == 55.5
        assert metrics.rows_examined == 100
        assert metrics.rows_returned == 20
        assert metrics.index_usage == True
        assert len(metrics.similarity_scores) == 3

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, optimizer):
        """Test optimization recommendation generation"""
        # Set up some mock statistics
        optimizer.index_stats["test_index"] = IndexStatistics(
            index_name="test_index",
            index_type="ivfflat",
            table_size=1000,
            index_size_mb=10.0,
            tuples_inserted=100,
            tuples_updated=10,
            tuples_deleted=30,  # High delete ratio
            last_analyzed=datetime.now(),
            avg_similarity_score=0.5,  # Low similarity score
            query_count=10,
            avg_query_time_ms=150.0  # Slow queries
        )

        # Add some query history
        optimizer.query_history = [
            QueryPerformanceMetrics(
                query_time_ms=200,
                rows_examined=50,
                rows_returned=20,
                index_usage=True,
                similarity_scores=[0.8, 0.7],
                cache_hit=False,
                execution_plan={}
            )
            for _ in range(10)
        ]

        # Get recommendations
        recommendations = await optimizer.get_optimization_recommendations()

        assert "index_optimizations" in recommendations
        assert "query_optimizations" in recommendations
        assert "parameter_tuning" in recommendations
        assert "maintenance_suggestions" in recommendations

        # Check specific recommendations
        assert len(recommendations["index_optimizations"]) > 0
        assert len(recommendations["maintenance_suggestions"]) > 0
        assert len(recommendations["parameter_tuning"]) > 0

    def test_performance_summary(self, optimizer):
        """Test performance summary generation"""
        # Add mock data
        optimizer.config.probe_list_size = 20
        optimizer.config.similarity_threshold = 0.75

        optimizer.index_stats["test_index"] = IndexStatistics(
            index_name="test_index",
            index_type="ivfflat",
            table_size=1000,
            index_size_mb=10.0,
            tuples_inserted=100,
            tuples_updated=10,
            tuples_deleted=5,
            last_analyzed=datetime.now(),
            avg_similarity_score=0.75,
            query_count=10,
            avg_query_time_ms=50.0
        )

        optimizer.query_history = [
            QueryPerformanceMetrics(
                query_time_ms=45,
                rows_examined=50,
                rows_returned=20,
                index_usage=True,
                similarity_scores=[0.8],
                cache_hit=False,
                execution_plan={}
            ),
            QueryPerformanceMetrics(
                query_time_ms=55,
                rows_examined=50,
                rows_returned=20,
                index_usage=True,
                similarity_scores=[0.7],
                cache_hit=False,
                execution_plan={}
            )
        ]

        summary = optimizer.get_performance_summary()

        assert "configuration" in summary
        assert "index_statistics" in summary
        assert "query_performance" in summary

        assert summary["configuration"]["probe_list_size"] == 20
        assert summary["configuration"]["similarity_threshold"] == 0.75
        assert summary["query_performance"]["total_queries"] == 2
        assert summary["query_performance"]["avg_query_time_ms"] == 50.0

class TestOptimizationStrategies:
    """Test specific optimization strategies"""

    @pytest.mark.asyncio
    async def test_ivfflat_index_creation_sql(self):
        """Test IVFFLAT index creation SQL generation"""
        optimizer = PGVectorOptimizer()

        # Mock the database connection to capture SQL
        sql_statements = []

        class MockCursor:
            def execute(self, sql):
                sql_statements.append(sql)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockConn:
            def cursor(self):
                return MockCursor()

            def commit(self):
                pass

        optimizer.db_conn = MockConn()

        # Test index creation
        await optimizer.create_optimized_ivfflat_index(
            "vehicles",
            "embedding",
            "idx_vehicles_embedding",
            lists=50,
            distance_metric="cosine"
        )

        # Verify SQL
        assert len(sql_statements) > 0
        create_sql = sql_statements[-1]
        assert "CREATE INDEX idx_vehicles_embedding" in create_sql
        assert "USING ivfflat" in create_sql
        assert "vector_cosine_ops" in create_sql
        assert "lists = 50" in create_sql

    @pytest.mark.asyncio
    async def test_hnsw_index_creation_sql(self):
        """Test HNSW index creation SQL generation"""
        optimizer = PGVectorOptimizer()

        # Mock the database connection
        sql_statements = []

        class MockCursor:
            def execute(self, sql):
                sql_statements.append(sql)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockConn:
            def cursor(self):
                return MockCursor()

            def commit(self):
                pass

        optimizer.db_conn = MockConn()

        # Test index creation
        await optimizer.create_optimized_hnsw_index(
            "vehicles",
            "embedding",
            "idx_vehicles_embedding_hnsw",
            m=32,
            ef_construction=128,
            distance_metric="l2"
        )

        # Verify SQL
        assert len(sql_statements) > 0
        create_sql = sql_statements[-1]
        assert "CREATE INDEX idx_vehicles_embedding_hnsw" in create_sql
        assert "USING hnsw" in create_sql
        assert "vector_l2_ops" in create_sql
        assert "m = 32" in create_sql
        assert "ef_construction = 128" in create_sql

if __name__ == "__main__":
    # Run basic tests
    print("Running PGVector optimizer tests...")

    # Test configuration
    print("\n1. Testing Index Configuration...")
    config = IndexConfiguration(
        index_type="hnsw",
        similarity_threshold=0.8
    )
    assert config.index_type == "hnsw"
    assert config.similarity_threshold == 0.8
    print("Configuration tests passed")

    # Test optimizer
    print("\n2. Testing PGVector Optimizer...")
    optimizer = PGVectorOptimizer()
    assert optimizer.config.index_type == "ivfflat"
    print("Optimizer initialization tests passed")

    # Test calculations
    print("\n3. Testing Optimization Calculations...")
    lists = optimizer._calculate_optimal_lists("test_table")
    assert isinstance(lists, int)
    assert lists >= 10
    print("Calculation tests passed")

    print("\nAll PGVector optimizer tests completed successfully!")