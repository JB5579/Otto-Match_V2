#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Otto.AI Vehicle Image Enhancement Service
Enhances real vehicle photos from PDFs for professional UI display
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def load_sample_image():
    """Load a sample image from PDF or use a test image"""
    # First try to extract from existing PDF processing
    sample_dir = Path(__file__).parent / 'docs' / 'Sample_Vehicle_Condition_Reports'
    pdf_files = list(sample_dir.glob("*.pdf"))

    if pdf_files:
        # Extract an image from the first PDF
        import fitz  # PyMuPDF

        try:
            doc = fitz.open(str(pdf_files[0]))
            page = doc.load_page(0)
            image_list = page.get_images(full=True)

            if image_list:
                xref = image_list[0][0]
                img_data = doc.extract_image(xref)
                if img_data and img_data.get("image"):
                    doc.close()
                    return img_data["image"], f"extracted_{pdf_files[0].name}.jpg"

            doc.close()
        except Exception as e:
            print(f"Failed to extract from PDF: {e}")

    # Fallback: create a simple test image
    print("Creating test image...")
    from PIL import Image
    import io

    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='blue')

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue(), "test_vehicle.jpg"

async def main():
    """Test vehicle image enhancement service"""
    print("Testing Otto.AI Vehicle Image Enhancement Service...")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check API key
    if not os.getenv('OPENROUTER_API_KEY'):
        print("Missing OPENROUTER_API_KEY")
        return

    print("Environment variables loaded")

    try:
        # Initialize service
        from src.services.vehicle_image_enhancement_service import (
            get_vehicle_image_enhancement_service,
            EnhancementType,
            EnhancementRequest
        )

        enhancement_service = await get_vehicle_image_enhancement_service()
        print("Vehicle image enhancement service initialized")

        # Load sample image
        image_data, filename = load_sample_image()
        print(f"Loaded sample image: {filename} ({len(image_data):,} bytes)")

        # Sample vehicle info
        vehicle_info = {
            "year": 2018,
            "make": "GMC",
            "model": "Canyon",
            "color": "Blue",
            "vin": "1GTP6DE16J1117146"
        }

        # Test different enhancement types
        enhancement_types = [
            EnhancementType.PROFESSIONAL_STYLING,
            EnhancementType.IMPROVE_QUALITY,
            EnhancementType.UI_OPTIMIZATION
        ]

        for enhancement_type in enhancement_types:
            print(f"\n=== Testing {enhancement_type.value} ===")

            request = EnhancementRequest(
                image_data=image_data,
                filename=filename,
                vehicle_info=vehicle_info,
                enhancement_type=enhancement_type
            )

            print(f"Applying {enhancement_type.value} enhancement...")
            enhanced_image = await enhancement_service.enhance_vehicle_image(request)

            print(f"SUCCESS: {enhancement_type.value} completed!")
            print(f"   - Original size: {enhanced_image.original_size}")
            print(f"   - Enhanced size: {enhanced_image.enhanced_size}")
            print(f"   - File format: {enhanced_image.file_format}")
            print(f"   - Processing time: {enhanced_image.processing_metadata.get('processing_time', 'N/A')}s")
            print(f"   - AI enhancement: {enhanced_image.processing_metadata.get('ai_enhancement', False)}")
            print(f"   - Local enhancement: {enhanced_image.processing_metadata.get('local_enhancement', False)}")

            # Save enhanced image for inspection
            import base64
            if enhanced_image.enhanced_data.startswith('data:'):
                enhanced_b64 = enhanced_image.enhanced_data.split(',')[1]
            else:
                enhanced_b64 = enhanced_image.enhanced_data

            with open(f'enhanced_{enhancement_type.value}.jpg', 'wb') as f:
                f.write(base64.b64decode(enhanced_b64))
            print(f"   - Saved as: enhanced_{enhancement_type.value}.jpg")

        # Test multiple image enhancement
        print(f"\n=== Testing Multiple Image Enhancement ===")
        print("Enhancing multiple sample images...")

        # Create multiple test images
        test_images = []
        test_filenames = []

        for i in range(3):
            from PIL import Image
            import io

            # Create test images with different colors
            colors = ['red', 'green', 'blue']
            img = Image.new('RGB', (600, 400), color=colors[i])

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            test_images.append(buffer.getvalue())
            test_filenames.append(f"test_vehicle_{i+1}.jpg")

        # Enhance all images
        enhanced_results = await enhancement_service.enhance_multiple_images(
            test_images,
            test_filenames,
            vehicle_info=vehicle_info,
            enhancement_type=EnhancementType.UI_OPTIMIZATION
        )

        print(f"\nSUCCESS: Enhanced {len(enhanced_results)} images!")
        for i, result in enumerate(enhanced_results, 1):
            print(f"   {i}. {result.processing_metadata.get('filename', 'unknown')}")

        # Cleanup
        await enhancement_service.close()
        print("\nSUCCESS: All enhancement tests completed!")

    except Exception as e:
        print(f"\nERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())