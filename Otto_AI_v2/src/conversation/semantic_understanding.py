"""
Semantic Understanding Service for Otto AI
Handles semantic understanding of vehicle features and user preferences
"""

import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

from src.conversation.groq_client import GroqClient
from src.conversation.nlu_service import Entity, UserPreference
from src.conversation.intent_models import EntityType

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VehicleFeature:
    """Represents a vehicle feature with semantic understanding"""
    name: str
    category: str  # 'safety', 'comfort', 'performance', 'technology', 'efficiency'
    description: str
    importance_score: float  # 0.0 to 1.0
    related_features: List[str]
    user_benefits: List[str]
    synonyms: List[str]


@dataclass
class PreferenceWeight:
    """Represents a weighted user preference"""
    preference: str
    weight: float
    confidence: float
    source: str  # 'explicit', 'implicit', 'inferred'
    context: Dict[str, Any]


@dataclass
class SemanticMatch:
    """Represents a semantic match between user and vehicle"""
    vehicle_id: str
    match_score: float
    matched_features: List[str]
    mismatched_features: List[str]
    explanation: str


class VehicleFeatureTaxonomy:
    """Manages vehicle feature taxonomy and relationships"""

    def __init__(self):
        self.features = self._initialize_feature_taxonomy()
        self.feature_embeddings = {}  # Would be populated with actual embeddings
        self.feature_hierarchy = self._build_feature_hierarchy()

    def _initialize_feature_taxonomy(self) -> Dict[str, VehicleFeature]:
        """Initialize comprehensive vehicle feature taxonomy"""

        return {
            # Safety Features
            'airbags': VehicleFeature(
                name='Airbags',
                category='safety',
                description='Protective cushions that deploy during collision',
                importance_score=0.95,
                related_features=['anti_lock_brakes', 'collision_warning', 'stability_control'],
                user_benefits=['Protects occupants in crash', 'Reduces injury risk', 'Peace of mind'],
                synonyms=['air bag', 'safety bags', 'supplemental restraints']
            ),
            'blind_spot_monitoring': VehicleFeature(
                name='Blind Spot Monitoring',
                category='safety',
                description='Alerts driver to vehicles in blind spots',
                importance_score=0.85,
                related_features=['lane_assist', 'rear_cross_traffic', '360_camera'],
                user_benefits=['Prevents lane change accidents', 'Increases awareness', 'Reduces stress'],
                synonyms=['blind spot detection', 'BSD', 'blind spot warning']
            ),
            'adaptive_cruise_control': VehicleFeature(
                name='Adaptive Cruise Control',
                category='safety',
                description='Automatically maintains distance from vehicle ahead',
                importance_score=0.8,
                related_features=['collision_warning', 'lane_keep_assist', 'traffic_jam_assist'],
                user_benefits=['Reduces driver fatigue', 'Prevents rear-end collisions', 'Comfortable highway driving'],
                synonyms=['ACC', 'dynamic cruise', 'intelligent cruise']
            ),
            'lane_assist': VehicleFeature(
                name='Lane Assist',
                category='safety',
                description='Helps keep vehicle in lane',
                importance_score=0.8,
                related_features=['lane_departure_warning', 'lane_centering', 'driver_monitoring'],
                user_benefits=['Prevents drifting', 'Reduces fatigue', 'Highway safety'],
                synonyms=['lane keeping', 'LKAS', 'lane guidance']
            ),
            'automatic_emergency_braking': VehicleFeature(
                name='Automatic Emergency Braking',
                category='safety',
                description='Automatically applies brakes to avoid collision',
                importance_score=0.9,
                related_features=['forward_collision_warning', 'pedestrian_detection', 'city_safety'],
                user_benefits=['Prevents accidents', 'Protects pedestrians', 'Insurance discounts'],
                synonyms=['AEB', 'auto brake', 'collision mitigation']
            ),

            # Performance Features
            'all_wheel_drive': VehicleFeature(
                name='All-Wheel Drive',
                category='performance',
                description='Power sent to all four wheels',
                importance_score=0.7,
                related_features=['traction_control', 'torque_vectoring', 'drive_modes'],
                user_benefits=['Better traction in snow/rain', 'Improved acceleration', 'Confidence in bad weather'],
                synonyms=['AWD', '4WD', 'four wheel drive', 'traction']
            ),
            'turbo_engine': VehicleFeature(
                name='Turbo Engine',
                category='performance',
                description='Engine with turbocharger for increased power',
                importance_score=0.6,
                related_features=['engine_power', 'fuel_efficiency', 'drive_modes'],
                user_benefits=['Quick acceleration', 'Better highway merging', 'Fun to drive'],
                synonyms=['turbocharged', 'turbo', 'forced induction']
            ),
            'sport_mode': VehicleFeature(
                name='Sport Mode',
                category='performance',
                description='Enhanced throttle and steering response',
                importance_score=0.5,
                related_features=['drive_modes', 'paddle_shifters', 'sport_suspension'],
                user_benefits=['More engaging driving', 'Better performance', 'Customizable experience'],
                synonyms=['sport', 'performance mode', 'dynamic mode']
            ),

            # Comfort Features
            'leather_seats': VehicleFeature(
                name='Leather Seats',
                category='comfort',
                description='Upholstery made of leather',
                importance_score=0.6,
                related_features=['heated_seats', 'ventilated_seats', 'seat_material'],
                user_benefits=['Premium feel', 'Easy to clean', 'Comfortable in all seasons'],
                synonyms=['leather upholstery', 'leather interior', 'premium seats']
            ),
            'heated_seats': VehicleFeature(
                name='Heated Seats',
                category='comfort',
                description='Seats with built-in heating elements',
                importance_score=0.7,
                related_features=['leather_seats', 'climate_control', 'remote_start'],
                user_benefits=['Comfort in cold weather', 'Relieves back pain', 'Quick warm-up'],
                synonyms=['seat heaters', 'heated seating', 'warm seats']
            ),
            'sunroof': VehicleFeature(
                name='Sunroof',
                category='comfort',
                description='Roof opening that lets in light and air',
                importance_score=0.5,
                related_features=['panoramic_roof', 'moonroof', 'climate_control'],
                user_benefits=['Natural light', 'Fresh air', 'Open feeling'],
                synonyms=['moonroof', 'roof opening', 'glass roof']
            ),
            'dual_zone_climate': VehicleFeature(
                name='Dual Zone Climate Control',
                category='comfort',
                description='Separate temperature controls for driver and passenger',
                importance_score=0.6,
                related_features=['automatic_climate', 'air_conditioning', 'heater'],
                user_benefits=['Personal comfort', 'No temperature arguments', 'Better air distribution'],
                synonyms=['dual climate', 'dual AC', 'separate climate']
            ),

            # Technology Features
            'apple_carplay': VehicleFeature(
                name='Apple CarPlay',
                category='technology',
                description='iPhone integration for apps and navigation',
                importance_score=0.75,
                related_features=['android_auto', 'infotainment', 'touchscreen'],
                user_benefits=['Access to apps', 'Familiar interface', 'Better navigation'],
                synonyms=['CarPlay', 'iPhone integration', 'Apple connectivity']
            ),
            'android_auto': VehicleFeature(
                name='Android Auto',
                category='technology',
                description='Android phone integration',
                importance_score=0.75,
                related_features=['apple_carplay', 'infotainment', 'voice_commands'],
                user_benefits=['Google Maps', 'Music apps', 'Voice control'],
                synonyms=['Google Auto', 'Android integration', 'phone connectivity']
            ),
            'navigation_system': VehicleFeature(
                name='Navigation System',
                category='technology',
                description='Built-in GPS navigation',
                importance_score=0.7,
                related_features=['touchscreen', 'voice_commands', 'traffic_alerts'],
                user_benefits=['Never get lost', 'Real-time traffic', 'Points of interest'],
                synonyms=['GPS', 'nav system', 'built-in navigation']
            ),
            'backup_camera': VehicleFeature(
                name='Backup Camera',
                category='technology',
                description='Camera showing view behind vehicle when reversing',
                importance_score=0.85,
                related_features=['parking_sensors', '360_camera', 'parking_assist'],
                user_benefits=['Prevents backing accidents', 'Easy parking', 'Safety feature'],
                synonyms=['rear_camera', 'rear_view_camera', 'reversing_camera']
            ),

            # Efficiency Features
            'hybrid_system': VehicleFeature(
                name='Hybrid System',
                category='efficiency',
                description='Combines gasoline engine with electric motor',
                importance_score=0.8,
                related_features=['fuel_efficiency', 'regenerative_braking', 'eco_mode'],
                user_benefits=['Better gas mileage', 'Lower emissions', 'Quieter operation'],
                synonyms=['hybrid', 'gas-electric', 'HEV']
            ),
            'start_stop_technology': VehicleFeature(
                name='Start-Stop Technology',
                category='efficiency',
                description='Automatically shuts off engine when stopped',
                importance_score=0.5,
                related_features=['fuel_efficiency', 'hybrid_system', 'eco_mode'],
                user_benefits=['Saves fuel in traffic', 'Reduced emissions', 'Modern feature'],
                synonyms=['auto start-stop', 'idle stop', 'engine stop-start']
            ),
            'eco_mode': VehicleFeature(
                name='Eco Mode',
                category='efficiency',
                description='Optimizes systems for maximum efficiency',
                importance_score=0.5,
                related_features=['fuel_efficiency', 'drive_modes', 'hybrid_system'],
                user_benefits=['Better gas mileage', 'Reduced wear', 'Environmentally friendly'],
                synonyms=['economy mode', 'green mode', 'efficiency mode']
            ),
            'cylinder_deactivation': VehicleFeature(
                name='Cylinder Deactivation',
                category='efficiency',
                description='Shuts off cylinders during light loads',
                importance_score=0.4,
                related_features=['fuel_efficiency', 'engine_performance', 'V8_engine'],
                user_benefits=['Improved highway MPG', 'Power when needed', 'Smart technology'],
                synonyms=['active fuel management', 'displacement on demand', 'cylinder shut-off']
            )
        }

    def _build_feature_hierarchy(self) -> Dict[str, Dict[str, List[str]]]:
        """Build hierarchical relationship between features"""
        return {
            'safety': {
                'primary': ['airbags', 'automatic_emergency_braking'],
                'secondary': ['blind_spot_monitoring', 'lane_assist', 'adaptive_cruise_control'],
                'tertiary': ['collision_warning', 'rear_cross_traffic', 'driver_monitoring']
            },
            'performance': {
                'primary': ['all_wheel_drive'],
                'secondary': ['turbo_engine', 'sport_mode'],
                'tertiary': ['paddle_shifters', 'sport_suspension', 'launch_control']
            },
            'comfort': {
                'primary': ['leather_seats'],
                'secondary': ['heated_seats', 'dual_zone_climate'],
                'tertiary': ['sunroof', 'ventilated_seats', 'premium_audio']
            },
            'technology': {
                'primary': ['apple_carplay', 'android_auto'],
                'secondary': ['navigation_system', 'backup_camera'],
                'tertiary': ['voice_commands', 'wireless_charging', 'head_up_display']
            },
            'efficiency': {
                'primary': ['hybrid_system'],
                'secondary': ['start_stop_technology', 'eco_mode'],
                'tertiary': ['cylinder_deactivation', 'regenerative_braking', 'aerodynamics']
            }
        }

    def get_feature(self, name: str) -> Optional[VehicleFeature]:
        """Get feature by name or synonym"""
        # Direct match
        if name in self.features:
            return self.features[name]

        # Check synonyms
        for feature in self.features.values():
            if name.lower() in [s.lower() for s in feature.synonyms]:
                return feature

        return None

    def get_related_features(self, feature_name: str, depth: int = 1) -> List[str]:
        """Get related features based on hierarchy and relationships"""
        feature = self.get_feature(feature_name)
        if not feature:
            return []

        related = set(feature.related_features)

        # Add hierarchical relationships
        if feature.category in self.feature_hierarchy:
            for level, features in self.feature_hierarchy[feature.category].items():
                if feature_name in features:
                    # Add all features at this level and adjacent levels
                    for other_level, other_features in self.feature_hierarchy[feature.category].items():
                        if other_level != level:
                            related.update(other_features)

        return list(related)[:10]  # Limit to 10 related features

    def calculate_feature_importance(self, features: List[str]) -> Dict[str, float]:
        """Calculate importance scores for a list of features"""
        scores = {}

        for feature_name in features:
            feature = self.get_feature(feature_name)
            if feature:
                scores[feature_name] = feature.importance_score

                # Boost related features
                for related in feature.related_features:
                    if related in self.features:
                        scores[related] = max(
                            scores.get(related, 0),
                            feature.importance_score * 0.5
                        )

        return scores


class SemanticUnderstanding:
    """Main service for semantic understanding of vehicles and preferences"""

    def __init__(
        self,
        groq_client: GroqClient,
        taxonomy: Optional[VehicleFeatureTaxonomy] = None
    ):
        self.groq_client = groq_client
        self.taxonomy = taxonomy or VehicleFeatureTaxonomy()
        self.initialized = False

        # Preference weight mappings
        self.preference_weights = {
            'safety': {
                'primary': ['family', 'kids', 'children', 'protect', 'secure', 'peace of mind'],
                'weight': 0.9
            },
            'performance': {
                'primary': ['fast', 'quick', 'powerful', 'sport', 'fun', 'exciting'],
                'weight': 0.8
            },
            'comfort': {
                'primary': ['comfortable', 'luxury', 'premium', 'nice', 'enjoy'],
                'weight': 0.7
            },
            'technology': {
                'primary': ['tech', 'technology', 'smart', 'connected', 'modern'],
                'weight': 0.6
            },
            'efficiency': {
                'primary': ['efficient', 'economy', 'save money', 'mpg', 'gas'],
                'weight': 0.75
            }
        }

    async def initialize(self) -> bool:
        """Initialize the semantic understanding service"""
        try:
            if not self.groq_client.initialized:
                logger.error("Groq client not initialized")
                return False

            self.initialized = True
            logger.info("Semantic understanding service initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize semantic understanding: {e}")
            return False

    async def understand_user_preferences(
        self,
        message: str,
        entities: List[Entity],
        explicit_preferences: List[UserPreference],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> List[PreferenceWeight]:
        """
        Analyze and weight user preferences semantically
        """

        preferences = []

        # Analyze message for implicit preferences
        message_lower = message.lower()

        # Check for category indicators
        for category, config in self.preference_weights.items():
            score = 0
            matched_keywords = []

            for keyword in config['primary']:
                if keyword in message_lower:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                # Normalize score
                confidence = min(score / len(config['primary']), 1.0)
                weight = config['weight'] * confidence

                preferences.append(PreferenceWeight(
                    preference=category,
                    weight=weight,
                    confidence=confidence,
                    source='semantic_analysis',
                    context={
                        'matched_keywords': matched_keywords,
                        'message_context': message_lower
                    }
                ))

        # Enhance with entity-based preferences
        entity_preferences = await self._extract_entity_preferences(entities)
        preferences.extend(entity_preferences)

        # Consider conversation history
        if conversation_context:
            historical_prefs = await self._analyze_historical_preferences(conversation_context)
            preferences.extend(historical_prefs)

        # Consolidate and rank preferences
        preferences = self._consolidate_preferences(preferences)

        return preferences

    async def _extract_entity_preferences(self, entities: List[Entity]) -> List[PreferenceWeight]:
        """Extract preferences from entities"""
        preferences = []

        for entity in entities:
            # Map entity types to preference categories
            if entity.entity_type == EntityType.FEATURE:
                feature = self.taxonomy.get_feature(str(entity.value))
                if feature:
                    preferences.append(PreferenceWeight(
                        preference=f"feature_{feature.category}",
                        weight=feature.importance_score * entity.confidence,
                        confidence=entity.confidence,
                        source='entity_extraction',
                        context={'feature_name': feature.name}
                    ))

            elif entity.entity_type == EntityType.VEHICLE_TYPE:
                # Infer preferences from vehicle type
                if str(entity.value).lower() in ['suv', 'truck']:
                    preferences.append(PreferenceWeight(
                        preference='space_utility',
                        weight=0.7 * entity.confidence,
                        confidence=entity.confidence,
                        source='vehicle_type_inference',
                        context={'vehicle_type': entity.value}
                    ))
                elif str(entity.value).lower() in ['electric', 'hybrid']:
                    preferences.append(PreferenceWeight(
                        preference='efficiency',
                        weight=0.8 * entity.confidence,
                        confidence=entity.confidence,
                        source='vehicle_type_inference',
                        context={'vehicle_type': entity.value}
                    ))

        return preferences

    async def _analyze_historical_preferences(
        self,
        context: Dict[str, Any]
    ) -> List[PreferenceWeight]:
        """Analyze preferences from conversation history"""
        preferences = []

        # This would analyze past conversations to identify patterns
        # For now, return empty list
        return preferences

    def _consolidate_preferences(
        self,
        preferences: List[PreferenceWeight]
    ) -> List[PreferenceWeight]:
        """Consolidate and deduplicate preferences"""
        consolidated = {}

        for pref in preferences:
            key = pref.preference
            if key not in consolidated:
                consolidated[key] = pref
            else:
                # Combine weights
                existing = consolidated[key]
                combined_weight = (existing.weight + pref.weight) / 2
                combined_confidence = max(existing.confidence, pref.confidence)

                # Prefer explicit sources
                if pref.source == 'explicit' and existing.source != 'explicit':
                    source = pref.source
                    context = pref.context
                else:
                    source = existing.source
                    context = existing.context

                consolidated[key] = PreferenceWeight(
                    preference=key,
                    weight=combined_weight,
                    confidence=combined_confidence,
                    source=source,
                    context=context
                )

        # Sort by weight
        return sorted(consolidated.values(), key=lambda p: p.weight, reverse=True)

    async def match_vehicle_to_preferences(
        self,
        vehicle: Dict[str, Any],
        preferences: List[PreferenceWeight]
    ) -> SemanticMatch:
        """
        Match a vehicle against user preferences
        """

        matched_features = []
        mismatched_features = []
        total_score = 0
        max_score = 0

        # Extract vehicle features
        vehicle_features = vehicle.get('features', [])
        if isinstance(vehicle_features, str):
            vehicle_features = [vehicle_features]

        # Check each preference category
        for pref in preferences:
            if pref.preference.startswith('feature_'):
                # Direct feature preference
                category = pref.preference.replace('feature_', '')
                category_features = self.taxonomy.feature_hierarchy.get(category, {})

                for level, features in category_features.items():
                    weight_multiplier = 1.0 if level == 'primary' else 0.7 if level == 'secondary' else 0.4
                    for feature in features:
                        max_score += pref.weight * weight_multiplier

                        if any(feature.lower() in vf.lower() for vf in vehicle_features):
                            matched_features.append(feature)
                            total_score += pref.weight * weight_multiplier
                        else:
                            mismatched_features.append(feature)

            elif pref.preference == 'space_utility':
                # Check for space-related features
                space_features = ['cargo_space', 'third_row', 'suv', 'minivan', 'wagon']
                max_score += pref.weight

                if any(feature in vehicle for feature in space_features):
                    matched_features.extend(space_features)
                    total_score += pref.weight
                else:
                    mismatched_features.extend(space_features)

            elif pref.preference == 'efficiency':
                # Check for efficiency features
                eff_features = ['hybrid', 'electric', 'highway_mpg', 'fuel_efficient']
                max_score += pref.weight

                vehicle_text = str(vehicle).lower()
                if any(feature in vehicle_text for feature in eff_features):
                    matched_features.extend(eff_features)
                    total_score += pref.weight
                else:
                    mismatched_features.extend(eff_features)

        # Calculate normalized score
        final_score = total_score / max_score if max_score > 0 else 0

        # Generate explanation
        explanation = await self._generate_match_explanation(
            vehicle,
            matched_features,
            mismatched_features,
            final_score
        )

        return SemanticMatch(
            vehicle_id=str(vehicle.get('id', vehicle.get('vin', 'unknown'))),
            match_score=final_score,
            matched_features=list(set(matched_features)),
            mismatched_features=list(set(mismatched_features)),
            explanation=explanation
        )

    async def _generate_match_explanation(
        self,
        vehicle: Dict[str, Any],
        matched: List[str],
        mismatched: List[str],
        score: float
    ) -> str:
        """Generate human-readable explanation of match"""

        vehicle_name = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip()

        if score > 0.8:
            explanation = f"Excellent match! The {vehicle_name} has most features you're looking for. "
            if matched:
                explanation += f"Key matches include: {', '.join(matched[:3])}."
        elif score > 0.6:
            explanation = f"Good match! The {vehicle_name} has many features you want. "
            if matched:
                explanation += f"You'll especially like: {', '.join(matched[:3])}."
            if mismatched:
                explanation += f" Note that it doesn't have: {', '.join(mismatched[:2])}."
        else:
            explanation = f"The {vehicle_name} might not be the best fit. "
            if matched:
                explanation += f"It does have: {', '.join(matched[:2])}, "
            explanation += "but you might want to consider other options that better match your preferences."

        return explanation

    async def explain_feature_benefit(
        self,
        feature_name: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Explain a feature's benefits in user-friendly language"""

        feature = self.taxonomy.get_feature(feature_name)
        if not feature:
            return f"I don't have information about '{feature_name}'. Let me help you with something else."

        # Generate contextual explanation
        explanation = f"{feature.name} is a great feature! {feature.description}. "

        # Add user benefits
        if feature.user_benefits:
            benefits = feature.user_benefits[:2]  # Top 2 benefits
            explanation += f"This means you get {benefits[0].lower()} and {benefits[1].lower()}. "

        # Add contextual benefit based on user
        if user_context:
            if 'family' in str(user_context).lower() and feature.category == 'safety':
                explanation += "For families, this feature provides extra peace of mind knowing your loved ones are protected. "
            elif 'commute' in str(user_context).lower() and feature.category == 'comfort':
                explanation += "This makes your daily commute much more comfortable and enjoyable. "

        # Add related features
        if feature.related_features:
            explanation += f"It often comes with related features like {', '.join(feature.related_features[:2])}."

        return explanation

    async def compare_features(
        self,
        feature1: str,
        feature2: str
    ) -> Dict[str, Any]:
        """Compare two features"""

        f1 = self.taxonomy.get_feature(feature1)
        f2 = self.taxonomy.get_feature(feature2)

        if not f1 or not f2:
            return {
                'error': f"Could not find one or both features: {feature1}, {feature2}"
            }

        comparison = {
            'feature1': {
                'name': f1.name,
                'category': f1.category,
                'importance': f1.importance_score,
                'benefits': f1.user_benefits
            },
            'feature2': {
                'name': f2.name,
                'category': f2.category,
                'importance': f2.importance_score,
                'benefits': f2.user_benefits
            },
            'similarities': [],
            'differences': []
        }

        # Find similarities
        if f1.category == f2.category:
            comparison['similarities'].append(f"Both are {f1.category} features")

        common_benefits = set(f1.user_benefits) & set(f2.user_benefits)
        if common_benefits:
            comparison['similarities'].append(f"Both provide: {', '.join(common_benefits)}")

        # Find differences
        if f1.importance_score != f2.importance_score:
            more_important = f1 if f1.importance_score > f2.importance_score else f2
            comparison['differences'].append(
                f"{more_important.name} is generally considered more important "
                f"({more_important.importance_score:.0%} vs "
                f"{min(f1.importance_score, f2.importance_score):.0%})"
            )

        return comparison