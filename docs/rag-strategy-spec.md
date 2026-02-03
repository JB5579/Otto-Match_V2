# Otto.AI RAG Strategy Specification

**Implementation Status:** ✅ IMPLEMENTED (Epic 1 Stories 1-9 to 1-12)
**Last Verified:** 2026-01-02
**Implementation:** All 4 RAG enhancement stories complete
- `src/search/hybrid_search_service.py` (14.5 KB) - Story 1-9
- `src/search/query_expansion_service.py` (10.7 KB) - Story 1-10
- `src/search/reranking_service.py` (9.4 KB) - Story 1-11
- `src/search/contextual_embedding_service.py` (7.7 KB) - Story 1-12
- `src/search/search_orchestrator.py` (13.7 KB) - Integration layer

## Executive Summary

This specification defines the enhanced RAG strategy for Otto.AI vehicle discovery, implementing:
- **Contextual Retrieval** for improved vehicle embeddings
- **Hybrid Search** combining semantic + keyword + filters
- **Re-ranking** for precision matching
- **Query Expansion** for brief natural language queries

---

## 1. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OTTO.AI RAG PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              USER QUERY
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUERY PROCESSING LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Query      │  │   Query      │  │   Filter     │                      │
│  │   Expansion  │──│   Embedding  │──│   Extraction │                      │
│  │   (LLM)      │  │   (OpenAI)   │  │   (NLU)      │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID SEARCH LAYER                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Vector Search   │  │  Keyword Search  │  │  Filter Search   │          │
│  │  (pgvector HNSW) │  │  (PostgreSQL FTS)│  │  (SQL WHERE)     │          │
│  │  Semantic Match  │  │  Make/Model/VIN  │  │  Year/Price/Cond │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           └─────────────────────┴─────────────────────┘                     │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌──────────────────────┐                                 │
│                    │   Result Fusion      │                                 │
│                    │   (RRF Algorithm)    │                                 │
│                    └──────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RE-RANKING LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                    Cross-Encoder Re-ranker                    │          │
│  │   - Query-Vehicle relevance scoring                          │          │
│  │   - Condition match boosting                                 │          │
│  │   - Price range affinity                                     │          │
│  │   - Feature overlap scoring                                  │          │
│  └──────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                         TOP-K RANKED VEHICLES
```

---

## 2. Dependencies

```bash
# Core RAG dependencies (add to requirements.txt)
pip install sentence-transformers>=2.2.0    # Re-ranking models
pip install cohere>=4.0                      # Optional: Cohere re-ranker API
pip install rank-bm25>=0.2.2                 # BM25 keyword search
pip install openai>=1.0.0                    # Embeddings + Query expansion

# Existing dependencies (already installed)
# pgvector, supabase, httpx, pydantic, fastapi
```

---

## 3. Configuration

```bash
# Add to .env file
# =================

# Query Expansion (uses existing OpenRouter)
QUERY_EXPANSION_MODEL=google/gemini-2.0-flash-lite-001  # Fast, cheap for expansion
QUERY_EXPANSION_ENABLED=true

# Re-ranking
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2     # Local model (free)
# COHERE_API_KEY=xxx                                     # Optional: Cohere re-ranker

# Hybrid Search Weights
VECTOR_SEARCH_WEIGHT=0.5
KEYWORD_SEARCH_WEIGHT=0.3
FILTER_BOOST_WEIGHT=0.2

# Search Limits
INITIAL_RETRIEVAL_LIMIT=50     # Candidates for re-ranking
FINAL_RESULT_LIMIT=10          # After re-ranking
```

---

## 4. Implementation Code

### 4.1 Query Expansion Service

```python
# src/search/query_expansion_service.py
"""
Query Expansion Service for Otto.AI
Expands brief user queries into semantically rich search terms
"""

import os
import httpx
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExpandedQuery:
    """Result of query expansion"""
    original: str
    expanded: str
    synonyms: List[str]
    vehicle_types: List[str]
    extracted_filters: Dict[str, any]


class QueryExpansionService:
    """Expands user queries for better semantic matching"""

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('QUERY_EXPANSION_MODEL', 'google/gemini-2.0-flash-lite-001')
        self.enabled = os.getenv('QUERY_EXPANSION_ENABLED', 'true').lower() == 'true'

    async def expand_query(self, query: str) -> ExpandedQuery:
        """
        Expand a user query into richer search terms

        Args:
            query: Original user query (e.g., "reliable truck for work")

        Returns:
            ExpandedQuery with synonyms, vehicle types, and extracted filters
        """
        if not self.enabled:
            return ExpandedQuery(
                original=query,
                expanded=query,
                synonyms=[],
                vehicle_types=[],
                extracted_filters={}
            )

        prompt = f"""Analyze this vehicle search query and expand it for better search matching.

Query: "{query}"

Return a JSON object with:
1. "expanded": The query rewritten with more descriptive terms
2. "synonyms": List of related vehicle terms (e.g., "SUV" → ["sport utility", "crossover"])
3. "vehicle_types": Specific vehicle categories that match (e.g., ["pickup", "truck", "work vehicle"])
4. "filters": Extracted constraints as key-value pairs (e.g., {{"max_price": 30000, "min_year": 2018}})

Return ONLY valid JSON, no markdown."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']

                    # Parse JSON response
                    import json
                    data = json.loads(content)

                    return ExpandedQuery(
                        original=query,
                        expanded=data.get('expanded', query),
                        synonyms=data.get('synonyms', []),
                        vehicle_types=data.get('vehicle_types', []),
                        extracted_filters=data.get('filters', {})
                    )

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}, using original query")

        # Fallback to original
        return ExpandedQuery(
            original=query,
            expanded=query,
            synonyms=[],
            vehicle_types=[],
            extracted_filters={}
        )
```

### 4.2 Hybrid Search Service

```python
# src/search/hybrid_search_service.py
"""
Hybrid Search Service for Otto.AI
Combines vector similarity, keyword matching, and structured filters
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Individual search result with scores"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str]
    price: Optional[float]
    condition_score: float
    vector_score: float
    keyword_score: float
    filter_score: float
    combined_score: float


class HybridSearchService:
    """
    Combines multiple search strategies using Reciprocal Rank Fusion (RRF)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.vector_weight = float(os.getenv('VECTOR_SEARCH_WEIGHT', '0.5'))
        self.keyword_weight = float(os.getenv('KEYWORD_SEARCH_WEIGHT', '0.3'))
        self.filter_weight = float(os.getenv('FILTER_BOOST_WEIGHT', '0.2'))
        self.initial_limit = int(os.getenv('INITIAL_RETRIEVAL_LIMIT', '50'))

    async def search(
        self,
        query_embedding: List[float],
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        synonyms: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Execute hybrid search combining vector, keyword, and filter strategies

        Args:
            query_embedding: Vector embedding of the query
            query_text: Original query text for keyword matching
            filters: Structured filters (year, price, condition, etc.)
            synonyms: Expanded synonyms for keyword matching

        Returns:
            List of SearchResult objects ranked by combined score
        """

        # 1. Vector similarity search
        vector_results = await self._vector_search(query_embedding)

        # 2. Keyword/Full-text search
        keyword_results = await self._keyword_search(query_text, synonyms or [])

        # 3. Filter-boosted search
        filter_results = await self._filter_search(filters or {})

        # 4. Fuse results using RRF
        fused = self._reciprocal_rank_fusion(
            vector_results,
            keyword_results,
            filter_results
        )

        return fused[:self.initial_limit]

    async def _vector_search(self, embedding: List[float]) -> List[Dict]:
        """Semantic similarity search using pgvector"""
        result = self.supabase.rpc(
            'match_vehicle_listings',
            {
                'query_embedding': embedding,
                'match_count': self.initial_limit,
                'min_similarity': 0.0
            }
        ).execute()

        return [
            {**r, 'vector_score': r.get('similarity', 0)}
            for r in (result.data or [])
        ]

    async def _keyword_search(self, query: str, synonyms: List[str]) -> List[Dict]:
        """Full-text search on make, model, description"""
        # Combine query terms with synonyms
        search_terms = [query] + synonyms
        search_string = ' | '.join(search_terms)  # OR search

        # Use PostgreSQL full-text search
        result = self.supabase.rpc(
            'keyword_search_vehicles',
            {
                'search_query': search_string,
                'limit_count': self.initial_limit
            }
        ).execute()

        return [
            {**r, 'keyword_score': r.get('rank', 0)}
            for r in (result.data or [])
        ]

    async def _filter_search(self, filters: Dict[str, Any]) -> List[Dict]:
        """Boost vehicles matching extracted filters"""
        query = self.supabase.table('vehicle_listings').select('*')

        # Apply filters
        if 'max_price' in filters:
            query = query.lte('price', filters['max_price'])
        if 'min_year' in filters:
            query = query.gte('year', filters['min_year'])
        if 'make' in filters:
            query = query.ilike('make', f"%{filters['make']}%")
        if 'condition_grade' in filters:
            query = query.eq('condition_grade', filters['condition_grade'])

        result = query.limit(self.initial_limit).execute()

        # Score based on how many filters matched
        filter_count = len(filters)
        return [
            {**r, 'filter_score': 1.0}  # Full score for matching filters
            for r in (result.data or [])
        ]

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        filter_results: List[Dict],
        k: int = 60  # RRF constant
    ) -> List[SearchResult]:
        """
        Combine rankings using Reciprocal Rank Fusion (RRF)

        RRF Score = Σ 1 / (k + rank_i) for each ranking list
        """
        scores = {}
        vehicle_data = {}

        # Score vector results
        for rank, r in enumerate(vector_results):
            vid = r['id']
            scores[vid] = scores.get(vid, 0) + self.vector_weight / (k + rank + 1)
            vehicle_data[vid] = r

        # Score keyword results
        for rank, r in enumerate(keyword_results):
            vid = r['id']
            scores[vid] = scores.get(vid, 0) + self.keyword_weight / (k + rank + 1)
            if vid not in vehicle_data:
                vehicle_data[vid] = r

        # Score filter results (boost matching vehicles)
        for rank, r in enumerate(filter_results):
            vid = r['id']
            scores[vid] = scores.get(vid, 0) + self.filter_weight / (k + rank + 1)
            if vid not in vehicle_data:
                vehicle_data[vid] = r

        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for vid, combined_score in ranked:
            v = vehicle_data[vid]
            results.append(SearchResult(
                id=vid,
                vin=v.get('vin', ''),
                year=v.get('year', 0),
                make=v.get('make', ''),
                model=v.get('model', ''),
                trim=v.get('trim'),
                price=v.get('price'),
                condition_score=v.get('condition_score', 0),
                vector_score=v.get('vector_score', 0),
                keyword_score=v.get('keyword_score', 0),
                filter_score=v.get('filter_score', 0),
                combined_score=combined_score
            ))

        return results
```

### 4.3 Re-ranking Service

```python
# src/search/reranking_service.py
"""
Re-ranking Service for Otto.AI
Uses cross-encoder models to precisely rank search results
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Lazy load to avoid startup cost if not used
_reranker_model = None

def get_reranker():
    """Lazy load the cross-encoder model"""
    global _reranker_model
    if _reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            model_name = os.getenv(
                'RERANKER_MODEL',
                'cross-encoder/ms-marco-MiniLM-L-6-v2'
            )
            _reranker_model = CrossEncoder(model_name)
            logger.info(f"Loaded re-ranker model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, re-ranking disabled")
            return None
    return _reranker_model


@dataclass
class RankedResult:
    """Re-ranked search result"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    relevance_score: float
    original_rank: int
    new_rank: int


class RerankingService:
    """
    Re-ranks search results using a cross-encoder for precise relevance scoring
    """

    def __init__(self):
        self.final_limit = int(os.getenv('FINAL_RESULT_LIMIT', '10'))
        self.enabled = True

    def rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: Optional[int] = None
    ) -> List[RankedResult]:
        """
        Re-rank candidate vehicles based on query relevance

        Args:
            query: User's search query
            candidates: List of candidate vehicles from hybrid search
            top_k: Number of results to return (default: FINAL_RESULT_LIMIT)

        Returns:
            Re-ranked list of RankedResult objects
        """
        if not candidates:
            return []

        top_k = top_k or self.final_limit

        reranker = get_reranker()
        if reranker is None:
            # Fallback: return candidates as-is
            return [
                RankedResult(
                    id=c.id,
                    vin=c.vin,
                    year=c.year,
                    make=c.make,
                    model=c.model,
                    relevance_score=c.combined_score,
                    original_rank=i,
                    new_rank=i
                )
                for i, c in enumerate(candidates[:top_k])
            ]

        # Create query-document pairs for cross-encoder
        pairs = []
        for candidate in candidates:
            # Create rich vehicle description for comparison
            vehicle_text = self._create_vehicle_text(candidate)
            pairs.append([query, vehicle_text])

        # Score all pairs
        scores = reranker.predict(pairs)

        # Combine with original scores and sort
        scored_candidates = list(zip(candidates, scores, range(len(candidates))))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top_k results
        results = []
        for new_rank, (candidate, score, original_rank) in enumerate(scored_candidates[:top_k]):
            results.append(RankedResult(
                id=candidate.id,
                vin=candidate.vin,
                year=candidate.year,
                make=candidate.make,
                model=candidate.model,
                relevance_score=float(score),
                original_rank=original_rank,
                new_rank=new_rank
            ))

        return results

    def _create_vehicle_text(self, vehicle) -> str:
        """Create searchable text representation of vehicle"""
        parts = [
            f"{vehicle.year} {vehicle.make} {vehicle.model}",
        ]

        if hasattr(vehicle, 'trim') and vehicle.trim:
            parts.append(vehicle.trim)

        if hasattr(vehicle, 'condition_score'):
            if vehicle.condition_score >= 4.0:
                parts.append("excellent condition")
            elif vehicle.condition_score >= 3.0:
                parts.append("good condition")
            else:
                parts.append("fair condition")

        if hasattr(vehicle, 'price') and vehicle.price:
            if vehicle.price < 20000:
                parts.append("budget friendly affordable")
            elif vehicle.price < 40000:
                parts.append("mid-range")
            else:
                parts.append("premium luxury")

        return " ".join(parts)
```

### 4.4 Contextual Embedding Service

```python
# src/search/contextual_embedding_service.py
"""
Contextual Embedding Service for Otto.AI
Adds vehicle category context to embeddings for better semantic matching
"""

import os
import logging
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

# Vehicle category definitions for context injection
VEHICLE_CATEGORIES = {
    "truck": ["pickup", "work vehicle", "hauling", "towing", "utility"],
    "suv": ["sport utility", "crossover", "family vehicle", "all-wheel drive"],
    "sedan": ["passenger car", "commuter", "fuel efficient"],
    "sports": ["performance", "coupe", "convertible", "fast", "sporty"],
    "luxury": ["premium", "high-end", "executive", "comfort"],
    "electric": ["EV", "zero emissions", "plug-in", "battery powered"],
    "hybrid": ["fuel efficient", "eco-friendly", "gas and electric"],
    "minivan": ["family hauler", "passenger van", "kid-friendly"],
}

# Make-based category hints
MAKE_CATEGORIES = {
    "Ford": {"F-150": "truck", "F-250": "truck", "Mustang": "sports", "Explorer": "suv"},
    "GMC": {"Sierra": "truck", "Canyon": "truck", "Yukon": "suv"},
    "BMW": {"i3": "electric", "M3": "sports", "X5": "suv"},
    "Tesla": {"Model S": "electric", "Model 3": "electric", "Model X": "electric"},
    "Toyota": {"Camry": "sedan", "RAV4": "suv", "Tacoma": "truck", "Prius": "hybrid"},
    "Honda": {"Civic": "sedan", "CR-V": "suv", "Pilot": "suv", "Odyssey": "minivan"},
}


class ContextualEmbeddingService:
    """
    Enhances vehicle embeddings with category context
    Implements the Contextual Retrieval pattern from Anthropic
    """

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.embedding_model = os.getenv('OPENROUTER_EMBEDDING_MODEL', 'openai/text-embedding-3-small')
        self.embedding_dim = 1536

    def get_vehicle_category(self, make: str, model: str) -> str:
        """Determine vehicle category from make/model"""
        # Check make-specific categories
        if make in MAKE_CATEGORIES:
            if model in MAKE_CATEGORIES[make]:
                return MAKE_CATEGORIES[make][model]

        # Fallback to model name heuristics
        model_lower = model.lower()
        for category, keywords in VEHICLE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in model_lower:
                    return category

        return "vehicle"  # Generic fallback

    def create_contextual_text(
        self,
        vehicle: Dict,
        include_context: bool = True
    ) -> str:
        """
        Create context-enhanced text for embedding

        Args:
            vehicle: Vehicle data dictionary
            include_context: Whether to prepend category context

        Returns:
            Contextual text string for embedding
        """
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        year = vehicle.get('year', '')
        trim = vehicle.get('trim', '')

        # Base vehicle description
        base_text = f"{year} {make} {model}"
        if trim:
            base_text += f" {trim}"

        if not include_context:
            return base_text

        # Add category context
        category = self.get_vehicle_category(make, model)
        category_keywords = VEHICLE_CATEGORIES.get(category, [])

        # Build context prefix
        context_parts = [f"This is a {category}"]
        if category_keywords:
            context_parts.append(f"commonly used for {', '.join(category_keywords[:3])}")

        # Add condition context
        condition_score = vehicle.get('condition_score', 0)
        if condition_score >= 4.0:
            context_parts.append("in excellent condition")
        elif condition_score >= 3.0:
            context_parts.append("in good condition")

        # Add price context
        price = vehicle.get('price')
        if price:
            if price < 15000:
                context_parts.append("budget-friendly option")
            elif price < 30000:
                context_parts.append("mid-range price point")
            elif price < 50000:
                context_parts.append("premium segment")
            else:
                context_parts.append("luxury tier")

        context = ". ".join(context_parts) + "."

        return f"{context} {base_text}"

    async def generate_contextual_embedding(
        self,
        vehicle: Dict
    ) -> List[float]:
        """
        Generate embedding with contextual enhancement

        Args:
            vehicle: Vehicle data dictionary

        Returns:
            1536-dimensional embedding vector
        """
        text = self.create_contextual_text(vehicle, include_context=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.embedding_model,
                    "input": text,
                    "dimensions": self.embedding_dim
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                logger.error(f"Embedding generation failed: {response.status_code}")
                raise Exception(f"Embedding API error: {response.status_code}")
```

### 4.5 Unified Search Orchestrator

```python
# src/search/search_orchestrator.py
"""
Search Orchestrator for Otto.AI
Coordinates query expansion, hybrid search, and re-ranking
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .query_expansion_service import QueryExpansionService, ExpandedQuery
from .hybrid_search_service import HybridSearchService, SearchResult
from .reranking_service import RerankingService, RankedResult

logger = logging.getLogger(__name__)


@dataclass
class SearchResponse:
    """Complete search response with metadata"""
    query: str
    expanded_query: Optional[str]
    total_candidates: int
    results: List[Dict[str, Any]]
    search_metadata: Dict[str, Any]


class SearchOrchestrator:
    """
    Orchestrates the complete search pipeline:
    1. Query Expansion
    2. Embedding Generation
    3. Hybrid Search
    4. Re-ranking
    """

    def __init__(self, supabase_client, embedding_service):
        self.query_expander = QueryExpansionService()
        self.hybrid_search = HybridSearchService(supabase_client)
        self.reranker = RerankingService()
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> SearchResponse:
        """
        Execute full search pipeline

        Args:
            query: User's natural language search query
            filters: Optional pre-extracted filters
            limit: Maximum results to return

        Returns:
            SearchResponse with ranked results and metadata
        """
        logger.info(f"Search query: {query}")

        # Step 1: Query Expansion
        expanded = await self.query_expander.expand_query(query)
        logger.info(f"Expanded to: {expanded.expanded}")

        # Merge extracted filters with provided filters
        all_filters = {**(filters or {}), **expanded.extracted_filters}

        # Step 2: Generate query embedding
        query_embedding = await self.embedding_service.generate_text_embedding(
            expanded.expanded
        )

        # Step 3: Hybrid Search
        candidates = await self.hybrid_search.search(
            query_embedding=query_embedding.embedding,
            query_text=expanded.expanded,
            filters=all_filters,
            synonyms=expanded.synonyms
        )
        logger.info(f"Hybrid search returned {len(candidates)} candidates")

        # Step 4: Re-ranking
        ranked = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=limit
        )
        logger.info(f"Re-ranked to top {len(ranked)} results")

        # Build response
        return SearchResponse(
            query=query,
            expanded_query=expanded.expanded if expanded.expanded != query else None,
            total_candidates=len(candidates),
            results=[asdict(r) for r in ranked],
            search_metadata={
                'synonyms_used': expanded.synonyms,
                'filters_extracted': expanded.extracted_filters,
                'filters_applied': all_filters
            }
        )
```

---

## 5. Database Schema Additions

```sql
-- Add to migrations/rag_enhancements.sql

-- Full-text search index for keyword matching
CREATE INDEX IF NOT EXISTS idx_vehicle_listings_fts
ON vehicle_listings
USING gin(to_tsvector('english',
    coalesce(make, '') || ' ' ||
    coalesce(model, '') || ' ' ||
    coalesce(trim, '') || ' ' ||
    coalesce(description_text, '')
));

-- Keyword search function
CREATE OR REPLACE FUNCTION keyword_search_vehicles(
    search_query text,
    limit_count int DEFAULT 50
)
RETURNS TABLE (
    id uuid,
    vin varchar,
    year int,
    make varchar,
    model varchar,
    "trim" varchar,
    rank real
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vl.id,
        vl.vin,
        vl.year,
        vl.make,
        vl.model,
        vl."trim",
        ts_rank(
            to_tsvector('english',
                coalesce(vl.make, '') || ' ' ||
                coalesce(vl.model, '') || ' ' ||
                coalesce(vl."trim", '') || ' ' ||
                coalesce(vl.description_text, '')
            ),
            plainto_tsquery('english', search_query)
        ) as rank
    FROM vehicle_listings vl
    WHERE vl.status = 'active'
    AND to_tsvector('english',
            coalesce(vl.make, '') || ' ' ||
            coalesce(vl.model, '') || ' ' ||
            coalesce(vl."trim", '') || ' ' ||
            coalesce(vl.description_text, '')
        ) @@ plainto_tsquery('english', search_query)
    ORDER BY rank DESC
    LIMIT limit_count;
END;
$$;

-- Add contextual_embedding column for enhanced embeddings
ALTER TABLE vehicle_listings
ADD COLUMN IF NOT EXISTS contextual_embedding vector(1536);

-- Index for contextual embeddings
CREATE INDEX IF NOT EXISTS idx_vehicle_listings_contextual_embedding
ON vehicle_listings
USING hnsw (contextual_embedding vector_cosine_ops);
```

---

## 6. Implementation Checklist

### Phase 1: Query Enhancement (Week 1)
- [ ] Install `sentence-transformers` dependency
- [ ] Create `src/search/` directory structure
- [ ] Implement `QueryExpansionService`
- [ ] Add unit tests for query expansion
- [ ] Configure environment variables

### Phase 2: Hybrid Search (Week 1-2)
- [ ] Run database migration for FTS index
- [ ] Implement `keyword_search_vehicles` SQL function
- [ ] Implement `HybridSearchService`
- [ ] Add RRF (Reciprocal Rank Fusion) algorithm
- [ ] Test hybrid search with sample queries

### Phase 3: Re-ranking (Week 2)
- [ ] Implement `RerankingService`
- [ ] Download and test cross-encoder model
- [ ] Benchmark re-ranking latency
- [ ] Add fallback for missing model

### Phase 4: Contextual Embeddings (Week 2-3)
- [ ] Implement `ContextualEmbeddingService`
- [ ] Add vehicle category mappings
- [ ] Run migration for `contextual_embedding` column
- [ ] Backfill contextual embeddings for existing vehicles
- [ ] Update ingestion pipeline to generate contextual embeddings

### Phase 5: Integration (Week 3)
- [ ] Implement `SearchOrchestrator`
- [ ] Update `semantic_search_api.py` to use orchestrator
- [ ] Add search response metadata to API
- [ ] End-to-end testing with real queries

### Phase 6: Optimization (Week 4)
- [ ] Benchmark full pipeline latency
- [ ] Tune RRF weights based on user feedback
- [ ] Add caching for query expansions
- [ ] Monitor and log search quality metrics

---

## 7. Expected Performance

| Metric | Current | After Implementation |
|--------|---------|---------------------|
| Query Latency | ~500ms | ~800ms (with re-ranking) |
| Precision@5 | ~60% | ~85% (estimated) |
| Recall@10 | ~70% | ~90% (estimated) |
| Query Types Supported | Semantic only | Semantic + Keyword + Filters |

---

## 8. Cost Analysis

| Component | Cost per 1000 Queries |
|-----------|----------------------|
| Query Expansion (Gemini Flash) | ~$0.01 |
| Embeddings (text-embedding-3-small) | ~$0.02 |
| Re-ranking (local model) | $0.00 |
| **Total** | **~$0.03 per 1000 queries** |
