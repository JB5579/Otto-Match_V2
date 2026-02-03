"""
Preference Engine for Otto.AI
Extracts, tracks, and evolves user preferences from conversations
"""

import json
import logging
import re
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
Entity = Any
UserPreference = Any


class PreferenceCategory(Enum):
    """Categories of user preferences"""
    BUDGET = "budget"
    VEHICLE_TYPE = "vehicle_type"
    BRAND = "brand"
    FEATURE = "feature"
    LIFESTYLE = "lifestyle"
    FAMILY_SIZE = "family_size"
    COMMUTE = "commute"
    ENVIRONMENT = "environment"
    SAFETY = "safety"
    PERFORMANCE = "performance"
    TECHNOLOGY = "technology"
    STYLE = "style"


class PreferenceSource(Enum):
    """Sources of preference detection"""
    EXPLICIT = "explicit"      # Directly stated by user
    IMPLICIT = "implicit"      # Inferred from behavior
    CONTEXTUAL = "contextual"  # Inferred from conversation context
    CORRECTED = "corrected"    # User corrected previous assumption


@dataclass
class PreferenceConflict:
    """Represents a conflict between preferences"""
    category: PreferenceCategory
    old_preference: UserPreference
    new_preference: UserPreference
    confidence_delta: float
    resolution_strategy: str  # "merge", "replace", "ask_user", "weight_average"


@dataclass
class PreferenceEvolution:
    """Tracks evolution of a preference over time"""
    category: PreferenceCategory
    values: List[Tuple[Any, float, datetime]]  # (value, confidence, timestamp)
    trend: str  # "increasing", "decreasing", "stable", "fluctuating"
    last_change: datetime
    change_frequency: float  # Changes per month


@dataclass
class BehaviorSignal:
    """Signal from user behavior indicating preference"""
    signal_type: str  # "click", "save", "compare", "ignore", "return"
    entity_id: str
    entity_type: str  # "vehicle", "brand", "feature"
    timestamp: datetime
    weight: float  # Strength of the signal
    context: Dict[str, Any]


class PreferenceEngine:
    """Engine for extracting and managing user preferences"""

    def __init__(
        self,
        groq_client: GroqClient,
        temporal_memory: TemporalMemoryManager,
        confidence_threshold: float = 0.6,
        evolution_window: int = 30  # days
    ):
        self.groq_client = groq_client
        self.temporal_memory = temporal_memory
        self.confidence_threshold = confidence_threshold
        self.evolution_window = evolution_window
        self.initialized = False

        # Preference extraction patterns
        self.extraction_patterns = self._initialize_extraction_patterns()

        # Brand and feature taxonomies
        self.vehicle_brands = self._load_vehicle_brands()
        self.vehicle_features = self._load_vehicle_features()

        # User preference histories
        self.preference_histories: Dict[str, Dict[PreferenceCategory, PreferenceEvolution]] = {}

    async def initialize(self) -> bool:
        """Initialize the preference engine"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            if not self.temporal_memory.initialized:
                logger.error("Temporal memory manager not initialized")
                return False

            self.initialized = True
            logger.info("Preference engine initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize preference engine: {e}")
            return False

    async def extract_preferences(
        self,
        message: str,
        entities: List[Entity],
        context: Optional[Dict[str, Any]] = None
    ) -> List[UserPreference]:
        """Extract preferences from user message"""
        if not self.initialized:
            return []

        try:
            preferences = []
            context = context or {}

            # Extract explicit preferences
            explicit_prefs = await self._extract_explicit_preferences(message, entities)
            preferences.extend(explicit_prefs)

            # Extract implicit preferences from language patterns
            implicit_prefs = await self._extract_implicit_preferences(message, context)
            preferences.extend(implicit_prefs)

            # Detect conflicts and resolve
            resolved_prefs = await self._resolve_preference_conflicts(
                context.get("user_id", "anonymous"),
                preferences
            )

            # Apply confidence boosting based on repetition
            boosted_prefs = await self._boost_confidence_from_repetition(
                context.get("user_id", "anonymous"),
                resolved_prefs
            )

            return boosted_prefs

        except Exception as e:
            logger.error(f"Failed to extract preferences: {e}")
            return []

    async def update_preferences_from_behavior(
        self,
        user_id: str,
        behavior_signals: List[BehaviorSignal]
    ) -> List[UserPreference]:
        """Update preferences based on user behavior signals"""
        if not self.initialized:
            return []

        try:
            updated_preferences = []

            for signal in behavior_signals:
                # Infer preference from behavior
                inferred_pref = await self._infer_preference_from_behavior(signal)
                if inferred_pref:
                    # Adjust weight based on behavior type
                    inferred_pref.weight *= self._get_behavior_weight_multiplier(signal.signal_type)
                    updated_preferences.append(inferred_pref)

                    # Store behavioral memory
                    await self.temporal_memory.add_memory_fragment(
                        user_id=user_id,
                        content=f"Behavioral signal: {signal.signal_type} on {signal.entity_type}",
                        memory_type=MemoryType.SEMANTIC,
                        importance=signal.weight,
                        associated_preferences=[asdict(inferred_pref)]
                    )

            return updated_preferences

        except Exception as e:
            logger.error(f"Failed to update preferences from behavior: {e}")
            return []

    async def get_evolved_preferences(
        self,
        user_id: str,
        categories: Optional[List[PreferenceCategory]] = None
    ) -> Dict[PreferenceCategory, UserPreference]:
        """Get evolved preferences applying time decay and evolution"""
        if not self.initialized:
            return {}

        try:
            # Get current preferences
            context = await self.temporal_memory.get_contextual_memory(user_id, "")
            base_prefs = context.user_preferences.get("preferences", {})

            evolved_prefs = {}

            for category in categories or PreferenceCategory:
                if category.value in base_prefs:
                    pref_data = base_prefs[category.value]

                    # Apply time decay
                    decayed_strength = self._apply_time_decay(
                        pref_data.get("strength", 0.5),
                        pref_data.get("updated_at", datetime.now().isoformat())
                    )

                    # Create evolved preference
                    evolved_pref = UserPreference(
                        category=category.value,
                        value=pref_data.get("value"),
                        weight=decayed_strength,
                        source=pref_data.get("source", "unknown"),
                        confidence=pref_data.get("confidence", 0.5)
                    )

                    evolved_prefs[category] = evolved_pref

            return evolved_prefs

        except Exception as e:
            logger.error(f"Failed to get evolved preferences: {e}")
            return {}

    async def detect_preference_changes(
        self,
        user_id: str,
        days_back: int = 30
    ) -> List[PreferenceEvolution]:
        """Detect significant changes in user preferences"""
        if not self.initialized:
            return []

        try:
            evolutions = []

            # Get historical preference data
            history = await self._get_preference_history(user_id, days_back)

            # Analyze each category
            for category, values in history.items():
                if len(values) < 2:
                    continue

                # Calculate trend
                trend = self._calculate_preference_trend(values)

                # Detect significant changes
                significant_changes = self._detect_significant_changes(values)

                if significant_changes:
                    evolution = PreferenceEvolution(
                        category=PreferenceCategory(category),
                        values=values,
                        trend=trend,
                        last_change=significant_changes[-1][2],
                        change_frequency=len(significant_changes) / (days_back / 30)
                    )
                    evolutions.append(evolution)

            return evolutions

        except Exception as e:
            logger.error(f"Failed to detect preference changes: {e}")
            return []

    async def cross_reference_preferences(
        self,
        user_id: str,
        explicit_prefs: List[UserPreference],
        implicit_prefs: List[UserPreference]
    ) -> Dict[str, Any]:
        """Cross-reference explicit and implicit preferences"""
        if not self.initialized:
            return {}

        try:
            analysis = {
                "consistent": [],
                "conflicting": [],
                "reinforcing": [],
                "gaps": []
            }

            # Group by category
            explicit_by_category = {p.category: p for p in explicit_prefs}
            implicit_by_category = {p.category: p for p in implicit_prefs}

            # Check each category
            all_categories = set(explicit_by_category.keys()) | set(implicit_by_category.keys())

            for category in all_categories:
                explicit = explicit_by_category.get(category)
                implicit = implicit_by_category.get(category)

                if explicit and implicit:
                    # Compare values
                    if self._values_match(explicit.value, implicit.value):
                        # Consistent - boost confidence
                        analysis["consistent"].append({
                            "category": category,
                            "explicit_value": explicit.value,
                            "implicit_value": implicit.value,
                            "boosted_confidence": min(1.0, (explicit.confidence + implicit.confidence) / 2 + 0.2)
                        })
                        analysis["reinforcing"].append(category)
                    else:
                        # Conflicting - need resolution
                        analysis["conflicting"].append({
                            "category": category,
                            "explicit_value": explicit.value,
                            "implicit_value": implicit.value,
                            "resolution_needed": True
                        })
                elif explicit and not implicit:
                    # Gap in implicit detection
                    analysis["gaps"].append({
                        "category": category,
                        "type": "implicit_not_detected",
                        "value": explicit.value
                    })
                elif implicit and not explicit:
                    # Gap in explicit detection
                    analysis["gaps"].append({
                        "category": category,
                        "type": "explicit_not_stated",
                        "value": implicit.value
                    })

            return analysis

        except Exception as e:
            logger.error(f"Failed to cross-reference preferences: {e}")
            return {}

    def _initialize_extraction_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize regex patterns for preference extraction"""
        return {
            "budget": {
                "patterns": [
                    r"under ?\$?(\d+(?:,\d+)*)",
                    r"less than ?\$?(\d+(?:,\d+)*)",
                    r"around ?\$?(\d+(?:,\d+)*)",
                    r"budget of ?\$?(\d+(?:,\d+)*)",
                    r"max ?\$?(\d+(?:,\d+)*)"
                ],
                "extractor": self._extract_budget_preference
            },
            "vehicle_type": {
                "patterns": [
                    r"(SUV|sedan|truck|coupe|convertible|hatchback|van|minivan)",
                    r"(electric|hybrid|gas|diesel)",
                    r"(compact|midsize|full-size|subcompact)",
                    r"(luxury|sports|family|economy)"
                ],
                "extractor": self._extract_vehicle_type_preference
            },
            "brand": {
                "patterns": [
                    r"\b(" + "|".join([
                        "Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes",
                        "Audi", "Volkswagen", "Tesla", "Nissan", "Mazda", "Hyundai",
                        "Kia", "Subaru", "Volvo", "Lexus", "Infiniti", "Acura",
                        "Cadillac", "Lincoln", "Jeep", "Ram", "Dodge", "Buick"
                    ]) + r")\b"
                ],
                "extractor": self._extract_brand_preference
            },
            "feature": {
                "patterns": [
                    r"(all-wheel drive|AWD|four-wheel drive|4WD)",
                    r"(sunroof|moonroof|panoramic roof)",
                    r"(leather seats|cloth seats|heated seats)",
                    r"(navigation|GPS|Apple CarPlay|Android Auto)",
                    r"(backup camera|parking sensors|360 camera)",
                    r"(blind spot monitoring|lane assist|adaptive cruise)"
                ],
                "extractor": self._extract_feature_preference
            },
            "family_size": {
                "patterns": [
                    r"family of (\d+)",
                    r"(\d+) (kids?|children)",
                    r"need space for (\d+)",
                    r"seats? for (\d+)"
                ],
                "extractor": self._extract_family_size_preference
            }
        }

    def _load_vehicle_brands(self) -> Set[str]:
        """Load known vehicle brands"""
        return {
            "Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes", "Audi",
            "Volkswagen", "Tesla", "Nissan", "Mazda", "Hyundai", "Kia",
            "Subaru", "Volvo", "Lexus", "Infiniti", "Acura", "Cadillac",
            "Lincoln", "Jeep", "Ram", "Dodge", "Buick", "Mitsubishi",
            "Porsche", "Jaguar", "Land Rover", "Ferrari", "Lamborghini"
        }

    def _load_vehicle_features(self) -> Dict[str, List[str]]:
        """Load vehicle feature taxonomy"""
        return {
            "safety": [
                "airbags", "ABS", "traction control", "stability control",
                "blind spot monitoring", "lane departure warning", "forward collision warning"
            ],
            "comfort": [
                "air conditioning", "heated seats", "ventilated seats",
                "leather upholstery", "power seats", "sunroof", "premium audio"
            ],
            "technology": [
                "touchscreen", "navigation", "Bluetooth", "USB ports",
                "Apple CarPlay", "Android Auto", "Wi-Fi hotspot"
            ],
            "performance": [
                "turbocharger", "sport mode", "paddle shifters",
                "AWD", "4WD", "sport suspension"
            ]
        }

    async def _extract_explicit_preferences(
        self,
        message: str,
        entities: List[Entity]
    ) -> List[UserPreference]:
        """Extract explicitly stated preferences"""
        preferences = []
        message_lower = message.lower()

        # Extract from entities first
        for entity in entities:
            if entity.confidence > 0.7:
                pref = UserPreference(
                    category=entity.type,
                    value=entity.value,
                    weight=0.8,
                    source="explicit",
                    extracted_at=datetime.now()
                )
                preferences.append(pref)

        # Apply extraction patterns
        for category, config in self.extraction_patterns.items():
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, message, re.IGNORECASE)
                for match in matches:
                    pref = config["extractor"](match, message)
                    if pref:
                        preferences.append(pref)

        return preferences

    async def _extract_implicit_preferences(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> List[UserPreference]:
        """Extract implicit preferences from language patterns"""
        preferences = []

        # Analyze sentiment and emotional language
        if any(word in message.lower() for word in ["love", "really like", "prefer", "want"]):
            # Positive sentiment indicates preference
            preferences.extend(await self._extract_sentiment_preferences(message, "positive"))

        if any(word in message.lower() for word in ["hate", "dislike", "avoid", "don't want"]):
            # Negative sentiment indicates anti-preference
            preferences.extend(await self._extract_sentiment_preferences(message, "negative"))

        # Analyze contextual clues
        if "commute" in message.lower():
            preferences.append(UserPreference(
                category="lifestyle",
                value="commuter",
                weight=0.6,
                source="implicit"
            ))

        if "family" in message.lower() or "kids" in message.lower():
            preferences.append(UserPreference(
                category="lifestyle",
                value="family_oriented",
                weight=0.7,
                source="implicit"
            ))

        return preferences

    async def _update_preference_confidence(
        self,
        existing_preferences: List[UserPreference],
        new_preference: UserPreference
    ) -> List[UserPreference]:
        """Update confidence scores based on repeated preferences"""
        updated = existing_preferences.copy()

        # Find matching preferences
        for i, pref in enumerate(updated):
            if (pref.category == new_preference.category and
                str(pref.value) == str(new_preference.value)):

                # Increase confidence based on repetition
                pref.confidence = min(0.99, pref.confidence + 0.1)

                # Update timestamp
                pref.timestamp = datetime.now()

                # Adjust weight if confidence increased significantly
                if pref.confidence > 0.8:
                    pref.weight = min(1.0, pref.weight * 1.1)

                logger.info(f"Updated confidence for {pref.category}: {pref.confidence:.2f}")

        return updated

    async def _calculate_confidence_score(
        self,
        preference: UserPreference,
        user_history: List[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate confidence score for a preference based on:
        - Source reliability
        - Repetition frequency
        - Consistency over time
        - Context relevance
        """
        base_confidence = 0.5  # Starting confidence

        # Source-based confidence
        source_weights = {
            "explicit": 0.3,
            "implicit": 0.1,
            "behavioral": 0.15,
            "corrected": 0.4,
            "inferred": 0.2
        }
        base_confidence += source_weights.get(preference.source, 0.1)

        # Repetition bonus (if we have history)
        if user_history:
            repetitions = sum(
                1 for h in user_history
                if (h.get("category") == preference.category and
                    str(h.get("value")) == str(preference.value))
            )
            repetition_bonus = min(0.3, repetitions * 0.1)
            base_confidence += repetition_bonus

        # Consistency check
        # Higher confidence for preferences that haven't changed
        if hasattr(preference, "first_seen"):
            days_since_first = (datetime.now() - preference.first_seen).days
            if days_since_first > 7:  # Consistent for over a week
                base_confidence += 0.1

        # Weight importance influence
        if preference.weight > 0.8:
            base_confidence += 0.1

        return min(0.99, max(0.1, base_confidence))

    async def _decay_confidence_over_time(
        self,
        preference: UserPreference,
        days_without_reinforcement: int = 30
    ) -> UserPreference:
        """Apply time-based decay to confidence scores"""
        if not preference.timestamp:
            return preference

        days_old = (datetime.now() - preference.timestamp).days
        decay_factor = max(0, 1 - (days_old / days_without_reinforcement))

        # Apply decay
        preference.confidence *= decay_factor

        # Don't let confidence go below minimum threshold
        preference.confidence = max(0.1, preference.confidence)

        # Also decay weight slightly for very old preferences
        if days_old > 90:
            preference.weight *= 0.9

        return preference

    async def _boost_confidence_from_repetition(
        self,
        user_id: str,
        preferences: List[UserPreference]
    ) -> List[UserPreference]:
        """Boost confidence for preferences that appear frequently"""
        # Count occurrences of each preference
        pref_counts = {}
        for pref in preferences:
            key = f"{pref.category}:{pref.value}"
            pref_counts[key] = pref_counts.get(key, 0) + 1

        # Apply confidence boost for repeated preferences
        boosted = []
        for pref in preferences:
            key = f"{pref.category}:{pref.value}"
            count = pref_counts.get(key, 1)

            # Boost based on frequency
            if count > 1:
                boost = min(0.3, (count - 1) * 0.1)
                pref.confidence = min(0.99, pref.confidence + boost)

                # Also slightly boost weight
                pref.weight = min(1.0, pref.weight * (1 + boost * 0.5))

            boosted.append(pref)

        return boosted

    async def _detect_preference_conflicts(
        self,
        preferences: List[UserPreference]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between preferences"""
        conflicts = []

        # Group by category
        by_category = {}
        for pref in preferences:
            if pref.category not in by_category:
                by_category[pref.category] = []
            by_category[pref.category].append(pref)

        # Check for conflicts in each category
        for category, prefs in by_category.items():
            if len(prefs) > 1:
                # Check for conflicting values
                values = [str(p.value) for p in prefs]
                unique_values = list(set(values))

                if len(unique_values) > 1:
                    conflicts.append({
                        "category": category,
                        "conflicting_values": unique_values,
                        "count": len(prefs),
                        "highest_confidence": max(p.confidence for p in prefs),
                        "suggestion": f"Multiple {category} preferences detected"
                    })

        return conflicts

    async def _validate_preference(
        self,
        preference: UserPreference
    ) -> bool:
        """Validate preference structure and values"""
        # Check required fields
        if not preference.category or not preference.value:
            return False

        # Category validation
        valid_categories = [
            "brand", "price_range", "vehicle_type", "fuel_type",
            "safety_priority", "family_friendly", "budget",
            "location", "usage_pattern", "features", "color"
        ]

        if preference.category not in valid_categories:
            logger.warning(f"Unknown preference category: {preference.category}")

        # Value validation based on category
        if preference.category == "price_range":
            if isinstance(preference.value, dict):
                min_val = preference.value.get("min", 0)
                max_val = preference.value.get("max", float("inf"))
                if min_val > max_val:
                    return False

        # Weight and confidence validation
        if not (0 <= preference.weight <= 1.0):
            return False
        if not (0 <= preference.confidence <= 1.0):
            return False

        return True

    async def _resolve_preference_conflicts(
        self,
        user_id: str,
        preferences: List[UserPreference]
    ) -> List[UserPreference]:
        """Detect and resolve conflicts between preferences"""
        # Group by category
        by_category = {}
        for pref in preferences:
            if pref.category not in by_category:
                by_category[pref.category] = []
            by_category[pref.category].append(pref)

        resolved = []

        for category, category_prefs in by_category.items():
            if len(category_prefs) == 1:
                resolved.append(category_prefs[0])
            else:
                # Conflict detected - resolve based on confidence
                sorted_prefs = sorted(category_prefs, key=lambda p: p.confidence, reverse=True)
                winner = sorted_prefs[0]

                # Average conflicting preferences if they're close
                if len(sorted_prefs) >= 2 and abs(sorted_prefs[0].confidence - sorted_prefs[1].confidence) < 0.2:
                    winner.weight = sum(p.weight for p in sorted_prefs[:2]) / 2
                    winner.confidence = sum(p.confidence for p in sorted_prefs[:2]) / 2

                resolved.append(winner)

        return resolved

    async def _boost_confidence_from_repetition(
        self,
        user_id: str,
        preferences: List[UserPreference]
    ) -> List[UserPreference]:
        """Boost confidence based on repeated preferences"""
        # Get historical preferences
        context = await self.temporal_memory.get_contextual_memory(user_id, "")
        historical = context.user_preferences.get("preferences", {})

        for pref in preferences:
            if pref.category in historical:
                hist_pref = historical[pref.category]

                # Check if value matches
                if hist_pref.get("value") == pref.value:
                    # Boost confidence based on interaction count
                    interaction_count = hist_pref.get("interaction_count", 0)
                    boost = min(0.3, interaction_count * 0.05)
                    pref.confidence = min(1.0, pref.confidence + boost)

        return preferences

    def _extract_budget_preference(self, match, message: str) -> Optional[UserPreference]:
        """Extract budget preference from regex match"""
        try:
            value = int(match.group(1).replace(",", ""))
            if value < 100:  # Likely in thousands
                value *= 1000

            return UserPreference(
                category="budget",
                value=value,
                weight=0.8,
                source="explicit"
            )
        except:
            return None

    def _extract_vehicle_type_preference(self, match, message: str) -> Optional[UserPreference]:
        """Extract vehicle type preference from regex match"""
        value = match.group(1).lower()

        # Normalize some values
        type_mapping = {
            "suv": "SUV",
            "electric": "EV",
            "hybrid": "Hybrid",
            "luxury": "Luxury"
        }

        normalized_value = type_mapping.get(value, value.title())

        return UserPreference(
            category="vehicle_type",
            value=normalized_value,
            weight=0.7,
            source="explicit"
        )

    def _extract_brand_preference(self, match, message: str) -> Optional[UserPreference]:
        """Extract brand preference from regex match"""
        brand = match.group(1).title()

        # Determine if positive or negative sentiment
        words_before = message[:match.start()].lower()
        is_negative = any(word in words_before.split() for word in ["not", "don't", "avoid", "hate"])

        weight = 0.7 if not is_negative else -0.7

        return UserPreference(
            category="brand",
            value=brand,
            weight=abs(weight),
            source="explicit"
        )

    def _extract_feature_preference(self, match, message: str) -> Optional[UserPreference]:
        """Extract feature preference from regex match"""
        feature = match.group(1).lower()

        # Determine feature category
        feature_category = "other"
        for cat, features in self.vehicle_features.items():
            if any(f in feature for f in features):
                feature_category = cat
                break

        return UserPreference(
            category="feature",
            value={
                "name": feature,
                "category": feature_category
            },
            weight=0.6,
            source="explicit"
        )

    def _extract_family_size_preference(self, match, message: str) -> Optional[UserPreference]:
        """Extract family size preference from regex match"""
        size = int(match.group(1))

        return UserPreference(
            category="family_size",
            value=size,
            weight=0.8,
            source="explicit"
        )

    async def _extract_sentiment_preferences(
        self,
        message: str,
        sentiment: str
    ) -> List[UserPreference]:
        """Extract preferences from sentiment analysis"""
        # Use Groq to analyze sentiment preferences
        try:
            prompt = f"""
            Analyze the following message for vehicle preferences:

            Message: "{message}"
            Sentiment: {sentiment}

            Extract any vehicle preferences implied by the sentiment. Return as JSON:
            {{
                "preferences": [
                    {{
                        "category": "preference_category",
                        "value": "preference_value",
                        "confidence": 0.0-1.0
                    }}
                ]
            }}
            """

            response = await self.groq_client.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )

            # Parse Groq response
            result = json.loads(response.choices[0].message.content)
            preferences = []

            for pref_data in result.get("preferences", []):
                pref = UserPreference(
                    category=pref_data.get("category"),
                    value=pref_data.get("value"),
                    weight=0.5,
                    source="implicit",
                    confidence=pref_data.get("confidence", 0.5)
                )
                preferences.append(pref)

            return preferences

        except Exception as e:
            logger.error(f"Failed to analyze sentiment preferences: {e}")
            return []

    async def _infer_preference_from_behavior(self, signal: BehaviorSignal) -> Optional[UserPreference]:
        """Infer preference from behavioral signal"""
        if signal.signal_type == "save":
            # User saved a vehicle - positive preference
            return UserPreference(
                category="implicit_interest",
                value=signal.entity_id,
                weight=signal.weight,
                source="implicit",
                confidence=0.8
            )
        elif signal.signal_type == "compare":
            # User comparing vehicles - considering features
            return UserPreference(
                category="consideration",
                value={
                    "entity_id": signal.entity_id,
                    "comparison_context": signal.context
                },
                weight=signal.weight * 0.6,
                source="implicit"
            )
        elif signal.signal_type == "ignore":
            # User ignored recommendation - negative preference
            return UserPreference(
                category="avoid",
                value=signal.entity_id,
                weight=signal.weight * -0.5,
                source="implicit"
            )

        return None

    def _get_behavior_weight_multiplier(self, signal_type: str) -> float:
        """Get weight multiplier for different behavior types"""
        multipliers = {
            "click": 0.3,
            "save": 0.8,
            "compare": 0.6,
            "ignore": -0.4,
            "return": 0.7,
            "share": 0.5,
            "inquire": 0.6
        }
        return multipliers.get(signal_type, 0.5)

    def _apply_time_decay(self, strength: float, updated_at: str) -> float:
        """Apply time decay to preference strength"""
        try:
            last_update = datetime.fromisoformat(updated_at)
            days_elapsed = (datetime.now() - last_update).days
            decay_factor = 0.95 ** days_elapsed
            return strength * decay_factor
        except:
            return strength

    async def _get_preference_history(
        self,
        user_id: str,
        days_back: int
    ) -> Dict[str, List[Tuple[Any, float, datetime]]]:
        """Get historical preference data"""
        # This would query stored preference history
        # For now, return empty dict
        return {}

    def _calculate_preference_trend(
        self,
        values: List[Tuple[Any, float, datetime]]
    ) -> str:
        """Calculate trend of preference values"""
        if len(values) < 2:
            return "stable"

        # Simple linear regression on confidence values
        confidences = [v[1] for v in values]
        if confidences[-1] > confidences[0] + 0.2:
            return "increasing"
        elif confidences[-1] < confidences[0] - 0.2:
            return "decreasing"
        elif self._is_fluctuating(confidences):
            return "fluctuating"
        else:
            return "stable"

    def _detect_significant_changes(
        self,
        values: List[Tuple[Any, float, datetime]],
        threshold: float = 0.3
    ) -> List[Tuple[Any, float, datetime]]:
        """Detect significant changes in preference values"""
        changes = []
        for i in range(1, len(values)):
            if values[i][1] - values[i-1][1] > threshold:
                changes.append(values[i])
        return changes

    def _is_fluctuating(self, values: List[float], window: int = 3) -> bool:
        """Check if values are fluctuating"""
        if len(values) < window * 2:
            return False

        # Calculate standard deviation in sliding window
        for i in range(len(values) - window + 1):
            window_vals = values[i:i+window]
            std_dev = np.std(window_vals)
            if std_dev > 0.2:  # High fluctuation threshold
                return True
        return False

    def _values_match(self, value1: Any, value2: Any) -> bool:
        """Check if two preference values match"""
        if value1 is None or value2 is None:
            return False

        # Handle numeric values
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return abs(value1 - value2) < 0.1 * max(value1, value2, 1)

        # Handle strings
        if isinstance(value1, str) and isinstance(value2, str):
            return value1.lower() == value2.lower()

        # Handle dictionaries
        if isinstance(value1, dict) and isinstance(value2, dict):
            return value1.get("name") == value2.get("name")

        return value1 == value2