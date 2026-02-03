"""
Simple performance validation test for AC#3: <2 seconds per vehicle
Tests without Unicode characters to avoid encoding issues
"""

import asyncio
import sys
import os
import time
import statistics

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

def create_test_vehicle(index: int) -> VehicleData:
    """Create a test vehicle with realistic data"""
    makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan"]
    models = ["Camry", "Accord", "F-150", "Silverado", "Altima"]

    make = makes[index % len(makes)]
    model = models[index % len(models)]
    year = 2020 + (index % 6)  # 2020-2025
    price = 20000 + (index * 1000)  # $20,000-$30,000

    # Create 2-3 images per vehicle
    image_count = 2 + (index % 2)
    images = []
    image_types = [VehicleImageType.EXTERIOR, VehicleImageType.INTERIOR, VehicleImageType.DETAIL]

    for j in range(image_count):
        images.append({
            "path": f"/test/images/vehicle_{index}_image_{j}.jpg",
            "type": image_types[j % len(image_types)]
        })

    return VehicleData(
        vehicle_id=f"perf-test-{index:03d}",
        make=make,
        model=model,
        year=year,
        mileage=10000 + (index * 1000),
        price=price,
        description=f"Performance test vehicle {index} - {year} {make} {model}",
        features=[f"Feature {j}" for j in range(min(5, index % 8))],
        images=images
    )

async def test_ac3_performance():
    """Test AC#3: Processing completes within <2 seconds per vehicle"""
    print("Testing AC#3: <2 seconds per vehicle requirement")
    print("=" * 60)

    try:
        # Create service instance
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        # Test with 15 vehicles to get good statistical sample
        num_vehicles = 15
        vehicles = [create_test_vehicle(i) for i in range(num_vehicles)]

        print(f"Processing {num_vehicles} vehicles...")

        processing_times = []
        successful_count = 0

        for i, vehicle in enumerate(vehicles):
            print(f"Processing vehicle {i+1}/{num_vehicles}...", end=" ")

            start_time = time.time()
            try:
                result = await service.process_vehicle_data(vehicle)
                processing_time = time.time() - start_time

                if result.success:
                    successful_count += 1
                    processing_times.append(processing_time)
                    status = "OK" if processing_time < 2.0 else "SLOW"
                    print(f"{status} {processing_time:.3f}s")
                else:
                    print(f"FAIL {result.error}")

            except Exception as e:
                processing_time = time.time() - start_time
                print(f"ERROR {e}")

        # Analyze results
        print(f"\nResults Summary:")
        print("-" * 40)
        print(f"Total vehicles: {num_vehicles}")
        print(f"Successful: {successful_count}")
        print(f"Success rate: {successful_count/num_vehicles*100:.1f}%")

        if processing_times:
            avg_time = statistics.mean(processing_times)
            min_time = min(processing_times)
            max_time = max(processing_times)
            under_2_sec = len([t for t in processing_times if t < 2.0])

            print(f"Average processing time: {avg_time:.3f}s")
            print(f"Min/Max time: {min_time:.3f}s / {max_time:.3f}s")
            print(f"Vehicles under 2s: {under_2_sec}/{len(processing_times)} ({under_2_sec/len(processing_times)*100:.1f}%)")

            # AC#3 Validation
            meets_avg_requirement = avg_time < 2.0
            meets_percent_requirement = (under_2_sec / len(processing_times)) >= 0.95
            meets_success_requirement = (successful_count / num_vehicles) >= 0.95

            print(f"\nAC#3 Validation:")
            print(f"Average time < 2s: {'PASS' if meets_avg_requirement else 'FAIL'} ({avg_time:.3f}s)")
            print(f"95% under 2s: {'PASS' if meets_percent_requirement else 'FAIL'} ({under_2_sec/len(processing_times)*100:.1f}%)")
            print(f"95% success rate: {'PASS' if meets_success_requirement else 'FAIL'} ({successful_count/num_vehicles*100:.1f}%)")

            overall_result = meets_avg_requirement and meets_percent_requirement and meets_success_requirement

            print(f"\nOverall AC#3 Result: {'PASS' if overall_result else 'FAIL'}")

            if overall_result:
                print("PASS AC#3 requirement (<2 seconds per vehicle) is MET")
            else:
                print("FAIL AC#3 requirement (<2 seconds per vehicle) is NOT MET")

            return overall_result
        else:
            print("ERROR: No successful processing")
            return False

    except Exception as e:
        print(f"ERROR: Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_caching_benefit():
    """Test caching performance benefit"""
    print("\nTesting Caching Performance Benefit")
    print("=" * 40)

    try:
        service = VehicleProcessingService()
        service.openrouter_api_key = "test-key"
        service.embedding_dim = 3072

        # Create similar vehicles for caching test
        base_vehicle = create_test_vehicle(1)
        similar_vehicles = [
            VehicleData(
                vehicle_id=f"cache-test-{i}",
                make=base_vehicle.make,
                model=base_vehicle.model,
                year=base_vehicle.year,
                price=base_vehicle.price,
                description=base_vehicle.description,
                features=base_vehicle.features,
                images=base_vehicle.images
            )
            for i in range(8)
        ]

        print("Processing similar vehicles (caching test):")

        # Process first 4 vehicles (cache misses)
        first_pass_times = []
        for i, vehicle in enumerate(similar_vehicles[:4]):
            start_time = time.time()
            result = await service.process_vehicle_data(vehicle)
            processing_time = time.time() - start_time
            first_pass_times.append(processing_time)
            print(f"  Pass 1 - Vehicle {i+1}: {processing_time:.4f}s")

        # Process next 4 vehicles (cache hits)
        second_pass_times = []
        for i, vehicle in enumerate(similar_vehicles[4:]):
            start_time = time.time()
            result = await service.process_vehicle_data(vehicle)
            processing_time = time.time() - start_time
            second_pass_times.append(processing_time)
            print(f"  Pass 2 - Vehicle {i+5}: {processing_time:.4f}s")

        if first_pass_times and second_pass_times:
            first_avg = statistics.mean(first_pass_times)
            second_avg = statistics.mean(second_pass_times)

            print(f"\nCaching Analysis:")
            print(f"First pass (cache misses): {first_avg:.4f}s")
            print(f"Second pass (cache hits): {second_avg:.4f}s")

            if first_avg > 0:
                improvement = ((first_avg - second_avg) / first_avg) * 100
                print(f"Performance improvement: {improvement:.1f}%")

            # Test performance with caching
            all_times = first_pass_times + second_pass_times
            overall_avg = statistics.mean(all_times)
            under_2_sec = len([t for t in all_times if t < 2.0])

            print(f"\nWith Caching:")
            print(f"Overall average: {overall_avg:.4f}s")
            print(f"Under 2s: {under_2_sec}/{len(all_times)} ({under_2_sec/len(all_times)*100:.1f}%)")

            return overall_avg < 2.0
        else:
            return False

    except Exception as e:
        print(f"ERROR: Caching test failed: {e}")
        return False

async def main():
    """Run performance validation tests"""
    print("Story 1.2 Performance Validation")
    print("AC#3: <2 seconds per vehicle processing")
    print("=" * 60)

    # Run tests
    test1_result = await test_ac3_performance()
    test2_result = await test_caching_benefit()

    print(f"\n{'='*60}")
    print("Performance Test Results:")
    print(f"AC#3 Performance Test: {'PASS' if test1_result else 'FAIL'}")
    print(f"Caching Performance Test: {'PASS' if test2_result else 'FAIL'}")

    overall_result = test1_result and test2_result

    if overall_result:
        print(f"\nSUCCESS: All performance tests PASSED")
        print("AC#3 requirement is MET")
    else:
        print(f"\nWARNING: Some performance tests FAILED")
        print("AC#3 requirement may need improvement")

    return overall_result

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)