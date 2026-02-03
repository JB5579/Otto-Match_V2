"""
Test External Research Service Integration (Phase 2)

Tests:
- Service initialization and singleton pattern
- Ownership cost research
- Owner experience research
- Lease vs buy analysis
- Insurance delta estimation
- Conversation agent integration
- Research query detection
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.external_research_service import (
    get_research_service,
    ExternalResearchService,
    OwnershipCostReport,
    OwnerExperienceReport,
    LeaseVsBuyReport,
    InsuranceDeltaReport
)


async def test_service_initialization():
    """Test 1: Service initialization and singleton pattern"""
    print("\n" + "="*60)
    print("TEST 1: Service Initialization")
    print("="*60)

    service1 = get_research_service()
    service2 = get_research_service()

    assert service1 is service2, "Singleton pattern failed"
    assert service1.api_key is not None, "API key not found"

    print(f"[PASS] Service initialized successfully")
    print(f"       API endpoint: {service1.api_url}")
    print(f"       Model: {service1.model}")
    print(f"       Cache TTL: {service1.cache_ttl.total_seconds()/3600:.0f} hours")

    return True


async def test_ownership_cost_research():
    """Test 2: Ownership cost research"""
    print("\n" + "="*60)
    print("TEST 2: Ownership Cost Research")
    print("="*60)

    service = get_research_service()

    # Test with 2024 Tesla Model 3
    print("\nResearching: 2024 Tesla Model 3 ownership costs...")
    report = await service.get_ownership_costs(
        year=2024,
        make="Tesla",
        model="Model 3",
        annual_mileage=12000
    )

    assert isinstance(report, OwnershipCostReport), "Invalid report type"
    assert report.total_year1 > 0, "Missing first year cost"
    assert report.cost_per_month > 0, "Missing monthly cost"
    assert report.confidence > 0, "Missing confidence score"

    print(f"\n[PASS] Ownership cost research completed")
    print(f"       First Year Total: ${report.total_year1:,.0f}")
    print(f"       Monthly Cost: ${report.cost_per_month:,.0f}")
    print(f"       5-Year Total: ${report.total_5year:,.0f}")
    print(f"       Confidence: {report.confidence:.2f}")
    print(f"       Insurance: ${report.insurance_annual:,.0f}/year")
    print(f"       Maintenance: ${report.maintenance_annual:,.0f}/year")
    print(f"       Fuel: ${report.fuel_annual:,.0f}/year")

    if report.reasoning:
        print(f"\n       Reasoning: {report.reasoning[:200]}...")

    return True


async def test_owner_experience_research():
    """Test 3: Owner experience research"""
    print("\n" + "="*60)
    print("TEST 3: Owner Experience Research")
    print("="*60)

    service = get_research_service()

    # Test with 2023 Toyota RAV4
    print("\nResearching: 2023 Toyota RAV4 owner experiences...")
    report = await service.get_owner_experiences(
        year=2023,
        make="Toyota",
        model="RAV4"
    )

    assert isinstance(report, OwnerExperienceReport), "Invalid report type"
    assert report.overall_satisfaction >= 0, "Missing satisfaction rating"
    assert report.confidence > 0, "Missing confidence score"

    print(f"\n[PASS] Owner experience research completed")
    print(f"       Overall Satisfaction: {report.overall_satisfaction:.1f}/5")
    print(f"       Reliability: {report.reliability_rating:.1f}/5")
    print(f"       Value: {report.value_rating:.1f}/5")
    print(f"       Confidence: {report.confidence:.2f}")

    if report.positive_sentiment > 0:
        print(f"       Sentiment: {report.positive_sentiment*100:.0f}% positive, {report.negative_sentiment*100:.0f}% negative")

    if report.common_praises:
        print(f"\n       Common Praises:")
        for praise in report.common_praises[:2]:
            print(f"         • {praise}")

    if report.common_problems:
        print(f"\n       Common Problems:")
        for problem in report.common_problems[:2]:
            print(f"         • {problem}")

    return True


async def test_lease_vs_buy_analysis():
    """Test 4: Lease vs buy analysis"""
    print("\n" + "="*60)
    print("TEST 4: Lease vs Buy Analysis")
    print("="*60)

    service = get_research_service()

    # Test with 2024 Honda CR-V
    print("\nAnalyzing: 2024 Honda CR-V lease vs buy...")
    report = await service.get_lease_vs_buy_analysis(
        year=2024,
        make="Honda",
        model="CR-V",
        annual_mileage=12000
    )

    assert isinstance(report, LeaseVsBuyReport), "Invalid report type"
    assert report.lease_monthly_payment > 0, "Missing lease payment"
    assert report.purchase_monthly_payment > 0, "Missing purchase payment"
    assert report.confidence > 0, "Missing confidence score"

    print(f"\n[PASS] Lease vs buy analysis completed")
    print(f"       Lease Monthly: ${report.lease_monthly_payment:,.0f}")
    print(f"       Lease 3-Year Total: ${report.lease_total_3year:,.0f}")
    print(f"       Purchase Monthly: ${report.purchase_monthly_payment:,.0f}")
    print(f"       Purchase 5-Year Total: ${report.purchase_total_5year:,.0f}")
    print(f"       Confidence: {report.confidence:.2f}")

    if report.breakeven_months:
        print(f"       Break-even: {report.breakeven_months} months")

    if report.recommendation:
        print(f"\n       Recommendation: {report.recommendation}")

    return True


async def test_insurance_delta_estimation():
    """Test 5: Insurance delta estimation"""
    print("\n" + "="*60)
    print("TEST 5: Insurance Delta Estimation")
    print("="*60)

    service = get_research_service()

    # Test upgrading from 2018 Honda Accord to 2024 Tesla Model 3
    print("\nEstimating insurance change: 2018 Honda Accord → 2024 Tesla Model 3...")
    report = await service.get_insurance_delta(
        current_vehicle={
            'year': 2018,
            'make': 'Honda',
            'model': 'Accord'
        },
        new_vehicle={
            'year': 2024,
            'make': 'Tesla',
            'model': 'Model 3'
        }
    )

    assert isinstance(report, InsuranceDeltaReport), "Invalid report type"
    assert report.current_annual_premium > 0, "Missing current premium"
    assert report.new_annual_premium > 0, "Missing new premium"
    assert report.confidence > 0, "Missing confidence score"

    print(f"\n[PASS] Insurance delta estimation completed")
    print(f"       Current Premium: ${report.current_annual_premium:,.0f}/year")
    print(f"       New Premium: ${report.new_annual_premium:,.0f}/year")
    print(f"       Annual Change: ${report.annual_change:,.0f} ({report.percentage_change*100:+.1f}%)")
    print(f"       Monthly Change: ${report.monthly_change:,.0f}")
    print(f"       Confidence: {report.confidence:.2f}")

    if report.factors_driving_change:
        print(f"\n       Factors Driving Change:")
        for factor in report.factors_driving_change[:2]:
            print(f"         • {factor}")

    return True


async def test_cache_functionality():
    """Test 6: Cache functionality"""
    print("\n" + "="*60)
    print("TEST 6: Cache Functionality")
    print("="*60)

    service = get_research_service()

    # Clear existing cache
    service.cache.clear()
    initial_hits = service.stats['cache_hits']

    # First request - should miss cache
    print("\nFirst request (should miss cache)...")
    await service.get_ownership_costs(
        year=2024,
        make="Toyota",
        model="Camry",
        annual_mileage=12000
    )

    first_misses = service.stats['cache_misses']

    # Second identical request - should hit cache
    print("Second identical request (should hit cache)...")
    await service.get_ownership_costs(
        year=2024,
        make="Toyota",
        model="Camry",
        annual_mileage=12000
    )

    final_hits = service.stats['cache_hits']

    assert final_hits > initial_hits, "Cache hit not registered"

    print(f"\n[PASS] Cache functionality working")
    print(f"       Cache hits increased: {initial_hits} → {final_hits}")
    print(f"       Current stats: {service.stats}")

    return True


async def test_research_query_detection():
    """Test 7: Research query detection in conversation agent"""
    print("\n" + "="*60)
    print("TEST 7: Research Query Detection")
    print("="*60)

    # Import conversation agent components
    from src.conversation.conversation_agent import ConversationAgent
    from src.conversation.intent_models import Entity, EntityType

    agent = ConversationAgent()

    # Test ownership cost detection
    test_cases = [
        ("How much does it cost to own a Tesla Model 3?", "ownership_costs"),
        ("What are the maintenance costs for this vehicle?", "ownership_costs"),
        ("What do owners say about the reliability?", "owner_experience"),
        ("Are there common problems with this model?", "owner_experience"),
        ("Should I lease or buy this car?", "lease_vs_buy"),
        ("Is leasing a better option?", "lease_vs_buy"),
        ("How much more will insurance cost on my new car?", "insurance_delta"),
        ("What's the insurance increase from my current vehicle?", "insurance_delta"),
    ]

    print("\nTesting query detection:")
    passed = 0
    for message, expected_type in test_cases:
        detected = await agent._detect_research_query(message, [])
        if detected == expected_type:
            print(f"  [PASS] '{message[:50]}...' → {detected}")
            passed += 1
        else:
            print(f"  [FAIL] '{message[:50]}...' → Expected {expected_type}, got {detected}")

    assert passed == len(test_cases), f"Only {passed}/{len(test_cases)} detections correct"

    print(f"\n[PASS] All query detection tests passed ({passed}/{len(test_cases)})")

    return True


async def test_service_stats():
    """Test 8: Service statistics tracking"""
    print("\n" + "="*60)
    print("TEST 8: Service Statistics")
    print("="*60)

    service = get_research_service()
    stats = service.get_stats()

    print(f"\nService Statistics:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Ownership Costs: {stats['ownership_cost_requests']}")
    print(f"  Owner Experiences: {stats['owner_experience_requests']}")
    print(f"  Lease vs Buy: {stats['lease_vs_buy_requests']}")
    print(f"  Insurance Delta: {stats['insurance_delta_requests']}")
    print(f"  Cache Hits: {stats['cache_hits']}")
    print(f"  Cache Misses: {stats['cache_misses']}")
    print(f"  Errors: {stats['errors']}")

    if stats['total_requests'] > 0:
        cache_hit_rate = stats['cache_hits'] / stats['total_requests'] * 100
        print(f"  Cache Hit Rate: {cache_hit_rate:.1f}%")

    print(f"\n[PASS] Statistics tracking working")

    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXTERNAL RESEARCH SERVICE - INTEGRATION TESTS")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Service Initialization", test_service_initialization),
        ("Ownership Cost Research", test_ownership_cost_research),
        ("Owner Experience Research", test_owner_experience_research),
        ("Lease vs Buy Analysis", test_lease_vs_buy_analysis),
        ("Insurance Delta Estimation", test_insurance_delta_estimation),
        ("Cache Functionality", test_cache_functionality),
        ("Research Query Detection", test_research_query_detection),
        ("Service Statistics", test_service_stats),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "PASSED", None))
        except AssertionError as e:
            results.append((name, "FAILED", str(e)))
            print(f"\n[FAIL] {name}: {e}")
        except Exception as e:
            results.append((name, "ERROR", str(e)))
            print(f"\n[ERROR] {name}: {e}")

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, status, error in results:
        status_symbol = {
            "PASSED": "[PASS]",
            "FAILED": "[FAIL]",
            "ERROR": "[ERROR]"
        }[status]

        print(f"{status_symbol} {name}")
        if error:
            print(f"         {error}")

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    total = len(results)

    print("\n" + "="*60)
    print(f"OVERALL RESULT: {passed}/{total} tests passed")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
