"""
Integration tests for questioning modules
Tests the complete flow between questioning components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.memory.question_memory import QuestionMemory, QuestionRecord, QuestionStatus
from src.intelligence.questioning_strategy import QuestioningStrategy, Question, QuestionCategory
from src.intelligence.preference_conflict_detector import PreferenceConflictDetector


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for integration testing"""
    zep_client = Mock()
    zep_client.initialized = True

    temporal_memory = Mock()
    temporal_memory.initialized = True
    temporal_memory.store_memory = AsyncMock()
    temporal_memory.retrieve_by_user = AsyncMock(return_value=[])
    temporal_memory.retrieve_by_pattern = AsyncMock(return_value=[])

    groq_client = Mock()
    groq_client.initialized = True
    groq_client.generate_response = AsyncMock(return_value="Mock response")

    preference_engine = Mock()
    preference_engine.initialized = True
    preference_engine.update_preference = AsyncMock()
    preference_engine.get_preferences = AsyncMock(return_value=[])

    return zep_client, temporal_memory, groq_client, preference_engine


@pytest.fixture
async def integrated_components(mock_dependencies):
    """Create integrated questioning components"""
    zep_client, temporal_memory, groq_client, preference_engine = mock_dependencies

    # Create components
    question_memory = QuestionMemory(zep_client, temporal_memory)
    questioning_strategy = QuestioningStrategy(groq_client, temporal_memory, preference_engine)
    conflict_detector = PreferenceConflictDetector(groq_client, preference_engine)

    # Initialize all components
    await question_memory.initialize()
    await questioning_strategy.initialize()
    await conflict_detector.initialize()

    return {
        'memory': question_memory,
        'strategy': questioning_strategy,
        'conflict_detector': conflict_detector,
        'temporal_memory': temporal_memory,
        'groq_client': groq_client,
        'preference_engine': preference_engine
    }


class TestQuestioningIntegration:
    """Test integration between questioning modules"""

    @pytest.mark.asyncio
    async def test_question_selection_with_memory_tracking(self, integrated_components):
        """Test that questions selected are properly tracked in memory"""
        memory = integrated_components['memory']
        strategy = integrated_components['strategy']
        user_id = "test_user"

        # Create user context
        from src.intelligence.questioning_strategy import UserContext
        user_context = UserContext(
            user_id=user_id,
            session_id="session_123",
            conversation_history=[],
            asked_questions=[],
            preferences={},
            engagement_level=0.7,
            last_question_time=None
        )

        # Select questions
        questions = await strategy.select_next_question(user_context, max_questions=3)

        # Should return some questions
        assert len(questions) > 0

        # Track the first question
        first_question_score = questions[0]
        await memory.track_question(
            user_id=user_id,
            question=first_question_score.question,
            session_id="session_123",
            response="I need space for 4 people",
            response_time_ms=5000,
            engagement_indicators={"engagement_score": 0.8}
        )

        # Verify question was tracked
        was_asked = await memory.has_question_been_asked(user_id, first_question_score.question.id)
        assert was_asked == True

    @pytest.mark.asyncio
    async def test_conflict_detection_with_questioning_flow(self, integrated_components):
        """Test conflict detection integration with questioning strategy"""
        conflict_detector = integrated_components['conflict_detector']
        preference_engine = integrated_components['preference_engine']

        # Mock conflicting preferences
        from src.intelligence.preference_conflict_detector import UserPreference
        from src.intelligence.preference_engine import PreferenceCategory

        conflicting_prefs = [
            UserPreference(
                category=PreferenceCategory.PERFORMANCE,
                value="I want a fast sports car",
                confidence=0.9,
                source="explicit"
            ),
            UserPreference(
                category=PreferenceCategory.ENVIRONMENT,
                value="I need 50+ MPG fuel efficiency",
                confidence=0.9,
                source="explicit"
            )
        ]

        # Detect conflicts
        conflicts = await conflict_detector.detect_conflicts(conflicting_prefs)

        # Should detect performance vs efficiency conflict
        assert len(conflicts) > 0
        assert any("performance" in conflict.description.lower() for conflict in conflicts)

        # Should provide resolution strategies
        for conflict in conflicts:
            assert len(conflict.resolution_strategies) > 0
            assert len(conflict.recommended_questions) > 0

    @pytest.mark.asyncio
    async def test_cross_session_question_avoidance(self, integrated_components):
        """Test that questions from previous sessions are avoided"""
        memory = integrated_components['memory']
        strategy = integrated_components['strategy']
        user_id = "test_user"

        # Mock previous question asked
        previous_question = Question(
            id="family_size",
            text="How many people are in your family?",
            category=QuestionCategory.FAMILY,
            information_value=0.9,
            engagement_potential=0.8
        )

        # Track previous question
        await memory.track_question(
            user_id=user_id,
            question=previous_question,
            session_id="previous_session",
            response="4 people",
            response_time_ms=3000
        )

        # Create user context
        from src.intelligence.questioning_strategy import UserContext
        user_context = UserContext(
            user_id=user_id,
            session_id="current_session",
            conversation_history=[],
            asked_questions=[],
            preferences={},
            engagement_level=0.7,
            last_question_time=None
        )

        # Select questions
        questions = await strategy.select_next_question(user_context, max_questions=5)

        # Should not include the previously asked question
        question_ids = [q.question.id for q in questions]
        assert previous_question.id not in question_ids

    @pytest.mark.asyncio
    async def test_question_effectiveness_feedback_loop(self, integrated_components):
        """Test that question effectiveness feeds back into selection"""
        memory = integrated_components['memory']
        strategy = integrated_components['strategy']
        user_id = "test_user"

        # Create a sample question
        question = Question(
            id="budget_range",
            text="What's your budget range?",
            category=QuestionCategory.BUDGET,
            information_value=0.8,
            engagement_potential=0.7
        )

        # Track question with high effectiveness
        await memory.track_question(
            user_id=user_id,
            question=question,
            session_id="session_123",
            response="Around $30,000",
            response_time_ms=4000,
            effectiveness_score=0.9,
            engagement_indicators={"engagement_score": 0.9}
        )

        # Get effectiveness for the question
        effectiveness = await memory.get_question_effectiveness(user_id, question.id)

        # Should track effectiveness correctly
        assert effectiveness is not None
        assert effectiveness > 0.8

    @pytest.mark.asyncio
    async def test_family_need_questioning_integration(self, integrated_components):
        """Test family need questioning integration with memory"""
        from src.intelligence.family_need_questioning import FamilyNeedQuestioning
        from src.intelligence.family_need_questioning import FamilyProfile, VehicleRequirements

        # Create family need questioning module
        family_questioning = FamilyNeedQuestioning(integrated_components['groq_client'])
        await family_questioning.initialize()

        # Mock family responses
        responses = {
            "family_size": "4",
            "children_ages": "8 and 12",
            "primary_use": "school runs and family trips",
            "cargo_needs": "sports equipment and groceries",
            "safety_priorities": "crash test ratings and blind spot detection"
        }

        # Build family profile
        profile = await family_questioning.build_family_profile(responses)

        # Should create valid profile
        assert profile is not None
        assert profile.family_size == 4
        assert len(profile.children) == 2

        # Generate vehicle requirements
        requirements = await family_questioning.generate_vehicle_requirements(profile)

        # Should generate appropriate requirements
        assert requirements.min_seats >= 5
        assert requirements.safety_features is not None
        assert len(requirements.safety_features) > 0


class TestQuestioningPerformance:
    """Test performance of questioning components"""

    @pytest.mark.asyncio
    async def test_question_selection_latency(self, integrated_components):
        """Test question selection meets latency requirements"""
        strategy = integrated_components['strategy']

        # Create user context
        from src.intelligence.questioning_strategy import UserContext
        user_context = UserContext(
            user_id="perf_test_user",
            session_id="perf_session",
            conversation_history=[],
            asked_questions=[],
            preferences={},
            engagement_level=0.7,
            last_question_time=None
        )

        # Measure selection time
        start_time = datetime.now()
        questions = await strategy.select_next_question(user_context, max_questions=3)
        selection_time = (datetime.now() - start_time).total_seconds() * 1000

        # Should complete quickly (< 100ms)
        assert selection_time < 100
        assert len(questions) > 0

    @pytest.mark.asyncio
    async def test_conflict_detection_latency(self, integrated_components):
        """Test conflict detection meets latency requirements"""
        conflict_detector = integrated_components['conflict_detector']

        # Create large preference set
        from src.intelligence.preference_conflict_detector import UserPreference
        from src.intelligence.preference_engine import PreferenceCategory

        large_prefs = []
        for i in range(20):
            category = list(PreferenceCategory)[i % len(PreferenceCategory)]
            pref = UserPreference(
                category=category,
                f"Preference {i}",
                0.8,
                "explicit"
            )
            large_prefs.append(pref)

        # Measure detection time
        start_time = datetime.now()
        conflicts = await conflict_detector.detect_conflicts(large_prefs)
        detection_time = (datetime.now() - start_time).total_seconds() * 1000

        # Should complete quickly (< 200ms)
        assert detection_time < 200

    @pytest.mark.asyncio
    async def test_memory_operations_latency(self, integrated_components):
        """Test memory operations meet latency requirements"""
        memory = integrated_components['memory']

        # Create sample question
        from src.intelligence.questioning_strategy import Question, QuestionCategory
        question = Question(
            id="perf_test_question",
            text="Performance test question",
            category=QuestionCategory.BUDGET,
            information_value=0.8,
            engagement_potential=0.7
        )

        # Measure tracking time
        start_time = datetime.now()
        await memory.track_question(
            user_id="perf_user",
            question=question,
            session_id="perf_session",
            response="Test response",
            response_time_ms=1000
        )
        tracking_time = (datetime.now() - start_time).total_seconds() * 1000

        # Should complete quickly (< 50ms)
        assert tracking_time < 50

        # Measure retrieval time
        start_time = datetime.now()
        history = await memory.get_user_question_history("perf_user")
        retrieval_time = (datetime.now() - start_time).total_seconds() * 1000

        # Should complete quickly (< 100ms)
        assert retrieval_time < 100
        assert len(history) > 0


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])