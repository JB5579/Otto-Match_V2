"""
Integration test for Vehicle Processing Service with Database Service
Tests the complete workflow from processing to storage
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType
from vehicle_database_service import VehicleDatabaseService
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

async def test_integration():
    """Test integration between vehicle processing service and database service"""
    print("Starting Vehicle Processing Service Integration Test")

    try:
        # Create mock database connection
        mock_db_conn = Mock()
        mock_cursor = Mock()
        mock_db_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_conn.commit.return_value = None
        mock_db_conn.rollback.return_value = None

        # Mock database cursor for vehicle not found
        mock_cursor.fetchone.return_value = None

        # Initialize vehicle processing service with mocked database
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072
        service.db_conn = mock_db_conn

        # Initialize database service
        service.vehicle_db_service = VehicleDatabaseService(
            db_connection=mock_db_conn,
            embedding_dim=3072
        )

        # Mock the embedding generation methods
        service._process_vehicle_text = AsyncMock(return_value=[0.1] * 3072)
        service._process_vehicle_images = AsyncMock(return_value={
            'embeddings': [[0.2] * 3072],
            'processed_count': 2,
            'descriptions': ["Exterior description", "Interior description"]
        })
        service._process_vehicle_metadata = AsyncMock(return_value={
            'embedding': [0.3] * 3072,
            'processed': True
        })
        service._extract_semantic_tags = AsyncMock(return_value=["toyota", "camry", "sedan", "2022"])
        service._combine_embeddings = Mock(return_value=[0.5] * 3072)

        # Create test vehicle data
        vehicle_data = VehicleData(
            vehicle_id="integration-test-001",
            make="Toyota",
            model="Camry",
            year=2022,
            mileage=25000,
            price=25000.00,
            description="Clean 2022 Toyota Camry with low mileage",
            features=["Bluetooth", "Backup Camera", "Lane Assist"],
            images=[
                {"path": "/path/to/exterior.jpg", "type": VehicleImageType.EXTERIOR},
                {"path": "/path/to/interior.jpg", "type": VehicleImageType.INTERIOR}
            ]
        )

        print("✅ Test data created")

        # Process vehicle data
        result = await service.process_vehicle_data(vehicle_data)

        # Verify processing results
        assert result.success is True
        assert result.vehicle_id == "integration-test-001"
        assert len(result.embedding) == 3072
        assert result.semantic_tags == ["toyota", "camry", "sedan", "2022"]
        assert result.text_processed is True
        assert result.images_processed == 2
        assert result.metadata_processed is True

        print("✅ Vehicle processing completed successfully")

        # Verify database storage was called
        assert mock_cursor.execute.called, "Database storage should have been called"

        # Get the SQL execution calls
        execute_calls = mock_cursor.execute.call_args_list
        embedding_insert_call = None

        for call in execute_calls:
            if 'INSERT INTO vehicle_embeddings' in str(call):
                embedding_insert_call = call
                break

        assert embedding_insert_call is not None, "Should have inserted vehicle embedding"

        print("✅ Database integration verified")

        # Test batch processing integration
        vehicles = [
            VehicleData(
                vehicle_id=f"batch-test-{i:03d}",
                make="Honda",
                model="Civic",
                year=2023,
                price=22000.00,
                description=f"Batch test vehicle {i}"
            )
            for i in range(3)
        ]

        batch_result = await service.process_batch_vehicles(vehicles)

        assert batch_result.total_vehicles == 3
        assert batch_result.successful_vehicles == 3
        assert batch_result.failed_vehicles == 0
        assert len(batch_result.successful_results) == 3

        print("✅ Batch processing integration completed successfully")

        # Test database service methods directly
        db_service = service.vehicle_db_service

        # Test semantic tag search
        mock_cursor.fetchall.return_value = [
            {"vehicle_id": "tag-search-001", "vehicle_make": "Toyota", "semantic_tags": ["toyota", "camry"]},
            {"vehicle_id": "tag-search-002", "vehicle_make": "Honda", "semantic_tags": ["honda", "civic"]}
        ]

        tag_results = await db_service.search_by_semantic_tags(
            tags=["toyota", "honda"],
            match_all=False,
            limit=20
        )

        assert len(tag_results) == 2
        print("✅ Semantic tag search integration verified")

        # Test similar vehicles search
        query_embedding = [0.5] * 3072
        mock_cursor.fetchall.return_value = [
            {"vehicle_id": "similar-001", "similarity_score": 0.85, "vehicle_make": "Toyota"},
            {"vehicle_id": "similar-002", "similarity_score": 0.78, "vehicle_make": "Honda"}
        ]

        similar_results = await db_service.search_similar_vehicles(
            query_embedding=query_embedding,
            limit=10,
            similarity_threshold=0.7
        )

        assert len(similar_results) == 2
        assert similar_results[0]["similarity_score"] > similar_results[1]["similarity_score"]
        print("✅ Similarity search integration verified")

        print("\n✅ All integration tests passed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_price_range_categorization():
    """Test price range categorization logic"""
    print("\nTesting Price Range Categorization...")

    try:
        # Create service instance
        service = VehicleProcessingService()

        # Test price range categorization
        test_cases = [
            (10000, "budget"),
            (20000, "mid-range"),
            (40000, "premium"),
            (60000, "luxury"),
            (100000, "ultra-luxury")
        ]

        for price, expected_range in test_cases:
            actual_range = service._get_price_range(price)
            assert actual_range == expected_range, f"Price {price} should be {expected_range}, got {actual_range}"
            print(f"PASS ${price:,} -> {actual_range}")

        print("✅ Price range categorization test passed")
        return True

    except Exception as e:
        print(f"❌ Price range categorization test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Starting Vehicle Processing Integration Tests\n")

    tests = [
        test_integration,
        test_price_range_categorization
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"FAIL {test_func.__name__} with exception: {e}")

    print(f"\nIntegration Test Results: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)