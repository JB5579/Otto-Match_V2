"""
Otto.AI PDF Ingestion Service
Processes condition report PDFs into complete vehicle listing artifacts using
parallel OpenRouter (Gemini) vision analysis and PyMuPDF image extraction.

Architecture: OpenRouter for intelligence + PyMuPDF for extraction = Complete listing data
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import fitz  # PyMuPDF
import httpx
from PIL import Image
from pydantic import BaseModel, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Gemini-extracted metadata about an image"""
    page_number: int
    description: str
    category: str  # hero, carousel, detail, documentation
    quality_score: int
    vehicle_angle: str
    suggested_alt: str
    visible_damage: Optional[List[str]] = None


@dataclass
class ExtractedImage:
    """PyMuPDF-extracted raw image data"""
    page_number: int
    image_bytes: bytes
    width: int
    height: int
    format: str  # jpeg, png
    xref: int  # PDF internal reference


class EnrichedImage(BaseModel):
    """Merged result: Gemini metadata + PyMuPDF raw image"""
    # From Gemini
    description: str
    category: str
    quality_score: int
    vehicle_angle: str
    suggested_alt: str
    visible_damage: Optional[List[str]]

    # From PyMuPDF
    image_bytes: bytes
    width: int
    height: int
    format: str
    page_number: int

    # Generated
    storage_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class VehicleInfo(BaseModel):
    """Basic vehicle information"""
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: int = 0  # Default to 0 if not found
    drivetrain: Optional[str] = "Unknown"
    transmission: Optional[str] = "Unknown"
    engine: Optional[str] = "Unknown"
    exterior_color: Optional[str] = "Unknown"
    interior_color: Optional[str] = "Unknown"


class ConditionData(BaseModel):
    """Vehicle condition assessment"""
    score: float  # decimal like 4.3
    grade: str  # Clean, Average, Rough
    issues: Dict[str, List[Any]] = {}  # exterior, interior, mechanical, tiresWheels

    @field_validator('issues', mode='before')
    @classmethod
    def normalize_issues(cls, v):
        """Convert string issues to dictionaries if needed"""
        if not isinstance(v, dict):
            return {}

        normalized = {}
        for category, items in v.items():
            if not isinstance(items, list):
                items = [items] if items else []

            normalized_items = []
            for item in items:
                if isinstance(item, str):
                    # Convert "LOCATION: Issue description" to dict
                    if ':' in item:
                        parts = item.split(':', 1)
                        normalized_items.append({
                            'location': parts[0].strip(),
                            'issue': parts[1].strip()
                        })
                    else:
                        normalized_items.append({'description': item})
                elif isinstance(item, dict):
                    normalized_items.append(item)

            normalized[category] = normalized_items

        return normalized


class SellerInfo(BaseModel):
    """Seller information"""
    name: str
    type: str  # dealer, private


class VehicleListingArtifact(BaseModel):
    """Complete output for UI consumption"""
    vehicle: VehicleInfo
    condition: ConditionData
    images: List[EnrichedImage]
    seller: SellerInfo
    processing_metadata: Dict[str, Any] = {}
    created_at: datetime = datetime.utcnow()


class PDFIngestionService:
    """
    Processes condition report PDFs into complete listing artifacts.

    Uses parallel processing:
    1. OpenRouter/Gemini for intelligent extraction (data + image metadata)
    2. PyMuPDF for raw image bytes
    3. Vehicle image enhancement for UI-quality photos

    Then merges results for rich, UI-ready output.
    """

    def __init__(self):
        self.openrouter_api_key = self._get_env_var('OPENROUTER_API_KEY')
        self.openrouter_client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={"Authorization": f"Bearer {self.openrouter_api_key}"},
            timeout=120.0
        )
        self.pdf_annotations_cache = {}  # Cache for reuse annotations
        self.image_enhancement_enabled = True  # Enable by default

    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with helpful error if missing"""
        import os
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required")
        return value

    async def process_condition_report(
        self,
        pdf_bytes: bytes,
        filename: str
    ) -> VehicleListingArtifact:
        """
        Main entry point: PDF bytes → Complete listing artifact

        This is the "one-shot" pipeline that extracts everything needed
        to create a listing card like the UI prototypes.
        """
        logger.info(f"Starting PDF processing for {filename}")
        start_time = datetime.utcnow()

        try:
            # Sequential processing for debugging
            logger.info("Starting PyMuPDF image extraction...")
            pymupdf_images = self._extract_images_with_pymupdf(pdf_bytes)

            logger.info("Starting Gemini analysis...")
            gemini_result = await self._analyze_with_gemini(pdf_bytes)

            # Handle exceptions
            if isinstance(gemini_result, Exception):
                logger.error(f"Gemini analysis failed: {gemini_result}")
                raise gemini_result
            if isinstance(pymupdf_images, Exception):
                logger.error(f"PyMuPDF extraction failed: {pymupdf_images}")
                raise pymupdf_images

            # Merge: Gemini metadata + PyMuPDF raw images
            enriched_images = self._merge_image_data(
                gemini_result["images"],
                pymupdf_images
            )

            # Create the listing artifact
            artifact = VehicleListingArtifact(
                vehicle=VehicleInfo(**gemini_result["vehicle"]),
                condition=ConditionData(**gemini_result["condition"]),
                images=enriched_images,
                seller=SellerInfo(**gemini_result["seller"]),
                processing_metadata={
                    "filename": filename,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "gemini_images_found": len(gemini_result["images"]),
                    "pymupdf_images_extracted": len(pymupdf_images),
                    "final_merged_images": len(enriched_images)
                }
            )

            logger.info(f"Successfully processed {filename}: {artifact.vehicle.vin}")
            return artifact

        except Exception as e:
            logger.error(f"Failed to process PDF {filename}: {str(e)}")
            raise

    async def _analyze_with_gemini(self, pdf_bytes: bytes) -> dict:
        """
        Single OpenRouter call that extracts ALL structured data + image metadata.

        This is where the "intelligence" lives - Gemini sees the PDF visually
        and extracts rich semantic information.
        """
        # Check file size - OpenRouter/Gemini has limits (~20MB recommended)
        file_size_mb = len(pdf_bytes) / (1024 * 1024)
        if file_size_mb > 20:
            logger.warning(f"Large PDF detected ({file_size_mb:.1f}MB). May exceed API limits.")

        pdf_base64 = base64.b64encode(pdf_bytes).decode()
        logger.info(f"PDF size: {file_size_mb:.1f}MB, base64 size: {len(pdf_base64) / (1024 * 1024):.1f}MB")

        try:
            response = await self.openrouter_client.post(
                "/chat/completions",
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._get_extraction_prompt()
                            },
                            {
                                "type": "file",
                                "file": {
                                    "filename": "condition_report.pdf",
                                    "file_data": f"data:application/pdf;base64,{pdf_base64}"
                                }
                            }
                        ]
                    }],
                    "modalities": ["text", "image"],  # Get both text and image analysis
                    "plugins": [
                        {
                            "id": "file-parser",
                            "pdf": {
                                "engine": "pdf-text"  # Free option for structured condition reports
                            }
                        }
                    ]
                }
            )

            response.raise_for_status()
            data = response.json()

            # Debug: print the response structure
            logger.info(f"OpenRouter response structure: {list(data.keys())}")

            # Parse the structured response
            message = data["choices"][0]["message"]
            content = message.get("content", "")

            # Store annotations for potential reuse
            file_annotations = message.get("annotations")
            if file_annotations:
                logger.info(f"File annotations available for reuse: {type(file_annotations)}")

            logger.info(f"Response content type: {type(content)}")
            logger.info(f"Response content preview: {str(content)[:200]}...")

            # Check for images in the response (new with modalities)
            if message.get("images"):
                logger.info(f"Images in response: {len(message['images'])}")
                for i, img in enumerate(message.get("images", [])):
                    logger.info(f"  Image {i+1}: {img.get('image_url', {}).get('url', 'N/A')[:50]}...")

            if isinstance(content, str):
                # Extract JSON from markdown code blocks
                try:
                    # First try to extract JSON from markdown code block
                    import re
                    json_match = re.search(r'```(?:json)?\s*\n(\{[\s\S]*?\})\s*```', content)
                    if json_match:
                        content = json.loads(json_match.group(1))
                    else:
                        # Try direct JSON parse
                        content = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Try to find any JSON-like structure
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        content = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found in response")

            # Map field names from Gemini response to our expected format
            if isinstance(content, dict):
                # Convert keys to lowercase and replace spaces with underscores
                def normalize_keys(d):
                    return {k.lower().replace(' ', '_'): v for k, v in d.items()}

                content = normalize_keys(content)

                # Map vehicle_data or vehicle_data to vehicle
                for key in ['vehicle_data', 'vehicle']:
                    if key in content:
                        vehicle_data = normalize_keys(content[key])

                        # Map specific field names
                        field_mappings = {
                            'odometer_reading': 'odometer',
                            'trim_level': 'trim',
                            'exterior_color': 'exterior_color',
                            'interior_color': 'interior_color'
                        }

                        for old_field, new_field in field_mappings.items():
                            if old_field in vehicle_data:
                                vehicle_data[new_field] = vehicle_data[old_field]

                        # Add default values for missing required fields
                        defaults = {
                            'transmission': 'Automatic',
                            'engine': 'Unknown',
                            'drivetrain': 'Unknown',
                            'exterior_color': 'Unknown',
                            'interior_color': 'Unknown',
                            'odometer': 0
                        }

                        for field, default_val in defaults.items():
                            if field not in vehicle_data or vehicle_data[field] is None:
                                vehicle_data[field] = default_val

                        # Ensure odometer is an integer
                        if isinstance(vehicle_data.get('odometer'), str):
                            # Remove commas and convert to int
                            try:
                                vehicle_data['odometer'] = int(vehicle_data['odometer'].replace(',', '').replace(' ', ''))
                            except (ValueError, AttributeError):
                                vehicle_data['odometer'] = 0

                        content['vehicle'] = vehicle_data
                        break

                # Map condition_data to condition
                for key in ['condition_data', 'condition']:
                    if key in content:
                        condition_data = normalize_keys(content[key])

                        # Map specific condition field names
                        condition_mappings = {
                            'overall_score': 'score',
                            'overall_grade': 'grade',
                            'condition_score': 'score',
                            'condition_grade': 'grade'
                        }

                        for old_field, new_field in condition_mappings.items():
                            if old_field in condition_data:
                                condition_data[new_field] = condition_data[old_field]

                        # Add defaults for missing required fields
                        if 'score' not in condition_data:
                            condition_data['score'] = 4.0
                        if 'grade' not in condition_data:
                            if 'overall_score' in condition_data:
                                score = condition_data['overall_score']
                                if score >= 4.5:
                                    condition_data['grade'] = 'Clean'
                                elif score >= 3.5:
                                    condition_data['grade'] = 'Average'
                                else:
                                    condition_data['grade'] = 'Rough'
                            else:
                                condition_data['grade'] = 'Average'

                        # Ensure issues field exists
                        if 'issues' not in condition_data:
                            condition_data['issues'] = {}

                        content['condition'] = condition_data
                        break

                # Map seller_info or seller to seller
                for key in ['seller_information', 'seller_info', 'seller']:
                    if key in content:
                        content['seller'] = normalize_keys(content[key])
                        break

                # Add default seller if none found
                if 'seller' not in content:
                    content['seller'] = {
                        'name': 'Unknown Seller',
                        'type': 'dealer'
                    }

                # Map various image key names to 'images' (Gemini may use different keys)
                image_key_variants = [
                    'image_data',
                    'for_each_image_visible_in_the_pdf',
                    'image_metadata',
                    'extracted_images',
                    'pdf_images'
                ]

                images_found = False
                for key in image_key_variants:
                    if key in content and content[key]:
                        content['images'] = content[key]
                        logger.info(f"Mapped image data from key: {key}")
                        images_found = True
                        break

                if not images_found and 'images' not in content:
                    content['images'] = []

                logger.info(f"Normalized response keys: {list(content.keys())}")
                if 'vehicle' in content:
                    logger.info(f"Vehicle fields: {list(content['vehicle'].keys())}")

            logger.info(f"Gemini analysis completed: {content.get('vehicle', {}).get('vin', 'unknown')}")
            return content

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text[:500] if e.response.text else "No error details"
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            logger.error(f"Error details: {error_detail}")

            if e.response.status_code == 400:
                # Provide helpful message for common 400 errors
                if file_size_mb > 15:
                    raise ValueError(
                        f"PDF file too large ({file_size_mb:.1f}MB). "
                        f"OpenRouter/Gemini has size limits. Try a smaller file or compress the PDF. "
                        f"API response: {error_detail}"
                    )
                raise ValueError(f"Bad request to OpenRouter API: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            raise

    def _extract_images_with_pymupdf(self, pdf_bytes: bytes) -> List[ExtractedImage]:
        """
        Extract raw image bytes from PDF using PyMuPDF.

        This runs synchronously but is very fast (<100ms for typical PDFs).
        Filters out small decorative images and keeps only vehicle photos.
        """
        images = []

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)

                for img_info in image_list:
                    xref = img_info[0]

                    try:
                        img_data = doc.extract_image(xref)

                        if img_data and img_data.get("image"):
                            # Filter out tiny images (logos, icons, stamps)
                            width = img_data.get("width", 0)
                            height = img_data.get("height", 0)

                            if width >= 200 and height >= 150:  # Minimum size for vehicle photos
                                images.append(ExtractedImage(
                                    page_number=page_num + 1,  # 1-indexed for consistency
                                    image_bytes=img_data["image"],
                                    width=width,
                                    height=height,
                                    format=img_data["ext"],
                                    xref=xref
                                ))

                    except Exception as e:
                        # Log but don't fail - some images may be corrupt
                        logger.debug(f"Failed to extract image xref {xref}: {e}")

            doc.close()
            logger.info(f"PyMuPDF extracted {len(images)} images from PDF")
            return images

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {str(e)}")
            raise

    def _merge_image_data(
        self,
        gemini_metadata: List[dict],
        pymupdf_images: List[ExtractedImage]
    ) -> List[EnrichedImage]:
        """
        Match Gemini's rich metadata with PyMuPDF's raw bytes and enhance images.

        Matching strategy:
        1. Group by page number
        2. Match by position within page (Gemini provides approximate ordering)
        3. Fall back to size-based matching if needed
        4. Apply image enhancement if enabled
        """
        # Group PyMuPDF images by page
        images_by_page: dict[int, List[ExtractedImage]] = {}
        for img in pymupdf_images:
            images_by_page.setdefault(img.page_number, []).append(img)

        enriched = []

        # Log the structure of incoming metadata for debugging
        if gemini_metadata:
            logger.info(f"Processing {len(gemini_metadata)} image metadata entries")
            logger.debug(f"First metadata entry keys: {list(gemini_metadata[0].keys()) if gemini_metadata else 'none'}")

        for idx, meta in enumerate(gemini_metadata):
            # Validate required fields exist
            if not isinstance(meta, dict):
                logger.warning(f"Skipping non-dict metadata entry at index {idx}: {type(meta)}")
                continue

            # Handle missing page_number - try alternatives or default to 1
            page_num = meta.get("page_number") or meta.get("pageNumber") or meta.get("page") or 1

            # Ensure required fields have defaults (check for None/missing, not just key existence)
            if not meta.get("description"):
                meta["description"] = f"Vehicle image {idx + 1}"
            if not meta.get("vehicle_angle"):
                meta["vehicle_angle"] = "other"
            if not meta.get("category"):
                meta["category"] = "carousel"
            if meta.get("quality_score") is None:
                meta["quality_score"] = 5
            if not meta.get("suggested_alt"):
                meta["suggested_alt"] = meta.get("description", f"Vehicle image {idx + 1}")

            page_images = images_by_page.get(page_num, [])

            if not page_images:
                logger.debug(f"No raw image found for page {page_num} metadata")
                continue  # No raw image found for this metadata

            # Strategy: Use Gemini's description to find best match
            # For now, simple approach: take first available image on that page
            # TODO: Enhance with smarter matching using image features
            raw_image = page_images.pop(0)  # Remove to prevent double-matching

            # Determine if this is a key image that should be enhanced
            should_enhance = (
                self.image_enhancement_enabled and
                meta.get("category") in ["hero", "carousel"] and
                raw_image.width >= 800 and raw_image.height >= 600  # Minimum size for enhancement
            )

            image_bytes = raw_image.image_bytes

            # Apply image enhancement for key images
            if should_enhance:
                try:
                    import asyncio
                    # Import here to avoid circular imports
                    from .vehicle_image_enhancement_service import (
                        get_vehicle_image_enhancement_service,
                        EnhancementType,
                        EnhancementRequest
                    )

                    # Note: This will be enhanced asynchronously in process_condition_report
                    # For now, mark for enhancement
                    enhancement_requested = True
                    logger.info(f"Image marked for enhancement: {meta.get('category', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to mark image for enhancement: {e}")
                    enhancement_requested = False
            else:
                enhancement_requested = False

            enriched.append(EnrichedImage(
                # Gemini metadata
                description=meta["description"],
                category=meta["category"],
                quality_score=meta["quality_score"],
                vehicle_angle=meta["vehicle_angle"],
                suggested_alt=meta["suggested_alt"],
                visible_damage=meta.get("visible_damage") or [],

                # PyMuPDF raw data
                image_bytes=image_bytes,
                width=raw_image.width,
                height=raw_image.height,
                format=raw_image.format,
                page_number=raw_image.page_number
            ))

        # Fallback: If no images matched but we have PyMuPDF images, create basic entries
        if not enriched and pymupdf_images:
            logger.warning(f"No Gemini metadata matched. Creating basic entries for {len(pymupdf_images)} PyMuPDF images")
            for idx, raw_image in enumerate(pymupdf_images):
                enriched.append(EnrichedImage(
                    description=f"Vehicle image {idx + 1} extracted from PDF",
                    category="carousel" if idx > 0 else "hero",
                    quality_score=5,
                    vehicle_angle="other",
                    suggested_alt=f"Vehicle image {idx + 1}",
                    visible_damage=[],
                    image_bytes=raw_image.image_bytes,
                    width=raw_image.width,
                    height=raw_image.height,
                    format=raw_image.format,
                    page_number=raw_image.page_number
                ))

        # Sort by category priority: hero first, then carousel, etc.
        category_order = {"hero": 0, "carousel": 1, "detail": 2, "documentation": 3}
        enriched.sort(key=lambda x: category_order.get(x.category, 99))

        logger.info(f"Merged {len(enriched)} enriched images from {len(gemini_metadata)} metadata + {len(pymupdf_images)} raw images")
        return enriched

    def _create_thumbnail(self, image_bytes: bytes, max_size: int = 300) -> bytes:
        """Create thumbnail using Pillow"""
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (for JPEG output)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Create thumbnail while maintaining aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save as JPEG with optimization
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create thumbnail: {str(e)}")
            # Return original bytes as fallback
            return image_bytes

    def _get_extraction_prompt(self) -> str:
        """The master prompt for Gemini extraction"""
        return """Analyze this vehicle condition report PDF completely and extract ALL information as structured JSON.

You are an expert automotive analyst. Extract the following information with high accuracy:

1. VEHICLE DATA:
   - VIN (17-character identifier - critical)
   - Year, Make, Model, Trim level
   - Odometer reading as integer (no commas)
   - Drivetrain (FWD, RWD, AWD, 4WD)
   - Transmission type (manual, automatic, CVT)
   - Engine description (size, cylinders, configuration)
   - Exterior color (exact color name)
   - Interior color (exact color name)

2. CONDITION DATA:
   - Overall score as decimal (e.g., 4.3, 3.8)
   - Grade classification (Clean, Average, Rough)
   - Issues categorized by type:
     * exterior: body damage, paint issues, dents, scratches
     * interior: wear, tears, electronic issues, stains
     * mechanical: diagnostic codes, warning lights, fluid leaks
     * tiresWheels: tread depth, wheel damage, tire pressure

3. For EACH IMAGE visible in the PDF:
   - page_number: Which page (1-indexed)
   - description: Detailed description of what the image shows
   - vehicle_angle: EXACTLY one of [front, rear, driver_side, passenger_side,
     front_quarter, rear_quarter, interior_dash, interior_seats,
     engine, trunk, wheel, odometer, vin_plate, other]
   - quality_score: 1-10 rating of photo quality (10 = professional)
   - category: "hero" (best exterior shot), "carousel" (good supplementary),
     "detail" (close-ups/features), "documentation" (odometer, VIN, paperwork)
   - suggested_alt: Accessibility alt text for screen readers
   - visible_damage: Array of any damage visible in this specific image

4. SELLER INFORMATION:
   - name: Dealer name or individual seller name visible on document
   - type: "dealer" or "private" based on document format

Be thorough and precise. This data will be used to create vehicle listings and inform potential buyers."""

    def _get_extraction_schema(self) -> dict:
        """JSON Schema for structured output"""
        return {
            "type": "object",
            "properties": {
                "vehicle": {
                    "type": "object",
                    "properties": {
                        "vin": {"type": "string", "pattern": "^[A-HJ-NPR-Z0-9]{17}$"},
                        "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
                        "make": {"type": "string"},
                        "model": {"type": "string"},
                        "trim": {"type": "string"},
                        "odometer": {"type": "integer", "minimum": 0},
                        "drivetrain": {"type": "string"},
                        "transmission": {"type": "string"},
                        "engine": {"type": "string"},
                        "exterior_color": {"type": "string"},
                        "interior_color": {"type": "string"}
                    },
                    "required": ["vin", "year", "make", "model", "odometer"]
                },
                "condition": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 1, "maximum": 5},
                        "grade": {"type": "string", "enum": ["Clean", "Average", "Rough"]},
                        "issues": {
                            "type": "object",
                            "properties": {
                                "exterior": {"type": "array", "items": {"type": "object"}},
                                "interior": {"type": "array", "items": {"type": "object"}},
                                "mechanical": {"type": "array", "items": {"type": "object"}},
                                "tiresWheels": {"type": "array", "items": {"type": "object"}}
                            }
                        }
                    },
                    "required": ["score", "grade"]
                },
                "images": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "page_number": {"type": "integer", "minimum": 1},
                            "description": {"type": "string"},
                            "vehicle_angle": {
                                "type": "string",
                                "enum": ["front", "rear", "driver_side", "passenger_side",
                                        "front_quarter", "rear_quarter", "interior_dash",
                                        "interior_seats", "engine", "trunk", "wheel",
                                        "odometer", "vin_plate", "other"]
                            },
                            "quality_score": {"type": "integer", "minimum": 1, "maximum": 10},
                            "category": {
                                "type": "string",
                                "enum": ["hero", "carousel", "detail", "documentation"]
                            },
                            "suggested_alt": {"type": "string"},
                            "visible_damage": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["page_number", "description", "vehicle_angle",
                                   "quality_score", "category", "suggested_alt"]
                    }
                },
                "seller": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["dealer", "private"]}
                    },
                    "required": ["name", "type"]
                }
            },
            "required": ["vehicle", "condition", "images", "seller"]
        }

    async def process_and_persist_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        text_embedding: Optional[List[float]] = None,
        seller_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process PDF and persist directly to database.

        This is the main entry point for the PDF → Database pipeline.
        Combines PDF extraction with database persistence.

        Args:
            pdf_bytes: PDF file bytes
            filename: Original filename
            text_embedding: Optional text embedding for semantic search
            seller_id: Optional seller/user ID who owns this listing

        Returns:
            Dict with listing_id, vin, image_count, issue_count, status
        """
        try:
            # Step 1: Extract vehicle listing artifact from PDF
            artifact = await self.process_condition_report(pdf_bytes, filename)
            logger.info(f"Extracted artifact for VIN: {artifact.vehicle.vin}")

            # Step 2: Persist to database
            from .listing_persistence_service import get_listing_persistence_service
            persistence_service = get_listing_persistence_service()

            result = await persistence_service.persist_listing(
                artifact=artifact,
                text_embedding=text_embedding,
                seller_id=seller_id
            )

            logger.info(f"✅ Successfully processed and persisted listing {result['listing_id']}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to process and persist PDF {filename}: {e}")
            raise

    async def close(self):
        """Clean up resources"""
        await self.openrouter_client.aclose()


# Singleton instance for the application
pdf_ingestion_service = PDFIngestionService()


async def get_pdf_ingestion_service() -> PDFIngestionService:
    """Get the singleton PDF ingestion service instance"""
    return pdf_ingestion_service