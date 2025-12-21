"""
Basic functionality test for vehicle processing service
"""

from vehicle_processing_service import VehicleData, VehicleImageType

def test_vehicle_data_creation():
    """Test basic vehicle data creation"""
    print("Testing Vehicle Data Creation...")

    # Create sample vehicle data
    vehicle = VehicleData(
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

    # Validate data
    assert vehicle.vehicle_id == "test-001"
    assert vehicle.make == "Toyota"
    assert vehicle.model == "Camry"
    assert vehicle.year == 2022
    assert vehicle.price == 25000.00
    assert len(vehicle.features) == 3
    assert "engine" in vehicle.specifications
    assert len(vehicle.images) == 2

    print(f"PASS Vehicle ID: {vehicle.vehicle_id}")
    print(f"PASS Make: {vehicle.make}")
    print(f"PASS Model: {vehicle.model}")
    print(f"PASS Year: {vehicle.year}")
    print(f"PASS Price: ${vehicle.price:,.2f}")
    print(f"PASS Features: {vehicle.features}")
    print(f"PASS Images: {len(vehicle.images)} images")

    return True

def test_image_types():
    """Test vehicle image type enumeration"""
    print("\nTesting Vehicle Image Types...")

    # Test all image types
    assert VehicleImageType.EXTERIOR.value == "exterior"
    assert VehicleImageType.INTERIOR.value == "interior"
    assert VehicleImageType.DETAIL.value == "detail"
    assert VehicleImageType.UNKNOWN.value == "unknown"

    # Test image type creation from string
    exterior_type = VehicleImageType("exterior")
    assert exterior_type == VehicleImageType.EXTERIOR

    print("PASS All image types working correctly")
    return True

def main():
    """Run basic functionality tests"""
    print("Starting Basic Vehicle Processing Service Tests\n")

    try:
        test_vehicle_data_creation()
        test_image_types()
        print("\nPASS All basic tests passed successfully!")
        return True
    except Exception as e:
        print(f"\nFAIL Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)