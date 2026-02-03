"""
Test Gemini 2.5 Flash Image Integration

Validates RAG-Anything service with the new Gemini 2.5 Flash Image model
for both text processing and image generation capabilities.

Story: 1.1-initialize-semantic-search-infrastructure
Task: Configure RAG-Anything service integration (AC: #2)
"""

import os
import asyncio
import logging
import sys
import base64

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_text_processing():
    """Test text processing with Gemini 2.5 Flash Image"""
    print("🧠 Testing Text Processing with Gemini 2.5 Flash Image")
    print("=" * 60)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not await service.initialize(supabase_url, supabase_key):
            print("❌ Service initialization failed")
            return False

        # Test vehicle description processing
        vehicle_description = """
        2023 Tesla Model Y Performance in Midnight Silver Metallic with black interior.
        Features include: Full Self-Driving capability, Performance upgrade,
        21" Überturbine wheels, Premium interior, Autopilot, heated seats,
        panoramic glass roof, towing package, and premium sound system.
        """

        request = EmbeddingRequest(text=vehicle_description)
        response = await service.generate_embedding(request)

        print(f"✅ Text processing successful")
        print(f"📏 Embedding dimensions: {response.embedding_dim}")
        print(f"⏱️ Processing time: {response.processing_time:.3f}s")
        print(f"📊 Sample embedding values: {response.embedding[:5]}...")

        return True

    except Exception as e:
        print(f"❌ Text processing test failed: {str(e)}")
        return False


async def test_image_generation():
    """Test image generation with Gemini 2.5 Flash Image"""
    print("\n🎨 Testing Image Generation with Gemini 2.5 Flash Image")
    print("=" * 60)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Test vehicle image generation
        vehicle_desc = "2023 Tesla Model Y Performance in Midnight Silver Metallic, parked on a scenic mountain road"

        result = await service.generate_vehicle_image(
            vehicle_description=vehicle_desc,
            aspect_ratio="16:9",
            style_hint="professional automotive photography with dramatic lighting"
        )

        if result.get("success"):
            print("✅ Image generation successful")
            print(f"📐 Aspect ratio: {result.get('aspect_ratio')}")
            print(f"🤖 Model: {result.get('model')}")
            print(f"📝 Description: {result.get('text_description', 'N/A')[:100]}...")

            if result.get('image_data'):
                print(f"🖼️ Image data length: {len(result['image_data'])} characters (base64)")
                print(f"🖼️ Image data preview: {result['image_data'][:50]}...")
            else:
                print("⚠️ No image data returned")

            return True
        else:
            print(f"❌ Image generation failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Image generation test failed: {str(e)}")
        return False


async def test_multimodal_rag():
    """Test multimodal RAG processing"""
    print("\n🔍 Testing Multimodal RAG Processing")
    print("=" * 60)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        await service.initialize(supabase_url, supabase_key)

        # Test multimodal request
        vehicle_context = {
            "make": "BMW",
            "model": "X5",
            "year": 2024,
            "trim": "xDrive40i",
            "features": ["sports_package", "premium_audio", "panoramic_sunroof", "heads_up_display"],
            "color": "Phytonic Blue Metallic"
        }

        request = EmbeddingRequest(
            text="Luxury SUV with advanced technology and premium comfort features",
            context=vehicle_context
        )

        response = await service.generate_embedding(request)

        print("✅ Multimodal RAG processing successful")
        print(f"🚗 Vehicle: {vehicle_context['make']} {vehicle_context['model']} {vehicle_context['year']}")
        print(f"🎨 Color: {vehicle_context['color']}")
        print(f"⚙️ Features: {', '.join(vehicle_context['features'][:3])}...")
        print(f"📏 Embedding dimensions: {response.embedding_dim}")
        print(f"⏱️ Processing time: {response.processing_time:.3f}s")

        return True

    except Exception as e:
        print(f"❌ Multimodal RAG test failed: {str(e)}")
        return False


async def test_service_integration():
    """Test complete service integration"""
    print("\n🔗 Testing Complete Service Integration")
    print("=" * 60)

    try:
        service = OttoAIEmbeddingService()

        # Initialize
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        init_success = await service.initialize(supabase_url, supabase_key)
        print(f"🚀 Service initialization: {'✅' if init_success else '❌'}")

        # Check RAG-Anything components
        rag_initialized = service.rag is not None
        lightrag_initialized = service.lightrag is not None
        db_connected = service.db_conn is not None

        print(f"📊 Component Status:")
        print(f"  🔗 Database: {'✅ Connected' if db_connected else '❌ Not connected'}")
        print(f"  🔗 LightRAG: {'✅ Initialized' if lightrag_initialized else '❌ Not initialized'}")
        print(f"  🔗 RAGAnything: {'✅ Initialized' if rag_initialized else '❌ Not initialized'}")

        # Test basic connectivity
        print(f"\n🧪 Running connectivity tests...")

        # Test text embedding
        test_request = EmbeddingRequest(text="Test vehicle description for connectivity check")
        test_response = await service.generate_embedding(test_request)

        embedding_works = len(test_response.embedding) > 0
        print(f"  📝 Text embeddings: {'✅ Working' if embedding_works else '❌ Failed'}")

        return init_success and rag_initialized and db_connected and embedding_works

    except Exception as e:
        print(f"❌ Service integration test failed: {str(e)}")
        return False


async def main():
    """Run all integration tests for Gemini 2.5 Flash Image"""
    print("🚀 Otto AI Gemini 2.5 Flash Image Integration Tests")
    print("=" * 70)
    print("Story 1.1 - Task 2: Configure RAG-Anything Service Integration")
    print("Testing with google/gemini-2.5-flash-image model")
    print("=" * 70)

    # Check environment variables
    required_vars = [
        'OPENROUTER_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_DB_PASSWORD'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False

    print(f"✅ All required environment variables present")

    # Run tests
    tests = [
        ("Text Processing", test_text_processing),
        ("Image Generation", test_image_generation),
        ("Multimodal RAG", test_multimodal_rag),
        ("Service Integration", test_service_integration)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*70}")
            result = await test_func()
            results[test_name] = result
            print(f"{'='*70}")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Summary
    print("\n🎯 Test Results Summary")
    print("=" * 70)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Gemini 2.5 Flash Image integration is working correctly.")
        print("\n🔧 Ready for:")
        print("  📝 Text-based RAG processing")
        print("  🎨 Vehicle image generation")
        print("  🔍 Multimodal vehicle analysis")
        print("  🚗 Vehicle listing creation pipeline")
        return True
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)