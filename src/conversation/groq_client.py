"""
Groq API Client for Otto.AI
Handles communication with Groq's compound-beta model for AI responses
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# Configure logging
logger = logging.getLogger(__name__)


class GroqClient:
    """Client for interacting with Groq API through OpenRouter or direct Groq"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        self.base_url = base_url or os.getenv('OPENROUTER_BASE_URL', 'https://api.openai.com/v1')
        self.client = None
        self.initialized = False
        self.model = os.getenv('GROQ_MODEL', 'groq/llama-3.1-8b-instruct:free')  # Default to free model

        # Check if we should use OpenRouter for Groq access
        if 'openrouter.ai' in self.base_url.lower():
            self.model = f"anthropic/claude-3.5-sonnet"  # Default OpenRouter model

        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not installed. Install with: pip install openai")
            return

        if not self.api_key:
            logger.warning("No API key provided for Groq/OpenRouter")
            return

    async def initialize(self) -> bool:
        """Initialize the Groq client"""
        try:
            if not OPENAI_AVAILABLE or not self.api_key:
                return False

            # Initialize client
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

            # Test with a simple request
            await self._test_connection()

            self.initialized = True
            logger.info(f"Groq client initialized with model: {self.model}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return False

    async def _test_connection(self):
        """Test connection with a minimal request"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            logger.debug("Groq connection test successful")
        except Exception as e:
            raise Exception(f"Groq connection test failed: {e}")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate AI response using Groq compound-beta"""

        if not self.initialized:
            return {
                'success': False,
                'error': 'Client not initialized',
                'response': None
            }

        try:
            # Prepare messages
            formatted_messages = []

            # Add system prompt if provided
            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add conversation messages
            formatted_messages.extend(messages)

            # Make the request
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=max_tokens or 500,
                temperature=temperature,
                tools=tools,
                stream=False
            )

            # Extract response
            response_message = completion.choices[0].message

            result = {
                'success': True,
                'response': response_message.content,
                'model': self.model,
                'usage': {
                    'prompt_tokens': completion.usage.prompt_tokens if completion.usage else 0,
                    'completion_tokens': completion.usage.completion_tokens if completion.usage else 0,
                    'total_tokens': completion.usage.total_tokens if completion.usage else 0
                },
                'finish_reason': completion.choices[0].finish_reason,
                'created_at': datetime.now().isoformat()
            }

            # Handle tool calls if present
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                result['tool_calls'] = [
                    {
                        'id': tc.id,
                        'type': tc.type,
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]

            return result

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': None
            }

    async def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming AI response"""

        if not self.initialized:
            yield "[ERROR] Client not initialized"
            return

        try:
            # Prepare messages
            formatted_messages = []

            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            formatted_messages.extend(messages)

            # Create streaming request
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                max_tokens=max_tokens or 500,
                temperature=temperature,
                stream=True
            )

            # Yield chunks
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming response error: {e}")
            yield f"[ERROR] {str(e)}"

    async def analyze_message_intent(
        self,
        message: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze user message to understand intent and extract entities"""

        system_prompt = """You are Otto AI's intent analyzer. Analyze the user's message and:
1. Determine the primary intent (search, compare, ask_question, greet, etc.)
2. Extract key entities (vehicle types, brands, budget, features, etc.)
3. Identify any emotional sentiment
4. Determine if this requires vehicle data lookup

Respond with JSON format:
{
    "intent": "search|compare|question|greet|other",
    "entities": {
        "vehicle_types": ["suv", "sedan"],
        "brands": ["toyota", "honda"],
        "budget": {"min": 20000, "max": 30000},
        "features": ["awd", "leather_seats"],
        "location": "new york"
    },
    "sentiment": "positive|neutral|negative",
    "requires_data": true|false,
    "confidence": 0.95
}"""

        # Include context if provided
        context_messages = []
        if conversation_context:
            context_messages.append({
                "role": "system",
                "content": f"Conversation context: {json.dumps(conversation_context)}"
            })

        context_messages.append({
            "role": "user",
            "content": f"Analyze this message: {message}"
        })

        response = await self.generate_response(
            messages=context_messages,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for consistent analysis
            max_tokens=200
        )

        if response['success'] and response['response']:
            try:
                # Extract JSON from response
                content = response['response']
                # Find JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    analysis = json.loads(json_str)
                    return {
                        'success': True,
                        'analysis': analysis
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent analysis JSON: {response['response']}")

        # Fallback if analysis fails
        return {
            'success': False,
            'error': 'Failed to analyze intent',
            'fallback_intent': 'question'  # Default fallback
        }

    async def generate_vehicle_search_query(
        self,
        user_message: str,
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate a structured search query based on user intent"""

        entities = intent_analysis.get('analysis', {}).get('entities', {})

        # Build search query components
        query_parts = []

        # Vehicle types
        if entities.get('vehicle_types'):
            query_parts.extend(entities['vehicle_types'])

        # Brands
        if entities.get('brands'):
            query_parts.extend(entities['brands'])

        # Features
        if entities.get('features'):
            query_parts.extend(entities['features'])

        # Convert to natural query
        if query_parts:
            search_query = " ".join(query_parts)
        else:
            # Fallback to original message
            search_query = user_message

        return search_query

    async def format_conversation_response(
        self,
        response_data: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> str:
        """Format AI response with Otto AI personality"""

        system_prompt = """You are Otto AI, a friendly and knowledgeable vehicle discovery assistant.
Your role is to help users find their perfect vehicle through natural conversation.

Guidelines:
1. Be conversational and friendly
2. Ask clarifying questions when user preferences are unclear
3. Provide helpful information about vehicles
4. Be honest about what you don't know
5. Always maintain a helpful and encouraging tone

If vehicle data is provided, incorporate it naturally into your response."""

        # Create response based on context
        if response_data.get('vehicle_results'):
            # Format vehicle recommendations
            vehicles = response_data['vehicle_results']
            context_message = f"User is looking for vehicles. Here are some matches: {json.dumps(vehicles[:3])}"
        else:
            context_message = f"User context: {json.dumps(user_context)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_message},
            {"role": "user", "content": response_data.get('original_message', '')}
        ]

        result = await self.generate_response(messages, temperature=0.8)

        if result['success']:
            return result['response']
        else:
            return "I'm here to help you find your perfect vehicle! Could you tell me more about what you're looking for?"

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'model': self.model,
            'base_url': self.base_url,
            'initialized': self.initialized,
            'capabilities': [
                'text_generation',
                'intent_analysis',
                'streaming_responses',
                'tool_calling'
            ] if self.initialized else []
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Groq client"""
        return {
            'initialized': self.initialized,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'base_url': self.base_url,
            'openai_available': OPENAI_AVAILABLE
        }