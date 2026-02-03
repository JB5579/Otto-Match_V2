"""
Otto.AI Collections Trending Algorithm

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Algorithm for identifying and ranking trending collections

Features:
- Engagement-based trending calculation
- Market trend detection from external sources
- Multi-factor scoring with weighted importance
- Trend decay mechanism for stale collections
- Automatic trending collection generation
"""

import os
import asyncio
import logging
import psycopg
from psycopg.rows import dict_row
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import uuid
import numpy as np
import requests
from enum import Enum

logger = logging.getLogger(__name__)

class TrendFactor(Enum):
    """Trending calculation factors"""
    VIEWS = "views"
    CLICKS = "clicks"
    SHARES = "shares"
    CONVERSIONS = "conversions"
    GROWTH_RATE = "growth_rate"
    RECENCY = "recency"

@dataclass
class TrendMetrics:
    """Trending metrics for a collection"""
    collection_id: str
    views: int = 0
    clicks: int = 0
    shares: int = 0
    conversions: int = 0
    engagement_score: float = 0.0
    growth_rate: float = 0.0
    recency_score: float = 0.0
    trending_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MarketTrendData:
    """Market trend data from external sources"""
    trend_name: str
    trend_score: float
    keywords: List[str]
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class TrendingAlgorithm:
    """
    Algorithm for calculating collection trends
    """

    def __init__(self):
        """Initialize trending algorithm"""
        self.db_conn = None
        self.trending_weights = {
            TrendFactor.VIEWS: 0.2,
            TrendFactor.CLICKS: 0.3,
            TrendFactor.SHARES: 0.2,
            TrendFactor.CONVERSIONS: 0.25,
            TrendFactor.GROWTH_RATE: 0.15,
            TrendFactor.RECENCY: 0.1
        }
        self.trend_decay_days = 30
        self.market_trend_sources = [
            "https://api.edmunds.com/api/trending",
            "https://api.kbb.com/market-trends",
            "https://api.nhtsa.gov/recalls-trends"
        ]

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous key

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to Supabase
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)

            logger.info("TrendingAlgorithm initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize TrendingAlgorithm: {e}")
            return False

    async def calculate_collection_trends(
        self,
        collection_id: str,
        days_back: int = 7
    ) -> Optional[TrendMetrics]:
        """
        Calculate trending metrics for a collection

        Args:
            collection_id: Collection ID
            days_back: Number of days to analyze

        Returns:
            TrendMetrics object or None if calculation fails
        """
        try:
            # Get analytics data for the period
            start_date = datetime.utcnow() - timedelta(days=days_back)
            end_date = datetime.utcnow()

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get engagement metrics
                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN event_type = 'view' THEN 1 END) as views,
                        COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                        COUNT(CASE WHEN event_type = 'share' THEN 1 END) as shares,
                        COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) as conversions
                    FROM collection_analytics
                    WHERE collection_id = %s
                    AND created_at BETWEEN %s AND %s
                """, (collection_id, start_date, end_date))

                metrics_data = cur.fetchone()
                if not metrics_data:
                    return None

            # Get previous period data for growth calculation
            prev_start = start_date - timedelta(days=days_back)
            prev_end = start_date

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT COUNT(*) as total_events
                    FROM collection_analytics
                    WHERE collection_id = %s
                    AND created_at BETWEEN %s AND %s
                """, (collection_id, prev_start, prev_end))

                prev_data = cur.fetchone()
                prev_total = prev_data['total_events'] if prev_data else 0

            # Calculate metrics
            total_current = (
                metrics_data['views'] +
                metrics_data['clicks'] +
                metrics_data['shares'] +
                metrics_data['conversions']
            )

            # Calculate growth rate
            growth_rate = 0.0
            if prev_total > 0:
                growth_rate = (total_current - prev_total) / prev_total

            # Calculate engagement score (weighted sum)
            engagement_score = (
                metrics_data['views'] * 1 +
                metrics_data['clicks'] * 5 +
                metrics_data['shares'] * 10 +
                metrics_data['conversions'] * 20
            )

            # Calculate recency score (more recent = higher score)
            days_since_last = min(days_back, (datetime.utcnow() - start_date).days)
            recency_score = 1.0 - (days_since_last / days_back)

            # Calculate overall trending score
            trending_score = (
                engagement_score * 0.4 +
                growth_rate * 0.3 +
                recency_score * 0.3
            )

            # Normalize score to 0-100 range
            trending_score = min(100.0, trending_score / 10.0)

            return TrendMetrics(
                collection_id=collection_id,
                views=metrics_data['views'],
                clicks=metrics_data['clicks'],
                shares=metrics_data['shares'],
                conversions=metrics_data['conversions'],
                engagement_score=engagement_score,
                growth_rate=growth_rate,
                recency_score=recency_score,
                trending_score=trending_score
            )

        except Exception as e:
            logger.error(f"Failed to calculate trends for collection {collection_id}: {e}")
            return None

    async def get_trending_collections(
        self,
        limit: int = 10,
        min_score_threshold: float = 10.0
    ) -> List[Tuple[str, float]]:
        """
        Get top trending collections

        Args:
            limit: Maximum number of collections to return
            min_score_threshold: Minimum trending score threshold

        Returns:
            List of (collection_id, trending_score) tuples
        """
        try:
            # Get all active collections
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT id, name, type
                    FROM vehicle_collections
                    WHERE is_active = TRUE
                    AND type IN ('curated', 'dynamic', 'template')
                    ORDER BY created_at DESC
                """)

                collections = cur.fetchall()

            # Calculate trends for each collection
            trending_scores = []
            for collection in collections:
                metrics = await self.calculate_collection_trends(collection['id'])
                if metrics and metrics.trending_score >= min_score_threshold:
                    trending_scores.append((collection['id'], metrics.trending_score))

            # Sort by trending score (descending)
            trending_scores.sort(key=lambda x: x[1], reverse=True)

            # Return top N
            return trending_scores[:limit]

        except Exception as e:
            logger.error(f"Failed to get trending collections: {e}")
            return []

    async def detect_market_trends(self) -> List[MarketTrendData]:
        """
        Detect market trends from external sources

        Returns:
            List of MarketTrendData objects
        """
        try:
            market_trends = []

            # In a real implementation, this would fetch from external APIs
            # For now, return simulated trends based on common patterns

            current_month = datetime.utcnow().month
            seasonal_trends = self._get_seasonal_trends(current_month)
            market_trends.extend(seasonal_trends)

            # Add constant trends
            market_trends.extend([
                MarketTrendData(
                    trend_name="Electric Vehicles",
                    trend_score=0.85,
                    keywords=["electric", "EV", "hybrid", "plug-in"],
                    source="industry_analysis",
                    timestamp=datetime.utcnow()
                ),
                MarketTrendData(
                    trend_name="SUVs and Crossovers",
                    trend_score=0.75,
                    keywords=["SUV", "crossover", "family", "AWD"],
                    source="market_analysis",
                    timestamp=datetime.utcnow()
                ),
                MarketTrendData(
                    trend_name="Fuel Efficiency",
                    trend_score=0.70,
                    keywords=["fuel_efficient", "hybrid", "MPG", "eco-friendly"],
                    source="market_trends",
                    timestamp=datetime.utcnow()
                )
            ])

            return market_trends

        except Exception as e:
            logger.error(f"Failed to detect market trends: {e}")
            return []

    def _get_seasonal_trends(self, month: int) -> List[MarketTrendData]:
        """Get seasonal trends based on month"""
        seasonal_map = {
            1: ["Winter Ready", "All-Wheel Drive", "Heated Seats"],
            2: ["Winter Clearance", "4x4 Vehicles"],
            3: ["Spring Models", "Convertibles"],
            4: ["Earth Day Special", "Eco-Friendly"],
            5: ["Summer Travel", "Road Trip Ready"],
            6: ["Family Vacation", "Large SUVs"],
            7: ["Summer Sales", "Sport Cars"],
            8: ["Back to School", "Commuter Cars"],
            9: ["Fall Models", "New Releases"],
            10: ["Harvest Special", "Trucks"],
            11: ["Pre-Winter Prep", "All-Weather"],
            12: ["Holiday Deals", "Luxury Vehicles"]
        }

        trends = []
        for trend_name in seasonal_map.get(month, []):
            trends.append(MarketTrendData(
                trend_name=trend_name,
                trend_score=0.6 + (0.1 * len(trend_name.split())),
                keywords=trend_name.lower().split(),
                source="seasonal",
                timestamp=datetime.utcnow()
            ))

        return trends

    async def generate_trending_collection(
        self,
        trend_data: MarketTrendData,
        max_vehicles: int = 50
    ) -> Optional[str]:
        """
        Generate a trending collection based on market trend data

        Args:
            trend_data: Market trend information
            max_vehicles: Maximum number of vehicles in collection

        Returns:
            Collection ID or None if generation fails
        """
        try:
            from src.collections.collection_engine import CollectionEngine, CollectionCriteria

            # Initialize collection engine
            engine = CollectionEngine()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            await engine.initialize(supabase_url, supabase_key)

            # Build criteria from trend keywords
            criteria = CollectionCriteria()

            # Simple keyword matching (in production, use more sophisticated matching)
            if "electric" in trend_data.keywords or "ev" in trend_data.keywords:
                criteria.fuel_type = ["electric", "plug-in_hybrid"]
            if "suv" in trend_data.keywords or "crossover" in trend_data.keywords:
                criteria.vehicle_type = "SUV"
            if "hybrid" in trend_data.keywords:
                criteria.fuel_type = ["hybrid", "plug-in_hybrid"]
            if "awd" in trend_data.keywords or "4x4" in trend_data.keywords:
                criteria.custom_rules = {"drive_type": "awd"}

            # Create collection
            collection_name = f"Trending: {trend_data.trend_name}"
            description = f"Trending collection based on market insights: {trend_data.description if hasattr(trend_data, 'description') else ''}"

            collection_id = await engine.create_collection(
                name=collection_name,
                description=description,
                collection_type=CollectionType.TRENDING,
                criteria=criteria
            )

            # Set as featured
            await engine.update_collection(
                collection_id=collection_id,
                is_featured=True
            )

            logger.info(f"Generated trending collection {collection_id} for trend {trend_data.trend_name}")
            return collection_id

        except Exception as e:
            logger.error(f"Failed to generate trending collection: {e}")
            return None

    async def update_trending_scores(self):
        """
        Update trending scores for all collections

        This should be run periodically (e.g., hourly) to keep scores fresh
        """
        try:
            # Get all collections
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT id
                    FROM vehicle_collections
                    WHERE is_active = TRUE
                """)

                collection_ids = [row[0] for row in cur.fetchall()]

            # Update scores for each collection
            for collection_id in collection_ids:
                metrics = await self.calculate_collection_trends(collection_id)
                if metrics:
                    # Store score in database (or cache)
                    # In production, this might update a trending_scores table
                    logger.debug(f"Updated trending score for {collection_id}: {metrics.trending_score}")

            logger.info(f"Updated trending scores for {len(collection_ids)} collections")

        except Exception as e:
            logger.error(f"Failed to update trending scores: {e}")

    async def apply_trend_decay(self):
        """
        Apply decay to old trending scores

        Reduces trending scores for collections that haven't been updated recently
        """
        try:
            decay_threshold_days = self.trend_decay_days
            threshold_date = datetime.utcnow() - timedelta(days=decay_threshold)

            with self.db_conn.cursor() as cur:
                # Find collections with old trending scores
                cur.execute("""
                    UPDATE vehicle_collections
                    SET last_refreshed_at = last_refreshed_at - INTERVAL '1 day'
                    WHERE is_active = TRUE
                    AND type = 'trending'
                    AND last_refreshed_at < %s
                """, (threshold_date,))

            logger.info("Applied trend decay to old collections")

        except Exception as e:
            logger.error(f"Failed to apply trend decay: {e}")

    async def run_trending_scheduler(self):
        """
        Run the complete trending update process

        1. Detect market trends
        2. Generate trending collections for new trends
        3. Update existing collection scores
        4. Apply decay to stale collections
        """
        try:
            logger.info("Starting trending scheduler run")

            # Detect market trends
            market_trends = await self.detect_market_trends()
            logger.info(f"Detected {len(market_trends)} market trends")

            # Generate collections for new trends
            for trend in market_trends:
                if trend.trend_score > 0.5:  # Only generate for significant trends
                    collection_id = await self.generate_trending_collection(trend)
                    if collection_id:
                        logger.info(f"Generated collection {collection_id} for trend {trend.trend_name}")

            # Update trending scores
            await self.update_trending_scores()

            # Apply decay
            await self.apply_trend_decay()

            logger.info("Trending scheduler run completed")

        except Exception as e:
            logger.error(f"Failed to run trending scheduler: {e}")

    async def get_trending_insights(self, collection_id: str) -> Dict[str, Any]:
        """
        Get insights about why a collection is trending

        Args:
            collection_id: Collection ID

        Returns:
            Dictionary with trending insights
        """
        try:
            metrics = await self.calculate_collection_trends(collection_id)
            if not metrics:
                return {}

            insights = {
                "trending_score": metrics.trending_score,
                "factors": {
                    "engagement": {
                        "score": metrics.engagement_score,
                        "weight": self.trending_weights[TrendFactor.VIEWS] +
                                   self.trending_weights[TrendFactor.CLICKS] +
                                   self.trending_weights[TrendFactor.SHARES] +
                                   self.trending_weights[TrendFactor.CONVERSIONS],
                        "components": {
                            "views": metrics.views,
                            "clicks": metrics.clicks,
                            "shares": metrics.shares,
                            "conversions": metrics.conversions
                        }
                    },
                    "growth": {
                        "score": metrics.growth_rate,
                        "weight": self.trending_weights[TrendFactor.GROWTH_RATE],
                        "description": f"{metrics.growth_rate:.1%} growth in engagement"
                    },
                    "recency": {
                        "score": metrics.recency_score,
                        "weight": self.trending_weights[TrendFactor.RECENCY],
                        "description": "Recent activity level"
                    }
                },
                "recommendations": self._generate_trending_recommendations(metrics)
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to get trending insights: {e}")
            return {}

    def _generate_trending_recommendations(self, metrics: TrendMetrics) -> List[str]:
        """Generate recommendations based on trending metrics"""
        recommendations = []

        if metrics.conversions == 0:
            recommendations.append("Focus on conversion optimization - users are viewing but not converting")

        if metrics.shares == 0:
            recommendations.append("Add social sharing buttons to increase reach")

        if metrics.growth_rate < 0:
            recommendations.append("Collection engagement is declining - consider refreshing criteria")

        if metrics.trending_score > 80:
            recommendations.append("High trending score - consider featuring on homepage")

        if metrics.views > 1000 and metrics.clicks < 100:
            recommendations.append("Low click-through rate - review collection title and preview")

        return recommendations