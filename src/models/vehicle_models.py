"""
Otto.AI Vehicle Data Models

Shared data models for vehicle specifications, features, and comparison results.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal


class ComparisonFeatureType(Enum):
    """Feature types for vehicle comparison"""
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    BODY_STYLE = "body_style"
    DRIVETRAIN = "drivetrain"
    FUEL_TYPE = "fuel_type"
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    SAFETY = "safety"
    TECHNOLOGY = "technology"
    PERFORMANCE = "performance"


class FeatureDifferenceType(Enum):
    """Types of feature differences"""
    EXCLUSIVE = "exclusive"  # Feature exists in one vehicle only
    SUPERIOR = "superior"     # Feature is better in one vehicle
    EQUIVALENT = "equivalent" # Features are equivalent
    MISSING = "missing"       # Feature expected but not found


@dataclass
class VehicleFeatures:
    """Vehicle features and specifications"""
    # Basic specifications
    year: int
    make: str
    model: str
    trim: Optional[str] = None

    # Vehicle details
    body_style: Optional[str] = None
    drivetrain: Optional[str] = None
    engine: Optional[str] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None

    # Pricing
    price: Optional[Decimal] = None
    msrp: Optional[Decimal] = None

    # Features lists
    exterior_features: List[str] = field(default_factory=list)
    interior_features: List[str] = field(default_factory=list)
    safety_features: List[str] = field(default_factory=list)
    technology_features: List[str] = field(default_factory=list)

    # Media
    images: List[str] = field(default_factory=list)
    description: Optional[str] = None

    # Metadata
    source_id: Optional[str] = None
    listing_url: Optional[str] = None
    listed_date: Optional[datetime] = None


@dataclass
class VehicleSpecification:
    """Detailed vehicle specification"""
    vehicle: VehicleFeatures
    specifications: Dict[str, Any] = field(default_factory=dict)
    condition_report: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "vehicle": self.vehicle.__dict__,
            "specifications": self.specifications,
            "condition_report": self.condition_report
        }


@dataclass
class FeatureDifference:
    """Difference between two vehicles for a specific feature"""
    feature_name: str
    feature_type: ComparisonFeatureType
    vehicle1_value: Any
    vehicle2_value: Any
    difference_type: FeatureDifferenceType
    importance_score: float = 1.0
    description: Optional[str] = None


@dataclass
class PriceAnalysis:
    """Price comparison and market analysis"""
    vehicle1_price: Optional[Decimal]
    vehicle2_price: Optional[Decimal]
    price_difference: Optional[Decimal]
    market_average: Optional[Decimal]
    value_score: float  # Value for money score 0-1
    price_trend: Optional[str] = None


@dataclass
class SemanticSimilarity:
    """Semantic similarity between vehicles based on features and description"""
    similarity_score: float  # 0-1
    feature_similarity: float
    description_similarity: float
    similar_features: List[str] = field(default_factory=list)
    different_features: List[str] = field(default_factory=list)


@dataclass
class VehicleComparisonResult:
    """Result of comparing two vehicles"""
    vehicle1: VehicleSpecification
    vehicle2: VehicleSpecification

    # Analysis results
    feature_differences: List[FeatureDifference]
    price_analysis: Optional[PriceAnalysis]
    semantic_similarity: Optional[SemanticSimilarity]

    # Summary scores
    overall_similarity_score: float  # 0-1
    vehicle1_better_features: int
    vehicle2_better_features: int
    tie_features: int

    # Metadata
    comparison_date: datetime = field(default_factory=datetime.now)
    comparison_version: str = "1.0"


@dataclass
class FilterCriteria:
    """Vehicle search filter criteria"""
    # Basic filters
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    makes: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)

    # Vehicle filters
    body_styles: List[str] = field(default_factory=list)
    drivetrains: List[str] = field(default_factory=list)
    fuel_types: List[str] = field(default_factory=list)

    # Price filters
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None

    # Feature filters (must-have)
    required_features: List[str] = field(default_factory=list)

    # Semantic search
    natural_language_query: Optional[str] = None
    similarity_threshold: float = 0.7

    # Pagination
    limit: int = 20
    offset: int = 0


@dataclass
class SearchRequest:
    """Vehicle search request"""
    filters: FilterCriteria
    user_context: Optional[Dict[str, Any]] = None
    search_id: Optional[str] = None


@dataclass
class SearchResponse:
    """Vehicle search response"""
    results: List[VehicleSpecification]
    total_count: int
    search_id: Optional[str] = None
    search_time_ms: Optional[int] = None
    semantic_query_used: bool = False
    pagination: Optional[Dict[str, Any]] = None