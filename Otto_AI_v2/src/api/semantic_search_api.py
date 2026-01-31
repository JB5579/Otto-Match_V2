"""
Otto.AI Semantic Search API Endpoints

Production-ready semantic search API endpoints for vehicle discovery.
Implements Story 1-3: Build Semantic Search API Endpoints

Features:
- Natural language vehicle search with semantic understanding
- Hybrid search combining vector similarity with traditional filters
- Performance optimized for <800ms response times
- Rate limiting and comprehensive error handling
- Real database integration with TARB compliance
"""

import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import uuid

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest
from src.semantic.vehicle_processing_service import VehicleProcessingService
from src.semantic.vehicle_database_service import VehicleDatabaseService

# RAG Strategy services (Story 1-9 through 1-12)
from src.search.search_orchestrator import SearchOrchestrator, SearchRequest as OrchestratorRequest
from src.search.query_expansion_service import QueryExpansionService
from src.search.hybrid_search_service import HybridSearchService
from src.search.reranking_service import RerankingService
from src.search.contextual_embedding_service import ContextualEmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for API
# ============================================================================

class SearchFilters(BaseModel):
    """Traditional search filters for hybrid search

    Story 3-7 Updates:
    - Added multi-select support for makes and vehicle_types
    - Uses effective_price for price filtering (handles NULL prices)
    - Removed features filter (no database support)
    """
    # Single-select filters (backward compatibility)
    make: Optional[str] = Field(None, description="Vehicle make (e.g., 'Toyota', 'Honda')")
    model: Optional[str] = Field(None, description="Vehicle model (e.g., 'Camry', 'Pilot')")
    vehicle_type: Optional[str] = Field(None, description="Vehicle type (e.g., 'SUV', 'Sedan', 'Truck')")

    # Multi-select filters (NEW - Story 3-7)
    makes: Optional[List[str]] = Field(None, description="Multiple vehicle makes (e.g., ['Toyota', 'Honda'])")
    vehicle_types: Optional[List[str]] = Field(None, description="Multiple vehicle types (e.g., ['SUV', 'Sedan'])")

    # Range filters
    year_min: Optional[int] = Field(None, ge=1900, le=2030, description="Minimum model year")
    year_max: Optional[int] = Field(None, ge=1900, le=2030, description="Maximum model year")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price (uses effective_price)")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price (uses effective_price)")
    mileage_max: Optional[int] = Field(None, ge=0, description="Maximum mileage")

    # Other filters
    fuel_type: Optional[str] = Field(None, description="Fuel type (e.g., 'Gasoline', 'Electric', 'Hybrid')")
    transmission: Optional[str] = Field(None, description="Transmission type")
    exterior_color: Optional[str] = Field(None, description="Exterior color preference")
    city: Optional[str] = Field(None, description="City location")
    state: Optional[str] = Field(None, description="State location")

    @validator('year_max')
    def validate_year_range(cls, v, values):
        if v is not None and 'year_min' in values and values['year_min'] is not None:
            if v < values['year_min']:
                raise ValueError('year_max must be greater than or equal to year_min')
        return v

    @validator('price_max')
    def validate_price_range(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v < values['price_min']:
                raise ValueError('price_max must be greater than or equal to price_min')
        return v

class SemanticSearchRequest(BaseModel):
    """Semantic search request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    filters: Optional[SearchFilters] = Field(None, description="Traditional search filters")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results to return")
    offset: int = Field(0, ge=0, le=1000, description="Number of results to skip")
    sort_by: str = Field("relevance", description="Sort by: relevance, price, year, mileage")
    sort_order: str = Field("desc", description="Sort order: asc, desc")
    include_similarity_scores: bool = Field(True, description="Include similarity scores in response")
    search_id: Optional[str] = Field(None, description="Unique search identifier for tracking")

    # RAG Strategy enhancements (Story 1-9 through 1-12)
    enable_expansion: bool = Field(True, description="Enable LLM query expansion")
    enable_reranking: bool = Field(True, description="Enable cross-encoder re-ranking")
    enable_hybrid: bool = Field(True, description="Enable hybrid search (vector + keyword + filters)")
    use_rag_pipeline: bool = Field(True, description="Use advanced RAG pipeline")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['relevance', 'price', 'year', 'mileage']
        if v not in allowed:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        allowed = ['asc', 'desc']
        if v not in allowed:
            raise ValueError(f'sort_order must be one of: {", ".join(allowed)}')
        return v

class VehicleResult(BaseModel):
    """Vehicle search result model"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str]
    vehicle_type: str
    price: float
    mileage: Optional[int]
    description: str
    features: List[str]
    exterior_color: str
    interior_color: str
    city: str
    state: str
    condition: str
    images: List[str] = []

    # Search-specific fields
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Semantic similarity score")
    match_explanation: Optional[str] = Field(None, description="Explanation of why this vehicle matches")
    preference_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Personal preference score")

class SemanticSearchResponse(BaseModel):
    """Semantic search response model"""
    query: str
    search_id: str
    total_results: int
    processing_time: float
    results: List[VehicleResult]
    filters_applied: Optional[Dict[str, Any]] = None
    search_metadata: Dict[str, Any] = {}

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

# ============================================================================
# Rate Limiting Implementation
# ============================================================================

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests: int = 0
    window_start: datetime = None

    def __post_init__(self):
        if self.window_start is None:
            self.window_start = datetime.now()

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_requests: int = 10, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.client_requests: Dict[str, RateLimitInfo] = {}

    def is_rate_limited(self, client_id: str) -> tuple[bool, Dict[str, Any]]:
        """Check if client is rate limited"""
        now = datetime.now()

        # Clean up expired entries
        expired_clients = [
            client for client, info in self.client_requests.items()
            if now - info.window_start > timedelta(minutes=self.window_minutes)
        ]
        for client in expired_clients:
            del self.client_requests[client]

        # Check current client
        if client_id not in self.client_requests:
            self.client_requests[client_id] = RateLimitInfo()

        info = self.client_requests[client_id]

        # Reset window if expired
        if now - info.window_start > timedelta(minutes=self.window_minutes):
            info.requests = 0
            info.window_start = now

        # Check rate limit
        if info.requests >= self.max_requests:
            return True, {
                "allowed": False,
                "limit": self.max_requests,
                "remaining": 0,
                "reset_time": info.window_start + timedelta(minutes=self.window_minutes),
                "retry_after": int((info.window_start + timedelta(minutes=self.window_minutes) - now).total_seconds())
            }

        # Increment request count
        info.requests += 1

        return False, {
            "allowed": True,
            "limit": self.max_requests,
            "remaining": self.max_requests - info.requests,
            "reset_time": info.window_start + timedelta(minutes=self.window_minutes)
        }

# ============================================================================
# Semantic Search Service
# ============================================================================

class SemanticSearchService:
    """Core semantic search service with RAG pipeline integration"""

    def __init__(self):
        self.embedding_service: Optional[OttoAIEmbeddingService] = None
        self.vehicle_db_service: Optional[VehicleDatabaseService] = None
        self.vehicle_processing_service: Optional[VehicleProcessingService] = None
        self.rate_limiter = RateLimiter(max_requests=10, window_minutes=1)

        # RAG Pipeline components (Story 1-9 through 1-12)
        self.search_orchestrator: Optional[SearchOrchestrator] = None
        self.rag_enabled = True  # Feature flag for RAG pipeline

        # Performance tracking
        self.search_stats = {
            "total_searches": 0,
            "avg_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rag_searches": 0,
            "legacy_searches": 0
        }

        # Simple cache for frequent queries
        self.query_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """Initialize the search service"""
        try:
            logger.info("🚀 Initializing Semantic Search Service...")

            # Initialize embedding service
            self.embedding_service = OttoAIEmbeddingService()
            if not await self.embedding_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize embedding service")

            # Initialize vehicle database service
            self.vehicle_db_service = VehicleDatabaseService()
            if not await self.vehicle_db_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize vehicle database service")

            # Initialize vehicle processing service
            self.vehicle_processing_service = VehicleProcessingService()
            if not await self.vehicle_processing_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize vehicle processing service")

            # Initialize RAG Pipeline (Story 1-9 through 1-12)
            try:
                self.search_orchestrator = SearchOrchestrator()
                if await self.search_orchestrator.initialize(
                    supabase_url, supabase_key, self.embedding_service
                ):
                    logger.info("✅ RAG Pipeline initialized (hybrid search + query expansion + re-ranking)")
                    self.rag_enabled = True
                else:
                    logger.warning("⚠️ RAG Pipeline initialization failed, using legacy search")
                    self.rag_enabled = False
            except Exception as rag_error:
                logger.warning(f"⚠️ RAG Pipeline not available: {rag_error}")
                self.rag_enabled = False

            logger.info("✅ Semantic Search Service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Semantic Search Service: {e}")
            return False

    def _get_cache_key(self, query: str, filters: Optional[SearchFilters], limit: int) -> str:
        """Generate cache key for search query"""
        filter_str = str(filters.dict()) if filters else "no_filters"
        cache_data = f"{query}:{filter_str}:{limit}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get results from cache if available and not expired"""
        if cache_key in self.query_cache:
            cached_data = self.query_cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=self.cache_ttl):
                self.search_stats["cache_hits"] += 1
                return cached_data["results"]
            else:
                # Remove expired entry
                del self.query_cache[cache_key]

        self.search_stats["cache_misses"] += 1
        return None

    def _store_in_cache(self, cache_key: str, results: Dict):
        """Store results in cache"""
        self.query_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now()
        }

        # Clean up old cache entries (keep only last 100)
        if len(self.query_cache) > 100:
            oldest_key = min(
                self.query_cache.keys(),
                key=lambda k: self.query_cache[k]["timestamp"]
            )
            del self.query_cache[oldest_key]

    async def semantic_search(self, request: SemanticSearchRequest, client_id: str) -> SemanticSearchResponse:
        """Perform semantic vehicle search with optional RAG pipeline"""
        start_time = time.time()

        # Generate search ID if not provided
        search_id = request.search_id or str(uuid.uuid4())

        try:
            # Check cache first
            cache_key = self._get_cache_key(request.query, request.filters, request.limit)
            cached_results = self._get_from_cache(cache_key)

            if cached_results:
                logger.info(f"Cache hit for search: {request.query[:50]}...")
                return SemanticSearchResponse(**cached_results)

            # Build database filters
            db_filters = {}
            if request.filters:
                filter_dict = request.filters.dict(exclude_unset=True)
                db_filters.update(filter_dict)

            # Use RAG Pipeline if enabled and requested
            if self.rag_enabled and request.use_rag_pipeline and self.search_orchestrator:
                return await self._rag_pipeline_search(
                    request, search_id, db_filters, client_id, start_time, cache_key
                )

            # Fallback to legacy search
            return await self._legacy_search(
                request, search_id, db_filters, client_id, start_time, cache_key
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Search failed after {processing_time:.3f}s: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Semantic search failed: {str(e)}"
            )

    async def _rag_pipeline_search(
        self,
        request: SemanticSearchRequest,
        search_id: str,
        db_filters: Dict,
        client_id: str,
        start_time: float,
        cache_key: str
    ) -> SemanticSearchResponse:
        """Execute search using RAG pipeline (Story 1-9 through 1-12)"""
        self.search_stats["rag_searches"] += 1

        # Create orchestrator request
        orch_request = OrchestratorRequest(
            query=request.query,
            filters=db_filters,
            limit=request.limit,
            offset=request.offset,
            enable_expansion=request.enable_expansion,
            enable_reranking=request.enable_reranking,
            enable_contextual=True
        )

        # Execute RAG pipeline
        orch_response = await self.search_orchestrator.search(orch_request)

        # Convert to API response format
        vehicle_results = []
        for result in orch_response.results:
            vehicle_result = VehicleResult(
                id=result.id,
                vin=result.vin,
                year=result.year,
                make=result.make,
                model=result.model,
                trim=result.trim,
                vehicle_type=result.vehicle_type or "",
                price=float(result.price) if result.price else 0,
                mileage=result.mileage,
                description=result.description or "",
                features=[],
                exterior_color="",
                interior_color="",
                city="",
                state="",
                condition="",
                images=[],
                similarity_score=result.similarity_score,
                match_explanation=None,
                preference_score=result.rerank_score
            )
            vehicle_results.append(vehicle_result)

        processing_time = time.time() - start_time
        response = SemanticSearchResponse(
            query=request.query,
            search_id=search_id,
            total_results=orch_response.total_results,
            processing_time=processing_time,
            results=vehicle_results,
            filters_applied=db_filters if db_filters else None,
            search_metadata={
                "search_type": "rag_pipeline",
                "client_id": client_id,
                "cache_used": False,
                "expansion_enabled": request.enable_expansion,
                "reranking_enabled": request.enable_reranking,
                "expansion_latency_ms": orch_response.expansion_latency_ms,
                "search_latency_ms": orch_response.search_latency_ms,
                "rerank_latency_ms": orch_response.rerank_latency_ms,
                "expanded_query": orch_response.metadata.get("expanded_query"),
                "extracted_filters": orch_response.metadata.get("extracted_filters")
            }
        )

        # Cache results
        response_dict = response.dict()
        self._store_in_cache(cache_key, response_dict)

        # Update statistics
        self.search_stats["total_searches"] += 1
        total_time = self.search_stats["avg_processing_time"] * (self.search_stats["total_searches"] - 1)
        self.search_stats["avg_processing_time"] = (total_time + processing_time) / self.search_stats["total_searches"]

        logger.info(
            f"✅ RAG search completed: {len(vehicle_results)} results in {processing_time:.3f}s "
            f"(expand: {orch_response.expansion_latency_ms:.0f}ms, "
            f"search: {orch_response.search_latency_ms:.0f}ms, "
            f"rerank: {orch_response.rerank_latency_ms:.0f}ms)"
        )

        return response

    async def _legacy_search(
        self,
        request: SemanticSearchRequest,
        search_id: str,
        db_filters: Dict,
        client_id: str,
        start_time: float,
        cache_key: str
    ) -> SemanticSearchResponse:
        """Execute legacy vector-only search"""
        self.search_stats["legacy_searches"] += 1

        # Generate embedding for search query
        embedding_request = EmbeddingRequest(text=request.query)
        embedding_response = await self.embedding_service.generate_embedding(embedding_request)
        query_embedding = embedding_response.embedding

        # Perform hybrid search (vector similarity + traditional filters)
        search_results = await self.vehicle_db_service.hybrid_search(
            query_embedding=query_embedding,
            filters=db_filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )

        # Convert to API response format
        vehicle_results = []
        for result in search_results["results"]:
            vehicle_data = result["vehicle"]

            vehicle_result = VehicleResult(
                id=vehicle_data.get("id", ""),
                vin=vehicle_data.get("vin", ""),
                year=vehicle_data.get("year", 0),
                make=vehicle_data.get("make", ""),
                model=vehicle_data.get("model", ""),
                trim=vehicle_data.get("trim"),
                vehicle_type=vehicle_data.get("vehicle_type", ""),
                price=float(vehicle_data.get("price", 0)),
                mileage=vehicle_data.get("mileage"),
                description=vehicle_data.get("description", ""),
                features=vehicle_data.get("features", []),
                exterior_color=vehicle_data.get("exterior_color", ""),
                interior_color=vehicle_data.get("interior_color", ""),
                city=vehicle_data.get("city", ""),
                state=vehicle_data.get("state", ""),
                condition=vehicle_data.get("condition", ""),
                images=vehicle_data.get("images", []),
                similarity_score=result.get("similarity_score"),
                match_explanation=result.get("match_explanation"),
                preference_score=result.get("preference_score")
            )
            vehicle_results.append(vehicle_result)

        # Build response
        processing_time = time.time() - start_time
        response = SemanticSearchResponse(
            query=request.query,
            search_id=search_id,
            total_results=search_results["total_count"],
            processing_time=processing_time,
            results=vehicle_results,
            filters_applied=db_filters if db_filters else None,
            search_metadata={
                "embedding_dim": len(query_embedding),
                "search_type": "legacy",
                "client_id": client_id,
                "cache_used": False
            }
        )

        # Cache results
        response_dict = response.dict()
        self._store_in_cache(cache_key, response_dict)

        # Update statistics
        self.search_stats["total_searches"] += 1
        total_time = self.search_stats["avg_processing_time"] * (self.search_stats["total_searches"] - 1)
        self.search_stats["avg_processing_time"] = (total_time + processing_time) / self.search_stats["total_searches"]

        logger.info(f"✅ Legacy search completed: {len(vehicle_results)} results in {processing_time:.3f}s")

        return response

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search performance statistics"""
        return {
            **self.search_stats,
            "cache_size": len(self.query_cache),
            "rate_limit_clients": len(self.rate_limiter.client_requests)
        }

# ============================================================================
# FastAPI Application
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Otto.AI Semantic Search API",
    description="Production semantic search endpoints for vehicle discovery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global search service
search_service: Optional[SemanticSearchService] = None

# ============================================================================
# Startup and Dependencies
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the search service on startup"""
    global search_service

    try:
        logger.info("🚀 Starting Otto.AI Semantic Search API...")

        # Check required environment variables
        required_vars = [
            'OPENROUTER_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_DB_PASSWORD'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Initialize search service
        search_service = SemanticSearchService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not await search_service.initialize(supabase_url, supabase_key):
            raise Exception("Failed to initialize search service")

        logger.info("✅ Semantic Search API ready for requests")
        logger.info("📖 API docs available at: /docs")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

def get_client_id(request: Request) -> str:
    """Extract client ID for rate limiting"""
    # Try to get client IP, fallback to user agent hash
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    if client_ip:
        return f"ip_{client_ip}"
    else:
        return f"ua_{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"

async def rate_limit_check(client_id: str):
    """Check rate limiting and raise exception if exceeded"""
    if search_service:
        is_limited, limit_info = search_service.rate_limiter.is_rate_limited(client_id)

        if is_limited:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit_info["limit"],
                    "retry_after": limit_info["retry_after"]
                }
            )

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Otto.AI Semantic Search API",
        "version": "1.0.0",
        "status": "ready",
        "endpoints": {
            "health": "/health",
            "semantic_search": "/api/search/semantic",
            "search_stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "search_service": search_service is not None,
        "stats": search_service.get_search_stats() if search_service else {}
    }

@app.post("/api/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search_endpoint(
    request: SemanticSearchRequest,
    client_id: str = Depends(get_client_id)
):
    """
    Perform semantic vehicle search

    - **query**: Natural language search query (required)
    - **filters**: Traditional filters (optional)
    - **limit**: Maximum results (1-100, default: 20)
    - **offset**: Results to skip (0-1000, default: 0)
    - **sort_by**: Sort by relevance, price, year, or mileage
    - **sort_order**: Sort order asc or desc

    Returns vehicles ranked by semantic relevance to the query.
    """
    try:
        # Rate limiting check
        await rate_limit_check(client_id)

        # Validate query length
        if len(request.query.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters long"
            )

        # Perform semantic search
        result = await search_service.semantic_search(request, client_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during search"
        )

@app.get("/api/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search_get_endpoint(
    query: str = Query(..., min_length=1, max_length=1000, description="Natural language search query"),
    make: Optional[str] = Query(None, description="Vehicle make filter"),
    model: Optional[str] = Query(None, description="Vehicle model filter"),
    year_min: Optional[int] = Query(None, ge=1900, le=2030, description="Minimum year"),
    year_max: Optional[int] = Query(None, ge=1900, le=2030, description="Maximum year"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, le=1000, description="Results offset"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price, year, mileage"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    client_id: str = Depends(get_client_id)
):
    """GET endpoint for semantic search (for simple queries)"""

    # Build filters from query parameters
    filters = None
    if any([make, model, year_min, year_max, price_min, price_max]):
        filters = SearchFilters(
            make=make,
            model=model,
            year_min=year_min,
            year_max=year_max,
            price_min=price_min,
            price_max=price_max
        )

    # Create search request
    request = SemanticSearchRequest(
        query=query,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Use POST endpoint logic
    return await semantic_search_endpoint(request, client_id)

@app.get("/stats")
async def get_search_statistics():
    """Get search performance statistics"""
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not available")

    return search_service.get_search_stats()

@app.get("/sample_queries")
async def get_sample_queries():
    """Get sample search queries for testing"""
    return {
        "sample_queries": [
            {
                "query": "family SUV good for road trips with lots of cargo space",
                "description": "Looking for family-friendly SUV with cargo capacity"
            },
            {
                "query": "eco-friendly commuter car",
                "description": "Environmentally conscious daily driver"
            },
            {
                "query": "luxury sports car under $50000",
                "description": "High-performance vehicle within budget"
            },
            {
                "query": "reliable truck for hauling equipment",
                "description": "Work vehicle with towing capacity"
            },
            {
                "query": "compact car with good gas mileage",
                "description": "Fuel-efficient small vehicle"
            }
        ]
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            timestamp=datetime.now()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            timestamp=datetime.now()
        ).dict()
    )

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Otto.AI Semantic Search API...")
    print("📖 Production-ready semantic search endpoints")
    print("🌐 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")

    # Run the API
    uvicorn.run(
        "semantic_search_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Production mode
        log_level="info"
    )