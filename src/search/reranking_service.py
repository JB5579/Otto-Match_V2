"""
Otto.AI Re-ranking Service

Cross-encoder re-ranking using BAAI/bge-reranker-large via OpenRouter
for precise relevance scoring of search candidates.

Story: 1-11 Implement Re-ranking Layer
"""

import os
import asyncio
import logging
import time
import math
from typing import Dict, Any, Optional, List

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RerankCandidate(BaseModel):
    """Candidate for re-ranking"""
    id: str
    text: str
    original_score: float = 0.0
    vehicle_data: Dict[str, Any] = Field(default_factory=dict)


class RerankResult(BaseModel):
    """Re-ranked result"""
    id: str
    rerank_score: float = Field(0.0, description="Cross-encoder relevance score")
    original_score: float = Field(0.0, description="Original hybrid score")
    final_score: float = Field(0.0, description="Final combined score")
    vehicle_data: Dict[str, Any] = Field(default_factory=dict)


class RerankingService:
    """
    Cross-encoder re-ranking for precise relevance scoring.

    Takes top candidates from hybrid search and re-scores them using
    a cross-encoder model that evaluates (query, document) pairs directly.

    Trade-off: Adds ~200ms latency but significantly improves precision.
    """

    def __init__(
        self,
        batch_size: int = 10,
        timeout_ms: int = 250,
        enabled: bool = True
    ):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('RERANK_MODEL', 'baai/bge-reranker-large')
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
        self.enabled = enabled
        self.api_url = "https://openrouter.ai/api/v1/rerank"

        # Statistics
        self.stats = {
            "total_reranks": 0,
            "candidates_processed": 0,
            "avg_latency_ms": 0.0,
            "timeouts": 0,
            "errors": 0,
            "skipped": 0
        }

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 20
    ) -> List[RerankResult]:
        """
        Re-rank candidates using cross-encoder model.

        Args:
            query: Original user search query
            candidates: List of candidate vehicles with hybrid scores
            top_k: Number of top results to return

        Returns:
            List of RerankResult sorted by cross-encoder score
        """
        if not self.enabled:
            self.stats["skipped"] += 1
            return self._passthrough(candidates, top_k)

        if not candidates:
            return []

        start_time = time.time()
        self.stats["total_reranks"] += 1
        self.stats["candidates_processed"] += len(candidates)

        # Prepare candidates
        rerank_candidates = [
            RerankCandidate(
                id=str(c.get('id', '')),
                text=self._create_vehicle_text(c),
                original_score=c.get('hybrid_score', 0),
                vehicle_data=c
            )
            for c in candidates
        ]

        try:
            # Batch candidates
            batches = [
                rerank_candidates[i:i + self.batch_size]
                for i in range(0, len(rerank_candidates), self.batch_size)
            ]

            # Process batches with timeout
            remaining_ms = self.timeout_ms - int((time.time() - start_time) * 1000)
            if remaining_ms <= 0:
                logger.warning("Re-ranking timeout before processing")
                self.stats["timeouts"] += 1
                return self._passthrough(candidates, top_k)

            # Process batches in parallel
            tasks = [self._score_batch(query, batch) for batch in batches]

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=remaining_ms / 1000
                )
            except asyncio.TimeoutError:
                logger.warning("Re-ranking timeout during batch processing")
                self.stats["timeouts"] += 1
                return self._passthrough(candidates, top_k)

            # Collect scores
            all_scores: Dict[str, float] = {}
            for batch_result in results:
                if isinstance(batch_result, Exception):
                    logger.warning(f"Batch failed: {batch_result}")
                    continue
                all_scores.update(batch_result)

            # Build reranked results
            reranked: List[RerankResult] = []
            for candidate in rerank_candidates:
                rerank_score = all_scores.get(candidate.id, candidate.original_score)
                reranked.append(RerankResult(
                    id=candidate.id,
                    rerank_score=rerank_score,
                    original_score=candidate.original_score,
                    final_score=rerank_score,
                    vehicle_data=candidate.vehicle_data
                ))

            # Sort by rerank score
            reranked.sort(key=lambda x: x.final_score, reverse=True)

            # Update stats
            latency_ms = (time.time() - start_time) * 1000
            total = self.stats["total_reranks"]
            self.stats["avg_latency_ms"] = (
                (self.stats["avg_latency_ms"] * (total - 1) + latency_ms) / total
            )

            logger.info(
                f"Re-ranked {len(candidates)} candidates in {latency_ms:.0f}ms"
            )

            return reranked[:top_k]

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Re-ranking failed: {e}")
            return self._passthrough(candidates, top_k)

    async def _score_batch(
        self,
        query: str,
        batch: List[RerankCandidate]
    ) -> Dict[str, float]:
        """Score a batch of candidates using cross-encoder"""

        texts = [c.text for c in batch]
        ids = [c.id for c in batch]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://otto.ai",
                        "X-Title": "Otto.AI Re-ranking"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": texts,
                        "top_n": len(texts)
                    },
                    timeout=5
                )

                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code}")

                result = response.json()

                # Map scores back to IDs
                scores: Dict[str, float] = {}
                for item in result.get("results", []):
                    idx = item["index"]
                    raw_score = item.get("relevance_score", 0)
                    scores[ids[idx]] = self._normalize_score(raw_score)

                return scores

        except Exception as e:
            logger.warning(f"Batch scoring failed: {e}")
            # Return original scores as fallback
            return {c.id: c.original_score for c in batch}

    def _normalize_score(self, score: float) -> float:
        """Normalize cross-encoder score to 0-1 range using sigmoid"""
        # BGE reranker outputs logits, apply sigmoid
        return 1 / (1 + math.exp(-score))

    def _create_vehicle_text(self, vehicle: Dict[str, Any]) -> str:
        """Create text representation for cross-encoder"""
        parts = [
            f"{vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}",
            vehicle.get('trim', ''),
            vehicle.get('vehicle_type', ''),
            # Truncate description for efficiency
            (vehicle.get('description', '') or '')[:300]
        ]
        return " ".join(filter(None, parts))

    def _passthrough(
        self,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[RerankResult]:
        """Pass through results without re-ranking"""
        results = [
            RerankResult(
                id=str(c.get('id', '')),
                rerank_score=c.get('hybrid_score', 0),
                original_score=c.get('hybrid_score', 0),
                final_score=c.get('hybrid_score', 0),
                vehicle_data=c
            )
            for c in candidates[:top_k]
        ]
        return results

    def set_enabled(self, enabled: bool):
        """Enable or disable re-ranking"""
        self.enabled = enabled
        logger.info(f"Re-ranking {'enabled' if enabled else 'disabled'}")

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "enabled": self.enabled,
            "batch_size": self.batch_size,
            "timeout_ms": self.timeout_ms
        }
