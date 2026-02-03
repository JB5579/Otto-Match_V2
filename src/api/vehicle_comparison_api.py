"""
Otto.AI Vehicle Comparison and Recommendation API Endpoints

Production-ready comparison and recommendation API endpoints for vehicle discovery.
Implements Story 1-5: Build Vehicle Comparison and Recommendation Engine

Features:
- Side-by-side vehicle comparison with detailed feature analysis
- Personalized recommendations using collaborative and content-based filtering
- Semantic similarity scoring between vehicles
- Real-time performance with caching
- Comprehensive user interaction tracking for personalization
- A/B testing framework for recommendation algorithms
"""

import os
import time
import asyncio
import logging
import hashlib
import uuid
import json
import pickle
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, root_validator
import uvicorn
import sys
import re

# Redis imports
import redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError, ConnectionError

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.embedding_service import OttoAIEmbeddingService, EmbeddingRequest
from src.semantic.vehicle_database_service import VehicleDatabaseService
from src.recommendation.comparison_engine import ComparisonEngine
from src.recommendation.recommendation_engine import RecommendationEngine
from src.recommendation.interaction_tracker import InteractionTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Enums and Constants
# ============================================================================

class RecommendationType(str, Enum):
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    SIMILARITY = "similarity"

class ComparisonFeatureType(str, Enum):
    SPECIFICATION = "specification"
    FEATURE = "feature"
    PRICE = "price"
    PERFORMANCE = "performance"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"

class FeatureDifferenceType(str, Enum):
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"
    NEUTRAL = "neutral"

# ============================================================================
# Pydantic Models for API
# ============================================================================

class VehicleComparisonRequest(BaseModel):
    """Vehicle comparison request model with comprehensive validation"""
    vehicle_ids: List[str] = Field(..., min_items=2, max_items=4, description="Vehicle IDs to compare")
    comparison_criteria: Optional[List[str]] = Field(None, description="Specific criteria to compare")
    include_semantic_similarity: bool = Field(True, description="Include semantic similarity scores")
    include_price_analysis: bool = Field(True, description="Include price and market analysis")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    comparison_id: Optional[str] = Field(None, description="Unique comparison identifier")

    @validator('vehicle_ids')
    def validate_vehicle_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Vehicle IDs must be unique')

        # Validate vehicle ID format (alphanumeric, hyphens, underscores)
        for vehicle_id in v:
            if not vehicle_id or not isinstance(vehicle_id, str):
                raise ValueError('Vehicle IDs must be non-empty strings')
            if not re.match(r'^[a-zA-Z0-9\-_]{1,50}$', vehicle_id):
                raise ValueError('Vehicle IDs must be 1-50 characters (alphanumeric, hyphens, underscores)')

        return v

    @validator('comparison_criteria')
    def validate_comparison_criteria(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Comparison criteria must be a list')
            if len(v) > 20:
                raise ValueError('Maximum 20 comparison criteria allowed')
            for criterion in v:
                if not isinstance(criterion, str) or len(criterion.strip()) == 0:
                    raise ValueError('Each comparison criterion must be a non-empty string')
                if len(criterion) > 100:
                    raise ValueError('Each comparison criterion must be less than 100 characters')
        return v

    @validator('user_id')
    def validate_user_id(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('User ID must be a string')
            if not re.match(r'^[a-zA-Z0-9\-_@.]{1,100}$', v):
                raise ValueError('User ID contains invalid characters')
        return v

    @validator('comparison_id')
    def validate_comparison_id(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Comparison ID must be a string')
            if not re.match(r'^[a-zA-Z0-9\-_]{1,50}$', v):
                raise ValueError('Comparison ID format is invalid')
        return v

    @root_validator
    def validate_request_consistency(cls, values):
        # Ensure at least one analysis type is enabled
        semantic = values.get('include_semantic_similarity', True)
        price = values.get('include_price_analysis', True)
        if not semantic and not price:
            raise ValueError('At least one analysis type (semantic similarity or price analysis) must be enabled')
        return values

class VehicleSpecification(BaseModel):
    """Vehicle specification details"""
    category: str
    name: str
    value: Union[str, int, float, bool]
    unit: Optional[str] = None
    importance_score: float = Field(1.0, ge=0.0, le=1.0, description="Importance weight for comparison")

class VehicleFeatures(BaseModel):
    """Vehicle features and amenities"""
    category: str
    features: List[str]
    included: bool
    value_score: float = Field(0.0, ge=0.0, le=1.0, description="Feature value score")

class FeatureDifference(BaseModel):
    """Feature difference between vehicles"""
    feature_name: str
    feature_type: ComparisonFeatureType
    vehicle_a_value: Union[str, int, float, bool]
    vehicle_b_value: Union[str, int, float, bool]
    difference_type: FeatureDifferenceType
    importance_weight: float = Field(1.0, ge=0.0, le=1.0)
    description: str

class PriceAnalysis(BaseModel):
    """Price analysis and market comparison"""
    current_price: float
    market_average: float
    market_range: Tuple[float, float]
    price_position: str  # "below_market", "at_market", "above_market"
    savings_amount: Optional[float] = None
    savings_percentage: Optional[float] = None
    price_trend: str  # "increasing", "stable", "decreasing"
    market_demand: str  # "low", "medium", "high"

class SemanticSimilarity(BaseModel):
    """Semantic similarity between vehicles"""
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    shared_features: List[str]
    unique_features_a: List[str]
    unique_features_b: List[str]
    similarity_explanation: str

class VehicleComparisonResult(BaseModel):
    """Individual vehicle comparison result"""
    vehicle_id: str
    vehicle_data: Dict[str, Any]
    specifications: List[VehicleSpecification]
    features: List[VehicleFeatures]
    price_analysis: PriceAnalysis
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall comparison score")

class VehicleComparisonResponse(BaseModel):
    """Complete vehicle comparison response"""
    comparison_id: str
    vehicle_ids: List[str]
    comparison_results: List[VehicleComparisonResult]
    feature_differences: List[FeatureDifference]
    semantic_similarity: Optional[Dict[str, SemanticSimilarity]] = None
    recommendation_summary: Optional[str] = None
    processing_time: float
    cached: bool = False
    timestamp: datetime

class RecommendationRequest(BaseModel):
    """Recommendation request model with comprehensive validation"""
    user_id: str = Field(..., description="User ID for personalization")
    context_vehicle_ids: Optional[List[str]] = Field(None, description="Context vehicles for recommendations")
    search_query: Optional[str] = Field(None, description="Current search query")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    recommendation_type: RecommendationType = Field(RecommendationType.HYBRID, description="Type of recommendation algorithm")
    limit: int = Field(10, ge=1, le=50, description="Number of recommendations")
    include_explanations: bool = Field(True, description="Include recommendation explanations")
    session_id: Optional[str] = Field(None, description="Session identifier")

    @validator('user_id')
    def validate_user_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError('User ID is required and must be a non-empty string')
        if not re.match(r'^[a-zA-Z0-9\-_@.]{1,100}$', v):
            raise ValueError('User ID contains invalid characters')
        if len(v) > 100:
            raise ValueError('User ID must be less than 100 characters')
        return v.strip()

    @validator('context_vehicle_ids')
    def validate_context_vehicle_ids(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Context vehicle IDs must be a list')
            if len(v) > 10:
                raise ValueError('Maximum 10 context vehicles allowed')
            if len(v) != len(set(v)):
                raise ValueError('Context vehicle IDs must be unique')
            for vehicle_id in v:
                if not isinstance(vehicle_id, str) or not vehicle_id.strip():
                    raise ValueError('Each context vehicle ID must be a non-empty string')
                if not re.match(r'^[a-zA-Z0-9\-_]{1,50}$', vehicle_id):
                    raise ValueError('Context vehicle ID format is invalid')
        return v

    @validator('search_query')
    def validate_search_query(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Search query must be a string')
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Search query must be less than 500 characters')
            # Check for potentially malicious content
            if any(char in v for char in ['<', '>', '"', "'", '&', 'script', 'javascript']):
                raise ValueError('Search query contains invalid characters')
        return v

    @validator('user_preferences')
    def validate_user_preferences(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('User preferences must be a dictionary')
            # Validate preference structure
            allowed_keys = {
                'preferred_brands', 'price_range', 'vehicle_types', 'features_priority',
                'color_preference', 'fuel_type_preference', 'transmission_preference'
            }
            invalid_keys = set(v.keys()) - allowed_keys
            if invalid_keys:
                raise ValueError(f'Invalid preference keys: {invalid_keys}')
        return v

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Session ID must be a string')
            if not re.match(r'^[a-zA-Z0-9\-_]{1,100}$', v):
                raise ValueError('Session ID format is invalid')
        return v

class RecommendationExplanation(BaseModel):
    """Explanation for recommendation"""
    reasoning_type: str
    explanation: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    supporting_factors: List[str]
    user_relevance_score: float = Field(..., ge=0.0, le=1.0)

class Recommendation(BaseModel):
    """Individual vehicle recommendation"""
    vehicle_id: str
    vehicle_data: Dict[str, Any]
    recommendation_score: float = Field(..., ge=0.0, le=1.0)
    match_percentage: int = Field(..., ge=0, le=100)
    explanation: RecommendationExplanation
    personalization_factors: List[str]
    trending_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    urgency_indicators: List[str] = []

class RecommendationResponse(BaseModel):
    """Complete recommendation response"""
    user_id: str
    recommendation_id: str
    recommendations: List[Recommendation]
    algorithm_version: str
    a_b_test_group: Optional[str] = None
    processing_time: float
    cached: bool = False
    timestamp: datetime

class UserInteraction(BaseModel):
    """User interaction tracking model with comprehensive validation"""
    user_id: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session identifier")
    interaction_type: str = Field(..., description="Type of interaction")
    vehicle_ids: List[str] = Field(..., description="Vehicle IDs involved in interaction")
    interaction_data: Dict[str, Any] = Field(default_factory=dict, description="Additional interaction data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Interaction timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Interaction context")

    @validator('user_id')
    def validate_user_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError('User ID is required and must be a non-empty string')
        if not re.match(r'^[a-zA-Z0-9\-_@.]{1,100}$', v):
            raise ValueError('User ID format is invalid')
        return v.strip()

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Session ID must be a string')
            if not re.match(r'^[a-zA-Z0-9\-_]{1,100}$', v):
                raise ValueError('Session ID format is invalid')
        return v

    @validator('interaction_type')
    def validate_interaction_type(cls, v):
        valid_types = {"view", "save", "compare", "search", "recommendation_click", "favorite", "share"}
        if v not in valid_types:
            raise ValueError(f'Invalid interaction type. Must be one of: {valid_types}')
        return v

    @validator('vehicle_ids')
    def validate_vehicle_ids(cls, v):
        if not isinstance(v, list):
            raise ValueError('Vehicle IDs must be a list')
        if len(v) == 0:
            raise ValueError('At least one vehicle ID is required')
        if len(v) > 50:  # Reasonable limit
            raise ValueError('Maximum 50 vehicle IDs allowed per interaction')
        if len(v) != len(set(v)):
            raise ValueError('Vehicle IDs must be unique')
        for vehicle_id in v:
            if not isinstance(vehicle_id, str) or not vehicle_id.strip():
                raise ValueError('Each vehicle ID must be a non-empty string')
            if not re.match(r'^[a-zA-Z0-9\-_]{1,50}$', vehicle_id):
                raise ValueError('Vehicle ID format is invalid')
        return v

    @validator('interaction_data')
    def validate_interaction_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Interaction data must be a dictionary')
        # Limit interaction data size to prevent abuse
        if len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Interaction data is too large')
        return v

class FeedbackRequest(BaseModel):
    """Recommendation feedback model with comprehensive validation"""
    user_id: str = Field(..., description="User ID")
    recommendation_id: str = Field(..., description="Recommendation identifier")
    vehicle_id: str = Field(..., description="Vehicle ID being reviewed")
    feedback_type: str = Field(..., description="Type of feedback")
    feedback_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Feedback score (0.0-1.0)")
    feedback_text: Optional[str] = Field(None, description="Detailed feedback text")
    timestamp: datetime = Field(default_factory=datetime.now, description="Feedback timestamp")

    @validator('user_id')
    def validate_user_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError('User ID is required and must be a non-empty string')
        if not re.match(r'^[a-zA-Z0-9\-_@.]{1,100}$', v):
            raise ValueError('User ID format is invalid')
        return v.strip()

    @validator('recommendation_id')
    def validate_recommendation_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError('Recommendation ID is required and must be a non-empty string')
        if not re.match(r'^[a-zA-Z0-9\-_]{1,100}$', v):
            raise ValueError('Recommendation ID format is invalid')
        return v.strip()

    @validator('vehicle_id')
    def validate_vehicle_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError('Vehicle ID is required and must be a non-empty string')
        if not re.match(r'^[a-zA-Z0-9\-_]{1,50}$', v):
            raise ValueError('Vehicle ID format is invalid')
        return v.strip()

    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        valid_types = {"helpful", "not_helpful", "bookmarked", "dismissed", "shared", "viewed_details"}
        if v not in valid_types:
            raise ValueError(f'Invalid feedback type. Must be one of: {valid_types}')
        return v

    @validator('feedback_text')
    def validate_feedback_text(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Feedback text must be a string')
            v = v.strip()
            if len(v) > 2000:  # 2KB limit
                raise ValueError('Feedback text must be less than 2000 characters')
            # Check for potentially malicious content
            if any(char in v for char in ['<', '>', '"', "'", '&', 'script', 'javascript']):
                raise ValueError('Feedback text contains invalid characters')
        return v

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

# ============================================================================
# Rate Limiting and Redis Caching
# ============================================================================

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests: int
    window_seconds: int
    remaining: int
    reset_time: datetime

class RedisCache:
    """Redis-backed cache for comparison results with fallback to in-memory"""

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 3600, prefix: str = "otto_ai:"):
        """
        Initialize Redis cache with fallback

        Args:
            redis_url: Redis connection URL (optional)
            ttl_seconds: Time-to-live for cached items
            prefix: Key prefix for Redis
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.ttl_seconds = ttl_seconds
        self.prefix = prefix
        self.redis_client: Optional[AsyncRedis] = None
        self.fallback_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.max_fallback_size = 100
        self.using_redis = False

    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_client = AsyncRedis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle binary data ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            self.using_redis = True
            logger.info("✅ Redis cache initialized successfully")
            return True

        except (ConnectionError, RedisError) as e:
            logger.warning(f"⚠️ Redis connection failed, using fallback in-memory cache: {e}")
            self.using_redis = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error initializing Redis: {e}")
            self.using_redis = False
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback"""
        cache_key = f"{self.prefix}{key}"

        if self.using_redis and self.redis_client:
            try:
                # Try Redis first
                data = await self.redis_client.get(cache_key)
                if data:
                    return pickle.loads(data)
            except RedisError as e:
                logger.warning(f"Redis get error for key {key}: {e}")
                # Fall back to in-memory cache

        # Fallback to in-memory cache
        return self._get_fallback(key)

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with fallback"""
        cache_key = f"{self.prefix}{key}"

        if self.using_redis and self.redis_client:
            try:
                # Try Redis first
                serialized_data = pickle.dumps(value)
                await self.redis_client.setex(cache_key, self.ttl_seconds, serialized_data)
                return
            except RedisError as e:
                logger.warning(f"Redis set error for key {key}: {e}")
                # Fall back to in-memory cache

        # Fallback to in-memory cache
        self._set_fallback(key, value)

    def _get_fallback(self, key: str) -> Optional[Any]:
        """Get from fallback in-memory cache"""
        if key in self.fallback_cache:
            data, timestamp = self.fallback_cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                return data
            else:
                del self.fallback_cache[key]
        return None

    def _set_fallback(self, key: str, value: Any) -> None:
        """Set in fallback in-memory cache"""
        if len(self.fallback_cache) >= self.max_fallback_size:
            # Remove oldest entry
            oldest_key = min(self.fallback_cache.keys(), key=lambda k: self.fallback_cache[k][1])
            del self.fallback_cache[oldest_key]
        self.fallback_cache[key] = (value, datetime.now())

    def generate_key(self, vehicle_ids: List[str], criteria: Optional[List[str]] = None) -> str:
        """Generate cache key for comparison"""
        vehicle_ids_sorted = sorted(vehicle_ids)
        key_data = f"cmp:{'_'.join(vehicle_ids_sorted)}"
        if criteria:
            key_data += f":{hashlib.md5('_'.join(sorted(criteria)).encode()).hexdigest()[:8]}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

# Global instances
comparison_cache: Optional[RedisCache] = None

# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimiter:
    """Redis-based rate limiting with in-memory fallback"""

    def __init__(self, redis_client: Optional[AsyncRedis] = None):
        self.redis_client = redis_client
        self.memory_store: Dict[str, Dict[str, Any]] = {}

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Rate limit key (e.g., 'api', 'user', 'ip')
            limit: Number of requests allowed
            window: Time window in seconds
            identifier: Unique identifier (user_id, ip_address, etc.)

        Returns:
            Tuple of (allowed, info_dict)
        """
        if identifier:
            rate_key = f"rate_limit:{key}:{identifier}"
        else:
            rate_key = f"rate_limit:{key}"

        now = int(time.time())
        window_start = now - window

        if self.redis_client:
            return await self._redis_rate_limit(rate_key, limit, window, now, window_start)
        else:
            return self._memory_rate_limit(rate_key, limit, window, now, window_start)

    async def _redis_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        now: int,
        window_start: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
            pipe.zcard(key)  # Count current requests
            pipe.zadd(key, {str(now): now})  # Add current request
            pipe.expire(key, window)  # Set expiration
            results = await pipe.execute()

            current_requests = results[1]
            allowed = current_requests <= limit

            return allowed, {
                "allowed": allowed,
                "limit": limit,
                "remaining": max(0, limit - current_requests),
                "reset_time": now + window,
                "current_requests": current_requests
            }

        except RedisError:
            logger.warning("Redis rate limiting failed, falling back to in-memory")
            return self._memory_rate_limit(key, limit, window, now, window_start)

    def _memory_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        now: int,
        window_start: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """In-memory rate limiting fallback"""
        if key not in self.memory_store:
            self.memory_store[key] = {"requests": [], "created": now}

        # Remove old requests
        self.memory_store[key]["requests"] = [
            req_time for req_time in self.memory_store[key]["requests"]
            if req_time > window_start
        ]

        # Add current request
        self.memory_store[key]["requests"].append(now)
        current_requests = len(self.memory_store[key]["requests"])

        allowed = current_requests <= limit

        return allowed, {
            "allowed": allowed,
            "limit": limit,
            "remaining": max(0, limit - current_requests),
            "reset_time": now + window,
            "current_requests": current_requests
        }

# Rate limiting middleware
class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, app):
        self.app = app
        self.rate_limiter: Optional[RateLimiter] = None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Initialize rate limiter if not already done
        if self.rate_limiter is None:
            redis_client = None
            if comparison_cache and comparison_cache.using_redis:
                redis_client = comparison_cache.redis_client
            self.rate_limiter = RateLimiter(redis_client)

        # Extract client information
        client_ip = scope.get("client", ["127.0.0.1"])[0]
        user_agent = scope.get("headers", {}).get(b"user-agent", b"").decode("utf-8")

        # Apply rate limits
        await self._apply_rate_limits(scope, client_ip, user_agent)

        await self.app(scope, receive, send)

    async def _apply_rate_limits(self, scope: dict, client_ip: str, user_agent: str):
        """Apply appropriate rate limits based on endpoint"""
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Different rate limits for different endpoints
        if path.startswith("/api/vehicles/compare"):
            # Strict rate limiting for comparison endpoint (computationally expensive)
            allowed, info = await self.rate_limiter.is_allowed(
                key="compare",
                limit=10,  # 10 requests
                window=60,  # per minute
                identifier=client_ip
            )
        elif path.startswith("/api/recommendations/"):
            # Moderate rate limiting for recommendations
            allowed, info = await self.rate_limiter.is_allowed(
                key="recommendations",
                limit=30,  # 30 requests
                window=60,  # per minute
                identifier=client_ip
            )
        elif path.startswith("/api/"):
            # General API rate limiting
            allowed, info = await self.rate_limiter.is_allowed(
                key="general",
                limit=100,  # 100 requests
                window=60,  # per minute
                identifier=client_ip
            )
        else:
            # No rate limiting for health endpoints and docs
            return

        # Add rate limit headers to response
        scope["rate_limit_info"] = info

        if not allowed:
            # Create HTTP 429 response
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {
                        "limit": info["limit"],
                        "window": 60,
                        "retry_after": info["reset_time"] - int(time.time())
                    }
                }
            )

            await self._send_response(response, scope.get("receive"), scope.get("send"))

    async def _send_response(self, response, receive, send):
        """Send HTTP response"""
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (k.encode(), v.encode()) for k, v in response.headers.items()
            ],
        })
        await send({
            "type": "http.response.body",
            "body": response.body,
        })

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Otto.AI Vehicle Comparison and Recommendation API",
    description="Production-ready vehicle comparison and recommendation engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances (will be initialized in startup)
vehicle_db_service: Optional[VehicleDatabaseService] = None
embedding_service: Optional[OttoAIEmbeddingService] = None
comparison_engine: Optional[ComparisonEngine] = None
recommendation_engine: Optional[RecommendationEngine] = None
interaction_tracker: Optional[InteractionTracker] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with proper Supabase and Redis connections"""
    global vehicle_db_service, embedding_service, comparison_engine, recommendation_engine, interaction_tracker, comparison_cache

    logger.info("Starting Otto.AI Vehicle Comparison API...")

    try:
        # Initialize Redis cache first
        comparison_cache = RedisCache()
        redis_initialized = await comparison_cache.initialize()
        if redis_initialized:
            logger.info("✅ Redis cache initialized")
        else:
            logger.warning("⚠️ Redis cache unavailable, using in-memory fallback")

        # Initialize vehicle database service with Supabase connection
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

        # Initialize services
        vehicle_db_service = VehicleDatabaseService()

        # Initialize database connection
        db_initialized = await vehicle_db_service.initialize(supabase_url, supabase_key)
        if not db_initialized:
            raise RuntimeError("Failed to initialize database connection")

        embedding_service = OttoAIEmbeddingService()
        comparison_engine = ComparisonEngine(vehicle_db_service, embedding_service)
        recommendation_engine = RecommendationEngine(vehicle_db_service, embedding_service)
        interaction_tracker = InteractionTracker()

        logger.info("✅ All services initialized successfully with Supabase and Redis connections")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Initialize fallback services
        if not comparison_cache:
            comparison_cache = RedisCache()
            await comparison_cache.initialize()

        vehicle_db_service = VehicleDatabaseService()
        embedding_service = OttoAIEmbeddingService()
        comparison_engine = ComparisonEngine(vehicle_db_service, embedding_service)
        recommendation_engine = RecommendationEngine(vehicle_db_service, embedding_service)
        interaction_tracker = InteractionTracker()

        logger.warning("⚠️ Services initialized with limited functionality")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global comparison_cache
    logger.info("Shutting down Otto.AI Vehicle Comparison API...")

    # Close Redis connection
    if comparison_cache:
        await comparison_cache.close()

    logger.info("Cleanup completed")

# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/vehicles/compare", response_model=VehicleComparisonResponse)
async def compare_vehicles(
    request: VehicleComparisonRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """
    Compare multiple vehicles side-by-side with detailed analysis
    """
    start_time = time.time()

    try:
        # Generate comparison ID if not provided
        comparison_id = request.comparison_id or str(uuid.uuid4())

        # Check cache first
        cache_key = comparison_cache.generate_key(request.vehicle_ids, request.comparison_criteria)
        cached_result = await comparison_cache.get(cache_key)

        if cached_result:
            logger.info(f"Returning cached comparison for {len(request.vehicle_ids)} vehicles")
            cached_result.cached = True
            return cached_result

        # Perform comparison
        logger.info(f"Performing vehicle comparison for {len(request.vehicle_ids)} vehicles")

        comparison_results = await comparison_engine.compare_vehicles(
            vehicle_ids=request.vehicle_ids,
            criteria=request.comparison_criteria,
            include_semantic_similarity=request.include_semantic_similarity,
            include_price_analysis=request.include_price_analysis,
            user_id=request.user_id
        )

        processing_time = time.time() - start_time

        # Create response
        response = VehicleComparisonResponse(
            comparison_id=comparison_id,
            vehicle_ids=request.vehicle_ids,
            comparison_results=comparison_results.comparison_results,
            feature_differences=comparison_results.feature_differences,
            semantic_similarity=comparison_results.semantic_similarity,
            recommendation_summary=comparison_results.recommendation_summary,
            processing_time=processing_time,
            cached=False,
            timestamp=datetime.now()
        )

        # Cache the result
        await comparison_cache.set(cache_key, response)

        # Track interaction in background
        if request.user_id:
            background_tasks.add_task(
                interaction_tracker.track_comparison,
                user_id=request.user_id,
                vehicle_ids=request.vehicle_ids,
                comparison_id=comparison_id,
                processing_time=processing_time
            )

        logger.info(f"Vehicle comparison completed in {processing_time:.3f}s")
        return response

    except Exception as e:
        logger.error(f"Vehicle comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: str,
    context_vehicle_ids: Optional[str] = Query(None, description="Comma-separated vehicle IDs"),
    search_query: Optional[str] = Query(None, description="Current search query"),
    recommendation_type: RecommendationType = Query(RecommendationType.HYBRID),
    limit: int = Query(10, ge=1, le=50),
    include_explanations: bool = Query(True),
    session_id: Optional[str] = Query(None)
):
    """
    Get personalized vehicle recommendations for a user
    """
    start_time = time.time()

    try:
        # Parse context vehicle IDs
        context_vehicles = None
        if context_vehicle_ids:
            context_vehicles = [vid.strip() for vid in context_vehicle_ids.split(',') if vid.strip()]

        # Generate recommendation ID
        recommendation_id = str(uuid.uuid4())

        # Get recommendations
        logger.info(f"Generating recommendations for user {user_id}")

        recommendations = await recommendation_engine.get_recommendations(
            user_id=user_id,
            context_vehicle_ids=context_vehicles,
            search_query=search_query,
            recommendation_type=recommendation_type,
            limit=limit,
            include_explanations=include_explanations,
            session_id=session_id
        )

        processing_time = time.time() - start_time

        # Create response
        response = RecommendationResponse(
            user_id=user_id,
            recommendation_id=recommendation_id,
            recommendations=recommendations.recommendations,
            algorithm_version=recommendations.algorithm_version,
            a_b_test_group=recommendations.a_b_test_group,
            processing_time=processing_time,
            cached=recommendations.cached,
            timestamp=datetime.now()
        )

        logger.info(f"Recommendations generated for user {user_id} in {processing_time:.3f}s")
        return response

    except Exception as e:
        logger.error(f"Recommendation generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interactions", status_code=201)
async def track_interaction(
    interaction: UserInteraction,
    background_tasks: BackgroundTasks
):
    """
    Track user interactions for personalization and analytics
    """
    try:
        # Validate interaction data
        if not interaction.vehicle_ids and interaction.interaction_type in ["view", "save", "compare"]:
            raise HTTPException(status_code=400, detail="Vehicle IDs required for this interaction type")

        # Track interaction in background
        background_tasks.add_task(
            interaction_tracker.track_interaction,
            interaction.dict()
        )

        logger.info(f"Interaction tracked for user {interaction.user_id}: {interaction.interaction_type}")
        return {"status": "tracked", "interaction_id": str(uuid.uuid4())}

    except Exception as e:
        logger.error(f"Interaction tracking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/feedback", status_code=201)
async def submit_recommendation_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit feedback on recommendations to improve algorithms
    """
    try:
        # Process feedback in background
        background_tasks.add_task(
            recommendation_engine.process_feedback,
            feedback.dict()
        )

        logger.info(f"Feedback processed for recommendation {feedback.recommendation_id}")
        return {"status": "processed", "feedback_id": str(uuid.uuid4())}

    except Exception as e:
        logger.error(f"Feedback processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "services": {
            "vehicle_db": "connected" if vehicle_db_service else "disconnected",
            "embedding_service": "connected" if embedding_service else "disconnected",
            "comparison_engine": "ready" if comparison_engine else "not_ready",
            "recommendation_engine": "ready" if recommendation_engine else "not_ready",
            "interaction_tracker": "ready" if interaction_tracker else "not_ready"
        }
    }

# ============================================================================
# Error Handling
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_EXCEPTION",
            message=exc.detail,
            timestamp=datetime.now()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            timestamp=datetime.now()
        ).dict()
    )

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "vehicle_comparison_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )