"""
API Endpoint Tests for Otto.AI Collections System

Tests for all REST API endpoints including admin, public, and analytics APIs.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main import app
from src.api.admin.collections_api import (
    CreateCollectionRequest,
    UpdateCollectionRequest,
    CollectionCriteriaRequest
)
from src.api.analytics_api import (
    TrackEventRequest,
    DashboardRequest,
    ExportRequest
)

# Create test client
client = TestClient(app)

# ============================================================================
# Admin Collections API Tests
# ============================================================================

class TestAdminCollectionsAPI:
    """Test admin collections API endpoints"""

    def test_create_collection_success(self):
        """Test successful collection creation"""
        request_data = {
            "name": "Test Collection",
            "description": "Test Description",
            "collection_type": "curated",
            "criteria": {
                "vehicle_type": "SUV",
                "fuel_type": ["electric"],
                "price_max": 50000
            },
            "sort_order": 1,
            "is_featured": True
        }

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.create_collection.return_value = "test_collection_id"
            mock_engine.get_collection.return_value = MagicMock(
                id="test_collection_id",
                name="Test Collection",
                description="Test Description",
                type="curated",
                criteria=MagicMock(),
                vehicle_ids=[],
                metadata={},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_get_engine.return_value = mock_engine

            response = client.post(
                "/api/admin/collections/create",
                json=request_data,
                headers={"x-user-id": "test_user"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Collection"
            assert data["type"] == "curated"

    def test_create_collection_invalid_type(self):
        """Test collection creation with invalid type"""
        request_data = {
            "name": "Test Collection",
            "collection_type": "invalid_type",
            "criteria": {"vehicle_type": "SUV"}
        }

        response = client.post(
            "/api/admin/collections/create",
            json=request_data
        )

        assert response.status_code == 422  # Validation error

    def test_update_collection_success(self):
        """Test successful collection update"""
        collection_id = "test_collection_id"
        request_data = {
            "name": "Updated Collection",
            "description": "Updated Description"
        }

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.update_collection.return_value = True
            mock_engine.get_collection.return_value = MagicMock(
                id=collection_id,
                name="Updated Collection",
                description="Updated Description",
                type="curated",
                criteria=MagicMock(),
                vehicle_ids=[],
                metadata={"sort_order": 0, "is_featured": False},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_get_engine.return_value = mock_engine

            response = client.put(
                f"/api/admin/collections/{collection_id}/update",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Collection"

    def test_update_collection_not_found(self):
        """Test updating non-existent collection"""
        collection_id = "non_existent_id"
        request_data = {"name": "Updated"}

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.update_collection.return_value = False
            mock_get_engine.return_value = mock_engine

            response = client.put(
                f"/api/admin/collections/{collection_id}/update",
                json=request_data
            )

            assert response.status_code == 404

    def test_delete_collection_success(self):
        """Test successful collection deletion"""
        collection_id = "test_collection_id"

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.delete_collection.return_value = True
            mock_get_engine.return_value = mock_engine

            response = client.delete(f"/api/admin/collections/{collection_id}/delete")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_list_collections_success(self):
        """Test successful collection listing"""
        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collections.return_value = [
                MagicMock(
                    id="collection_1",
                    name="Collection 1",
                    description="Description 1",
                    type="curated",
                    criteria=MagicMock(),
                    vehicle_ids=["v1", "v2"],
                    metadata={"sort_order": 1, "is_featured": True},
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00"
                ),
                MagicMock(
                    id="collection_2",
                    name="Collection 2",
                    description="Description 2",
                    type="trending",
                    criteria=MagicMock(),
                    vehicle_ids=["v3", "v4"],
                    metadata={"sort_order": 2, "is_featured": False},
                    created_at="2024-01-02T00:00:00",
                    updated_at="2024-01-02T00:00:00"
                )
            ]
            mock_get_engine.return_value = mock_engine

            response = client.get("/api/admin/collections/list")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Collection 1"

    def test_refresh_collection_success(self):
        """Test successful collection refresh"""
        collection_id = "test_collection_id"

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collection.return_value = MagicMock(
                id=collection_id,
                vehicle_ids=["v1", "v2", "v3"]
            )
            mock_engine._generate_collection_vehicles = AsyncMock()
            mock_get_engine.return_value = mock_engine

            # Mock database cursor
            with patch.object(mock_engine.db_conn, 'cursor') as mock_cursor:
                mock_cursor.return_value.__enter__.return_value = MagicMock()

                response = client.post(f"/api/admin/collections/{collection_id}/refresh")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_generate_from_template_success(self):
        """Test successful collection generation from template"""
        request_data = {
            "template_name": "Electric Vehicles",
            "collection_name": "My Electric Cars",
            "description": "Custom electric vehicle collection"
        }

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.generate_collection_from_template.return_value = "generated_collection_id"
            mock_engine.get_collection.return_value = MagicMock(
                id="generated_collection_id",
                name="My Electric Cars",
                description="Custom electric vehicle collection",
                type="template",
                criteria=MagicMock(),
                vehicle_ids=["v1", "v2"],
                metadata={"sort_order": 0, "is_featured": False},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_get_engine.return_value = mock_engine

            response = client.post(
                "/api/admin/collections/generate-from-template",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "My Electric Cars"

    def test_generate_from_template_not_found(self):
        """Test generation with non-existent template"""
        request_data = {
            "template_name": "Non Existent Template",
            "collection_name": "Test Collection"
        }

        with patch('src.api.admin.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.generate_collection_from_template.return_value = None
            mock_get_engine.return_value = mock_engine

            response = client.post(
                "/api/admin/collections/generate-from-template",
                json=request_data
            )

            assert response.status_code == 400

# ============================================================================
# Public Collections API Tests
# ============================================================================

class TestPublicCollectionsAPI:
    """Test public collections API endpoints"""

    def test_get_collections_success(self):
        """Test successful collections retrieval"""
        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collections.return_value = [
                MagicMock(
                    id="collection_1",
                    name="Featured Cars",
                    description="Top featured vehicles",
                    type="curated",
                    criteria=MagicMock(),
                    vehicle_ids=["v1", "v2", "v3"],
                    metadata={"is_featured": True},
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00"
                )
            ]
            mock_get_engine.return_value = mock_engine

            response = client.get("/api/collections/")

            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
            assert len(data["collections"]) > 0

    def test_get_collections_with_filters(self):
        """Test collections retrieval with filters"""
        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collections.return_value = []
            mock_get_engine.return_value = mock_engine

            response = client.get(
                "/api/collections/?collection_type=curated&featured=true&limit=10"
            )

            assert response.status_code == 200
            # Verify filters were passed (would need to check mock calls)

    def test_get_collection_detail_success(self):
        """Test successful collection detail retrieval"""
        collection_id = "test_collection_id"

        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collection.return_value = MagicMock(
                id=collection_id,
                name="Test Collection",
                description="Test Description",
                type="curated",
                criteria=MagicMock(),
                vehicle_ids=["v1", "v2", "v3"],
                metadata={},
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_engine.get_collection_vehicles.return_value = [
                {"id": "v1", "make": "Tesla", "model": "Model 3", "price": 40000},
                {"id": "v2", "make": "Ford", "model": "Mustang", "price": 35000}
            ]
            mock_get_engine.return_value = mock_engine

            response = client.get(f"/api/collections/{collection_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == collection_id
            assert "vehicles" in data

    def test_get_collection_detail_not_found(self):
        """Test collection detail retrieval for non-existent collection"""
        collection_id = "non_existent_id"

        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collection.return_value = None
            mock_get_engine.return_value = mock_engine

            response = client.get(f"/api/collections/{collection_id}")

            assert response.status_code == 404

    def test_get_collection_vehicles_success(self):
        """Test successful collection vehicles retrieval"""
        collection_id = "test_collection_id"

        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_collection.return_value = MagicMock(
                id=collection_id,
                vehicle_ids=["v1", "v2", "v3"]
            )
            mock_engine.get_collection_vehicles.return_value = [
                {"id": "v1", "make": "Tesla", "model": "Model 3"},
                {"id": "v2", "make": "Ford", "model": "Mustang"},
                {"id": "v3", "make": "BMW", "model": "X5"}
            ]
            mock_get_engine.return_value = mock_engine

            response = client.get(f"/api/collections/{collection_id}/vehicles")

            assert response.status_code == 200
            data = response.json()
            assert "vehicles" in data
            assert len(data["vehicles"]) == 3

    def test_get_trending_collections_success(self):
        """Test successful trending collections retrieval"""
        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_trending_collections.return_value = [
                ("collection_1", 85.5),
                ("collection_2", 75.2),
                ("collection_3", 65.8)
            ]
            mock_engine.get_collections.return_value = [
                MagicMock(
                    id="collection_1",
                    name="Trending SUVs",
                    type="trending",
                    vehicle_ids=[]
                ),
                MagicMock(
                    id="collection_2",
                    name="Electric Cars",
                    type="trending",
                    vehicle_ids=[]
                )
            ]
            mock_get_engine.return_value = mock_engine

            response = client.get("/api/collections/trending")

            assert response.status_code == 200
            data = response.json()
            assert "collections" in data

    def test_get_categories_success(self):
        """Test successful categories retrieval"""
        with patch('src.api.collections_api.get_collection_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.get_categories.return_value = {
                "vehicle_types": ["SUV", "Sedan", "Truck", "Convertible"],
                "fuel_types": ["gasoline", "electric", "hybrid", "diesel"],
                "price_ranges": [
                    {"min": 0, "max": 25000, "label": "Under $25k"},
                    {"min": 25000, "max": 50000, "label": "$25k - $50k"},
                    {"min": 50000, "max": 100000, "label": "$50k - $100k"},
                    {"min": 100000, "max": None, "label": "Over $100k"}
                ]
            }
            mock_get_engine.return_value = mock_engine

            response = client.get("/api/collections/categories")

            assert response.status_code == 200
            data = response.json()
            assert "categories" in data
            assert "vehicle_types" in data["categories"]
            assert "fuel_types" in data["categories"]

# ============================================================================
# Analytics API Tests
# ============================================================================

class TestAnalyticsAPI:
    """Test analytics API endpoints"""

    def test_track_event_success(self):
        """Test successful event tracking"""
        request_data = {
            "event_type": "view",
            "collection_id": "test_collection_id",
            "user_id": "test_user",
            "session_id": "session_123",
            "metadata": {"source": "homepage"}
        }

        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.track_event = AsyncMock()
            mock_get_dashboard.return_value = mock_dashboard

            response = client.post(
                "/api/analytics/track",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_track_event_invalid_type(self):
        """Test event tracking with invalid event type"""
        request_data = {
            "event_type": "invalid_event",
            "collection_id": "test_collection_id"
        }

        response = client.post("/api/analytics/track", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_get_dashboard_data_success(self):
        """Test successful dashboard data retrieval"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.get_dashboard_data.return_value = {
                "time_period": "day",
                "date_range": {
                    "start": "2024-01-01T00:00:00",
                    "end": "2024-01-02T00:00:00"
                },
                "widgets": [
                    {
                        "widget_id": "overview_metrics",
                        "widget_type": "metric_cards",
                        "data": {"metrics": []}
                    }
                ],
                "summary": {
                    "total_collections": 10,
                    "total_views": 1000
                }
            }
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "widgets" in data
            assert "summary" in data

    def test_get_collection_insights_success(self):
        """Test successful collection insights retrieval"""
        collection_id = "test_collection_id"

        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.get_collection_insights.return_value = MagicMock(
                collection_id=collection_id,
                collection_name="Test Collection",
                total_views=1000,
                total_clicks=150,
                total_conversions=10,
                engagement_rate=0.15,
                click_through_rate=0.15,
                conversion_rate=0.01,
                trending_score=75.5,
                performance_trend="improving",
                user_demographics={},
                recommendations=[]
            )
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get(f"/api/analytics/collections/{collection_id}/insights")

            assert response.status_code == 200
            data = response.json()
            assert data["collection_id"] == collection_id
            assert "metrics" in data

    def test_get_top_collections_success(self):
        """Test successful top collections retrieval"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.get_top_collections.return_value = [
                {
                    "id": "collection_1",
                    "name": "Top Collection",
                    "type": "curated",
                    "metric_value": 1000,
                    "views": 1000,
                    "clicks": 150,
                    "conversions": 10
                }
            ]
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/collections/top")

            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
            assert len(data["collections"]) > 0

    def test_export_analytics_csv(self):
        """Test analytics export in CSV format"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.export_analytics_report.return_value = "test_report.csv"
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/export?format_type=csv")

            assert response.status_code == 200

    def test_export_analytics_json(self):
        """Test analytics export in JSON format"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.export_analytics_report.return_value = '{"data": "test"}'
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/export?format_type=json")

            assert response.status_code == 200
            data = response.json()
            assert "data" in data

    def test_get_metrics_summary_success(self):
        """Test successful metrics summary retrieval"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = {
                "total_collections": 10,
                "total_views": 10000,
                "total_clicks": 1500,
                "total_conversions": 100,
                "total_shares": 200,
                "unique_users": 5000
            }
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/metrics/summary")

            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert data["summary"]["total_collections"] == 10

    def test_get_realtime_metrics_success(self):
        """Test successful real-time metrics retrieval"""
        with patch('src.api.analytics_api.get_analytics_dashboard') as mock_get_dashboard:
            mock_dashboard = AsyncMock()
            mock_dashboard.db_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
                {"minute": "2024-01-01 12:00", "event_type": "view", "count": 10},
                {"minute": "2024-01-01 12:00", "event_type": "click", "count": 2}
            ]
            mock_get_dashboard.return_value = mock_dashboard

            response = client.get("/api/analytics/realtime")

            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data

# ============================================================================
# Health and Root Endpoint Tests
# ============================================================================

class TestHealthEndpoints:
    """Test health and root endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Welcome to Otto.AI API"

# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test API error handling"""

    def test_404_not_found(self):
        """Test 404 error for non-existent endpoint"""
        response = client.get("/api/non-existent-endpoint")

        assert response.status_code == 404

    def test_missing_supabase_config(self):
        """Test behavior when Supabase configuration is missing"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None

            response = client.post(
                "/api/admin/collections/create",
                json={
                    "name": "Test",
                    "collection_type": "curated",
                    "criteria": {}
                }
            )

            assert response.status_code == 500

    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payload"""
        response = client.post(
            "/api/analytics/track",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test validation for missing required fields"""
        # Missing required fields in collection creation
        response = client.post(
            "/api/admin/collections/create",
            json={}
        )

        assert response.status_code == 422

# ============================================================================
# Test Configuration and Utilities
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Mock environment variables
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_key',
        'SUPABASE_DB_PASSWORD': 'test_password'
    }):
        yield

# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run all API tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])