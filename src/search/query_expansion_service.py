"""
Otto.AI Query Expansion Service

LLM-powered query expansion using Groq via OpenRouter.
Extracts synonyms, implicit filters, and expanded query text.

Story: 1-10 Add Query Expansion Service
"""

import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryExpansion(BaseModel):
    """Result of query expansion"""
    original_query: str = Field(..., description="Original user query")
    expanded_query: str = Field(..., description="Query with synonyms added")
    synonyms: List[str] = Field(default_factory=list, description="Related vehicle terms")
    extracted_filters: Dict[str, Any] = Field(default_factory=dict, description="Implicit filters")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    cached: bool = Field(False, description="Whether result was cached")
    latency_ms: float = Field(0.0, description="Processing time in milliseconds")


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: QueryExpansion
    timestamp: datetime


class QueryExpansionService:
    """
    LLM-powered query expansion using Groq via OpenRouter.

    Expands brief queries with synonyms and extracts implicit filters:
    - "cheap truck" -> synonyms: ["pickup", "work truck"], filters: {price_max: 25000}
    - "electric SUV" -> synonyms: ["EV", "battery"], filters: {fuel_type: "Electric"}
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('QUERY_EXPANSION_MODEL', 'openai/gpt-oss-20b')
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = cache_ttl_seconds
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
            "avg_latency_ms": 0.0
        }

    async def expand_query(self, query: str) -> QueryExpansion:
        """
        Expand a search query with synonyms and extracted filters.

        Args:
            query: Original user search query

        Returns:
            QueryExpansion with expanded query, synonyms, and filters
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Check cache first
        cache_key = self._get_cache_key(query)
        if cached := self._get_from_cache(cache_key):
            self.stats["cache_hits"] += 1
            cached.cached = True
            cached.latency_ms = (time.time() - start_time) * 1000
            return cached

        try:
            # Call LLM for expansion
            self.stats["api_calls"] += 1
            expansion = await self._call_llm(query)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            expansion.latency_ms = latency_ms

            # Update average latency
            total_calls = self.stats["api_calls"]
            self.stats["avg_latency_ms"] = (
                (self.stats["avg_latency_ms"] * (total_calls - 1) + latency_ms) / total_calls
            )

            # Cache the result
            self._store_in_cache(cache_key, expansion)

            logger.info(
                f"Query expansion: '{query[:50]}...' -> "
                f"{len(expansion.synonyms)} synonyms, "
                f"{len(expansion.extracted_filters)} filters, "
                f"{latency_ms:.0f}ms"
            )

            return expansion

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(f"Query expansion failed for '{query}': {e}")

            # Return fallback with original query
            return QueryExpansion(
                original_query=query,
                expanded_query=query,
                synonyms=[],
                extracted_filters={},
                confidence=0.0,
                cached=False,
                latency_ms=(time.time() - start_time) * 1000
            )

    async def _call_llm(self, query: str) -> QueryExpansion:
        """Call LLM API for query expansion"""

        prompt = f'''You are a vehicle search assistant. Analyze this search query and extract structured information to improve search results.

Query: "{query}"

Return a JSON object with:
1. "expanded_query": The query with relevant automotive synonyms added (keep it concise)
2. "synonyms": List of related vehicle terms (max 5)
3. "extracted_filters": Any implicit filters detected:
   - price_max: If "cheap", "budget", "affordable" -> 25000-35000
   - price_min: If "luxury", "premium" -> 40000+
   - vehicle_type: "SUV", "Truck", "Sedan", "Coupe", "Minivan", etc.
   - fuel_type: "Electric", "Hybrid", "Gasoline", "Diesel"
   - year_min: If "new", "recent" -> current_year - 3
   - make: If specific brand mentioned
4. "confidence": How confident you are (0.0-1.0)

Examples:
- "cheap truck" -> {{"expanded_query": "affordable pickup truck work", "synonyms": ["pickup", "work truck", "hauling"], "extracted_filters": {{"price_max": 30000, "vehicle_type": "Truck"}}, "confidence": 0.8}}
- "electric SUV" -> {{"expanded_query": "electric SUV EV crossover zero emission", "synonyms": ["EV", "battery electric", "crossover"], "extracted_filters": {{"fuel_type": "Electric", "vehicle_type": "SUV"}}, "confidence": 0.9}}
- "family minivan" -> {{"expanded_query": "family minivan spacious seating", "synonyms": ["van", "people mover", "third row"], "extracted_filters": {{"vehicle_type": "Minivan"}}, "confidence": 0.85}}

Return ONLY valid JSON, no explanation:'''

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto.ai",
                    "X-Title": "Otto.AI Query Expansion"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=10
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Parse JSON from response (handle markdown code blocks)
            json_str = content.strip()
            if json_str.startswith('```'):
                # Extract from code block
                lines = json_str.split('\n')
                json_str = '\n'.join(lines[1:-1])

            data = json.loads(json_str)

            return QueryExpansion(
                original_query=query,
                expanded_query=data.get('expanded_query', query),
                synonyms=data.get('synonyms', [])[:5],  # Limit to 5
                extracted_filters=self._validate_filters(data.get('extracted_filters', {})),
                confidence=min(1.0, max(0.0, data.get('confidence', 0.5)))
            )

    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extracted filters"""
        validated = {}

        # Price filters
        if 'price_max' in filters:
            try:
                validated['price_max'] = float(filters['price_max'])
            except (ValueError, TypeError):
                pass

        if 'price_min' in filters:
            try:
                validated['price_min'] = float(filters['price_min'])
            except (ValueError, TypeError):
                pass

        # Year filters
        if 'year_min' in filters:
            try:
                year = int(filters['year_min'])
                if 1900 <= year <= 2030:
                    validated['year_min'] = year
            except (ValueError, TypeError):
                pass

        if 'year_max' in filters:
            try:
                year = int(filters['year_max'])
                if 1900 <= year <= 2030:
                    validated['year_max'] = year
            except (ValueError, TypeError):
                pass

        # String filters
        string_fields = ['vehicle_type', 'fuel_type', 'make', 'model']
        for field in string_fields:
            if field in filters and filters[field]:
                validated[field] = str(filters[field]).strip()[:50]

        return validated

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from normalized query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[QueryExpansion]:
        """Get expansion from cache if valid"""
        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]
        if datetime.now() - entry.timestamp > timedelta(seconds=self.cache_ttl):
            del self.cache[cache_key]
            return None

        return entry.data

    def _store_in_cache(self, cache_key: str, expansion: QueryExpansion):
        """Store expansion in cache"""
        self.cache[cache_key] = CacheEntry(
            data=expansion,
            timestamp=datetime.now()
        )

        # Clean up old entries if cache is too large
        if len(self.cache) > 1000:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].timestamp
            )
            del self.cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            )
        }

    def clear_cache(self):
        """Clear the query cache"""
        self.cache.clear()
        logger.info("Query expansion cache cleared")
