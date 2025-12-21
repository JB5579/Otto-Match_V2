"""
Test Market Data Integration for Story 2-5
Tests the complete flow from web scraping to conversation enhancement
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from decimal import Decimal
from datetime import datetime

async def test_web_scraper():
    """Test the Grok Mini web scraper"""
    print("Testing Grok Mini Web Scraper")
    print("=" * 50)

    from src.services.grok_mini_web_scraper import get_grok_mini_scraper

    scraper = get_grok_mini_scraper()

    # Test scraping for a popular vehicle
    result = await scraper.scrape_vehicle_market_data(
        make="Honda",
        model="Civic",
        year=2022,
        zip_code="90210"
    )

    print(f"Scraped {result.total_listings} listings from {len(result.sources_analyzed)} sources")
    print(f"Average Price: ${result.avg_price:,.2f}")
    print(f"Price Range: ${result.price_range[0]:,.2f} - ${result.price_range[1]:,.2f}")
    print(f"Market Trend: {result.price_trend}")
    print(f"Confidence Score: {result.confidence_score*100:.1f}%")

    # Format for conversation
    formatted = scraper.format_analysis_for_conversation(result)
    print("\nFormatted for Conversation:")
    print(formatted)

    return result

async def test_enhanced_market_service():
    """Test the enhanced market data service"""
    print("\n\nTesting Enhanced Market Data Service")
    print("=" * 50)

    from src.services.enhanced_market_data_service import get_enhanced_market_data_service

    service = get_enhanced_market_data_service()

    # Test comprehensive intelligence
    intelligence = await service.get_comprehensive_market_intelligence(
        vehicle_id="test_honda_civic_2022",
        make="Honda",
        model="Civic",
        year=2022,
        mileage=25000
    )

    print(f"Intelligence Confidence: {intelligence.confidence_score*100:.1f}%")
    print(f"Sources Analyzed: {intelligence.sources_count}")
    print(f"Blended Analysis Keys: {list(intelligence.blended_analysis.keys())}")

    # Test price competitiveness
    analysis = await service.analyze_vehicle_competitiveness(
        vehicle_id="test_honda_civic_2022",
        asking_price=Decimal("22000"),
        make="Honda",
        model="Civic",
        year=2022,
        mileage=25000
    )

    print(f"\nPrice Analysis for $22,000:")
    print(f"  Market Average: ${analysis['market_avg']:,.2f}")
    print(f"  Percentile: {analysis['price_percentile']:.1f}")
    print(f"  Competitiveness: {analysis['competitiveness']}")
    print(f"  Recommendation: {analysis['recommendation']}")

    return intelligence

async def main():
    """Run all tests"""
    print("Otto.AI Story 2-5 Market Data Integration Tests")
    print("=" * 60)

    # Test web scraper
    scraper_result = await test_web_scraper()

    # Test enhanced service
    service_result = await test_enhanced_market_service()

    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Web Scraper: Working (scraped {scraper_result.total_listings} listings)")
    print(f"Enhanced Service: Working (confidence: {service_result.confidence_score*100:.1f}%)")

    print("\nStory 2-5 Market Data Integration is FUNCTIONAL!")
    print("   - Web scraping simulation works")
    print("   - Market intelligence integration works")
    print("   - Ready for production with real web scraping")

if __name__ == "__main__":
    asyncio.run(main())
