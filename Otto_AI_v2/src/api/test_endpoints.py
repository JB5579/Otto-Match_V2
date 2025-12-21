"""
Test API Endpoints for Semantic Search

Simple FastAPI endpoints for testing the semantic search functionality
with sample vehicle data during development.

Story: 1.1-initialize-semantic-search-infrastructure
Task: Implement basic API endpoints for testing (AC: #5)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest
from src.semantic.sample_vehicle_data import SAMPLE_VEHICLES

# Pydantic models for API
class VehicleSearchResponse(BaseModel):
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str]
    vehicle_type: str
    price: int
    similarity_score: float
    description: str
    features: List[str]
    exterior_color: str
    interior_color: str
    city: str
    state: str
    condition: str

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class EmbeddingTestRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

# Initialize FastAPI app
app = FastAPI(
    title="Otto.AI Semantic Search Test API",
    description="Test endpoints for semantic search functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
embedding_service: Optional[OttoAIEmbeddingService] = None
vehicle_embeddings: Dict[str, Dict] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global embedding_service, vehicle_embeddings

    try:
        print("🚀 Initializing Otto.AI Test API...")

        # Initialize embedding service
        embedding_service = OttoAIEmbeddingService()

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not await embedding_service.initialize(supabase_url, supabase_key):
            raise Exception("Failed to initialize embedding service")

        # Generate embeddings for sample vehicles
        await generate_vehicle_embeddings()

        print(f"✅ API ready with {len(vehicle_embeddings)} vehicle embeddings")
        print("🌐 Test endpoints available at: http://localhost:8000")
        print("📖 API docs at: http://localhost:8000/docs")

    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        raise


async def generate_vehicle_embeddings():
    """Generate embeddings for all sample vehicles"""
    global vehicle_embeddings

    print("🧠 Generating embeddings for sample vehicles...")

    for vehicle in SAMPLE_VEHICLES:
        try:
            # Create comprehensive text for embedding
            vehicle_text = f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle.get('trim', '')} {vehicle['vehicle_type']} {vehicle['description']} {' '.join(vehicle.get('features', []))}"

            # Generate embedding
            request = EmbeddingRequest(text=vehicle_text)
            response = await embedding_service.generate_embedding(request)

            # Store embedding
            vehicle_embeddings[vehicle['vin']] = {
                'embedding': response.embedding,
                'vehicle': vehicle,
                'search_text': vehicle_text
            }

        except Exception as e:
            print(f"❌ Failed to generate embedding for {vehicle['vin']}: {str(e)}")
            continue


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import numpy as np

    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Otto.AI Semantic Search Test API",
        "version": "1.0.0",
        "status": "ready",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "vehicles": "/vehicles",
            "test_embedding": "/test_embedding"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "embedding_service": embedding_service is not None,
        "vehicle_count": len(vehicle_embeddings)
    }


@app.get("/vehicles")
async def get_vehicles():
    """Get all sample vehicles"""
    return {
        "count": len(SAMPLE_VEHICLES),
        "vehicles": SAMPLE_VEHICLES
    }


@app.post("/search")
async def search_vehicles(search_query: SearchQuery):
    """Search vehicles using semantic similarity"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="Embedding service not initialized")

        # Generate embedding for search query
        request = EmbeddingRequest(text=search_query.query)
        response = await embedding_service.generate_embedding(request)
        query_embedding = response.embedding

        # Calculate similarities
        similarities = []
        for vin, vehicle_data in vehicle_embeddings.items():
            similarity = cosine_similarity(query_embedding, vehicle_data['embedding'])
            similarities.append((vehicle_data['vehicle'], similarity))

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k results
        top_results = similarities[:search_query.top_k]

        # Convert to response model
        search_results = []
        for vehicle, score in top_results:
            search_results.append(VehicleSearchResponse(
                vin=vehicle['vin'],
                year=vehicle['year'],
                make=vehicle['make'],
                model=vehicle['model'],
                trim=vehicle.get('trim'),
                vehicle_type=vehicle['vehicle_type'],
                price=vehicle['price'],
                similarity_score=round(float(score), 4),
                description=vehicle['description'],
                features=vehicle['features'],
                exterior_color=vehicle['exterior_color'],
                interior_color=vehicle['interior_color'],
                city=vehicle['city'],
                state=vehicle['state'],
                condition=vehicle['condition']
            ))

        return {
            "query": search_query.query,
            "total_results": len(search_results),
            "results": search_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/search")
async def search_vehicles_get(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return")
):
    """Search vehicles using GET request"""
    search_query = SearchQuery(query=query, top_k=top_k)
    return await search_vehicles(search_query)


@app.post("/test_embedding")
async def test_embedding(request: EmbeddingTestRequest):
    """Test embedding generation"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="Embedding service not initialized")

        # Generate embedding
        embedding_request = EmbeddingRequest(
            text=request.text,
            context=request.context
        )
        response = await embedding_service.generate_embedding(embedding_request)

        return {
            "text": request.text,
            "embedding_dim": response.embedding_dim,
            "processing_time": response.processing_time,
            "sample_values": response.embedding[:5],  # First 5 values
            "success": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.get("/stats")
async def get_search_stats():
    """Get search statistics"""
    vehicle_stats = {}
    for vehicle in SAMPLE_VEHICLES:
        vehicle_type = vehicle['vehicle_type']
        if vehicle_type not in vehicle_stats:
            vehicle_stats[vehicle_type] = 0
        vehicle_stats[vehicle_type] += 1

    price_stats = {
        "min_price": min(v['price'] for v in SAMPLE_VEHICLES),
        "max_price": max(v['price'] for v in SAMPLE_VEHICLES),
        "avg_price": sum(v['price'] for v in SAMPLE_VEHICLES) / len(SAMPLE_VEHICLES)
    }

    return {
        "total_vehicles": len(SAMPLE_VEHICLES),
        "vehicle_types": vehicle_stats,
        "price_stats": price_stats,
        "embeddings_generated": len(vehicle_embeddings),
        "embedding_dim": 3072  # OpenAI text-embedding-3-large dimensions
    }


@app.get("/sample_queries")
async def get_sample_queries():
    """Get sample search queries for testing"""
    from src.semantic.sample_vehicle_data import create_sample_search_queries

    return {
        "sample_queries": create_sample_search_queries()
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error"}


if __name__ == "__main__":
    print("🚀 Starting Otto.AI Semantic Search Test API...")
    print("📖 This is a development API for testing semantic search functionality")
    print("🌐 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")

    # Check environment variables
    required_vars = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before starting the API.")
        sys.exit(1)

    # Run the API
    uvicorn.run(
        "test_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )