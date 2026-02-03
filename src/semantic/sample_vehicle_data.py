"""
Sample Vehicle Data for Testing

Provides realistic vehicle data for testing the semantic search infrastructure.
Includes diverse vehicle types, makes, models, and features.

Story: 1.1-initialize-semantic-search-infrastructure
Task: Create sample data and testing suite (AC: #5)
"""

from typing import List, Dict, Any
import random
import json


# Sample vehicle data for testing semantic search
SAMPLE_VEHICLES = [
    {
        "vin": "1HGCM82633A123456",
        "make": "Honda",
        "model": "Accord",
        "year": 2023,
        "trim": "EX-L",
        "vehicle_type": "sedan",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "drivetrain": "front_wheel_drive",
        "engine_displacement": "1.5L",
        "horsepower": 192,
        "torque": 192,
        "exterior_color": "Platinum White Pearl",
        "interior_color": "Black",
        "num_doors": 4,
        "price": 28950,
        "msrp": 31650,
        "mileage": 12500,
        "condition": "excellent",
        "city": "Los Angeles",
        "state": "CA",
        "country": "USA",
        "description": "2023 Honda Accord EX-L in excellent condition with low mileage. Features leather seats, moonroof, premium audio system, and advanced safety features. Perfect commuter car with excellent fuel economy and reliable performance.",
        "features": [
            "leather_seats",
            "moonroof",
            "premium_audio",
            "adaptive_cruise_control",
            "lane_assist",
            "blind_spot_monitor",
            "apple_carplay",
            "android_auto",
            "heated_seats",
            "keyless_entry"
        ],
        "images": [
            "honda_accord_2023_exterior_front.jpg",
            "honda_accord_2023_interior_dashboard.jpg",
            "honda_accord_2023_side_profile.jpg"
        ],
        "title": "Clean 2023 Honda Accord EX-L - Low Mileage - Premium Features",
        "is_active": True,
        "is_available": True
    },
    {
        "vin": "2T3BF4DV9NW123457",
        "make": "Toyota",
        "model": "RAV4",
        "year": 2024,
        "trim": "Limited",
        "vehicle_type": "suv",
        "fuel_type": "hybrid",
        "transmission": "automatic",
        "drivetrain": "all_wheel_drive",
        "engine_displacement": "2.5L",
        "horsepower": 219,
        "torque": 163,
        "exterior_color": "Midnight Black Metallic",
        "interior_color": "Saddle Tan",
        "num_doors": 4,
        "price": 38995,
        "msrp": 41865,
        "mileage": 8500,
        "condition": "excellent",
        "city": "Seattle",
        "state": "WA",
        "country": "USA",
        "description": "2024 Toyota RAV4 Limited Hybrid in pristine condition with premium features. AWD capability perfect for all weather conditions. Excellent fuel efficiency from hybrid system combined with spacious SUV versatility.",
        "features": [
            "hybrid_system",
            "all_wheel_drive",
            "panoramic_sunroof",
            "jbl_premium_audio",
            "heated_steering_wheel",
            "power_liftgate",
            "toyota_safety_sense",
            "wireless_charging",
            "digital_display",
            "roof_rails"
        ],
        "images": [
            "toyota_rav4_2024_limited_black.jpg",
            "toyota_rav4_2024_interior_tan.jpg",
            "toyota_rav4_2024_rear_cargo.jpg"
        ],
        "title": "2024 Toyota RAV4 Limited Hybrid - AWD - Premium Package - Like New",
        "is_active": True,
        "is_available": True
    },
    {
        "vin": "1FTFW1ET5DFC123458",
        "make": "Ford",
        "model": "F-150",
        "year": 2013,
        "trim": "XLT",
        "vehicle_type": "truck",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "drivetrain": "four_wheel_drive",
        "engine_displacement": "3.5L V6",
        "horsepower": 365,
        "torque": 420,
        "exterior_color": "Oxford White",
        "interior_color": "Medium Stone",
        "num_doors": 4,
        "price": 24500,
        "msrp": 35900,
        "mileage": 68000,
        "condition": "good",
        "city": "Dallas",
        "state": "TX",
        "country": "USA",
        "description": "2013 Ford F-150 XLT SuperCrew with 4WD and powerful V8 engine. Well-maintained work truck with towing package and bed liner. Great for work and play with proven Ford reliability.",
        "features": [
            "four_wheel_drive",
            "towing_package",
            "bed_liner",
            "trailer_brake_controller",
            "sync_infotainment",
            "cruise_control",
            "power_windows",
            "remote_keyless_entry",
            "tow_hooks",
            "step_bars"
        ],
        "images": [
            "ford_f150_2013_xlt_white.jpg",
            "ford_f150_2013_interior.jpg",
            "ford_f150_2013_bed_view.jpg"
        ],
        "title": "2013 Ford F-150 XLT 4WD - Low Miles - Work Ready - V8 Power",
        "is_active": True,
        "is_available": True
    },
    {
        "vin": "5YJ3E1EA5MF123459",
        "make": "Tesla",
        "model": "Model 3",
        "year": 2021,
        "trim": "Long Range AWD",
        "vehicle_type": "sedan",
        "fuel_type": "electric",
        "transmission": "automatic",
        "drivetrain": "all_wheel_drive",
        "engine_displacement": "Electric",
        "horsepower": 343,
        "torque": 389,
        "exterior_color": "Deep Blue Metallic",
        "interior_color": "Black",
        "num_doors": 4,
        "price": 42999,
        "msrp": 49990,
        "mileage": 28000,
        "condition": "very_good",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "description": "2021 Tesla Model 3 Long Range AWD with Full Self-Driving capability. Premium interior with premium audio package. Excellent range and performance with zero emissions driving.",
        "features": [
            "full_self_driving",
            "premium_audio",
            "autopilot",
            "over_air_updates",
            "premium_interior",
            "glass_roof",
            "heated_seats",
            "heated_steering_wheel",
            "phone_key",
            "autopark"
        ],
        "images": [
            "tesla_model3_2021_blue.jpg",
            "tesla_model3_2021_interior.jpg",
            "tesla_model3_2021_dashboard.jpg"
        ],
        "title": "2021 Tesla Model 3 Long Range AWD - FSD - Premium - No Gas!",
        "is_active": True,
        "is_available": True
    },
    {
        "vin": "JTDKB20U993123460",
        "make": "Toyota",
        "model": "Prius",
        "year": 2009,
        "trim": "Base",
        "vehicle_type": "hatchback",
        "fuel_type": "hybrid",
        "transmission": "automatic",
        "drivetrain": "front_wheel_drive",
        "engine_displacement": "1.8L",
        "horsepower": 134,
        "torque": 105,
        "exterior_color": "Silver",
        "interior_color": "Gray",
        "num_doors": 5,
        "price": 8995,
        "msrp": 22950,
        "mileage": 125000,
        "condition": "fair",
        "city": "Portland",
        "state": "OR",
        "country": "USA",
        "description": "2009 Toyota Prius with excellent fuel economy. Reliable hybrid system with battery replacement done recently. Perfect commuter car for eco-conscious drivers looking to save on gas costs.",
        "features": [
            "hybrid_system",
            "keyless_entry",
            "cruise_control",
            "power_windows",
            "automatic_climate_control",
            "cd_player",
            "fabric_seats",
            "rear_camera",
            "bluetooth",
            "eco_mode"
        ],
        "images": [
            "toyota_prius_2009_silver.jpg",
            "toyota_prius_2009_interior.jpg",
            "toyota_prius_2009_hybrid_display.jpg"
        ],
        "title": "2009 Toyota Prius Hybrid - 50 MPG! - New Battery - Reliable Commuter",
        "is_active": True,
        "is_available": True
    },
    {
        "vin": "1C4HJXFG4MW123461",
        "make": "Jeep",
        "model": "Wrangler",
        "year": 2021,
        "trim": "Rubicon",
        "vehicle_type": "suv",
        "fuel_type": "gasoline",
        "transmission": "manual",
        "drivetrain": "four_wheel_drive",
        "engine_displacement": "3.6L V6",
        "horsepower": 285,
        "torque": 260,
        "exterior_color": "Firecracker Red",
        "interior_color": "Black",
        "num_doors": 2,
        "price": 48995,
        "msrp": 54995,
        "mileage": 18000,
        "condition": "very_good",
        "city": "Denver",
        "state": "CO",
        "country": "USA",
        "description": "2021 Jeep Wrangler Rubicon 4-door with manual transmission and legendary off-road capability. Extensively modified with premium lift kit, upgraded suspension, and off-road tires. Ready for serious trail adventures.",
        "features": [
            "four_wheel_drive",
            "rock_trac_system",
            "lift_kit",
            "offroad_tires",
            "winch",
            "led_lighting",
            "hard_top",
            "heated_seats",
            "touchscreen_infotainment",
            "offroad_camera"
        ],
        "images": [
            "jeep_wrangler_2021_rubicon_red.jpg",
            "jeep_wrangler_2021_interior.jpg",
            "jeep_wrangler_2021_offroad.jpg"
        ],
        "title": "2021 Jeep Wrangler Rubicon 4DR - Manual - Off-Road Ready - Lifted",
        "is_active": True,
        "is_available": True
    }
]


def get_random_vehicles(count: int = 3) -> List[Dict[str, Any]]:
    """Get random sample of vehicles for testing"""
    return random.sample(SAMPLE_VEHICLES, min(count, len(SAMPLE_VEHICLES)))


def get_vehicles_by_type(vehicle_type: str) -> List[Dict[str, Any]]:
    """Get vehicles filtered by type"""
    return [v for v in SAMPLE_VEHICLES if v["vehicle_type"] == vehicle_type]


def get_vehicles_by_make(make: str) -> List[Dict[str, Any]]:
    """Get vehicles filtered by make"""
    return [v for v in SAMPLE_VEHICLES if v["make"].lower() == make.lower()]


def get_vehicles_by_price_range(min_price: int, max_price: int) -> List[Dict[str, Any]]:
    """Get vehicles within price range"""
    return [v for v in SAMPLE_VEHICLES if min_price <= v["price"] <= max_price]


def create_sample_search_queries() -> List[str]:
    """Create sample search queries for testing semantic search"""
    return [
        "compact car good fuel economy",
        "family SUV with all wheel drive",
        "pickup truck for towing",
        "electric vehicle with long range",
        "luxury sedan with premium features",
        "off-road vehicle for trails",
        "affordable hybrid commuter car",
        "spacious SUV for road trips",
        "reliable work truck",
        "eco-friendly car with low emissions",
        "sports car with high performance",
        "practical hatchback with good cargo space",
        "full-size truck with crew cab",
        "convertible for summer driving",
        "minivan for large families"
    ]


def save_sample_data_to_json(file_path: str = "sample_vehicles.json"):
    """Save sample vehicle data to JSON file for testing"""
    with open(file_path, 'w') as f:
        json.dump(SAMPLE_VEHICLES, f, indent=2)
    print(f"Sample vehicle data saved to {file_path}")


# Example usage for testing
if __name__ == "__main__":
    print("Sample Vehicle Data for Semantic Search Testing")
    print("=" * 50)

    # Print basic stats
    print(f"Total sample vehicles: {len(SAMPLE_VEHICLES)}")
    print(f"Vehicle types: {set(v['vehicle_type'] for v in SAMPLE_VEHICLES)}")
    print(f"Makes available: {set(v['make'] for v in SAMPLE_VEHICLES)}")
    print(f"Price range: ${min(v['price'] for v in SAMPLE_VEHICLES):,} - ${max(v['price'] for v in SAMPLE_VEHICLES):,}")

    # Show sample search queries
    print("\nSample search queries:")
    for i, query in enumerate(create_sample_search_queries()[:5], 1):
        print(f"  {i}. {query}")

    # Save to JSON file
    save_sample_data_to_json()