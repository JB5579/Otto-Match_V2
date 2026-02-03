"""
Real Data Testing Framework for Story 1.2
Tests vehicle processing with actual Condition Report PDFs and live APIs
"""

import os
import sys
import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType
from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG
import PyPDF2
from PIL import Image
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RealTestResults:
    """Results of real data testing"""
    test_name: str
    total_files: int
    processed_files: int
    failed_files: List[str]
    processing_times: List[float]
    api_calls_made: int
    actual_cost_estimate: float  # USD
    embeddings_generated: int
    images_processed: int
    semantic_tags_extracted: List[str]
    database_operations: int
    performance_metrics: Dict[str, Any]

    @property
    def success_rate(self) -> float:
        return (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0

    @property
    def avg_processing_time(self) -> float:
        return sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

class RealDataTester:
    """
    Tests vehicle processing with real Condition Report PDFs and live APIs
    """

    def __init__(self):
        self.processing_service = None
        self.condition_reports_dir = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports")
        self.test_results = []
        self.api_call_count = 0

        # Cost estimates (USD per API call)
        self.cost_per_rag_call = 0.001  # Approximate cost per RAG-Anything call
        self.cost_per_embedding = 0.0001  # Approximate cost per embedding generation

    async def initialize(self):
        """Initialize the processing service with real credentials"""
        try:
            logger.info("🚀 Initializing Real Data Testing Framework...")

            # Initialize processing service with real configuration
            self.processing_service = VehicleProcessingService()

            # Use real API keys from environment
            self.processing_service.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
            self.processing_service.embedding_dim = 3072

            # Initialize with real Supabase credentials
            supabase_url = os.getenv('SUPABASE_URL')
            if not supabase_url:
                raise ValueError("SUPABASE_URL not found in environment")

            logger.info(f"📊 Initializing with Supabase: {supabase_url}")

            # Initialize the service (this will connect to real database)
            success = await self.processing_service.initialize(
                supabase_url=supabase_url,
                supabase_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            )

            if success:
                logger.info("✅ Processing service initialized successfully")
            else:
                logger.error("❌ Failed to initialize processing service")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract structured data from Condition Report PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""

                for page in pdf_reader.pages:
                    text_content += page.extract_text()

            # Extract vehicle information from text
            vehicle_data = self._parse_condition_report_text(text_content, pdf_path.name)

            logger.info(f"📄 Extracted data from {pdf_path.name}")
            return vehicle_data

        except Exception as e:
            logger.error(f"❌ Failed to extract from {pdf_path.name}: {e}")
            return None

    def _parse_condition_report_text(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse Condition Report text to extract vehicle information"""

        # Extract year from filename or text
        year = self._extract_year(text, filename)

        # Extract make and model
        make, model = self._extract_make_model(text)

        # Extract other information
        mileage = self._extract_mileage(text)
        price = self._extract_price(text)
        vin = self._extract_vin(text)

        # Extract features and specifications
        features = self._extract_features(text)
        specifications = self._extract_specifications(text)

        return {
            "vehicle_id": f"real-test-{filename.replace('.pdf', '').replace(' ', '-').lower()}",
            "make": make or "Unknown",
            "model": model or "Unknown",
            "year": year or 2020,
            "mileage": mileage,
            "price": price,
            "vin": vin,
            "description": text[:500] + "..." if len(text) > 500 else text,
            "features": features,
            "specifications": specifications,
            "source_file": str(filename),
            "raw_text": text
        }

    def _extract_year(self, text: str, filename: str) -> Optional[int]:
        """Extract vehicle year from text or filename"""
        import re

        # Try filename first
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())

        # Try text
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            return int(year_match.group())

        return None

    def _extract_make_model(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract vehicle make and model from text"""
        # Common vehicle makes
        makes = ["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes", "Lexus",
                "GM", "Buick", "GMC", "Jeep", "Chrysler", "Dodge", "Ram"]

        for make in makes:
            if make.lower() in text.lower():
                # Simple model extraction - look for make followed by model
                make_pattern = re.compile(f"{make}\\s+([A-Za-z0-9\\-]+)", re.IGNORECASE)
                match = make_pattern.search(text)
                if match:
                    return make, match.group(1)
                return make, None

        return None, None

    def _extract_mileage(self, text: str) -> Optional[int]:
        """Extract mileage from text"""
        import re

        # Look for mileage patterns
        mileage_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:miles|mi|odometer)', text, re.IGNORECASE)
        if mileage_match:
            return int(mileage_match.group(1).replace(',', ''))

        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text"""
        import re

        # Look for price patterns
        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
        if price_match:
            return float(price_match.group(1).replace(',', ''))

        return None

    def _extract_vin(self, text: str) -> Optional[str]:
        """Extract VIN from text"""
        import re

        # VIN pattern (17 characters)
        vin_match = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\b', text)
        if vin_match:
            return vin_match.group(1)

        return None

    def _extract_features(self, text: str) -> List[str]:
        """Extract vehicle features from text"""
        features = []

        # Common features to look for
        feature_keywords = [
            "air conditioning", "cruise control", "power windows", "power locks",
            "leather seats", "sunroof", "navigation", "backup camera",
            "bluetooth", "alloy wheels", "remote start", "heated seats"
        ]

        text_lower = text.lower()
        for feature in feature_keywords:
            if feature in text_lower:
                features.append(feature.title())

        return features[:10]  # Limit to 10 features

    def _extract_specifications(self, text: str) -> Dict[str, Any]:
        """Extract vehicle specifications from text"""
        specs = {}

        # Engine
        engine_match = re.search(r'(\d\.\d+[L]\s*\d+\s*-?Cylinder)', text, re.IGNORECASE)
        if engine_match:
            specs["engine"] = engine_match.group(1)

        # Transmission
        if "automatic" in text.lower():
            specs["transmission"] = "Automatic"
        elif "manual" in text.lower():
            specs["transmission"] = "Manual"

        # Drive type
        if "awd" in text.lower() or "all wheel drive" in text.lower():
            specs["drivetrain"] = "AWD"
        elif "4wd" in text.lower() or "four wheel drive" in text.lower():
            specs["drivetrain"] = "4WD"
        elif "fwd" in text.lower() or "front wheel drive" in text.lower():
            specs["drivetrain"] = "FWD"

        return specs

    async def process_real_condition_report(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single real Condition Report with live APIs"""

        start_time = time.time()

        try:
            logger.info(f"🔄 Processing: {pdf_path.name}")

            # Extract data from PDF
            extracted_data = self.extract_text_from_pdf(pdf_path)
            if not extracted_data:
                return {"success": False, "error": "Failed to extract PDF data"}

            # Create VehicleData object
            vehicle_data = VehicleData(
                vehicle_id=extracted_data["vehicle_id"],
                make=extracted_data["make"],
                model=extracted_data["model"],
                year=extracted_data["year"],
                mileage=extracted_data["mileage"],
                price=extracted_data["price"],
                description=extracted_data["description"],
                features=extracted_data["features"],
                specifications=extracted_data["specifications"],
                images=[],  # No images in PDFs initially
                metadata={
                    "source": "condition_report_pdf",
                    "source_file": extracted_data["source_file"],
                    "vin": extracted_data["vin"]
                }
            )

            # Process with real APIs
            result = await self.processing_service.process_vehicle_data(vehicle_data)

            processing_time = time.time() - start_time

            # Track API usage
            self.api_call_count += 1  # Estimate: 1 RAG-Anything call per vehicle

            return {
                "success": result.success,
                "processing_time": processing_time,
                "vehicle_id": result.vehicle_id,
                "embedding_dim": result.embedding_dim,
                "semantic_tags": result.semantic_tags,
                "text_processed": result.text_processed,
                "images_processed": result.images_processed,
                "metadata_processed": result.metadata_processed,
                "error": result.error,
                "extracted_make": extracted_data["make"],
                "extracted_model": extracted_data["model"],
                "extracted_year": extracted_data["year"]
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
            return {
                "success": False,
                "processing_time": processing_time,
                "error": str(e)
            }

    async def run_real_data_test(self, max_files: int = 5) -> RealTestResults:
        """Run real data test with Condition Report PDFs"""

        logger.info(f"🧪 Starting Real Data Test with max {max_files} files...")

        # Find PDF files
        pdf_files = list(self.condition_reports_dir.glob("*.pdf"))
        pdf_files = pdf_files[:max_files]  # Limit to max_files

        if not pdf_files:
            logger.error("❌ No PDF files found in condition reports directory")
            return None

        logger.info(f"📁 Found {len(pdf_files)} PDF files to process")

        test_results = RealTestResults(
            test_name="Real Condition Report Processing",
            total_files=len(pdf_files),
            processed_files=0,
            failed_files=[],
            processing_times=[],
            api_calls_made=0,
            actual_cost_estimate=0.0,
            embeddings_generated=0,
            images_processed=0,
            semantic_tags_extracted=[],
            database_operations=0,
            performance_metrics={}
        )

        # Process each file
        for i, pdf_path in enumerate(pdf_files):
            logger.info(f"\n📊 Processing file {i+1}/{len(pdf_files)}: {pdf_path.name}")

            result = await self.process_real_condition_report(pdf_path)

            if result["success"]:
                test_results.processed_files += 1
                test_results.processing_times.append(result["processing_time"])
                test_results.embeddings_generated += 1
                test_results.images_processed += result.get("images_processed", 0)
                test_results.semantic_tags_extracted.extend(result.get("semantic_tags", []))

                logger.info(f"✅ Success: {result['vehicle_id']} ({result['processing_time']:.3f}s)")
                logger.info(f"   Make/Model: {result.get('extracted_make', 'Unknown')} {result.get('extracted_model', 'Unknown')}")
                logger.info(f"   Tags: {result.get('semantic_tags', [])}")
            else:
                test_results.failed_files.append(pdf_path.name)
                logger.error(f"❌ Failed: {result.get('error', 'Unknown error')}")

        # Calculate final metrics
        test_results.api_calls_made = self.api_call_count
        test_results.actual_cost_estimate = (
            self.api_call_count * self.cost_per_rag_call +
            test_results.embeddings_generated * self.cost_per_embedding
        )

        test_results.performance_metrics = {
            "success_rate": test_results.success_rate,
            "avg_processing_time": test_results.avg_processing_time,
            "total_processing_time": sum(test_results.processing_times),
            "vehicles_per_minute": (test_results.processed_files / sum(test_results.processing_times)) * 60 if test_results.processing_times else 0,
            "cost_per_vehicle": test_results.actual_cost_estimate / test_results.processed_files if test_results.processed_files > 0 else 0
        }

        return test_results

    def generate_test_report(self, results: RealTestResults) -> str:
        """Generate comprehensive test report"""

        report = f"""
# Story 1.2 Real Data Testing Report
**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Test Type**: Live API Testing with Real Condition Report PDFs

## Test Summary
- **Files Tested**: {results.total_files}
- **Successfully Processed**: {results.processed_files}
- **Failed**: {len(results.failed_files)}
- **Success Rate**: {results.success_rate:.1f}%

## Performance Metrics (Real Data)
- **Average Processing Time**: {results.avg_processing_time:.3f}s per vehicle
- **Vehicles Per Minute**: {results.performance_metrics.get('vehicles_per_minute', 0):.1f}
- **Total Processing Time**: {results.performance_metrics.get('total_processing_time', 0):.2f}s

## API Usage & Costs
- **API Calls Made**: {results.api_calls_made}
- **Estimated Cost**: ${results.actual_cost_estimate:.4f}
- **Cost Per Vehicle**: ${results.performance_metrics.get('cost_per_vehicle', 0):.6f}

## Processing Results
- **Embeddings Generated**: {results.embeddings_generated}
- **Images Processed**: {results.images_processed}
- **Unique Semantic Tags**: {len(set(results.semantic_tags_extracted))}
- **Database Operations**: {results.database_operations}

## Validation Against Requirements
- **AC#1 (Multimodal Processing)**: {'✅ PASS' if results.processed_files > 0 else '❌ FAIL'}
- **AC#3 (<2s processing)**: {'✅ PASS' if results.avg_processing_time < 2.0 else '❌ FAIL'}
- **Real API Integration**: {'✅ PASS' if results.api_calls_made > 0 else '❌ FAIL'}

## Failed Files
"""

        if results.failed_files:
            for failed_file in results.failed_files:
                report += f"- {failed_file}\n"
        else:
            report += "None\n"

        report += f"""
## Semantic Tags Extracted (Sample)
{', '.join(list(set(results.semantic_tags_extracted))[:20])}

## Recommendations
"""

        if results.success_rate >= 80:
            report += "✅ **EXCELLENT**: Real data processing working well with high success rate\n"
        elif results.success_rate >= 60:
            report += "⚠️ **GOOD**: Real data processing functional but needs optimization\n"
        else:
            report += "❌ **NEEDS WORK**: Real data processing has significant issues\n"

        if results.avg_processing_time < 2.0:
            report += "✅ Performance meets requirements with real data\n"
        else:
            report += "❌ Performance does not meet requirements with real data\n"

        return report

async def main():
    """Run real data testing"""
    print("🚀 Story 1.2 Real Data Testing")
    print("=" * 60)

    tester = RealDataTester()

    # Initialize with real credentials
    if not await tester.initialize():
        print("❌ Failed to initialize testing framework")
        return False

    # Run the test with 5 files (adjust as needed)
    results = await tester.run_real_data_test(max_files=5)

    if results:
        # Generate and display report
        report = tester.generate_test_report(results)
        print(report)

        # Save report to file
        report_path = "D:/Otto_AI_v2/src/semantic/real_data_test_report.md"
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_path}")

        # Determine overall success
        success = results.success_rate >= 80 and results.avg_processing_time < 2.0
        print(f"\n{'✅ SUCCESS' if success else '❌ NEEDS WORK'}: Real data testing {'passed' if success else 'failed'}")

        return success
    else:
        print("❌ Test failed to run")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)