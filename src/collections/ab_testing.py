"""
Otto.AI Collections A/B Testing Framework

Implements Story 1.7: Add Curated Vehicle Collections and Categories
A/B testing framework for optimizing collection placement and presentation

Features:
- A/B test creation and management
- Traffic splitting and user assignment
- Statistical significance calculation
- Conversion tracking and analysis
- Test result reporting
"""

import os
import asyncio
import logging
import hashlib
import secrets
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import psycopg
from psycopg.rows import dict_row
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """A/B test status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TestMetric(Enum):
    """Test metrics"""
    CLICK_THROUGH_RATE = "ctr"
    CONVERSION_RATE = "conversion"
    ENGAGEMENT_TIME = "engagement"
    BOUNCE_RATE = "bounce"

@dataclass
class ABTest:
    """A/B test configuration"""
    id: str
    name: str
    collection_id: str
    description: str
    status: TestStatus
    variations: List[Dict[str, Any]]
    traffic_split: Dict[str, float]  # variation_name -> traffic_percentage
    test_metric: TestMetric
    confidence_level: float = 0.95
    sample_size_min: int = 100
    duration_days: int = 14
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class TestResult:
    """A/B test result data"""
    test_id: str
    variation_name: str
    total_participants: int = 0
    conversions: int = 0
    clicks: int = 0
    engagement_time: float = 0.0
    conversion_rate: float = 0.0
    click_through_rate: float = 0.0
    statistical_significance: float = 0.0
    is_winner: bool = False
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

class ABTestingFramework:
    """
    Framework for managing A/B tests on collections
    """

    def __init__(self):
        """Initialize A/B testing framework"""
        self.db_conn = None
        self.active_tests: Dict[str, ABTest] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {test_id: variation}

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

            # Load active tests
            await self._load_active_tests()

            logger.info("ABTestingFramework initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ABTestingFramework: {e}")
            return False

    async def _load_active_tests(self):
        """Load active A/B tests from database"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT id, test_name, collection_id, description, status,
                           variations, traffic_split, test_metric, confidence_level,
                           sample_size_min, duration_days, created_at, started_at, completed_at
                    FROM collection_ab_tests
                    WHERE is_active = TRUE
                """)

                for row in cur.fetchall():
                    test = ABTest(
                        id=row['id'],
                        name=row['test_name'],
                        collection_id=row['collection_id'],
                        description=row['description'],
                        status=TestStatus(row['status']),
                        variations=json.loads(row['variation_config']),
                        traffic_split=json.loads(row['traffic_split']),
                        test_metric=TestMetric(row['test_metric']),
                        confidence_level=row['confidence_level'],
                        sample_size_min=row['sample_size_min'],
                        duration_days=row['duration_days'],
                        created_at=row['created_at'],
                        started_at=row['started_at'],
                        completed_at=row['completed_at']
                    )
                    self.active_tests[test.id] = test

            logger.info(f"Loaded {len(self.active_tests)} active A/B tests")

        except Exception as e:
            logger.error(f"Failed to load active A/B tests: {e}")

    async def create_test(
        self,
        name: str,
        collection_id: str,
        description: str,
        variations: List[Dict[str, Any]],
        test_metric: TestMetric,
        confidence_level: float = 0.95,
        sample_size_min: int = 100,
        duration_days: int = 14
    ) -> Optional[str]:
        """
        Create a new A/B test

        Args:
            name: Test name
            collection_id: Collection ID to test
            description: Test description
            variations: List of test variations
            test_metric: Primary metric to optimize
            confidence_level: Statistical confidence level
            sample_size_min: Minimum sample size per variation
            duration_days: Test duration in days

        Returns:
            Test ID or None if creation fails
        """
        try:
            test_id = str(uuid.uuid4())

            # Validate variations
            if len(variations) < 2:
                raise ValueError("A/B test must have at least 2 variations")

            # Calculate equal traffic split
            traffic_split = {}
            split_percentage = 1.0 / len(variations)
            for variation in variations:
                traffic_split[variation['name']] = split_percentage

            # Create test in database
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collection_ab_tests
                    (id, test_name, collection_id, description, status,
                     variation_config, traffic_split, test_metric,
                     confidence_level, sample_size_min, duration_days)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    test_id, name, collection_id, description,
                    TestStatus.DRAFT.value,
                    json.dumps(variations),
                    json.dumps(traffic_split),
                    test_metric.value,
                    confidence_level,
                    sample_size_min,
                    duration_days
                ))

            # Create test object
            test = ABTest(
                id=test_id,
                name=name,
                collection_id=collection_id,
                description=description,
                status=TestStatus.DRAFT,
                variations=variations,
                traffic_split=traffic_split,
                test_metric=test_metric,
                confidence_level=confidence_level,
                sample_size_min=sample_size_min,
                duration_days=duration_days
            )

            self.active_tests[test_id] = test

            logger.info(f"Created A/B test: {test_id}")
            return test_id

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            return None

    async def start_test(self, test_id: str) -> bool:
        """
        Start an A/B test

        Args:
            test_id: Test ID to start

        Returns:
            True if successful, False otherwise
        """
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"Test {test_id} not found")

            test = self.active_tests[test_id]

            # Update test status
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE collection_ab_tests
                    SET status = %s, started_at = NOW()
                    WHERE id = %s
                """, (TestStatus.RUNNING.value, test_id))

            test.status = TestStatus.RUNNING
            test.started_at = datetime.utcnow()

            logger.info(f"Started A/B test: {test_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start A/B test {test_id}: {e}")
            return False

    async def assign_user_to_variation(
        self,
        user_id: str,
        test_id: str
    ) -> Optional[str]:
        """
        Assign user to A/B test variation

        Args:
            user_id: User identifier
            test_id: Test ID

        Returns:
            Variation name or None if test not found
        """
        try:
            if test_id not in self.active_tests:
                return None

            test = self.active_tests[test_id]

            # Check if user already assigned
            if user_id in self.user_assignments:
                if test_id in self.user_assignments[user_id]:
                    return self.user_assignments[user_id][test_id]

            # Consistent assignment based on user ID
            user_hash = hashlib.sha256(f"{user_id}:{test_id}".encode()).hexdigest()
            user_hash_int = int(user_hash, 16)

            # Use traffic split to determine variation
            cumulative = 0.0
            for variation_name, percentage in test.traffic_split.items():
                cumulative += percentage
                if user_hash_int / 0xFFFFFFFF < cumulative:
                    # Store assignment
                    if user_id not in self.user_assignments:
                        self.user_assignments[user_id] = {}
                    self.user_assignments[user_id][test_id] = variation_name

                    # Track assignment in database
                    await self._track_user_assignment(user_id, test_id, variation_name)

                    return variation_name

            return None

        except Exception as e:
            logger.error(f"Failed to assign user to variation: {e}")
            return None

    async def _track_user_assignment(self, user_id: str, test_id: str, variation_name: str):
        """Track user assignment in database"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collection_ab_test_assignments
                    (test_id, user_id, variation_name, assigned_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (test_id, user_id) DO UPDATE
                    SET variation_name = EXCLUDED.variation_name,
                        assigned_at = EXCLUDED.assigned_at
                """, (test_id, user_id, variation_name))

        except Exception as e:
            logger.error(f"Failed to track user assignment: {e}")

    async def track_conversion(
        self,
        user_id: str,
        test_id: str,
        event_type: str,
        value: float = 0.0
    ):
        """
        Track conversion event for A/B test

        Args:
            user_id: User identifier
            test_id: Test ID
            event_type: Type of event ('click', 'conversion', 'engagement')
            value: Event value (e.g., conversion amount)
        """
        try:
            # Get user's variation assignment
            variation = await self.assign_user_to_variation(user_id, test_id)
            if not variation:
                return

            # Track event in database
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO collection_ab_test_results
                    (test_id, user_id, variation_name, event_type, conversion_value)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (test_id, user_id, variation, event_type, value))

        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")

    async def get_test_results(self, test_id: str) -> Dict[str, TestResult]:
        """
        Get results for an A/B test

        Args:
            test_id: Test ID

        Returns:
            Dictionary of variation names to TestResult objects
        """
        try:
            if test_id not in self.active_tests:
                return {}

            test = self.active_tests[test_id]
            results = {}

            # Get results for each variation
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT variation_name,
                           COUNT(*) as total_participants,
                           COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) as conversions,
                           COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                           AVG(conversion_value) as avg_value
                    FROM collection_ab_test_results
                    WHERE test_id = %s
                    GROUP BY variation_name
                """, (test_id,))

                for row in cur.fetchall():
                    total = row['total_participants']
                    conversions = row['conversions'] or 0
                    clicks = row['clicks'] or 0

                    # Calculate metrics
                    conversion_rate = (conversions / total * 100) if total > 0 else 0
                    click_through_rate = (clicks / total * 100) if total > 0 else 0

                    # Calculate confidence interval for conversion rate
                    confidence_interval = self._calculate_confidence_interval(
                        conversions, total, test.confidence_level
                    )

                    results[row['variation_name']] = TestResult(
                        test_id=test_id,
                        variation_name=row['variation_name'],
                        total_participants=total,
                        conversions=conversions,
                        clicks=clicks,
                        conversion_rate=conversion_rate,
                        click_through_rate=click_through_rate,
                        confidence_interval=confidence_interval,
                        statistical_significance=0.0,  # Will be calculated in analysis
                        is_winner=False
                    )

            # Perform statistical analysis
            if len(results) >= 2:
                await self._analyze_test_significance(test_id, results)

            return results

        except Exception as e:
            logger.error(f"Failed to get test results: {e}")
            return {}

    async def _analyze_test_significance(self, test_id: str, results: Dict[str, TestResult]):
        """Perform statistical significance analysis"""
        try:
            test = self.active_tests[test_id]
            variation_names = list(results.keys())

            if len(variation_names) < 2:
                return

            # Compare each variation with control (first variation)
            control = results[variation_names[0]]

            for i in range(1, len(variation_names)):
                variation = results[variation_names[i]]

                # Perform statistical test based on test metric
                if test.test_metric == TestMetric.CONVERSION_RATE:
                    # Two-proportion z-test
                    stat_significance = self._two_proportion_z_test(
                        control.conversions,
                        control.total_participants,
                        variation.conversions,
                        variation.total_participants,
                        test.confidence_level
                    )
                elif test.test_metric == TestMetric.CLICK_THROUGH_RATE:
                    # Two-proportion z-test
                    stat_significance = self._two_proportion_z_test(
                        control.clicks,
                        control.total_participants,
                        variation.clicks,
                        variation.total_participants,
                        test.confidence_level
                    )
                else:
                    # Default to conversion rate test
                    stat_significance = self._two_proportion_z_test(
                        control.conversions,
                        control.total_participants,
                        variation.conversions,
                        variation.total_participants,
                        test.confidence_level
                    )

                variation.statistical_significance = stat_significance

            # Determine winner (highest conversion rate with significance)
            best_variation = max(results.values(), key=lambda x: x.conversion_rate)
            best_variation.is_winner = True

        except Exception as e:
            logger.error(f"Failed to analyze test significance: {e}")

    def _two_proportion_z_test(
        self,
        successes1: int,
        trials1: int,
        successes2: int,
        trials2: int,
        confidence_level: float
    ) -> float:
        """
        Perform two-proportion z-test

        Args:
            successes1: Conversions in variation 1
            trials1: Participants in variation 1
            successes2: Conversions in variation 2
            trials2: Participants in variation 2
            confidence_level: Desired confidence level

        Returns:
            P-value from z-test
        """
        if trials1 == 0 or trials2 == 0:
            return 1.0

        # Calculate proportions
        p1 = successes1 / trials1
        p2 = successes2 / trials2

        # Pooled proportion
        p_pooled = (successes1 + successes2) / (trials1 + trials2)

        # Standard error
        se = np.sqrt(p_pooled * (1 - p_p) * (1/trials1 + 1/trials2))

        if se == 0:
            return 1.0

        # Z-score
        z_score = abs((p1 - p2) / se)

        # P-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(z_score))

        return p_value

    def _calculate_confidence_interval(
        self,
        successes: int,
        trials: int,
        confidence_level: float
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for proportion

        Args:
            successes: Number of successes
            trials: Number of trials
            confidence_level: Desired confidence level

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if trials == 0:
            return (0.0, 0.0)

        proportion = successes / trials
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin = z_score * np.sqrt(proportion * (1 - proportion) / trials)

        return (
            max(0.0, proportion - margin),
            min(1.0, proportion + margin)
        )

    async def complete_test(self, test_id: str) -> bool:
        """
        Complete an A/B test

        Args:
            test_id: Test ID to complete

        Returns:
            True if successful, False otherwise
        """
        try:
            if test_id not in self.active_tests:
                raise ValueError(f"Test {test_id} not found")

            test = self.active_tests[test_id]

            # Update test status
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE collection_ab_tests
                    SET status = %s, completed_at = NOW(), is_active = FALSE
                    WHERE id = %s
                """, (TestStatus.COMPLETED.value, test_id))

            test.status = TestStatus.COMPLETED
            test.completed_at = datetime.utcnow()

            # Remove from active tests
            del self.active_tests[test_id]

            # Clean up user assignments
            for user_id in self.user_assignments:
                if test_id in self.user_assignments[user_id]:
                    del self.user_assignments[user_id][test_id]

            logger.info(f"Completed A/B test: {test_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to complete A/B test {test_id}: {e}")
            return False

    async def get_test_summary(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive test summary

        Args:
            test_id: Test ID

        Returns:
            Test summary dictionary or None
        """
        try:
            if test_id not in self.active_tests:
                return None

            test = self.active_tests[test_id]
            results = await self.get_test_results(test_id)

            if not results:
                return {
                    "test": test.__dict__,
                    "status": "no_data"
                }

            # Find winner
            winner = None
            for variation, result in results.items():
                if result.is_winner:
                    winner = variation
                    break

            # Calculate improvement
            baseline = results[list(results.keys())[0]]
            improvement = 0.0
            if winner and winner != baseline.variation_name:
                improvement = (
                    results[winner].conversion_rate - baseline.conversion_rate
                ) / baseline.conversion_rate * 100

            return {
                "test": test.__dict__,
                "results": {name: result.__dict__ for name, result in results.items()},
                "winner": winner,
                "improvement_percentage": improvement,
                "status": test.status.value,
                "recommendation": self._generate_recommendation(test, results)
            }

        except Exception as e:
            logger.error(f"Failed to get test summary: {e}")
            return None

    def _generate_recommendation(
        self,
        test: ABTest,
        results: Dict[str, TestResult]
    ) -> str:
        """Generate recommendation based on test results"""
        if not results:
            return "No data available for recommendation"

        # Check statistical significance
        significant_winner = None
        for variation, result in results.items():
            if result.is_winner and result.statistical_significance < 0.05:
                significant_winner = variation
                break

        if significant_winner:
            return f"Implement {significant_winner} variation - shows {results[significant_winner].improvement}% improvement with statistical significance"
        elif test.status == TestStatus.RUNNING:
            return "Test is still running - collect more data before making a decision"
        elif test.status == TestStatus.COMPLETED:
            # Check if there's a clear winner without statistical significance
            sorted_results = sorted(
                results.items(),
                key=lambda x: x[1].conversion_rate,
                reverse=True
            )
            if len(sorted_results) > 1:
                improvement = (
                    sorted_results[0][1].conversion_rate -
                    sorted_results[1][1].conversion_rate
                ) / sorted_results[1][1].conversion_rate * 100
                if improvement > 10:
                    return f"Consider implementing {sorted_results[0][0]} - shows {improvement:.1f}% improvement, but may need more data for statistical significance"

        return "Results are inconclusive - consider running test longer or with different variations"

    async def get_all_tests(self, status_filter: Optional[TestStatus] = None) -> List[Dict[str, Any]]:
        """
        Get all A/B tests with optional status filter

        Args:
            status_filter: Optional status filter

        Returns:
            List of test dictionaries
        """
        try:
            tests = []

            # Get from database
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                query = """
                    SELECT id, test_name, collection_id, description, status,
                           variation_config, traffic_split, test_metric, confidence_level,
                           sample_size_min, duration_days, created_at, started_at, completed_at, is_active
                    FROM collection_ab_tests
                """
                params = []

                if status_filter:
                    query += " WHERE status = %s"
                    params.append(status_filter.value)

                query += " ORDER BY created_at DESC"

                cur.execute(query, params)

                for row in cur.fetchall():
                    test = ABTest(
                        id=row['id'],
                        name=row['test_name'],
                        collection_id=row['collection_id'],
                        description=row['description'],
                        status=TestStatus(row['status']),
                        variations=json.loads(row['variation_config']),
                        traffic_split=json.loads(row['traffic_split']),
                        test_metric=TestMetric(row['test_metric']),
                        confidence_level=row['confidence_level'],
                        sample_size_min=row['sample_size_min'],
                        duration_days=row['duration_days'],
                        created_at=row['created_at'],
                        started_at=row['started_at'],
                        completed_at=row['completed_at']
                    )

                    # Add to active tests if needed
                    if row['is_active'] and test.id not in self.active_tests:
                        self.active_tests[test.id] = test

                    tests.append({
                        "id": test.id,
                        "name": test.name,
                        "description": test.description,
                        "status": test.status.value,
                        "collection_id": test.collection_id,
                        "variations": test.variations,
                        "test_metric": test.test_metric.value,
                        "created_at": test.created_at.isoformat(),
                        "started_at": test.started_at.isoformat() if test.started_at else None,
                        "completed_at": test.completed_at.isoformat() if test.completed_at else None
                    })

            return tests

        except Exception as e:
            logger.error(f"Failed to get all tests: {e}")
            return []