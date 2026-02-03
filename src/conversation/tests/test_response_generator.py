"""
Tests for Response Generator
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.conversation.response_generator import ResponseGenerator, GeneratedResponse, OttoPersonality
from src.conversation.groq_client import GroqClient
from src.conversation.nlu_service import NLUResult, Intent, Entity, UserPreference
from src.conversation.intent_models import EntityType
from src.memory.zep_client import ConversationContext


@pytest.fixture
async def response_generator():
    """Create response generator instance for testing"""
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    generator = ResponseGenerator(groq_client=groq_client)
    await generator.initialize()
    return generator


@pytest.fixture
def sample_nlu_result():
    """Create sample NLU result"""
    return NLUResult(
        intent=Intent(primary="search", confidence=0.95, requires_data=True),
        entities=[
            Entity(type=EntityType.VEHICLE_TYPE, value="SUV", confidence=0.9),
            Entity(type=EntityType.PRICE, value=30000, confidence=0.95)
        ],
        preferences=[
            UserPreference(category="budget", value=30000, weight=0.9)
        ],
        sentiment="neutral",
        emotional_state="excited",
        response_time_sensitive=False,
        context_relevance_score=0.8
    )


@pytest.fixture
def sample_context():
    """Create sample conversation context"""
    return ConversationContext(
        working_memory=[],
        episodic_memory=[],
        semantic_memory={},
        user_preferences={
            'vehicle_types': ['SUV'],
            'budget': {'max': 30000}
        }
    )


class TestResponseGenerator:
    """Test cases for Response Generator"""

    @pytest.mark.asyncio
    async def test_generate_search_response(self, response_generator, sample_nlu_result, sample_context):
        """Test generation of search response"""
        # Mock Groq response
        response_generator.groq_client.generate_response = AsyncMock(return_value={
            'success': True,
            'response': 'I\'ll help you find SUVs under $30,000. Let me search for the best options.'
        })

        result = await response_generator.generate_response(
            user_id="test_user",
            nlu_result=sample_nlu_result,
            context=sample_context
        )

        assert isinstance(result, GeneratedResponse)
        assert result.response_type in ['text', 'vehicle_results', 'question']
        assert result.personality_applied == True
        assert result.confidence > 0
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_generate_greeting_response(self, response_generator, sample_context):
        """Test generation of greeting response"""
        # Create greeting NLU result
        nlu_result = NLUResult(
            intent=Intent(primary="greet", confidence=1.0),
            entities=[],
            preferences=[],
            sentiment="positive"
        )

        result = await response_generator.generate_response(
            user_id="new_user",
            nlu_result=nlu_result,
            context=sample_context
        )

        assert isinstance(result, GeneratedResponse)
        assert result.response_type == 'text'
        assert 'welcome' in result.message.lower() or 'hello' in result.message.lower()
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_generate_compare_response(self, response_generator, sample_context):
        """Test generation of comparison response"""
        # Create compare NLU result
        nlu_result = NLUResult(
            intent=Intent(primary="compare", confidence=0.9),
            entities=[
                Entity(type=EntityType.BRAND, value="Toyota", confidence=0.9),
                Entity(type=EntityType.BRAND, value="Honda", confidence=0.9)
            ],
            preferences=[],
            sentiment="neutral"
        )

        result = await response_generator.generate_response(
            user_id="test_user",
            nlu_result=nlu_result,
            context=sample_context
        )

        assert isinstance(result, GeneratedResponse)
        assert 'compare' in result.message.lower() or 'versus' in result.message.lower()
        assert result.response_type == 'recommendation'

    @pytest.mark.asyncio
    async def test_build_search_criteria(self, response_generator):
        """Test building search criteria from entities and preferences"""
        entities = [
            Entity(type=EntityType.VEHICLE_TYPE, value="SUV", confidence=0.9),
            Entity(type=EntityType.BRAND, value="Toyota", confidence=0.8),
            Entity(type=EntityType.PRICE, value=30000, confidence=0.95)
        ]

        preferences = [
            UserPreference(category="safety", value=True, weight=0.9)
        ]

        criteria = response_generator._build_search_criteria(entities, preferences)

        assert criteria['vehicle_type'] == "SUV"
        assert 'Toyota' in criteria['brands']
        assert criteria['budget']['max'] == 30000
        assert criteria['safety'] == True

    @pytest.mark.asyncio
    async def test_identify_missing_search_criteria(self, response_generator):
        """Test identification of missing search criteria"""
        # Test with no criteria
        criteria = {}
        missing = response_generator._identify_missing_search_criteria(criteria)
        assert 'vehicle_type' in missing
        assert 'budget' in missing

        # Test with complete criteria
        criteria = {
            'vehicle_type': 'SUV',
            'budget': {'max': 30000}
        }
        missing = response_generator._identify_missing_search_criteria(criteria)
        assert len(missing) == 0

    @pytest.mark.asyncio
    async def test_acknowledge_search(self, response_generator):
        """Test search acknowledgment response"""
        criteria = {
            'vehicle_type': 'SUV',
            'budget': {'max': 30000}
        }

        response = await response_generator._acknowledge_search(
            criteria,
            {},
            {}
        )

        assert isinstance(response, GeneratedResponse)
        assert 'searching' in response.message.lower()
        assert response.response_type == 'text'
        assert response.metadata['searching'] == True

    @pytest.mark.asyncio
    async def test_format_search_results(self, response_generator):
        """Test formatting of search results"""
        vehicle_data = {
            'results': [
                {
                    'make': 'Toyota',
                    'model': 'RAV4',
                    'year': 2024,
                    'price': 28000,
                    'mpg': 28,
                    'features': ['AWD', 'Backup Camera']
                },
                {
                    'make': 'Honda',
                    'model': 'CR-V',
                    'year': 2024,
                    'price': 27000,
                    'mpg': 30,
                    'features': ['Safety Suite', 'Apple CarPlay']
                }
            ]
        }

        response = await response_generator._format_search_results(
            vehicle_data['results'],
            {'vehicle_type': 'SUV'},
            {},
            {}
        )

        assert isinstance(response, GeneratedResponse)
        assert response.response_type == 'vehicle_results'
        assert '2 vehicles' in response.message
        assert 'Toyota RAV4' in response.message
        assert 'Honda CR-V' in response.message

    @pytest.mark.asyncio
    async def test_analyze_user_situation(self, response_generator):
        """Test user situation analysis"""
        preferences = [
            UserPreference(category='family_size', value=4, weight=0.9),
            UserPreference(category='budget', value={'max': 30000}, weight=0.8)
        ]

        situation = response_generator._analyze_user_situation(preferences, {})

        assert 'summary' in situation
        assert 'primary_factor' in situation
        assert 'family' in situation['summary'].lower()

    @pytest.mark.asyncio
    async def test_personality_adjustment(self, response_generator):
        """Test Otto personality adjustment"""
        # Test with frustrated user
        adjusted = response_generator.personality.adjust_personality({
            'emotional_state': 'frustrated',
            'sentiment': 'negative'
        })

        assert adjusted['enthusiasm'] < response_generator.personality.traits['enthusiasm']
        assert adjusted['patience'] > response_generator.personality.traits['patience']

        # Test with excited user
        adjusted = response_generator.personality.adjust_personality({
            'emotional_state': 'excited',
            'sentiment': 'positive'
        })

        assert adjusted['enthusiasm'] > response_generator.personality.traits['enthusiasm']

    @pytest.mark.asyncio
    async def test_response_coherence(self, response_generator):
        """Test response coherence with conversation history"""
        from src.memory.zep_client import Message

        response = GeneratedResponse(
            message="I'll search for SUVs for you.",
            response_type='text',
            suggestions=[],
            metadata={},
            personality_applied=True,
            confidence=0.9,
            follow_up_actions=[]
        )

        context = {
            'working_memory': [
                Message(role='assistant', content='I already searched for SUVs and found 5 options.')
            ]
        }

        conv_state = {'message_count': 5}

        # Check coherence
        coherent_response = await response_generator._ensure_coherence(
            response,
            context,
            conv_state
        )

        assert isinstance(coherent_response, GeneratedResponse)
        # In a real implementation, this would adjust the response for coherence

    @pytest.mark.asyncio
    async def test_response_validation(self, response_generator):
        """Test response validation"""
        nlu_result = NLUResult(
            intent=Intent(primary="question", confidence=0.8),
            entities=[],
            preferences=[],
            sentiment="neutral"
        )

        response = GeneratedResponse(
            message="This is a test response",
            response_type="recommendation",  # Wrong type for question intent
            suggestions=[],
            metadata={},
            personality_applied=True,
            confidence=0.8,
            follow_up_actions=[]
        )

        # Validate should fix the response type
        validated = await response_generator._validate_response(response, nlu_result)

        assert isinstance(validated, GeneratedResponse)
        assert validated.response_type == 'text'  # Should be corrected

    @pytest.mark.asyncio
    async def test_fallback_response(self, response_generator):
        """Test fallback response generation"""
        response = response_generator._generate_fallback_response()

        assert isinstance(response, GeneratedResponse)
        assert response.response_type == 'error'
        assert 'trouble' in response.message.lower()
        assert response.confidence == 0.5


class TestOttoPersonality:
    """Test cases for Otto Personality"""

    def test_personality_initialization(self):
        """Test personality initialization"""
        personality = OttoPersonality()

        assert personality.traits['friendliness'] > 0.8
        assert personality.traits['expertise'] > 0.8
        assert personality.traits['helpfulness'] > 0.9

    def test_personality_adjustment(self):
        """Test personality adjustment based on context"""
        personality = OttoPersonality()

        # Test frustrated user adjustment
        adjusted = personality.adjust_personality({
            'emotional_state': 'frustrated'
        })
        assert adjusted['enthusiasm'] < personality.traits['enthusiasm']
        assert adjusted['patience'] > personality.traits['patience']

        # Test excited user adjustment
        adjusted = personality.adjust_personality({
            'emotional_state': 'excited'
        })
        assert adjusted['enthusiasm'] > personality.traits['enthusiasm']

        # Test first-time user adjustment
        adjusted = personality.adjust_personality({
            'is_first_time': True
        })
        assert adjusted['friendliness'] > personality.traits['friendliness']

    def test_personality_prompt_generation(self):
        """Test generation of personality prompt"""
        personality = OttoPersonality()
        adjusted_traits = personality.adjust_personality({})

        prompt = personality.generate_personality_prompt(adjusted_traits)

        assert 'Otto AI' in prompt
        assert 'friendly' in prompt.lower()
        assert 'knowledgeable' in prompt.lower()
        assert 'helpful' in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__])