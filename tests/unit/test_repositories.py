"""
Unit tests for Otto.AI Repositories
Tests for listing_repository and image_repository
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Import repositories
from src.repositories.listing_repository import (
    ListingRepository,
    ListingCreate,
    ListingUpdate,
    get_listing_repository
)
from src.repositories.image_repository import (
    ImageRepository,
    ImageCreate,
    ImageUpdate,
    get_image_repository
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def sample_listing_data() -> Dict[str, Any]:
    """Sample listing data for tests"""
    return {
        'id': 'test-uuid-1234',
        'vin': '1HGBH41JXMN109186',
        'year': 2021,
        'make': 'Honda',
        'model': 'Civic',
        'trim': 'EX',
        'odometer': 15000,
        'drivetrain': 'FWD',
        'transmission': 'CVT',
        'engine': '2.0L 4-Cylinder',
        'exterior_color': 'Silver',
        'interior_color': 'Black',
        'condition_score': 4.2,
        'condition_grade': 'Clean',
        'description_text': 'Well-maintained vehicle',
        'status': 'active',
        'listing_source': 'pdf_upload',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_image_data() -> Dict[str, Any]:
    """Sample image data for tests"""
    return {
        'id': 'img-uuid-5678',
        'listing_id': 'test-uuid-1234',
        'vin': '1HGBH41JXMN109186',
        'category': 'hero',
        'vehicle_angle': 'front_three_quarter',
        'description': 'Front view of the vehicle',
        'suggested_alt': 'Silver Honda Civic front view',
        'quality_score': 8,
        'visible_damage': [],
        'file_format': 'jpeg',
        'width': 1920,
        'height': 1080,
        'web_url': 'https://storage.example.com/image.jpg',
        'thumbnail_url': 'https://storage.example.com/thumb.jpg',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


# ============================================================================
# ListingRepository Tests
# ============================================================================

class TestListingRepository:
    """Tests for ListingRepository CRUD operations"""

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    def test_init(self, mock_get_client):
        """Test repository initialization"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repo = ListingRepository()

        assert repo.client == mock_client
        assert repo.table_name == 'vehicle_listings'

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_create_listing(self, mock_get_client, sample_listing_data):
        """Test creating a new listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Setup mock response
        mock_result = MagicMock()
        mock_result.data = [sample_listing_data]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        repo = ListingRepository()

        listing_create = ListingCreate(
            vin=sample_listing_data['vin'],
            year=sample_listing_data['year'],
            make=sample_listing_data['make'],
            model=sample_listing_data['model'],
            trim=sample_listing_data['trim'],
            odometer=sample_listing_data['odometer'],
            drivetrain=sample_listing_data['drivetrain'],
            transmission=sample_listing_data['transmission'],
            engine=sample_listing_data['engine'],
            exterior_color=sample_listing_data['exterior_color'],
            interior_color=sample_listing_data['interior_color'],
            condition_score=sample_listing_data['condition_score'],
            condition_grade=sample_listing_data['condition_grade']
        )

        result = await repo.create(listing_create)

        assert result['id'] == sample_listing_data['id']
        assert result['vin'] == sample_listing_data['vin']
        mock_client.table.assert_called_with('vehicle_listings')

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_get_client, sample_listing_data):
        """Test getting a listing by ID"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_listing_data]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        result = await repo.get_by_id('test-uuid-1234')

        assert result is not None
        assert result['id'] == 'test-uuid-1234'

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_get_client):
        """Test getting a listing that doesn't exist"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        result = await repo.get_by_id('nonexistent-id')

        assert result is None

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_get_by_vin(self, mock_get_client, sample_listing_data):
        """Test getting a listing by VIN"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_listing_data]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        result = await repo.get_by_vin('1HGBH41JXMN109186')

        assert result is not None
        assert result['vin'] == '1HGBH41JXMN109186'

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_list_all(self, mock_get_client, sample_listing_data):
        """Test listing all listings with filters"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_listing_data]

        # Setup chained mock calls
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.range.return_value.execute.return_value = mock_result
        mock_client.table.return_value.select.return_value = mock_query

        repo = ListingRepository()
        result = await repo.list_all(limit=20, offset=0, make='Honda')

        assert len(result) == 1
        assert result[0]['make'] == 'Honda'

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_update_listing(self, mock_get_client, sample_listing_data):
        """Test updating a listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        updated_data = {**sample_listing_data, 'odometer': 20000}
        mock_result = MagicMock()
        mock_result.data = [updated_data]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        updates = ListingUpdate(odometer=20000)
        result = await repo.update('test-uuid-1234', updates)

        assert result is not None
        assert result['odometer'] == 20000

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_delete_listing(self, mock_get_client, sample_listing_data):
        """Test soft-deleting a listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [{**sample_listing_data, 'status': 'inactive'}]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        result = await repo.delete('test-uuid-1234')

        assert result is True

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_count_listings(self, mock_get_client):
        """Test counting listings by status"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.count = 5
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        repo = ListingRepository()
        result = await repo.count(status='active')

        assert result == 5


# ============================================================================
# ImageRepository Tests
# ============================================================================

class TestImageRepository:
    """Tests for ImageRepository CRUD operations"""

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    def test_init(self, mock_get_client):
        """Test repository initialization"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repo = ImageRepository()

        assert repo.client == mock_client
        assert repo.table_name == 'vehicle_images'

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_create_image(self, mock_get_client, sample_image_data):
        """Test creating a new image"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_image_data]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        repo = ImageRepository()

        image_create = ImageCreate(
            listing_id=sample_image_data['listing_id'],
            vin=sample_image_data['vin'],
            category=sample_image_data['category'],
            vehicle_angle=sample_image_data['vehicle_angle'],
            description=sample_image_data['description'],
            suggested_alt=sample_image_data['suggested_alt'],
            quality_score=sample_image_data['quality_score'],
            file_format=sample_image_data['file_format']
        )

        result = await repo.create(image_create)

        assert result['id'] == sample_image_data['id']
        assert result['category'] == 'hero'

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_create_batch(self, mock_get_client, sample_image_data):
        """Test batch creating images"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_image_data, {**sample_image_data, 'id': 'img-2'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        repo = ImageRepository()

        images = [
            ImageCreate(
                listing_id='test-uuid-1234',
                vin='1HGBH41JXMN109186',
                category='hero',
                vehicle_angle='front',
                description='Front view',
                suggested_alt='Front view',
                quality_score=8,
                file_format='jpeg'
            ),
            ImageCreate(
                listing_id='test-uuid-1234',
                vin='1HGBH41JXMN109186',
                category='carousel',
                vehicle_angle='side',
                description='Side view',
                suggested_alt='Side view',
                quality_score=7,
                file_format='jpeg'
            )
        ]

        result = await repo.create_batch(images)

        assert len(result) == 2

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_get_by_listing(self, mock_get_client, sample_image_data):
        """Test getting images by listing ID"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_image_data]
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result

        repo = ImageRepository()
        result = await repo.get_by_listing('test-uuid-1234')

        assert len(result) == 1
        assert result[0]['listing_id'] == 'test-uuid-1234'

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_get_hero_image(self, mock_get_client, sample_image_data):
        """Test getting hero image for a listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_image_data]
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result

        repo = ImageRepository()
        result = await repo.get_hero_image('test-uuid-1234')

        assert result is not None
        assert result['category'] == 'hero'

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_delete_by_listing(self, mock_get_client, sample_image_data):
        """Test deleting all images for a listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data = [sample_image_data, {**sample_image_data, 'id': 'img-2'}]
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result

        repo = ImageRepository()
        result = await repo.delete_by_listing('test-uuid-1234')

        assert result == 2

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @pytest.mark.asyncio
    async def test_count_by_listing(self, mock_get_client):
        """Test counting images for a listing"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.count = 5
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        repo = ImageRepository()
        result = await repo.count_by_listing('test-uuid-1234')

        assert result == 5


# ============================================================================
# Singleton Tests
# ============================================================================

class TestSingletons:
    """Tests for singleton patterns"""

    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    def test_listing_repository_singleton(self, mock_get_client):
        """Test ListingRepository singleton"""
        mock_get_client.return_value = MagicMock()

        # Reset singleton
        import src.repositories.listing_repository as lr
        lr._listing_repository = None

        repo1 = get_listing_repository()
        repo2 = get_listing_repository()

        assert repo1 is repo2

    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    def test_image_repository_singleton(self, mock_get_client):
        """Test ImageRepository singleton"""
        mock_get_client.return_value = MagicMock()

        # Reset singleton
        import src.repositories.image_repository as ir
        ir._image_repository = None

        repo1 = get_image_repository()
        repo2 = get_image_repository()

        assert repo1 is repo2


# ============================================================================
# Model Validation Tests
# ============================================================================

class TestModels:
    """Tests for Pydantic model validation"""

    def test_listing_create_required_fields(self):
        """Test ListingCreate requires all mandatory fields"""
        listing = ListingCreate(
            vin='1HGBH41JXMN109186',
            year=2021,
            make='Honda',
            model='Civic',
            odometer=15000,
            drivetrain='FWD',
            transmission='CVT',
            engine='2.0L',
            exterior_color='Silver',
            interior_color='Black',
            condition_score=4.2,
            condition_grade='Clean'
        )

        assert listing.vin == '1HGBH41JXMN109186'
        assert listing.status == 'active'  # default value

    def test_listing_create_optional_fields(self):
        """Test ListingCreate optional fields"""
        listing = ListingCreate(
            vin='1HGBH41JXMN109186',
            year=2021,
            make='Honda',
            model='Civic',
            trim='EX',
            odometer=15000,
            drivetrain='FWD',
            transmission='CVT',
            engine='2.0L',
            exterior_color='Silver',
            interior_color='Black',
            condition_score=4.2,
            condition_grade='Clean',
            description_text='Well maintained',
            text_embedding=[0.1, 0.2, 0.3]
        )

        assert listing.trim == 'EX'
        assert listing.text_embedding == [0.1, 0.2, 0.3]

    def test_image_create_required_fields(self):
        """Test ImageCreate requires all mandatory fields"""
        image = ImageCreate(
            listing_id='test-uuid',
            vin='1HGBH41JXMN109186',
            category='hero',
            vehicle_angle='front',
            description='Front view',
            suggested_alt='Front view alt',
            quality_score=8,
            file_format='jpeg'
        )

        assert image.listing_id == 'test-uuid'
        assert image.visible_damage == []  # default value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
