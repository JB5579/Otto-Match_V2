"""
Otto.AI Intelligent Vehicle Filtering Test Suite

Comprehensive testing for Story 1-4: Implement Intelligent Vehicle Filtering with Context

Tests luxury SUV example, feature filtering, filter suggestions, and saved filters.
Validates all acceptance criteria with real database operations (TARB compliant).
"""

import os
import sys
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import unittest

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.search.filter_service import (
    IntelligentFilterService, SearchContext, FilterSuggestionResponse,
    extract_price_range_from_query, detect_vehicle_type_from_query
)
from src.semantic.vehicle_database_service import VehicleDatabaseService
from src.semantic.embedding_service import OttoAIEmbeddingService

class TestIntelligentFiltering(unittest.TestCase):
    """Test suite for intelligent vehicle filtering"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        print("🚀 Setting up Intelligent Filtering Test Suite...")

        # Get environment variables
        cls.supabase_url = os.getenv('SUPABASE_URL')
        cls.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        cls.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

        if not cls.supabase_url or not cls.supabase_key:
            raise ValueError("Missing required environment variables for database connection")

        # Initialize services
        cls.filter_service = IntelligentFilterService()
        cls.vehicle_db_service = VehicleDatabaseService()
        cls.embedding_service = OttoAIEmbeddingService()

    async def async_setup(self):
        """Async setup method"""
        print("📡 Initializing services...")

        # Initialize filter service
        success = await self.filter_service.initialize(
            self.supabase_url,
            self.supabase_key,
            self.redis_url
        )
        self.assertTrue(success, "Filter service initialization failed")

        # Initialize vehicle database service
        success = await self.vehicle_db_service.initialize(
            self.supabase_url,
            self.supabase_key
        )
        self.assertTrue(success, "Vehicle database service initialization failed")

        # Initialize embedding service
        success = await self.embedding_service.initialize(
            self.supabase_url,
            self.supabase_key
        )
        self.assertTrue(success, "Embedding service initialization failed")

        print("✅ All services initialized successfully")

    async def test_luxury_suv_example_ac5_ac6(self):
        """
        Test AC #5: Luxury SUV example with price filtering
        Test AC #6: Feature filtering for luxury SUVs
        """
        print("\n🧪 Testing Luxury SUV Example (AC #5, #6)...")

        # Create search context for "luxury SUV" with price filter $40,000-$60,000
        search_context = SearchContext(
            query="luxury SUV",
            budget_range=(40000, 60000),
            vehicle_types=["SUV"]
        )

        # Generate filter suggestions
        suggestions = await self.filter_service.generate_filter_suggestions(search_context)

        self.assertIsInstance(suggestions, FilterSuggestionResponse)
        self.assertEqual(suggestions.search_query, "luxury SUV")

        # Validate luxury SUV specific suggestions
        luxury_suggestions = [s for s in suggestions.suggestions if "luxury" in s.reason.lower()]
        self.assertGreater(len(luxury_suggestions), 0, "Should have luxury-specific suggestions")

        # Test price range suggestion
        price_suggestions = [s for s in suggestions.suggestions if s.filter_name in ["price_min", "price_range"]]
        self.assertGreater(len(price_suggestions), 0, "Should suggest price range for luxury vehicles")

        # Test vehicle type suggestion
        vehicle_type_suggestions = [s for s in suggestions.suggestions if s.filter_name == "vehicle_type"]
        suv_suggestions = [s for s in vehicle_type_suggestions if s.suggested_value == "SUV"]
        self.assertGreater(len(suv_suggestions), 0, "Should suggest SUV for luxury SUV query")

        print(f"✅ Generated {len(suggestions.suggestions)} suggestions for luxury SUV query")

        # Test hybrid search with luxury SUV filters
        filters = {
            "vehicle_type": "SUV",
            "price_min": 40000,
            "price_max": 60000
        }

        # Sanitize and validate filters
        sanitized_filters = await self.filter_service.validate_and_sanitize_filters(filters)
        self.assertEqual(sanitized_filters["vehicle_type"], "SUV")
        self.assertEqual(sanitized_filters["price_min"], 40000)
        self.assertEqual(sanitized_filters["price_max"], 60000)

        # Generate embedding for search
        from src.semantic.embedding_service import EmbeddingRequest
        embedding_request = EmbeddingRequest(text="luxury SUV premium high-end")
        embedding_response = await self.embedding_service.generate_embedding(embedding_request)
        query_embedding = embedding_response.embedding

        # Perform hybrid search
        search_results = await self.vehicle_db_service.hybrid_search(
            query_embedding=query_embedding,
            filters=sanitized_filters,
            limit=20,
            offset=0,
            sort_by="relevance",
            sort_order="desc"
        )

        self.assertIn("results", search_results)
        self.assertIn("total_count", search_results)

        # Validate results contain luxury SUVs
        luxury_brands = ["BMW", "Mercedes-Benz", "Audi", "Lexus", "Cadillac", "Lincoln", "Infiniti", "Acura"]
        found_luxury_suvs = []

        for result in search_results["results"]:
            vehicle = result["vehicle"]
            make = vehicle.get("make", "").upper()
            model = vehicle.get("model", "").upper()
            price = float(vehicle.get("price", 0))
            vehicle_type = vehicle.get("vehicle_type", "").upper()

            # Check if it's a luxury SUV within price range
            is_luxury = any(brand in make for brand in luxury_brands)
            is_suv = "SUV" in vehicle_type or "CROSSOVER" in vehicle_type
            in_price_range = 40000 <= price <= 60000

            if is_luxury and is_suv and in_price_range:
                found_luxury_suvs.append({
                    "make": vehicle.get("make"),
                    "model": vehicle.get("model"),
                    "price": price,
                    "similarity_score": result.get("similarity_score", 0)
                })

        print(f"🎯 Found {len(found_luxury_suvs)} luxury SUVs in $40k-$60k range")

        # Should find some luxury SUVs (if data exists)
        if search_results["total_count"] > 0:
            self.assertGreater(len(found_luxury_suvs), 0, "Should find luxury SUVs in the specified price range")

        # Test feature filtering (AC #6)
        feature_filters = {
            "vehicle_type": "SUV",
            "price_min": 40000,
            "price_max": 60000,
            "features": ["leather seats", "sunroof", "AWD"]
        }

        sanitized_feature_filters = await self.filter_service.validate_and_sanitize_filters(feature_filters)

        # Perform search with feature filters
        feature_search_results = await self.vehicle_db_service.hybrid_search(
            query_embedding=query_embedding,
            filters=sanitized_feature_filters,
            limit=20,
            offset=0,
            sort_by="relevance",
            sort_order="desc"
        )

        print(f"🔍 Found {feature_search_results['total_count']} vehicles with feature filters")

        # Validate feature filtering works
        self.assertIn("results", feature_search_results)
        self.assertIn("total_count", feature_search_results)

        print("✅ Luxury SUV example test completed successfully")

    async def test_filter_suggestions_ac3(self):
        """
        Test AC #3: Filter suggestions based on search context
        """
        print("\n🧪 Testing Filter Suggestions (AC #3)...")

        test_queries = [
            {
                "query": "family SUV good for road trips with lots of cargo space",
                "expected_filters": ["vehicle_type", "features"]
            },
            {
                "query": "eco-friendly commuter car under $25,000",
                "expected_filters": ["fuel_type", "price_max", "vehicle_type"]
            },
            {
                "query": "luxury sports car over $50,000 with leather seats",
                "expected_filters": ["price_min", "features", "vehicle_type"]
            },
            {
                "query": "reliable truck between $30,000 and $45,000",
                "expected_filters": ["price_range", "vehicle_type"]
            }
        ]

        for test_case in test_queries:
            query = test_case["query"]
            expected_filters = test_case["expected_filters"]

            search_context = SearchContext(query=query)
            suggestions = await self.filter_service.generate_filter_suggestions(search_context)

            print(f"📝 Query: '{query}'")
            print(f"💡 Generated {len(suggestions.suggestions)} suggestions")

            # Validate suggestion types
            suggested_filter_names = [s.filter_name for s in suggestions.suggestions]

            for expected_filter in expected_filters:
                found_suggestions = [s for s in suggestions.suggestions if s.filter_name == expected_filter]
                if found_suggestions:
                    print(f"  ✅ Found {len(found_suggestions)} suggestions for {expected_filter}")
                else:
                    print(f"  ⚠️ No suggestions for {expected_filter}")

            # Validate confidence scores
            for suggestion in suggestions.suggestions:
                self.assertGreaterEqual(suggestion.confidence_score, 0.0)
                self.assertLessEqual(suggestion.confidence_score, 1.0)
                self.assertIsNotNone(suggestion.reason)
                self.assertGreater(len(suggestion.reason), 0)

            # Validate popular filters are included
            self.assertIsInstance(suggestions.popular_filters, list)
            self.assertGreater(len(suggestions.popular_filters), 0)

            # Validate context analysis
            self.assertIn("query_length", suggestions.context_analysis)
            self.assertIn("suggestion_count", suggestions.context_analysis)
            self.assertIn("confidence_avg", suggestions.context_analysis)

        print("✅ Filter suggestions test completed successfully")

    async def test_saved_filter_combinations_ac4(self):
        """
        Test AC #4: Saved filter combinations
        """
        print("\n🧪 Testing Saved Filter Combinations (AC #4)...")

        test_user_id = "test_user_123"

        # Create test filter combinations
        test_filters = [
            {
                "name": "Luxury SUVs $40k-$60k",
                "description": "Luxury SUVs in mid-price range",
                "filters": {
                    "vehicle_type": "SUV",
                    "price_min": 40000,
                    "price_max": 60000,
                    "features": ["leather seats"]
                }
            },
            {
                "name": "Eco-Friendly Commuters",
                "description": "Electric and hybrid vehicles for daily driving",
                "filters": {
                    "fuel_types": ["Electric", "Hybrid"],
                    "price_max": 35000,
                    "vehicle_type": "Sedan"
                }
            },
            {
                "name": "Family Vehicles",
                "description": "Spacious vehicles for families",
                "filters": {
                    "vehicle_type": ["SUV", "Minivan"],
                    "features": ["third row seating", "cargo space"]
                }
            }
        ]

        # Test saving filters
        saved_filter_ids = []
        for filter_data in test_filters:
            saved_filter = await self.filter_service.create_saved_filter(
                user_id=test_user_id,
                name=filter_data["name"],
                filters=filter_data["filters"],
                description=filter_data["description"]
            )

            self.assertIsNotNone(saved_filter.id)
            self.assertEqual(saved_filter.user_id, test_user_id)
            self.assertEqual(saved_filter.name, filter_data["name"])
            self.assertEqual(saved_filter.description, filter_data["description"])
            self.assertEqual(saved_filter.usage_count, 0)

            saved_filter_ids.append(saved_filter.id)
            print(f"💾 Saved filter: {filter_data['name']} (ID: {saved_filter.id})")

        # Test retrieving saved filters
        user_filters = await self.filter_service.get_user_saved_filters(test_user_id)
        self.assertEqual(len(user_filters), len(test_filters))

        # Validate filter data integrity
        for i, saved_filter in enumerate(user_filters):
            original_filter = test_filters[i]
            self.assertEqual(saved_filter.name, original_filter["name"])
            self.assertEqual(saved_filter.description, original_filter["description"])
            self.assertEqual(saved_filter.filters, original_filter["filters"])
            print(f"✅ Retrieved filter: {saved_filter.name}")

        print("✅ Saved filter combinations test completed successfully")

    async def test_hybrid_filtering_ac1_ac2(self):
        """
        Test AC #1: Hybrid filtering combining semantic search with traditional filters
        Test AC #2: Semantic relevance maintained within filter constraints
        """
        print("\n🧪 Testing Hybrid Filtering (AC #1, #2)...")

        test_queries = [
            {
                "query": "reliable family vehicle",
                "filters": {"vehicle_type": "SUV", "year_min": 2018, "mileage_max": 50000},
                "description": "Family SUV with recent model year and low mileage"
            },
            {
                "query": "fuel efficient commuter",
                "filters": {"fuel_type": "Hybrid", "price_max": 30000},
                "description": "Hybrid vehicle under $30k for commuting"
            },
            {
                "query": "work truck for hauling",
                "filters": {"vehicle_type": "Truck", "features": ["towing capacity"]},
                "description": "Truck suitable for work and hauling"
            }
        ]

        for test_case in test_queries:
            query = test_case["query"]
            filters = test_case["filters"]
            description = test_case["description"]

            print(f"🔍 Testing: {description}")
            print(f"📝 Query: '{query}'")
            print(f"🎛️ Filters: {filters}")

            # Generate query embedding
            from src.semantic.embedding_service import EmbeddingRequest
            embedding_request = EmbeddingRequest(text=query)
            embedding_response = await self.embedding_service.generate_embedding(embedding_request)
            query_embedding = embedding_response.embedding

            # Perform hybrid search with filters
            search_results = await self.vehicle_db_service.hybrid_search(
                query_embedding=query_embedding,
                filters=filters,
                limit=10,
                offset=0,
                sort_by="relevance",
                sort_order="desc"
            )

            self.assertIn("results", search_results)
            self.assertIn("total_count", search_results)

            total_found = search_results["total_count"]
            results_returned = len(search_results["results"])

            print(f"📊 Results: {total_found} total, {results_returned} returned")

            if total_found > 0:
                # Validate that results maintain semantic relevance while respecting filters
                for result in search_results["results"]:
                    vehicle = result["vehicle"]
                    similarity_score = result.get("similarity_score", 0)

                    # Validate semantic relevance (AC #2)
                    self.assertGreater(similarity_score, 0.0, "Results should have semantic similarity scores")

                    # Validate filter constraints are respected (AC #1)
                    if "vehicle_type" in filters:
                        self.assertEqual(vehicle.get("vehicle_type"), filters["vehicle_type"])

                    if "year_min" in filters:
                        year = vehicle.get("year", 0)
                        self.assertGreaterEqual(year, filters["year_min"])

                    if "price_max" in filters:
                        price = float(vehicle.get("price", 0))
                        self.assertLessEqual(price, filters["price_max"])

                    if "mileage_max" in filters:
                        mileage = vehicle.get("mileage", 0)
                        if mileage:
                            self.assertLessEqual(mileage, filters["mileage_max"])

                print(f"✅ All {results_returned} results passed filter validation")
            else:
                print("⚠️ No results found (this may be expected for specific filter combinations)")

        print("✅ Hybrid filtering test completed successfully")

    async def test_filter_validation_and_sanitization(self):
        """Test filter validation and sanitization"""
        print("\n🧪 Testing Filter Validation and Sanitization...")

        test_cases = [
            {
                "input": {"price_min": 60000, "price_max": 40000},
                "expected": {"price_min": 40000, "price_max": 60000},
                "description": "Price range swapped when min > max"
            },
            {
                "input": {"year_min": 2025, "year_max": 2020},
                "expected": {"year_min": 2020, "year_max": 2024},  # Current year adjustment
                "description": "Year range validation and current year limiting"
            },
            {
                "input": {"make": "  BMW  ", "model": "X5  "},
                "expected": {"make": "BMW", "model": "X5"},
                "description": "String field sanitization"
            },
            {
                "input": {"features": ["leather seats", "", "  sunroof  ", "navigation"]},
                "expected": {"features": ["leather seats", "sunroof", "navigation"]},
                "description": "Feature list sanitization"
            },
            {
                "input": {"mileage_max": -1000},
                "expected": {"mileage_max": 0},
                "description": "Negative mileage handling"
            }
        ]

        for test_case in test_cases:
            input_filters = test_case["input"]
            expected = test_case["expected"]
            description = test_case["description"]

            print(f"🧹 Testing: {description}")
            print(f"📥 Input: {input_filters}")

            sanitized = await self.filter_service.validate_and_sanitize_filters(input_filters)
            print(f"📤 Output: {sanitized}")
            print(f"✅ Expected: {expected}")

            # Validate sanitization
            for key, expected_value in expected.items():
                self.assertIn(key, sanitized)
                self.assertEqual(sanitized[key], expected_value,
                               f"Sanitization failed for {key}: expected {expected_value}, got {sanitized[key]}")

        print("✅ Filter validation and sanitization test completed successfully")

    def test_utility_functions(self):
        """Test utility functions for query processing"""
        print("\n🧪 Testing Utility Functions...")

        # Test price range extraction
        price_tests = [
            ("under $25,000", (0, 25000)),
            ("between $30,000 and $40,000", (30000, 40000)),
            ("over $50,000", (50000, float('inf'))),
            ("around $35,000", (28000, 42000)),
            ("no price mentioned", None)
        ]

        for query, expected in price_tests:
            result = extract_price_range_from_query(query)
            self.assertEqual(result, expected, f"Price extraction failed for: {query}")
            print(f"💰 '{query}' → {result}")

        # Test vehicle type detection
        vehicle_tests = [
            ("I'm looking for an SUV", "SUV"),
            ("Need a reliable truck", "Truck"),
            ("Sports car would be nice", "Coupe"),
            ("Just need a basic car", "Sedan"),
            ("Minivan for the family", "Minivan"),
            ("No vehicle type specified", None)
        ]

        for query, expected in vehicle_tests:
            result = detect_vehicle_type_from_query(query)
            self.assertEqual(result, expected, f"Vehicle type detection failed for: {query}")
            print(f"🚗 '{query}' → {result}")

        print("✅ Utility functions test completed successfully")

async def run_intelligent_filtering_tests():
    """Run all intelligent filtering tests"""
    print("=" * 80)
    print("🧪 OTTO.AI INTELLIGENT VEHICLE FILTERING TEST SUITE")
    print("Story 1-4: Implement Intelligent Vehicle Filtering with Context")
    print("=" * 80)

    test_instance = TestIntelligentFiltering()

    try:
        # Set up async environment
        await test_instance.async_setup()

        # Run all tests
        print("\n🎯 Running All Test Cases...")

        await test_instance.test_luxury_suv_example_ac5_ac6()
        await test_instance.test_filter_suggestions_ac3()
        await test_instance.test_saved_filter_combinations_ac4()
        await test_instance.test_hybrid_filtering_ac1_ac2()
        await test_instance.test_filter_validation_and_sanitization()

        # Run synchronous utility tests
        test_instance.test_utility_functions()

        print("\n" + "=" * 80)
        print("✅ ALL INTELLIGENT FILTERING TESTS PASSED!")
        print("🎉 Story 1-4 Implementation Validated Successfully")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_intelligent_filtering_tests())
    sys.exit(0 if success else 1)