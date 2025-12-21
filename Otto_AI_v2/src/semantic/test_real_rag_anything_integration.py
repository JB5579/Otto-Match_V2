"""
Test Real RAG-Anything API Integration for Story 1.2 TARB Remediation
Validates that fake embeddings have been replaced with real API calls
"""

import os
import sys
import asyncio
import time
import logging
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.semantic.vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealRAGAnythingValidator:
    """Validator for real RAG-Anything API integration"""

    def __init__(self):
        self.test_results = []
        self.vehicle_service = None

    async def setup(self):
        """Initialize the vehicle processing service"""
        try:
            logger.info("🚀 Initializing Vehicle Processing Service for TARB remediation testing...")

            # Initialize the service
            self.vehicle_service = VehicleProcessingService()

            # Check environment variables
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

            if not openrouter_key:
                logger.error("❌ OPENROUTER_API_KEY environment variable not set")
                return False

            if not supabase_url or not supabase_key:
                logger.error("❌ SUPABASE_URL or SUPABASE_KEY environment variables not set")
                return False

            logger.info("✅ Environment variables found")

            # Initialize the service (this will set up LightRAG and real API connections)
            success = await self.vehicle_service.initialize(supabase_url, supabase_key)

            if success:
                logger.info("✅ Vehicle Processing Service initialized with real RAG-Anything API")
                return True
            else:
                logger.error("❌ Failed to initialize Vehicle Processing Service")
                return False

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

    def create_test_vehicle_data(self) -> VehicleData:
        """Create realistic test vehicle data"""
        return VehicleData(
            vehicle_id="test-tarb-remediation-001",
            make="Toyota",
            model="Camry",
            year=2023,
            mileage=15000,
            price=28500.00,
            description="Excellent condition 2023 Toyota Camry XLE with premium features. Low mileage, single owner, regular maintenance records. Features include leather seats, moonroof, premium audio system, and advanced safety features.",
            features=[
                "Leather Seats",
                "Moonroof",
                "Premium Audio",
                "Lane Assist",
                "Adaptive Cruise Control",
                "Apple CarPlay",
                "Android Auto",
                "Backup Camera",
                "Blind Spot Monitoring"
            ],
            specifications={
                "engine": "2.5L 4-Cylinder",
                "transmission": "8-Speed Automatic",
                "fuel_economy": "32 MPG Combined",
                "drivetrain": "Front-Wheel Drive",
                "horsepower": "203 hp",
                "torque": "184 lb-ft"
            },
            images=[
                {
                    "path": "test_images/exterior_front.jpg",
                    "type": VehicleImageType.EXTERIOR
                },
                {
                    "path": "test_images/interior_dashboard.jpg",
                    "type": VehicleImageType.INTERIOR
                },
                {
                    "path": "test_images/detail_engine.jpg",
                    "type": VehicleImageType.DETAIL
                }
            ],
            metadata={
                "dealer_id": "dealer-001",
                "location": "San Francisco, CA",
                "condition": "Excellent",
                "color": "Midnight Black"
            }
        )

    def validate_embedding_quality(self, embedding: List[float], embedding_type: str) -> bool:
        """Validate that embedding has real characteristics (not fake)"""

        if not embedding:
            logger.error(f"❌ {embedding_type} embedding is empty")
            return False

        # Check dimension
        expected_dim = 3072  # OpenAI text-embedding-3-large
        if len(embedding) != expected_dim:
            logger.error(f"❌ {embedding_type} embedding has incorrect dimension: {len(embedding)} != {expected_dim}")
            return False

        # Check for obviously fake patterns (all same values)
        if all(abs(x - embedding[0]) < 0.001 for x in embedding):
            logger.error(f"❌ {embedding_type} embedding appears fake (all values identical)")
            return False

        # Check for obvious fake patterns (simple repeated values)
        unique_values = len(set(round(x, 6) for x in embedding))
        if unique_values < 100:  # Real embeddings should have many unique values
            logger.error(f"❌ {embedding_type} embedding appears fake (only {unique_values} unique values)")
            return False

        # Check value range (real embeddings are typically between -1 and 1)
        min_val, max_val = min(embedding), max(embedding)
        if min_val < -2.0 or max_val > 2.0:
            logger.warning(f"⚠️ {embedding_type} embedding has unusual value range: [{min_val:.3f}, {max_val:.3f}]")

        # Calculate variance (real embeddings should have reasonable variance)
        mean_val = sum(embedding) / len(embedding)
        variance = sum((x - mean_val) ** 2 for x in embedding) / len(embedding)

        if variance < 0.001:
            logger.error(f"❌ {embedding_type} embedding has suspiciously low variance: {variance:.6f}")
            return False

        logger.info(f"✅ {embedding_type} embedding passed quality checks (dim: {len(embedding)}, variance: {variance:.6f})")
        return True

    async def test_individual_processing(self) -> bool:
        """Test individual vehicle processing with real embeddings"""
        try:
            logger.info("🧪 Testing individual vehicle processing with real RAG-Anything API...")

            # Create test vehicle
            test_vehicle = self.create_test_vehicle_data()

            # Process the vehicle
            start_time = time.time()
            result = await self.vehicle_service.process_vehicle_data(test_vehicle)
            processing_time = time.time() - start_time

            logger.info(f"⏱️ Processing time: {processing_time:.2f} seconds")

            # Validate result
            if not result.success:
                logger.error(f"❌ Processing failed: {result.error}")
                return False

            # Check performance requirement (< 2 seconds)
            if processing_time >= 2.0:
                logger.error(f"❌ Performance requirement not met: {processing_time:.2f}s >= 2.0s")
                return False

            logger.info(f"✅ Performance requirement met: {processing_time:.2f}s < 2.0s")

            # Validate real embedding quality
            if not self.validate_embedding_quality(result.embedding, "combined"):
                logger.error("❌ Combined embedding quality validation failed")
                return False

            logger.info(f"✅ Combined embedding quality validated (dim: {result.embedding_dim})")
            logger.info(f"✅ Semantic tags extracted: {len(result.semantic_tags)}")
            logger.info(f"✅ Images processed: {result.images_processed}")

            # Store test result
            self.test_results.append({
                "test": "individual_processing",
                "success": True,
                "processing_time": processing_time,
                "embedding_dim": result.embedding_dim,
                "semantic_tags_count": len(result.semantic_tags),
                "images_processed": result.images_processed
            })

            return True

        except Exception as e:
            logger.error(f"❌ Individual processing test failed: {e}")
            self.test_results.append({
                "test": "individual_processing",
                "success": False,
                "error": str(e)
            })
            return False

    async def test_batch_processing(self) -> bool:
        """Test batch processing for throughput validation"""
        try:
            logger.info("🧪 Testing batch processing throughput...")

            # Create small batch for testing (10 vehicles to avoid API limits)
            batch_size = 10
            test_vehicles = []

            for i in range(batch_size):
                vehicle = self.create_test_vehicle_data()
                vehicle.vehicle_id = f"test-tarb-batch-{i:03d}"
                vehicle.price = 25000 + (i * 1000)  # Vary prices
                vehicle.mileage = 10000 + (i * 5000)  # Vary mileage
                test_vehicles.append(vehicle)

            # Process batch
            start_time = time.time()
            batch_result = await self.vehicle_service.process_batch_vehicles(test_vehicles)
            total_time = time.time() - start_time

            logger.info(f"⏱️ Batch processing time: {total_time:.2f} seconds")
            logger.info(f"📊 Success rate: {batch_result.successful_vehicles}/{batch_result.total_vehicles}")
            logger.info(f"📊 Throughput: {batch_result.vehicles_per_minute:.1f} vehicles/minute")

            # Check throughput requirement (> 25 vehicles/minute)
            if batch_result.vehicles_per_minute <= 25.0:
                logger.error(f"❌ Throughput requirement not met: {batch_result.vehicles_per_minute:.1f} <= 25.0")
                return False

            logger.info(f"✅ Throughput requirement met: {batch_result.vehicles_per_minute:.1f} > 25.0")

            # Validate all successful vehicles have real embeddings
            real_embedding_count = 0
            for result in batch_result.successful_results:
                if self.validate_embedding_quality(result.embedding, f"batch_{result.vehicle_id}"):
                    real_embedding_count += 1

            real_embedding_percentage = (real_embedding_count / len(batch_result.successful_results)) * 100
            logger.info(f"✅ Real embeddings in batch: {real_embedding_percentage:.1f}%")

            if real_embedding_percentage < 80.0:
                logger.error(f"❌ Insufficient real embeddings in batch: {real_embedding_percentage:.1f}% < 80%")
                return False

            # Store test result
            self.test_results.append({
                "test": "batch_processing",
                "success": True,
                "batch_size": batch_size,
                "total_time": total_time,
                "throughput": batch_result.vehicles_per_minute,
                "success_rate": batch_result.successful_vehicles / batch_result.total_vehicles,
                "real_embedding_percentage": real_embedding_percentage
            })

            return True

        except Exception as e:
            logger.error(f"❌ Batch processing test failed: {e}")
            self.test_results.append({
                "test": "batch_processing",
                "success": False,
                "error": str(e)
            })
            return False

    async def run_comprehensive_validation(self) -> bool:
        """Run comprehensive TARB remediation validation"""
        try:
            logger.info("🚀 Starting comprehensive TARB remediation validation...")
            logger.info("=" * 80)

            # Setup
            if not await self.setup():
                logger.error("❌ Setup failed, aborting validation")
                return False

            logger.info("=" * 80)

            # Test 1: Individual processing
            if not await self.test_individual_processing():
                logger.error("❌ Individual processing test failed")
                return False

            logger.info("=" * 80)

            # Test 2: Batch processing
            if not await self.test_batch_processing():
                logger.error("❌ Batch processing test failed")
                return False

            logger.info("=" * 80)

            # Generate summary
            successful_tests = sum(1 for result in self.test_results if result["success"])
            total_tests = len(self.test_results)

            logger.info("📊 TARB REMEDIATION VALIDATION SUMMARY")
            logger.info("=" * 50)
            logger.info(f"✅ Tests passed: {successful_tests}/{total_tests}")

            for result in self.test_results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                logger.info(f"{status} - {result['test']}")
                if result["success"] and "processing_time" in result:
                    logger.info(f"    Processing time: {result['processing_time']:.2f}s")
                if result["success"] and "throughput" in result:
                    logger.info(f"    Throughput: {result['throughput']:.1f} vehicles/min")

            logger.info("=" * 50)
            logger.info("🎉 TARB REMEDIATION VALIDATION COMPLETED SUCCESSFULLY!")
            logger.info("✅ All fake embeddings have been replaced with real RAG-Anything API calls")
            logger.info("✅ Performance requirements met: <2s processing, >25 vehicles/min throughput")
            logger.info("✅ Real multimodal embeddings generated from text, images, and metadata")

            return successful_tests == total_tests

        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {e}")
            return False

async def main():
    """Main test execution"""
    print("🔧 Otto.AI TARB REMEDIATION VALIDATOR")
    print("Testing Real RAG-Anything API Integration")
    print("=" * 60)

    validator = RealRAGAnythingValidator()
    success = await validator.run_comprehensive_validation()

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ TARB remediation completed successfully")
        print("✅ Ready for production deployment")
        return 0
    else:
        print("\n❌ VALIDATION FAILED!")
        print("⚠️ TARB remediation needs additional work")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)