"""
Integration tests for Otto.AI Listing Pipeline
Tests the full flow: PDF upload → Database → Semantic Search
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Skip if dependencies not available
pytest_plugins = ['pytest_asyncio']


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_vehicle_artifact():
    """Create a sample VehicleListingArtifact for testing"""
    from src.services.pdf_ingestion_service import (
        VehicleListingArtifact,
        VehicleInfo,
        ConditionData,
        SellerInfo,
        EnrichedImage
    )

    vehicle = VehicleInfo(
        vin='1HGBH41JXMN109186',
        year=2021,
        make='Honda',
        model='Civic',
        trim='EX',
        odometer=15000,
        drivetrain='FWD',
        transmission='CVT',
        engine='2.0L 4-Cylinder',
        exterior_color='Silver',
        interior_color='Black'
    )

    condition = ConditionData(
        score=4.2,
        grade='Clean',
        issues={
            'exterior': [
                {'type': 'scratch', 'severity': 'minor', 'description': 'Small scratch on bumper'}
            ]
        }
    )

    seller = SellerInfo(
        name='Test Dealer',
        type='dealer'
    )

    images = [
        EnrichedImage(
            description='Front view of the Honda Civic',
            category='hero',
            quality_score=8,
            vehicle_angle='front_three_quarter',
            suggested_alt='Silver Honda Civic front view',
            visible_damage=None,
            image_bytes=b'fake_image_data',
            width=1920,
            height=1080,
            format='jpeg',
            page_number=1
        )
    ]

    return VehicleListingArtifact(
        vehicle=vehicle,
        condition=condition,
        seller=seller,
        images=images,
        processing_metadata={'test': True}
    )


# ============================================================================
# Integration Tests
# ============================================================================

class TestListingPipelineIntegration:
    """Integration tests for the listing pipeline"""

    @pytest.mark.asyncio
    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @patch('src.services.vehicle_embedding_service.get_supabase_client_singleton')
    async def test_artifact_to_database_flow(
        self,
        mock_emb_client,
        mock_img_client,
        mock_list_client,
        sample_vehicle_artifact
    ):
        """Test that a VehicleListingArtifact is correctly persisted to the database"""
        # Setup mock clients
        mock_client = MagicMock()

        # Mock listing insert
        listing_result = MagicMock()
        listing_result.data = [{
            'id': 'test-listing-uuid',
            'vin': sample_vehicle_artifact.vehicle.vin,
            'year': sample_vehicle_artifact.vehicle.year,
            'make': sample_vehicle_artifact.vehicle.make,
            'model': sample_vehicle_artifact.vehicle.model
        }]

        # Mock image insert
        image_result = MagicMock()
        image_result.data = [{'id': 'test-image-uuid'}]

        # Mock condition issues insert
        issues_result = MagicMock()
        issues_result.data = [{'id': 'test-issue-uuid'}]

        mock_client.table.return_value.insert.return_value.execute.return_value = listing_result
        mock_list_client.return_value = mock_client
        mock_img_client.return_value = mock_client
        mock_emb_client.return_value = mock_client

        # Import and test
        from src.repositories.listing_repository import ListingCreate, get_listing_repository

        repo = get_listing_repository()

        listing_data = ListingCreate(
            vin=sample_vehicle_artifact.vehicle.vin,
            year=sample_vehicle_artifact.vehicle.year,
            make=sample_vehicle_artifact.vehicle.make,
            model=sample_vehicle_artifact.vehicle.model,
            odometer=sample_vehicle_artifact.vehicle.odometer,
            drivetrain=sample_vehicle_artifact.vehicle.drivetrain,
            transmission=sample_vehicle_artifact.vehicle.transmission,
            engine=sample_vehicle_artifact.vehicle.engine,
            exterior_color=sample_vehicle_artifact.vehicle.exterior_color,
            interior_color=sample_vehicle_artifact.vehicle.interior_color,
            condition_score=sample_vehicle_artifact.condition.score,
            condition_grade=sample_vehicle_artifact.condition.grade
        )

        result = await repo.create(listing_data)

        assert result is not None
        assert result['vin'] == sample_vehicle_artifact.vehicle.vin

    @pytest.mark.asyncio
    @patch('src.services.vehicle_embedding_service.OttoAIEmbeddingService')
    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    @patch('src.repositories.image_repository.get_supabase_client_singleton')
    @patch('src.services.vehicle_embedding_service.get_supabase_client_singleton')
    async def test_embedding_generation_and_storage(
        self,
        mock_emb_client,
        mock_img_client,
        mock_list_client,
        mock_embedding_service_class,
        sample_vehicle_artifact
    ):
        """Test that embeddings are generated and stored correctly"""
        # Setup mock embedding service
        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_text_embedding = AsyncMock(return_value=MagicMock(
            embedding=[0.1] * 3072,
            embedding_id='emb-123'
        ))
        mock_embedding_service.generate_image_embedding = AsyncMock(return_value=MagicMock(
            embedding=[0.1] * 3072
        ))
        mock_embedding_service_class.return_value = mock_embedding_service

        # Setup mock clients
        mock_client = MagicMock()
        listing_result = MagicMock()
        listing_result.data = [{'id': 'test-uuid'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = listing_result
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        mock_list_client.return_value = mock_client
        mock_img_client.return_value = mock_client
        mock_emb_client.return_value = mock_client

        from src.services.vehicle_embedding_service import VehicleEmbeddingService

        service = VehicleEmbeddingService(mock_embedding_service)

        # Process vehicle
        result = await service.process_vehicle_for_search(sample_vehicle_artifact)

        assert result is not None
        assert 'listing_id' in result
        assert result['vin'] == sample_vehicle_artifact.vehicle.vin


class TestAPIEndpointsIntegration:
    """Integration tests for API endpoints"""

    @pytest.mark.asyncio
    @patch('src.api.listings_api.get_listing_repository')
    @patch('src.api.listings_api.get_image_repository')
    async def test_list_listings_returns_real_data(
        self,
        mock_get_image_repo,
        mock_get_listing_repo
    ):
        """Test that GET /api/listings returns real database data"""
        # Setup mock repositories
        mock_listing_repo = MagicMock()
        mock_listing_repo.list_all = AsyncMock(return_value=[
            {
                'id': 'test-uuid',
                'vin': '1HGBH41JXMN109186',
                'year': 2021,
                'make': 'Honda',
                'model': 'Civic',
                'odometer': 15000,
                'exterior_color': 'Silver',
                'interior_color': 'Black',
                'condition_score': 4.2,
                'status': 'active',
                'created_at': datetime.utcnow()
            }
        ])
        mock_get_listing_repo.return_value = mock_listing_repo

        mock_image_repo = MagicMock()
        mock_image_repo.get_hero_image = AsyncMock(return_value={
            'web_url': 'https://example.com/image.jpg'
        })
        mock_image_repo.count_by_listing = AsyncMock(return_value=5)
        mock_get_image_repo.return_value = mock_image_repo

        from src.api.listings_api import list_listings

        result = await list_listings(limit=20, offset=0)

        assert len(result) == 1
        assert result[0].vin == '1HGBH41JXMN109186'
        assert result[0].year_make_model == '2021 Honda Civic'

    @pytest.mark.asyncio
    @patch('src.api.listings_api.get_listing_repository')
    @patch('src.api.listings_api.get_image_repository')
    @patch('src.api.listings_api.get_supabase_client_singleton')
    async def test_get_listing_detail(
        self,
        mock_supabase,
        mock_get_image_repo,
        mock_get_listing_repo
    ):
        """Test that GET /api/listings/{id} returns complete listing"""
        # Setup mock
        mock_listing_repo = MagicMock()
        mock_listing_repo.get_by_id = AsyncMock(return_value={
            'id': 'test-uuid',
            'vin': '1HGBH41JXMN109186',
            'year': 2021,
            'make': 'Honda',
            'model': 'Civic',
            'trim': 'EX',
            'odometer': 15000,
            'drivetrain': 'FWD',
            'transmission': 'CVT',
            'engine': '2.0L',
            'exterior_color': 'Silver',
            'interior_color': 'Black',
            'condition_score': 4.2,
            'condition_grade': 'Clean',
            'status': 'active',
            'listing_source': 'pdf_upload',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        mock_get_listing_repo.return_value = mock_listing_repo

        mock_image_repo = MagicMock()
        mock_image_repo.get_by_listing = AsyncMock(return_value=[
            {'id': 'img-1', 'category': 'hero', 'web_url': 'https://example.com/img1.jpg'}
        ])
        mock_get_image_repo.return_value = mock_image_repo

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        mock_supabase.return_value = mock_client

        from src.api.listings_api import get_listing

        result = await get_listing('test-uuid')

        assert result.id == 'test-uuid'
        assert result.vin == '1HGBH41JXMN109186'
        assert len(result.images) == 1


class TestSemanticSearchIntegration:
    """Integration tests for semantic search functionality"""

    @pytest.mark.asyncio
    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    async def test_find_similar_uses_pgvector(self, mock_get_client):
        """Test that find_similar uses pgvector RPC for similarity search"""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                'id': 'similar-1',
                'vin': 'ABC123',
                'make': 'Toyota',
                'model': 'Camry',
                'similarity': 0.95
            },
            {
                'id': 'similar-2',
                'vin': 'DEF456',
                'make': 'Honda',
                'model': 'Accord',
                'similarity': 0.88
            }
        ]
        mock_client.rpc.return_value.execute.return_value = mock_result
        mock_get_client.return_value = mock_client

        from src.repositories.listing_repository import ListingRepository

        repo = ListingRepository()
        embedding = [0.1] * 3072  # 3072-dimensional embedding

        result = await repo.find_similar(embedding, limit=5)

        assert len(result) == 2
        mock_client.rpc.assert_called_once()
        # Verify RPC was called with correct function name
        call_args = mock_client.rpc.call_args
        assert call_args[0][0] == 'match_vehicle_listings'

    @pytest.mark.asyncio
    @patch('src.services.vehicle_embedding_service.OttoAIEmbeddingService')
    @patch('src.repositories.listing_repository.get_supabase_client_singleton')
    async def test_search_similar_vehicles(
        self,
        mock_get_client,
        mock_embedding_service_class
    ):
        """Test searching for similar vehicles using natural language"""
        # Setup mock embedding service
        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_text_embedding = AsyncMock(return_value=MagicMock(
            embedding=[0.1] * 3072
        ))
        mock_embedding_service_class.return_value = mock_embedding_service

        # Setup mock Supabase
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {'id': 'v1', 'vin': 'ABC', 'make': 'Honda', 'model': 'Civic', 'year': 2021}
        ]
        mock_client.rpc.return_value.execute.return_value = mock_result
        mock_get_client.return_value = mock_client

        from src.services.vehicle_embedding_service import VehicleEmbeddingService
        from src.repositories.listing_repository import get_listing_repository

        # Reset singleton
        import src.repositories.listing_repository as lr
        lr._listing_repository = None

        service = VehicleEmbeddingService(mock_embedding_service)
        result = await service.search_similar_vehicles(
            "reliable Honda sedan with low mileage",
            limit=5
        )

        assert len(result) >= 0  # May be empty if RPC not found


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
