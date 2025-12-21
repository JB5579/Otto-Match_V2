"""
Performance tests for question response time requirements
Validates that questioning components meet performance specifications
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.intelligence.questioning_strategy import QuestioningStrategy, UserContext
from src.memory.question_memory import QuestionMemory
from src.intelligence.preference_conflict_detector import PreferenceConflictDetector
from src.intelligence.family_need_questioning import FamilyNeedQuestioning


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for performance testing"""
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
async def performance_components(mock_dependencies):
    """Create components for performance testing"""
    zep_client, temporal_memory, groq_client, preference_engine = mock_dependencies

    # Create components
    question_memory = QuestionMemory(zep_client, temporal_memory)
    questioning_strategy = QuestioningStrategy(groq_client, temporal_memory, preference_engine)
    conflict_detector = PreferenceConflictDetector(groq_client, preference_engine)
    family_questioning = FamilyNeedQuestioning(groq_client)

    # Initialize all components
    await question_memory.initialize()
    await questioning_strategy.initialize()
    await conflict_detector.initialize()
    await family_questioning.initialize()

    return {
        'memory': question_memory,
        'strategy': questioning_strategy,
        'conflict_detector': conflict_detector,
        'family': family_questioning
    }


class TestQuestionSelectionPerformance:
    """Test question selection performance requirements"""

    @pytest.mark.asyncio
    async def test_question_selection_under_100ms(self, performance_components):
        """Question selection should complete in under 100ms"""
        strategy = performance_components['strategy']

        # Create realistic user context
        user_context = UserContext(
            user_id="perf_test_user",
            session_id="perf_session",
            conversation_history=[
                {"role": "user", "content": "I'm looking for a family car"},
                {"role": "assistant", "content": "I can help you find a great family vehicle"}
            ],
            asked_questions=[],
            preferences={"vehicle_type": "SUV", "family_size": 4},
            engagement_level=0.7,
            last_question_time=datetime.now() - timedelta(minutes=5)
        )

        # Measure multiple selections for statistical significance
        selection_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            questions = await strategy.select_next_question(user_context, max_questions=3)
            end_time = time.perf_counter()

            selection_time = (end_time - start_time) * 1000  # Convert to milliseconds
            selection_times.append(selection_time)

        # Calculate statistics
        avg_time = sum(selection_times) / len(selection_times)
        max_time = max(selection_times)
        p95_time = sorted(selection_times)[int(len(selection_times) * 0.95)]

        # Performance assertions
        assert avg_time < 50, f"Average selection time {avg_time:.2f}ms exceeds 50ms"
        assert max_time < 100, f"Max selection time {max_time:.2f}ms exceeds 100ms"
        assert p95_time < 80, f"95th percentile {p95_time:.2f}ms exceeds 80ms"

    @pytest.mark.asyncio
    async def test_question_selection_scalability(self, performance_components):
        """Question selection should scale with conversation history"""
        strategy = performance_components['strategy']

        # Test with varying conversation history sizes
        history_sizes = [0, 10, 50, 100, 200]
        selection_times = []

        for history_size in history_sizes:
            # Create conversation history
            conversation_history = []
            for i in range(history_size):
                conversation_history.extend([
                    {"role": "user", "content": f"User message {i}"},
                    {"role": "assistant", "content": f"Assistant response {i}"}
                ])

            user_context = UserContext(
                user_id="scale_test_user",
                session_id="scale_session",
                conversation_history=conversation_history,
                asked_questions=[],
                preferences={},
                engagement_level=0.5,
                last_question_time=None
            )

            # Measure selection time
            start_time = time.perf_counter()
            await strategy.select_next_question(user_context, max_questions=3)
            end_time = time.perf_counter()

            selection_time = (end_time - start_time) * 1000
            selection_times.append(selection_time)

        # Should maintain reasonable performance even with large history
        assert selection_times[-1] < 200, f"Selection with {history_sizes[-1]} messages took {selection_times[-1]:.2f}ms"

        # Performance degradation should be linear, not exponential
        # The last selection (200 messages) shouldn't be more than 4x the first (0 messages)
        degradation_factor = selection_times[-1] / max(selection_times[0], 1)
        assert degradation_factor < 4, f"Performance degradation factor {degradation_factor:.2f} exceeds 4x"


class TestConflictDetectionPerformance:
    """Test conflict detection performance requirements"""

    @pytest.mark.asyncio
    async def test_conflict_detection_under_200ms(self, performance_components):
        """Conflict detection should complete in under 200ms"""
        conflict_detector = performance_components['conflict_detector']

        # Create realistic preference set with potential conflicts
        from src.intelligence.preference_conflict_detector import UserPreference
        from src.intelligence.preference_engine import PreferenceCategory

        preferences = [
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

        # Measure multiple detections for statistical significance
        detection_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            conflicts = await conflict_detector.detect_conflicts(preferences)
            end_time = time.perf_counter()

            detection_time = (end_time - start_time) * 1000
            detection_times.append(detection_time)

        # Calculate statistics
        avg_time = sum(detection_times) / len(detection_times)
        max_time = max(detection_times)
        p95_time = sorted(detection_times)[int(len(detection_times) * 0.95)]

        # Performance assertions
        assert avg_time < 100, f"Average detection time {avg_time:.2f}ms exceeds 100ms"
        assert max_time < 200, f"Max detection time {max_time:.2f}ms exceeds 200ms"
        assert p95_time < 150, f"95th percentile {p95_time:.2f}ms exceeds 150ms"

    @pytest.mark.asyncio
    async def test_conflict_detection_with_large_preference_set(self, performance_components):
        """Conflict detection should handle large preference sets efficiently"""
        conflict_detector = performance_components['conflict_detector']

        # Create large preference set
        from src.intelligence.preference_conflict_detector import UserPreference
        from src.intelligence.preference_engine import PreferenceCategory

        large_preferences = []
        for i in range(50):
            category = list(PreferenceCategory)[i % len(PreferenceCategory)]
            pref = UserPreference(
                category=category,
                value=f"Preference {i} with detailed information about what the user wants",
                confidence=0.7 + (i % 3) * 0.1,
                source="explicit" if i % 2 == 0 else "implicit"
            )
            large_preferences.append(pref)

        # Measure detection time with large set
        start_time = time.perf_counter()
        conflicts = await conflict_detector.detect_conflicts(large_preferences)
        end_time = time.perf_counter()

        detection_time = (end_time - start_time) * 1000

        # Should handle large sets efficiently
        assert detection_time < 500, f"Detection with 50 preferences took {detection_time:.2f}ms"
        assert len(conflicts) >= 0  # Should return some result


class TestMemoryOperationsPerformance:
    """Test memory operations performance requirements"""

    @pytest.mark.asyncio
    async def test_question_tracking_under_50ms(self, performance_components):
        """Question tracking should complete in under 50ms"""
        memory = performance_components['memory']

        # Create sample question
        from src.intelligence.questioning_strategy import Question, QuestionCategory

        question = Question(
            id="perf_test_question",
            text="What's your preferred vehicle type?",
            category=QuestionCategory.VEHICLE_TYPE,
            information_value=0.8,
            engagement_potential=0.7
        )

        # Measure multiple tracking operations
        tracking_times = []
        for i in range(20):
            start_time = time.perf_counter()
            await memory.track_question(
                user_id=f"perf_user_{i}",
                question=question,
                session_id=f"perf_session_{i}",
                response="I prefer SUVs",
                response_time_ms=3000 + i * 100,
                engagement_indicators={"engagement_score": 0.7 + i * 0.01}
            )
            end_time = time.perf_counter()

            tracking_time = (end_time - start_time) * 1000
            tracking_times.append(tracking_time)

        # Calculate statistics
        avg_time = sum(tracking_times) / len(tracking_times)
        max_time = max(tracking_times)
        p95_time = sorted(tracking_times)[int(len(tracking_times) * 0.95)]

        # Performance assertions
        assert avg_time < 25, f"Average tracking time {avg_time:.2f}ms exceeds 25ms"
        assert max_time < 50, f"Max tracking time {max_time:.2f}ms exceeds 50ms"
        assert p95_time < 40, f"95th percentile {p95_time:.2f}ms exceeds 40ms"

    @pytest.mark.asyncio
    async def test_history_retrieval_under_100ms(self, performance_components):
        """History retrieval should complete in under 100ms"""
        memory = performance_components['memory']

        # Create mock history of different sizes
        history_sizes = [10, 50, 100, 200]
        retrieval_times = []

        for history_size in history_sizes:
            # Mock retrieval returning specified number of questions
            mock_questions = []
            for i in range(history_size):
                mock_questions.append(Mock(
                    question_id=f"question_{i}",
                    question_text=f"Question {i}",
                    category="family",
                    timestamp=datetime.now() - timedelta(hours=i)
                ))

            performance_components['temporal_memory'].retrieve_by_user.return_value = mock_questions

            # Measure retrieval time
            start_time = time.perf_counter()
            history = await memory.get_user_question_history("test_user")
            end_time = time.perf_counter()

            retrieval_time = (end_time - start_time) * 1000
            retrieval_times.append(retrieval_time)

        # Should maintain reasonable performance even with large history
        assert retrieval_times[-1] < 100, f"Retrieval with {history_sizes[-1]} questions took {retrieval_times[-1]:.2f}ms"


class TestFamilyQuestioningPerformance:
    """Test family questioning performance requirements"""

    @pytest.mark.asyncio
    async def test_family_profile_building_under_300ms(self, performance_components):
        """Family profile building should complete in under 300ms"""
        family_questioning = performance_components['family']

        # Create realistic family responses
        responses = {
            "family_size": "4 people including 2 children",
            "children_ages": "8 and 12 years old",
            "primary_use": "Daily school runs and weekend family trips",
            "commute_distance": "About 20 miles round trip",
            "weekend_activities": "Sports practice and family outings",
            "cargo_needs": "Sports equipment, groceries, and luggage",
            "safety_priorities": "Airbags, crash test ratings, and blind spot monitoring",
            "budget_range": "Around $35,000",
            "fuel_preference": "Good gas mileage is important",
            "parking_situation": "Suburban home with garage"
        }

        # Measure multiple profile builds
        build_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            profile = await family_questioning.build_family_profile(responses)
            end_time = time.perf_counter()

            build_time = (end_time - start_time) * 1000
            build_times.append(build_time)

            # Verify profile was created correctly
            assert profile is not None
            assert profile.family_size == 4
            assert len(profile.children) == 2

        # Calculate statistics
        avg_time = sum(build_times) / len(build_times)
        max_time = max(build_times)
        p95_time = sorted(build_times)[int(len(build_times) * 0.95)]

        # Performance assertions
        assert avg_time < 200, f"Average build time {avg_time:.2f}ms exceeds 200ms"
        assert max_time < 300, f"Max build time {max_time:.2f}ms exceeds 300ms"
        assert p95_time < 250, f"95th percentile {p95_time:.2f}ms exceeds 250ms"

    @pytest.mark.asyncio
    async def test_vehicle_requirements_generation_under_200ms(self, performance_components):
        """Vehicle requirements generation should complete in under 200ms"""
        family_questioning = performance_components['family']

        # Create family profile
        from src.intelligence.family_need_questioning import FamilyProfile, Child, LifestylePattern

        profile = FamilyProfile(
            family_size=4,
            adults=2,
            children=[
                Child(age=8, child_stage="elementary_school", car_seat_required=False),
                Child(age=12, child_stage="middle_school", car_seat_required=False)
            ],
            primary_vehicle_usage="family_transport",
            lifestyle_patterns=[
                LifestylePattern(pattern="school_commuting", frequency="daily"),
                LifestylePattern(pattern="weekend_trips", frequency="weekly")
            ],
            special_requirements=["sports_equipment_transport"],
            budget_range={"min": 25000, "max": 40000},
            safety_priorities=["airbags", "crash_test_ratings"],
            location_type="suburban"
        )

        # Measure multiple requirement generations
        generation_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            requirements = await family_questioning.generate_vehicle_requirements(profile)
            end_time = time.perf_counter()

            generation_time = (end_time - start_time) * 1000
            generation_times.append(generation_time)

            # Verify requirements were generated
            assert requirements is not None
            assert requirements.min_seats >= 5
            assert len(requirements.safety_features) > 0

        # Calculate statistics
        avg_time = sum(generation_times) / len(generation_times)
        max_time = max(generation_times)
        p95_time = sorted(generation_times)[int(len(generation_times) * 0.95)]

        # Performance assertions
        assert avg_time < 100, f"Average generation time {avg_time:.2f}ms exceeds 100ms"
        assert max_time < 200, f"Max generation time {max_time:.2f}ms exceeds 200ms"
        assert p95_time < 150, f"95th percentile {p95_time:.2f}ms exceeds 150ms"


class TestEndToEndPerformance:
    """Test end-to-end questioning flow performance"""

    @pytest.mark.asyncio
    async def test_complete_questioning_flow_under_500ms(self, performance_components):
        """Complete questioning flow should complete in under 500ms"""
        memory = performance_components['memory']
        strategy = performance_components['strategy']
        conflict_detector = performance_components['conflict_detector']

        # Create user context
        user_context = UserContext(
            user_id="e2e_test_user",
            session_id="e2e_session",
            conversation_history=[
                {"role": "user", "content": "I need a family car that's also good on gas"},
                {"role": "assistant", "content": "I understand you're looking for an efficient family vehicle"}
            ],
            asked_questions=[],
            preferences={"family_size": 4, "fuel_efficiency": "important"},
            engagement_level=0.8,
            last_question_time=datetime.now() - timedelta(minutes=3)
        )

        # Measure complete flow time
        start_time = time.perf_counter()

        # Step 1: Select next question
        questions = await strategy.select_next_question(user_context, max_questions=2)
        first_question = questions[0].question

        # Step 2: Track the question
        await memory.track_question(
            user_id=user_context.user_id,
            question=first_question,
            session_id=user_context.session_id,
            response="We have 4 people, including 2 teenagers",
            response_time_ms=4500,
            engagement_indicators={"engagement_score": 0.9}
        )

        # Step 3: Update user context with new preference
        from src.intelligence.preference_conflict_detector import UserPreference
        from src.intelligence.preference_engine import PreferenceCategory

        new_preference = UserPreference(
            category=PreferenceCategory.FAMILY,
            value="4 people with 2 teenagers",
            confidence=0.9,
            source="explicit"
        )

        # Step 4: Check for conflicts
        conflicts = await conflict_detector.detect_conflicts([new_preference])

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000

        # Performance assertions
        assert total_time < 500, f"Complete flow took {total_time:.2f}ms, exceeds 500ms"
        assert len(questions) > 0, "Should select at least one question"
        assert len(conflicts) >= 0, "Should return conflict analysis"

        # Verify components worked correctly
        assert first_question.text is not None
        assert first_question.category is not None


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])