"""
Family Need Questioning for Otto.AI
Specialized questioning module for family-oriented vehicle needs
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Type hints to avoid circular imports
GroqClient = Any
Question = Any
QuestionCategory = Any
QuestionComplexity = Any


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
        groq_client: GroqClient
    ):
        self.groq_client = groq_client
        self.initialized = False

        # Family-focused question templates
        self.question_templates = self._initialize_question_templates()

        # Vehicle type recommendations by family profile
        self.vehicle_recommendations = self._initialize_vehicle_recommendations()

        # Safety feature priorities by age group
        self.safety_priorities = self._initialize_safety_priorities()

    async def initialize(self) -> bool:
        """Initialize the family need questioning module"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            self.initialized = True
            logger.info("Family need questioning initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize family need questioning: {e}")
            return False

    def _initialize_question_templates(self) -> Dict[str, Question]:
        """Initialize family-specific question templates"""
        return {
            "family_size_initial": Question(
                id="family_size_initial",
                text="How many people will typically be traveling in this vehicle?",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.BASIC,
                information_value=0.9,
                engagement_potential=0.7,
                follow_up_questions=["family_ages", "family_growth"],
                prerequisites=[],
                tags=["family", "size", "capacity"],
                example_answers=["Just myself", "Two people", "Family of four", "Five or more"]
            ),

            "family_ages": Question(
                id="family_ages",
                text="What are the ages of the passengers? This helps me recommend the right safety features.",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.85,
                engagement_potential=0.6,
                follow_up_questions=["car_seats", "teenager_needs", "safety_priorities"],
                prerequisites=["family_size_initial"],
                tags=["family", "ages", "safety", "children"],
                example_answers=["Adults only", "Two adults, one toddler", "Kids aged 8 and 12", "Mix of all ages"]
            ),

            "family_growth": Question(
                id="family_growth",
                text="Do you expect your family to grow in the next few years? This affects long-term vehicle needs.",
                category=QuestionCategory.FAMILY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.7,
                engagement_potential=0.6,
                follow_up_questions=["flexible_seating", "future_needs"],
                prerequisites=["family_size_initial"],
                tags=["family", "planning", "future", "flexibility"],
                example_answers=["Planning for children", "Kids will be teenagers soon", "Family is complete", "Grandkids visit often"]
            ),

            "car_seats": Question(
                id="car_seats",
                text="Do you need car seats? How many and what types? This impacts seating configuration and ease of access.",
                category=QuestionCategory.SAFETY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.8,
                engagement_potential=0.5,
                follow_up_questions=["seat_access", "latch_system", "third_row_access"],
                prerequisites=["family_ages"],
                tags=["safety", "car_seats", "children", "access"],
                example_answers=["2 car seats", "Booster seats only", "No car seats needed", "Special needs car seat"]
            ),

            "daily_activities": Question(
                id="daily_activities",
                text="What does a typical week look like for your family? School runs, activities, commuting patterns?",
                category=QuestionCategory.USAGE,
                complexity=QuestionComplexity.OPEN,
                information_value=0.8,
                engagement_potential=0.7,
                follow_up_questions=["weekend_activities", "cargo_needs", "fuel_priority"],
                prerequisites=[],
                tags=["usage", "activities", "routine", "lifestyle"],
                example_answers=["School and work commute", "Sports practices daily", "Mostly local driving", "Lots of activities"]
            ),

            "weekend_activities": Question(
                id="weekend_activities",
                text="What does your family do on weekends? This helps with space and feature recommendations.",
                category=QuestionCategory.LIFESTYLE,
                complexity=QuestionComplexity.OPEN,
                information_value=0.7,
                engagement_potential=0.8,
                follow_up_questions=["cargo_space", "all_weather", "entertainment"],
                prerequisites=["daily_activities"],
                tags=["lifestyle", "weekend", "recreation", "activities"],
                example_answers=["Road trips", "Sports tournaments", "Home improvement projects", "Beach trips"]
            ),

            "cargo_needs": Question(
                id="cargo_needs",
                text="Besides passengers, what do you regularly transport? Sports equipment, groceries, pets, etc.",
                category=QuestionCategory.FEATURE,
                complexity=QuestionComplexity.OPEN,
                information_value=0.75,
                engagement_potential=0.6,
                follow_up_questions=["cargo_frequency", "cargo_size", "roof_rack"],
                prerequisites=["daily_activities"],
                tags=["cargo", "storage", "utility", "gear"],
                example_answers=["Sports equipment", "Groceries for 6", "Large dog", "Band instruments"]
            ),

            "teenager_needs": Question(
                id="teenager_needs",
                text="Do you have teenagers? They have different space and technology needs than younger kids.",
                category=QuestionCategory.LIFESTYLE,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.6,
                engagement_potential=0.7,
                follow_up_questions=["teen_space", "tech_features", "driver_training"],
                prerequisites=["family_ages"],
                tags=["teenager", "space", "technology", "family"],
                example_answers=["One teenager", "Two teens driving soon", "No teens yet", "Young adult children"]
            ),

            "pet_transport": Question(
                id="pet_transport",
                text="Do you have pets that travel with you? Size and number matter for vehicle selection.",
                category=QuestionCategory.LIFESTYLE,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.6,
                engagement_potential=0.7,
                follow_up_questions=["pet_size", "pet_containment", "clean_air"],
                prerequisites=[],
                tags=["pets", "animals", "transport", "family"],
                example_answers=["Large dog", "Multiple cats", "Small dog", "No pets"]
            ),

            "accessibility_needs": Question(
                id="accessibility_needs",
                text="Does anyone in your family have mobility considerations or special accessibility needs?",
                category=QuestionCategory.SAFETY,
                complexity=QuestionComplexity.SENSITIVE,
                information_value=0.8,
                engagement_potential=0.4,
                follow_up_questions=["entry_height", "seat_height", "controls"],
                prerequisites=[],
                tags=["accessibility", "mobility", "special_needs", "safety"],
                example_answers=["Elderly parents", "Wheelchair user", "Difficulty with stairs", "No special needs"]
            ),

            "entertainment_needs": Question(
                id="entertainment_needs",
                text="What entertainment features are important for family trips? Screens, Wi-Fi, charging ports?",
                category=QuestionCategory.TECHNOLOGY,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.5,
                engagement_potential=0.7,
                follow_up_questions=["screen_count", "device_charging", "connectivity"],
                prerequisites=["weekend_activities"],
                tags=["entertainment", "technology", "family", "travel"],
                example_answers=["Rear entertainment", "Multiple charging ports", "Wi-Fi hotspot", "Basic radio only"]
            ),

            "budget_flexibility": Question(
                id="budget_flexibility",
                text="How does having a family affect your vehicle budget? Are you looking for value or premium features?",
                category=QuestionCategory.BUDGET,
                complexity=QuestionComplexity.INTERMEDIATE,
                information_value=0.8,
                engagement_potential=0.5,
                follow_up_questions=["total_cost_focus", "feature_priority", "long_term_value"],
                prerequisites=["family_size_initial"],
                tags=["budget", "value", "family", "financial"],
                example_answers=["Need maximum value", "Willing to pay for safety", "Budget conscious", "Premium preferred"]
            )
        }

    def _initialize_vehicle_recommendations(self) -> Dict[FamilyComposition, List[str]]:
        """Initialize vehicle type recommendations by family composition"""
        return {
            FamilyComposition.INDIVIDUAL: [
                "Compact Car", "Sedan", "Coupe", "Compact SUV"
            ],
            FamilyComposition.COUPLE: [
                "Sedan", "Compact SUV", "Mid-size SUV", "Sports Car", "Luxury Vehicle"
            ],
            FamilyComposition.SMALL_FAMILY: [
                "Compact SUV", "Mid-size SUV", "Minivan", "Wagon", "Crossover"
            ],
            FamilyComposition.LARGE_FAMILY: [
                "Minivan", "3-Row SUV", "Full-size SUV", "Large Wagon"
            ],
            FamilyComposition.EXTENDED_FAMILY: [
                "Full-size SUV", "Extended-length Vehicle", "Van", "3-Row SUV with third row"
            ]
        }

    def _initialize_safety_priorities(self) -> Dict[AgeGroup, List[str]]:
        """Initialize safety feature priorities by age group"""
        return {
            AgeGroup.INFANT: [
                "LATCH system", "Rear-facing car seat compatibility",
                "Air bag deactivation", "Climate control for rear"
            ],
            AgeGroup.TODDLER: [
                "LATCH system", "Forward-facing seat anchors",
                "Child safety locks", "Rear climate control"
            ],
            AgeGroup.CHILD: [
                "Booster seat compatibility", "Rear entertainment",
                "Window safety locks", "Rear USB ports"
            ],
            AgeGroup.TEENAGER: [
                "Driver assistance features", "Blind spot monitoring",
                "Teen driver settings", "Connectivity features"
            ],
            AgeGroup.ADULT: [
                "Adaptive cruise control", "Lane keeping assist",
                "Premium safety features", "Comfort features"
            ]
        }

    async def build_family_profile(
        self,
        responses: Dict[str, str]
    ) -> Optional[FamilyProfile]:
        """
        Build a family profile from questionnaire responses
        """
        if not self.initialized:
            return None

        try:
            # Determine family composition
            family_size_response = responses.get("family_size_initial", "1")
            member_count = self._parse_member_count(family_size_response)

            if member_count == 1:
                composition = FamilyComposition.INDIVIDUAL
            elif member_count == 2:
                composition = FamilyComposition.COUPLE
            elif member_count <= 4:
                composition = FamilyComposition.SMALL_FAMILY
            elif member_count <= 6:
                composition = FamilyComposition.LARGE_FAMILY
            else:
                composition = FamilyComposition.EXTENDED_FAMILY

            # Parse age groups
            age_groups = self._parse_age_groups(responses.get("family_ages", ""))

            # Identify special needs
            special_needs = []
            if responses.get("car_seats"):
                special_needs.append("car_seats")
            if responses.get("accessibility_needs"):
                special_needs.append("accessibility")
            if responses.get("pet_transport"):
                special_needs.append("pet_transport")

            # Determine primary activities
            primary_activities = self._parse_usage_patterns(
                responses.get("daily_activities", ""),
                responses.get("weekend_activities", "")
            )

            # Identify lifestyle factors
            lifestyle_factors = self._parse_lifestyle_factors(responses)

            return FamilyProfile(
                composition=composition,
                member_count=member_count,
                age_groups=age_groups,
                special_needs=special_needs,
                primary_activities=primary_activities,
                lifestyle_factors=lifestyle_factors
            )

        except Exception as e:
            logger.error(f"Failed to build family profile: {e}")
            return None

    async def generate_vehicle_requirements(
        self,
        family_profile: FamilyProfile
    ) -> List[VehicleRequirement]:
        """
        Generate vehicle requirements based on family profile
        """
        requirements = []

        try:
            # Seating requirements
            if family_profile.member_count >= 5:
                requirements.append(VehicleRequirement(
                    requirement_type="seating",
                    minimum_spec=f"Minimum {family_profile.member_count} seats",
                    preferred_spec="3rd row seating preferred",
                    priority=0.9,
                    flexibility=False
                ))

            # Cargo requirements
            if UsagePattern.CARGO_NEEDS in family_profile.primary_activities:
                requirements.append(VehicleRequirement(
                    requirement_type="cargo",
                    minimum_spec="20+ cubic feet with seats up",
                    preferred_spec="Flexible cargo configuration",
                    priority=0.8,
                    flexibility=True
                ))

            # Safety requirements by age group
            safety_features = set()
            for age_group in family_profile.age_groups:
                safety_features.update(self.safety_priorities.get(age_group, []))

            if safety_features:
                requirements.append(VehicleRequirement(
                    requirement_type="safety",
                    minimum_spec=", ".join(list(safety_features)[:3]),
                    preferred_spec="Full safety suite recommended",
                    priority=0.95,
                    flexibility=False
                ))

            # Accessibility requirements
            if "accessibility" in family_profile.special_needs:
                requirements.append(VehicleRequirement(
                    requirement_type="accessibility",
                    minimum_spec="Easy entry/exit",
                    preferred_spec="Low step-in height, wide door openings",
                    priority=0.9,
                    flexibility=False
                ))

            # Pet transport requirements
            if "pet_transport" in family_profile.special_needs:
                requirements.append(VehicleRequirement(
                    requirement_type="pet_friendly",
                    minimum_spec="Durable interior, easy to clean",
                    preferred_spec="Pet barriers, climate control for cargo",
                    priority=0.6,
                    flexibility=True
                ))

            # Sort by priority
            requirements.sort(key=lambda x: x.priority, reverse=True)

            return requirements

        except Exception as e:
            logger.error(f"Failed to generate vehicle requirements: {e}")
            return []

    def _parse_member_count(self, response: str) -> int:
        """Parse family size from response"""
        import re

        # Look for numbers
        numbers = re.findall(r'\d+', response)
        if numbers:
            return max(int(n) for n in numbers)

        # Check for keywords
        response_lower = response.lower()
        if any(word in response_lower for word in ["family", "us", "everyone"]):
            if "four" in response_lower or "4" in response_lower:
                return 4
            elif "five" in response_lower or "5" in response_lower:
                return 5
            elif "six" in response_lower or "6" in response_lower:
                return 6
            elif "seven" in response_lower or "7" in response_lower:
                return 7

        # Default assumptions
        if "couple" in response_lower or "two" in response_lower:
            return 2
        elif "just me" in response_lower or "only me" in response_lower:
            return 1
        else:
            return 3  # Default assumption

    def _parse_age_groups(self, response: str) -> List[AgeGroup]:
        """Parse age groups from response"""
        age_groups = []
        response_lower = response.lower()

        if any(word in response_lower for word in ["infant", "baby", "newborn"]):
            age_groups.append(AgeGroup.INFANT)
        if any(word in response_lower for word in ["toddler", "young child", "preschool"]):
            age_groups.append(AgeGroup.TODDLER)
        if any(word in response_lower for word in ["child", "kid", "grade school"]):
            age_groups.append(AgeGroup.CHILD)
        if any(word in response_lower for word in ["teenager", "teen", "high school"]):
            age_groups.append(AgeGroup.TEENAGER)

        # Always include adults
        if not age_groups or "adult" in response_lower:
            age_groups.append(AgeGroup.ADULT)

        return age_groups

    def _parse_usage_patterns(
        self,
        daily_response: str,
        weekend_response: str
    ) -> List[UsagePattern]:
        """Parse usage patterns from responses"""
        patterns = []
        combined_text = f"{daily_response} {weekend_response}".lower()

        if any(word in combined_text for word in ["commute", "work", "school"]):
            patterns.append(UsagePattern.DAILY_COMMUTE)
        if any(word in combined_text for word in ["school runs", "drop off", "pick up"]):
            patterns.append(UsagePattern.SCHOOL_RUNS)
        if any(word in combined_text for word in ["weekend", "saturday", "sunday", "activities"]):
            patterns.append(UsagePattern.WEEKEND_ACTIVITIES)
        if any(word in combined_text for word in ["road trip", "travel", "vacation"]):
            patterns.append(UsagePattern.ROAD_TRIPS)
        if any(word in combined_text for word in ["sports", "practice", "games", "equipment"]):
            patterns.append(UsagePattern.SPORTS_TRANSPORT)
        if any(word in combined_text for word in ["dog", "cat", "pet"]):
            patterns.append(UsagePattern.PET_TRANSPORT)
        if any(word in combined_text for word in ["cargo", "haul", "carry", "transport"]):
            patterns.append(UsagePattern.CARGO_NEEDS)

        return patterns

    def _parse_lifestyle_factors(self, responses: Dict[str, str]) -> List[str]:
        """Parse lifestyle factors from responses"""
        factors = []
        combined_text = " ".join(responses.values()).lower()

        if any(word in combined_text for word in ["outdoor", "camping", "hiking", "adventure"]):
            factors.append("outdoor_enthusiast")
        if any(word in combined_text for word in ["city", "urban", "parking"]):
            factors.append("urban_living")
        if any(word in combined_text for word in ["suburban", "neighborhood"]):
            factors.append("suburban_family")
        if any(word in combined_text for word in ["rural", "country"]):
            factors.append("rural_living")
        if any(word in combined_text for word in ["eco", "green", "environment"]):
            factors.append("environmentally_conscious")
        if any(word in combined_text for word in ["tech", "technology", "connected"]):
            factors.append("tech_savvy")

        return factors

    async def get_follow_up_questions(
        self,
        last_question_id: str,
        response: str,
        family_profile: Optional[FamilyProfile] = None
    ) -> List[Question]:
        """
        Get appropriate follow-up questions based on response
        """
        if not self.initialized:
            return []

        try:
            follow_ups = []

            # Get the question that was just asked
            if last_question_id not in self.question_templates:
                return []

            last_question = self.question_templates[last_question_id]

            # Check each potential follow-up
            for follow_id in last_question.follow_up_questions:
                if follow_id in self.question_templates:
                    follow_question = self.question_templates[follow_id]

                    # Check if follow-up is relevant based on response
                    if await self._is_follow_up_relevant(follow_question, response, family_profile):
                        follow_ups.append(follow_question)

            return follow_ups

        except Exception as e:
            logger.error(f"Failed to get follow-up questions: {e}")
            return []

    async def _is_follow_up_relevant(
        self,
        follow_question: Question,
        response: str,
        family_profile: Optional[FamilyProfile]
    ) -> bool:
        """Check if a follow-up question is relevant based on the response"""
        response_lower = response.lower()

        # Check response content
        if "no" in response_lower or "don't" in response_lower:
            # Skip follow-ups if response is negative
            return False

        # Check family profile if available
        if family_profile:
            # Skip car seat questions if no children
            if follow_question.id == "car_seats" and not any(
                age in [AgeGroup.INFANT, AgeGroup.TODDLER, AgeGroup.CHILD]
                for age in family_profile.age_groups
            ):
                return False

            # Skip teenager questions if no teens
            if follow_question.id == "teenager_needs" and AgeGroup.TEENAGER not in family_profile.age_groups:
                return False

        # Check response triggers
        triggers = {
            "family_ages": ["child", "kid", "children", "age", "old"],
            "car_seats": ["seat", "car seat", "safety"],
            "teenager_needs": ["teen", "teenager", "driving", "license"],
            "cargo_needs": ["cargo", "haul", "carry", "transport", "equipment"],
            "pet_transport": ["pet", "dog", "cat", "animal"],
            "entertainment_needs": ["entertainment", "movie", "screen", "tablet"]
        }

        if follow_question.id in triggers:
            keywords = triggers[follow_question.id]
            if any(keyword in response_lower for keyword in keywords):
                return True

        return True  # Default to showing the follow-up

    async def generate_recommendation_summary(
        self,
        family_profile: FamilyProfile,
        requirements: List[VehicleRequirement]
    ) -> str:
        """
        Generate a summary of recommendations based on family profile and requirements
        """
        try:
            summary = f"Based on your family profile, I recommend "

            # Vehicle type recommendations
            vehicle_types = self.vehicle_recommendations.get(family_profile.composition, [])
            if vehicle_types:
                summary += f"looking at {', '.join(vehicle_types[:3])}"

            # Key requirements
            high_priority = [r for r in requirements if r.priority > 0.8]
            if high_priority:
                summary += ". Your key requirements include "
                req_descriptions = [r.minimum_spec for r in high_priority[:3]]
                summary += ", ".join(req_descriptions)

            # Special considerations
            if family_profile.special_needs:
                summary += ". I've noted your special needs for "
                summary += ", ".join(family_profile.special_needs)

            return summary + "."

        except Exception as e:
            logger.error(f"Failed to generate recommendation summary: {e}")
            return "I have some vehicle recommendations for your family needs."