"""
Otto.AI Search Orchestrator

Coordinates the full RAG search pipeline:
1. Query Expansion (LLM-powered)
2. Hybrid Search (Vector + Keyword + Filters via RRF)
3. Re-ranking (Cross-encoder)

Implements the RAG strategy from docs/rag-strategy-spec.md
"""

import os
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .query_expansion_service import QueryExpansionService, QueryExpansion
from .hybrid_search_service import HybridSearchService, HybridSearchResult
from .reranking_service import RerankingService, RerankResult
from .contextual_embedding_service import ContextualEmbeddingService

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request parameters"""
    query: str = Field(..., min_length=1, max_length=1000)
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

    # Feature flags
    enable_expansion: bool = Field(True, description="Enable query expansion")
    enable_reranking: bool = Field(True, description="Enable cross-encoder re-ranking")
    enable_contextual: bool = Field(True, description="Use contextual embeddings")


class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    vehicle_type: Optional[str] = None
    price: Optional[float] = None
    price_source: Optional[str] = None
    mileage: Optional[int] = None
    description: Optional[str] = None

    # Scores
    similarity_score: float = Field(0.0, description="Final relevance score")
    vector_score: float = Field(0.0, description="Vector similarity")
    keyword_score: float = Field(0.0, description="Keyword match score")
    hybrid_score: float = Field(0.0, description="RRF fusion score")
    rerank_score: Optional[float] = Field(None, description="Cross-encoder score")


class SearchResponse(BaseModel):
    """Complete search response"""
    query: str
    results: List[SearchResult]
    total_results: int

    # Timing
    total_latency_ms: float
    expansion_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    search_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchOrchestrator:
    """
    Orchestrates the full RAG search pipeline.

    Pipeline stages:
    1. Query Expansion: Expand query with synonyms, extract implicit filters
    2. Embedding: Generate query embedding (optionally contextual)
    3. Hybrid Search: Vector + Keyword + Filters with RRF fusion
    4. Re-ranking: Cross-encoder for precise relevance (optional)
    """

    def __init__(
        self,
        expansion_service: Optional[QueryExpansionService] = None,
        hybrid_service: Optional[HybridSearchService] = None,
        rerank_service: Optional[RerankingService] = None,
        contextual_service: Optional[ContextualEmbeddingService] = None,
        embedding_service=None
    ):
        self.expansion_service = expansion_service or QueryExpansionService()
        self.hybrid_service = hybrid_service or HybridSearchService()
        self.rerank_service = rerank_service or RerankingService()
        self.contextual_service = contextual_service or ContextualEmbeddingService()
        self.embedding_service = embedding_service

        # Statistics
        self.stats = {
            "total_searches": 0,
            "avg_total_latency_ms": 0.0,
            "expansion_enabled": 0,
            "reranking_enabled": 0
        }

    async def initialize(
        self,
        supabase_url: str,
        supabase_key: str,
        embedding_service=None
    ) -> bool:
        """Initialize all sub-services"""
        try:
            logger.info("Initializing SearchOrchestrator...")

            # Initialize hybrid search
            if not await self.hybrid_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize HybridSearchService")

            # Set embedding service
            if embedding_service:
                self.embedding_service = embedding_service
                self.contextual_service.set_embedding_service(embedding_service)

            logger.info("SearchOrchestrator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SearchOrchestrator: {e}")
            return False

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute the full search pipeline.

        Args:
            request: Search request with query and options

        Returns:
            SearchResponse with ranked results and timing info
        """
        start_time = time.time()
        self.stats["total_searches"] += 1

        timings = {
            "expansion": 0.0,
            "embedding": 0.0,
            "search": 0.0,
            "rerank": 0.0
        }

        try:
            # Stage 1: Query Expansion
            expansion = None
            expanded_query = request.query
            merged_filters = dict(request.filters or {})

            if request.enable_expansion:
                self.stats["expansion_enabled"] += 1
                t0 = time.time()
                expansion = await self.expansion_service.expand_query(request.query)
                timings["expansion"] = (time.time() - t0) * 1000

                expanded_query = expansion.expanded_query

                # Merge extracted filters with explicit filters
                for key, value in expansion.extracted_filters.items():
                    if key not in merged_filters:
                        merged_filters[key] = value

            # Stage 2: Generate Query Embedding
            t0 = time.time()
            if request.enable_contextual and self.contextual_service:
                query_embedding = await self.contextual_service.generate_query_embedding(
                    request.query
                )
            else:
                from src.semantic.embedding_service import EmbeddingRequest
                embed_request = EmbeddingRequest(text=request.query)
                embed_response = await self.embedding_service.generate_embedding(embed_request)
                query_embedding = embed_response.embedding
            timings["embedding"] = (time.time() - t0) * 1000

            # Stage 3: Hybrid Search
            t0 = time.time()
            # Get more candidates for re-ranking
            candidate_limit = request.limit * 3 if request.enable_reranking else request.limit

            hybrid_response = await self.hybrid_service.hybrid_search(
                query=request.query,
                query_embedding=query_embedding,
                filters=merged_filters,
                expanded_query=expanded_query,
                limit=candidate_limit
            )
            timings["search"] = (time.time() - t0) * 1000

            # Stage 4: Re-ranking (optional)
            final_results: List[SearchResult] = []

            if request.enable_reranking and len(hybrid_response.results) > 0:
                self.stats["reranking_enabled"] += 1
                t0 = time.time()

                # Convert to dict format for reranking
                candidates = [
                    {
                        "id": r.id,
                        "vin": r.vin,
                        "year": r.year,
                        "make": r.make,
                        "model": r.model,
                        "trim": r.trim,
                        "vehicle_type": r.vehicle_type,
                        "price": r.price,
                        "price_source": r.price_source,
                        "mileage": r.mileage,
                        "description": r.description,
                        "hybrid_score": r.hybrid_score,
                        "vector_score": r.vector_score,
                        "keyword_score": r.keyword_score
                    }
                    for r in hybrid_response.results
                ]

                reranked = await self.rerank_service.rerank(
                    query=request.query,
                    candidates=candidates,
                    top_k=request.limit
                )
                timings["rerank"] = (time.time() - t0) * 1000

                # Convert reranked results
                for rr in reranked:
                    vd = rr.vehicle_data
                    final_results.append(SearchResult(
                        id=rr.id,
                        vin=vd.get('vin', ''),
                        year=vd.get('year', 0),
                        make=vd.get('make', ''),
                        model=vd.get('model', ''),
                        trim=vd.get('trim'),
                        vehicle_type=vd.get('vehicle_type'),
                        price=vd.get('price'),
                        price_source=vd.get('price_source'),
                        mileage=vd.get('mileage'),
                        description=vd.get('description'),
                        similarity_score=rr.final_score,
                        vector_score=vd.get('vector_score', 0),
                        keyword_score=vd.get('keyword_score', 0),
                        hybrid_score=vd.get('hybrid_score', 0),
                        rerank_score=rr.rerank_score
                    ))
            else:
                # Use hybrid results directly
                for hr in hybrid_response.results[:request.limit]:
                    final_results.append(SearchResult(
                        id=hr.id,
                        vin=hr.vin,
                        year=hr.year,
                        make=hr.make,
                        model=hr.model,
                        trim=hr.trim,
                        vehicle_type=hr.vehicle_type,
                        price=hr.price,
                        price_source=hr.price_source,
                        mileage=hr.mileage,
                        description=hr.description,
                        similarity_score=hr.hybrid_score,
                        vector_score=hr.vector_score,
                        keyword_score=hr.keyword_score,
                        hybrid_score=hr.hybrid_score,
                        rerank_score=None
                    ))

            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000

            # Update stats
            total = self.stats["total_searches"]
            self.stats["avg_total_latency_ms"] = (
                (self.stats["avg_total_latency_ms"] * (total - 1) + total_latency) / total
            )

            # Build response
            response = SearchResponse(
                query=request.query,
                results=final_results,
                total_results=len(final_results),
                total_latency_ms=total_latency,
                expansion_latency_ms=timings["expansion"],
                embedding_latency_ms=timings["embedding"],
                search_latency_ms=timings["search"],
                rerank_latency_ms=timings["rerank"],
                metadata={
                    "expansion_enabled": request.enable_expansion,
                    "reranking_enabled": request.enable_reranking,
                    "contextual_enabled": request.enable_contextual,
                    "expanded_query": expanded_query if expansion else None,
                    "extracted_filters": expansion.extracted_filters if expansion else {},
                    "filters_applied": merged_filters
                }
            )

            logger.info(
                f"Search completed: '{request.query[:30]}...' -> "
                f"{len(final_results)} results in {total_latency:.0f}ms "
                f"(expand: {timings['expansion']:.0f}ms, "
                f"embed: {timings['embedding']:.0f}ms, "
                f"search: {timings['search']:.0f}ms, "
                f"rerank: {timings['rerank']:.0f}ms)"
            )

            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            "expansion_stats": self.expansion_service.get_stats(),
            "hybrid_stats": self.hybrid_service.get_stats(),
            "rerank_stats": self.rerank_service.get_stats(),
            "contextual_stats": self.contextual_service.get_stats()
        }

    def set_reranking_enabled(self, enabled: bool):
        """Enable or disable re-ranking globally"""
        self.rerank_service.set_enabled(enabled)

    def configure_weights(
        self,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.3,
        filter_weight: float = 0.3
    ):
        """Configure RRF weights"""
        self.hybrid_service.vector_weight = vector_weight
        self.hybrid_service.keyword_weight = keyword_weight
        self.hybrid_service.filter_weight = filter_weight
        logger.info(
            f"Configured weights: vector={vector_weight}, "
            f"keyword={keyword_weight}, filter={filter_weight}"
        )
