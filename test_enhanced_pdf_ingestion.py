#!/usr/bin/env python3
"""
Test Enhanced PDF Ingestion Service with Market Data Integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def main():
    """Test the enhanced PDF ingestion service with market data"""
    print("Testing Enhanced PDF Ingestion Service with Market Data Integration...")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check API keys
    required_keys = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        print(f"Missing environment variables: {', '.join(missing_keys)}")
        return

    print("Environment variables loaded successfully")

    try:
        # Import services
        from src.services.enhanced_pdf_ingestion_service import get_enhanced_pdf_ingestion_service
        from src.services.pdf_ingestion_service import get_pdf_ingestion_service
        from supabase import create_client

        print("Services imported successfully")

        # Initialize services
        enhanced_service = await get_enhanced_pdf_ingestion_service()
        base_service = await get_pdf_ingestion_service()
        supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

        print("Services initialized")

        # Test with a sample PDF
        sample_dir = Path(__file__).parent / 'docs' / 'Sample_Vehicle_Condition_Reports'
        pdf_files = list(sample_dir.glob("*.pdf"))

        if not pdf_files:
            print("No sample PDFs found in docs/Sample_Vehicle_Condition_Reports")
            return

        # Use the first PDF
        test_pdf = pdf_files[0]
        print(f"\nTesting with: {test_pdf.name}")

        # Read PDF bytes
        with open(test_pdf, 'rb') as f:
            pdf_bytes = f.read()

        print(f"PDF loaded: {len(pdf_bytes)} bytes")

        # Test base service first
        print("\n=== Testing Base PDF Ingestion ===")
        base_artifact = await base_service.process_condition_report(pdf_bytes, test_pdf.name)

        print("✅ Base processing successful")
        print(f"  Vehicle: {base_artifact.vehicle.year} {base_artifact.vehicle.make} {base_artifact.vehicle.model}")
        print(f"  VIN: {base_artifact.vehicle.vin or 'Not found'}")
        print(f"  Images: {len(base_artifact.images)} extracted")

        # Test enhanced service with market data
        print("\n=== Testing Enhanced PDF Ingestion with Market Data ===")
        enhanced_artifact = await enhanced_service.process_condition_report_with_market_data(
            pdf_bytes,
            test_pdf.name,
            region="west",  # Test with West Coast regional pricing
            zip_code="90210"  # Test with Beverly Hills zip code
        )

        print("✅ Enhanced processing successful")
        print(f"  Vehicle: {enhanced_artifact.vehicle.year} {enhanced_artifact.vehicle.make} {enhanced_artifact.vehicle.model}")

        # Check if market data was added
        if 'market_data' in enhanced_artifact.processing_metadata:
            market_data = enhanced_artifact.processing_metadata['market_data']
            print(f"  Market Price Range: ${market_data['price_range']['min']:,.0f} - ${market_data['price_range']['max']:,.0f}")
            print(f"  Average Market Price: ${market_data['price_range']['average']:,.0f}")
            print(f"  Days on Market: {market_data['days_on_market_average']} days")
            print(f"  Demand Indicator: {market_data['demand_indicator']}")
            print(f"  Data Source: {market_data['data_source']}")
            print(f"  Confidence: {market_data['confidence_score']:.1%}")
        else:
            print("  ⚠️  No market data found in artifact")

        # Verify data was stored in Supabase
        print("\n=== Verifying Supabase Storage ===")

        # Try to find the vehicle in the database
        if base_artifact.vehicle.vin:
            result = supabase.table('vehicle_listings').select('*').eq('vin', base_artifact.vehicle.vin).execute()

            if result.data and len(result.data) > 0:
                vehicle = result.data[0]
                print(f"✅ Vehicle found in Supabase")
                print(f"  Database ID: {vehicle['id']}")
                print(f"  Market Price Min: ${vehicle.get('market_price_min', 'N/A')}")
                print(f"  Market Price Max: ${vehicle.get('market_price_max', 'N/A')}")
                print(f"  Demand Indicator: {vehicle.get('demand_indicator', 'N/A')}")
                print(f"  Market Data Updated: {vehicle.get('market_data_updated_at', 'Never')}")
            else:
                print("⚠️  Vehicle not found in Supabase")

        # Test market cache
        print("\n=== Testing Market Data Cache ===")
        cache_result = supabase.table('market_data_cache').select('*').eq('make', base_artifact.vehicle.make).eq('model', base_artifact.vehicle.model).eq('year', base_artifact.vehicle.year).execute()

        if cache_result.data and len(cache_result.data) > 0:
            print(f"✅ Market data found in cache")
            for cache_entry in cache_result.data:
                print(f"  Cache Key: {cache_entry['cache_key']}")
                print(f"  Expires: {cache_entry['expires_at']}")
        else:
            print("ℹ️  No cache entries found (might be normal if caching failed)")

        # Cleanup
        await enhanced_service.close()
        await base_service.close()

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())