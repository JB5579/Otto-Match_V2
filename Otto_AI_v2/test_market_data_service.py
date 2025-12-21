#!/usr/bin/env python3
"""
Test Market Data Service independently
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def main():
    """Test the market data service"""
    print("Testing Market Data Service...")

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from src.services.market_data_service import (
            get_market_data_service,
            MarketDataRequest
        )

        print("Services imported successfully")

        # Initialize service
        market_service = await get_market_data_service()
        print("Market data service initialized")

        # Test with a known vehicle
        request = MarketDataRequest(
            make="GMC",
            model="Canyon",
            year=2018,
            mileage=50000,
            region="west"
        )

        print(f"\nFetching market data for: {request.year} {request.make} {request.model}")

        # Fetch market data
        market_data = await market_service.fetch_market_data(request)

        print(f"✅ Market data fetched successfully!")
        print(f"  Price Range: ${market_data.market_price_range[0]:,.0f} - ${market_data.market_price_range[1]:,.0f}")
        print(f"  Average Price: ${(market_data.market_price_range[0] + market_data.market_price_range[1]) / 2:,.0f}")
        print(f"  Days on Market: {market_data.average_days_on_market}")
        print(f"  Regional Multiplier: {market_data.regional_multiplier}")
        print(f"  Demand Indicator: {market_data.demand_indicator}")
        print(f"  Confidence Score: {market_data.confidence_score:.1%}")
        print(f"  Data Source: {market_data.source}")

        # Test price competitiveness
        dealer_price = 28000
        competitiveness = market_service.calculate_price_competitiveness(dealer_price, market_data)
        print(f"\nDealer Price: ${dealer_price:,}")
        print(f"Price Competitiveness: {competitiveness}")

        # Test with different region
        request_northeast = MarketDataRequest(
            make="GMC",
            model="Canyon",
            year=2018,
            region="northeast"
        )

        market_data_ne = await market_service.fetch_market_data(request_northeast)
        print(f"\nNortheast pricing:")
        print(f"  Price Range: ${market_data_ne.market_price_range[0]:,.0f} - ${market_data_ne.market_price_range[1]:,.0f}")
        print(f"  Regional Multiplier: {market_data_ne.regional_multiplier}")

        # Cleanup
        await market_service.close()

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())