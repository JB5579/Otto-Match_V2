#!/usr/bin/env python3
"""
Test all 4 sample condition report PDFs and verify database storage.
Run with: python test_all_condition_reports.py
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def check_existing_data():
    """Check what's already in the database"""
    print("\n" + "="*60)
    print("CHECKING EXISTING DATABASE DATA")
    print("="*60)

    from dotenv import load_dotenv
    load_dotenv()

    from src.services.supabase_client import get_supabase_client_singleton

    try:
        client = get_supabase_client_singleton()

        # Check listings
        listings = client.table('vehicle_listings').select('id, vin, year, make, model, created_at').execute()
        print(f"\nExisting Listings: {len(listings.data) if listings.data else 0}")
        if listings.data:
            for listing in listings.data[:10]:  # Show first 10
                print(f"  - {listing['year']} {listing['make']} {listing['model']} (VIN: {listing['vin'][:8]}...)")

        # Check images
        images = client.table('vehicle_images').select('id, vin, category, vehicle_angle, created_at').execute()
        print(f"\nExisting Images: {len(images.data) if images.data else 0}")
        if images.data:
            by_vin = {}
            for img in images.data:
                vin = img['vin'][:8] + "..."
                by_vin[vin] = by_vin.get(vin, 0) + 1
            for vin, count in by_vin.items():
                print(f"  - VIN {vin}: {count} images")

        return True
    except Exception as e:
        print(f"Error checking database: {e}")
        return False


async def test_single_pdf(pdf_path: Path):
    """Test a single PDF file"""
    print(f"\n{'='*60}")
    print(f"TESTING: {pdf_path.name}")
    print(f"{'='*60}")

    from src.services.pdf_ingestion_service import get_pdf_ingestion_service

    try:
        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        print(f"File size: {len(pdf_bytes):,} bytes")

        # Initialize service
        pdf_service = await get_pdf_ingestion_service()

        # Process PDF
        start_time = datetime.utcnow()
        print("Processing with OpenRouter/Gemini + PyMuPDF...")

        artifact = await pdf_service.process_condition_report(
            pdf_bytes=pdf_bytes,
            filename=pdf_path.name
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Display results
        print(f"\nSUCCESS! Processing completed in {processing_time:.2f}s")
        print(f"Vehicle: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
        print(f"VIN: {artifact.vehicle.vin}")
        print(f"Odometer: {artifact.vehicle.odometer:,} miles")
        print(f"Condition: {artifact.condition.score}/5 ({artifact.condition.grade})")
        print(f"Images extracted: {len(artifact.images)}")

        if artifact.images:
            print("\nImage Details:")
            for i, img in enumerate(artifact.images[:5], 1):  # Show first 5
                print(f"  {i}. {img.category} - {img.vehicle_angle}")
                print(f"     Size: {img.width}x{img.height} ({img.format})")
                print(f"     Quality: {img.quality_score}/10")

        metadata = artifact.processing_metadata
        print(f"\nProcessing Stats:")
        print(f"  - Gemini images found: {metadata.get('gemini_images_found', 'N/A')}")
        print(f"  - PyMuPDF images extracted: {metadata.get('pymupdf_images_extracted', 'N/A')}")
        print(f"  - Final merged images: {metadata.get('final_merged_images', 'N/A')}")

        return {
            'filename': pdf_path.name,
            'success': True,
            'vin': artifact.vehicle.vin,
            'vehicle': f"{artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}",
            'images': len(artifact.images),
            'processing_time': processing_time
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'filename': pdf_path.name,
            'success': False,
            'error': str(e)
        }


async def test_with_database_storage(pdf_path: Path):
    """Test PDF processing AND database storage"""
    print(f"\n{'='*60}")
    print(f"TESTING WITH DB STORAGE: {pdf_path.name}")
    print(f"{'='*60}")

    from src.services.pdf_ingestion_service import get_pdf_ingestion_service
    from src.services.vehicle_embedding_service import VehicleEmbeddingService
    from src.semantic.embedding_service import OttoAIEmbeddingService

    try:
        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        print(f"File size: {len(pdf_bytes):,} bytes")

        # Initialize services
        pdf_service = await get_pdf_ingestion_service()

        # Process PDF
        start_time = datetime.utcnow()
        print("Step 1: Processing PDF with OpenRouter/Gemini + PyMuPDF...")

        artifact = await pdf_service.process_condition_report(
            pdf_bytes=pdf_bytes,
            filename=pdf_path.name
        )

        pdf_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"  PDF processing: {pdf_time:.2f}s")
        print(f"  Vehicle: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
        print(f"  Images: {len(artifact.images)}")

        # Store in database (skip embedding for now to test storage)
        print("\nStep 2: Storing in Supabase...")

        from src.repositories.listing_repository import get_listing_repository, ListingCreate
        from src.repositories.image_repository import get_image_repository, ImageCreate

        listing_repo = get_listing_repository()
        image_repo = get_image_repository()

        v = artifact.vehicle
        c = artifact.condition

        # Create listing (without embedding for this test)
        listing_data = ListingCreate(
            vin=v.vin,
            year=v.year,
            make=v.make,
            model=v.model,
            trim=v.trim,
            odometer=v.odometer,
            drivetrain=v.drivetrain or "Unknown",
            transmission=v.transmission or "Unknown",
            engine=v.engine or "Unknown",
            exterior_color=v.exterior_color or "Unknown",
            interior_color=v.interior_color or "Unknown",
            condition_score=c.score,
            condition_grade=c.grade,
            description_text=f"{v.year} {v.make} {v.model} {v.trim or ''}".strip(),
            status='active',
            listing_source='pdf_upload',
            processing_metadata=artifact.processing_metadata
        )

        created_listing = await listing_repo.create(listing_data)
        listing_id = created_listing['id']
        print(f"  Created listing: {listing_id}")

        # Create images
        image_count = 0
        for idx, img in enumerate(artifact.images):
            image_data = ImageCreate(
                listing_id=listing_id,
                vin=v.vin,
                category=img.category,
                vehicle_angle=img.vehicle_angle,
                description=img.description,
                suggested_alt=img.suggested_alt,
                quality_score=img.quality_score,
                visible_damage=img.visible_damage or [],
                file_format=img.format,
                width=img.width,
                height=img.height,
                original_url=img.storage_url,
                web_url=img.storage_url,
                thumbnail_url=img.thumbnail_url,
                page_number=img.page_number,
                display_order=idx
            )
            await image_repo.create(image_data)
            image_count += 1

        print(f"  Created {image_count} images")

        total_time = (datetime.utcnow() - start_time).total_seconds()

        return {
            'filename': pdf_path.name,
            'success': True,
            'listing_id': listing_id,
            'vin': v.vin,
            'vehicle': f"{v.year} {v.make} {v.model}",
            'images_stored': image_count,
            'total_time': total_time
        }

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'filename': pdf_path.name,
            'success': False,
            'error': str(e)
        }


async def main():
    """Test all 4 condition report PDFs"""
    print("="*60)
    print("OTTO.AI PDF INGESTION TEST SUITE")
    print("="*60)

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Check required variables
    required_vars = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        return

    print("Environment variables loaded")

    # Check existing data
    await check_existing_data()

    # Find sample PDFs
    sample_dir = Path(__file__).parent / 'docs' / 'Sample_Vehicle_Condition_Reports'

    # The 4 specific PDFs mentioned
    target_files = [
        "2014BMWi3V28503 (1).pdf",
        "2018GMCCanyon.pdf",
        "ACVMercedes.pdf",
        "2008F-250 (1).pdf"
    ]

    pdf_files = []
    for name in target_files:
        path = sample_dir / name
        if path.exists():
            pdf_files.append(path)
        else:
            print(f"WARNING: File not found: {name}")

    if not pdf_files:
        print("ERROR: No sample PDFs found!")
        # List what's available
        available = list(sample_dir.glob("*.pdf"))
        print(f"Available files in {sample_dir}:")
        for f in available:
            print(f"  - {f.name}")
        return

    print(f"\nFound {len(pdf_files)} PDFs to test:")
    for pdf in pdf_files:
        print(f"  - {pdf.name} ({pdf.stat().st_size:,} bytes)")

    # Ask user which mode to run
    print("\n" + "="*60)
    print("SELECT TEST MODE:")
    print("  1. Process only (no database storage)")
    print("  2. Process AND store in database")
    print("="*60)

    mode = input("Enter choice (1 or 2): ").strip()

    results = []

    if mode == "2":
        # Test with database storage
        for pdf_path in pdf_files:
            result = await test_with_database_storage(pdf_path)
            results.append(result)
    else:
        # Process only
        for pdf_path in pdf_files:
            result = await test_single_pdf(pdf_path)
            results.append(result)

    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    for r in successful:
        images = r.get('images', r.get('images_stored', 0))
        print(f"  [OK] {r['filename']}")
        print(f"       {r['vehicle']} - {images} images")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  [FAIL] {r['filename']}: {r.get('error', 'Unknown error')}")

    # Check database after
    if mode == "2":
        await check_existing_data()

    # Close services
    from src.services.pdf_ingestion_service import get_pdf_ingestion_service
    pdf_service = await get_pdf_ingestion_service()
    await pdf_service.close()

    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(main())
