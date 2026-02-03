"""
Otto.AI Listings API
FastAPI endpoints for PDF ingestion and vehicle listing management.
Integrates with PDFIngestionService to provide complete listing creation workflow.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services.pdf_ingestion_service import get_pdf_ingestion_service, VehicleListingArtifact
from ..services.storage_service import get_storage_service
from ..services.vehicle_embedding_service import VehicleEmbeddingService, process_listing_for_search
from ..semantic.embedding_service import OttoAIEmbeddingService
from ..repositories.listing_repository import get_listing_repository, ListingUpdate
from ..repositories.image_repository import get_image_repository

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


class BatchFileStatus(BaseModel):
    """Status for individual file in a batch"""
    filename: str
    status: str  # queued, processing, completed, failed
    progress: float
    message: str
    listing_id: Optional[str] = None
    vin: Optional[str] = None
    error: Optional[str] = None


class BatchUploadResponse(BaseModel):
    """Response for batch upload initiation"""
    success: bool
    batch_id: str
    total_files: int
    message: str


class BatchStatus(BaseModel):
    """Complete batch processing status"""
    batch_id: str
    status: str  # queued, processing, completed, partial, failed
    total_files: int
    completed: int
    failed: int
    in_progress: int
    queued: int
    progress: float  # Overall progress 0-100
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    files: List[BatchFileStatus]
    seller_id: Optional[str] = None


# In-memory task storage (in production, use Redis or database)
processing_tasks: Dict[str, ProcessingStatus] = {}

# Batch processing storage
batch_jobs: Dict[str, BatchStatus] = {}


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


@listings_router.post("/upload/bulk", response_model=BatchUploadResponse)
async def upload_condition_reports_bulk(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple vehicle condition report PDFs"),
    seller_id: Optional[str] = Query(None, description="Seller identifier"),
    max_concurrent: int = Query(3, ge=1, le=10, description="Max concurrent processing jobs")
):
    """
    Upload and process multiple vehicle condition report PDFs in batch.

    This endpoint accepts multiple PDF files and queues them for asynchronous processing.
    Use the batch status endpoint to monitor progress.

    - **files**: List of PDF files to upload (max 50 per batch)
    - **seller_id**: Optional seller identifier to associate with all listings
    - **max_concurrent**: Maximum number of PDFs to process simultaneously (1-10)

    Returns a batch_id that can be used to track processing status.
    """
    # Validate file count
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 files per batch upload"
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="No files provided"
        )

    # Validate all files are PDFs
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported. Invalid file: {file.filename}"
            )

    try:
        # Generate batch ID
        batch_id = f"batch_{int(datetime.utcnow().timestamp())}_{len(files)}"

        # Read all PDF bytes upfront
        pdf_data_list = []
        for file in files:
            pdf_bytes = await file.read()
            pdf_data_list.append({
                'filename': file.filename,
                'bytes': pdf_bytes,
                'size': len(pdf_bytes)
            })

        # Initialize batch status
        file_statuses = [
            BatchFileStatus(
                filename=pdf['filename'],
                status='queued',
                progress=0.0,
                message='Queued for processing'
            )
            for pdf in pdf_data_list
        ]

        batch_jobs[batch_id] = BatchStatus(
            batch_id=batch_id,
            status='queued',
            total_files=len(files),
            completed=0,
            failed=0,
            in_progress=0,
            queued=len(files),
            progress=0.0,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            files=file_statuses,
            seller_id=seller_id
        )

        logger.info(f"Created batch job {batch_id} with {len(files)} files")

        # Start batch processing in background
        background_tasks.add_task(
            process_batch_async,
            batch_id,
            pdf_data_list,
            seller_id,
            max_concurrent
        )

        return BatchUploadResponse(
            success=True,
            batch_id=batch_id,
            total_files=len(files),
            message=f"Batch upload queued. {len(files)} files will be processed. Use GET /api/listings/batch/{batch_id} to monitor progress."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create batch upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create batch upload: {str(e)}"
        )


async def process_batch_async(
    batch_id: str,
    pdf_data_list: List[Dict[str, Any]],
    seller_id: Optional[str],
    max_concurrent: int
):
    """
    Process a batch of PDFs asynchronously with concurrency control.

    Uses a semaphore to limit concurrent processing and updates batch status
    as each file completes.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    # Update batch status to processing
    batch_jobs[batch_id].status = 'processing'
    batch_jobs[batch_id].updated_at = datetime.utcnow()

    async def process_single_pdf(index: int, pdf_data: Dict[str, Any]):
        """Process a single PDF with semaphore control"""
        async with semaphore:
            filename = pdf_data['filename']
            pdf_bytes = pdf_data['bytes']

            # Update status to processing
            batch_jobs[batch_id].files[index].status = 'processing'
            batch_jobs[batch_id].files[index].message = 'Processing PDF...'
            batch_jobs[batch_id].in_progress += 1
            batch_jobs[batch_id].queued -= 1
            batch_jobs[batch_id].updated_at = datetime.utcnow()
            _update_batch_progress(batch_id)

            try:
                # Process the PDF
                result = await process_pdf_for_batch(pdf_bytes, filename, seller_id)

                # Update status to completed
                batch_jobs[batch_id].files[index].status = 'completed'
                batch_jobs[batch_id].files[index].progress = 100.0
                batch_jobs[batch_id].files[index].message = 'Successfully processed'
                batch_jobs[batch_id].files[index].listing_id = result.get('listing_id')
                batch_jobs[batch_id].files[index].vin = result.get('vin')
                batch_jobs[batch_id].completed += 1
                batch_jobs[batch_id].in_progress -= 1

                logger.info(f"Batch {batch_id}: Completed {filename} -> {result.get('listing_id')}")

            except Exception as e:
                # Update status to failed
                batch_jobs[batch_id].files[index].status = 'failed'
                batch_jobs[batch_id].files[index].progress = 0.0
                batch_jobs[batch_id].files[index].message = 'Processing failed'
                batch_jobs[batch_id].files[index].error = str(e)
                batch_jobs[batch_id].failed += 1
                batch_jobs[batch_id].in_progress -= 1

                logger.error(f"Batch {batch_id}: Failed {filename}: {str(e)}")

            batch_jobs[batch_id].updated_at = datetime.utcnow()
            _update_batch_progress(batch_id)

    # Create tasks for all PDFs
    tasks = [
        process_single_pdf(i, pdf_data)
        for i, pdf_data in enumerate(pdf_data_list)
    ]

    # Wait for all to complete
    await asyncio.gather(*tasks, return_exceptions=True)

    # Update final batch status
    batch = batch_jobs[batch_id]
    if batch.failed == 0:
        batch.status = 'completed'
    elif batch.completed == 0:
        batch.status = 'failed'
    else:
        batch.status = 'partial'

    batch.completed_at = datetime.utcnow()
    batch.updated_at = datetime.utcnow()
    batch.progress = 100.0

    logger.info(f"Batch {batch_id} finished: {batch.completed} completed, {batch.failed} failed")


async def process_pdf_for_batch(
    pdf_bytes: bytes,
    filename: str,
    seller_id: Optional[str]
) -> Dict[str, Any]:
    """
    Process a single PDF as part of a batch.
    Returns dict with listing_id and vin on success.
    """
    start_time = datetime.utcnow()

    # Get services
    pdf_service = await get_pdf_ingestion_service()
    storage_service = await get_storage_service()

    # Process PDF
    artifact = await pdf_service.process_condition_report(pdf_bytes, filename)

    # Upload images to storage
    upload_tasks = []
    for image in artifact.images:
        hash_prefix = hashlib.md5(image.image_bytes[:1024]).hexdigest()[:8]
        img_filename = f"{artifact.vehicle.vin}_{image.vehicle_angle}_{hash_prefix}.{image.format}"
        upload_tasks.append(
            storage_service.upload_vehicle_image(
                image.image_bytes,
                img_filename,
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

    # Add processing metadata
    artifact.processing_metadata = {
        'filename': filename,
        'seller_id': seller_id,
        'processed_at': start_time.isoformat(),
        'batch_processing': True
    }

    # Persist to database with embeddings
    embedding_service = OttoAIEmbeddingService()
    embedding_result = await process_listing_for_search(artifact, embedding_service)
    listing_id = embedding_result.get('listing_id', f"listing_{artifact.vehicle.vin}")

    return {
        'listing_id': listing_id,
        'vin': artifact.vehicle.vin,
        'processing_time': (datetime.utcnow() - start_time).total_seconds()
    }


def _update_batch_progress(batch_id: str):
    """Update overall batch progress percentage"""
    batch = batch_jobs[batch_id]
    total = batch.total_files
    completed = batch.completed + batch.failed
    batch.progress = (completed / total) * 100 if total > 0 else 0


@listings_router.get("/batch/{batch_id}", response_model=BatchStatus)
async def get_batch_status(batch_id: str):
    """
    Get the status of a batch upload job.

    Returns detailed status for the batch including:
    - Overall progress and status
    - Individual file statuses
    - Listing IDs for completed files
    - Error messages for failed files
    """
    if batch_id not in batch_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Batch job {batch_id} not found"
        )

    return batch_jobs[batch_id]


@listings_router.get("/batch", response_model=List[BatchStatus])
async def list_batch_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of batches to return")
):
    """
    List all batch upload jobs.

    Optionally filter by status: queued, processing, completed, partial, failed
    """
    batches = list(batch_jobs.values())

    # Filter by status if provided
    if status:
        batches = [b for b in batches if b.status == status]

    # Sort by started_at descending (newest first)
    batches.sort(key=lambda b: b.started_at, reverse=True)

    return batches[:limit]


async def process_pdf_sync(
    pdf_bytes: bytes,
    filename: str,
    seller_id: Optional[str]
) -> ListingUploadResponse:
    """Process PDF synchronously, persist to database, and return results"""
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
            img_filename = f"{artifact.vehicle.vin}_{image.vehicle_angle}_{hash_prefix}.{image.format}"

            task = storage_service.upload_vehicle_image(
                image.image_bytes,
                img_filename,
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

        # Add processing metadata
        artifact.processing_metadata = {
            'filename': filename,
            'seller_id': seller_id,
            'processed_at': start_time.isoformat(),
            'processing_time': (datetime.utcnow() - start_time).total_seconds()
        }

        # Persist to database with embeddings
        logger.info(f"Persisting listing to database for VIN {artifact.vehicle.vin}")
        try:
            embedding_service = OttoAIEmbeddingService()
            embedding_result = await process_listing_for_search(artifact, embedding_service)
            listing_id = embedding_result.get('listing_id', f"listing_{artifact.vehicle.vin}")
            logger.info(f"✅ Listing persisted with ID: {listing_id}")
        except Exception as emb_error:
            logger.error(f"Failed to persist listing to database: {emb_error}")
            # Fallback to temporary listing ID if persistence fails
            listing_id = f"temp_{artifact.vehicle.vin}_{int(start_time.timestamp())}"

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"Successfully processed {filename}: VIN {artifact.vehicle.vin}")

        return ListingUploadResponse(
            success=True,
            listing_id=listing_id,
            vin=artifact.vehicle.vin,
            vehicle_info=artifact.vehicle.dict(),
            image_count=len(artifact.images),
            processing_time=processing_time,
            message="PDF processed and persisted to database successfully"
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
    """Process PDF asynchronously, persist to database, and update task status"""
    try:
        start_time = datetime.utcnow()

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
            img_filename = f"{artifact.vehicle.vin}_{image.vehicle_angle}_{hash_prefix}.{image.format}"
            upload_tasks.append(
                storage_service.upload_vehicle_image(
                    image.image_bytes,
                    img_filename,
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

        # Update progress
        processing_tasks[task_id].progress = 75.0
        processing_tasks[task_id].message = "Images uploaded, persisting to database..."

        # Add processing metadata
        artifact.processing_metadata = {
            'filename': filename,
            'seller_id': seller_id,
            'task_id': task_id,
            'processed_at': start_time.isoformat()
        }

        # Persist to database with embeddings
        try:
            embedding_service = OttoAIEmbeddingService()
            embedding_result = await process_listing_for_search(artifact, embedding_service)
            listing_id = embedding_result.get('listing_id', f"listing_{artifact.vehicle.vin}")
            logger.info(f"✅ Listing persisted with ID: {listing_id}")
        except Exception as emb_error:
            logger.error(f"Failed to persist listing to database: {emb_error}")
            listing_id = f"temp_{artifact.vehicle.vin}_{int(datetime.utcnow().timestamp())}"

        # Update final status
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="completed",
            progress=100.0,
            message="Processing and persistence completed successfully",
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


class ListingDetail(BaseModel):
    """Full listing detail response model"""
    id: str
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    odometer: int
    drivetrain: str
    transmission: str
    engine: str
    exterior_color: str
    interior_color: str
    condition_score: float
    condition_grade: str
    description_text: Optional[str] = None
    status: str
    listing_source: str
    created_at: datetime
    updated_at: datetime
    images: List[Dict[str, Any]] = []
    condition_issues: List[Dict[str, Any]] = []


@listings_router.get("/{listing_id}", response_model=ListingDetail)
async def get_listing(listing_id: str):
    """Get detailed information for a specific listing including images and condition issues"""
    try:
        listing_repo = get_listing_repository()
        image_repo = get_image_repository()

        # Get listing
        listing = await listing_repo.get_by_id(listing_id)

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Get images for this listing
        images = await image_repo.get_by_listing(listing_id)

        # Get condition issues
        from ..services.supabase_client import get_supabase_client_singleton
        supabase = get_supabase_client_singleton()
        issues_result = supabase.table('vehicle_condition_issues') \
            .select('*') \
            .eq('listing_id', listing_id) \
            .execute()
        condition_issues = issues_result.data if issues_result.data else []

        return ListingDetail(
            id=listing['id'],
            vin=listing['vin'],
            year=listing['year'],
            make=listing['make'],
            model=listing['model'],
            trim=listing.get('trim'),
            odometer=listing['odometer'],
            drivetrain=listing['drivetrain'],
            transmission=listing['transmission'],
            engine=listing['engine'],
            exterior_color=listing['exterior_color'],
            interior_color=listing['interior_color'],
            condition_score=listing['condition_score'],
            condition_grade=listing['condition_grade'],
            description_text=listing.get('description_text'),
            status=listing['status'],
            listing_source=listing['listing_source'],
            created_at=listing['created_at'],
            updated_at=listing['updated_at'],
            images=images,
            condition_issues=condition_issues
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@listings_router.get("/", response_model=List[ListingSummary])
async def list_listings(
    limit: int = Query(20, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Number of listings to skip"),
    make: Optional[str] = Query(None, description="Filter by vehicle make"),
    model: Optional[str] = Query(None, description="Filter by vehicle model"),
    year_min: Optional[int] = Query(None, description="Minimum year"),
    year_max: Optional[int] = Query(None, description="Maximum year"),
    price_min: Optional[int] = Query(None, description="Minimum price"),
    price_max: Optional[int] = Query(None, description="Maximum price"),
    status: str = Query("active", description="Listing status filter")
):
    """
    Get a paginated list of vehicle listings with optional filtering.

    Returns real vehicle listings from the database with images.
    """
    try:
        listing_repo = get_listing_repository()
        image_repo = get_image_repository()

        # Query listings from database
        listings = await listing_repo.list_all(
            limit=limit,
            offset=offset,
            make=make,
            model=model,
            year_min=year_min,
            year_max=year_max,
            status=status
        )

        # Build summary responses with primary images
        summaries = []
        for listing in listings:
            # Get hero image for this listing
            hero_image = await image_repo.get_hero_image(listing['id'])
            primary_image_url = hero_image.get('web_url', '') if hero_image else ''

            # Get image count
            image_count = await image_repo.count_by_listing(listing['id'])

            summaries.append(ListingSummary(
                listing_id=listing['id'],
                vin=listing['vin'],
                year_make_model=f"{listing['year']} {listing['make']} {listing['model']}",
                odometer=listing['odometer'],
                exterior_color=listing['exterior_color'],
                interior_color=listing['interior_color'],
                condition_score=listing['condition_score'],
                primary_image_url=primary_image_url,
                created_at=listing['created_at'],
                status=listing['status']
            ))

        return summaries

    except Exception as e:
        logger.error(f"Failed to list listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@listings_router.delete("/{listing_id}")
async def delete_listing(listing_id: str):
    """Delete a vehicle listing (soft delete - sets status to inactive)"""
    try:
        listing_repo = get_listing_repository()

        # Soft delete the listing
        success = await listing_repo.delete(listing_id)

        if not success:
            raise HTTPException(status_code=404, detail="Listing not found")

        return {"success": True, "message": f"Listing {listing_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete listing {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@listings_router.post("/{listing_id}/favorite")
async def favorite_listing(listing_id: str):
    """Add a listing to user favorites"""
    # TODO: Implement favorites functionality
    return {"message": f"Favorites for listing {listing_id} not yet implemented"}


class SimilarListing(BaseModel):
    """Response model for similar listing results"""
    listing_id: str
    vin: str
    year: int
    make: str
    model: str
    odometer: int
    condition_score: float
    similarity_score: float
    primary_image_url: Optional[str] = None


@listings_router.get("/{listing_id}/similar", response_model=List[SimilarListing])
async def get_similar_listings(
    listing_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of similar listings")
):
    """Get similar vehicle listings based on semantic similarity using pgvector"""
    try:
        listing_repo = get_listing_repository()
        image_repo = get_image_repository()

        # Get the source listing to get its embedding
        listing = await listing_repo.get_by_id(listing_id)

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Get the text embedding from the listing
        text_embedding = listing.get('text_embedding')

        if not text_embedding:
            # If no embedding, return empty result
            return []

        # Parse embedding if stored as string
        if isinstance(text_embedding, str):
            import ast
            text_embedding = ast.literal_eval(text_embedding)

        # Find similar listings using pgvector
        similar_listings = await listing_repo.find_similar(
            embedding=text_embedding,
            limit=limit,
            exclude_id=listing_id
        )

        # Build response with images
        results = []
        for similar in similar_listings:
            hero_image = await image_repo.get_hero_image(similar['id'])
            primary_image_url = hero_image.get('web_url', '') if hero_image else ''

            results.append(SimilarListing(
                listing_id=similar['id'],
                vin=similar['vin'],
                year=similar['year'],
                make=similar['make'],
                model=similar['model'],
                odometer=similar['odometer'],
                condition_score=similar['condition_score'],
                similarity_score=similar.get('similarity', 0.0),
                primary_image_url=primary_image_url
            ))

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get similar listings for {listing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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