"""
Comprehensive Unit Tests for Vehicle Recommendation Engine

Tests for Story 1-5: Build Vehicle Comparison and Recommendation Engine
Covers all recommendation algorithms and personalization features.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.recommendation.recommendation_engine import RecommendationEngine, RecommendationResult
from src.api.vehicle_comparison_api import (
    RecommendationRequest, RecommendationResponse, Recommendation,
    RecommendationExplanation, RecommendationType, UserInteraction,
    FeedbackRequest
)


class TestRecommendationEngine:
    """Test suite for RecommendationEngine"""

    @pytest.fixture
    def mock_vehicle_db_service(self):
        """Mock vehicle database service"""
        mock_db = Mock()
        mock_db.get_vehicle_by_id = AsyncMock()
        mock_db.get_similar_vehicles = AsyncMock(return_value=[])
        mock_db.search_vehicles = AsyncMock(return_value=[])
        mock_db.get_trending_vehicles = AsyncMock(return_value=[])
        return mock_db

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service"""
        mock_embedding = Mock()
        mock_embedding.generate_embeddings = AsyncMock()
        return mock_embedding

    @pytest.fixture
    def recommendation_engine(self, mock_vehicle_db_service, mock_embedding_service):
        """Create RecommendationEngine instance with mocked dependencies"""
        return RecommendationEngine(mock_vehicle_db_service, mock_embedding_service)

    @pytest.fixture
    def sample_vehicles(self):
        """Sample vehicle data for testing"""
        return [
            {
                'id': 'vehicle_1',
                'vin': '1HGCM82633A123456',
                'year': 2022,
                'make': 'Toyota',
                'model': 'Camry',
                'trim': 'SE',
                'vehicle_type': 'Sedan',
                'price': 25000.0,
                'mileage': 15000,
                'description': 'Well-maintained Toyota Camry with excellent features',
                'features': ['bluetooth', 'backup camera', 'apple carplay', 'android auto', 'leather seats'],
                'exterior_color': 'Silver',
                'interior_color': 'Black',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['image1.jpg', 'image2.jpg']
            },
            {
                'id': 'vehicle_2',
                'vin': '2HGCM82633A654321',
                'year': 2021,
                'make': 'Honda',
                'model': 'Accord',
                'trim': 'EX',
                'vehicle_type': 'Sedan',
                'price': 26000.0,
                'mileage': 20000,
                'description': 'Honda Accord in great condition with low mileage',
                'features': ['bluetooth', 'backup camera', 'android auto', 'heated seats', 'sunroof'],
                'exterior_color': 'White',
                'interior_color': 'Beige',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['image3.jpg', 'image4.jpg']
            },
            {
                'id': 'vehicle_3',
                'vin': '3HGCM82633A111222',
                'year': 2023,
                'make': 'Toyota',
                'model': 'RAV4',
                'trim': 'XLE',
                'vehicle_type': 'SUV',
                'price': 32000.0,
                'mileage': 8000,
                'description': 'Nearly new Toyota RAV4 with advanced safety features',
                'features': ['bluetooth', 'backup camera', 'apple carplay', 'android auto', 'blind spot monitoring', 'lane keeping assist'],
                'exterior_color': 'Blue',
                'interior_color': 'Gray',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['image5.jpg', 'image6.jpg']
            }
        ]

    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile for testing"""
        return {
            'user_id': 'test_user_123',
            'preferences': {
                'preferred_brands': ['Toyota', 'Honda', 'Ford'],
                'price_range': {'min': 20000, 'max': 40000},
                'vehicle_types': ['SUV', 'Sedan'],
                'must_have_features': ['bluetooth', 'backup camera'],
                'avoid_features': ['manual transmission'],
                'price_sensitivity': 0.7,
                'brand_loyalty': 0.6,
                'feature_importance': 0.8
            },
            'interaction_history': {
                'viewed_vehicles': ['vehicle_1', 'vehicle_2'],
                'saved_vehicles': ['vehicle_1'],
                'compared_vehicles': [['vehicle_1', 'vehicle_2']],
                'search_history': ['safe family SUV', 'fuel efficient sedan']
            },
            'demographics': {
                'age': 35,
                'location': {'city': 'Seattle', 'state': 'WA'},
                'family_size': 4
            }
        }

    @pytest.mark.asyncio
    async def test_get_recommendations_hybrid_success(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test successful hybrid recommendation generation"""
        # Setup mocks
        mock_vehicle_db_service.get_similar_vehicles.return_value = sample_vehicles[:2]
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles
        mock_vehicle_db_service.get_trending_vehicles.return_value = [sample_vehicles[2]]

        # Test recommendation generation
        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            context_vehicle_ids=['vehicle_1'],
            search_query='safe family car',
            recommendation_type=RecommendationType.HYBRID,
            limit=5,
            include_explanations=True
        )

        # Verify results
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 5
        assert result.algorithm_version is not None
        assert result.a_b_test_group in recommendation_engine.ab_test_groups.keys()

        # Check recommendation structure
        for rec in result.recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.vehicle_id is not None
            assert rec.vehicle_data is not None
            assert 0 <= rec.recommendation_score <= 1
            assert 0 <= rec.match_percentage <= 100
            assert rec.explanation is not None
            assert isinstance(rec.personalization_factors, list)
            assert isinstance(rec.urgency_indicators, list)

    @pytest.mark.asyncio
    async def test_get_recommendations_collaborative_filtering(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test collaborative filtering recommendations"""
        # Setup mocks
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            recommendation_type=RecommendationType.COLLABORATIVE,
            limit=3,
            include_explanations=True
        )

        assert isinstance(result, RecommendationResult)
        # Collaborative filtering might return fewer results if no similar users found
        assert len(result.recommendations) <= 3

    @pytest.mark.asyncio
    async def test_get_recommendations_content_based(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test content-based filtering recommendations"""
        # Setup mocks
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            search_query='fuel efficient SUV',
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=3,
            include_explanations=True
        )

        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 3

    @pytest.mark.asyncio
    async def test_get_recommendations_similarity_based(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test similarity-based recommendations"""
        # Setup mocks
        mock_vehicle_db_service.get_similar_vehicles.return_value = sample_vehicles[1:]

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            context_vehicle_ids=['vehicle_1'],
            recommendation_type=RecommendationType.SIMILARITY,
            limit=2
        )

        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 2

    @pytest.mark.asyncio
    async def test_get_recommendations_no_candidates(self, recommendation_engine, mock_vehicle_db_service):
        """Test recommendations when no candidate vehicles are available"""
        # Setup mocks to return empty lists
        mock_vehicle_db_service.get_similar_vehicles.return_value = []
        mock_vehicle_db_service.search_vehicles.return_value = []
        mock_vehicle_db_service.get_trending_vehicles.return_value = []

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            limit=5
        )

        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) == 0

    @pytest.mark.asyncio
    async def test_get_user_profile(self, recommendation_engine):
        """Test user profile generation"""
        user_profile = await recommendation_engine._get_user_profile('test_user_123')

        assert isinstance(user_profile, dict)
        assert 'user_id' in user_profile
        assert 'preferences' in user_profile
        assert 'interaction_history' in user_profile
        assert 'demographics' in user_profile

        # Check preferences structure
        preferences = user_profile['preferences']
        assert 'preferred_brands' in preferences
        assert 'price_range' in preferences
        assert 'vehicle_types' in preferences

    @pytest.mark.asyncio
    async def test_get_candidate_vehicles(self, recommendation_engine, sample_vehicles, sample_user_profile, mock_vehicle_db_service):
        """Test candidate vehicle generation"""
        # Setup mocks
        mock_vehicle_db_service.get_similar_vehicles.return_value = sample_vehicles[:1]
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles[1:]
        mock_vehicle_db_service.get_trending_vehicles.return_value = sample_vehicles[2:]

        candidates = await recommendation_engine._get_candidate_vehicles(
            context_vehicle_ids=['vehicle_1'],
            user_profile=sample_user_profile,
            limit=10
        )

        assert isinstance(candidates, list)
        assert len(candidates) <= 10
        # Should remove context vehicles from candidates
        candidate_ids = [v['id'] for v in candidates]
        assert 'vehicle_1' not in candidate_ids

    @pytest.mark.asyncio
    async def test_create_user_preference_vector(self, recommendation_engine, sample_user_profile):
        """Test user preference vector creation"""
        preference_vector = await recommendation_engine._create_user_preference_vector(sample_user_profile)

        assert isinstance(preference_vector, dict)
        assert 'brands' in preference_vector
        assert 'price_range' in preference_vector
        assert 'vehicle_types' in preference_vector
        assert 'must_have_features' in preference_vector
        assert 'avoid_features' in preference_vector

    @pytest.mark.asyncio
    async def test_calculate_content_similarity(self, recommendation_engine, sample_vehicles, sample_user_profile):
        """Test content similarity calculation"""
        vehicle = sample_vehicles[0]
        user_preference_vector = await recommendation_engine._create_user_preference_vector(sample_user_profile)

        similarity_score = await recommendation_engine._calculate_content_similarity(
            vehicle, user_preference_vector, 'safe family car'
        )

        assert isinstance(similarity_score, float)
        assert 0 <= similarity_score <= 1

    @pytest.mark.asyncio
    async def test_calculate_query_relevance(self, recommendation_engine, sample_vehicles):
        """Test query relevance calculation"""
        vehicle = sample_vehicles[0]
        relevance_score = await recommendation_engine._calculate_query_relevance(
            vehicle, 'Toyota Camry'
        )

        assert isinstance(relevance_score, float)
        assert 0 <= relevance_score <= 1

        # Test with no query
        relevance_score = await recommendation_engine._calculate_query_relevance(vehicle, None)
        assert relevance_score == 0.0

    @pytest.mark.asyncio
    async def test_get_similar_users(self, recommendation_engine):
        """Test similar user identification"""
        similar_users = await recommendation_engine._get_similar_users('test_user_123', 10)

        assert isinstance(similar_users, list)
        assert len(similar_users) <= 10

        # Check similar user structure
        for user in similar_users:
            assert 'user_id' in user
            assert 'similarity_score' in user
            assert 'liked_vehicles' in user
            assert 0 <= user['similarity_score'] <= 1

    @pytest.mark.asyncio
    async def test_generate_recommendation_explanation(self, recommendation_engine, sample_vehicles, sample_user_profile):
        """Test recommendation explanation generation"""
        vehicle = sample_vehicles[0]
        recommendation = Recommendation(
            vehicle_id=vehicle['id'],
            vehicle_data=vehicle,
            recommendation_score=0.85,
            match_percentage=85,
            explanation=None,
            personalization_factors=["content_match", "similar_to_viewed"],
            trending_score=None,
            urgency_indicators=[]
        )

        explanation = await recommendation_engine._generate_recommendation_explanation(
            recommendation, sample_user_profile, 'safe family car', ['vehicle_2']
        )

        assert isinstance(explanation, RecommendationExplanation)
        assert explanation.reasoning_type is not None
        assert explanation.explanation is not None
        assert len(explanation.explanation) > 0
        assert 0 <= explanation.confidence_score <= 1
        assert isinstance(explanation.supporting_factors, list)
        assert 0 <= explanation.user_relevance_score <= 1

    @pytest.mark.asyncio
    async def test_calculate_trending_score(self, recommendation_engine):
        """Test trending score calculation"""
        trending_score = await recommendation_engine._calculate_trending_score('vehicle_1')

        # Should return either None (no data) or a float between 0 and 1
        if trending_score is not None:
            assert isinstance(trending_score, float)
            assert 0 <= trending_score <= 1

    @pytest.mark.asyncio
    async def test_get_urgency_indicators(self, recommendation_engine):
        """Test urgency indicator generation"""
        urgency_indicators = await recommendation_engine._get_urgency_indicators('vehicle_1')

        assert isinstance(urgency_indicators, list)
        # All indicators should be from valid set
        valid_indicators = ['high_demand', 'limited_availability', 'price_drop']
        for indicator in urgency_indicators:
            assert indicator in valid_indicators

    def test_get_ab_test_group(self, recommendation_engine):
        """Test A/B test group assignment"""
        user_id = 'test_user_123'
        group = recommendation_engine._get_ab_test_group(user_id)

        assert group in recommendation_engine.ab_test_groups.keys()

        # Should be consistent for same user
        group2 = recommendation_engine._get_ab_test_group(user_id)
        assert group == group2

        # Different users might get different groups (statistically)
        different_user = 'different_user_456'
        group3 = recommendation_engine._get_ab_test_group(different_user)
        assert group3 in recommendation_engine.ab_test_groups.keys()

    def test_generate_cache_key(self, recommendation_engine):
        """Test cache key generation"""
        cache_key = recommendation_engine._generate_cache_key(
            user_id='test_user_123',
            context_vehicle_ids=['vehicle_1', 'vehicle_2'],
            search_query='safe SUV',
            recommendation_type=RecommendationType.HYBRID,
            limit=10
        )

        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length

        # Should generate same key for same parameters
        cache_key2 = recommendation_engine._generate_cache_key(
            user_id='test_user_123',
            context_vehicle_ids=['vehicle_1', 'vehicle_2'],
            search_query='safe SUV',
            recommendation_type=RecommendationType.HYBRID,
            limit=10
        )
        assert cache_key == cache_key2

        # Should generate different key for different parameters
        cache_key3 = recommendation_engine._generate_cache_key(
            user_id='test_user_123',
            context_vehicle_ids=['vehicle_1'],
            search_query='safe SUV',
            recommendation_type=RecommendationType.HYBRID,
            limit=10
        )
        assert cache_key != cache_key3

    @pytest.mark.asyncio
    async def test_cache_operations(self, recommendation_engine):
        """Test caching functionality"""
        cache_key = 'test_cache_key'
        test_result = RecommendationResult(
            recommendations=[],
            algorithm_version='1.0.0',
            a_b_test_group='control',
            cached=False
        )

        # Test cache miss
        cached_result = await recommendation_engine._get_from_cache(cache_key)
        assert cached_result is None

        # Test cache set and get
        await recommendation_engine._cache_result(cache_key, test_result)
        cached_result = await recommendation_engine._get_from_cache(cache_key)
        assert cached_result is not None
        assert cached_result.cached is True
        assert cached_result.algorithm_version == '1.0.0'

    @pytest.mark.asyncio
    async def test_process_feedback(self, recommendation_engine):
        """Test feedback processing"""
        feedback_data = {
            'user_id': 'test_user_123',
            'recommendation_id': 'rec_123',
            'vehicle_id': 'vehicle_1',
            'feedback_type': 'helpful',
            'feedback_score': 0.9,
            'feedback_text': 'Great recommendation!',
            'timestamp': datetime.now().isoformat()
        }

        # Should not raise exception
        await recommendation_engine.process_feedback(feedback_data)

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test performance with larger dataset"""
        # Setup mocks to return more vehicles
        large_vehicle_list = []
        for i in range(50):
            vehicle = sample_vehicles[0].copy()
            vehicle['id'] = f'vehicle_{i}'
            vehicle['price'] = 20000 + (i * 1000)
            large_vehicle_list.append(vehicle)

        mock_vehicle_db_service.search_vehicles.return_value = large_vehicle_list[:30]
        mock_vehicle_db_service.get_trending_vehicles.return_value = large_vehicle_list[30:]

        start_time = time.time()
        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            limit=20
        )
        processing_time = time.time() - start_time

        # Should complete within reasonable time
        assert processing_time < 3.0  # 3 seconds
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) <= 20

    @pytest.mark.asyncio
    async def test_edge_case_empty_user_profile(self, recommendation_engine):
        """Test edge case with empty user profile"""
        with patch.object(recommendation_engine, '_get_user_profile') as mock_get_profile:
            mock_get_profile.return_value = {
                'user_id': 'empty_user',
                'preferences': {},
                'interaction_history': {},
                'demographics': {}
            }

            result = await recommendation_engine.get_recommendations(
                user_id='empty_user',
                limit=5
            )

            assert isinstance(result, RecommendationResult)

    @pytest.mark.asyncio
    async def test_edge_case_invalid_recommendation_type(self, recommendation_engine):
        """Test edge case with invalid recommendation type"""
        # Should handle gracefully even with unexpected type
        with patch('src.api.vehicle_comparison_api.RecommendationType', return_value='invalid_type'):
            result = await recommendation_engine.get_recommendations(
                user_id='test_user_123',
                recommendation_type='invalid_type',
                limit=5
            )

            assert isinstance(result, RecommendationResult)

    @pytest.mark.asyncio
    async def test_personalization_factors_generation(self, recommendation_engine, sample_vehicles, sample_user_profile, mock_vehicle_db_service):
        """Test personalization factors in recommendations"""
        # Setup mocks
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            search_query='SUV',
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=2,
            include_explanations=True
        )

        for recommendation in result.recommendations:
            assert isinstance(recommendation.personalization_factors, list)
            # Should have at least one personalization factor
            assert len(recommendation.personalization_factors) > 0

    @pytest.mark.asyncio
    async def test_recommendation_score_normalization(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test recommendation score normalization"""
        # Setup mocks
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles

        result = await recommendation_engine.get_recommendations(
            user_id='test_user_123',
            limit=10
        )

        for recommendation in result.recommendations:
            assert 0 <= recommendation.recommendation_score <= 1
            assert 0 <= recommendation.match_percentage <= 100
            # Match percentage should align with score
            assert abs(recommendation.match_percentage - (recommendation.recommendation_score * 100)) < 1


class TestRecommendationEngineIntegration:
    """Integration tests for RecommendationEngine"""

    @pytest.mark.asyncio
    async def test_end_to_end_recommendation_flow(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service, mock_embedding_service):
        """Test complete recommendation flow with feedback loop"""
        # Setup comprehensive mocks
        mock_vehicle_db_service.get_similar_vehicles.return_value = sample_vehicles[:2]
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles
        mock_vehicle_db_service.get_trending_vehicles.return_value = [sample_vehicles[2]]

        # Generate initial recommendations
        result = await recommendation_engine.get_recommendations(
            user_id='integration_test_user',
            context_vehicle_ids=['vehicle_1'],
            search_query='family SUV with safety features',
            recommendation_type=RecommendationType.HYBRID,
            limit=5,
            include_explanations=True
        )

        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) > 0

        # Test feedback processing
        for rec in result.recommendations[:2]:  # Test feedback for first 2 recommendations
            feedback_data = {
                'user_id': 'integration_test_user',
                'recommendation_id': result.recommendation_id,
                'vehicle_id': rec.vehicle_id,
                'feedback_type': 'helpful',
                'feedback_score': 0.8
            }

            await recommendation_engine.process_feedback(feedback_data)

        # Verify recommendations have explanations
        for rec in result.recommendations:
            assert rec.explanation is not None
            assert rec.explanation.explanation is not None
            assert len(rec.explanation.explanation) > 0
            assert 0 <= rec.explanation.confidence_score <= 1

        # Verify A/B testing group assignment
        assert result.a_b_test_group is not None
        assert result.a_b_test_group in recommendation_engine.ab_test_groups

    @pytest.mark.asyncio
    async def test_cache_hit_scenario(self, recommendation_engine, sample_vehicles, mock_vehicle_db_service):
        """Test cache hit scenario"""
        # Setup mocks
        mock_vehicle_db_service.search_vehicles.return_value = sample_vehicles

        user_id = 'cache_test_user'
        request_params = {
            'user_id': user_id,
            'search_query': 'Toyota SUV',
            'recommendation_type': RecommendationType.CONTENT_BASED,
            'limit': 5,
            'include_explanations': True
        }

        # First call - cache miss
        start_time = time.time()
        result1 = await recommendation_engine.get_recommendations(**request_params)
        first_call_time = time.time() - start_time

        # Second call - cache hit
        start_time = time.time()
        result2 = await recommendation_engine.get_recommendations(**request_params)
        second_call_time = time.time() - start_time

        # Verify results are the same
        assert len(result1.recommendations) == len(result2.recommendations)
        assert result1.algorithm_version == result2.algorithm_version
        assert result1.a_b_test_group == result2.a_b_test_group

        # Second call should be faster due to caching
        assert second_call_time < first_call_time

        # Verify cache was used
        assert result2.cached is True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])