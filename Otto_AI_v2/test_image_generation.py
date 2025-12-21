#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Otto.AI Image Generation Service
Generates professional vehicle photos using OpenRouter
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.services.image_generation_service import get_image_generation_service, ImagePurpose, ImageAspect

async def main():
    """Test image generation service"""
    print("Testing Otto.AI Image Generation Service...")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check API key
    if not os.getenv('OPENROUTER_API_KEY'):
        print("Missing OPENROUTER_API_KEY")
        return

    print("Environment variables loaded")

    # Sample vehicle info
    vehicle_info = {
        "year": 2018,
        "make": "GMC",
        "model": "Canyon",
        "trim": "SLT",
        "exterior_color": "Blue",
        "interior_color": "Tan",
        "vin": "1GTP6DE16J1117146"
    }

    try:
        # Initialize service
        img_service = await get_image_generation_service()
        print("Image generation service initialized")

        # Test single image generation
        print("\n=== Testing Hero Shot Generation ===")
        from src.services.image_generation_service import ImageGenerationRequest

        request = ImageGenerationRequest(
            vehicle_info=vehicle_info,
            purpose=ImagePurpose.HERO_SHOT,
            aspect_ratio=ImageAspect.WIDESCREEN_16_9,
            style_prompt="professional automotive photography, bright daylight, clean background"
        )

        print("Generating hero shot...")
        hero_image = await img_service.generate_image(request)

        print("SUCCESS: Hero shot generated!")
        print(f"   - Size: {len(hero_image.image_data)} characters")
        print(f"   - Aspect: {hero_image.aspect_ratio}")
        print(f"   - Generation time: {hero_image.generation_metadata.get('generation_time', 'N/A')}s")
        print(f"   - Model: {hero_image.generation_metadata.get('model', 'N/A')}")

        # Save sample to file for inspection
        import base64
        hero_data = hero_image.image_url.split(',')[1]  # Remove data URL prefix
        with open('generated_hero.png', 'wb') as f:
            f.write(base64.b64decode(hero_data))
        print("   - Saved as: generated_hero.png")

        # Cleanup
        await img_service.close()
        print("\nSUCCESS: Image generation test completed!")

    except Exception as e:
        print(f"\nERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())