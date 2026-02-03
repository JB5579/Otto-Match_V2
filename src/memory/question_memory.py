"""
Question Memory for Otto.AI
Tracks questions asked across sessions using Zep Cloud temporal memory
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.memory.zep_client import ZepClient, ConversationContext, Message
from src.memory.temporal_memory import TemporalMemoryManager, MemoryType, MemoryFragment

# Configure logging
logger = logging.getLogger(__name__)

# Type hints to avoid circular imports - only import for type checking
if TYPE_CHECKING:
    from src.intelligence.questioning_strategy import Question, QuestionCategory


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
    category: Any  # QuestionCategory enum from questioning_strategy
    timestamp: datetime
    session_id: str
    status: QuestionStatus
    effectiveness: Optional[QuestionEffectiveness] = None
    user_response: Optional[str] = None
    follow_up_questions: List[str] = None

    def __post_init__(self):
        if self.follow_up_questions is None:
            self.follow_up_questions = []


@dataclass
class QuestionMetrics:
    """Metrics for question effectiveness"""
    total_asked: int = 0
    total_answered: int = 0
    total_skipped: int = 0
    average_effectiveness: float = 0.0
    most_effective_questions: List[str] = None
    least_effective_questions: List[str] = None

    def __post_init__(self):
        if self.most_effective_questions is None:
            self.most_effective_questions = []
        if self.least_effective_questions is None:
            self.least_effective_questions = []


class QuestionMemory:
    """
    Manages question history and metrics using Zep Cloud temporal memory.

    This service tracks which questions have been asked to users,
    their responses, and effectiveness ratings to optimize future questioning.
    """

    def __init__(self, zep_client: ZepClient, cache: Optional[Any] = None):
        """
        Initialize QuestionMemory with Zep client.

        Args:
            zep_client: Zep Cloud client for temporal storage
            cache: Optional cache for frequently accessed questions
        """
        self.zep_client = zep_client
        self.cache = cache
        self.temporal_memory = TemporalMemoryManager(zep_client)

        # Configure memory types
        self.memory_type = MemoryType.QUESTION_HISTORY

    async def record_question(
        self,
        user_id: str,
        question_id: str,
        question_text: str,
        category: Any,  # QuestionCategory enum
        session_id: str,
        asked_at: Optional[datetime] = None
    ) -> QuestionRecord:
        """
        Record that a question was asked to a user.

        Args:
            user_id: User identifier
            question_id: Unique question identifier
            question_text: The question text
            category: Question category
            session_id: Current session identifier
            asked_at: When the question was asked (defaults to now)

        Returns:
            QuestionRecord with the recorded information
        """
        if asked_at is None:
            asked_at = datetime.now()

        # Create memory fragment
        fragment = MemoryFragment(
            user_id=user_id,
            session_id=session_id,
            content={
                "question_id": question_id,
                "question_text": question_text,
                "category": str(category.value) if hasattr(category, 'value') else str(category),
                "action": "question_asked",
                "timestamp": asked_at.isoformat()
            },
            metadata={
                "memory_type": "question_asked",
                "question_category": str(category)
            }
        )

        # Store in temporal memory
        await self.temporal_memory.add_fragment(fragment, memory_type=self.memory_type)

        # Create record
        record = QuestionRecord(
            question_id=question_id,
            question_text=question_text,
            category=category,
            timestamp=asked_at,
            session_id=session_id,
            status=QuestionStatus.ASKED
        )

        logger.info(f"Recorded question '{question_id}' for user {user_id}")

        return record

    async def record_answer(
        self,
        user_id: str,
        question_id: str,
        answer: str,
        session_id: str,
        effectiveness: Optional[QuestionEffectiveness] = None
    ) -> QuestionRecord:
        """
        Record a user's answer to a question.

        Args:
            user_id: User identifier
            question_id: Question identifier
            answer: User's response
            session_id: Current session identifier
            effectiveness: Optional effectiveness rating

        Returns:
            Updated QuestionRecord
        """
        answered_at = datetime.now()

        # Create memory fragment for answer
        fragment = MemoryFragment(
            user_id=user_id,
            session_id=session_id,
            content={
                "question_id": question_id,
                "answer": answer,
                "effectiveness": str(effectiveness.value) if effectiveness else None,
                "action": "question_answered",
                "timestamp": answered_at.isoformat()
            },
            metadata={
                "memory_type": "question_answered",
                "effectiveness": str(effectiveness) if effectiveness else None
            }
        )

        # Store in temporal memory
        await self.temporal_memory.add_fragment(fragment, memory_type=self.memory_type)

        # Create record
        record = QuestionRecord(
            question_id=question_id,
            question_text="",  # Will be populated from memory
            category=Any,  # Will be populated from memory
            timestamp=answered_at,
            session_id=session_id,
            status=QuestionStatus.ANSWERED,
            user_response=answer,
            effectiveness=effectiveness
        )

        logger.info(f"Recorded answer for question '{question_id}' from user {user_id}")

        return record

    async def get_user_question_history(
        self,
        user_id: str,
        category: Optional[Any] = None,
        days_back: int = 30,
        limit: int = 100
    ) -> List[QuestionRecord]:
        """
        Get question history for a user.

        Args:
            user_id: User identifier
            category: Optional category filter
            days_back: How many days back to look
            limit: Maximum number of records to return

        Returns:
            List of QuestionRecords
        """
        since_date = datetime.now() - timedelta(days=days_back)

        # Retrieve from temporal memory
        fragments = await self.temporal_memory.retrieve_by_user(
            user_id=user_id,
            memory_type=self.memory_type,
            since=since_date
        )

        # Convert to QuestionRecords
        records = []
        for fragment in fragments[:limit]:
            content = fragment.content
            metadata = fragment.metadata or {}

            # Determine status from action
            action = content.get("action", "")
            if action == "question_answered":
                status = QuestionStatus.ANSWERED
            elif action == "question_asked":
                status = QuestionStatus.ASKED
            else:
                status = QuestionStatus.SKIPPED

            # Map category string back to enum if needed
            category_str = metadata.get("question_category")
            # Note: For runtime, we keep as string to avoid circular import

            record = QuestionRecord(
                question_id=content.get("question_id", ""),
                question_text=content.get("question_text", ""),
                category=category_str,  # String representation to avoid circular import
                timestamp=datetime.fromisoformat(content.get("timestamp", datetime.now().isoformat())),
                session_id=content.get("session_id", ""),
                status=status,
                user_response=content.get("answer"),
                effectiveness=QuestionEffectiveness(metadata.get("effectiveness")) if metadata.get("effectiveness") else None
            )
            records.append(record)

        # Filter by category if specified
        if category:
            category_str = str(category.value) if hasattr(category, 'value') else str(category)
            records = [r for r in records if str(r.category) == category_str]

        logger.info(f"Retrieved {len(records)} question records for user {user_id}")

        return records

    async def was_question_asked(
        self,
        user_id: str,
        question_id: str,
        days_back: int = 7
    ) -> bool:
        """
        Check if a specific question was asked to a user.

        Args:
            user_id: User identifier
            question_id: Question identifier
            days_back: How many days back to check

        Returns:
            True if the question was asked
        """
        history = await self.get_user_question_history(
            user_id=user_id,
            days_back=days_back,
            limit=1000
        )

        return any(record.question_id == question_id for record in history)

    async def get_questions_by_category(
        self,
        user_id: str,
        category: Any,
        days_back: int = 30
    ) -> List[QuestionRecord]:
        """
        Get all questions from a specific category.

        Args:
            user_id: User identifier
            category: Question category to filter by
            days_back: How many days back to look

        Returns:
            List of QuestionRecords from the category
        """
        return await self.get_user_question_history(
            user_id=user_id,
            category=category,
            days_back=days_back
        )

    async def calculate_metrics(
        self,
        user_id: str,
        days_back: int = 30
    ) -> QuestionMetrics:
        """
        Calculate question effectiveness metrics for a user.

        Args:
            user_id: User identifier
            days_back: How many days back to analyze

        Returns:
            QuestionMetrics with calculated statistics
        """
        history = await self.get_user_question_history(
            user_id=user_id,
            days_back=days_back,
            limit=1000
        )

        total_asked = len([r for r in history if r.status == QuestionStatus.ASKED or r.status == QuestionStatus.ANSWERED])
        total_answered = len([r for r in history if r.status == QuestionStatus.ANSWERED])
        total_skipped = len([r for r in history if r.status == QuestionStatus.SKIPPED])

        # Calculate average effectiveness
        effectiveness_values = [
            r.effectiveness.value for r in history
            if r.effectiveness is not None
        ]

        if effectiveness_values:
            # Map enum values to numeric scores
            score_map = {
                "very_poor": 1,
                "poor": 2,
                "average": 3,
                "good": 4,
                "excellent": 5
            }
            scores = [score_map.get(e, 3) for e in effectiveness_values]
            average_effectiveness = sum(scores) / len(scores)
        else:
            average_effectiveness = 0.0

        # Identify most/least effective questions
        question_scores = {}
        for record in history:
            if record.effectiveness is not None:
                if record.question_id not in question_scores:
                    question_scores[record.question_id] = []
                score_map = {
                    QuestionEffectiveness.VERY_POOR: 1,
                    QuestionEffectiveness.POOR: 2,
                    QuestionEffectiveness.AVERAGE: 3,
                    QuestionEffectiveness.GOOD: 4,
                    QuestionEffectiveness.EXCELLENT: 5
                }
                question_scores[record.question_id].append(score_map.get(record.effectiveness, 3))

        # Calculate averages per question
        question_averages = {
            q_id: sum(scores) / len(scores)
            for q_id, scores in question_scores.items()
        }

        # Sort by effectiveness
        most_effective = sorted(
            question_averages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        least_effective = sorted(
            question_averages.items(),
            key=lambda x: x[1]
        )[:5]

        metrics = QuestionMetrics(
            total_asked=total_asked,
            total_answered=total_answered,
            total_skipped=total_skipped,
            average_effectiveness=average_effectiveness,
            most_effective_questions=[q[0] for q in most_effective],
            least_effective_questions=[q[0] for q in least_effective]
        )

        logger.info(f"Calculated metrics for user {user_id}: {metrics}")

        return metrics

    async def cleanup_old_questions(
        self,
        user_id: str,
        days_to_keep: int = 90
    ) -> int:
        """
        Clean up old question records beyond retention period.

        Args:
            user_id: User identifier
            days_to_keep: How many days of history to keep

        Returns:
            Number of records cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Get old fragments
        fragments = await self.temporal_memory.retrieve_by_user(
            user_id=user_id,
            memory_type=self.memory_type,
            since=cutoff_date
        )

        # In production, you might want to archive these instead of deleting
        # For now, this is a placeholder for cleanup logic
        cleaned_count = len(fragments)

        logger.info(f"Cleanup: Found {cleaned_count} old question records for user {user_id}")

        return cleaned_count


# Singleton instance for dependency injection
_question_memory_instance: Optional[QuestionMemory] = None


def get_question_memory(zep_client: Optional[ZepClient] = None) -> QuestionMemory:
    """
    Get or create the QuestionMemory singleton instance.

    Args:
        zep_client: Optional Zep client (uses existing instance if provided)

    Returns:
        QuestionMemory instance
    """
    global _question_memory_instance

    if _question_memory_instance is None:
        if zep_client is None:
            raise ValueError("Zep client required for first initialization")

        _question_memory_instance = QuestionMemory(zep_client=zep_client)

    return _question_memory_instance
