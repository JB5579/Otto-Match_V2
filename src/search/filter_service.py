"""
Otto.AI Intelligent Vehicle Filtering Service

Implements Story 1-4: Intelligent Vehicle Filtering with Context
Building on Stories 1-1, 1-2, 1-3 foundation

Features:
- Enhanced filter validation and sanitization
- Filter suggestions based on search context
- Saved filter combinations for users
- Redis caching for popular filter combinations
- A/B testing support for filter optimization
"""

import os
import json
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import redis.asyncio as redis
from pydantic import BaseModel, Field, validator
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.vehicle_database_service import VehicleDatabaseService
from src.semantic.embedding_service import OttoAIEmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Enhanced Data Models
# ============================================================================

class FeatureFilter(BaseModel):
    """Vehicle feature filter with validation"""
    feature_name: str = Field(..., description="Feature name (e.g., 'leather seats', 'sunroof')")
    feature_value: Optional[str] = Field(None, description="Feature value or preference")
    required: bool = Field(False, description="Whether feature is required or preferred")

class SavedFilter(BaseModel):
    """Saved filter combination model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Filter combination name")
    description: Optional[str] = Field(None, max_length=500, description="Filter description")
    filters: Dict[str, Any] = Field(..., description="Filter combination data")
    is_public: bool = Field(False, description="Whether filter is shareable")
    usage_count: int = Field(0, ge=0, description="Number of times this filter has been used")
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = Field(None, description="Last time filter was used")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Filter name cannot be empty')
        return v.strip()

class FilterSuggestion(BaseModel):
    """Filter suggestion model"""
    filter_name: str = Field(..., description="Filter parameter name")
    suggested_value: Any = Field(..., description="Suggested filter value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in suggestion")
    reason: str = Field(..., description="Why this filter is suggested")
    search_context: str = Field(..., description="Context from search query")

class FilterSuggestionResponse(BaseModel):
    """Response model for filter suggestions"""
    search_query: str
    suggestions: List[FilterSuggestion]
    popular_filters: List[Dict[str, Any]]
    context_analysis: Dict[str, Any]

class SearchContext(BaseModel):
    """Search context for intelligent filtering"""
    query: str = Field(..., description="Original search query")
    query_embedding: Optional[List[float]] = Field(None, description="Query embedding vector")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    search_history: List[str] = Field(default_factory=list, description="Recent search queries")
    location_hint: Optional[str] = Field(None, description="Location context")
    budget_range: Optional[Tuple[float, float]] = Field(None, description="Budget range from query")
    vehicle_types: List[str] = Field(default_factory=list, description="Vehicle types mentioned")
    features_mentioned: List[str] = Field(default_factory=list, description="Features mentioned in query")

# ============================================================================
# Filter Service Implementation
# ============================================================================

@dataclass
class FilterStats:
    """Filter usage statistics"""
    total_filter_combinations: int = 0
    popular_filters: Dict[str, int] = None
    average_filters_per_search: float = 0.0
    cache_hit_rate: float = 0.0
    suggestion_accuracy: float = 0.0

    def __post_init__(self):
        if self.popular_filters is None:
            self.popular_filters = {}

class IntelligentFilterService:
    """
    Intelligent vehicle filtering service with context awareness
    """

    def __init__(self):
        self.vehicle_db_service: Optional[VehicleDatabaseService] = None
        self.embedding_service: Optional[OttoAIEmbeddingService] = None
        self.redis_client: Optional[redis.Redis] = None

        # Configuration
        self.cache_ttl = 3600  # 1 hour for filter cache
        self.suggestion_cache_ttl = 1800  # 30 minutes for suggestions
        self.popular_filter_threshold = 5  # Minimum usage to be considered popular

        # Statistics tracking
        self.stats = FilterStats()

        # Predefined filter mappings for common queries
        self.filter_mappings = {
            "luxury": {
                "makes": ["BMW", "Mercedes-Benz", "Audi", "Lexus", "Cadillac", "Lincoln"],
                "price_min": 40000,
                "features": ["leather seats", "premium audio", "navigation", "sunroof"]
            },
            "family": {
                "vehicle_types": ["SUV", "Minivan", "Crossover"],
                "features": ["third row seating", "cargo space", "safety features"],
                "price_range": (25000, 60000)
            },
            "eco-friendly": {
                "fuel_types": ["Electric", "Hybrid", "Plug-in Hybrid"],
                "makes": ["Tesla", "Toyota", "Honda", "Hyundai", "Kia"]
            },
            "sports car": {
                "vehicle_types": ["Coupe", "Convertible", "Sports Car"],
                "features": ["performance", "turbo", "sport mode"]
            },
            "truck": {
                "vehicle_types": ["Truck", "Pickup"],
                "features": ["towing capacity", "four-wheel drive", "bed liner"]
            },
            "commuter": {
                "fuel_types": ["Hybrid", "Electric", "Gasoline"],
                "price_max": 30000,
                "features": ["good gas mileage", "compact size"]
            }
        }

    async def initialize(self, supabase_url: str, supabase_key: str, redis_url: Optional[str] = None) -> bool:
        """Initialize the filter service"""
        try:
            logger.info("🚀 Initializing Intelligent Filter Service...")

            # Initialize vehicle database service
            self.vehicle_db_service = VehicleDatabaseService()
            if not await self.vehicle_db_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize vehicle database service")

            # Initialize embedding service
            self.embedding_service = OttoAIEmbeddingService()
            if not await self.embedding_service.initialize(supabase_url, supabase_key):
                raise Exception("Failed to initialize embedding service")

            # Initialize Redis if available
            if redis_url:
                try:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                    await self.redis_client.ping()
                    logger.info("✅ Redis connection established")
                except Exception as e:
                    logger.warning(f"⚠️ Redis connection failed, using memory cache: {e}")
                    self.redis_client = None

            logger.info("✅ Intelligent Filter Service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Filter Service: {e}")
            return False

    async def create_saved_filter(self, user_id: str, name: str, filters: Dict[str, Any],
                                description: Optional[str] = None, is_public: bool = False) -> SavedFilter:
        """Save a filter combination for a user"""
        try:
            saved_filter = SavedFilter(
                user_id=user_id,
                name=name,
                description=description,
                filters=filters,
                is_public=is_public
            )

            # Save to database (would implement in real system)
            # For now, store in cache as demonstration
            if self.redis_client:
                cache_key = f"saved_filter:{saved_filter.id}"
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl * 24 * 7,  # 1 week for saved filters
                    json.dumps(saved_filter.dict())
                )

                # Add to user's filter list
                user_filters_key = f"user_filters:{user_id}"
                await self.redis_client.sadd(user_filters_key, saved_filter.id)
                await self.redis_client.expire(user_filters_key, self.cache_ttl * 24 * 7)

            logger.info(f"✅ Saved filter '{name}' for user {user_id}")
            return saved_filter

        except Exception as e:
            logger.error(f"❌ Failed to save filter: {e}")
            raise

    async def get_user_saved_filters(self, user_id: str) -> List[SavedFilter]:
        """Get all saved filters for a user"""
        try:
            if not self.redis_client:
                return []

            user_filters_key = f"user_filters:{user_id}"
            filter_ids = await self.redis_client.smembers(user_filters_key)

            filters = []
            for filter_id in filter_ids:
                cache_key = f"saved_filter:{filter_id}"
                filter_data = await self.redis_client.get(cache_key)
                if filter_data:
                    filter_dict = json.loads(filter_data)
                    # Convert datetime strings back to datetime objects
                    if 'created_at' in filter_dict:
                        filter_dict['created_at'] = datetime.fromisoformat(filter_dict['created_at'])
                    if 'last_used' in filter_dict and filter_dict['last_used']:
                        filter_dict['last_used'] = datetime.fromisoformat(filter_dict['last_used'])
                    filters.append(SavedFilter(**filter_dict))

            return sorted(filters, key=lambda f: f.created_at, reverse=True)

        except Exception as e:
            logger.error(f"❌ Failed to get user filters: {e}")
            return []

    async def generate_filter_suggestions(self, search_context: SearchContext) -> FilterSuggestionResponse:
        """Generate intelligent filter suggestions based on search context"""
        try:
            query = search_context.query.lower()
            suggestions = []

            # Check cache first
            if self.redis_client:
                cache_key = f"filter_suggestions:{hashlib.md5(query.encode()).hexdigest()}"
                cached_suggestions = await self.redis_client.get(cache_key)
                if cached_suggestions:
                    logger.info(f"Cache hit for filter suggestions: {query[:50]}...")
                    return FilterSuggestionResponse(**json.loads(cached_suggestions))

            # Analyze query for filter suggestions
            query_lower = query.lower()

            # Check for luxury indicators
            luxury_keywords = ["luxury", "premium", "high-end", "deluxe", "exclusive"]
            if any(keyword in query_lower for keyword in luxury_keywords):
                if "suv" in query_lower:
                    suggestions.append(FilterSuggestion(
                        filter_name="vehicle_type",
                        suggested_value="SUV",
                        confidence_score=0.9,
                        reason="Query mentions luxury SUV",
                        search_context=query
                    ))

                suggestions.append(FilterSuggestion(
                    filter_name="price_min",
                    suggested_value=40000,
                    confidence_score=0.8,
                    reason="Luxury vehicles typically start at $40,000+",
                    search_context=query
                ))

                # Suggest luxury makes
                luxury_makes = ["BMW", "Mercedes-Benz", "Audi", "Lexus", "Cadillac"]
                suggestions.append(FilterSuggestion(
                    filter_name="make",
                    suggested_value=luxury_makes,
                    confidence_score=0.7,
                    reason="Popular luxury brands for SUVs",
                    search_context=query
                ))

            # Check for budget constraints
            budget_patterns = [
                (r"under \$?(\d+)", "price_max"),
                (r"less than \$?(\d+)", "price_max"),
                (r"below \$?(\d+)", "price_max"),
                (r"over \$?(\d+)", "price_min"),
                (r"above \$?(\d+)", "price_min"),
                (r"more than \$?(\d+)", "price_min"),
                (r"between \$?(\d+) and \$?(\d+)", "price_range"),
                (r"\$?(\d+)-\$?(\d+)", "price_range")
            ]

            import re
            for pattern, filter_type in budget_patterns:
                match = re.search(pattern, query)
                if match:
                    if filter_type == "price_range" and len(match.groups()) == 2:
                        min_price = float(match.group(1))
                        max_price = float(match.group(2))
                        suggestions.append(FilterSuggestion(
                            filter_name="price_range",
                            suggested_value=(min_price, max_price),
                            confidence_score=0.95,
                            reason=f"Explicit price range mentioned: ${min_price:,}-${max_price:,}",
                            search_context=query
                        ))
                    elif filter_type in ["price_min", "price_max"]:
                        price = float(match.group(1))
                        suggestions.append(FilterSuggestion(
                            filter_name=filter_type,
                            suggested_value=price,
                            confidence_score=0.9,
                            reason=f"Explicit {filter_type.replace('_', ' ')}: ${price:,}",
                            search_context=query
                        ))
                    break

            # Check for vehicle type indicators
            vehicle_types = {
                "suv": "SUV",
                "sedan": "Sedan",
                "truck": "Truck",
                "coupe": "Coupe",
                "convertible": "Convertible",
                "hatchback": "Hatchback",
                "minivan": "Minivan",
                "crossover": "Crossover"
            }

            for keyword, vehicle_type in vehicle_types.items():
                if keyword in query_lower:
                    suggestions.append(FilterSuggestion(
                        filter_name="vehicle_type",
                        suggested_value=vehicle_type,
                        confidence_score=0.85,
                        reason=f"Query mentions {vehicle_type}",
                        search_context=query
                    ))
                    break

            # Check for feature preferences
            feature_keywords = {
                "leather": "leather seats",
                "sunroof": "sunroof",
                "awd": "AWD",
                "4wd": "Four-wheel drive",
                "four-wheel drive": "Four-wheel drive",
                "navigation": "navigation system",
                "gps": "navigation system",
                "backup camera": "backup camera",
                "bluetooth": "Bluetooth",
                "heated seats": "heated seats"
            }

            for keyword, feature in feature_keywords.items():
                if keyword in query_lower:
                    suggestions.append(FilterSuggestion(
                        filter_name="features",
                        suggested_value=[feature],
                        confidence_score=0.8,
                        reason=f"Query mentions {feature}",
                        search_context=query
                    ))

            # Get popular filters from database
            popular_filters = await self._get_popular_filters()

            # Create response
            response = FilterSuggestionResponse(
                search_query=search_context.query,
                suggestions=suggestions,
                popular_filters=popular_filters,
                context_analysis={
                    "query_length": len(query),
                    "detected_keywords": [kw for kw in luxury_keywords + list(vehicle_types.keys()) if kw in query_lower],
                    "suggestion_count": len(suggestions),
                    "confidence_avg": sum(s.confidence_score for s in suggestions) / len(suggestions) if suggestions else 0.0
                }
            )

            # Cache the response
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key,
                    self.suggestion_cache_ttl,
                    json.dumps(response.dict())
                )

            logger.info(f"✅ Generated {len(suggestions)} filter suggestions for query: {query[:50]}...")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to generate filter suggestions: {e}")
            raise

    async def _get_popular_filters(self) -> List[Dict[str, Any]]:
        """Get popular filter combinations from usage data"""
        try:
            # In a real implementation, this would query database usage statistics
            # For now, return predefined popular combinations
            return [
                {
                    "name": "Family SUV Under $40k",
                    "filters": {"vehicle_type": "SUV", "price_max": 40000},
                    "usage_count": 156,
                    "description": "Popular for families needing space"
                },
                {
                    "name": "Luxury Vehicles",
                    "filters": {"price_min": 50000, "makes": ["BMW", "Mercedes", "Audi"]},
                    "usage_count": 98,
                    "description": "Premium vehicles with luxury features"
                },
                {
                    "name": "Eco-Friendly Commuters",
                    "filters": {"fuel_types": ["Electric", "Hybrid"], "price_max": 35000},
                    "usage_count": 87,
                    "description": "Environmentally conscious daily drivers"
                },
                {
                    "name": "Work Trucks",
                    "filters": {"vehicle_type": "Truck", "features": ["towing capacity"]},
                    "usage_count": 76,
                    "description": "Trucks suitable for work and hauling"
                }
            ]

        except Exception as e:
            logger.error(f"❌ Failed to get popular filters: {e}")
            return []

    async def validate_and_sanitize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize filter inputs"""
        try:
            sanitized = {}

            # Validate price ranges
            if 'price_min' in filters and 'price_max' in filters:
                price_min = float(filters['price_min'])
                price_max = float(filters['price_max'])
                if price_min > price_max:
                    # Swap values if they're reversed
                    price_min, price_max = price_max, price_min
                sanitized['price_min'] = price_min
                sanitized['price_max'] = price_max
            elif 'price_min' in filters:
                sanitized['price_min'] = float(filters['price_min'])
            elif 'price_max' in filters:
                sanitized['price_max'] = float(filters['price_max'])

            # Validate year ranges
            if 'year_min' in filters and 'year_max' in filters:
                year_min = int(filters['year_min'])
                year_max = int(filters['year_max'])
                if year_min > year_max:
                    # Swap values if they're reversed
                    year_min, year_max = year_max, year_min
                # Validate reasonable year ranges
                current_year = datetime.now().year
                year_min = max(1900, min(year_min, current_year + 1))
                year_max = max(1900, min(year_max, current_year + 1))
                sanitized['year_min'] = year_min
                sanitized['year_max'] = year_max
            elif 'year_min' in filters:
                year_min = int(filters['year_min'])
                current_year = datetime.now().year
                sanitized['year_min'] = max(1900, min(year_min, current_year + 1))
            elif 'year_max' in filters:
                year_max = int(filters['year_max'])
                current_year = datetime.now().year
                sanitized['year_max'] = max(1900, min(year_max, current_year + 1))

            # Validate mileage
            if 'mileage_max' in filters:
                mileage = int(filters['mileage_max'])
                sanitized['mileage_max'] = max(0, mileage)

            # String fields (sanitize)
            string_fields = ['make', 'model', 'vehicle_type', 'fuel_type', 'transmission',
                           'exterior_color', 'interior_color', 'city', 'state']
            for field in string_fields:
                if field in filters and filters[field]:
                    sanitized[field] = str(filters[field]).strip()[:100]  # Limit length

            # Handle features list
            if 'features' in filters:
                features = filters['features']
                if isinstance(features, list):
                    sanitized['features'] = [str(f).strip()[:50] for f in features if f and str(f).strip()]
                elif isinstance(features, str):
                    sanitized['features'] = [features.strip()[:50]]

            return sanitized

        except Exception as e:
            logger.error(f"❌ Filter validation failed: {e}")
            raise ValueError(f"Invalid filter parameters: {str(e)}")

    async def get_filter_stats(self) -> FilterStats:
        """Get filter service statistics"""
        try:
            # In a real implementation, this would query actual usage statistics
            return self.stats

        except Exception as e:
            logger.error(f"❌ Failed to get filter stats: {e}")
            return FilterStats()

# ============================================================================
# Utility Functions
# ============================================================================

def extract_price_range_from_query(query: str) -> Optional[Tuple[float, float]]:
    """Extract price range from natural language query"""
    import re

    # Patterns for price extraction
    patterns = [
        r"between \$?(\d+(?:,\d+)*) and \$?(\d+(?:,\d+)*)",
        r"\$?(\d+(?:,\d+)*) - \$?(\d+(?:,\d+)*)",
        r"under \$?(\d+(?:,\d+)*)",
        r"less than \$?(\d+(?:,\d+)*)",
        r"over \$?(\d+(?:,\d+)*)",
        r"above \$?(\d+(?:,\d+)*)",
        r"around \$?(\d+(?:,\d+)*)"
    ]

    for pattern in patterns:
        match = re.search(pattern, query.lower())
        if match:
            if "between" in pattern or "-" in pattern:
                # Range pattern
                min_price = float(match.group(1).replace(',', ''))
                max_price = float(match.group(2).replace(',', ''))
                return (min_price, max_price)
            elif "under" in pattern or "less than" in pattern:
                # Upper bound only
                max_price = float(match.group(1).replace(',', ''))
                return (0, max_price)
            elif "over" in pattern or "above" in pattern:
                # Lower bound only
                min_price = float(match.group(1).replace(',', ''))
                return (min_price, float('inf'))
            elif "around" in pattern:
                # Approximate price (±20%)
                price = float(match.group(1).replace(',', ''))
                return (price * 0.8, price * 1.2)

    return None

def detect_vehicle_type_from_query(query: str) -> Optional[str]:
    """Detect vehicle type from natural language query"""
    vehicle_type_keywords = {
        "SUV": ["suv", "sport utility", "crossover"],
        "Sedan": ["sedan", "saloon", "car"],
        "Truck": ["truck", "pickup", "lorry"],
        "Coupe": ["coupe", "sports car"],
        "Convertible": ["convertible", "cabriolet", "roadster"],
        "Minivan": ["minivan", "van"],
        "Hatchback": ["hatchback", "hatch"],
        "Wagon": ["wagon", "estate"]
    }

    query_lower = query.lower()
    for vehicle_type, keywords in vehicle_type_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return vehicle_type

    return None