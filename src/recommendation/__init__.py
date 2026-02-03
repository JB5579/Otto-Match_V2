"""
Otto.AI Recommendation Package

Contains vehicle comparison and recommendation engines.
"""

from .comparison_engine import ComparisonEngine
from .recommendation_engine import RecommendationEngine
from .interaction_tracker import InteractionTracker
from .favorites_recommendation_engine import (
    FavoritesRecommendationEngine,
    VehicleSimilarityScore,
    RecommendationRequest,
    Recommendation
)

__all__ = [
    'ComparisonEngine',
    'RecommendationEngine',
    'InteractionTracker',
    'FavoritesRecommendationEngine',
    'VehicleSimilarityScore',
    'RecommendationRequest',
    'Recommendation'
]