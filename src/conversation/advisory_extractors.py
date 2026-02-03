"""
Advisory Entity Extractors for Otto AI - Phase 1
Enhanced NLU capabilities for lifestyle context, priority rankings, and decision signals

Based on NLU Gap Analysis and Conversation Architecture Analysis
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

# Avoid circular imports - we define intent types locally for pattern matching
# The actual IntentType enum is in intent_models.py

logger = logging.getLogger(__name__)


# Local enum for advisory intents to avoid circular import
class AdvisoryIntentType(Enum):
    """Advisory-specific intent types (mirrors IntentType additions)"""
    UPGRADE_INTEREST = "upgrade_interest"
    LIFESTYLE_DISCLOSURE = "lifestyle_disclosure"
    INFRASTRUCTURE_DISCLOSURE = "infrastructure"
    PRIORITY_EXPRESSION = "priority_expression"
    ALTERNATIVE_INQUIRY = "alternative_inquiry"
    DECISION_COMMITMENT = "decision_commitment"
    NEXT_STEPS_INQUIRY = "next_steps_inquiry"
    TRADEOFF_QUESTION = "tradeoff_question"
    CONFIRMATION_SEEKING = "confirmation_seeking"
    CONCERN_EXPRESSION = "concern_expression"


# ============================================================================
# Data Models for Enhanced Extraction
# ============================================================================

@dataclass
class CurrentVehicleEntity:
    """Represents user's current/trade-in vehicle"""
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    ownership_type: str = "current"  # 'current', 'previous', 'considering'
    sentiment: str = "neutral"  # 'satisfied', 'neutral', 'unsatisfied'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class CommutePattern:
    """Represents user's commute information"""
    distance_miles: Optional[float] = None
    trip_type: str = "one_way"  # 'one_way', 'round_trip'
    road_type: Optional[str] = None  # 'highway', 'city', 'mixed'
    frequency: str = "daily"  # 'daily', 'weekly', 'occasional'
    time_minutes: Optional[int] = None
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class WorkPattern:
    """Represents user's work arrangement"""
    wfh_days_per_week: Optional[int] = None
    work_arrangement: str = "office"  # 'office', 'remote', 'hybrid'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class RoadTripPattern:
    """Represents user's road trip habits"""
    frequency_per_year: Optional[int] = None
    typical_distance_miles: Optional[int] = None
    distance_qualifier: str = "approximate"  # 'exact', 'approximate'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class ChargingInfrastructure:
    """Represents user's charging/parking infrastructure"""
    parking_type: Optional[str] = None  # 'garage', 'driveway', 'street', 'apartment'
    can_install_charger: Optional[bool] = None
    has_charger: bool = False
    ownership: str = "unknown"  # 'owned', 'rented', 'unknown'
    workplace_charging: Optional[bool] = None
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class RangeRequirement:
    """Represents user's range needs for EVs"""
    minimum_range: Optional[int] = None
    ideal_range: Optional[int] = None
    concern_level: str = "medium"  # 'low', 'medium', 'high'
    primary_use_case: Optional[str] = None  # 'commute', 'road_trips', 'mixed'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class BudgetFlexibility:
    """Represents user's budget with flexibility indicators"""
    preferred_max: Optional[float] = None
    hard_max: Optional[float] = None
    comfortable_payment: Optional[float] = None  # monthly payment
    flexibility: str = "moderate"  # 'strict', 'moderate', 'flexible'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class PriorityRanking:
    """Represents a priority comparison between attributes"""
    higher_priority: str = ""
    lower_priority: str = ""
    expression_type: str = "comparison"  # 'comparison', 'absolute', 'negation'
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class DecisionSignal:
    """Represents decision readiness indicators"""
    signal_type: str = ""  # 'commitment', 'hesitation', 'confirmation_seeking', 'next_steps'
    confidence_level: float = 0.0  # 0.0 to 1.0
    trigger_phrase: str = ""
    raw_text: str = ""


@dataclass
class LifestyleProfile:
    """Aggregated lifestyle context from all extractors"""
    current_vehicle: Optional[CurrentVehicleEntity] = None
    commute: Optional[CommutePattern] = None
    work_pattern: Optional[WorkPattern] = None
    annual_mileage: Optional[Tuple[int, int]] = None  # (low, high)
    road_trips: Optional[RoadTripPattern] = None
    charging: Optional[ChargingInfrastructure] = None
    range_needs: Optional[RangeRequirement] = None
    budget: Optional[BudgetFlexibility] = None
    priorities: List[PriorityRanking] = field(default_factory=list)
    decision_signals: List[DecisionSignal] = field(default_factory=list)


# ============================================================================
# Lifestyle Entity Extractor
# ============================================================================

class LifestyleEntityExtractor:
    """Extracts lifestyle-related entities from conversation"""

    def __init__(self):
        self.stats = {
            'extractions': 0,
            'current_vehicle': 0,
            'commute': 0,
            'work_pattern': 0,
            'road_trips': 0,
            'charging': 0,
            'annual_mileage': 0
        }

        # Brand list for current vehicle detection
        self.brands = [
            'toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'tesla', 'bmw',
            'mercedes', 'audi', 'hyundai', 'kia', 'nissan', 'mazda', 'volkswagen',
            'subaru', 'jeep', 'ram', 'gmc', 'buick', 'cadillac', 'lexus', 'infiniti',
            'acura', 'volvo', 'jaguar', 'land rover', 'porsche', 'genesis', 'mini',
            'mitsubishi', 'chrysler', 'dodge', 'lincoln', 'alfa romeo', 'fiat',
            'lucid', 'rivian', 'polestar'
        ]

    async def extract_all(self, message: str) -> Dict[str, Any]:
        """Extract all lifestyle entities from message"""
        self.stats['extractions'] += 1

        results = {}

        # Extract each entity type
        current_vehicle = self._extract_current_vehicle(message)
        if current_vehicle and current_vehicle.confidence > 0.5:
            results['current_vehicle'] = current_vehicle
            self.stats['current_vehicle'] += 1

        commute = self._extract_commute_pattern(message)
        if commute and commute.confidence > 0.5:
            results['commute'] = commute
            self.stats['commute'] += 1

        work = self._extract_work_pattern(message)
        if work and work.confidence > 0.5:
            results['work_pattern'] = work
            self.stats['work_pattern'] += 1

        road_trips = self._extract_road_trip_pattern(message)
        if road_trips and road_trips.confidence > 0.5:
            results['road_trips'] = road_trips
            self.stats['road_trips'] += 1

        charging = self._extract_charging_infrastructure(message)
        if charging and charging.confidence > 0.5:
            results['charging'] = charging
            self.stats['charging'] += 1

        mileage = self._extract_annual_mileage(message)
        if mileage:
            results['annual_mileage'] = mileage
            self.stats['annual_mileage'] += 1

        return results

    def _extract_current_vehicle(self, message: str) -> Optional[CurrentVehicleEntity]:
        """Extract current/trade-in vehicle information"""
        message_lower = message.lower()

        # Patterns for current vehicle mentions
        patterns = [
            # "my 2018 Honda Accord" / "I drive a 2020 Tesla Model 3"
            r"(?:my|i\s+(?:have|drive|own|currently\s+have)(?:\s+a)?)\s+(?:a\s+)?(\d{4})?\s*([a-z\s]+?)(?:\s+([a-z0-9\s\-]+))?(?:\.|,|$|\s+(?:and|but|which|that))",
            # "current car is a 2018 Honda"
            r"(?:current|existing)\s+(?:car|vehicle|suv|truck)\s+(?:is\s+)?(?:a\s+)?(\d{4})?\s*([a-z\s]+?)(?:\s+([a-z0-9\s\-]+))?",
            # "trading in my 2018 Honda"
            r"(?:trade|trading)\s+(?:in\s+)?(?:my\s+)?(\d{4})?\s*([a-z\s]+?)(?:\s+([a-z0-9\s\-]+))?",
            # "It's a 2018 Honda Accord"
            r"(?:it'?s|it\s+is)\s+(?:a\s+)?(\d{4})?\s*([a-z\s]+?)(?:\s+([a-z0-9\s\-]+))?"
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                year = int(groups[0]) if groups[0] else None

                # Extract make and model
                make = None
                model = None

                if groups[1]:
                    # Check if any brand is in the captured text
                    potential_make = groups[1].strip()
                    for brand in self.brands:
                        if brand in potential_make.lower():
                            make = brand.title()
                            break

                if groups[2]:
                    model = groups[2].strip().title()

                # Determine sentiment
                sentiment = "neutral"
                if any(word in message_lower for word in ['love', 'great', 'reliable', 'good']):
                    sentiment = "satisfied"
                elif any(word in message_lower for word in ['hate', 'problem', 'issue', 'tired', 'old']):
                    sentiment = "unsatisfied"

                # Determine ownership type
                ownership = "current"
                if "trade" in message_lower or "trading" in message_lower:
                    ownership = "trading"
                elif any(word in message_lower for word in ['had', 'previous', 'used to']):
                    ownership = "previous"

                if make or year:  # Only return if we found something meaningful
                    return CurrentVehicleEntity(
                        year=year,
                        make=make,
                        model=model,
                        ownership_type=ownership,
                        sentiment=sentiment,
                        raw_text=match.group(0),
                        confidence=0.8 if (make and year) else 0.6
                    )

        return None

    def _extract_commute_pattern(self, message: str) -> Optional[CommutePattern]:
        """Extract commute information"""
        message_lower = message.lower()

        commute = CommutePattern()
        found = False

        # Distance patterns
        distance_patterns = [
            # "45 miles round trip"
            (r'(\d+(?:\.\d+)?)\s*(?:mile|mi)s?\s*(?:round\s*trip|roundtrip)', 'round_trip'),
            # "45 mile commute" / "commute is 45 miles"
            (r'(?:commute(?:\s+is)?|drive)\s*(?:about\s+)?(\d+(?:\.\d+)?)\s*(?:mile|mi)s?', 'one_way'),
            # "45 miles each way"
            (r'(\d+(?:\.\d+)?)\s*(?:mile|mi)s?\s*each\s*way', 'one_way'),
            # "about 45 miles to work"
            (r'(?:about\s+)?(\d+(?:\.\d+)?)\s*(?:mile|mi)s?\s*(?:to\s+work|to\s+the\s+office)', 'one_way'),
        ]

        for pattern, trip_type in distance_patterns:
            match = re.search(pattern, message_lower)
            if match:
                commute.distance_miles = float(match.group(1))
                commute.trip_type = trip_type
                commute.raw_text = match.group(0)
                found = True
                break

        # Time patterns
        time_patterns = [
            r'(\d+)\s*(?:minute|min)s?\s*(?:commute|drive)',
            r'commute(?:\s+is)?\s*(?:about\s+)?(\d+)\s*(?:minute|min)s?',
        ]

        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                commute.time_minutes = int(match.group(1))
                found = True
                break

        # Road type
        if 'highway' in message_lower or 'freeway' in message_lower or 'interstate' in message_lower:
            commute.road_type = 'highway'
        elif 'city' in message_lower or 'urban' in message_lower or 'traffic' in message_lower:
            commute.road_type = 'city'
        elif 'mix' in message_lower or 'both' in message_lower:
            commute.road_type = 'mixed'

        if found:
            commute.confidence = 0.8 if commute.distance_miles else 0.6
            return commute

        return None

    def _extract_work_pattern(self, message: str) -> Optional[WorkPattern]:
        """Extract work arrangement information"""
        message_lower = message.lower()

        work = WorkPattern()
        found = False

        # WFH patterns
        wfh_patterns = [
            # "work from home 2 days a week"
            r'work\s*(?:from\s*home|remotely)\s*(?:about\s+)?(\d+)\s*days?\s*(?:a\s*week|per\s*week|weekly)?',
            # "2 days remote"
            r'(\d+)\s*days?\s*(?:remote|from\s*home|wfh)',
            # "work from home a couple days"
            r'work\s*from\s*home\s*(?:a\s*)?(couple|few)\s*days?',
        ]

        for pattern in wfh_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if match.group(1) in ['couple', 'few']:
                    work.wfh_days_per_week = 2 if match.group(1) == 'couple' else 3
                else:
                    work.wfh_days_per_week = int(match.group(1))
                work.work_arrangement = 'hybrid'
                work.raw_text = match.group(0)
                found = True
                break

        # Full remote detection
        if any(phrase in message_lower for phrase in ['fully remote', 'work remotely', 'work from home full']):
            work.work_arrangement = 'remote'
            work.wfh_days_per_week = 5
            found = True

        # Office detection
        if any(phrase in message_lower for phrase in ['go to the office', 'office job', 'in the office']):
            if work.wfh_days_per_week is None:
                work.work_arrangement = 'office'
                work.wfh_days_per_week = 0
            found = True

        if found:
            work.confidence = 0.8
            return work

        return None

    def _extract_road_trip_pattern(self, message: str) -> Optional[RoadTripPattern]:
        """Extract road trip habits"""
        message_lower = message.lower()

        # Frequency patterns
        patterns = [
            # "road trips 3-4 times a year" or "road trips maybe 3-4 times a year"
            r'road\s*trips?\s*(?:maybe\s+)?(?:about\s+)?(\d+)(?:\s*[-to]+\s*(\d+))?\s*times?\s*(?:a\s*year|annually|per\s*year)',
            # "take road trips maybe 3-4 times a year"
            r'(?:take\s+)?road\s*trips?\s*(?:maybe\s+)?(\d+)(?:\s*[-to]+\s*(\d+))?\s*times?\s*(?:a\s*year|annually)',
            # "take road trips a few times a year"
            r'(?:take\s+)?road\s*trips?\s*(?:a\s*)?(few|couple|several)\s*times?\s*(?:a\s*year|annually)',
            # "go on road trips occasionally"
            r'(?:go\s+on\s+)?road\s*trips?\s*(occasionally|sometimes|rarely|often|frequently)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                road_trip = RoadTripPattern(raw_text=match.group(0))

                if match.group(1) in ['few', 'couple', 'several', 'occasionally', 'sometimes', 'rarely', 'often', 'frequently']:
                    frequency_map = {
                        'few': 3, 'couple': 2, 'several': 4,
                        'occasionally': 2, 'sometimes': 3, 'rarely': 1,
                        'often': 6, 'frequently': 8
                    }
                    road_trip.frequency_per_year = frequency_map.get(match.group(1), 3)
                else:
                    road_trip.frequency_per_year = int(match.group(1))
                    if match.group(2):
                        # Take average of range
                        road_trip.frequency_per_year = (int(match.group(1)) + int(match.group(2))) // 2

                road_trip.confidence = 0.8

                # Try to extract distance
                distance_match = re.search(r'(?:few\s+)?(\d+)(?:\s*[-to]+\s*(\d+))?\s*(?:hundred\s+)?(?:mile|mi)s?', message_lower)
                if distance_match:
                    if 'hundred' in message_lower:
                        road_trip.typical_distance_miles = int(distance_match.group(1)) * 100
                    else:
                        road_trip.typical_distance_miles = int(distance_match.group(1))
                    road_trip.distance_qualifier = 'approximate'

                return road_trip

        return None

    def _extract_charging_infrastructure(self, message: str) -> Optional[ChargingInfrastructure]:
        """Extract charging/parking infrastructure"""
        message_lower = message.lower()

        charging = ChargingInfrastructure()
        found = False

        # Parking type detection
        if 'garage' in message_lower:
            charging.parking_type = 'garage'
            found = True
        elif 'driveway' in message_lower:
            charging.parking_type = 'driveway'
            found = True
        elif 'street parking' in message_lower or 'park on the street' in message_lower:
            charging.parking_type = 'street'
            found = True
        elif 'apartment' in message_lower or 'condo' in message_lower:
            charging.parking_type = 'apartment'
            found = True

        # Charger installation capability
        install_patterns = [
            r'(?:can|could|able\s+to)\s*install\s*(?:a\s+)?(?:home\s+)?charger',
            r'install(?:ing)?\s+(?:a\s+)?(?:home\s+)?charger',
            r'charger\s+(?:can\s+be\s+)?installed',
        ]

        for pattern in install_patterns:
            if re.search(pattern, message_lower):
                charging.can_install_charger = True
                found = True
                break

        # Already has charger
        if any(phrase in message_lower for phrase in ['have a charger', 'already have charging', 'charging at home']):
            charging.has_charger = True
            charging.can_install_charger = True
            found = True

        # Cannot install
        if any(phrase in message_lower for phrase in ['can\'t install', 'cannot install', 'no way to charge']):
            charging.can_install_charger = False
            found = True

        # Ownership
        if 'own' in message_lower or 'my house' in message_lower or 'my home' in message_lower:
            charging.ownership = 'owned'
        elif 'rent' in message_lower or 'landlord' in message_lower:
            charging.ownership = 'rented'

        # Workplace charging
        if any(phrase in message_lower for phrase in ['charging at work', 'work has chargers', 'charge at the office']):
            charging.workplace_charging = True
            found = True

        if found:
            charging.confidence = 0.8
            return charging

        return None

    def _extract_annual_mileage(self, message: str) -> Optional[Tuple[int, int]]:
        """Extract annual mileage estimate"""
        message_lower = message.lower()

        patterns = [
            # "12,000-15,000 miles a year"
            r'(\d{1,3}(?:,\d{3})?)\s*(?:[-to]+)\s*(\d{1,3}(?:,\d{3})?)\s*(?:mile|mi)s?\s*(?:a\s*year|annually|per\s*year)',
            # "about 15,000 miles annually"
            r'(?:about|around|roughly)\s*(\d{1,3}(?:,\d{3})?)\s*(?:mile|mi)s?\s*(?:a\s*year|annually|per\s*year)',
            # "drive 15,000 miles a year"
            r'drive\s*(?:about\s+)?(\d{1,3}(?:,\d{3})?)\s*(?:mile|mi)s?\s*(?:a\s*year|annually|per\s*year)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    low = int(groups[0].replace(',', ''))
                    high = int(groups[1].replace(',', ''))
                    return (low, high)
                else:
                    value = int(groups[0].replace(',', ''))
                    # Add 10% variance for single values
                    return (int(value * 0.9), int(value * 1.1))

        return None

    def get_stats(self) -> Dict[str, int]:
        """Return extraction statistics"""
        return self.stats.copy()


# ============================================================================
# Priority Ranking Extractor
# ============================================================================

class PriorityRankingExtractor:
    """Extracts priority rankings and tradeoff expressions"""

    def __init__(self):
        self.stats = {
            'extractions': 0,
            'priority_rankings': 0,
            'budget_flexibility': 0
        }

        # Priority attributes that can be ranked
        self.priority_attributes = [
            'performance', 'luxury', 'comfort', 'range', 'reliability', 'safety',
            'fuel economy', 'mpg', 'efficiency', 'technology', 'tech', 'features',
            'price', 'value', 'style', 'design', 'space', 'size', 'practicality',
            'speed', 'acceleration', 'handling', 'power', 'brand', 'resale',
            'maintenance', 'cost', 'interior', 'cargo', 'towing'
        ]

    async def extract_all(self, message: str) -> Dict[str, Any]:
        """Extract all priority-related entities"""
        self.stats['extractions'] += 1

        results = {}

        # Extract priority rankings
        rankings = self._extract_priority_rankings(message)
        if rankings:
            results['priority_rankings'] = rankings
            self.stats['priority_rankings'] += len(rankings)

        # Extract budget flexibility
        budget = self._extract_budget_flexibility(message)
        if budget and budget.confidence > 0.5:
            results['budget_flexibility'] = budget
            self.stats['budget_flexibility'] += 1

        return results

    def _extract_priority_rankings(self, message: str) -> List[PriorityRanking]:
        """Extract priority comparison statements"""
        message_lower = message.lower()
        rankings = []

        # Comparison patterns
        comparison_patterns = [
            # "X is more important than Y"
            r'(\w+(?:\s+\w+)?)\s+is\s+more\s+important\s+(?:to\s+me\s+)?than\s+(\w+(?:\s+\w+)?)',
            # "X over Y"
            r'(\w+(?:\s+\w+)?)\s+over\s+(\w+(?:\s+\w+)?)',
            # "prioritize X over Y"
            r'prioritize\s+(\w+(?:\s+\w+)?)\s+over\s+(\w+(?:\s+\w+)?)',
            # "X matters more than Y"
            r'(\w+(?:\s+\w+)?)\s+matters?\s+more\s+than\s+(\w+(?:\s+\w+)?)',
            # "care more about X than Y"
            r'care\s+more\s+about\s+(\w+(?:\s+\w+)?)\s+than\s+(\w+(?:\s+\w+)?)',
            # "X > Y" (literal)
            r'(\w+(?:\s+\w+)?)\s*>\s*(\w+(?:\s+\w+)?)',
        ]

        for pattern in comparison_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                higher = match.group(1).strip()
                lower = match.group(2).strip()

                # Validate both are recognized priorities
                higher_valid = any(attr in higher for attr in self.priority_attributes)
                lower_valid = any(attr in lower for attr in self.priority_attributes)

                if higher_valid or lower_valid:
                    rankings.append(PriorityRanking(
                        higher_priority=higher,
                        lower_priority=lower,
                        expression_type='comparison',
                        raw_text=match.group(0),
                        confidence=0.9 if (higher_valid and lower_valid) else 0.7
                    ))

        # Absolute priority patterns
        absolute_patterns = [
            # "X is my top priority"
            r'(\w+(?:\s+\w+)?)\s+is\s+(?:my\s+)?(?:top|main|primary|biggest)\s+priority',
            # "X is most important"
            r'(\w+(?:\s+\w+)?)\s+is\s+(?:the\s+)?most\s+important',
            # "top priority is X"
            r'(?:top|main|primary)\s+priority\s+is\s+(\w+(?:\s+\w+)?)',
        ]

        for pattern in absolute_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                priority = match.group(1).strip()
                if any(attr in priority for attr in self.priority_attributes):
                    rankings.append(PriorityRanking(
                        higher_priority=priority,
                        lower_priority='other',
                        expression_type='absolute',
                        raw_text=match.group(0),
                        confidence=0.85
                    ))

        # Negation patterns
        negation_patterns = [
            # "don't care about X"
            r"don'?t\s+(?:really\s+)?care\s+(?:about\s+)?(\w+(?:\s+\w+)?)",
            # "X doesn't matter"
            r"(\w+(?:\s+\w+)?)\s+doesn'?t\s+(?:really\s+)?matter",
            # "not worried about X"
            r"not\s+(?:really\s+)?worried\s+about\s+(\w+(?:\s+\w+)?)",
        ]

        for pattern in negation_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                priority = match.group(1).strip()
                if any(attr in priority for attr in self.priority_attributes):
                    rankings.append(PriorityRanking(
                        higher_priority='other',
                        lower_priority=priority,
                        expression_type='negation',
                        raw_text=match.group(0),
                        confidence=0.8
                    ))

        return rankings

    def _extract_budget_flexibility(self, message: str) -> Optional[BudgetFlexibility]:
        """Extract budget with flexibility indicators"""
        message_lower = message.lower()

        budget = BudgetFlexibility()
        found = False

        # Budget with flexibility patterns
        patterns = [
            # "prefer under $100k but could stretch" (various forms)
            r"prefer(?:\s+to\s+stay)?\s+under\s+\$?(\d{1,3}(?:,\d{3})?k?)\s+(?:if\s+possible\s*,?\s*)?(?:but\s+)?(?:i\s+)?(?:could|can)\s+stretch",
            # "prefer to stay under $100k if possible, but I could stretch a bit"
            r"prefer\s+to\s+stay\s+under\s+\$?(\d{1,3}(?:,\d{3})?k?)",
            # "budget is around $50k, flexible"
            r'budget\s+(?:is\s+)?(?:around|about)\s+\$?(\d{1,3}(?:,\d{3})?k?)\s*,?\s*(?:pretty\s+)?flexible',
            # "$50k max but flexible"
            r'\$?(\d{1,3}(?:,\d{3})?k?)\s+max(?:imum)?\s+(?:but\s+)?flexible',
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount_str = match.group(1).replace(',', '')
                if 'k' in amount_str.lower():
                    budget.preferred_max = float(amount_str.lower().replace('k', '')) * 1000
                else:
                    budget.preferred_max = float(amount_str)

                # Determine flexibility from context
                if any(word in message_lower for word in ['stretch', 'flexible', 'wiggle room']):
                    budget.flexibility = 'flexible'
                elif 'if possible' in message_lower:
                    budget.flexibility = 'moderate'
                else:
                    budget.flexibility = 'moderate'

                budget.raw_text = match.group(0)
                found = True
                break

        # Strict budget patterns
        strict_patterns = [
            # "can't go over $50k"
            r"can'?t\s+go\s+over\s+\$?(\d{1,3}(?:,\d{3})?k?)",
            # "$50k is my absolute max"
            r'\$?(\d{1,3}(?:,\d{3})?k?)\s+is\s+(?:my\s+)?absolute\s+max',
            # "hard limit of $50k"
            r'hard\s+limit\s+(?:of\s+)?\$?(\d{1,3}(?:,\d{3})?k?)',
        ]

        for pattern in strict_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount_str = match.group(1).replace(',', '')
                if 'k' in amount_str:
                    amount = float(amount_str.replace('k', '')) * 1000
                else:
                    amount = float(amount_str)
                budget.hard_max = amount
                budget.preferred_max = amount
                budget.flexibility = 'strict'
                budget.raw_text = match.group(0)
                found = True
                break

        # Monthly payment patterns
        payment_patterns = [
            # "$500/month" or "$500 a month"
            r'\$?(\d{3,4})\s*(?:/|per|a)\s*month',
            # "monthly payment of $500"
            r'monthly\s+payment\s+(?:of\s+)?\$?(\d{3,4})',
        ]

        for pattern in payment_patterns:
            match = re.search(pattern, message_lower)
            if match:
                budget.comfortable_payment = float(match.group(1))
                found = True
                break

        if found:
            budget.confidence = 0.85
            return budget

        return None

    def get_stats(self) -> Dict[str, int]:
        """Return extraction statistics"""
        return self.stats.copy()


# ============================================================================
# Decision Signal Detector
# ============================================================================

class DecisionSignalDetector:
    """Detects decision readiness and commitment signals"""

    def __init__(self):
        self.stats = {
            'detections': 0,
            'commitment_signals': 0,
            'hesitation_signals': 0,
            'next_steps_signals': 0
        }

        # Commitment signal patterns
        self.commitment_patterns = [
            (r'sounds?\s+like\s+(?:the\s+)?winner', 0.9),
            (r'this\s+is\s+(?:the\s+)?(?:one|it)', 0.9),
            (r"i'?m\s+(?:really\s+)?(?:sold|convinced)", 0.85),
            (r"let'?s\s+(?:do\s+)?(?:it|this)", 0.85),
            (r"i'?m\s+ready\s+to", 0.8),
            (r'(?:feels?|sounds?)\s+(?:right|perfect)', 0.8),
            (r"that'?s\s+(?:the\s+)?(?:one|it)", 0.85),
            (r"i\s+(?:think\s+)?(?:i'?ve\s+)?(?:made|found)\s+(?:my|a)\s+(?:decision|choice)", 0.9),
            (r"i'?m\s+(?:going\s+)?(?:with|for)\s+(?:the\s+)?", 0.8),
        ]

        # Hesitation patterns
        self.hesitation_patterns = [
            (r"i'?m\s+(?:still\s+)?(?:not\s+sure|unsure|uncertain)", 0.7),
            (r'(?:need|want)\s+(?:more\s+)?time\s+to\s+think', 0.8),
            (r"(?:don'?t|do\s+not)\s+want\s+to\s+(?:rush|hurry)", 0.7),
            (r'(?:let\s+me|i\s+need\s+to)\s+(?:think|consider|sleep\s+on)', 0.75),
            (r"i'?m\s+(?:a\s+bit\s+)?(?:hesitant|worried|concerned)", 0.7),
        ]

        # Confirmation seeking patterns
        self.confirmation_patterns = [
            (r"(?:am\s+i|are\s+there)\s+(?:missing|forgetting)\s+(?:anything|something)", 0.85),
            (r'(?:is\s+there|are\s+there)\s+(?:any(?:thing)?|something)\s+(?:else\s+)?(?:i\s+should\s+)?(?:know|consider)', 0.85),
            (r'(?:what|anything)\s+(?:am\s+i|should\s+i\s+be)\s+(?:missing|overlooking)', 0.8),
            (r'(?:any|are\s+there\s+any)\s+(?:catches|downsides|issues)', 0.8),
            (r"(?:anything|something)\s+i'?m\s+(?:not\s+)?(?:thinking|seeing)", 0.75),
        ]

        # Next steps patterns
        self.next_steps_patterns = [
            (r'what\s+(?:happens|is)\s+next', 0.9),
            (r'(?:how\s+)?(?:do\s+)?(?:i|we)\s+(?:proceed|move\s+forward)', 0.85),
            (r'(?:next|what\s+are\s+the)\s+steps?', 0.85),
            (r'(?:how\s+)?(?:can|do)\s+(?:i|we)\s+(?:get|start)', 0.8),
            (r'(?:when|how\s+soon)\s+can\s+(?:i|we)', 0.75),
        ]

    async def detect_all(self, message: str) -> Dict[str, Any]:
        """Detect all decision signals in message"""
        self.stats['detections'] += 1

        results = {
            'signals': [],
            'overall_readiness': 0.0
        }

        message_lower = message.lower()

        # Check commitment signals
        for pattern, confidence in self.commitment_patterns:
            match = re.search(pattern, message_lower)
            if match:
                results['signals'].append(DecisionSignal(
                    signal_type='commitment',
                    confidence_level=confidence,
                    trigger_phrase=match.group(0),
                    raw_text=message
                ))
                self.stats['commitment_signals'] += 1

        # Check hesitation signals
        for pattern, confidence in self.hesitation_patterns:
            match = re.search(pattern, message_lower)
            if match:
                results['signals'].append(DecisionSignal(
                    signal_type='hesitation',
                    confidence_level=confidence,
                    trigger_phrase=match.group(0),
                    raw_text=message
                ))
                self.stats['hesitation_signals'] += 1

        # Check confirmation seeking
        for pattern, confidence in self.confirmation_patterns:
            match = re.search(pattern, message_lower)
            if match:
                results['signals'].append(DecisionSignal(
                    signal_type='confirmation_seeking',
                    confidence_level=confidence,
                    trigger_phrase=match.group(0),
                    raw_text=message
                ))

        # Check next steps
        for pattern, confidence in self.next_steps_patterns:
            match = re.search(pattern, message_lower)
            if match:
                results['signals'].append(DecisionSignal(
                    signal_type='next_steps',
                    confidence_level=confidence,
                    trigger_phrase=match.group(0),
                    raw_text=message
                ))
                self.stats['next_steps_signals'] += 1

        # Calculate overall readiness
        if results['signals']:
            commitment_signals = [s for s in results['signals'] if s.signal_type == 'commitment']
            hesitation_signals = [s for s in results['signals'] if s.signal_type == 'hesitation']
            next_steps_signals = [s for s in results['signals'] if s.signal_type == 'next_steps']

            if commitment_signals:
                readiness = max(s.confidence_level for s in commitment_signals)
                if next_steps_signals:
                    readiness = min(1.0, readiness + 0.1)  # Boost if also asking next steps
            elif hesitation_signals:
                readiness = 1.0 - max(s.confidence_level for s in hesitation_signals)
            elif next_steps_signals:
                readiness = 0.7  # Asking next steps implies interest
            else:
                readiness = 0.5  # Neutral

            results['overall_readiness'] = readiness

        return results

    def get_stats(self) -> Dict[str, int]:
        """Return detection statistics"""
        return self.stats.copy()


# ============================================================================
# Advisory Intent Classifier
# ============================================================================

class AdvisoryIntentClassifier:
    """Classifies advisory-specific intents for mode detection"""

    def __init__(self):
        self.stats = {
            'classifications': 0,
            'advisory_intents': {}
        }

        # Intent patterns
        self.intent_patterns = {
            AdvisoryIntentType.UPGRADE_INTEREST: [
                r'(?:thinking\s+(?:about|of)\s+)?upgrading',
                r'(?:want|looking)\s+to\s+(?:upgrade|replace|trade)',
                r'(?:time\s+(?:to|for)\s+)?(?:a\s+)?new\s+(?:car|vehicle)',
                r'(?:my\s+)?(?:current|old)\s+(?:car|vehicle)',
            ],
            AdvisoryIntentType.LIFESTYLE_DISCLOSURE: [
                r'(?:my\s+)?(?:daily\s+)?commute\s+is',
                r'(?:i\s+)?(?:drive|travel)\s+(?:about\s+)?\d+\s+(?:mile|minute)',
                r'(?:i\s+)?work\s+(?:from\s+home|remotely)',
                r'(?:we\s+)?(?:have|got)\s+(?:a\s+)?(?:family|kids?|children)',
            ],
            AdvisoryIntentType.INFRASTRUCTURE_DISCLOSURE: [
                r'(?:i\s+)?have\s+(?:a\s+)?garage',
                r'(?:can|could)\s+install\s+(?:a\s+)?charger',
                r'(?:park|parking)\s+(?:on\s+the\s+)?street',
                r'(?:apartment|condo)\s+parking',
            ],
            AdvisoryIntentType.PRIORITY_EXPRESSION: [
                r'(?:\w+)\s+is\s+more\s+important',
                r'prioritize\s+\w+',
                r'(?:top|main|biggest)\s+priority',
                r'\w+\s+over\s+\w+',
            ],
            AdvisoryIntentType.ALTERNATIVE_INQUIRY: [
                r'(?:am\s+i|are\s+there)\s+missing',
                r'(?:any)?(?:thing|one)\s+else\s+(?:i\s+should\s+)?consider',
                r'other\s+options?',
                r'what\s+(?:else|about)',
            ],
            AdvisoryIntentType.DECISION_COMMITMENT: [
                r'sounds?\s+like\s+(?:the\s+)?winner',
                r'this\s+is\s+(?:the\s+)?(?:one|it)',
                r"i'?m\s+(?:sold|convinced|ready)",
                r"let'?s\s+(?:do\s+)?(?:it|this)",
            ],
            AdvisoryIntentType.NEXT_STEPS_INQUIRY: [
                r'what\s+(?:happens?|is)\s+next',
                r'(?:next|what\s+are\s+the)\s+steps?',
                r'(?:how\s+)?(?:do\s+)?(?:i|we)\s+(?:proceed|move\s+forward)',
                r'(?:when|how)\s+can\s+(?:i|we)',
            ],
            AdvisoryIntentType.TRADEOFF_QUESTION: [
                r"what'?s\s+the\s+(?:real\s+)?difference",
                r'(?:how\s+)?(?:do\s+)?they\s+(?:compare|stack\s+up)',
                r'(?:which\s+is|what)\s+(?:better|worse)\s+(?:for|about)',
                r'(?:pros?\s+and\s+)?cons?',
            ],
            AdvisoryIntentType.CONFIRMATION_SEEKING: [
                r'(?:is\s+there|are\s+there)\s+(?:any(?:thing)?)\s+(?:i\s+should\s+)?know',
                r'(?:any|are\s+there\s+any)\s+(?:catches|downsides|concerns)',
                r"anything\s+i'?m\s+(?:missing|overlooking)",
                r'should\s+i\s+(?:be\s+)?(?:worried|concerned)',
            ],
            AdvisoryIntentType.CONCERN_EXPRESSION: [
                r"(?:don'?t|do\s+not)\s+want\s+to\s+regret",
                r'(?:worried|concerned)\s+(?:about|that)',
                r"(?:what\s+if|hope)\s+(?:it|i)\s+(?:doesn'?t|don'?t)",
                r'(?:nervous|anxious|scared)\s+(?:about|that)',
            ],
        }

    async def classify(self, message: str) -> List[Tuple[AdvisoryIntentType, float]]:
        """Classify message for advisory intents"""
        self.stats['classifications'] += 1

        message_lower = message.lower()
        detected_intents = []

        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = 0.8  # Base confidence for pattern match
                    detected_intents.append((intent_type, confidence))

                    # Track stats
                    intent_name = intent_type.value
                    self.stats['advisory_intents'][intent_name] = \
                        self.stats['advisory_intents'].get(intent_name, 0) + 1

                    break  # Only count each intent once

        # Sort by confidence
        detected_intents.sort(key=lambda x: x[1], reverse=True)

        return detected_intents

    def get_stats(self) -> Dict[str, Any]:
        """Return classification statistics"""
        return self.stats.copy()


# ============================================================================
# Unified Advisory Extractor (combines all extractors)
# ============================================================================

class AdvisoryExtractor:
    """Unified extractor that combines all Phase 1 advisory capabilities"""

    def __init__(self):
        self.lifestyle_extractor = LifestyleEntityExtractor()
        self.priority_extractor = PriorityRankingExtractor()
        self.decision_detector = DecisionSignalDetector()
        self.intent_classifier = AdvisoryIntentClassifier()

    async def extract_all(self, message: str) -> Dict[str, Any]:
        """Extract all advisory entities and signals from message"""
        results = {}

        # Extract lifestyle entities
        lifestyle = await self.lifestyle_extractor.extract_all(message)
        if lifestyle:
            results['lifestyle'] = lifestyle

        # Extract priority rankings
        priorities = await self.priority_extractor.extract_all(message)
        if priorities:
            results['priorities'] = priorities

        # Detect decision signals
        decisions = await self.decision_detector.detect_all(message)
        if decisions['signals']:
            results['decision_signals'] = decisions

        # Classify advisory intents
        intents = await self.intent_classifier.classify(message)
        if intents:
            results['advisory_intents'] = intents

        return results

    def build_lifestyle_profile(self, extraction_history: List[Dict[str, Any]]) -> LifestyleProfile:
        """Build aggregated lifestyle profile from extraction history"""
        profile = LifestyleProfile()

        for extraction in extraction_history:
            lifestyle = extraction.get('lifestyle', {})
            priorities = extraction.get('priorities', {})
            decisions = extraction.get('decision_signals', {})

            # Update profile with latest data
            if 'current_vehicle' in lifestyle:
                profile.current_vehicle = lifestyle['current_vehicle']
            if 'commute' in lifestyle:
                profile.commute = lifestyle['commute']
            if 'work_pattern' in lifestyle:
                profile.work_pattern = lifestyle['work_pattern']
            if 'annual_mileage' in lifestyle:
                profile.annual_mileage = lifestyle['annual_mileage']
            if 'road_trips' in lifestyle:
                profile.road_trips = lifestyle['road_trips']
            if 'charging' in lifestyle:
                profile.charging = lifestyle['charging']
            if 'budget_flexibility' in priorities:
                profile.budget = priorities['budget_flexibility']
            if 'priority_rankings' in priorities:
                profile.priorities.extend(priorities['priority_rankings'])
            if 'signals' in decisions:
                profile.decision_signals.extend(decisions['signals'])

        return profile

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all extractors"""
        return {
            'lifestyle': self.lifestyle_extractor.get_stats(),
            'priority': self.priority_extractor.get_stats(),
            'decision': self.decision_detector.get_stats(),
            'intent': self.intent_classifier.get_stats()
        }
