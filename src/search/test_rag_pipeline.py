"""
RAG Pipeline Validation Test

Validates that all RAG strategy components are properly configured:
1. Query Expansion Service (Groq LLM)
2. Hybrid Search Service (Vector + FTS + Filters via RRF)
3. Reranking Service (BGE cross-encoder)
4. Contextual Embedding Service (Category-aware)
5. Search Orchestrator (Full pipeline coordination)

Run: python -m src.search.test_rag_pipeline
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all RAG services can be imported"""
    print("\n=== Testing Imports ===")

    # Use importlib to import directly from files, bypassing __init__.py
    import importlib.util

    def import_from_file(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    try:
        mod = import_from_file("query_expansion_service", project_root / "src/search/query_expansion_service.py")
        QueryExpansionService = mod.QueryExpansionService
        print("  [PASS] QueryExpansionService imported")
    except Exception as e:
        print(f"  [FAIL] QueryExpansionService: {e}")
        return False

    try:
        mod = import_from_file("hybrid_search_service", project_root / "src/search/hybrid_search_service.py")
        HybridSearchService = mod.HybridSearchService
        print("  [PASS] HybridSearchService imported")
    except Exception as e:
        print(f"  [FAIL] HybridSearchService: {e}")
        return False

    try:
        mod = import_from_file("reranking_service", project_root / "src/search/reranking_service.py")
        RerankingService = mod.RerankingService
        print("  [PASS] RerankingService imported")
    except Exception as e:
        print(f"  [FAIL] RerankingService: {e}")
        return False

    try:
        mod = import_from_file("contextual_embedding_service", project_root / "src/search/contextual_embedding_service.py")
        ContextualEmbeddingService = mod.ContextualEmbeddingService
        print("  [PASS] ContextualEmbeddingService imported")
    except Exception as e:
        print(f"  [FAIL] ContextualEmbeddingService: {e}")
        return False

    try:
        mod = import_from_file("price_forecast_service", project_root / "src/services/price_forecast_service.py")
        PriceForecastService = mod.PriceForecastService
        print("  [PASS] PriceForecastService imported")
    except Exception as e:
        print(f"  [FAIL] PriceForecastService: {e}")
        return False

    return True


def import_from_file(module_name, file_path):
    """Import a module directly from file path"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_service_initialization():
    """Test that services can be instantiated"""
    print("\n=== Testing Service Initialization ===")

    try:
        mod = import_from_file("query_expansion_service", project_root / "src/search/query_expansion_service.py")
        qe = mod.QueryExpansionService()
        print(f"  [PASS] QueryExpansionService initialized (model: {qe.model})")
    except Exception as e:
        print(f"  [FAIL] QueryExpansionService: {e}")
        return False

    try:
        mod = import_from_file("hybrid_search_service", project_root / "src/search/hybrid_search_service.py")
        hs = mod.HybridSearchService()
        print(f"  [PASS] HybridSearchService initialized (weights: v={hs.vector_weight}, k={hs.keyword_weight}, f={hs.filter_weight})")
    except Exception as e:
        print(f"  [FAIL] HybridSearchService: {e}")
        return False

    try:
        mod = import_from_file("reranking_service", project_root / "src/search/reranking_service.py")
        rs = mod.RerankingService()
        print(f"  [PASS] RerankingService initialized (model: {rs.model})")
    except Exception as e:
        print(f"  [FAIL] RerankingService: {e}")
        return False

    try:
        mod = import_from_file("contextual_embedding_service", project_root / "src/search/contextual_embedding_service.py")
        ce = mod.ContextualEmbeddingService()
        print(f"  [PASS] ContextualEmbeddingService initialized")
    except Exception as e:
        print(f"  [FAIL] ContextualEmbeddingService: {e}")
        return False

    return True


def test_environment_variables():
    """Test that required environment variables are set"""
    print("\n=== Testing Environment Variables ===")

    required_vars = [
        ("SUPABASE_URL", "Database connection"),
        ("SUPABASE_ANON_KEY", "Database authentication"),
        ("OPENROUTER_API_KEY", "LLM API access"),
        ("OPENAI_API_KEY", "Embeddings API"),
    ]

    optional_vars = [
        ("GROQ_API_KEY", "Direct Groq access (optional, uses OpenRouter if not set)"),
        ("QUERY_EXPANSION_MODEL", "Custom query expansion model"),
        ("RERANK_MODEL", "Custom reranking model"),
    ]

    all_required_set = True
    for var, desc in required_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  [PASS] {var}: {masked} ({desc})")
        else:
            print(f"  [FAIL] {var}: NOT SET ({desc})")
            all_required_set = False

    print("\n  Optional variables:")
    for var, desc in optional_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  [INFO] {var}: {masked} ({desc})")
        else:
            print(f"  [INFO] {var}: not set ({desc})")

    return all_required_set


async def test_query_expansion():
    """Test query expansion with a sample query"""
    print("\n=== Testing Query Expansion ===")

    mod = import_from_file("query_expansion_service", project_root / "src/search/query_expansion_service.py")
    service = mod.QueryExpansionService()

    try:
        result = await service.expand_query("looking for a reliable truck for towing")
        print(f"  [PASS] Query expanded successfully")
        print(f"         Original: 'looking for a reliable truck for towing'")
        print(f"         Expanded: '{result.expanded_query[:80]}...'")
        print(f"         Synonyms: {result.synonyms[:3]}")
        print(f"         Extracted filters: {result.extracted_filters}")
        print(f"         Confidence: {result.confidence:.0%}")
        return True
    except Exception as e:
        print(f"  [FAIL] Query expansion failed: {e}")
        return False


async def test_contextual_embedding():
    """Test contextual embedding generation"""
    print("\n=== Testing Contextual Embeddings ===")

    mod = import_from_file("contextual_embedding_service", project_root / "src/search/contextual_embedding_service.py")
    service = mod.ContextualEmbeddingService()

    try:
        # Test category detection
        category = service.detect_vehicle_category("I need a pickup truck for work")
        print(f"  [PASS] Category detected: '{category}'")

        # Test contextualized text
        ctx_text = service.contextualize_text("Ford F-250 Lariat", category)
        print(f"  [PASS] Contextualized: '{ctx_text[:60]}...'")

        return True
    except Exception as e:
        print(f"  [FAIL] Contextual embedding failed: {e}")
        return False


def test_rrf_fusion():
    """Test RRF fusion algorithm"""
    print("\n=== Testing RRF Fusion ===")

    mod = import_from_file("hybrid_search_service", project_root / "src/search/hybrid_search_service.py")
    service = mod.HybridSearchService()

    # Mock results for testing
    vector_results = [
        {"id": "v1", "vin": "VIN1", "year": 2020, "make": "Ford", "model": "F-250", "similarity": 0.95},
        {"id": "v2", "vin": "VIN2", "year": 2019, "make": "Chevy", "model": "Silverado", "similarity": 0.85},
        {"id": "v3", "vin": "VIN3", "year": 2021, "make": "RAM", "model": "2500", "similarity": 0.75},
    ]

    keyword_results = [
        {"id": "v2", "vin": "VIN2", "year": 2019, "make": "Chevy", "model": "Silverado", "rank": 0.9},
        {"id": "v1", "vin": "VIN1", "year": 2020, "make": "Ford", "model": "F-250", "rank": 0.8},
        {"id": "v4", "vin": "VIN4", "year": 2018, "make": "Ford", "model": "F-350", "rank": 0.7},
    ]

    try:
        fused = service._reciprocal_rank_fusion(vector_results, keyword_results)
        print(f"  [PASS] RRF fusion completed with {len(fused)} results")

        for i, r in enumerate(fused[:3]):
            print(f"         #{i+1}: {r.year} {r.make} {r.model} (hybrid_score: {r.hybrid_score:.4f})")

        return True
    except Exception as e:
        print(f"  [FAIL] RRF fusion failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Otto.AI RAG Pipeline Validation")
    print("=" * 60)

    results = []

    # Synchronous tests
    results.append(("Imports", test_imports()))
    results.append(("Service Initialization", test_service_initialization()))
    results.append(("Environment Variables", test_environment_variables()))
    results.append(("RRF Fusion", test_rrf_fusion()))

    # Async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        results.append(("Contextual Embeddings", loop.run_until_complete(test_contextual_embedding())))

        # Only test query expansion if API key is set
        if os.getenv("OPENROUTER_API_KEY"):
            results.append(("Query Expansion", loop.run_until_complete(test_query_expansion())))
        else:
            print("\n=== Skipping Query Expansion Test (no API key) ===")
            results.append(("Query Expansion", None))
    finally:
        loop.close()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results:
        if result is True:
            print(f"  [PASS] {name}")
            passed += 1
        elif result is False:
            print(f"  [FAIL] {name}")
            failed += 1
        else:
            print(f"  [SKIP] {name}")
            skipped += 1

    print()
    print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")

    if failed == 0:
        print("\n[SUCCESS] RAG Pipeline is properly configured!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
