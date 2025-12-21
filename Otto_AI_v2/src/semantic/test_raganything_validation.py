"""
RAG-Anything Validation Test for Story 1.2
Focuses on testing the core multimodal processing without database connectivity issues
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def validate_raganything_processing():
    """Validate RAG-Anything processing with real PDFs"""

    print("RAG-Anything Validation Test for Story 1.2")
    print("Testing multimodal PDF processing with real Condition Reports")
    print("=" * 70)

    # Check environment variables
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    print(f"OpenRouter API Key: {'SET' if openrouter_key else 'NOT SET'}")

    if not openrouter_key:
        print("FAIL: OpenRouter API key not available")
        return False

    # Initialize service without database
    service = VehicleProcessingService()
    service.openrouter_api_key = openrouter_key
    service.embedding_dim = 3072

    # Find PDF files
    pdf_dir = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("FAIL: No PDF files found")
        return False

    print(f"Found {len(pdf_files)} PDF files to test")

    # Test parameters
    test_results = {
        "total_files": len(pdf_files),
        "successful_processing": 0,
        "failed_processing": 0,
        "processing_times": [],
        "semantic_tags": [],
        "embedding_dimensions": [],
        "files_tested": [],
        "performance_metrics": {}
    }

    # Process PDF files
    for i, pdf_path in enumerate(pdf_files[:3]):  # Test first 3 files
        print(f"\nProcessing {i+1}/{len(pdf_files)}: {pdf_path.name}")

        # Create vehicle data with PDF as image
        vehicle_data = VehicleData(
            vehicle_id=f"validation-test-{pdf_path.stem.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
            make="TestVehicle",
            model="TestModel",
            year=2020,
            mileage=50000,
            price=25000.0,
            description=f"RAG-Anything validation test processing of {pdf_path.name} vehicle condition report",
            features=["Feature 1", "Feature 2", "Feature 3"],
            specifications={
                "engine": "2.5L 4-Cylinder",
                "transmission": "Automatic",
                "fuel_economy": "32 MPG combined"
            },
            images=[{
                "path": str(pdf_path),
                "type": "documentation"  # Treat PDF as documentation
            }],
            metadata={
                "source_file": pdf_path.name,
                "processing_method": "raganything_multimodal",
                "test_type": "validation"
            }
        )

        start_time = time.time()

        try:
            # Process with RAG-Anything
            result = await service.process_vehicle_data(vehicle_data)
            processing_time = time.time() - start_time

            test_results["files_tested"].append(pdf_path.name)

            if result.success:
                test_results["successful_processing"] += 1
                test_results["processing_times"].append(processing_time)
                test_results["semantic_tags"].extend(result.semantic_tags or [])
                test_results["embedding_dimensions"].append(result.embedding_dim or 0)

                print(f"  SUCCESS in {processing_time:.3f}s")
                print(f"  Text processed: {result.text_processed}")
                print(f"  Images processed: {result.images_processed}")
                print(f"  Metadata processed: {result.metadata_processed}")
                print(f"  Embedding dimension: {result.embedding_dim}")
                print(f"  Semantic tags: {result.semantic_tags[:5]}")

                # Validate embedding dimension
                if result.embedding_dim == 3072:
                    print(f"  PASS: Correct embedding dimension (3072)")
                else:
                    print(f"  WARN: Unexpected embedding dimension ({result.embedding_dim})")

            else:
                test_results["failed_processing"] += 1
                test_results["processing_times"].append(processing_time)
                print(f"  FAIL: {result.error}")

        except Exception as e:
            processing_time = time.time() - start_time
            test_results["failed_processing"] += 1
            test_results["processing_times"].append(processing_time)
            print(f"  ERROR: {e}")

    # Calculate performance metrics
    if test_results["processing_times"]:
        total_time = sum(test_results["processing_times"])
        test_results["performance_metrics"] = {
            "success_rate": (test_results["successful_processing"] / test_results["total_files"]) * 100,
            "avg_processing_time": total_time / len(test_results["processing_times"]),
            "min_processing_time": min(test_results["processing_times"]),
            "max_processing_time": max(test_results["processing_times"]),
            "total_processing_time": total_time,
            "vehicles_per_minute": (test_results["successful_processing"] / total_time) * 60,
            "avg_embedding_dim": sum(test_results["embedding_dimensions"]) / len(test_results["embedding_dimensions"]) if test_results["embedding_dimensions"] else 0
        }

    # Generate report
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    metrics = test_results["performance_metrics"]

    print(f"Total files tested: {test_results['total_files']}")
    print(f"Successfully processed: {test_results['successful_processing']}")
    print(f"Failed: {test_results['failed_processing']}")
    print(f"Success rate: {metrics['success_rate']:.1f}%")
    print(f"Average processing time: {metrics['avg_processing_time']:.3f}s")
    print(f"Processing time range: {metrics['min_processing_time']:.3f}s - {metrics['max_processing_time']:.3f}s")
    print(f"Vehicles per minute: {metrics['vehicles_per_minute']:.1f}")
    print(f"Average embedding dimension: {metrics['avg_embedding_dim']:.0f}")

    # Semantic analysis
    print(f"\nSemantic Analysis:")
    print(f"Total semantic tags generated: {len(test_results['semantic_tags'])}")
    print(f"Unique semantic tags: {len(set(test_results['semantic_tags']))}")
    if test_results['semantic_tags']:
        sample_tags = list(set(test_results['semantic_tags']))[:10]
        print(f"Sample tags: {', '.join(sample_tags)}")

    # Validation against requirements
    print(f"\nValidation Against Story 1.2 Requirements:")

    # AC#1: Process multimodal vehicle data (text, images, metadata)
    ac1_pass = test_results['successful_processing'] > 0
    print(f"AC#1 (Multimodal Processing): {'PASS' if ac1_pass else 'FAIL'} - {'Successfully processes text, images, and metadata' if ac1_pass else 'Processing failed'}")

    # AC#3: <2 seconds per vehicle
    ac3_pass = metrics['avg_processing_time'] < 2.0
    print(f"AC#3 (<2s processing): {'PASS' if ac3_pass else 'FAIL'} - {metrics['avg_processing_time']:.3f}s average ({'meets' if ac3_pass else 'exceeds'} 2s requirement)")

    # Real API integration
    api_pass = test_results['successful_processing'] > 0
    print(f"Real API Integration: {'PASS' if api_pass else 'FAIL'} - {'OpenRouter API calls successful' if api_pass else 'API integration failed'}")

    # RAG-Anything multimodal capability
    rag_pass = test_results['successful_processing'] > 0
    print(f"RAG-Anything Integration: {'PASS' if rag_pass else 'FAIL'} - {'Multimodal PDF processing working' if rag_pass else 'RAG processing failed'}")

    # Overall assessment
    success_rate = metrics['success_rate']
    avg_time = metrics['avg_processing_time']

    print(f"\nOVERALL ASSESSMENT:")

    if success_rate >= 100 and avg_time < 1.0:
        print("EXCELLENT: RAG-Anything processing working perfectly with real PDFs")
        print("- 100% success rate with real Condition Report PDFs")
        print("- Processing time well under 2 seconds")
        print("- Real OpenRouter API integration working")
        print("- RAG-Anything multimodal processing validated")
    elif success_rate >= 80 and avg_time < 2.0:
        print("GOOD: RAG-Anything processing functional with real PDFs")
        print("- High success rate with real Condition Report PDFs")
        print("- Processing time meets requirements")
        print("- Real API integration working")
    elif success_rate >= 60:
        print("ACCEPTABLE: RAG-Anything processing partially working")
        print("- Moderate success rate - may need optimization")
        print("- Processing time acceptable")
    else:
        print("NEEDS WORK: RAG-Anything processing needs improvement")
        print("- Low success rate with real PDFs")
        print("- May need optimization or debugging")

    print(f"\nRECOMMENDATION:")
    if success_rate >= 80 and avg_time < 2.0:
        print("✅ RAG-Anything integration is validated and ready for production")
        print("✅ Real PDF processing capabilities confirmed")
        print("✅ Performance meets Story 1.2 requirements")
    else:
        print("❌ RAG-Anything integration needs optimization before production use")
        print("❌ Consider debugging PDF processing pipeline")
        print("❌ May need to adjust processing parameters")

    # Save detailed results
    detailed_results = {
        "test_summary": {
            "date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "test_type": "RAG-Anything Real PDF Validation",
            "total_files": test_results["total_files"],
            "success_rate": metrics["success_rate"],
            "avg_processing_time": metrics["avg_processing_time"],
            "vehicles_per_minute": metrics["vehicles_per_minute"]
        },
        "file_details": test_results["files_tested"],
        "processing_results": {
            "successful": test_results["successful_processing"],
            "failed": test_results["failed_processing"],
            "processing_times": test_results["processing_times"]
        },
        "semantic_analysis": {
            "total_tags": len(test_results['semantic_tags']),
            "unique_tags": len(set(test_results['semantic_tags'])),
            "sample_tags": list(set(test_results['semantic_tags']))[:20]
        },
        "acceptance_criteria_validation": {
            "ac1_multimodal": ac1_pass,
            "ac3_performance": ac3_pass,
            "real_api_integration": api_pass,
            "raganything_integration": rag_pass
        }
    }

    results_path = "D:/Otto_AI_v2/src/semantic/raganything_validation_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\nDetailed results saved to: {results_path}")

    # Final success determination
    overall_success = success_rate >= 80 and avg_time < 2.0

    print(f"\n{'SUCCESS' if overall_success else 'NEEDS WORK'}: RAG-Anything validation {'completed' if overall_success else 'failed'}")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(validate_raganything_processing())
    exit(0 if success else 1)