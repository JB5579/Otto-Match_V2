# Story 1-11: Implement Re-ranking Layer

**Story Status:** ✅ DONE | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 1 - Semantic Vehicle Intelligence
**Story ID**: 1-11
**Status**: done
**Completed**: 2025-12-31
**Verified**: 2026-01-02
**Priority**: P2 - Medium
**Actual Effort**: 1-2 days

**Implementation:** `src/search/reranking_service.py` (9.4 KB) - RerankingService with BGE cross-encoder

---

## Summary

**As a** vehicle buyer,
**I want** search results to be precisely ranked by relevance,
**So that** the best matches appear at the top even when initial scores are similar.

---

## Business Context

Hybrid search returns good candidates, but initial ranking may not be optimal. Re-ranking uses a cross-encoder model to evaluate each candidate against the original query for precise relevance scoring.

**How it works**:
1. Hybrid search returns top 50 candidates
2. Cross-encoder scores each (query, vehicle) pair
3. Results are re-sorted by cross-encoder score
4. Top 20 are returned to user

**Trade-off**: Adds ~200ms latency but significantly improves precision.

**Expected Impact**: Search precision from ~75% to ~85%

---

## Acceptance Criteria

### AC1: Cross-Encoder Integration
**Given** a search query and candidate vehicles
**When** re-ranking is executed
**Then** the `BAAI/bge-reranker-large` model is called via OpenRouter
**And** each candidate receives a relevance score (0-1)
**And** results are re-sorted by score

### AC2: Batch Processing
**Given** 50 candidates to re-rank
**When** the re-ranker is called
**Then** candidates are batched for efficiency
**And** batch size is configurable (default: 10)
**And** batches are processed in parallel

### AC3: Latency Budget
**Given** the performance requirement
**When** re-ranking is executed
**Then** total re-ranking time is < 250ms
**And** if latency exceeds budget, partial results are returned
**And** timeout is configurable

### AC4: Score Normalization
**Given** raw cross-encoder scores
**When** normalized
**Then** scores are in 0-1 range
**And** scores are comparable across different queries
**And** original hybrid score is preserved as fallback

### AC5: Optional Re-ranking
**Given** the search request
**When** `enable_reranking=false` is passed
**Then** re-ranking is skipped
**And** hybrid search results are returned directly
**And** this is useful for latency-sensitive applications

---

## Technical Implementation

### Files to Create

| File | Purpose |
|------|---------|
| `src/search/reranking_service.py` | Cross-encoder re-ranking |

### RerankingService Design

```python
class RerankingService:
    """Cross-encoder re-ranking for precise relevance scoring"""

    def __init__(self, batch_size: int = 10, timeout_ms: int = 250):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = "baai/bge-reranker-large"
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """Re-rank candidates using cross-encoder model"""

        if not candidates:
            return []

        start_time = time.time()

        # Prepare pairs for cross-encoder
        pairs = [
            {
                "id": c["id"],
                "text": self._create_vehicle_text(c),
                "original_score": c.get("hybrid_score", 0)
            }
            for c in candidates
        ]

        # Batch processing
        batches = [
            pairs[i:i + self.batch_size]
            for i in range(0, len(pairs), self.batch_size)
        ]

        try:
            # Process batches in parallel with timeout
            tasks = [
                self._score_batch(query, batch)
                for batch in batches
            ]

            remaining_time = (self.timeout_ms / 1000) - (time.time() - start_time)
            if remaining_time <= 0:
                logger.warning("Re-ranking timeout before batch processing")
                return candidates[:top_k]

            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=remaining_time
            )

            # Flatten results
            all_scores = {}
            for batch_result in results:
                if isinstance(batch_result, Exception):
                    logger.warning(f"Batch failed: {batch_result}")
                    continue
                all_scores.update(batch_result)

            # Re-sort by cross-encoder score
            reranked = []
            for candidate in candidates:
                cid = candidate["id"]
                rerank_score = all_scores.get(cid, candidate.get("hybrid_score", 0))
                reranked.append({
                    **candidate,
                    "rerank_score": rerank_score,
                    "final_score": rerank_score
                })

            reranked.sort(key=lambda x: x["final_score"], reverse=True)

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Re-ranked {len(candidates)} candidates in {elapsed:.0f}ms")

            return reranked[:top_k]

        except asyncio.TimeoutError:
            logger.warning("Re-ranking timeout, returning hybrid results")
            return candidates[:top_k]

    async def _score_batch(
        self,
        query: str,
        batch: List[Dict]
    ) -> Dict[str, float]:
        """Score a batch of candidates"""

        texts = [item["text"] for item in batch]
        ids = [item["id"] for item in batch]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/rerank",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": texts,
                    "top_n": len(texts)
                },
                timeout=5
            )

            result = response.json()

            # Map scores back to IDs
            scores = {}
            for item in result.get("results", []):
                idx = item["index"]
                score = item["relevance_score"]
                scores[ids[idx]] = self._normalize_score(score)

            return scores

    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-1 range"""
        # BGE reranker outputs logits, apply sigmoid
        import math
        return 1 / (1 + math.exp(-score))

    def _create_vehicle_text(self, vehicle: Dict) -> str:
        """Create searchable text from vehicle data"""
        parts = [
            f"{vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}",
            vehicle.get('trim', ''),
            vehicle.get('vehicle_type', ''),
            vehicle.get('description', '')[:200]  # Truncate for efficiency
        ]
        return " ".join(filter(None, parts))
```

---

## Dependencies

### Prerequisites
- Story 1-9 (Hybrid Search) - Provides candidates
- Story 1-10 (Query Expansion) - Optional but improves results

### External
- OpenRouter API with rerank endpoint
- BAAI/bge-reranker-large model access

---

## Test Plan

### Unit Tests
- [ ] `test_batch_processing()` - Batches created correctly
- [ ] `test_score_normalization()` - Sigmoid applied
- [ ] `test_timeout_handling()` - Graceful fallback

### Integration Tests
- [ ] `test_rerank_improves_precision()` - Top result more relevant
- [ ] `test_rerank_latency()` - < 250ms for 50 candidates

### A/B Testing
- [ ] Configure feature flag for reranking
- [ ] Compare precision with/without reranking
- [ ] Monitor latency impact

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Re-ranking latency | < 250ms for 50 candidates |
| Precision improvement | +10% over hybrid-only |
| Timeout rate | < 5% |
| Top-1 accuracy | > 85% |

---

## Definition of Done

- [ ] `RerankingService` implemented
- [ ] Cross-encoder via OpenRouter working
- [ ] Batch processing with parallelism
- [ ] Timeout handling with fallback
- [ ] Optional via `enable_reranking` flag
- [ ] Unit tests pass
- [ ] Performance benchmarks met
- [ ] Code reviewed and approved
