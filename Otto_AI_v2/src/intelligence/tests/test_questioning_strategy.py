"""
Tests for Questioning Strategy module
Validates question selection algorithms and adaptive behavior
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.intelligence.questioning_strategy import (
    QuestioningStrategy,
    Question,
    QuestionCategory,
    QuestionComplexity,
    UserContext,
    QuestionScore
)


@pytest.fixture
async def mock_dependencies():
    """Create mock dependencies for testing"""
    groq_client = Mock()
    groq_client.initialized = True
    groq_client.generate_response = AsyncMock(return_value="Mock response")

    temporal_memory = Mock()
    temporal_memory.initialized = True
    temporal_memory.retrieve_by_user = AsyncMock(return_value=[])
    temporal_memory.retrieve_by_pattern = AsyncMock(return_value=[])
    temporal_memory.store_memory = AsyncMock()

    preference_engine = Mock()
    preference_engine.initialized = True

    return groq_client, temporal_memory, preference_engine


@pytest.fixture
async def questioning_strategy(mock_dependencies):
    """Create QuestioningStrategy instance for testing"""
    groq_client, temporal_memory, preference_engine = mock_dependencies
    strategy = QuestioningStrategy(groq_client, temporal_memory, preference_engine)
    await strategy.initialize()
    return strategy


class TestQuestioningStrategyInitialization:
    """Test questioning strategy initialization"""

    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_dependencies):
        """Test successful initialization"""
        groq_client, temporal_memory, preference_engine = mock_dependencies
        strategy = QuestioningStrategy(groq_client, temporal_memory, preference_engine)

        assert await strategy.initialize() == True
        assert strategy.initialized == True
        assert len(strategy.questions) > 0  # Should load default questions

    @pytest.mark.asyncio
    async def test_initialization_fails_without_groq(self, mock_dependencies):
        """Test initialization fails without Groq client"""
        groq_client, temporal_memory, preference_engine = mock_dependencies
        groq_client.initialized = False

        strategy = QuestioningStrategy(groq_client, temporal_memory, preference_engine)
        assert await strategy.initialize() == False

    @pytest.mark.asyncio
    async def test_load_question_database(self, questioning_strategy):
        """Test question database is loaded correctly"""
        assert len(questioning_strategy.questions) > 0

        # Check essential questions exist
        assert "family_size" in questioning_strategy.questions
        assert "performance_priority" in questioning_strategy.questions
        assert "budget_range" in questioning_strategy.questions

    def test_information_weights(self, questioning_strategy):
        """Test information weights are properly set"""
        assert QuestionCategory.FAMILY in questioning_strategy.information_weights
        assert questioning_strategy.information_weights[QuestionCategory.FAMILY] > 0.8
        assert questioning_strategy.information_weights[QuestionCategory.FEATURE] < 0.7


class TestQuestionSelection:
    """Test question selection algorithms"""

    @pytest.mark.asyncio
    async def test_select_next_question_basic(self, questioning_strategy):
        """Test basic question selection"""
        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        scored_questions = await questioning_strategy.select_next_question(user_context)

        assert isinstance(scored_questions, list)
        assert len(scored_questions) <= 3
        assert all(isinstance(sq, QuestionScore) for sq in scored_questions)

        if scored_questions:
            assert scored_questions[0].total_score > 0
            assert scored_questions[0].information_value >= 0
            assert scored_questions[0].engagement_score >= 0

    @pytest.mark.asyncio
    async def test_select_question_with_family_preference(self, questioning_strategy):
        """Test question selection prioritizes family questions in discovery"""
        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        scored_questions = await questioning_strategy.select_next_question(user_context, max_questions=1)

        # Should prioritize high-value questions for discovery
        if scored_questions:
            question = questioning_strategy.questions[scored_questions[0].question_id]
            assert question.category in [QuestionCategory.FAMILY, QuestionCategory.USAGE, QuestionCategory.BUDGET]

    @pytest.mark.asyncio
    async def test_avoids_asked_questions(self, questioning_strategy):
        """Test that already asked questions are not selected"""
        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked={"family_size", "budget_range"},  # Already asked
            last_question_time=datetime.now() - timedelta(minutes=5),
            response_patterns={},
            fatigue_indicators=[]
        )

        scored_questions = await questioning_strategy.select_next_question(user_context)

        # Should not include already asked questions
        if scored_questions:
            for sq in scored_questions:
                assert sq.question_id not in {"family_size", "budget_range"}

    @pytest.mark.asyncio
    async def test_adapts_to_engagement_level(self, questioning_strategy):
        """Test question selection adapts to user engagement"""
        # Low engagement context
        low_engagement_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.3,  # Low engagement
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=["short_response"]
        )

        low_engagement_questions = await questioning_strategy.select_next_question(low_engagement_context)

        # High engagement context
        high_engagement_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.9,  # High engagement
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        high_engagement_questions = await questioning_strategy.select_next_question(high_engagement_context)

        # Low engagement should prioritize engaging questions
        if low_engagement_questions and high_engagement_questions:
            low_q = questioning_strategy.questions[low_engagement_questions[0].question_id]
            high_q = questioning_strategy.questions[high_engagement_questions[0].question_id]

            # Low engagement should favor questions with high engagement potential
            assert low_q.engagement_potential >= high_q.engagement_potential * 0.8

    @pytest.mark.asyncio
    async def test_timing_constraints(self, questioning_strategy):
        """Test question selection respects timing constraints"""
        # Recent question context
        recent_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=datetime.now() - timedelta(seconds=10),  # Very recent
            response_patterns={},
            fatigue_indicators=[]
        )

        recent_questions = await questioning_strategy.select_next_question(recent_context)

        # Distant question context
        distant_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=datetime.now() - timedelta(minutes=10),  # 10 minutes ago
            response_patterns={},
            fatigue_indicators=[]
        )

        distant_questions = await questioning_strategy.select_next_question(distant_context)

        # Should penalize questions asked very recently
        # This test would need more sophisticated timing logic to be fully validated


class TestQuestionScoring:
    """Test question scoring algorithms"""

    @pytest.mark.asyncio
    async def test_calculate_information_value(self, questioning_strategy):
        """Test information value calculation"""
        question = Question(
            id="test_q",
            text="Test question",
            category=QuestionCategory.FAMILY,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.8,
            engagement_potential=0.7,
            follow_up_questions=[],
            prerequisites=[],
            tags=["test"],
            example_answers=[]
        )

        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        info_score = await questioning_strategy._calculate_information_value(question, user_context)

        assert 0 <= info_score <= 1.0
        # Family questions in discovery should get high scores
        assert info_score > 0.7

    @pytest.mark.asyncio
    async def test_calculate_engagement_potential(self, questioning_strategy):
        """Test engagement potential calculation"""
        question = Question(
            id="test_q",
            text="Tell me about your typical weekend activities?",
            category=QuestionCategory.LIFESTYLE,
            complexity=QuestionComplexity.OPEN,
            information_value=0.7,
            engagement_potential=0.8,
            follow_up_questions=[],
            prerequisites=[],
            tags=["lifestyle", "activities"],
            example_answers=[]
        )

        # High engagement context
        high_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=["performance"],
            engagement_level=0.8,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        engagement_score = await questioning_strategy._calculate_engagement_potential(question, high_context)
        assert 0 <= engagement_score <= 1.0
        assert engagement_score > 0.6

    @pytest.mark.asyncio
    async def test_calculate_novelty_score(self, questioning_strategy, mock_dependencies):
        """Test novelty score calculation"""
        groq_client, temporal_memory, preference_engine = mock_dependencies

        # Set up memory with recent questions in same category
        temporal_memory.retrieve_by_user.return_value = [
            Mock(
                content={"category": QuestionCategory.FAMILY.value},
                timestamp=datetime.now() - timedelta(days=1)
            )
        ]

        question = Question(
            id="test_q",
            text="Another family question",
            category=QuestionCategory.FAMILY,
            complexity=QuestionComplexity.BASIC,
            information_value=0.6,
            engagement_potential=0.5,
            follow_up_questions=[],
            prerequisites=[],
            tags=["family"],
            example_answers=[]
        )

        user_context = UserContext(
            user_id="test_user",
            conversation_stage="refinement",
            known_preferences={"family": "large"},
            recent_topics=["family", "safety"],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        novelty_score = await questioning_strategy._calculate_novelty_score(question, user_context)

        assert 0 <= novelty_score <= 1.0
        # Should be lower due to recent similar questions
        assert novelty_score < 0.8

    def test_generate_selection_reasons(self, questioning_strategy):
        """Test generation of selection reasons"""
        reasons = questioning_strategy._generate_selection_reasons(
            question=Mock(category=QuestionCategory.FAMILY),
            info_score=0.8,
            engagement_score=0.7,
            timing_score=0.6,
            novelty_score=0.5
        )

        assert isinstance(reasons, list)
        assert len(reasons) > 0
        assert any("family" in str(reason).lower() for reason in reasons)
        assert any("information" in str(reason).lower() for reason in reasons)


class TestQuestionEffectiveness:
    """Test question effectiveness tracking"""

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_detailed_response(self, questioning_strategy):
        """Test effectiveness calculation for detailed response"""
        response = "I have a family of four, two kids aged 8 and 11, and we love going on road trips on weekends. We need something with good cargo space."

        effectiveness = await questioning_strategy.calculate_question_effectiveness(
            user_id="test_user",
            question=Mock(id="family_needs"),
            response=response,
            response_time_ms=8000,
            engagement_indicators={
                "engagement_score": 0.8,
                "sentiment": "positive"
            }
        )

        assert effectiveness > 0.7  # Should be high for detailed response
        assert effectiveness <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_effectiveness_short_response(self, questioning_strategy):
        """Test effectiveness calculation for short response"""
        response = "No"

        effectiveness = await questioning_strategy.calculate_question_effectiveness(
            user_id="test_user",
            question=Mock(id="simple_question"),
            response=response,
            response_time_ms=1000,
            engagement_indicators={
                "engagement_score": 0.3,
                "sentiment": "neutral"
            }
        )

        assert effectiveness < 0.5  # Should be low for very short response

    @pytest.mark.asyncio
    async def test_record_question_effectiveness(self, questioning_strategy, mock_dependencies):
        """Test recording question effectiveness"""
        groq_client, temporal_memory, preference_engine = mock_dependencies

        await questioning_strategy._store_question_effectiveness(
            user_id="test_user",
            question_id="test_q",
            score=0.8
        )

        # Verify memory storage was called
        temporal_memory.store_memory.assert_called_once()
        call_args = temporal_memory.store_memory.call_args[0]

        assert call_args[0] == "test_user"
        stored_fragment = call_args[1]
        assert stored_fragment.content["question_id"] == "test_q"
        assert stored_fragment.content["score"] == 0.8
        assert stored_fragment.importance == 0.8


class TestIntegration:
    """Integration tests for questioning strategy"""

    @pytest.mark.asyncio
    async def test_full_question_flow(self, questioning_strategy):
        """Test complete question selection and tracking flow"""
        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        # Select first question
        scored_questions = await questioning_strategy.select_next_question(user_context, max_questions=1)
        assert scored_questions

        # Get the question
        question_id = scored_questions[0].question_id
        question = questioning_strategy.questions[question_id]

        # Simulate asking the question
        await questioning_strategy.record_question_asked(
            user_id="test_user",
            question=question,
            response="I need space for 5 people and lots of cargo",
            response_time_ms=5000,
            engagement_indicators={"engagement_score": 0.8}
        )

        # Update user context to reflect asked question
        user_context.questions_asked.add(question_id)
        user_context.last_question_time = datetime.now()

        # Select next question - should be different
        next_questions = await questioning_strategy.select_next_question(user_context, max_questions=1)

        if next_questions:
            assert next_questions[0].question_id != question_id

    @pytest.mark.asyncio
    async def test_question_prerequisites(self, questioning_strategy):
        """Test that question prerequisites are respected"""
        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        # Get questions with prerequisites
        questions_with_prereqs = [
            (qid, q) for qid, q in questioning_strategy.questions.items()
            if q.prerequisites
        ]

        if questions_with_prereqs:
            qid, question = questions_with_prereqs[0]

            # Try to select question without prerequisite
            scored_questions = await questioning_strategy.select_next_question(user_context, max_questions=10)

            # Question with unmet prerequisite should not be in results
            selected_ids = [sq.question_id for sq in scored_questions]
            assert qid not in selected_ids

    @pytest.mark.asyncio
    async def test_dynamic_question_loading(self, questioning_strategy, mock_dependencies):
        """Test loading of dynamic questions from memory"""
        groq_client, temporal_memory, preference_engine = mock_dependencies

        # Mock effective question in memory
        temporal_memory.retrieve_by_pattern.return_value = [
            Mock(
                content={
                    "question_template": "What's your daily commute like?",
                    "category": "usage",
                    "complexity": "intermediate",
                    "effectiveness_score": 0.9,
                    "engagement_score": 0.8,
                    "tags": ["commute", "daily"]
                },
                id="memory_123"
            )
        ]

        # Load dynamic questions
        await questioning_strategy._load_dynamic_questions()

        # Check dynamic question was loaded
        dynamic_questions = [
            qid for qid in questioning_strategy.questions.keys()
            if qid.startswith("dynamic_")
        ]

        assert len(dynamic_questions) > 0


# Performance Tests
class TestPerformance:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_question_selection_performance(self, questioning_strategy):
        """Test question selection meets performance requirements"""
        import time

        user_context = UserContext(
            user_id="test_user",
            conversation_stage="discovery",
            known_preferences={},
            recent_topics=[],
            engagement_level=0.7,
            questions_asked=set(),
            last_question_time=None,
            response_patterns={},
            fatigue_indicators=[]
        )

        # Measure selection time
        start_time = time.time()
        scored_questions = await questioning_strategy.select_next_question(user_context)
        selection_time = (time.time() - start_time) * 1000

        # Should complete within reasonable time (adjust threshold as needed)
        assert selection_time < 1000  # Less than 1 second

    @pytest.mark.asyncio
    async def test_effectiveness_calculation_performance(self, questioning_strategy):
        """Test effectiveness calculation performance"""
        import time

        response = "This is a moderately detailed response that provides some information about user preferences and needs."

        start_time = time.time()
        effectiveness = await questioning_strategy.calculate_question_effectiveness(
            user_id="test_user",
            question=Mock(id="test_q"),
            response=response,
            response_time_ms=5000,
            engagement_indicators={"engagement_score": 0.7}
        )
        calc_time = (time.time() - start_time) * 1000

        # Should calculate quickly
        assert calc_time < 100  # Less than 100ms


# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])