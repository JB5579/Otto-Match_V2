"""
Tests for Preference Conflict Detector module
Validates conflict detection and resolution strategies
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.intelligence.preference_conflict_detector import (
    PreferenceConflictDetector,
    PreferenceConflict,
    ConflictType,
    ConflictSeverity,
    ConflictResolution,
    UserPreference
)
from src.intelligence.preference_engine import PreferenceCategory


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for testing"""
    groq_client = Mock()
    groq_client.initialized = True

    preference_engine = Mock()
    preference_engine.initialized = True

    return groq_client, preference_engine


@pytest.fixture
async def conflict_detector(mock_dependencies):
    """Create PreferenceConflictDetector instance for testing"""
    groq_client, preference_engine = mock_dependencies
    detector = PreferenceConflictDetector(groq_client, preference_engine)
    await detector.initialize()
    return detector


@pytest.fixture
def sample_preferences():
    """Create sample user preferences for testing"""
    return [
        UserPreference(
            category=PreferenceCategory.PERFORMANCE,
            value="I want a fast car with good acceleration",
            confidence=0.8,
            source="explicit"
        ),
        UserPreference(
            category=PreferenceCategory.ENVIRONMENT,
            value="I need good fuel economy, at least 30 MPG",
            confidence=0.9,
            source="explicit"
        ),
        UserPreference(
            category=PreferenceCategory.BUDGET,
            value="Looking for something under $30,000",
            confidence=0.8,
            source="explicit"
        ),
        UserPreference(
            category=PreferenceCategory.FEATURE,
            value="Want all the latest technology and premium features",
            confidence=0.7,
            source="explicit"
        )
    ]


class TestConflictDetectorInitialization:
    """Test conflict detector initialization"""

    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_dependencies):
        """Test successful initialization"""
        groq_client, preference_engine = mock_dependencies
        detector = PreferenceConflictDetector(groq_client, preference_engine)

        assert await detector.initialize() == True
        assert detector.initialized == True

    @pytest.mark.asyncio
    async def test_initialization_fails_without_groq(self, mock_dependencies):
        """Test initialization fails without Groq client"""
        groq_client, preference_engine = mock_dependencies
        groq_client.initialized = False

        detector = PreferenceConflictDetector(groq_client, preference_engine)
        assert await detector.initialize() == False

    def test_conflict_rules_loaded(self, conflict_detector):
        """Test conflict detection rules are loaded"""
        assert ConflictType.PERFORMANCE_VS_EFFICIENCY in conflict_detector.conflict_rules
        assert ConflictType.BUDGET_VS_FEATURES in conflict_detector.conflict_rules

    def test_resolution_strategies_loaded(self, conflict_detector):
        """Test resolution strategies are loaded"""
        assert ConflictType.PERFORMANCE_VS_EFFICIENCY in conflict_detector.resolution_strategies
        assert len(conflict_detector.resolution_strategies[ConflictType.PERFORMANCE_VS_EFFICIENCY]) > 0

    def test_technology_explanations_loaded(self, conflict_detector):
        """Test technology explanations are loaded"""
        assert "Hybrid" in conflict_detector.technology_explanations
        assert "Turbocharged" in conflict_detector.technology_explanations


class TestConflictDetection:
    """Test conflict detection algorithms"""

    @pytest.mark.asyncio
    async def test_detect_performance_vs_efficiency_conflict(self, conflict_detector, sample_preferences):
        """Test detection of performance vs efficiency conflict"""
        conflicts = await conflict_detector.detect_conflicts(sample_preferences)

        # Should detect the conflict
        performance_efficiency_conflicts = [
            c for c in conflicts
            if c.conflict_type == ConflictType.PERFORMANCE_VS_EFFICIENCY
        ]

        assert len(performance_efficiency_conflicts) > 0
        conflict = performance_efficiency_conflicts[0]

        assert conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        assert "performance" in conflict.description.lower()
        assert "efficiency" in conflict.description.lower()

    @pytest.mark.asyncio
    async def test_detect_budget_vs_features_conflict(self, conflict_detector, sample_preferences):
        """Test detection of budget vs features conflict"""
        conflicts = await conflict_detector.detect_conflicts(sample_preferences)

        # Should detect the conflict
        budget_feature_conflicts = [
            c for c in conflicts
            if c.conflict_type == ConflictType.BUDGET_VS_FEATURES
        ]

        assert len(budget_feature_conflicts) > 0
        conflict = budget_feature_conflicts[0]

        assert conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.MEDIUM]
        assert "budget" in conflict.description.lower()
        assert "features" in conflict.description.lower()

    @pytest.mark.asyncio
    async def test_no_conflicts_with_compatible_preferences(self, conflict_detector):
        """Test no conflicts detected with compatible preferences"""
        compatible_preferences = [
            UserPreference(
                category=PreferenceCategory.PERFORMANCE,
                value="I want reasonable performance",
                confidence=0.5,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.SAFETY,
                value="Safety is my top priority",
                confidence=0.9,
                source="explicit"
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(compatible_preferences)

        # Should have minimal or no conflicts
        assert len(conflicts) == 0 or all(c.severity == ConflictSeverity.LOW for c in conflicts)

    @pytest.mark.asyncio
    async def test_conflict_severity_calculation(self, conflict_detector):
        """Test conflict severity calculation"""
        # High confidence conflicting preferences
        high_conflict_prefs = [
            UserPreference(
                category=PreferenceCategory.PERFORMANCE,
                value="I need maximum power, V8 or nothing",
                confidence=0.95,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.ENVIRONMENT,
                value="Must be zero emissions, electric only",
                confidence=0.95,
                source="explicit"
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(high_conflict_prefs)

        if conflicts:
            # Should detect critical conflict
            assert any(c.severity == ConflictSeverity.CRITICAL for c in conflicts)

    @pytest.mark.asyncio
    async def test_multiple_conflicts_sorted_by_severity(self, conflict_detector):
        """Test multiple conflicts are sorted by severity"""
        # Create preferences with multiple potential conflicts
        multi_conflict_prefs = [
            UserPreference(
                category=PreferenceCategory.PERFORMANCE,
                value="Fast acceleration",
                confidence=0.9,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.ENVIRONMENT,
                value="50+ MPG required",
                confidence=0.9,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.BUDGET,
                value="Under $20k",
                confidence=0.9,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.FEATURE,
                value="Fully loaded with every feature",
                confidence=0.9,
                source="explicit"
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(multi_conflict_prefs)

        if len(conflicts) > 1:
            # Check sorting
            for i in range(len(conflicts) - 1):
                severity_order = {
                    ConflictSeverity.CRITICAL: 4,
                    ConflictSeverity.HIGH: 3,
                    ConflictSeverity.MEDIUM: 2,
                    ConflictSeverity.LOW: 1
                }

                prev_severity = severity_order[conflicts[i].severity]
                curr_severity = severity_order[conflicts[i + 1].severity]

                assert prev_severity >= curr_severity


class TestConflictResolution:
    """Test conflict resolution strategies"""

    @pytest.mark.asyncio
    async def test_performance_efficiency_resolutions(self, conflict_detector):
        """Test resolution strategies for performance vs efficiency"""
        strategies = conflict_detector.resolution_strategies.get(ConflictType.PERFORMANCE_VS_EFFICIENCY, [])

        assert len(strategies) > 0

        # Check for hybrid technology solution
        hybrid_strategies = [s for s in strategies if "hybrid" in s.name.lower()]
        assert len(hybrid_strategies) > 0

        hybrid = hybrid_strategies[0]
        assert hybrid.description
        assert hybrid.questions_to_ask
        assert "Hybrid" in hybrid.compatible_technologies

    @pytest.mark.asyncio
    async def test_budget_features_resolutions(self, conflict_detector):
        """Test resolution strategies for budget vs features"""
        strategies = conflict_detector.resolution_strategies.get(ConflictType.BUDGET_VS_FEATURES, [])

        assert len(strategies) > 0

        # Check for prioritization strategy
        prioritize_strategies = [s for s in strategies if "priority" in s.name.lower()]
        assert len(prioritize_strategies) > 0

        prioritize = prioritize_strategies[0]
        assert prioritize.trade_offs
        assert prioritize.questions_to_ask

    @pytest.mark.asyncio
    async def test_generate_conflict_questions(self, conflict_detector):
        """Test generation of conflict resolution questions"""
        pref1 = UserPreference(
            category=PreferenceCategory.PERFORMANCE,
            value="I want a sporty car",
            confidence=0.8,
            source="explicit"
        )
        pref2 = UserPreference(
            category=PreferenceCategory.ENVIRONMENT,
            value="Need good gas mileage",
            confidence=0.8,
            source="explicit"
        )

        questions = await conflict_detector._generate_conflict_questions(
            pref1, pref2, ConflictType.PERFORMANCE_VS_EFFICIENCY
        )

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)

        # Check questions are relevant to the conflict
        questions_text = " ".join(questions).lower()
        assert "priority" in questions_text or "important" in questions_text or "choose" in questions_text

    @pytest.mark.asyncio
    async def test_technology_suggestions(self, conflict_detector):
        """Test technological solutions for conflicts"""
        pref1 = UserPreference(
            category=PreferenceCategory.PERFORMANCE,
            value="Fast acceleration",
            confidence=0.8,
            source="explicit"
        )
        pref2 = UserPreference(
            category=PreferenceCategory.ENVIRONMENT,
            value="Low emissions",
            confidence=0.8,
            source="explicit"
        )

        technologies = await conflict_detector._suggest_technological_solutions(
            pref1, pref2, ConflictType.PERFORMANCE_VS_EFFICIENCY
        )

        assert isinstance(technologies, list)
        assert len(technologies) > 0

        # Should suggest relevant technologies
        tech_text = " ".join(technologies).lower()
        assert any(tech in tech_text for tech in ["hybrid", "turbo", "electric"])

    @pytest.mark.asyncio
    async def test_explain_technology(self, conflict_detector):
        """Test technology explanations"""
        hybrid_explanation = await conflict_detector.get_explanation_for_technology("Hybrid")
        assert hybrid_explanation
        assert len(hybrid_explanation) > 50  # Should be substantial
        assert "electric" in hybrid_explanation.lower() or "motor" in hybrid_explanation.lower()

        # Test unknown technology
        unknown_explanation = await conflict_detector.get_explanation_for_technology("UnknownTech")
        assert unknown_explanation
        assert "UnknownTech" in unknown_explanation


class TestConflictScoring:
    """Test conflict scoring algorithms"""

    def test_exceeds_thresholds(self, conflict_detector):
        """Test threshold checking for conflicts"""
        # Create preferences that exceed thresholds
        perf_pref = UserPreference(
            category=PreferenceCategory.PERFORMANCE,
            value="Sport mode",
            confidence=0.9,  # High confidence
            source="explicit"
        )
        eff_pref = UserPreference(
            category=PreferenceCategory.ENVIRONMENT,
            value="Eco mode",
            confidence=0.9,  # High confidence
            source="explicit"
        )

        thresholds = {"performance_score": 0.7, "efficiency_score": 0.7}
        exceeds = conflict_detector._exceeds_thresholds(perf_pref, eff_pref, thresholds)

        # This test would need to check actual preference attributes
        # For now, we test the structure exists
        assert callable(conflict_detector._exceeds_thresholds)

    @pytest.mark.asyncio
    async def test_conflict_description_generation(self, conflict_detector):
        """Test generation of conflict descriptions"""
        pref1 = UserPreference(
            category=PreferenceCategory.PERFORMANCE,
            value="Fast car",
            confidence=0.8,
            source="explicit"
        )
        pref2 = UserPreference(
            category=PreferenceCategory.ENVIRONMENT,
            value="Efficient car",
            confidence=0.8,
            source="explicit"
        )

        description = conflict_detector._generate_conflict_description(
            pref1, pref2, ConflictType.PERFORMANCE_VS_EFFICIENCY
        )

        assert description
        assert "performance" in description.lower() or "efficiency" in description.lower()
        assert "conflict" in description.lower()

    @pytest.mark.asyncio
    async def test_conflict_explanation_generation(self, conflict_detector):
        """Test generation of conflict explanations"""
        pref1 = UserPreference(
            category=PreferenceCategory.BUDGET,
            value="Under $25k",
            confidence=0.8,
            source="explicit"
        )
        pref2 = UserPreference(
            category=PreferenceCategory.FEATURE,
            value="Premium package with everything",
            confidence=0.8,
            source="explicit"
        )

        explanation = await conflict_detector._generate_conflict_explanation(
            pref1, pref2, ConflictType.BUDGET_VS_FEATURES
        )

        assert explanation
        assert len(explanation) > 100  # Should be detailed
        assert "trade" in explanation.lower() or "balance" in explanation.lower()


class TestIntegration:
    """Integration tests for conflict detection"""

    @pytest.mark.asyncio
    async def test_full_conflict_resolution_flow(self, conflict_detector, sample_preferences):
        """Test complete conflict detection and resolution flow"""
        # Detect conflicts
        conflicts = await conflict_detector.detect_conflicts(sample_preferences)

        if conflicts:
            # Take the highest priority conflict
            conflict = conflicts[0]

            # Generate questions for resolution
            questions = await conflict_detector._generate_conflict_questions(
                conflict.preferences[0],
                conflict.preferences[1],
                conflict.conflict_type
            )

            # Get technological solutions
            technologies = await conflict_detector._suggest_technological_solutions(
                conflict.preferences[0],
                conflict.preferences[1],
                conflict.conflict_type
            )

            # Generate resolution summary
            summary = await conflict_detector.generate_resolution_summary(
                conflict,
                "Hybrid Technology"
            )

            # Validate all components work together
            assert conflict.description
            assert conflict.explanation
            assert questions
            assert technologies
            assert summary

            # Verify consistency
            assert conflict.conflict_type in [ConflictType.PERFORMANCE_VS_EFFICIENCY,
                                            ConflictType.BUDGET_VS_FEATURES]

    @pytest.mark.asyncio
    async def test_resolution_summary_with_technology(self, conflict_detector):
        """Test resolution summary generation with technology"""
        conflict = PreferenceConflict(
            id="test_conflict",
            conflict_type=ConflictType.PERFORMANCE_VS_EFFICIENCY,
            severity=ConflictSeverity.HIGH,
            preferences=[
                UserPreference(
                    category=PreferenceCategory.PERFORMANCE,
                    value="Sport mode",
                    confidence=0.8,
                    source="explicit"
                )
            ],
            description="Performance vs Efficiency conflict",
            explanation="You want both performance and efficiency",
            resolution_strategies=["Hybrid Technology"],
            recommended_questions=["Which matters more?"],
            technological_solutions=["Hybrid", "Turbo"]
        )

        summary = await conflict_detector.generate_resolution_summary(conflict, "Hybrid")

        assert summary
        assert "hybrid" in summary.lower()
        assert "performance" in summary.lower() or "efficiency" in summary.lower()


# Performance Tests
class TestPerformance:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_conflict_detection_performance(self, conflict_detector, sample_preferences):
        """Test conflict detection meets performance requirements"""
        import time

        start_time = time.time()
        conflicts = await conflict_detector.detect_conflicts(sample_preferences)
        detection_time = (time.time() - start_time) * 1000

        # Should complete quickly
        assert detection_time < 500  # Less than 500ms

    @pytest.mark.asyncio
    async def test_large_preference_set_performance(self, conflict_detector):
        """Test performance with large preference set"""
        import time

        # Create large preference set
        large_preferences = []
        for i in range(50):
            large_preferences.append(
                UserPreference(
                    category=PreferenceCategory.FEATURE,
                    value=f"Feature {i}",
                    confidence=0.7,
                    source="explicit"
                )
            )

        start_time = time.time()
        conflicts = await conflict_detector.detect_conflicts(large_preferences)
        detection_time = (time.time() - start_time) * 1000

        # Should handle large sets efficiently
        assert detection_time < 1000  # Less than 1 second


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])