# Story 1-9: Implement Hybrid Search with Full-Text Search

**Story Status:** ✅ DONE | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 1 - Semantic Vehicle Intelligence
**Story ID**: 1-9
**Status**: done
**Completed**: 2025-12-31
**Verified**: 2026-01-02
**Priority**: P0 - Critical Enhancement
**Actual Effort**: 2-3 days

**Implementation:** `src/search/hybrid_search_service.py` (14.5 KB), Supabase migration with `hybrid_search_vehicles()` function

---

## Summary

**As a** vehicle buyer using Otto AI,
**I want** search to combine semantic understanding with keyword matching,
**So that** I get more precise results when I use specific terms like model names or features.

---

## Business Context

Current semantic-only search misses exact keyword matches. A search for "F-250 Super Duty" may not prioritize the exact match if another truck has a closer semantic embedding. Hybrid search combines:

1. **Vector similarity** - semantic understanding of intent
2. **Keyword search** - exact term matching via PostgreSQL FTS
3. **Structured filters** - make, model, year, price, etc.

Results are fused using Reciprocal Rank Fusion (RRF) for optimal ranking.

**Expected Impact**: Search precision improvement from ~60% to ~75%

---

## Acceptance Criteria

### AC1: PostgreSQL Full-Text Search Setup
**Given** the database schema
**When** FTS is configured
**Then** a `fts_document` tsvector column exists on `vehicle_listings`
**And** a GIN index exists for efficient FTS queries
**And** the column auto-updates via GENERATED ALWAYS AS

### AC2: Keyword Search Function
**Given** a user searches for "F-250 crew cab"
**When** the keyword search is executed
**Then** vehicles containing those exact terms rank higher
**And** PostgreSQL `ts_rank` is used for relevance scoring
**And** results return within 100ms

### AC3: Reciprocal Rank Fusion
**Given** results from vector search, keyword search, and filters
**When** results are combined
**Then** RRF formula is applied: `1 / (k + rank)` where k=60
**And** weights are configurable (default: 0.4 vector, 0.3 keyword, 0.3 filter)
**And** final scores are normalized to 0-1 range

### AC4: HybridSearchService Implementation
**Given** `src/search/hybrid_search_service.py` is created
**When** `hybrid_search()` is called with a query
**Then** it executes vector, keyword, and filter searches in parallel
**And** combines results using RRF
**And** returns unified ranked results

### AC5: Performance Requirements
**Given** a hybrid search request
**When** executed
**Then** total latency is < 400ms
**And** database queries run in parallel
**And** results are cached for 5 minutes

---

## Technical Implementation

### Database Migration

```sql
-- Add FTS column with auto-update
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS fts_document tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(make, '') || ' ' ||
      coalesce(model, '') || ' ' ||
      coalesce("trim", '') || ' ' ||
      coalesce(vehicle_type, '') || ' ' ||
      coalesce(description_text, '')
    )
  ) STORED;

-- Create GIN index for fast FTS
CREATE INDEX IF NOT EXISTS idx_vehicle_fts ON vehicle_listings USING GIN(fts_document);

-- Keyword search function
CREATE OR REPLACE FUNCTION keyword_search_vehicles(
  search_query text,
  match_count int DEFAULT 20
)
RETURNS TABLE(
  id uuid,
  vin varchar,
  year int,
  make varchar,
  model varchar,
  rank float
)
LANGUAGE sql STABLE
AS $$
  SELECT id, vin, year, make, model,
         ts_rank(fts_document, websearch_to_tsquery('english', search_query)) AS rank
  FROM vehicle_listings
  WHERE fts_document @@ websearch_to_tsquery('english', search_query)
    AND status = 'active'
  ORDER BY rank DESC
  LIMIT match_count;
$$;
```

### Files to Create

| File | Purpose |
|------|---------|
| `src/search/hybrid_search_service.py` | Core hybrid search with RRF fusion |
| `migrations/add_fts_search.sql` | Database migration for FTS |

### Files to Modify

| File | Changes |
|------|---------|
| `src/api/semantic_search_api.py` | Replace basic search with hybrid search |
| `src/semantic/vehicle_database_service.py` | Add `keyword_search()` method |

### HybridSearchService Design

```python
class HybridSearchService:
    def __init__(
        self,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.3,
        filter_weight: float = 0.3,
        rrf_k: int = 60
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.filter_weight = filter_weight
        self.rrf_k = rrf_k

    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        # Execute all searches in parallel
        vector_task = self._vector_search(query_embedding, limit * 2)
        keyword_task = self._keyword_search(query, limit * 2)
        filter_task = self._filter_search(filters, limit * 2)

        vector_results, keyword_results, filter_results = await asyncio.gather(
            vector_task, keyword_task, filter_task
        )

        # Apply RRF fusion
        fused = self._reciprocal_rank_fusion(
            vector_results, keyword_results, filter_results
        )

        return fused[:limit]

    def _reciprocal_rank_fusion(
        self,
        vector_results: List,
        keyword_results: List,
        filter_results: List
    ) -> List[Dict]:
        scores = defaultdict(float)
        vehicle_data = {}

        for rank, result in enumerate(vector_results, 1):
            vehicle_id = result['id']
            scores[vehicle_id] += self.vector_weight * (1 / (self.rrf_k + rank))
            vehicle_data[vehicle_id] = result

        for rank, result in enumerate(keyword_results, 1):
            vehicle_id = result['id']
            scores[vehicle_id] += self.keyword_weight * (1 / (self.rrf_k + rank))
            if vehicle_id not in vehicle_data:
                vehicle_data[vehicle_id] = result

        for rank, result in enumerate(filter_results, 1):
            vehicle_id = result['id']
            scores[vehicle_id] += self.filter_weight * (1 / (self.rrf_k + rank))
            if vehicle_id not in vehicle_data:
                vehicle_data[vehicle_id] = result

        # Sort by fused score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {**vehicle_data[vid], 'hybrid_score': score}
            for vid, score in ranked
        ]
```

---

## Dependencies

### Prerequisites
- Story 1-1 (Semantic Search Infrastructure) - Done
- Story 1-3 (Semantic Search API) - Done

### External
- PostgreSQL with pgvector extension
- Supabase with RPC function support

---

## Test Plan

### Unit Tests
- [ ] `test_rrf_fusion()` - Verify RRF algorithm correctness
- [ ] `test_weight_normalization()` - Verify weights sum to 1.0
- [ ] `test_parallel_search()` - Verify searches run concurrently

### Integration Tests
- [ ] `test_keyword_search_function()` - Verify SQL function works
- [ ] `test_hybrid_vs_vector_only()` - Compare result quality
- [ ] `test_exact_match_ranking()` - Exact terms rank higher

### Performance Tests
- [ ] `test_hybrid_latency()` - < 400ms target
- [ ] `test_cache_effectiveness()` - Cache hit rate > 50%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Hybrid search latency | < 400ms |
| Exact match in top 3 | 95%+ |
| Cache hit rate | > 50% |
| Search precision | ~75% (up from 60%) |

---

## Definition of Done

- [ ] FTS column and GIN index created
- [ ] `keyword_search_vehicles()` function works
- [ ] `HybridSearchService` implemented with RRF
- [ ] Searches execute in parallel
- [ ] Unit and integration tests pass
- [ ] Performance benchmarks met
- [ ] Code reviewed and approved
