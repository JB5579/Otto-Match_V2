"""
Semantic Search API Validation Script

Quick validation script to test that the semantic search API
can be initialized and basic functionality works.

This is a lightweight validation for development testing.
"""

import os
import asyncio
import sys
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

async def validate_api_initialization():
    """Validate that the semantic search API can be initialized"""
    print("🚀 Validating Semantic Search API Initialization...")

    try:
        # Check environment variables
        required_vars = [
            'OPENROUTER_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_DB_PASSWORD'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False

        print("✅ Environment variables validated")

        # Import and initialize the search service
        from src.api.semantic_search_api import SemanticSearchService, SemanticSearchRequest

        search_service = SemanticSearchService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        print("🔌 Connecting to services...")
        if not await search_service.initialize(supabase_url, supabase_key):
            print("❌ Failed to initialize search service")
            return False

        print("✅ Search service initialized successfully")

        # Test basic search functionality
        print("🔍 Testing basic search...")
        request = SemanticSearchRequest(
            query="family SUV",
            limit=5
        )

        result = await search_service.semantic_search(request, "validation_test")

        print(f"✅ Basic search completed")
        print(f"   Query: '{request.query}'")
        print(f"   Results: {len(result.results)} vehicles found")
        print(f"   Processing time: {result.processing_time:.3f}s")
        print(f"   Total available: {result.total_results}")

        if result.results:
            sample_vehicle = result.results[0]
            print(f"   Sample result: {sample_vehicle.year} {sample_vehicle.make} {sample_vehicle.model}")
            print(f"   Similarity score: {sample_vehicle.similarity_score:.3f}")

        # Test search with filters
        print("\n🎛️ Testing search with filters...")
        from src.api.semantic_search_api import SearchFilters

        filters = SearchFilters(
            make="Toyota",
            vehicle_type="SUV"
        )

        request_with_filters = SemanticSearchRequest(
            query="reliable family vehicle",
            filters=filters,
            limit=3
        )

        result_filtered = await search_service.semantic_search(request_with_filters, "validation_test")

        print(f"✅ Filtered search completed")
        print(f"   Query: '{request_with_filters.query}'")
        print(f"   Filters: make={filters.make}, type={filters.vehicle_type}")
        print(f"   Results: {len(result_filtered.results)} vehicles found")
        print(f"   Processing time: {result_filtered.processing_time:.3f}s")

        # Get search statistics
        stats = search_service.get_search_stats()
        print(f"\n📊 Search Statistics:")
        print(f"   Total searches: {stats['total_searches']}")
        print(f"   Average processing time: {stats['avg_processing_time']:.3f}s")
        print(f"   Cache size: {stats['cache_size']}")

        print("\n🎉 Semantic Search API validation completed successfully!")
        print("✅ All core functionality is working properly")
        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def validate_integration_with_stories():
    """Validate integration with Stories 1-1 and 1-2"""
    print("\n🔗 Validating Integration with Previous Stories...")

    try:
        from src.api.semantic_search_api import SemanticSearchService, SemanticSearchRequest
        from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest
        from src.semantic.vehicle_database_service import VehicleDatabaseService

        # Initialize services
        search_service = SemanticSearchService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not await search_service.initialize(supabase_url, supabase_key):
            print("❌ Failed to initialize services for integration test")
            return False

        # Test Story 1-1 Integration (embedding service)
        print("🧠 Testing Story 1-1 Integration (Embedding Service)...")
        embedding_service = search_service.embedding_service

        if embedding_service is None:
            print("❌ Embedding service not available")
            return False

        embedding_request = EmbeddingRequest(text="family SUV with lots of cargo space")
        embedding_response = await embedding_service.generate_embedding(embedding_request)

        if not embedding_response or not embedding_response.embedding:
            print("❌ Embedding generation failed")
            return False

        print(f"✅ Embedding generated successfully (dim: {len(embedding_response.embedding)})")

        # Test Story 1-2 Integration (vehicle database service)
        print("🚗 Testing Story 1-2 Integration (Vehicle Database)...")
        vehicle_db_service = search_service.vehicle_db_service

        if vehicle_db_service is None:
            print("❌ Vehicle database service not available")
            return False

        db_stats = await vehicle_db_service.get_database_statistics()
        total_vehicles = db_stats.get('total_vehicles', 0)

        print(f"✅ Vehicle database accessible ({total_vehicles} vehicles with embeddings)")

        # Test end-to-end integration
        print("🔄 Testing End-to-End Integration...")
        integration_request = SemanticSearchRequest(
            query="family SUV good for road trips with lots of cargo space",
            limit=5
        )

        integration_result = await search_service.semantic_search(integration_request, "integration_test")

        success = (
            integration_result.total_results >= 0 and
            len(integration_result.results) <= 5 and
            integration_result.processing_time > 0
        )

        if success:
            print(f"✅ End-to-end integration successful")
            print(f"   Query: '{integration_request.query}'")
            print(f"   Results: {len(integration_result.results)} vehicles")
            print(f"   Processing time: {integration_result.processing_time:.3f}s")

            if integration_result.results:
                sample = integration_result.results[0]
                print(f"   Sample: {sample.year} {sample.make} {sample.model}")
                if sample.match_explanation:
                    print(f"   Match explanation: {sample.match_explanation}")
        else:
            print("❌ End-to-end integration failed")
            return False

        print("✅ Integration with Stories 1-1 and 1-2 validated successfully!")
        return True

    except Exception as e:
        print(f"❌ Integration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("🎯 Otto.AI Semantic Search API Validation")
    print("Story 1-3: Build Semantic Search API Endpoints")
    print("TARB COMPLIANCE: Real database connections only")
    print("="*60)

    async def run_validation():
        # Basic API validation
        basic_success = await validate_api_initialization()

        if not basic_success:
            print("\n❌ Basic API validation failed - stopping validation")
            return False

        # Integration validation
        integration_success = await validate_integration_with_stories()

        if not integration_success:
            print("\n⚠️ Integration validation had issues")

        # Overall assessment
        overall_success = basic_success and integration_success

        print("\n" + "="*60)
        if overall_success:
            print("🎉 OVERALL VALIDATION: ✅ SUCCESS")
            print("Semantic Search API is ready for Story 1-3 completion!")
        else:
            print("❌ OVERALL VALIDATION: FAILED")
            print("Please address the issues above before completing Story 1-3")
        print("="*60)

        return overall_success

    # Run validation
    return asyncio.run(run_validation())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)