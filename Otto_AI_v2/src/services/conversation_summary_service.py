"""
Conversation Summary Service for Otto.AI
Generates AI-powered summaries of conversations, extracts preferences, tracks vehicles discussed,
and detects preference evolution over time.
"""

import os
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import openai
from openai import AsyncOpenAI

from src.memory.zep_client import ZepClient, Message
from src.cache.multi_level_cache import MultiLevelCache

# Configure logging
logger = logging.getLogger(__name__)


class JourneyStage(Enum):
    """Stages in the vehicle discovery journey"""
    DISCOVERY = "discovery"  # Initial exploration
    CONSIDERATION = "consideration"  # Comparing options
    DECISION = "decision"  # Narrowing down
    PURCHASED = "purchased"  # Made purchase


@dataclass
class VehicleMention:
    """Represents a vehicle mentioned in conversation"""
    make: str
    model: str
    year: Optional[int] = None
    trim: Optional[str] = None
    relevance_score: float = 0.5
    mentioned_count: int = 1
    sentiment: Optional[str] = None  # positive, neutral, negative


@dataclass
class ExtractedPreferences:
    """Structured preference extraction from conversation"""
    budget: Optional[Dict[str, Any]] = None  # {min, max, currency, monthly_cap}
    vehicle_types: List[str] = None  # ['SUV', 'crossover', 'sedan']
    brands: List[str] = None  # ['Toyota', 'Honda', 'Ford']
    features: List[str] = None  # ['leather_seats', 'sunroof', 'awd']
    lifestyle: List[str] = None  # ['family', 'commute', 'towing']
    colors: List[str] = None
    deal_breakers: List[str] = None  # Things to avoid

    def __post_init__(self):
        if self.vehicle_types is None:
            self.vehicle_types = []
        if self.brands is None:
            self.brands = []
        if self.features is None:
            self.features = []
        if self.lifestyle is None:
            self.lifestyle = []
        if self.colors is None:
            self.colors = []
        if self.deal_breakers is None:
            self.deal_breakers = []


@dataclass
class ConversationSummary:
    """Complete conversation summary"""
    conversation_id: str
    session_id: str
    user_id: Optional[str]

    # Summary content
    title: str  # Auto-generated title
    summary: str  # Full conversation summary
    key_points: List[str]  # Bullet points of key takeaways

    # Extracted data
    preferences: ExtractedPreferences
    vehicles_discussed: List[VehicleMention]

    # Journey tracking
    journey_stage: JourneyStage
    evolution_detected: bool
    evolution_notes: List[str]  # How preferences changed

    # Metadata
    message_count: int
    started_at: datetime
    ended_at: datetime
    duration_minutes: float

    # AI metadata
    model_used: str
    summary_tokens: int
    generated_at: datetime


class ConversationSummaryService:
    """Service for generating AI-powered conversation summaries"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        zep_client: Optional[ZepClient] = None,
        cache: Optional[MultiLevelCache] = None
    ):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.zep_client = zep_client
        self.cache = cache

        # Initialize OpenAI client
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not provided. Summarization will use fallback methods.")

        # Configuration
        self.default_model = "gpt-4o"  # Most capable model for summaries
        self.fallback_model = "gpt-4o-mini"  # Faster, cheaper alternative
        self.max_tokens_summary = 500
        self.max_messages_for_summary = 100  # Limit to prevent token overflow

        # Vehicle pattern matching for extraction
        self.vehicle_patterns = {
            'makes': [
                'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'Hyundai',
                'Kia', 'Mazda', 'Subaru', 'Volkswagen', 'BMW', 'Mercedes',
                'Audi', 'Lexus', 'Tesla', 'Rivian', 'Jeep', 'RAM', 'GMC'
            ],
            'types': [
                'SUV', 'crossover', 'sedan', 'truck', 'pickup', 'van',
                'coupe', 'convertible', 'hatchback', 'wagon', 'EV'
            ]
        }

    async def generate_conversation_summary(
        self,
        messages: List[Message],
        conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> ConversationSummary:
        """Generate comprehensive conversation summary

        Args:
            messages: List of conversation messages
            conversation_id: Unique conversation identifier
            session_id: Zep session ID
            user_id: Optional authenticated user ID

        Returns:
            ConversationSummary with all extracted information
        """
        try:
            logger.info(f"Generating summary for conversation {conversation_id}")

            # Prepare messages for summarization
            messages_to_summarize = messages[-self.max_messages_for_summary:]

            # Generate summary components in parallel
            title_task = self._generate_title(messages_to_summarize)
            summary_task = self._generate_summary(messages_to_summarize)
            preferences_task = self._extract_preferences(messages_to_summarize)
            vehicles_task = self._extract_vehicles(messages_to_summarize)
            journey_task = self._determine_journey_stage(messages_to_summarize)

            # Execute all tasks concurrently
            title, summary, extracted_prefs, vehicles, journey_stage = await asyncio.gather(
                title_task,
                summary_task,
                preferences_task,
                vehicles_task,
                journey_task,
                return_exceptions=True
            )

            # Handle any failures
            if isinstance(title, Exception):
                logger.error(f"Title generation failed: {title}")
                title = f"Conversation {conversation_id[:8]}"

            if isinstance(summary, Exception):
                logger.error(f"Summary generation failed: {summary}")
                summary = "Unable to generate summary."

            if isinstance(extracted_prefs, Exception):
                logger.error(f"Preference extraction failed: {extracted_prefs}")
                extracted_prefs = ExtractedPreferences()

            if isinstance(vehicles, Exception):
                logger.error(f"Vehicle extraction failed: {vehicles}")
                vehicles = []

            if isinstance(journey_stage, Exception):
                logger.error(f"Journey stage detection failed: {journey_stage}")
                journey_stage = JourneyStage.DISCOVERY

            # Detect preference evolution
            evolution_detected, evolution_notes = await self._detect_preference_evolution(
                messages_to_summarize, extracted_prefs
            )

            # Calculate metadata
            message_count = len(messages)
            started_at = messages[0].created_at if messages else datetime.now()
            ended_at = messages[-1].created_at if messages else datetime.now()
            duration_minutes = (ended_at - started_at).total_seconds() / 60 if started_at and ended_at else 0

            # Generate key points from summary
            key_points = await self._extract_key_points(summary)

            summary_result = ConversationSummary(
                conversation_id=conversation_id,
                session_id=session_id,
                user_id=user_id,
                title=title,
                summary=summary,
                key_points=key_points,
                preferences=extracted_prefs,
                vehicles_discussed=vehicles,
                journey_stage=journey_stage,
                evolution_detected=evolution_detected,
                evolution_notes=evolution_notes,
                message_count=message_count,
                started_at=started_at,
                ended_at=ended_at,
                duration_minutes=duration_minutes,
                model_used=self.default_model,
                summary_tokens=0,  # Would be tracked from actual API response
                generated_at=datetime.now()
            )

            # Cache the summary
            if self.cache:
                cache_key = f"summary:{conversation_id}"
                await self.cache.set(
                    cache_key,
                    asdict(summary_result),
                    ttl=86400  # 24 hours
                )

            logger.info(f"Successfully generated summary for {conversation_id}: {title}")
            return summary_result

        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            raise

    async def _generate_title(self, messages: List[Message]) -> str:
        """Generate a concise title for the conversation

        Examples:
        - "Toyota RAV4 Research - Family SUV Search"
        - "Electric Vehicle Exploration - Budget $40k"
        - "Pickup Truck Comparison - Towing Capacity Focus"
        """
        if not self.openai_client:
            return self._generate_fallback_title(messages)

        try:
            # Prepare conversation text
            conversation_text = self._format_messages_for_llm(messages, max_chars=2000)

            prompt = f"""Generate a concise, descriptive title (max 60 characters) for this vehicle discovery conversation.

Conversation:
{conversation_text}

The title should:
- Be concise (under 60 characters)
- Mention key vehicle types/brands discussed
- Indicate the main focus (budget, family, performance, etc.)
- Be engaging and helpful for the user

Return ONLY the title, nothing else."""

            response = await self.openai_client.chat.completions.create(
                model=self.fallback_model,  # Use cheaper model for titles
                messages=[
                    {"role": "system", "content": "You are an expert at generating concise, helpful titles for vehicle search conversations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )

            title = response.choices[0].message.content.strip()
            return title[:60]  # Ensure max length

        except Exception as e:
            logger.error(f"Failed to generate AI title: {e}")
            return self._generate_fallback_title(messages)

    def _generate_fallback_title(self, messages: List[Message]) -> str:
        """Generate title without AI using keyword extraction"""
        user_messages = [msg.content for msg in messages if msg.role == 'user']

        # Extract keywords
        keywords = set()
        for msg in user_messages[:5]:  # Check first 5 messages
            msg_lower = msg.lower()

            # Check for vehicle makes
            for make in self.vehicle_patterns['makes']:
                if make.lower() in msg_lower:
                    keywords.add(make)

            # Check for vehicle types
            for vtype in self.vehicle_patterns['types']:
                if vtype.lower() in msg_lower:
                    keywords.add(vtype.title())

            # Check for budget
            if '$' in msg and ('budget' in msg_lower or 'under' in msg_lower or 'below' in msg_lower):
                import re
                budgets = re.findall(r'\$[0-9,]+k?', msg)
                if budgets:
                    keywords.append(budgets[0])

        if keywords:
            top_keywords = list(keywords)[:3]
            return " - ".join(top_keywords)
        else:
            date_str = datetime.now().strftime("%b %d")
            return f"Vehicle Search - {date_str}"

    async def _generate_summary(self, messages: List[Message]) -> str:
        """Generate comprehensive conversation summary"""
        if not self.openai_client:
            return self._generate_fallback_summary(messages)

        try:
            conversation_text = self._format_messages_for_llm(messages)

            prompt = f"""Summarize this vehicle discovery conversation in 2-3 paragraphs.

Conversation:
{conversation_text}

Your summary should:
1. Capture the user's main vehicle search criteria
2. Highlight key vehicles discussed and why they're relevant
3. Note any important preferences or concerns mentioned
4. Be clear, concise, and helpful for reviewing the conversation later

Write in a natural, conversational style."""

            response = await self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing vehicle discovery conversations in a clear, helpful way."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens_summary,
                temperature=0.5
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate AI summary: {e}")
            return self._generate_fallback_summary(messages)

    def _generate_fallback_summary(self, messages: List[Message]) -> str:
        """Generate summary without AI"""
        user_messages = [msg for msg in messages if msg.role == 'user']
        assistant_messages = [msg for msg in messages if msg.role == 'assistant']

        message_count = len(messages)
        user_msg_count = len(user_messages)

        # Extract basic info
        summary = f"This conversation contains {message_count} messages ({user_msg_count} from user). "

        # Extract key topics
        topics = set()
        for msg in user_messages[:10]:
            msg_lower = msg.content.lower()
            for make in self.vehicle_patterns['makes']:
                if make.lower() in msg_lower:
                    topics.add(make)

        if topics:
            summary += f"Vehicles discussed include {', '.join(list(topics)[:5])}. "

        summary += "Full conversation stored in Zep Cloud."
        return summary

    async def _extract_key_points(self, summary: str) -> List[str]:
        """Extract bullet points from summary"""
        if not self.openai_client:
            return []

        try:
            prompt = f"""Extract 3-5 key bullet points from this summary.

Summary:
{summary}

Return as a simple list, one point per line."""

            response = await self.openai_client.chat.completions.create(
                model=self.fallback_model,
                messages=[
                    {"role": "system", "content": "Extract key points from text as bullet points."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )

            points_text = response.choices[0].message.content.strip()
            # Parse bullet points
            points = [
                line.lstrip('•-* ').strip()
                for line in points_text.split('\n')
                if line.strip() and not line.startswith('Here are')
            ]
            return points[:5]  # Max 5 points

        except Exception as e:
            logger.error(f"Failed to extract key points: {e}")
            return []

    async def _extract_preferences(self, messages: List[Message]) -> ExtractedPreferences:
        """Extract structured preferences from conversation"""
        user_messages = [msg for msg in messages if msg.role == 'user']

        preferences = ExtractedPreferences()

        for msg in user_messages:
            content_lower = msg.content.lower()

            # Extract budget
            if 'budget' in content_lower or 'under $' in content_lower or 'below $' in content_lower or 'max' in content_lower:
                import re
                budgets = re.findall(r'\$[0-9,]+k?', msg.content)
                if budgets:
                    if not preferences.budget:
                        preferences.budget = {}
                    # Parse budget value
                    for budget_str in budgets:
                        budget_str = budget_str.replace('$', '').replace(',', '').replace('k', '000')
                        try:
                            budget_value = int(budget_str)
                            if 'max' not in preferences.budget or budget_value < preferences.budget.get('max', float('inf')):
                                preferences.budget['max'] = budget_value
                        except ValueError:
                            pass

            # Extract vehicle types
            for vtype in self.vehicle_patterns['types']:
                if vtype.lower() in content_lower and vtype.title() not in preferences.vehicle_types:
                    preferences.vehicle_types.append(vtype.title())

            # Extract brands
            for make in self.vehicle_patterns['makes']:
                if make.lower() in content_lower and make not in preferences.brands:
                    preferences.brands.append(make)

            # Extract features
            features = {
                'leather': 'leather_seats',
                'sunroof': 'sunroof',
                'awd': 'awd',
                '4wd': '4wd',
                'backup camera': 'backup_camera',
                'navigation': 'navigation',
                'heated seats': 'heated_seats',
                'third row': 'third_row_seating',
                'towing': 'towing_package'
            }

            for feature_key, feature_value in features.items():
                if feature_key in content_lower and feature_value not in preferences.features:
                    preferences.features.append(feature_value)

            # Extract lifestyle needs
            if any(word in content_lower for word in ['family', 'kids', 'children', 'carpool']):
                if 'family' not in preferences.lifestyle:
                    preferences.lifestyle.append('family')

            if any(word in content_lower for word in ['commute', 'work', 'highway', 'mpg']):
                if 'commute' not in preferences.lifestyle:
                    preferences.lifestyle.append('commute')

            if any(word in content_lower for word in ['tow', 'trailer', 'boat']):
                if 'towing' not in preferences.lifestyle:
                    preferences.lifestyle.append('towing')

        return preferences

    async def _extract_vehicles(self, messages: List[Message]) -> List[VehicleMention]:
        """Extract vehicles discussed in conversation"""
        user_messages = [msg for msg in messages if msg.role == 'user']
        vehicles_dict = {}

        for msg in user_messages:
            content = msg.content
            content_lower = content.lower()

            # Look for make + model patterns
            for make in self.vehicle_patterns['makes']:
                if make.lower() in content_lower:
                    # Try to find model
                    make_pattern = re.escape(make)
                    model_match = re.search(
                        rf'{make_pattern}\s+(\w+)',
                        content,
                        re.IGNORECASE
                    )

                    if model_match:
                        model = model_match.group(1).title()

                        # Extract year if present
                        year_match = re.search(r'\b(20\d{2})\b', content)
                        year = int(year_match.group(1)) if year_match else None

                        # Create vehicle key
                        vehicle_key = f"{make}_{model}_{year or ''}"

                        # Increment mention count
                        if vehicle_key not in vehicles_dict:
                            vehicles_dict[vehicle_key] = VehicleMention(
                                make=make,
                                model=model,
                                year=year,
                                mentioned_count=1,
                                relevance_score=0.5
                            )
                        else:
                            vehicles_dict[vehicle_key].mentioned_count += 1
                            # Increase relevance score with more mentions
                            vehicles_dict[vehicle_key].relevance_score = min(
                                0.95,
                                vehicles_dict[vehicle_key].relevance_score + 0.1
                            )

        # Convert to list and sort by relevance
        vehicles = sorted(
            list(vehicles_dict.values()),
            key=lambda v: v.relevance_score,
            reverse=True
        )

        return vehicles[:10]  # Return top 10 vehicles

    async def _determine_journey_stage(self, messages: List[Message]) -> JourneyStage:
        """Determine where user is in their vehicle discovery journey"""
        user_messages = [msg.content.lower() for msg in messages if msg.role == 'user']

        combined_text = ' '.join(user_messages)

        # Check for indicators of each stage
        discovery_keywords = ['looking for', 'interested in', 'considering', 'thinking about', 'exploring']
        consideration_keywords = ['compare', 'difference between', 'vs', 'versus', 'which is better']
        decision_keywords = ['decided on', 'narrowed down', 'going with', 'chose', 'selected', 'definitely']
        purchased_keywords = ['bought', 'purchased', 'signed for', 'ordered', 'picked up']

        # Count keyword matches
        discovery_count = sum(1 for kw in discovery_keywords if kw in combined_text)
        consideration_count = sum(1 for kw in consideration_keywords if kw in combined_text)
        decision_count = sum(1 for kw in decision_keywords if kw in combined_text)
        purchased_count = sum(1 for kw in purchased_keywords if kw in combined_text)

        # Determine stage based on highest count
        if purchased_count > 0:
            return JourneyStage.PURCHASED
        elif decision_count > consideration_count and decision_count > discovery_count:
            return JourneyStage.DECISION
        elif consideration_count > discovery_count:
            return JourneyStage.CONSIDERATION
        else:
            return JourneyStage.DISCOVERY

    async def _detect_preference_evolution(
        self,
        messages: List[Message],
        current_preferences: ExtractedPreferences
    ) -> Tuple[bool, List[str]]:
        """Detect if preferences changed during conversation"""
        evolution_notes = []

        # Split conversation into thirds to detect changes
        user_messages = [msg for msg in messages if msg.role == 'user']
        if len(user_messages) < 3:
            return False, []

        third = len(user_messages) // 3
        early_messages = user_messages[:third]
        late_messages = user_messages[-third:]

        # Extract preferences from early and late messages
        early_prefs = await self._extract_preferences(early_messages)
        late_prefs = await self._extract_preferences(late_messages)

        # Check for budget changes
        if early_prefs.budget and late_prefs.budget:
            early_max = early_prefs.budget.get('max')
            late_max = late_prefs.budget.get('max')
            if early_max and late_max and early_max != late_max:
                direction = 'increased' if late_max > early_max else 'decreased'
                evolution_notes.append(f"Budget {direction} from ${early_max:,} to ${late_max:,}")

        # Check for vehicle type changes
        early_types = set(early_prefs.vehicle_types)
        late_types = set(late_prefs.vehicle_types)
        added_types = late_types - early_types
        removed_types = early_types - late_types

        if added_types:
            evolution_notes.append(f"Added interest in: {', '.join(added_types)}")
        if removed_types:
            evolution_notes.append(f"No longer interested in: {', '.join(removed_types)}")

        # Check for brand changes
        early_brands = set(early_prefs.brands)
        late_brands = set(late_prefs.brands)
        added_brands = late_brands - early_brands
        if added_brands:
            evolution_notes.append(f"Started considering: {', '.join(added_brands)}")

        evolution_detected = len(evolution_notes) > 0
        return evolution_detected, evolution_notes

    def _format_messages_for_llm(self, messages: List[Message], max_chars: int = 4000) -> str:
        """Format messages for LLM consumption with character limit"""
        formatted = []
        total_chars = 0

        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            msg_text = f"{role_label}: {msg.content}\n"

            if total_chars + len(msg_text) > max_chars:
                break

            formatted.append(msg_text)
            total_chars += len(msg_text)

        return '\n'.join(formatted)

    async def get_cached_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        """Retrieve cached summary if available"""
        if not self.cache:
            return None

        try:
            cache_key = f"summary:{conversation_id}"
            cached = await self.cache.get(cache_key)

            if cached:
                logger.debug(f"Retrieved cached summary for {conversation_id}")
                return ConversationSummary(**cached)

        except Exception as e:
            logger.error(f"Failed to retrieve cached summary: {e}")

        return None

    async def invalidate_cache(self, conversation_id: str):
        """Invalidate cached summary"""
        if self.cache:
            try:
                cache_key = f"summary:{conversation_id}"
                await self.cache.delete(cache_key)
                logger.debug(f"Invalidated cache for {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")


# Singleton instance for dependency injection
_summary_service_instance: Optional[ConversationSummaryService] = None


def get_summary_service(
    openai_api_key: Optional[str] = None,
    zep_client: Optional[ZepClient] = None,
    cache: Optional[MultiLevelCache] = None
) -> ConversationSummaryService:
    """Get or create singleton ConversationSummaryService instance"""
    global _summary_service_instance

    if _summary_service_instance is None:
        _summary_service_instance = ConversationSummaryService(
            openai_api_key=openai_api_key,
            zep_client=zep_client,
            cache=cache
        )

    return _summary_service_instance
