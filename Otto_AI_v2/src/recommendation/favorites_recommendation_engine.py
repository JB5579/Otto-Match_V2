"""
Otto.AI Favorites Recommendation Engine

Implements Story 1.6: Vehicle Favorites and Notifications (Technical Notes)
Recommendation engine for suggesting alternatives when favorites become unavailable

Features:
- Semantic search for similar vehicles using RAG-Anything
- Preference-based filtering and ranking
- Fallback suggestions when favorites become unavailable
- User preference learning and adaptation
- Recommendation template generation
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

@dataclass
class VehicleSimilarityScore:
    """Vehicle similarity score data model"""
    vehicle_id: str
    similarity_score: float
    match_reasons: List[str]
    price_difference: Optional[float]
    feature_matches: List[str]
    location_distance: Optional[float]

@dataclass
class RecommendationRequest:
    """Recommendation request data model"""
    user_id: str
    unavailable_vehicle_id: str
    original_vehicle_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    max_recommendations: int = 5
    include_price_range: bool = True
    include_location: bool = True

@dataclass
class Recommendation:
    """Vehicle recommendation data model"""
    vehicle_id: str
    vehicle_data: Dict[str, Any]
    similarity_score: float
    match_reasons: List[str]
    confidence_score: float
    price_comparison: Optional[Dict[str, Any]]
    location_comparison: Optional[Dict[str, Any]]
    recommendation_type: str  # similar_make_model, similar_price, similar_features, user_preference

class FavoritesRecommendationEngine:
    """
    Service for generating vehicle recommendations when favorites become unavailable
    """

    def __init__(self):
        """Initialize recommendation engine"""
        self.db_conn = None
        self.rag_service = None
        self.min_similarity_threshold = 0.6
        self.price_tolerance_percent = 20.0
        self.location_tolerance_km = 100.0

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection and external services

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous key

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to Supabase
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)

            logger.info("✅ Favorites Recommendation Engine connected to Supabase")

            # Initialize RAG-Anything service
            await self._initialize_rag_service()

            # Create recommendation tracking tables
            await self._create_recommendation_tables()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Favorites Recommendation Engine: {e}")
            return False

    async def _initialize_rag_service(self) -> None:
        """Initialize RAG-Anything service for semantic search"""
        try:
            # Import and initialize RAG-Anything
            from raganything import RAGAnything

            self.rag_service = RAGAnything()
            logger.info("✅ RAG-Anything service initialized")

        except ImportError:
            logger.warning("⚠️ RAG-Anything not available, falling back to database search")
            self.rag_service = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG-Anything: {e}")
            self.rag_service = None

    async def _create_recommendation_tables(self) -> None:
        """Create recommendation tracking tables"""
        try:
            with self.db_conn.cursor() as cur:
                # Create recommendations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vehicle_recommendations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        unavailable_vehicle_id VARCHAR(255) NOT NULL,
                        recommended_vehicle_id VARCHAR(255) NOT NULL,
                        similarity_score DECIMAL(5,4),
                        match_reasons TEXT[],
                        confidence_score DECIMAL(5,4),
                        recommendation_type VARCHAR(50),
                        user_interacted BOOLEAN DEFAULT false,
                        interaction_type VARCHAR(50),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_recommendations_user_id (user_id),
                        INDEX idx_recommendations_unavailable_vehicle (unavailable_vehicle_id),
                        INDEX idx_recommendations_created_at (created_at)
                    );
                """)

                # Create user preference learning table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommendation_feedback (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_id VARCHAR(255) NOT NULL,
                        recommendation_id UUID REFERENCES vehicle_recommendations(id),
                        feedback_type VARCHAR(50), -- clicked, favorited, dismissed, converted
                        feedback_score INTEGER, -- 1-5 rating
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        INDEX idx_feedback_user_id (user_id),
                        INDEX idx_feedback_vehicle_id (vehicle_id)
                    );
                """)

                self.db_conn.commit()
                logger.info("✅ Recommendation tables created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create recommendation tables: {e}")
            raise

    async def generate_recommendations_for_unavailable_favorite(
        self,
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """
        Generate recommendations for an unavailable favorite vehicle

        Args:
            request: Recommendation request containing vehicle and user data

        Returns:
            List of vehicle recommendations
        """
        try:
            logger.info(f"🔍 Generating recommendations for unavailable vehicle {request.unavailable_vehicle_id}")

            # Extract key attributes from the original vehicle
            original_attrs = self._extract_vehicle_attributes(request.original_vehicle_data)

            # Find similar vehicles using multiple strategies
            similar_vehicles = []

            # Strategy 1: Similar make/model/year
            make_model_similar = await self._find_similar_make_model(original_attrs)
            similar_vehicles.extend(make_model_similar)

            # Strategy 2: Similar price range
            price_similar = await self._find_similar_price_range(original_attrs, request.user_preferences)
            similar_vehicles.extend(price_similar)

            # Strategy 3: Similar features and specifications
            feature_similar = await self._find_similar_features(original_attrs)
            similar_vehicles.extend(feature_similar)

            # Strategy 4: User preference-based recommendations
            preference_based = await self._find_preference_based_recommendations(
                request.user_preferences,
                original_attrs
            )
            similar_vehicles.extend(preference_based)

            # Strategy 5: Semantic similarity if RAG-Anything is available
            if self.rag_service:
                semantic_similar = await self._find_semantically_similar_vehicles(original_attrs)
                similar_vehicles.extend(semantic_similar)

            # Remove duplicates and sort by similarity
            unique_vehicles = self._deduplicate_vehicles(similar_vehicles)
            ranked_vehicles = self._rank_recommendations(unique_vehicles, original_attrs, request.user_preferences)

            # Create recommendation objects
            recommendations = []
            for i, vehicle_data in enumerate(ranked_vehicles[:request.max_recommendations]):
                similarity_score = self._calculate_similarity_score(vehicle_data, original_attrs)
                match_reasons = self._generate_match_reasons(vehicle_data, original_attrs)
                confidence_score = self._calculate_confidence_score(vehicle_data, original_attrs, request.user_preferences)

                recommendation = Recommendation(
                    vehicle_id=vehicle_data.get('id', ''),
                    vehicle_data=vehicle_data,
                    similarity_score=similarity_score,
                    match_reasons=match_reasons,
                    confidence_score=confidence_score,
                    price_comparison=self._compare_prices(vehicle_data, original_attrs),
                    location_comparison=self._compare_locations(vehicle_data, original_attrs) if request.include_location else None,
                    recommendation_type=self._determine_recommendation_type(vehicle_data, original_attrs)
                )

                recommendations.append(recommendation)

                # Track recommendations in database
                await self._track_recommendation(request.user_id, request.unavailable_vehicle_id, recommendation)

            logger.info(f"✅ Generated {len(recommendations)} recommendations for vehicle {request.unavailable_vehicle_id}")
            return recommendations

        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return []

    def _extract_vehicle_attributes(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key attributes from vehicle data"""
        return {
            'id': vehicle_data.get('id'),
            'make': vehicle_data.get('make', '').lower().strip(),
            'model': vehicle_data.get('model', '').lower().strip(),
            'year': vehicle_data.get('year'),
            'price': vehicle_data.get('price'),
            'mileage': vehicle_data.get('mileage'),
            'body_type': vehicle_data.get('body_type', '').lower().strip(),
            'fuel_type': vehicle_data.get('fuel_type', '').lower().strip(),
            'transmission': vehicle_data.get('transmission', '').lower().strip(),
            'drivetrain': vehicle_data.get('drivetrain', '').lower().strip(),
            'color': vehicle_data.get('color', '').lower().strip(),
            'features': [f.lower().strip() for f in vehicle_data.get('features', [])],
            'location': vehicle_data.get('location'),
            'latitude': vehicle_data.get('latitude'),
            'longitude': vehicle_data.get('longitude'),
            'description': vehicle_data.get('description', '').lower()
        }

    async def _find_similar_make_model(self, original_attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find vehicles with similar make, model, and year"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Build query for similar make/model/year
                year_range = 2  # ±2 years
                make = original_attrs.get('make', '')
                model = original_attrs.get('model', '')
                year = original_attrs.get('year')

                if not make or not year:
                    return []

                cur.execute("""
                    SELECT DISTINCT v.*
                    FROM vehicles v
                    WHERE LOWER(v.make) = %s
                      AND LOWER(v.model) LIKE %s
                      AND v.year BETWEEN %s AND %s
                      AND v.id != %s
                      AND v.availability_status = 'available'
                      AND v.price IS NOT NULL
                    LIMIT 10;
                """, (
                    make,
                    f"%{model}%",
                    year - year_range,
                    year + year_range,
                    original_attrs.get('id')
                ))

                results = cur.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"❌ Error finding similar make/model: {e}")
            return []

    async def _find_similar_price_range(
        self,
        original_attrs: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find vehicles in similar price range"""
        try:
            original_price = original_attrs.get('price')
            if not original_price:
                return []

            # Get user's price preference if available
            price_range = user_preferences.get('price_range')
            if price_range:
                min_price = price_range.get('min', original_price * 0.8)
                max_price = price_range.get('max', original_price * 1.2)
            else:
                # Use tolerance percentage around original price
                tolerance = self.price_tolerance_percent / 100
                min_price = original_price * (1 - tolerance)
                max_price = original_price * (1 + tolerance)

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT DISTINCT v.*
                    FROM vehicles v
                    WHERE v.price BETWEEN %s AND %s
                      AND v.id != %s
                      AND v.availability_status = 'available'
                      AND v.make IS NOT NULL
                      AND v.model IS NOT NULL
                    ORDER BY v.price
                    LIMIT 20;
                """, (min_price, max_price, original_attrs.get('id')))

                results = cur.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"❌ Error finding similar price range: {e}")
            return []

    async def _find_similar_features(self, original_attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find vehicles with similar features and specifications"""
        try:
            features = original_attrs.get('features', [])
            body_type = original_attrs.get('body_type')
            fuel_type = original_attrs.get('fuel_type')
            transmission = original_attrs.get('transmission')

            if not any([features, body_type, fuel_type, transmission]):
                return []

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Build conditions for feature matching
                conditions = []
                params = []
                param_idx = 1

                conditions.append("v.id != %s")
                params.append(original_attrs.get('id'))
                param_idx += 1

                conditions.append("v.availability_status = 'available'")
                conditions.append("v.price IS NOT NULL")

                if body_type:
                    conditions.append(f"LOWER(v.body_type) = %{param_idx}s")
                    params.append(body_type)
                    param_idx += 1

                if fuel_type:
                    conditions.append(f"LOWER(v.fuel_type) = %{param_idx}s")
                    params.append(fuel_type)
                    param_idx += 1

                if transmission:
                    conditions.append(f"LOWER(v.transmission) = %{param_idx}s")
                    params.append(transmission)
                    param_idx += 1

                where_clause = " AND ".join(conditions)

                cur.execute(f"""
                    SELECT DISTINCT v.*
                    FROM vehicles v
                    WHERE {where_clause}
                    ORDER BY v.price
                    LIMIT 15;
                """, params)

                results = cur.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"❌ Error finding similar features: {e}")
            return []

    async def _find_preference_based_recommendations(
        self,
        user_preferences: Dict[str, Any],
        original_attrs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find vehicles based on user's stated preferences"""
        try:
            if not user_preferences:
                return []

            conditions = []
            params = []
            param_idx = 1

            # Apply user preferences to query
            preferred_makes = user_preferences.get('preferred_brands', [])
            if preferred_makes:
                make_conditions = [f"LOWER(v.make) = %{param_idx}s" for _ in preferred_makes]
                conditions.append(f"({(' OR '.join(make_conditions))})")
                params.extend([make.lower() for make in preferred_makes])
                param_idx += len(preferred_makes)

            preferred_features = user_preferences.get('must_have_features', [])
            if preferred_features:
                # For features, we'd need a more complex query or post-processing
                pass

            # Always exclude unavailable and original vehicle
            conditions.extend([
                "v.availability_status = 'available'",
                "v.price IS NOT NULL",
                "v.id != %s"
            ])
            params.append(original_attrs.get('id'))
            param_idx += 1

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"""
                    SELECT DISTINCT v.*
                    FROM vehicles v
                    WHERE {where_clause}
                    ORDER BY v.make, v.model, v.year DESC
                    LIMIT 25;
                """, params)

                results = cur.fetchall()
                vehicles = [dict(row) for row in results]

                # Post-process for feature matching if needed
                if preferred_features:
                    vehicles = [
                        v for v in vehicles
                        if any(feature.lower() in [f.lower() for f in v.get('features', [])]
                           for feature in preferred_features)
                    ]

                return vehicles

        except Exception as e:
            logger.error(f"❌ Error finding preference-based recommendations: {e}")
            return []

    async def _find_semantically_similar_vehicles(
        self,
        original_attrs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find semantically similar vehicles using RAG-Anything"""
        try:
            if not self.rag_service:
                return []

            # Create search text from original vehicle
            search_text = self._create_search_text(original_attrs)

            # Generate embeddings and search
            search_results = await self.rag_service.search(
                query=search_text,
                filters={"availability_status": "available"},
                limit=20
            )

            # Extract vehicle data from results
            similar_vehicles = []
            for result in search_results:
                if result.get('metadata', {}).get('type') == 'vehicle':
                    vehicle_data = result.get('metadata', {})
                    # Ensure vehicle has required fields
                    if vehicle_data.get('id') != original_attrs.get('id'):
                        similar_vehicles.append(vehicle_data)

            return similar_vehicles

        except Exception as e:
            logger.error(f"❌ Error finding semantically similar vehicles: {e}")
            return []

    def _create_search_text(self, original_attrs: Dict[str, Any]) -> str:
        """Create search text for semantic search"""
        components = [
            f"{original_attrs.get('year', '')} {original_attrs.get('make', '')} {original_attrs.get('model', '')}",
            f"{original_attrs.get('body_type', '')} {original_attrs.get('fuel_type', '')} {original_attrs.get('transmission', '')}",
            original_attrs.get('description', ''),
            " ".join(original_attrs.get('features', [])[:10])  # Limit features for search
        ]

        return " ".join(filter(None, components))

    def _deduplicate_vehicles(self, vehicles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate vehicles from recommendations"""
        seen_ids = set()
        unique_vehicles = []

        for vehicle in vehicles:
            vehicle_id = vehicle.get('id')
            if vehicle_id and vehicle_id not in seen_ids:
                seen_ids.add(vehicle_id)
                unique_vehicles.append(vehicle)

        return unique_vehicles

    def _rank_recommendations(
        self,
        vehicles: List[Dict[str, Any]],
        original_attrs: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank recommendations by similarity and user preferences"""
        try:
            scored_vehicles = []
            for vehicle in vehicles:
                score = self._calculate_overall_score(vehicle, original_attrs, user_preferences)
                scored_vehicles.append((score, vehicle))

            # Sort by score (highest first)
            scored_vehicles.sort(key=lambda x: x[0], reverse=True)

            # Return just the vehicles (without scores)
            return [vehicle for score, vehicle in scored_vehicles]

        except Exception as e:
            logger.error(f"❌ Error ranking recommendations: {e}")
            return vehicles

    def _calculate_overall_score(
        self,
        vehicle: Dict[str, Any],
        original_attrs: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> float:
        """Calculate overall similarity score for ranking"""
        try:
            scores = []

            # Make/model similarity (30% weight)
            make_score = self._calculate_make_model_similarity(vehicle, original_attrs)
            scores.append(('make_model', make_score, 0.3))

            # Price similarity (25% weight)
            price_score = self._calculate_price_similarity(vehicle, original_attrs)
            scores.append(('price', price_score, 0.25))

            # Feature similarity (25% weight)
            feature_score = self._calculate_feature_similarity(vehicle, original_attrs)
            scores.append(('features', feature_score, 0.25))

            # User preference alignment (20% weight)
            preference_score = self._calculate_preference_alignment(vehicle, user_preferences)
            scores.append(('preferences', preference_score, 0.2))

            # Calculate weighted score
            total_score = sum(score * weight for score, weight in scores)
            return total_score

        except Exception as e:
            logger.error(f"❌ Error calculating overall score: {e}")
            return 0.0

    def _calculate_make_model_similarity(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate make/model similarity score"""
        score = 0.0

        # Make match (40% of this category)
        if vehicle.get('make', '').lower() == original_attrs.get('make', '').lower():
            score += 0.4

        # Model similarity (60% of this category)
        vehicle_model = vehicle.get('model', '').lower()
        original_model = original_attrs.get('model', '').lower()

        if vehicle_model == original_model:
            score += 0.6
        elif original_model in vehicle_model or vehicle_model in original_model:
            score += 0.3  # Partial match
        else:
            # Use simple string similarity for remaining
            similarity = self._simple_string_similarity(vehicle_model, original_model)
            score += similarity * 0.6

        return score

    def _calculate_price_similarity(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate price similarity score"""
        try:
            vehicle_price = vehicle.get('price')
            original_price = original_attrs.get('price')

            if not vehicle_price or not original_price:
                return 0.5  # Neutral score if prices are missing

            # Calculate percentage difference
            price_diff = abs(vehicle_price - original_price)
            price_diff_percent = (price_diff / original_price) * 100

            # Convert to similarity score (closer price = higher score)
            if price_diff_percent <= 10:
                return 1.0
            elif price_diff_percent <= 25:
                return 0.8
            elif price_diff_percent <= 50:
                return 0.6
            elif price_diff_percent <= 100:
                return 0.4
            else:
                return 0.2

        except Exception:
            return 0.5

    def _calculate_feature_similarity(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate feature similarity score"""
        try:
            vehicle_features = set(f.lower() for f in vehicle.get('features', []))
            original_features = set(f.lower() for f in original_attrs.get('features', []))

            if not vehicle_features and not original_features:
                return 0.5  # Neutral score if no features

            if not vehicle_features or not original_features:
                return 0.0  # No match possible if one has no features

            # Calculate Jaccard similarity
            intersection = vehicle_features & original_features
            union = vehicle_features | original_features

            similarity = len(intersection) / len(union) if union else 0

            return similarity

        except Exception:
            return 0.5

    def _calculate_preference_alignment(self, vehicle: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """Calculate how well vehicle aligns with user preferences"""
        try:
            if not user_preferences:
                return 0.5  # Neutral score if no preferences

            score = 0.0
            total_checks = 0

            # Preferred brands check
            preferred_makes = user_preferences.get('preferred_brands', [])
            if preferred_makes:
                total_checks += 1
                if vehicle.get('make', '').lower() in [make.lower() for make in preferred_makes]:
                    score += 1.0

            # Must-have features check
            must_have_features = user_preferences.get('must_have_features', [])
            if must_have_features:
                total_checks += 1
                vehicle_features = [f.lower() for f in vehicle.get('features', [])]
                if all(feature.lower() in vehicle_features for feature in must_have_features):
                    score += 1.0

            # Price range check
            price_range = user_preferences.get('price_range')
            if price_range:
                total_checks += 1
                vehicle_price = vehicle.get('price')
                min_price = price_range.get('min', 0)
                max_price = price_range.get('max', float('inf'))
                if vehicle_price and min_price <= vehicle_price <= max_price:
                    score += 1.0

            # Avoid features check
            avoid_features = user_preferences.get('avoid_features', [])
            if avoid_features:
                total_checks += 1
                vehicle_features = [f.lower() for f in vehicle.get('features', [])]
                if not any(feature.lower() in vehicle_features for feature in avoid_features):
                    score += 1.0

            return score / total_checks if total_checks > 0 else 0.5

        except Exception:
            return 0.5

    def _simple_string_similarity(self, str1: str, str2: str) -> float:
        """Simple string similarity calculation"""
        try:
            if not str1 or not str2:
                return 0.0

            # Check for exact match
            if str1 == str2:
                return 1.0

            # Check if one is substring of the other
            if str1 in str2 or str2 in str1:
                return 0.8

            # Simple character-based similarity
            common_chars = set(str1) & set(str2)
            total_chars = set(str1) | set(str2)

            return len(common_chars) / len(total_chars) if total_chars else 0.0

        except Exception:
            return 0.0

    def _calculate_similarity_score(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate detailed similarity score between two vehicles"""
        try:
            scores = []
            weights = {
                'make_model': 0.3,
                'price': 0.25,
                'year': 0.15,
                'features': 0.2,
                'body_type': 0.1
            }

            # Calculate individual scores
            scores.append(('make_model', self._calculate_make_model_similarity(vehicle, original_attrs)))
            scores.append(('price', self._calculate_price_similarity(vehicle, original_attrs)))
            scores.append(('year', self._calculate_year_similarity(vehicle, original_attrs)))
            scores.append(('features', self._calculate_feature_similarity(vehicle, original_attrs)))
            scores.append(('body_type', self._calculate_body_type_similarity(vehicle, original_attrs)))

            # Weighted average
            total_score = sum(score * weights.get(metric, 0) for metric, score in scores)
            return total_score

        except Exception:
            return 0.5

    def _calculate_year_similarity(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate year similarity score"""
        try:
            vehicle_year = vehicle.get('year')
            original_year = original_attrs.get('year')

            if not vehicle_year or not original_year:
                return 0.5

            year_diff = abs(vehicle_year - original_year)

            if year_diff == 0:
                return 1.0
            elif year_diff <= 1:
                return 0.9
            elif year_diff <= 2:
                return 0.8
            elif year_diff <= 3:
                return 0.6
            elif year_diff <= 5:
                return 0.4
            else:
                return 0.2

        except Exception:
            return 0.5

    def _calculate_body_type_similarity(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> float:
        """Calculate body type similarity score"""
        try:
            vehicle_body = vehicle.get('body_type', '').lower()
            original_body = original_attrs.get('body_type', '').lower()

            if not vehicle_body or not original_body:
                return 0.5

            return 1.0 if vehicle_body == original_body else 0.0

        except Exception:
            return 0.5

    def _generate_match_reasons(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> List[str]:
        """Generate reasons why this vehicle is a good match"""
        reasons = []

        try:
            # Make/model reasons
            if vehicle.get('make', '').lower() == original_attrs.get('make', '').lower():
                reasons.append(f"Same make: {vehicle.get('make')}")

            if vehicle.get('model', '').lower() == original_attrs.get('model', '').lower():
                reasons.append(f"Same model: {vehicle.get('model')}")

            # Price reasons
            vehicle_price = vehicle.get('price')
            original_price = original_attrs.get('price')
            if vehicle_price and original_price:
                price_diff = vehicle_price - original_price
                if abs(price_diff) <= original_price * 0.1:  # Within 10%
                    if price_diff > 0:
                        reasons.append(f"Slightly higher price: ${price_diff:,.0f} more")
                    else:
                        reasons.append(f"Great value: ${abs(price_diff):,.0f} less")

            # Feature reasons
            vehicle_features = [f.lower() for f in vehicle.get('features', [])]
            original_features = [f.lower() for f in original_attrs.get('features', [])]
            common_features = set(vehicle_features) & set(original_features)

            if common_features:
                reasons.append(f"Shared features: {', '.join(list(common_features)[:3])}")

            # Year reason
            vehicle_year = vehicle.get('year')
            original_year = original_attrs.get('year')
            if vehicle_year and original_year and abs(vehicle_year - original_year) <= 2:
                reasons.append(f"Similar year: {vehicle_year}")

            # Body type reason
            if (vehicle.get('body_type', '').lower() == original_attrs.get('body_type', '').lower() and
                vehicle.get('body_type')):
                reasons.append(f"Same body type: {vehicle.get('body_type')}")

            return reasons[:5]  # Limit to 5 reasons

        except Exception:
            return ["Similar vehicle characteristics"]

    def _calculate_confidence_score(
        self,
        vehicle: Dict[str, Any],
        original_attrs: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the recommendation"""
        try:
            base_confidence = self._calculate_similarity_score(vehicle, original_attrs)

            # Boost confidence based on data completeness
            data_completeness = 0.0
            required_fields = ['make', 'model', 'year', 'price', 'features']
            for field in required_fields:
                if vehicle.get(field):
                    data_completeness += 0.2

            # Boost confidence based on user preference alignment
            preference_boost = self._calculate_preference_alignment(vehicle, user_preferences) * 0.1

            confidence = (base_confidence * 0.7) + (data_completeness * 0.2) + preference_boost
            return min(1.0, confidence)

        except Exception:
            return 0.5

    def _compare_prices(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Compare prices between two vehicles"""
        try:
            vehicle_price = vehicle.get('price')
            original_price = original_attrs.get('price')

            if not vehicle_price or not original_price:
                return {"available": False}

            price_diff = vehicle_price - original_price
            price_diff_percent = (price_diff / original_price) * 100 if original_price > 0 else 0

            return {
                "available": True,
                "original_price": original_price,
                "recommended_price": vehicle_price,
                "price_difference": price_diff,
                "price_difference_percent": round(price_diff_percent, 2),
                "more_expensive": price_diff > 0,
                "significantly_different": abs(price_diff_percent) > 20
            }

        except Exception:
            return {"available": False}

    def _compare_locations(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Compare locations between two vehicles"""
        try:
            vehicle_loc = vehicle.get('location')
            original_loc = original_attrs.get('location')

            if not vehicle_loc or not original_loc:
                return {"available": False}

            # For now, just compare location strings
            # In a real implementation, you'd use geocoding to calculate distances
            location_match = vehicle_loc.lower() == original_loc.lower()

            return {
                "available": True,
                "location_match": location_match,
                "original_location": original_loc,
                "recommended_location": vehicle_loc,
                "distance_km": 0 if location_match else None
            }

        except Exception:
            return {"available": False}

    def _determine_recommendation_type(self, vehicle: Dict[str, Any], original_attrs: Dict[str, Any]) -> str:
        """Determine the type of recommendation"""
        try:
            # Check for exact make/model match
            if (vehicle.get('make', '').lower() == original_attrs.get('make', '').lower() and
                vehicle.get('model', '').lower() == original_attrs.get('model', '').lower()):
                return "exact_make_model_match"

            # Check for same make, different model
            if vehicle.get('make', '').lower() == original_attrs.get('make', '').lower():
                return "same_make_alternative"

            # Check for similar price range
            vehicle_price = vehicle.get('price')
            original_price = original_attrs.get('price')
            if vehicle_price and original_price:
                price_diff_percent = abs((vehicle_price - original_price) / original_price) * 100
                if price_diff_percent <= 20:
                    return "similar_price_range"

            # Check for similar features
            vehicle_features = set(f.lower() for f in vehicle.get('features', []))
            original_features = set(f.lower() for f in original_attrs.get('features', []))
            if vehicle_features and original_features:
                similarity = len(vehicle_features & original_features) / len(vehicle_features | original_features)
                if similarity > 0.5:
                    return "similar_features"

            # Default to general alternative
            return "general_alternative"

        except Exception:
            return "unknown"

    async def _track_recommendation(
        self,
        user_id: str,
        unavailable_vehicle_id: str,
        recommendation: Recommendation
    ) -> None:
        """Track recommendation in database for analytics"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vehicle_recommendations (
                        user_id, unavailable_vehicle_id, recommended_vehicle_id,
                        similarity_score, match_reasons, confidence_score, recommendation_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    user_id,
                    unavailable_vehicle_id,
                    recommendation.vehicle_id,
                    recommendation.similarity_score,
                    recommendation.match_reasons,
                    recommendation.confidence_score,
                    recommendation.recommendation_type
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to track recommendation: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    async def record_recommendation_feedback(
        self,
        user_id: str,
        vehicle_id: str,
        feedback_type: str,
        feedback_score: Optional[int] = None,
        recommendation_id: Optional[str] = None
    ) -> bool:
        """
        Record user feedback on recommendations

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier
            feedback_type: Type of feedback (clicked, favorited, dismissed, converted)
            feedback_score: Optional score (1-5)
            recommendation_id: Optional recommendation identifier

        Returns:
            True if recorded successfully, False otherwise
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recommendation_feedback (
                        user_id, vehicle_id, recommendation_id, feedback_type, feedback_score
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (user_id, vehicle_id, recommendation_id, feedback_type, feedback_score))

                self.db_conn.commit()

            logger.info(f"📝 Recorded recommendation feedback: {feedback_type} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record recommendation feedback: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def get_recommendation_analytics(
        self,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics on recommendation performance

        Args:
            days_back: Number of days to look back for analytics

        Returns:
            Analytics data dictionary
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get recommendation generation stats
                cur.execute("""
                    SELECT
                        COUNT(*) as total_recommendations,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT unavailable_vehicle_id) as vehicles_recommended_for,
                        AVG(similarity_score) as avg_similarity_score,
                        AVG(confidence_score) as avg_confidence_score
                    FROM vehicle_recommendations
                    WHERE created_at >= %s;
                """, (cutoff_date,))

                rec_stats = cur.fetchone()

                # Get interaction stats
                cur.execute("""
                    SELECT
                        feedback_type,
                        COUNT(*) as count,
                        AVG(feedback_score) as avg_score
                    FROM recommendation_feedback rf
                    JOIN vehicle_recommendations vr ON rf.recommendation_id = vr.id
                    WHERE vr.created_at >= %s
                    GROUP BY feedback_type;
                """, (cutoff_date,))

                interaction_stats = cur.fetchall()

                # Get recommendation type performance
                cur.execute("""
                    SELECT
                        recommendation_type,
                        COUNT(*) as count,
                        AVG(rf.feedback_score) as avg_feedback_score,
                        COUNT(CASE WHEN rf.feedback_type = 'converted' THEN 1 END) * 1.0 / COUNT(*) as conversion_rate
                    FROM vehicle_recommendations vr
                    LEFT JOIN recommendation_feedback rf ON vr.id = rf.recommendation_id
                    WHERE vr.created_at >= %s
                    GROUP BY recommendation_type
                    ORDER BY count DESC;
                """, (cutoff_date,))

                type_performance = cur.fetchall()

            analytics = {
                "period_days": days_back,
                "recommendations": {
                    "total_generated": rec_stats['total_recommendations'] or 0,
                    "unique_users": rec_stats['unique_users'] or 0,
                    "vehicles_covered": rec_stats['vehicles_recommended_for'] or 0,
                    "avg_similarity_score": float(rec_stats['avg_similarity_score'] or 0),
                    "avg_confidence_score": float(rec_stats['avg_confidence_score'] or 0)
                },
                "interactions": [
                    {
                        "type": stat['feedback_type'],
                        "count": stat['count'],
                        "avg_score": float(stat['avg_score']) if stat['avg_score'] else None
                    }
                    for stat in interaction_stats
                ],
                "performance_by_type": [
                    {
                        "type": perf['recommendation_type'],
                        "count": perf['count'],
                        "avg_feedback_score": float(perf['avg_feedback_score']) if perf['avg_feedback_score'] else None,
                        "conversion_rate": float(perf['conversion_rate']) if perf['conversion_rate'] else 0
                    }
                    for perf in type_performance
                ],
                "generated_at": datetime.utcnow().isoformat()
            }

            return analytics

        except Exception as e:
            logger.error(f"❌ Failed to get recommendation analytics: {e}")
            return {}

    async def close(self) -> None:
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Favorites Recommendation Engine connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass