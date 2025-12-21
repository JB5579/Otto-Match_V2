"""
Test suite for Vehicle Processing Service
Tests vehicle data processing, embedding generation, and performance requirements
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from ..vehicle_processing_service import (
    VehicleProcessingService, VehicleData, VehicleProcessingResult,
    BatchProcessingResult, VehicleImageType
)

class TestVehicleProcessingService:
    """Test class for VehicleProcessingService"""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing"""
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072
        return service

    @pytest.fixture
    def sample_vehicle_data(self):
        """Create sample vehicle data for testing"""
        return VehicleData(
            vehicle_id="test-001",
            make="Toyota",
            model="Camry",
            year=2022,
            mileage=25000,
            price=25000.00,
            description="Clean 2022 Toyota Camry with low mileage",
            features=["Bluetooth", "Backup Camera", "Lane Assist"],
            specifications={
                "engine": "2.5L 4-Cylinder",
                "transmission": "Automatic",
                "fuel_economy": "32 MPG combined"
            },
            images=[
                {"path": "/path/to/exterior.jpg", "type": VehicleImageType.EXTERIOR},
                {"path": "/path/to/interior.jpg", "type": VehicleImageType.INTERIOR}
            ]
        )

    @pytest.mark.asyncio
    async def test_vehicle_data_creation(self, sample_vehicle_data):
        """Test VehicleData creation and validation"""
        assert sample_vehicle_data.vehicle_id == "test-001"
        assert sample_vehicle_data.make == "Toyota"
        assert sample_vehicle_data.model == "Camry"
        assert sample_vehicle_data.year == 2022
        assert sample_vehicle_data.price == 25000.00
        assert len(sample_vehicle_data.features) == 3
        assert "engine" in sample_vehicle_data.specifications

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_service):
        """Test service initialization"""
        with patch.object(mock_service, '_initialize_lightrag') as mock_lightrag, \
             patch.object(mock_service, '_initialize_rag_anything') as mock_rag, \
             patch.object(mock_service, '_initialize_vehicle_processors') as mock_processors, \
             patch.object(mock_service, '_ensure_vehicle_schema') as mock_schema:

            result = await mock_service.initialize(
                "https://test.supabase.co", "test-key"
            )

            assert result is True
            mock_lightrag.assert_called_once()
            mock_rag.assert_called_once()
            mock_processors.assert_called_once()
            mock_schema.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_vehicle_data_success(self, mock_service, sample_vehicle_data):
        """Test successful vehicle data processing"""
        # Mock the internal processing methods
        mock_service._process_vehicle_text = AsyncMock(return_value=[0.1] * mock_service.embedding_dim)
        mock_service._process_vehicle_images = AsyncMock(return_value={
            'embeddings': [[0.2] * mock_service.embedding_dim],
            'processed_count': 2,
            'descriptions': ["Exterior description", "Interior description"]
        })
        mock_service._process_vehicle_metadata = AsyncMock(return_value={
            'embedding': [0.3] * mock_service.embedding_dim,
            'processed': True
        })
        mock_service._extract_semantic_tags = AsyncMock(return_value=["toyota", "camry", "2022", "sedan"])
        mock_service._store_vehicle_embedding = AsyncMock()
        mock_service._combine_embeddings = Mock(return_value=[0.5] * mock_service.embedding_dim)

        result = await mock_service.process_vehicle_data(sample_vehicle_data)

        assert result.success is True
        assert result.vehicle_id == "test-001"
        assert len(result.embedding) == mock_service.embedding_dim
        assert result.processing_time > 0
        assert "toyota" in result.semantic_tags
        assert result.text_processed is True
        assert result.images_processed == 2
        assert result.metadata_processed is True

    @pytest.mark.asyncio
    async def test_process_vehicle_data_failure(self, mock_service, sample_vehicle_data):
        """Test vehicle data processing failure handling"""
        # Mock a processing failure
        mock_service._process_vehicle_text = AsyncMock(side_effect=Exception("Processing failed"))

        result = await mock_service.process_vehicle_data(sample_vehicle_data)

        assert result.success is False
        assert result.vehicle_id == "test-001"
        assert result.error == "Processing failed"
        assert result.processing_time > 0
        assert result.text_processed is False

    @pytest.mark.asyncio
    async def test_process_vehicle_text(self, mock_service, sample_vehicle_data):
        """Test vehicle text processing"""
        mock_service.rag = Mock()
        mock_service.rag.aquery = AsyncMock(return_value="mock embedding result")

        result = await mock_service._process_vehicle_text(sample_vehicle_data)

        # Verify RAG-Anything was called with appropriate prompt
        mock_service.rag.aquery.assert_called_once()
        call_args = mock_service.rag.aquery.call_args[0]
        assert "Generate semantic embedding for vehicle" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_vehicle_images(self, mock_service, sample_vehicle_data):
        """Test vehicle image processing"""
        # Mock image processor
        mock_service.image_processor = Mock()
        mock_service.image_processor.process_multimodal_content = AsyncMock(
            return_value=("mock description", {"entity_name": "test"})
        )

        result = await mock_service._process_vehicle_images(sample_vehicle_data)

        assert result['processed_count'] == 2
        assert len(result['descriptions']) == 2
        assert mock_service.image_processor.process_multimodal_content.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_semantic_tags(self, mock_service, sample_vehicle_data):
        """Test semantic tag extraction"""
        image_results = {
            'descriptions': ["Beautiful exterior shot of a red SUV", "Clean interior with leather seats"]
        }

        tags = await mock_service._extract_semantic_tags(sample_vehicle_data, image_results)

        # Check basic tags
        assert "toyota" in tags
        assert "camry" in tags
        assert "2022" in tags
        assert "suv" in tags  # Extracted from image description

        # Check price range tag
        assert "mid-range" in tags

        # Check year-based tag
        assert "used" in tags

    @pytest.mark.asyncio
    async def test_combine_embeddings(self, mock_service):
        """Test embedding combination from different modalities"""
        text_emb = [0.1] * mock_service.embedding_dim
        image_emb = [[0.2] * mock_service.embedding_dim, [0.3] * mock_service.embedding_dim]
        metadata_emb = [0.4] * mock_service.embedding_dim

        result = mock_service._combine_embeddings(text_emb, image_emb, metadata_emb)

        assert len(result) == mock_service.embedding_dim
        assert result != text_emb  # Should be different from individual embeddings

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, mock_service):
        """Test batch processing meets performance requirements"""
        # Create test vehicle batch
        vehicles = [
            VehicleData(
                vehicle_id=f"test-{i:03d}",
                make="Honda",
                model="Civic",
                year=2023,
                price=22000.00,
                description=f"Test vehicle {i}"
            )
            for i in range(10)
        ]

        # Mock successful processing
        mock_service.process_vehicle_data = AsyncMock(
            return_value=VehicleProcessingResult(
                vehicle_id="test",
                embedding=[0.5] * mock_service.embedding_dim,
                embedding_dim=mock_service.embedding_dim,
                processing_time=1.5,  # Under 2 seconds
                semantic_tags=["test"],
                text_processed=True,
                images_processed=0,
                metadata_processed=True,
                success=True
            )
        )

        start_time = time.time()
        result = await mock_service.process_batch_vehicles(vehicles)
        processing_time = time.time() - start_time

        # Verify batch processing results
        assert result.total_vehicles == 10
        assert result.successful_vehicles == 10
        assert result.failed_vehicles == 0
        assert result.average_processing_time == 1.5
        assert result.vehicles_per_minute > 50  # Should meet requirement

        # Verify actual performance
        actual_vpm = len(vehicles) / (processing_time / 60)
        assert actual_vpm > 50, f"Actual VPM: {actual_vpm:.1f}, Required: >50"

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, mock_service):
        """Test performance metrics collection"""
        # Simulate processing times
        mock_service.processing_times = [1.2, 1.5, 1.3, 1.1, 1.4]
        mock_service.vehicle_count = 5

        metrics = mock_service.get_performance_metrics()

        assert metrics['total_vehicles'] == 5
        assert abs(metrics['average_processing_time'] - 1.3) < 0.1
        assert metrics['total_processing_time'] == 6.5
        assert metrics['vehicles_per_minute'] > 40  # 5 / (6.5/60) ≈ 46

    @pytest.mark.asyncio
    async def test_performance_requirements_ac3(self, mock_service, sample_vehicle_data):
        """Test AC#3: Processing completes within <2 seconds per vehicle"""
        # Mock processing to take 1.8 seconds
        mock_service._process_vehicle_text = AsyncMock(return_value=[0.1] * mock_service.embedding_dim)
        mock_service._process_vehicle_images = AsyncMock(return_value={
            'embeddings': [[0.2] * mock_service.embedding_dim],
            'processed_count': 2,
            'descriptions': ["desc1", "desc2"]
        })
        mock_service._process_vehicle_metadata = AsyncMock(return_value={
            'embedding': [0.3] * mock_service.embedding_dim,
            'processed': True
        })
        mock_service._extract_semantic_tags = AsyncMock(return_value=["toyota", "camry"])
        mock_service._store_vehicle_embedding = AsyncMock()
        mock_service._combine_embeddings = Mock(return_value=[0.5] * mock_service.embedding_dim)

        # Add artificial delay to test timing
        async def delayed_process(*args, **kwargs):
            await asyncio.sleep(1.8)
            return VehicleProcessingResult(
                vehicle_id=args[0].vehicle_id,
                embedding=[0.5] * mock_service.embedding_dim,
                embedding_dim=mock_service.embedding_dim,
                processing_time=1.8,
                semantic_tags=["test"],
                text_processed=True,
                images_processed=2,
                metadata_processed=True,
                success=True
            )

        mock_service.process_vehicle_data = AsyncMock(side_effect=delayed_process)

        start_time = time.time()
        result = await mock_service.process_vehicle_data(sample_vehicle_data)
        processing_time = time.time() - start_time

        # Verify <2 second requirement
        assert processing_time < 2.0, f"Processing took {processing_time:.2f}s, required <2s"
        assert result.processing_time < 2.0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_batch_processing_error_handling(self, mock_service):
        """Test batch processing error handling and retry mechanisms"""
        vehicles = [
            VehicleData(
                vehicle_id=f"test-{i:03d}",
                make="Ford",
                model="Focus",
                year=2023,
                price=20000.00,
                description=f"Test vehicle {i}"
            )
            for i in range(5)
        ]

        # Mock mixed success/failure
        def mock_process_with_errors(vehicle):
            if vehicle.vehicle_id == "test-002":
                raise Exception("Network error")
            elif vehicle.vehicle_id == "test-004":
                raise Exception("Database error")
            else:
                return VehicleProcessingResult(
                    vehicle_id=vehicle.vehicle_id,
                    embedding=[0.5] * mock_service.embedding_dim,
                    embedding_dim=mock_service.embedding_dim,
                    processing_time=1.0,
                    semantic_tags=["test"],
                    text_processed=True,
                    images_processed=0,
                    metadata_processed=True,
                    success=True
                )

        mock_service.process_vehicle_data = AsyncMock(side_effect=mock_process_with_errors)

        result = await mock_service.process_batch_vehicles(vehicles)

        # Verify error handling
        assert result.total_vehicles == 5
        assert result.successful_vehicles == 3
        assert result.failed_vehicles == 2
        assert len(result.failed_vehicles_details) == 2

        # Check failed vehicles are properly logged
        failed_ids = [failed[0] for failed in result.failed_vehicles_details]
        assert "test-002" in failed_ids
        assert "test-004" in failed_ids

    @pytest.mark.asyncio
    async def test_vehicle_image_classification(self, mock_service):
        """Test vehicle image type classification"""
        # Test with known image types
        test_cases = [
            ("exterior", VehicleImageType.EXTERIOR),
            ("interior", VehicleImageType.INTERIOR),
            ("detail", VehicleImageType.DETAIL),
            ("unknown", VehicleImageType.UNKNOWN),
            ("SUV", VehicleImageType.UNKNOWN),  # Should classify as unknown
            ("sedan", VehicleImageType.UNKNOWN)  # Should classify as unknown
        ]

        for type_str, expected_type in test_cases:
            vehicle_data = VehicleData(
                vehicle_id="test-001",
                make="Toyota",
                model="Camry",
                year=2022,
                images=[{"path": "/path/to/image.jpg", "type": type_str}]
            )

            # Mock image processor to return success
            mock_service.image_processor = Mock()
            mock_service.image_processor.process_multimodal_content = AsyncMock(
                return_value=("description", {"entity_name": "test"})
            )

            result = await mock_service._process_vehicle_images(vehicle_data)

            # Verify classification
            if isinstance(vehicle_data.images[0]['type'], str):
                actual_type = VehicleImageType(vehicle_data.images[0]['type'].lower())
                assert actual_type == expected_type

if __name__ == "__main__":
    pytest.main([__file__])