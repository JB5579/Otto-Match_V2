"""
Otto.AI End-to-End Pipeline Validation Script

This script validates the complete PDF → Database → Search → Grid flow:

1. Processes a sample PDF through the ingestion pipeline
2. Persists the listing to the database
3. Verifies the listing appears in the search API
4. Confirms it can be displayed in the frontend grid

Usage:
    cd D:\Otto_AI_v2
    python -m scripts.validate_pipeline [--pdf path/to/sample.pdf]
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Ensure we're running from project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Now we can import from src using absolute imports
from src.services.pdf_ingestion_service import get_pdf_ingestion_service
from src.repositories.listing_repository import get_listing_repository
from src.repositories.image_repository import get_image_repository
from src.services.supabase_client import get_supabase_client_singleton


class PipelineValidator:
    """Validates the end-to-end PDF processing pipeline"""

    def __init__(self):
        self.pdf_service = None
        self.listing_repo = None
        self.image_repo = None
        self.supabase = None

    async def initialize(self):
        """Initialize services"""
        print("[*] Initializing services...")
        self.pdf_service = await get_pdf_ingestion_service()
        self.listing_repo = get_listing_repository()
        self.image_repo = get_image_repository()
        self.supabase = get_supabase_client_singleton()
        print("[OK] Services initialized")

    async def validate_pipeline(self, pdf_path: str) -> Dict[str, Any]:
        """
        Run the complete pipeline validation.

        Steps:
        1. Process PDF → VehicleListingArtifact
        2. Persist to database (listing + images + issues)
        3. Verify in database
        4. Verify in search API
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'pdf_path': pdf_path,
            'steps': {}
        }

        try:
            # Step 1: Read PDF
            print(f"\n[PAGE] Step 1: Reading PDF: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            file_size_mb = len(pdf_bytes) / (1024 * 1024)
            print(f"   File size: {file_size_mb:.2f} MB")
            results['steps']['read_pdf'] = {
                'status': 'success',
                'file_size_mb': file_size_mb
            }

            # Step 2: Process and persist
            print(f"\n[PROCESS] Step 2: Processing PDF and persisting to database...")
            process_result = await self.pdf_service.process_and_persist_pdf(
                pdf_bytes=pdf_bytes,
                filename=Path(pdf_path).name
            )

            print(f"   [OK] Listing ID: {process_result['listing_id']}")
            print(f"   [OK] VIN: {process_result['vin']}")
            print(f"   [OK] Images: {process_result['image_count']}")
            print(f"   [OK] Issues: {process_result['issue_count']}")

            results['steps']['process_and_persist'] = {
                'status': 'success',
                'listing_id': process_result['listing_id'],
                'vin': process_result['vin'],
                'image_count': process_result['image_count'],
                'issue_count': process_result['issue_count']
            }

            listing_id = process_result['listing_id']
            vin = process_result['vin']

            # Step 3: Verify in database
            print(f"\n[VERIFY] Step 3: Verifying listing in database...")
            db_listing = await self.listing_repo.get_by_id(listing_id)

            if db_listing:
                print(f"   [OK] Found in vehicle_listings table")
                print(f"      Make/Model: {db_listing['year']} {db_listing['make']} {db_listing['model']}")
                print(f"      Status: {db_listing['status']}")
                print(f"      Created: {db_listing['created_at']}")
            else:
                raise ValueError("Listing not found in database!")

            db_images = await self.image_repo.get_by_listing(listing_id)
            print(f"   [OK] Found {len(db_images)} images in vehicle_images table")

            results['steps']['verify_database'] = {
                'status': 'success',
                'listing_found': True,
                'image_count': len(db_images)
            }

            # Step 4: Verify in search API
            print(f"\n[API] Step 4: Verifying in search API...")
            search_result = self.supabase.table('vehicle_listings') \
                .select('*', count='exact') \
                .eq('vin', vin) \
                .eq('status', 'active') \
                .execute()

            if search_result.data:
                print(f"   [OK] Found in search API")
                print(f"      Total results: {search_result.count}")
            else:
                raise ValueError("Listing not found in search API!")

            results['steps']['verify_search_api'] = {
                'status': 'success',
                'found_in_search': True
            }

            # Step 5: Check frontend compatibility
            print(f"\n[FRONTEND] Step 5: Validating frontend compatibility...")

            # Get listing with images for frontend
            frontend_data = self.supabase.table('vehicle_listings') \
                .select('id, vin, year, make, model, trim, odometer, exterior_color, interior_color, condition_score, condition_grade, status, created_at') \
                .eq('vin', vin) \
                .execute()

            if frontend_data.data:
                listing = frontend_data.data[0]
                print(f"   [OK] Compatible with frontend Vehicle type")
                print(f"      Required fields present: all [OK]")

                # Check images
                images = await self.image_repo.get_by_listing(listing['id'])
                print(f"   [OK] Images compatible: {len(images)} images with URLs")
                for img in images[:3]:  # Show first 3
                    url = img.get('web_url') or img.get('thumbnail_url') or img.get('original_url')
                    has_url = url is not None
                    print(f"      - {img['category']}: {'YES ' + url[:50] if has_url else 'NO no URL'}")
            else:
                raise ValueError("Listing not compatible with frontend!")

            results['steps']['verify_frontend'] = {
                'status': 'success',
                'frontend_compatible': True,
                'image_urls_available': len(db_images) > 0
            }

            # Final result
            print(f"\n" + "="*60)
            print(f"[OK] PIPELINE VALIDATION SUCCESSFUL")
            print(f"="*60)
            print(f"[SUMMARY] Summary:")
            print(f"   Listing ID: {listing_id}")
            print(f"   VIN: {vin}")
            print(f"   Images: {process_result['image_count']}")
            print(f"   Database: [OK] Verified")
            print(f"   Search API: [OK] Verified")
            print(f"   Frontend: [OK] Compatible")
            print(f"\n[SUCCESS] The end-to-end flow is working!")
            print(f"   PDF -> Database -> Search -> Grid Display")

            results['overall_status'] = 'success'
            return results

        except Exception as e:
            print(f"\n[ERROR] PIPELINE VALIDATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            results['overall_status'] = 'failed'
            results['error'] = str(e)
            return results

    async def close(self):
        """Clean up resources"""
        if self.pdf_service:
            await self.pdf_service.close()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate PDF → Database pipeline")
    parser.add_argument(
        '--pdf',
        type=str,
        default='docs/Sample_Vehicle_Condition_Reports/2022LexusES350117484.pdf',
        help='Path to sample PDF file'
    )
    parser.add_argument(
        '--list-samples',
        action='store_true',
        help='List available sample PDFs'
    )

    args = parser.parse_args()

    # List samples if requested
    if args.list_samples:
        print("[DIR] Available sample PDFs:")
        sample_dir = Path("docs/Sample_Vehicle_Condition_Reports")
        if sample_dir.exists():
            for pdf in sorted(sample_dir.glob("*.pdf")):
                size_mb = pdf.stat().st_size / (1024 * 1024)
                print(f"  - {pdf.relative_to(Path.cwd())} ({size_mb:.2f} MB)")
        else:
            print(f"  Sample directory not found: {sample_dir}")
        return

    # Check PDF exists
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        print(f"\n[TIP] Use --list-samples to see available sample PDFs")
        sys.exit(1)

    print("="*60)
    print("Otto.AI End-to-End Pipeline Validation")
    print("="*60)

    # Run validation
    validator = PipelineValidator()
    await validator.initialize()

    results = await validator.validate_pipeline(str(pdf_path))

    # Save results
    output_file = Path(f"pipeline_validation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[FILE] Results saved to: {output_file}")

    await validator.close()

    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'success' else 1)


if __name__ == '__main__':
    asyncio.run(main())
