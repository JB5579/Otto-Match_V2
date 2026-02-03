"""
Tests for NLU Service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.conversation.nlu_service import NLUService, NLUResult, Intent, Entity
from src.conversation.groq_client import GroqClient
from src.conversation.intent_models import EntityType
from src.memory.zep_client import ZepClient, ConversationContext


@pytest.fixture
async def nlu_service():
    """Create NLU service instance for testing"""
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    zep_client = Mock(spec=ZepClient)

    service = NLUService(groq_client=groq_client, zep_client=zep_client)
    await service.initialize()
    return service


@pytest.fixture
def sample_context():
    """Create sample conversation context"""
    return ConversationContext(
        working_memory=[],
        episodic_memory=[],
        semantic_memory={},
        user_preferences={}
    )


class TestNLUService:
    """Test cases for NLU Service"""

    @pytest.mark.asyncio
    async def test_analyze_search_intent(self, nlu_service, sample_context):
        """Test analysis of search intent"""
        # Mock Groq response for intent
        nlu_service.groq_client.generate_response = AsyncMock(return_value={
            'success': True,
            'response': '{"primary_intent": "search", "confidence": 0.95, "requires_data": true, "urgency": "normal"}'
        })

        # Test message
        message = "I'm looking for a safe family SUV under $30,000"
        user_id = "test_user"

        result = await nlu_service.analyze_message(user_id, message, context=sample_context)

        # Assertions
        assert isinstance(result, NLUResult)
        assert result.intent.primary == "search"
        assert result.intent.confidence == pytest.approx(0.95)
        assert result.intent.requires_data == True
        assert len(result.entities) > 0  # Should extract price and vehicle type
        assert any(e.type == EntityType.PRICE for e in result.entities)
        assert any(e.type == EntityType.VEHICLE_TYPE for e in result.entities)

    @pytest.mark.asyncio
    async def test_analyze_compare_intent(self, nlu_service, sample_context):
        """Test analysis of compare intent"""
        # Mock Groq response for intent
        nlu_service.groq_client.generate_response = AsyncMock(return_value={
            'success': True,
            'response': '{"primary_intent": "compare", "confidence": 0.90, "requires_data": true, "urgency": "normal"}'
        })

        message = "Compare Toyota RAV4 vs Honda CR-V"
        user_id = "test_user"

        result = await nlu_service.analyze_message(user_id, message, context=sample_context)

        assert result.intent.primary == "compare"
        assert result.intent.confidence == pytest.approx(0.90)
        assert len(result.entities) > 0  # Should extract brands

    @pytest.mark.asyncio
    async def test_entity_extraction(self, nlu_service):
        """Test entity extraction from message"""
        entities = await nlu_service.entity_extractor.extract_entities(
            "I need a 2023 Toyota Camry under $25,000 with leather seats"
        )

        # Check extracted entities
        entity_types = [e.entity_type for e in entities]
        assert EntityType.YEAR in entity_types
        assert EntityType.BRAND in entity_types
        assert EntityType.MODEL in entity_types
        assert EntityType.PRICE in entity_types
        assert EntityType.FEATURE in entity_types

    @pytest.mark.asyncio
    async def test_context_ranking(self, nlu_service):
        """Test conversation context ranking"""
        from src.memory.zep_client import Message

        # Create test messages with timestamps
        messages = [
            Message(role="user", content="I need a family car", created_at=datetime.now()),
            Message(role="assistant", content="I can help with that", created_at=datetime.now()),
            Message(role="user", content="What about SUVs?", created_at=datetime.now()),
        ]

        # Add entities to context
        context = {
            'working_memory': messages,
            'episodic_memory': []
        }

        # Test relevance calculation
        relevance = nlu_service._calculate_context_relevance(
            "Tell me more about SUVs",
            context
        )

        assert relevance > 0  # Should have some relevance

    @pytest.mark.asyncio
    async def test_preference_detection(self, nlu_service):
        """Test preference detection from message"""
        message = "I need something safe for my family under $30,000"
        entities = []

        preferences = await nlu_service._extract_message_preferences(message)

        # Check extracted preferences
        pref_categories = [p.category for p in preferences]
        assert 'max_budget' in pref_categories
        assert 'vehicle_types' in pref_categories

    @pytest.mark.asyncio
    async def test_emotional_state_detection(self, nlu_service):
        """Test emotional state detection"""
        # Test excited state
        result = nlu_service._detect_emotional_state(
            "I'm so excited about getting a new car!",
            'positive',
            {}
        )
        assert result == 'excited'

        # Test confused state
        result = nlu_service._detect_emotional_state(
            "I don't understand all these features",
            'neutral',
            {}
        )
        assert result == 'confused'

    @pytest.mark.asyncio
    async def test_conversation_thread_tracking(self, nlu_service):
        """Test conversation thread tracking"""
        user_id = "test_user"
        message = "Looking for an SUV"
        nlu_result = NLUResult(
            intent=Intent(primary="search", confidence=0.9),
            entities=[],
            preferences=[],
            sentiment="neutral"
        )

        await nlu_service._update_conversation_thread(user_id, message, nlu_result)

        # Check thread was updated
        thread_key = f"{user_id}:default"
        assert thread_key in nlu_service.conversation_threads
        assert nlu_service.conversation_threads[thread_key]['message_count'] == 1
        assert 'search' in nlu_service.conversation_threads[thread_key]['intents']

    @pytest.mark.asyncio
    async def test_fallback_intent_detection(self, nlu_service):
        """Test fallback intent detection"""
        # Test greeting
        intent = nlu_service._fallback_intent_detection("Hello there!")
        assert intent.primary == "greet"

        # Test question
        intent = nlu_service._fallback_intent_detection("What is the best SUV?")
        assert intent.primary == "information"

        # Test search
        intent = nlu_service._fallback_intent_detection("I need to find a car")
        assert intent.primary == "search"

    @pytest.mark.asyncio
    async def test_regex_entity_extraction(self, nlu_service):
        """Test regex-based entity extraction"""
        message = "Budget is $25,000 and I want a 2023 model"
        entities = nlu_service._regex_entity_extraction(message)

        # Should extract price and year
        entity_values = [e.value for e in entities]
        assert 25000 in entity_values
        assert 2023 in entity_values

    @pytest.mark.asyncio
    async def test_entity_normalization(self, nlu_service):
        """Test entity normalization and deduplication"""
        from src.conversation.nlu_service import Entity

        entities = [
            Entity(type=EntityType.VEHICLE_TYPE, value="SUV", confidence=0.8),
            Entity(type=EntityType.VEHICLE_TYPE, value="suv", confidence=0.9),
            Entity(type=EntityType.BRAND, value="Toyota", confidence=0.85),
            Entity(type=EntityType.BRAND, value="Toyota", confidence=0.7)
        ]

        normalized = nlu_service._normalize_entities(entities)

        # Should deduplicate
        assert len(normalized) == 2
        assert len([e for e in normalized if e.type == EntityType.VEHICLE_TYPE]) == 1
        assert len([e for e in normalized if e.type == EntityType.BRAND]) == 1
        # Keep higher confidence
        suv_entity = next(e for e in normalized if e.type == EntityType.VEHICLE_TYPE)
        assert suv_entity.confidence == 0.9

    @pytest.mark.asyncio
    async def test_time_sensitivity_detection(self, nlu_service):
        """Test time-sensitive response detection"""
        # Create intent and entities
        intent = Intent(primary="information", urgency="high")
        entities = [
            Entity(type=EntityType.VEHICLE_TYPE, value="urgent request", confidence=1.0)
        ]

        is_sensitive = nlu_service._is_time_sensitive(intent, entities)
        assert is_sensitive == True

        # Test non-urgent
        intent = Intent(primary="search", urgency="normal")
        is_sensitive = nlu_service._is_time_sensitive(intent, [])
        assert is_sensitive == False


@pytest.mark.asyncio
async def test_nlu_integration():
    """Integration test for NLU service with all components"""
    # Create mock clients
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    zep_client = Mock(spec=ZepClient)
    zep_client.initialized = True

    # Mock Zep responses
    zep_client.get_conversation_history = AsyncMock(return_value=[])
    zep_client.search_conversations = AsyncMock(return_value=[])
    zep_client._extract_user_knowledge = AsyncMock(return_value={})
    zep_client._extract_user_preferences = AsyncMock(return_value={})

    # Mock Groq responses
    groq_client.generate_response = AsyncMock(
        side_effect=[
            # Intent analysis
            {
                'success': True,
                'response': '{"primary_intent": "search", "confidence": 0.95, "requires_data": true, "urgency": "normal"}'
            },
            # Entity extraction
            {
                'success': True,
                'response': '[{"type": "vehicle_type", "value": "SUV", "confidence": 0.9}, {"type": "price", "value": 30000, "confidence": 0.95}]'
            }
        ]
    )

    # Create service
    service = NLUService(groq_client=groq_client, zep_client=zep_client)
    await service.initialize()

    # Test complete analysis
    message = "I need a safe SUV under $30,000 for my family"
    result = await service.analyze_message("user123", message)

    # Verify result
    assert isinstance(result, NLUResult)
    assert result.intent.primary == "search"
    assert result.intent.confidence > 0.9
    assert len(result.entities) > 0


if __name__ == "__main__":
    pytest.main([__file__])