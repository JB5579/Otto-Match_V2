"""
Conversation Summarizer for Otto.AI
Generates summaries of long conversations for efficient context retrieval
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from enum import Enum

from src.conversation.groq_client import GroqClient
from src.memory.zep_client import Message

# Configure logging
logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """Types of conversation summaries"""
    KEY_DECISIONS = "key_decisions"      # Important decisions made
    PREFERENCE_SUMMARY = "preference_summary"  # User preferences learned
    CONVERSATION_FLOW = "conversation_flow"   # Progress and next steps
    EMOTIONAL_JOURNEY = "emotional_journey"   # User's emotional state changes
    ACTION_ITEMS = "action_items"           # Tasks or follow-ups needed


@dataclass
class KeyDecision:
    """Represents a key decision point in conversation"""
    decision: str
    context: str
    timestamp: datetime
    confidence: float
    impact: str  # "high", "medium", "low"
    related_entities: List[str]


@dataclass
class ConversationSummary:
    """Structured summary of a conversation"""
    summary_id: str
    conversation_id: str
    user_id: str
    created_at: datetime
    summary_type: SummaryType
    content: str
    key_decisions: List[KeyDecision]
    preferences_learned: Dict[str, Any]
    next_steps: List[str]
    sentiment_trend: str  # "positive", "negative", "neutral", "mixed"
    completeness_score: float  # 0.0 to 1.0
    metadata: Dict[str, Any]


class ConversationSummarizer:
    """Service for generating conversation summaries"""

    def __init__(
        self,
        groq_client: GroqClient,
        max_summary_length: int = 500,
        min_messages_for_summary: int = 10
    ):
        self.groq_client = groq_client
        self.max_summary_length = max_summary_length
        self.min_messages_for_summary = min_messages_for_summary
        self.initialized = False

        # Summary templates
        self.summary_templates = self._initialize_templates()

    async def initialize(self) -> bool:
        """Initialize the conversation summarizer"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            self.initialized = True
            logger.info("Conversation summarizer initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize conversation summarizer: {e}")
            return False

    async def summarize_conversation(
        self,
        messages: List[Message],
        user_id: str,
        conversation_id: str,
        summary_type: SummaryType = SummaryType.CONVERSATION_FLOW
    ) -> Optional[ConversationSummary]:
        """Generate summary of conversation messages"""
        if not self.initialized:
            return None

        if len(messages) < self.min_messages_for_summary:
            logger.debug(f"Not enough messages for summary ({len(messages)} < {self.min_messages_for_summary})")
            return None

        try:
            # Prepare conversation for summarization
            conversation_text = self._prepare_conversation_text(messages)

            # Generate summary based on type
            if summary_type == SummaryType.KEY_DECISIONS:
                summary_content = await self._summarize_key_decisions(conversation_text)
            elif summary_type == SummaryType.PREFERENCE_SUMMARY:
                summary_content = await self._summarize_preferences(conversation_text)
            elif summary_type == SummaryType.CONVERSATION_FLOW:
                summary_content = await self._summarize_conversation_flow(conversation_text)
            elif summary_type == SummaryType.EMOTIONAL_JOURNEY:
                summary_content = await self._summarize_emotional_journey(conversation_text)
            elif summary_type == SummaryType.ACTION_ITEMS:
                summary_content = await self._summarize_action_items(conversation_text)
            else:
                summary_content = await self._summarize_general(conversation_text)

            # Extract key decisions from summary
            key_decisions = await self._extract_key_decisions(conversation_text)

            # Extract learned preferences
            preferences_learned = await self._extract_preferences_from_conversation(conversation_text)

            # Determine next steps
            next_steps = await self._identify_next_steps(conversation_text)

            # Analyze sentiment trend
            sentiment_trend = await self._analyze_sentiment_trend(messages)

            # Calculate completeness
            completeness_score = self._calculate_summary_completeness(summary_content, messages)

            # Create summary object
            summary = ConversationSummary(
                summary_id=f"summary_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                conversation_id=conversation_id,
                user_id=user_id,
                created_at=datetime.now(),
                summary_type=summary_type,
                content=summary_content,
                key_decisions=key_decisions,
                preferences_learned=preferences_learned,
                next_steps=next_steps,
                sentiment_trend=sentiment_trend,
                completeness_score=completeness_score,
                metadata={
                    "message_count": len(messages),
                    "conversation_span": self._calculate_conversation_span(messages),
                    "summary_length": len(summary_content)
                }
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return None

    async def incremental_summary(
        self,
        existing_summary: ConversationSummary,
        new_messages: List[Message]
    ) -> Optional[ConversationSummary]:
        """Update existing summary with new messages"""
        if not self.initialized:
            return None

        try:
            # Get the original messages (mock implementation)
            # In production, these would be retrieved
            all_messages = new_messages  # Simplified

            # Generate new summary
            updated_summary = await self.summarize_conversation(
                all_messages,
                existing_summary.user_id,
                existing_summary.conversation_id,
                existing_summary.summary_type
            )

            if updated_summary:
                # Preserve original summary ID
                updated_summary.summary_id = existing_summary.summary_id

                # Merge metadata
                updated_summary.metadata.update(existing_summary.metadata)
                updated_summary.metadata["incremental_update"] = True

            return updated_summary

        except Exception as e:
            logger.error(f"Failed to create incremental summary: {e}")
            return None

    async def extract_essence(
        self,
        conversation_text: str,
        max_points: int = 5
    ) -> List[str]:
        """Extract essential points from conversation"""
        if not self.initialized:
            return []

        try:
            prompt = f"""
            Extract the {max_points} most important points from this conversation.
            Focus on decisions, preferences, and key information.

            Conversation:
            {conversation_text}

            Return as JSON array:
            {{
                "key_points": [
                    "Point 1",
                    "Point 2",
                    ...
                ]
            }}
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("key_points", [])

        except Exception as e:
            logger.error(f"Failed to extract conversation essence: {e}")
            return []

    def _initialize_templates(self) -> Dict[SummaryType, str]:
        """Initialize summary templates"""
        return {
            SummaryType.KEY_DECISIONS: """
            Summarize the key decisions made in this conversation. Focus on:
            1. What vehicles or features were decided on
            2. What criteria were established
            3. What options were eliminated
            4. Any compromises or trade-offs made
            5. The reasoning behind decisions

            Keep it concise and factual.
            """,

            SummaryType.PREFERENCE_SUMMARY: """
            Summarize the user preferences learned in this conversation:
            1. Vehicle type preferences
            2. Budget constraints
            3. Feature requirements
            4. Brand preferences or aversions
            5. Lifestyle needs (family size, commute, etc.)
            6. Any conflicting preferences mentioned

            Be specific about values where mentioned.
            """,

            SummaryType.CONVERSATION_FLOW: """
            Summarize the progression of this conversation:
            1. Initial inquiry/goal
            2. Major topics discussed
            3. Questions asked and answers received
            4. Current status of search/discovery
            5. Next logical step in the process

            Maintain the flow and context.
            """,

            SummaryType.EMOTIONAL_JOURNEY: """
            Summarize the user's emotional journey through this conversation:
            1. Initial mood/attitude
            2. Points of excitement or interest
            3. Any frustrations or concerns
            4. Moments of clarity or decision
            5. Overall emotional progression

            Focus on feelings and attitudes expressed.
            """,

            SummaryType.ACTION_ITEMS: """
            Summarize action items and follow-ups needed:
            1. Research needed
            2. Questions to ask
            3. Vehicles to compare
            4. Features to investigate
            5. Next conversation points

            Be specific and actionable.
            """
        }

    def _prepare_conversation_text(self, messages: List[Message]) -> str:
        """Prepare conversation text for summarization"""
        conversation_parts = []
        for msg in messages[-50:]:  # Limit to last 50 messages
            role = msg.role.upper()
            content = msg.content.strip()
            conversation_parts.append(f"{role}: {content}")

        return "\n".join(conversation_parts)

    async def _summarize_key_decisions(self, conversation_text: str) -> str:
        """Generate summary focusing on key decisions"""
        try:
            prompt = f"""
            {self.summary_templates[SummaryType.KEY_DECISIONS]}

            Conversation:
            {conversation_text}

            Provide a concise summary in 2-3 sentences.
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize key decisions: {e}")
            return "Unable to generate summary for key decisions."

    async def _summarize_preferences(self, conversation_text: str) -> str:
        """Generate summary focusing on preferences"""
        try:
            prompt = f"""
            {self.summary_templates[SummaryType.PREFERENCE_SUMMARY]}

            Conversation:
            {conversation_text}

            Provide a concise summary of learned preferences in 2-3 sentences.
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize preferences: {e}")
            return "Unable to generate preference summary."

    async def _summarize_conversation_flow(self, conversation_text: str) -> str:
        """Generate summary focusing on conversation flow"""
        try:
            prompt = f"""
            {self.summary_templates[SummaryType.CONVERSATION_FLOW]}

            Conversation:
            {conversation_text}

            Provide a concise summary of the conversation flow in 2-3 sentences.
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize conversation flow: {e}")
            return "Unable to generate conversation flow summary."

    async def _summarize_emotional_journey(self, conversation_text: str) -> str:
        """Generate summary focusing on emotional journey"""
        try:
            prompt = f"""
            {self.summary_templates[SummaryType.EMOTIONAL_JOURNEY]}

            Conversation:
            {conversation_text}

            Provide a concise summary of the emotional journey in 2-3 sentences.
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.4  # Higher temperature for emotional content
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize emotional journey: {e}")
            return "Unable to generate emotional journey summary."

    async def _summarize_action_items(self, conversation_text: str) -> str:
        """Generate summary focusing on action items"""
        try:
            prompt = f"""
            {self.summary_templates[SummaryType.ACTION_ITEMS]}

            Conversation:
            {conversation_text}

            Provide a concise summary of action items in 2-3 sentences.
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to summarize action items: {e}")
            return "Unable to generate action items summary."

    async def _summarize_general(self, conversation_text: str) -> str:
        """Generate general conversation summary"""
        try:
            prompt = f"""
            Provide a concise summary of this conversation in 2-3 sentences.
            Focus on the main topic, key outcomes, and current status.

            Conversation:
            {conversation_text}
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate general summary: {e}")
            return "Unable to generate conversation summary."

    async def _extract_key_decisions(self, conversation_text: str) -> List[KeyDecision]:
        """Extract key decisions from conversation"""
        decisions = []

        try:
            # Look for decision indicators
            decision_indicators = [
                "decided on", "chose", "selected", "narrowed down",
                "eliminated", "ruled out", "settled on", "committed to"
            ]

            sentences = conversation_text.split('.')
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in decision_indicators):
                    # Extract decision context
                    decision = KeyDecision(
                        decision=sentence.strip(),
                        context=self._extract_context(sentence, conversation_text),
                        timestamp=datetime.now(),  # Would be actual message timestamp
                        confidence=0.8,
                        impact="medium",
                        related_entities=[]  # Would extract from sentence
                    )
                    decisions.append(decision)

            return decisions[:5]  # Limit to top 5 decisions

        except Exception as e:
            logger.error(f"Failed to extract key decisions: {e}")
            return []

    async def _extract_preferences_from_conversation(self, conversation_text: str) -> Dict[str, Any]:
        """Extract preferences learned from conversation"""
        preferences = {}

        try:
            # Simple pattern matching for common preferences
            if "under $" in conversation_text or "less than $" in conversation_text:
                # Extract budget preference
                import re
                budget_match = re.search(r'\$(\d+(?:,\d+)*)', conversation_text)
                if budget_match:
                    budget = int(budget_match.group(1).replace(',', ''))
                    if budget < 1000:
                        budget *= 1000
                    preferences["budget"] = budget

            # Extract vehicle type preferences
            vehicle_types = ["SUV", "sedan", "truck", "EV", "hybrid", "convertible"]
            for vt in vehicle_types:
                if vt.lower() in conversation_text.lower():
                    preferences["vehicle_type"] = vt
                    break

            # Extract brand preferences
            brands = ["Toyota", "Honda", "Ford", "Tesla", "BMW", "Mercedes"]
            mentioned_brands = [b for b in brands if b.lower() in conversation_text.lower()]
            if mentioned_brands:
                preferences["brands"] = mentioned_brands

            return preferences

        except Exception as e:
            logger.error(f"Failed to extract preferences: {e}")
            return {}

    async def _identify_next_steps(self, conversation_text: str) -> List[str]:
        """Identify next steps based on conversation"""
        next_steps = []

        try:
            # Analyze conversation for indicators of next steps
            if "compare" in conversation_text.lower():
                next_steps.append("Compare specific vehicles")

            if "research" in conversation_text.lower():
                next_steps.append("Research vehicle features")

            if "visit" in conversation_text.lower():
                next_steps.append("Schedule dealership visit")

            if "test drive" in conversation_text.lower():
                next_steps.append("Arrange test drive")

            # If no explicit next steps, suggest based on context
            if not next_steps:
                if "decided" in conversation_text.lower():
                    next_steps.append("Provide final recommendations")
                else:
                    next_steps.append("Continue narrowing down options")

            return next_steps[:3]  # Limit to top 3 next steps

        except Exception as e:
            logger.error(f"Failed to identify next steps: {e}")
            return []

    async def _analyze_sentiment_trend(self, messages: List[Message]) -> str:
        """Analyze sentiment trend across messages"""
        try:
            # Simple sentiment analysis based on keywords
            positive_words = ["love", "great", "perfect", "excellent", "like", "interested"]
            negative_words = ["hate", "terrible", "awful", "dislike", "frustrated", "confused"]

            sentiment_scores = []
            for msg in messages:
                content = msg.content.lower()
                pos_count = sum(1 for word in positive_words if word in content)
                neg_count = sum(1 for word in negative_words if word in content)

                score = pos_count - neg_count
                sentiment_scores.append(score)

            if not sentiment_scores:
                return "neutral"

            # Calculate trend
            if len(sentiment_scores) < 2:
                return "neutral"

            first_half = sentiment_scores[:len(sentiment_scores)//2]
            second_half = sentiment_scores[len(sentiment_scores)//2:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            if second_avg > first_avg + 0.5:
                return "positive"
            elif second_avg < first_avg - 0.5:
                return "negative"
            elif abs(second_avg - first_avg) > 1.0:
                return "mixed"
            else:
                return "neutral"

        except Exception as e:
            logger.error(f"Failed to analyze sentiment trend: {e}")
            return "neutral"

    def _calculate_summary_completeness(self, summary: str, messages: List[Message]) -> float:
        """Calculate how complete the summary is"""
        try:
            # Check for key elements
            completeness_factors = 0
            total_factors = 5

            # Has meaningful length
            if len(summary) > 50:
                completeness_factors += 1

            # Mentions key topics
            if any(word in summary.lower() for word in ["vehicle", "car", "suv", "budget", "prefer"]):
                completeness_factors += 1

            # Captures conversation outcome
            if any(word in summary.lower() for word in ["decided", "chose", "selected", "narrowed"]):
                completeness_factors += 1

            # Includes next steps
            if any(word in summary.lower() for word in ["next", "step", "follow", "continue"]):
                completeness_factors += 1

            # Reasonable length (not too short, not too long)
            if 100 <= len(summary) <= self.max_summary_length:
                completeness_factors += 1

            return completeness_factors / total_factors

        except Exception as e:
            logger.error(f"Failed to calculate summary completeness: {e}")
            return 0.0

    def _calculate_conversation_span(self, messages: List[Message]) -> int:
        """Calculate time span of conversation in minutes"""
        if len(messages) < 2:
            return 0

        try:
            first_time = messages[0].created_at or datetime.now()
            last_time = messages[-1].created_at or datetime.now()
            span = last_time - first_time
            return int(span.total_seconds() / 60)
        except:
            return 0

    def _extract_context(self, sentence: str, full_text: str) -> str:
        """Extract context around a sentence"""
        sentence_index = full_text.find(sentence)
        if sentence_index == -1:
            return ""

        # Get 100 characters before and after
        start = max(0, sentence_index - 100)
        end = min(len(full_text), sentence_index + len(sentence) + 100)
        return full_text[start:end].strip()