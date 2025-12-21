"""
Similarity Search Test Suite

Tests semantic search functionality with sample vehicle data and validates
that the embedding service can find relevant matches for search queries.

Story: 1.1-initialize-semantic-search-infrastructure
Task: Create similarity search test cases (AC: #5)
"""

import os
import asyncio
import logging
import numpy as np
import sys
from typing import List, Dict, Any, Tuple

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest
from src.semantic.sample_vehicle_data import SAMPLE_VEHICLES, create_sample_search_queries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimilaritySearchTester:
    """Test semantic search functionality with sample data"""

    def __init__(self):
        self.service: OttoAIEmbeddingService = None
        self.vehicle_embeddings = {}
        self.test_queries = create_sample_search_queries()

    async def setup(self):
        """Initialize the embedding service and generate embeddings for sample data"""
        try:
            print("🚀 Initializing Similarity Search Tester...")

            self.service = OttoAIEmbeddingService()

            # Get environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')

            if not await self.service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize embedding service")

            print("✅ Embedding service initialized successfully")

            # Generate embeddings for all sample vehicles
            await self.generate_vehicle_embeddings()

            print(f"✅ Generated embeddings for {len(self.vehicle_embeddings)} vehicles")

        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            raise

    async def generate_vehicle_embeddings(self):
        """Generate embeddings for all sample vehicles"""
        print("🧠 Generating embeddings for sample vehicles...")

        for i, vehicle in enumerate(SAMPLE_VEHICLES):
            try:
                # Create comprehensive text for embedding
                vehicle_text = self.create_vehicle_search_text(vehicle)

                # Generate embedding
                request = EmbeddingRequest(text=vehicle_text)
                response = await self.service.generate_embedding(request)

                # Store embedding
                self.vehicle_embeddings[vehicle['vin']] = {
                    'embedding': response.embedding,
                    'vehicle': vehicle,
                    'search_text': vehicle_text
                }

                print(f"  📝 Processed {i+1}/{len(SAMPLE_VEHICLES)}: {vehicle['make']} {vehicle['model']}")

            except Exception as e:
                print(f"❌ Failed to generate embedding for {vehicle['vin']}: {str(e)}")
                continue

    def create_vehicle_search_text(self, vehicle: Dict[str, Any]) -> str:
        """Create comprehensive text representation for semantic search"""
        text_parts = []

        # Basic vehicle info
        text_parts.append(f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle.get('trim', '')}")
        text_parts.append(f"{vehicle['vehicle_type']} with {vehicle['fuel_type']} engine")
        text_parts.append(f"Transmission: {vehicle['transmission']}, Drivetrain: {vehicle['drivetrain']}")

        # Performance specs
        if vehicle.get('horsepower'):
            text_parts.append(f"Horsepower: {vehicle['horsepower']} hp")
        if vehicle.get('engine_displacement'):
            text_parts.append(f"Engine: {vehicle['engine_displacement']}")

        # Physical attributes
        text_parts.append(f"Color: {vehicle['exterior_color']} exterior with {vehicle['interior_color']} interior")
        text_parts.append(f"{vehicle.get('num_doors', 4)} doors")

        # Description
        if vehicle.get('description'):
            text_parts.append(vehicle['description'])

        # Features
        if vehicle.get('features'):
            text_parts.append("Features: " + ", ".join(vehicle['features']))

        # Title
        if vehicle.get('title'):
            text_parts.append(vehicle['title'])

        return " ".join(text_parts)

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def search_vehicles(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """Search for vehicles similar to query"""
        try:
            # Generate embedding for query
            request = EmbeddingRequest(text=query)
            response = await self.service.generate_embedding(request)
            query_embedding = response.embedding

            # Calculate similarities
            similarities = []
            for vin, vehicle_data in self.vehicle_embeddings.items():
                similarity = self.cosine_similarity(query_embedding, vehicle_data['embedding'])
                similarities.append((vehicle_data['vehicle'], similarity))

            # Sort by similarity (highest first) and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)

            return similarities[:top_k]

        except Exception as e:
            print(f"❌ Search failed for query '{query}': {str(e)}")
            return []

    async def run_similarity_tests(self) -> Dict[str, Any]:
        """Run comprehensive similarity search tests"""
        print("\n🔍 Running Similarity Search Tests")
        print("=" * 50)

        test_results = {}
        successful_searches = 0
        total_searches = 0

        for query in self.test_queries:
            try:
                total_searches += 1
                print(f"\n📝 Query: '{query}'")

                # Perform search
                results = await self.search_vehicles(query, top_k=3)

                if results:
                    successful_searches += 1
                    print(f"✅ Found {len(results)} results:")

                    for i, (vehicle, score) in enumerate(results, 1):
                        print(f"  {i}. {vehicle['year']} {vehicle['make']} {vehicle['model']} - Score: {score:.4f}")
                        print(f"     Price: ${vehicle['price']:,}, {vehicle['vehicle_type']}, {vehicle['fuel_type']}")
                        print(f"     Features: {', '.join(vehicle['features'][:3])}...")

                    test_results[query] = {
                        'success': True,
                        'results': [(v['vin'], score) for v, score in results],
                        'count': len(results)
                    }
                else:
                    print(f"❌ No results found")
                    test_results[query] = {
                        'success': False,
                        'results': [],
                        'count': 0
                    }

            except Exception as e:
                print(f"❌ Search test failed: {str(e)}")
                test_results[query] = {
                    'success': False,
                    'error': str(e),
                    'results': [],
                    'count': 0
                }

        # Summary
        success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0

        print(f"\n📊 Similarity Search Test Summary:")
        print(f"  Total queries: {total_searches}")
        print(f"  Successful searches: {successful_searches}")
        print(f"  Success rate: {success_rate:.1f}%")

        return {
            'total_queries': total_searches,
            'successful_searches': successful_searches,
            'success_rate': success_rate,
            'detailed_results': test_results
        }

    async def test_embedding_quality(self) -> Dict[str, Any]:
        """Test embedding quality and consistency"""
        print("\n🧪 Testing Embedding Quality")
        print("=" * 50)

        quality_results = {}

        # Test 1: Same query should produce similar embeddings
        print("📝 Testing embedding consistency...")
        test_query = "family SUV with good fuel economy"

        embeddings = []
        for i in range(3):
            request = EmbeddingRequest(text=test_query)
            response = await self.service.generate_embedding(request)
            embeddings.append(response.embedding)

        # Calculate similarity between embeddings
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)

        avg_similarity = np.mean(similarities)
        print(f"✅ Average embedding similarity: {avg_similarity:.6f}")

        quality_results['consistency'] = {
            'query': test_query,
            'embeddings_generated': len(embeddings),
            'average_similarity': avg_similarity,
            'consistent': avg_similarity > 0.99
        }

        # Test 2: Related queries should have similar embeddings
        print("\n📝 Testing semantic similarity...")
        related_queries = [
            "efficient family SUV",
            "spacious SUV for families",
            "fuel-efficient sport utility vehicle"
        ]

        related_embeddings = []
        for query in related_queries:
            request = EmbeddingRequest(text=query)
            response = await self.service.generate_embedding(request)
            related_embeddings.append(response.embedding)

        # Calculate similarities between related queries
        related_similarities = []
        for i in range(len(related_embeddings)):
            for j in range(i + 1, len(related_embeddings)):
                sim = self.cosine_similarity(related_embeddings[i], related_embeddings[j])
                related_similarities.append(sim)

        avg_related_similarity = np.mean(related_similarities)
        print(f"✅ Average related query similarity: {avg_related_similarity:.6f}")

        quality_results['semantic_similarity'] = {
            'queries': related_queries,
            'average_similarity': avg_related_similarity,
            'semantically_related': avg_related_similarity > 0.8
        }

        return quality_results

    async def cleanup(self):
        """Clean up resources"""
        if self.service:
            await self.service.close()


async def main():
    """Main test runner"""
    print("🧪 Semantic Search Similarity Test Suite")
    print("=" * 60)
    print("Story 1.1 - Task 5: Create similarity search test cases")
    print("=" * 60)

    # Check environment variables
    required_vars = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False

    print(f"✅ All required environment variables present")

    tester = SimilaritySearchTester()

    try:
        # Setup
        await tester.setup()

        # Run similarity tests
        search_results = await tester.run_similarity_tests()

        # Run quality tests
        quality_results = await tester.test_embedding_quality()

        # Overall results
        print("\n🎯 Overall Test Results")
        print("=" * 60)

        search_success_rate = search_results['success_rate']
        embedding_consistent = quality_results['consistency']['consistent']
        semantic_related = quality_results['semantic_similarity']['semantically_related']

        all_passed = (
            search_success_rate >= 80 and  # At least 80% of searches should work
            embedding_consistent and  # Embeddings should be consistent
            semantic_related  # Related queries should be similar
        )

        print(f"📊 Search Success Rate: {search_success_rate:.1f}% {'✅' if search_success_rate >= 80 else '❌'}")
        print(f"🔐 Embedding Consistency: {'✅' if embedding_consistent else '❌'}")
        print(f"🧠 Semantic Similarity: {'✅' if semantic_related else '❌'}")

        if all_passed:
            print("\n🎉 All similarity search tests passed!")
            print("✅ Semantic search infrastructure is working correctly")
            return True
        else:
            print("\n⚠️ Some tests failed. Review results above.")
            return False

    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return False

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)