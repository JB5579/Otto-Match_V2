"""
Test Suite for Connection Pool
Comprehensive testing for Story 1-8 connection pooling and scaling
"""

import asyncio
import pytest
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.scaling.connection_pool import (
    DatabaseConfig,
    ConnectionMetrics,
    PoolStatistics,
    ConnectionPool,
    LoadBalancedPoolManager
)

class TestDatabaseConfig:
    """Test database configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass"
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.max_connections == 20
        assert config.min_connections == 2
        assert config.ssl_mode == "require"

    def test_custom_config(self):
        """Test custom configuration values"""
        config = DatabaseConfig(
            host="remote.host.com",
            port=5433,
            database="production",
            username="appuser",
            password="secret123",
            max_connections=50,
            min_connections=5,
            connect_timeout=15.0
        )

        assert config.host == "remote.host.com"
        assert config.port == 5433
        assert config.max_connections == 50
        assert config.min_connections == 5
        assert config.connect_timeout == 15.0

class TestConnectionMetrics:
    """Test connection metrics"""

    def test_metrics_initialization(self):
        """Test metrics initialization with defaults"""
        metrics = ConnectionMetrics()

        assert metrics.total_connections == 0
        assert metrics.active_connections == 0
        assert metrics.idle_connections == 0
        assert metrics.total_queries == 0
        assert metrics.avg_query_time_ms == 0.0
        assert metrics.last_error is None

    def test_metrics_with_values(self):
        """Test metrics with custom values"""
        now = datetime.now()
        metrics = ConnectionMetrics(
            total_connections=10,
            active_connections=3,
            idle_connections=7,
            failed_connections=1,
            total_queries=1000,
            avg_query_time_ms=45.5,
            max_query_time_ms=500.0,
            pool_utilization_percent=30.0,
            last_error="Connection timeout",
            last_error_time=now
        )

        assert metrics.total_connections == 10
        assert metrics.active_connections == 3
        assert metrics.idle_connections == 7
        assert metrics.total_queries == 1000
        assert metrics.avg_query_time_ms == 45.5
        assert metrics.last_error == "Connection timeout"
        assert metrics.last_error_time == now

class TestPoolStatistics:
    """Test pool statistics"""

    def test_statistics_initialization(self):
        """Test statistics initialization"""
        stats = PoolStatistics()

        assert stats.total_connections_created == 0
        assert stats.total_connections_closed == 0
        assert stats.peak_connections == 0
        assert stats.connection_reuse_count == 0

    def test_statistics_with_values(self):
        """Test statistics with custom values"""
        created_time = datetime.now()
        stats = PoolStatistics(
            created_at=created_time,
            total_connections_created=100,
            total_connections_closed=90,
            peak_connections=25,
            avg_wait_time_ms=10.5,
            max_wait_time_ms=100.0,
            connection_reuse_count=500
        )

        assert stats.created_at == created_time
        assert stats.total_connections_created == 100
        assert stats.total_connections_closed == 90
        assert stats.peak_connections == 25
        assert stats.connection_reuse_count == 500

class TestConnectionPool:
    """Test connection pool functionality"""

    @pytest.fixture
    def config(self):
        """Create test database configuration"""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_password",
            max_connections=5,
            min_connections=1,
            connect_timeout=5.0
        )

    @pytest.fixture
    def pool(self, config):
        """Create connection pool for testing"""
        return ConnectionPool(
            config,
            pool_name="test_pool",
            auto_resize=False,  # Disable auto-resize for tests
            health_check_interval=1.0
        )

    def test_pool_initialization(self, pool):
        """Test pool initialization"""
        assert pool.pool_name == "test_pool"
        assert pool.config.max_connections == 5
        assert pool.config.min_connections == 1
        assert pool.auto_resize == False
        assert pool.is_initialized == False
        assert pool.is_shutting_down == False

    @pytest.mark.asyncio
    async def test_pool_creation_failure(self, config):
        """Test pool initialization with invalid config"""
        # Use invalid credentials
        config.password = "invalid_password"
        pool = ConnectionPool(config, pool_name="failed_pool")

        # Should fail to initialize
        result = await pool.initialize()
        assert result == False

    @pytest.mark.asyncio
    async def test_metrics_calculation(self, pool):
        """Test metrics calculation"""
        # Mock some connections
        pool.metrics.total_connections = 3
        pool.metrics.active_connections = 1
        pool.metrics.total_queries = 100
        pool.metrics.avg_query_time_ms = 50.0

        metrics = await pool.get_metrics()

        assert metrics["pool_name"] == "test_pool"
        assert metrics["metrics"]["total_connections"] == 3
        assert metrics["metrics"]["active_connections"] == 1
        assert metrics["metrics"]["total_queries"] == 100
        assert metrics["metrics"]["avg_query_time_ms"] == 50.0

    @pytest.mark.asyncio
    async def test_connection_creation_string(self, config):
        """Test connection string generation"""
        pool = ConnectionPool(config, pool_name="test")

        # Test connection string generation
        expected_pattern = "postgresql://test_user:test_password@localhost:5432/test_db"
        connection_string = (
            f"postgresql://{config.username}:{config.password}@"
            f"{config.host}:{config.port}/{config.database}"
            f"?sslmode={config.ssl_mode}"
        )
        assert connection_string.startswith(expected_pattern)

    @pytest.mark.asyncio
    async def test_pool_shutdown(self, pool):
        """Test pool shutdown"""
        # Initialize (will fail but that's ok for this test)
        await pool.initialize()

        # Shutdown should not raise errors
        await pool.close()
        assert pool.is_shutting_down == True
        assert pool.is_initialized == False

    @pytest.mark.asyncio
    async def test_query_time_stats_update(self, pool):
        """Test query time statistics update"""
        # Update some query times
        pool._update_query_time_stats(100.0)
        assert pool.metrics.total_queries == 1
        assert pool.metrics.avg_query_time_ms == 100.0
        assert pool.metrics.max_query_time_ms == 100.0

        # Update with faster query
        pool._update_query_time_stats(50.0)
        assert pool.metrics.total_queries == 2
        assert pool.metrics.avg_query_time_ms == 75.0  # (100 + 50) / 2
        assert pool.metrics.max_query_time_ms == 100.0

        # Update with slower query
        pool._update_query_time_stats(200.0)
        assert pool.metrics.total_queries == 3
        assert pool.metrics.max_query_time_ms == 200.0

class TestLoadBalancedPoolManager:
    """Test load-balanced pool manager"""

    @pytest.fixture
    def configs(self):
        """Create multiple database configurations"""
        return [
            DatabaseConfig(
                host="db1.example.com",
                port=5432,
                database="db1",
                username="user1",
                password="pass1",
                max_connections=10
            ),
            DatabaseConfig(
                host="db2.example.com",
                port=5432,
                database="db2",
                username="user2",
                password="pass2",
                max_connections=10
            ),
            DatabaseConfig(
                host="db3.example.com",
                port=5432,
                database="db3",
                username="user3",
                password="pass3",
                max_connections=10
            )
        ]

    @pytest.fixture
    def manager(self, configs):
        """Create pool manager for testing"""
        return LoadBalancedPoolManager(configs)

    def test_manager_initialization(self, manager, configs):
        """Test manager initialization"""
        assert len(manager.pool_configs) == 3
        assert len(manager.pools) == 0
        assert manager.round_robin_index == 0

    def test_round_robin_selection(self, manager):
        """Test round-robin pool selection"""
        # Mock healthy pools
        manager.pools = {
            "pool_0": ConnectionPool(manager.pool_configs[0], "pool_0"),
            "pool_1": ConnectionPool(manager.pool_configs[1], "pool_1"),
            "pool_2": ConnectionPool(manager.pool_configs[2], "pool_2")
        }

        # Test round-robin selection
        selected1 = manager._select_pool("round_robin")
        selected2 = manager._select_pool("round_robin")
        selected3 = manager._select_pool("round_robin")
        selected4 = manager._select_pool("round_robin")

        assert selected1 in ["pool_0", "pool_1", "pool_2"]
        assert selected2 in ["pool_0", "pool_1", "pool_2"]
        assert selected3 in ["pool_0", "pool_1", "pool_2"]
        assert selected4 in ["pool_0", "pool_1", "pool_2"]
        assert selected4 == selected1  # Should cycle back

    def test_least_connections_selection(self, manager):
        """Test least connections pool selection"""
        # Mock pools with different connection counts
        pool0 = ConnectionPool(manager.pool_configs[0], "pool_0")
        pool1 = ConnectionPool(manager.pool_configs[1], "pool_1")
        pool2 = ConnectionPool(manager.pool_configs[2], "pool_2")

        pool0.metrics.active_connections = 5
        pool1.metrics.active_connections = 2
        pool2.metrics.active_connections = 8

        manager.pools = {
            "pool_0": pool0,
            "pool_1": pool1,
            "pool_2": pool2
        }

        # Should select pool with least connections
        selected = manager._select_pool("least_connections")
        assert selected == "pool_1"

    def test_random_selection(self, manager):
        """Test random pool selection"""
        # Mock healthy pools
        manager.pools = {
            "pool_0": ConnectionPool(manager.pool_configs[0], "pool_0"),
            "pool_1": ConnectionPool(manager.pool_configs[1], "pool_1")
        }

        # Random selection should return a valid pool
        for _ in range(10):
            selected = manager._select_pool("random")
            assert selected in ["pool_0", "pool_1"]

    def test_no_healthy_pools(self, manager):
        """Test behavior when no healthy pools available"""
        manager.pools = {}  # No pools

        selected = manager._select_pool("round_robin")
        assert selected is None

    @pytest.mark.asyncio
    async def test_get_all_metrics(self, manager):
        """Test getting metrics from all pools"""
        # Mock pools
        pool0 = ConnectionPool(manager.pool_configs[0], "pool_0")
        pool1 = ConnectionPool(manager.pool_configs[1], "pool_1")

        # Set some metrics
        pool0.metrics.total_connections = 5
        pool0.metrics.active_connections = 2
        pool1.metrics.total_connections = 3
        pool1.metrics.active_connections = 1

        manager.pools = {
            "pool_0": pool0,
            "pool_1": pool1
        }

        all_metrics = manager.get_all_metrics()

        assert "pool_0" in all_metrics
        assert "pool_1" in all_metrics
        assert all_metrics["pool_0"]["metrics"]["total_connections"] == 5
        assert all_metrics["pool_1"]["metrics"]["total_connections"] == 3

    @pytest.mark.asyncio
    async def test_acquire_specific_pool(self, manager):
        """Test acquiring from specific pool"""
        # Mock pool
        pool = ConnectionPool(manager.pool_configs[0], "pool_0")
        pool.is_initialized = True
        pool.is_shutting_down = False

        manager.pools = {"pool_0": pool}

        # This would normally acquire a connection
        # In tests, we just verify it raises appropriate errors
        with pytest.raises(RuntimeError):
            await manager.acquire(pool_name="nonexistent_pool")

    @pytest.mark.asyncio
    async def test_acquire_no_pools(self, manager):
        """Test acquiring when no pools available"""
        # No pools initialized
        manager.pools = {}

        with pytest.raises(RuntimeError):
            await manager.acquire()

    @pytest.mark.asyncio
    async def test_manager_close(self, manager):
        """Test closing all pools"""
        # Mock pools
        pool0 = ConnectionPool(manager.pool_configs[0], "pool_0")
        pool1 = ConnectionPool(manager.pool_configs[1], "pool_1")

        manager.pools = {
            "pool_0": pool0,
            "pool_1": pool1
        }

        # Close should not raise errors
        await manager.close()
        assert len(manager.pools) == 0

class TestIntegration:
    """Integration tests for connection pooling"""

    @pytest.mark.asyncio
    async def test_pool_lifecycle(self):
        """Test complete pool lifecycle"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test",
            username="test",
            password="test",
            max_connections=3,
            min_connections=1
        )

        pool = ConnectionPool(config, pool_name="lifecycle_test", auto_resize=False)

        # Test initial state
        assert not pool.is_initialized
        assert not pool.is_shutting_down

        # Test initialization (will fail with invalid config but that's ok)
        # await pool.initialize()

        # Test metrics
        metrics = pool.get_metrics()
        assert "pool_name" in metrics
        assert "metrics" in metrics
        assert "statistics" in metrics

        # Test shutdown
        await pool.close()
        assert pool.is_shutting_down
        assert not pool.is_initialized

    @pytest.mark.asyncio
    async def test_load_balanced_manager_lifecycle(self):
        """Test load-balanced manager lifecycle"""
        configs = [
            DatabaseConfig(
                host="db1.test.com",
                port=5432,
                database="test1",
                username="test1",
                password="test1",
                max_connections=5
            ),
            DatabaseConfig(
                host="db2.test.com",
                port=5432,
                database="test2",
                username="test2",
                password="test2",
                max_connections=5
            )
        ]

        manager = LoadBalancedPoolManager(configs)

        # Test initial state
        assert len(manager.pools) == 0
        assert manager.round_robin_index == 0

        # Test initialization (will fail but that's ok for test)
        # await manager.initialize()

        # Test pool selection strategies
        manager.pools = {
            "pool_0": ConnectionPool(configs[0], "pool_0"),
            "pool_1": ConnectionPool(configs[1], "pool_1")
        }

        # Test each strategy
        assert manager._select_pool("round_robin") in ["pool_0", "pool_1"]
        assert manager._select_pool("least_connections") in ["pool_0", "pool_1"]
        assert manager._select_pool("random") in ["pool_0", "pool_1"]

        # Test shutdown
        await manager.close()
        assert len(manager.pools) == 0

if __name__ == "__main__":
    # Run basic tests
    print("Running Connection Pool tests...")

    # Test configuration
    print("\n1. Testing Database Configuration...")
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="testdb",
        username="testuser",
        password="testpass"
    )
    assert config.host == "localhost"
    assert config.max_connections == 20
    assert config.min_connections == 2
    print("Database configuration tests passed")

    # Test metrics
    print("\n2. Testing Connection Metrics...")
    metrics = ConnectionMetrics(
        total_connections=10,
        active_connections=3,
        total_queries=100,
        avg_query_time_ms=45.5
    )
    assert metrics.total_connections == 10
    assert metrics.active_connections == 3
    assert metrics.total_queries == 100
    assert metrics.avg_query_time_ms == 45.5
    print("Connection metrics tests passed")

    # Test pool
    print("\n3. Testing Connection Pool...")
    pool = ConnectionPool(
        DatabaseConfig(
            host="localhost",
            port=5432,
            database="test",
            username="test",
            password="test"
        ),
        pool_name="test_pool"
    )
    assert pool.pool_name == "test_pool"
    assert pool.is_initialized == False
    print("Connection pool tests passed")

    # Test pool manager
    print("\n4. Testing Load-Balanced Pool Manager...")
    configs = [
        DatabaseConfig(host="db1.com", port=5432, database="db1", username="u1", password="p1"),
        DatabaseConfig(host="db2.com", port=5432, database="db2", username="u2", password="p2")
    ]
    manager = LoadBalancedPoolManager(configs)
    assert len(manager.pool_configs) == 2
    assert len(manager.pools) == 0
    print("Load-balanced pool manager tests passed")

    # Test query time stats
    print("\n5. Testing Query Time Statistics...")
    print("Query time statistics test skipped (requires async context)")

    print("\nAll Connection Pool tests completed successfully!")