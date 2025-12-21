"""
1000 Vehicle Batch Processing Test for Story 1.2 Acceptance Criteria #4 and #5
Tests AC#4: 1000 vehicle batch processing
Tests AC#5: >50 vehicles per minute throughput
"""

import asyncio
import sys
import os
import time
import statistics
from typing import List

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

def create_test_vehicle(index: int) -> VehicleData:
    """Create a realistic test vehicle"""
    makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes", "Audi", "Volkswagen", "Hyundai"]
    models = ["Camry", "Accord", "F-150", "Silverado", "Altima", "3 Series", "C-Class", "A4", "Passat", "Elantra"]

    make = makes[index % len(makes)]
    model = models[index % len(models)]
    year = 2020 + (index % 6)  # 2020-2025
    price = 20000 + (index * 50)  # $20,000-$70,000

    # Create 0-3 images per vehicle to simulate real-world variety
    image_count = index % 4
    images = []
    image_types = [VehicleImageType.EXTERIOR, VehicleImageType.INTERIOR, VehicleImageType.DETAIL]

    for j in range(image_count):
        images.append({
            "path": f"/test/images/vehicle_{index:04d}_image_{j}.jpg",
            "type": image_types[j % len(image_types)]
        })

    # Create realistic features
    base_features = ["Bluetooth", "Backup Camera", "Cruise Control", "Power Windows", "Air Conditioning"]
    extra_features = ["Leather Seats", "Sunroof", "Navigation", "Premium Audio", "Heated Seats", "Lane Assist", "Adaptive Cruise"]

    features = base_features.copy()
    if index % 3 == 0:
        features.extend(extra_features[:index % len(extra_features)])

    return VehicleData(
        vehicle_id=f"batch-test-{index:04d}",
        make=make,
        model=model,
        year=year,
        mileage=10000 + (index * 1000),
        price=price,
        description=f"Test vehicle {index} for batch processing validation - {year} {make} {model} with {len(images)} images",
        features=features,
        specifications={
            "engine": f"{2.0 + (index % 2) + (index % 3) * 0.5}L {4 + (index % 2)}-Cylinder",
            "transmission": "Automatic" if index % 5 != 0 else "Manual",
            "fuel_economy": f"{25 + (index % 15)} MPG combined",
            "drivetrain": "FWD" if index % 4 < 2 else "AWD",
            "color": ["Black", "White", "Silver", "Gray", "Blue", "Red", "Green"][index % 7]
        },
        images=images
    )

def log_batch_progress(processed: int, total: int, percentage: float):
    """Log batch processing progress"""
    if percentage % 5 == 0 or processed == total:
        print(f"  Progress: {percentage:.1f}% ({processed}/{total} vehicles)")

async def test_ac4_1000_vehicle_batch():
    """Test AC#4: Process exactly 1000 vehicles in batch"""
    print("Testing AC#4: 1000 Vehicle Batch Processing")
    print("=" * 70)

    try:
        # Create service instance
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        print(f"Creating 1000 test vehicles...")
        vehicles = [create_test_vehicle(i) for i in range(1000)]

        print(f"Starting batch processing of 1000 vehicles...")
        print("This may take several minutes. Progress will be shown below:")
        print("-" * 50)

        # Process large batch with progress tracking
        start_time = time.time()
        result = await service.process_large_batch(vehicles)
        actual_processing_time = time.time() - start_time

        # Validate AC#4 requirements
        print(f"\n{'='*70}")
        print("AC#4 - 1000 Vehicle Batch Results:")
        print("-" * 50)
        print(f"Total Vehicles: {result.total_vehicles}")
        print(f"Successful: {result.successful_vehicles}")
        print(f"Failed: {result.failed_vehicles}")
        print(f"Success Rate: {result.successful_vehicles/result.total_vehicles*100:.1f}%")

        # AC#4: Must process 1000 vehicles
        ac4_success_rate_met = result.successful_vehicles >= 1000
        print(f"AC#4 (1000 vehicles): {'PASS' if ac4_success_rate_met else 'FAIL'} - {result.successful_vehicles} vehicles processed")

        # Calculate and validate AC#5 requirements
        vehicles_per_minute = result.vehicles_per_minute
        ac5_throughput_met = vehicles_per_minute > 50.0

        print(f"\nAC#5 - Throughput Analysis:")
        print("-" * 30)
        print(f"Throughput: {vehicles_per_minute:.1f} vehicles/minute")
        print(f"Target: >50 vehicles/minute")
        print(f"AC#5 (>50/min): {'PASS' if ac5_throughput_met else 'FAIL'}")

        # Additional performance metrics
        avg_processing_time = result.average_processing_time
        print(f"\nPerformance Metrics:")
        print(f"Average processing time per vehicle: {avg_processing_time:.3f}s")
        print(f"Total processing time: {actual_processing_time:.1f}s ({actual_processing_time/60:.1f} minutes)")
        print(f"Efficiency score: {result.successful_vehicles/result.total_vehicles*100:.1f}%")

        # Performance analysis
        if avg_processing_time < 1.0:
            speed_rating = "EXCELLENT"
        elif avg_processing_time < 1.5:
            speed_rating = "GOOD"
        elif avg_processing_time < 2.0:
            speed_rating = "ACCEPTABLE"
        else:
            speed_rating = "NEEDS_IMPROVEMENT"

        print(f"Speed Rating: {speed_rating}")

        # Overall assessment
        overall_success = ac4_success_rate_met and ac5_throughput_met

        print(f"\n{'='*70}")
        print("Overall Assessment:")
        if overall_success:
            print("SUCCESS: Both AC#4 and AC#5 requirements MET!")
            print(f"   AC#4 (1000 vehicles): PASSED")
            print(f"   AC#5 (>50/min): PASSED")
        else:
            print("PARTIAL SUCCESS: Some requirements not met")
            print(f"   AC#4 (1000 vehicles): {'PASSED' if ac4_success_rate_met else 'FAILED'}")
            print(f"   AC#5 (>50/min): {'PASSED' if ac5_throughput_met else 'FAILED'}")

        return overall_success

    except Exception as e:
        print(f"ERROR: 1000 vehicle batch test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_batch_scaling_performance():
    """Test batch processing performance with different batch sizes"""
    print("\nTesting Batch Scaling Performance")
    print("=" * 50)

    try:
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        # Test different batch sizes to find optimal performance
        batch_sizes = [100, 250, 500, 750, 1000]
        results = []

        for batch_size in batch_sizes:
            print(f"\nTesting batch size: {batch_size}")
            print("-" * 30)

            # Create test vehicles
            vehicles = [create_test_vehicle(i) for i in range(batch_size)]

            # Process batch
            start_time = time.time()
            result = await service.process_large_batch(vehicles)
            processing_time = time.time() - start_time

            throughput = result.vehicles_per_minute
            success_rate = result.successful_vehicles / batch_size * 100

            results.append({
                'batch_size': batch_size,
                'success_rate': success_rate,
                'throughput': throughput,
                'processing_time': processing_time,
                'avg_time_per_vehicle': processing_time / batch_size
            })

            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Throughput: {throughput:.1f} vehicles/min")
            print(f"  Time: {processing_time:.1f}s")
            print(f"  Avg per vehicle: {processing_time/batch_size:.3f}s")

            # Pass/fail evaluation
            status = "PASS" if success_rate >= 95 and throughput >= 50 else "FAIL"
            print(f"  Status: {status}")

        # Find optimal batch size
        print(f"\nOptimal Batch Size Analysis:")
        print("-" * 40)

        best_throughput = max(results, key=lambda x: x['throughput'])
        best_efficiency = min(results, key=lambda x: x['avg_time_per_vehicle'])
        best_overall = max(results, key=lambda x: x['throughput'] * (x['success_rate'] / 100))

        print(f"Best throughput: {best_throughput['batch_size']} vehicles @ {best_throughput['throughput']:.1f} vehicles/min")
        print(f"Best efficiency: {best_efficiency['batch_size']} vehicles @ {best_efficiency['avg_time_per_vehicle']:.3f}s per vehicle")
        print(f"Best overall: {best_overall['batch_size']} vehicles (throughput: {best_overall['throughput']:.1f} vehicles/min, success rate: {best_overall['success_rate']:.1f}%)")

        return results

    except Exception as e:
        print(f"ERROR: Batch scaling test failed: {e}")
        return []

async def main():
    """Run all 1000 vehicle batch tests"""
    print("Story 1.2 - 1000 Vehicle Batch Processing Test")
    print("Validating AC#4 (1000 vehicles) and AC#5 (>50 vehicles/min)")
    print("=" * 80)

    tests = [
        ("AC#4 & AC#5 - 1000 Vehicle Batch", test_ac4_1000_vehicle_batch),
        ("Batch Scaling Performance", test_batch_scaling_performance)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*30} {test_name} {'='*30}")
        try:
            result = await test_func()
            if result is True or (isinstance(result, list) and len(result) > 0):  # Pass for boolean or list
                passed += 1
                print(f"PASS {test_name} PASSED")
            else:
                print(f"FAIL {test_name} FAILED")
        except Exception as e:
            print(f"FAIL {test_name} FAILED with exception: {e}")

    print(f"\n{'='*80}")
    print("Test Results Summary:")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("SUCCESS: All 1000 vehicle batch tests PASSED!")
        print("PASS AC#4 requirement (1000 vehicle batch) is MET")
        print("PASS AC#5 requirement (>50 vehicles/min) is MET")
    else:
        print("WARNING: Some 1000 vehicle batch tests FAILED")
        print("FAIL AC#4 and/or AC#5 requirements may not be fully met")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)