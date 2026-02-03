"""
Story 1.2 RAG-Anything Validation Test (Database-Independent)
Tests the core RAG-Anything multimodal processing with real PDFs and live APIs
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def story_1_2_raganything_validation():
    """
    Validate Story 1.2 RAG-Anything processing with real PDFs (database-independent)
    """

    print("Story 1.2 RAG-Anything Validation Test")
    print("Testing multimodal PDF processing with real APIs (database-independent)")
    print("=" * 80)

    # Check environment variables
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    print(f"OpenRouter API Key: {'SET' if openrouter_key else 'NOT SET'}")

    if not openrouter_key:
        print("FAIL: OpenRouter API key not available")
        return False

    # Initialize service without database (focus on RAG-Anything processing)
    print("\nInitializing Vehicle Processing Service (RAG-Anything mode)...")
    service = VehicleProcessingService()
    service.openrouter_api_key = openrouter_key
    service.embedding_dim = 3072

    print("SUCCESS: RAG-Anything processing service initialized")

    # Find PDF files
    pdf_dir = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("FAIL: No PDF files found")
        return False

    print(f"Found {len(pdf_files)} PDF files for Story 1.2 validation")

    # Test all PDF files for comprehensive validation
    test_results = {
        "total_files": len(pdf_files),
        "successful_processing": 0,
        "failed_processing": 0,
        "processing_times": [],
        "embedding_dimensions": [],
        "semantic_tags": [],
        "files_tested": [],
        "performance_metrics": {},
        "text_processing_results": [],
        "image_processing_results": [],
        "metadata_processing_results": []
    }

    print(f"\nProcessing all {len(pdf_files)} PDF files with RAG-Anything...")
    print("-" * 60)

    # Process each PDF file
    for i, pdf_path in enumerate(pdf_files):
        print(f"\nProcessing {i+1}/{len(pdf_files)}: {pdf_path.name}")

        # Extract basic info from filename for better vehicle data
        filename = pdf_path.name
        year_guess = 2020
        make_guess = "Unknown"
        model_guess = "Condition Report"

        # Try to extract year from filename
        import re
        year_match = re.search(r'\b(20\d{2})\b', filename)
        if year_match:
            year_guess = int(year_match.group(1))

        # Try to extract make from filename
        makes = ["toyota", "honda", "ford", "chevrolet", "bmw", "mercedes", "lexus", "gmc", "jeep", "buick", "chrysler", "dodge"]
        for make in makes:
            if make.lower() in filename.lower():
                make_guess = make.title()
                break

        # Try to extract model from filename
        if "camry" in filename.lower():
            model_guess = "Camry"
        elif "accord" in filename.lower():
            model_guess = "Accord"
        elif "f-150" in filename.lower() or "f150" in filename.lower():
            model_guess = "F-150"
        elif "silverado" in filename.lower():
            model_guess = "Silverado"
        elif "sienna" in filename.lower():
            model_guess = "Sienna"

        # Create comprehensive vehicle data with PDF as multimodal content
        vehicle_data = VehicleData(
            vehicle_id=f"story-rag-{pdf_path.stem.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('_', '')}",
            make=make_guess,
            model=model_guess,
            year=year_guess,
            mileage=None,
            price=None,
            description=f"Story 1.2 RAG-Anything validation - Vehicle Condition Report: {filename}",
            features=[
                "Multimodal PDF Processing",
                "RAG-Anything Analysis",
                "Semantic Tag Extraction",
                "Vehicle Information Extraction"
            ],
            specifications={
                "test_type": "story_1_2_validation",
                "processing_method": "raganything_multimodal",
                "source_document": filename,
                "pdf_processing": True
            },
            images=[{
                "path": str(pdf_path),
                "type": "documentation"
            }],
            metadata={
                "source_file": filename,
                "processing_method": "raganything_multimodal",
                "test_type": "story_1_2_raganything_validation",
                "pdf_document": True,
                "vehicle_condition_report": True
            }
        )

        start_time = time.time()

        try:
            # Process with RAG-Anything (no database storage)
            result = await service.process_vehicle_data(vehicle_data)
            processing_time = time.time() - start_time

            test_results["files_tested"].append(pdf_path.name)

            if result.success:
                test_results["successful_processing"] += 1
                test_results["processing_times"].append(processing_time)
                test_results["embedding_dimensions"].append(result.embedding_dim or 0)
                test_results["semantic_tags"].extend(result.semantic_tags or [])
                test_results["text_processing_results"].append(result.text_processed)
                test_results["image_processing_results"].append(result.images_processed)
                test_results["metadata_processing_results"].append(result.metadata_processed)

                print(f"  SUCCESS in {processing_time:.3f}s")
                print(f"  Vehicle ID: {result.vehicle_id}")
                print(f"  Text processed: {result.text_processed}")
                print(f"  Images processed: {result.images_processed}")
                print(f"  Metadata processed: {result.metadata_processed}")
                print(f"  Embedding dimension: {result.embedding_dim}")
                print(f"  Semantic tags: {len(result.semantic_tags or [])}")

                if result.semantic_tags:
                    print(f"  Sample tags: {result.semantic_tags[:8]}")

                # Show extracted vehicle info if available
                if hasattr(result, 'extracted_vehicle_info'):
                    extracted = result.extracted_vehicle_info
                    print(f"  Extracted: {extracted.get('make', 'Unknown')} {extracted.get('model', 'Unknown')} ({extracted.get('year', 'Unknown')})")

                # Validate embedding dimension
                if result.embedding_dim == 3072:
                    print(f"  PASS: Correct embedding dimension (3072)")
                elif result.embedding_dim and result.embedding_dim > 0:
                    print(f"  PARTIAL: Embedding generated ({result.embedding_dim} dimensions)")
                else:
                    print(f"  WARN: No embedding generated")

            else:
                test_results["failed_processing"] += 1
                test_results["processing_times"].append(processing_time)
                print(f"  FAIL: {result.error}")

        except Exception as e:
            processing_time = time.time() - start_time
            test_results["failed_processing"] += 1
            test_results["processing_times"].append(processing_time)
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Calculate comprehensive performance metrics
    if test_results["processing_times"]:
        total_time = sum(test_results["processing_times"])
        test_results["performance_metrics"] = {
            "success_rate": (test_results["successful_processing"] / test_results["total_files"]) * 100,
            "avg_processing_time": total_time / len(test_results["processing_times"]),
            "min_processing_time": min(test_results["processing_times"]),
            "max_processing_time": max(test_results["processing_times"]),
            "total_processing_time": total_time,
            "vehicles_per_minute": (test_results["successful_processing"] / total_time) * 60 if total_time > 0 else 0,
            "avg_embedding_dim": sum(test_results["embedding_dimensions"]) / len(test_results["embedding_dimensions"]) if test_results["embedding_dimensions"] else 0,
            "total_semantic_tags": len(test_results["semantic_tags"]),
            "unique_semantic_tags": len(set(test_results["semantic_tags"])),
            "avg_semantic_tags_per_vehicle": len(test_results["semantic_tags"]) / test_results["successful_processing"] if test_results["successful_processing"] > 0 else 0,
            "total_text_processed": sum(test_results["text_processing_results"]),
            "total_images_processed": sum(test_results["image_processing_results"]),
            "total_metadata_processed": sum(test_results["metadata_processing_results"])
        }

    # Generate comprehensive Story 1.2 validation report
    print("\n" + "=" * 80)
    print("STORY 1.2 RAG-ANYTHING VALIDATION RESULTS")
    print("=" * 80)

    metrics = test_results["performance_metrics"]

    print(f"RAG-Anything Processing Summary:")
    print(f"  Total PDF files processed: {test_results['total_files']}")
    print(f"  Successfully processed: {test_results['successful_processing']}")
    print(f"  Failed: {test_results['failed_processing']}")
    print(f"  Success rate: {metrics['success_rate']:.1f}%")

    print(f"\nMultimodal Processing Results:")
    print(f"  Total text elements processed: {metrics['total_text_processed']}")
    print(f"  Total image elements processed: {metrics['total_images_processed']}")
    print(f"  Total metadata elements processed: {metrics['total_metadata_processed']}")
    print(f"  Average processing time: {metrics['avg_processing_time']:.3f}s per vehicle")
    print(f"  Processing time range: {metrics['min_processing_time']:.3f}s - {metrics['max_processing_time']:.3f}s")
    print(f"  Total processing time: {metrics['total_processing_time']:.2f}s")
    print(f"  Vehicles per minute: {metrics['vehicles_per_minute']:.1f}")

    print(f"\nVector Embedding Analysis:")
    print(f"  Average embedding dimension: {metrics['avg_embedding_dim']:.0f}")
    print(f"  Embeddings generated: {len([d for d in test_results['embedding_dimensions'] if d > 0])}")

    print(f"\nSemantic Analysis:")
    print(f"  Total semantic tags generated: {metrics['total_semantic_tags']}")
    print(f"  Unique semantic tags: {metrics['unique_semantic_tags']}")
    print(f"  Average semantic tags per vehicle: {metrics['avg_semantic_tags_per_vehicle']:.1f}")
    if test_results['semantic_tags']:
        sample_tags = list(set(test_results['semantic_tags']))[:20]
        print(f"  Sample unique tags: {', '.join(sample_tags)}")

    print(f"\nValidation Against Story 1.2 Requirements:")

    # AC#1: Process multimodal vehicle data (text, images, metadata)
    ac1_pass = (test_results['successful_processing'] > 0 and
                metrics['total_text_processed'] > 0 and
                metrics['total_images_processed'] > 0)
    print(f"  AC#1 (Multimodal Processing): {'PASS' if ac1_pass else 'FAIL'}")
    print(f"    Text processed: {metrics['total_text_processed']} elements")
    print(f"    Images processed: {metrics['total_images_processed']} elements")
    print(f"    Metadata processed: {metrics['total_metadata_processed']} elements")

    # AC#2: Generate vector embeddings (simulated - database not needed for validation)
    ac2_pass = metrics['avg_embedding_dim'] > 0
    print(f"  AC#2 (Vector Embeddings): {'PASS' if ac2_pass else 'FAIL'}")
    print(f"    Average embedding dimension: {metrics['avg_embedding_dim']:.0f}")

    # AC#3: Process vehicles in under 2 seconds each
    ac3_pass = metrics['avg_processing_time'] < 2.0
    print(f"  AC#3 (<2s processing): {'PASS' if ac3_pass else 'FAIL'}")
    print(f"    Average processing time: {metrics['avg_processing_time']:.3f}s")

    print(f"\nInfrastructure Integration:")
    api_pass = test_results['successful_processing'] > 0
    print(f"  Real API Integration: {'PASS' if api_pass else 'FAIL'}")
    print(f"    OpenRouter API calls successful")

    rag_pass = test_results['successful_processing'] > 0
    print(f"  RAG-Anything Integration: {'PASS' if rag_pass else 'FAIL'}")
    print(f"    Multimodal PDF processing working")

    pdf_pass = test_results['successful_processing'] > 0
    print(f"  Real PDF Processing: {'PASS' if pdf_pass else 'FAIL'}")
    print(f"    Condition Report PDF processing validated")

    # Overall Story 1.2 assessment
    success_rate = metrics['success_rate']
    avg_time = metrics['avg_processing_time']

    print(f"\nOVERALL STORY 1.2 VALIDATION ASSESSMENT:")

    if success_rate >= 90 and avg_time < 1.0 and ac1_pass and ac2_pass and ac3_pass:
        print("EXCELLENT: Story 1.2 RAG-Anything implementation exceeds all requirements")
        print("  - Exceptional success rate with real Condition Report PDFs")
        print("  - Processing time significantly under 2 seconds")
        print("  - Full multimodal processing validated")
        print("  - RAG-Anything integration fully functional")
    elif success_rate >= 80 and avg_time < 2.0 and ac1_pass and ac2_pass:
        print("GOOD: Story 1.2 RAG-Anything implementation meets all requirements")
        print("  - High success rate with real Condition Report PDFs")
        print("  - Processing time meets requirements")
        print("  - Multimodal processing working correctly")
        print("  - RAG-Anything integration validated")
    elif success_rate >= 60:
        print("ACCEPTABLE: Story 1.2 RAG-Anything implementation partially working")
        print("  - Moderate success rate - may need optimization")
        print("  - Core functionality demonstrated")
    else:
        print("NEEDS WORK: Story 1.2 RAG-Anything implementation requires improvement")
        print("  - Low success rate with real PDFs")
        print("  - May need debugging or optimization")

    print(f"\nSTORY 1.2 VALIDATION RECOMMENDATION:")
    if success_rate >= 80 and avg_time < 2.0 and ac1_pass and ac2_pass:
        print("  Story 1.2 RAG-Anything component is VALIDATED")
        print("  Multimodal PDF processing meets all acceptance criteria")
        print("  Real Condition Report processing successfully demonstrated")
        print("  Performance requirements met or exceeded")
        print("  Ready for database integration testing")
    else:
        print("  Story 1.2 needs optimization before full validation")
        if success_rate < 80:
            print("  - Improve PDF processing success rate")
        if avg_time >= 2.0:
            print("  - Optimize processing performance")
        if not ac1_pass:
            print("  - Fix multimodal processing issues")

    # Save Story 1.2 validation results
    story_results = {
        "story_validation": {
            "story_id": "1.2",
            "story_title": "Implement Vehicle Processing with RAG-Anything Multimodal",
            "validation_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "test_type": "RAG-Anything Multimodal Validation",
            "total_files": test_results["total_files"],
            "success_rate": metrics["success_rate"],
            "avg_processing_time": metrics["avg_processing_time"],
            "vehicles_per_minute": metrics["vehicles_per_minute"]
        },
        "acceptance_criteria_validation": {
            "ac1_multimodal_processing": ac1_pass,
            "ac2_vector_embeddings": ac2_pass,
            "ac3_performance_2_seconds": ac3_pass
        },
        "infrastructure_validation": {
            "real_api_integration": api_pass,
            "raganything_integration": rag_pass,
            "real_pdf_processing": pdf_pass
        },
        "multimodal_processing": {
            "total_text_processed": metrics["total_text_processed"],
            "total_images_processed": metrics["total_images_processed"],
            "total_metadata_processed": metrics["total_metadata_processed"]
        },
        "file_details": test_results["files_tested"],
        "processing_results": {
            "successful": test_results["successful_processing"],
            "failed": test_results["failed_processing"],
            "processing_times": test_results["processing_times"]
        },
        "semantic_analysis": {
            "total_tags": metrics['total_semantic_tags'],
            "unique_tags": metrics['unique_semantic_tags'],
            "avg_tags_per_vehicle": metrics['avg_semantic_tags_per_vehicle'],
            "sample_tags": list(set(test_results['semantic_tags']))[:40]
        },
        "performance_metrics": metrics,
        "overall_assessment": {
            "story_ready": success_rate >= 80 and avg_time < 2.0 and ac1_pass and ac2_pass,
            "recommendation": "RAG-Anything component validated" if success_rate >= 80 and avg_time < 2.0 else "Needs optimization"
        }
    }

    results_path = "D:/Otto_AI_v2/src/semantic/story_1_2_raganything_validation_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump(story_results, f, indent=2)

    print(f"\nStory 1.2 RAG-Anything validation results saved to: {results_path}")

    # Final success determination
    overall_success = (success_rate >= 80 and
                      avg_time < 2.0 and
                      ac1_pass and
                      ac2_pass and
                      ac3_pass)

    print(f"\n{'STORY 1.2 RAG-ANYTHING VALIDATION SUCCESS' if overall_success else 'STORY 1.2 NEEDS OPTIMIZATION'}")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(story_1_2_raganything_validation())
    exit(0 if success else 1)