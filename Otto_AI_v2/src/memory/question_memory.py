"""
Question Memory for Otto.AI
Tracks questions asked across sessions using Zep Cloud temporal memory
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.memory.zep_client import ZepClient, ConversationContext, Message
from src.memory.temporal_memory import TemporalMemoryManager, MemoryType, MemoryFragment

# Configure logging
logger = logging.getLogger(__name__)

# Type hints to avoid circular imports
Question = Any
QuestionCategory = Any


class QuestionStatus(Enum):
    """Status of a question in the conversation flow"""
    ASKED = "asked"
    ANSWERED = "answered"
    SKIPPED = "skipped"
    DECLINED = "declined"
    FOLLOW_UP = "follow_up"


class QuestionEffectiveness(Enum):
    """Effectiveness rating for questions"""
    VERY_POOR = "very_poor"
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class QuestionRecord:
    """Record of a question asked to a user"""
    question_id: str
    question_text: str
    category: QuestionCategory
    timestamp: datetime
    session_id: str
    status: QuestionStatus
    response: Optional[str]
    response_time_ms: Optional[int]
    effectiveness_score: Optional[float]
    follow_up_generated: bool
    metadata: Dict[str, Any]


@dataclass
class QuestionPattern:
    """Pattern in user's question responses"""
    pattern_type: str  # "category_preference", "response_length", "time_of_day"
    frequency: float
    confidence: float
    last_seen: datetime
    associated_questions: List[str]


@dataclass
class PreferenceEvolution:
    """Tracks how preferences have changed over time"""
    preference_key: str
    initial_value: Any
    current_value: Any
    change_count: int
    change_dates: List[datetime]
    questions_triggered: List[str]
    confidence_score: float


class QuestionMemory:
    """Manages question history and cross-session tracking"""

    def __init__(
        self,
        zep_client: ZepClient,
        temporal_memory: TemporalMemoryManager
    ):
        self.zep_client = zep_client
        self.temporal_memory = temporal_memory
        self.initialized = False

        # In-memory cache for recent questions
        self.recent_questions_cache: Dict[str, List[QuestionRecord]] = {}
        self.cache_expiry_minutes = 10

        # Question effectiveness tracking
        self.effectiveness_threshold = 0.5
        self.min_samples_for_effectiveness = 5

    async def initialize(self) -> bool:
        """Initialize the question memory manager"""
        try:
            if not self.zep_client.initialized:
                logger.error("Zep client not initialized")
                return False

            if not self.temporal_memory.initialized:
                logger.error("Temporal memory not initialized")
                return False

            self.initialized = True
            logger.info("Question memory initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize question memory: {e}")
            return False

    async def track_question(
        self,
        user_id: str,
        question: Question,
        session_id: str,
        response: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        engagement_indicators: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a question asked to the user
        """
        if not self.initialized:
            return False

        try:
            # Create question record
            record = QuestionRecord(
                question_id=question.id,
                question_text=question.text,
                category=question.category,
                timestamp=datetime.now(),
                session_id=session_id,
                status=QuestionStatus.ASKED,
                response=response,
                response_time_ms=response_time_ms,
                effectiveness_score=None,
                follow_up_generated=False,
                metadata={
                    "complexity": question.complexity.value,
                    "information_value": question.information_value,
                    "engagement_potential": question.engagement_potential,
                    "tags": question.tags,
                    "engagement_indicators": engagement_indicators or {}
                }
            )

            # Store in temporal memory
            memory_fragment = MemoryFragment(
                content=asdict(record),
                memory_type=MemoryType.EPISODIC,
                importance=question.information_value,
                timestamp=record.timestamp,
                decay_factor=0.1,
                associated_preferences=[]
            )

            await self.temporal_memory.store_memory(user_id, memory_fragment)

            # Update cache
            await self._update_cache(user_id, record)

            logger.debug(f"Tracked question {question.id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to track question: {e}")
            return False

    async def update_question_response(
        self,
        user_id: str,
        question_id: str,
        response: str,
        response_time_ms: Optional[int] = None,
        effectiveness_score: Optional[float] = None
    ) -> bool:
        """
        Update a question record with the user's response
        """
        if not self.initialized:
            return False

        try:
            # Find the question record
            records = await self.get_user_question_history(user_id, limit=50)

            for record in records:
                if record.question_id == question_id and record.status == QuestionStatus.ASKED:
                    # Update the record
                    record.response = response
                    record.response_time_ms = response_time_ms
                    record.status = QuestionStatus.ANSWERED
                    record.effectiveness_score = effectiveness_score

                    # Store updated record
                    memory_fragment = MemoryFragment(
                        content=asdict(record),
                        memory_type=MemoryType.EPISODIC,
                        importance=record.metadata.get("information_value", 0.5),
                        timestamp=datetime.now(),
                        decay_factor=0.1,
                        associated_preferences=[]
                    )

                    await self.temporal_memory.store_memory(user_id, memory_fragment)

                    # Update cache
                    await self._update_cache_record(user_id, record)

                    logger.debug(f"Updated response for question {question_id}")
                    return True

            logger.warning(f"Question {question_id} not found or already answered")
            return False

        except Exception as e:
            logger.error(f"Failed to update question response: {e}")
            return False

    async def has_question_been_asked(
        self,
        user_id: str,
        question_id: str,
        within_days: Optional[int] = None
    ) -> bool:
        """
        Check if a question has been asked to the user
        """
        if not self.initialized:
            return False

        try:
            # Check cache first
            if user_id in self.recent_questions_cache:
                for record in self.recent_questions_cache[user_id]:
                    if record.question_id == question_id:
                        if within_days is None:
                            return True

                        days_diff = (datetime.now() - record.timestamp).days
                        if days_diff <= within_days:
                            return True

            # Check temporal memory
            memories = await self.temporal_memory.retrieve_by_user(
                user_id,
                pattern=f"question_id:{question_id}",
                limit=10
            )

            for memory in memories:
                record_data = memory.content
                if record_data.get("question_id") == question_id:
                    if within_days is None:
                        return True

                    question_date = memory.timestamp
                    days_diff = (datetime.now() - question_date).days
                    if days_diff <= within_days:
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to check if question was asked: {e}")
            return False

    async def get_questions_by_category(
        self,
        user_id: str,
        category: QuestionCategory,
        limit: int = 20
    ) -> List[QuestionRecord]:
        """
        Get all questions asked in a specific category
        """
        if not self.initialized:
            return []

        try:
            all_records = await self.get_user_question_history(user_id, limit=100)

            category_records = [
                record for record in all_records
                if record.category == category
            ]

            # Sort by timestamp descending
            category_records.sort(key=lambda x: x.timestamp, reverse=True)

            return category_records[:limit]

        except Exception as e:
            logger.error(f"Failed to get questions by category: {e}")
            return []

    async def detect_preference_changes(
        self,
        user_id: str,
        preference_key: str,
        new_value: Any
    ) -> Optional[PreferenceEvolution]:
        """
        Detect and track changes in user preferences
        """
        if not self.initialized:
            return None

        try:
            # Look for previous mentions of this preference
            memories = await self.temporal_memory.retrieve_by_user(
                user_id,
                pattern=f"preference:{preference_key}",
                limit=20
            )

            if not memories:
                # First time seeing this preference
                evolution = PreferenceEvolution(
                    preference_key=preference_key,
                    initial_value=new_value,
                    current_value=new_value,
                    change_count=0,
                    change_dates=[],
                    questions_triggered=[],
                    confidence_score=1.0
                )
            else:
                # Track evolution
                most_recent = max(memories, key=lambda m: m.timestamp)
                initial_value = most_recent.content.get("initial_value", new_value)

                # Check if value actually changed
                if initial_value == new_value:
                    return None

                # Count changes
                change_count = sum(1 for m in memories if m.content.get("value") != new_value)

                # Collect questions that triggered changes
                questions_triggered = [
                    m.content.get("question_id", "unknown")
                    for m in memories
                    if m.content.get("question_id")
                ]

                evolution = PreferenceEvolution(
                    preference_key=preference_key,
                    initial_value=initial_value,
                    current_value=new_value,
                    change_count=change_count,
                    change_dates=[m.timestamp for m in memories],
                    questions_triggered=questions_triggered,
                    confidence_score=min(0.9, 0.5 + (change_count * 0.1))
                )

            # Store the evolution
            memory_fragment = MemoryFragment(
                content={
                    "type": "preference_evolution",
                    "preference_key": preference_key,
                    "value": new_value,
                    "evolution": asdict(evolution)
                },
                memory_type=MemoryType.SEMANTIC,
                importance=0.7,
                timestamp=datetime.now(),
                decay_factor=0.05,
                associated_preferences=[]
            )

            await self.temporal_memory.store_memory(user_id, memory_fragment)

            return evolution

        except Exception as e:
            logger.error(f"Failed to detect preference changes: {e}")
            return None

    async def get_question_effectiveness(
        self,
        user_id: str,
        question_id: str
    ) -> Optional[float]:
        """
        Get the effectiveness score for a specific question
        """
        if not self.initialized:
            return None

        try:
            # Look for question effectiveness patterns
            memories = await self.temporal_memory.retrieve_by_user(
                user_id,
                pattern=f"question_effectiveness:{question_id}",
                limit=10
            )

            if memories:
                # Calculate average effectiveness
                scores = [m.content.get("score", 0.5) for m in memories]
                return sum(scores) / len(scores)

            return None

        except Exception as e:
            logger.error(f"Failed to get question effectiveness: {e}")
            return None

    async def calculate_question_effectiveness(
        self,
        user_id: str,
        question: Question,
        response: str,
        response_time_ms: int,
        engagement_indicators: Dict[str, Any]
    ) -> float:
        """
        Calculate effectiveness score for a question response
        """
        effectiveness = 0.0

        try:
            # Response quality (length and detail)
            word_count = len(response.split())
            if word_count > 15:
                effectiveness += 0.3
            elif word_count > 8:
                effectiveness += 0.2
            elif word_count > 3:
                effectiveness += 0.1

            # Response time (too quick might mean low engagement)
            if response_time_ms:
                if 3000 <= response_time_ms <= 15000:  # 3-15 seconds
                    effectiveness += 0.2
                elif response_time_ms > 30000:  # Very thoughtful response
                    effectiveness += 0.3
                elif response_time_ms < 2000:  # Too quick
                    effectiveness -= 0.1

            # Engagement indicators
            engagement_score = engagement_indicators.get("engagement_score", 0.5)
            effectiveness += engagement_score * 0.2

            # Information extraction
            if self._contains_preference_information(response):
                effectiveness += 0.2

            # Sentiment and follow-up readiness
            sentiment = engagement_indicators.get("sentiment", "neutral")
            if sentiment in ["positive", "excited", "thoughtful"]:
                effectiveness += 0.1

            # Follow-up questions or requests
            if "?" in response or "what about" in response.lower():
                effectiveness += 0.1

            # Store the effectiveness for learning
            await self._store_question_effectiveness(
                user_id, question.id, effectiveness
            )

            return min(max(effectiveness, 0.0), 1.0)

        except Exception as e:
            logger.error(f"Failed to calculate question effectiveness: {e}")
            return 0.5  # Default to average

    async def get_user_question_history(
        self,
        user_id: str,
        limit: int = 50,
        category: Optional[QuestionCategory] = None,
        days_back: Optional[int] = None
    ) -> List[QuestionRecord]:
        """
        Get the user's question history
        """
        if not self.initialized:
            return []

        try:
            # Check cache first
            cache_key = f"{user_id}_{limit}_{category}_{days_back}"
            if cache_key in self.recent_questions_cache:
                cache_time = self.recent_questions_cache[cache_key][0].timestamp if self.recent_questions_cache[cache_key] else datetime.min
                if (datetime.now() - cache_time).total_seconds() < self.cache_expiry_minutes * 60:
                    return self.recent_questions_cache[cache_key]

            # Retrieve from temporal memory
            memories = await self.temporal_memory.retrieve_by_user(
                user_id,
                pattern="question_record",
                limit=limit * 2  # Get more to filter
            )

            # Convert to QuestionRecord objects
            records = []
            for memory in memories:
                if memory.content.get("question_id"):
                    record = QuestionRecord(**memory.content)
                    record.timestamp = memory.timestamp

                    # Apply filters
                    if category and record.category != category:
                        continue

                    if days_back:
                        days_diff = (datetime.now() - record.timestamp).days
                        if days_diff > days_back:
                            continue

                    records.append(record)

            # Sort by timestamp descending
            records.sort(key=lambda x: x.timestamp, reverse=True)

            # Update cache
            self.recent_questions_cache[cache_key] = records[:limit]

            return records[:limit]

        except Exception as e:
            logger.error(f"Failed to get user question history: {e}")
            return []

    async def _update_cache(self, user_id: str, record: QuestionRecord) -> None:
        """Update the in-memory cache with a new record"""
        if user_id not in self.recent_questions_cache:
            self.recent_questions_cache[user_id] = []

        self.recent_questions_cache[user_id].insert(0, record)

        # Keep cache size manageable
        if len(self.recent_questions_cache[user_id]) > 100:
            self.recent_questions_cache[user_id] = self.recent_questions_cache[user_id][:100]

    async def _update_cache_record(self, user_id: str, updated_record: QuestionRecord) -> None:
        """Update a specific record in the cache"""
        if user_id in self.recent_questions_cache:
            for i, record in enumerate(self.recent_questions_cache[user_id]):
                if record.question_id == updated_record.question_id:
                    self.recent_questions_cache[user_id][i] = updated_record
                    break

    async def _store_question_effectiveness(
        self,
        user_id: str,
        question_id: str,
        score: float
    ) -> None:
        """Store question effectiveness for learning"""
        try:
            memory_fragment = MemoryFragment(
                content={
                    "type": "question_effectiveness",
                    "question_id": question_id,
                    "score": score,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type=MemoryType.SEMANTIC,
                importance=score,
                timestamp=datetime.now(),
                decay_factor=0.05,
                associated_preferences=[]
            )

            await self.temporal_memory.store_memory(user_id, memory_fragment)

        except Exception as e:
            logger.error(f"Failed to store question effectiveness: {e}")

    def _contains_preference_information(self, response: str) -> bool:
        """Check if response contains preference information"""
        preference_keywords = [
            "prefer", "like", "want", "need", "important", "priority",
            "must have", "deal breaker", "essential", "looking for",
            "would rather", "instead of", "compared to"
        ]

        response_lower = response.lower()
        return any(keyword in response_lower for keyword in preference_keywords)

    async def get_cross_session_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get insights about question patterns across sessions
        """
        if not self.initialized:
            return {}

        try:
            insights = {}

            # Get all question records
            all_records = await self.get_user_question_history(user_id, limit=200)

            if not all_records:
                return {"message": "No question history available"}

            # Category preferences
            category_counts = {}
            for record in all_records:
                cat = record.category.value
                category_counts[cat] = category_counts.get(cat, 0) + 1
            insights["category_preferences"] = category_counts

            # Most effective questions
            effective_questions = [
                (r.question_id, r.effectiveness_score)
                for r in all_records
                if r.effectiveness_score and r.effectiveness_score > 0.7
            ]
            effective_questions.sort(key=lambda x: x[1], reverse=True)
            insights["most_effective_questions"] = effective_questions[:5]

            # Response patterns
            response_times = [r.response_time_ms for r in all_records if r.response_time_ms]
            if response_times:
                insights["avg_response_time_ms"] = sum(response_times) / len(response_times)

            # Session frequency
            sessions = set(r.session_id for r in all_records)
            insights["total_sessions"] = len(sessions)
            insights["questions_per_session"] = len(all_records) / len(sessions) if sessions else 0

            # Recent activity
            last_question = max(all_records, key=lambda x: x.timestamp) if all_records else None
            if last_question:
                insights["days_since_last_question"] = (datetime.now() - last_question.timestamp).days

            return insights

        except Exception as e:
            logger.error(f"Failed to get cross-session insights: {e}")
            return {"error": str(e)}