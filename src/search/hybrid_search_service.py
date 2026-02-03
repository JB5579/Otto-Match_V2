"""
Otto.AI Hybrid Search Service

Combines vector similarity, keyword search (FTS), and structured filters
using Reciprocal Rank Fusion (RRF) for optimal ranking.

Story: 1-9 Implement Hybrid Search with FTS
"""

import os
import asyncio
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel, Field
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class HybridSearchResult(BaseModel):
    """Individual search result with scores"""
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

    # Scoring
    vector_score: float = Field(0.0, description="Vector similarity score")
    keyword_score: float = Field(0.0, description="Keyword/FTS score")
    filter_score: float = Field(0.0, description="Filter match score")
    hybrid_score: float = Field(0.0, description="Combined RRF score")


class HybridSearchResponse(BaseModel):
    """Hybrid search response"""
    query: str
    results: List[HybridSearchResult]
    total_found: int
    search_type: str = "hybrid"
    latency_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: HybridSearchResponse
    timestamp: datetime


class HybridSearchService:
    """
    Hybrid search combining vector, keyword, and filter search with RRF fusion.

    RRF Formula: score = sum(weight_i * (1 / (k + rank_i)))
    - k = 60 (constant to prevent high-ranked items from dominating)
    - Weights: vector=0.4, keyword=0.3, filter=0.3
    """

    def __init__(
        self,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.3,
        filter_weight: float = 0.3,
        rrf_k: int = 60,
        cache_ttl_seconds: int = 300
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.filter_weight = filter_weight
        self.rrf_k = rrf_k
        self.cache_ttl = cache_ttl_seconds

        self.supabase: Optional[Client] = None
        self.cache: Dict[str, CacheEntry] = {}

        # Statistics
        self.stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "avg_latency_ms": 0.0,
            "vector_searches": 0,
            "keyword_searches": 0
        }

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """Initialize Supabase connection"""
        try:
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("HybridSearchService initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize HybridSearchService: {e}")
            return False

    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        expanded_query: Optional[str] = None,
        limit: int = 20
    ) -> HybridSearchResponse:
        """
        Perform hybrid search combining vector, keyword, and filter results.

        Args:
            query: Original user query
            query_embedding: Vector embedding of the query
            filters: Structured filters (make, model, year, price, etc.)
            expanded_query: LLM-expanded query for keyword search
            limit: Maximum results to return

        Returns:
            HybridSearchResponse with ranked results
        """
        start_time = time.time()
        self.stats["total_searches"] += 1

        # Check cache
        cache_key = self._get_cache_key(query, filters, limit)
        if cached := self._get_from_cache(cache_key):
            self.stats["cache_hits"] += 1
            return cached

        try:
            # Use SQL function for hybrid search (more efficient)
            results = await self._execute_hybrid_search_sql(
                query_embedding=query_embedding,
                search_query=expanded_query or query,
                filters=filters or {},
                limit=limit
            )

            latency_ms = (time.time() - start_time) * 1000

            response = HybridSearchResponse(
                query=query,
                results=results,
                total_found=len(results),
                latency_ms=latency_ms,
                metadata={
                    "vector_weight": self.vector_weight,
                    "keyword_weight": self.keyword_weight,
                    "filter_weight": self.filter_weight,
                    "expanded_query": expanded_query,
                    "filters_applied": filters
                }
            )

            # Cache result
            self._store_in_cache(cache_key, response)

            # Update stats
            self._update_latency_stats(latency_ms)

            logger.info(
                f"Hybrid search: '{query[:30]}...' -> "
                f"{len(results)} results in {latency_ms:.0f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    async def _execute_hybrid_search_sql(
        self,
        query_embedding: List[float],
        search_query: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[HybridSearchResult]:
        """Execute hybrid search using database RPC function"""

        try:
            # Call the hybrid_search_vehicles SQL function
            result = self.supabase.rpc(
                'hybrid_search_vehicles',
                {
                    'query_embedding': query_embedding,
                    'search_query': search_query if search_query else None,
                    'filter_make': filters.get('make'),
                    'filter_model': filters.get('model'),
                    'filter_year_min': filters.get('year_min'),
                    'filter_year_max': filters.get('year_max'),
                    'filter_price_min': filters.get('price_min'),
                    'filter_price_max': filters.get('price_max'),
                    'filter_mileage_max': filters.get('mileage_max'),
                    'filter_vehicle_type': filters.get('vehicle_type'),
                    'match_count': limit,
                    'vector_weight': self.vector_weight,
                    'keyword_weight': self.keyword_weight,
                    'filter_weight': self.filter_weight,
                    'rrf_k': self.rrf_k
                }
            ).execute()

            if not result.data:
                return []

            # Convert to HybridSearchResult objects
            return [
                HybridSearchResult(
                    id=str(row['id']),
                    vin=row['vin'],
                    year=row['year'],
                    make=row['make'],
                    model=row['model'],
                    trim=row.get('trim'),
                    vehicle_type=row.get('vehicle_type'),
                    price=float(row['price']) if row.get('price') else None,
                    price_source=row.get('price_source'),
                    mileage=row.get('mileage'),
                    description=row.get('description_text'),
                    vector_score=float(row.get('vector_similarity', 0)),
                    keyword_score=float(row.get('keyword_rank', 0)),
                    hybrid_score=float(row.get('hybrid_score', 0))
                )
                for row in result.data
            ]

        except Exception as e:
            logger.warning(f"SQL hybrid search failed, falling back to Python RRF: {e}")
            return await self._execute_hybrid_search_python(
                query_embedding, search_query, filters, limit
            )

    async def _execute_hybrid_search_python(
        self,
        query_embedding: List[float],
        search_query: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[HybridSearchResult]:
        """Fallback: Execute hybrid search in Python with RRF fusion"""

        candidate_limit = limit * 3  # Get more candidates for fusion

        # Execute searches in parallel
        vector_task = self._vector_search(query_embedding, filters, candidate_limit)
        keyword_task = self._keyword_search(search_query, candidate_limit)

        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(vector_results, Exception):
            logger.warning(f"Vector search failed: {vector_results}")
            vector_results = []
        if isinstance(keyword_results, Exception):
            logger.warning(f"Keyword search failed: {keyword_results}")
            keyword_results = []

        self.stats["vector_searches"] += 1
        self.stats["keyword_searches"] += 1

        # Apply RRF fusion
        fused = self._reciprocal_rank_fusion(vector_results, keyword_results)

        return fused[:limit]

    async def _vector_search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Execute vector similarity search"""

        result = self.supabase.rpc(
            'match_vehicle_listings',
            {
                'query_embedding': query_embedding,
                'match_count': limit,
                'min_similarity': 0.0
            }
        ).execute()

        return result.data or []

    async def _keyword_search(
        self,
        search_query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Execute keyword/FTS search"""

        if not search_query or not search_query.strip():
            return []

        result = self.supabase.rpc(
            'keyword_search_vehicles',
            {
                'search_query': search_query,
                'match_count': limit
            }
        ).execute()

        return result.data or []

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict]
    ) -> List[HybridSearchResult]:
        """Apply RRF to combine search results"""

        scores: Dict[str, float] = defaultdict(float)
        vehicle_data: Dict[str, Dict] = {}
        vector_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}

        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            vid = str(result['id'])
            scores[vid] += self.vector_weight * (1 / (self.rrf_k + rank))
            vector_scores[vid] = result.get('similarity', 0)
            vehicle_data[vid] = result

        # Process keyword results
        for rank, result in enumerate(keyword_results, 1):
            vid = str(result['id'])
            scores[vid] += self.keyword_weight * (1 / (self.rrf_k + rank))
            keyword_scores[vid] = result.get('rank', 0)
            if vid not in vehicle_data:
                vehicle_data[vid] = result

        # Sort by fused score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build result objects
        results = []
        for vid, score in ranked:
            data = vehicle_data[vid]
            results.append(HybridSearchResult(
                id=vid,
                vin=data.get('vin', ''),
                year=data.get('year', 0),
                make=data.get('make', ''),
                model=data.get('model', ''),
                trim=data.get('trim'),
                vehicle_type=data.get('vehicle_type'),
                price=float(data['effective_price']) if data.get('effective_price') else None,
                price_source=data.get('price_source'),
                mileage=data.get('mileage') or data.get('odometer'),
                vector_score=vector_scores.get(vid, 0),
                keyword_score=keyword_scores.get(vid, 0),
                hybrid_score=score
            ))

        return results

    def _get_cache_key(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> str:
        """Generate cache key"""
        filter_str = json.dumps(filters, sort_keys=True) if filters else ""
        cache_data = f"{query.lower().strip()}:{filter_str}:{limit}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[HybridSearchResponse]:
        """Get from cache if valid"""
        if cache_key not in self.cache:
            return None
        entry = self.cache[cache_key]
        if datetime.now() - entry.timestamp > timedelta(seconds=self.cache_ttl):
            del self.cache[cache_key]
            return None
        return entry.data

    def _store_in_cache(self, cache_key: str, response: HybridSearchResponse):
        """Store in cache"""
        self.cache[cache_key] = CacheEntry(data=response, timestamp=datetime.now())
        if len(self.cache) > 500:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest]

    def _update_latency_stats(self, latency_ms: float):
        """Update average latency statistics"""
        total = self.stats["total_searches"]
        self.stats["avg_latency_ms"] = (
            (self.stats["avg_latency_ms"] * (total - 1) + latency_ms) / total
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_searches"]
                if self.stats["total_searches"] > 0 else 0
            )
        }


# Import json for cache key generation
import json
