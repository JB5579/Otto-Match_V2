"""
Analyze the actual content of the Lexus ES350 PDF
Compare real content to our extraction results
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
import re

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicle_processing_service import VehicleProcessingService, VehicleData, VehicleImageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_pdf_text_directly(pdf_path):
    """Extract text from PDF directly using PyPDF2"""

    print(f"Direct PDF Text Extraction: {pdf_path.name}")
    print("=" * 60)

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""

            print(f"PDF Pages: {len(pdf_reader.pages)}")
            print(f"PDF Info: {pdf_reader.metadata}")

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text_content += f"\n--- PAGE {page_num + 1} ---\n"
                text_content += page_text
                print(f"Page {page_num + 1} characters: {len(page_text)}")
                if page_text.strip():
                    print(f"Page {page_num + 1} preview: {page_text[:200]}...")

        return text_content

    except Exception as e:
        print(f"ERROR extracting PDF text: {e}")
        return None

def analyze_text_content(text):
    """Analyze extracted text for vehicle information"""

    print(f"\nText Content Analysis")
    print("=" * 40)

    if not text:
        print("No text content to analyze")
        return {}

    extracted_info = {}

    # Look for VIN patterns (17 characters, alphanumeric)
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    vin_matches = re.findall(vin_pattern, text)
    if vin_matches:
        extracted_info['vin'] = vin_matches
        print(f"VINs found: {vin_matches}")

    # Look for make
    makes = ["lexus", "toyota", "bmw", "mercedes", "gmc", "ford", "chevrolet", "honda", "jeep"]
    for make in makes:
        if make in text.lower():
            extracted_info['make'] = make.title()
            print(f"Make found: {make.title()}")
            break

    # Look for model
    lexus_models = ["es350", "es 350", "rx350", "rx 350", "gx460", "nx200t", "rx450h", "es250", "es300h", "es330"]
    for model in lexus_models:
        if model.replace(" ", "").lower() in text.lower():
            extracted_info['model'] = model.upper().replace(" ", "")
            print(f"Model found: {model.upper()}")
            break

    # Look for year (2000-2030 range)
    year_pattern = r'\b(20[0-2][0-9])\b'
    year_matches = re.findall(year_pattern, text)
    if year_matches:
        extracted_info['years'] = year_matches
        print(f"Years found: {year_matches}")

    # Look for color
    colors = ["black", "white", "silver", "gray", "grey", "red", "blue", "green", "brown", "beige", "gold", "champagne"]
    found_colors = []
    for color in colors:
        if color in text.lower():
            found_colors.append(color.title())
    if found_colors:
        extracted_info['colors'] = found_colors
        print(f"Colors found: {found_colors}")

    # Look for mileage
    mileage_pattern = r'\b(\d{1,3}(?:,\d{3})*)\s*(?:miles|mi|odometer)\b'
    mileage_matches = re.findall(mileage_pattern, text.lower())
    if mileage_matches:
        extracted_info['mileage'] = mileage_matches
        print(f"Mileage found: {mileage_matches}")

    # Look for price
    price_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*)'
    price_matches = re.findall(price_pattern, text)
    if price_matches:
        extracted_info['price'] = price_matches
        print(f"Price found: {price_matches}")

    # Look for condition keywords
    condition_keywords = ["excellent", "good", "fair", "poor", "like new", "mint", "well maintained", "clean"]
    found_conditions = []
    for condition in condition_keywords:
        if condition in text.lower():
            found_conditions.append(condition.title())
    if found_conditions:
        extracted_info['conditions'] = found_conditions
        print(f"Conditions found: {found_conditions}")

    return extracted_info

async def analyze_rag_anything_processing():
    """Compare our RAG-Anything processing to direct extraction"""

    print(f"\nRAG-Anything Processing Analysis")
    print("=" * 40)

    # Initialize service
    service = VehicleProcessingService()
    service.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    service.embedding_dim = 3072

    # Create vehicle data from filename
    pdf_path = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports/2022LexusES350117484.pdf")

    vehicle_data = VehicleData(
        vehicle_id=f"analysis-{pdf_path.stem.lower().replace(' ', '-').replace('(', '').replace(')', '')}",
        make="Lexus",  # Based on filename
        model="ES350",  # Based on filename
        year=2022,      # Based on filename
        description=f"Analysis of vehicle processing: {pdf_path.name}",
        features=["PDF Processing Analysis", "Extraction Validation"],
        specifications={"analysis_type": "content_comparison"},
        images=[{
            "path": str(pdf_path),
            "type": "documentation"
        }],
        metadata={
            "source_file": pdf_path.name,
            "analysis_type": "content_validation"
        }
    )

    # Process with RAG-Anything
    print("Processing PDF with RAG-Anything...")
    result = await service.process_vehicle_data(vehicle_data)

    if result.success:
        print(f"RAG-Anything Processing Results:")
        print(f"  Success: True")
        print(f"  Vehicle ID: {result.vehicle_id}")
        print(f"  Text processed: {result.text_processed}")
        print(f"  Images processed: {result.images_processed}")
        print(f"  Metadata processed: {result.metadata_processed}")
        print(f"  Embedding dimension: {result.embedding_dim}")
        print(f"  Semantic tags: {result.semantic_tags}")
        print(f"  Processing time: {getattr(result, 'processing_time', 'N/A')}")

        return {
            "rag_success": True,
            "vehicle_id": result.vehicle_id,
            "semantic_tags": result.semantic_tags,
            "embedding_dim": result.embedding_dim,
            "text_processed": result.text_processed,
            "images_processed": result.images_processed,
            "metadata_processed": result.metadata_processed
        }
    else:
        print(f"RAG-Anything Processing Failed: {result.error}")
        return {
            "rag_success": False,
            "error": result.error
        }

def compare_results(direct_extraction, rag_results, full_text):
    """Compare direct extraction with RAG-Anything results"""

    print(f"\nComparison Analysis")
    print("=" * 40)

    print(f"\nDirect PDF Text Extraction Results:")
    for key, value in direct_extraction.items():
        print(f"  {key}: {value}")

    print(f"\nRAG-Anything Processing Results:")
    for key, value in rag_results.items():
        print(f"  {key}: {value}")

    print(f"\nFull Text Length: {len(full_text)} characters")
    print(f"First 500 characters: {full_text[:500]}...")

    # Assessment
    print(f"\nAssessment:")

    # Check if RAG-Anything actually analyzed the PDF content
    rag_analyzed_content = (rag_results.get("text_processed", False) or
                          rag_results.get("metadata_processed", False) or
                          len(rag_results.get("semantic_tags", [])) > 0)

    if not rag_analyzed_content:
        print("  ❌ CONCERN: RAG-Anything may not be analyzing actual PDF content")
        print("  ❌ Processing appears to be using filename-based assumptions only")
        print("  ❌ This indicates false positive testing results")
    else:
        print("  ✅ RAG-Anything appears to analyze actual PDF content")

    # Check if extraction matches reality
    if direct_extraction:
        print(f"\nReality Check:")
        if "lexus" in full_text.lower():
            print("  ✅ PDF actually contains Lexus information")
        else:
            print("  ❌ PDF may not contain Lexus information - processing may be based on filename only")

        if "es350" in full_text.lower():
            print("  ✅ PDF actually contains ES350 model information")
        else:
            print("  ❌ PDF may not contain ES350 model information")

    return rag_analyzed_content

async def main():
    """Main analysis function"""

    print("Lexus PDF Analysis - Content Validation")
    print("Checking for false positives in our testing results")
    print("=" * 80)

    # Get PDF path
    pdf_path = Path("D:/Otto_AI_v2/docs/Sample_Vehicle_Condition_Reports/2022LexusES350117484.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False

    # Direct text extraction
    print("\n1. Direct PDF Text Extraction")
    print("=" * 40)
    direct_text = extract_pdf_text_directly(pdf_path)

    if not direct_text:
        print("❌ Failed to extract text from PDF")
        return False

    # Analyze extracted text
    extracted_info = analyze_text_content(direct_text)

    # RAG-Anything processing
    print("\n2. RAG-Anything Processing")
    print("=" * 40)
    rag_results = await analyze_rag_anything_processing()

    # Compare results
    print("\n3. Results Comparison")
    print("=" * 40)
    valid_processing = compare_results(extracted_info, rag_results, direct_text)

    print(f"\nFinal Assessment:")
    if valid_processing:
        print("✅ Processing appears to analyze actual PDF content")
        return True
    else:
        print("❌ CRITICAL ISSUE: Processing may be using false positive results")
        print("❌ Story 1.2 validation may not be accurate")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)