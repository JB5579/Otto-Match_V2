"""
Otto.AI Vehicle Recommendation Engine

Implements personalized vehicle recommendations using collaborative filtering,
content-based filtering, and hybrid approaches.
Part of Story 1-5: Build Vehicle Comparison and Recommendation Engine
"""

import asyncio
import logging
import time
import random
import hashlib
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

# OpenAI imports for GPT-4 integration
import openai
from openai import AsyncOpenAI

# Import recommendation models from the correct location
from .favorites_recommendation_engine import (
    RecommendationRequest, Recommendation
)

# For now, stub the missing types that were imported from vehicle_models
# These are not currently used in the recommendation engine
RecommendationResponse = None
RecommendationExplanation = None
RecommendationType = None
UserInteraction = None
FeedbackRequest = None

logger = logging.getLogger(__name__)

@dataclass
class RecommendationResult:
    """Internal recommendation result structure"""
    recommendations: List[Recommendation]
    algorithm_version: str
    a_b_test_group: Optional[str]
    cached: bool = False

class RecommendationEngine:
    """Vehicle recommendation engine with multiple algorithms"""

    def __init__(self, vehicle_db_service, embedding_service):
        """
        Initialize recommendation engine

        Args:
            vehicle_db_service: Vehicle database service
            embedding_service: Embedding service for semantic analysis
        """
        self.vehicle_db = vehicle_db_service
        self.embedding_service = embedding_service

        # Initialize OpenAI client for GPT-4 explanations
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=openai_api_key)
            self.gpt4_enabled = True
            logger.info("✅ GPT-4 integration enabled for recommendation explanations")
        else:
            self.openai_client = None
            self.gpt4_enabled = False
            logger.warning("⚠️ OPENAI_API_KEY not found, using template-based explanations")

        # Algorithm version for tracking and A/B testing
        self.algorithm_version = "1.0.0"

        # User preference weights (configurable)
        self.preference_weights = {
            'price_sensitivity': 0.25,
            'brand_preference': 0.20,
            'feature_preference': 0.25,
            'performance_preference': 0.15,
            'efficiency_preference': 0.15
        }

        # Recommendation algorithm parameters
        self.collaborative_weight = 0.4  # Weight for collaborative filtering
        self.content_weight = 0.6       # Weight for content-based filtering
        self.min_similarity_threshold = 0.3
        self.max_recommendations = 50

        # A/B testing groups
        self.ab_test_groups = {
            'control': {'collaborative_weight': 0.4, 'content_weight': 0.6},
            'variant_a': {'collaborative_weight': 0.5, 'content_weight': 0.5},
            'variant_b': {'collaborative_weight': 0.3, 'content_weight': 0.7}
        }

        # Cache for recommendation results
        self.recommendation_cache: Dict[str, Tuple[RecommendationResult, datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)

    async def get_recommendations(
        self,
        user_id: str,
        context_vehicle_ids: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        recommendation_type: RecommendationType = RecommendationType.HYBRID,
        limit: int = 10,
        include_explanations: bool = True,
        session_id: Optional[str] = None
    ) -> RecommendationResult:
        """
        Get personalized vehicle recommendations for a user

        Args:
            user_id: User identifier
            context_vehicle_ids: Context vehicles for recommendations
            search_query: Current search query
            recommendation_type: Type of recommendation algorithm
            limit: Number of recommendations to return
            include_explanations: Include recommendation explanations
            session_id: Session identifier

        Returns:
            RecommendationResult with personalized recommendations
        """
        start_time = time.time()

        try:
            logger.info(f"Generating recommendations for user {user_id}")

            # Check cache first
            cache_key = self._generate_cache_key(
                user_id, context_vehicle_ids, search_query, recommendation_type, limit
            )
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Returning cached recommendations for user {user_id}")
                return cached_result

            # Determine A/B test group
            ab_test_group = self._get_ab_test_group(user_id)

            # Get user profile and preferences
            user_profile = await self._get_user_profile(user_id)

            # Get candidate vehicles
            candidate_vehicles = await self._get_candidate_vehicles(
                context_vehicle_ids, user_profile, limit * 3
            )

            if not candidate_vehicles:
                logger.warning(f"No candidate vehicles found for user {user_id}")
                return RecommendationResult(
                    recommendations=[],
                    algorithm_version=self.algorithm_version,
                    a_b_test_group=ab_test_group
                )

            # Generate recommendations based on type
            recommendations = []

            if recommendation_type == RecommendationType.COLLABORATIVE:
                recommendations = await self._collaborative_filtering(
                    user_id, candidate_vehicles, user_profile, limit
                )
            elif recommendation_type == RecommendationType.CONTENT_BASED:
                recommendations = await self._content_based_filtering(
                    user_id, candidate_vehicles, user_profile, search_query, limit
                )
            elif recommendation_type == RecommendationType.SIMILARITY:
                recommendations = await self._similarity_based_recommendations(
                    context_vehicle_ids, candidate_vehicles, limit
                )
            else:  # HYBRID
                recommendations = await self._hybrid_recommendations(
                    user_id, candidate_vehicles, user_profile, search_query,
                    context_vehicle_ids, limit, ab_test_group
                )

            # Generate explanations if requested
            if include_explanations:
                for rec in recommendations:
                    if not rec.explanation:
                        rec.explanation = await self._generate_recommendation_explanation(
                            rec, user_profile, search_query, context_vehicle_ids
                        )

            # Sort by recommendation score
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)

            # Apply final filtering and ranking
            recommendations = recommendations[:limit]

            # Add trending scores and urgency indicators
            for rec in recommendations:
                rec.trending_score = await self._calculate_trending_score(rec.vehicle_id)
                rec.urgency_indicators = await self._get_urgency_indicators(rec.vehicle_id)

            processing_time = time.time() - start_time

            # Create result
            result = RecommendationResult(
                recommendations=recommendations,
                algorithm_version=self.algorithm_version,
                a_b_test_group=ab_test_group,
                cached=False
            )

            # Cache the result
            await self._cache_result(cache_key, result)

            logger.info(f"Recommendations generated for user {user_id} in {processing_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Recommendation engine error: {str(e)}")
            raise

    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile and preferences"""
        # This would integrate with user profile service
        # For now, return mock data
        return {
            'user_id': user_id,
            'preferences': {
                'preferred_brands': ['Toyota', 'Honda', 'Ford'],
                'price_range': {'min': 20000, 'max': 40000},
                'vehicle_types': ['SUV', 'Sedan'],
                'must_have_features': ['bluetooth', 'backup camera'],
                'avoid_features': ['manual transmission'],
                'price_sensitivity': 0.7,  # 0 = not sensitive, 1 = very sensitive
                'brand_loyalty': 0.6,      # 0 = not loyal, 1 = very loyal
                'feature_importance': 0.8  # 0 = not important, 1 = very important
            },
            'interaction_history': {
                'viewed_vehicles': [],
                'saved_vehicles': [],
                'compared_vehicles': [],
                'search_history': []
            },
            'demographics': {
                'age': 35,
                'location': {'city': 'Seattle', 'state': 'WA'},
                'family_size': 4
            }
        }

    async def _get_candidate_vehicles(
        self,
        context_vehicle_ids: Optional[List[str]],
        user_profile: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get candidate vehicles for recommendations"""
        candidates = []

        try:
            # Get vehicles similar to context vehicles
            if context_vehicle_ids:
                for vehicle_id in context_vehicle_ids:
                    similar_vehicles = await self._get_similar_vehicles(vehicle_id, limit // 2)
                    candidates.extend(similar_vehicles)

            # Get vehicles matching user preferences
            preference_matches = await self._get_preference_matches(user_profile, limit)
            candidates.extend(preference_matches)

            # Get trending/popular vehicles
            trending_vehicles = await self._get_trending_vehicles(limit // 3)
            candidates.extend(trending_vehicles)

            # Remove duplicates and context vehicles
            seen_ids = set(context_vehicle_ids or [])
            unique_candidates = []
            for vehicle in candidates:
                if vehicle['id'] not in seen_ids:
                    unique_candidates.append(vehicle)
                    seen_ids.add(vehicle['id'])

            return unique_candidates[:limit]

        except Exception as e:
            logger.error(f"Error getting candidate vehicles: {str(e)}")
            return []

    async def _get_similar_vehicles(self, vehicle_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get vehicles similar to the given vehicle"""
        try:
            # This would integrate with semantic search service
            # For now, return mock data
            return await self.vehicle_db.get_similar_vehicles(vehicle_id, limit)
        except Exception as e:
            logger.error(f"Error getting similar vehicles for {vehicle_id}: {str(e)}")
            return []

    async def _get_preference_matches(self, user_profile: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get vehicles matching user preferences"""
        try:
            preferences = user_profile.get('preferences', {})

            # Build search filters from preferences
            filters = {}
            if 'price_range' in preferences:
                filters['price_min'] = preferences['price_range']['min']
                filters['price_max'] = preferences['price_range']['max']

            if 'preferred_brands' in preferences:
                filters['makes'] = preferences['preferred_brands']

            if 'vehicle_types' in preferences:
                filters['vehicle_types'] = preferences['vehicle_types']

            # Search for matching vehicles
            return await self.vehicle_db.search_vehicles(filters, limit)

        except Exception as e:
            logger.error(f"Error getting preference matches: {str(e)}")
            return []

    async def _get_trending_vehicles(self, limit: int) -> List[Dict[str, Any]]:
        """Get currently trending vehicles"""
        try:
            # This would integrate with analytics service
            # For now, return recently viewed popular vehicles
            return await self.vehicle_db.get_trending_vehicles(limit)
        except Exception as e:
            logger.error(f"Error getting trending vehicles: {str(e)}")
            return []

    async def _collaborative_filtering(
        self,
        user_id: str,
        candidate_vehicles: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        limit: int
    ) -> List[Recommendation]:
        """Generate recommendations using collaborative filtering"""
        recommendations = []

        try:
            # Get similar users
            similar_users = await self._get_similar_users(user_id, 50)

            if not similar_users:
                return recommendations

            # Get vehicles liked by similar users
            user_vehicle_scores = {}

            for similar_user in similar_users:
                user_score = similar_user['similarity_score']
                liked_vehicles = similar_user.get('liked_vehicles', [])

                for vehicle_id in liked_vehicles:
                    if vehicle_id not in user_vehicle_scores:
                        user_vehicle_scores[vehicle_id] = 0
                    user_vehicle_scores[vehicle_id] += user_score

            # Filter candidate vehicles
            candidate_ids = {v['id'] for v in candidate_vehicles}
            filtered_scores = {
                vid: score for vid, score in user_vehicle_scores.items()
                if vid in candidate_ids
            }

            # Create recommendations
            for vehicle in candidate_vehicles:
                vehicle_id = vehicle['id']
                if vehicle_id in filtered_scores:
                    score = min(filtered_scores[vehicle_id] / 10, 1.0)  # Normalize to 0-1

                    recommendation = Recommendation(
                        vehicle_id=vehicle_id,
                        vehicle_data=vehicle,
                        recommendation_score=score,
                        match_percentage=int(score * 100),
                        explanation=None,  # Will be generated later
                        personalization_factors=["similar_users_preferences"],
                        trending_score=None,
                        urgency_indicators=[]
                    )
                    recommendations.append(recommendation)

            # Sort by score and return top results
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error in collaborative filtering: {str(e)}")
            return []

    async def _content_based_filtering(
        self,
        user_id: str,
        candidate_vehicles: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        search_query: Optional[str],
        limit: int
    ) -> List[Recommendation]:
        """Generate recommendations using content-based filtering"""
        recommendations = []

        try:
            # Create user preference profile
            user_preference_vector = await self._create_user_preference_vector(user_profile)

            for vehicle in candidate_vehicles:
                # Calculate content similarity
                content_score = await self._calculate_content_similarity(
                    vehicle, user_preference_vector, search_query
                )

                if content_score > self.min_similarity_threshold:
                    recommendation = Recommendation(
                        vehicle_id=vehicle['id'],
                        vehicle_data=vehicle,
                        recommendation_score=content_score,
                        match_percentage=int(content_score * 100),
                        explanation=None,  # Will be generated later
                        personalization_factors=["content_match"],
                        trending_score=None,
                        urgency_indicators=[]
                    )
                    recommendations.append(recommendation)

            # Sort by score and return top results
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error in content-based filtering: {str(e)}")
            return []

    async def _similarity_based_recommendations(
        self,
        context_vehicle_ids: Optional[List[str]],
        candidate_vehicles: List[Dict[str, Any]],
        limit: int
    ) -> List[Recommendation]:
        """Generate recommendations based on vehicle similarity"""
        recommendations = []

        if not context_vehicle_ids:
            return recommendations

        try:
            # Calculate similarity scores
            for vehicle in candidate_vehicles:
                max_similarity = 0

                for context_id in context_vehicle_ids:
                    similarity = await self._calculate_vehicle_similarity(vehicle['id'], context_id)
                    max_similarity = max(max_similarity, similarity)

                if max_similarity > self.min_similarity_threshold:
                    recommendation = Recommendation(
                        vehicle_id=vehicle['id'],
                        vehicle_data=vehicle,
                        recommendation_score=max_similarity,
                        match_percentage=int(max_similarity * 100),
                        explanation=None,  # Will be generated later
                        personalization_factors=["similar_to_viewed"],
                        trending_score=None,
                        urgency_indicators=[]
                    )
                    recommendations.append(recommendation)

            # Sort by similarity and return top results
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error in similarity-based recommendations: {str(e)}")
            return []

    async def _hybrid_recommendations(
        self,
        user_id: str,
        candidate_vehicles: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        search_query: Optional[str],
        context_vehicle_ids: Optional[List[str]],
        limit: int,
        ab_test_group: str
    ) -> List[Recommendation]:
        """Generate hybrid recommendations combining multiple algorithms"""
        try:
            # Get weights for A/B test group
            weights = self.ab_test_groups.get(ab_test_group, self.ab_test_groups['control'])
            collaborative_weight = weights['collaborative_weight']
            content_weight = weights['content_weight']

            # Get recommendations from both algorithms
            collaborative_recs = await self._collaborative_filtering(
                user_id, candidate_vehicles, user_profile, limit * 2
            )
            content_recs = await self._content_based_filtering(
                user_id, candidate_vehicles, user_profile, search_query, limit * 2
            )

            # Add similarity-based recommendations if context vehicles exist
            similarity_recs = []
            if context_vehicle_ids:
                similarity_recs = await self._similarity_based_recommendations(
                    context_vehicle_ids, candidate_vehicles, limit
                )

            # Combine recommendations
            combined_scores = {}

            # Process collaborative filtering results
            for rec in collaborative_recs:
                combined_scores[rec.vehicle_id] = {
                    'vehicle': rec,
                    'collaborative_score': rec.recommendation_score,
                    'content_score': 0,
                    'similarity_score': 0
                }

            # Process content-based results
            for rec in content_recs:
                if rec.vehicle_id in combined_scores:
                    combined_scores[rec.vehicle_id]['content_score'] = rec.recommendation_score
                else:
                    combined_scores[rec.vehicle_id] = {
                        'vehicle': rec,
                        'collaborative_score': 0,
                        'content_score': rec.recommendation_score,
                        'similarity_score': 0
                    }

            # Process similarity results
            for rec in similarity_recs:
                if rec.vehicle_id in combined_scores:
                    combined_scores[rec.vehicle_id]['similarity_score'] = rec.recommendation_score
                else:
                    combined_scores[rec.vehicle_id] = {
                        'vehicle': rec,
                        'collaborative_score': 0,
                        'content_score': 0,
                        'similarity_score': rec.recommendation_score
                    }

            # Calculate hybrid scores
            hybrid_recommendations = []

            for vehicle_id, scores in combined_scores.items():
                # Weighted combination of scores
                hybrid_score = (
                    collaborative_weight * scores['collaborative_score'] +
                    content_weight * scores['content_score'] +
                    0.2 * scores['similarity_score']  # Lower weight for similarity
                )

                # Determine personalization factors
                personalization_factors = []
                if scores['collaborative_score'] > 0.5:
                    personalization_factors.append("similar_users_preferences")
                if scores['content_score'] > 0.5:
                    personalization_factors.append("content_match")
                if scores['similarity_score'] > 0.5:
                    personalization_factors.append("similar_to_viewed")

                recommendation = Recommendation(
                    vehicle_id=vehicle_id,
                    vehicle_data=scores['vehicle'].vehicle_data,
                    recommendation_score=hybrid_score,
                    match_percentage=int(hybrid_score * 100),
                    explanation=None,  # Will be generated later
                    personalization_factors=personalization_factors,
                    trending_score=None,
                    urgency_indicators=[]
                )
                hybrid_recommendations.append(recommendation)

            # Sort by hybrid score and return top results
            hybrid_recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            return hybrid_recommendations[:limit]

        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {str(e)}")
            return []

    async def _create_user_preference_vector(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create user preference vector for content-based filtering"""
        preferences = user_profile.get('preferences', {})

        return {
            'brands': preferences.get('preferred_brands', []),
            'price_range': preferences.get('price_range', {}),
            'vehicle_types': preferences.get('vehicle_types', []),
            'must_have_features': preferences.get('must_have_features', []),
            'avoid_features': preferences.get('avoid_features', []),
            'price_sensitivity': preferences.get('price_sensitivity', 0.5),
            'feature_importance': preferences.get('feature_importance', 0.5)
        }

    async def _calculate_content_similarity(
        self,
        vehicle: Dict[str, Any],
        user_preference_vector: Dict[str, Any],
        search_query: Optional[str]
    ) -> float:
        """Calculate content similarity between vehicle and user preferences"""
        try:
            score = 0.0
            total_weight = 0.0

            # Brand preference
            if 'brands' in user_preference_vector and 'make' in vehicle:
                if vehicle['make'] in user_preference_vector['brands']:
                    score += 0.3
                total_weight += 0.3

            # Price preference
            if 'price_range' in user_preference_vector and 'price' in vehicle:
                price_min = user_preference_vector['price_range'].get('min', 0)
                price_max = user_preference_vector['price_range'].get('max', float('inf'))
                vehicle_price = vehicle['price']

                if price_min <= vehicle_price <= price_max:
                    score += 0.25
                elif vehicle_price < price_min:
                    score += 0.15  # Still good if cheaper
                total_weight += 0.25

            # Vehicle type preference
            if 'vehicle_types' in user_preference_vector and 'vehicle_type' in vehicle:
                if vehicle['vehicle_type'] in user_preference_vector['vehicle_types']:
                    score += 0.2
                total_weight += 0.2

            # Feature preferences
            if 'must_have_features' in user_preference_vector and 'features' in vehicle:
                vehicle_features = set(vehicle.get('features', []))
                must_have = set(user_preference_vector['must_have_features'])
                avoid = set(user_preference_vector.get('avoid_features', []))

                # Check must-have features
                must_have_count = len(vehicle_features & must_have)
                if must_have_count > 0:
                    score += 0.15 * (must_have_count / len(must_have))

                # Penalty for avoided features
                avoid_count = len(vehicle_features & avoid)
                if avoid_count > 0:
                    score -= 0.1 * (avoid_count / len(avoid)) if avoid else 0

                total_weight += 0.25

            # Search query relevance
            if search_query:
                query_relevance = await self._calculate_query_relevance(vehicle, search_query)
                score += 0.1 * query_relevance
                total_weight += 0.1

            # Normalize score
            if total_weight > 0:
                return min(score / total_weight, 1.0)
            return 0.0

        except Exception as e:
            logger.error(f"Error calculating content similarity: {str(e)}")
            return 0.0

    async def _calculate_query_relevance(self, vehicle: Dict[str, Any], query: str) -> float:
        """Calculate relevance of vehicle to search query"""
        try:
            # This would integrate with semantic search service
            # For now, implement simple keyword matching
            query_lower = query.lower()
            vehicle_text = f"{vehicle.get('make', '')} {vehicle.get('model', '')} {vehicle.get('description', '')} {' '.join(vehicle.get('features', []))}".lower()

            # Simple word overlap
            query_words = set(query_lower.split())
            vehicle_words = set(vehicle_text.split())

            if len(query_words) == 0:
                return 0.0

            overlap = len(query_words & vehicle_words)
            relevance = overlap / len(query_words)

            return min(relevance, 1.0)

        except Exception as e:
            logger.error(f"Error calculating query relevance: {str(e)}")
            return 0.0

    async def _get_similar_users(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get users with similar preferences and behavior"""
        try:
            # This would integrate with user similarity service
            # For now, return mock similar users
            return [
                {
                    'user_id': f'similar_user_{i}',
                    'similarity_score': 0.7 - (i * 0.1),
                    'liked_vehicles': [f'vehicle_{random.randint(1, 100)}' for _ in range(5)]
                }
                for i in range(limit)
            ]
        except Exception as e:
            logger.error(f"Error getting similar users: {str(e)}")
            return []

    async def _calculate_vehicle_similarity(self, vehicle_a_id: str, vehicle_b_id: str) -> float:
        """Calculate similarity between two vehicles"""
        try:
            # This would integrate with vehicle similarity service
            # For now, return mock similarity
            return random.uniform(0.2, 0.9)
        except Exception as e:
            logger.error(f"Error calculating vehicle similarity: {str(e)}")
            return 0.0

    async def _generate_recommendation_explanation(
        self,
        recommendation: Recommendation,
        user_profile: Dict[str, Any],
        search_query: Optional[str],
        context_vehicle_ids: Optional[List[str]]
    ) -> RecommendationExplanation:
        """Generate explanation for recommendation using GPT-4 or fallback"""
        try:
            vehicle_data = recommendation.vehicle_data
            confidence_score = recommendation.recommendation_score
            supporting_factors = recommendation.personalization_factors

            # Try GPT-4 first if available
            if self.gpt4_enabled and self.openai_client:
                try:
                    explanation = await self._generate_gpt4_explanation(
                        vehicle_data, user_profile, search_query,
                        context_vehicle_ids, confidence_score, supporting_factors
                    )
                    reasoning_type = "gpt4_personalized"
                    user_relevance_score = confidence_score

                    return RecommendationExplanation(
                        reasoning_type=reasoning_type,
                        explanation=explanation,
                        confidence_score=confidence_score,
                        supporting_factors=supporting_factors,
                        user_relevance_score=user_relevance_score
                    )
                except Exception as e:
                    logger.warning(f"GPT-4 explanation failed, falling back to template: {e}")

            # Fallback to template-based explanation
            return await self._generate_template_explanation(
                recommendation, user_profile, search_query, context_vehicle_ids
            )

        except Exception as e:
            logger.error(f"Error generating recommendation explanation: {str(e)}")
            return RecommendationExplanation(
                reasoning_type="generic",
                explanation="This vehicle matches your preferences",
                confidence_score=0.5,
                supporting_factors=["preferences"],
                user_relevance_score=0.5
            )

    async def _generate_gpt4_explanation(
        self,
        vehicle_data: Dict[str, Any],
        user_profile: Dict[str, Any],
        search_query: Optional[str],
        context_vehicle_ids: Optional[List[str]],
        confidence_score: float,
        supporting_factors: List[str]
    ) -> str:
        """Generate personalized explanation using GPT-4"""
        try:
            # Create comprehensive prompt for GPT-4
            vehicle_info = {
                'make': vehicle_data.get('make', 'Unknown'),
                'model': vehicle_data.get('model', 'Unknown'),
                'year': vehicle_data.get('year', 'Unknown'),
                'price': vehicle_data.get('price', 0),
                'vehicle_type': vehicle_data.get('vehicle_type', 'vehicle'),
                'features': vehicle_data.get('features', [])[:5],  # Limit features
                'description': vehicle_data.get('description', '')[:200]  # Limit description
            }

            user_preferences = user_profile.get('preferences', {})
            user_context = {
                'search_query': search_query,
                'preferred_brands': user_preferences.get('preferred_brands', []),
                'price_range': user_preferences.get('price_range', {}),
                'vehicle_types': user_preferences.get('vehicle_types', []),
                'features_priority': user_preferences.get('features_priority', [])
            }

            # Craft the prompt
            prompt = f"""
            You are an expert automotive recommendation assistant for Otto.AI. Generate a personalized, compelling explanation for why this vehicle is recommended to a user.

            VEHICLE DETAILS:
            - {vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}
            - Price: ${vehicle_info['price']:,.0f}
            - Type: {vehicle_info['vehicle_type']}
            - Key Features: {', '.join(vehicle_info['features'][:3])}
            - Description: {vehicle_info['description']}

            USER PROFILE:
            - Search Query: "{user_context['search_query'] or 'No specific search'}"
            - Preferred Brands: {', '.join(user_context['preferred_brands']) or 'No preference'}
            - Price Range: {user_context['price_range'] or 'Flexible'}
            - Vehicle Types: {', '.join(user_context['vehicle_types']) or 'Open to all types'}

            RECOMMENDATION FACTORS:
            - Match Confidence: {confidence_score:.1%}
            - Personalization Factors: {', '.join(supporting_factors)}

            TASK:
            Write a concise, personalized explanation (2-3 sentences) that clearly explains why this vehicle is a great match for this specific user. Focus on:
            1. Personal relevance to their preferences and search
            2. Key features that match their needs
            3. Value proposition or unique selling points
            4. Natural, conversational tone

            Explanation:
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert automotive recommendation assistant. Write personalized, helpful vehicle recommendations in a natural, conversational tone."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated GPT-4 explanation for {vehicle_info['make']} {vehicle_info['model']}")
            return explanation

        except Exception as e:
            logger.error(f"Error generating GPT-4 explanation: {e}")
            raise

    async def _generate_template_explanation(
        self,
        recommendation: Recommendation,
        user_profile: Dict[str, Any],
        search_query: Optional[str],
        context_vehicle_ids: Optional[List[str]]
    ) -> RecommendationExplanation:
        """Generate template-based explanation as fallback"""
        reasoning_type = "template_personalized"
        explanation_parts = []
        confidence_score = recommendation.recommendation_score
        supporting_factors = recommendation.personalization_factors

        # Build explanation based on personalization factors
        if "similar_users_preferences" in supporting_factors:
            explanation_parts.append("Users with similar preferences also liked this vehicle")

        if "content_match" in supporting_factors:
            explanation_parts.append("This vehicle matches your stated preferences")

        if "similar_to_viewed" in supporting_factors:
            explanation_parts.append("Similar to vehicles you've recently viewed")

        # Add specific preference matches
        vehicle_data = recommendation.vehicle_data
        user_preferences = user_profile.get('preferences', {})

        preference_matches = []
        if 'preferred_brands' in user_preferences:
            if vehicle_data.get('make') in user_preferences['preferred_brands']:
                preference_matches.append(f"matches your preference for {vehicle_data.get('make')} vehicles")

        if preference_matches:
            explanation_parts.append(f"It {', '.join(preference_matches)}")

        # Add search query relevance
        if search_query:
            explanation_parts.append(f"Relevant to your search for '{search_query}'")

        # Combine explanation parts
        if explanation_parts:
            explanation = "This vehicle is recommended because " + ". ".join(explanation_parts) + "."
        else:
            explanation = "This vehicle matches your profile and preferences."

        # Calculate user relevance score
        user_relevance_score = confidence_score

        return RecommendationExplanation(
            reasoning_type=reasoning_type,
            explanation=explanation,
            confidence_score=confidence_score,
            supporting_factors=supporting_factors,
            user_relevance_score=user_relevance_score
        )

    async def _calculate_trending_score(self, vehicle_id: str) -> Optional[float]:
        """Calculate trending score for vehicle"""
        try:
            # This would integrate with analytics service
            # For now, return random trending score
            return random.uniform(0.0, 1.0)
        except Exception as e:
            logger.error(f"Error calculating trending score: {str(e)}")
            return None

    async def _get_urgency_indicators(self, vehicle_id: str) -> List[str]:
        """Get urgency indicators for vehicle"""
        try:
            indicators = []

            # This would integrate with inventory and analytics services
            # For now, return mock urgency indicators
            if random.random() < 0.2:  # 20% chance of high demand
                indicators.append("high_demand")

            if random.random() < 0.1:  # 10% chance of limited availability
                indicators.append("limited_availability")

            if random.random() < 0.15:  # 15% chance of price drop
                indicators.append("price_drop")

            return indicators

        except Exception as e:
            logger.error(f"Error getting urgency indicators: {str(e)}")
            return []

    def _get_ab_test_group(self, user_id: str) -> str:
        """Determine A/B test group for user"""
        # Consistent hashing for group assignment
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        group_index = hash_value % len(self.ab_test_groups)
        return list(self.ab_test_groups.keys())[group_index]

    def _generate_cache_key(
        self,
        user_id: str,
        context_vehicle_ids: Optional[List[str]],
        search_query: Optional[str],
        recommendation_type: RecommendationType,
        limit: int
    ) -> str:
        """Generate cache key for recommendations"""
        key_parts = [
            user_id,
            recommendation_type.value,
            str(limit),
            str(context_vehicle_ids or []),
            search_query or ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[RecommendationResult]:
        """Get recommendations from cache"""
        if cache_key in self.recommendation_cache:
            result, timestamp = self.recommendation_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                result.cached = True
                return result
            else:
                del self.recommendation_cache[cache_key]
        return None

    async def _cache_result(self, cache_key: str, result: RecommendationResult) -> None:
        """Cache recommendation result"""
        self.recommendation_cache[cache_key] = (result, datetime.now())

        # Clean old cache entries if too many
        if len(self.recommendation_cache) > 1000:
            # Remove oldest entries
            sorted_items = sorted(self.recommendation_cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_items[:200]:  # Remove oldest 200
                del self.recommendation_cache[key]

    async def process_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Process user feedback on recommendations"""
        try:
            user_id = feedback_data.get('user_id')
            vehicle_id = feedback_data.get('vehicle_id')
            feedback_type = feedback_data.get('feedback_type')
            feedback_score = feedback_data.get('feedback_score')

            logger.info(f"Processing feedback: {feedback_type} for user {user_id}, vehicle {vehicle_id}")

            # This would integrate with feedback processing service
            # For now, just log the feedback
            logger.info(f"Feedback processed: {feedback_data}")

        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")