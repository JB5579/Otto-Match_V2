"""
Process Sample Vehicle Condition Reports
Ingests sample PDFs into Supabase database for testing
"""

import asyncio
import logging
import os
from pathlib import Path

from src.services.enhanced_pdf_ingestion_service import EnhancedPDFIngestionService
from src.services.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_sample_pdfs():
    """Process all sample vehicle condition report PDFs"""

    # Initialize services
    pdf_service = EnhancedPDFIngestionService()
    supabase = get_supabase_client()

    # Sample PDFs directory
    sample_dir = Path("docs/Sample_Vehicle_Condition_Reports")

    if not sample_dir.exists():
        logger.error(f"Sample directory not found: {sample_dir}")
        return

    # Get all PDF files
    pdf_files = list(sample_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} sample PDF files to process")

    results = {
        'success': [],
        'failed': [],
        'total': len(pdf_files)
    }

    for pdf_file in pdf_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pdf_file.name}")
        logger.info(f"{'='*60}")

        try:
            # Read PDF file
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()

            # Process through enhanced PDF ingestion pipeline
            artifact = await pdf_service.process_condition_report_with_market_data(
                pdf_bytes=pdf_bytes,
                filename=pdf_file.name,
                region='US',  # Default region
                zip_code=None
            )

            # Store in Supabase
            vehicle_data = await _store_vehicle_listing(supabase, artifact, pdf_file.name)

            logger.info(f"✅ SUCCESS: {pdf_file.name}")
            logger.info(f"   Vehicle: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
            logger.info(f"   VIN: {artifact.vehicle.vin}")
            logger.info(f"   Odometer: {artifact.vehicle.odometer:,} miles")

            results['success'].append({
                'file': pdf_file.name,
                'vehicle': f"{artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}",
                'vin': artifact.vehicle.vin,
                'odometer': artifact.vehicle.odometer
            })

        except Exception as e:
            logger.error(f"❌ FAILED: {pdf_file.name} - {str(e)}")
            results['failed'].append({
                'file': pdf_file.name,
                'error': str(e)
            })

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("PROCESSING SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total: {results['total']}")
    logger.info(f"Success: {len(results['success'])}")
    logger.info(f"Failed: {len(results['failed'])}")

    if results['success']:
        logger.info(f"\n✅ Successfully Processed Vehicles:")
        for v in results['success']:
            logger.info(f"   - {v['vehicle']} ({v['vin']})")

    if results['failed']:
        logger.warning(f"\n❌ Failed Processing:")
        for f in results['failed']:
            logger.warning(f"   - {f['file']}: {f['error']}")

    return results


async def _store_vehicle_listing(supabase, artifact, filename):
    """Store vehicle listing in Supabase"""

    vehicle = artifact.vehicle

    # Prepare vehicle data for insertion
    # Use getattr with fallbacks for robustness
    listing_data = {
        'vin': vehicle.vin,
        'year': vehicle.year,
        'make': vehicle.make,
        'model': vehicle.model,
        'trim': getattr(vehicle, 'trim', None) or '',
        'odometer': getattr(vehicle, 'odometer', 0) or 0,
        'drivetrain': getattr(vehicle, 'drivetrain', 'Unknown') or 'Unknown',
        'transmission': getattr(vehicle, 'transmission', 'Unknown') or 'Unknown',
        'engine': getattr(vehicle, 'engine', 'Unknown') or 'Unknown',
        'exterior_color': getattr(vehicle, 'exterior_color', 'Unknown') or 'Unknown',
        'interior_color': getattr(vehicle, 'interior_color', 'Unknown') or 'Unknown',
        'body_style': getattr(vehicle, 'body_style', 'SUV') or 'SUV',
        'fuel_type': getattr(vehicle, 'fuel_type', 'Gasoline') or 'Gasoline',
        'vehicle_type': getattr(vehicle, 'vehicle_type', 'SUV') or 'SUV',
        'condition_score': 4.0,
        'condition_grade': 'Average',
        'description_text': f"{vehicle.year} {vehicle.make} {vehicle.model}",
        'status': 'active',
        'listing_source': 'pdf_upload',
        'asking_price': None,  # VehicleInfo doesn't have price field
        'processing_metadata': {
            'source_file': filename,
            'extraction_method': 'enhanced_pdf_ingestion',
            'processed_at': str(artifact.processing_metadata.get('processing_time', 'unknown'))
        }
    }

    # Upsert into vehicle_listings table (handle duplicate VINs)
    result = supabase.table('vehicle_listings').upsert(
        listing_data,
        on_conflict='vin'  # VIN is the unique constraint
    ).execute()

    if result.data:
        listing_id = result.data[0]['id']
        action = "Updated" if len(result.data) > 0 else "Inserted"
        logger.info(f"{action} vehicle listing: {listing_id}")

        # Store images if available
        if hasattr(artifact, 'images') and artifact.images:
            try:
                await _store_vehicle_images(supabase, listing_id, artifact.images, vehicle)
            except Exception as e:
                logger.warning(f"Failed to store images: {str(e)}")

        return listing_id
    else:
        raise Exception("Failed to store vehicle listing")


async def _store_vehicle_images(supabase, listing_id, images, vehicle):
    """Store vehicle images in Supabase

    Note: images are EnrichedImage Pydantic models, not dicts - use attribute access
    """

    for idx, image in enumerate(images):
        try:
            image_data = {
                'listing_id': listing_id,
                'vin': vehicle.vin,
                'category': 'hero' if idx == 0 else 'carousel',
                'vehicle_angle': getattr(image, 'vehicle_angle', 'exterior'),
                'description': getattr(image, 'description', f"{vehicle.year} {vehicle.make} {vehicle.model}"),
                'suggested_alt': getattr(image, 'suggested_alt', f"{vehicle.make} {vehicle.model}"),
                'quality_score': getattr(image, 'quality_score', 8),
                'file_format': 'jpeg',
                'display_order': idx,
                'processing_metadata': {
                    'source': 'pdf_extraction',
                    'page_number': getattr(image, 'page_number', 1)
                }
            }

            supabase.table('vehicle_images').insert(image_data).execute()
            logger.info(f"  Stored image {idx + 1}: {getattr(image, 'vehicle_angle', 'exterior')}")

        except Exception as e:
            logger.warning(f"  Failed to store image {idx + 1}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(process_sample_pdfs())
