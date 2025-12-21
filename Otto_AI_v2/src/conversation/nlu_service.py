"""
Natural Language Understanding Service for Otto AI
Handles intent detection, entity extraction, and semantic understanding
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio

from src.conversation.groq_client import GroqClient
from src.memory.zep_client import ZepClient, ConversationContext, Message

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Represents a detected user intent"""
    primary: str  # 'search', 'compare', 'advice', 'information', 'greet', 'farewell'
    secondary: Optional[str] = None  # Optional secondary intent
    confidence: float = 0.0
    requires_data: bool = False
    urgency: str = 'normal'  # 'low', 'normal', 'high'


@dataclass
class Entity:
    """Represents an extracted entity"""
    type: str  # 'vehicle_type', 'brand', 'model', 'price', 'feature', etc.
    value: Any
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserPreference:
    """Represents a user preference extracted from conversation"""
    category: str  # 'budget', 'vehicle_type', 'feature', 'brand', etc.
    value: Any
    weight: float = 1.0  # Importance weight (0.0 to 1.0)
    source: str = 'explicit'  # 'explicit', 'implicit', 'inferred'
    extracted_at: datetime = None

    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.now()


@dataclass
class NLUResult:
    """Complete NLU analysis result"""
    intent: Intent
    entities: List[Entity]
    preferences: List[UserPreference]
    sentiment: str  # 'positive', 'neutral', 'negative'
    emotional_state: Optional[str] = None  # 'excited', 'frustrated', 'confused', etc.
    response_time_sensitive: bool = False
    context_relevance_score: float = 0.0


class NLUService:
    """Natural Language Understanding Service for Otto AI"""

    def __init__(
        self,
        groq_client: GroqClient,
        zep_client: Optional[ZepClient] = None,
        cache: Optional[Any] = None
    ):
        self.groq_client = groq_client
        self.zep_client = zep_client
        self.cache = cache
        self.initialized = False

        # Vehicle feature taxonomy
        self.vehicle_taxonomy = self._initialize_vehicle_taxonomy()

        # Conversation state tracking
        self.conversation_threads: Dict[str, Dict[str, Any]] = {}

        # Context ranking weights
        self.context_weights = {
            'recency': 0.4,  # How recent the context is
            'relevance': 0.3,  # Semantic similarity to current query
            'importance': 0.2,  # User-stated importance
            'frequency': 0.1  # How often mentioned
        }

    async def initialize(self) -> bool:
        """Initialize the NLU service"""
        try:
            # Test Groq client
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            self.initialized = True
            logger.info("NLU Service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize NLU service: {e}")
            return False

    async def analyze_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[ConversationContext] = None
    ) -> NLUResult:
        """
        Perform complete NLU analysis on a user message
        """
        if not self.initialized:
            raise Exception("NLU service not initialized")

        try:
            # Get conversation context
            if not context:
                context = await self._get_enhanced_context(user_id, message, session_id)

            # Perform analysis in parallel for efficiency
            intent_task = self._detect_intent(message, context)
            entities_task = self._extract_entities(message, context)
            preferences_task = self._extract_preferences(message, context)
            sentiment_task = self._analyze_sentiment(message, context)

            # Wait for all analyses
            intent, entities, preferences, sentiment = await asyncio.gather(
                intent_task, entities_task, preferences_task, sentiment_task
            )

            # Calculate context relevance
            relevance_score = self._calculate_context_relevance(message, context)

            # Detect emotional state
            emotional_state = self._detect_emotional_state(message, sentiment, context)

            # Determine if response time is critical
            time_sensitive = self._is_time_sensitive(intent, entities)

            # Create result
            result = NLUResult(
                intent=intent,
                entities=entities,
                preferences=preferences,
                sentiment=sentiment,
                emotional_state=emotional_state,
                response_time_sensitive=time_sensitive,
                context_relevance_score=relevance_score
            )

            # Update conversation thread
            await self._update_conversation_thread(user_id, message, result, session_id)

            return result

        except Exception as e:
            logger.error(f"Error in NLU analysis: {e}")
            # Return fallback result
            return NLUResult(
                intent=Intent(primary='question', confidence=0.5),
                entities=[],
                preferences=[],
                sentiment='neutral'
            )

    async def _detect_intent(
        self,
        message: str,
        context: ConversationContext
    ) -> Intent:
        """
        Detect user intent with context awareness
        """

        # Build context for intent detection
        context_messages = []

        # Add recent conversation for context
        if context.working_memory:
            for msg in context.working_memory[-3:]:  # Last 3 messages
                context_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add user preferences
        if context.user_preferences:
            context_messages.append({
                "role": "system",
                "content": f"User preferences: {json.dumps(context.user_preferences)}"
            })

        # Build enhanced prompt for intent detection
        system_prompt = """You are Otto AI's intent analyzer. Analyze the user's message considering the conversation context.

Primary intent categories:
- search: User wants to find/search for vehicles
- compare: User wants to compare multiple vehicles
- advice: User seeks recommendations or advice
- information: User asks for information about vehicles/features
- greet: User is greeting or starting conversation
- farewell: User is ending conversation
- clarify: User needs clarification on previous responses
- navigate: User wants to navigate the app/interface

Consider the conversation context to disambiguate intents.

Respond with JSON:
{
    "primary_intent": "category",
    "secondary_intent": "category" | null,
    "confidence": 0.95,
    "requires_data": true/false,
    "urgency": "low/normal/high",
    "reasoning": "brief explanation"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            *context_messages,
            {"role": "user", "content": message}
        ]

        response = await self.groq_client.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=150
        )

        if response['success'] and response['response']:
            try:
                # Extract JSON
                content = response['response']
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    analysis = json.loads(json_str)

                    return Intent(
                        primary=analysis.get('primary_intent', 'information'),
                        secondary=analysis.get('secondary_intent'),
                        confidence=analysis.get('confidence', 0.5),
                        requires_data=analysis.get('requires_data', False),
                        urgency=analysis.get('urgency', 'normal')
                    )
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent JSON: {content}")

        # Fallback: rule-based intent detection
        return self._fallback_intent_detection(message)

    async def _extract_entities(
        self,
        message: str,
        context: ConversationContext
    ) -> List[Entity]:
        """
        Extract vehicle-related entities from message
        """

        entities = []

        # Use AI for entity extraction
        system_prompt = """Extract vehicle-related entities from the message.

Entity types to extract:
- vehicle_type: SUV, sedan, truck, electric, hybrid, etc.
- brand: Toyota, Honda, Ford, Tesla, etc.
- model: Camry, F-150, Model 3, etc.
- price: budget ranges or specific prices
- feature: AWD, leather seats, sunroof, etc.
- location: cities, states, regions
- fuel_type: gas, electric, hybrid, diesel
- year: vehicle year or year range
- color: vehicle color preferences
- family_size: number of people

Respond with JSON array:
[
    {
        "type": "entity_type",
        "value": "extracted_value",
        "confidence": 0.95,
        "metadata": {"original_text": "text from message"}
    }
]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract entities from: {message}"}
        ]

        response = await self.groq_client.generate_response(
            messages=messages,
            temperature=0.2,
            max_tokens=300
        )

        if response['success'] and response['response']:
            try:
                content = response['response']
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    extracted = json.loads(json_str)

                    for item in extracted:
                        entities.append(Entity(
                            type=item.get('type'),
                            value=item.get('value'),
                            confidence=item.get('confidence', 0.5),
                            metadata=item.get('metadata')
                        ))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse entities JSON: {content}")

        # Add regex-based extraction for common patterns
        entities.extend(self._regex_entity_extraction(message))

        # Normalize and deduplicate entities
        entities = self._normalize_entities(entities)

        return entities

    async def _extract_preferences(
        self,
        message: str,
        context: ConversationContext
    ) -> List[UserPreference]:
        """
        Extract user preferences from message and context
        """

        preferences = []

        # Extract from current message
        message_prefs = self._extract_message_preferences(message)
        preferences.extend(message_prefs)

        # Infer preferences from context
        if context.working_memory:
            implicit_prefs = self._infer_implicit_preferences(context)
            preferences.extend(implicit_prefs)

        # Update existing preferences with new information
        if context.user_preferences:
            updated_prefs = self._update_existing_preferences(
                preferences,
                context.user_preferences
            )
            preferences.extend(updated_prefs)

        return preferences

    def _initialize_vehicle_taxonomy(self) -> Dict[str, Any]:
        """
        Initialize vehicle feature taxonomy for better understanding
        """
        return {
            'vehicle_types': {
                'suv': ['crossover', 'compact suv', 'midsize suv', 'fullsize suv'],
                'sedan': ['compact sedan', 'midsize sedan', 'fullsize sedan', 'luxury sedan'],
                'truck': ['pickup truck', 'compact truck', 'fullsize truck'],
                'electric': ['ev', 'electric vehicle', 'battery electric'],
                'hybrid': ['hybrid vehicle', 'plug-in hybrid', 'phev'],
                'sports_car': ['coupe', 'convertible', 'sports car'],
                'minivan': ['van', 'minivan', 'passenger van'],
                'hatchback': ['compact hatchback', 'hot hatch']
            },
            'features': {
                'safety': ['airbags', 'abs', 'traction control', 'lane assist', 'blind spot monitoring'],
                'comfort': ['leather seats', 'heated seats', 'climate control', 'sunroof'],
                'technology': ['apple carplay', 'android auto', 'bluetooth', 'navigation', 'infotainment'],
                'performance': ['awd', '4wd', 'turbo', 'sport mode', 'paddle shifters'],
                'efficiency': ['eco mode', 'start-stop', 'regenerative braking']
            },
            'price_ranges': {
                'budget': {'min': 0, 'max': 25000},
                'affordable': {'min': 20000, 'max': 35000},
                'mid_range': {'min': 30000, 'max': 50000},
                'premium': {'min': 45000, 'max': 75000},
                'luxury': {'min': 70000, 'max': 150000},
                'exotic': {'min': 150000, 'max': 1000000}
            }
        }

    async def _get_enhanced_context(
        self,
        user_id: str,
        current_query: str,
        session_id: Optional[str] = None
    ) -> ConversationContext:
        """
        Get enhanced context with semantic search and ranking
        """
        if not self.zep_client or not self.zep_client.initialized:
            return ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )

        try:
            # Get recent working memory
            working_memory = await self.zep_client.get_conversation_history(
                user_id=user_id,
                session_id=session_id,
                limit=10
            )

            # Get semantically relevant past conversations
            episodic_memory = await self.zep_client.search_conversations(
                user_id=user_id,
                query=current_query,
                limit=5
            )

            # Rank and filter context based on relevance
            ranked_context = self._rank_context_relevance(
                working_memory,
                episodic_memory,
                current_query
            )

            # Extract semantic memory (user knowledge)
            semantic_memory = await self._build_semantic_memory(user_id)

            # Extract and weight user preferences
            user_preferences = await self._extract_weighted_preferences(
                ranked_context['working_memory'],
                semantic_memory
            )

            return ConversationContext(
                working_memory=ranked_context['working_memory'],
                episodic_memory=ranked_context['episodic_memory'],
                semantic_memory=semantic_memory,
                user_preferences=user_preferences
            )

        except Exception as e:
            logger.error(f"Failed to get enhanced context: {e}")
            return ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )

    def _rank_context_relevance(
        self,
        working_memory: List[Message],
        episodic_memory: List[Dict[str, Any]],
        current_query: str
    ) -> Dict[str, Any]:
        """
        Rank context items by relevance to current query
        """

        # Calculate recency scores for working memory
        now = datetime.now()
        scored_working = []

        for msg in working_memory:
            recency_score = 1.0
            if msg.created_at:
                hours_ago = (now - msg.created_at).total_seconds() / 3600
                recency_score = max(0.1, 1.0 - (hours_ago / 24))  # Decay over 24 hours

            # Simple keyword relevance
            query_words = set(current_query.lower().split())
            msg_words = set(msg.content.lower().split())
            overlap = len(query_words & msg_words) / max(len(query_words), 1)

            total_score = (
                self.context_weights['recency'] * recency_score +
                self.context_weights['relevance'] * overlap
            )

            scored_working.append((msg, total_score))

        # Sort by score and keep top messages
        scored_working.sort(key=lambda x: x[1], reverse=True)
        ranked_working = [msg for msg, score in scored_working[:10]]

        # Score episodic memories
        scored_episodic = []
        for memory in episodic_memory:
            # Use Zep's relevance score
            zep_score = memory.get('score', 0.5)

            # Adjust for recency
            if memory.get('message', {}).get('created_at'):
                created_at = datetime.fromisoformat(memory['message']['created_at'])
                hours_ago = (now - created_at).total_seconds() / 3600
                recency_adj = max(0.1, 1.0 - (hours_ago / 168))  # Decay over a week
                zep_score *= recency_adj

            scored_episodic.append((memory, zep_score))

        # Sort and keep top episodic memories
        scored_episodic.sort(key=lambda x: x[1], reverse=True)
        ranked_episodic = [mem for mem, score in scored_episodic[:5]]

        return {
            'working_memory': ranked_working,
            'episodic_memory': ranked_episodic
        }

    async def _build_semantic_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Build semantic memory from user's conversation history
        """
        # This would use Zep's knowledge graph features
        # For now, return structured user knowledge
        return {
            'vehicle_knowledge': {},  # What user knows about vehicles
            'stated_preferences': {},  # Explicit preferences
            'behavioral_patterns': {},  # Inferred patterns
            'conversation_style': {},  # How user converses
            'decision_factors': {}  # What influences user decisions
        }

    async def _extract_weighted_preferences(
        self,
        working_memory: List[Message],
        semantic_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and weight user preferences from context
        """

        preferences = {}

        # Extract from recent messages with weighting
        for i, msg in enumerate(working_memory):
            if msg.role == 'user':
                # More recent messages get higher weight
                recency_weight = 1.0 - (i * 0.1)

                # Extract preferences using pattern matching
                extracted = self._preference_extraction_patterns(msg.content)

                for category, value in extracted.items():
                    if category not in preferences:
                        preferences[category] = []

                    preferences[category].append({
                        'value': value,
                        'weight': recency_weight,
                        'source': 'conversation',
                        'timestamp': msg.created_at or datetime.now()
                    })

        # Aggregate and rank preferences
        aggregated = {}
        for category, items in preferences.items():
            # Count occurrences and sum weights
            value_counts = {}
            total_weights = {}

            for item in items:
                val = str(item['value'])
                value_counts[val] = value_counts.get(val, 0) + 1
                total_weights[val] = total_weights.get(val, 0) + item['weight']

            # Sort by weighted score
            sorted_values = sorted(
                value_counts.items(),
                key=lambda x: total_weights[x[0]],
                reverse=True
            )

            aggregated[category] = [
                {
                    'value': val,
                    'confidence': total_weights[val] / max(sum(total_weights.values()), 1),
                    'frequency': count
                }
                for val, count in sorted_values[:3]  # Top 3 per category
            ]

        return aggregated

    def _preference_extraction_patterns(self, message: str) -> Dict[str, Any]:
        """
        Extract preferences using pattern matching
        """
        message_lower = message.lower()
        preferences = {}

        # Budget patterns
        budget_patterns = [
            (r'under \$?([0-9,]+)', 'max_budget'),
            (r'below \$?([0-9,]+)', 'max_budget'),
            (r'around \$?([0-9,]+)', 'target_budget'),
            (r'between \$?([0-9,]+) and \$?([0-9,]+)', 'budget_range'),
            (r'budget is \$?([0-9,]+)', 'max_budget')
        ]

        for pattern, pref_type in budget_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if pref_type == 'budget_range':
                    preferences['budget'] = {
                        'min': int(match.group(1).replace(',', '')),
                        'max': int(match.group(2).replace(',', ''))
                    }
                else:
                    preferences[pref_type] = int(match.group(1).replace(',', ''))
                break

        # Vehicle type patterns
        for vtype, synonyms in self.vehicle_taxonomy['vehicle_types'].items():
            if vtype in message_lower or any(syn in message_lower for syn in synonyms):
                preferences.setdefault('vehicle_types', []).append(vtype)

        # Feature patterns
        for ftype, features in self.vehicle_taxonomy['features'].items():
            for feature in features:
                if feature in message_lower:
                    preferences.setdefault('features', []).append(feature)

        # Brand patterns
        brands = ['toyota', 'honda', 'ford', 'chevrolet', 'tesla', 'bmw', 'mercedes', 'audi', 'hyundai', 'kia']
        for brand in brands:
            if brand in message_lower:
                preferences.setdefault('brands', []).append(brand)

        # Family size patterns
        family_patterns = [
            (r'family of (\d+)', 'family_size'),
            (r'(\d+) kids?', 'family_size'),
            (r'(\d+) people', 'family_size')
        ]

        for pattern, pref_type in family_patterns:
            match = re.search(pattern, message_lower)
            if match:
                preferences[pref_type] = int(match.group(1))
                break

        return preferences

    def _fallback_intent_detection(self, message: str) -> Intent:
        """
        Fallback rule-based intent detection
        """
        message_lower = message.lower()

        # Greeting patterns
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
            return Intent(primary='greet', confidence=0.9)

        # Farewell patterns
        if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'thanks', 'thank you']):
            return Intent(primary='farewell', confidence=0.9)

        # Question patterns
        if any(message_lower.startswith(q) for q in ['what', 'how', 'when', 'where', 'why', 'which', 'who']):
            return Intent(primary='information', confidence=0.8)

        # Search patterns
        if any(word in message_lower for word in ['looking for', 'search', 'find', 'show me', 'need']):
            return Intent(primary='search', confidence=0.8, requires_data=True)

        # Compare patterns
        if any(word in message_lower for word in ['compare', 'difference', 'versus', 'vs', 'or']):
            return Intent(primary='compare', confidence=0.8)

        # Advice patterns
        if any(word in message_lower for word in ['recommend', 'suggest', 'advice', 'what should']):
            return Intent(primary='advice', confidence=0.8)

        # Default
        return Intent(primary='information', confidence=0.5)

    def _regex_entity_extraction(self, message: str) -> List[Entity]:
        """
        Extract entities using regex patterns
        """
        entities = []

        # Price extraction
        price_patterns = [
            r'\$([0-9,]+)',
            r'([0-9,]+) dollars?',
            r'([0-9,]+) bucks?'
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                price = int(match.replace(',', ''))
                if 1000 <= price <= 200000:  # Reasonable vehicle price range
                    entities.append(Entity(
                        type='price',
                        value=price,
                        confidence=0.9,
                        metadata={'extracted_by': 'regex'}
                    ))

        # Year extraction
        year_matches = re.findall(r'\b(20[0-2][0-9])\b', message)
        for year in year_matches:
            year_int = int(year)
            if 2000 <= year_int <= datetime.now().year + 1:  # Reasonable year range
                entities.append(Entity(
                    type='year',
                    value=year_int,
                    confidence=0.8,
                    metadata={'extracted_by': 'regex'}
                ))

        return entities

    def _normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Normalize and deduplicate entities
        """
        normalized = {}

        for entity in entities:
            key = f"{entity.type}:{entity.value}"
            if key not in normalized or entity.confidence > normalized[key].confidence:
                normalized[key] = entity

        return list(normalized.values())

    async def _analyze_sentiment(
        self,
        message: str,
        context: ConversationContext
    ) -> str:
        """
        Analyze message sentiment
        """

        # Simple keyword-based sentiment analysis
        positive_words = ['great', 'excellent', 'perfect', 'love', 'awesome', 'good', 'nice']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'poor', 'disappointing']

        message_lower = message.lower()

        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _detect_emotional_state(
        self,
        message: str,
        sentiment: str,
        context: ConversationContext
    ) -> Optional[str]:
        """
        Detect user's emotional state
        """
        message_lower = message.lower()

        # Excitement indicators
        if any(word in message_lower for word in ['excited', 'can\'t wait', 'really', 'definitely', 'absolutely']):
            return 'excited'

        # Frustration indicators
        if any(word in message_lower for word in ['confused', 'don\'t understand', 'help', 'stuck']):
            return 'confused'

        # Urgency indicators
        if any(word in message_lower for word in ['urgent', 'asap', 'need now', 'quickly']):
            return 'urgent'

        # Consider sentiment
        if sentiment == 'negative':
            return 'frustrated'

        return None

    def _is_time_sensitive(
        self,
        intent: Intent,
        entities: List[Entity]
    ) -> bool:
        """
        Determine if response requires fast processing
        """

        # High urgency intent
        if intent.urgency == 'high':
            return True

        # Urgency in entities
        urgent_entities = ['urgent', 'asap', 'emergency', 'immediately']
        for entity in entities:
            if isinstance(entity.value, str):
                if any(word in entity.value.lower() for word in urgent_entities):
                    return True

        return False

    def _calculate_context_relevance(
        self,
        message: str,
        context: ConversationContext
    ) -> float:
        """
        Calculate how relevant the context is to current message
        """

        if not context.working_memory:
            return 0.0

        # Simple relevance calculation
        # In production, this would use semantic similarity
        recent_messages = [msg.content for msg in context.working_memory[-3:]]

        # Word overlap scoring
        message_words = set(message.lower().split())
        context_words = set()

        for msg in recent_messages:
            context_words.update(msg.lower().split())

        overlap = len(message_words & context_words)
        relevance = overlap / max(len(message_words), 1)

        return min(relevance, 1.0)

    async def _update_conversation_thread(
        self,
        user_id: str,
        message: str,
        nlu_result: NLUResult,
        session_id: Optional[str] = None
    ):
        """
        Update conversation thread tracking
        """

        thread_key = f"{user_id}:{session_id or 'default'}"

        if thread_key not in self.conversation_threads:
            self.conversation_threads[thread_key] = {
                'started_at': datetime.now(),
                'last_activity': datetime.now(),
                'message_count': 0,
                'intents': [],
                'topics': [],
                'entities': []
            }

        thread = self.conversation_threads[thread_key]

        # Update thread info
        thread['last_activity'] = datetime.now()
        thread['message_count'] += 1
        thread['intents'].append(nlu_result.intent.primary)

        # Add entities
        for entity in nlu_result.entities:
            if entity.type not in [e['type'] for e in thread['entities'][-10:]]:
                thread['entities'].append({
                    'type': entity.type,
                    'value': entity.value,
                    'mentioned_at': datetime.now()
                })

        # Keep only recent history
        thread['intents'] = thread['intents'][-20:]
        thread['entities'] = thread['entities'][-50:]

    def _extract_message_preferences(self, message: str) -> List[UserPreference]:
        """
        Extract preferences from a single message
        """
        preferences = []
        extracted = self._preference_extraction_patterns(message)

        for category, value in extracted.items():
            preferences.append(UserPreference(
                category=category,
                value=value,
                weight=1.0,  # Explicit preferences have full weight
                source='explicit'
            ))

        return preferences

    def _infer_implicit_preferences(self, context: ConversationContext) -> List[UserPreference]:
        """
        Infer implicit preferences from context
        """
        preferences = []

        # Analyze patterns in working memory
        if context.working_memory:
            # Look for repeated mentions
            entity_counts = {}

            for msg in context.working_memory:
                if msg.role == 'user':
                    # Extract entities from message
                    msg_entities = self._regex_entity_extraction(msg.content)
                    for entity in msg_entities:
                        key = f"{entity.type}:{entity.value}"
                        entity_counts[key] = entity_counts.get(key, 0) + 1

            # Create preferences for frequently mentioned entities
            for key, count in entity_counts.items():
                if count >= 2:  # Mentioned at least twice
                    entity_type, value = key.split(':', 1)
                    preferences.append(UserPreference(
                        category=f"implicit_{entity_type}",
                        value=value,
                        weight=min(count / 5, 1.0),  # Weight based on frequency
                        source='implicit'
                    ))

        return preferences

    def _update_existing_preferences(
        self,
        new_preferences: List[UserPreference],
        existing_preferences: Dict[str, Any]
    ) -> List[UserPreference]:
        """
        Update existing preferences with new information
        """
        updated = []

        for pref in new_preferences:
            # Check if this preference already exists
            if pref.category in existing_preferences:
                # Update weight based on reinforcement
                existing = existing_preferences[pref.category]
                if isinstance(existing, list):
                    # Multiple values for this category
                    for item in existing:
                        if item.get('value') == pref.value:
                            # Reinforce existing preference
                            updated.append(UserPreference(
                                category=pref.category,
                                value=pref.value,
                                weight=min(item.get('confidence', 0.5) + 0.1, 1.0),
                                source='reinforced'
                            ))
                            break
                    else:
                        # New value for existing category
                        updated.append(pref)

        return updated