"""
Service functionality test for vehicle processing service
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

async def test_service_initialization():
    """Test service initialization"""
    print("Testing Service Initialization...")

    try:
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        print(f"PASS Service created with embedding dimension: {service.embedding_dim}")
        return True
    except Exception as e:
        print(f"FAIL Service initialization failed: {e}")
        return False

async def test_vehicle_processing_methods():
    """Test vehicle processing methods exist and are callable"""
    print("\nTesting Vehicle Processing Methods...")

    try:
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        # Create sample vehicle
        vehicle = VehicleData(
            vehicle_id="test-001",
            make="Toyota",
            model="Camry",
            year=2022,
            mileage=25000,
            price=25000.00,
            description="Clean 2022 Toyota Camry with low mileage",
            features=["Bluetooth", "Backup Camera"],
            images=[{"path": "/path/to/image.jpg", "type": VehicleImageType.EXTERIOR}]
        )

        # Test that methods exist
        assert hasattr(service, 'process_vehicle_data')
        assert hasattr(service, 'process_batch_vehicles')
        assert hasattr(service, '_process_vehicle_text')
        assert hasattr(service, '_process_vehicle_images')
        assert hasattr(service, '_process_vehicle_metadata')
        assert hasattr(service, '_extract_semantic_tags')
        assert hasattr(service, '_combine_embeddings')

        print("PASS All required methods exist")
        return True
    except Exception as e:
        print(f"FAIL Method testing failed: {e}")
        return False

async def test_database_schema():
    """Test database schema creation"""
    print("\nTesting Database Schema...")

    try:
        service = VehicleProcessingService()

        # Test schema method exists and returns SQL
        schema_sql = service._get_vehicle_schema_sql()
        assert isinstance(schema_sql, str)
        assert "CREATE TABLE" in schema_sql
        assert "vehicle_embeddings" in schema_sql
        assert "VECTOR" in schema_sql  # pgvector uses VECTOR type

        print("PASS Database schema SQL generated successfully")
        print(f"Schema contains {schema_sql.count('CREATE TABLE')} table definitions")
        return True
    except Exception as e:
        import traceback
        print(f"FAIL Database schema test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run service functionality tests"""
    print("Starting Vehicle Processing Service Tests\n")

    tests = [
        test_service_initialization,
        test_vehicle_processing_methods,
        test_database_schema
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

    print(f"\nTest Results: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)