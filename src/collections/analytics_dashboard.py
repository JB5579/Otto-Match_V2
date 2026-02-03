"""
Otto.AI Collections Analytics Dashboard

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Analytics dashboard for collection insights and engagement tracking

Features:
- Real-time analytics for collection performance
- Engagement metrics visualization
- A/B testing results dashboard
- Trending collections insights
- User behavior analysis
- Collection optimization recommendations
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import uuid
import psycopg
from psycopg.rows import dict_row
import numpy as np
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Analytics metric types"""
    VIEWS = "views"
    CLICKS = "clicks"
    SHARES = "shares"
    CONVERSIONS = "conversions"
    ENGAGEMENT_RATE = "engagement_rate"
    CLICK_THROUGH_RATE = "click_through_rate"
    CONVERSION_RATE = "conversion_rate"
    AVERAGE_TIME_VIEWED = "average_time_viewed"
    BOUNCE_RATE = "bounce_rate"

class TimePeriod(Enum):
    """Time periods for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class AnalyticsMetric:
    """Analytics metric data model"""
    metric_type: MetricType
    value: float
    collection_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollectionInsights:
    """Insights for a specific collection"""
    collection_id: str
    collection_name: str
    total_views: int = 0
    total_clicks: int = 0
    total_shares: int = 0
    total_conversions: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    conversion_rate: float = 0.0
    average_time_viewed: float = 0.0
    bounce_rate: float = 0.0
    trending_score: float = 0.0
    user_demographics: Dict[str, Any] = field(default_factory=dict)
    performance_trend: str = "stable"  # 'improving', 'declining', 'stable'
    recommendations: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str  # 'metric_card', 'chart', 'table', 'heatmap'
    title: str
    metric_types: List[MetricType]
    time_period: TimePeriod
    filters: Dict[str, Any] = field(default_factory=dict)
    visualization_config: Dict[str, Any] = field(default_factory=dict)

class CollectionsAnalyticsDashboard:
    """
    Analytics dashboard for collection insights and optimization
    """

    def __init__(self):
        """Initialize analytics dashboard"""
        self.db_conn = None
        self.cache_timeout = 300  # 5 minutes
        self.default_widgets = self._initialize_default_widgets()

    def _initialize_default_widgets(self) -> List[DashboardWidget]:
        """Initialize default dashboard widgets"""
        return [
            DashboardWidget(
                widget_id="overview_metrics",
                widget_type="metric_cards",
                title="Overview Metrics",
                metric_types=[MetricType.VIEWS, MetricType.CLICKS, MetricType.CONVERSIONS, MetricType.ENGAGEMENT_RATE],
                time_period=TimePeriod.DAY,
                visualization_config={
                    "layout": "grid",
                    "columns": 4,
                    "show_trend": True,
                    "show_comparison": True
                }
            ),
            DashboardWidget(
                widget_id="collection_performance",
                widget_type="table",
                title="Collection Performance",
                metric_types=[MetricType.VIEWS, MetricType.CLICKS, MetricType.CONVERSION_RATE],
                time_period=TimePeriod.WEEK,
                visualization_config={
                    "sortable": True,
                    "paginated": True,
                    "rows_per_page": 10,
                    "show_rankings": True
                }
            ),
            DashboardWidget(
                widget_id="engagement_trends",
                widget_type="line_chart",
                title="Engagement Trends",
                metric_types=[MetricType.ENGAGEMENT_RATE, MetricType.CLICK_THROUGH_RATE],
                time_period=TimePeriod.MONTH,
                visualization_config={
                    "multi_line": True,
                    "show_annotations": True,
                    "smooth_curve": True
                }
            ),
            DashboardWidget(
                widget_id="conversion_funnel",
                widget_type="funnel_chart",
                title="Conversion Funnel",
                metric_types=[MetricType.VIEWS, MetricType.CLICKS, MetricType.CONVERSIONS],
                time_period=TimePeriod.MONTH,
                visualization_config={
                    "show_percentages": True,
                    "animated": True
                }
            ),
            DashboardWidget(
                widget_id="ab_test_results",
                widget_type="ab_test_table",
                title="A/B Test Results",
                metric_types=[MetricType.CONVERSION_RATE, MetricType.CLICK_THROUGH_RATE],
                time_period=TimePeriod.QUARTER,
                visualization_config={
                    "show_confidence": True,
                    "show_significance": True,
                    "filter_active": True
                }
            ),
            DashboardWidget(
                widget_id="user_demographics",
                widget_type="donut_chart",
                title="User Demographics",
                metric_types=[MetricType.VIEWS],
                time_period=TimePeriod.MONTH,
                visualization_config={
                    "group_by": "demographic",
                    "show_percentages": True
                }
            )
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

            logger.info("CollectionsAnalyticsDashboard initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CollectionsAnalyticsDashboard: {e}")
            return False

    async def track_event(
        self,
        event_type: str,
        collection_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track analytics event

        Args:
            event_type: Type of event (view, click, share, conversion)
            collection_id: Collection ID
            user_id: User ID (optional)
            metadata: Additional event metadata
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collection_analytics (
                        collection_id, user_id, event_type,
                        session_id, metadata, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    collection_id,
                    user_id,
                    event_type,
                    metadata.get('session_id') if metadata else None,
                    json.dumps(metadata) if metadata else None
                ))

            self.db_conn.commit()
            logger.debug(f"Tracked {event_type} event for collection {collection_id}")

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            self.db_conn.rollback()

    async def get_collection_insights(
        self,
        collection_id: str,
        days_back: int = 30
    ) -> Optional[CollectionInsights]:
        """
        Get comprehensive insights for a collection

        Args:
            collection_id: Collection ID
            days_back: Number of days to analyze

        Returns:
            CollectionInsights object or None
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)

            # Get collection details
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT id, name, type
                    FROM vehicle_collections
                    WHERE id = %s
                """, (collection_id,))

                collection = cur.fetchone()
                if not collection:
                    return None

            # Get analytics data
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN event_type = 'view' THEN 1 END) as views,
                        COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                        COUNT(CASE WHEN event_type = 'share' THEN 1 END) as shares,
                        COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) as conversions,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_time_viewed
                    FROM collection_analytics
                    WHERE collection_id = %s
                    AND created_at >= %s
                """, (collection_id, start_date))

                analytics = cur.fetchone()

            # Calculate rates
            views = analytics['views'] or 0
            clicks = analytics['clicks'] or 0
            shares = analytics['shares'] or 0
            conversions = analytics['conversions'] or 0
            avg_time_viewed = analytics['avg_time_viewed'] or 0

            engagement_rate = (clicks + shares) / views if views > 0 else 0
            click_through_rate = clicks / views if views > 0 else 0
            conversion_rate = conversions / views if views > 0 else 0

            # Get bounce rate (single view sessions)
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    WITH session_views AS (
                        SELECT session_id, COUNT(*) as view_count
                        FROM collection_analytics
                        WHERE collection_id = %s
                        AND event_type = 'view'
                        AND created_at >= %s
                        GROUP BY session_id
                    )
                    SELECT
                        COUNT(CASE WHEN view_count = 1 THEN 1 END) as single_view_sessions,
                        COUNT(*) as total_sessions
                    FROM session_views
                """, (collection_id, start_date))

                bounce_data = cur.fetchone()
                if bounce_data and bounce_data['total_sessions'] > 0:
                    bounce_rate = bounce_data['single_view_sessions'] / bounce_data['total_sessions']
                else:
                    bounce_rate = 0

            # Get trending score
            trending_score = await self._calculate_trending_score(collection_id, days_back)

            # Get user demographics
            demographics = await self._get_user_demographics(collection_id, days_back)

            # Analyze performance trend
            performance_trend = await self._analyze_performance_trend(collection_id, days_back)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                collection_id, views, clicks, conversions, engagement_rate
            )

            return CollectionInsights(
                collection_id=collection_id,
                collection_name=collection['name'],
                total_views=views,
                total_clicks=clicks,
                total_shares=shares,
                total_conversions=conversions,
                engagement_rate=engagement_rate,
                click_through_rate=click_through_rate,
                conversion_rate=conversion_rate,
                average_time_viewed=avg_time_viewed,
                bounce_rate=bounce_rate,
                trending_score=trending_score,
                user_demographics=demographics,
                performance_trend=performance_trend,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Failed to get collection insights: {e}")
            return None

    async def get_dashboard_data(
        self,
        time_period: TimePeriod = TimePeriod.DAY,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get data for the analytics dashboard

        Args:
            time_period: Time period for analytics
            filters: Optional filters to apply

        Returns:
            Dashboard data dictionary
        """
        try:
            # Calculate date range
            days_back = self._get_days_from_period(time_period)
            start_date = datetime.utcnow() - timedelta(days=days_back)

            dashboard_data = {
                "time_period": time_period.value,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": datetime.utcnow().isoformat()
                },
                "widgets": []
            }

            # Generate data for each widget
            for widget in self.default_widgets:
                widget_data = await self._generate_widget_data(widget, start_date, filters)
                dashboard_data["widgets"].append(widget_data)

            # Add summary metrics
            dashboard_data["summary"] = await self._get_summary_metrics(start_date, filters)

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}

    async def get_top_collections(
        self,
        metric_type: MetricType = MetricType.VIEWS,
        limit: int = 10,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get top performing collections by metric

        Args:
            metric_type: Metric to sort by
            limit: Maximum number of collections
            days_back: Number of days to analyze

        Returns:
            List of collection performance data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)

            # Build query based on metric type
            metric_column = self._get_metric_column(metric_type)

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"""
                    SELECT
                        vc.id,
                        vc.name,
                        vc.type,
                        COUNT(CASE WHEN ca.event_type = '{metric_column}' THEN 1 END) as metric_value,
                        COUNT(CASE WHEN ca.event_type = 'view' THEN 1 END) as views,
                        COUNT(CASE WHEN ca.event_type = 'click' THEN 1 END) as clicks,
                        COUNT(CASE WHEN ca.event_type = 'conversion' THEN 1 END) as conversions
                    FROM vehicle_collections vc
                    LEFT JOIN collection_analytics ca ON vc.id = ca.collection_id
                    WHERE vc.is_active = TRUE
                    AND (ca.created_at >= %s OR ca.created_at IS NULL)
                    GROUP BY vc.id, vc.name, vc.type
                    ORDER BY metric_value DESC
                    LIMIT %s
                """, (start_date, limit))

                return cur.fetchall()

        except Exception as e:
            logger.error(f"Failed to get top collections: {e}")
            return []

    async def export_analytics_report(
        self,
        format_type: str = "csv",
        collection_ids: Optional[List[str]] = None,
        days_back: int = 30
    ) -> str:
        """
        Export analytics report

        Args:
            format_type: Export format (csv, json, excel)
            collection_ids: Specific collections to include
            days_back: Number of days to include

        Returns:
            File path or data string
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)

            # Get analytics data
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                query = """
                    SELECT
                        vc.id as collection_id,
                        vc.name as collection_name,
                        vc.type as collection_type,
                        ca.event_type,
                        ca.user_id,
                        ca.session_id,
                        ca.metadata,
                        ca.created_at
                    FROM vehicle_collections vc
                    LEFT JOIN collection_analytics ca ON vc.id = ca.collection_id
                    WHERE vc.is_active = TRUE
                    AND ca.created_at >= %s
                """

                params = [start_date]
                if collection_ids:
                    placeholders = ','.join(['%s'] * len(collection_ids))
                    query += f" AND vc.id IN ({placeholders})"
                    params.extend(collection_ids)

                query += " ORDER BY ca.created_at DESC"
                cur.execute(query, params)

                data = cur.fetchall()

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Export based on format
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            if format_type.lower() == "csv":
                filename = f"collection_analytics_{timestamp}.csv"
                df.to_csv(filename, index=False)
                return filename

            elif format_type.lower() == "json":
                return df.to_json(orient='records', indent=2)

            elif format_type.lower() == "excel":
                filename = f"collection_analytics_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
                return filename

            else:
                raise ValueError(f"Unsupported export format: {format_type}")

        except Exception as e:
            logger.error(f"Failed to export analytics report: {e}")
            raise

    async def _calculate_trending_score(self, collection_id: str, days_back: int) -> float:
        """Calculate trending score for a collection"""
        try:
            from src.collections.trending_algorithm import TrendingAlgorithm

            # Initialize trending algorithm
            algorithm = TrendingAlgorithm()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            await algorithm.initialize(supabase_url, supabase_key)

            # Get trending metrics
            metrics = await algorithm.calculate_collection_trends(collection_id, days_back)
            return metrics.trending_score if metrics else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate trending score: {e}")
            return 0.0

    async def _get_user_demographics(self, collection_id: str, days_back: int) -> Dict[str, Any]:
        """Get user demographics for collection"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)

            # This would typically join with a users table
            # For now, return simulated data
            return {
                "age_groups": {
                    "18-24": 0.15,
                    "25-34": 0.35,
                    "35-44": 0.30,
                    "45-54": 0.15,
                    "55+": 0.05
                },
                "locations": {
                    "urban": 0.45,
                    "suburban": 0.35,
                    "rural": 0.20
                },
                "device_types": {
                    "desktop": 0.40,
                    "mobile": 0.50,
                    "tablet": 0.10
                }
            }

        except Exception as e:
            logger.error(f"Failed to get user demographics: {e}")
            return {}

    async def _analyze_performance_trend(self, collection_id: str, days_back: int) -> str:
        """Analyze performance trend for collection"""
        try:
            # Compare recent performance to previous period
            mid_date = datetime.utcnow() - timedelta(days=days_back//2)
            start_date = datetime.utcnow() - timedelta(days=days_back)

            # Get recent period metrics
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT COUNT(*) as events
                    FROM collection_analytics
                    WHERE collection_id = %s
                    AND created_at >= %s
                """, (collection_id, mid_date))

                recent_data = cur.fetchone()

            # Get previous period metrics
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT COUNT(*) as events
                    FROM collection_analytics
                    WHERE collection_id = %s
                    AND created_at BETWEEN %s AND %s
                """, (collection_id, start_date, mid_date))

                previous_data = cur.fetchone()

            # Calculate trend
            recent_count = recent_data['events'] if recent_data else 0
            previous_count = previous_data['events'] if previous_data else 0

            if previous_count == 0:
                return "stable" if recent_count == 0 else "improving"

            change_rate = (recent_count - previous_count) / previous_count

            if change_rate > 0.1:
                return "improving"
            elif change_rate < -0.1:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Failed to analyze performance trend: {e}")
            return "stable"

    async def _generate_recommendations(
        self,
        collection_id: str,
        views: int,
        clicks: int,
        conversions: int,
        engagement_rate: float
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if views == 0:
            recommendations.append("Collection has no views - consider improving visibility and title")
        elif clicks == 0:
            recommendations.append("Low click-through rate - review collection preview and description")
        elif conversions == 0:
            recommendations.append("No conversions - check if vehicles match user intent")
        elif engagement_rate < 0.1:
            recommendations.append("Low engagement - add more compelling vehicles or improve presentation")
        elif engagement_rate > 0.5:
            recommendations.append("High engagement - consider featuring this collection on homepage")

        # Get A/B test recommendations
        try:
            from src.collections.ab_testing import ABTestingFramework

            ab_framework = ABTestingFramework()
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            await ab_framework.initialize(supabase_url, supabase_key)

            test_recommendations = await ab_framework.get_test_recommendations(collection_id)
            recommendations.extend(test_recommendations)

        except Exception as e:
            logger.error(f"Failed to get A/B test recommendations: {e}")

        return recommendations

    async def _generate_widget_data(
        self,
        widget: DashboardWidget,
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate data for a specific widget"""
        try:
            widget_data = {
                "widget_id": widget.widget_id,
                "widget_type": widget.widget_type,
                "title": widget.title,
                "data": {}
            }

            if widget.widget_type == "metric_cards":
                widget_data["data"] = await self._get_metric_cards_data(widget.metric_types, start_date, filters)

            elif widget.widget_type == "table":
                widget_data["data"] = await self._get_table_data(widget.metric_types, start_date, filters)

            elif widget.widget_type == "line_chart":
                widget_data["data"] = await self._get_line_chart_data(widget.metric_types, start_date, filters)

            elif widget.widget_type == "funnel_chart":
                widget_data["data"] = await self._get_funnel_data(widget.metric_types, start_date, filters)

            elif widget.widget_type == "ab_test_table":
                widget_data["data"] = await self._get_ab_test_data(widget.metric_types, start_date, filters)

            elif widget.widget_type == "donut_chart":
                widget_data["data"] = await self._get_donut_chart_data(widget.metric_types, start_date, filters)

            return widget_data

        except Exception as e:
            logger.error(f"Failed to generate widget data: {e}")
            return {"widget_id": widget.widget_id, "error": str(e)}

    async def _get_metric_cards_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get data for metric cards widget"""
        cards = []

        for metric_type in metric_types:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                if metric_type == MetricType.VIEWS:
                    cur.execute("""
                        SELECT COUNT(*) as value
                        FROM collection_analytics
                        WHERE event_type = 'view'
                        AND created_at >= %s
                    """, (start_date,))

                elif metric_type == MetricType.CLICKS:
                    cur.execute("""
                        SELECT COUNT(*) as value
                        FROM collection_analytics
                        WHERE event_type = 'click'
                        AND created_at >= %s
                    """, (start_date,))

                elif metric_type == MetricType.CONVERSIONS:
                    cur.execute("""
                        SELECT COUNT(*) as value
                        FROM collection_analytics
                        WHERE event_type = 'conversion'
                        AND created_at >= %s
                    """, (start_date,))

                elif metric_type == MetricType.ENGAGEMENT_RATE:
                    cur.execute("""
                        SELECT
                            COUNT(CASE WHEN event_type IN ('click', 'share') THEN 1 END) * 1.0 /
                            NULLIF(COUNT(CASE WHEN event_type = 'view' THEN 1 END), 0) as value
                        FROM collection_analytics
                        WHERE created_at >= %s
                    """, (start_date,))

                result = cur.fetchone()
                value = result['value'] if result else 0

                cards.append({
                    "metric": metric_type.value,
                    "value": round(value, 4) if isinstance(value, float) else value,
                    "format": "percentage" if metric_type in [MetricType.ENGAGEMENT_RATE, MetricType.CONVERSION_RATE] else "number"
                })

        return cards

    async def _get_table_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for table widget"""
        with self.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    vc.id,
                    vc.name,
                    vc.type,
                    COUNT(CASE WHEN ca.event_type = 'view' THEN 1 END) as views,
                    COUNT(CASE WHEN ca.event_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN ca.event_type = 'conversion' THEN 1 END) as conversions,
                    COUNT(CASE WHEN ca.event_type IN ('click', 'share') THEN 1 END) * 1.0 /
                    NULLIF(COUNT(CASE WHEN ca.event_type = 'view' THEN 1 END), 0) as engagement_rate
                FROM vehicle_collections vc
                LEFT JOIN collection_analytics ca ON vc.id = ca.collection_id
                WHERE vc.is_active = TRUE
                AND (ca.created_at >= %s OR ca.created_at IS NULL)
                GROUP BY vc.id, vc.name, vc.type
                ORDER BY views DESC
                LIMIT 50
            """, (start_date,))

            return {"rows": cur.fetchall()}

    async def _get_line_chart_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for line chart widget"""
        # Get daily metrics for trend line
        with self.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(CASE WHEN event_type = 'view' THEN 1 END) as views,
                    COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) as conversions
                FROM collection_analytics
                WHERE created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date,))

            return {"timeline": cur.fetchall()}

    async def _get_funnel_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for funnel chart"""
        with self.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    event_type,
                    COUNT(*) as count
                FROM collection_analytics
                WHERE created_at >= %s
                AND event_type IN ('view', 'click', 'conversion')
                GROUP BY event_type
                ORDER BY
                    CASE event_type
                        WHEN 'view' THEN 1
                        WHEN 'click' THEN 2
                        WHEN 'conversion' THEN 3
                    END
            """, (start_date,))

            return {"stages": cur.fetchall()}

    async def _get_ab_test_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for A/B test table"""
        with self.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    abt.id,
                    abt.name,
                    abt.status,
                    abt.created_at,
                    COUNT(DISTINCT abtr.user_id) as participants,
                    AVG(abtr.conversion_rate) as avg_conversion_rate
                FROM collection_ab_tests abt
                LEFT JOIN collection_ab_test_results abtr ON abt.id = abtr.test_id
                WHERE abt.created_at >= %s
                GROUP BY abt.id, abt.name, abt.status, abt.created_at
                ORDER BY abt.created_at DESC
                LIMIT 20
            """, (start_date,))

            return {"tests": cur.fetchall()}

    async def _get_donut_chart_data(
        self,
        metric_types: List[MetricType],
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get data for donut chart (demographics)"""
        # Return simulated demographics data
        return {
            "segments": [
                {"category": "Desktop", "value": 40, "percentage": 0.4},
                {"category": "Mobile", "value": 50, "percentage": 0.5},
                {"category": "Tablet", "value": 10, "percentage": 0.1}
            ]
        }

    async def _get_summary_metrics(
        self,
        start_date: datetime,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        with self.db_conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    COUNT(DISTINCT vc.id) as total_collections,
                    COUNT(CASE WHEN ca.event_type = 'view' THEN 1 END) as total_views,
                    COUNT(CASE WHEN ca.event_type = 'click' THEN 1 END) as total_clicks,
                    COUNT(CASE WHEN ca.event_type = 'conversion' THEN 1 END) as total_conversions,
                    COUNT(CASE WHEN ca.event_type = 'share' THEN 1 END) as total_shares,
                    COUNT(DISTINCT ca.user_id) as unique_users
                FROM vehicle_collections vc
                LEFT JOIN collection_analytics ca ON vc.id = ca.collection_id
                WHERE vc.is_active = TRUE
                AND (ca.created_at >= %s OR ca.created_at IS NULL)
            """, (start_date,))

            return cur.fetchone() or {}

    def _get_days_from_period(self, time_period: TimePeriod) -> int:
        """Convert time period to days"""
        period_map = {
            TimePeriod.HOUR: 1,
            TimePeriod.DAY: 1,
            TimePeriod.WEEK: 7,
            TimePeriod.MONTH: 30,
            TimePeriod.QUARTER: 90,
            TimePeriod.YEAR: 365
        }
        return period_map.get(time_period, 1)

    def _get_metric_column(self, metric_type: MetricType) -> str:
        """Convert metric type to database column"""
        metric_map = {
            MetricType.VIEWS: 'view',
            MetricType.CLICKS: 'click',
            MetricType.SHARES: 'share',
            MetricType.CONVERSIONS: 'conversion'
        }
        return metric_map.get(metric_type, 'view')

    async def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("CollectionsAnalyticsDashboard connection closed")