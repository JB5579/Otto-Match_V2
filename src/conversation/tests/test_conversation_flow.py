"""
Tests for Conversation Flow and Integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.conversation.conversation_agent import ConversationAgent, ConversationResponse
from src.conversation.groq_client import GroqClient
from src.conversation.nlu_service import NLUResult, Intent, Entity, UserPreference
from src.conversation.intent_models import EntityType
from src.memory.zep_client import ZepClient, ConversationContext, Message


@pytest.fixture
async def conversation_agent():
    """Create conversation agent instance for testing"""
    # Mock all dependencies
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    zep_client = Mock(spec=ZepClient)
    zep_client.initialized = True

    # Create agent
    agent = ConversationAgent(groq_client=groq_client, zep_client=zep_client)

    # Initialize all mock services
    agent.groq_client.initialize = AsyncMock(return_value=True)
    agent.nlu_service.initialize = AsyncMock(return_value=True)
    agent.response_generator.initialize = AsyncMock(return_value=True)

    await agent.initialize()
    return agent


class TestConversationFlow:
    """Test cases for complete conversation flow"""

    @pytest.mark.asyncio
    async def test_first_time_user_greeting_flow(self, conversation_agent):
        """Test conversation flow for first-time user"""
        user_id = "new_user_123"
        message = "Hi, I'm looking for my first car"

        # Mock Zep to return empty context (new user)
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )

        # Mock NLU analysis
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="greet", confidence=0.95),
                entities=[],
                preferences=[],
                sentiment="positive",
                emotional_state="excited"
            )
        )

        # Mock entity extraction
        conversation_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])

        # Mock preference detection
        conversation_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])

        # Mock scenario detection
        conversation_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)

        # Mock response generation
        conversation_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="Hello! I'm Otto AI, your personal vehicle discovery assistant. I'd love to help you find your perfect first car!",
                response_type="text",
                suggestions=[
                    "I'm looking for something under $20,000",
                    "I need a reliable commuter car",
                    "Help me understand what to look for"
                ],
                metadata={},
                needs_follow_up=True
            )
        )

        # Process message
        response = await conversation_agent.process_message(user_id, message)

        # Verify response
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "text"
        assert "Otto AI" in response.message
        assert len(response.suggestions) > 0

        # Verify NLU was called
        conversation_agent.nlu_service.analyze_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_vehicle_search_flow(self, conversation_agent):
        """Test vehicle search conversation flow"""
        user_id = "search_user_456"
        message = "I need a safe family SUV under $30,000"

        # Mock NLU analysis
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.95, requires_data=True),
                entities=[
                    Entity(type=EntityType.VEHICLE_TYPE, value="SUV", confidence=0.9),
                    Entity(type=EntityType.PRICE, value=30000, confidence=0.95),
                    Entity(type=EntityType.FEATURE, value="safety", confidence=0.8)
                ],
                preferences=[
                    UserPreference(category="family_friendly", value=True, weight=0.9),
                    UserPreference(category="budget", value=30000, weight=0.95)
                ],
                sentiment="neutral",
                emotional_state=None
            )
        )

        # Mock other components
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )
        conversation_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        conversation_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
        conversation_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)

        # Mock response generation for search
        conversation_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="I'll help you find a safe family SUV under $30,000. Based on your needs, I'm looking at highly-rated options with top safety features.",
                response_type="vehicle_results",
                suggestions=[
                    "Show me the top 3 options",
                    "Which has the best safety rating?",
                    "Are there any hybrid SUVs in this range?"
                ],
                metadata={
                    "nlu_intent": "search",
                    "search_criteria": {
                        "vehicle_type": "SUV",
                        "max_price": 30000,
                        "safety_priority": True
                    }
                },
                needs_follow_up=True
            )
        )

        # Process message
        response = await conversation_agent.process_message(user_id, message)

        # Verify response
        assert response.response_type == "vehicle_results"
        assert "SUV" in response.message
        assert "$30,000" in response.message
        assert response.metadata["nlu_intent"] == "search"

    @pytest.mark.asyncio
    async def test_scenario_based_flow(self, conversation_agent):
        """Test scenario-based conversation flow"""
        user_id = "family_user_789"
        message = "I need a car for my family of 5"

        # Mock NLU
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.9),
                entities=[
                    Entity(type=EntityType.FAMILY_SIZE, value=5, confidence=0.95)
                ],
                preferences=[
                    UserPreference(category="family_size", value=5, weight=1.0)
                ],
                sentiment="neutral"
            )
        )

        # Mock scenario detection (family vehicle scenario)
        from src.conversation.template_engine import ScenarioType, ConversationTemplate
        mock_template = Mock(spec=ConversationTemplate)
        mock_template.scenario_type = ScenarioType.FAMILY_VEHICLE

        conversation_agent.scenario_manager.detect_scenario = AsyncMock(return_value=mock_template)

        # Mock other components
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )
        conversation_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        conversation_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])

        # Mock template rendering
        conversation_agent.template_engine.render_template = AsyncMock(
            return_value="For a family of 5, you'll want to look at vehicles with 3 rows of seats. How important is cargo space for you?"
        )

        # Mock response generation
        conversation_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="For a family of 5, you'll want to look at vehicles with 3 rows of seats. How important is cargo space for you?",
                response_type="question",
                suggestions=[
                    "Cargo space is very important",
                    "Moderate cargo space is fine",
                    "I mainly need passenger space"
                ],
                metadata={
                    "scenario": "family_vehicle",
                    "template_step": 1
                },
                needs_follow_up=True
            )
        )

        # Process message
        response = await conversation_agent.process_message(user_id, message)

        # Verify scenario-based response
        assert response.response_type == "question"
        assert "family of 5" in response.message
        assert response.metadata["scenario"] == "family_vehicle"

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, conversation_agent):
        """Test multi-turn conversation context retention"""
        user_id = "multi_turn_user"
        session_id = "session_001"

        # First message - establish preferences
        first_message = "I'm looking for a reliable sedan under $25,000"

        # Mock NLU for first message
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.9),
                entities=[
                    Entity(type=EntityType.VEHICLE_TYPE, value="sedan", confidence=0.9),
                    Entity(type=EntityType.PRICE, value=25000, confidence=0.95)
                ],
                preferences=[],
                sentiment="neutral"
            )
        )

        # Mock response for first message
        conversation_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="I'll help you find a reliable sedan under $25,000. Would you prefer Japanese or American brands?",
                response_type="question",
                suggestions=["Japanese brands", "American brands", "No preference"],
                metadata={},
                needs_follow_up=True
            )
        )

        # Mock other components
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )
        conversation_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        conversation_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
        conversation_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)

        # Process first message
        response1 = await conversation_agent.process_message(user_id, first_message, session_id)

        # Second message - user responds with preference
        second_message = "Japanese brands please"

        # Mock context with previous conversation
        mock_context = ConversationContext(
            working_memory=[
                Message(role="user", content=first_message, created_at=datetime.now()),
                Message(role="assistant", content=response1.message, created_at=datetime.now())
            ],
            episodic_memory=[],
            semantic_memory={},
            user_preferences={
                'vehicle_types': ['sedan'],
                'budget': {'max': 25000}
            }
        )

        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(return_value=mock_context)

        # Mock NLU for second message
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="information", confidence=0.8),
                entities=[
                    Entity(type=EntityType.BRAND, value="Japanese", confidence=0.9)
                ],
                preferences=[
                    UserPreference(category="brand_origin", value="Japanese", weight=0.8)
                ],
                sentiment="neutral",
                context_relevance_score=0.9
            )
        )

        # Mock response for second message (shows context awareness)
        conversation_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="Great choice! Japanese sedans are known for reliability. Based on your $25,000 budget and preference for Japanese brands, I'd recommend looking at the Toyota Camry, Honda Accord, or Nissan Altima. Would you like to see specific models?",
                response_type="text",
                suggestions=["Show me Camry options", "Show me Accord options", "Compare all three"],
                metadata={},
                needs_follow_up=True
            )
        )

        # Process second message
        response2 = await conversation_agent.process_message(user_id, second_message, session_id)

        # Verify context awareness
        assert "$25,000" in response2.message or "25000" in response2.message
        assert "Japanese" in response2.message
        assert response2.metadata.get('nlu_context_relevance', 0) > 0.5

    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_agent):
        """Test error handling in conversation flow"""
        user_id = "error_test_user"
        message = "Test error handling"

        # Mock NLU to raise an exception
        conversation_agent.nlu_service.analyze_message = AsyncMock(
            side_effect=Exception("NLU service error")
        )

        # Process message should handle error gracefully
        response = await conversation_agent.process_message(user_id, message)

        assert response.response_type == "error"
        assert "trouble" in response.message.lower() or "error" in response.message.lower()

    @pytest.mark.asyncio
    async def test_conversation_state_persistence(self, conversation_agent):
        """Test conversation state persistence across messages"""
        user_id = "state_test_user"

        # Initialize dialogue state
        dialogue_state = await conversation_agent._get_dialogue_state(user_id)
        assert dialogue_state.stage == 'greeting'

        # Simulate state update
        from src.conversation.nlu_service import NLUResult, Intent
        nlu_result = NLUResult(
            intent=Intent(primary="search", confidence=0.9),
            entities=[],
            preferences=[],
            sentiment="neutral"
        )

        entities = []
        preferences = []

        await conversation_agent._update_enhanced_dialogue_state(
            user_id, dialogue_state, nlu_result, entities, preferences
        )

        # Verify state update
        updated_state = await conversation_agent._get_dialogue_state(user_id)
        assert updated_state.stage == 'recommendation'
        assert updated_state.user_intent == "search"
        assert 'nlu_insights' in updated_state.collected_info


@pytest.mark.asyncio
async def test_conversation_integration():
    """Integration test for complete conversation system"""
    # Create realistic mocks
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True
    groq_client.initialize = AsyncMock(return_value=True)

    zep_client = Mock(spec=ZepClient)
    zep_client.initialized = True
    zep_client.initialize = AsyncMock(return_value=True)

    # Create agent
    agent = ConversationAgent(groq_client=groq_client, zep_client=zep_client)

    # Mock the entire initialization chain
    agent.nlu_service.initialize = AsyncMock(return_value=True)
    agent.response_generator.initialize = AsyncMock(return_value=True)
    agent.nlu_service._get_enhanced_context = AsyncMock(
        return_value=ConversationContext(
            working_memory=[],
            episodic_memory=[],
            semantic_memory={},
            user_preferences={}
        )
    )
    agent.nlu_service.analyze_message = AsyncMock(
        return_value=NLUResult(
            intent=Intent(primary="greet", confidence=0.95),
            entities=[],
            preferences=[],
            sentiment="positive"
        )
    )
    agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
    agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
    agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)
    agent.response_generator.generate_response = AsyncMock(
        return_value=ConversationResponse(
            message="Hello! I'm Otto AI. How can I help you today?",
            response_type="text",
            suggestions=[],
            metadata={},
            needs_follow_up=False
        )
    )

    # Initialize
    await agent.initialize()
    assert agent.initialized == True

    # Test conversation
    response = await agent.process_message("user123", "Hi Otto!")

    assert isinstance(response, ConversationResponse)
    assert agent.initialized == True


if __name__ == "__main__":
    pytest.main([__file__])