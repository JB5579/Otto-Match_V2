"""
Otto.AI Enhanced Semantic Search API with AI Intelligence

Extends the semantic search API to include AI-powered vehicle intelligence
from Groq Compound AI for enhanced search and filtering capabilities.
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

# Import existing search API components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.api.semantic_search_api import (
    SemanticSearchService,
    SemanticSearchRequest,
    SemanticSearchResponse,
    VehicleResult,
    SearchFilters,
    RateLimiter,
    get_client_id,
    rate_limit_check
)
from src.services.vehicle_intelligence_service import VehicleIntelligenceService
from src.services.ai_intelligence_database_service import AIIntelligenceDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Enhanced Pydantic Models with AI Intelligence
# ============================================================================

class AISearchFilters(SearchFilters):
    """Extended search filters with AI intelligence options"""
    min_ai_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Minimum AI confidence score")
    market_demand: Optional[str] = Field(None, description="Market demand level: high, medium, low")
    max_price_vs_market: Optional[float] = Field(None, description="Maximum price as percentage of market average (e.g., 1.2 for 120%)")
    has_competitive_advantages: bool = Field(False, description="Only show vehicles with competitive advantages")
    exclude_common_complaints: bool = Field(False, description="Exclude vehicles with common complaints")
    availability_min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum availability score")

class VehicleIntelligenceResult(BaseModel):
    """Vehicle intelligence data for API response"""
    market_price_range: Optional[Dict[str, float]] = None
    market_average_price: Optional[float] = None
    price_confidence: float = 0.0
    market_demand: str = "unknown"
    availability_score: float = 0.0
    days_on_market_avg: Optional[int] = None
    feature_popularity: Dict[str, float] = {}
    competitive_advantages: List[str] = []
    common_complaints: List[str] = []
    market_insights: List[Dict[str, Any]] = []
    ai_confidence_overall: float = 0.0
    ai_model_used: str = ""
    generated_at: Optional[str] = None

class EnhancedVehicleResult(VehicleResult):
    """Extended vehicle result with AI intelligence"""
    ai_intelligence: Optional[VehicleIntelligenceResult] = None
    price_vs_market_average: Optional[float] = None  # Price as percentage of market average
    ai_confidence: float = 0.0
    has_intelligence: bool = False

class AISearchRequest(SemanticSearchRequest):
    """Enhanced search request with AI options"""
    filters: Optional[AISearchFilters] = Field(None, description="AI-enhanced search filters")
    include_ai_intelligence: bool = Field(True, description="Include AI intelligence in results")
    ai_priority_sorting: bool = Field(False, description="Prioritize results with high AI confidence")

class AISearchResponse(SemanticSearchResponse):
    """Enhanced search response with AI intelligence"""
    results: List[EnhancedVehicleResult]
    ai_filters_applied: Optional[Dict[str, Any]] = None
    ai_processing_metadata: Dict[str, Any] = {}

# ============================================================================
# Enhanced Search Service with AI Intelligence
# ============================================================================

class EnhancedSemanticSearchService(SemanticSearchService):
    """Extended semantic search service with AI intelligence"""

    def __init__(self):
        super().__init__()
        self.ai_service = VehicleIntelligenceService()
        self.ai_db_service = AIIntelligenceDatabaseService()

        # AI-specific statistics
        self.ai_stats = {
            "ai_enhanced_searches": 0,
            "ai_cache_hits": 0,
            "ai_intelligence_included": 0,
            "avg_ai_processing_time": 0.0
        }

    async def ai_enhanced_search(self, request: AISearchRequest, client_id: str) -> AISearchResponse:
        """Perform AI-enhanced semantic search"""
        start_time = time.time()

        # Generate search ID if not provided
        search_id = request.search_id or str(uuid.uuid4())

        try:
            # Convert to base search request for semantic search
            base_request = SemanticSearchRequest(
                query=request.query,
                filters=request.filters,
                limit=request.limit,
                offset=request.offset,
                sort_by=request.sort_by,
                sort_order=request.sort_order,
                include_similarity_scores=request.include_similarity_scores,
                search_id=search_id
            )

            # Perform base semantic search
            base_response = await self.semantic_search(base_request, client_id)

            # Convert to enhanced results
            enhanced_results = []
            vehicle_ids = []

            for vehicle_result in base_response.results:
                enhanced_result = EnhancedVehicleResult(**vehicle_result.dict())
                vehicle_ids.append(enhanced_result.id)
                enhanced_results.append(enhanced_result)

            # Fetch AI intelligence if requested
            ai_intelligence_map = {}
            if request.include_ai_intelligence and enhanced_results:
                ai_start_time = time.time()
                logger.info(f"Fetching AI intelligence for {len(enhanced_results)} vehicles...")

                # Get AI intelligence for vehicles
                ai_intelligence_map = await self._batch_get_ai_intelligence(enhanced_results)

                ai_processing_time = time.time() - ai_start_time
                self.ai_stats["avg_ai_processing_time"] = (
                    (self.ai_stats["avg_ai_processing_time"] * self.ai_stats["ai_enhanced_searches"] + ai_processing_time) /
                    (self.ai_stats["ai_enhanced_searches"] + 1)
                )

                logger.info(f"AI intelligence fetched in {ai_processing_time:.2f}s")

            # Apply AI filters and enhance results
            filtered_results = []
            ai_filters = {}

            for vehicle_result in enhanced_results:
                vehicle_id = vehicle_result.id

                # Add AI intelligence to result
                ai_intelligence = ai_intelligence_map.get(vehicle_id)
                if ai_intelligence:
                    vehicle_result.ai_intelligence = self._convert_intelligence_to_result(ai_intelligence)
                    vehicle_result.ai_confidence = ai_intelligence.confidence_overall
                    vehicle_result.has_intelligence = True

                    # Calculate price vs market average
                    if (ai_intelligence.market_average_price and
                        vehicle_result.price > 0 and
                        ai_intelligence.market_average_price > 0):
                        vehicle_result.price_vs_market_average = (
                            vehicle_result.price / float(ai_intelligence.market_average_price)
                        )

                # Apply AI filters
                if self._passes_ai_filters(vehicle_result, request.filters, ai_filters):
                    filtered_results.append(vehicle_result)

            # Apply AI priority sorting if requested
            if request.ai_priority_sorting and filtered_results:
                filtered_results.sort(
                    key=lambda v: (
                        v.ai_confidence,
                        v.price_vs_market_average if v.price_vs_market_average and v.price_vs_market_average <= 1.0 else 2.0,
                        v.similarity_score or 0.0
                    ),
                    reverse=True
                )

            # Build enhanced response
            processing_time = time.time() - start_time

            # Convert any AI filter values for response
            ai_filters_response = {}
            if request.filters:
                filter_dict = request.filters.dict(exclude_unset=True)
                ai_filters_response = {k: v for k, v in filter_dict.items()
                                     if k.startswith('ai_') or k in ['market_demand', 'max_price_vs_market']}

            response = AISearchResponse(
                query=request.query,
                search_id=search_id,
                total_results=len(filtered_results),
                processing_time=processing_time,
                results=filtered_results,
                filters_applied=base_response.filters_applied,
                ai_filters_applied=ai_filters_response or None,
                search_metadata={
                    **base_response.search_metadata,
                    "ai_enhanced": True,
                    "ai_results_count": len([r for r in filtered_results if r.has_intelligence]),
                    "ai_avg_confidence": sum(r.ai_confidence for r in filtered_results) / len(filtered_results) if filtered_results else 0.0
                },
                ai_processing_metadata={
                    "ai_processing_time": self.ai_stats["avg_ai_processing_time"],
                    "ai_cache_hits": self.ai_stats["ai_cache_hits"],
                    "ai_intelligence_included": self.ai_stats["ai_intelligence_included"]
                }
            )

            # Update statistics
            self.ai_stats["ai_enhanced_searches"] += 1
            if request.include_ai_intelligence:
                self.ai_stats["ai_intelligence_included"] += 1

            logger.info(f"✅ AI-enhanced search completed: {len(filtered_results)} results in {processing_time:.3f}s")

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ AI-enhanced search failed after {processing_time:.3f}s: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"AI-enhanced search failed: {str(e)}"
            )

    async def _batch_get_ai_intelligence(
        self,
        vehicles: List[EnhancedVehicleResult]
    ) -> Dict[str, Any]:
        """Get AI intelligence for multiple vehicles efficiently"""

        intelligence_map = {}

        try:
            # First, check database for existing intelligence
            vehicle_ids = [v.id for v in vehicles]
            db_intelligence = await self._get_intelligence_from_db(vehicle_ids)

            # Identify vehicles that need fresh intelligence
            vehicles_needing_ai = []
            for vehicle in vehicles:
                if vehicle.id not in db_intelligence:
                    # Create request for AI service
                    vehicles_needing_ai.append({
                        "make": vehicle.make,
                        "model": vehicle.model,
                        "year": vehicle.year,
                        "vin": vehicle.vin,
                        "current_price": vehicle.price
                    })

            # Fetch fresh intelligence for missing vehicles
            if vehicles_needing_ai:
                fresh_intelligence = await self.ai_service.batch_get_intelligence(vehicles_needing_ai)

                # Cache the fresh intelligence
                for intel in fresh_intelligence:
                    await self.ai_db_service.cache_intelligence(intel)
                    intelligence_map[intel.vehicle_id] = intel

            # Combine results
            for vehicle_id, intel_data in db_intelligence.items():
                intelligence_map[vehicle_id] = intel_data

        except Exception as e:
            logger.error(f"Error batch fetching AI intelligence: {str(e)}")

        return intelligence_map

    async def _get_intelligence_from_db(self, vehicle_ids: List[str]) -> Dict[str, Any]:
        """Get existing intelligence from database"""
        try:
            # This would involve querying the vehicle_listings table with AI intelligence columns
            # For now, return empty dict - would be implemented based on specific DB schema
            return {}
        except Exception as e:
            logger.error(f"Error getting intelligence from DB: {str(e)}")
            return {}

    def _passes_ai_filters(
        self,
        vehicle: EnhancedVehicleResult,
        filters: Optional[AISearchFilters],
        ai_filters: Dict[str, Any]
    ) -> bool:
        """Check if vehicle passes AI intelligence filters"""

        if not filters:
            return True

        # Track which filters are applied
        filters_applied = 0

        # Minimum AI confidence
        if filters.min_ai_confidence > 0:
            filters_applied += 1
            if vehicle.ai_confidence < filters.min_ai_confidence:
                return False

        # Market demand filter
        if filters.market_demand:
            filters_applied += 1
            if (not vehicle.ai_intelligence or
                vehicle.ai_intelligence.market_demand != filters.market_demand):
                return False

        # Price vs market average filter
        if filters.max_price_vs_market:
            filters_applied += 1
            if (not vehicle.price_vs_market_average or
                vehicle.price_vs_market_average > filters.max_price_vs_market):
                return False

        # Competitive advantages filter
        if filters.has_competitive_advantages:
            filters_applied += 1
            if (not vehicle.ai_intelligence or
                len(vehicle.ai_intelligence.competitive_advantages) == 0):
                return False

        # Exclude common complaints filter
        if filters.exclude_common_complaints:
            filters_applied += 1
            if (not vehicle.ai_intelligence or
                len(vehicle.ai_intelligence.common_complaints) > 0):
                return False

        # Minimum availability score
        if filters.availability_min_score > 0:
            filters_applied += 1
            if (not vehicle.ai_intelligence or
                vehicle.ai_intelligence.availability_score < filters.availability_min_score):
                return False

        # Update filters applied count
        if filters_applied > 0:
            ai_filters["ai_filters_count"] = filters_applied

        return True

    def _convert_intelligence_to_result(self, intelligence) -> VehicleIntelligenceResult:
        """Convert VehicleIntelligence to API response format"""

        # Convert price range
        price_range = None
        if intelligence.market_price_range:
            price_range = {
                "min": float(intelligence.market_price_range[0]) if intelligence.market_price_range[0] else None,
                "max": float(intelligence.market_price_range[1]) if intelligence.market_price_range[1] else None
            }

        # Convert market insights
        insights = []
        for insight in (intelligence.insights or []):
            insights.append({
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "confidence": insight.confidence,
                "sources": [
                    {
                        "source_name": source.source_name,
                        "source_url": source.source_url,
                        "source_type": source.source_type,
                        "reliability_score": source.reliability_score
                    }
                    for source in insight.sources
                ],
                "data_points": insight.data_points,
                "relevance_score": insight.relevance_score
            })

        return VehicleIntelligenceResult(
            market_price_range=price_range,
            market_average_price=float(intelligence.market_average_price) if intelligence.market_average_price else None,
            price_confidence=intelligence.price_confidence,
            market_demand=intelligence.market_demand,
            availability_score=intelligence.availability_score,
            days_on_market_avg=intelligence.days_on_market_avg,
            feature_popularity=intelligence.feature_popularity or {},
            competitive_advantages=intelligence.competitive_advantages or [],
            common_complaints=intelligence.common_complaints or [],
            market_insights=insights,
            ai_confidence_overall=intelligence.confidence_overall,
            ai_model_used=intelligence.ai_model_used,
            generated_at=intelligence.generated_at.isoformat() if intelligence.generated_at else None
        )

    def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI-specific statistics"""
        return {
            **self.ai_stats,
            "cache_size": len(self.ai_service._cache) if hasattr(self.ai_service, '_cache') else 0
        }

# ============================================================================
# Enhanced FastAPI Application
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Otto.AI Enhanced Semantic Search API",
    description="AI-enhanced semantic search endpoints with Groq Compound AI intelligence",
    version="2.0.0",
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

# Global enhanced search service
enhanced_search_service: Optional[EnhancedSemanticSearchService] = None

# ============================================================================
# Startup and Dependencies
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize the enhanced search service on startup"""
    global enhanced_search_service

    try:
        logger.info("🚀 Starting Otto.AI Enhanced Semantic Search API...")

        # Check required environment variables
        required_vars = [
            'OPENROUTER_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_DB_PASSWORD',
            'GROQ_API_KEY'  # Required for AI intelligence
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Initialize enhanced search service
        enhanced_search_service = EnhancedSemanticSearchService()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not await enhanced_search_service.initialize(supabase_url, supabase_key):
            raise Exception("Failed to initialize enhanced search service")

        logger.info("✅ Enhanced Semantic Search API ready for requests")
        logger.info("🤖 AI Intelligence features enabled")
        logger.info("📖 API docs available at: /docs")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# ============================================================================
# Enhanced API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with enhanced capabilities"""
    return {
        "service": "Otto.AI Enhanced Semantic Search API",
        "version": "2.0.0",
        "status": "ready",
        "features": [
            "Semantic Search",
            "AI-Powered Intelligence",
            "Market Analysis",
            "Enhanced Filtering"
        ],
        "endpoints": {
            "health": "/health",
            "ai_search": "/api/search/ai-enhanced",
            "search_stats": "/stats",
            "ai_stats": "/ai-stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "search_service": enhanced_search_service is not None,
        "ai_intelligence_enabled": True,
        "stats": enhanced_search_service.get_search_stats() if enhanced_search_service else {},
        "ai_stats": enhanced_search_service.get_ai_stats() if enhanced_search_service else {}
    }

@app.post("/api/search/ai-enhanced", response_model=AISearchResponse)
async def ai_enhanced_search_endpoint(
    request: AISearchRequest,
    client_id: str = Depends(get_client_id)
):
    """
    Perform AI-enhanced semantic vehicle search

    Extends standard semantic search with:
    - AI-powered market intelligence
    - Advanced filtering by AI confidence
    - Price vs market analysis
    - Competitive advantages insights
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

        # Perform AI-enhanced search
        result = await enhanced_search_service.ai_enhanced_search(request, client_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI-enhanced search endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during AI-enhanced search"
        )

@app.get("/api/search/ai-enhanced", response_model=AISearchResponse)
async def ai_enhanced_search_get_endpoint(
    query: str = Query(..., min_length=1, max_length=1000, description="Natural language search query"),
    make: Optional[str] = Query(None, description="Vehicle make filter"),
    model: Optional[str] = Query(None, description="Vehicle model filter"),
    year_min: Optional[int] = Query(None, ge=1900, le=2030, description="Minimum year"),
    year_max: Optional[int] = Query(None, ge=1900, le=2030, description="Maximum year"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_ai_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum AI confidence"),
    market_demand: Optional[str] = Query(None, description="Market demand level"),
    max_price_vs_market: Optional[float] = Query(None, description="Max price as % of market average"),
    has_competitive_advantages: bool = Query(False, description="Vehicles with competitive advantages only"),
    exclude_common_complaints: bool = Query(False, description="Exclude vehicles with complaints"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, le=1000, description="Results offset"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price, year, mileage"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    include_ai_intelligence: bool = Query(True, description="Include AI intelligence"),
    ai_priority_sorting: bool = Query(False, description="Prioritize high AI confidence"),
    client_id: str = Depends(get_client_id)
):
    """GET endpoint for AI-enhanced semantic search"""

    # Build filters from query parameters
    filters = None
    if any([make, model, year_min, year_max, price_min, price_max,
            min_ai_confidence > 0, market_demand, max_price_vs_market,
            has_competitive_advantages, exclude_common_complaints]):
        filters = AISearchFilters(
            make=make,
            model=model,
            year_min=year_min,
            year_max=year_max,
            price_min=price_min,
            price_max=price_max,
            min_ai_confidence=min_ai_confidence,
            market_demand=market_demand,
            max_price_vs_market=max_price_vs_market,
            has_competitive_advantages=has_competitive_advantages,
            exclude_common_complaints=exclude_common_complaints
        )

    # Create search request
    request = AISearchRequest(
        query=query,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
        include_ai_intelligence=include_ai_intelligence,
        ai_priority_sorting=ai_priority_sorting
    )

    # Use POST endpoint logic
    return await ai_enhanced_search_endpoint(request, client_id)

@app.get("/ai-stats")
async def get_ai_statistics():
    """Get AI intelligence statistics"""
    if not enhanced_search_service:
        raise HTTPException(status_code=503, detail="Enhanced search service not available")

    return enhanced_search_service.get_ai_stats()

@app.get("/sample-ai-queries")
async def get_sample_ai_queries():
    """Get sample AI-enhanced search queries"""
    return {
        "sample_ai_queries": [
            {
                "query": "reliable SUV under $30000",
                "ai_filters": {
                    "min_ai_confidence": 0.7,
                    "market_demand": "high",
                    "exclude_common_complaints": True
                },
                "description": "High-demand SUVs with good reliability ratings"
            },
            {
                "query": "luxury sedan with good resale value",
                "ai_filters": {
                    "has_competitive_advantages": True,
                    "max_price_vs_market": 1.1
                },
                "description": "Luxury vehicles priced near market average"
            },
            {
                "query": "fuel efficient commuter car",
                "ai_filters": {
                    "min_ai_confidence": 0.6,
                    "availability_min_score": 0.7
                },
                "description": "Readily available fuel-efficient vehicles"
            },
            {
                "query": "family vehicle with high safety ratings",
                "ai_filters": {
                    "market_demand": "medium",
                    "has_competitive_advantages": True
                },
                "description": "Family vehicles with competitive safety features"
            }
        ]
    }

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Otto.AI Enhanced Semantic Search API...")
    print("🤖 AI Intelligence features powered by Groq Compound AI")
    print("🌐 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")

    # Run the API
    import uvicorn
    uvicorn.run(
        "enhanced_semantic_search_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Production mode
        log_level="info"
    )