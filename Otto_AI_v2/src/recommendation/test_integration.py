"""
Integration and End-to-End Tests for Vehicle Comparison and Recommendation Engine

Tests for Story 1-5: Build Vehicle Comparison and Recommendation Engine
Tests the complete system integration and real-world usage scenarios.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.api.vehicle_comparison_api import (
    VehicleComparisonRequest, VehicleComparisonResponse,
    RecommendationRequest, RecommendationResponse,
    RecommendationType, UserInteraction, FeedbackRequest
)
from src.recommendation.comparison_engine import ComparisonEngine
from src.recommendation.recommendation_engine import RecommendationEngine
from src.recommendation.interaction_tracker import InteractionTracker, InteractionType


class TestSystemIntegration:
    """Integration tests for the complete system"""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        mock_vehicle_db = Mock()
        mock_vehicle_db.get_vehicle_by_id = AsyncMock()
        mock_vehicle_db.get_similar_vehicles = AsyncMock(return_value=[])
        mock_vehicle_db.search_vehicles = AsyncMock(return_value=[])
        mock_vehicle_db.get_trending_vehicles = AsyncMock(return_value=[])

        mock_embedding_service = Mock()
        mock_embedding_service.generate_embeddings = AsyncMock()

        return {
            'vehicle_db': mock_vehicle_db,
            'embedding_service': mock_embedding_service
        }

    @pytest.fixture
    def engines(self, mock_services):
        """Create engine instances with mocked services"""
        comparison_engine = ComparisonEngine(
            mock_services['vehicle_db'],
            mock_services['embedding_service']
        )
        recommendation_engine = RecommendationEngine(
            mock_services['vehicle_db'],
            mock_services['embedding_service']
        )
        interaction_tracker = InteractionTracker()

        return {
            'comparison': comparison_engine,
            'recommendation': recommendation_engine,
            'tracker': interaction_tracker
        }

    @pytest.fixture
    def sample_vehicles(self):
        """Realistic sample vehicle data"""
        return [
            {
                'id': 'toyota_camry_2022',
                'vin': '1HGCM82633A123456',
                'year': 2022,
                'make': 'Toyota',
                'model': 'Camry',
                'trim': 'SE',
                'vehicle_type': 'Sedan',
                'price': 27500.0,
                'mileage': 12000,
                'description': 'Excellent condition Toyota Camry SE with premium features and low mileage. One owner, regularly serviced, non-smoker.',
                'features': [
                    'bluetooth', 'backup camera', 'apple carplay', 'android auto',
                    'leather seats', 'heated front seats', 'dual zone climate control',
                    'blind spot monitoring', 'lane departure warning', 'adaptive cruise control'
                ],
                'exterior_color': 'Midnight Black Metallic',
                'interior_color': 'Black Leather',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['camry_ext1.jpg', 'camry_int1.jpg', 'camry_ext2.jpg'],
                'engine': '2.5L 4-Cylinder',
                'transmission': '8-Speed Automatic',
                'horsepower': 203,
                'torque': 184,
                'fuel_efficiency_city': 28,
                'fuel_efficiency_hwy': 39,
                'safety_rating': 5,
                'drivetrain': 'FWD',
                'acceleration_0_60': 7.9,
                'top_speed': 135,
                'length': 192.1,
                'width': 72.4,
                'height': 56.9,
                'wheelbase': 111.2,
                'cargo_capacity': 15.1,
                'airbags': 10
            },
            {
                'id': 'honda_accord_2023',
                'vin': '2HGCM82633A654321',
                'year': 2023,
                'make': 'Honda',
                'model': 'Accord',
                'trim': 'EX-L',
                'vehicle_type': 'Sedan',
                'price': 28900.0,
                'mileage': 8000,
                'description': 'Nearly new Honda Accord EX-L with advanced safety features and premium comfort options. Dealer maintained with full service history.',
                'features': [
                    'bluetooth', 'backup camera', 'apple carplay', 'android auto',
                    'leather seats', 'heated front seats', 'ventilated front seats',
                    'moonroof', 'premium audio system', 'wireless charging pad',
                    'lane keeping assist', 'adaptive cruise control', 'traffic sign recognition'
                ],
                'exterior_color': 'Platinum White Pearl',
                'interior_color': 'Gray Leather',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['accord_ext1.jpg', 'accord_int1.jpg'],
                'engine': '1.5L Turbocharged 4-Cylinder',
                'transmission': 'CVT',
                'horsepower': 192,
                'torque': 192,
                'fuel_efficiency_city': 32,
                'fuel_efficiency_hwy': 42,
                'safety_rating': 5,
                'drivetrain': 'FWD',
                'acceleration_0_60': 7.2,
                'top_speed': 130,
                'length': 195.7,
                'width': 73.3,
                'height': 57.1,
                'wheelbase': 111.4,
                'cargo_capacity': 16.7,
                'airbags': 10
            },
            {
                'id': 'toyota_rav4_2023',
                'vin': '3HGCM82633A111222',
                'year': 2023,
                'make': 'Toyota',
                'model': 'RAV4',
                'trim': 'Limited',
                'vehicle_type': 'SUV',
                'price': 35900.0,
                'mileage': 5000,
                'description': 'Brand new Toyota RAV4 Limited with hybrid powertrain and all-wheel drive. Loaded with premium features and advanced safety technology.',
                'features': [
                    'bluetooth', 'backup camera', 'apple carplay', 'android auto',
                    'leather seats', 'heated front seats', 'heated steering wheel',
                    'panoramic sunroof', 'premium audio', 'head-up display',
                    'blind spot monitoring', 'lane departure warning', 'adaptive cruise control',
                    'parking assist', '360-degree camera', 'all-wheel drive'
                ],
                'exterior_color': 'Ice Cap',
                'interior_color': 'Saddle Tan Leather',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['rav4_ext1.jpg', 'rav4_int1.jpg', 'rav4_ext2.jpg'],
                'engine': '2.5L Hybrid 4-Cylinder',
                'transmission': 'CVT',
                'horsepower': 219,
                'torque': 163,
                'fuel_efficiency_city': 41,
                'fuel_efficiency_hwy': 38,
                'safety_rating': 5,
                'drivetrain': 'AWD',
                'acceleration_0_60': 8.1,
                'top_speed': 120,
                'length': 180.9,
                'width': 73.0,
                'height': 67.0,
                'wheelbase': 105.9,
                'cargo_capacity': 37.6,
                'airbags': 10
            },
            {
                'id': 'ford_escape_2022',
                'vin': '4HGCM82633A999999',
                'year': 2022,
                'make': 'Ford',
                'model': 'Escape',
                'trim': 'Titanium',
                'vehicle_type': 'SUV',
                'price': 31900.0,
                'mileage': 15000,
                'description': 'Well-maintained Ford Escape Titanium with advanced technology features. Perfect for families needing versatility and modern amenities.',
                'features': [
                    'bluetooth', 'backup camera', 'apple carplay', 'android auto',
                    'heated seats', 'heated steering wheel', 'remote start',
                    'panoramic sunroof', 'premium audio', 'wireless charging',
                    'blind spot monitoring', 'lane keeping assist', 'adaptive cruise control'
                ],
                'exterior_color': 'Velocity Blue',
                'interior_color': 'Charcoal Black',
                'city': 'Seattle',
                'state': 'WA',
                'condition': 'excellent',
                'images': ['escape_ext1.jpg', 'escape_int1.jpg'],
                'engine': '2.0L EcoBoost 4-Cylinder',
                'transmission': '8-Speed Automatic',
                'horsepower': 250,
                'torque': 280,
                'fuel_efficiency_city': 23,
                'fuel_efficiency_hwy': 31,
                'safety_rating': 5,
                'drivetrain': 'AWD',
                'acceleration_0_60': 7.1,
                'top_speed': 125,
                'length': 178.1,
                'width': 72.4,
                'height': 66.7,
                'wheelbase': 106.7,
                'cargo_capacity': 34.4,
                'airbags': 10
            }
        ]

    @pytest.mark.asyncio
    async def test_complete_user_journey_scenario(self, engines, sample_vehicles, mock_services):
        """Test complete user journey from search to comparison to recommendations"""
        user_id = 'integration_test_user'
        session_id = 'test_session_123'

        # Setup mock services to return sample vehicles
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles
        mock_services['vehicle_db'].get_trending_vehicles.return_value = [sample_vehicles[2]]
        mock_services['embedding_service'].generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        )

        # Step 1: User searches for vehicles
        search_query = "family SUV with good safety rating under $40000"

        # Track search interaction
        await engines['tracker'].track_interaction({
            'user_id': user_id,
            'session_id': session_id,
            'interaction_type': InteractionType.SEARCH,
            'vehicle_ids': [],
            'interaction_data': {'query': search_query},
            'context': {'source': 'homepage_search'},
            'timestamp': datetime.now()
        })

        # Step 2: Get recommendations based on search
        recommendations_result = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            search_query=search_query,
            recommendation_type=RecommendationType.HYBRID,
            limit=3,
            include_explanations=True
        )

        assert recommendations_result.recommendations is not None
        assert len(recommendations_result.recommendations) > 0
        print(f"Found {len(recommendations_result.recommendations)} recommendations")

        # Step 3: User views and saves some vehicles
        viewed_vehicles = []
        for i, rec in enumerate(recommendations_result.recommendations[:2]):
            vehicle_id = rec.vehicle_id

            # Track view interaction
            await engines['tracker'].track_interaction({
                'user_id': user_id,
                'session_id': session_id,
                'interaction_type': InteractionType.VIEW,
                'vehicle_ids': [vehicle_id],
                'interaction_data': {
                    'source': 'recommendations',
                    'position': i,
                    'duration': 45
                },
                'timestamp': datetime.now() + timedelta(seconds=i * 30)
            })

            viewed_vehicles.append(vehicle_id)

            # Track recommendation click
            await engines['tracker'].track_interaction({
                'user_id': user_id,
                'session_id': session_id,
                'interaction_type': InteractionType.RECOMMENDATION_CLICK,
                'vehicle_ids': [vehicle_id],
                'interaction_data': {
                    'recommendation_id': recommendations_result.recommendation_id,
                    'position': i,
                    'score': rec.recommendation_score
                },
                'timestamp': datetime.now() + timedelta(seconds=i * 30 + 10)
            })

            # Save the first vehicle
            if i == 0:
                await engines['tracker'].track_interaction({
                    'user_id': user_id,
                    'session_id': session_id,
                    'interaction_type': InteractionType.SAVE,
                    'vehicle_ids': [vehicle_id],
                    'interaction_data': {
                        'source': 'vehicle_details',
                        'list': 'favorites'
                    },
                    'timestamp': datetime.now() + timedelta(seconds=i * 30 + 20)
                })

        # Step 4: Compare vehicles
        if len(viewed_vehicles) >= 2:
            comparison_result = await engines['comparison'].compare_vehicles(
                vehicle_ids=viewed_vehicles[:2],
                include_semantic_similarity=True,
                include_price_analysis=True,
                user_id=user_id
            )

            assert comparison_result.comparison_results is not None
            assert len(comparison_result.comparison_results) == 2
            assert len(comparison_result.feature_differences) > 0
            print(f"Comparison generated with {len(comparison_result.feature_differences)} feature differences")

            # Track comparison interaction
            await engines['tracker'].track_comparison(
                user_id=user_id,
                vehicle_ids=viewed_vehicles[:2],
                comparison_id=f'comp_{int(time.time())}',
                processing_time=1.5
            )

        # Step 5: Get personalized recommendations based on user behavior
        personalized_recommendations = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            context_vehicle_ids=viewed_vehicles,
            recommendation_type=RecommendationType.HYBRID,
            limit=3,
            include_explanations=True
        )

        assert personalized_recommendations.recommendations is not None
        print(f"Generated {len(personalized_recommendations.recommendations)} personalized recommendations")

        # Verify personalization factors are present
        for rec in personalized_recommendations.recommendations:
            assert len(rec.personalization_factors) > 0
            print(f"Recommendation for {rec.vehicle_id}: {rec.personalization_factors}")

        # Step 6: Verify user profile was updated
        user_profile = await engines['tracker'].get_user_profile(user_id)
        assert user_profile.total_views >= len(viewed_vehicles)
        assert user_profile.total_saves >= 1
        assert user_profile.total_searches >= 1
        assert user_profile.total_comparisons >= 1 if len(viewed_vehicles) >= 2 else 0

        print(f"User profile updated: {user_profile.total_views} views, {user_profile.total_saves} saves")

    @pytest.mark.asyncio
    async def test_api_endpoint_simulation(self, engines, sample_vehicles, mock_services):
        """Test API-like endpoint simulation"""
        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['embedding_service'].generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )

        # Simulate POST /api/vehicles/compare
        comparison_request = VehicleComparisonRequest(
            vehicle_ids=['toyota_camry_2022', 'honda_accord_2023'],
            include_semantic_similarity=True,
            include_price_analysis=True,
            user_id='api_test_user'
        )

        # Process comparison request
        comparison_result = await engines['comparison'].compare_vehicles(
            vehicle_ids=comparison_request.vehicle_ids,
            include_semantic_similarity=comparison_request.include_semantic_similarity,
            include_price_analysis=comparison_request.include_price_analysis,
            user_id=comparison_request.user_id
        )

        # Verify response structure
        assert comparison_result.comparison_results is not None
        assert len(comparison_result.comparison_results) == 2
        assert comparison_result.recommendation_summary is not None

        # Simulate GET /api/recommendations/{user_id}
        recommendation_request = RecommendationRequest(
            user_id='api_test_user',
            context_vehicle_ids=['toyota_camry_2022'],
            search_query='reliable sedan',
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=5,
            include_explanations=True
        )

        recommendation_result = await engines['recommendation'].get_recommendations(
            user_id=recommendation_request.user_id,
            context_vehicle_ids=recommendation_request.context_vehicle_ids,
            search_query=recommendation_request.search_query,
            recommendation_type=recommendation_request.recommendation_type,
            limit=recommendation_request.limit,
            include_explanations=recommendation_request.include_explanations
        )

        # Verify recommendation response
        assert recommendation_result.recommendations is not None
        assert len(recommendation_result.recommendations) <= 5

        for rec in recommendation_result.recommendations:
            assert rec.explanation is not None
            assert rec.match_percentage >= 0
            assert rec.match_percentage <= 100

    @pytest.mark.asyncio
    async def test_performance_and_caching(self, engines, sample_vehicles, mock_services):
        """Test system performance and caching functionality"""
        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles
        mock_services['embedding_service'].generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )

        user_id = 'performance_test_user'
        vehicle_ids = ['toyota_camry_2022', 'honda_accord_2023', 'toyota_rav4_2023']

        # Test comparison performance
        comparison_times = []
        for i in range(5):
            start_time = time.time()
            result = await engines['comparison'].compare_vehicles(
                vehicle_ids=vehicle_ids[:2],  # Compare first 2 vehicles
                include_semantic_similarity=True,
                include_price_analysis=True,
                user_id=user_id
            )
            processing_time = time.time() - start_time
            comparison_times.append(processing_time)

            # Verify results consistency
            assert result.comparison_results is not None
            assert len(result.comparison_results) == 2

        avg_comparison_time = sum(comparison_times) / len(comparison_times)
        print(f"Average comparison time: {avg_comparison_time:.3f}s")
        assert avg_comparison_time < 2.0  # Should complete within 2 seconds

        # Test recommendation performance with caching
        recommendation_times = []
        for i in range(3):
            start_time = time.time()
            result = await engines['recommendation'].get_recommendations(
                user_id=user_id,
                context_vehicle_ids=vehicle_ids[:1],
                search_query='family car',
                recommendation_type=RecommendationType.HYBRID,
                limit=5,
                include_explanations=True
            )
            processing_time = time.time() - start_time
            recommendation_times.append(processing_time)

            # Verify results consistency
            assert result.recommendations is not None

        avg_recommendation_time = sum(recommendation_times) / len(recommendation_times)
        print(f"Average recommendation time: {avg_recommendation_time:.3f}s")
        assert avg_recommendation_time < 1.5  # Should complete within 1.5 seconds

        # Second set of calls should be faster due to caching
        start_time = time.time()
        cached_result = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            context_vehicle_ids=vehicle_ids[:1],
            search_query='family car',
            recommendation_type=RecommendationType.HYBRID,
            limit=5,
            include_explanations=True
        )
        cached_time = time.time() - start_time

        print(f"Cached recommendation time: {cached_time:.3f}s")
        # Cached call should be significantly faster
        assert cached_time < avg_recommendation_time * 0.5

    @pytest.mark.asyncio
    async def test_error_handling_and_edge_cases(self, engines):
        """Test error handling and edge cases"""
        user_id = 'edge_case_test_user'

        # Test with non-existent vehicles
        with pytest.raises(ValueError, match="Vehicles not found"):
            await engines['comparison'].compare_vehicles(
                vehicle_ids=['non_existent_vehicle_1', 'non_existent_vehicle_2']
            )

        # Test with insufficient vehicles for comparison
        with pytest.raises(ValueError, match="At least 2 vehicles required"):
            await engines['comparison'].compare_vehicles(
                vehicle_ids=['single_vehicle']
            )

        # Test with too many vehicles for comparison
        many_vehicles = [f'vehicle_{i}' for i in range(6)]
        with pytest.raises(ValueError, match="Maximum 4 vehicles allowed"):
            await engines['comparison'].compare_vehicles(
                vehicle_ids=many_vehicles
            )

        # Test recommendations with no user data
        with patch.object(engines['recommendation'], '_get_candidate_vehicles') as mock_candidates:
            mock_candidates.return_value = []

            result = await engines['recommendation'].get_recommendations(
                user_id=user_id,
                limit=5
            )

            # Should handle gracefully with empty results
            assert result.recommendations == []

    @pytest.mark.asyncio
    async def test_feedback_loop_integration(self, engines, sample_vehicles, mock_services):
        """Test feedback loop integration"""
        user_id = 'feedback_test_user'

        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles

        # Generate initial recommendations
        result = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            limit=3,
            include_explanations=True
        )

        assert len(result.recommendations) > 0

        # Process feedback for recommendations
        for i, rec in enumerate(result.recommendations):
            feedback_data = {
                'user_id': user_id,
                'recommendation_id': result.recommendation_id,
                'vehicle_id': rec.vehicle_id,
                'feedback_type': 'helpful' if i == 0 else 'not_helpful',
                'feedback_score': 0.9 if i == 0 else 0.3,
                'feedback_text': f'Great recommendation for vehicle {i+1}' if i == 0 else f'Not what I was looking for',
                'timestamp': datetime.now().isoformat()
            }

            # Process feedback (should not raise exception)
            await engines['recommendation'].process_feedback(feedback_data)

            print(f"Processed feedback for {rec.vehicle_id}: {feedback_data['feedback_type']}")

        # Verify feedback was tracked
        user_profile = await engines['tracker'].get_user_profile(user_id)
        assert user_profile.user_id == user_id

    @pytest.mark.asyncio
    async def test_a_b_testing_integration(self, engines, sample_vehicles, mock_services):
        """Test A/B testing integration"""
        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles

        # Test different users get different A/B test groups
        user_groups = {}
        for i in range(10):
            user_id = f'ab_test_user_{i}'

            result = await engines['recommendation'].get_recommendations(
                user_id=user_id,
                limit=2,
                recommendation_type=RecommendationType.HYBRID
            )

            user_groups[user_id] = result.a_b_test_group
            assert result.a_b_test_group in engines['recommendation'].ab_test_groups.keys()

        # Verify distribution of A/B test groups
        group_counts = {}
        for group in user_groups.values():
            group_counts[group] = group_counts.get(group, 0) + 1

        print(f"A/B test group distribution: {group_counts}")
        assert len(group_counts) <= len(engines['recommendation'].ab_test_groups)

        # Each user should get consistent group assignment
        for user_id in user_groups:
            group1 = user_groups[user_id]

            # Get recommendations again for same user
            result2 = await engines['recommendation'].get_recommendations(
                user_id=user_id,
                limit=2,
                recommendation_type=RecommendationType.HYBRID
            )

            group2 = result2.a_b_test_group
            assert group1 == group2, f"User {user_id} got inconsistent A/B test group: {group1} vs {group2}"


class TestRealWorldScenarios:
    """Real-world usage scenario tests"""

    @pytest.mark.asyncio
    async def test_family_car_shopping_journey(self, engines, sample_vehicles, mock_services):
        """Test typical family car shopping journey"""
        user_id = 'family_shopper'
        family_size = 4

        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles

        # Journey: Looking for safe family vehicle
        search_queries = [
            "safe family SUV under $40000",
            "reliable sedan with good safety rating",
            "fuel efficient car for commuting"
        ]

        all_viewed_vehicles = []

        for i, query in enumerate(search_queries):
            # Track search
            await engines['tracker'].track_interaction({
                'user_id': user_id,
                'interaction_type': InteractionType.SEARCH,
                'vehicle_ids': [],
                'interaction_data': {'query': query, 'family_size': family_size},
                'timestamp': datetime.now() + timedelta(minutes=i * 10)
            })

            # Get recommendations
            result = await engines['recommendation'].get_recommendations(
                user_id=user_id,
                search_query=query,
                recommendation_type=RecommendationType.HYBRID,
                limit=3,
                include_explanations=True
            )

            # View top recommendations
            for j, rec in enumerate(result.recommendations[:2]):
                await engines['tracker'].track_interaction({
                    'user_id': user_id,
                    'interaction_type': InteractionType.VIEW,
                    'vehicle_ids': [rec.vehicle_id],
                    'interaction_data': {
                        'source': 'search_results',
                        'query': query,
                        'position': j
                    },
                    'timestamp': datetime.now() + timedelta(minutes=i * 10 + j * 2)
                })

                all_viewed_vehicles.append(rec.vehicle_id)

        # Compare top viewed vehicles
        if len(all_viewed_vehicles) >= 2:
            comparison_result = await engines['comparison'].compare_vehicles(
                vehicle_ids=all_viewed_vehicles[:3],  # Compare top 3
                include_semantic_similarity=True,
                include_price_analysis=True,
                user_id=user_id
            )

            assert comparison_result.recommendation_summary is not None
            print(f"Family shopping journey: Compared {len(comparison_result.comparison_results)} vehicles")

            # Track comparison
            await engines['tracker'].track_comparison(
                user_id=user_id,
                vehicle_ids=all_viewed_vehicles[:3],
                comparison_id='family_comparison',
                processing_time=2.0
            )

        # Verify journey completion
        user_profile = await engines['tracker'].get_user_profile(user_id)
        assert user_profile.total_views >= len(all_viewed_vehicles)
        assert user_profile.total_searches == len(search_queries)
        assert user_profile.total_comparisons >= 1

        print(f"Family journey completed: {user_profile.total_views} views, {user_profile.total_comparisons} comparisons")

    @pytest.mark.asyncio
    async def test_first_time_car_buyer_journey(self, engines, sample_vehicles, mock_services):
        """Test first-time car buyer journey"""
        user_id = 'first_time_buyer'

        # Setup mocks
        def mock_get_vehicle(vehicle_id):
            return next((v for v in sample_vehicles if v['id'] == vehicle_id), None)

        mock_services['vehicle_db'].get_vehicle_by_id.side_effect = mock_get_vehicle
        mock_services['vehicle_db'].search_vehicles.return_value = sample_vehicles

        # Journey: First-time buyer with limited knowledge
        initial_search = "good first car under $30000"

        # Track initial search
        await engines['tracker'].track_interaction({
            'user_id': user_id,
            'interaction_type': InteractionType.SEARCH,
            'vehicle_ids': [],
            'interaction_data': {
                'query': initial_search,
                'experience_level': 'first_time',
                'budget_max': 30000
            },
            'timestamp': datetime.now()
        })

        # Get initial recommendations
        result = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            search_query=initial_search,
            recommendation_type=RecommendationType.CONTENT_BASED,
            limit=5,
            include_explanations=True
        )

        # First-time buyer views several vehicles and seeks more information
        for i, rec in enumerate(result.recommendations[:3]):
            # View vehicle
            await engines['tracker'].track_interaction({
                'user_id': user_id,
                'interaction_type': InteractionType.VIEW,
                'vehicle_ids': [rec.vehicle_id],
                'interaction_data': {
                    'source': 'recommendations',
                    'experience_level': 'first_time',
                    'view_duration': 120  # Longer viewing time for first-time buyers
                },
                'timestamp': datetime.now() + timedelta(minutes=i * 5)
            })

            # Save favorites
            await engines['tracker'].track_interaction({
                'user_id': user_id,
                'interaction_type': InteractionType.SAVE,
                'vehicle_ids': [rec.vehicle_id],
                'interaction_data': {
                    'source': 'vehicle_details',
                    'experience_level': 'first_time'
                },
                'timestamp': datetime.now() + timedelta(minutes=i * 5 + 2)
            })

        # Get more recommendations based on saved vehicles
        saved_vehicles = ['toyota_camry_2022', 'honda_accord_2023', 'ford_escape_2022']
        personalized_result = await engines['recommendation'].get_recommendations(
            user_id=user_id,
            context_vehicle_ids=saved_vehicles,
            recommendation_type=RecommendationType.COLLABORATIVE,
            limit=3,
            include_explanations=True
        )

        # Verify first-time buyer specific recommendations
        for rec in personalized_result.recommendations:
            assert rec.explanation is not None
            # Explanations should be helpful for first-time buyers
            assert len(rec.explanation.explanation) > 50  # Detailed explanations

        # Verify journey metrics
        user_profile = await engines['tracker'].get_user_profile(user_id)
        assert user_profile.total_views >= 3
        assert user_profile.total_saves >= 3
        assert user_profile.total_searches >= 1

        print(f"First-time buyer journey: {user_profile.total_saves} vehicles saved, {user_profile.total_views} total views")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])