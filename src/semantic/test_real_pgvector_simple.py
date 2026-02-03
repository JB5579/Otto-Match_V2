"""
Real pgvector Similarity Search Test Suite (Simplified)

Tests semantic search functionality using REAL Supabase pgvector operations
instead of in-memory cosine similarity calculations.

Story: 1.1-initialize-semantic-search-infrastructure (TARB Remediation)
Task: Replace all mock/simulated testing with real pgvector operations
"""

import os
import asyncio
import logging
import time
import sys
from typing import List, Dict, Any, Tuple, Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealPgVectorSearchTester:
    """Test semantic search functionality using REAL pgvector database operations"""

    def __init__(self):
        self.service: OttoAIEmbeddingService = None
        self.db_conn = None

    async def setup(self):
        """Initialize the embedding service with real database connection"""
        try:
            print("INITIALIZING Real pgvector Search Tester...")

            self.service = OttoAIEmbeddingService()

            # Get environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')

            if not await self.service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize embedding service")

            self.db_conn = self.service.db_conn

            print("SUCCESS: Embedding service initialized with real Supabase database")

        except Exception as e:
            print(f"SETUP FAILED: {str(e)}")
            raise

    async def test_pgvector_extension(self) -> Dict[str, Any]:
        """Test that pgvector extension is working"""
        print("\nTESTING pgvector Extension")
        print("=" * 40)

        try:
            with self.db_conn.cursor() as cursor:
                # Test vector extension
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                result = cursor.fetchone()

                if result:
                    version = result[0]
                    print(f"SUCCESS: pgvector extension installed: version {version}")

                    # Test basic vector operations
                    cursor.execute("SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector as distance")
                    distance = cursor.fetchone()[0]
                    print(f"SUCCESS: Vector distance calculation working: {distance:.4f}")

                    return {
                        'success': True,
                        'pgvector_version': version,
                        'vector_operations_work': True,
                        'test_distance': float(distance)
                    }
                else:
                    print("ERROR: pgvector extension not found")
                    return {'success': False, 'error': 'pgvector extension not found'}

        except Exception as e:
            print(f"ERROR: pgvector test failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def test_existing_embeddings(self) -> Dict[str, Any]:
        """Test existing embeddings in the database"""
        print("\nTESTING Existing Embeddings")
        print("=" * 40)

        try:
            with self.db_conn.cursor() as cursor:
                # Check vehicle_embeddings table
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_embeddings,
                        COUNT(CASE WHEN combined_embedding IS NOT NULL THEN 1 END) as combined_count,
                        COUNT(CASE WHEN description_embedding IS NOT NULL THEN 1 END) as description_count,
                        COUNT(CASE WHEN features_embedding IS NOT NULL THEN 1 END) as features_count
                    FROM vehicle_embeddings
                """)
                result = cursor.fetchone()

                print(f"Vehicle Embeddings Summary:")
                print(f"  Total records: {result[0]}")
                print(f"  Combined embeddings: {result[1]}")
                print(f"  Description embeddings: {result[2]}")
                print(f"  Features embeddings: {result[3]}")

                # Check rag_vehicle_embeddings table
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_rag_embeddings,
                        COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as valid_embeddings,
                        array_length(embedding::real[], 1) as dimensions
                    FROM rag_vehicle_embeddings
                    WHERE embedding IS NOT NULL
                    LIMIT 1
                """)
                rag_result = cursor.fetchone()

                if rag_result:
                    print(f"RAG Vehicle Embeddings Summary:")
                    print(f"  Total records: {rag_result[0]}")
                    print(f"  Valid embeddings: {rag_result[1]}")
                    print(f"  Vector dimensions: {rag_result[2]}")

                return {
                    'success': True,
                    'vehicle_embeddings': {
                        'total': result[0],
                        'combined': result[1],
                        'description': result[2],
                        'features': result[3]
                    },
                    'rag_embeddings': {
                        'total': rag_result[0] if rag_result else 0,
                        'valid': rag_result[1] if rag_result else 0,
                        'dimensions': rag_result[2] if rag_result else None
                    }
                }

        except Exception as e:
            print(f"ERROR: Existing embeddings test failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def test_real_vector_similarity_search(self) -> Dict[str, Any]:
        """Test REAL vector similarity search using pgvector"""
        print("\nTESTING REAL Vector Similarity Search")
        print("=" * 50)

        test_queries = [
            "family SUV with good fuel economy",
            "luxury sedan with leather seats",
            "electric vehicle with long range",
            "pickup truck for towing capacity",
            "compact car for city driving"
        ]

        search_results = {}
        successful_searches = 0
        total_searches = 0

        for query in test_queries:
            try:
                total_searches += 1
                print(f"\nQuery: '{query}'")

                start_time = time.time()

                # Generate embedding for the query
                request = EmbeddingRequest(text=query)
                response = await self.service.generate_embedding(request)
                query_embedding = response.embedding
                embedding_time = time.time() - start_time

                # Perform REAL pgvector similarity search
                search_start = time.time()

                with self.db_conn.cursor() as cursor:
                    # Use pgvector's <=> operator for cosine similarity
                    cursor.execute("""
                        SELECT
                            v.id,
                            v.make,
                            v.model,
                            v.year,
                            v.price,
                            ve.combined_embedding <=> %s::vector as similarity_score,
                            pg_column_size(ve.combined_embedding) as embedding_size
                        FROM vehicles v
                        JOIN vehicle_embeddings ve ON v.id = ve.vehicle_id
                        WHERE ve.combined_embedding IS NOT NULL
                        ORDER BY ve.combined_embedding <=> %s::vector
                        LIMIT 5
                    """, (query_embedding, query_embedding))

                    results = cursor.fetchall()
                    search_time = time.time() - search_start

                if results:
                    successful_searches += 1
                    print(f"SUCCESS: Found {len(results)} results in {search_time:.4f}s (embedding: {embedding_time:.4f}s):")

                    for i, row in enumerate(results, 1):
                        vehicle_id, make, model, year, price, similarity_score, embedding_size = row
                        # Convert similarity score (lower is better for <=>) to match score (higher is better)
                        match_score = (1 - similarity_score) * 100
                        print(f"  {i}. {year} {make} {model} - Match: {match_score:.1f}%, Price: ${price:,}")
                        print(f"     Embedding size: {embedding_size} bytes, Similarity: {similarity_score:.6f}")

                    search_results[query] = {
                        'success': True,
                        'results': results,
                        'count': len(results),
                        'embedding_time': embedding_time,
                        'search_time': search_time,
                        'total_time': embedding_time + search_time
                    }
                else:
                    print(f"WARNING: No results found")
                    search_results[query] = {
                        'success': False,
                        'results': [],
                        'count': 0,
                        'embedding_time': embedding_time,
                        'search_time': search_time
                    }

            except Exception as e:
                print(f"ERROR: Search test failed: {str(e)}")
                search_results[query] = {
                    'success': False,
                    'error': str(e),
                    'results': [],
                    'count': 0
                }

        # Summary
        success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
        avg_embedding_time = sum(r.get('embedding_time', 0) for r in search_results.values()) / total_searches
        avg_search_time = sum(r.get('search_time', 0) for r in search_results.values()) / total_searches

        print(f"\nREAL pgvector Search Performance Summary:")
        print(f"  Total queries: {total_searches}")
        print(f"  Successful searches: {successful_searches}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average embedding generation time: {avg_embedding_time:.4f}s")
        print(f"  Average database search time: {avg_search_time:.4f}s")
        print(f"  Average total time: {avg_embedding_time + avg_search_time:.4f}s")

        return {
            'total_queries': total_searches,
            'successful_searches': successful_searches,
            'success_rate': success_rate,
            'avg_embedding_time': avg_embedding_time,
            'avg_search_time': avg_search_time,
            'avg_total_time': avg_embedding_time + avg_search_time,
            'detailed_results': search_results
        }

    async def run_comprehensive_pgvector_tests(self) -> Dict[str, Any]:
        """Run comprehensive pgvector testing suite"""
        print("STARTING Comprehensive pgvector Testing Suite")
        print("=" * 60)

        all_results = {}

        try:
            # Test 1: pgvector extension
            all_results['pgvector_extension'] = await self.test_pgvector_extension()

            # Test 2: Existing embeddings
            all_results['existing_embeddings'] = await self.test_existing_embeddings()

            # Test 3: Real vector similarity search
            all_results['real_vector_search'] = await self.test_real_vector_similarity_search()

            # Overall summary
            print("\nCOMPREHENSIVE pgvector TEST SUMMARY")
            print("=" * 50)

            all_tests_passed = all(result.get('success', False) for result in all_results.values())

            print(f"Tests Passed: {sum(1 for r in all_results.values() if r.get('success', False))}/{len(all_results)}")

            if all_results['pgvector_extension'].get('success'):
                print(f"  - pgvector Extension: SUCCESS v{all_results['pgvector_extension']['pgvector_version']}")
            else:
                print(f"  - pgvector Extension: FAILED {all_results['pgvector_extension'].get('error', 'Unknown error')}")

            if all_results['real_vector_search'].get('success'):
                search_results = all_results['real_vector_search']
                print(f"  - Real Vector Search: SUCCESS {search_results['success_rate']:.1f}% success rate")
                print(f"    Average search time: {search_results['avg_total_time']:.4f}s")
            else:
                print(f"  - Real Vector Search: FAILED {all_results['real_vector_search'].get('error', 'Unknown error')}")

            if all_results['existing_embeddings'].get('success'):
                embed_results = all_results['existing_embeddings']
                print(f"  - Database Embeddings: SUCCESS {embed_results['vehicle_embeddings']['total']} vehicle embeddings")

            if all_tests_passed:
                print("\nALL pgvector TESTS PASSED! Real database integration is working correctly.")
            else:
                print("\nWARNING: Some tests failed. Review the detailed results above.")

            return {
                'overall_success': all_tests_passed,
                'tests_passed': sum(1 for r in all_results.values() if r.get('success', False)),
                'total_tests': len(all_results),
                'detailed_results': all_results
            }

        except Exception as e:
            print(f"\nCRITICAL: Comprehensive test suite failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'detailed_results': all_results
            }


async def main():
    """Main test execution"""
    print("Otto.AI Real pgvector Search Test Suite")
    print("=" * 60)
    print("TARB REMEDIATION: Replacing mock testing with REAL pgvector operations")
    print("=" * 60)

    tester = RealPgVectorSearchTester()

    try:
        await tester.setup()
        results = await tester.run_comprehensive_pgvector_tests()

        print(f"\nTesting completed!")
        print(f"Overall Result: {'SUCCESS' if results['overall_success'] else 'FAILED'}")

        return results['overall_success']

    except Exception as e:
        print(f"\nFATAL: Test execution failed: {str(e)}")
        return False

    finally:
        if tester.db_conn:
            tester.db_conn.close()
            print("Database connection closed")


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)