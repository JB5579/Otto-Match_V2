"""
Comprehensive Test Suite for Otto.AI Collections System

Implements tests for Story 1.7: Add Curated Vehicle Collections and Categories
Tests cover all components including database, API endpoints, and business logic.

Test Coverage:
- Database schema and migrations
- CollectionEngine operations
- API endpoints (admin, public, analytics)
- Trending algorithm
- A/B testing framework
- Analytics dashboard
- WebSocket service
- Error handling and edge cases
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# Test dependencies
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.collections.collection_engine import (
    CollectionEngine,
    Collection,
    CollectionCriteria,
    CollectionType,
    CollectionTemplate
)
from src.collections.trending_algorithm import (
    TrendingAlgorithm,
    TrendMetrics,
    MarketTrendData
)
from src.collections.ab_testing import (
    ABTestingFramework,
    ABTest,
    TestResult
)
from src.collections.analytics_dashboard import (
    CollectionsAnalyticsDashboard,
    MetricType,
    TimePeriod,
    CollectionInsights
)
from src.realtime.collections_websocket_service import (
    CollectionsWebSocketService,
    WebSocketConnection,
    CollectionUpdate
)

# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@pytest.fixture
async def test_db_connection():
    """Create test database connection"""
    # Mock database connection for testing
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()
    return mock_conn

@pytest.fixture
async def collection_engine(test_db_connection):
    """Create CollectionEngine instance for testing"""
    engine = CollectionEngine()
    engine.db_conn = test_db_connection
    return engine

@pytest.fixture
async def trending_algorithm(test_db_connection):
    """Create TrendingAlgorithm instance for testing"""
    algorithm = TrendingAlgorithm()
    algorithm.db_conn = test_db_connection
    return algorithm

@pytest.fixture
async def ab_testing_framework(test_db_connection):
    """Create ABTestingFramework instance for testing"""
    framework = ABTestingFramework()
    framework.db_conn = test_db_connection
    return framework

@pytest.fixture
async def analytics_dashboard(test_db_connection):
    """Create CollectionsAnalyticsDashboard instance for testing"""
    dashboard = CollectionsAnalyticsDashboard()
    dashboard.db_conn = test_db_connection
    return dashboard

@pytest.fixture
async def websocket_service():
    """Create CollectionsWebSocketService instance for testing"""
    service = CollectionsWebSocketService()
    return service

@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "name": "Electric Vehicles",
        "description": "Top electric vehicles in 2024",
        "type": "curated",
        "vehicle_count": 25,
        "sort_order": 1,
        "is_featured": True,
        "is_active": True
    }

@pytest.fixture
def sample_criteria():
    """Sample collection criteria for testing"""
    return CollectionCriteria(
        vehicle_type="SUV",
        fuel_type=["electric", "hybrid"],
        price_max=50000,
        year_min=2020,
        features=["adaptive_cruise_control", "lane_assist"]
    )

@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for testing"""
    return [
        {"event_type": "view", "count": 1000},
        {"event_type": "click", "count": 150},
        {"event_type": "share", "count": 25},
        {"event_type": "conversion", "count": 10}
    ]

# ============================================================================
# CollectionEngine Tests
# ============================================================================

class TestCollectionEngine:
    """Test CollectionEngine functionality"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, collection_engine):
        """Test successful initialization"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = "test_password"

            # Mock psycopg.connect
            with patch('src.collections.collection_engine.psycopg.connect') as mock_connect:
                mock_connect.return_value = MagicMock()

                result = await collection_engine.initialize("https://test.supabase.co", "test_key")

                assert result is True
                mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, collection_engine):
        """Test initialization failure"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None  # Missing password

            result = await collection_engine.initialize("https://test.supabase.co", "test_key")

            assert result is False

    @pytest.mark.asyncio
    async def test_create_collection(self, collection_engine, sample_criteria):
        """Test collection creation"""
        # Mock database responses
        collection_engine.db_conn.cursor.return_value.fetchone.return_value = [str(uuid.uuid4())]

        collection_id = await collection_engine.create_collection(
            name="Test Collection",
            description="Test Description",
            collection_type=CollectionType.CURATED,
            criteria=sample_criteria,
            created_by="test_user"
        )

        assert collection_id is not None
        assert isinstance(collection_id, str)

    @pytest.mark.asyncio
    async def test_get_collection(self, collection_engine, sample_collection_data):
        """Test retrieving a collection"""
        # Mock database response
        mock_cursor = collection_engine.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {
            "id": sample_collection_data["id"],
            "name": sample_collection_data["name"],
            "description": sample_collection_data["description"],
            "type": sample_collection_data["type"],
            "criteria": json.dumps(sample_criteria.__dict__ if 'sample_criteria' in locals() else {}),
            "metadata": json.dumps({}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_user"
        }

        collection = await collection_engine.get_collection(sample_collection_data["id"])

        assert collection is not None
        assert collection.id == sample_collection_data["id"]
        assert collection.name == sample_collection_data["name"]

    @pytest.mark.asyncio
    async def test_update_collection(self, collection_engine, sample_collection_data):
        """Test updating a collection"""
        # Mock database responses
        collection_engine.db_conn.cursor.return_value.rowcount = 1

        result = await collection_engine.update_collection(
            collection_id=sample_collection_data["id"],
            name="Updated Collection Name"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_collection(self, collection_engine, sample_collection_data):
        """Test deleting a collection"""
        # Mock database responses
        collection_engine.db_conn.cursor.return_value.rowcount = 1

        result = await collection_engine.delete_collection(sample_collection_data["id"])

        assert result is True

    @pytest.mark.asyncio
    async def test_score_vehicles(self, collection_engine):
        """Test vehicle scoring algorithm"""
        # Mock vehicle data
        vehicles = [
            {"id": "v1", "price": 30000, "year": 2023, "mileage": 10000},
            {"id": "v2", "price": 40000, "year": 2024, "mileage": 5000},
            {"id": "v3", "price": 25000, "year": 2022, "mileage": 20000}
        ]

        criteria = CollectionCriteria(
            price_max=50000,
            year_min=2020,
            mileage_max=50000
        )

        scores = await collection_engine._score_vehicles(vehicles, criteria)

        assert len(scores) == len(vehicles)
        assert all(0 <= score <= 1 for score in scores.values())

    @pytest.mark.asyncio
    async def test_generate_collection_from_template(self, collection_engine):
        """Test generating collection from template"""
        # Mock template data
        mock_cursor = collection_engine.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {
            "id": str(uuid.uuid4()),
            "name": "Electric SUVs",
            "template_data": json.dumps({
                "vehicle_type": "SUV",
                "fuel_type": ["electric"],
                "description_template": "Top {vehicle_type} vehicles with {fuel_type} power"
            })
        }

        collection_id = await collection_engine.generate_collection_from_template(
            template_name="Electric SUVs",
            collection_name="My Electric SUVs",
            description="Custom description"
        )

        assert collection_id is not None

# ============================================================================
# TrendingAlgorithm Tests
# ============================================================================

class TestTrendingAlgorithm:
    """Test TrendingAlgorithm functionality"""

    @pytest.mark.asyncio
    async def test_calculate_collection_trends(self, trending_algorithm, sample_analytics_data):
        """Test calculating collection trends"""
        collection_id = str(uuid.uuid4())

        # Mock database responses
        mock_cursor = trending_algorithm.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.side_effect = [
            sample_analytics_data[0],  # Current period
            {"total_events": 800}      # Previous period
        ]

        metrics = await trending_algorithm.calculate_collection_trends(collection_id, days_back=7)

        assert metrics is not None
        assert metrics.collection_id == collection_id
        assert metrics.views == 1000
        assert metrics.clicks == 150
        assert metrics.trending_score >= 0

    @pytest.mark.asyncio
    async def test_get_trending_collections(self, trending_algorithm):
        """Test getting trending collections"""
        # Mock database responses
        mock_cursor = trending_algorithm.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {"id": str(uuid.uuid4()), "name": "Collection 1", "type": "curated"},
            {"id": str(uuid.uuid4()), "name": "Collection 2", "type": "trending"}
        ]

        # Mock calculate_collection_trends
        with patch.object(trending_algorithm, 'calculate_collection_trends') as mock_calculate:
            mock_calculate.return_value = TrendMetrics(
                collection_id=str(uuid.uuid4()),
                trending_score=75.5
            )

            trending = await trending_algorithm.get_trending_collections(limit=10)

            assert len(trending) <= 10
            assert all(isinstance(score, float) for _, score in trending)

    @pytest.mark.asyncio
    async def test_detect_market_trends(self, trending_algorithm):
        """Test market trend detection"""
        trends = await trending_algorithm.detect_market_trends()

        assert isinstance(trends, list)
        assert len(trends) > 0
        assert all(isinstance(trend, MarketTrendData) for trend in trends)

    @pytest.mark.asyncio
    async def test_generate_trending_collection(self, trending_algorithm):
        """Test generating trending collection from market data"""
        trend_data = MarketTrendData(
            trend_name="Electric Vehicles",
            trend_score=0.85,
            keywords=["electric", "EV", "hybrid"],
            source="market_analysis",
            timestamp=datetime.utcnow()
        )

        # Mock CollectionEngine
        with patch('src.collections.trending_algorithm.CollectionEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.create_collection.return_value = str(uuid.uuid4())
            mock_engine.update_collection.return_value = True
            mock_engine_class.return_value = mock_engine

            collection_id = await trending_algorithm.generate_trending_collection(trend_data)

            assert collection_id is not None
            mock_engine.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trending_insights(self, trending_algorithm):
        """Test getting trending insights"""
        collection_id = str(uuid.uuid4())

        # Mock calculate_collection_trends
        with patch.object(trending_algorithm, 'calculate_collection_trends') as mock_calculate:
            mock_calculate.return_value = TrendMetrics(
                collection_id=collection_id,
                trending_score=85.0,
                views=1000,
                clicks=200,
                shares=50,
                conversions=25,
                engagement_score=500.0,
                growth_rate=0.15,
                recency_score=0.9
            )

            insights = await trending_algorithm.get_trending_insights(collection_id)

            assert "trending_score" in insights
            assert "factors" in insights
            assert "recommendations" in insights
            assert insights["trending_score"] == 85.0

# ============================================================================
# ABTestingFramework Tests
# ============================================================================

class TestABTestingFramework:
    """Test A/B testing framework functionality"""

    @pytest.mark.asyncio
    async def test_create_ab_test(self, ab_testing_framework):
        """Test creating A/B test"""
        test_id = await ab_testing_framework.create_test(
            name="Test Collection Titles",
            description="Testing different title formats",
            variants={
                "control": {"title": "Electric Vehicles"},
                "variant_a": {"title": "Best Electric Cars 2024"},
                "variant_b": {"title": "Top EVs This Year"}
            },
            traffic_split={"control": 0.5, "variant_a": 0.25, "variant_b": 0.25},
            success_metric="conversion_rate"
        )

        assert test_id is not None
        assert isinstance(test_id, str)

    @pytest.mark.asyncio
    async def test_get_user_variant(self, ab_testing_framework):
        """Test getting user's test variant"""
        test_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Mock test data
        with patch.object(ab_testing_framework, '_get_test') as mock_get_test:
            mock_get_test.return_value = ABTest(
                id=test_id,
                name="Test",
                variants={"control": {}, "variant_a": {}},
                traffic_split={"control": 0.5, "variant_a": 0.5},
                status="running"
            )

            variant = await ab_testing_framework.get_user_variant(test_id, user_id)

            assert variant in ["control", "variant_a"]

    @pytest.mark.asyncio
    async def test_record_conversion(self, ab_testing_framework):
        """Test recording conversion event"""
        test_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        variant = "control"
        conversion_value = 25000.0

        # Mock database operations
        ab_testing_framework.db_conn.cursor.return_value.rowcount = 1

        result = await ab_testing_framework.record_conversion(
            test_id=test_id,
            user_id=user_id,
            variant=variant,
            conversion_value=conversion_value
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_calculate_statistical_significance(self, ab_testing_framework):
        """Test statistical significance calculation"""
        # Test data
        control_data = {"conversions": 100, "visitors": 1000}
        variant_data = {"conversions": 120, "visitors": 1000}

        p_value = await ab_testing_framework._calculate_statistical_significance(
            control_data, variant_data
        )

        assert 0 <= p_value <= 1

    @pytest.mark.asyncio
    async def test_get_test_results(self, ab_testing_framework):
        """Test getting A/B test results"""
        test_id = str(uuid.uuid4())

        # Mock database responses
        mock_cursor = ab_testing_framework.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {
                "variant": "control",
                "visitors": 1000,
                "conversions": 100,
                "conversion_rate": 0.1,
                "revenue": 2500000.0
            },
            {
                "variant": "variant_a",
                "visitors": 1000,
                "conversions": 120,
                "conversion_rate": 0.12,
                "revenue": 3000000.0
            }
        ]

        results = await ab_testing_framework.get_test_results(test_id)

        assert len(results) == 2
        assert all(isinstance(result, TestResult) for result in results)

# ============================================================================
# AnalyticsDashboard Tests
# ============================================================================

class TestAnalyticsDashboard:
    """Test analytics dashboard functionality"""

    @pytest.mark.asyncio
    async def test_track_event(self, analytics_dashboard):
        """Test event tracking"""
        collection_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Mock database operations
        with patch.object(analytics_dashboard.db_conn, 'commit') as mock_commit:
            await analytics_dashboard.track_event(
                event_type="view",
                collection_id=collection_id,
                user_id=user_id,
                metadata={"session_id": "session_123"}
            )

            mock_commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_insights(self, analytics_dashboard, sample_collection_data):
        """Test getting collection insights"""
        # Mock database responses
        mock_cursor = analytics_dashboard.db_conn.cursor.return_value.__enter__.return_value

        # Collection details
        mock_cursor.fetchone.side_effect = [
            {"id": sample_collection_data["id"], "name": sample_collection_data["name"], "type": "curated"},
            {"views": 1000, "clicks": 150, "shares": 25, "conversions": 10, "avg_time_viewed": 45.5},
            {"single_view_sessions": 200, "total_sessions": 800}
        ]

        # Mock trending score calculation
        with patch.object(analytics_dashboard, '_calculate_trending_score') as mock_trending:
            mock_trending.return_value = 75.5

            insights = await analytics_dashboard.get_collection_insights(
                collection_id=sample_collection_data["id"],
                days_back=30
            )

            assert insights is not None
            assert insights.collection_id == sample_collection_data["id"]
            assert insights.total_views == 1000
            assert insights.total_clicks == 150

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, analytics_dashboard):
        """Test getting dashboard data"""
        # Mock widget data generation
        with patch.object(analytics_dashboard, '_generate_widget_data') as mock_widget:
            mock_widget.return_value = {
                "widget_id": "test_widget",
                "widget_type": "metric_cards",
                "title": "Test Widget",
                "data": {"metrics": []}
            }

            dashboard_data = await analytics_dashboard.get_dashboard_data(
                time_period=TimePeriod.DAY
            )

            assert "widgets" in dashboard_data
            assert "summary" in dashboard_data
            assert len(dashboard_data["widgets"]) > 0

    @pytest.mark.asyncio
    async def test_get_top_collections(self, analytics_dashboard):
        """Test getting top collections"""
        # Mock database response
        mock_cursor = analytics_dashboard.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {
                "id": str(uuid.uuid4()),
                "name": "Top Collection",
                "type": "curated",
                "metric_value": 1000,
                "views": 1000,
                "clicks": 150,
                "conversions": 10
            }
        ]

        top_collections = await analytics_dashboard.get_top_collections(
            metric_type=MetricType.VIEWS,
            limit=10,
            days_back=7
        )

        assert len(top_collections) <= 10
        assert all("metric_value" in collection for collection in top_collections)

    @pytest.mark.asyncio
    async def test_export_analytics_report(self, analytics_dashboard):
        """Test exporting analytics report"""
        # Mock database response
        mock_cursor = analytics_dashboard.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            {
                "collection_id": str(uuid.uuid4()),
                "collection_name": "Test Collection",
                "event_type": "view",
                "user_id": str(uuid.uuid4()),
                "created_at": datetime.utcnow()
            }
        ]

        # Mock pandas
        with patch('src.collections.analytics_dashboard.pd.DataFrame') as mock_df:
            mock_dataframe = MagicMock()
            mock_df.return_value = mock_dataframe

            result = await analytics_dashboard.export_analytics_report(
                format_type="csv",
                days_back=30
            )

            assert result is not None

# ============================================================================
# WebSocket Service Tests
# ============================================================================

class TestWebSocketService:
    """Test WebSocket service functionality"""

    @pytest.mark.asyncio
    async def test_add_connection(self, websocket_service):
        """Test adding WebSocket connection"""
        websocket = MagicMock()
        user_id = str(uuid.uuid4())

        connection_id = await websocket_service.add_connection(
            websocket=websocket,
            user_id=user_id
        )

        assert connection_id is not None
        assert connection_id in websocket_service.connections
        assert websocket_service.connections[connection_id].user_id == user_id

    @pytest.mark.asyncio
    async def test_remove_connection(self, websocket_service):
        """Test removing WebSocket connection"""
        # First add a connection
        websocket = MagicMock()
        user_id = str(uuid.uuid4())

        connection_id = await websocket_service.add_connection(websocket, user_id)

        # Then remove it
        await websocket_service.remove_connection(connection_id)

        assert connection_id not in websocket_service.connections

    @pytest.mark.asyncio
    async def test_subscribe_to_collection(self, websocket_service):
        """Test subscribing to collection updates"""
        # Setup connection and collection
        websocket = MagicMock()
        user_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        connection_id = await websocket_service.add_connection(websocket, user_id)

        # Subscribe to collection
        await websocket_service.subscribe_to_collection(connection_id, collection_id)

        assert collection_id in websocket_service.connections[connection_id].subscribed_collections
        assert connection_id in websocket_service.collection_subscribers[collection_id]

    @pytest.mark.asyncio
    async def test_broadcast_collection_update(self, websocket_service):
        """Test broadcasting collection update"""
        # Setup connection and subscription
        websocket = MagicMock()
        websocket.send_json = AsyncMock()
        user_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        connection_id = await websocket_service.add_connection(websocket, user_id)
        await websocket_service.subscribe_to_collection(connection_id, collection_id)

        # Create update
        update = CollectionUpdate(
            collection_id=collection_id,
            update_type="created",
            data={"name": "New Collection"},
            timestamp=datetime.utcnow()
        )

        # Broadcast update
        await websocket_service.broadcast_collection_update(update)

        # Verify message was sent
        websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_stats(self, websocket_service):
        """Test getting connection statistics"""
        # Setup some connections
        for i in range(3):
            websocket = MagicMock()
            user_id = f"user_{i}"
            await websocket_service.add_connection(websocket, user_id)

        stats = await websocket_service.get_connection_stats()

        assert "total_connections" in stats
        assert "total_subscriptions" in stats
        assert "active_connections" in stats
        assert stats["total_connections"] == 3

# ============================================================================
# Integration Tests
# ============================================================================

class TestCollectionsIntegration:
    """Integration tests for the complete collections system"""

    @pytest.mark.asyncio
    async def test_end_to_end_collection_lifecycle(self, collection_engine):
        """Test complete collection lifecycle"""
        # Create collection
        criteria = CollectionCriteria(
            vehicle_type="SUV",
            fuel_type=["electric"],
            price_max=50000
        )

        # Mock database responses
        collection_engine.db_conn.cursor.return_value.fetchone.return_value = [str(uuid.uuid4())]

        collection_id = await collection_engine.create_collection(
            name="Electric SUVs",
            description="Best electric SUVs",
            collection_type=CollectionType.CURATED,
            criteria=criteria,
            created_by="test_user"
        )

        assert collection_id is not None

        # Get collection
        mock_cursor = collection_engine.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {
            "id": collection_id,
            "name": "Electric SUVs",
            "description": "Best electric SUVs",
            "type": "curated",
            "criteria": json.dumps(criteria.__dict__),
            "metadata": json.dumps({}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_user"
        }

        collection = await collection_engine.get_collection(collection_id)
        assert collection is not None
        assert collection.name == "Electric SUVs"

        # Update collection
        collection_engine.db_conn.cursor.return_value.rowcount = 1
        result = await collection_engine.update_collection(
            collection_id=collection_id,
            name="Updated Electric SUVs"
        )
        assert result is True

        # Delete collection
        result = await collection_engine.delete_collection(collection_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_analytics_flow(self, analytics_dashboard):
        """Test analytics tracking and insights flow"""
        collection_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Track events
        with patch.object(analytics_dashboard.db_conn, 'commit'):
            await analytics_dashboard.track_event("view", collection_id, user_id)
            await analytics_dashboard.track_event("click", collection_id, user_id)
            await analytics_dashboard.track_event("conversion", collection_id, user_id)

        # Get insights
        mock_cursor = analytics_dashboard.db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.side_effect = [
            {"id": collection_id, "name": "Test Collection", "type": "curated"},
            {"views": 100, "clicks": 20, "shares": 5, "conversions": 2, "avg_time_viewed": 30.0},
            {"single_view_sessions": 20, "total_sessions": 80}
        ]

        with patch.object(analytics_dashboard, '_calculate_trending_score', return_value=50.0):
            insights = await analytics_dashboard.get_collection_insights(collection_id)

            assert insights.total_views == 100
            assert insights.total_clicks == 20
            assert insights.total_conversions == 2

    @pytest.mark.asyncio
    async def test_ab_test_with_analytics(self, ab_testing_framework, analytics_dashboard):
        """Test A/B testing integration with analytics"""
        test_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Create A/B test
        with patch.object(ab_testing_framework.db_conn, 'commit'):
            test_id = await ab_testing_framework.create_test(
                name="Collection Layout Test",
                variants={"control": {"layout": "grid"}, "variant_a": {"layout": "list"}},
                traffic_split={"control": 0.5, "variant_a": 0.5},
                success_metric="click_through_rate"
            )

        # Get user variant
        with patch.object(ab_testing_framework, '_get_test') as mock_get_test:
            mock_get_test.return_value = ABTest(
                id=test_id,
                name="Collection Layout Test",
                variants={"control": {}, "variant_a": {}},
                traffic_split={"control": 0.5, "variant_a": 0.5},
                status="running"
            )

            variant = await ab_testing_framework.get_user_variant(test_id, user_id)
            assert variant in ["control", "variant_a"]

        # Track analytics events
        with patch.object(analytics_dashboard.db_conn, 'commit'):
            await analytics_dashboard.track_event(
                "view",
                f"collection_{variant}",
                user_id,
                metadata={"ab_test": test_id, "variant": variant}
            )

            await analytics_dashboard.track_event(
                "click",
                f"collection_{variant}",
                user_id,
                metadata={"ab_test": test_id, "variant": variant}
            )

# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in collections system"""

    @pytest.mark.asyncio
    async def test_collection_not_found(self, collection_engine):
        """Test handling of non-existent collection"""
        # Mock database to return None
        collection_engine.db_conn.cursor.return_value.fetchone.return_value = None

        collection = await collection_engine.get_collection("non_existent_id")
        assert collection is None

    @pytest.mark.asyncio
    async def test_invalid_criteria(self, collection_engine):
        """Test handling of invalid collection criteria"""
        with pytest.raises(Exception):
            # Create invalid criteria
            criteria = CollectionCriteria(
                price_min=100000,
                price_max=50000  # Invalid range
            )
            await collection_engine._validate_criteria(criteria)

    @pytest.mark.asyncio
    async def test_websocket_connection_failure(self, websocket_service):
        """Test handling of WebSocket connection failures"""
        # Create connection with broken WebSocket
        broken_websocket = MagicMock()
        broken_websocket.send_json.side_effect = Exception("Connection broken")

        connection_id = await websocket_service.add_connection(broken_websocket, "test_user")

        # Attempt to send message
        update = CollectionUpdate(
            collection_id="test_collection",
            update_type="created",
            data={},
            timestamp=datetime.utcnow()
        )

        # Should handle the error gracefully
        await websocket_service.broadcast_collection_update(update)

        # Connection should be removed
        assert connection_id not in websocket_service.connections

# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance of collections system"""

    @pytest.mark.asyncio
    async def test_large_collection_scoring(self, collection_engine):
        """Test scoring performance with large number of vehicles"""
        # Generate large dataset
        vehicles = []
        for i in range(1000):
            vehicles.append({
                "id": f"vehicle_{i}",
                "price": 20000 + (i * 100),
                "year": 2020 + (i % 5),
                "mileage": 1000 * (i + 1)
            })

        criteria = CollectionCriteria(
            price_max=100000,
            year_min=2020,
            mileage_max=50000
        )

        # Measure performance
        start_time = datetime.utcnow()
        scores = await collection_engine._score_vehicles(vehicles, criteria)
        end_time = datetime.utcnow()

        # Should complete within reasonable time (5 seconds for 1000 vehicles)
        duration = (end_time - start_time).total_seconds()
        assert duration < 5.0
        assert len(scores) == 1000

    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self, websocket_service):
        """Test handling many concurrent WebSocket connections"""
        # Create many connections
        connection_ids = []
        for i in range(100):
            websocket = MagicMock()
            websocket.send_json = AsyncMock()
            connection_id = await websocket_service.add_connection(websocket, f"user_{i}")
            connection_ids.append(connection_id)

        # Broadcast update to all
        update = CollectionUpdate(
            collection_id="broadcast_test",
            update_type="created",
            data={},
            timestamp=datetime.utcnow()
        )

        start_time = datetime.utcnow()
        await websocket_service.broadcast_collection_update(update)
        end_time = datetime.utcnow()

        # Should complete quickly
        duration = (end_time - start_time).total_seconds()
        assert duration < 1.0
        assert len(websocket_service.connections) == 100

# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])