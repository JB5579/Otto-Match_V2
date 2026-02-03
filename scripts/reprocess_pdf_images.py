"""
Re-process PDFs to upload images to Supabase Storage.

This script:
1. Processes PDFs through the ingestion pipeline
2. Uploads images to Supabase Storage
3. Updates database records with image URLs
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from src.services.pdf_ingestion_service import (
    PDFIngestionService,
    get_pdf_ingestion_service
)
from src.services.listing_persistence_service import (
    ListingPersistenceService,
    get_listing_persistence_service
)
from src.services.supabase_client import get_supabase_client_singleton


async def reprocess_pdf(pdf_path: str):
    """Process a single PDF and upload images to storage."""
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path}")
    print(f"{'='*60}")

    try:
        # Get services
        pdf_service = await get_pdf_ingestion_service()
        persistence_service = get_listing_persistence_service()
        supabase = get_supabase_client_singleton()

        # Step 1: Read PDF file
        print("Step 1: Reading PDF file...")
        import os
        filename = os.path.basename(pdf_path)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        print(f"  File size: {len(pdf_bytes) / 1024 / 1024:.1f} MB")

        # Step 2: Ingest PDF
        print("Step 2: Processing PDF...")
        artifact = await pdf_service.process_condition_report(pdf_bytes, filename)
        print(f"  VIN: {artifact.vehicle.vin}")
        print(f"  Make/Model: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
        print(f"  Images extracted: {len(artifact.images)}")

        # Step 3: Check if listing exists
        print("Step 3: Checking existing listing...")
        existing = supabase.table('vehicle_listings').select('*').eq('vin', artifact.vehicle.vin).execute()

        if existing.data:
            listing_id = existing.data[0]['id']
            print(f"  Found existing listing: {listing_id}")

            # Step 4: Delete existing image records for this listing
            print("Step 4: Cleaning up old image records...")
            supabase.table('vehicle_images').delete().eq('listing_id', listing_id).execute()
            print("  Old image records deleted")

            # Step 5: Upload new images
            print("Step 5: Uploading images to storage...")
            from src.services.storage_service import get_storage_service
            storage_service = await get_storage_service()

            uploaded_count = 0
            for idx, enriched_image in enumerate(artifact.images):
                try:
                    from datetime import datetime
                    ext = enriched_image.format or 'jpg'
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"{artifact.vehicle.vin}_{timestamp}_{idx}.{ext}"

                    # Upload to storage
                    upload_result = await storage_service.upload_vehicle_image(
                        image_bytes=enriched_image.image_bytes,
                        filename=filename,
                        optimize=True,
                        create_variants=True
                    )

                    # Create image record
                    from src.repositories.image_repository import ImageCreate
                    image_create = ImageCreate(
                        listing_id=listing_id,
                        vin=artifact.vehicle.vin,
                        category=enriched_image.category,
                        vehicle_angle=enriched_image.vehicle_angle,
                        description=enriched_image.description,
                        suggested_alt=enriched_image.suggested_alt,
                        quality_score=enriched_image.quality_score,
                        visible_damage=enriched_image.visible_damage or [],
                        original_filename=filename,
                        file_format=enriched_image.format or 'jpeg',
                        file_size_bytes=len(enriched_image.image_bytes),
                        width=enriched_image.width,
                        height=enriched_image.height,
                        original_url=upload_result.get('original_url'),
                        web_url=upload_result.get('web_url'),
                        thumbnail_url=upload_result.get('thumbnail_url'),
                        detail_url=upload_result.get('detail_url'),
                        page_number=enriched_image.page_number,
                        display_order=idx
                    )

                    # Insert image record
                    supabase.table('vehicle_images').insert(image_create.dict(exclude_none=True)).execute()
                    uploaded_count += 1

                    print(f"  [{idx+1}/{len(artifact.images)}] Uploaded: {filename}")
                    print(f"       Web URL: {upload_result.get('web_url', 'N/A')}")

                except Exception as e:
                    print(f"  [ERROR] Failed to upload image {idx}: {e}")

            print(f"\n  Successfully uploaded {uploaded_count}/{len(artifact.images)} images")

        else:
            print("  Listing not found - creating new listing...")
            # Create new listing with images
            result = await persistence_service.persist_listing(artifact)
            print(f"  Created listing: {result['listing_id']}")
            print(f"  Images uploaded: {result['image_count']}")

        print(f"\n  Processing complete!")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    import os

    # PDF files to process
    pdf_files = [
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2008F-250 (1).pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2014BMWi3V28503 (1).pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2018GMCCanyon.pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2019CherokeeLatitudePlus326765.pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2022LexusES350117484.pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\2023ChevyEquinox (1).pdf",
        "D:\\Otto_AI_v2\\docs\\Sample_Vehicle_Condition_Reports\\ACVMercedes.pdf",
    ]

    print("="*60)
    print("PDF Re-processing Script")
    print("="*60)
    print(f"Total PDFs to process: {len(pdf_files)}")
    print("This will:")
    print("  1. Extract images from PDFs")
    print("  2. Upload images to Supabase Storage")
    print("  3. Update database records with image URLs")
    print("="*60)

    # Process each PDF
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            await reprocess_pdf(pdf_file)
        else:
            print(f"\n[WARNING] File not found: {pdf_file}")

    print("\n" + "="*60)
    print("All PDFs processed!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Refresh the frontend to see images")
    print("  2. Vehicle cards should now display actual images instead of emojis")


if __name__ == "__main__":
    asyncio.run(main())
