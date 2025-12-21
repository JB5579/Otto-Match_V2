"""
Comprehensive Unit Tests for Vehicle Comparison Engine

Tests for Story 1-5: Build Vehicle Comparison and Recommendation Engine
Covers all comparison engine algorithms and edge cases.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

from src.recommendation.comparison_engine import ComparisonEngine
from src.api.vehicle_comparison_api import (
    VehicleSpecification, VehicleFeatures, FeatureDifference,
    PriceAnalysis, SemanticSimilarity, ComparisonFeatureType,
    FeatureDifferenceType
)


class TestComparisonEngine:
    """Test suite for ComparisonEngine"""

    @pytest.fixture
    def mock_vehicle_db_service(self):
        """Mock vehicle database service"""
        mock_db = Mock()
        mock_db.get_vehicle_by_id = AsyncMock()
        mock_db.get_similar_vehicles = AsyncMock(return_value=[])
        return mock_db

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service"""
        mock_embedding = Mock()
        mock_embedding.generate_embeddings = AsyncMock()
        return mock_embedding

    @pytest.fixture
    def comparison_engine(self, mock_vehicle_db_service, mock_embedding_service):
        """Create ComparisonEngine instance with mocked dependencies"""
        return ComparisonEngine(mock_vehicle_db_service, mock_embedding_service)

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
                'images': ['image1.jpg', 'image2.jpg'],
                'engine': '2.5L I4',
                'transmission': 'Automatic',
                'horsepower': 203,
                'fuel_efficiency_city': 28,
                'fuel_efficiency_hwy': 39,
                'safety_rating': 5
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
                'images': ['image3.jpg', 'image4.jpg'],
                'engine': '1.5L Turbo',
                'transmission': 'CVT',
                'horsepower': 192,
                'fuel_efficiency_city': 30,
                'fuel_efficiency_hwy': 38,
                'safety_rating': 5
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
                'images': ['image5.jpg', 'image6.jpg'],
                'engine': '2.5L I4',
                'transmission': 'Automatic',
                'horsepower': 203,
                'fuel_efficiency_city': 25,
                'fuel_efficiency_hwy': 33,
                'safety_rating': 5
            }
        ]

    @pytest.mark.asyncio
    async def test_compare_vehicles_success(self, comparison_engine, sample_vehicles, mock_vehicle_db_service):
        """Test successful vehicle comparison"""
        # Setup mocks
        for vehicle in sample_vehicles:
            mock_vehicle_db_service.get_vehicle_by_id.return_value = vehicle

        # Test comparison
        vehicle_ids = ['vehicle_1', 'vehicle_2']
        result = await comparison_engine.compare_vehicles(
            vehicle_ids=vehicle_ids,
            include_semantic_similarity=True,
            include_price_analysis=True
        )

        # Verify results
        assert result is not None
        assert len(result.comparison_results) == 2
        assert len(result.feature_differences) > 0
        assert result.recommendation_summary is not None

        # Check comparison results structure
        for comp_result in result.comparison_results:
            assert comp_result.vehicle_id in vehicle_ids
            assert comp_result.vehicle_data is not None
            assert isinstance(comp_result.specifications, list)
            assert isinstance(comp_result.features, list)
            assert comp_result.price_analysis is not None
            assert 0 <= comp_result.overall_score <= 1

    @pytest.mark.asyncio
    async def test_compare_vehicles_insufficient_vehicles(self, comparison_engine):
        """Test comparison with insufficient vehicles"""
        with pytest.raises(ValueError, match="At least 2 vehicles required for comparison"):
            await comparison_engine.compare_vehicles(vehicle_ids=['vehicle_1'])

    @pytest.mark.asyncio
    async def test_compare_vehicles_too_many_vehicles(self, comparison_engine):
        """Test comparison with too many vehicles"""
        vehicle_ids = ['vehicle_1', 'vehicle_2', 'vehicle_3', 'vehicle_4', 'vehicle_5']
        with pytest.raises(ValueError, match="Maximum 4 vehicles allowed for comparison"):
            await comparison_engine.compare_vehicles(vehicle_ids=vehicle_ids)

    @pytest.mark.asyncio
    async def test_compare_vehicles_missing_vehicle(self, comparison_engine, mock_vehicle_db_service):
        """Test comparison with missing vehicle"""
        mock_vehicle_db_service.get_vehicle_by_id.return_value = None

        with pytest.raises(ValueError, match="Vehicles not found"):
            await comparison_engine.compare_vehicles(vehicle_ids=['vehicle_1', 'missing_vehicle'])

    @pytest.mark.asyncio
    async def test_extract_specifications(self, comparison_engine, sample_vehicles):
        """Test specification extraction from vehicle data"""
        vehicle = sample_vehicles[0]
        specifications = await comparison_engine._extract_specifications(vehicle)

        assert isinstance(specifications, list)
        assert len(specifications) > 0

        # Check specification structure
        for spec in specifications:
            assert isinstance(spec, VehicleSpecification)
            assert spec.category is not None
            assert spec.name is not None
            assert spec.value is not None
            assert 0 <= spec.importance_score <= 1

    @pytest.mark.asyncio
    async def test_extract_features(self, comparison_engine, sample_vehicles):
        """Test feature extraction from vehicle data"""
        vehicle = sample_vehicles[0]
        features = await comparison_engine._extract_features(vehicle)

        assert isinstance(features, list)
        assert len(features) > 0

        # Check feature structure
        for feature in features:
            assert isinstance(feature, VehicleFeatures)
            assert feature.category is not None
            assert isinstance(feature.features, list)
            assert isinstance(feature.included, bool)
            assert 0 <= feature.value_score <= 1

    @pytest.mark.asyncio
    async def test_analyze_price(self, comparison_engine, sample_vehicles):
        """Test price analysis"""
        vehicle = sample_vehicles[0]
        price_analysis = await comparison_engine._analyze_price(vehicle, sample_vehicles)

        assert isinstance(price_analysis, PriceAnalysis)
        assert price_analysis.current_price == vehicle['price']
        assert price_analysis.market_average > 0
        assert len(price_analysis.market_range) == 2
        assert price_analysis.price_position in ['below_market', 'at_market', 'above_market']
        assert price_analysis.price_trend in ['increasing', 'stable', 'decreasing']
        assert price_analysis.market_demand in ['low', 'medium', 'high']

    @pytest.mark.asyncio
    async def test_calculate_overall_score(self, comparison_engine, sample_vehicles):
        """Test overall score calculation"""
        vehicle = sample_vehicles[0]
        specifications = await comparison_engine._extract_specifications(vehicle)
        features = await comparison_engine._extract_features(vehicle)

        overall_score = await comparison_engine._calculate_overall_score(
            vehicle, sample_vehicles, specifications, features
        )

        assert isinstance(overall_score, float)
        assert 0 <= overall_score <= 1

    @pytest.mark.asyncio
    async def test_analyze_feature_differences(self, comparison_engine, sample_vehicles):
        """Test feature difference analysis"""
        differences = await comparison_engine._analyze_feature_differences(
            sample_vehicles[:2], None
        )

        assert isinstance(differences, list)

        # Check difference structure
        for diff in differences:
            assert isinstance(diff, FeatureDifference)
            assert diff.feature_name is not None
            assert diff.feature_type in ComparisonFeatureType
            assert diff.difference_type in FeatureDifferenceType
            assert 0 <= diff.importance_weight <= 1
            assert diff.description is not None

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity(self, comparison_engine, sample_vehicles, mock_embedding_service):
        """Test semantic similarity calculation"""
        # Setup mock embedding service
        mock_embedding_service.generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )

        similarities = await comparison_engine._calculate_semantic_similarity(sample_vehicles[:2])

        assert isinstance(similarities, dict)
        assert len(similarities) == 1  # One pair comparison

        # Check similarity structure
        for key, similarity in similarities.items():
            assert 'vehicle_' in key
            assert '_vs_' in key
            assert isinstance(similarity, SemanticSimilarity)
            assert 0 <= similarity.similarity_score <= 1
            assert isinstance(similarity.shared_features, list)
            assert isinstance(similarity.unique_features_a, list)
            assert isinstance(similarity.unique_features_b, list)
            assert similarity.similarity_explanation is not None

    @pytest.mark.asyncio
    async def test_cosine_similarity_calculation(self, comparison_engine):
        """Test cosine similarity calculation"""
        # Test identical vectors
        vector_a = [1.0, 2.0, 3.0]
        vector_b = [1.0, 2.0, 3.0]
        similarity = await comparison_engine._calculate_cosine_similarity(vector_a, vector_b)
        assert abs(similarity - 1.0) < 0.001

        # Test orthogonal vectors
        vector_c = [1.0, 0.0]
        vector_d = [0.0, 1.0]
        similarity = await comparison_engine._calculate_cosine_similarity(vector_c, vector_d)
        assert abs(similarity - 0.0) < 0.001

        # Test different length vectors (should handle gracefully)
        vector_e = [1.0, 2.0]
        vector_f = [1.0, 2.0, 3.0]
        similarity = await comparison_engine._calculate_cosine_similarity(vector_e, vector_f)
        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_normalize_spec_value(self, comparison_engine):
        """Test specification value normalization"""
        # Test numeric values
        spec_mock = Mock(category='performance', value=25)  # mpg
        normalized = await comparison_engine._normalize_spec_value(spec_mock)
        assert isinstance(normalized, float)
        assert 0 <= normalized <= 1

        # Test string values
        spec_mock = Mock(category='transmission', value='Automatic')
        normalized = await comparison_engine._normalize_spec_value(spec_mock)
        assert isinstance(normalized, float)
        assert 0 <= normalized <= 1

    @pytest.mark.asyncio
    async def test_evaluate_spec_difference(self, comparison_engine):
        """Test specification difference evaluation"""
        # Test horsepower (higher is better)
        diff_type, importance = await comparison_engine._evaluate_spec_difference(
            'horsepower', 250, 200
        )
        assert diff_type == FeatureDifferenceType.ADVANTAGE
        assert importance > 0.5

        # Test horsepower (lower is better)
        diff_type, importance = await comparison_engine._evaluate_spec_difference(
            'horsepower', 200, 250
        )
        assert diff_type == FeatureDifferenceType.DISADVANTAGE
        assert importance > 0.5

        # Test price (lower is better)
        diff_type, importance = await comparison_engine._evaluate_spec_difference(
            'price', 25000, 30000
        )
        assert diff_type == FeatureDifferenceType.ADVANTAGE
        assert importance > 0.5

    @pytest.mark.asyncio
    async def test_evaluate_feature_importance(self, comparison_engine):
        """Test feature importance evaluation"""
        # Test high importance features
        high_importance_score = await comparison_engine._evaluate_feature_importance(
            'Blind Spot Monitoring System'
        )
        assert high_importance_score >= 0.7

        # Test medium importance features
        medium_importance_score = await comparison_engine._evaluate_feature_importance(
            'Bluetooth Connectivity'
        )
        assert 0.4 <= medium_importance_score < 0.8

        # Test low importance features
        low_importance_score = await comparison_engine._evaluate_feature_importance(
            'Floor Mats'
        )
        assert 0.2 <= low_importance_score < 0.5

    @pytest.mark.asyncio
    async def test_create_vehicle_description(self, comparison_engine, sample_vehicles):
        """Test vehicle description creation for semantic analysis"""
        vehicle = sample_vehicles[0]
        description = await comparison_engine._create_vehicle_description(vehicle)

        assert isinstance(description, str)
        assert len(description) > 0
        assert 'Toyota' in description
        assert 'Camry' in description
        assert '2022' in description

    @pytest.mark.asyncio
    async def test_generate_similarity_explanation(self, comparison_engine):
        """Test similarity explanation generation"""
        similarity_score = 0.75
        shared_features = ['bluetooth', 'backup camera']
        unique_features_a = ['leather seats']
        unique_features_b = ['heated seats']

        explanation = await comparison_engine._generate_similarity_explanation(
            similarity_score, shared_features, unique_features_a, unique_features_b
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'similar' in explanation.lower()
        assert str(int(similarity_score * 100)) + '%' in explanation

    @pytest.mark.asyncio
    async def test_generate_recommendation_summary(self, comparison_engine, sample_vehicles):
        """Test recommendation summary generation"""
        # Create mock comparison results
        mock_results = []
        for vehicle in sample_vehicles:
            from src.api.vehicle_comparison_api import VehicleComparisonResult, PriceAnalysis
            mock_price_analysis = PriceAnalysis(
                current_price=vehicle['price'],
                market_average=vehicle['price'] * 1.1,
                market_range=(vehicle['price'] * 0.9, vehicle['price'] * 1.3),
                price_position='below_market',
                price_trend='stable',
                market_demand='medium'
            )

            result = VehicleComparisonResult(
                vehicle_id=vehicle['id'],
                vehicle_data=vehicle,
                specifications=[],
                features=[],
                price_analysis=mock_price_analysis,
                overall_score=0.8
            )
            mock_results.append(result)

        summary = await comparison_engine._generate_recommendation_summary(
            mock_results, [], 'test_user_123'
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'ranks highest' in summary

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, comparison_engine, mock_vehicle_db_service):
        """Test performance with larger dataset"""
        # Setup mock to return many vehicles
        mock_vehicle_db_service.get_vehicle_by_id.side_effect = lambda vehicle_id: {
            'id': vehicle_id,
            'make': 'Test',
            'model': f'Model_{vehicle_id}',
            'year': 2022,
            'price': 25000.0,
            'features': ['bluetooth', 'backup camera'],
            'condition': 'good'
        }

        start_time = time.time()
        vehicle_ids = [f'vehicle_{i}' for i in range(4)]

        result = await comparison_engine.compare_vehicles(
            vehicle_ids=vehicle_ids,
            include_semantic_similarity=False,  # Skip for performance test
            include_price_analysis=True
        )

        processing_time = time.time() - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 2.0  # 2 seconds
        assert len(result.comparison_results) == 4

    @pytest.mark.asyncio
    async def test_error_handling_in_embedding_service(self, comparison_engine, sample_vehicles, mock_embedding_service):
        """Test error handling in embedding service"""
        # Setup mock to raise exception
        mock_embedding_service.generate_embeddings.side_effect = Exception("Embedding service error")

        # Should handle the error gracefully
        result = await comparison_engine._calculate_semantic_similarity(sample_vehicles[:2])

        # Should return empty similarities list due to error
        assert result == {}

    @pytest.mark.asyncio
    async def test_edge_case_empty_vehicle_data(self, comparison_engine):
        """Test edge case with minimal vehicle data"""
        minimal_vehicle = {
            'id': 'minimal_vehicle',
            'make': 'Test',
            'model': 'Minimal',
            'year': 2022,
            'price': 10000.0
        }

        specifications = await comparison_engine._extract_specifications(minimal_vehicle)
        features = await comparison_engine._extract_features(minimal_vehicle)

        # Should handle minimal data gracefully
        assert isinstance(specifications, list)
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_edge_case_duplicate_vehicle_ids(self, comparison_engine):
        """Test edge case with duplicate vehicle IDs"""
        duplicate_ids = ['vehicle_1', 'vehicle_1']

        with pytest.raises(ValueError, match="Vehicle IDs must be unique"):
            await comparison_engine.compare_vehicles(vehicle_ids=duplicate_ids)


# Integration-style tests that test multiple components together
class TestComparisonEngineIntegration:
    """Integration tests for ComparisonEngine"""

    @pytest.mark.asyncio
    async def test_end_to_end_comparison_flow(self, comparison_engine, sample_vehicles, mock_vehicle_db_service, mock_embedding_service):
        """Test complete comparison flow from start to finish"""
        # Setup mocks
        mock_vehicle_db_service.get_vehicle_by_id.side_effect = lambda vehicle_id: next(
            (v for v in sample_vehicles if v['id'] == vehicle_id), None
        )

        # Mock embedding service for semantic similarity
        mock_embedding_service.generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        )

        # Perform comprehensive comparison
        vehicle_ids = ['vehicle_1', 'vehicle_2', 'vehicle_3']
        result = await comparison_engine.compare_vehicles(
            vehicle_ids=vehicle_ids,
            criteria=['price', 'safety', 'features'],
            include_semantic_similarity=True,
            include_price_analysis=True,
            user_id='test_user_123'
        )

        # Verify complete results
        assert result is not None
        assert len(result.comparison_results) == 3
        assert len(result.feature_differences) > 0
        assert result.semantic_similarity is not None
        assert len(result.semantic_similarity) == 3  # 3 choose 2 = 3 pairs
        assert result.recommendation_summary is not None

        # Verify semantic similarities
        for pair_key, similarity in result.semantic_similarity.items():
            assert isinstance(similarity.similarity_score, float)
            assert 0 <= similarity.similarity_score <= 1
            assert isinstance(similarity.shared_features, list)
            assert isinstance(similarity.unique_features_a, list)
            assert isinstance(similarity.unique_features_b, list)
            assert similarity.similarity_explanation is not None

        # Verify recommendation summary includes user context
        assert 'test_user_123' in result.recommendation_summary or 'personalized' in result.recommendation_summary.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])