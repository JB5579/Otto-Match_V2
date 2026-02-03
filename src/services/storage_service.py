"""
Otto.AI Storage Service
Handles image optimization, upload to Supabase Storage, and CDN management.
Integrates with existing Supabase infrastructure from the Otto.AI architecture.
"""

import asyncio
import io
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PIL import Image, ImageEnhance
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for image storage and optimization"""
    # Image sizes
    thumbnail_size: int = 300
    web_optimized_width: int = 1200
    detail_view_width: int = 800

    # Quality settings
    thumbnail_quality: int = 70
    web_quality: int = 80
    detail_quality: int = 85

    # Format settings
    output_format: str = "JPEG"
    enable_progressive: bool = True


class ImageProcessor:
    """Handles image optimization and format conversion"""

    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()

    def create_thumbnail(self, image_bytes: bytes) -> bytes:
        """Create optimized thumbnail image"""
        return self._resize_image(image_bytes, self.config.thumbnail_size,
                               self.config.thumbnail_quality, maintain_aspect=True)

    def create_web_optimized(self, image_bytes: bytes) -> bytes:
        """Create web-optimized version for main display"""
        return self._resize_image(image_bytes, self.config.web_optimized_width,
                               self.config.web_quality, maintain_aspect=True)

    def create_detail_view(self, image_bytes: bytes) -> bytes:
        """Create detail view optimized version"""
        return self._resize_image(image_bytes, self.config.detail_view_width,
                               self.config.detail_quality, maintain_aspect=True)

    def _resize_image(self, image_bytes: bytes, max_width: int, quality: int,
                     maintain_aspect: bool = True) -> bytes:
        """Internal method to resize and optimize images"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if necessary for JPEG output
                if img.mode in ('RGBA', 'P', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                original_width, original_height = img.size

                if maintain_aspect:
                    # Calculate new height to maintain aspect ratio
                    aspect_ratio = original_height / original_width
                    new_height = int(max_width * aspect_ratio)
                    new_size = (max_width, new_height)
                else:
                    # Fixed width, scale height proportionally
                    scale_factor = max_width / original_width
                    new_height = int(original_height * scale_factor)
                    new_size = (max_width, new_height)

                # Resize with high-quality resampling
                img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Apply subtle enhancements for better web display
                img = self._enhance_for_web(img)

                # Save with optimization
                buffer = io.BytesIO()
                save_kwargs = {
                    'format': self.config.output_format,
                    'quality': quality,
                    'optimize': True
                }

                if self.config.output_format == "JPEG" and self.config.enable_progressive:
                    save_kwargs['progressive'] = True

                img.save(buffer, **save_kwargs)
                return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            return image_bytes  # Return original if processing fails

    def _enhance_for_web(self, img: Image.Image) -> Image.Image:
        """Apply subtle enhancements for better web display"""
        try:
            # Slight sharpening for better clarity
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.05)

            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.02)

            return img
        except Exception:
            return img  # Return original if enhancement fails


class SupabaseStorageService:
    """
    Service for uploading and managing files in Supabase Storage.
    Integrates with Otto.AI's existing Supabase infrastructure.
    """

    def __init__(self):
        self.supabase_url = self._get_env_var('SUPABASE_URL')
        self.supabase_service_key = self._get_env_var('SUPABASE_SERVICE_ROLE_KEY')
        self.storage_bucket = self._get_env_var('SUPABASE_STORAGE_BUCKET', 'vehicle-images')

        self.client = httpx.AsyncClient(
            base_url=self.supabase_url,
            headers={
                "Authorization": f"Bearer {self.supabase_service_key}",
                "apikey": self.supabase_service_key
            },
            timeout=30.0
        )

        self.image_processor = ImageProcessor()

    def _get_env_var(self, var_name: str, default: str = None) -> str:
        """Get environment variable with helpful error if missing"""
        import os
        value = os.getenv(var_name, default)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required")
        return value

    async def upload_vehicle_image(
        self,
        image_bytes: bytes,
        filename: str,
        optimize: bool = True,
        create_variants: bool = True
    ) -> Dict[str, Any]:
        """
        Upload vehicle image with optimization and CDN distribution.

        Args:
            image_bytes: Raw image data
            filename: Unique filename for the image
            optimize: Whether to create web-optimized versions
            create_variants: Whether to create thumbnail and detail versions

        Returns:
            Dict with URLs for different image variants
        """
        try:
            # Generate unique storage path
            storage_path = f"vehicles/{datetime.utcnow().strftime('%Y/%m')}/{filename}"

            upload_results = {}

            if optimize:
                # Create web-optimized version
                web_optimized = self.image_processor.create_web_optimized(image_bytes)
                web_url = await self._upload_file(web_optimized, f"{storage_path}_web")
                upload_results['web_url'] = web_url

                if create_variants:
                    # Create thumbnail
                    thumbnail = self.image_processor.create_thumbnail(image_bytes)
                    thumbnail_url = await self._upload_file(thumbnail, f"{storage_path}_thumb")
                    upload_results['thumbnail_url'] = thumbnail_url

                    # Create detail view
                    detail = self.image_processor.create_detail_view(image_bytes)
                    detail_url = await self._upload_file(detail, f"{storage_path}_detail")
                    upload_results['detail_url'] = detail_url
            else:
                # Upload original without optimization
                original_url = await self._upload_file(image_bytes, storage_path)
                upload_results['original_url'] = original_url

            logger.info(f"Successfully uploaded image variants: {list(upload_results.keys())}")
            return upload_results

        except Exception as e:
            logger.error(f"Failed to upload vehicle image {filename}: {str(e)}")
            raise

    async def _upload_file(self, file_bytes: bytes, storage_path: str) -> str:
        """Upload file to Supabase Storage and return public URL"""
        try:
            # Upload file
            response = await self.client.post(
                f"/storage/v1/object/{self.storage_bucket}/{storage_path}",
                headers={
                    "Content-Type": "image/jpeg"
                },
                content=file_bytes
            )
            response.raise_for_status()

            # Get public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{self.storage_bucket}/{storage_path}"

            logger.info(f"Uploaded file to {storage_path}")
            return public_url

        except httpx.HTTPStatusError as e:
            logger.error(f"Upload failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            raise

    async def create_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Create signed URL for temporary access to private files"""
        try:
            response = await self.client.post(
                "/storage/v1/object/sign",
                json={
                    "bucketId": self.storage_bucket,
                    "object": storage_path,
                    "expiresIn": expires_in
                }
            )
            response.raise_for_status()

            data = response.json()
            return data.get('signedUrl')

        except Exception as e:
            logger.error(f"Failed to create signed URL for {storage_path}: {str(e)}")
            raise

    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        try:
            response = await self.client.delete(
                f"/storage/v1/object/{self.storage_bucket}/{storage_path}"
            )
            response.raise_for_status()

            logger.info(f"Deleted file: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {str(e)}")
            return False

    async def batch_upload_images(
        self,
        images: List[Dict[str, Any]],  # Each dict should have 'bytes' and 'filename'
        optimize: bool = True
    ) -> List[Dict[str, Any]]:
        """Upload multiple images concurrently"""
        tasks = [
            self.upload_vehicle_image(
                img['bytes'],
                img['filename'],
                optimize=optimize
            )
            for img in images
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        successful_uploads = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to upload image {i}: {str(result)}")
                successful_uploads.append({"error": str(result)})
            else:
                successful_uploads.append(result)

        return successful_uploads

    async def close(self):
        """Clean up resources"""
        await self.client.aclose()


# Singleton instance for the application
storage_service = SupabaseStorageService()


async def get_storage_service() -> SupabaseStorageService:
    """Get the singleton storage service instance"""
    return storage_service