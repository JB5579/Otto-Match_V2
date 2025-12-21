"""
Unit tests for FavoritesService
Tests core functionality with mocked database connections
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from user.favorites_service import FavoritesService, FavoriteItem


class TestFavoritesService:
    """Test suite for FavoritesService"""

    @pytest.fixture
    def mock_db_conn(self):
        """Mock database connection"""
        conn = Mock()
        conn.cursor = MagicMock()
        conn.commit = Mock()
        conn.rollback = Mock()
        conn.close = Mock()
        return conn

    @pytest.fixture
    def service(self):
        """Create FavoritesService instance"""
        service = FavoritesService()
        return service

    @pytest.mark.asyncio
    async def test_initialize_success(self, service, mock_db_conn):
        """Test successful initialization"""
        with patch('psycopg.connect', return_value=mock_db_conn):
            with patch.object(service, '_create_favorites_table', return_value=None):
                result = await service.initialize(
                    'https://test.supabase.co',
                    'test_key'
                )
                assert result is True
                assert service.db_conn == mock_db_conn

    @pytest.mark.asyncio
    async def test_initialize_failure(self, service):
        """Test initialization failure"""
        with patch('psycopg.connect', side_effect=Exception("Connection failed")):
            result = await service.initialize(
                'https://test.supabase.co',
                'test_key'
            )
            assert result is False
            assert service.db_conn is None

    @pytest.mark.asyncio
    async def test_add_to_favorites_new(self, service, mock_db_conn):
        """Test adding new favorite"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = ('uuid-123', datetime.now())
        mock_db_conn.cursor.return_value.__enter__.return_value.execute = Mock()
        service.db_conn = mock_db_conn

        # Mock favorite_exists to return False
        with patch.object(service, 'favorite_exists', return_value=False):
            result = await service.add_to_favorites('user123', 'vehicle456')
            assert result is True

    @pytest.mark.asyncio
    async def test_add_to_favorites_duplicate(self, service):
        """Test adding duplicate favorite"""
        service.db_conn = Mock()
        with patch.object(service, 'favorite_exists', return_value=True):
            result = await service.add_to_favorites('user123', 'vehicle456')
            assert result is False

    @pytest.mark.asyncio
    async def test_remove_from_favorites_success(self, service, mock_db_conn):
        """Test successful favorite removal"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = ('uuid-123',)
        mock_db_conn.cursor.return_value.__enter__.return_value.execute = Mock()
        service.db_conn = mock_db_conn

        result = await service.remove_from_favorites('user123', 'vehicle456')
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_from_favorites_not_found(self, service, mock_db_conn):
        """Test removing non-existent favorite"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        mock_db_conn.cursor.return_value.__enter__.return_value.execute = Mock()
        service.db_conn = mock_db_conn

        result = await service.remove_from_favorites('user123', 'vehicle456')
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_favorites(self, service):
        """Test getting user favorites"""
        # Mock data
        mock_rows = [
            {
                'id': 'uuid-1',
                'user_id': 'user123',
                'vehicle_id': 'vehicle456',
                'created_at': datetime.now(),
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Camry',
                'vehicle_year': 2022,
                'price': 25000.0,
                'vehicle_image': 'http://example.com/image.jpg',
                'vehicle_url': 'http://example.com/vehicle'
            }
        ]

        # Setup mock
        mock_conn = Mock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.fetchall.side_effect = [
            [{'total': 1}],  # Count query result
            mock_rows         # Favorites query result
        ]
        mock_cursor.fetchone.side_effect = [
            {'total': 1},  # First fetchone for count
            mock_cursor.fetchall()  # Second fetchone returns all rows
        ]

        mock_conn.cursor = Mock(return_value=mock_cursor)
        service.db_conn = mock_conn

        # Create a proper mock for dict_row factory
        from psycopg.rows import dict_row
        mock_cursor.row_factory = dict_row

        favorites, total = await service.get_user_favorites('user123', limit=20, offset=0)
        assert len(favorites) == 1
        assert total == 1
        assert favorites[0].vehicle_id == 'vehicle456'
        assert favorites[0].vehicle_make == 'Toyota'

    @pytest.mark.asyncio
    async def test_favorite_exists_true(self, service, mock_db_conn):
        """Test checking if favorite exists - true case"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)
        service.db_conn = mock_db_conn

        result = await service.favorite_exists('user123', 'vehicle456')
        assert result is True

    @pytest.mark.asyncio
    async def test_favorite_exists_false(self, service, mock_db_conn):
        """Test checking if favorite exists - false case"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)
        service.db_conn = mock_db_conn

        result = await service.favorite_exists('user123', 'vehicle456')
        assert result is False

    @pytest.mark.asyncio
    async def test_get_favorite_count(self, service, mock_db_conn):
        """Test getting favorite count"""
        # Setup mock
        mock_db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (5,)
        service.db_conn = mock_db_conn

        count = await service.get_favorite_count('user123')
        assert count == 5

    def test_favorite_item_creation(self):
        """Test FavoriteItem dataclass creation"""
        favorite = FavoriteItem(
            id='uuid-123',
            user_id='user123',
            vehicle_id='vehicle456',
            created_at=datetime.now(),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2022,
            price=25000.0,
            vehicle_image='http://example.com/image.jpg',
            vehicle_url='http://example.com/vehicle'
        )

        assert favorite.id == 'uuid-123'
        assert favorite.user_id == 'user123'
        assert favorite.vehicle_id == 'vehicle456'
        assert favorite.vehicle_make == 'Toyota'
        assert favorite.price == 25000.0