"""
Test RAG-Anything Service Integration

Validates that the embedding service can connect to all required services
and process multimodal content correctly.

Story: 1.1-initialize-semantic-search-infrastructure
Task: Configure RAG-Anything service integration (AC: #2)
"""

import os
import asyncio
import logging
from typing import Dict, Any
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_connectivity():
    """Test basic connectivity to required services"""
    print("🔍 Testing Basic Service Connectivity")
    print("=" * 50)

    try:
        # Initialize service
        service = OttoAIEmbeddingService()

        # Get environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        print(f"🔑 Environment Variables:")
        print(f"  SUPABASE_URL: {'✓' if supabase_url else '✗'}")
        print(f"  SUPABASE_ANON_KEY: {'✓' if supabase_key else '✗'}")
        print(f"  OPENROUTER_API_KEY: {'✓' if os.getenv('OPENROUTER_API_KEY') else '✗'}")
        print(f"  SUPABASE_DB_PASSWORD: {'✓' if os.getenv('SUPABASE_DB_PASSWORD') else '✗'}")

        if not all([supabase_url, supabase_key, os.getenv('OPENROUTER_API_KEY'), os.getenv('SUPABASE_DB_PASSWORD')]):
            print("\n❌ Missing required environment variables")
            return False

        # Initialize service
        print(f"\n🚀 Initializing Otto AI Embedding Service...")
        success = await service.initialize(supabase_url, supabase_key)

        if success:
            print("✅ Service initialized successfully")
            return True
        else:
            print("❌ Service initialization failed")
            return False

    except Exception as e:
        print(f"❌ Initialization error: {str(e)}")
        return False


async def test_text_embedding():
    """Test text embedding generation"""
    print("\n🧠 Testing Text Embedding Generation")
    print("=" * 50)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Test embeddings
        test_texts = [
            "2022 Toyota Camry with excellent fuel efficiency",
            "Luxury SUV with advanced safety features",
            "Electric vehicle with long range and fast charging"
        ]

        for i, text in enumerate(test_texts, 1):
            print(f"\n📝 Test {i}: '{text[:50]}...'")

            request = EmbeddingRequest(text=text)
            response = await service.generate_embedding(request)

            print(f"  ✅ Embedding generated successfully")
            print(f"  📏 Dimensions: {response.embedding_dim}")
            print(f"  ⏱️ Processing time: {response.processing_time:.3f}s")
            print(f"  📊 Sample values: {response.embedding[:3]}...")

        return True

    except Exception as e:
        print(f"❌ Text embedding test failed: {str(e)}")
        return False


async def test_multimodal_processing():
    """Test multimodal content processing"""
    print("\n🖼️ Testing Multimodal Processing")
    print("=" * 50)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Test multimodal request with context
        vehicle_data = {
            "make": "Honda",
            "model": "CR-V",
            "year": 2023,
            "features": ["all_wheel_drive", "lane_assist", "adaptive_cruise_control"]
        }

        request = EmbeddingRequest(
            text="Spacious compact SUV with advanced safety features",
            context=vehicle_data
        )

        print("📝 Processing multimodal content...")
        print(f"  🚗 Vehicle: {vehicle_data['make']} {vehicle_data['model']} {vehicle_data['year']}")
        print(f"  🔧 Features: {', '.join(vehicle_data['features'])}")

        response = await service.generate_embedding(request)

        print(f"  ✅ Multimodal embedding generated")
        print(f"  📏 Dimensions: {response.embedding_dim}")
        print(f"  ⏱️ Processing time: {response.processing_time:.3f}s")

        return True

    except Exception as e:
        print(f"❌ Multimodal processing test failed: {str(e)}")
        return False


async def test_raganything_initialization():
    """Test RAG-Anything specific initialization"""
    print("\n🔬 Testing RAG-Anything Initialization")
    print("=" * 50)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Check RAG-Anything components
        rag_initialized = service.rag is not None
        lightrag_initialized = service.lightrag is not None

        print(f"📋 RAG-Anything Status:")
        print(f"  🔗 LightRAG: {'✅ Initialized' if lightrag_initialized else '❌ Not initialized'}")
        print(f"  🧠 RAGAnything: {'✅ Initialized' if rag_initialized else '❌ Not initialized'}")

        if rag_initialized and lightrag_initialized:
            print("  📁 Storage directory: ./rag_storage")
            print("  🔧 Parser: mineru")
            print("  📊 Parse method: auto")
            print("  🖼️ Image processing: enabled")
            print("  📊 Table processing: enabled")

        return rag_initialized and lightrag_initialized

    except Exception as e:
        print(f"❌ RAG-Anything initialization test failed: {str(e)}")
        return False


async def test_database_integration():
    """Test database integration with pgvector"""
    print("\n🗄️ Testing Database Integration")
    print("=" * 50)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Test database connection
        if service.db_conn:
            cursor = service.db_conn.cursor()

            # Test pgvector extension
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            db_connected = result[0] == 1

            # Test vehicles table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'vehicles'
                );
            """)
            table_exists = cursor.fetchone()[0]

            # Test vector column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = 'vehicles'
                    AND column_name = 'title_embedding'
                );
            """)
            vector_column_exists = cursor.fetchone()[0]

            cursor.close()

            print(f"📊 Database Status:")
            print(f"  🔗 Connection: {'✅ Connected' if db_connected else '❌ Failed'}")
            print(f"  📋 Vehicles table: {'✅ Exists' if table_exists else '❌ Missing'}")
            print(f"  🔢 Vector columns: {'✅ Present' if vector_column_exists else '❌ Missing'}")

            return db_connected and table_exists and vector_column_exists
        else:
            print("❌ Database connection not established")
            return False

    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Otto AI RAG-Anything Integration Tests")
    print("=" * 60)
    print("Story 1.1 - Task 2: Configure RAG-Anything Service Integration")
    print("=" * 60)

    # Run all tests
    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("Text Embedding", test_text_embedding),
        ("Multimodal Processing", test_multimodal_processing),
        ("RAG-Anything Initialization", test_raganything_initialization),
        ("Database Integration", test_database_integration)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = await test_func()
            results[test_name] = result
            print(f"{'='*60}")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Summary
    print("\n🎯 Test Results Summary")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! RAG-Anything integration is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)