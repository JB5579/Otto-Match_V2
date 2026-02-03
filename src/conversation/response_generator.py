"""
Response Generator for Otto AI
Generates contextually appropriate responses with personality
"""

import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import asyncio

from src.conversation.groq_client import GroqClient
from src.conversation.nlu_service import NLUResult, Intent, Entity, UserPreference
from src.conversation.intent_models import VehicleIntent, EntityType
from src.memory.zep_client import ConversationContext

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ResponseTemplate:
    """Template for generating responses"""
    template_id: str
    category: str
    pattern: str
    variables: List[str]
    personality_tone: str
    context_requirements: List[str]


@dataclass
class GeneratedResponse:
    """Complete generated response"""
    message: str
    response_type: str  # 'text', 'question', 'recommendation', 'clarification', 'error'
    suggestions: List[str]
    metadata: Dict[str, Any]
    personality_applied: bool
    confidence: float
    follow_up_actions: List[str]


class OttoPersonality:
    """Manages Otto AI's personality and tone"""

    def __init__(self):
        self.traits = {
            'friendliness': 0.9,  # How friendly and approachable
            'expertise': 0.85,  # Vehicle knowledge confidence
            'enthusiasm': 0.7,  # Energy level
            'helpfulness': 0.95,  # Desire to assist
            'professionalism': 0.8,  # Professional demeanor
            'patience': 0.9  # Patience with user needs
        }

        self.voice_characteristics = {
            'greeting_style': 'warm and welcoming',
            'explanation_style': 'clear and simple',
            'recommendation_style': 'thoughtful and considered',
            'question_style': 'curious and engaged'
        }

        self.adaptive_modifiers = {
            'user_frustration': -0.3,  # Tone down enthusiasm
            'user_confusion': -0.2,  # Be more patient
            'user_excitement': +0.2,  # Match energy
            'complex_topic': -0.1,  # Be clearer
            'first_time_user': +0.1  # More welcoming
        }

    def adjust_personality(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Adjust personality based on context"""
        adjusted = self.traits.copy()

        # Apply modifiers based on context
        if context.get('emotional_state') == 'frustrated':
            adjusted['enthusiasm'] += self.adaptive_modifiers['user_frustration']
            adjusted['patience'] += 0.2

        if context.get('emotional_state') == 'confused':
            adjusted['friendliness'] += 0.1
            adjusted['patience'] += 0.2

        if context.get('emotional_state') == 'excited':
            adjusted['enthusiasm'] += self.adaptive_modifiers['user_excitement']

        if context.get('is_first_time'):
            adjusted['friendliness'] += self.adaptive_modifiers['first_time_user']
            adjusted['helpfulness'] += 0.1

        # Ensure values stay in valid range
        for key in adjusted:
            adjusted[key] = max(0.0, min(1.0, adjusted[key]))

        return adjusted

    def generate_personality_prompt(self, adjusted_traits: Dict[str, float]) -> str:
        """Generate personality instructions for AI"""

        prompt = """You are Otto AI, a friendly and knowledgeable vehicle discovery assistant. """

        # Add trait-based instructions
        if adjusted_traits['friendliness'] > 0.8:
            prompt += "Be warm, friendly, and use conversational language. "

        if adjusted_traits['expertise'] > 0.8:
            prompt += "Demonstrate deep vehicle knowledge while keeping explanations simple. "

        if adjusted_traits['enthusiasm'] > 0.7:
            prompt += "Show genuine enthusiasm for helping find the perfect vehicle. "

        if adjusted_traits['patience'] > 0.8:
            prompt += "Be patient and take time to understand the user's needs. "

        prompt += """
Guidelines:
- Always be helpful and encouraging
- Ask clarifying questions when needed
- Use "we" and "let's" to create a collaborative feeling
- Share interesting facts about vehicles when relevant
- Be honest about what you don't know
- Maintain a positive, can-do attitude
- End with an open-ended question or next step suggestion"""

        return prompt


class ResponseGenerator:
    """Generates contextual responses with Otto AI personality"""

    def __init__(
        self,
        groq_client: GroqClient,
        cache: Optional[Any] = None
    ):
        self.groq_client = groq_client
        self.cache = cache
        self.initialized = False
        self.personality = OttoPersonality()

        # Initialize response templates
        self.templates = self._initialize_templates()

        # Conversation state tracking
        self.conversation_states: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> bool:
        """Initialize the response generator"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            self.initialized = True
            logger.info("Response generator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize response generator: {e}")
            return False

    async def generate_response(
        self,
        user_id: str,
        nlu_result: NLUResult,
        context: ConversationContext,
        vehicle_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> GeneratedResponse:
        """
        Generate a contextual response
        """

        if not self.initialized:
            raise Exception("Response generator not initialized")

        try:
            # Get conversation state
            conv_state = await self._get_conversation_state(user_id, session_id)

            # Adjust personality based on context
            adjusted_personality = self.personality.adjust_personality({
                'emotional_state': nlu_result.emotional_state,
                'sentiment': nlu_result.sentiment,
                'is_first_time': conv_state.get('message_count', 0) < 3
            })

            # Generate response based on intent
            response = await self._generate_by_intent(
                intent=nlu_result.intent,
                entities=nlu_result.entities,
                preferences=nlu_result.preferences,
                context=context,
                personality=adjusted_personality,
                vehicle_data=vehicle_data,
                conv_state=conv_state
            )

            # Add multi-turn coherence
            response = await self._ensure_coherence(
                response=response,
                context=context,
                conv_state=conv_state
            )

            # Validate response
            response = await self._validate_response(response, nlu_result)

            # Update conversation state
            await self._update_conversation_state(user_id, response, session_id)

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response()

    async def _generate_by_intent(
        self,
        intent: Intent,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        vehicle_data: Optional[Dict[str, Any]],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate response based on detected intent"""

        if intent.primary == 'search':
            return await self._generate_search_response(
                entities, preferences, context, personality, vehicle_data, conv_state
            )
        elif intent.primary == 'compare':
            return await self._generate_compare_response(
                entities, preferences, context, personality, conv_state
            )
        elif intent.primary == 'advice':
            return await self._generate_advice_response(
                entities, preferences, context, personality, vehicle_data, conv_state
            )
        elif intent.primary == 'information':
            return await self._generate_info_response(
                entities, preferences, context, personality, vehicle_data, conv_state
            )
        elif intent.primary == 'greet':
            return await self._generate_greeting_response(
                context, personality, conv_state
            )
        elif intent.primary == 'clarify':
            return await self._generate_clarification_response(
                entities, preferences, context, personality, conv_state
            )
        else:
            return await self._generate_general_response(
                entities, preferences, context, personality, conv_state
            )

    async def _generate_search_response(
        self,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        vehicle_data: Optional[Dict[str, Any]],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate response for search intent"""

        # Build search criteria from entities and preferences
        criteria = self._build_search_criteria(entities, preferences)

        # Check if we have enough criteria
        missing_criteria = self._identify_missing_search_criteria(criteria)

        if missing_criteria:
            # Ask for missing information
            return await self._request_missing_criteria(
                missing_criteria, personality, context
            )

        # Generate search response
        if vehicle_data and vehicle_data.get('results'):
            # We have search results
            return await self._format_search_results(
                vehicle_data['results'],
                criteria,
                personality,
                context
            )
        else:
            # Acknowledge search and indicate we're looking
            return await self._acknowledge_search(
                criteria, personality, context
            )

    async def _generate_compare_response(
        self,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate response for compare intent"""

        # Extract vehicles to compare
        vehicles_to_compare = self._extract_comparison_vehicles(entities)

        if len(vehicles_to_compare) < 2:
            # Need more vehicles to compare
            return GeneratedResponse(
                message="I'd be happy to help you compare vehicles! Could you tell me which specific vehicles you'd like to compare? For example, you could say 'Compare a Toyota RAV4 and Honda CR-V' or 'Compare electric SUVs under $40,000'.",
                response_type='question',
                suggestions=[
                    "Compare Toyota RAV4 vs Honda CR-V",
                    "Show me electric SUV comparisons",
                    "Compare luxury sedans under $40,000"
                ],
                metadata={'needs_more_vehicles': True},
                personality_applied=True,
                confidence=0.9,
                follow_up_actions=['specify_vehicles']
            )

        # Generate comparison response
        return GeneratedResponse(
            message=f"Great choice! Let's compare the {', '.join(vehicles_to_compare[:-1])} and {vehicles_to_compare[-1]}. I'll look at key factors like price, features, fuel efficiency, and reliability to help you make the best decision.",
            response_type='recommendation',
            suggestions=[
                "Show me detailed specifications",
                "Which has better resale value?",
                "What about safety ratings?"
            ],
            metadata={
                'vehicles': vehicles_to_compare,
                'comparison_points': ['price', 'features', 'efficiency', 'reliability']
            },
            personality_applied=True,
            confidence=0.85,
            follow_up_actions=['detailed_comparison']
        )

    async def _generate_advice_response(
        self,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        vehicle_data: Optional[Dict[str, Any]],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate response for advice/recommendation intent"""

        # Analyze user's situation from preferences and context
        user_situation = self._analyze_user_situation(preferences, context)

        # Generate personalized advice
        advice_prompt = f"""
Based on what you've told me, here's my recommendation:

{user_situation['summary']}

I suggest focusing on these key factors:
1. {user_situation['primary_factor']}
2. {user_situation['secondary_factor']}
3. {user_situation['tertiary_factor']}

Would you like me to show you some specific vehicles that match these criteria?"""

        return GeneratedResponse(
            message=advice_prompt,
            response_type='recommendation',
            suggestions=[
                "Show me matching vehicles",
                "Tell me more about reliability",
                "What about total cost of ownership?"
            ],
            metadata={
                'advice_type': 'recommendation',
                'factors': [
                    user_situation['primary_factor'],
                    user_situation['secondary_factor']
                ]
            },
            personality_applied=True,
            confidence=0.9,
            follow_up_actions=['show_matches']
        )

    async def _generate_info_response(
        self,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        vehicle_data: Optional[Dict[str, Any]],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate response for information request"""

        # Determine what information is being requested
        info_request = self._identify_info_request(entities, context)

        # Generate informative response
        if info_request['type'] == 'vehicle_info':
            return await self._provide_vehicle_info(
                info_request['vehicle'],
                personality,
                vehicle_data
            )
        elif info_request['type'] == 'feature_info':
            return await self._provide_feature_info(
                info_request['feature'],
                personality
            )
        else:
            return await self._provide_general_info(
                info_request['topic'],
                personality
            )

    async def _generate_greeting_response(
        self,
        context: ConversationContext,
        personality: Dict[str, float],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate greeting response"""

        if conv_state.get('message_count', 0) > 1:
            # Returning user
            greeting = "Welcome back! I'm excited to continue helping you find your perfect vehicle. "

            # Reference previous conversation if available
            if context.user_preferences:
                if 'vehicle_types' in context.user_preferences:
                    types = context.user_preferences['vehicle_types'][:2]
                    greeting += f"I remember you were interested in {', '.join(types)}. "

            greeting += "What would you like to explore today?"
        else:
            # First time user
            greeting = """Hello! I'm Otto AI, your personal vehicle discovery assistant. I'm here to help you find the perfect vehicle that matches your needs and preferences.

Think of me as your knowledgeable car expert friend who's excited to help you on this journey. What kind of vehicle are you looking for, or would you like to start by telling me about your lifestyle and needs?"""

        return GeneratedResponse(
            message=greeting,
            response_type='text',
            suggestions=[
                "I'm looking for a family SUV under $30,000",
                "Show me electric vehicles with good range",
                "Help me choose my first car",
                "I need something reliable for commuting"
            ],
            metadata={'is_greeting': True},
            personality_applied=True,
            confidence=1.0,
            follow_up_actions=['start_search']
        )

    async def _generate_clarification_response(
        self,
        entities: List[Entity],
        preferences: List[UserPreference],
        context: ConversationContext,
        personality: Dict[str, float],
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Generate clarification response"""

        # Identify what needs clarification
        ambiguous_points = self._identify_ambiguity(entities, preferences, context)

        clarification_msg = "I want to make sure I understand exactly what you're looking for. "

        if ambiguous_points:
            clarification_msg += f"Could you clarify {ambiguous_points['primary']}? "
            if ambiguous_points.get('secondary'):
                clarification_msg += f"And I'm also wondering about {ambiguous_points['secondary']}. "

        return GeneratedResponse(
            message=clarification_msg,
            response_type='question',
            suggestions=ambiguous_points.get('suggestions', []),
            metadata={'needs_clarification': True},
            personality_applied=True,
            confidence=0.8,
            follow_up_actions=['provide_clarification']
        )

    def _build_search_criteria(
        self,
        entities: List[Entity],
        preferences: List[UserPreference]
    ) -> Dict[str, Any]:
        """Build search criteria from entities and preferences"""

        criteria = {}

        # Extract from entities
        for entity in entities:
            if entity.entity_type == EntityType.VEHICLE_TYPE:
                criteria['vehicle_type'] = entity.value
            elif entity.entity_type == EntityType.BRAND:
                criteria.setdefault('brands', []).append(entity.value)
            elif entity.entity_type == EntityType.PRICE:
                if 'budget' not in criteria:
                    criteria['budget'] = {}
                if isinstance(entity.value, dict):
                    criteria['budget'].update(entity.value)
                else:
                    criteria['budget']['max'] = entity.value
            elif entity.entity_type == EntityType.FEATURE:
                criteria.setdefault('features', []).append(entity.value)
            elif entity.entity_type == EntityType.FUEL_TYPE:
                criteria['fuel_type'] = entity.value

        # Extract from preferences
        for pref in preferences:
            if pref.source == 'explicit':
                criteria[pref.category] = pref.value

        return criteria

    def _identify_missing_search_criteria(self, criteria: Dict[str, Any]) -> List[str]:
        """Identify what criteria are missing for a good search"""

        missing = []

        if 'vehicle_type' not in criteria:
            missing.append('vehicle_type')

        if 'budget' not in criteria or not criteria.get('budget'):
            missing.append('budget')

        # Optional but helpful
        if len(criteria) < 3:
            missing.append('additional_preferences')

        return missing

    async def _request_missing_criteria(
        self,
        missing: List[str],
        personality: Dict[str, float],
        context: ConversationContext
    ) -> GeneratedResponse:
        """Request missing search criteria from user"""

        questions = []

        for criteria in missing:
            if criteria == 'vehicle_type':
                questions.append("What type of vehicle interests you most (SUV, sedan, truck, etc.)?")
            elif criteria == 'budget':
                questions.append("What's your budget range?")
            elif criteria == 'additional_preferences':
                questions.append("Are there any specific features that are important to you?")

        # Build friendly question
        if len(questions) == 1:
            message = f"Great! To find you the best matches, {questions[0].lower()}"
        else:
            message = f"To help you find the perfect vehicle, I'd love to know: {' '.join(questions[:-1])}, and {questions[-1].lower()}"

        return GeneratedResponse(
            message=message,
            response_type='question',
            suggestions=self._generate_criteria_suggestions(missing),
            metadata={'missing_criteria': missing},
            personality_applied=True,
            confidence=0.9,
            follow_up_actions=['provide_criteria']
        )

    def _generate_criteria_suggestions(self, missing: List[str]) -> List[str]:
        """Generate suggestions for missing criteria"""
        suggestions = []

        if 'vehicle_type' in missing:
            suggestions.extend([
                "I'm looking for an SUV",
                "Show me sedans",
                "I need a truck"
            ])

        if 'budget' in missing:
            suggestions.extend([
                "Under $30,000",
                "Around $25,000",
                "Up to $40,000"
            ])

        if 'additional_preferences' in missing:
            suggestions.extend([
                "Good safety ratings",
                "Fuel efficient",
                "All-wheel drive"
            ])

        return suggestions[:4]  # Return top 4 suggestions

    async def _acknowledge_search(
        self,
        criteria: Dict[str, Any],
        personality: Dict[str, float],
        context: ConversationContext
    ) -> GeneratedResponse:
        """Acknowledge search and indicate we're working on it"""

        # Build acknowledgment message
        ack_msg = "I'm searching for vehicles that match your criteria. "

        # Summarize criteria
        criteria_parts = []
        if criteria.get('vehicle_type'):
            criteria_parts.append(f"{criteria['vehicle_type']}")
        if criteria.get('budget', {}).get('max'):
            criteria_parts.append(f"under ${criteria['budget']['max']:,}")
        if criteria.get('features'):
            criteria_parts.append(f"with {', '.join(criteria['features'][:2])}")

        if criteria_parts:
            ack_msg += f"You're looking for {' '.join(criteria_parts)}. "

        ack_msg += "Let me find the best options for you..."

        return GeneratedResponse(
            message=ack_msg,
            response_type='text',
            suggestions=[
                "Show me results as they come in",
                "What's most popular in this category?",
                "Are there any good deals right now?"
            ],
            metadata={'searching': True, 'criteria': criteria},
            personality_applied=True,
            confidence=0.95,
            follow_up_actions=['wait_for_results']
        )

    async def _format_search_results(
        self,
        results: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        personality: Dict[str, float],
        context: ConversationContext
    ) -> GeneratedResponse:
        """Format search results into a friendly response"""

        if not results:
            return GeneratedResponse(
                message="I couldn't find any exact matches for your criteria. Would you like me to broaden the search, or would you prefer to adjust some of your requirements?",
                response_type='question',
                suggestions=[
                    "Show me similar options",
                    "Adjust my budget",
                    "Consider other vehicle types"
                ],
                metadata={'no_results': True},
                personality_applied=True,
                confidence=0.8,
                follow_up_actions=['modify_search']
            )

        # Format top results
        top_results = results[:3]  # Show top 3

        message = f"Great! I found {len(results)} vehicles that match your criteria. Here are the top matches:\n\n"

        for i, vehicle in enumerate(top_results, 1):
            message += f"{i}. **{vehicle.get('year', '2024')} {vehicle.get('make', 'Unknown')} {vehicle.get('model', 'Unknown')}**\n"

            # Key features
            if vehicle.get('price'):
                message += f"   Price: ${vehicle['price']:,}\n"

            if vehicle.get('mpg'):
                message += f"   MPG: {vehicle['mpg']}\n"

            if vehicle.get('features'):
                top_features = vehicle['features'][:2]
                message += f"   Features: {', '.join(top_features)}\n"

            message += "\n"

        message += f"I found {len(results) - 3} more options if you'd like to see them. What would you like to know about these vehicles?"

        return GeneratedResponse(
            message=message,
            response_type='vehicle_results',
            suggestions=[
                "Tell me more about the first one",
                "Compare these options",
                "Show me all results"
            ],
            metadata={
                'result_count': len(results),
                'vehicles': top_results
            },
            personality_applied=True,
            confidence=0.95,
            follow_up_actions=['explore_results']
        )

    def _analyze_user_situation(
        self,
        preferences: List[UserPreference],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze user's situation based on preferences and context"""

        situation = {
            'summary': '',
            'primary_factor': '',
            'secondary_factor': '',
            'tertiary_factor': ''
        }

        # Analyze from preferences
        has_family = any(pref.category == 'family_size' for pref in preferences)
        has_budget = any(pref.category == 'budget' for pref in preferences)
        has_commuting = any(pref.value == 'commute_friendly' for pref in preferences)

        if has_family:
            situation['summary'] = "You're looking for a family vehicle that balances space, safety, and value."
            situation['primary_factor'] = "Safety ratings and family-friendly features"
            situation['secondary_factor'] = "Reliability and low maintenance costs"
            situation['tertiary_factor'] = "Fuel efficiency for family trips"
        elif has_budget:
            situation['summary'] = "You're budget-conscious and want the best value for your money."
            situation['primary_factor'] = "Total cost of ownership"
            situation['secondary_factor'] = "Fuel efficiency and reliability"
            situation['tertiary_factor'] = "Warranty coverage"
        elif has_commuting:
            situation['summary'] = "You need a reliable vehicle for daily commuting."
            situation['primary_factor'] = "Fuel economy and comfort"
            situation['secondary_factor'] = "Reliability ratings"
            situation['tertiary_factor'] = "Technology features for the commute"
        else:
            situation['summary'] = "You're looking for a vehicle that matches your lifestyle."
            situation['primary_factor'] = "Your daily needs and usage patterns"
            situation['secondary_factor'] = "Long-term value and reliability"
            situation['tertiary_factor'] = "Features that enhance your driving experience"

        return situation

    def _extract_comparison_vehicles(self, entities: List[Entity]) -> List[str]:
        """Extract vehicles to compare from entities"""
        vehicles = []

        for entity in entities:
            if entity.entity_type in [EntityType.BRAND, EntityType.MODEL]:
                vehicles.append(str(entity.value))

        return vehicles

    def _identify_info_request(
        self,
        entities: List[Entity],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Identify what information is being requested"""

        # Look for specific vehicle mentions
        vehicle_entities = [e for e in entities if e.entity_type in [EntityType.BRAND, EntityType.MODEL]]
        if vehicle_entities:
            return {
                'type': 'vehicle_info',
                'vehicle': vehicle_entities[0].value
            }

        # Look for feature mentions
        feature_entities = [e for e in entities if e.entity_type == EntityType.FEATURE]
        if feature_entities:
            return {
                'type': 'feature_info',
                'feature': feature_entities[0].value
            }

        # Default to general info
        return {
            'type': 'general',
            'topic': 'vehicles'
        }

    async def _ensure_coherence(
        self,
        response: GeneratedResponse,
        context: ConversationContext,
        conv_state: Dict[str, Any]
    ) -> GeneratedResponse:
        """Ensure response is coherent with conversation history"""

        # Check if response contradicts previous statements
        if context.working_memory:
            # Simple coherence check - in production would be more sophisticated
            last_assistant_msg = None
            for msg in reversed(context.working_memory):
                if msg.role == 'assistant':
                    last_assistant_msg = msg.content
                    break

            if last_assistant_msg:
                # Check for contradictions
                if "I'll search" in response.message and "already searched" in last_assistant_msg:
                    # Adjust response to acknowledge previous search
                    response.message = "Let me search for some additional options that might interest you based on what we've discussed."

        return response

    async def _validate_response(
        self,
        response: GeneratedResponse,
        nlu_result: NLUResult
    ) -> GeneratedResponse:
        """Validate response meets requirements"""

        # Check response length
        if len(response.message) > 1000:
            # Too long, truncate
            response.message = response.message[:950] + "..."

        # Check for appropriate response type
        if nlu_result.intent.primary == 'question' and response.response_type not in ['text', 'information']:
            response.response_type = 'text'

        # Ensure we have suggestions
        if not response.suggestions:
            response.suggestions = [
                "Tell me more",
                "What else should I consider?",
                "Show me some examples"
            ]

        return response

    async def _update_conversation_state(
        self,
        user_id: str,
        response: GeneratedResponse,
        session_id: Optional[str] = None
    ):
        """Update conversation state tracking"""

        state_key = f"{user_id}:{session_id or 'default'}"

        if state_key not in self.conversation_states:
            self.conversation_states[state_key] = {
                'message_count': 0,
                'last_responses': [],
                'topics_discussed': []
            }

        state = self.conversation_states[state_key]
        state['message_count'] += 1
        state['last_responses'].append({
            'type': response.response_type,
            'timestamp': datetime.now(),
            'had_suggestions': len(response.suggestions) > 0
        })

        # Keep only recent responses
        state['last_responses'] = state['last_responses'][-10:]

    async def _get_conversation_state(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversation state for user"""

        state_key = f"{user_id}:{session_id or 'default'}"
        return self.conversation_states.get(state_key, {'message_count': 0})

    def _generate_fallback_response(self) -> GeneratedResponse:
        """Generate fallback response when something goes wrong"""

        return GeneratedResponse(
            message="I'm having a bit of trouble right now, but I'm here to help! Could you try asking me again in a different way?",
            response_type='error',
            suggestions=[
                "Search for SUVs under $30,000",
                "Tell me about electric cars",
                "Help me choose a vehicle"
            ],
            metadata={'fallback': True},
            personality_applied=True,
            confidence=0.5,
            follow_up_actions=['retry']
        )

    def _initialize_templates(self) -> Dict[str, ResponseTemplate]:
        """Initialize response templates"""

        return {
            'greeting_returning': ResponseTemplate(
                template_id='greet_return',
                category='greeting',
                pattern="Welcome back! I remember you were interested in {previous_interests}. What would you like to explore today?",
                variables=['previous_interests'],
                personality_tone='warm_recognition',
                context_requirements=['conversation_history']
            ),
            'search_complete': ResponseTemplate(
                template_id='search_done',
                category='search',
                pattern="I found {count} vehicles matching your criteria! Here are the top {top_count} options. {summary}",
                variables=['count', 'top_count', 'summary'],
                personality_tone='enthusiastic_helpful',
                context_requirements=['search_results']
            ),
            'budget_discussion': ResponseTemplate(
                template_id='budget_talk',
                category='financial',
                pattern="When considering a ${budget} budget, it's good to think about total ownership costs including insurance, maintenance, and fuel. Have you considered these factors?",
                variables=['budget'],
                personality_tone='thoughtful_advisor',
                context_requirements=['user_budget']
            )
        }