"""
Tests for Question Memory module
Validates question tracking across sessions using Zep Cloud
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.memory.question_memory import (
    QuestionMemory,
    QuestionRecord,
    QuestionStatus,
    PreferenceEvolution,
    UserContext
)
from src.memory.temporal_memory import MemoryType, MemoryFragment
from src.intelligence.questioning_strategy import Question, QuestionCategory, QuestionComplexity


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for testing"""
    zep_client = Mock()
    zep_client.initialized = True

    temporal_memory = Mock()
    temporal_memory.initialized = True
    temporal_memory.store_memory = AsyncMock()
    temporal_memory.retrieve_by_user = AsyncMock()
    temporal_memory.retrieve_by_pattern = AsyncMock()

    return zep_client, temporal_memory


@pytest.fixture
async def question_memory(mock_dependencies):
    """Create QuestionMemory instance for testing"""
    zep_client, temporal_memory = mock_dependencies
    memory = QuestionMemory(zep_client, temporal_memory)
    await memory.initialize()
    return memory


@pytest.fixture
def sample_question():
    """Create sample question for testing"""
    return Question(
        id="family_size",
        text="How many people are in your family?",
        category=QuestionCategory.FAMILY,
        complexity=QuestionComplexity.BASIC,
        information_value=0.9,
        engagement_potential=0.7,
        follow_up_questions=["family_ages"],
        prerequisites=[],
        tags=["family", "size"],
        example_answers=["Just me", "Two people", "Four of us"]
    )


class TestQuestionMemoryInitialization:
    """Test question memory initialization"""

    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_dependencies):
        """Test successful initialization"""
        zep_client, temporal_memory = mock_dependencies
        memory = QuestionMemory(zep_client, temporal_memory)

        assert await memory.initialize() == True
        assert memory.initialized == True

    @pytest.mark.asyncio
    async def test_initialization_fails_without_zep(self, mock_dependencies):
        """Test initialization fails without Zep client"""
        zep_client, temporal_memory = mock_dependencies
        zep_client.initialized = False

        memory = QuestionMemory(zep_client, temporal_memory)
        assert await memory.initialize() == False

    def test_cache_configuration(self, question_memory):
        """Test cache configuration"""
        assert question_memory.cache_expiry_minutes == 10
        assert question_memory.effectiveness_threshold == 0.5
        assert question_memory.min_samples_for_effectiveness == 5


class TestQuestionTracking:
    """Test question tracking functionality"""

    @pytest.mark.asyncio
    async def test_track_question_asked(self, question_memory, sample_question):
        """Test tracking a question asked to user"""
        user_id = "test_user"
        session_id = "session_123"

        success = await question_memory.track_question(
            user_id=user_id,
            question=sample_question,
            session_id=session_id,
            response="Four people",
            response_time_ms=5000,
            engagement_indicators={"engagement_score": 0.8}
        )

        assert success == True

        # Verify temporal memory was called
        question_memory.temporal_memory.store_memory.assert_called_once()
        call_args = question_memory.temporal_memory.store_memory.call_args
        assert call_args[0][0] == user_id  # First argument should be user_id

    @pytest.mark.asyncio
    async def test_track_question_without_response(self, question_memory, sample_question):
        """Test tracking a question without immediate response"""
        user_id = "test_user"
        session_id = "session_123"

        success = await question_memory.track_question(
            user_id=user_id,
            question=sample_question,
            session_id=session_id
        )

        assert success == True

    @pytest.mark.asyncio
    async def test_update_question_response(self, question_memory, sample_question):
        """Test updating question with response"""
        user_id = "test_user"

        # First track the question
        await question_memory.track_question(
            user_id=user_id,
            question=sample_question,
            session_id="session_123",
            response=None  # No response yet
        )

        # Mock retrieval of question history
        question_memory.temporal_memory.retrieve_by_user.return_value = [
            Mock(
                content={
                    "question_id": sample_question.id,
                    "status": QuestionStatus.ASKED.value,
                    "response": None,
                    "response_time_ms": None,
                    "effectiveness_score": None
                }
            )
        ]

        # Update with response
        success = await question_memory.update_question_response(
            user_id=user_id,
            question_id=sample_question.id,
            response="Four people total",
            response_time_ms=4000,
            effectiveness_score=0.8
        )

        assert success == True

    @pytest.mark.asyncio
    async def test_update_nonexistent_question(self, question_memory):
        """Test updating response for non-existent question"""
        question_memory.temporal_memory.retrieve_by_user.return_value = []

        success = await question_memory.update_question_response(
            user_id="test_user",
            question_id="nonexistent",
            response="Test response"
        )

        assert success == False

    @pytest.mark.asyncio
    async def test_has_question_been_asked(self, question_memory):
        """Test checking if question has been asked"""
        user_id = "test_user"
        question_id = "family_size"

        # Test with cache
        question_memory.recent_questions_cache[user_id] = [
            QuestionRecord(
                question_id=question_id,
                question_text="How many people?",
                category=QuestionCategory.FAMILY,
                timestamp=datetime.now() - timedelta(days=1),
                session_id="session_123",
                status=QuestionStatus.ANSWERED,
                response="Four",
                response_time_ms=3000,
                effectiveness_score=0.8,
                follow_up_generated=False,
                metadata={}
            )
        ]

        # Should find the question
        assert await question_memory.has_question_been_asked(user_id, question_id) == True

        # Should not find different question
        assert await question_memory.has_question_been_asked(user_id, "different_question") == False

    @pytest.mark.asyncio
    async def test_has_question_been_asked_within_days(self, question_memory):
        """Test checking if question was asked within specific days"""
        user_id = "test_user"
        question_id = "recent_question"

        # Mock recent question (within 7 days)
        question_memory.temporal_memory.retrieve_by_user.return_value = [
            Mock(
                content={"question_id": question_id},
                timestamp=datetime.now() - timedelta(days=3)
            )
        ]

        # Should find within 7 days
        assert await question_memory.has_question_been_asked(user_id, question_id, within_days=7) == True

        # Should not find within 1 day
        assert await question_memory.has_question_been_asked(user_id, question_id, within_days=1) == False

    @pytest.mark.asyncio
    async def test_get_questions_by_category(self, question_memory):
        """Test retrieving questions by category"""
        user_id = "test_user"

        # Mock question history
        mock_questions = [
            QuestionRecord(
                question_id="family_size",
                question_text="Family size?",
                category=QuestionCategory.FAMILY,
                timestamp=datetime.now(),
                session_id="session_1",
                status=QuestionStatus.ANSWERED,
                response="4",
                response_time_ms=5000,
                effectiveness_score=0.8,
                follow_up_generated=False,
                metadata={}
            ),
            QuestionRecord(
                question_id="budget_range",
                question_text="Budget?",
                category=QuestionCategory.BUDGET,
                timestamp=datetime.now(),
                session_id="session_1",
                status=QuestionStatus.ANSWERED,
                response="$30k",
                response_time_ms=3000,
                effectiveness_score=0.7,
                follow_up_generated=False,
                metadata={}
            )
        ]

        question_memory.recent_questions_cache[user_id] = mock_questions

        # Get family questions
        family_questions = await question_memory.get_questions_by_category(
            user_id, QuestionCategory.FAMILY
        )

        assert len(family_questions) == 1
        assert family_questions[0].category == QuestionCategory.FAMILY

        # Get budget questions
        budget_questions = await question_memory.get_questions_by_category(
            user_id, QuestionCategory.BUDGET
        )

        assert len(budget_questions) == 1
        assert budget_questions[0].category == QuestionCategory.BUDGET


class TestPreferenceEvolution:
    """Test preference evolution tracking"""

    @pytest.mark.asyncio
    async def test_detect_preference_change(self, question_memory):
        """Test detecting changes in user preferences"""
        user_id = "test_user"
        preference_key = "vehicle_type"
        new_value = "SUV"

        # Mock no previous history
        question_memory.temporal_memory.retrieve_by_user.return_value = []

        evolution = await question_memory.detect_preference_changes(
            user_id, preference_key, new_value
        )

        assert evolution is not None
        assert evolution.preference_key == preference_key
        assert evolution.initial_value == new_value
        assert evolution.current_value == new_value
        assert evolution.change_count == 0

    @pytest.mark.asyncio
    async def test_track_preference_evolution(self, question_memory):
        """Test tracking preference evolution over time"""
        user_id = "test_user"
        preference_key = "budget"

        # Mock existing preference
        question_memory.temporal_memory.retrieve_by_user.return_value = [
            Mock(
                content={
                    "preference": "budget",
                    "initial_value": "$30k",
                    "value": "$30k"
                },
                timestamp=datetime.now() - timedelta(days=10)
            )
        ]

        # Update with new value
        evolution = await question_memory.detect_preference_changes(
            user_id, preference_key, "$40k"
        )

        assert evolution is not None
        assert evolution.initial_value == "$30k"
        assert evolution.current_value == "$40k"

    @pytest.mark.asyncio
    async def test_no_change_detected(self, question_memory):
        """Test no evolution detected when value hasn't changed"""
        user_id = "test_user"
        preference_key = "brand"
        value = "Toyota"

        # Mock existing preference with same value
        question_memory.temporal_memory.retrieve_by_user.return_value = [
            Mock(
                content={"initial_value": value, "value": value},
                timestamp=datetime.now() - timedelta(days=5)
            )
        ]

        evolution = await question_memory.detect_preference_changes(
            user_id, preference_key, value
        )

        assert evolution is None  # No change detected


class TestQuestionEffectiveness:
    """Test question effectiveness tracking"""

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_detailed_response(self, question_memory):
        """Test effectiveness calculation for detailed response"""
        question = Mock()
        question.information_value = 0.8

        response = "I need space for a family of four, with good safety features, and preferably under $30,000"
        response_time_ms = 8000
        engagement_indicators = {
            "engagement_score": 0.9,
            "sentiment": "positive"
        }

        effectiveness = await question_memory.calculate_question_effectiveness(
            user_id="test_user",
            question=question,
            response=response,
            response_time_ms=response_time_ms,
            engagement_indicators=engagement_indicators
        )

        assert effectiveness > 0.7  # Should be high for detailed response
        assert effectiveness <= 1.0

        # Check effectiveness was stored
        question_memory.temporal_memory.store_memory.assert_called()
        stored_content = question_memory.temporal_memory.store_memory.call_args[0][1].content
        assert stored_content["score"] == effectiveness
        assert stored_content["question_id"] == question.id

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_short_response(self, question_memory):
        """Test effectiveness calculation for short response"""
        question = Mock()
        question.information_value = 0.5

        response = "No"
        response_time_ms = 1000
        engagement_indicators = {"engagement_score": 0.2}

        effectiveness = await question_memory.calculate_question_effectiveness(
            user_id="test_user",
            question=question,
            response=response,
            response_time_ms=response_time_ms,
            engagement_indicators=engagement_indicators
        )

        assert effectiveness < 0.5  # Should be low for very short response

    @pytest.mark.asyncio
    async def test_get_question_effectiveness(self, question_memory):
        """Test retrieving question effectiveness"""
        user_id = "test_user"
        question_id = "test_question"

        # Mock effectiveness data
        question_memory.temporal_memory.retrieve_by_user.return_value = [
            Mock(content={"score": 0.8}),
            Mock(content={"score": 0.7}),
            Mock(content={"score": 0.9})
        ]

        effectiveness = await question_memory.get_question_effectiveness(user_id, question_id)

        assert effectiveness is not None
        assert effectiveness == 0.8  # Should be average of scores

    @pytest.mark.asyncio
    async def test_get_question_effectiveness_no_data(self, question_memory):
        """Test getting effectiveness with no data"""
        question_memory.temporal_memory.retrieve_by_user.return_value = []

        effectiveness = await question_memory.get_question_effectiveness("user", "question")

        assert effectiveness is None


class TestUserQuestionHistory:
    """Test user question history retrieval"""

    @pytest.mark.asyncio
    async def test_get_user_question_history(self, question_memory):
        """Test retrieving user's complete question history"""
        user_id = "test_user"

        # Mock memory fragments
        mock_fragments = [
            Mock(
                content={
                    "question_id": "q1",
                    "question_text": "Question 1",
                    "category": "family",
                    "status": "answered",
                    "response": "Response 1"
                }
            ),
            Mock(
                content={
                    "question_id": "q2",
                    "question_text": "Question 2",
                    "category": "budget",
                    "status": "asked",
                    "response": None
                }
            )
        ]
        question_memory.temporal_memory.retrieve_by_user.return_value = mock_fragments

        # Convert to QuestionRecord format
        for fragment in mock_fragments:
            fragment.timestamp = datetime.now() - timedelta(hours=mock_fragments.index(fragment))

        history = await question_memory.get_user_question_history(user_id)

        assert len(history) == 2
        assert all(isinstance(record, QuestionRecord) for record in history)

    @pytest.mark.asyncio
    async def test_get_question_history_with_filters(self, question_memory):
        """Test getting history with category and time filters"""
        user_id = "test_user"

        # Create mock records with different categories
        mock_records = [
            QuestionRecord(
                question_id="family_q",
                question_text="Family question",
                category=QuestionCategory.FAMILY,
                timestamp=datetime.now() - timedelta(days=2),
                session_id="s1",
                status=QuestionStatus.ANSWERED,
                response="Family response",
                response_time_ms=5000,
                effectiveness_score=0.8,
                follow_up_generated=False,
                metadata={}
            ),
            QuestionRecord(
                question_id="budget_q",
                question_text="Budget question",
                category=QuestionCategory.BUDGET,
                timestamp=datetime.now() - timedelta(days=10),  # Older than 7 days
                session_id="s2",
                status=QuestionStatus.ANSWERED,
                response="Budget response",
                response_time_ms=3000,
                effectiveness_score=0.7,
                follow_up_generated=False,
                metadata={}
            )
        ]

        question_memory.recent_questions_cache[user_id] = mock_records

        # Filter by family category
        family_history = await question_memory.get_user_question_history(
            user_id, category=QuestionCategory.FAMILY
        )

        assert len(family_history) == 1
        assert family_history[0].category == QuestionCategory.FAMILY

        # Filter by last 7 days
        recent_history = await question_memory.get_user_question_history(
            user_id, days_back=7
        )

        assert len(recent_history) == 1  # Only the recent family question


class TestCrossSessionInsights:
    """Test cross-session insights generation"""

    @pytest.mark.asyncio
    async def test_get_cross_session_insights(self, question_memory):
        """Test generating insights across sessions"""
        user_id = "test_user"

        # Mock question history
        mock_records = [
            QuestionRecord(
                question_id="q1",
                question_text="Question 1",
                category=QuestionCategory.FAMILY,
                timestamp=datetime.now() - timedelta(days=1),
                session_id="session_1",
                status=QuestionStatus.ANSWERED,
                response="Response 1",
                response_time_ms=5000,
                effectiveness_score=0.8,
                follow_up_generated=False,
                metadata={}
            ),
            QuestionRecord(
                question_id="q2",
                question_text="Question 2",
                category=QuestionCategory.FAMILY,
                timestamp=datetime.now() - timedelta(days=2),
                session_id="session_2",
                status=QuestionStatus.ANSWERED,
                response="Response 2",
                response_time_ms=4000,
                effectiveness_score=0.9,
                follow_up_generated=False,
                metadata={}
            )
        ]

        question_memory.recent_questions_cache[user_id] = mock_records

        insights = await question_memory.get_cross_session_insights(user_id)

        assert isinstance(insights, dict)
        assert "category_preferences" in insights
        assert "total_sessions" in insights
        assert "questions_per_session" in insights

        # Should show family category preference
        assert insights["category_preferences"]["family"] >= 2

    @pytest.mark.asyncio
    async def test_cross_session_insights_empty_history(self, question_memory):
        """Test insights with no question history"""
        question_memory.recent_questions_cache = {}

        insights = await question_memory.get_cross_session_insights("new_user")

        assert isinstance(insights, dict)
        assert "message" in insights
        assert "No question history available" in insights["message"]


class TestHelperMethods:
    """Test helper methods"""

    def test_contains_preference_information(self, question_memory):
        """Test preference information detection"""
        assert question_memory._contains_preference_information("I prefer SUVs") == True
        assert question_memory._contains_preference_information("Need good gas mileage") == True
        assert question_memory._contains_preference_information("Must have leather seats") == True
        assert question_memory._contains_preference_information("Just browsing") == False

    def test_classify_response_type(self, question_memory):
        """Test response type classification"""
        assert question_memory._classify_response_type("yes") == "simple_choice"
        assert question_memory._classify_response_type("Budget is $30,000") == "quantitative"
        assert question_memory._classify_response_type("It's okay") == "short_answer"
        assert question_memory._classify_response_type("What about the warranty?") == "question"
        assert question_memory._classify_response_type("I need something reliable with good safety features") == "detailed_answer"


# Performance Tests
class TestPerformance:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_question_tracking_performance(self, question_memory, sample_question):
        """Test question tracking performance"""
        import time

        start_time = time.time()
        await question_memory.track_question(
            user_id="test_user",
            question=sample_question,
            session_id="session_123",
            response="Test response",
            response_time_ms=5000,
            engagement_indicators={}
        )
        tracking_time = (time.time() - start_time) * 1000

        # Should complete quickly
        assert tracking_time < 100  # Less than 100ms

    @pytest.mark.asyncio
    async def test_history_retrieval_performance(self, question_memory):
        """Test history retrieval performance"""
        import time

        # Mock large history
        question_memory.recent_questions_cache["test_user"] = [
            QuestionRecord(
                question_id=f"q{i}",
                question_text=f"Question {i}",
                category=QuestionCategory.FEATURE,
                timestamp=datetime.now() - timedelta(hours=i),
                session_id=f"s{i}",
                status=QuestionStatus.ANSWERED,
                response=f"Response {i}",
                response_time_ms=5000,
                effectiveness_score=0.7,
                follow_up_generated=False,
                metadata={}
            )
            for i in range(100)
        ]

        start_time = time.time()
        history = await question_memory.get_user_question_history("test_user")
        retrieval_time = (time.time() - start_time) * 1000

        # Should handle large histories efficiently
        assert retrieval_time < 200  # Less than 200ms


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])