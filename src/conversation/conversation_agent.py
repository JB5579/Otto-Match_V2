"""
Otto AI Conversation Agent
Core conversation processing and management for vehicle discovery
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio

from src.memory.zep_client import ZepClient, ConversationContext, Message
from src.conversation.groq_client import GroqClient
from src.conversation.nlu_service import NLUService, NLUResult, Entity, UserPreference
from src.conversation.intent_models import IntentClassifier, EntityExtractor, PreferenceDetector
from src.conversation.response_generator import ResponseGenerator, GeneratedResponse
from src.conversation.template_engine import ScenarioManager, TemplateRenderer, TemplateContext
from src.cache.multi_level_cache import MultiLevelCache

# Import new components for persistent memory
from src.memory.temporal_memory import TemporalMemoryManager, MemoryType
from src.intelligence.preference_engine import PreferenceEngine, PreferenceSource, PreferenceCategory
from src.services.profile_service import ProfileService
from src.analytics.preference_analytics import PreferenceAnalytics
from src.intelligence.conversation_summarizer import ConversationSummarizer, SummaryType

# Import new questioning modules
from src.intelligence.questioning_strategy import QuestioningStrategy, UserContext, QuestionScore
from src.intelligence.preference_conflict_detector import PreferenceConflictDetector, PreferenceConflict
from src.memory.question_memory import QuestionMemory
from src.intelligence.family_need_questioning import FamilyNeedQuestioning

# Import market data enhancer
from src.conversation.market_data_enhancer import get_market_data_enhancer

# Import external research service (Phase 2 integration)
from src.services.external_research_service import (
    get_research_service,
    ExternalResearchService,
    OwnershipCostReport,
    OwnerExperienceReport,
    LeaseVsBuyReport,
    InsuranceDeltaReport
)

# Import RAG Search Pipeline (Epic 1 integration)
from src.search.search_orchestrator import SearchOrchestrator, SearchRequest, SearchResponse, SearchResult
from src.semantic.embedding_service import OttoAIEmbeddingService

# Import voice-related components
from src.services.voice_input_service import VoiceInputService, VoiceResult
from src.models.voice_models import VoiceCommand, VoiceCommandType, parse_vehicle_command, VoiceState

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ConversationResponse:
    """Standard response structure for conversation messages"""
    message: str
    response_type: str  # 'text', 'vehicle_results', 'question', 'error'
    metadata: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    vehicle_results: Optional[List[Dict[str, Any]]] = None
    needs_follow_up: bool = False
    processing_time_ms: Optional[float] = None
    # Voice-specific fields
    voice_transcript: Optional[str] = None  # Original voice transcript
    voice_confidence: Optional[float] = None  # Confidence score of voice recognition
    voice_command: Optional[VoiceCommand] = None  # Parsed voice command
    is_voice_input: bool = False  # Whether input came from voice


@dataclass
class DialogueState:
    """Tracks the current state of the conversation"""
    stage: str  # 'greeting', 'discovery', 'refinement', 'recommendation', 'closing'
    user_intent: Optional[str] = None
    collected_info: Dict[str, Any] = None
    last_query: Optional[str] = None
    conversation_summary: Optional[str] = None


class ConversationAgent:
    """Main Otto AI conversation agent"""

    def __init__(
        self,
        zep_client: Optional[ZepClient] = None,
        groq_client: Optional[GroqClient] = None,
        cache: Optional[MultiLevelCache] = None,
        voice_service: Optional[VoiceInputService] = None
    ):
        self.zep_client = zep_client or ZepClient(cache=cache)
        self.groq_client = groq_client or GroqClient()
        self.cache = cache
        self.dialogue_states: Dict[str, DialogueState] = {}
        self.initialized = False

        # Voice input service
        self.voice_service = voice_service or VoiceInputService()
        self.voice_enabled = False  # Track if voice is currently active

        # Initialize NLU components
        self.nlu_service = NLUService(groq_client=self.groq_client, zep_client=self.zep_client, cache=cache)
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.preference_detector = PreferenceDetector()

        # Initialize response generation
        self.response_generator = ResponseGenerator(groq_client=self.groq_client, cache=cache)

        # Initialize template engine for scenarios
        self.scenario_manager = ScenarioManager()
        self.template_engine = TemplateRenderer()

        # Initialize persistent memory components
        self.temporal_memory = TemporalMemoryManager(self.zep_client)
        self.preference_engine = PreferenceEngine(self.groq_client, self.temporal_memory)
        self.profile_service = ProfileService()
        self.preference_analytics = PreferenceAnalytics(self.profile_service, self.temporal_memory)
        self.conversation_summarizer = ConversationSummarizer(self.groq_client)

        # Initialize questioning components
        self.questioning_strategy = QuestioningStrategy(
            self.groq_client,
            self.temporal_memory,
            self.preference_engine
        )
        self.conflict_detector = PreferenceConflictDetector(
            self.groq_client,
            self.preference_engine
        )
        self.question_memory = QuestionMemory(
            self.zep_client,
            self.temporal_memory
        )
        self.family_questioning = FamilyNeedQuestioning(self.groq_client)

        # Market data enhancer
        self.market_enhancer = get_market_data_enhancer()

        # External research service (Phase 2 integration)
        self.research_service = get_research_service()
        self.research_enabled = True  # Enable external research by default

        # RAG Search Pipeline (Epic 1 integration)
        self.search_orchestrator: Optional[SearchOrchestrator] = None
        self.embedding_service: Optional[OttoAIEmbeddingService] = None
        self.rag_search_enabled = False

        # Otto AI personality settings
        self.personality = {
            'name': 'Otto AI',
            'tone': 'friendly and knowledgeable',
            'expertise': 'vehicle discovery and matching',
            'response_style': 'conversational with helpful suggestions'
        }

    async def initialize(self) -> bool:
        """Initialize the conversation agent and its dependencies"""
        try:
            # Initialize Zep client
            zep_initialized = await self.zep_client.initialize()
            if not zep_initialized:
                logger.warning("Zep client initialization failed, continuing without memory")

            # Initialize Groq client
            groq_initialized = await self.groq_client.initialize()
            if not groq_initialized:
                logger.error("Groq client initialization failed - cannot continue")
                return False

            # Initialize NLU service
            nlu_initialized = await self.nlu_service.initialize()
            if not nlu_initialized:
                logger.error("NLU service initialization failed - cannot continue")
                return False

            # Initialize response generator
            response_initialized = await self.response_generator.initialize()
            if not response_initialized:
                logger.error("Response generator initialization failed - cannot continue")
                return False

            # Initialize temporal memory manager
            temporal_initialized = await self.temporal_memory.initialize()
            if not temporal_initialized:
                logger.warning("Temporal memory manager initialization failed, continuing without enhanced memory")

            # Initialize preference engine
            preference_initialized = await self.preference_engine.initialize()
            if not preference_initialized:
                logger.warning("Preference engine initialization failed, continuing without preference learning")

            # Initialize profile service
            profile_initialized = await self.profile_service.initialize()
            if not profile_initialized:
                logger.warning("Profile service initialization failed, continuing without profile management")

            # Initialize preference analytics
            analytics_initialized = await self.preference_analytics.initialize()
            if not analytics_initialized:
                logger.warning("Preference analytics initialization failed, continuing without analytics")

            # Initialize conversation summarizer
            summarizer_initialized = await self.conversation_summarizer.initialize()
            if not summarizer_initialized:
                logger.warning("Conversation summarizer initialization failed, continuing without summarization")

            # Initialize questioning components
            questioning_initialized = await self.questioning_strategy.initialize()
            if not questioning_initialized:
                logger.warning("Questioning strategy initialization failed, continuing without adaptive questions")

            conflict_initialized = await self.conflict_detector.initialize()
            if not conflict_initialized:
                logger.warning("Conflict detector initialization failed, continuing without conflict detection")

            question_memory_initialized = await self.question_memory.initialize()
            if not question_memory_initialized:
                logger.warning("Question memory initialization failed, continuing without question tracking")

            family_initialized = await self.family_questioning.initialize()
            if not family_initialized:
                logger.warning("Family questioning initialization failed, continuing without specialized family questions")

            # Initialize RAG Search Pipeline (Epic 1 integration)
            try:
                import os
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                if supabase_url and supabase_key:
                    self.embedding_service = OttoAIEmbeddingService()
                    await self.embedding_service.initialize(supabase_url, supabase_key)

                    self.search_orchestrator = SearchOrchestrator()
                    if await self.search_orchestrator.initialize(
                        supabase_url, supabase_key, self.embedding_service
                    ):
                        self.rag_search_enabled = True
                        logger.info("RAG Search Pipeline initialized (hybrid search + query expansion + re-ranking)")
                    else:
                        logger.warning("RAG Search Pipeline initialization failed, using fallback search")
                else:
                    logger.warning("Supabase credentials not found, RAG Search Pipeline disabled")
            except Exception as e:
                logger.warning(f"RAG Search Pipeline initialization failed: {e}, continuing without advanced search")

            self.initialized = True
            logger.info("Conversation agent initialized successfully with all components including questioning strategy")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize conversation agent: {e}")
            return False

    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        voice_result: Optional[VoiceResult] = None
    ) -> ConversationResponse:
        """
        Process a user message and generate an appropriate response
        """
        start_time = datetime.now()
        is_voice_input = voice_result is not None
        voice_command = None

        try:
            # Handle voice input if provided
            if is_voice_input and voice_result:
                # Parse voice command
                voice_command = parse_vehicle_command(
                    voice_result.transcript,
                    voice_result.confidence
                )

                # Add voice metadata to message
                message_with_voice = f"[VOICE: {voice_result.transcript}]"
            else:
                message_with_voice = message

            # Get or create dialogue state
            dialogue_state = await self._get_dialogue_state(user_id)

            # Store user message with voice metadata
            await self._store_message(user_id, session_id, message_with_voice, 'user')

            # Store voice interaction in temporal memory if applicable
            if is_voice_input and voice_result:
                await self._store_voice_interaction(user_id, voice_result, voice_command)

            # Get conversation context from Zep (enhanced with NLU)
            conversation_context = await self.nlu_service._get_enhanced_context(user_id, message_with_voice, session_id)

            # Perform complete NLU analysis
            nlu_result = await self.nlu_service.analyze_message(
                user_id=user_id,
                message=message_with_voice,
                session_id=session_id,
                context=conversation_context
            )

            # Enhance NLU with voice command if available
            if is_voice_input and voice_command:
                nlu_result = await self._enhance_nlu_with_voice_command(nlu_result, voice_command)

            # Update dialogue state with NLU results
            dialogue_state.user_intent = nlu_result.intent.primary
            dialogue_state.last_query = message

            # Extract entities for additional processing
            entities = await self.entity_extractor.extract_entities(message)

            # Detect preferences using enhanced preference engine
            enhanced_preferences = await self.preference_engine.extract_preferences(
                message, entities, {'emotional_state': nlu_result.emotional_state}
            )

            # Merge with traditional preference detection
            preferences = await self.preference_detector.detect_preferences(
                message, entities, {'emotional_state': nlu_result.emotional_state}
            )
            preferences.extend(enhanced_preferences)

            # Store preferences in temporal memory
            for pref in preferences:
                await self.temporal_memory.add_memory_fragment(
                    user_id=user_id,
                    content=f"Preference: {pref.category} = {pref.value}",
                    memory_type=MemoryType.SEMANTIC,
                    importance=pref.weight,
                    associated_preferences=[asdict(pref)]
                )

            # Update user profile with learned preferences
            await self.profile_service.update_profile_preferences(user_id, preferences)

            # Detect and handle preference conflicts
            conflicts = await self.conflict_detector.detect_conflicts(preferences)
            if conflicts:
                # Log conflicts for context
                for conflict in conflicts:
                    logger.info(f"Detected preference conflict: {conflict.description}")

            # Enhance conversation with market intelligence
            market_intelligence = None
            try:
                # Create context for market enhancement
                conv_context = {
                    'user_id': user_id,
                    'user_location': dialogue_state.collected_info.get('location'),
                    'intent': nlu_result.intent.primary
                }

                # Extract entities for market lookup
                entity_list = [asdict(e) for e in entities]

                # Get market intelligence
                market_intelligence = await self.market_enhancer.enhance_with_market_intelligence(
                    conversation_context=conv_context,
                    extracted_entities=entity_list
                )

                # Also check for pricing queries
                if 'price' in message.lower() or 'cost' in message.lower() or 'worth' in message.lower():
                    vehicle_info = {
                        'make': next((e['value'] for e in entity_list if e.get('type') == 'make'), None),
                        'model': next((e['value'] for e in entity_list if e.get('type') == 'model'), None),
                        'year': next((e.get('value') for e in entity_list if e.get('type') == 'year'), None)
                    }
                    if all(vehicle_info.values()):
                        pricing_analysis = await self.market_enhancer.analyze_price_query(
                            query=message,
                            vehicle_info=vehicle_info
                        )
                        if pricing_analysis:
                            market_intelligence = pricing_analysis

            except Exception as e:
                logger.error(f"Market intelligence enhancement failed: {e}")
                market_intelligence = None

            # Check for external research opportunities (Phase 2)
            external_research = None
            try:
                research_type = await self._detect_research_query(message, entities)
                if research_type:
                    logger.info(f"Detected research query: {research_type}")
                    external_research = await self._perform_external_research(
                        research_type, message, entities, user_id, dialogue_state
                    )
                    if external_research:
                        logger.info(f"External research completed: {research_type}")
            except Exception as e:
                logger.error(f"External research detection/execution failed: {e}")
                external_research = None

            # Check if we should ask questions based on conversation context
            await self._handle_questioning_strategy(
                user_id, message, session_id, dialogue_state, preferences, conflicts
            )

            # Track user behavior for adaptive learning
            await self._track_user_behavior(user_id, message, entities, nlu_result, preferences)

            # Check for scenario-based conversation
            scenario = await self.scenario_manager.detect_scenario(
                user_id, message, entities, preferences
            )

            # Generate response based on NLU and context
            generated_response = await self.response_generator.generate_response(
                user_id=user_id,
                nlu_result=nlu_result,
                context=conversation_context,
                session_id=session_id
            )

            # If scenario is active, use template engine
            if scenario:
                template_context = TemplateContext(
                    user_id=user_id,
                    variables=dialogue_state.collected_info,
                    current_step=self.scenario_manager.active_scenarios.get(user_id, {}).get('step', 0)
                )

                template_response = await self.template_engine.render_template(
                    template=scenario,
                    context=template_context,
                    message=message,
                    entities=entities,
                    preferences=preferences
                )

                # Blend template and generated response
                if nlu_result.intent.primary != 'greet':
                    generated_response.message = template_response

            # Convert GeneratedResponse to ConversationResponse
            response_metadata = {
                'nlu_intent': nlu_result.intent.primary,
                'nlu_confidence': nlu_result.intent.confidence,
                'entities': [asdict(e) for e in entities],
                'preferences': [asdict(p) for p in preferences],
                'scenario': scenario.scenario_type.value if scenario else None,
                'response_metadata': generated_response.metadata
            }

            # Add market intelligence to response if available
            if market_intelligence:
                response_metadata['market_intelligence'] = market_intelligence

                # Append market insights to response message if it's pricing-related
                if market_intelligence.get('type') in ['pricing_analysis', 'market_intelligence']:
                    if 'summary' in market_intelligence:
                        generated_response.message += f"\n\n💰 {market_intelligence['summary']}"
                    elif 'insights' in market_intelligence and market_intelligence['insights']:
                        insights_text = "\n".join([f"• {insight}" for insight in market_intelligence['insights'][:3]])
                        generated_response.message += f"\n\n📊 Market Insights:\n{insights_text}"

            # Add external research to response if available (Phase 2)
            if external_research:
                response_metadata['external_research'] = {
                    'type': external_research['type'],
                    'report': external_research['report'].dict() if hasattr(external_research['report'], 'dict') else external_research['report']
                }

                # Append research summary to response message
                if 'summary' in external_research:
                    generated_response.message += f"\n\n{external_research['summary']}"

            response = ConversationResponse(
                message=generated_response.message,
                response_type=generated_response.response_type,
                metadata=response_metadata,
                suggestions=generated_response.suggestions,
                needs_follow_up=generated_response.follow_up_actions is not None,
                processing_time_ms=None,  # Will be set below
                voice_transcript=voice_result.transcript if voice_result else None,
                voice_confidence=voice_result.confidence if voice_result else None,
                voice_command=voice_command,
                is_voice_input=is_voice_input
            )

            # Store assistant response
            await self._store_message(user_id, session_id, response.message, 'assistant')

            # Check if conversation needs summarization (every 20 messages)
            message_count = len(await self.zep_client.get_conversation_history(user_id, limit=100))
            if message_count % 20 == 0 and message_count > 0:
                await self._create_conversation_summary(user_id, session_id)

            # Update dialogue state with enhanced information
            await self._update_enhanced_dialogue_state(
                user_id, dialogue_state, nlu_result, entities, preferences
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time

            # Log performance
            if processing_time > 2000:  # > 2 seconds warning
                logger.warning(f"Slow response time for user {user_id}: {processing_time:.2f}ms")

            return response

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return ConversationResponse(
                message="I'm having trouble processing that right now. Could you please rephrase your question?",
                response_type="error",
                metadata={'error': str(e)},
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _get_dialogue_state(self, user_id: str) -> DialogueState:
        """Get or create dialogue state for user"""
        if user_id not in self.dialogue_states:
            self.dialogue_states[user_id] = DialogueState(
                stage='greeting',
                collected_info={}
            )
        return self.dialogue_states[user_id]

    async def _store_message(self, user_id: str, session_id: str, content: str, role: str):
        """Store message in Zep Cloud"""
        if self.zep_client.initialized:
            try:
                from src.memory.zep_client import ConversationData
                message = Message(
                    role=role,
                    content=content,
                    created_at=datetime.now(),
                    metadata={'user_id': user_id}
                )

                # Create conversation data with this single message
                conversation_data = ConversationData(
                    messages=[message],
                    user_id=user_id,
                    session_id=session_id
                )

                # Store in Zep
                await self.zep_client.store_conversation(user_id, conversation_data)

            except Exception as e:
                logger.error(f"Failed to store message in Zep: {e}")

    async def _get_conversation_context(self, user_id: str, current_query: str) -> ConversationContext:
        """Get conversation context from Zep"""
        if self.zep_client.initialized:
            try:
                return await self.zep_client.get_contextual_memory(user_id, current_query)
            except Exception as e:
                logger.error(f"Failed to get conversation context: {e}")

        # Return empty context if Zep is not available
        return ConversationContext(
            working_memory=[],
            episodic_memory=[],
            semantic_memory={},
            user_preferences={}
        )

    async def _generate_response_by_intent(
        self,
        user_id: str,
        message: str,
        intent: Dict[str, Any],
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Generate response based on analyzed intent"""

        intent_type = intent.get('analysis', {}).get('intent', 'question')
        entities = intent.get('analysis', {}).get('entities', {})

        if intent_type == 'greeting':
            return await self._handle_greeting(user_id, context, dialogue_state)

        elif intent_type == 'search':
            return await self._handle_search_intent(user_id, message, entities, context, dialogue_state)

        elif intent_type == 'compare':
            return await self._handle_compare_intent(user_id, message, entities, context, dialogue_state)

        elif intent_type == 'question':
            return await self._handle_question_intent(user_id, message, entities, context, dialogue_state)

        else:
            return await self._handle_general_intent(user_id, message, context, dialogue_state)

    async def _handle_greeting(
        self,
        user_id: str,
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Handle greeting messages"""

        # Check if user has history
        if context.working_memory:
            # Returning user
            greeting = f"Welcome back! I see you've been exploring vehicles with me. "
            if context.user_preferences:
                greeting += "I still remember you're interested in "
                if 'vehicle_types' in context.user_preferences:
                    greeting += f"{', '.join(context.user_preferences['vehicle_types'])}. "
            greeting += "What would you like to explore today?"
        else:
            # New user
            greeting = (
                "Hello! I'm Otto AI, your personal vehicle discovery assistant. "
                "I can help you find the perfect vehicle based on your needs and preferences. "
                "What kind of vehicle are you looking for today?"
            )

        dialogue_state.stage = 'discovery'

        return ConversationResponse(
            message=greeting,
            response_type='text',
            suggestions=[
                "I'm looking for an SUV under $30,000",
                "Show me electric vehicles with good range",
                "I need a family-friendly car"
            ],
            needs_follow_up=True
        )

    async def _handle_search_intent(
        self,
        user_id: str,
        message: str,
        entities: Dict[str, Any],
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Handle vehicle search intent using RAG pipeline"""

        # Extract search criteria from entities
        search_criteria = {
            'vehicle_types': entities.get('vehicle_types', []),
            'brands': entities.get('brands', []),
            'budget': entities.get('budget'),
            'features': entities.get('features', [])
        }

        # Build filters from extracted entities
        filters = self._build_search_filters(entities, context)

        # Generate enhanced search query
        search_query = await self.groq_client.generate_vehicle_search_query(message, entities)

        vehicle_results = []
        search_metadata = {
            'search_query': search_query,
            'criteria': search_criteria,
            'rag_enabled': self.rag_search_enabled
        }

        # Execute RAG search pipeline if enabled
        if self.rag_search_enabled and self.search_orchestrator:
            try:
                # Create search request for RAG pipeline
                search_request = SearchRequest(
                    query=message,  # Use original message for query expansion
                    filters=filters,
                    limit=10,  # Reasonable limit for conversation
                    offset=0,
                    enable_expansion=True,
                    enable_reranking=True,
                    enable_contextual=True
                )

                # Execute RAG search
                search_response: SearchResponse = await self.search_orchestrator.search(search_request)

                # Convert results to conversation format
                vehicle_results = self._format_search_results_for_conversation(search_response.results)

                # Add search metadata
                search_metadata.update({
                    'total_results': search_response.total_results,
                    'latency_ms': search_response.total_latency_ms,
                    'expanded_query': search_response.metadata.get('expanded_query'),
                    'extracted_filters': search_response.metadata.get('extracted_filters', {}),
                    'expansion_latency_ms': search_response.expansion_latency_ms,
                    'rerank_latency_ms': search_response.rerank_latency_ms
                })

                logger.info(
                    f"RAG search completed: {len(vehicle_results)} results in {search_response.total_latency_ms:.0f}ms"
                )

            except Exception as e:
                logger.error(f"RAG search failed, falling back: {e}")
                search_metadata['rag_error'] = str(e)

        # Generate response message based on results
        response_message = self._generate_search_response_message(
            search_query, vehicle_results, search_criteria
        )

        # Update dialogue state
        dialogue_state.stage = 'recommendation'
        dialogue_state.collected_info.update(search_criteria)
        dialogue_state.collected_info['last_search_results'] = len(vehicle_results)

        # Generate contextual suggestions based on results
        suggestions = self._generate_search_suggestions(vehicle_results, search_criteria)

        return ConversationResponse(
            message=response_message,
            response_type='vehicle_results',
            metadata=search_metadata,
            suggestions=suggestions,
            needs_follow_up=True,
            vehicle_results=vehicle_results
        )

    def _build_search_filters(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Build search filters from entities and context"""
        filters = {}

        # Extract make/model from entities
        if entities.get('brands'):
            filters['make'] = entities['brands'][0]
        if entities.get('models'):
            filters['model'] = entities['models'][0]

        # Extract budget/price range
        budget = entities.get('budget')
        if budget:
            if isinstance(budget, dict):
                if budget.get('max'):
                    filters['price_max'] = budget['max']
                if budget.get('min'):
                    filters['price_min'] = budget['min']
            elif isinstance(budget, (int, float)):
                filters['price_max'] = budget

        # Extract year range
        if entities.get('year_min'):
            filters['year_min'] = entities['year_min']
        if entities.get('year_max'):
            filters['year_max'] = entities['year_max']

        # Extract vehicle type
        if entities.get('vehicle_types'):
            filters['vehicle_type'] = entities['vehicle_types'][0]

        # Extract mileage
        if entities.get('mileage_max'):
            filters['mileage_max'] = entities['mileage_max']

        # Add user preferences from context if available
        if context.user_preferences:
            if not filters.get('vehicle_type') and context.user_preferences.get('vehicle_types'):
                filters['vehicle_type'] = context.user_preferences['vehicle_types'][0]

        return filters

    def _format_search_results_for_conversation(
        self,
        results: List[SearchResult]
    ) -> List[Dict[str, Any]]:
        """Format RAG search results for conversation response"""
        formatted = []
        for r in results:
            formatted.append({
                'id': r.id,
                'vin': r.vin,
                'year': r.year,
                'make': r.make,
                'model': r.model,
                'trim': r.trim,
                'vehicle_type': r.vehicle_type,
                'price': r.price,
                'price_source': r.price_source,
                'mileage': r.mileage,
                'description': r.description,
                'relevance_score': r.similarity_score,
                'match_details': {
                    'vector_score': r.vector_score,
                    'keyword_score': r.keyword_score,
                    'hybrid_score': r.hybrid_score,
                    'rerank_score': r.rerank_score
                }
            })
        return formatted

    def _generate_search_response_message(
        self,
        search_query: str,
        results: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> str:
        """Generate a natural language response for search results"""
        if not results:
            vehicle_desc = ', '.join(criteria.get('vehicle_types', [])) or 'vehicles'
            return (
                f"I searched for {search_query}, but couldn't find any exact matches. "
                f"Would you like me to broaden the search or adjust the criteria?"
            )

        count = len(results)
        top_result = results[0]

        # Build vehicle description
        vehicle_desc = f"{top_result['year']} {top_result['make']} {top_result['model']}"
        if top_result.get('trim'):
            vehicle_desc += f" {top_result['trim']}"

        # Price info
        price_info = ""
        if top_result.get('price'):
            price_info = f" priced at ${top_result['price']:,.0f}"

        if count == 1:
            return (
                f"I found a great match for you: a {vehicle_desc}{price_info}. "
                f"This vehicle has a {top_result.get('relevance_score', 0)*100:.0f}% match to your criteria."
            )
        else:
            return (
                f"I found {count} vehicles matching your search. "
                f"The top match is a {vehicle_desc}{price_info} with a "
                f"{top_result.get('relevance_score', 0)*100:.0f}% relevance score. "
                f"Would you like more details on any of these?"
            )

    def _generate_search_suggestions(
        self,
        results: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[str]:
        """Generate contextual suggestions based on search results"""
        if not results:
            return [
                "Try a different vehicle type",
                "Increase your budget range",
                "Search for similar models"
            ]

        suggestions = []

        # If we have results, suggest exploration
        if len(results) > 1:
            suggestions.append("Compare the top vehicles")

        # Suggest details on top result
        top = results[0]
        suggestions.append(f"Tell me more about the {top['year']} {top['make']} {top['model']}")

        # Suggest price analysis if price available
        if top.get('price'):
            suggestions.append("Is this a good price?")

        # Suggest alternatives
        if len(results) >= 3:
            suggestions.append("Show me different options")

        return suggestions[:4]  # Limit to 4 suggestions

    async def _handle_compare_intent(
        self,
        user_id: str,
        message: str,
        entities: Dict[str, Any],
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Handle vehicle comparison intent"""

        # For now, acknowledge comparison request
        # In production, would fetch specific vehicles to compare
        response_message = (
            "I'd be happy to help you compare vehicles! "
            "To provide the best comparison, could you tell me which specific vehicles you'd like to compare? "
            "Or if you'd like, I can suggest some popular options to compare based on your preferences."
        )

        return ConversationResponse(
            message=response_message,
            response_type='text',
            suggestions=[
                "Compare Toyota RAV4 vs Honda CR-V",
                "Show me electric SUV comparisons",
                "Compare luxury sedans under $40,000"
            ],
            needs_follow_up=True
        )

    async def _handle_question_intent(
        self,
        user_id: str,
        message: str,
        entities: Dict[str, Any],
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Handle general questions"""

        # Prepare context for Groq
        context_data = {
            'user_message': message,
            'entities': entities,
            'user_preferences': context.user_preferences,
            'recent_conversation': [
                {'role': msg.role, 'content': msg.content}
                for msg in context.working_memory[-5:]  # Last 5 messages
            ]
        }

        # Generate response using Groq
        response = await self.groq_client.format_conversation_response(
            response_data={
                'original_message': message,
                'vehicle_results': None
            },
            user_context=context_data
        )

        return ConversationResponse(
            message=response,
            response_type='text',
            needs_follow_up=True
        )

    async def _handle_general_intent(
        self,
        user_id: str,
        message: str,
        context: ConversationContext,
        dialogue_state: DialogueState
    ) -> ConversationResponse:
        """Handle general/unclear intents"""

        return ConversationResponse(
            message=(
                "I'm here to help you find your perfect vehicle! "
                "You can tell me about what you're looking for - like vehicle type, budget, "
                "or specific features that are important to you. "
                "What would you like to explore?"
            ),
            response_type='text',
            suggestions=[
                "Tell me about SUVs under $30,000",
                "I'm interested in electric vehicles",
                "Help me choose between brands"
            ],
            needs_follow_up=True
        )

    async def _detect_research_query(
        self,
        message: str,
        entities: List[Entity]
    ) -> Optional[str]:
        """
        Detect if user is asking for external research
        Returns research type: 'ownership_costs', 'owner_experience', 'lease_vs_buy', 'insurance_delta'
        """
        message_lower = message.lower()

        # Ownership cost indicators
        ownership_keywords = [
            'total cost', 'ownership cost', 'cost to own', 'annual cost',
            'maintenance cost', 'insurance cost', 'depreciation',
            'how much will it cost', 'expensive to own', 'operating cost'
        ]
        if any(keyword in message_lower for keyword in ownership_keywords):
            return 'ownership_costs'

        # Owner experience indicators
        experience_keywords = [
            'owner review', 'owner experience', 'what do owners say',
            'reliable', 'reliability', 'common problems', 'common issues',
            'satisfaction', 'owner rating', 'forum', 'real world'
        ]
        if any(keyword in message_lower for keyword in experience_keywords):
            return 'owner_experience'

        # Lease vs buy indicators
        lease_keywords = [
            'lease or buy', 'lease vs buy', 'should i lease', 'leasing',
            'finance or lease', 'better to lease', 'lease option'
        ]
        if any(keyword in message_lower for keyword in lease_keywords):
            return 'lease_vs_buy'

        # Insurance delta indicators (when comparing current to new)
        insurance_keywords = [
            'insurance cost', 'insurance premium', 'insurance change',
            'insurance increase', 'insurance difference', 'how much more insurance'
        ]
        # Check if they mentioned current vehicle
        has_current_vehicle = any(
            word in message_lower for word in ['current', 'my car', 'trading', 'upgrade from']
        )
        if any(keyword in message_lower for keyword in insurance_keywords) and has_current_vehicle:
            return 'insurance_delta'

        return None

    async def _perform_external_research(
        self,
        research_type: str,
        message: str,
        entities: List[Entity],
        user_id: str,
        dialogue_state: DialogueState
    ) -> Optional[Dict[str, Any]]:
        """
        Perform external research based on detected query type
        Returns research results formatted for conversation
        """
        if not self.research_enabled or not self.research_service:
            return None

        try:
            # Extract vehicle information from entities and dialogue state
            vehicle_info = self._extract_vehicle_info_for_research(entities, dialogue_state)

            if not vehicle_info.get('make') or not vehicle_info.get('model'):
                logger.warning("Insufficient vehicle information for research")
                return None

            # Get lifestyle profile for personalized research
            lifestyle_profile = None
            if hasattr(self.nlu_service, 'get_user_lifestyle_profile'):
                lifestyle_profile = self.nlu_service.get_user_lifestyle_profile(user_id)

            # Perform research based on type
            if research_type == 'ownership_costs':
                result = await self._research_ownership_costs(vehicle_info, lifestyle_profile)
            elif research_type == 'owner_experience':
                result = await self._research_owner_experience(vehicle_info)
            elif research_type == 'lease_vs_buy':
                result = await self._research_lease_vs_buy(vehicle_info, lifestyle_profile)
            elif research_type == 'insurance_delta':
                result = await self._research_insurance_delta(vehicle_info, lifestyle_profile, dialogue_state)
            else:
                return None

            return result

        except Exception as e:
            logger.error(f"External research failed: {e}")
            return None

    def _extract_vehicle_info_for_research(
        self,
        entities: List[Entity],
        dialogue_state: DialogueState
    ) -> Dict[str, Any]:
        """Extract vehicle info from entities and dialogue state"""
        vehicle_info = {}

        # Extract from entities
        for entity in entities:
            if hasattr(entity, 'entity_type'):
                entity_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                if entity_type == 'make':
                    vehicle_info['make'] = entity.value
                elif entity_type == 'model':
                    vehicle_info['model'] = entity.value
                elif entity_type == 'year':
                    vehicle_info['year'] = entity.value
                elif entity_type == 'trim':
                    vehicle_info['trim'] = entity.value

        # Fall back to dialogue state if needed
        if not vehicle_info.get('make') and dialogue_state.collected_info:
            # Look for last mentioned make/model in collected info
            if 'entity_make' in dialogue_state.collected_info:
                recent_make = dialogue_state.collected_info['entity_make']
                if isinstance(recent_make, list) and recent_make:
                    vehicle_info['make'] = recent_make[-1]['value']

            if 'entity_model' in dialogue_state.collected_info:
                recent_model = dialogue_state.collected_info['entity_model']
                if isinstance(recent_model, list) and recent_model:
                    vehicle_info['model'] = recent_model[-1]['value']

            if 'entity_year' in dialogue_state.collected_info:
                recent_year = dialogue_state.collected_info['entity_year']
                if isinstance(recent_year, list) and recent_year:
                    vehicle_info['year'] = recent_year[-1]['value']

        return vehicle_info

    async def _research_ownership_costs(
        self,
        vehicle_info: Dict[str, Any],
        lifestyle_profile = None
    ) -> Dict[str, Any]:
        """Research total cost of ownership"""
        # Get annual mileage from lifestyle profile
        annual_mileage = 12000  # Default
        if lifestyle_profile and hasattr(lifestyle_profile, 'annual_mileage'):
            if lifestyle_profile.annual_mileage:
                # Average of low and high if range
                low, high = lifestyle_profile.annual_mileage
                annual_mileage = (low + high) / 2 if low and high else (low or high or 12000)

        report = await self.research_service.get_ownership_costs(
            year=vehicle_info.get('year'),
            make=vehicle_info['make'],
            model=vehicle_info['model'],
            trim=vehicle_info.get('trim'),
            annual_mileage=int(annual_mileage)
        )

        return {
            'type': 'ownership_costs',
            'report': report,
            'summary': self._format_ownership_cost_summary(report, vehicle_info)
        }

    def _format_ownership_cost_summary(
        self,
        report: OwnershipCostReport,
        vehicle_info: Dict[str, Any]
    ) -> str:
        """Format ownership cost report into conversational summary"""
        vehicle_name = f"{vehicle_info.get('year', '')} {vehicle_info['make']} {vehicle_info['model']}".strip()

        summary = f"Here's what it costs to own a {vehicle_name}:\n\n"
        summary += f"💰 **First Year Total**: ${report.total_year1:,.0f}\n"
        summary += f"📅 **Monthly Cost**: ${report.cost_per_month:,.0f}\n"
        summary += f"🔧 **5-Year Total**: ${report.total_5year:,.0f}\n\n"

        summary += "**Breakdown:**\n"
        summary += f"• Insurance: ${report.insurance_annual:,.0f}/year\n"
        summary += f"• Maintenance: ${report.maintenance_annual:,.0f}/year\n"
        summary += f"• Fuel: ${report.fuel_annual:,.0f}/year\n"

        if report.depreciation_5year > 0:
            summary += f"\n📉 Expect about ${report.depreciation_5year:,.0f} in depreciation over 5 years"

        if report.reasoning:
            summary += f"\n\n💡 {report.reasoning}"

        return summary

    async def _research_owner_experience(
        self,
        vehicle_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Research real owner experiences"""
        report = await self.research_service.get_owner_experiences(
            year=vehicle_info.get('year'),
            make=vehicle_info['make'],
            model=vehicle_info['model'],
            trim=vehicle_info.get('trim')
        )

        return {
            'type': 'owner_experience',
            'report': report,
            'summary': self._format_owner_experience_summary(report, vehicle_info)
        }

    def _format_owner_experience_summary(
        self,
        report: OwnerExperienceReport,
        vehicle_info: Dict[str, Any]
    ) -> str:
        """Format owner experience report into conversational summary"""
        vehicle_name = f"{vehicle_info.get('year', '')} {vehicle_info['make']} {vehicle_info['model']}".strip()

        summary = f"Here's what real owners say about the {vehicle_name}:\n\n"

        # Overall ratings
        summary += f"⭐ **Overall Satisfaction**: {report.overall_satisfaction:.1f}/5\n"
        summary += f"🔧 **Reliability**: {report.reliability_rating:.1f}/5\n"
        summary += f"💎 **Value**: {report.value_rating:.1f}/5\n"

        # Sentiment
        if report.positive_sentiment > 0 or report.negative_sentiment > 0:
            summary += f"\n📊 **Sentiment**: {report.positive_sentiment*100:.0f}% positive, {report.negative_sentiment*100:.0f}% negative"

        # Common praises
        if report.common_praises:
            summary += f"\n\n👍 **What Owners Love:**\n"
            for praise in report.common_praises[:3]:
                summary += f"• {praise}\n"

        # Common problems
        if report.common_problems:
            summary += f"\n⚠️ **Common Issues:**\n"
            for problem in report.common_problems[:3]:
                summary += f"• {problem}\n"

        # Recommendation
        if report.would_recommend > 0:
            summary += f"\n✅ {report.would_recommend*100:.0f}% of owners would recommend this vehicle"

        # Key insights
        if report.key_insights:
            summary += f"\n\n💡 **Key Insights:**\n"
            for insight in report.key_insights[:2]:
                summary += f"• {insight}\n"

        return summary

    async def _research_lease_vs_buy(
        self,
        vehicle_info: Dict[str, Any],
        lifestyle_profile = None
    ) -> Dict[str, Any]:
        """Research lease vs buy comparison"""
        # Get annual mileage from lifestyle profile
        annual_mileage = 12000
        if lifestyle_profile and hasattr(lifestyle_profile, 'annual_mileage'):
            if lifestyle_profile.annual_mileage:
                low, high = lifestyle_profile.annual_mileage
                annual_mileage = (low + high) / 2 if low and high else (low or high or 12000)

        report = await self.research_service.get_lease_vs_buy_analysis(
            year=vehicle_info.get('year'),
            make=vehicle_info['make'],
            model=vehicle_info['model'],
            trim=vehicle_info.get('trim'),
            annual_mileage=int(annual_mileage)
        )

        return {
            'type': 'lease_vs_buy',
            'report': report,
            'summary': self._format_lease_vs_buy_summary(report, vehicle_info)
        }

    def _format_lease_vs_buy_summary(
        self,
        report: LeaseVsBuyReport,
        vehicle_info: Dict[str, Any]
    ) -> str:
        """Format lease vs buy report into conversational summary"""
        vehicle_name = f"{vehicle_info.get('year', '')} {vehicle_info['make']} {vehicle_info['model']}".strip()

        summary = f"Lease vs Buy comparison for {vehicle_name}:\n\n"

        summary += f"**Leasing:**\n"
        summary += f"• Monthly: ${report.lease_monthly_avg:,.0f}\n"
        summary += f"• Down: ${report.lease_down_payment:,.0f}\n"
        summary += f"• 5-Year Total: ${report.lease_total_5year:,.0f}\n\n"

        summary += f"**Buying:**\n"
        summary += f"• Monthly: ${report.purchase_monthly_avg:,.0f}\n"
        summary += f"• Down: ${report.purchase_down_payment:,.0f}\n"
        summary += f"• 5-Year Total: ${report.purchase_total_5year:,.0f}\n"

        if report.breakeven_years:
            summary += f"\n\nBreak-even point: {report.breakeven_years:.1f} years"

        if report.recommendation:
            summary += f"\n\nRecommendation: {report.recommendation}"

        if report.reasoning:
            summary += f"\n\n{report.reasoning}"

        return summary

    async def _research_insurance_delta(
        self,
        vehicle_info: Dict[str, Any],
        lifestyle_profile,
        dialogue_state: DialogueState
    ) -> Dict[str, Any]:
        """Research insurance premium change"""
        # Extract current vehicle from lifestyle profile or dialogue state
        current_vehicle = None
        if lifestyle_profile and hasattr(lifestyle_profile, 'current_vehicle'):
            current_vehicle = lifestyle_profile.current_vehicle

        if not current_vehicle:
            return None

        current_vehicle_dict = {
            'year': current_vehicle.year,
            'make': current_vehicle.make,
            'model': current_vehicle.model
        }

        report = await self.research_service.get_insurance_delta(
            current_vehicle=current_vehicle_dict,
            new_vehicle=vehicle_info
        )

        return {
            'type': 'insurance_delta',
            'report': report,
            'summary': self._format_insurance_delta_summary(report, current_vehicle_dict, vehicle_info)
        }

    def _format_insurance_delta_summary(
        self,
        report: InsuranceDeltaReport,
        current_vehicle: Dict[str, Any],
        new_vehicle: Dict[str, Any]
    ) -> str:
        """Format insurance delta report into conversational summary"""
        current_name = f"{current_vehicle.get('year', '')} {current_vehicle['make']} {current_vehicle.get('model', '')}".strip()
        new_name = f"{new_vehicle.get('year', '')} {new_vehicle['make']} {new_vehicle['model']}".strip()

        summary = f"Insurance cost change from {current_name} to {new_name}:\n\n"

        summary += f"**Current Vehicle**: ${report.current_vehicle_premium:,.0f}/year\n"
        summary += f"**New Vehicle**: ${report.new_vehicle_premium:,.0f}/year\n"

        # Calculate change
        change_direction = "increase" if report.annual_delta > 0 else "decrease"
        change_pct = abs(report.percent_change * 100)

        summary += f"\n**{change_direction.title()}**: ${abs(report.annual_delta):,.0f}/year ({change_pct:.1f}%)"
        summary += f"\n**Monthly Impact**: ${abs(report.monthly_delta):,.0f}/month"

        if report.factors:
            summary += f"\n\n**Why the change:**\n"
            for factor in report.factors[:3]:
                summary += f"• {factor}\n"

        if report.reasoning:
            summary += f"\n\n{report.reasoning}"

        return summary

    async def _update_dialogue_state(
        self,
        user_id: str,
        dialogue_state: DialogueState,
        intent: Dict[str, Any],
        response: ConversationResponse
    ):
        """Update dialogue state based on interaction"""

        # Update stage based on intent and response
        intent_type = intent.get('analysis', {}).get('intent', 'question')

        stage_transitions = {
            'greeting': 'discovery',
            'search': 'recommendation',
            'compare': 'refinement',
            'question': 'discovery'
        }

        if intent_type in stage_transitions:
            dialogue_state.stage = stage_transitions[intent_type]

        # Store important entities
        entities = intent.get('analysis', {}).get('entities', {})
        if entities:
            for key, value in entities.items():
                if value:
                    dialogue_state.collected_info[key] = value

        # Update conversation summary periodically
        if len(dialogue_state.collected_info) > 5:
            dialogue_state.conversation_summary = (
                f"User is looking for {dialogue_state.collected_info.get('vehicle_types', 'vehicles')} "
                f"with preferences including {list(dialogue_state.collected_info.keys())[:3]}"
            )

        # Store updated state
        self.dialogue_states[user_id] = dialogue_state

    async def _update_enhanced_dialogue_state(
        self,
        user_id: str,
        dialogue_state: DialogueState,
        nlu_result: Any,  # NLUResult
        entities: List[Any],  # VehicleEntity
        preferences: List[Any]  # UserPreference
    ):
        """Update dialogue state with enhanced NLU information"""

        # Enhanced stage transitions based on NLU
        stage_transitions = {
            'greet': 'discovery',
            'search': 'recommendation',
            'compare': 'refinement',
            'advice': 'exploration',
            'information': 'learning',
            'clarify': 'refinement'
        }

        if nlu_result.intent.primary in stage_transitions:
            dialogue_state.stage = stage_transitions[nlu_result.intent.primary]

        # Store extracted entities
        if entities:
            for entity in entities:
                key = f"entity_{entity.entity_type.value}"
                if key not in dialogue_state.collected_info:
                    dialogue_state.collected_info[key] = []
                dialogue_state.collected_info[key].append({
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'extracted_at': datetime.now().isoformat()
                })

        # Store detected preferences
        if preferences:
            for pref in preferences:
                if pref.category not in dialogue_state.collected_info:
                    dialogue_state.collected_info[f"pref_{pref.category}"] = []
                dialogue_state.collected_info[f"pref_{pref.category}"].append({
                    'value': pref.value,
                    'weight': pref.weight,
                    'source': pref.source,
                    'extracted_at': pref.extracted_at.isoformat()
                })

        # Store NLU insights
        dialogue_state.collected_info['nlu_insights'] = {
            'last_intent': nlu_result.intent.primary,
            'intent_confidence': nlu_result.intent.confidence,
            'sentiment': nlu_result.sentiment,
            'emotional_state': nlu_result.emotional_state,
            'context_relevance': nlu_result.context_relevance_score
        }

        # Enhanced conversation summary
        vehicle_types = dialogue_state.collected_info.get('entity_vehicle_type', [])
        budget = dialogue_state.collected_info.get('entity_price', [])
        features = dialogue_state.collected_info.get('entity_feature', [])

        summary_parts = []
        if vehicle_types:
            summary_parts.append(f"interested in {', '.join([v['value'] for v in vehicle_types[:2]])}")
        if budget:
            max_budget = max([b['value'] for b in budget if isinstance(b.get('value'), (int, float))], default=None)
            if max_budget:
                summary_parts.append(f"budget up to ${max_budget:,}")
        if features:
            summary_parts.append(f"wants {len(features)} specific features")

        if summary_parts:
            dialogue_state.conversation_summary = f"User {', '.join(summary_parts)}"

        # Store updated state
        self.dialogue_states[user_id] = dialogue_state

    async def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of the user's conversation"""

        try:
            # Get dialogue state
            dialogue_state = await self._get_dialogue_state(user_id)

            # Get Zep session stats if available
            session_stats = {}
            if self.zep_client.initialized:
                session_stats = await self.zep_client.get_session_stats(user_id)

            return {
                'dialogue_stage': dialogue_state.stage,
                'user_intent': dialogue_state.user_intent,
                'collected_preferences': dialogue_state.collected_info,
                'conversation_summary': dialogue_state.conversation_summary,
                'last_query': dialogue_state.last_query,
                'session_stats': session_stats
            }

        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {}

    async def reset_conversation(self, user_id: str) -> bool:
        """Reset conversation state for user"""
        try:
            # Clear dialogue state
            if user_id in self.dialogue_states:
                del self.dialogue_states[user_id]

            # Clear cache if available
            if self.cache:
                cache_keys = [f"conversation:{user_id}:*"]
                for key in cache_keys:
                    await self.cache.delete(key)

            logger.info(f"Reset conversation for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset conversation: {e}")
            return False

    async def _create_conversation_summary(self, user_id: str, session_id: str):
        """Create a summary of the conversation"""
        try:
            # Get recent messages
            messages = await self.zep_client.get_conversation_history(user_id, limit=50)

            # Convert Zep messages to Message format
            message_objects = []
            for msg in messages:
                message_objects.append(Message(
                    id=msg.get('uuid', ''),
                    role=msg.get('role', 'user'),
                    content=msg.get('content', ''),
                    timestamp=datetime.fromisoformat(msg.get('created_at', datetime.now().isoformat())),
                    metadata=msg.get('metadata', {})
                ))

            if len(message_objects) >= self.conversation_summarizer.min_messages_for_summary:
                # Generate summary
                summary = await self.conversation_summarizer.summarize_conversation(
                    message_objects, user_id, session_id, SummaryType.CONVERSATION_FLOW
                )
                if summary:
                    # Store summary in temporal memory
                    await self.temporal_memory.add_memory_fragment(
                        user_id=user_id,
                        content=summary.content,
                        memory_type=MemoryType.EPISODIC,
                        importance=summary.completeness_score,
                        session_id=session_id,
                        associated_preferences=[{"summary": summary.content}]
                    )
                    logger.info(f"Created conversation summary for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create conversation summary: {e}")

    async def _track_user_behavior(
        self,
        user_id: str,
        message: str,
        entities: List[Entity],
        nlu_result: Any,
        preferences: List[UserPreference]
    ) -> None:
        """Track user behavior for adaptive learning"""
        try:
            # Extract behavioral signals from the interaction
            behavior_data = {
                "timestamp": datetime.now().isoformat(),
                "message_length": len(message),
                "entities_detected": len(entities),
                "intent": nlu_result.intent.primary if hasattr(nlu_result, 'intent') else 'unknown',
                "emotional_state": getattr(nlu_result, 'emotional_state', 'neutral'),
                "preferences_extracted": len(preferences)
            }

            # Track vehicle-related behaviors
            vehicle_entities = [e for e in entities if e.label in ['VEHICLE_TYPE', 'BRAND', 'MODEL', 'YEAR']]
            if vehicle_entities:
                behavior_data["vehicle_interests"] = [
                    {
                        "entity": e.text,
                        "type": e.label,
                        "confidence": e.confidence
                    }
                    for e in vehicle_entities
                ]

            # Track search patterns from message
            search_keywords = []
            if "looking for" in message.lower() or "search" in message.lower():
                behavior_data["search_active"] = True
                # Extract potential search terms
                search_terms = ["suv", "sedan", "truck", "hatchback", "coupe", "convertible", "hybrid", "electric"]
                for term in search_terms:
                    if term in message.lower():
                        search_keywords.append(term)

            if search_keywords:
                behavior_data["search_terms"] = search_keywords

            # Track comparison behavior
            if "compare" in message.lower() or "versus" in message.lower() or "vs" in message.lower():
                behavior_data["comparison_active"] = True

            # Track explicit preference indicators
            if "prefer" in message.lower() or "like" in message.lower() or "love" in message.lower():
                behavior_data["preference_expression"] = "positive"
            elif "don't" in message.lower() or "hate" in message.lower() or "avoid" in message.lower():
                behavior_data["preference_expression"] = "negative"

            # Store behavior patterns in profile
            await self.profile_service.update_behavior_patterns(user_id, behavior_data)

            logger.debug(f"Tracked behavior for user {user_id}: {len(behavior_data)} data points")

        except Exception as e:
            logger.error(f"Failed to track user behavior: {e}")

    async def _handle_questioning_strategy(
        self,
        user_id: str,
        message: str,
        session_id: str,
        dialogue_state: DialogueState,
        preferences: List,
        conflicts: List[PreferenceConflict]
    ) -> None:
        """Handle intelligent questioning based on context and needs"""
        try:
            # Build user context for question selection
            questions_asked = await self.question_memory.get_user_question_history(
                user_id, limit=20
            )
            asked_question_ids = {q.question_id for q in questions_asked}

            user_context = UserContext(
                user_id=user_id,
                conversation_stage=dialogue_state.stage,
                known_preferences={p.category.value: p.value for p in preferences if hasattr(p, 'category')},
                recent_topics=[p.category.value for p in preferences[-5:] if hasattr(p, 'category')],
                engagement_level=self._calculate_engagement_level(dialogue_state),
                questions_asked=asked_question_ids,
                last_question_time=questions_asked[0].timestamp if questions_asked else None,
                response_patterns=self._extract_response_patterns(questions_asked),
                fatigue_indicators=self._detect_fatigue_indicators(dialogue_state)
            )

            # Select next questions if appropriate
            if self._should_ask_question(user_context, message, conflicts):
                scored_questions = await self.questioning_strategy.select_next_question(
                    user_context,
                    max_questions=2
                )

                if scored_questions:
                    # Store pending questions in dialogue state
                    dialogue_state.collected_info = dialogue_state.collected_info or {}
                    dialogue_state.collected_info['pending_questions'] = [
                        {
                            'question_id': score.question_id,
                            'score': score.total_score,
                            'reasons': score.selection_reasons
                        }
                        for score in scored_questions
                    ]

                    # Track high-priority conflicts for questioning
                    if conflicts:
                        high_priority_conflicts = [
                            c for c in conflicts if c.severity.value in ['high', 'critical']
                        ]
                        if high_priority_conflicts:
                            dialogue_state.collected_info['priority_conflict'] = high_priority_conflicts[0]

            # Check for family-specific questioning needs
            if self._should_ask_family_questions(user_context, message):
                family_questions = await self._get_family_questions(user_context, message)
                if family_questions:
                    dialogue_state.collected_info = dialogue_state.collected_info or {}
                    dialogue_state.collected_info['family_questions'] = family_questions

        except Exception as e:
            logger.error(f"Failed to handle questioning strategy: {e}")

    def _calculate_engagement_level(self, dialogue_state: DialogueState) -> float:
        """Calculate user engagement level from dialogue state"""
        base_engagement = 0.5

        # Increase based on conversation depth
        if dialogue_state.conversation_summary and len(dialogue_state.conversation_summary) > 100:
            base_engagement += 0.2

        # Check for rich responses
        if dialogue_state.collected_info:
            response_count = len([k for k in dialogue_state.collected_info.keys() if 'answer' in k.lower()])
            base_engagement += min(response_count * 0.1, 0.3)

        return min(base_engagement, 1.0)

    def _extract_response_patterns(self, questions_asked) -> Dict[str, Any]:
        """Extract patterns from user responses"""
        patterns = {
            'avg_response_length': 0,
            'question_response_rate': 0,
            'preferred_complexity': []
        }

        if not questions_asked:
            return patterns

        # Calculate average response length
        responses = [q.response for q in questions_asked if q.response]
        if responses:
            total_words = sum(len(r.split()) for r in responses)
            patterns['avg_response_length'] = total_words / len(responses)

        # Calculate response rate
        answered_questions = [q for q in questions_asked if q.response]
        patterns['question_response_rate'] = len(answered_questions) / len(questions_asked)

        # Track preferred complexity
        answered_with_effectiveness = [
            q for q in answered_questions
            if q.effectiveness_score and q.effectiveness_score > 0.7
        ]
        if answered_with_effectiveness:
            complexities = [q.metadata.get('complexity') for q in answered_with_effectiveness]
            patterns['preferred_complexity'] = complexities

        return patterns

    def _detect_fatigue_indicators(self, dialogue_state: DialogueState) -> List[str]:
        """Detect signs of question fatigue"""
        fatigue_indicators = []

        if dialogue_state.last_query:
            # Check for short, disengaged responses
            if len(dialogue_state.last_query.split()) < 3:
                fatigue_indicators.append("short_response")

            # Check for negative sentiment
            negative_words = ["boring", "irrelevant", "again", "already", "stop"]
            if any(word in dialogue_state.last_query.lower() for word in negative_words):
                fatigue_indicators.append("negative_sentiment")

            # Check for topic repetition
            if dialogue_state.collected_info:
                recent_topics = list(dialogue_state.collected_info.keys())[-3:]
                if len(set(recent_topics)) < len(recent_topics) / 2:
                    fatigue_indicators.append("topic_repetition")

        return fatigue_indicators

    def _should_ask_question(
        self,
        user_context: UserContext,
        message: str,
        conflicts: List[PreferenceConflict]
    ) -> bool:
        """Determine if we should ask a question now"""
        # Don't ask if user is asking direct questions
        if message.strip().endswith('?'):
            return False

        # Don't ask if user is expressing frustration
        if any(word in message.lower() for word in ["frustrated", "annoyed", "just tell me", "skip"]):
            return False

        # Ask if there are high-priority conflicts
        if conflicts and any(c.severity.value in ['high', 'critical'] for c in conflicts):
            return True

        # Ask if engagement is low and we haven't asked many questions
        if user_context.engagement_level < 0.5 and len(user_context.questions_asked) < 5:
            return True

        # Ask if in discovery stage with insufficient information
        if (user_context.conversation_stage == 'discovery' and
            len(user_context.known_preferences) < 5 and
            len(user_context.questions_asked) < 8):
            return True

        return False

    def _should_ask_family_questions(self, user_context: UserContext, message: str) -> bool:
        """Check if we should ask family-specific questions"""
        # Check for family-related keywords
        family_keywords = ["family", "kids", "children", "wife", "husband", "spouse", "baby"]
        if any(keyword in message.lower() for keyword in family_keywords):
            return True

        # Check if we have family size information but not details
        if "family_size_initial" in user_context.questions_asked:
            family_related_questions = [
                q for q in user_context.questions_asked
                if q.startswith("family_")
            ]
            if len(family_related_questions) < 3:
                return True

        return False

    async def _get_family_questions(self, user_context: UserContext, message: str) -> List[Dict]:
        """Get appropriate family questions"""
        # This would integrate with the family_need_questioning module
        # For now, return basic family questions
        return [
            {
                'type': 'family_ages',
                'text': 'What are the ages of your family members?',
                'priority': 0.8
            }
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Check health of conversation agent"""
        return {
            'initialized': self.initialized,
            'zep_client': await self.zep_client.health_check() if self.zep_client else {'initialized': False},
            'groq_client': await self.groq_client.health_check() if self.groq_client else {'initialized': False},
            'active_dialogues': len(self.dialogue_states),
            'voice_service': {
                'initialized': self.voice_service is not None,
                'browser_supported': self.voice_service.is_browser_supported() if self.voice_service else False,
                'is_listening': self.voice_service.is_listening if self.voice_service else False
            },
            'questioning_components': {
                'questioning_strategy': self.questioning_strategy.initialized if self.questioning_strategy else False,
                'conflict_detector': self.conflict_detector.initialized if self.conflict_detector else False,
                'question_memory': self.question_memory.initialized if self.question_memory else False,
                'family_questioning': self.family_questioning.initialized if self.family_questioning else False
            },
            'rag_search': {
                'enabled': self.rag_search_enabled,
                'orchestrator_initialized': self.search_orchestrator is not None,
                'stats': self.search_orchestrator.get_stats() if self.search_orchestrator else {}
            },
            'external_research': {
                'enabled': self.research_enabled,
                'service_initialized': self.research_service is not None,
                'stats': self.research_service.get_stats() if self.research_service else {}
            },
            'personality': self.personality
        }

    async def _store_voice_interaction(self, user_id: str, voice_result: VoiceResult, voice_command: VoiceCommand):
        """Store voice interaction in temporal memory"""
        try:
            # Create voice interaction summary
            voice_summary = {
                "type": "voice_interaction",
                "transcript": voice_result.transcript,
                "confidence": voice_result.confidence,
                "command_type": voice_command.command_type.value,
                "vehicle_types": voice_command.vehicle_types,
                "price_range": voice_command.price_range,
                "features": voice_command.features,
                "timestamp": voice_result.timestamp
            }

            # Store in temporal memory
            await self.temporal_memory.add_memory_fragment(
                user_id=user_id,
                content=f"Voice command: {voice_result.transcript}",
                memory_type=MemoryType.EPISODIC,
                importance=voice_result.confidence,
                associated_preferences=[voice_summary]
            )

            # Update user profile with voice preferences
            if voice_command.vehicle_types:
                await self.profile_service.update_profile_preferences(
                    user_id,
                    [UserPreference(
                        category="vehicle_type",
                        value=vt,
                        weight=voice_result.confidence,
                        source="voice"
                    ) for vt in voice_command.vehicle_types]
                )

            logger.info(f"Stored voice interaction for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to store voice interaction: {e}")

    async def _enhance_nlu_with_voice_command(self, nlu_result, voice_command: VoiceCommand):
        """Enhance NLU result with parsed voice command information"""
        try:
            # Update intent if voice command has strong confidence
            if voice_command.confidence > 0.8 and voice_command.command_type != VoiceCommandType.GENERAL:
                intent_mapping = {
                    VoiceCommandType.SEARCH: "search",
                    VoiceCommandType.COMPARE: "compare",
                    VoiceCommandType.FILTER: "filter",
                    VoiceCommandType.HELP: "question"
                }
                if voice_command.command_type in intent_mapping:
                    nlu_result.intent.primary = intent_mapping[voice_command.command_type]
                    nlu_result.intent.confidence = max(nlu_result.intent.confidence, voice_command.confidence)

            # Add vehicle types from voice command
            if voice_command.vehicle_types:
                if not hasattr(nlu_result, 'entities'):
                    nlu_result.entities = []

                for vt in voice_command.vehicle_types:
                    # Create a simple entity-like object
                    entity = type('Entity', (), {
                        'entity_type': 'VEHICLE_TYPE',
                        'value': vt,
                        'confidence': voice_command.confidence,
                        'text': vt
                    })()
                    nlu_result.entities.append(entity)

            # Add price range information
            if voice_command.price_range:
                if not hasattr(nlu_result, 'entities'):
                    nlu_result.entities = []

                price_entity = type('Entity', (), {
                    'entity_type': 'PRICE',
                    'value': voice_command.price_range.get('max'),
                    'confidence': voice_command.confidence,
                    'text': str(voice_command.price_range.get('max', ''))
                })()
                nlu_result.entities.append(price_entity)

            logger.debug(f"Enhanced NLU with voice command: {voice_command.command_type}")

        except Exception as e:
            logger.error(f"Failed to enhance NLU with voice command: {e}")

        return nlu_result

    async def start_voice_session(self, user_id: str, result_callback, error_callback) -> bool:
        """Start a voice input session for a user"""
        try:
            if not self.voice_service.initialize():
                return False

            success = self.voice_service.start_listening(
                result_callback=result_callback,
                error_callback=error_callback
            )

            if success:
                self.voice_enabled = True
                logger.info(f"Started voice session for user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to start voice session: {e}")
            return False

    async def stop_voice_session(self) -> bool:
        """Stop the current voice session"""
        try:
            if self.voice_service:
                success = self.voice_service.stop_listening()
                self.voice_enabled = False
                logger.info("Voice session stopped")
                return success
            return False

        except Exception as e:
            logger.error(f"Failed to stop voice session: {e}")
            return False

    def get_voice_performance_stats(self) -> Dict[str, Any]:
        """Get voice input performance statistics"""
        if self.voice_service:
            return self.voice_service.get_performance_stats()
        return {}