"""
Analytics module for Otto.AI
Contains preference analytics, user behavior analysis, and insights
"""

from .favorites_analytics_service import (
    FavoritesAnalyticsService,
    FavoriteEvent,
    ConversionMetrics
)
from .preference_analytics import PreferenceAnalytics, TrendDirection, SeasonalPattern

__all__ = [
    'FavoritesAnalyticsService',
    'FavoriteEvent',
    'ConversionMetrics',
    'PreferenceAnalytics',
    'TrendDirection',
    'SeasonalPattern'
]