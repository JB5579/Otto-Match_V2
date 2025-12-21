"""
Otto.AI Listings API
FastAPI endpoints for PDF ingestion and vehicle listing management.
Integrates with PDFIngestionService to provide complete listing creation workflow.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services.pdf_ingestion_service import get_pdf_ingestion_service, VehicleListingArtifact
from ..services.storage_service import get_storage_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for listings endpoints
listings_router = APIRouter(prefix="/api/listings", tags=["listings"])


# Pydantic models for API requests/responses
class ListingUploadResponse(BaseModel):
    """Response model for successful listing upload"""
    success: bool
    listing_id: str
    vin: str
    vehicle_info: Dict[str, Any]
    image_count: int
    processing_time: float
    message: str


class ListingSummary(BaseModel):
    """Summary model for listing listings"""
    listing_id: str
    vin: str
    year_make_model: str
    odometer: int
    exterior_color: str
    interior_color: str
    condition_score: float
    primary_image_url: str
    created_at: datetime
    status: str


class ProcessingStatus(BaseModel):
    """Processing status for async operations"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None


# In-memory task storage (in production, use Redis or database)
processing_tasks: Dict[str, ProcessingStatus] = {}


@listings_router.post("/upload", response_model=ListingUploadResponse)
async def upload_condition_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Vehicle condition report PDF"),
    seller_id: Optional[str] = Query(None, description="Seller identifier"),
    priority: str = Query("normal", description="Processing priority"),
    async_processing: bool = Query(False, description="Process asynchronously")
):
    """
    Upload and process a vehicle condition report PDF.

    This endpoint accepts a condition report PDF and processes it using:
    1. OpenRouter/Gemini for intelligent data extraction
    2. PyMuPDF for image extraction
    3. Supabase Storage for optimized image hosting
    4. RAG-Anything for semantic search integration

    Returns a complete vehicle listing ready for display.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        # Read PDF file
        pdf_bytes = await file.read()
        file_size = len(pdf_bytes)

        logger.info(f"Processing PDF upload: {file.filename} ({file_size:,} bytes)")

        if async_processing:
            # Process asynchronously
            task_id = f"task_{datetime.utcnow().timestamp()}_{file.filename}"

            processing_tasks[task_id] = ProcessingStatus(
                task_id=task_id,
                status="pending",
                progress=0.0,
                message="Task queued for processing"
            )

            background_tasks.add_task(
                process_pdf_async,
                task_id,
                pdf_bytes,
                file.filename,
                seller_id
            )

            return ListingUploadResponse(
                success=True,
                listing_id=task_id,
                vin="processing",
                vehicle_info={},
                image_count=0,
                processing_time=0.0,
                message=f"PDF upload queued for processing. Task ID: {task_id}"
            )
        else:
            # Process synchronously
            return await process_pdf_sync(pdf_bytes, file.filename, seller_id)

    except Exception as e:
        logger.error(f"Failed to process PDF upload {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


async def process_pdf_sync(
    pdf_bytes: bytes,
    filename: str,
    seller_id: Optional[str]
) -> ListingUploadResponse:
    """Process PDF synchronously and return immediate results"""
    start_time = datetime.utcnow()

    try:
        # Get services
        pdf_service = await get_pdf_ingestion_service()
        storage_service = await get_storage_service()

        # Process PDF
        logger.info(f"Starting PDF processing for {filename}")
        artifact = await pdf_service.process_condition_report(pdf_bytes, filename)

        # Upload images to storage
        logger.info(f"Uploading {len(artifact.images)} images to storage")
        upload_tasks = []
        for i, image in enumerate(artifact.images):
            # Generate unique filename
            hash_prefix = hashlib.md5(image.image_bytes[:1024]).hexdigest()[:8]
            filename = f"{artifact.vehicle.vin}_{image.vehicle_angle}_{hash_prefix}.{image.format}"

            task = storage_service.upload_vehicle_image(
                image.image_bytes,
                filename,
                optimize=True,
                create_variants=True
            )
            upload_tasks.append(task)

        # Wait for all image uploads
        upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)

        # Update image URLs in artifact
        for i, (image, result) in enumerate(zip(artifact.images, upload_results)):
            if isinstance(result, Exception):
                logger.error(f"Failed to upload image {i}: {str(result)}")
                continue

            image.storage_url = result.get('web_url')
            image.thumbnail_url = result.get('thumbnail_url')

        # Generate listing ID (using VIN as base)
        listing_id = f"listing_{artifact.vehicle.vin}_{int(start_time.timestamp())}"

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"Successfully processed {filename}: VIN {artifact.vehicle.vin}")

        return ListingUploadResponse(
            success=True,
            listing_id=listing_id,
            vin=artifact.vehicle.vin,
            vehicle_info=artifact.vehicle.dict(),
            image_count=len(artifact.images),
            processing_time=processing_time,
            message="PDF processed successfully"
        )

    except Exception as e:
        logger.error(f"Synchronous processing failed for {filename}: {str(e)}")
        raise


async def process_pdf_async(
    task_id: str,
    pdf_bytes: bytes,
    filename: str,
    seller_id: Optional[str]
):
    """Process PDF asynchronously and update task status"""
    try:
        # Update status to processing
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="processing",
            progress=10.0,
            message="Starting PDF analysis..."
        )

        # Process PDF
        pdf_service = await get_pdf_ingestion_service()
        artifact = await pdf_service.process_condition_report(pdf_bytes, filename)

        # Update progress
        processing_tasks[task_id].progress = 50.0
        processing_tasks[task_id].message = "PDF analysis complete, uploading images..."

        # Upload images
        storage_service = await get_storage_service()
        upload_tasks = []
        for image in artifact.images:
            hash_prefix = hashlib.md5(image.image_bytes[:1024]).hexdigest()[:8]
            filename = f"{artifact.vehicle.vin}_{image.vehicle_angle}_{hash_prefix}.{image.format}"
            upload_tasks.append(
                storage_service.upload_vehicle_image(
                    image.image_bytes,
                    filename,
                    optimize=True,
                    create_variants=True
                )
            )

        # Wait for uploads
        upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)

        # Update image URLs
        for image, result in zip(artifact.images, upload_results):
            if isinstance(result, Exception):
                continue
            image.storage_url = result.get('web_url')
            image.thumbnail_url = result.get('thumbnail_url')

        # Generate listing ID
        listing_id = f"listing_{artifact.vehicle.vin}_{int(datetime.utcnow().timestamp())}"

        # Update final status
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="completed",
            progress=100.0,
            message="Processing completed successfully",
            result={
                "listing_id": listing_id,
                "vin": artifact.vehicle.vin,
                "vehicle_info": artifact.vehicle.dict(),
                "image_count": len(artifact.images),
                "artifact": artifact.dict()  # Full artifact for frontend consumption
            }
        )

        logger.info(f"Async processing completed for task {task_id}")

    except Exception as e:
        logger.error(f"Async processing failed for task {task_id}: {str(e)}")
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="failed",
            progress=0.0,
            message=f"Processing failed: {str(e)}"
        )


@listings_router.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str):
    """Get the status of an async processing task"""
    if task_id not in processing_tasks:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return processing_tasks[task_id]


@listings_router.get("/{listing_id}")
async def get_listing(listing_id: str):
    """Get detailed information for a specific listing"""
    # TODO: Implement listing retrieval from database
    # For now, return placeholder
    return {
        "listing_id": listing_id,
        "message": "Listing retrieval not yet implemented",
        "status": "placeholder"
    }


@listings_router.get("/", response_model=List[ListingSummary])
async def list_listings(
    limit: int = Query(20, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Number of listings to skip"),
    make: Optional[str] = Query(None, description="Filter by vehicle make"),
    model: Optional[str] = Query(None, description="Filter by vehicle model"),
    year_min: Optional[int] = Query(None, description="Minimum year"),
    year_max: Optional[int] = Query(None, description="Maximum year"),
    price_min: Optional[int] = Query(None, description="Minimum price"),
    price_max: Optional[int] = Query(None, description="Maximum price")
):
    """
    Get a paginated list of vehicle listings with optional filtering.

    This endpoint will connect to the database to return existing listings.
    For now, returns placeholder data.
    """
    # TODO: Implement database query with filters
    placeholder_listings = [
        ListingSummary(
            listing_id="placeholder_1",
            vin="1HGBH41JXMN109186",
            year_make_model="2021 Honda Civic",
            odometer=15000,
            exterior_color="Silver",
            interior_color="Black",
            condition_score=4.2,
            primary_image_url="/placeholder-image.jpg",
            created_at=datetime.utcnow(),
            status="available"
        )
    ]

    return placeholder_listings[:limit]


@listings_router.delete("/{listing_id}")
async def delete_listing(listing_id: str):
    """Delete a vehicle listing"""
    # TODO: Implement listing deletion from database
    return {"message": f"Listing {listing_id} deletion not yet implemented"}


@listings_router.post("/{listing_id}/favorite")
async def favorite_listing(listing_id: str):
    """Add a listing to user favorites"""
    # TODO: Implement favorites functionality
    return {"message": f"Favorites for listing {listing_id} not yet implemented"}


@listings_router.get("/{listing_id}/similar")
async def get_similar_listings(
    listing_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of similar listings")
):
    """Get similar vehicle listings based on semantic similarity"""
    # TODO: Implement similarity search using RAG-Anything embeddings
    return {"message": f"Similar listings for {listing_id} not yet implemented"}


# Health check endpoint
@listings_router.get("/health", tags=["health"])
async def health_check():
    """Health check for listings API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "listings_api",
        "version": "1.0.0"
    }


# Import for hashing
import hashlib