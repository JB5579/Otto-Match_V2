"""
Family Need Questioning for Otto.AI
Specialized questioning module for family-oriented vehicle needs
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

# Import for runtime use (QuestionCategory enum is used in runtime code)
from src.intelligence.questioning_strategy import QuestionCategory, QuestionComplexity

# Configure logging
logger = logging.getLogger(__name__)


class FamilyComposition(Enum):
    """Types of family compositions"""
    INDIVIDUAL = "individual"
    COUPLE = "couple"
    SMALL_FAMILY = "small_family"  # 3-4 people
    LARGE_FAMILY = "large_family"  # 5+ people
    EXTENDED_FAMILY = "extended_family"  # Regularly transports additional family


class AgeGroup(Enum):
    """Age categories for family members"""
    INFANT = "infant"  # 0-2 years
    TODDLER = "toddler"  # 3-5 years
    CHILD = "child"  # 6-12 years
    TEENAGER = "teenager"  # 13-17 years
    ADULT = "adult"  # 18+ years


class UsagePattern(Enum):
    """Common family usage patterns"""
    DAILY_COMMUTE = "daily_commute"
    SCHOOL_RUNS = "school_runs"
    WEEKEND_ACTIVITIES = "weekend_activities"
    ROAD_TRIPS = "road_trips"
    SPORTS_TRANSPORT = "sports_transport"
    PET_TRANSPORT = "pet_transport"
    CARGO_NEEDS = "cargo_needs"


@dataclass
class FamilyProfile:
    """Profile of the family's needs and composition"""
    composition: FamilyComposition
    member_count: int
    age_groups: List[AgeGroup]
    special_needs: List[str]  # car seats, wheelchair access, etc.
    primary_activities: List[UsagePattern]
    lifestyle_factors: List[str]  # outdoor activities, urban living, etc.


@dataclass
class VehicleRequirement:
    """Specific vehicle requirement based on family needs"""
    requirement_type: str  # seating, cargo, safety, etc.
    minimum_spec: str
    preferred_spec: str
    priority: float  # 0.0 to 1.0
    flexibility: bool  # Can this be compromised?


class FamilyNeedQuestioning:
    """Specialized questioning for family vehicle needs"""

    def __init__(
        self,
        groq_client: Any  # GroqClient from groq_client
    ):
        self.groq_client = groq_client
        self.initialized = False

        # Family-focused question templates
        self.question_templates: Dict[str, Any] = {}

        # Family profiles cache
        self.family_profiles: Dict[str, FamilyProfile] = {}

    async def initialize(self) -> bool:
        """
        Initialize family questioning module.

        Returns:
            True if initialization successful
        """
        try:
            self._initialize_question_templates()
            self.initialized = True
            logger.info("FamilyNeedQuestioning initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize FamilyNeedQuestioning: {e}")
            return False

    def _initialize_question_templates(self) -> Dict[str, Any]:
        """
        Initialize family-focused question templates.

        Returns:
            Dictionary of question templates
        """
        # Import Question here for runtime use
        from src.intelligence.questioning_strategy import Question

        self.question_templates = {
            "family_size_initial": Question(
                id="family_size_initial",
                text="How many people will typically be traveling in this vehicle?",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.BASIC,
                information_value=0.9,
                engagement_potential=0.7,
                follow_up_questions=["family_ages", "family_growth"]
            ),
            "family_ages": Question(
                id="family_ages",
                text="What are the ages of the passengers? This helps me recommend the right safety features.",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.85,
                engagement_potential=0.6,
                follow_up_questions=[]
            ),
            "family_growth": Question(
                id="family_growth",
                text="Do you expect your family to grow in the next few years? This affects long-term vehicle needs.",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.7,
                engagement_potential=0.6,
                follow_up_questions=[]
            ),
            "safety_priorities": Question(
                id="safety_priorities",
                text="What safety features are most important for your family? (e.g., advanced airbags, blind spot monitoring, driver assist features)",
                category=QuestionCategory.SAFETY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.85,
                engagement_potential=0.7,
                follow_up_questions=[]
            ),
            "cargo_needs": Question(
                id="cargo_needs",
                text="What kind of cargo do you typically carry? (stroller, sports equipment, groceries, luggage, etc.)",
                category=QuestionCategory.FEATURE,
                complexity=QuestionComplexity.BASIC,
                information_value=0.75,
                engagement_potential=0.6,
                follow_up_questions=[]
            ),
            "car_seat_compatibility": Question(
                id="car_seat_compatibility",
                text="Do you need car seat compatibility? If so, how many car seats do you typically use?",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.BASIC,
                information_value=0.8,
                engagement_potential=0.7,
                follow_up_questions=[]
            ),
            "activity_based_needs": Question(
                id="activity_based_needs",
                text="What family activities do you do regularly that might affect your vehicle choice? (weekend trips, sports practice, camping, etc.)",
                category=QuestionCategory.LIFESTYLE,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.8,
                engagement_potential=0.7,
                follow_up_questions=[]
            )
        }

        return self.question_templates

    async def analyze_family_composition(
        self,
        user_responses: Dict[str, Any]
    ) -> Optional[FamilyProfile]:
        """
        Analyze user responses to determine family composition.

        Args:
            user_responses: User's answers to family-related questions

        Returns:
            FamilyProfile if enough information gathered, None otherwise
        """
        try:
            # Determine family size
            member_count = user_responses.get("family_size", 0)
            if not member_count:
                return None

            # Determine composition type
            if member_count == 1:
                composition = FamilyComposition.INDIVIDUAL
            elif member_count == 2:
                composition = FamilyComposition.COUPLE
            elif 3 <= member_count <= 4:
                composition = FamilyComposition.SMALL_FAMILY
            elif member_count >= 5:
                composition = FamilyComposition.LARGE_FAMILY
            else:
                composition = FamilyComposition.INDIVIDUAL

            # Extract age groups
            age_groups = []
            ages_response = user_responses.get("family_ages", "")
            if "infant" in ages_response.lower() or "baby" in ages_response.lower():
                age_groups.append(AgeGroup.INFANT)
            if "toddler" in ages_response.lower() or "3" in ages_response or "4" in ages_response or "5" in ages_response:
                age_groups.append(AgeGroup.TODDLER)
            if "child" in ages_response.lower() or "kid" in ages_response.lower():
                age_groups.append(AgeGroup.CHILD)
            if "teen" in ages_response.lower() or "teenager" in ages_response.lower():
                age_groups.append(AgeGroup.TEENAGER)

            # Default to adults if no specific ages mentioned
            if not age_groups:
                age_groups = [AgeGroup.ADULT] * member_count

            # Determine special needs
            special_needs = []
            if user_responses.get("car_seat_compatibility"):
                special_needs.append("car_seats")
            if user_responses.get("wheelchair_access"):
                special_needs.append("wheelchair_access")

            # Determine usage patterns
            activities = user_responses.get("activity_based_needs", "")
            primary_activities = []
            if "commute" in activities.lower():
                primary_activities.append(UsagePattern.DAILY_COMMUTE)
            if "school" in activities.lower():
                primary_activities.append(UsagePattern.SCHOOL_RUNS)
            if "trip" in activities.lower() or "travel" in activities.lower():
                primary_activities.append(UsagePattern.ROAD_TRIPS)
            if "sport" in activities.lower():
                primary_activities.append(UsagePattern.SPORTS_TRANSPORT)

            # Lifestyle factors
            lifestyle_factors = []
            if "camping" in activities.lower() or "outdoor" in activities.lower():
                lifestyle_factors.append("outdoor_enthusiast")
            if "city" in activities.lower() or "urban" in activities.lower():
                lifestyle_factors.append("urban_living")

            profile = FamilyProfile(
                composition=composition,
                member_count=member_count,
                age_groups=age_groups,
                special_needs=special_needs,
                primary_activities=primary_activities,
                lifestyle_factors=lifestyle_factors
            )

            logger.info(f"Analyzed family profile: {composition.value} with {member_count} members")

            return profile

        except Exception as e:
            logger.error(f"Error analyzing family composition: {e}")
            return None

    async def generate_vehicle_requirements(
        self,
        profile: FamilyProfile
    ) -> List[VehicleRequirement]:
        """
        Generate vehicle requirements based on family profile.

        Args:
            profile: Family profile to analyze

        Returns:
            List of vehicle requirements
        """
        requirements = []

        # Seating requirements
        requirements.append(VehicleRequirement(
            requirement_type="seating",
            minimum_spec=f"At least {profile.member_count} seats",
            preferred_spec=f"{profile.member_count + 1}+ seats for extra comfort",
            priority=1.0,
            flexibility=False
        ))

        # Safety requirements based on age groups
        if AgeGroup.INFANT in profile.age_groups or AgeGroup.TODDLER in profile.age_groups:
            requirements.append(VehicleRequirement(
                requirement_type="safety",
                minimum_spec="LATCH system for car seats",
                preferred_spec="Multiple LATCH points + rear seat reminder",
                priority=0.95,
                flexibility=False
            ))

        # Cargo requirements
        if UsagePattern.SCHOOL_RUNS in profile.primary_activities:
            requirements.append(VehicleRequirement(
                requirement_type="cargo",
                minimum_spec="Backseat cargo space for backpacks",
                preferred_spec="Separate trunk compartment + foldable seats",
                priority=0.8,
                flexibility=True
            ))

        if UsagePattern.ROAD_TRIPS in profile.primary_activities:
            requirements.append(VehicleRequirement(
                requirement_type="cargo",
                minimum_spec="Medium trunk space (15+ cubic feet)",
                preferred_spec="Large cargo space with roof rack option",
                priority=0.85,
                flexibility=True
            ))

        # Entertainment for long drives
        if profile.member_count >= 4:
            requirements.append(VehicleRequirement(
                requirement_type="entertainment",
                minimum_spec="Basic audio system",
                preferred_spec="Rear entertainment system + multiple USB ports",
                priority=0.6,
                flexibility=True
            ))

        # Climate control based on lifestyle
        if "outdoor_enthusiast" in profile.lifestyle_factors:
            requirements.append(VehicleRequirement(
                requirement_type="climate",
                minimum_spec="Standard A/C",
                preferred_spec="Tri-zone climate control + ventilated seats",
                priority=0.7,
                flexibility=True
            ))

        logger.info(f"Generated {len(requirements)} vehicle requirements for family profile")

        return requirements

    async def get_next_question(
        self,
        user_id: str,
        conversation_context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get the next appropriate family question based on context.

        Args:
            user_id: User identifier
            conversation_context: Current conversation state

        Returns:
            Next Question object or None
        """
        # Import Question for runtime use
        from src.intelligence.questioning_strategy import Question

        # Check if we already have family size info
        if not conversation_context.get("family_size"):
            return self.question_templates.get("family_size_initial")

        # Check if we need ages
        if not conversation_context.get("family_ages"):
            return self.question_templates.get("family_ages")

        # Check if we need safety priorities
        if not conversation_context.get("safety_priorities"):
            return self.question_templates.get("safety_priorities")

        # Check if we need cargo info
        if not conversation_context.get("cargo_needs"):
            return self.question_templates.get("cargo_needs")

        # No more family-specific questions needed
        return None

    async def score_vehicles_for_family(
        self,
        vehicles: List[Dict[str, Any]],
        profile: FamilyProfile
    ) -> Dict[str, float]:
        """
        Score vehicles based on family suitability.

        Args:
            vehicles: List of vehicles to score
            profile: Family profile to score against

        Returns:
            Dictionary mapping vehicle_id to family suitability score
        """
        scores = {}

        for vehicle in vehicles:
            vehicle_id = vehicle.get("id", "")
            score = 0.5  # Base score

            # Seating capacity score
            seating_capacity = vehicle.get("seating_capacity", 5)
            if seating_capacity >= profile.member_count:
                score += 0.2
            elif seating_capacity >= profile.member_count - 1:
                score += 0.1
            else:
                score -= 0.3

            # Safety features score
            safety_features = vehicle.get("safety_features", [])
            if AgeGroup.INFANT in profile.age_groups or AgeGroup.TODDLER in profile.age_groups:
                if any("latch" in f.lower() for f in safety_features):
                    score += 0.15
                if any("airbag" in f.lower() for f in safety_features):
                    score += 0.1

            # Cargo space score
            cargo_volume = vehicle.get("cargo_volume", 0)  # cubic feet
            if profile.member_count >= 4:
                if cargo_volume >= 20:
                    score += 0.15
                elif cargo_volume >= 15:
                    score += 0.1

            # Family-friendly features
            if "entertainment" in vehicle:
                score += 0.05

            # Normalize score
            scores[vehicle_id] = max(0.0, min(1.0, score))

        return scores


# Singleton instance
_family_need_questioning_instance: Optional[FamilyNeedQuestioning] = None


def get_family_need_questioning(groq_client: Any) -> FamilyNeedQuestioning:
    """
    Get or create the FamilyNeedQuestioning singleton instance.

    Args:
        groq_client: Groq client for AI processing

    Returns:
        FamilyNeedQuestioning instance
    """
    global _family_need_questioning_instance

    if _family_need_questioning_instance is None:
        _family_need_questioning_instance = FamilyNeedQuestioning(groq_client=groq_client)

    return _family_need_questioning_instance
