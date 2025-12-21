"""
Unit tests for Preference Engine
"""

import pytest
from datetime import datetime, timedelta
from src.intelligence.preference_engine import PreferenceEngine
from src.conversation.nlu_service import UserPreference, Entity


@pytest.mark.unit
class TestPreferenceEngine:
    """Test suite for PreferenceEngine"""

    async def test_initialization(self, mock_groq_client, temporal_memory_manager):
        """Test preference engine initialization"""
        engine = PreferenceEngine(mock_groq_client, temporal_memory_manager)

        assert engine.groq_client == mock_groq_client
        assert engine.temporal_memory == temporal_memory_manager
        assert isinstance(engine.preference_cache, dict)

    async def test_extract_preferences_explicit(self, preference_engine, sample_entities):
        """Test extracting explicit preferences from user message"""
        message = "I want a Toyota SUV under $30,000"

        preferences = await preference_engine.extract_preferences(
            message=message,
            entities=sample_entities,
            context={"conversation_stage": "discovery"}
        )

        assert len(preferences) >= 3  # Should extract brand, type, and price

        # Check brand preference
        brand_prefs = [p for p in preferences if p.category == "brand"]
        assert len(brand_prefs) > 0
        assert "Toyota" in brand_prefs[0].value
        assert brand_prefs[0].source == "explicit"

        # Check vehicle type preference
        type_prefs = [p for p in preferences if p.category == "vehicle_type"]
        assert len(type_prefs) > 0
        assert type_prefs[0].value == "SUV"

        # Check price preference
        price_prefs = [p for p in preferences if p.category == "price_range"]
        assert len(price_prefs) > 0
        assert 30000 in price_prefs[0].value.values()

    async def test_extract_preferences_implicit(self, preference_engine):
        """Test extracting implicit preferences from user message"""
        message = "I need something safe for my kids"

        preferences = await preference_engine.extract_preferences(
            message=message,
            entities=[],
            context={"conversation_stage": "needs_analysis"}
        )

        # Should infer family-friendly preference
        family_prefs = [p for p in preferences if p.category == "family_friendly"]
        assert len(family_prefs) > 0
        assert family_prefs[0].value is True
        assert family_prefs[0].source == "implicit"

        # Should infer safety preference
        safety_prefs = [p for p in preferences if p.category == "safety_priority"]
        assert len(safety_prefs) > 0
        assert safety_prefs[0].weight > 0.7  # High weight for safety

    async def test_preference_confidence_scoring(self, preference_engine):
        """Test preference confidence scoring algorithm"""
        # First mention - lower confidence
        pref1 = UserPreference(
            category="brand",
            value="Toyota",
            weight=0.5,
            source="explicit",
            confidence=0.5
        )

        # Multiple mentions should increase confidence
        preferences = [pref1]
        for i in range(3):
            # Simulate repeated preference
            updated = await preference_engine._update_preference_confidence(
                preferences,
                UserPreference(
                    category="brand",
                    value="Toyota",
                    weight=0.5,
                    source="explicit"
                )
            )

        # Check confidence increased
        toyota_prefs = [p for p in updated if p.category == "brand" and p.value == "Toyota"]
        assert len(toyota_prefs) > 0
        assert toyota_prefs[0].confidence > 0.5  # Should have increased

    async def test_preference_conflict_detection(self, preference_engine):
        """Test preference conflict detection and resolution"""
        # Create conflicting preferences
        preferences = [
            UserPreference(
                category="price_range",
                value={"min": 20000, "max": 30000},
                weight=0.8,
                source="explicit",
                confidence=0.9
            ),
            UserPreference(
                category="price_range",
                value={"min": 50000, "max": 60000},
                weight=0.7,
                source="explicit",
                confidence=0.6
            )
        ]

        conflicts = await preference_engine._detect_preference_conflicts(preferences)

        assert len(conflicts) > 0
        assert conflicts[0]["category"] == "price_range"
        assert "conflicting_values" in conflicts[0]

    async def test_preference_weight_evolution(self, preference_engine):
        """Test preference weight evolution over time"""
        user_id = "test_user_123"

        # Create initial preference
        initial_pref = UserPreference(
            category="brand",
            value="Toyota",
            weight=0.7,
            source="explicit",
            confidence=0.8,
            timestamp=datetime.now() - timedelta(days=10)
        )

        # Simulate time decay
        evolved_pref = await preference_engine._apply_time_decay(initial_pref)

        # Weight should have decayed
        assert evolved_pref.weight < initial_pref.weight

        # Add positive feedback to boost weight
        feedback = {"Toyota": 0.9}  # High positive feedback
        boosted_pref = await preference_engine._apply_feedback_weight(
            evolved_pref,
            feedback
        )

        # Weight should be boosted due to feedback
        assert boosted_pref.weight > evolved_pref.weight

    async def test_cross_reference_preferences(self, preference_engine):
        """Test cross-referencing explicit and implicit preferences"""
        preferences = [
            UserPreference(
                category="brand",
                value=["Toyota", "Honda"],
                weight=0.8,
                source="explicit"
            ),
            UserPreference(
                category="reliability",
                value="high",
                weight=0.9,
                source="implicit"
            )
        ]

        # Cross-reference should find correlation
        correlations = await preference_engine._cross_reference_preferences(preferences)

        assert len(correlations) > 0
        # Should find that Japanese brands correlate with reliability preference
        assert any("Toyota" in str(c) or "Honda" in str(c) for c in correlations)

    async def test_preference_extraction_accuracy(self, preference_engine):
        """Test preference extraction accuracy (>90% requirement)"""
        test_messages = [
            ("I want a reliable Japanese SUV under $30k", {
                "brand": ["Toyota", "Honda", "Nissan"],
                "vehicle_type": "SUV",
                "price_range": {"max": 30000}
            }),
            ("Need good fuel economy for commuting", {
                "fuel_efficiency": "high",
                "usage_pattern": "commuting"
            }),
            ("Safety is my top priority", {
                "safety_priority": "high"
            })
        ]

        correct_extractions = 0
        total_extractions = 0

        for message, expected in test_messages:
            preferences = await preference_engine.extract_preferences(message, [])

            for category, expected_value in expected.items():
                total_extractions += 1
                extracted = [p for p in preferences if p.category == category]

                if extracted:
                    # Check if extracted value matches expected
                    if isinstance(expected_value, list):
                        if any(val in extracted[0].value for val in expected_value):
                            correct_extractions += 1
                    else:
                        if extracted[0].value == expected_value:
                            correct_extractions += 1

        accuracy = (correct_extractions / total_extractions) * 100 if total_extractions > 0 else 0
        assert accuracy >= 90, f"Extraction accuracy {accuracy:.2f}% is below 90% requirement"

    async def test_preference_validation(self, preference_engine):
        """Test preference validation and consistency checking"""
        # Valid preference
        valid_pref = UserPreference(
            category="price_range",
            value={"min": 20000, "max": 40000},
            weight=0.7,
            source="explicit"
        )

        is_valid = await preference_engine._validate_preference(valid_pref)
        assert is_valid is True

        # Invalid preference (min > max)
        invalid_pref = UserPreference(
            category="price_range",
            value={"min": 40000, "max": 20000},
            weight=0.7,
            source="explicit"
        )

        is_valid = await preference_engine._validate_preference(invalid_pref)
        assert is_valid is False

    async def test_batch_preference_processing(self, preference_engine):
        """Test batch processing of preferences"""
        user_id = "test_user_123"
        messages = [
            "I like Toyota and Honda",
            "Need something under $35k",
            "SUV would be perfect for my family"
        ]

        # Process all messages at once
        all_preferences = []
        for message in messages:
            prefs = await preference_engine.extract_preferences(message, [])
            all_preferences.extend(prefs)

        # Check that all preferences were extracted
        assert len(all_preferences) >= 3
        categories = {p.category for p in all_preferences}
        assert "brand" in categories
        assert "price_range" in categories or "price" in categories
        assert "vehicle_type" in categories