"""
Otto.AI Comprehensive PDF Testing
Tests the complete PDF ingestion pipeline with all sample condition reports

Usage:
    python test_all_sample_pdfs.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.pdf_ingestion_service import get_pdf_ingestion_service, VehicleListingArtifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensivePDFTester:
    """Test the PDF ingestion pipeline with all sample condition reports"""

    def __init__(self):
        self.pdf_service = None
        self.test_results = {}
        self.sample_pdfs_dir = Path(__file__).parent.parent.parent / 'docs' / 'Sample_Vehicle_Condition_Reports'

    async def setup(self):
        """Initialize services and environment"""
        logger.info("🚀 Setting up comprehensive PDF testing...")

        try:
            # Check required environment variables
            required_vars = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']

            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
                logger.warning("Tests will simulate processing without actual API calls")
                return False

            # Initialize service
            self.pdf_service = await get_pdf_ingestion_service()
            logger.info("✅ PDF ingestion service initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            return False

    def get_sample_pdfs(self) -> list:
        """Get all sample PDF files"""
        if not self.sample_pdfs_dir.exists():
            logger.error(f"❌ Sample PDFs directory not found: {self.sample_pdfs_dir}")
            return []

        pdf_files = list(self.sample_pdfs_dir.glob("*.pdf"))
        logger.info(f"📄 Found {len(pdf_files)} sample PDFs:")
        for pdf in pdf_files:
            logger.info(f"   • {pdf.name}")

        return sorted(pdf_files)

    async def process_single_pdf(self, pdf_path: Path) -> dict:
        """Process a single PDF file"""
        logger.info(f"📄 Processing: {pdf_path.name}")

        try:
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            file_size = len(pdf_bytes)
            logger.info(f"   📊 Size: {file_size:,} bytes")

            # Process PDF
            start_time = datetime.utcnow()

            if self.pdf_service:
                # Real processing with API calls
                artifact = await self.pdf_service.process_condition_report(
                    pdf_bytes=pdf_bytes,
                    filename=pdf_path.name
                )
            else:
                # Simulate processing for testing without API keys
                artifact = self._simulate_processing(pdf_bytes, pdf_path.name)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Extract key information
            result = {
                'success': True,
                'filename': pdf_path.name,
                'file_size_bytes': file_size,
                'processing_time': processing_time,
                'vehicle': {
                    'vin': artifact.vehicle.vin,
                    'year': artifact.vehicle.year,
                    'make': artifact.vehicle.make,
                    'model': artifact.vehicle.model,
                    'trim': artifact.vehicle.trim,
                    'odometer': artifact.vehicle.odometer,
                    'engine': artifact.vehicle.engine,
                    'exterior_color': artifact.vehicle.exterior_color,
                    'interior_color': artifact.vehicle.interior_color
                },
                'condition': {
                    'score': artifact.condition.score,
                    'grade': artifact.condition.grade,
                    'issues_count': len(artifact.condition.issues)
                },
                'images': {
                    'total_count': len(artifact.images),
                    'categories': {cat: len([img for img in artifact.images if img.category == cat])
                                 for cat in set(img.category for img in artifact.images)},
                    'avg_quality_score': sum(img.quality_score for img in artifact.images) / len(artifact.images) if artifact.images else 0
                },
                'seller': {
                    'name': artifact.seller.name,
                    'type': artifact.seller.type
                }
            }

            logger.info(f"   ✅ SUCCESS: {artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}")
            logger.info(f"   📊 VIN: {artifact.vehicle.vin}")
            logger.info(f"   🖼️ Images: {len(artifact.images)}")
            logger.info(f"   ⏱️ Time: {processing_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"   ❌ FAILED: {str(e)}")
            return {
                'success': False,
                'filename': pdf_path.name,
                'error': str(e)
            }

    def _simulate_processing(self, pdf_bytes: bytes, filename: str) -> VehicleListingArtifact:
        """Simulate PDF processing when API keys are not available"""
        import hashlib
        from src.services.pdf_ingestion_service import (
            VehicleInfo, ConditionData, SellerInfo, EnrichedImage
        )

        # Generate mock data based on filename
        hash_prefix = hashlib.md5(pdf_bytes[:1024]).hexdigest()[:8]
        vin = f"SIMU{hash_prefix.upper()}123456789"

        # Extract vehicle info from filename
        vehicle_info = self._extract_vehicle_from_filename(filename)

        return VehicleListingArtifact(
            vehicle=VehicleInfo(
                vin=vin,
                **vehicle_info
            ),
            condition=ConditionData(
                score=4.2,
                grade="Average",
                issues={}
            ),
            images=[
                EnrichedImage(
                    description=f"Simulated vehicle image for {vehicle_info.get('make', 'Unknown')} {vehicle_info.get('model', 'Unknown')}",
                    category="hero",
                    quality_score=8,
                    vehicle_angle="front",
                    suggested_alt=f"Front view of {vehicle_info.get('make', 'Unknown')} {vehicle_info.get('model', 'Unknown')}",
                    visible_damage=[],
                    image_bytes=b"simulated_image_bytes",
                    width=800,
                    height=600,
                    format="jpeg",
                    page_number=1
                )
            ],
            seller=SellerInfo(
                name="Simulated Dealer",
                type="dealer"
            ),
            processing_metadata={"simulated": True}
        )

    def _extract_vehicle_from_filename(self, filename: str) -> dict:
        """Extract vehicle information from filename"""
        # Remove extension and clean up
        clean_name = filename.replace('.pdf', '').replace('(1)', '').strip()

        # Common patterns in filenames
        vehicle_patterns = {
            'lexus': {'make': 'Lexus'},
            'bmw': {'make': 'BMW'},
            'gmc': {'make': 'GMC'},
            'chevy': {'make': 'Chevrolet'},
            'mercedes': {'make': 'Mercedes-Benz'},
            'cherokee': {'model': 'Cherokee', 'make': 'Jeep'},
            'canyon': {'model': 'Canyon', 'make': 'GMC'},
            'equinox': {'model': 'Equinox', 'make': 'Chevrolet'},
            'f-250': {'model': 'F-250', 'make': 'Ford'},
            'es350': {'model': 'ES350', 'make': 'Lexus'},
            'i3': {'model': 'i3', 'make': 'BMW'},
        }

        # Extract year
        year = None
        for word in clean_name.split():
            if word.isdigit() and len(word) == 4:
                year = int(word)
                break

        # Determine make and model
        make = "Unknown"
        model = "Unknown"

        for pattern_key, pattern_data in vehicle_patterns.items():
            if pattern_key.lower() in clean_name.lower():
                make = pattern_data.get('make', pattern_key.title())
                if 'model' in pattern_data:
                    model = pattern_data['model']
                break

        # Default values
        return {
            'year': year or 2020,
            'make': make,
            'model': model,
            'trim': None,
            'odometer': 50000,
            'engine': "V6 3.0L",
            'drivetrain': "AWD",
            'transmission': "Automatic",
            'exterior_color': "Black",
            'interior_color': "Black"
        }

    async def run_comprehensive_test(self):
        """Test all sample PDFs"""
        logger.info("🎯 Starting comprehensive PDF testing...")

        pdf_files = self.get_sample_pdfs()
        if not pdf_files:
            logger.error("❌ No sample PDFs found")
            return

        results = []

        # Process each PDF
        for pdf_path in pdf_files:
            result = await self.process_single_pdf(pdf_path)
            results.append(result)

        # Analyze results
        await self.analyze_results(results)

    async def analyze_results(self, results: list):
        """Analyze and report on all test results"""
        logger.info("📊 Analyzing test results...")

        # Count successes and failures
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]

        logger.info(f"✅ Successful: {len(successful)}/{len(results)}")
        logger.info(f"❌ Failed: {len(failed)}/{len(results)}")

        # Analyze vehicle data
        if successful:
            makes = {}
            years = []
            conditions = []
            image_counts = []

            for result in successful:
                vehicle = result['vehicle']
                makes[vehicle['make']] = makes.get(vehicle['make'], 0) + 1
                years.append(vehicle['year'])
                conditions.append(result['condition']['score'])
                image_counts.append(result['images']['total_count'])

            logger.info("\n📈 Vehicle Statistics:")
            for make, count in sorted(makes.items()):
                logger.info(f"   • {make}: {count} vehicles")

            if years:
                logger.info(f"\n📅 Year Range: {min(years)} - {max(years)}")
                logger.info(f"   Average Year: {sum(years)/len(years):.1f}")

            if conditions:
                logger.info(f"\n📊 Condition Scores:")
                logger.info(f"   • Average: {sum(conditions)/len(conditions):.2f}")
                logger.info(f"   • Range: {min(conditions):.2f} - {max(conditions):.2f}")

            if image_counts:
                logger.info(f"\n🖼️ Image Statistics:")
                logger.info(f"   • Average per vehicle: {sum(image_counts)/len(image_counts):.1f}")
                logger.info(f"   • Range: {min(image_counts)} - {max(image_counts)}")

        # Log failures
        if failed:
            logger.info("\n❌ Failed Processing:")
            for result in failed:
                logger.info(f"   • {result['filename']}: {result.get('error', 'Unknown error')}")

        # Save detailed results
        self.save_results(results, successful, failed)

    def save_results(self, results: list, successful: list, failed: list):
        """Save detailed test results"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        results_file = Path(__file__).parent / f"pdf_test_results_{timestamp}.json"

        test_report = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_files': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': f"{len(successful)/len(results)*100:.1f}%"
            },
            'detailed_results': results,
            'successful_vehicles': successful,
            'failed_processing': failed
        }

        with open(results_file, 'w') as f:
            json.dump(test_report, f, indent=2, default=str)

        logger.info(f"\n📄 Detailed results saved: {results_file}")

    async def cleanup(self):
        """Clean up resources"""
        if self.pdf_service:
            await self.pdf_service.close()
        logger.info("🧹 Cleanup completed")


async def main():
    """Main test function"""
    tester = ComprehensivePDFTester()

    try:
        # Setup
        if not await tester.setup():
            logger.warning("⚠️ Running in simulation mode without API keys")

        # Run comprehensive test
        await tester.run_comprehensive_test()

        logger.info("🎉 Comprehensive PDF testing completed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())