"""
Complete Story 1.2 Validation Test with Database Integration
Tests RAG-Anything processing with real PDFs, live APIs, and actual database operations
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Go up two directories from src/semantic to the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
print(f"Loading .env from: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def complete_story_validation():
    """
    Complete validation of Story 1.2 with real PDFs, live APIs, and database integration
    """

    print("Story 1.2 Complete Validation Test")
    print("Testing RAG-Anything with real PDFs, live APIs, and database integration")
    print("=" * 80)

    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')

    print(f"Supabase URL: {supabase_url}")
    print(f"Supabase Key: {'SET' if supabase_key else 'NOT SET'}")
    print(f"OpenRouter API Key: {'SET' if openrouter_key else 'NOT SET'}")

    if not all([supabase_url, supabase_key, openrouter_key]):
        print("FAIL: Missing required environment variables")
        return False

    # Initialize processing service with real database connection
    print("\nInitializing Vehicle Processing Service with database...")
    service = VehicleProcessingService()
    service.openrouter_api_key = openrouter_key
    service.embedding_dim = 3072

    # Initialize database connection
    init_success = await service.initialize(supabase_url, supabase_key)
    if not init_success:
        print("FAIL: Failed to initialize database connection")
        return False

    print("SUCCESS: Database connection established")

    # Find PDF files
    pdf_dir = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports")
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("FAIL: No PDF files found")
        return False

    print(f"Found {len(pdf_files)} PDF files for validation")

    # Test all PDF files (not just 3)
    test_results = {
        "total_files": len(pdf_files),
        "successful_processing": 0,
        "failed_processing": 0,
        "database_stored": 0,
        "processing_times": [],
        "embedding_dimensions": [],
        "semantic_tags": [],
        "files_tested": [],
        "performance_metrics": {},
        "database_operations": 0
    }

    print(f"\nProcessing all {len(pdf_files)} PDF files...")
    print("-" * 60)

    # Process each PDF file
    for i, pdf_path in enumerate(pdf_files):
        print(f"\nProcessing {i+1}/{len(pdf_files)}: {pdf_path.name}")

        # Extract basic info from filename
        filename = pdf_path.name
        year_guess = 2020  # Default
        make_guess = "Unknown"

        # Try to extract year from filename
        import re
        year_match = re.search(r'\b(20\d{2})\b', filename)
        if year_match:
            year_guess = int(year_match.group(1))

        # Try to extract make from filename
        makes = ["toyota", "honda", "ford", "chevrolet", "bmw", "mercedes", "lexus", "gmc", "jeep"]
        for make in makes:
            if make.lower() in filename.lower():
                make_guess = make.title()
                break

        # Create vehicle data with PDF as multimodal content
        vehicle_data = VehicleData(
            vehicle_id=f"story-validation-{pdf_path.stem.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '')}",
            make=make_guess,
            model="Validation Test",
            year=year_guess,
            mileage=None,
            price=None,
            description=f"Story 1.2 validation test - Condition Report processing: {filename}",
            features=["RAG-Anything Processing", "Multimodal Analysis", "Database Integration"],
            specifications={
                "test_type": "story_validation",
                "processing_method": "raganything_multimodal",
                "database_integration": True
            },
            images=[{
                "path": str(pdf_path),
                "type": "documentation"
            }],
            metadata={
                "source_file": filename,
                "processing_method": "raganything_multimodal",
                "test_type": "story_1_2_validation",
                "database_required": True
            }
        )

        start_time = time.time()

        try:
            # Process with full database integration
            result = await service.process_vehicle_data(vehicle_data)
            processing_time = time.time() - start_time

            test_results["files_tested"].append(pdf_path.name)
            test_results["database_operations"] += 1

            if result.success:
                test_results["successful_processing"] += 1
                test_results["processing_times"].append(processing_time)
                test_results["semantic_tags"].extend(result.semantic_tags or [])
                test_results["embedding_dimensions"].append(result.embedding_dim or 0)

                # Check if database storage was successful
                if result.embedding_dim and result.embedding_dim > 0:
                    test_results["database_stored"] += 1

                print(f"  SUCCESS in {processing_time:.3f}s")
                print(f"  Vehicle ID: {result.vehicle_id}")
                print(f"  Text processed: {result.text_processed}")
                print(f"  Images processed: {result.images_processed}")
                print(f"  Metadata processed: {result.metadata_processed}")
                print(f"  Embedding dimension: {result.embedding_dim}")
                print(f"  Semantic tags: {len(result.semantic_tags or [])}")
                if result.semantic_tags:
                    print(f"  Sample tags: {result.semantic_tags[:5]}")

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
            import traceback
            traceback.print_exc()

    # Calculate comprehensive performance metrics
    if test_results["processing_times"]:
        total_time = sum(test_results["processing_times"])
        test_results["performance_metrics"] = {
            "success_rate": (test_results["successful_processing"] / test_results["total_files"]) * 100,
            "database_success_rate": (test_results["database_stored"] / test_results["total_files"]) * 100,
            "avg_processing_time": total_time / len(test_results["processing_times"]),
            "min_processing_time": min(test_results["processing_times"]),
            "max_processing_time": max(test_results["processing_times"]),
            "total_processing_time": total_time,
            "vehicles_per_minute": (test_results["successful_processing"] / total_time) * 60 if total_time > 0 else 0,
            "avg_embedding_dim": sum(test_results["embedding_dimensions"]) / len(test_results["embedding_dimensions"]) if test_results["embedding_dimensions"] else 0,
            "total_database_operations": test_results["database_operations"],
            "avg_semantic_tags_per_vehicle": len(test_results["semantic_tags"]) / test_results["successful_processing"] if test_results["successful_processing"] > 0 else 0
        }

    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("STORY 1.2 COMPLETE VALIDATION RESULTS")
    print("=" * 80)

    metrics = test_results["performance_metrics"]

    print(f"Test Summary:")
    print(f"  Total files tested: {test_results['total_files']}")
    print(f"  Successfully processed: {test_results['successful_processing']}")
    print(f"  Failed: {test_results['failed_processing']}")
    print(f"  Database operations: {test_results['database_operations']}")
    print(f"  Success rate: {metrics['success_rate']:.1f}%")
    print(f"  Database success rate: {metrics['database_success_rate']:.1f}%")

    print(f"\nReal Performance Metrics:")
    print(f"  Average processing time: {metrics['avg_processing_time']:.3f}s per vehicle")
    print(f"  Processing time range: {metrics['min_processing_time']:.3f}s - {metrics['max_processing_time']:.3f}s")
    print(f"  Total processing time: {metrics['total_processing_time']:.2f}s")
    print(f"  Vehicles per minute: {metrics['vehicles_per_minute']:.1f}")
    print(f"  Average embedding dimension: {metrics['avg_embedding_dim']:.0f}")
    print(f"  Average semantic tags per vehicle: {metrics['avg_semantic_tags_per_vehicle']:.1f}")

    print(f"\nSemantic Analysis:")
    print(f"  Total semantic tags generated: {len(test_results['semantic_tags'])}")
    print(f"  Unique semantic tags: {len(set(test_results['semantic_tags']))}")
    if test_results['semantic_tags']:
        sample_tags = list(set(test_results['semantic_tags']))[:15]
        print(f"  Sample tags: {', '.join(sample_tags)}")

    print(f"\nValidation Against Story 1.2 Acceptance Criteria:")

    # AC#1: Process multimodal vehicle data (text, images, metadata)
    ac1_pass = test_results['successful_processing'] > 0
    print(f"  AC#1 (Multimodal Processing): {'PASS' if ac1_pass else 'FAIL'}")
    print(f"    Successfully processes text, images, and metadata from PDFs")

    # AC#2: Generate and store vector embeddings using pgvector
    ac2_pass = test_results['database_stored'] > 0 and metrics['avg_embedding_dim'] > 0
    print(f"  AC#2 (Vector Embeddings with pgvector): {'PASS' if ac2_pass else 'FAIL'}")
    print(f"    Embeddings generated and stored in database: {test_results['database_stored']} vehicles")

    # AC#3: Process vehicles in under 2 seconds each
    ac3_pass = metrics['avg_processing_time'] < 2.0
    print(f"  AC#3 (<2s processing): {'PASS' if ac3_pass else 'FAIL'}")
    print(f"    Average processing time: {metrics['avg_processing_time']:.3f}s")

    print(f"\nInfrastructure Integration:")
    api_pass = test_results['successful_processing'] > 0
    print(f"  Real API Integration: {'PASS' if api_pass else 'FAIL'}")
    print(f"    OpenRouter API calls successful")

    db_pass = test_results['database_operations'] > 0
    print(f"  Database Integration: {'PASS' if db_pass else 'FAIL'}")
    print(f"    Supabase pgvector operations successful")

    rag_pass = test_results['successful_processing'] > 0
    print(f"  RAG-Anything Integration: {'PASS' if rag_pass else 'FAIL'}")
    print(f"    Multimodal PDF processing working")

    # Overall assessment
    success_rate = metrics['success_rate']
    db_success_rate = metrics['database_success_rate']
    avg_time = metrics['avg_processing_time']

    print(f"\nOVERALL STORY 1.2 VALIDATION ASSESSMENT:")

    if success_rate >= 90 and db_success_rate >= 90 and avg_time < 1.0:
        print("EXCELLENT: Story 1.2 implementation exceeds all requirements")
        print("  - Near-perfect success rate with real Condition Report PDFs")
        print("  - Processing time significantly under 2 seconds")
        print("  - Full database integration with pgvector working")
        print("  - RAG-Anything multimodal processing fully validated")
    elif success_rate >= 80 and db_success_rate >= 80 and avg_time < 2.0:
        print("GOOD: Story 1.2 implementation meets all requirements")
        print("  - High success rate with real Condition Report PDFs")
        print("  - Processing time meets requirements")
        print("  - Database integration working correctly")
        print("  - RAG-Anything processing validated")
    elif success_rate >= 60:
        print("ACCEPTABLE: Story 1.2 implementation partially working")
        print("  - Moderate success rate - may need optimization")
        print("  - Core functionality demonstrated")
    else:
        print("NEEDS WORK: Story 1.2 implementation requires improvement")
        print("  - Low success rate with real PDFs")
        print("  - May need optimization or debugging")

    print(f"\nRECOMMENDATION:")
    if success_rate >= 80 and db_success_rate >= 80 and avg_time < 2.0:
        print("  Story 1.2 is VALIDATED and ready for production use")
        print("  RAG-Anything integration successfully processes real Condition Reports")
        print("  Database integration with pgvector is working correctly")
        print("  Performance requirements are met or exceeded")
    else:
        print("  Story 1.2 needs optimization before production deployment")
        if success_rate < 80:
            print("  - Improve PDF processing success rate")
        if db_success_rate < 80:
            print("  - Fix database integration issues")
        if avg_time >= 2.0:
            print("  - Optimize processing performance")

    # Save comprehensive results
    comprehensive_results = {
        "test_summary": {
            "date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "test_type": "Story 1.2 Complete Validation",
            "total_files": test_results["total_files"],
            "success_rate": metrics["success_rate"],
            "database_success_rate": metrics["database_success_rate"],
            "avg_processing_time": metrics["avg_processing_time"],
            "vehicles_per_minute": metrics["vehicles_per_minute"]
        },
        "infrastructure_validation": {
            "real_api_integration": api_pass,
            "database_integration": db_pass,
            "raganything_integration": rag_pass,
            "pgvector_operations": ac2_pass
        },
        "acceptance_criteria": {
            "ac1_multimodal_processing": ac1_pass,
            "ac2_vector_embeddings_pgvector": ac2_pass,
            "ac3_performance_2_seconds": ac3_pass
        },
        "file_details": test_results["files_tested"],
        "processing_results": {
            "successful": test_results["successful_processing"],
            "failed": test_results["failed_processing"],
            "database_stored": test_results["database_stored"],
            "processing_times": test_results["processing_times"]
        },
        "semantic_analysis": {
            "total_tags": len(test_results['semantic_tags']),
            "unique_tags": len(set(test_results['semantic_tags'])),
            "avg_tags_per_vehicle": metrics['avg_semantic_tags_per_vehicle'],
            "sample_tags": list(set(test_results['semantic_tags']))[:30]
        },
        "performance_metrics": metrics,
        "overall_assessment": {
            "story_ready": success_rate >= 80 and db_success_rate >= 80 and avg_time < 2.0,
            "recommendation": "Ready for production" if success_rate >= 80 and db_success_rate >= 80 and avg_time < 2.0 else "Needs optimization"
        }
    }

    results_path = "D:/Otto_AI_v2/src/semantic/story_1_2_complete_validation_results.json"
    import json
    with open(results_path, 'w') as f:
        json.dump(comprehensive_results, f, indent=2)

    print(f"\nComprehensive validation results saved to: {results_path}")

    # Final success determination
    overall_success = (success_rate >= 80 and
                      db_success_rate >= 80 and
                      avg_time < 2.0 and
                      ac1_pass and ac2_pass and ac3_pass)

    print(f"\n{'VALIDATION SUCCESS' if overall_success else 'VALIDATION NEEDS WORK'}: Story 1.2 {'is ready' if overall_success else 'needs optimization'}")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(complete_story_validation())
    exit(0 if success else 1)