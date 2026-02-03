"""
Intent Classification and Entity Extraction Models for Otto AI
Specialized models for vehicle domain understanding
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from src.conversation.nlu_service import Entity, UserPreference

# Configure logging
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Primary intent types for Otto AI"""
    SEARCH = "search"
    COMPARE = "compare"
    ADVICE = "advice"
    INFORMATION = "information"
    GREET = "greet"
    FAREWELL = "farewell"
    CLARIFY = "clarify"
    NAVIGATE = "navigate"
    RESERVE = "reserve"
    SCHEDULE = "schedule"

    # Phase 1: Advisory intent types (from conversation simulation analysis)
    UPGRADE_INTEREST = "upgrade_interest"          # "thinking about upgrading my current car"
    LIFESTYLE_DISCLOSURE = "lifestyle_disclosure"  # sharing driving patterns, commute info
    INFRASTRUCTURE_DISCLOSURE = "infrastructure"   # "I have a garage", charging capability
    PRIORITY_EXPRESSION = "priority_expression"    # "X is more important than Y"
    ALTERNATIVE_INQUIRY = "alternative_inquiry"    # "am I missing anything?"
    DECISION_COMMITMENT = "decision_commitment"    # "sounds like the winner", "I'm ready"
    NEXT_STEPS_INQUIRY = "next_steps_inquiry"      # "what happens next?"
    TRADEOFF_QUESTION = "tradeoff_question"        # "what's the real difference between..."
    CONFIRMATION_SEEKING = "confirmation_seeking"  # "is there anything I should know?"
    CONCERN_EXPRESSION = "concern_expression"      # "I don't want to regret this"


class EntityType(Enum):
    """Entity types for vehicle domain"""
    VEHICLE_TYPE = "vehicle_type"
    BRAND = "brand"
    MODEL = "model"
    PRICE = "price"
    BUDGET = "budget"
    FEATURE = "feature"
    YEAR = "year"
    COLOR = "color"
    FUEL_TYPE = "fuel_type"
    TRANSMISSION = "transmission"
    LOCATION = "location"
    MILEAGE = "mileage"
    CONDITION = "condition"
    FAMILY_SIZE = "family_size"
    USAGE = "usage"
    PRIORITY = "priority"

    # Phase 1: Lifestyle context entities (from NLU gap analysis)
    CURRENT_VEHICLE = "current_vehicle"              # "my 2018 Honda Accord"
    COMMUTE_PATTERN = "commute_pattern"              # "45 miles round trip on highway"
    WORK_PATTERN = "work_pattern"                    # "work from home 2 days a week"
    ANNUAL_MILEAGE = "annual_mileage"                # "12,000-15,000 miles annually"
    ROAD_TRIP_PATTERN = "road_trip_pattern"          # "road trips 3-4 times a year"
    CHARGING_INFRASTRUCTURE = "charging_infrastructure"  # "have a garage, can install charger"
    RANGE_REQUIREMENT = "range_requirement"          # "need 300+ miles per charge"
    BUDGET_FLEXIBILITY = "budget_flexibility"        # "prefer under $100k but could stretch"
    PRIORITY_RANKING = "priority_ranking"            # "performance > luxury"
    PERFORMANCE_PREFERENCE = "performance_preference"  # "sporty feel, quick acceleration"
    DECISION_READINESS = "decision_readiness"        # confidence level in decision


@dataclass
class VehicleIntent:
    """Vehicle-specific intent with extracted parameters"""
    intent_type: IntentType
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_vehicle_data: bool = False
    urgency_level: str = "normal"  # "low", "normal", "high"
    missing_info: List[str] = field(default_factory=list)


@dataclass
class VehicleEntity:
    """Vehicle domain-specific entity"""
    entity_type: EntityType
    value: Any
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    extracted_from: str = ""  # Message text where extracted
    position: Optional[Tuple[int, int]] = None  # Start and end position


class IntentClassifier:
    """Specialized intent classifier for vehicle domain"""

    def __init__(self):
        # Intent patterns with weights
        self.intent_patterns = {
            IntentType.SEARCH: {
                'keywords': ['looking for', 'search', 'find', 'show me', 'need', 'want', 'interested in'],
                'weight': 1.0,
                'contexts': ['vehicle', 'car', 'suv', 'truck', 'sedan', 'electric']
            },
            IntentType.COMPARE: {
                'keywords': ['compare', 'difference', 'versus', 'vs', 'or', 'better', 'which one'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.ADVICE: {
                'keywords': ['recommend', 'suggest', 'advice', 'what should', 'help me choose', 'which is best'],
                'weight': 1.0,
                'contexts': ['vehicle', 'car']
            },
            IntentType.INFORMATION: {
                'keywords': ['what is', 'how does', 'tell me about', 'explain', 'information', 'details'],
                'weight': 0.8,
                'contexts': []
            },
            IntentType.GREET: {
                'keywords': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'greetings'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.FAREWELL: {
                'keywords': ['bye', 'goodbye', 'see you', 'thanks', 'thank you', 'that\'s all'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.CLARIFY: {
                'keywords': ['what do you mean', 'clarify', 'explain again', 'not clear'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.NAVIGATE: {
                'keywords': ['go to', 'show page', 'navigate', 'open', 'view'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.RESERVE: {
                'keywords': ['reserve', 'book', 'hold', 'save', 'appointment'],
                'weight': 1.0,
                'contexts': []
            },
            IntentType.SCHEDULE: {
                'keywords': ['schedule', 'appointment', 'when can', 'book time', 'test drive'],
                'weight': 1.0,
                'contexts': []
            }
        }

        # Question patterns for better intent detection
        self.question_patterns = [
            r'\b(what|how|when|where|why|which|who|is|are|do|does|can|could|would)\b',
            r'\?$'
        ]

        # Urgency indicators
        self.urgency_keywords = {
            'high': ['urgent', 'asap', 'immediately', 'right away', 'need now', 'emergency'],
            'low': ['just browsing', 'no rush', 'when you have time', 'eventually', 'someday']
        }

    async def classify_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        previous_intent: Optional[IntentType] = None
    ) -> VehicleIntent:
        """
        Classify user intent with domain awareness
        """

        message_lower = message.lower()

        # Initialize scores
        intent_scores = {intent_type: 0.0 for intent_type in IntentType}

        # Score based on keyword matches
        for intent_type, config in self.intent_patterns.items():
            score = 0

            # Keyword matching
            for keyword in config['keywords']:
                if keyword in message_lower:
                    # Exact phrase match gets higher score
                    if f" {keyword} " in f" {message_lower} ":
                        score += config['weight']
                    else:
                        score += config['weight'] * 0.7

            # Context relevance
            for ctx_word in config['contexts']:
                if ctx_word in message_lower:
                    score += config['weight'] * 0.3

            intent_scores[intent_type] = score

        # Adjust scores based on message type
        if self._is_question(message):
            intent_scores[IntentType.INFORMATION] += 0.5

        # Consider conversation context
        if context:
            intent_scores = self._adjust_scores_with_context(intent_scores, context)

        # Consider previous intent for continuity
        if previous_intent:
            intent_scores[previous_intent] += 0.2

        # Get best intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_type = best_intent[0]
        confidence = min(best_intent[1] / 2.0, 1.0)  # Normalize to 0-1

        # Determine urgency
        urgency = self._determine_urgency(message_lower)

        # Check what info is missing for this intent
        missing_info = self._identify_missing_info(intent_type, message, context)

        # Determine if vehicle data is needed
        requires_data = self._requires_vehicle_data(intent_type, message)

        return VehicleIntent(
            intent_type=intent_type,
            confidence=confidence,
            parameters=self._extract_intent_parameters(intent_type, message),
            requires_vehicle_data=requires_data,
            urgency_level=urgency,
            missing_info=missing_info
        )

    def _is_question(self, message: str) -> bool:
        """Check if message is a question"""
        for pattern in self.question_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def _determine_urgency(self, message: str) -> str:
        """Determine urgency level from message"""
        for level, keywords in self.urgency_keywords.items():
            if any(keyword in message for keyword in keywords):
                return level
        return "normal"

    def _identify_missing_info(
        self,
        intent_type: IntentType,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Identify what information is missing to fulfill the intent"""

        missing = []

        if intent_type == IntentType.SEARCH:
            # Check for basic search criteria
            if not any(word in message.lower() for word in ['type', 'suv', 'sedan', 'truck', 'car']):
                missing.append('vehicle_type')

            if not any(word in message.lower() for word in ['$', 'budget', 'price', 'under', 'over']):
                missing.append('budget')

        elif intent_type == IntentType.COMPARE:
            # Need at least two items to compare
            entities = self._quick_entity_extract(message)
            if len(entities.get('brands', [])) + len(entities.get('models', [])) < 2:
                missing.append('vehicles_to_compare')

        elif intent_type == IntentType.ADVICE:
            # Need some criteria for advice
            if not any(word in message.lower() for word in ['family', 'kids', 'commute', 'budget', 'prefer']):
                missing.append('preferences')

        elif intent_type == IntentType.RESERVE or intent_type == IntentType.SCHEDULE:
            # Need contact info and specific vehicle
            if not any(word in message.lower() for word in ['phone', 'email', 'contact']):
                missing.append('contact_info')

        return missing

    def _requires_vehicle_data(self, intent_type: IntentType, message: str) -> bool:
        """Check if intent requires vehicle data lookup"""
        data_intents = {
            IntentType.SEARCH,
            IntentType.COMPARE,
            IntentType.ADVICE,
            IntentType.INFORMATION
        }
        return intent_type in data_intents

    def _extract_intent_parameters(self, intent_type: IntentType, message: str) -> Dict[str, Any]:
        """Extract parameters relevant to the intent"""
        params = {}

        if intent_type == IntentType.SEARCH:
            params.update(self._extract_search_params(message))
        elif intent_type == IntentType.COMPARE:
            params.update(self._extract_compare_params(message))
        elif intent_type == IntentType.RESERVE or intent_type == IntentType.SCHEDULE:
            params.update(self._extract_schedule_params(message))

        return params

    def _extract_search_params(self, message: str) -> Dict[str, Any]:
        """Extract search parameters"""
        params = {}

        # Budget extraction
        budget_patterns = [
            (r'under \$?([0-9,]+)', 'max_price'),
            (r'below \$?([0-9,]+)', 'max_price'),
            (r'between \$?([0-9,]+) and \$?([0-9,]+)', 'price_range'),
            (r'around \$?([0-9,]+)', 'target_price')
        ]

        for pattern, param in budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if param == 'price_range':
                    params[param] = {
                        'min': int(match.group(1).replace(',', '')),
                        'max': int(match.group(2).replace(',', ''))
                    }
                else:
                    params[param] = int(match.group(1).replace(',', ''))
                break

        # Vehicle types
        vehicle_types = ['suv', 'sedan', 'truck', 'coupe', 'convertible', 'hatchback', 'minivan', 'van']
        for vtype in vehicle_types:
            if vtype in message.lower():
                params.setdefault('vehicle_types', []).append(vtype)

        # Fuel types
        fuel_types = ['electric', 'hybrid', 'gas', 'diesel', 'plug-in']
        for ftype in fuel_types:
            if ftype in message.lower():
                params['fuel_type'] = ftype

        # Features
        features = {
            'awd': 'all-wheel drive',
            '4wd': 'four-wheel drive',
            'leather': 'leather seats',
            'sunroof': 'sunroof/moonroof',
            'navigation': 'navigation system',
            'backup': 'backup camera',
            'bluetooth': 'bluetooth connectivity'
        }

        found_features = []
        for key, feature_name in features.items():
            if key in message.lower():
                found_features.append(feature_name)

        if found_features:
            params['features'] = found_features

        return params

    def _extract_compare_params(self, message: str) -> Dict[str, Any]:
        """Extract comparison parameters"""
        params = {}

        # Extract brands/models for comparison
        brands = ['toyota', 'honda', 'ford', 'chevrolet', 'tesla', 'bmw', 'mercedes', 'audi', 'hyundai', 'kia',
                  'nissan', 'mazda', 'volkswagen', 'subaru', 'jeep', 'ram', 'gmc', 'buick', 'cadillac', 'lexus']

        mentioned = []
        for brand in brands:
            if brand in message.lower():
                mentioned.append(brand.capitalize())

        if mentioned:
            params['vehicles'] = mentioned

        # Comparison criteria
        criteria = ['price', 'safety', 'fuel', 'performance', 'reliability', 'size', 'features']
        mentioned_criteria = []
        for criterion in criteria:
            if criterion in message.lower():
                mentioned_criteria.append(criterion)

        if mentioned_criteria:
            params['criteria'] = mentioned_criteria

        return params

    def _extract_schedule_params(self, message: str) -> Dict[str, Any]:
        """Extract scheduling parameters"""
        params = {}

        # Time expressions
        time_patterns = [
            (r'tomorrow', 'tomorrow'),
            (r'today', 'today'),
            (r'next week', 'next_week'),
            (r'morning', 'morning'),
            (r'afternoon', 'afternoon'),
            (r'evening', 'evening')
        ]

        for pattern, value in time_patterns:
            if pattern in message.lower():
                params['preferred_time'] = value
                break

        # Activity type
        if 'test drive' in message.lower():
            params['activity'] = 'test_drive'
        elif 'appointment' in message.lower():
            params['activity'] = 'appointment'
        else:
            params['activity'] = 'general'

        return params

    def _adjust_scores_with_context(
        self,
        intent_scores: Dict[IntentType, float],
        context: Dict[str, Any]
    ) -> Dict[IntentType, float]:
        """Adjust intent scores based on conversation context"""

        # If user just saw search results, likely wants to refine or compare
        if context.get('last_action') == 'search_results':
            intent_scores[IntentType.COMPARE] += 0.3
            intent_scores[IntentType.CLARIFY] += 0.2

        # If user is at beginning of conversation
        if context.get('message_count', 0) < 3:
            intent_scores[IntentType.GREET] += 0.2
            intent_scores[IntentType.SEARCH] += 0.1

        # If user has been searching for a while
        if context.get('message_count', 0) > 10:
            intent_scores[IntentType.ADVICE] += 0.2
            intent_scores[IntentType.SCHEDULE] += 0.2

        return intent_scores

    def _quick_entity_extract(self, message: str) -> Dict[str, List[str]]:
        """Quick entity extraction for comparison"""
        entities = {'brands': [], 'models': []}

        # Common brands
        brands = ['toyota', 'honda', 'ford', 'chevrolet', 'tesla', 'bmw', 'mercedes', 'audi']
        for brand in brands:
            if brand in message.lower():
                entities['brands'].append(brand)

        # Common models (simplified)
        models = ['camry', 'accord', 'f-150', 'model 3', 'explorer', 'cr-v', 'rav4']
        for model in models:
            if model in message.lower():
                entities['models'].append(model)

        return entities


class EntityExtractor:
    """Specialized entity extractor for vehicle domain"""

    def __init__(self):
        # Entity patterns for vehicle domain
        self.entity_patterns = {
            EntityType.VEHICLE_TYPE: {
                'patterns': [
                    r'\b(suv|sedan|truck|coupe|convertible|hatchback|minivan|van|crossover|wagon)\b',
                    r'\b(compact|midsize|fullsize)\s+(suv|sedan|truck)\b'
                ],
                'normalization': {
                    'crossover': 'suv',
                    'pickup': 'truck'
                }
            },
            EntityType.BRAND: {
                'patterns': [
                    r'\b(toyota|honda|ford|chevrolet|tesla|bmw|mercedes|audi|hyundai|kia|nissan|mazda|volkswagen|subaru|jeep|ram|gmc|buick|cadillac|lexus|infiniti|acura|volvo|jaguar|land rover|porsche|ferrari|lamborghini|maserati|bentley|rolls royce|mclaren|aston martin|genesis|mini|mitsubishi)\b'
                ],
                'normalization': {}
            },
            EntityType.MODEL: {
                'patterns': [
                    # Toyota
                    r'\b(camry|corolla|prius|rav4|highlander|sienna|tacoma|tundra|4runner)\b',
                    # Honda
                    r'\b(accord|civic|cr-v|pilot|odyssey|fit|hr-v|passport|ridgeline)\b',
                    # Ford
                    r'\b(f-150|f-250|explorer|escape|mustang|fusion|edge| Expedition|bronco)\b',
                    # Tesla
                    r'\b(model\s?3|model\s?s|model\s?x|model\s?y|cybertruck)\b',
                    # BMW
                    r'\b(3\s?series|5\s?series|x3|x5|x7|\d{3}[i|d|e])\b',
                    # Mercedes
                    r'\b(c-class|e-class|s-class|gla|glb|glc|gle|gls)\b',
                    # Audi
                    r'\b(a3|a4|a6|a8|q3|q5|q7|tt)\b'
                ],
                'normalization': {
                    'model 3': 'Model 3',
                    'model s': 'Model S',
                    'model x': 'Model X',
                    'model y': 'Model Y'
                }
            },
            EntityType.PRICE: {
                'patterns': [
                    r'\$([0-9,]+)',
                    r'([0-9,]+)\s*dollars?',
                    r'([0-9,]+)\s*bucks?'
                ],
                'validation': lambda x: 1000 <= x <= 500000  # Reasonable vehicle price range
            },
            EntityType.YEAR: {
                'patterns': [
                    r'\b(20[0-2][0-9])\b',
                    r"\b'([0-9]{2})\b"
                ],
                'validation': lambda x: 1990 <= x <= datetime.now().year + 1
            },
            EntityType.FEATURE: {
                'patterns': [
                    # Safety features
                    r'\b(abs|airbags|blind spot|lane assist|adaptive cruise|collision warning|parking assist)\b',
                    # Comfort features
                    r'\b(leather|heated seats|cooled seats|climate control|sunroof|moonroof|panoramic)\b',
                    # Technology features
                    r'\b(apple carplay|android auto|bluetooth|navigation|gps|infotainment|touchscreen)\b',
                    # Performance features
                    r'\b(awd|4wd|all wheel drive|four wheel drive|turbo|supercharged|hybrid|electric|ev|plugin|phev)\b'
                ],
                'normalization': {}
            },
            EntityType.COLOR: {
                'patterns': [
                    r'\b(black|white|silver|gray|red|blue|green|brown|beige|gold|orange|purple|yellow|pink)\b'
                ],
                'normalization': {}
            },
            EntityType.TRANSMISSION: {
                'patterns': [
                    r'\b(automatic|manual|cvt|dual clutch|paddle shifters)\b'
                ],
                'normalization': {
                    'auto': 'automatic',
                    'stick': 'manual',
                    'standard': 'manual'
                }
            },
            EntityType.FUEL_TYPE: {
                'patterns': [
                    r'\b(gasoline|diesel|electric|hybrid|plugin|hydrogen|cng|lpg)\b'
                ],
                'normalization': {
                    'gas': 'gasoline',
                    'ev': 'electric',
                    'phev': 'plugin hybrid'
                }
            },
            EntityType.FAMILY_SIZE: {
                'patterns': [
                    r'\b(family of (\d+)|(\d+) people|(\d+) seats?|(\d+) kids?)\b'
                ],
                'validation': lambda x: 1 <= x <= 8
            },
            EntityType.MILEAGE: {
                'patterns': [
                    r'\b([0-9,]+)\s*(?:miles|mi|kilometers|km)\b'
                ],
                'validation': lambda x: 0 <= x <= 300000
            }
        }

    async def extract_entities(self, message: str) -> List[VehicleEntity]:
        """
        Extract all vehicle domain entities from message
        """

        entities = []

        for entity_type, config in self.entity_patterns.items():
            # Try each pattern
            for pattern in config['patterns']:
                matches = re.finditer(pattern, message, re.IGNORECASE)

                for match in matches:
                    # Extract and validate value
                    raw_value = match.group(0)

                    # Special handling for entities with capture groups
                    if entity_type in [EntityType.PRICE, EntityType.YEAR, EntityType.FAMILY_SIZE, EntityType.MILEAGE]:
                        # Find the numeric group
                        groups = match.groups()
                        if groups:
                            value_str = groups[-1]  # Last group is usually the value
                            try:
                                if entity_type == EntityType.FAMILY_SIZE:
                                    # For family size, check multiple groups
                                    for g in groups:
                                        if g and g.isdigit():
                                            value = int(g)
                                            break
                                    else:
                                        continue
                                elif entity_type == EntityType.PRICE or entity_type == EntityType.MILEAGE:
                                    value = int(value_str.replace(',', ''))
                                else:
                                    value = int(value_str)

                                # Validate if validation function exists
                                if 'validation' in config and not config['validation'](value):
                                    continue
                            except ValueError:
                                continue
                        else:
                            continue
                    else:
                        value = raw_value

                    # Normalize if needed
                    if 'normalization' in config:
                        normalized = config['normalization'].get(value.lower(), value)
                        value = normalized.title() if isinstance(normalized, str) else value

                    # Create entity
                    entity = VehicleEntity(
                        entity_type=entity_type,
                        value=value,
                        confidence=self._calculate_confidence(entity_type, match, message),
                        context={
                            'pattern': pattern,
                            'full_match': raw_value
                        },
                        extracted_from=message,
                        position=(match.start(), match.end())
                    )

                    entities.append(entity)

        # Remove duplicates and merge similar entities
        entities = self._merge_similar_entities(entities)

        return entities

    def _calculate_confidence(
        self,
        entity_type: EntityType,
        match: re.Match,
        full_message: str
    ) -> float:
        """
        Calculate confidence score for extracted entity
        """

        # Base confidence
        confidence = 0.7

        # Boost for exact word boundaries
        if match.group(0) == full_message[match.start():match.end()]:
            confidence += 0.1

        # Boost based on entity type reliability
        type_confidence = {
            EntityType.BRAND: 0.9,
            EntityType.MODEL: 0.8,
            EntityType.PRICE: 0.9,
            EntityType.YEAR: 0.9,
            EntityType.VEHICLE_TYPE: 0.8,
            EntityType.FEATURE: 0.7,
            EntityType.FUEL_TYPE: 0.8,
            EntityType.TRANSMISSION: 0.8
        }

        confidence = (confidence + type_confidence.get(entity_type, 0.7)) / 2

        # Contextual adjustments
        if entity_type == EntityType.MODEL:
            # Check if brand is mentioned nearby
            context_window = 50
            start = max(0, match.start() - context_window)
            end = min(len(full_message), match.end() + context_window)
            context = full_message[start:end].lower()

            brands = ['toyota', 'honda', 'ford', 'chevrolet', 'tesla', 'bmw', 'mercedes', 'audi']
            if any(brand in context for brand in brands):
                confidence += 0.1

        return min(confidence, 1.0)

    def _merge_similar_entities(self, entities: List[VehicleEntity]) -> List[VehicleEntity]:
        """
        Merge duplicate or similar entities
        """

        merged = {}
        result = []

        for entity in entities:
            key = f"{entity.entity_type}:{str(entity.value).lower()}"

            if key in merged:
                # Update existing entity if this one has higher confidence
                if entity.confidence > merged[key].confidence:
                    merged[key] = entity
            else:
                merged[key] = entity

        # Convert back to list, sorted by confidence
        result = sorted(merged.values(), key=lambda e: e.confidence, reverse=True)

        return result


class PreferenceDetector:
    """Detect and weight user preferences from conversation"""

    def __init__(self):
        self.preference_keywords = {
            'budget': {
                'primary': ['cheap', 'expensive', 'affordable', 'budget', 'price', 'cost'],
                'modifiers': {
                    'under': 'max',
                    'below': 'max',
                    'over': 'min',
                    'above': 'min',
                    'around': 'target',
                    'about': 'target'
                }
            },
            'safety': {
                'primary': ['safe', 'safety', 'secure', 'protect', 'reliable'],
                'importance': ['very', 'extremely', 'really', 'must']
            },
            'performance': {
                'primary': ['fast', 'powerful', 'quick', 'sport', 'performance', 'speed'],
                'importance': ['very', 'extremely', 'really']
            },
            'efficiency': {
                'primary': ['efficient', 'economy', 'mpg', 'fuel', 'save money'],
                'importance': ['good', 'great', 'excellent', 'important']
            },
            'comfort': {
                'primary': ['comfortable', 'comfort', 'smooth', 'quiet', 'luxury'],
                'importance': ['very', 'extremely', 'really', 'must']
            },
            'technology': {
                'primary': ['tech', 'technology', 'features', 'connectivity', 'smart'],
                'importance': ['latest', 'new', 'modern', 'advanced']
            },
            'size': {
                'primary': ['big', 'small', 'large', 'compact', 'spacious', 'roomy'],
                'context': {
                    'family': 'needs_space',
                    'commute': 'compact_ok',
                    'parking': 'compact_preferred'
                }
            }
        }

    async def detect_preferences(
        self,
        message: str,
        entities: List[VehicleEntity],
        context: Optional[Dict[str, Any]] = None
    ) -> List[UserPreference]:
        """
        Detect user preferences from message and context
        """

        preferences = []
        message_lower = message.lower()

        # Extract from explicit mentions
        for category, config in self.preference_keywords.items():
            # Check for primary keywords
            for keyword in config['primary']:
                if keyword in message_lower:
                    # Determine weight based on modifiers
                    weight = self._calculate_preference_weight(message_lower, config)

                    # Determine value based on entities and context
                    value = self._determine_preference_value(
                        category,
                        message,
                        entities,
                        context
                    )

                    preferences.append(UserPreference(
                        category=category,
                        value=value,
                        weight=weight,
                        source='explicit'
                    ))

        # Extract from implicit indicators
        implicit_prefs = self._extract_implicit_preferences(message, entities)
        preferences.extend(implicit_prefs)

        # Consolidate and rank preferences
        preferences = self._consolidate_preferences(preferences)

        return preferences

    def _calculate_preference_weight(self, message: str, config: Dict[str, Any]) -> float:
        """Calculate weight based on importance modifiers"""
        weight = 0.5  # Base weight

        if 'importance' in config:
            for modifier in config['importance']:
                if modifier in message:
                    weight = 0.9  # High importance
                    break
        else:
            weight = 0.7  # Standard preference

        return weight

    def _determine_preference_value(
        self,
        category: str,
        message: str,
        entities: List[VehicleEntity],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Determine the specific preference value"""

        if category == 'budget':
            # Extract from price entities
            for entity in entities:
                if entity.entity_type == EntityType.PRICE:
                    return entity.value

            # Look for budget modifiers
            for modifier, meaning in self.preference_keywords['budget']['modifiers'].items():
                if modifier in message.lower():
                    # Extract following number
                    pattern = f"{modifier} \\$?([0-9,]+)"
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        return {meaning: int(match.group(1).replace(',', ''))}

        elif category == 'size':
            # Infer from vehicle type entities
            for entity in entities:
                if entity.entity_type == EntityType.VEHICLE_TYPE:
                    value = str(entity.value).lower()
                    if value in ['suv', 'truck', 'minivan', 'van']:
                        return 'needs_space'
                    elif value in ['sedan', 'compact', 'hatchback']:
                        return 'compact_ok'

        return True  # Generic preference

    def _extract_implicit_preferences(
        self,
        message: str,
        entities: List[VehicleEntity]
    ) -> List[UserPreference]:
        """Extract implicit preferences from message content"""

        preferences = []
        message_lower = message.lower()

        # Family-related preferences
        family_indicators = ['family', 'kids', 'children', 'car seats', 'school run']
        if any(indicator in message_lower for indicator in family_indicators):
            preferences.append(UserPreference(
                category='family_friendly',
                value=True,
                weight=0.8,
                source='implicit'
            ))

        # Commute-related preferences
        commute_indicators = ['commute', 'highway', 'traffic', 'mpg', 'fuel economy']
        if any(indicator in message_lower for indicator in commute_indicators):
            preferences.append(UserPreference(
                category='commute_friendly',
                value=True,
                weight=0.7,
                source='implicit'
            ))

        # Weather/climate preferences
        weather_indicators = ['snow', 'winter', 'rain', 'awd', '4wd']
        if any(indicator in message_lower for indicator in weather_indicators):
            preferences.append(UserPreference(
                category='weather_capability',
                value=True,
                weight=0.8,
                source='implicit'
            ))

        return preferences

    def _consolidate_preferences(self, preferences: List[UserPreference]) -> List[UserPreference]:
        """Consolidate and rank preferences"""

        # Group by category
        grouped = {}
        for pref in preferences:
            if pref.category not in grouped:
                grouped[pref.category] = []
            grouped[pref.category].append(pref)

        # Consolidate each category
        consolidated = []
        for category, prefs in grouped.items():
            if len(prefs) == 1:
                consolidated.append(prefs[0])
            else:
                # Multiple preferences in same category
                # Take the one with highest weight
                best = max(prefs, key=lambda p: p.weight)
                consolidated.append(best)

        # Sort by weight
        consolidated.sort(key=lambda p: p.weight, reverse=True)

        return consolidated


class ContextAwareIntentDisambiguation:
    """Handle ambiguous intents using conversation context"""

    def __init__(self):
        self.ambiguity_resolvers = {
            # Context patterns for resolving ambiguity
            'search_vs_info': {
                'indicates_search': ['show me', 'find', 'looking for', 'need'],
                'indicates_info': ['what is', 'tell me about', 'explain', 'how does']
            },
            'compare_vs_search': {
                'indicates_compare': ['vs', 'versus', 'or', 'better', 'difference'],
                'indicates_search': ['need', 'want', 'looking for']
            }
        }

    async def disambiguate_intent(
        self,
        primary_intent: VehicleIntent,
        secondary_intent: Optional[VehicleIntent],
        message: str,
        context: Dict[str, Any]
    ) -> VehicleIntent:
        """
        Disambiguate between competing intents
        """

        if not secondary_intent or primary_intent.confidence - secondary_intent.confidence > 0.3:
            # Clear winner
            return primary_intent

        # Resolve ambiguity based on context
        message_lower = message.lower()

        # Search vs Information ambiguity
        if (primary_intent.intent_type == IntentType.SEARCH and
            secondary_intent.intent_type == IntentType.INFORMATION):

            if any(phrase in message_lower for phrase in self.ambiguity_resolvers['search_vs_info']['indicates_search']):
                return primary_intent
            elif any(phrase in message_lower for phrase in self.ambiguity_resolvers['search_vs_info']['indicates_info']):
                return secondary_intent

        # Compare vs Search ambiguity
        if (primary_intent.intent_type in [IntentType.SEARCH, IntentType.COMPARE] and
            secondary_intent.intent_type in [IntentType.SEARCH, IntentType.COMPARE]):

            if any(phrase in message_lower for phrase in self.ambiguity_resolvers['compare_vs_search']['indicates_compare']):
                return primary_intent if primary_intent.intent_type == IntentType.COMPARE else secondary_intent
            elif any(phrase in message_lower for phrase in self.ambiguity_resolvers['compare_vs_search']['indicates_search']):
                return primary_intent if primary_intent.intent_type == IntentType.SEARCH else secondary_intent

        # Use conversation flow context
        if context.get('last_action') == 'search_results':
            # After search results, more likely to compare or ask questions
            if secondary_intent.intent_type in [IntentType.COMPARE, IntentType.INFORMATION]:
                return secondary_intent

        # Default to primary intent
        return primary_intent