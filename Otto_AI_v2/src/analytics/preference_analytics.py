"""
Preference Analytics Service for Otto.AI
Tracks and analyzes preference evolution patterns
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.services.profile_service import ProfileService, PreferenceChange
from src.memory.temporal_memory import TemporalMemoryManager
from src.conversation.nlu_service import UserPreference

# Configure logging
logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Direction of preference trend"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    UNKNOWN = "unknown"


class SeasonalPattern(Enum):
    """Seasonal patterns in preferences"""
    NONE = "none"
    SUMMER = "summer"          # e.g., convertibles more popular
    WINTER = "winter"          # e.g., AWD vehicles more popular
    SPRING = "spring"          # e.g., family vehicles for summer planning
    FALL = "fall"            # e.g., year-end purchases


@dataclass
class PreferenceTrend:
    """Analytics for preference trend"""
    category: str
    direction: TrendDirection
    confidence: float
    strength: float  # Rate of change
    duration: int  # Days trend has been active
    data_points: int  # Number of data points analyzed
    seasonal_pattern: SeasonalPattern
    predictions: List[Dict[str, Any]]


@dataclass
class SegmentInsight:
    """Insight about user segment"""
    segment_name: str
    size: int  # Number of users in segment
    defining_preferences: List[str]
    common_journey: List[str]
    conversion_rate: float
    avg_session_count: float


class PreferenceAnalytics:
    """Analytics service for preference evolution tracking"""

    def __init__(
        self,
        profile_service: ProfileService,
        temporal_memory: TemporalMemoryManager,
        analysis_window: int = 90  # days
    ):
        self.profile_service = profile_service
        self.temporal_memory = temporal_memory
        self.analysis_window = analysis_window
        self.initialized = False

        # Cache for computed analytics
        self.trend_cache: Dict[str, Dict[str, PreferenceTrend]] = {}
        self.cache_ttl = timedelta(hours=1)

    async def initialize(self) -> bool:
        """Initialize the analytics service"""
        try:
            if not self.profile_service.initialized:
                logger.error("Profile service not initialized")
                return False

            if not self.temporal_memory.initialized:
                logger.error("Temporal memory manager not initialized")
                return False

            self.initialized = True
            logger.info("Preference analytics initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize preference analytics: {e}")
            return False

    async def analyze_preference_trends(
        self,
        user_id: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, PreferenceTrend]:
        """Analyze trends in user's preferences"""
        if not self.initialized:
            return {}

        try:
            # Check cache first
            cache_key = f"{user_id}:{hash(tuple(categories) if categories else ())}"
            if cache_key in self.trend_cache:
                cached_time = self.trend_cache[cache_key].get("_timestamp")
                if cached_time and datetime.now() - cached_time < self.cache_ttl:
                    return self.trend_cache[cache_key]

            # Get preference history
            timeline = await self.profile_service.create_preference_timeline(
                user_id, self.analysis_window
            )

            # Group by category
            by_category = {}
            for change in timeline:
                category = change["category"]
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(change)

            # Analyze each category
            trends = {}
            for category, changes in by_category.items():
                if categories and category not in categories:
                    continue

                if len(changes) < 3:  # Need at least 3 data points
                    trends[category] = PreferenceTrend(
                        category=category,
                        direction=TrendDirection.UNKNOWN,
                        confidence=0.0,
                        strength=0.0,
                        duration=0,
                        data_points=len(changes),
                        seasonal_pattern=SeasonalPattern.NONE,
                        predictions=[]
                    )
                    continue

                # Calculate trend
                trend = self._calculate_trend(category, changes)
                trends[category] = trend

            # Cache results
            trends["_timestamp"] = datetime.now()
            self.trend_cache[cache_key] = trends

            return trends

        except Exception as e:
            logger.error(f"Failed to analyze preference trends: {e}")
            return {}

    async def identify_preference_segments(
        self,
        min_segment_size: int = 10
    ) -> List[SegmentInsight]:
        """Identify user segments based on preference patterns"""
        if not self.initialized:
            return []

        try:
            # Get all user profiles
            # In production, this would query from database
            all_profiles = list(self.profile_service.profiles.values())

            # Extract preference patterns
            preference_patterns = []
            for profile in all_profiles:
                pattern = self._extract_preference_pattern(profile)
                preference_patterns.append(pattern)

            # Cluster similar patterns
            segments = self._cluster_preferences(preference_patterns, min_segment_size)

            # Generate insights for each segment
            insights = []
            for segment_id, users in segments.items():
                if len(users) < min_segment_size:
                    continue

                insight = await self._generate_segment_insight(segment_id, users)
                insights.append(insight)

            # Sort by segment size
            insights.sort(key=lambda x: x.size, reverse=True)

            return insights

        except Exception as e:
            logger.error(f"Failed to identify preference segments: {e}")
            return []

    async def predict_preference_evolution(
        self,
        user_id: str,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Predict how user preferences might evolve"""
        if not self.initialized:
            return {}

        try:
            # Get current preferences
            evolved_prefs = await self.temporal_memory.get_evolved_preferences(user_id)

            # Get trends
            trends = await self.analyze_preference_trends(user_id)

            # Get similar users' evolution paths
            similar_users = await self._find_similar_users(user_id, evolved_prefs)

            predictions = {}
            for category, pref in evolved_prefs.items():
                trend = trends.get(category.value)
                if not trend:
                    continue

                # Base prediction on trend
                if trend.direction == TrendDirection.INCREASING:
                    predicted_strength = min(1.0, pref.weight + (trend.strength * days_ahead / 30))
                elif trend.direction == TrendDirection.DECREASING:
                    predicted_strength = max(0.0, pref.weight - (trend.strength * days_ahead / 30))
                else:
                    predicted_strength = pref.weight

                # Adjust based on similar users
                if similar_users:
                    adjustment = await self._calculate_similar_user_adjustment(
                        category, pref, similar_users, days_ahead
                    )
                    predicted_strength += adjustment

                predictions[category.value] = {
                    "current_value": pref.value,
                    "current_strength": round(pref.weight, 3),
                    "predicted_strength": round(max(0.0, min(1.0, predicted_strength)), 3),
                    "confidence": trend.confidence,
                    "trend_direction": trend.direction.value,
                    "seasonal_factor": self._get_seasonal_factor(category.value, days_ahead)
                }

            return {
                "user_id": user_id,
                "prediction_date": (datetime.now() + timedelta(days=days_ahead)).isoformat(),
                "predictions": predictions,
                "confidence": self._calculate_overall_confidence(trends)
            }

        except Exception as e:
            logger.error(f"Failed to predict preference evolution: {e}")
            return {}

    async def track_learning_effectiveness(
        self,
        user_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Track how well Otto is learning user preferences"""
        if not self.initialized:
            return {}

        try:
            # Get preference changes
            timeline = await self.profile_service.create_preference_timeline(user_id, days_back)

            # Calculate metrics
            total_changes = len(timeline)
            corrections = len([c for c in timeline if c.get("source") == "user_correction"])

            # Calculate accuracy
            if total_changes > 0:
                correction_rate = corrections / total_changes
                learning_accuracy = max(0.0, 1.0 - correction_rate)
            else:
                learning_accuracy = 0.0

            # Get preference confidence trends
            trends = await self.analyze_preference_trends(user_id)
            avg_confidence = np.mean([
                t.confidence for t in trends.values()
                if hasattr(t, 'confidence')
            ]) if trends else 0.0

            # Calculate response adaptation
            adaptation_score = await self._calculate_adaptation_score(user_id, timeline)

            return {
                "user_id": user_id,
                "period_days": days_back,
                "learning_metrics": {
                    "total_preference_changes": total_changes,
                    "user_corrections": corrections,
                    "learning_accuracy": round(learning_accuracy, 3),
                    "average_confidence": round(avg_confidence, 3),
                    "adaptation_score": round(adaptation_score, 3)
                },
                "recommendations": self._generate_learning_recommendations(
                    learning_accuracy, adaptation_score, trends
                )
            }

        except Exception as e:
            logger.error(f"Failed to track learning effectiveness: {e}")
            return {}

    def _calculate_trend(
        self,
        category: str,
        changes: List[Dict[str, Any]]
    ) -> PreferenceTrend:
        """Calculate trend for a preference category"""
        # Extract confidence values over time
        values = []
        timestamps = []

        for change in changes:
            values.append(change["confidence"]["new"])
            timestamps.append(datetime.fromisoformat(change["date"]))

        # Calculate linear regression
        if len(values) < 2:
            return PreferenceTrend(
                category=category,
                direction=TrendDirection.UNKNOWN,
                confidence=0.0,
                strength=0.0,
                duration=0,
                data_points=len(values),
                seasonal_pattern=SeasonalPattern.NONE,
                predictions=[]
            )

        # Simple trend calculation
        x = np.arange(len(values))
        y = np.array(values)

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        # Determine direction
        if slope > 0.05:
            direction = TrendDirection.INCREASING
        elif slope < -0.05:
            direction = TrendDirection.DECREASING
        else:
            direction = TrendDirection.STABLE

        # Check for fluctuation
        if self._is_fluctuating(values):
            direction = TrendDirection.FLUCTUATING

        # Calculate confidence in trend
        trend_variance = np.var(y)
        confidence = max(0.0, min(1.0, 1.0 - trend_variance))

        # Calculate duration
        duration = (timestamps[-1] - timestamps[0]).days if timestamps else 0

        # Detect seasonal pattern
        seasonal_pattern = self._detect_seasonal_pattern(category, timestamps, values)

        # Generate simple predictions
        predictions = self._generate_trend_predictions(slope, values, confidence)

        return PreferenceTrend(
            category=category,
            direction=direction,
            confidence=round(confidence, 3),
            strength=round(abs(slope), 3),
            duration=duration,
            data_points=len(values),
            seasonal_pattern=seasonal_pattern,
            predictions=predictions
        )

    def _is_fluctuating(self, values: List[float], threshold: float = 0.2) -> bool:
        """Check if values are fluctuating"""
        if len(values) < 4:
            return False

        # Calculate standard deviation
        std_dev = np.std(values)
        return std_dev > threshold

    def _detect_seasonal_pattern(
        self,
        category: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> SeasonalPattern:
        """Detect seasonal pattern in preference"""
        if len(timestamps) < 12:  # Need at least a year of data
            return SeasonalPattern.NONE

        # Group by month
        monthly_avg = {}
        for ts, val in zip(timestamps, values):
            month = ts.month
            if month not in monthly_avg:
                monthly_avg[month] = []
            monthly_avg[month].append(val)

        # Calculate monthly averages
        for month in monthly_avg:
            monthly_avg[month] = np.mean(monthly_avg[month])

        # Simple seasonal detection based on category
        if category in ["convertible", "sports_car"]:
            # Higher in summer
            summer_avg = np.mean([monthly_avg.get(m, 0) for m in [6, 7, 8]])
            winter_avg = np.mean([monthly_avg.get(m, 0) for m in [12, 1, 2]])
            if summer_avg > winter_avg * 1.2:
                return SeasonalPattern.SUMMER

        elif category in ["awd", "4wd", "heated_seats"]:
            # Higher in winter
            winter_avg = np.mean([monthly_avg.get(m, 0) for m in [12, 1, 2]])
            summer_avg = np.mean([monthly_avg.get(m, 0) for m in [6, 7, 8]])
            if winter_avg > summer_avg * 1.2:
                return SeasonalPattern.WINTER

        return SeasonalPattern.NONE

    def _generate_trend_predictions(
        self,
        slope: float,
        values: List[float],
        confidence: float
    ) -> List[Dict[str, Any]]:
        """Generate simple trend predictions"""
        predictions = []
        last_value = values[-1] if values else 0

        # Predict next 5 points
        for i in range(1, 6):
            predicted = last_value + (slope * i)
            predictions.append({
                "step": i,
                "predicted_value": round(max(0.0, min(1.0, predicted)), 3),
                "confidence": round(confidence * (1 - i * 0.1), 3)  # Decreasing confidence
            })

        return predictions

    def _extract_preference_pattern(self, profile) -> Dict[str, Any]:
        """Extract key preference pattern from profile"""
        pattern = {
            "user_id": profile.user_id,
            "preferences": {}
        }

        # Extract high-confidence preferences
        for key, value in profile.preferences.items():
            if key.startswith("pref_"):
                category = key[5:]
                if value.get("confidence", 0) > 0.7:
                    pattern["preferences"][category] = value.get("value")

        return pattern

    def _cluster_preferences(
        self,
        patterns: List[Dict[str, Any]],
        min_size: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Simple clustering of preference patterns"""
        segments = {}
        segment_id = 0

        # This is a very simplified clustering
        # In production, use proper clustering algorithms
        for pattern in patterns:
            # Simple heuristic-based segmentation
            segment_key = self._get_segment_key(pattern)

            if segment_key not in segments:
                segments[segment_key] = []
            segments[segment_key].append(pattern)

        # Filter by minimum size
        return {
            k: v for k, v in segments.items()
            if len(v) >= min_size
        }

    def _get_segment_key(self, pattern: Dict[str, Any]) -> str:
        """Generate segment key based on preference pattern"""
        prefs = pattern.get("preferences", {})

        # Simple segmentation logic
        if "budget" in prefs and prefs["budget"] < 30000:
            if "family_size" in prefs and prefs["family_size"] > 2:
                return "budget_family"
            elif "vehicle_type" in prefs and prefs["vehicle_type"] == "EV":
                return "budget_ev"
            else:
                return "budget_basic"
        elif "vehicle_type" in prefs and prefs["vehicle_type"] == "Luxury":
            return "luxury_buyer"
        elif "family_size" in prefs and prefs["family_size"] > 2:
            return "family_oriented"
        else:
            return "general"

    async def _generate_segment_insight(
        self,
        segment_id: str,
        users: List[Dict[str, Any]]
    ) -> SegmentInsight:
        """Generate insights for a user segment"""
        # Calculate defining preferences
        all_prefs = {}
        for user in users:
            for category, value in user.get("preferences", {}).items():
                if category not in all_prefs:
                    all_prefs[category] = {}
                if value not in all_prefs[category]:
                    all_prefs[category][value] = 0
                all_prefs[category][value] += 1

        # Get most common preferences
        defining_prefs = []
        for category, values in all_prefs.items():
            most_common = max(values.items(), key=lambda x: x[1])
            if most_common[1] > len(users) * 0.5:  # Appears in >50% of segment
                defining_prefs.append(f"{category}: {most_common[0]}")

        # Mock other metrics (would be calculated from real data)
        return SegmentInsight(
            segment_name=segment_id,
            size=len(users),
            defining_preferences=defining_prefs,
            common_journey=["browse", "compare", "save", "inquire"],
            conversion_rate=0.15,
            avg_session_count=3.2
        )

    async def _find_similar_users(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> List[str]:
        """Find users with similar preferences"""
        # Simple similarity based on matching categories
        similar_users = []

        for other_user_id, profile in self.profile_service.profiles.items():
            if other_user_id == user_id:
                continue

            # Calculate similarity score
            score = 0
            total = 0

            for category, pref in preferences.items():
                total += 1
                pref_key = f"pref_{category.value}"
                if pref_key in profile.preferences:
                    other_value = profile.preferences[pref_key].get("value")
                    if other_value == pref.value:
                        score += 1

            if total > 0 and score / total > 0.7:  # 70% similarity
                similar_users.append(other_user_id)

        return similar_users[:10]  # Limit to 10 similar users

    async def _calculate_similar_user_adjustment(
        self,
        category,
        current_pref,
        similar_users: List[str],
        days_ahead: int
    ) -> float:
        """Calculate adjustment based on similar users' evolution"""
        total_adjustment = 0
        count = 0

        for user_id in similar_users:
            # Get their evolution
            timeline = await self.profile_service.create_preference_timeline(user_id, 60)

            # Find changes in same category
            category_changes = [
                c for c in timeline
                if c["category"] == category
            ]

            if len(category_changes) >= 2:
                # Calculate average change
                first_conf = category_changes[0]["confidence"]["new"]
                last_conf = category_changes[-1]["confidence"]["new"]
                change = last_conf - first_conf
                total_adjustment += change * 0.1  # Weight adjustment
                count += 1

        return total_adjustment / count if count > 0 else 0

    def _get_seasonal_factor(
        self,
        category: str,
        days_ahead: int
    ) -> float:
        """Get seasonal adjustment factor"""
        # Simple seasonal factor calculation
        future_date = datetime.now() + timedelta(days=days_ahead)
        month = future_date.month

        # Summer months (June-August)
        if month in [6, 7, 8]:
            if category in ["convertible", "sports", "performance"]:
                return 0.1
            elif category in ["awd", "heated_seats"]:
                return -0.1

        # Winter months (December-February)
        elif month in [12, 1, 2]:
            if category in ["awd", "heated_seats", "safety"]:
                return 0.1
            elif category in ["convertible", "sports"]:
                return -0.1

        return 0.0

    def _calculate_overall_confidence(self, trends: Dict[str, PreferenceTrend]) -> float:
        """Calculate overall confidence in predictions"""
        if not trends:
            return 0.0

        confidences = [
            t.confidence for t in trends.values()
            if hasattr(t, 'confidence')
        ]

        return np.mean(confidences) if confidences else 0.0

    async def _calculate_adaptation_score(
        self,
        user_id: str,
        timeline: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well Otto adapts to user preferences"""
        # This would measure response accuracy over time
        # For now, return a mock value
        return 0.75

    def _generate_learning_recommendations(
        self,
        accuracy: float,
        adaptation: float,
        trends: Dict[str, PreferenceTrend]
    ) -> List[str]:
        """Generate recommendations for improving learning"""
        recommendations = []

        if accuracy < 0.7:
            recommendations.append(
                "Increase preference validation by asking users to confirm key preferences"
            )

        if adaptation < 0.7:
            recommendations.append(
                "Improve response adaptation by giving more weight to recent user feedback"
            )

        # Check for fluctuating trends
        fluctuating = [
            cat for cat, trend in trends.items()
            if trend.direction == TrendDirection.FLUCTUATING
        ]

        if fluctuating:
            recommendations.append(
                f"Review preferences in fluctuating categories: {', '.join(fluctuating[:3])}"
            )

        if not recommendations:
            recommendations.append("Learning is performing well - continue current approach")

        return recommendations