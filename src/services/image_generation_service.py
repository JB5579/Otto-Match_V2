"""
Otto.AI Image Generation Service
Generates professional vehicle photos using OpenRouter and AI models

This service creates:
- Hero images for vehicle listings
- Additional angles missing from condition reports
- Enhanced marketing visuals
- Background replacements for professional appearance
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

logger = logging.getLogger(__name__)


class ImageAspect(Enum):
    """Supported image aspect ratios for generation"""
    SQUARE = "1:1"          # 1024x1024
    PORTRAIT_2_3 = "2:3"   # 832x1248
    LANDSCAPE_3_2 = "3:2"  # 1248x832
    PORTRAIT_3_4 = "3:4"   # 864x1184
    LANDSCAPE_4_3 = "4:3"  # 1184x864
    WIDESCREEN_16_9 = "16:9"  # 1344x768
    ULTRAWIDE_21_9 = "21:9"  # 1536x672


class ImagePurpose(Enum):
    """Purpose of the generated image"""
    HERO_SHOT = "hero"              # Main listing image
    EXTERIOR_FRONT = "exterior_front"
    EXTERIOR_REAR = "exterior_rear"
    EXTERIOR_SIDE = "exterior_side"
    INTERIOR_DASH = "interior_dash"
    INTERIOR_SEATS = "interior_seats"
    ENGINE_BAY = "engine_bay"
    WHEEL_DETAIL = "wheel_detail"
    MARKETING_LIFESTYLE = "marketing_lifestyle"


@dataclass
class ImageGenerationRequest:
    """Request for generating vehicle images"""
    vehicle_info: Dict[str, Any]
    purpose: ImagePurpose
    aspect_ratio: ImageAspect = ImageAspect.WIDESCREEN_16_9
    style_prompt: Optional[str] = None
    reference_images: Optional[List[str]] = None  # Base64 images for reference


class GeneratedImage(BaseModel):
    """Result of image generation"""
    image_data: str  # Base64 encoded image
    image_url: str   # Data URL format
    aspect_ratio: str
    purpose: str
    generation_metadata: Dict[str, Any]
    created_at: datetime = datetime.utcnow()


class ImageGenerationService:
    """
    Generates professional vehicle images using OpenRouter and AI models
    """

    # Best models for vehicle image generation
    VEHICLE_GENERATION_MODELS = [
        "google/gemini-2.5-flash-image-preview",
        "black-forest-labs/flux.2-pro",
        "black-forest-labs/flux.2-flex",
        "sourceful/riverflow-v2-standard-preview"
    ]

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

    def _build_vehicle_prompt(
        self,
        vehicle_info: Dict[str, Any],
        purpose: ImagePurpose,
        style_prompt: Optional[str] = None
    ) -> str:
        """Build a detailed prompt for vehicle image generation"""

        base_prompt = self._get_base_prompt_for_purpose(purpose)

        vehicle_details = []
        if vehicle_info.get("year"):
            vehicle_details.append(f"{vehicle_info['year']}")
        if vehicle_info.get("make"):
            vehicle_details.append(vehicle_info["make"])
        if vehicle_info.get("model"):
            vehicle_details.append(vehicle_info["model"])
        if vehicle_info.get("trim"):
            vehicle_details.append(vehicle_info["trim"])
        if vehicle_info.get("exterior_color"):
            vehicle_details.append(f"in {vehicle_info['exterior_color']}")

        vehicle_desc = " ".join(vehicle_details) if vehicle_details else "modern vehicle"

        full_prompt = base_prompt.format(
            vehicle=vehicle_desc,
            color=vehicle_info.get("exterior_color", "neutral color"),
            style=style_prompt or "professional automotive photography"
        )

        return full_prompt

    def _get_base_prompt_for_purpose(self, purpose: ImagePurpose) -> str:
        """Get base prompt template for each image purpose"""

        prompts = {
            ImagePurpose.HERO_SHOT: (
                "Professional automotive photograph of a {vehicle} {color} "
                "studio lighting, clean background, flagship dealership quality, "
                "showcasing the vehicle's best features, {style}"
            ),
            ImagePurpose.EXTERIOR_FRONT: (
                "Front three-quarter view of a {vehicle} {color}, "
                "professional automotive photography, outdoor lighting, "
                "showing grille, headlights, and front design, {style}"
            ),
            ImagePurpose.EXTERIOR_REAR: (
                "Rear three-quarter view of a {vehicle} {color}, "
                "professional automotive photography, showing taillights, "
                "trunk, and rear design elements, {style}"
            ),
            ImagePurpose.EXTERIOR_SIDE: (
                "Side profile view of a {vehicle} {color}, "
                "professional automotive photography, showcasing the vehicle's "
                "lines, wheels, and side design, {style}"
            ),
            ImagePurpose.INTERIOR_DASH: (
                "Interior dashboard view of a {vehicle}, showing steering wheel, "
                "instrument cluster, infotainment system, professional automotive "
                "interior photography, clean and well-lit, {style}"
            ),
            ImagePurpose.INTERIOR_SEATS: (
                "Interior seating view of a {vehicle}, showing seats, door panels, "
                "center console, professional automotive interior photography, "
                "premium materials and craftsmanship, {style}"
            ),
            ImagePurpose.ENGINE_BAY: (
                "Engine bay view of a {vehicle}, clean engine compartment, "
                "professional automotive photography, showing engine components, "
                "hoses, and mechanical details, {style}"
            ),
            ImagePurpose.WHEEL_DETAIL: (
                "Close-up view of {vehicle} wheels and tires, professional automotive "
                "photography, showing wheel design, brake calipers, and tire tread, "
                "{style}"
            ),
            ImagePurpose.MARKETING_LIFESTYLE: (
                "Lifestyle automotive photograph of a {vehicle} {color}, "
                "scenic setting, golden hour lighting, aspirational composition, "
                "professional commercial photography, {style}"
            )
        }

        return prompts.get(purpose, prompts[ImagePurpose.HERO_SHOT])

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        model: Optional[str] = None
    ) -> GeneratedImage:
        """
        Generate a single vehicle image using OpenRouter
        """
        if not model:
            model = self.VEHICLE_GENERATION_MODELS[0]  # Default to first model

        prompt = self._build_vehicle_prompt(
            request.vehicle_info,
            request.purpose,
            request.style_prompt
        )

        try:
            # Build request payload
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {
                    "aspect_ratio": request.aspect_ratio.value
                }
            }

            # Add reference images if provided
            if request.reference_images:
                content = payload["messages"][0]["content"]
                for ref_image in request.reference_images:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": ref_image
                        }
                    })

            logger.info(f"Generating image for {request.purpose.value} using {model}")
            start_time = datetime.utcnow()

            response = await self.openrouter_client.post(
                "/chat/completions",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Extract generated image
            message = data["choices"][0]["message"]
            images = message.get("images", [])

            if not images:
                raise ValueError("No images generated in response")

            # Use first generated image
            image_data = images[0]["image_url"]["url"]  # This is a data URL

            generation_time = (datetime.utcnow() - start_time).total_seconds()

            generated_image = GeneratedImage(
                image_data=image_data,
                image_url=image_data,
                aspect_ratio=request.aspect_ratio.value,
                purpose=request.purpose.value,
                generation_metadata={
                    "model": model,
                    "prompt": prompt,
                    "generation_time": generation_time,
                    "usage": data.get("usage", {}),
                    "reference_images_count": len(request.reference_images or [])
                }
            )

            logger.info(f"Successfully generated {request.purpose.value} image in {generation_time:.2f}s")
            return generated_image

        except Exception as e:
            logger.error(f"Failed to generate image for {request.purpose.value}: {str(e)}")
            raise

    async def generate_complete_set(
        self,
        vehicle_info: Dict[str, Any],
        existing_images: Optional[List[str]] = None,
        style_prompt: Optional[str] = None
    ) -> List[GeneratedImage]:
        """
        Generate a complete set of professional vehicle images
        """
        # Determine which images we need based on existing images
        required_purposes = [
            ImagePurpose.HERO_SHOT,
            ImagePurpose.EXTERIOR_FRONT,
            ImagePurpose.EXTERIOR_REAR,
            ImagePurpose.EXTERIOR_SIDE,
            ImagePurpose.INTERIOR_DASH,
            ImagePurpose.INTERIOR_SEATS
        ]

        # For now, generate all required images
        # TODO: Analyze existing_images to avoid duplicates
        generation_tasks = []

        for purpose in required_purposes:
            # Choose appropriate aspect ratio for each purpose
            if purpose in [ImagePurpose.HERO_SHOT]:
                aspect = ImageAspect.WIDESCREEN_16_9
            elif purpose in [ImagePurpose.EXTERIOR_FRONT, ImagePurpose.EXTERIOR_REAR, ImagePurpose.EXTERIOR_SIDE]:
                aspect = ImageAspect.LANDSCAPE_3_2
            else:
                aspect = ImageAspect.LANDSCAPE_4_3

            request = ImageGenerationRequest(
                vehicle_info=vehicle_info,
                purpose=purpose,
                aspect_ratio=aspect,
                style_prompt=style_prompt,
                reference_images=existing_images[:1] if existing_images else None  # Use first existing as reference
            )

            generation_tasks.append(self.generate_image(request))

        logger.info(f"Generating {len(generation_tasks)} vehicle images...")

        # Generate images in parallel (limit to 2 concurrent to avoid rate limits)
        results = []
        for i in range(0, len(generation_tasks), 2):
            batch = generation_tasks[i:i+2]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Image generation failed: {result}")
                else:
                    results.append(result)

        logger.info(f"Successfully generated {len(results)}/{len(generation_tasks)} vehicle images")
        return results

    async def enhance_existing_image(
        self,
        original_image: str,  # Base64 image data
        enhancement_type: str,  # "remove_background", "improve_quality", "change_lighting"
        vehicle_info: Optional[Dict[str, Any]] = None
    ) -> GeneratedImage:
        """
        Enhance an existing vehicle image (background removal, quality improvement, etc.)
        """
        enhancement_prompts = {
            "remove_background": "Professional automotive photo of vehicle with clean white background, studio lighting",
            "improve_quality": "High-resolution professional automotive photography, enhanced clarity and color",
            "change_lighting": "Professional automotive photo with golden hour lighting, warm tones",
            "showcase_features": "Professional automotive photo highlighting vehicle features and design elements"
        }

        prompt = enhancement_prompts.get(
            enhancement_type,
            "Professional automotive photography enhancement"
        )

        if vehicle_info:
            vehicle_desc = f"{vehicle_info.get('year', '')} {vehicle_info.get('make', '')} {vehicle_info.get('model', '')}"
            prompt += f" of {vehicle_desc.strip()}"

        try:
            payload = {
                "model": self.VEHICLE_GENERATION_MODELS[0],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{prompt}. Use this image as reference and enhance it."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": original_image
                                }
                            }
                        ]
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {
                    "aspect_ratio": "16:9"
                }
            }

            response = await self.openrouter_client.post(
                "/chat/completions",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            images = message.get("images", [])

            if not images:
                raise ValueError("No enhanced image generated")

            enhanced_image = GeneratedImage(
                image_data=images[0]["image_url"]["url"],
                image_url=images[0]["image_url"]["url"],
                aspect_ratio="16:9",
                purpose=f"enhanced_{enhancement_type}",
                generation_metadata={
                    "model": self.VEHICLE_GENERATION_MODELS[0],
                    "enhancement_type": enhancement_type,
                    "original_image_size": len(original_image),
                    "usage": data.get("usage", {})
                }
            )

            logger.info(f"Successfully enhanced image with {enhancement_type}")
            return enhanced_image

        except Exception as e:
            logger.error(f"Failed to enhance image: {str(e)}")
            raise

    async def close(self):
        """Clean up resources"""
        await self.openrouter_client.aclose()


# Singleton instance
image_generation_service = ImageGenerationService()


async def get_image_generation_service() -> ImageGenerationService:
    """Get the singleton image generation service instance"""
    return image_generation_service