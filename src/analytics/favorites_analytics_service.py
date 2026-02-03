"""
Otto.AI Favorites Analytics Service

Implements Story 1.6: Vehicle Favorites and Notifications (Technical Notes)
Analytics tracking for favorites conversion and user behavior

Features:
- Track favorite-to-conversion metrics
- Monitor user engagement with favorites
- Generate analytics dashboard data
- Track conversion rates and patterns
- Support A/B testing framework for notification effectiveness
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

@dataclass
class FavoriteEvent:
    """Favorite interaction event data model"""
    id: str
    user_id: str
    vehicle_id: str
    event_type: str  # favorited, unfavorited, viewed_from_favorites, converted, notification_sent
    timestamp: datetime
    data: Dict[str, Any]
    session_id: Optional[str] = None

@dataclass
class ConversionMetrics:
    """Conversion metrics data model"""
    user_id: str
    vehicle_id: str
    favorited_at: datetime
    conversion_events: List[Dict[str, Any]]
    converted: bool
    conversion_time: Optional[timedelta]
    conversion_type: Optional[str]  # reservation, inquiry, purchase
    conversion_value: Optional[float]

class FavoritesAnalyticsService:
    """
    Service for tracking and analyzing favorites conversion metrics
    """

    def __init__(self):
        """Initialize analytics service"""
        self.db_conn = None

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection and create analytics tables

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

            logger.info("✅ Favorites Analytics Service connected to Supabase")

            # Create required tables
            await self._create_analytics_tables()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Favorites Analytics Service: {e}")
            return False

    async def _create_analytics_tables(self) -> None:
        """Create analytics tracking tables"""
        try:
            with self.db_conn.cursor() as cur:
                # Create favorite_events table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS favorite_events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        data JSONB DEFAULT '{}',
                        session_id VARCHAR(255),
                        INDEX idx_favorite_events_user_id (user_id),
                        INDEX idx_favorite_events_vehicle_id (vehicle_id),
                        INDEX idx_favorite_events_timestamp (timestamp),
                        INDEX idx_favorite_events_type (event_type)
                    );
                """)

                # Create conversion_tracking table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversion_tracking (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_id VARCHAR(255) NOT NULL,
                        favorited_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        converted BOOLEAN DEFAULT false,
                        conversion_time TIMESTAMP WITH TIME ZONE,
                        conversion_type VARCHAR(50),
                        conversion_value DECIMAL(10,2),
                        notification_effective BOOLEAN DEFAULT false,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_conversion_user_id (user_id),
                        INDEX idx_conversion_vehicle_id (vehicle_id),
                        INDEX idx_conversion_converted (converted)
                    );
                """)

                # Create favorite_performance_metrics table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS favorite_performance_metrics (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        vehicle_id VARCHAR(255) NOT NULL,
                        total_favorites INTEGER DEFAULT 0,
                        total_conversions INTEGER DEFAULT 0,
                        conversion_rate DECIMAL(5,4) DEFAULT 0,
                        avg_time_to_conversion_hours DECIMAL(10,2),
                        notification_effectiveness_rate DECIMAL(5,4),
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_performance_vehicle_id (vehicle_id)
                    );
                """)

                # Create ab_test_results table for notification testing
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ab_test_results (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        test_name VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        test_group VARCHAR(50) NOT NULL, -- control, treatment_a, treatment_b
                        metric_type VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(10,4),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_ab_test_name (test_name),
                        INDEX idx_ab_test_user_id (user_id)
                    );
                """)

                self.db_conn.commit()
                logger.info("✅ Analytics tables created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create analytics tables: {e}")
            raise

    async def track_favorite_event(
        self,
        user_id: str,
        vehicle_id: str,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Track a favorite-related event

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            event_type: Type of event (favorited, unfavorited, viewed, converted, etc.)
            data: Additional event data
            session_id: Optional session identifier

        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            event_id = str(uuid.uuid4())

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO favorite_events (
                        id, user_id, vehicle_id, event_type, data, session_id
                    ) VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    event_id, user_id, vehicle_id, event_type,
                    json.dumps(data), session_id
                ))

                self.db_conn.commit()

            # Update conversion tracking if this is a conversion event
            if event_type in ['converted', 'reservation', 'inquiry', 'purchase']:
                await self._update_conversion_tracking(user_id, vehicle_id, event_type, data)

            logger.info(f"📊 Tracked event {event_type} for user {user_id}, vehicle {vehicle_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to track favorite event: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def track_favorite_conversion(
        self,
        user_id: str,
        vehicle_id: str,
        conversion_type: str,
        conversion_value: Optional[float] = None,
        notification_triggered: bool = False
    ) -> bool:
        """
        Track a conversion from favorite to action

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            conversion_type: Type of conversion (reservation, inquiry, purchase)
            conversion_value: Optional monetary value of conversion
            notification_triggered: Whether this conversion was triggered by notification

        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            # Get original favorite timestamp
            favorited_at = await self._get_favorite_timestamp(user_id, vehicle_id)
            if not favorited_at:
                logger.warning(f"No favorite found for user {user_id}, vehicle {vehicle_id}")
                return False

            conversion_time = datetime.utcnow()
            time_to_conversion = conversion_time - favorited_at

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversion_tracking (
                        user_id, vehicle_id, favorited_at, converted, conversion_time,
                        conversion_type, conversion_value, notification_effective
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, vehicle_id) DO UPDATE SET
                        converted = EXCLUDED.converted,
                        conversion_time = EXCLUDED.conversion_time,
                        conversion_type = EXCLUDED.conversion_type,
                        conversion_value = EXCLUDED.conversion_value,
                        notification_effective = EXCLUDED.notification_effective,
                        updated_at = NOW();
                """, (
                    user_id, vehicle_id, favorited_at, True, conversion_time,
                    conversion_type, conversion_value, notification_triggered
                ))

                self.db_conn.commit()

            # Update vehicle performance metrics
            await self._update_vehicle_performance_metrics(vehicle_id)

            # Track conversion event
            await self.track_favorite_event(
                user_id, vehicle_id, conversion_type,
                {
                    'conversion_value': conversion_value,
                    'time_to_conversion_hours': time_to_conversion.total_seconds() / 3600,
                    'notification_triggered': notification_triggered
                }
            )

            logger.info(f"💰 Tracked conversion {conversion_type} for user {user_id}, vehicle {vehicle_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to track conversion: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def _get_favorite_timestamp(self, user_id: str, vehicle_id: str) -> Optional[datetime]:
        """Get the timestamp when user favorited the vehicle"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT timestamp
                    FROM favorite_events
                    WHERE user_id = %s AND vehicle_id = %s AND event_type = 'favorited'
                    ORDER BY timestamp ASC
                    LIMIT 1;
                """, (user_id, vehicle_id))

                result = cur.fetchone()
                return result['timestamp'] if result else None

        except Exception as e:
            logger.error(f"❌ Failed to get favorite timestamp: {e}")
            return None

    async def _update_conversion_tracking(
        self,
        user_id: str,
        vehicle_id: str,
        conversion_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Update conversion tracking with new conversion event"""
        try:
            favorited_at = await self._get_favorite_timestamp(user_id, vehicle_id)
            if not favorited_at:
                return

            conversion_time = datetime.utcnow()
            conversion_value = data.get('conversion_value')

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversion_tracking (
                        user_id, vehicle_id, favorited_at, converted, conversion_time,
                        conversion_type, conversion_value, notification_effective
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, vehicle_id) DO UPDATE SET
                        converted = EXCLUDED.converted,
                        conversion_time = EXCLUDED.conversion_time,
                        conversion_type = EXCLUDED.conversion_type,
                        conversion_value = EXCLUDED.conversion_value,
                        updated_at = NOW();
                """, (
                    user_id, vehicle_id, favorited_at, True, conversion_time,
                    conversion_type, conversion_value, data.get('notification_triggered', False)
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update conversion tracking: {e}")

    async def _update_vehicle_performance_metrics(self, vehicle_id: str) -> None:
        """Update performance metrics for a vehicle"""
        try:
            with self.db_conn.cursor() as cur:
                # Get favorite count
                cur.execute("""
                    SELECT COUNT(*) as total_favorites
                    FROM favorite_events
                    WHERE vehicle_id = %s AND event_type = 'favorited';
                """, (vehicle_id,))
                total_favorites = cur.fetchone()[0]

                # Get conversion count and average time
                cur.execute("""
                    SELECT
                        COUNT(*) as total_conversions,
                        AVG(EXTRACT(EPOCH FROM (conversion_time - favorited_at))/3600) as avg_time_hours,
                        COUNT(CASE WHEN notification_effective = true THEN 1 END) * 1.0 / COUNT(*) as notification_effectiveness
                    FROM conversion_tracking
                    WHERE vehicle_id = %s AND converted = true;
                """, (vehicle_id,))
                result = cur.fetchone()
                total_conversions, avg_time_hours, notification_effectiveness = result

                # Calculate conversion rate
                conversion_rate = (total_conversions / total_favorites) if total_favorites > 0 else 0

                # Update performance metrics
                cur.execute("""
                    INSERT INTO favorite_performance_metrics (
                        vehicle_id, total_favorites, total_conversions, conversion_rate,
                        avg_time_to_conversion_hours, notification_effectiveness_rate
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vehicle_id) DO UPDATE SET
                        total_favorites = EXCLUDED.total_favorites,
                        total_conversions = EXCLUDED.total_conversions,
                        conversion_rate = EXCLUDED.conversion_rate,
                        avg_time_to_conversion_hours = EXCLUDED.avg_time_to_conversion_hours,
                        notification_effectiveness_rate = EXCLUDED.notification_effectiveness_rate,
                        last_updated = NOW();
                """, (
                    vehicle_id, total_favorites, total_conversions, conversion_rate,
                    avg_time_hours, notification_effectiveness or 0
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update vehicle performance metrics: {e}")

    async def get_favorites_analytics(
        self,
        user_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive favorites analytics

        Args:
            user_id: Optional user filter
            vehicle_id: Optional vehicle filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Analytics data dictionary
        """
        try:
            # Build base query conditions
            conditions = []
            params = []
            param_index = 1

            if user_id:
                conditions.append(f"user_id = ${param_index}")
                params.append(user_id)
                param_index += 1

            if vehicle_id:
                conditions.append(f"vehicle_id = ${param_index}")
                params.append(vehicle_id)
                param_index += 1

            if start_date:
                conditions.append(f"timestamp >= ${param_index}")
                params.append(start_date)
                param_index += 1

            if end_date:
                conditions.append(f"timestamp <= ${param_index}")
                params.append(end_date)
                param_index += 1

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get event counts by type
                cur.execute(f"""
                    SELECT
                        event_type,
                        COUNT(*) as count,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM favorite_events
                    {where_clause}
                    GROUP BY event_type
                    ORDER BY count DESC;
                """, params)

                event_counts = cur.fetchall()

                # Get daily trends
                cur.execute(f"""
                    SELECT
                        DATE(timestamp) as date,
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN event_type = 'favorited' THEN 1 END) as favorites,
                        COUNT(CASE WHEN event_type IN ('converted', 'reservation', 'inquiry', 'purchase') THEN 1 END) as conversions
                    FROM favorite_events
                    {where_clause}
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                    LIMIT 30;
                """, params)

                daily_trends = cur.fetchall()

                # Get top performing vehicles
                if not vehicle_id:  # Only if not filtering by specific vehicle
                    cur.execute(f"""
                        SELECT
                            fe.vehicle_id,
                            COUNT(CASE WHEN fe.event_type = 'favorited' THEN 1 END) as favorites,
                            COUNT(CASE WHEN fe.event_type IN ('converted', 'reservation', 'inquiry', 'purchase') THEN 1 END) as conversions,
                            COALESCE(fpm.conversion_rate, 0) as conversion_rate
                        FROM favorite_events fe
                        LEFT JOIN favorite_performance_metrics fpm ON fe.vehicle_id = fpm.vehicle_id
                        {where_clause.replace('timestamp', 'fe.timestamp')}
                        GROUP BY fe.vehicle_id, fpm.conversion_rate
                        ORDER BY favorites DESC
                        LIMIT 10;
                    """, params)

                    top_vehicles = cur.fetchall()
                else:
                    top_vehicles = []

            # Calculate overall metrics
            total_favorites = next((event['count'] for event in event_counts if event['event_type'] == 'favorited'), 0)
            total_conversions = sum(event['count'] for event in event_counts if event['event_type'] in ['converted', 'reservation', 'inquiry', 'purchase'])
            overall_conversion_rate = (total_conversions / total_favorites) if total_favorites > 0 else 0

            analytics = {
                'summary': {
                    'total_favorites': total_favorites,
                    'total_conversions': total_conversions,
                    'overall_conversion_rate': round(overall_conversion_rate * 100, 2),
                    'unique_users': sum(event['unique_users'] for event in event_counts),
                    'filter_applied': {
                        'user_id': user_id,
                        'vehicle_id': vehicle_id,
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    }
                },
                'event_breakdown': [
                    {
                        'event_type': event['event_type'],
                        'count': event['count'],
                        'unique_users': event['unique_users']
                    }
                    for event in event_counts
                ],
                'daily_trends': [
                    {
                        'date': trend['date'].isoformat(),
                        'total_events': trend['total_events'],
                        'favorites': trend['favorites'],
                        'conversions': trend['conversions']
                    }
                    for trend in daily_trends
                ],
                'top_vehicles': [
                    {
                        'vehicle_id': vehicle['vehicle_id'],
                        'favorites': vehicle['favorites'],
                        'conversions': vehicle['conversions'],
                        'conversion_rate': round(vehicle['conversion_rate'] * 100, 2)
                    }
                    for vehicle in top_vehicles
                ],
                'generated_at': datetime.utcnow().isoformat()
            }

            return analytics

        except Exception as e:
            logger.error(f"❌ Failed to get favorites analytics: {e}")
            return {}

    async def get_user_favorite_journey(self, user_id: str, vehicle_id: str) -> Dict[str, Any]:
        """
        Get the complete journey of a user's interaction with a favorited vehicle

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier

        Returns:
            User journey data
        """
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get all events for this user-vehicle pair
                cur.execute("""
                    SELECT
                        event_type,
                        timestamp,
                        data,
                        session_id
                    FROM favorite_events
                    WHERE user_id = %s AND vehicle_id = %s
                    ORDER BY timestamp ASC;
                """, (user_id, vehicle_id))

                events = cur.fetchall()

                # Get conversion data
                cur.execute("""
                    SELECT
                        favorited_at,
                        converted,
                        conversion_time,
                        conversion_type,
                        conversion_value,
                        notification_effective
                    FROM conversion_tracking
                    WHERE user_id = %s AND vehicle_id = %s;
                """, (user_id, vehicle_id))

                conversion_data = cur.fetchone()

                # Calculate journey metrics
                if events and conversion_data:
                    first_event = events[0]['timestamp']
                    last_event = events[-1]['timestamp']
                    journey_duration = last_event - first_event

                    if conversion_data['converted'] and conversion_data['conversion_time']:
                        time_to_conversion = conversion_data['conversion_time'] - conversion_data['favorited_at']
                    else:
                        time_to_conversion = None
                else:
                    journey_duration = None
                    time_to_conversion = None

                journey = {
                    'user_id': user_id,
                    'vehicle_id': vehicle_id,
                    'events': [
                        {
                            'event_type': event['event_type'],
                            'timestamp': event['timestamp'].isoformat(),
                            'data': event['data'],
                            'session_id': event['session_id']
                        }
                        for event in events
                    ],
                    'conversion': {
                        'converted': conversion_data['converted'] if conversion_data else False,
                        'conversion_type': conversion_data['conversion_type'] if conversion_data else None,
                        'conversion_value': float(conversion_data['conversion_value']) if conversion_data and conversion_data['conversion_value'] else None,
                        'notification_effective': conversion_data['notification_effective'] if conversion_data else False,
                        'time_to_conversion_hours': (time_to_conversion.total_seconds() / 3600) if time_to_conversion else None
                    } if conversion_data else None,
                    'journey_metrics': {
                        'total_events': len(events),
                        'journey_duration_hours': (journey_duration.total_seconds() / 3600) if journey_duration else None,
                        'time_to_conversion_hours': (time_to_conversion.total_seconds() / 3600) if time_to_conversion else None,
                        'conversion_successful': conversion_data['converted'] if conversion_data else False
                    },
                    'generated_at': datetime.utcnow().isoformat()
                }

                return journey

        except Exception as e:
            logger.error(f"❌ Failed to get user favorite journey: {e}")
            return {}

    async def ab_test_notification_effectiveness(
        self,
        test_name: str,
        user_id: str,
        test_group: str,
        metric_type: str,
        metric_value: float
    ) -> bool:
        """
        Record A/B test result for notification effectiveness

        Args:
            test_name: Name of the A/B test
            user_id: User identifier
            test_group: Test group (control, treatment_a, treatment_b)
            metric_type: Type of metric being measured
            metric_value: Value of the metric

        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ab_test_results (
                        test_name, user_id, test_group, metric_type, metric_value
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (test_name, user_id, test_group, metric_type, metric_value))

                self.db_conn.commit()

            logger.info(f"🧪 Recorded A/B test result: {test_name} - {test_group} - {metric_type}: {metric_value}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record A/B test result: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def get_notification_effectiveness_report(
        self,
        test_name: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Generate effectiveness report for notification A/B tests

        Args:
            test_name: Name of the A/B test
            days_back: Number of days to look back for data

        Returns:
            Effectiveness report data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get test results
                cur.execute("""
                    SELECT
                        test_group,
                        metric_type,
                        AVG(metric_value) as avg_value,
                        COUNT(*) as sample_size,
                        STDDEV(metric_value) as std_dev
                    FROM ab_test_results
                    WHERE test_name = %s AND created_at >= %s
                    GROUP BY test_group, metric_type
                    ORDER BY test_group, metric_type;
                """, (test_name, cutoff_date))

                results = cur.fetchall()

                # Group results by metric type
                metrics = {}
                for result in results:
                    metric_type = result['metric_type']
                    if metric_type not in metrics:
                        metrics[metric_type] = []
                    metrics[metric_type].append({
                        'group': result['test_group'],
                        'avg_value': float(result['avg_value']),
                        'sample_size': result['sample_size'],
                        'std_dev': float(result['std_dev']) if result['std_dev'] else 0
                    })

                # Calculate statistical significance for each metric
                report = {
                    'test_name': test_name,
                    'period_days': days_back,
                    'metrics': {},
                    'generated_at': datetime.utcnow().isoformat()
                }

                for metric_type, groups in metrics.items():
                    if len(groups) >= 2:  # Need at least 2 groups for comparison
                        control = next((g for g in groups if g['group'] == 'control'), groups[0])
                        treatment = next((g for g in groups if g['group'] != 'control'), groups[1])

                        # Simple uplift calculation
                        if control['avg_value'] > 0:
                            uplift = ((treatment['avg_value'] - control['avg_value']) / control['avg_value']) * 100
                        else:
                            uplift = 0

                        report['metrics'][metric_type] = {
                            'control': {
                                'avg_value': control['avg_value'],
                                'sample_size': control['sample_size'],
                                'std_dev': control['std_dev']
                            },
                            'treatment': {
                                'avg_value': treatment['avg_value'],
                                'sample_size': treatment['sample_size'],
                                'std_dev': treatment['std_dev'],
                                'group_name': treatment['group']
                            },
                            'uplift_percentage': round(uplift, 2)
                        }

                return report

        except Exception as e:
            logger.error(f"❌ Failed to get notification effectiveness report: {e}")
            return {}

    async def close(self) -> None:
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Favorites Analytics Service connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass