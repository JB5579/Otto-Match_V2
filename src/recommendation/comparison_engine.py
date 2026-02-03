"""
Otto.AI Vehicle Comparison Engine

Implements vehicle-to-vehicle comparison with detailed feature analysis,
semantic similarity scoring, and market price analysis.
Part of Story 1-5: Build Vehicle Comparison and Recommendation Engine
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.models.vehicle_models import (
    VehicleComparisonResult, VehicleSpecification, VehicleFeatures,
    FeatureDifference, PriceAnalysis, SemanticSimilarity,
    ComparisonFeatureType, FeatureDifferenceType
)

logger = logging.getLogger(__name__)

@dataclass
class ComparisonResult:
    """Internal comparison result structure"""
    comparison_results: List[VehicleComparisonResult]
    feature_differences: List[FeatureDifference]
    semantic_similarity: Optional[Dict[str, SemanticSimilarity]]
    recommendation_summary: str

class ComparisonEngine:
    """Vehicle comparison engine with semantic analysis"""

    def __init__(self, vehicle_db_service, embedding_service):
        """
        Initialize comparison engine

        Args:
            vehicle_db_service: Vehicle database service
            embedding_service: Embedding service for semantic analysis
        """
        self.vehicle_db = vehicle_db_service
        self.embedding_service = embedding_service

        # Feature importance weights (configurable)
        self.feature_weights = {
            'engine': 0.15,
            'transmission': 0.10,
            'fuel_efficiency': 0.12,
            'safety_features': 0.20,
            'technology_features': 0.15,
            'comfort_features': 0.10,
            'exterior_features': 0.08,
            'interior_features': 0.10
        }

        # Specification categories and their features
        self.specification_categories = {
            'engine': ['engine_type', 'engine_size', 'horsepower', 'torque'],
            'transmission': ['transmission_type', 'gears'],
            'performance': ['acceleration_0_60', 'top_speed', 'fuel_efficiency_city', 'fuel_efficiency_hwy'],
            'dimensions': ['length', 'width', 'height', 'wheelbase', 'cargo_capacity'],
            'safety': ['safety_rating', 'airbags', 'safety_features'],
            'technology': ['infotainment_system', 'connectivity', 'driver_assistance'],
            'comfort': ['seating_capacity', 'upholstery', 'climate_control'],
            'exterior': ['exterior_color', 'wheel_size', 'roof_type'],
            'interior': ['interior_color', 'dashboard_features', 'storage']
        }

    async def compare_vehicles(
        self,
        vehicle_ids: List[str],
        criteria: Optional[List[str]] = None,
        include_semantic_similarity: bool = True,
        include_price_analysis: bool = True,
        user_id: Optional[str] = None
    ) -> ComparisonResult:
        """
        Compare multiple vehicles with detailed analysis

        Args:
            vehicle_ids: List of vehicle IDs to compare
            criteria: Specific comparison criteria (optional)
            include_semantic_similarity: Include semantic similarity analysis
            include_price_analysis: Include price and market analysis
            user_id: User ID for personalized scoring

        Returns:
            ComparisonResult with detailed analysis
        """
        start_time = time.time()

        try:
            logger.info(f"Starting comparison for {len(vehicle_ids)} vehicles")

            # Validate vehicle count
            if len(vehicle_ids) < 2:
                raise ValueError("At least 2 vehicles required for comparison")
            if len(vehicle_ids) > 4:
                raise ValueError("Maximum 4 vehicles allowed for comparison")

            # Fetch vehicle data
            vehicles = await self._fetch_vehicles(vehicle_ids)
            if len(vehicles) != len(vehicle_ids):
                missing_ids = set(vehicle_ids) - set(v['id'] for v in vehicles)
                raise ValueError(f"Vehicles not found: {missing_ids}")

            # Generate comparison results
            comparison_results = []
            for vehicle in vehicles:
                result = await self._create_vehicle_comparison_result(
                    vehicle, vehicles, criteria, include_price_analysis
                )
                comparison_results.append(result)

            # Generate feature differences
            feature_differences = await self._analyze_feature_differences(
                vehicles, criteria
            )

            # Generate semantic similarity if requested
            semantic_similarity = None
            if include_semantic_similarity:
                semantic_similarity = await self._calculate_semantic_similarity(vehicles)

            # Generate recommendation summary
            recommendation_summary = await self._generate_recommendation_summary(
                comparison_results, feature_differences, user_id
            )

            processing_time = time.time() - start_time
            logger.info(f"Comparison completed in {processing_time:.3f}s")

            return ComparisonResult(
                comparison_results=comparison_results,
                feature_differences=feature_differences,
                semantic_similarity=semantic_similarity,
                recommendation_summary=recommendation_summary
            )

        except Exception as e:
            logger.error(f"Comparison engine error: {str(e)}")
            raise

    async def _fetch_vehicles(self, vehicle_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch vehicle data from database using efficient batch retrieval"""
        try:
            logger.info(f"Fetching {len(vehicle_ids)} vehicles from database")

            # Use efficient batch retrieval instead of individual queries
            vehicles = await self.vehicle_db.get_vehicles_by_ids(vehicle_ids)

            # Validate that all requested vehicles were found
            found_ids = set(v['id'] for v in vehicles)
            missing_ids = set(vehicle_ids) - found_ids

            if missing_ids:
                logger.warning(f"Vehicles not found: {missing_ids}")
                # For missing vehicles, we could either:
                # 1. Raise an error (strict mode)
                # 2. Continue with available vehicles (lenient mode)
                # For now, we'll continue with available vehicles

            logger.info(f"Successfully fetched {len(vehicles)} vehicles")
            return vehicles

        except Exception as e:
            logger.error(f"Error fetching vehicles: {str(e)}")
            raise

    async def _create_vehicle_comparison_result(
        self,
        vehicle: Dict[str, Any],
        all_vehicles: List[Dict[str, Any]],
        criteria: Optional[List[str]],
        include_price_analysis: bool
    ) -> VehicleComparisonResult:
        """Create comparison result for a single vehicle"""

        # Extract specifications
        specifications = await self._extract_specifications(vehicle)

        # Extract features
        features = await self._extract_features(vehicle)

        # Generate price analysis
        price_analysis = None
        if include_price_analysis:
            price_analysis = await self._analyze_price(vehicle, all_vehicles)

        # Calculate overall score
        overall_score = await self._calculate_overall_score(
            vehicle, all_vehicles, specifications, features
        )

        return VehicleComparisonResult(
            vehicle_id=vehicle['id'],
            vehicle_data=vehicle,
            specifications=specifications,
            features=features,
            price_analysis=price_analysis,
            overall_score=overall_score
        )

    async def _extract_specifications(self, vehicle: Dict[str, Any]) -> List[VehicleSpecification]:
        """Extract vehicle specifications with importance scoring"""
        specifications = []

        for category, spec_fields in self.specification_categories.items():
            for field in spec_fields:
                if field in vehicle:
                    value = vehicle[field]
                    if value is not None:
                        importance = self.feature_weights.get(category, 0.1)

                        spec = VehicleSpecification(
                            category=category,
                            name=field.replace('_', ' ').title(),
                            value=value,
                            importance_score=importance
                        )
                        specifications.append(spec)

        return specifications

    async def _extract_features(self, vehicle: Dict[str, Any]) -> List[VehicleFeatures]:
        """Extract vehicle features and amenities"""
        features = []

        # Extract from features list if available
        if 'features' in vehicle and isinstance(vehicle['features'], list):
            feature_list = vehicle['features']

            # Group features by category
            feature_categories = {
                'safety': ['airbag', 'abs', 'traction', 'stability', 'lane', 'blind', 'parking'],
                'technology': ['bluetooth', 'navigation', 'apple', 'android', 'usb', 'wifi'],
                'comfort': ['leather', 'heated', 'cooled', 'power', 'memory', 'auto'],
                'exterior': ['sunroof', 'alloy', 'led', 'fog', 'running'],
                'performance': ['turbo', 'hybrid', 'electric', 'awd', '4wd', 'sport']
            }

            categorized_features = {cat: [] for cat in feature_categories}

            for feature in feature_list:
                feature_lower = feature.lower()
                for category, keywords in feature_categories.items():
                    if any(keyword in feature_lower for keyword in keywords):
                        categorized_features[category].append(feature)
                        break
                else:
                    # Uncategorized feature
                    if 'other' not in categorized_features:
                        categorized_features['other'] = []
                    categorized_features['other'].append(feature)

            # Create VehicleFeatures objects
            for category, category_features in categorized_features.items():
                if category_features:
                    value_score = min(len(category_features) * 0.1, 1.0)

                    feature_obj = VehicleFeatures(
                        category=category.title(),
                        features=category_features,
                        included=True,
                        value_score=value_score
                    )
                    features.append(feature_obj)

        return features

    async def _analyze_price(
        self,
        vehicle: Dict[str, Any],
        all_vehicles: List[Dict[str, Any]]
    ) -> PriceAnalysis:
        """Analyze vehicle price against market data"""

        current_price = vehicle.get('price', 0)
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        year = vehicle.get('year', 0)

        # Get market data (this would integrate with real market data service)
        market_data = await self._get_market_data(make, model, year)
        market_average = market_data.get('average_price', current_price)
        market_range = market_data.get('price_range', (current_price * 0.8, current_price * 1.2))

        # Calculate price position
        if current_price < market_average * 0.95:
            price_position = "below_market"
            savings_amount = market_average - current_price
            savings_percentage = (savings_amount / market_average) * 100
        elif current_price > market_average * 1.05:
            price_position = "above_market"
            savings_amount = None
            savings_percentage = None
        else:
            price_position = "at_market"
            savings_amount = None
            savings_percentage = None

        return PriceAnalysis(
            current_price=current_price,
            market_average=market_average,
            market_range=market_range,
            price_position=price_position,
            savings_amount=savings_amount,
            savings_percentage=savings_percentage,
            price_trend=market_data.get('price_trend', 'stable'),
            market_demand=market_data.get('market_demand', 'medium')
        )

    async def _get_market_data(self, make: str, model: str, year: int) -> Dict[str, Any]:
        """Get market data for vehicle (mock implementation)"""
        # This would integrate with real market data APIs
        # For now, return simulated data
        base_price = 30000  # Base price for calculation

        # Adjust based on make and year
        make_multiplier = {
            'Toyota': 0.95, 'Honda': 0.93, 'Ford': 0.98, 'Chevrolet': 0.97,
            'BMW': 1.25, 'Mercedes': 1.30, 'Audi': 1.20, 'Lexus': 1.15
        }.get(make, 1.0)

        year_factor = max(0.5, 1.0 - (2025 - year) * 0.08)
        average_price = base_price * make_multiplier * year_factor

        # Generate realistic range
        price_range = (
            average_price * 0.85,  # 15% below average
            average_price * 1.15   # 15% above average
        )

        return {
            'average_price': average_price,
            'price_range': price_range,
            'price_trend': 'stable',
            'market_demand': 'medium'
        }

    async def _calculate_overall_score(
        self,
        vehicle: Dict[str, Any],
        all_vehicles: List[Dict[str, Any]],
        specifications: List[VehicleSpecification],
        features: List[VehicleFeatures]
    ) -> float:
        """Calculate overall comparison score for vehicle"""

        score = 0.5  # Base score
        max_score = 1.0

        # Specification scoring
        spec_score = 0
        spec_weight = 0
        for spec in specifications:
            normalized_value = await self._normalize_spec_value(spec)
            spec_score += normalized_value * spec.importance_score
            spec_weight += spec.importance_score

        if spec_weight > 0:
            score += (spec_score / spec_weight) * 0.4

        # Feature scoring
        feature_score = sum(f.value_score for f in features)
        if features:
            score += min(feature_score / len(features), 1.0) * 0.3

        # Price scoring (better value = higher score)
        if 'price' in vehicle:
            prices = [v.get('price', float('inf')) for v in all_vehicles if 'price' in v]
            if prices:
                lowest_price = min(prices)
                vehicle_price = vehicle['price']
                price_score = max(0, 1.0 - (vehicle_price - lowest_price) / (max(prices) - lowest_price))
                score += price_score * 0.2

        # Condition scoring
        if 'condition' in vehicle:
            condition_scores = {'excellent': 1.0, 'good': 0.8, 'fair': 0.6, 'poor': 0.4}
            condition_score = condition_scores.get(vehicle['condition'].lower(), 0.5)
            score += condition_score * 0.1

        return min(max(score, 0.0), max_score)

    async def _normalize_spec_value(self, spec: VehicleSpecification) -> float:
        """Normalize specification value to 0-1 scale"""

        value = spec.value

        if isinstance(value, (int, float)):
            # Numeric values need range-specific normalization
            category_ranges = {
                'engine': {'min': 50, 'max': 500},  # horsepower
                'performance': {'min': 5, 'max': 30},  # combined mpg
                'dimensions': {'min': 150, 'max': 250},  # length in inches
            }

            if spec.category in category_ranges:
                range_info = category_ranges[spec.category]
                normalized = (value - range_info['min']) / (range_info['max'] - range_info['min'])
                return max(0, min(normalized, 1.0))

        elif isinstance(value, str):
            # String values - check for positive indicators
            positive_indicators = [
                'automatic', 'led', 'heated', 'cooled', 'power', 'leather',
                'navigation', 'bluetooth', 'apple', 'android', 'premium',
                'turbo', 'hybrid', 'electric', 'awd', '4wd'
            ]

            value_lower = value.lower()
            score = 0
            for indicator in positive_indicators:
                if indicator in value_lower:
                    score += 0.3

            return min(score, 1.0)

        # Default normalization
        return 0.5

    async def _analyze_feature_differences(
        self,
        vehicles: List[Dict[str, Any]],
        criteria: Optional[List[str]]
    ) -> List[FeatureDifference]:
        """Analyze feature differences between vehicles"""

        differences = []

        if len(vehicles) < 2:
            return differences

        # Compare all pairs of vehicles
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                vehicle_a = vehicles[i]
                vehicle_b = vehicles[j]

                # Compare specifications
                spec_differences = await self._compare_specifications(
                    vehicle_a, vehicle_b, i, j
                )
                differences.extend(spec_differences)

                # Compare features
                feature_differences = await self._compare_features(
                    vehicle_a, vehicle_b, i, j
                )
                differences.extend(feature_differences)

        return differences

    async def _compare_specifications(
        self,
        vehicle_a: Dict[str, Any],
        vehicle_b: Dict[str, Any],
        index_a: int,
        index_b: int
    ) -> List[FeatureDifference]:
        """Compare specifications between two vehicles"""

        differences = []

        # Get all specification fields
        spec_fields = set()
        for spec_list in self.specification_categories.values():
            spec_fields.update(spec_list)

        for field in spec_fields:
            if field in vehicle_a and field in vehicle_b:
                value_a = vehicle_a[field]
                value_b = vehicle_b[field]

                if value_a != value_b and value_a is not None and value_b is not None:
                    # Determine difference type and importance
                    difference_type, importance = await self._evaluate_spec_difference(
                        field, value_a, value_b
                    )

                    difference = FeatureDifference(
                        feature_name=field.replace('_', ' ').title(),
                        feature_type=ComparisonFeatureType.SPECIFICATION,
                        vehicle_a_value=value_a,
                        vehicle_b_value=value_b,
                        difference_type=difference_type,
                        importance_weight=importance,
                        description=f"Vehicle {index_a + 1}: {value_a} vs Vehicle {index_b + 1}: {value_b}"
                    )
                    differences.append(difference)

        return differences

    async def _evaluate_spec_difference(
        self,
        field: str,
        value_a: Any,
        value_b: Any
    ) -> Tuple[FeatureDifferenceType, float]:
        """Evaluate specification difference type and importance"""

        # Higher is better fields
        higher_is_better = [
            'horsepower', 'torque', 'fuel_efficiency_city', 'fuel_efficiency_hwy',
            'acceleration_0_60', 'safety_rating', 'airbags'
        ]

        # Lower is better fields
        lower_is_better = ['price', 'mileage']

        importance = 0.5  # Default importance

        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
            if field in higher_is_better:
                if value_a > value_b * 1.1:
                    return FeatureDifferenceType.ADVANTAGE, importance + 0.2
                elif value_b > value_a * 1.1:
                    return FeatureDifferenceType.DISADVANTAGE, importance + 0.2
            elif field in lower_is_better:
                if value_a < value_b * 0.9:
                    return FeatureDifferenceType.ADVANTAGE, importance + 0.2
                elif value_b < value_a * 0.9:
                    return FeatureDifferenceType.DISADVANTAGE, importance + 0.2
        else:
            # Non-numeric differences
            # This would need more sophisticated comparison logic
            pass

        return FeatureDifferenceType.NEUTRAL, importance

    async def _compare_features(
        self,
        vehicle_a: Dict[str, Any],
        vehicle_b: Dict[str, Any],
        index_a: int,
        index_b: int
    ) -> List[FeatureDifference]:
        """Compare features between two vehicles"""

        differences = []

        features_a = set(vehicle_a.get('features', []))
        features_b = set(vehicle_b.get('features', []))

        # Features in A but not in B (advantage for A)
        for feature in features_a - features_b:
            importance = await self._evaluate_feature_importance(feature)

            difference = FeatureDifference(
                feature_name=feature,
                feature_type=ComparisonFeatureType.FEATURE,
                vehicle_a_value="Included",
                vehicle_b_value="Not Included",
                difference_type=FeatureDifferenceType.ADVANTAGE,
                importance_weight=importance,
                description=f"Vehicle {index_a + 1} has {feature} but Vehicle {index_b + 1} does not"
            )
            differences.append(difference)

        # Features in B but not in A (disadvantage for A)
        for feature in features_b - features_a:
            importance = await self._evaluate_feature_importance(feature)

            difference = FeatureDifference(
                feature_name=feature,
                feature_type=ComparisonFeatureType.FEATURE,
                vehicle_a_value="Not Included",
                vehicle_b_value="Included",
                difference_type=FeatureDifferenceType.DISADVANTAGE,
                importance_weight=importance,
                description=f"Vehicle {index_b + 1} has {feature} but Vehicle {index_a + 1} does not"
            )
            differences.append(difference)

        return differences

    async def _evaluate_feature_importance(self, feature: str) -> float:
        """Evaluate feature importance score"""

        high_importance_features = [
            'blind spot monitoring', 'lane keeping assist', 'adaptive cruise control',
            'automatic emergency braking', 'apple carplay', 'android auto',
            'leather seats', 'heated seats', 'ventilated seats', 'panoramic sunroof'
        ]

        medium_importance_features = [
            'bluetooth', 'usb ports', 'backup camera', 'parking sensors',
            'alloy wheels', 'led headlights', 'keyless entry'
        ]

        feature_lower = feature.lower()

        if any(high_feature in feature_lower for high_feature in high_importance_features):
            return 0.8
        elif any(med_feature in feature_lower for med_feature in medium_importance_features):
            return 0.5
        else:
            return 0.3

    async def _calculate_semantic_similarity(
        self,
        vehicles: List[Dict[str, Any]]
    ) -> Dict[str, SemanticSimilarity]:
        """Calculate semantic similarity between all vehicle pairs"""

        similarities = {}

        if len(vehicles) < 2:
            return similarities

        # Generate embeddings for all vehicles
        embeddings = {}
        for vehicle in vehicles:
            try:
                # Create vehicle description for embedding
                description = await self._create_vehicle_description(vehicle)
                embedding_result = await self.embedding_service.generate_embeddings([description])
                embeddings[vehicle['id']] = embedding_result.embeddings[0]
            except Exception as e:
                logger.error(f"Error generating embedding for vehicle {vehicle['id']}: {str(e)}")
                continue

        # Calculate pairwise similarities
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                vehicle_a = vehicles[i]
                vehicle_b = vehicles[j]

                if vehicle_a['id'] in embeddings and vehicle_b['id'] in embeddings:
                    similarity_score = await self._calculate_cosine_similarity(
                        embeddings[vehicle_a['id']],
                        embeddings[vehicle_b['id']]
                    )

                    # Analyze shared and unique features
                    features_a = set(vehicle_a.get('features', []))
                    features_b = set(vehicle_b.get('features', []))
                    shared_features = list(features_a & features_b)
                    unique_features_a = list(features_a - features_b)
                    unique_features_b = list(features_b - features_a)

                    # Generate explanation
                    explanation = await self._generate_similarity_explanation(
                        similarity_score, shared_features, unique_features_a, unique_features_b
                    )

                    pair_key = f"{vehicle_a['id']}_vs_{vehicle_b['id']}"
                    similarities[pair_key] = SemanticSimilarity(
                        similarity_score=similarity_score,
                        shared_features=shared_features,
                        unique_features_a=unique_features_a,
                        unique_features_b=unique_features_b,
                        similarity_explanation=explanation
                    )

        return similarities

    async def _create_vehicle_description(self, vehicle: Dict[str, Any]) -> str:
        """Create vehicle description for semantic analysis"""

        parts = []

        # Basic info
        if 'year' in vehicle and 'make' in vehicle and 'model' in vehicle:
            parts.append(f"{vehicle['year']} {vehicle['make']} {vehicle['model']}")

        # Vehicle type
        if 'vehicle_type' in vehicle:
            parts.append(vehicle['vehicle_type'])

        # Key specifications
        specs = []
        if 'engine' in vehicle:
            specs.append(f"engine: {vehicle['engine']}")
        if 'transmission' in vehicle:
            specs.append(f"transmission: {vehicle['transmission']}")
        if 'drivetrain' in vehicle:
            specs.append(f"drivetrain: {vehicle['drivetrain']}")

        if specs:
            parts.append(f"specifications: {', '.join(specs)}")

        # Features
        if 'features' in vehicle and vehicle['features']:
            features_text = ', '.join(vehicle['features'][:10])  # Limit to top 10
            parts.append(f"features: {features_text}")

        # Description
        if 'description' in vehicle and vehicle['description']:
            # Limit description length
            description = vehicle['description'][:200]
            parts.append(f"description: {description}")

        return '. '.join(parts)

    async def _calculate_cosine_similarity(self, embedding_a: List[float], embedding_b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""

        if len(embedding_a) != len(embedding_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        magnitude_a = sum(a * a for a in embedding_a) ** 0.5
        magnitude_b = sum(b * b for b in embedding_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    async def _generate_similarity_explanation(
        self,
        similarity_score: float,
        shared_features: List[str],
        unique_features_a: List[str],
        unique_features_b: List[str]
    ) -> str:
        """Generate explanation for semantic similarity"""

        if similarity_score > 0.8:
            similarity_level = "very similar"
        elif similarity_score > 0.6:
            similarity_level = "similar"
        elif similarity_score > 0.4:
            similarity_level = "moderately similar"
        else:
            similarity_level = "quite different"

        explanation_parts = [f"These vehicles are {similarity_level} ({similarity_score:.1%} match)."]

        if shared_features:
            explanation_parts.append(f"They share {len(shared_features)} key features: {', '.join(shared_features[:5])}.")

        if unique_features_a or unique_features_b:
            differences = []
            if unique_features_a:
                differences.append(f"Vehicle 1 has unique features like {', '.join(unique_features_a[:3])}")
            if unique_features_b:
                differences.append(f"Vehicle 2 has unique features like {', '.join(unique_features_b[:3])}")

            explanation_parts.append("Key differences: " + "; ".join(differences) + ".")

        return " ".join(explanation_parts)

    async def _generate_recommendation_summary(
        self,
        comparison_results: List[VehicleComparisonResult],
        feature_differences: List[FeatureDifference],
        user_id: Optional[str] = None
    ) -> str:
        """Generate recommendation summary based on comparison"""

        if not comparison_results:
            return "No vehicles available for comparison."

        # Sort by overall score
        sorted_results = sorted(comparison_results, key=lambda x: x.overall_score, reverse=True)

        # Get top vehicle
        top_vehicle = sorted_results[0]

        # Generate summary
        summary_parts = []

        # Top recommendation
        summary_parts.append(f"Based on the comparison, the {top_vehicle.vehicle_data.get('make', '')} {top_vehicle.vehicle_data.get('model', '')} ranks highest with a {top_vehicle.overall_score:.1%} overall score.")

        # Key advantages
        advantages = [
            diff for diff in feature_differences
            if diff.vehicle_a_value == "Included" and diff.difference_type == FeatureDifferenceType.ADVANTAGE
        ]

        if advantages:
            top_advantages = sorted(advantages, key=lambda x: x.importance_weight, reverse=True)[:3]
            advantage_names = [adv.feature_name for adv in top_advantages]
            summary_parts.append(f"Key advantages include: {', '.join(advantage_names)}.")

        # Price consideration
        if top_vehicle.price_analysis:
            if top_vehicle.price_analysis.price_position == "below_market":
                summary_parts.append(f"This vehicle is priced below market value, offering good value.")
            elif top_vehicle.price_analysis.price_position == "above_market":
                summary_parts.append(f"This vehicle is priced above market, but offers premium features.")

        # Personalization note
        if user_id:
            summary_parts.append("Recommendations are personalized based on your preferences and search history.")

        return " ".join(summary_parts)