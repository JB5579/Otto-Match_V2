# Story 1-10: Add Query Expansion Service

**Story Status:** ✅ DONE | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 1 - Semantic Vehicle Intelligence
**Story ID**: 1-10
**Status**: done
**Completed**: 2025-12-31
**Verified**: 2026-01-02
**Priority**: P1 - High
**Actual Effort**: 1-2 days

**Implementation:** `src/search/query_expansion_service.py` (10.7 KB) - QueryExpansionService with Groq LLM

---

## Summary

**As a** vehicle buyer using brief or colloquial queries,
**I want** my search intent to be understood and expanded,
**So that** queries like "cheap truck" return relevant results even without exact specifications.

---

## Business Context

Users often search with brief, ambiguous queries:
- "cheap truck" (what's cheap? what kind of truck?)
- "family car" (SUV? minivan? sedan?)
- "fast red car" (sports car? muscle car?)

Query expansion uses an LLM to:
1. **Extract synonyms** - "truck" -> "pickup, F-150, Silverado, RAM"
2. **Extract implicit filters** - "cheap" -> price_max: $25,000
3. **Disambiguate intent** - "family car" -> vehicle_types: [SUV, Minivan]

**Expected Impact**: Better recall for brief queries, improved user experience

---

## Acceptance Criteria

### AC1: LLM-Powered Query Expansion
**Given** a brief query "cheap truck for work"
**When** query expansion is executed
**Then** the LLM extracts:
  - Synonyms: ["pickup", "work truck", "hauling"]
  - Filters: {price_max: 30000, vehicle_type: "Truck"}
  - Expanded query: "affordable pickup truck work hauling towing"
**And** response time is < 200ms

### AC2: Groq Integration
**Given** the `QueryExpansionService`
**When** it makes LLM calls
**Then** it uses Groq via OpenRouter with model `openai/gpt-oss-20b`
**And** requests are properly rate-limited
**And** failures gracefully fallback to original query

### AC3: Structured Output Parsing
**Given** the LLM response
**When** parsed
**Then** JSON schema is enforced for:
  - `expanded_query: str`
  - `synonyms: List[str]`
  - `extracted_filters: Dict[str, Any]`
  - `confidence: float`
**And** invalid responses use fallback

### AC4: Caching for Common Queries
**Given** a query has been expanded before
**When** the same query is received
**Then** cached expansion is returned
**And** cache TTL is 1 hour
**And** cache key includes query normalization

### AC5: Integration with Hybrid Search
**Given** `HybridSearchService` receives a query
**When** expansion is enabled
**Then** expanded query is used for keyword search
**And** extracted filters are merged with user filters
**And** original query is used for embedding

---

## Technical Implementation

### Files to Create

| File | Purpose |
|------|---------|
| `src/search/query_expansion_service.py` | LLM-powered query expansion |

### QueryExpansionService Design

```python
class QueryExpansionService:
    """LLM-powered query expansion using Groq via OpenRouter"""

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = "openai/gpt-oss-20b"  # Groq-hosted model
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 hour

    async def expand_query(self, query: str) -> QueryExpansion:
        """Expand a search query with synonyms and extracted filters"""

        # Check cache first
        cache_key = self._normalize_query(query)
        if cached := self._get_from_cache(cache_key):
            return cached

        try:
            expansion = await self._call_llm(query)
            self._store_in_cache(cache_key, expansion)
            return expansion
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return QueryExpansion(
                original_query=query,
                expanded_query=query,
                synonyms=[],
                extracted_filters={},
                confidence=0.0
            )

    async def _call_llm(self, query: str) -> QueryExpansion:
        prompt = f'''Analyze this vehicle search query and extract structured information.

Query: "{query}"

Return JSON with:
- expanded_query: The query with relevant synonyms added
- synonyms: List of related vehicle terms
- extracted_filters: Any implicit filters (price_max, price_min, year_min, year_max, vehicle_type, make, fuel_type)
- confidence: How confident you are (0.0-1.0)

Examples:
- "cheap truck" -> {{"expanded_query": "affordable pickup truck budget", "synonyms": ["pickup", "work truck"], "extracted_filters": {{"price_max": 25000, "vehicle_type": "Truck"}}, "confidence": 0.8}}
- "electric SUV" -> {{"expanded_query": "electric SUV EV crossover", "synonyms": ["EV", "battery", "zero emission"], "extracted_filters": {{"fuel_type": "Electric", "vehicle_type": "SUV"}}, "confidence": 0.9}}

Return only valid JSON:'''

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
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=10
            )

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Parse JSON from response
            data = json.loads(content)

            return QueryExpansion(
                original_query=query,
                expanded_query=data.get('expanded_query', query),
                synonyms=data.get('synonyms', []),
                extracted_filters=data.get('extracted_filters', {}),
                confidence=data.get('confidence', 0.5)
            )
```

### Data Models

```python
from pydantic import BaseModel
from typing import List, Dict, Any

class QueryExpansion(BaseModel):
    """Result of query expansion"""
    original_query: str
    expanded_query: str
    synonyms: List[str]
    extracted_filters: Dict[str, Any]
    confidence: float
```

---

## Dependencies

### Prerequisites
- Story 1-9 (Hybrid Search) - For integration

### External
- OpenRouter API key (existing)
- Groq access via OpenRouter

---

## Test Plan

### Unit Tests
- [ ] `test_query_expansion_basic()` - "cheap truck" expands correctly
- [ ] `test_filter_extraction()` - "under $30k" extracts price_max
- [ ] `test_cache_hit()` - Same query returns cached result
- [ ] `test_fallback_on_error()` - API failure returns original query

### Integration Tests
- [ ] `test_expansion_with_hybrid_search()` - Expanded query improves results
- [ ] `test_groq_response_time()` - < 200ms latency

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Expansion latency | < 200ms |
| Cache hit rate | > 40% |
| Filter extraction accuracy | > 85% |
| Search improvement with expansion | +10% relevance |

---

## Definition of Done

- [ ] `QueryExpansionService` implemented
- [ ] Groq integration via OpenRouter working
- [ ] Response caching implemented
- [ ] Graceful fallback on errors
- [ ] Integration with HybridSearchService
- [ ] Unit tests pass
- [ ] Code reviewed and approved
