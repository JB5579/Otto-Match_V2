"""
Tests for Phase 1 Advisory Entity Extractors

Tests cover:
- Lifestyle entity extraction (current vehicle, commute, work pattern, etc.)
- Priority ranking extraction
- Decision signal detection
- Advisory intent classification
"""

import pytest
import asyncio
from src.conversation.advisory_extractors import (
    LifestyleEntityExtractor,
    PriorityRankingExtractor,
    DecisionSignalDetector,
    AdvisoryIntentClassifier,
    AdvisoryExtractor,
    AdvisoryIntentType,
    CurrentVehicleEntity,
    CommutePattern,
    PriorityRanking,
)


class TestLifestyleEntityExtractor:
    """Test lifestyle entity extraction"""

    @pytest.fixture
    def extractor(self):
        return LifestyleEntityExtractor()

    @pytest.mark.asyncio
    async def test_extract_current_vehicle_full(self, extractor):
        """Test extraction of current vehicle with year, make, model"""
        message = "I've been thinking about upgrading my current car. It's a 2018 Honda Accord."
        result = await extractor.extract_all(message)

        assert 'current_vehicle' in result
        vehicle = result['current_vehicle']
        assert vehicle.year == 2018
        assert vehicle.make == 'Honda'
        assert vehicle.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_extract_current_vehicle_trade_in(self, extractor):
        """Test detection of trade-in intent"""
        message = "I'm trading in my 2020 Tesla Model 3"
        result = await extractor.extract_all(message)

        assert 'current_vehicle' in result
        vehicle = result['current_vehicle']
        assert vehicle.year == 2020
        assert vehicle.make == 'Tesla'
        assert vehicle.ownership_type == 'trading'

    @pytest.mark.asyncio
    async def test_extract_commute_pattern_round_trip(self, extractor):
        """Test extraction of round trip commute"""
        message = "My daily commute is about 45 miles round trip on the highway."
        result = await extractor.extract_all(message)

        assert 'commute' in result
        commute = result['commute']
        assert commute.distance_miles == 45.0
        assert commute.trip_type == 'round_trip'
        assert commute.road_type == 'highway'

    @pytest.mark.asyncio
    async def test_extract_commute_pattern_one_way(self, extractor):
        """Test extraction of one-way commute"""
        message = "I drive about 25 miles each way to work"
        result = await extractor.extract_all(message)

        assert 'commute' in result
        commute = result['commute']
        assert commute.distance_miles == 25.0
        assert commute.trip_type == 'one_way'

    @pytest.mark.asyncio
    async def test_extract_work_pattern_hybrid(self, extractor):
        """Test extraction of hybrid work pattern"""
        message = "I work from home a couple days a week."
        result = await extractor.extract_all(message)

        assert 'work_pattern' in result
        work = result['work_pattern']
        assert work.wfh_days_per_week == 2
        assert work.work_arrangement == 'hybrid'

    @pytest.mark.asyncio
    async def test_extract_work_pattern_remote(self, extractor):
        """Test extraction of fully remote work"""
        message = "I work remotely full time, so I don't commute."
        result = await extractor.extract_all(message)

        assert 'work_pattern' in result
        work = result['work_pattern']
        assert work.work_arrangement == 'remote'
        assert work.wfh_days_per_week == 5

    @pytest.mark.asyncio
    async def test_extract_road_trip_pattern(self, extractor):
        """Test extraction of road trip habits"""
        message = "We take road trips maybe 3-4 times a year - usually a few hundred miles."
        result = await extractor.extract_all(message)

        assert 'road_trips' in result
        trips = result['road_trips']
        assert trips.frequency_per_year in [3, 4]  # Average of 3-4

    @pytest.mark.asyncio
    async def test_extract_charging_infrastructure_garage(self, extractor):
        """Test extraction of charging infrastructure with garage"""
        message = "Yes, I have a garage where I could install a home charger."
        result = await extractor.extract_all(message)

        assert 'charging' in result
        charging = result['charging']
        assert charging.parking_type == 'garage'
        assert charging.can_install_charger == True

    @pytest.mark.asyncio
    async def test_extract_charging_infrastructure_apartment(self, extractor):
        """Test extraction of apartment parking without charger"""
        message = "I live in an apartment and can't install a charger."
        result = await extractor.extract_all(message)

        assert 'charging' in result
        charging = result['charging']
        assert charging.parking_type == 'apartment'
        assert charging.can_install_charger == False

    @pytest.mark.asyncio
    async def test_extract_annual_mileage_range(self, extractor):
        """Test extraction of annual mileage range"""
        message = "I typically drive about 12,000-15,000 miles annually."
        result = await extractor.extract_all(message)

        assert 'annual_mileage' in result
        low, high = result['annual_mileage']
        assert low == 12000
        assert high == 15000


class TestPriorityRankingExtractor:
    """Test priority ranking extraction"""

    @pytest.fixture
    def extractor(self):
        return PriorityRankingExtractor()

    @pytest.mark.asyncio
    async def test_extract_priority_comparison(self, extractor):
        """Test extraction of priority comparison"""
        message = "Performance is more important to me than luxury."
        result = await extractor.extract_all(message)

        assert 'priority_rankings' in result
        rankings = result['priority_rankings']
        assert len(rankings) >= 1
        assert rankings[0].higher_priority == 'performance'
        assert rankings[0].lower_priority == 'luxury'

    @pytest.mark.asyncio
    async def test_extract_priority_over_pattern(self, extractor):
        """Test extraction of 'X over Y' pattern"""
        message = "I'd prioritize range over performance for my road trips."
        result = await extractor.extract_all(message)

        assert 'priority_rankings' in result
        rankings = result['priority_rankings']
        assert len(rankings) >= 1

    @pytest.mark.asyncio
    async def test_extract_absolute_priority(self, extractor):
        """Test extraction of absolute priority"""
        message = "Safety is my top priority with kids in the car."
        result = await extractor.extract_all(message)

        assert 'priority_rankings' in result
        rankings = result['priority_rankings']
        assert len(rankings) >= 1
        assert rankings[0].expression_type == 'absolute'

    @pytest.mark.asyncio
    async def test_extract_budget_flexibility_stretch(self, extractor):
        """Test extraction of flexible budget"""
        message = "I prefer to stay under $100k if possible, but I could stretch a bit for the right car."
        result = await extractor.extract_all(message)

        assert 'budget_flexibility' in result
        budget = result['budget_flexibility']
        assert budget.preferred_max == 100000
        assert budget.flexibility == 'flexible'

    @pytest.mark.asyncio
    async def test_extract_budget_flexibility_strict(self, extractor):
        """Test extraction of strict budget"""
        message = "I can't go over $50k - that's my absolute max."
        result = await extractor.extract_all(message)

        assert 'budget_flexibility' in result
        budget = result['budget_flexibility']
        assert budget.hard_max == 50000
        assert budget.flexibility == 'strict'


class TestDecisionSignalDetector:
    """Test decision signal detection"""

    @pytest.fixture
    def detector(self):
        return DecisionSignalDetector()

    @pytest.mark.asyncio
    async def test_detect_commitment_winner(self, detector):
        """Test detection of 'winner' commitment signal"""
        message = "The Tesla Model S Plaid sounds like the winner."
        result = await detector.detect_all(message)

        assert 'signals' in result
        signals = result['signals']
        commitment_signals = [s for s in signals if s.signal_type == 'commitment']
        assert len(commitment_signals) >= 1
        assert result['overall_readiness'] >= 0.8

    @pytest.mark.asyncio
    async def test_detect_commitment_ready(self, detector):
        """Test detection of 'ready' commitment signal"""
        message = "I'm ready to move forward with this."
        result = await detector.detect_all(message)

        signals = result['signals']
        commitment_signals = [s for s in signals if s.signal_type == 'commitment']
        assert len(commitment_signals) >= 1

    @pytest.mark.asyncio
    async def test_detect_next_steps(self, detector):
        """Test detection of next steps inquiry"""
        message = "What happens next?"
        result = await detector.detect_all(message)

        signals = result['signals']
        next_steps_signals = [s for s in signals if s.signal_type == 'next_steps']
        assert len(next_steps_signals) >= 1

    @pytest.mark.asyncio
    async def test_detect_hesitation(self, detector):
        """Test detection of hesitation signal"""
        message = "I'm still not sure. I need more time to think about it."
        result = await detector.detect_all(message)

        signals = result['signals']
        hesitation_signals = [s for s in signals if s.signal_type == 'hesitation']
        assert len(hesitation_signals) >= 1
        assert result['overall_readiness'] < 0.5

    @pytest.mark.asyncio
    async def test_detect_confirmation_seeking(self, detector):
        """Test detection of confirmation seeking"""
        message = "Am I missing anything? Is there something else I should consider?"
        result = await detector.detect_all(message)

        signals = result['signals']
        confirmation_signals = [s for s in signals if s.signal_type == 'confirmation_seeking']
        assert len(confirmation_signals) >= 1


class TestAdvisoryIntentClassifier:
    """Test advisory intent classification"""

    @pytest.fixture
    def classifier(self):
        return AdvisoryIntentClassifier()

    @pytest.mark.asyncio
    async def test_classify_upgrade_interest(self, classifier):
        """Test classification of upgrade interest"""
        message = "I've been thinking about upgrading my current car."
        result = await classifier.classify(message)

        intent_types = [intent.value for intent, _ in result]
        assert AdvisoryIntentType.UPGRADE_INTEREST.value in intent_types

    @pytest.mark.asyncio
    async def test_classify_lifestyle_disclosure(self, classifier):
        """Test classification of lifestyle disclosure"""
        message = "My daily commute is about 45 miles round trip."
        result = await classifier.classify(message)

        intent_types = [intent.value for intent, _ in result]
        assert AdvisoryIntentType.LIFESTYLE_DISCLOSURE.value in intent_types

    @pytest.mark.asyncio
    async def test_classify_infrastructure_disclosure(self, classifier):
        """Test classification of infrastructure disclosure"""
        message = "I have a garage where I could install a charger."
        result = await classifier.classify(message)

        intent_types = [intent.value for intent, _ in result]
        assert AdvisoryIntentType.INFRASTRUCTURE_DISCLOSURE.value in intent_types

    @pytest.mark.asyncio
    async def test_classify_decision_commitment(self, classifier):
        """Test classification of decision commitment"""
        message = "This is the one. Let's do it."
        result = await classifier.classify(message)

        intent_types = [intent.value for intent, _ in result]
        assert AdvisoryIntentType.DECISION_COMMITMENT.value in intent_types

    @pytest.mark.asyncio
    async def test_classify_next_steps_inquiry(self, classifier):
        """Test classification of next steps inquiry"""
        message = "What are the next steps to proceed?"
        result = await classifier.classify(message)

        intent_types = [intent.value for intent, _ in result]
        assert AdvisoryIntentType.NEXT_STEPS_INQUIRY.value in intent_types


class TestAdvisoryExtractorIntegration:
    """Test the unified AdvisoryExtractor"""

    @pytest.fixture
    def extractor(self):
        return AdvisoryExtractor()

    @pytest.mark.asyncio
    async def test_extract_all_from_complex_message(self, extractor):
        """Test extraction from a complex message with multiple entities"""
        message = (
            "I'm thinking about upgrading my 2018 Honda Accord. "
            "My commute is about 45 miles round trip, and I work from home a couple days a week. "
            "Performance is more important to me than luxury, and I'd prefer to stay under $80k. "
            "I have a garage where I could install a charger."
        )
        result = await extractor.extract_all(message)

        # Should extract lifestyle entities
        assert 'lifestyle' in result
        lifestyle = result['lifestyle']
        assert 'current_vehicle' in lifestyle
        assert 'commute' in lifestyle
        assert 'work_pattern' in lifestyle
        assert 'charging' in lifestyle

        # Should extract priorities
        assert 'priorities' in result
        priorities = result['priorities']
        assert 'priority_rankings' in priorities or 'budget_flexibility' in priorities

        # Should classify advisory intents
        assert 'advisory_intents' in result
        intents = result['advisory_intents']
        assert len(intents) > 0

    @pytest.mark.asyncio
    async def test_build_lifestyle_profile(self, extractor):
        """Test building aggregated lifestyle profile from multiple extractions"""
        messages = [
            "I'm thinking about upgrading my 2018 Honda Accord.",
            "My commute is about 45 miles round trip on the highway.",
            "I work from home a couple days a week.",
            "I have a garage where I could install a charger.",
            "We take road trips maybe 3-4 times a year."
        ]

        extraction_history = []
        for message in messages:
            result = await extractor.extract_all(message)
            if result:
                extraction_history.append(result)

        # Build profile from history
        profile = extractor.build_lifestyle_profile(extraction_history)

        # Profile should have aggregated data
        assert profile.current_vehicle is not None
        assert profile.commute is not None
        assert profile.work_pattern is not None
        assert profile.charging is not None
        assert profile.road_trips is not None

    @pytest.mark.asyncio
    async def test_decision_signal_flow(self, extractor):
        """Test decision signal detection through conversation flow"""
        # Simulating conversation progression
        messages = [
            "I'm looking at a few options...",  # Browsing
            "The Tesla seems like a good fit.",  # Considering
            "Am I missing anything?",  # Confirmation seeking
            "The Tesla Model S sounds like the winner.",  # Commitment
            "What happens next?"  # Next steps
        ]

        last_result = None
        for message in messages:
            result = await extractor.extract_all(message)
            if 'decision_signals' in result and result['decision_signals'].get('signals'):
                last_result = result

        # Should have detected decision signals
        assert last_result is not None
        assert 'decision_signals' in last_result


class TestExtractionFromSimulatedConversation:
    """Test extraction using examples from the Conversation Flow Simulation"""

    @pytest.fixture
    def extractor(self):
        return AdvisoryExtractor()

    @pytest.mark.asyncio
    async def test_jordan_ev_discovery_intro(self, extractor):
        """Test extraction from Jordan's EV discovery introduction"""
        message = (
            "I've been thinking about upgrading my current car. "
            "It's a 2018 Honda Accord and while it's been reliable, "
            "I'm interested in exploring electric vehicles."
        )
        result = await extractor.extract_all(message)

        # Should extract current vehicle
        assert 'lifestyle' in result
        assert 'current_vehicle' in result['lifestyle']
        vehicle = result['lifestyle']['current_vehicle']
        assert vehicle.year == 2018
        assert vehicle.make == 'Honda'
        assert vehicle.sentiment == 'neutral' or vehicle.sentiment == 'satisfied'

        # Should detect upgrade interest
        assert 'advisory_intents' in result
        intent_types = [i.value for i, _ in result['advisory_intents']]
        assert 'upgrade_interest' in intent_types

    @pytest.mark.asyncio
    async def test_jordan_lifestyle_disclosure(self, extractor):
        """Test extraction from Jordan's lifestyle disclosure"""
        message = (
            "My daily commute is about 45 miles round trip on the highway, "
            "and I work from home a couple days a week."
        )
        result = await extractor.extract_all(message)

        assert 'lifestyle' in result
        lifestyle = result['lifestyle']

        # Should extract commute
        assert 'commute' in lifestyle
        assert lifestyle['commute'].distance_miles == 45.0
        assert lifestyle['commute'].road_type == 'highway'

        # Should extract work pattern
        assert 'work_pattern' in lifestyle
        assert lifestyle['work_pattern'].wfh_days_per_week == 2

    @pytest.mark.asyncio
    async def test_jordan_priority_expression(self, extractor):
        """Test extraction from Jordan's priority expression"""
        message = "Performance is more important to me than luxury."
        result = await extractor.extract_all(message)

        assert 'priorities' in result
        rankings = result['priorities'].get('priority_rankings', [])
        assert len(rankings) >= 1
        assert rankings[0].higher_priority == 'performance'
        assert rankings[0].lower_priority == 'luxury'

    @pytest.mark.asyncio
    async def test_jordan_decision_commitment(self, extractor):
        """Test extraction from Jordan's decision commitment"""
        message = "The Tesla Model S Plaid sounds like the winner."
        result = await extractor.extract_all(message)

        assert 'decision_signals' in result
        signals = result['decision_signals'].get('signals', [])
        commitment_signals = [s for s in signals if s.signal_type == 'commitment']
        assert len(commitment_signals) >= 1

        # Should have high readiness
        assert result['decision_signals']['overall_readiness'] >= 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
