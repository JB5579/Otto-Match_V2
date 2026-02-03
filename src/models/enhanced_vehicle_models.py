"""
Otto.AI Enhanced Vehicle Data Models with AI Intelligence

Extends the base vehicle models to include AI-powered intelligence
from Groq Compound AI for comprehensive vehicle analysis.
"""

import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, validator

# Import base models
from .vehicle_models import (
    VehicleFeatures,
    VehicleSpecification,
    FilterCriteria,
    SearchRequest,
    SearchResponse
)

# ============================================================================
# AI Intelligence Enums and Models
# ============================================================================

class AIModelType(str, Enum):
    """Groq AI model types used for intelligence generation"""
    COMPOUND = "groq/compound"
    COMPOUND_MINI = "groq/compound-mini"

class AIConfidenceLevel(str, Enum):
    """AI confidence levels for intelligence data"""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.6
    LOW = "low"        # >= 0.4
    VERY_LOW = "very_low"  # < 0.4

class MarketDemandLevel(str, Enum):
    """Vehicle market demand levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class AIProcessingStatus(str, Enum):
    """AI processing status for vehicles"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"

class InsightType(str, Enum):
    """Types of AI-generated market insights"""
    PRICING = "pricing"
    DEMAND = "demand"
    FEATURE_COMPARISON = "feature_comparison"
    MARKET_TREND = "market_trend"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    AVAILABILITY = "availability"
    VALUE_ASSESSMENT = "value_assessment"
    ERROR = "error"

@dataclass
class AISource:
    """AI source attribution for intelligence data"""
    source_name: str
    source_url: Optional[str] = None
    source_type: str = "web_search"
    retrieval_date: datetime = field(default_factory=datetime.now)
    reliability_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "retrieval_date": self.retrieval_date.isoformat(),
            "reliability_score": self.reliability_score
        }

class AISourceModel(BaseModel):
    """Pydantic model for AI source"""
    source_name: str
    source_url: Optional[str] = None
    source_type: str = "web_search"
    retrieval_date: datetime
    reliability_score: float = Field(ge=0.0, le=1.0)

@dataclass
class MarketInsight:
    """AI-generated market insight"""
    insight_type: InsightType
    title: str
    description: str
    confidence: float  # 0-1
    sources: List[AISource]
    data_points: Dict[str, Any]
    relevance_score: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)

    def get_confidence_level(self) -> AIConfidenceLevel:
        """Get confidence level category"""
        if self.confidence >= 0.8:
            return AIConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            return AIConfidenceLevel.MEDIUM
        elif self.confidence >= 0.4:
            return AIConfidenceLevel.LOW
        else:
            return AIConfidenceLevel.VERY_LOW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_type": self.insight_type.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "confidence_level": self.get_confidence_level().value,
            "sources": [source.to_dict() for source in self.sources],
            "data_points": self.data_points,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat()
        }

class MarketInsightModel(BaseModel):
    """Pydantic model for market insight"""
    insight_type: InsightType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[AISourceModel] = Field(default_factory=list)
    data_points: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('confidence')
    def validate_confidence_level(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

    @property
    def confidence_level(self) -> AIConfidenceLevel:
        """Get confidence level category"""
        if self.confidence >= 0.8:
            return AIConfidenceLevel.HIGH
        elif self.confidence >= 0.6:
            return AIConfidenceLevel.MEDIUM
        elif self.confidence >= 0.4:
            return AIConfidenceLevel.LOW
        else:
            return AIConfidenceLevel.VERY_LOW

# ============================================================================
# Enhanced Vehicle Models with AI Intelligence
# ============================================================================

@dataclass
class VehicleIntelligence:
    """Complete AI intelligence for a vehicle"""
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: Optional[str] = None

    # Market Analysis
    market_price_range: Optional[Tuple[Decimal, Decimal]] = None
    market_average_price: Optional[Decimal] = None
    price_confidence: float = 0.0

    # Demand & Availability
    market_demand: MarketDemandLevel = MarketDemandLevel.UNKNOWN
    availability_score: float = 0.0  # 0-1, higher = more available
    days_on_market_avg: Optional[int] = None

    # Feature Intelligence
    feature_popularity: Dict[str, float] = field(default_factory=dict)
    competitive_advantages: List[str] = field(default_factory=list)
    common_complaints: List[str] = field(default_factory=list)

    # Market Insights
    insights: List[MarketInsight] = field(default_factory=list)

    # AI Metadata
    ai_model_used: AIModelType = AIModelType.COMPOUND_MINI
    generated_at: datetime = field(default_factory=datetime.now)
    cache_expires_at: Optional[datetime] = None
    confidence_overall: float = 0.0

    # Processing metadata
    processing_time_ms: Optional[int] = None
    sources_count: int = 0
    error_message: Optional[str] = None

    def get_price_range_display(self) -> Optional[str]:
        """Get human-readable price range"""
        if not self.market_price_range:
            return None
        min_price, max_price = self.market_price_range
        return f"${min_price:,.0f} - ${max_price:,.0f}"

    def get_overall_confidence_level(self) -> AIConfidenceLevel:
        """Get overall confidence level category"""
        if self.confidence_overall >= 0.8:
            return AIConfidenceLevel.HIGH
        elif self.confidence_overall >= 0.6:
            return AIConfidenceLevel.MEDIUM
        elif self.confidence_overall >= 0.4:
            return AIConfidenceLevel.LOW
        else:
            return AIConfidenceLevel.VERY_LOW

    def is_intelligent(self) -> bool:
        """Check if vehicle has meaningful intelligence"""
        return (
            self.confidence_overall > 0.3 and
            (self.market_average_price is not None or
             len(self.insights) > 0 or
             len(self.competitive_advantages) > 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "vehicle_id": self.vehicle_id,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "vin": self.vin,

            # Market Analysis
            "market_price_range": {
                "min": float(self.market_price_range[0]) if self.market_price_range and self.market_price_range[0] else None,
                "max": float(self.market_price_range[1]) if self.market_price_range and self.market_price_range[1] else None,
                "display": self.get_price_range_display()
            } if self.market_price_range else None,
            "market_average_price": float(self.market_average_price) if self.market_average_price else None,
            "price_confidence": self.price_confidence,

            # Demand & Availability
            "market_demand": self.market_demand.value,
            "availability_score": self.availability_score,
            "days_on_market_avg": self.days_on_market_avg,

            # Feature Intelligence
            "feature_popularity": self.feature_popularity,
            "competitive_advantages": self.competitive_advantages,
            "common_complaints": self.common_complaints,

            # Market Insights
            "insights": [insight.to_dict() for insight in self.insights],

            # AI Metadata
            "ai_model_used": self.ai_model_used.value,
            "generated_at": self.generated_at.isoformat(),
            "cache_expires_at": self.cache_expires_at.isoformat() if self.cache_expires_at else None,
            "confidence_overall": self.confidence_overall,
            "confidence_level": self.get_overall_confidence_level().value,

            # Processing metadata
            "processing_time_ms": self.processing_time_ms,
            "sources_count": self.sources_count,
            "error_message": self.error_message,
            "is_intelligent": self.is_intelligent()
        }

class VehicleIntelligenceModel(BaseModel):
    """Pydantic model for vehicle intelligence"""
    vehicle_id: str = Field(..., min_length=1)
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2030)
    vin: Optional[str] = Field(None, regex=r"^[A-HJ-NPR-Z0-9]{17}$")

    # Market Analysis
    market_price_min: Optional[Decimal] = Field(None, ge=0)
    market_price_max: Optional[Decimal] = Field(None, ge=0)
    market_average_price: Optional[Decimal] = Field(None, ge=0)
    price_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Demand & Availability
    market_demand: MarketDemandLevel = Field(default=MarketDemandLevel.UNKNOWN)
    availability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    days_on_market_avg: Optional[int] = Field(None, ge=0)

    # Feature Intelligence
    feature_popularity: Dict[str, float] = Field(default_factory=dict)
    competitive_advantages: List[str] = Field(default_factory=list)
    common_complaints: List[str] = Field(default_factory=list)

    # Market Insights
    insights: List[MarketInsightModel] = Field(default_factory=list)

    # AI Metadata
    ai_model_used: AIModelType = Field(default=AIModelType.COMPOUND_MINI)
    generated_at: datetime = Field(default_factory=datetime.now)
    cache_expires_at: Optional[datetime] = None
    confidence_overall: float = Field(default=0.0, ge=0.0, le=1.0)

    # Processing metadata
    processing_time_ms: Optional[int] = Field(None, ge=0)
    sources_count: int = Field(default=0, ge=0)
    error_message: Optional[str] = None

    @property
    def market_price_range(self) -> Optional[Tuple[Decimal, Decimal]]:
        """Get price range as tuple"""
        if self.market_price_min is not None and self.market_price_max is not None:
            return (self.market_price_min, self.market_price_max)
        return None

    @property
    def price_range_display(self) -> Optional[str]:
        """Get human-readable price range"""
        if not self.market_price_range:
            return None
        min_price, max_price = self.market_price_range
        return f"${min_price:,.0f} - ${max_price:,.0f}"

    @property
    def confidence_level(self) -> AIConfidenceLevel:
        """Get confidence level category"""
        if self.confidence_overall >= 0.8:
            return AIConfidenceLevel.HIGH
        elif self.confidence_overall >= 0.6:
            return AIConfidenceLevel.MEDIUM
        elif self.confidence_overall >= 0.4:
            return AIConfidenceLevel.LOW
        else:
            return AIConfidenceLevel.VERY_LOW

    @property
    def is_intelligent(self) -> bool:
        """Check if vehicle has meaningful intelligence"""
        return (
            self.confidence_overall > 0.3 and
            (self.market_average_price is not None or
             len(self.insights) > 0 or
             len(self.competitive_advantages) > 0)
        )

@dataclass
class EnhancedVehicleFeatures(VehicleFeatures):
    """Extended vehicle features with AI intelligence"""
    # Base features inherited from VehicleFeatures

    # AI Intelligence fields
    ai_intelligence: Optional[VehicleIntelligence] = None
    ai_processing_status: AIProcessingStatus = AIProcessingStatus.PENDING
    ai_last_processed: Optional[datetime] = None
    ai_processing_error: Optional[str] = None

    # Computed fields
    price_vs_market_average: Optional[float] = None  # Price as percentage of market average
    ai_confidence_level: AIConfidenceLevel = AIConfidenceLevel.VERY_LOW

    def has_ai_intelligence(self) -> bool:
        """Check if vehicle has AI intelligence"""
        return (
            self.ai_intelligence is not None and
            self.ai_intelligence.is_intelligent()
        )

    def calculate_price_vs_market(self) -> Optional[float]:
        """Calculate price as percentage of market average"""
        if (self.price is None or
            self.ai_intelligence is None or
            self.ai_intelligence.market_average_price is None or
            self.ai_intelligence.market_average_price <= 0):
            return None

        return float(self.price / self.ai_intelligence.market_average_price)

    def update_computed_fields(self):
        """Update computed fields based on AI intelligence"""
        self.price_vs_market_average = self.calculate_price_vs_market()

        if self.ai_intelligence:
            self.ai_confidence_level = self.ai_intelligence.get_overall_confidence_level()

class EnhancedVehicleSpecification(VehicleSpecification):
    """Enhanced vehicle specification with AI intelligence"""
    vehicle: EnhancedVehicleFeatures
    ai_intelligence: Optional[VehicleIntelligence] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        base_dict = super().to_dict()
        if self.ai_intelligence:
            base_dict["ai_intelligence"] = self.ai_intelligence.to_dict()
        return base_dict

# ============================================================================
# Enhanced Search Models
# ============================================================================

@dataclass
class AIFilterCriteria(FilterCriteria):
    """Extended filter criteria with AI intelligence options"""
    # AI-specific filters
    min_ai_confidence: float = 0.0
    max_ai_confidence: float = 1.0
    market_demand: Optional[MarketDemandLevel] = None
    has_ai_intelligence: bool = False
    max_price_vs_market: Optional[float] = None
    has_competitive_advantages: bool = False
    exclude_common_complaints: bool = False
    min_availability_score: float = 0.0
    ai_model_used: Optional[AIModelType] = None

@dataclass
class EnhancedSearchRequest(SearchRequest):
    """Enhanced search request with AI options"""
    filters: Optional[AIFilterCriteria] = None
    include_ai_intelligence: bool = True
    ai_priority_sorting: bool = False
    ai_confidence_weight: float = 0.3  # Weight for AI confidence in ranking

@dataclass
class EnhancedSearchResponse(SearchResponse):
    """Enhanced search response with AI intelligence"""
    ai_processing_metadata: Dict[str, Any] = field(default_factory=dict)
    ai_filters_applied: Optional[Dict[str, Any]] = None
    ai_stats: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# AI Intelligence Request/Response Models
# ============================================================================

class AIIntelligenceRequest(BaseModel):
    """Request model for AI intelligence generation"""
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2030)
    vin: Optional[str] = Field(None, regex=r"^[A-HJ-NPR-Z0-9]{17}$")
    features: List[str] = Field(default_factory=list)
    current_price: Optional[Decimal] = Field(None, ge=0)
    force_refresh: bool = Field(default=False)
    model_type: AIModelType = Field(default=AIModelType.COMPOUND_MINI)

class AIIntelligenceResponse(BaseModel):
    """Response model for AI intelligence generation"""
    success: bool
    intelligence: Optional[VehicleIntelligenceModel] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    cached: bool = False

class BatchAIIntelligenceRequest(BaseModel):
    """Request model for batch AI intelligence generation"""
    vehicles: List[AIIntelligenceRequest] = Field(..., min_items=1, max_items=50)
    force_refresh: bool = Field(default=False)
    concurrency_limit: int = Field(default=3, ge=1, le=10)

class BatchAIIntelligenceResponse(BaseModel):
    """Response model for batch AI intelligence generation"""
    success: bool
    results: List[AIIntelligenceResponse] = Field(...)
    total_processing_time_ms: Optional[int] = None
    successful_count: int
    failed_count: int
    cached_count: int

# ============================================================================
# Utility Functions
# ============================================================================

def create_vehicle_intelligence_from_dict(data: Dict[str, Any]) -> VehicleIntelligence:
    """Create VehicleIntelligence from dictionary data"""
    # Convert price range
    price_range = None
    if data.get("market_price_range"):
        price_data = data["market_price_range"]
        if isinstance(price_data, dict):
            min_price = price_data.get("min")
            max_price = price_data.get("max")
            if min_price is not None and max_price is not None:
                price_range = (Decimal(str(min_price)), Decimal(str(max_price)))

    # Convert insights
    insights = []
    for insight_data in data.get("insights", []):
        sources = []
        for source_data in insight_data.get("sources", []):
            sources.append(AISource(
                source_name=source_data["source_name"],
                source_url=source_data.get("source_url"),
                source_type=source_data["source_type"],
                retrieval_date=datetime.fromisoformat(source_data["retrieval_date"]),
                reliability_score=source_data["reliability_score"]
            ))

        insights.append(MarketInsight(
            insight_type=InsightType(insight_data["insight_type"]),
            title=insight_data["title"],
            description=insight_data["description"],
            confidence=insight_data["confidence"],
            sources=sources,
            data_points=insight_data["data_points"],
            relevance_score=insight_data.get("relevance_score", 1.0),
            created_at=datetime.fromisoformat(insight_data["created_at"])
        ))

    return VehicleIntelligence(
        vehicle_id=data["vehicle_id"],
        make=data["make"],
        model=data["model"],
        year=data["year"],
        vin=data.get("vin"),
        market_price_range=price_range,
        market_average_price=Decimal(str(data["market_average_price"])) if data.get("market_average_price") else None,
        price_confidence=data.get("price_confidence", 0.0),
        market_demand=MarketDemandLevel(data.get("market_demand", "unknown")),
        availability_score=data.get("availability_score", 0.0),
        days_on_market_avg=data.get("days_on_market_avg"),
        feature_popularity=data.get("feature_popularity", {}),
        competitive_advantages=data.get("competitive_advantages", []),
        common_complaints=data.get("common_complaints", []),
        insights=insights,
        ai_model_used=AIModelType(data.get("ai_model_used", "groq/compound-mini")),
        generated_at=datetime.fromisoformat(data["generated_at"]),
        cache_expires_at=datetime.fromisoformat(data["cache_expires_at"]) if data.get("cache_expires_at") else None,
        confidence_overall=data.get("confidence_overall", 0.0),
        processing_time_ms=data.get("processing_time_ms"),
        sources_count=data.get("sources_count", 0),
        error_message=data.get("error_message")
    )