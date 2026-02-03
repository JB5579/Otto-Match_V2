"""
Simple RAG-Anything Real Data Test
Tests vehicle processing with real Condition Report PDFs using RAG-Anything
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_raganything_with_pdfs():
    """Test RAG-Anything processing with real PDFs"""

    print("Testing RAG-Anything with Real Condition Report PDFs")
    print("=" * 60)

    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')

    print(f"Supabase URL: {supabase_url}")
    print(f"OpenRouter API Key: {'SET' if openrouter_key else 'NOT SET'}")

    # Initialize service without database first (test RAG-Anything only)
    service = VehicleProcessingService()
    service.openrouter_api_key = openrouter_key
    service.embedding_dim = 3072

    # Find PDF files
    pdf_dir = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found!")
        return False

    print(f"Found {len(pdf_files)} PDF files")

    # Test processing without database (RAG-Anything only)
    results = []
    total_time = 0
    successful_count = 0

    for i, pdf_path in enumerate(pdf_files[:3]):  # Test first 3 files
        print(f"\nProcessing {i+1}: {pdf_path.name}")

        # Create vehicle data with PDF as image
        vehicle_data = VehicleData(
            vehicle_id=f"test-{pdf_path.stem}",
            make="Test",
            model="Vehicle",
            year=2020,
            description=f"Test processing of {pdf_path.name}",
            images=[{
                "path": str(pdf_path),
                "type": "exterior"
            }],
            metadata={
                "source_file": pdf_path.name
            }
        )

        start_time = time.time()

        try:
            # Process the vehicle data
            result = await service.process_vehicle_data(vehicle_data)
            processing_time = time.time() - start_time

            total_time += processing_time

            if result.success:
                successful_count += 1
                print(f"  SUCCESS in {processing_time:.3f}s")
                print(f"  Text processed: {result.text_processed}")
                print(f"  Images processed: {result.images_processed}")
                print(f"  Semantic tags: {result.semantic_tags[:5]}")
                print(f"  Embedding dim: {result.embedding_dim}")

                results.append({
                    "file": pdf_path.name,
                    "success": True,
                    "time": processing_time,
                    "tags": result.semantic_tags,
                    "embedding_dim": result.embedding_dim
                })
            else:
                print(f"  FAILED: {result.error}")
                results.append({
                    "file": pdf_path.name,
                    "success": False,
                    "error": result.error,
                    "time": processing_time
                })

        except Exception as e:
            processing_time = time.time() - start_time
            total_time += processing_time
            print(f"  ERROR: {e}")
            results.append({
                "file": pdf_path.name,
                "success": False,
                "error": str(e),
                "time": processing_time
            })

    # Generate summary report
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(results)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {len(results) - successful_count}")
    print(f"Success rate: {(successful_count/len(results))*100:.1f}%")
    print(f"Total processing time: {total_time:.3f}s")
    print(f"Average time per file: {total_time/len(results):.3f}s")

    # Show sample results
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        print(f"\nSample successful results:")
        for result in successful_results[:2]:
            print(f"  {result['file']}: {result['time']:.3f}s, {len(result['tags'])} tags")
            print(f"    Tags: {result['tags'][:3]}")

    # Show failed files
    failed_results = [r for r in results if not r["success"]]
    if failed_results:
        print(f"\nFailed files:")
        for result in failed_results:
            print(f"  {result['file']}: {result.get('error', 'Unknown error')}")

    # Assessment
    success_rate = (successful_count/len(results))*100
    avg_time = total_time/len(results)

    print(f"\nASSESSMENT:")
    if success_rate >= 80 and avg_time < 2.0:
        print("PASS: RAG-Anything processing working well with real PDFs")
        print("Performance meets requirements")
    elif success_rate >= 60:
        print("PARTIAL: RAG-Anything processing functional but needs optimization")
    else:
        print("FAIL: RAG-Anything processing needs significant work")

    return success_rate >= 60

if __name__ == "__main__":
    success = asyncio.run(test_raganything_with_pdfs())
    exit(0 if success else 1)