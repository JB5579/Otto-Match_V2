"""
Otto.AI Vehicle Image Enhancement Service
Enhances existing vehicle photos from PDFs for professional UI display

This service improves extracted vehicle images by:
- Improving image quality and resolution
- Optimizing lighting and colors
- Removing background clutter
- Adding professional automotive styling
- Ensuring consistent aspect ratios for UI
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel
from PIL import Image, ImageEnhance, ImageFilter
import io

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """Types of image enhancements available"""
    IMPROVE_QUALITY = "improve_quality"
    OPTIMIZE_LIGHTING = "optimize_lighting"
    PROFESSIONAL_STYLING = "professional_styling"
    BACKGROUND_CLEANUP = "background_cleanup"
    UI_OPTIMIZATION = "ui_optimization"
    ALL_ENHANCEMENTS = "all_enhancements"


@dataclass
class EnhancementRequest:
    """Request for enhancing a vehicle image"""
    image_data: bytes  # Raw image bytes from PDF
    filename: str
    vehicle_info: Optional[Dict[str, Any]] = None
    enhancement_type: EnhancementType = EnhancementType.PROFESSIONAL_STYLING
    target_aspect: str = "16:9"  # For UI carousel display


class EnhancedImage(BaseModel):
    """Result of image enhancement"""
    enhanced_data: str  # Base64 encoded enhanced image
    original_size: tuple  # (width, height)
    enhanced_size: tuple  # (width, height)
    enhancement_type: str
    file_format: str
    quality_score: int  # 1-10 rating
    processing_metadata: Dict[str, Any]
    created_at: datetime = datetime.utcnow()


class VehicleImageEnhancementService:
    """
    Enhances vehicle images from PDFs for professional UI display
    using Google Gemini 2.5 Flash Image model
    """

    def __init__(self):
        self.openrouter_api_key = self._get_env_var('OPENROUTER_API_KEY')
        self.openrouter_client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={"Authorization": f"Bearer {self.openrouter_api_key}"},
            timeout=120.0
        )

    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with helpful error if missing"""
        import os
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required")
        return value

    def _get_enhancement_prompt(
        self,
        enhancement_type: EnhancementType,
        vehicle_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhancement prompt based on type and vehicle info"""

        vehicle_desc = ""
        if vehicle_info:
            parts = []
            if vehicle_info.get("year"):
                parts.append(str(vehicle_info["year"]))
            if vehicle_info.get("make"):
                parts.append(vehicle_info["make"])
            if vehicle_info.get("model"):
                parts.append(vehicle_info["model"])
            if vehicle_info.get("color"):
                parts.append(f"in {vehicle_info['color']}")
            vehicle_desc = " ".join(parts)

        base_prompts = {
            EnhancementType.IMPROVE_QUALITY: (
                "Improve this vehicle photo to professional dealership quality. "
                "Enhance clarity, sharpness, and resolution while maintaining authenticity. "
                "Fix any lighting issues and optimize colors."
            ),
            EnhancementType.OPTIMIZE_LIGHTING: (
                "Optimize the lighting in this vehicle photo. "
                "Balance exposure, reduce shadows/glare, and enhance visibility of details. "
                "Make it look like it was photographed in ideal lighting conditions."
            ),
            EnhancementType.PROFESSIONAL_STYLING: (
                "Transform this vehicle photo into professional automotive photography. "
                "Apply professional automotive photography standards with proper composition, "
                "color grading, and styling. Make it suitable for premium vehicle listings."
            ),
            EnhancementType.BACKGROUND_CLEANUP: (
                "Clean up the background of this vehicle photo. "
                "Remove distracting elements while maintaining the vehicle's authenticity. "
                "Create a clean, professional background that showcases the vehicle."
            ),
            EnhancementType.UI_OPTIMIZATION: (
                "Optimize this vehicle photo for UI display and carousel presentation. "
                "Ensure excellent quality, proper orientation, and professional appearance. "
                "Make it look like a premium listing photo that would attract buyers."
            ),
            EnhancementType.ALL_ENHANCEMENTS: (
                "Transform this into a premium professional vehicle photograph. "
                "Improve quality, optimize lighting, apply professional styling, "
                "and clean up the background. Make it dealership-quality suitable "
                "for premium vehicle listings and UI display."
            )
        }

        prompt = base_prompts.get(enhancement_type, base_prompts[EnhancementType.PROFESSIONAL_STYLING])

        if vehicle_desc:
            prompt = f"This is a photo of a {vehicle_desc}. {prompt}"

        prompt += " Maintain the authentic vehicle details while improving presentation quality."

        return prompt

    def _apply_local_enhancements(self, image_bytes: bytes) -> bytes:
        """Apply local image enhancements using PIL"""
        try:
            # Open image
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Apply enhancements
            # 1. Sharpness enhancement
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)

            # 2. Color enhancement
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)

            # 3. Contrast enhancement
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)

            # 4. Brightness adjustment
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)

            # Resize to optimal dimensions for UI (maintain aspect ratio)
            max_width, max_height = 1920, 1080
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save with high quality
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90, optimize=True)
            return buffer.getvalue()

        except Exception as e:
            logger.warning(f"Local enhancement failed: {e}")
            return image_bytes  # Return original if enhancement fails

    async def enhance_vehicle_image(
        self,
        request: EnhancementRequest
    ) -> EnhancedImage:
        """
        Enhance a vehicle image using Gemini 2.5 Flash Image model
        """
        # First apply local enhancements
        locally_enhanced = self._apply_local_enhancements(request.image_data)

        # Convert to base64 for API
        image_b64 = base64.b64encode(locally_enhanced).decode()
        image_data_url = f"data:image/jpeg;base64,{image_b64}"

        # Get original dimensions
        original_img = Image.open(io.BytesIO(request.image_data))
        original_size = original_img.size

        try:
            prompt = self._get_enhancement_prompt(
                request.enhancement_type,
                request.vehicle_info
            )

            logger.info(f"Enhancing image {request.filename} with {request.enhancement_type.value}")
            start_time = datetime.utcnow()

            # Use Gemini 2.5 Flash Image model
            payload = {
                "model": "google/gemini-2.5-flash-image",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url
                                }
                            }
                        ]
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {
                    "aspect_ratio": "16:9"  # Optimize for UI carousel
                }
            }

            response = await self.openrouter_client.post(
                "/chat/completions",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Extract enhanced image
            message = data["choices"][0]["message"]
            images = message.get("images", [])

            if not images:
                logger.warning("No enhanced image returned from AI, using locally enhanced version")
                # Fall back to locally enhanced image
                enhanced_data_url = image_data_url
            else:
                enhanced_data_url = images[0]["image_url"]["url"]

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Get enhanced dimensions
            if enhanced_data_url != image_data_url:
                # Decode to get dimensions
                enhanced_b64 = enhanced_data_url.split(',')[1]
                enhanced_bytes = base64.b64decode(enhanced_b64)
                enhanced_img = Image.open(io.BytesIO(enhanced_bytes))
                enhanced_size = enhanced_img.size
            else:
                enhanced_size = Image.open(io.BytesIO(locally_enhanced)).size

            enhanced_image = EnhancedImage(
                enhanced_data=enhanced_data_url,
                original_size=original_size,
                enhanced_size=enhanced_size,
                enhancement_type=request.enhancement_type.value,
                file_format="JPEG",
                quality_score=8,  # Will be calculated based on improvements
                processing_metadata={
                    "filename": request.filename,
                    "processing_time": processing_time,
                    "model": "google/gemini-2.5-flash-image",
                    "local_enhancement": True,
                    "ai_enhancement": len(images) > 0,
                    "usage": data.get("usage", {})
                }
            )

            logger.info(f"Successfully enhanced {request.filename} in {processing_time:.2f}s")
            return enhanced_image

        except Exception as e:
            logger.error(f"Failed to enhance image {request.filename}: {str(e)}")
            # Return locally enhanced image as fallback
            return EnhancedImage(
                enhanced_data=image_data_url,
                original_size=original_size,
                enhanced_size=Image.open(io.BytesIO(locally_enhanced)).size,
                enhancement_type="local_only",
                file_format="JPEG",
                quality_score=6,
                processing_metadata={
                    "filename": request.filename,
                    "error": str(e),
                    "fallback": True
                }
            )

    async def enhance_multiple_images(
        self,
        images_data: List[bytes],
        filenames: List[str],
        vehicle_info: Optional[Dict[str, Any]] = None,
        enhancement_type: EnhancementType = EnhancementType.PROFESSIONAL_STYLING
    ) -> List[EnhancedImage]:
        """
        Enhance multiple vehicle images with controlled concurrency
        """
        logger.info(f"Enhancing {len(images_data)} vehicle images...")

        # Limit concurrent processing to avoid rate limits
        concurrent_limit = 2
        results = []

        for i in range(0, len(images_data), concurrent_limit):
            batch_images = images_data[i:i+concurrent_limit]
            batch_filenames = filenames[i:i+concurrent_limit]

            batch_tasks = []
            for img_data, filename in zip(batch_images, batch_filenames):
                request = EnhancementRequest(
                    image_data=img_data,
                    filename=filename,
                    vehicle_info=vehicle_info,
                    enhancement_type=enhancement_type
                )
                batch_tasks.append(self.enhance_vehicle_image(request))

            # Process batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Image enhancement failed: {result}")
                else:
                    results.append(result)

        logger.info(f"Successfully enhanced {len(results)}/{len(images_data)} images")
        return results

    def calculate_quality_score(
        self,
        enhanced_image: EnhancedImage
    ) -> int:
        """Calculate quality score based on improvements"""
        base_score = 6

        # Boost for successful AI enhancement
        if enhanced_image.processing_metadata.get("ai_enhancement"):
            base_score += 2

        # Boost for resolution improvement
        orig_pixels = enhanced_image.original_size[0] * enhanced_image.original_size[1]
        enhanced_pixels = enhanced_image.enhanced_size[0] * enhanced_image.enhanced_size[1]
        if enhanced_pixels > orig_pixels:
            base_score += 1

        # Boost for aspect ratio optimization
        if enhanced_image.enhanced_size[0] / enhanced_image.enhanced_size[1] > 1.5:  # Widescreen
            base_score += 1

        return min(10, base_score)

    async def close(self):
        """Clean up resources"""
        await self.openrouter_client.aclose()


# Singleton instance
vehicle_image_enhancement_service = VehicleImageEnhancementService()


async def get_vehicle_image_enhancement_service() -> VehicleImageEnhancementService:
    """Get the singleton vehicle image enhancement service instance"""
    return vehicle_image_enhancement_service