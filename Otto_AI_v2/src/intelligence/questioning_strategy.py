"""
Questioning Strategy for Otto.AI
Adaptive question selection algorithms for intelligent preference discovery
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.memory.temporal_memory import TemporalMemoryManager, MemoryType, MemoryFragment

# Configure logging
logger = logging.getLogger(__name__)

# Type hints to avoid circular imports
GroqClient = Any
PreferenceEngine = Any
PreferenceCategory = Any


class QuestionCategory(Enum):
    """Categories of questions for targeted discovery"""
    FAMILY = "family"
    PERFORMANCE = "performance"
    BUDGET = "budget"
    LIFESTYLE = "lifestyle"
    SAFETY = "safety"
    TECHNOLOGY = "technology"
    ENVIRONMENT = "environment"
    USAGE = "usage"
    BRAND = "brand"
    FEATURE = "feature"


class QuestionComplexity(Enum):
    """Complexity levels for questions"""
    BASIC = "basic"           # Simple yes/no or single choice
    INTERMEDIATE = "intermediate"  # Requires some thought
    ADVANCED = "advanced"     # Complex scenario or trade-off
    OPEN = "open"            # Open-ended discussion


@dataclass
class Question:
    """Represents a question that can be asked to the user"""
    id: str
    text: str
    category: QuestionCategory
    complexity: QuestionComplexity
    information_value: float  # 0.0 to 1.0
    engagement_potential: float  # 0.0 to 1.0
    follow_up_questions: List[str]  # IDs of potential follow-ups
    prerequisites: List[str]  # Context needed before asking
    tags: List[str]  # Additional metadata
    example_answers: List[str]  # Sample answers for training


@dataclass
class UserContext:
    """Current context about the user and conversation"""
    user_id: str
    conversation_stage: str  # greeting, discovery, refinement, etc.
    known_preferences: Dict[str, Any]
    recent_topics: List[str]
    engagement_level: float  # 0.0 to 1.0
    questions_asked: Set[str]
    last_question_time: Optional[datetime]
    response_patterns: Dict[str, Any]
    fatigue_indicators: List[str]


@dataclass
class QuestionScore:
    """Score breakdown for a question"""
    question_id: str
    information_value: float
    engagement_score: float
    timing_score: float
    novelty_score: float
    total_score: float
    selection_reasons: List[str]


class QuestioningStrategy:
    """Adaptive question selection strategy for Otto AI"""

    def __init__(
        self,
        groq_client: GroqClient,
        temporal_memory: TemporalMemoryManager,
        preference_engine: PreferenceEngine
    ):
        self.groq_client = groq_client
        self.temporal_memory = temporal_memory
        self.preference_engine = preference_engine
        self.initialized = False

        # Question database
        self.questions: Dict[str, Question] = {}

        # Adaptive parameters
        self.information_weights = {
            QuestionCategory.FAMILY: 0.9,
            QuestionCategory.BUDGET: 0.85,
            QuestionCategory.USAGE: 0.8,
            QuestionCategory.PERFORMANCE: 0.75,
            QuestionCategory.LIFESTYLE: 0.7,
            QuestionCategory.SAFETY: 0.65,
            QuestionCategory.FEATURE: 0.6,
            QuestionCategory.BRAND: 0.5,
            QuestionCategory.TECHNOLOGY: 0.45,
            QuestionCategory.ENVIRONMENT: 0.4
        }

        # Conversation flow management
        self.min_questions_between_topics = 2
        self.max_questions_per_session = 10
        self.engagement_threshold = 0.3

        # Initialize question database
        self._load_question_database()

    async def initialize(self) -> bool:
        """Initialize the questioning strategy"""
        try:
            # Validate dependencies
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            if not self.temporal_memory.initialized:
                logger.error("Temporal memory not initialized")
                return False

            if not self.preference_engine.initialized:
                logger.error("Preference engine not initialized")
                return False

            # Load any dynamic questions from memory
            await self._load_dynamic_questions()

            self.initialized = True
            logger.info("Questioning strategy initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize questioning strategy: {e}")
            return False

    def _load_question_database(self) -> None:
        """Load the static question database"""
        # Family-related questions
        self.questions["family_size"] = Question(
            id="family_size",
            text="How many people will typically be traveling in this vehicle?",
            category=QuestionCategory.FAMILY,
            complexity=QuestionComplexity.BASIC,
            information_value=0.9,
            engagement_potential=0.7,
            follow_up_questions=["family_ages", "family_activities"],
            prerequisites=[],
            tags=["family", "size", "capacity"],
            example_answers=["Just me", "Two people", "Four of us", "Five or more"]
        )

        self.questions["family_ages"] = Question(
            id="family_ages",
            text="What are the age ranges of the passengers? This helps me recommend appropriate safety features.",
            category=QuestionCategory.FAMILY,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.85,
            engagement_potential=0.6,
            follow_up_questions=["car_seats", "safety_priorities"],
            prerequisites=["family_size"],
            tags=["family", "safety", "children"],
            example_answers=["Adults only", "One teenager", "Young children", "Mix of ages"]
        )

        self.questions["family_activities"] = Question(
            id="family_activities",
            text="What kind of activities does your family do together? This helps me find vehicles with the right features.",
            category=QuestionCategory.LIFESTYLE,
            complexity=QuestionComplexity.OPEN,
            information_value=0.8,
            engagement_potential=0.8,
            follow_up_questions=["cargo_needs", "feature_priorities"],
            prerequisites=["family_size"],
            tags=["lifestyle", "activities", "recreation"],
            example_answers=["Sports practices", "Road trips", "Daily commuting", "Outdoor adventures"]
        )

        # Performance-related questions
        self.questions["performance_priority"] = Question(
            id="performance_priority",
            text="When you think about performance, what matters most to you? Speed, acceleration, handling, or something else?",
            category=QuestionCategory.PERFORMANCE,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.75,
            engagement_potential=0.7,
            follow_up_questions=["performance_vs_efficiency", "driving_conditions"],
            prerequisites=[],
            tags=["performance", "driving", "preferences"],
            example_answers=["Acceleration", "Handling", "All-around balance", "Not a priority"]
        )

        self.questions["performance_vs_efficiency"] = Question(
            id="performance_vs_efficiency",
            text="I notice you're interested in both performance and efficiency. Most vehicles balance these differently. Which would you prioritize if you had to choose?",
            category=QuestionCategory.PERFORMANCE,
            complexity=QuestionComplexity.ADVANCED,
            information_value=0.9,
            engagement_potential=0.6,
            follow_up_questions=["hybrid_interest", "driving_style"],
            prerequisites=["performance_priority"],
            tags=["performance", "efficiency", "trade_off", "conflict"],
            example_answers=["Performance is more important", "Efficiency matters more", "Need a good balance"]
        )

        # Budget-related questions
        self.questions["budget_range"] = Question(
            id="budget_range",
            text="What's your budget range for this vehicle? Having a clear budget helps me find the best options.",
            category=QuestionCategory.BUDGET,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.85,
            engagement_potential=0.5,
            follow_up_questions=["payment_preference", "total_cost_focus"],
            prerequisites=[],
            tags=["budget", "price", "financial"],
            example_answers=["Under $30k", "$30-50k", "$50-70k", "Over $70k"]
        )

        self.questions["payment_preference"] = Question(
            id="payment_preference",
            text="Would you prefer to focus on the monthly payment or the total cost of ownership?",
            category=QuestionCategory.BUDGET,
            complexity=QuestionComplexity.BASIC,
            information_value=0.7,
            engagement_potential=0.6,
            follow_up_questions=["ownership_duration"],
            prerequisites=["budget_range"],
            tags=["budget", "payment", "planning"],
            example_answers=["Monthly payment", "Total cost", "Both are important"]
        )

        # Usage-related questions
        self.questions["daily_commute"] = Question(
            id="daily_commute",
            text="Tell me about your daily driving. How far do you typically drive and what kind of roads?",
            category=QuestionCategory.USAGE,
            complexity=QuestionComplexity.OPEN,
            information_value=0.8,
            engagement_potential=0.6,
            follow_up_questions=["weekend_driving", "road_trip_frequency"],
            prerequisites=[],
            tags=["usage", "commute", "daily"],
            example_answers=["Short city drives", "Long highway commute", "Mixed driving", "Work from home"]
        )

        self.questions["road_trip_frequency"] = Question(
            id="road_trip_frequency",
            text="How often do you take road trips or long drives? This affects comfort and feature priorities.",
            category=QuestionCategory.LIFESTYLE,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.7,
            engagement_potential=0.7,
            follow_up_questions=["road_trip_preferences", "entertainment_needs"],
            prerequisites=["daily_commute"],
            tags=["lifestyle", "travel", "road_trip"],
            example_answers=["Never", "Once or twice a year", "Monthly", "Frequently"]
        )

        # Safety-related questions
        self.questions["safety_priorities"] = Question(
            id="safety_priorities",
            text="What safety features are most important to you? Crash protection, driver assistance, or specific technologies?",
            category=QuestionCategory.SAFETY,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.8,
            engagement_potential=0.6,
            follow_up_questions=["safety_technology_interest"],
            prerequisites=["family_ages"],
            tags=["safety", "features", "protection"],
            example_answers=["Crash ratings", "Driver assistance", "Child safety", "All safety features"]
        )

        # Technology-related questions
        self.questions["tech_interest"] = Question(
            id="tech_interest",
            text="How do you feel about technology in vehicles? Do you prefer cutting-edge tech or simpler, more traditional interfaces?",
            category=QuestionCategory.TECHNOLOGY,
            complexity=QuestionComplexity.INTERMEDIATE,
            information_value=0.6,
            engagement_potential=0.7,
            follow_up_questions=["specific_tech_features", "infotainment_preference"],
            prerequisites=[],
            tags=["technology", "interface", "preferences"],
            example_answers=["Love technology", "Keep it simple", "Balance of both", "Tech frustrates me"]
        )

        logger.info(f"Loaded {len(self.questions)} questions in database")

    async def _load_dynamic_questions(self) -> None:
        """Load dynamic questions generated from learning"""
        try:
            # Check temporal memory for effective questions
            effective_questions = await self.temporal_memory.retrieve_by_pattern(
                pattern="question_effectiveness",
                limit=50
            )

            for memory in effective_questions:
                if memory.content.get("question_template"):
                    # Add high-performing dynamic questions
                    question_id = f"dynamic_{memory.id[:8]}"
                    if question_id not in self.questions:
                        self.questions[question_id] = Question(
                            id=question_id,
                            text=memory.content["question_template"],
                            category=QuestionCategory(memory.content.get("category", "lifestyle")),
                            complexity=QuestionComplexity(memory.content.get("complexity", "intermediate")),
                            information_value=memory.content.get("effectiveness_score", 0.5),
                            engagement_potential=memory.content.get("engagement_score", 0.5),
                            follow_up_questions=memory.content.get("follow_ups", []),
                            prerequisites=memory.content.get("prereqs", []),
                            tags=memory.content.get("tags", []),
                            example_answers=memory.content.get("examples", [])
                        )

            logger.info(f"Loaded {len([q for q in self.questions if q.startswith('dynamic_')])} dynamic questions")

        except Exception as e:
            logger.warning(f"Failed to load dynamic questions: {e}")

    async def select_next_question(
        self,
        user_context: UserContext,
        max_questions: int = 3
    ) -> List[QuestionScore]:
        """
        Select the best next questions to ask based on user context
        """
        if not self.initialized:
            logger.error("Questioning strategy not initialized")
            return []

        try:
            # Calculate scores for all eligible questions
            scored_questions = await self._score_all_questions(user_context)

            # Sort by total score
            scored_questions.sort(key=lambda x: x.total_score, reverse=True)

            # Apply conversation flow constraints
            filtered_questions = await self._apply_flow_constraints(scored_questions, user_context)

            # Return top questions
            return filtered_questions[:max_questions]

        except Exception as e:
            logger.error(f"Failed to select next question: {e}")
            return []

    async def _score_all_questions(self, user_context: UserContext) -> List[QuestionScore]:
        """Score all questions based on current context"""
        scored_questions = []

        for question_id, question in self.questions.items():
            # Skip already asked questions
            if question_id in user_context.questions_asked:
                continue

            # Skip if prerequisites not met
            if not await self._check_prerequisites(question, user_context):
                continue

            # Calculate various scores
            info_score = await self._calculate_information_value(question, user_context)
            engagement_score = await self._calculate_engagement_potential(question, user_context)
            timing_score = await self._calculate_timing_score(question, user_context)
            novelty_score = await self._calculate_novelty_score(question, user_context)

            # Combine scores with weights
            total_score = (
                info_score * 0.35 +
                engagement_score * 0.25 +
                timing_score * 0.20 +
                novelty_score * 0.20
            )

            # Generate selection reasons
            reasons = await self._generate_selection_reasons(
                question, info_score, engagement_score, timing_score, novelty_score
            )

            scored_questions.append(QuestionScore(
                question_id=question_id,
                information_value=info_score,
                engagement_score=engagement_score,
                timing_score=timing_score,
                novelty_score=novelty_score,
                total_score=total_score,
                selection_reasons=reasons
            ))

        return scored_questions

    async def _check_prerequisites(self, question: Question, user_context: UserContext) -> bool:
        """Check if question prerequisites are met"""
        for prereq in question.prerequisites:
            if prereq not in user_context.questions_asked:
                return False
        return True

    async def _calculate_information_value(
        self,
        question: Question,
        user_context: UserContext
    ) -> float:
        """Calculate the information value of a question"""
        base_value = question.information_value

        # Adjust based on category weight
        category_weight = self.information_weights.get(question.category, 0.5)

        # Boost value if it fills a knowledge gap
        category_filled = any(
            q.category == question.category
            for q_id in user_context.questions_asked
            if q_id in self.questions
        )
        if category_filled:
            base_value *= 0.5  # Reduce if category already addressed

        # Boost for high-priority categories based on conversation
        if user_context.conversation_stage == "discovery" and question.category in [
            QuestionCategory.FAMILY, QuestionCategory.USAGE, QuestionCategory.BUDGET
        ]:
            base_value *= 1.2

        return min(base_value * category_weight, 1.0)

    async def _calculate_engagement_potential(
        self,
        question: Question,
        user_context: UserContext
    ) -> float:
        """Calculate the engagement potential of a question"""
        base_potential = question.engagement_potential

        # Adjust based on user's engagement level
        if user_context.engagement_level < self.engagement_threshold:
            # Boost engaging questions for disengaged users
            if base_potential > 0.7:
                base_potential *= 1.3

        # Reduce if similar topic recently discussed
        if question.category.name.lower() in user_context.recent_topics[-2:]:
            base_potential *= 0.6

        # Adjust complexity based on engagement
        if user_context.engagement_level < 0.5 and question.complexity == QuestionComplexity.ADVANCED:
            base_potential *= 0.7
        elif user_context.engagement_level > 0.8 and question.complexity == QuestionComplexity.BASIC:
            base_potential *= 0.8

        # Check fatigue indicators
        fatigue_keywords = ["boring", "irrelevant", "already answered"]
        if any(keyword in " ".join(user_context.fatigue_indicators).lower() for keyword in fatigue_keywords):
            base_potential *= 0.5

        return min(base_potential, 1.0)

    async def _calculate_timing_score(
        self,
        question: Question,
        user_context: UserContext
    ) -> float:
        """Calculate the timing appropriateness of a question"""
        # Base timing score
        timing_score = 0.8

        # Check if too many questions asked recently
        if user_context.last_question_time:
            time_since_last = datetime.now() - user_context.last_question_time
            if time_since_last.total_seconds() < 30:  # Less than 30 seconds
                timing_score *= 0.5
            elif time_since_last.total_seconds() > 300:  # More than 5 minutes
                timing_score *= 1.2

        # Adjust based on questions in current session
        questions_this_session = len(user_context.questions_asked)
        if questions_this_session >= self.max_questions_per_session:
            timing_score *= 0.3
        elif questions_this_session > self.max_questions_per_session * 0.7:
            timing_score *= 0.6

        # Boost follow-up questions
        if any(fq in user_context.questions_asked[-3:] for fq in question.follow_up_questions):
            timing_score *= 1.3

        # Stage-appropriate timing
        stage_boosts = {
            "greeting": [QuestionCategory.FAMILY, QuestionCategory.USAGE],
            "discovery": [QuestionCategory.BUDGET, QuestionCategory.PERFORMANCE],
            "refinement": [QuestionCategory.FEATURE, QuestionCategory.SAFETY],
            "closing": []  # No questions in closing
        }

        if question.category in stage_boosts.get(user_context.conversation_stage, []):
            timing_score *= 1.2

        return min(timing_score, 1.0)

    async def _calculate_novelty_score(
        self,
        question: Question,
        user_context: UserContext
    ) -> float:
        """Calculate the novelty of a question for this user"""
        # Base novelty
        novelty = 0.7

        # Check historical question patterns
        try:
            question_history = await self.temporal_memory.retrieve_by_user(
                user_context.user_id,
                pattern="question_asked",
                limit=20
            )

            # Reduce novelty if similar questions asked before
            for memory in question_history:
                if memory.content.get("category") == question.category.value:
                    days_ago = (datetime.now() - memory.timestamp).days
                    if days_ago < 7:
                        novelty *= 0.4
                    elif days_ago < 30:
                        novelty *= 0.7

        except Exception as e:
            logger.warning(f"Failed to check question history: {e}")

        # Boost novel categories
        if not any(
            q.category == question.category
            for q_id in user_context.questions_asked
            if q_id in self.questions
        ):
            novelty *= 1.2

        return min(novelty, 1.0)

    async def _generate_selection_reasons(
        self,
        question: Question,
        info_score: float,
        engagement_score: float,
        timing_score: float,
        novelty_score: float
    ) -> List[str]:
        """Generate human-readable reasons for question selection"""
        reasons = []

        if info_score > 0.7:
            reasons.append(f"High information value in {question.category.value}")

        if engagement_score > 0.7:
            reasons.append("High engagement potential")
        elif engagement_score < 0.4:
            reasons.append("User may be losing engagement")

        if timing_score > 0.8:
            reasons.append("Optimal timing")
        elif timing_score < 0.5:
            reasons.append("May not be the best time")

        if novelty_score > 0.8:
            reasons.append("Covers new topic area")
        elif novelty_score < 0.5:
            reasons.append("Similar to recent discussions")

        if not reasons:
            reasons.append("Balanced choice for current context")

        return reasons

    async def _apply_flow_constraints(
        self,
        scored_questions: List[QuestionScore],
        user_context: UserContext
    ) -> List[QuestionScore]:
        """Apply conversation flow constraints to question selection"""
        constrained_questions = []

        for score in scored_questions:
            question = self.questions[score.question_id]

            # Skip if would break conversation flow
            if user_context.conversation_stage == "closing":
                continue

            # Ensure variety in question categories
            if constrained_questions:
                last_categories = [
                    self.questions[s.question_id].category
                    for s in constrained_questions[-2:]
                ]
                if question.category in last_categories:
                    score.total_score *= 0.7

            # Priority for unanswered prerequisites
            for prereq in question.prerequisites:
                if prereq not in user_context.questions_asked:
                    score.total_score *= 1.1

            constrained_questions.append(score)

        # Re-sort after adjustments
        constrained_questions.sort(key=lambda x: x.total_score, reverse=True)

        return constrained_questions

    async def record_question_asked(
        self,
        user_id: str,
        question: Question,
        response: str,
        engagement_indicators: Dict[str, Any]
    ) -> None:
        """Record that a question was asked and the response"""
        try:
            # Store in temporal memory
            memory_fragment = MemoryFragment(
                content={
                    "question_id": question.id,
                    "question_text": question.text,
                    "response": response,
                    "category": question.category.value,
                    "complexity": question.complexity.value,
                    "engagement_indicators": engagement_indicators,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type=MemoryType.EPISODIC,
                importance=question.information_value,
                timestamp=datetime.now(),
                decay_factor=0.1,
                associated_preferences=[]
            )

            await self.temporal_memory.store_memory(user_id, memory_fragment)

            # Calculate and store effectiveness
            effectiveness = await self._calculate_question_effectiveness(
                question, response, engagement_indicators
            )

            if effectiveness > 0.7:
                # Store effective question pattern
                await self.temporal_memory.store_memory(
                    user_id,
                    MemoryFragment(
                        content={
                            "pattern": "question_effectiveness",
                            "question_template": question.text,
                            "category": question.category.value,
                            "complexity": question.complexity.value,
                            "effectiveness_score": effectiveness,
                            "engagement_score": engagement_indicators.get("engagement_score", 0.5),
                            "response_type": self._classify_response_type(response),
                            "tags": question.tags
                        },
                        memory_type=MemoryType.SEMANTIC,
                        importance=effectiveness,
                        timestamp=datetime.now(),
                        decay_factor=0.05,
                        associated_preferences=[]
                    )
                )

            logger.info(f"Recorded question {question.id} with effectiveness: {effectiveness:.2f}")

        except Exception as e:
            logger.error(f"Failed to record question asked: {e}")

    async def _calculate_question_effectiveness(
        self,
        question: Question,
        response: str,
        engagement_indicators: Dict[str, Any]
    ) -> float:
        """Calculate how effective a question was"""
        effectiveness = 0.0

        # Response quality (length and detail)
        if len(response.split()) > 10:
            effectiveness += 0.3
        elif len(response.split()) > 5:
            effectiveness += 0.2

        # Engagement indicators
        engagement_score = engagement_indicators.get("engagement_score", 0.5)
        effectiveness += engagement_score * 0.3

        # Information extraction
        if self._contains_preference_information(response):
            effectiveness += 0.2

        # Follow-up readiness
        if "?" in response or "what about" in response.lower():
            effectiveness += 0.1

        # Emotional indicators
        if any(word in response.lower() for word in ["good", "great", "helpful", "interesting"]):
            effectiveness += 0.1

        return min(effectiveness, 1.0)

    def _contains_preference_information(self, response: str) -> bool:
        """Check if response contains preference information"""
        preference_keywords = [
            "prefer", "like", "want", "need", "important", "priority",
            "must have", "deal breaker", "essential", "looking for"
        ]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in preference_keywords)

    def _classify_response_type(self, response: str) -> str:
        """Classify the type of response given"""
        response_lower = response.lower().strip()

        if response_lower in ["yes", "no", "maybe", "not sure"]:
            return "simple_choice"
        elif any(char.isdigit() for char in response):
            return "quantitative"
        elif len(response.split()) < 5:
            return "short_answer"
        elif "?" in response:
            return "question"
        else:
            return "detailed_answer"