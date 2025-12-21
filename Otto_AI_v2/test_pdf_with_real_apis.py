#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test PDF ingestion with real API calls using environment variables
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.services.pdf_ingestion_service import get_pdf_ingestion_service

async def main():
    """Test with real APIs and smallest PDF"""
    print("Testing PDF ingestion with real API calls...")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check required variables
    required_vars = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        return

    print("Environment variables loaded")

    # Get the smallest PDF for testing
    sample_dir = Path(__file__).parent / 'docs' / 'Sample_Vehicle_Condition_Reports'
    test_files = list(sample_dir.glob("*.pdf"))

    if not test_files:
        print("No sample PDFs found")
        return

    # Pick smallest file for testing
    test_file = min(test_files, key=lambda f: f.stat().st_size)
    print(f"Testing with: {test_file.name} ({test_file.stat().st_size:,} bytes)")

    try:
        # Initialize service
        pdf_service = await get_pdf_ingestion_service()
        print("PDF ingestion service initialized")

        # Read PDF
        with open(test_file, 'rb') as f:
            pdf_bytes = f.read()

        # Process with real APIs
        start_time = datetime.utcnow()
        print("Processing PDF with OpenRouter/Gemini...")

        artifact = await pdf_service.process_condition_report(
            pdf_bytes=pdf_bytes,
            filename=test_file.name
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Display results
        print("\nSUCCESS! Real API processing complete")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Vehicle: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
        print(f"VIN: {artifact.vehicle.vin}")
        print(f"Odometer: {artifact.vehicle.odometer:,} miles")
        print(f"Engine: {artifact.vehicle.engine}")
        print(f"Exterior: {artifact.vehicle.exterior_color}")
        print(f"Interior: {artifact.vehicle.interior_color}")
        print(f"Condition Score: {artifact.condition.score}/5 ({artifact.condition.grade})")
        print(f"Images extracted: {len(artifact.images)}")

        if artifact.images:
            print("\nImage Details:")
            for i, img in enumerate(artifact.images, 1):
                print(f"  {i}. {img.category} - {img.vehicle_angle}")
                print(f"     Quality: {img.quality_score}/10")
                print(f"     Size: {img.width}x{img.height} ({img.format})")
                print(f"     Description: {img.description[:80]}...")
                if img.visible_damage:
                    print(f"     Damage detected: {', '.join(img.visible_damage)}")

        print(f"\nSeller: {artifact.seller.name} ({artifact.seller.type})")
        print(f"Processing metadata: {artifact.processing_metadata}")

        await pdf_service.close()
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\nError during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())