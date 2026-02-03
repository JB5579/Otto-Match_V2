"""
Test suite for Vehicle Database Service
Tests embedding storage, retrieval, similarity search, and semantic tag management
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

from ..vehicle_database_service import VehicleDatabaseService

class TestVehicleDatabaseService:
    """Test class for VehicleDatabaseService"""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection"""
        conn = Mock()
        cursor = Mock()
        conn.cursor.return_value.__enter__.return_value = cursor
        conn.cursor.return_value.__exit__.return_value = None
        conn.commit.return_value = None
        conn.rollback.return_value = None
        return conn

    @pytest.fixture
    def vehicle_db_service(self, mock_db_connection):
        """Create vehicle database service instance with mock connection"""
        return VehicleDatabaseService(
            db_connection=mock_db_connection,
            embedding_dim=3072
        )

    def test_service_initialization(self, mock_db_connection):
        """Test service initialization"""
        service = VehicleDatabaseService(
            db_connection=mock_db_connection,
            embedding_dim=3072
        )

        assert service.db_conn == mock_db_connection
        assert service.embedding_dim == 3072

    @pytest.mark.asyncio
    async def test_store_vehicle_embedding_success(self, vehicle_db_service, mock_db_connection):
        """Test successful vehicle embedding storage"""
        vehicle_id = "test-vehicle-001"
        embedding = [0.5] * 3072
        semantic_tags = ["toyota", "camry", "sedan", "2022"]

        # Mock successful database operations
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None  # Vehicle doesn't exist

        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id=vehicle_id,
            embedding=embedding,
            semantic_tags=semantic_tags,
            vehicle_make="Toyota",
            vehicle_model="Camry",
            vehicle_year=2022,
            price_range="mid-range"
        )

        assert result is True
        cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_store_vehicle_embedding_update_existing(self, vehicle_db_service, mock_db_connection):
        """Test updating existing vehicle embedding"""
        vehicle_id = "test-vehicle-001"
        embedding = [0.6] * 3072
        semantic_tags = ["toyota", "camry", "sedan", "2022", "updated"]

        # Mock existing vehicle
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {"id": 1}  # Vehicle exists

        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id=vehicle_id,
            embedding=embedding,
            semantic_tags=semantic_tags,
            vehicle_make="Toyota",
            vehicle_model="Camry",
            vehicle_year=2022,
            price_range="mid-range"
        )

        assert result is True
        cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_store_vehicle_embedding_validation_error(self, vehicle_db_service):
        """Test embedding storage with invalid inputs"""
        # Test invalid vehicle_id
        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id="",  # Empty string
            embedding=[0.5] * 3072,
            semantic_tags=["test"]
        )
        assert result is False

        # Test invalid embedding dimension
        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id="test-001",
            embedding=[0.5] * 1000,  # Wrong dimension
            semantic_tags=["test"]
        )
        assert result is False

        # Test invalid semantic_tags
        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id="test-001",
            embedding=[0.5] * 3072,
            semantic_tags="not_a_list"  # Should be a list
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_store_vehicle_embedding_retry_logic(self, vehicle_db_service, mock_db_connection):
        """Test retry logic on database errors"""
        vehicle_id = "test-vehicle-001"
        embedding = [0.5] * 3072
        semantic_tags = ["toyota", "camry"]

        # Mock database error first two times, success on third
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None

        # Simulate database errors
        side_effects = [
            psycopg2.Error("Connection failed"),
            psycopg2.Error("Timeout"),
            None  # Success
        ]
        cursor.execute.side_effect = side_effects

        result = await vehicle_db_service.store_vehicle_embedding(
            vehicle_id=vehicle_id,
            embedding=embedding,
            semantic_tags=semantic_tags
        )

        # Should eventually succeed after retries
        assert result is True
        assert cursor.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_get_vehicle_embedding_success(self, vehicle_db_service, mock_db_connection):
        """Test successful vehicle embedding retrieval"""
        vehicle_id = "test-vehicle-001"

        # Mock successful retrieval
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {
            "id": 1,
            "vehicle_id": vehicle_id,
            "embedding": [0.5] * 3072,
            "semantic_tags": ["toyota", "camry"],
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": 2022,
            "price_range": "mid-range",
            "image_count": 5,
            "metadata_processed": True
        }

        result = await vehicle_db_service.get_vehicle_embedding(vehicle_id)

        assert result is not None
        assert result["vehicle_id"] == vehicle_id
        assert result["vehicle_make"] == "Toyota"
        assert result["semantic_tags"] == ["toyota", "camry"]

    @pytest.mark.asyncio
    async def test_get_vehicle_embedding_not_found(self, vehicle_db_service, mock_db_connection):
        """Test retrieval of non-existent vehicle"""
        vehicle_id = "non-existent-vehicle"

        # Mock no results found
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None

        result = await vehicle_db_service.get_vehicle_embedding(vehicle_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_search_similar_vehicles_basic(self, vehicle_db_service, mock_db_connection):
        """Test basic similarity search"""
        query_embedding = [0.5] * 3072

        # Mock search results
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {
                "vehicle_id": "similar-001",
                "similarity_score": 0.85,
                "vehicle_make": "Toyota",
                "vehicle_model": "Camry"
            },
            {
                "vehicle_id": "similar-002",
                "similarity_score": 0.78,
                "vehicle_make": "Honda",
                "vehicle_model": "Accord"
            }
        ]

        results = await vehicle_db_service.search_similar_vehicles(
            query_embedding=query_embedding,
            limit=10,
            similarity_threshold=0.7
        )

        assert len(results) == 2
        assert results[0]["similarity_score"] > results[1]["similarity_score"]
        assert results[0]["vehicle_make"] == "Toyota"

    @pytest.mark.asyncio
    async def test_search_similar_vehicles_with_filters(self, vehicle_db_service, mock_db_connection):
        """Test similarity search with filters"""
        query_embedding = [0.5] * 3072

        # Mock filtered search results
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {
                "vehicle_id": "filtered-001",
                "similarity_score": 0.82,
                "vehicle_make": "Toyota",
                "vehicle_year": 2022
            }
        ]

        results = await vehicle_db_service.search_similar_vehicles(
            query_embedding=query_embedding,
            limit=10,
            similarity_threshold=0.7,
            vehicle_make="Toyota",
            vehicle_year_range=(2020, 2023),
            required_tags=["sedan"]
        )

        assert len(results) == 1
        assert results[0]["vehicle_make"] == "Toyota"
        assert results[0]["vehicle_year"] == 2022

    @pytest.mark.asyncio
    async def test_search_by_semantic_tags_match_any(self, vehicle_db_service, mock_db_connection):
        """Test semantic tag search with any match"""
        tags = ["suv", "toyota"]

        # Mock tag search results
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {"vehicle_id": "tag-match-001", "vehicle_make": "Toyota", "semantic_tags": ["suv", "toyota", "highlander"]},
            {"vehicle_id": "tag-match-002", "vehicle_make": "Ford", "semantic_tags": ["suv", "explorer"]}
        ]

        results = await vehicle_db_service.search_by_semantic_tags(
            tags=tags,
            match_all=False,
            limit=20
        )

        assert len(results) == 2
        assert all("suv" in result["semantic_tags"] or "toyota" in result["semantic_tags"]
                  for result in results)

    @pytest.mark.asyncio
    async def test_search_by_semantic_tags_match_all(self, vehicle_db_service, mock_db_connection):
        """Test semantic tag search requiring all tags"""
        tags = ["suv", "toyota"]

        # Mock strict tag search results
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {"vehicle_id": "strict-match-001", "semantic_tags": ["suv", "toyota", "highlander"]}
        ]

        results = await vehicle_db_service.search_by_semantic_tags(
            tags=tags,
            match_all=True,
            limit=20
        )

        assert len(results) == 1
        assert all(tag in results[0]["semantic_tags"] for tag in tags)

    @pytest.mark.asyncio
    async def test_get_popular_semantic_tags(self, vehicle_db_service, mock_db_connection):
        """Test retrieving popular semantic tags"""
        # Mock popular tags results
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {"tag": "suv", "vehicle_count": 150},
            {"tag": "toyota", "vehicle_count": 120},
            {"tag": "sedan", "vehicle_count": 100},
            {"tag": "honda", "vehicle_count": 85}
        ]

        results = await vehicle_db_service.get_popular_semantic_tags(limit=50)

        assert len(results) == 4
        assert results[0]["tag"] == "suv"
        assert results[0]["vehicle_count"] == 150
        assert all(isinstance(result["vehicle_count"], int) for result in results)

    @pytest.mark.asyncio
    async def test_update_vehicle_tags_merge(self, vehicle_db_service, mock_db_connection):
        """Test updating vehicle tags with merge option"""
        vehicle_id = "test-vehicle-001"
        new_tags = ["luxury", "leather-seats"]

        # Mock tag update
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.rowcount = 1  # One row affected

        result = await vehicle_db_service.update_vehicle_tags(
            vehicle_id=vehicle_id,
            new_tags=new_tags,
            merge_with_existing=True
        )

        assert result is True
        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vehicle_tags_replace(self, vehicle_db_service, mock_db_connection):
        """Test updating vehicle tags with replace option"""
        vehicle_id = "test-vehicle-001"
        new_tags = ["updated-tag-1", "updated-tag-2"]

        # Mock tag replacement
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.rowcount = 1  # One row affected

        result = await vehicle_db_service.update_vehicle_tags(
            vehicle_id=vehicle_id,
            new_tags=new_tags,
            merge_with_existing=False
        )

        assert result is True
        cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_database_statistics(self, vehicle_db_service, mock_db_connection):
        """Test retrieving comprehensive database statistics"""
        # Mock statistics queries
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor

        # Mock multiple query results
        def fetchone_side_effect():
            # Return different results for different queries
            if not hasattr(cursor, '_call_count'):
                cursor._call_count = 0
            cursor._call_count += 1

            if cursor._call_count == 1:
                return {"total_vehicles": 1000}
            elif cursor._call_count == 2:
                return {"vehicles_with_images": 800}
            elif cursor._call_count == 3:
                return {"avg_image_count": 4.5}
            elif cursor._call_count == 4:
                return None  # For popular makes query (handled by fetchall)
            elif cursor._call_count == 5:
                return None  # For year distribution (handled by fetchall)
            elif cursor._call_count == 6:
                return {"vehicles_with_tags": 950, "unique_tags": 200, "avg_tags_per_vehicle": 8.2}
            else:
                return None

        cursor.fetchone.side_effect = fetchone_side_effect
        cursor.fetchall.side_effect = [
            [{"make": "Toyota", "count": 200}, {"make": "Honda", "count": 150}],  # Popular makes
            [{"year": 2023, "count": 300}, {"year": 2022, "count": 250}]  # Year distribution
        ]

        stats = await vehicle_db_service.get_database_statistics()

        assert stats['total_vehicles'] == 1000
        assert stats['vehicles_with_images'] == 800
        assert stats['avg_image_count'] == 4.5
        assert len(stats['popular_makes']) == 2
        assert len(stats['year_distribution']) == 2
        assert stats['vehicles_with_tags'] == 950
        assert stats['unique_tags'] == 200
        assert stats['avg_tags_per_vehicle'] == 8.2

    @pytest.mark.asyncio
    async def test_delete_vehicle_embedding_success(self, vehicle_db_service, mock_db_connection):
        """Test successful vehicle embedding deletion"""
        vehicle_id = "test-vehicle-001"

        # Mock successful deletion
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.rowcount = 1  # One row deleted

        result = await vehicle_db_service.delete_vehicle_embedding(vehicle_id)

        assert result is True
        cursor.execute.assert_called_once_with(
            "DELETE FROM vehicle_embeddings WHERE vehicle_id = %s",
            (vehicle_id,)
        )

    @pytest.mark.asyncio
    async def test_delete_vehicle_embedding_not_found(self, vehicle_db_service, mock_db_connection):
        """Test deletion of non-existent vehicle"""
        vehicle_id = "non-existent-vehicle"

        # Mock no rows affected
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.rowcount = 0  # No rows deleted

        result = await vehicle_db_service.delete_vehicle_embedding(vehicle_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_database_error_handling(self, vehicle_db_service, mock_db_connection):
        """Test handling of database errors"""
        # Mock database error
        cursor = Mock()
        mock_db_connection.cursor.return_value.__enter__.return_value = cursor
        cursor.execute.side_effect = psycopg2.Error("Database connection failed")

        # Test that errors are handled gracefully
        with patch('vehicle_database_service.logger') as mock_logger:
            result = await vehicle_db_service.get_vehicle_embedding("test-vehicle")
            assert result is None
            mock_logger.error.assert_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])