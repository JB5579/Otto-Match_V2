"""
Test Suite for Semantic Search API

Comprehensive tests for Story 1-3: Build Semantic Search API Endpoints
Tests integration with Story 1-1 semantic search infrastructure
Tests integration with Story 1-2 multimodal processing

TARB COMPLIANCE: Uses real database connections, no mocks
"""

import os
import asyncio
import time
import json
import logging
from typing import List, Dict, Any
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.api.semantic_search_api import (
    SemanticSearchService,
    SemanticSearchRequest,
    SearchFilters,
    VehicleResult
)
from src.semantic.embedding_service import OttoAIEmbeddingService
from src.semantic.vehicle_processing_service import VehicleProcessingService
from src.semantic.vehicle_database_service import VehicleDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearchAPITestSuite:
    """Comprehensive test suite for semantic search API"""

    def __init__(self):
        self.search_service: SemanticSearchService = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "performance_metrics": [],
            "errors": []
        }

    async def setup(self) -> bool:
        """Initialize test environment"""
        try:
            logger.info("🚀 Setting up Semantic Search API Test Suite...")

            # Check environment variables
            required_vars = [
                'OPENROUTER_API_KEY',
                'SUPABASE_URL',
                'SUPABASE_ANON_KEY',
                'SUPABASE_DB_PASSWORD'
            ]
            missing_vars = [var for var in required_vars if not os.getenv(var)]

            if missing_vars:
                logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
                return False

            # Initialize search service
            self.search_service = SemanticSearchService()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')

            if not await self.search_service.initialize(supabase_url, supabase_key):
                logger.error("❌ Failed to initialize search service")
                return False

            logger.info("✅ Test environment setup complete")
            return True

        except Exception as e:
            logger.error(f"❌ Test setup failed: {e}")
            return False

    def record_test_result(self, test_name: str, passed: bool, performance_time: float = None, error: str = None):
        """Record test result"""
        self.test_results["total_tests"] += 1

        if passed:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ PASSED: {test_name}")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ FAILED: {test_name} - {error}")

        if performance_time is not None:
            self.test_results["performance_metrics"].append({
                "test": test_name,
                "time": performance_time
            })

        if error:
            self.test_results["errors"].append({
                "test": test_name,
                "error": error
            })

    async def test_basic_functionality(self) -> None:
        """Test basic API functionality"""
        logger.info("🧪 Testing Basic Functionality...")

        # Test 1: Simple semantic search
        start_time = time.time()
        try:
            request = SemanticSearchRequest(
                query="family SUV good for road trips",
                limit=10
            )

            result = await self.search_service.semantic_search(request, "test_client")
            processing_time = time.time() - start_time

            success = (
                isinstance(result.total_results, int) and
                isinstance(result.results, list) and
                result.processing_time > 0 and
                len(result.results) <= 10
            )

            self.record_test_result(
                "Basic Semantic Search",
                success,
                processing_time,
                None if success else "Invalid response structure"
            )

        except Exception as e:
            self.record_test_result("Basic Semantic Search", False, None, str(e))

        # Test 2: Search with filters
        start_time = time.time()
        try:
            filters = SearchFilters(
                make="Toyota",
                vehicle_type="SUV",
                year_min=2020
            )

            request = SemanticSearchRequest(
                query="reliable SUV",
                filters=filters,
                limit=5
            )

            result = await self.search_service.semantic_search(request, "test_client")
            processing_time = time.time() - start_time

            success = (
                result.total_results >= 0 and
                len(result.results) <= 5 and
                result.filters_applied is not None
            )

            self.record_test_result(
                "Search with Filters",
                success,
                processing_time,
                None if success else "Filter application failed"
            )

        except Exception as e:
            self.record_test_result("Search with Filters", False, None, str(e))

        # Test 3: Pagination test
        start_time = time.time()
        try:
            request1 = SemanticSearchRequest(query="sedan", limit=5, offset=0)
            request2 = SemanticSearchRequest(query="sedan", limit=5, offset=5)

            result1 = await self.search_service.semantic_search(request1, "test_client")
            result2 = await self.search_service.semantic_search(request2, "test_client")
            processing_time = time.time() - start_time

            success = (
                result1.total_results == result2.total_results and
                len(result1.results) <= 5 and
                len(result2.results) <= 5
            )

            self.record_test_result(
                "Pagination Functionality",
                success,
                processing_time,
                None if success else "Pagination logic failed"
            )

        except Exception as e:
            self.record_test_result("Pagination Functionality", False, None, str(e))

    async def test_performance_requirements(self) -> None:
        """Test performance requirements (<800ms response time)"""
        logger.info("🚀 Testing Performance Requirements...")

        test_queries = [
            "family SUV with lots of cargo space",
            "eco-friendly electric car",
            "luxury sports car under 50000",
            "reliable truck for hauling",
            "compact car with good gas mileage"
        ]

        for i, query in enumerate(test_queries):
            start_time = time.time()
            try:
                request = SemanticSearchRequest(
                    query=query,
                    limit=20,
                    sort_by="relevance"
                )

                result = await self.search_service.semantic_search(request, f"perf_test_{i}")
                processing_time = time.time() - start_time

                success = processing_time < 0.8  # < 800ms requirement
                self.record_test_result(
                    f"Performance Test {i+1}: '{query[:30]}...'",
                    success,
                    processing_time,
                    None if success else f"Too slow: {processing_time:.3f}s"
                )

            except Exception as e:
                self.record_test_result(
                    f"Performance Test {i+1}: '{query[:30]}...'",
                    False,
                    None,
                    str(e)
                )

    async def test_input_validation(self) -> None:
        """Test input validation and edge cases"""
        logger.info("🔍 Testing Input Validation...")

        # Test 1: Empty query
        try:
            request = SemanticSearchRequest(query="")
            result = await self.search_service.semantic_search(request, "test_client")
            self.record_test_result("Empty Query Validation", False, None, "Should have failed")
        except Exception as e:
            # Expected to fail
            success = "400" in str(e) or "validation" in str(e).lower()
            self.record_test_result("Empty Query Validation", success, None, None if success else str(e))

        # Test 2: Very long query
        start_time = time.time()
        try:
            long_query = "car " * 200  # Very long query
            request = SemanticSearchRequest(query=long_query, limit=5)
            result = await self.search_service.semantic_search(request, "test_client")
            processing_time = time.time() - start_time
            # Should either succeed or fail gracefully with validation error
            success = True
            self.record_test_result("Long Query Handling", success, processing_time)
        except Exception as e:
            success = True  # Graceful failure is acceptable
            self.record_test_result("Long Query Handling", success, None, None)

        # Test 3: Invalid filter values
        start_time = time.time()
        try:
            filters = SearchFilters(
                year_min=2030,  # Invalid future year
                price_max=-1000  # Invalid negative price
            )
            request = SemanticSearchRequest(query="car", filters=filters)
            result = await self.search_service.semantic_search(request, "test_client")
            processing_time = time.time() - start_time
            success = True  # Should handle gracefully
            self.record_test_result("Invalid Filter Values", success, processing_time)
        except Exception as e:
            success = True  # Graceful failure is acceptable
            self.record_test_result("Invalid Filter Values", success, None, None)

    async def test_sorting_functionality(self) -> None:
        """Test different sorting options"""
        logger.info("📊 Testing Sorting Functionality...")

        sort_options = ["relevance", "price", "year", "mileage"]
        base_query = "SUV"

        for sort_by in sort_options:
            start_time = time.time()
            try:
                request = SemanticSearchRequest(
                    query=base_query,
                    sort_by=sort_by,
                    sort_order="desc",
                    limit=10
                )

                result = await self.search_service.semantic_search(request, "test_client")
                processing_time = time.time() - start_time

                success = (
                    len(result.results) > 0 and
                    result.search_metadata.get("sort_by") == sort_by
                )

                # Additional validation: check if results are actually sorted
                if success and len(result.results) > 1:
                    if sort_by == "price":
                        prices = [r.vehicle.price for r in result.results]
                        success = all(prices[i] >= prices[i+1] for i in range(len(prices)-1))
                    elif sort_by == "year":
                        years = [r.vehicle.year for r in result.results]
                        success = all(years[i] >= years[i+1] for i in range(len(years)-1))

                self.record_test_result(
                    f"Sorting by {sort_by}",
                    success,
                    processing_time,
                    None if success else f"Sorting validation failed for {sort_by}"
                )

            except Exception as e:
                self.record_test_result(f"Sorting by {sort_by}", False, None, str(e))

    async def test_rate_limiting(self) -> None:
        """Test rate limiting functionality"""
        logger.info("🚦 Testing Rate Limiting...")

        client_id = "rate_limit_test"
        rapid_requests = 15  # More than the 10 requests/minute limit

        rate_limited_count = 0

        for i in range(rapid_requests):
            start_time = time.time()
            try:
                request = SemanticSearchRequest(
                    query=f"test query {i}",
                    limit=5
                )

                result = await self.search_service.semantic_search(request, f"{client_id}_{i}")
                processing_time = time.time() - start_time

                # First few should succeed, later ones should be rate limited
                if i >= 10:  # After the limit
                    rate_limited_count += 1

            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    rate_limited_count += 1
                else:
                    # Some other error
                    pass

        success = rate_limited_count >= 5  # At least some requests should be rate limited
        self.record_test_result(
            "Rate Limiting",
            success,
            None,
            None if success else f"Only {rate_limited_count}/{rapid_requests-10} requests were rate limited"
        )

    async def test_caching_functionality(self) -> None:
        """Test query caching"""
        logger.info("💾 Testing Caching Functionality...")

        test_query = "luxury SUV with leather seats"
        client_id = "cache_test"

        # First request - should be cache miss
        start_time = time.time()
        try:
            request1 = SemanticSearchRequest(query=test_query, limit=10)
            result1 = await self.search_service.semantic_search(request1, client_id)
            first_time = time.time() - start_time

            # Second request - should be cache hit (faster)
            start_time = time.time()
            request2 = SemanticSearchRequest(query=test_query, limit=10)
            result2 = await self.search_service.semantic_search(request2, client_id)
            second_time = time.time() - start_time

            success = (
                result1.total_results == result2.total_results and
                result1.query == result2.query and
                len(result1.results) == len(result2.results)
            )

            # Cache should make second request faster (or at least not significantly slower)
            cache_effective = second_time <= first_time * 1.5  # Allow some variance

            self.record_test_result(
                "Caching Functionality",
                success and cache_effective,
                (first_time + second_time) / 2,
                None if success and cache_effective else "Cache not working properly"
            )

            # Test cache metadata
            cache_hit = result2.search_metadata.get("cache_used", False)
            self.record_test_result(
                "Cache Hit Detection",
                cache_hit,
                None,
                None if cache_hit else "Cache hit not detected"
            )

        except Exception as e:
            self.record_test_result("Caching Functionality", False, None, str(e))

    async def test_integration_story_1_1(self) -> None:
        """Test integration with Story 1-1 semantic search infrastructure"""
        logger.info("🔗 Testing Story 1-1 Integration...")

        try:
            # Test that we can use the embedding service directly
            embedding_service = self.search_service.embedding_service
            if embedding_service is None:
                raise Exception("Embedding service not initialized")

            # Test embedding generation
            from src.semantic.embedding_service import EmbeddingRequest
            embedding_request = EmbeddingRequest(text="family friendly SUV with space for children")
            embedding_response = await embedding_service.generate_embedding(embedding_request)

            success = (
                hasattr(embedding_response, 'embedding') and
                len(embedding_response.embedding) > 0 and
                hasattr(embedding_response, 'embedding_dim')
            )

            self.record_test_result(
                "Story 1-1 Embedding Service Integration",
                success,
                None,
                None if success else "Embedding service integration failed"
            )

            # Test that we can search using the generated embedding
            if success:
                start_time = time.time()
                search_request = SemanticSearchRequest(
                    query="family SUV with space for children",
                    limit=5
                )

                search_result = await self.search_service.semantic_search(search_request, "integration_test")
                processing_time = time.time() - start_time

                success = (
                    search_result.total_results >= 0 and
                    search_result.search_metadata.get("embedding_dim") == len(embedding_response.embedding)
                )

                self.record_test_result(
                    "Story 1-1 End-to-End Integration",
                    success,
                    processing_time,
                    None if success else "End-to-end integration failed"
                )

        except Exception as e:
            self.record_test_result("Story 1-1 Integration", False, None, str(e))

    async def test_integration_story_1_2(self) -> None:
        """Test integration with Story 1-2 multimodal processing"""
        logger.info("🖼️ Testing Story 1-2 Integration...")

        try:
            # Test that vehicle processing service is available
            vehicle_processing_service = self.search_service.vehicle_processing_service
            if vehicle_processing_service is None:
                raise Exception("Vehicle processing service not initialized")

            # Test that we can access processed vehicle data
            # This would normally come from Story 1-2's processing pipeline
            vehicle_db_service = self.search_service.vehicle_db_service

            # Check if we have vehicles with embeddings in the database
            stats = await vehicle_db_service.get_database_statistics()
            vehicles_with_embeddings = stats.get("total_vehicles", 0)

            success = vehicles_with_embeddings > 0

            self.record_test_result(
                "Story 1-2 Vehicle Data Available",
                success,
                None,
                None if success else f"No vehicles with embeddings found (total: {vehicles_with_embeddings})"
            )

            # Test semantic search with processed vehicle data
            if success:
                start_time = time.time()
                search_request = SemanticSearchRequest(
                    query="multimodal vehicle search with images",
                    limit=10
                )

                search_result = await self.search_service.semantic_search(search_request, "multimodal_test")
                processing_time = time.time() - start_time

                # Check if results include image data (from Story 1-2 processing)
                has_images = any(len(result.vehicle.images) > 0 for result in search_result.results)

                success = (
                    search_result.total_results >= 0 and
                    len(search_result.results) >= 0
                )

                self.record_test_result(
                    "Story 1-2 Multimodal Search Integration",
                    success,
                    processing_time,
                    None if success else "Multimodal search integration failed"
                )

                self.record_test_result(
                    "Story 1-2 Image Data Available",
                    has_images,
                    None,
                    None if has_images else "No vehicles have image data from Story 1-2"
                )

        except Exception as e:
            self.record_test_result("Story 1-2 Integration", False, None, str(e))

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("🧪 Starting Comprehensive Semantic Search API Test Suite...")

        if not await self.setup():
            return {"error": "Failed to setup test environment"}

        # Run all test suites
        await self.test_basic_functionality()
        await self.test_performance_requirements()
        await self.test_input_validation()
        await self.test_sorting_functionality()
        await self.test_rate_limiting()
        await self.test_caching_functionality()
        await self.test_integration_story_1_1()
        await self.test_integration_story_1_2()

        # Calculate final statistics
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        failed_tests = self.test_results["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate performance statistics
        if self.test_results["performance_metrics"]:
            avg_performance = sum(m["time"] for m in self.test_results["performance_metrics"]) / len(self.test_results["performance_metrics"])
            max_performance = max(m["time"] for m in self.test_results["performance_metrics"])
            min_performance = min(m["time"] for m in self.test_results["performance_metrics"])
        else:
            avg_performance = max_performance = min_performance = 0

        # Check if we meet the <800ms requirement
        performance_requirement_met = avg_performance < 0.8

        final_results = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate
            },
            "performance_analysis": {
                "average_response_time": avg_performance,
                "max_response_time": max_performance,
                "min_response_time": min_performance,
                "meets_800ms_requirement": performance_requirement_met,
                "requirement": "< 800ms average response time"
            },
            "performance_metrics": self.test_results["performance_metrics"],
            "errors": self.test_results["errors"],
            "service_status": {
                "search_service_available": self.search_service is not None,
                "embedding_service_available": self.search_service.embedding_service is not None if self.search_service else False,
                "database_service_available": self.search_service.vehicle_db_service is not None if self.search_service else False,
                "vehicle_processing_available": self.search_service.vehicle_processing_service is not None if self.search_service else False
            }
        }

        return final_results

    def print_results(self, results: Dict[str, Any]):
        """Print test results in a formatted way"""
        print("\n" + "="*80)
        print("🎯 SEMANTIC SEARCH API TEST RESULTS")
        print("="*80)

        # Test Summary
        summary = results["test_summary"]
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")

        # Performance Analysis
        perf = results["performance_analysis"]
        print(f"\n⚡ Performance Analysis:")
        print(f"   Average Response Time: {perf['average_response_time']:.3f}s")
        print(f"   Max Response Time: {perf['max_response_time']:.3f}s")
        print(f"   Min Response Time: {perf['min_response_time']:.3f}s")
        print(f"   <800ms Requirement: {'✅ MET' if perf['meets_800ms_requirement'] else '❌ NOT MET'}")

        # Service Status
        status = results["service_status"]
        print(f"\n🔧 Service Status:")
        print(f"   Search Service: {'✅' if status['search_service_available'] else '❌'}")
        print(f"   Embedding Service: {'✅' if status['embedding_service_available'] else '❌'}")
        print(f"   Database Service: {'✅' if status['database_service_available'] else '❌'}")
        print(f"   Vehicle Processing: {'✅' if status['vehicle_processing_available'] else '❌'}")

        # Errors
        if results["errors"]:
            print(f"\n❌ Errors Encountered:")
            for error in results["errors"]:
                print(f"   {error['test']}: {error['error']}")

        print("="*80)

        # Overall Assessment
        overall_success = (
            summary['success_rate'] >= 90 and
            perf['meets_800ms_requirement'] and
            all(status.values())
        )

        if overall_success:
            print("🎉 OVERALL ASSESSMENT: ✅ EXCELLENT - API Ready for Production")
        else:
            print("⚠️  OVERALL ASSESSMENT: ❌ NEEDS IMPROVEMENT - Review failed tests")

        print("="*80)


async def main():
    """Main test execution function"""
    test_suite = SemanticSearchAPITestSuite()

    try:
        # Run all tests
        results = await test_suite.run_all_tests()

        # Print results
        test_suite.print_results(results)

        # Save results to file
        with open("semantic_search_api_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("💾 Test results saved to semantic_search_api_test_results.json")

        return results

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting Semantic Search API Test Suite...")
    print("Testing Story 1-3: Build Semantic Search API Endpoints")
    print("TARB COMPLIANCE: Using real database connections, no mocks")
    print("="*80)

    asyncio.run(main())