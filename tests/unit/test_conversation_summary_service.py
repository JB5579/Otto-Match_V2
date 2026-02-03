"""
Unit tests for Conversation Summary Service

Story: 2-7.13 - Create backend test suite
Tests conversation summarization, preference extraction, and journey stage detection
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.services.conversation_summary_service import (
    ConversationSummaryService,
    ConversationSummary,
    ExtractedPreferences,
    VehicleMention,
    JourneyStage,
    get_summary_service
)
from src.memory.zep_client import Message


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('src.services.conversation_summary_service.AsyncOpenAI') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def summary_service(mock_openai_client):
    """Create summary service with mocked dependencies"""
    service = ConversationSummaryService(
        openai_api_key="test-key",
        zep_client=None,
        cache=None
    )
    # Set the mocked client
    service.openai_client = mock_openai_client
    return service


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing"""
    return [
        Message(
            role="user",
            content="I'm looking for an SUV under $30000 for my family of 4",
            metadata={},
            created_at=datetime.now() - timedelta(minutes=10)
        ),
        Message(
            role="assistant",
            content="I can help you find a great family SUV! What features are important to you?",
            metadata={},
            created_at=datetime.now() - timedelta(minutes=9)
        ),
        Message(
            role="user",
            content="We need good safety ratings and preferably a Toyota or Honda",
            metadata={},
            created_at=datetime.now() - timedelta(minutes=8)
        ),
        Message(
            role="assistant",
            content="Both Toyota and Honda have excellent SUVs with top safety ratings. Let me show you some options...",
            metadata={},
            created_at=datetime.now() - timedelta(minutes=7)
        )
    ]


# =================================================================
# Conversation Summary Tests
# =================================================================

class TestConversationSummaryService:
    """Test conversation summary generation"""

    @pytest.mark.asyncio
    async def test_generate_conversation_summary(self, summary_service, sample_messages):
        """Test generating complete conversation summary"""
        # Mock OpenAI responses
        summary_service.openai_client.chat.completions.create = AsyncMock(
            return_value=Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="Family SUV Search"
                        )
                    )
                ]
            )
        )

        summary_service.openai_client.chat.completions.create = AsyncMock(
            side_effect=[
            # Title response
            Mock(choices=[Mock(message=Mock(content="Family SUV Search"))]),
            # Summary response
            Mock(choices=[Mock(message=Mock(content="User is looking for a family SUV under $30000 from Toyota or Honda."))]),
            # Key points response
            Mock(choices=[Mock(message=Mock(content="Budget: under $30000\nBrands: Toyota, Honda\nNeed: family-friendly, good safety"))])
        ]

        summary = await summary_service.generate_conversation_summary(
            messages=sample_messages,
            conversation_id="test-conv-1",
            session_id="test-session-1",
            user_id="test-user-1"
        )

        assert summary.conversation_id == "test-conv-1"
        assert summary.session_id == "test-session-1"
        assert summary.user_id == "test-user-1"
        assert summary.title == "Family SUV Search"
        assert summary.message_count == 4
        assert summary.journey_stage == JourneyStage.DISCOVERY

    @pytest.mark.asyncio
    async def test_extract_preferences(self, summary_service, sample_messages):
        """Test preference extraction from messages"""
        preferences = await summary_service._extract_preferences(sample_messages)

        assert isinstance(preferences, ExtractedPreferences)
        assert 'SUV' in preferences.vehicle_types
        assert 'Toyota' in preferences.brands
        assert 'Honda' in preferences.brands
        assert 'family' in preferences.lifestyle
        assert preferences.budget is not None
        assert 'max' in preferences.budget

    @pytest.mark.asyncio
    async def test_extract_vehicles(self, summary_service):
        """Test vehicle extraction from messages"""
        messages = [
            Message(
                role="user",
                content="I'm interested in the 2023 Toyota RAV4 and Honda CR-V",
                metadata={},
                created_at=datetime.now()
            ),
            Message(
                role="user",
                content="The Toyota Highlander is also an option",
                metadata={},
                created_at=datetime.now()
            )
        ]

        vehicles = await summary_service._extract_vehicles(messages)

        assert len(vehicles) == 3
        assert any(v.make == "Toyota" and v.model == "RAV4" for v in vehicles)
        assert any(v.make == "Honda" and v.model == "CR-V" for v in vehicles)
        assert any(v.make == "Toyota" and v.model == "Highlander" for v in vehicles)

    @pytest.mark.asyncio
    async def test_determine_journey_stage(self, summary_service):
        """Test journey stage detection"""
        # Discovery stage
        discovery_msgs = [
            Message(role="user", content="I'm looking for a car", metadata={}, created_at=datetime.now()),
            Message(role="user", content="Interested in SUVs", metadata={}, created_at=datetime.now())
        ]
        stage = await summary_service._determine_journey_stage(discovery_msgs)
        assert stage == JourneyStage.DISCOVERY

        # Consideration stage
        consideration_msgs = [
            Message(role="user", content="Compare the RAV4 vs CR-V", metadata={}, created_at=datetime.now()),
            Message(role="user", content="Which is better?", metadata={}, created_at=datetime.now())
        ]
        stage = await summary_service._determine_journey_stage(consideration_msgs)
        assert stage == JourneyStage.CONSIDERATION

        # Decision stage
        decision_msgs = [
            Message(role="user", content="I've decided on the RAV4", metadata={}, created_at=datetime.now()),
            Message(role="user", content="Going to buy it", metadata={}, created_at=datetime.now())
        ]
        stage = await summary_service._determine_journey_stage(decision_msgs)
        assert stage == JourneyStage.DECISION

    @pytest.mark.asyncio
    async def test_detect_preference_evolution(self, summary_service):
        """Test preference evolution detection"""
        # Create messages with evolving budget
        early_budget_msg = Message(
            role="user",
            content="My budget is under $25000",
            metadata={},
            created_at=datetime.now() - timedelta(minutes=20)
        )

        late_budget_msg = Message(
            role="user",
            content="I've increased my budget to under $35000",
            metadata={},
            created_at=datetime.now()
        )

        messages = [early_budget_msg, late_budget_msg]

        # Extract preferences
        all_prefs = await summary_service._extract_preferences(messages)
        early_prefs = await summary_service._extract_preferences([early_budget_msg])
        late_prefs = await summary_service._extract_preferences([late_budget_msg])

        # Detect evolution
        evolved, notes = await summary_service._detect_preference_evolution(messages, all_prefs)

        assert evolved is True
        assert len(notes) > 0
        assert any("increased" in note.lower() for note in notes)


# =================================================================
# Fallback Tests (without OpenAI)
# =================================================================

class TestFallbackMethods:
    """Test fallback methods when OpenAI is unavailable"""

    def test_generate_fallback_title(self, summary_service):
        """Test title generation without AI"""
        messages = [
            Message(role="user", content="Looking for Toyota SUV", metadata={}, created_at=datetime.now()),
            Message(role="user", content="Under $30000", metadata={}, created_at=datetime.now())
        ]

        title = summary_service._generate_fallback_title(messages)

        assert "Toyota" in title or "SUV" in title or "$30000" in title

    def test_generate_fallback_summary(self, summary_service):
        """Test summary generation without AI"""
        messages = [
            Message(role="user", content="Looking for a car", metadata={}, created_at=datetime.now()),
            Message(role="assistant", content="I can help!", metadata={}, created_at=datetime.now())
        ]

        summary = summary_service._generate_fallback_summary(messages)

        assert "conversation" in summary.lower()
        assert "messages" in summary.lower()


# =================================================================
# Singleton Tests
# =================================================================

class TestSingleton:
    """Test singleton instance management"""

    def test_get_summary_service(self):
        """Test getting singleton instance"""
        service1 = get_summary_service()
        service2 = get_summary_service()

        assert service1 is service2  # Same instance

    def test_singleton_initialization(self):
        """Test singleton is properly initialized"""
        service = get_summary_service()

        assert service is not None
        assert service.default_model == "gpt-4o"
        assert service.fallback_model == "gpt-4o-mini"


# =================================================================
# Integration Tests
# =================================================================

class TestIntegration:
    """Integration tests for conversation summary service"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_summary_workflow(self, summary_service, sample_messages):
        """Test complete summary generation workflow"""
        # This would require actual OpenAI API or comprehensive mocking
        # For unit tests, we focus on individual components

        # Test that all components can be called
        title = await summary_service._generate_title(sample_messages)
        assert title is not None

        preferences = await summary_service._extract_preferences(sample_messages)
        assert isinstance(preferences, ExtractedPreferences)

        vehicles = await summary_service._extract_vehicles(sample_messages)
        assert isinstance(vehicles, list)

        stage = await summary_service._determine_journey_stage(sample_messages)
        assert isinstance(stage, JourneyStage)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
