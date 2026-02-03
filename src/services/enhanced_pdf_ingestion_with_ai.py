"""
Otto.AI Enhanced PDF Ingestion with AI Intelligence

Extends the PDF ingestion pipeline to automatically fetch AI intelligence
after vehicle data extraction using Groq Compound AI.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .pdf_ingestion_service import (
    PDFIngestionService,
    VehicleListingArtifact
)
from .vehicle_intelligence_service import (
    VehicleIntelligenceService,
    VehicleIntelligence
)
from .ai_intelligence_database_service import (
    AIIntelligenceDatabaseService
)

logger = logging.getLogger(__name__)


class EnhancedPDFIngestionWithAI:
    """
    Enhanced PDF ingestion service that adds AI intelligence
    to the standard PDF processing pipeline.
    """

    def __init__(self):
        self.pdf_service = PDFIngestionService()
        self.ai_service = VehicleIntelligenceService()
        self.db_service = AIIntelligenceDatabaseService()
        self._ai_processing_enabled = True  # Can be toggled for testing

    async def process_condition_report_with_ai(
        self,
        pdf_bytes: bytes,
        filename: str,
        force_refresh_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Process PDF and automatically fetch AI intelligence.

        Returns a combined artifact containing both the standard PDF
        extraction results and the AI intelligence data.
        """

        logger.info(f"Starting enhanced PDF processing with AI for {filename}")
        start_time = datetime.now()

        try:
            # Step 1: Standard PDF processing (extract vehicle data)
            logger.info("Step 1: Processing PDF with standard pipeline...")
            pdf_artifact = await self.pdf_service.process_condition_report(
                pdf_bytes=pdf_bytes,
                filename=filename
            )

            # Step 2: Extract key vehicle info for AI processing
            vehicle_info = pdf_artifact.vehicle
            features = self._extract_vehicle_features(pdf_artifact)

            # Step 3: Fetch AI intelligence (async with retry logic)
            ai_intelligence = None
            ai_error = None

            if self._ai_processing_enabled:
                logger.info("Step 2: Fetching AI intelligence...")
                try:
                    ai_intelligence = await self._get_intelligence_with_retry(
                        make=vehicle_info.make,
                        model=vehicle_info.model,
                        year=vehicle_info.year,
                        vin=vehicle_info.vin,
                        features=features,
                        current_price=Decimal(str(vehicle_info.odometer)),  # Using odometer as proxy for now
                        force_refresh=force_refresh_ai
                    )

                    logger.info(f"AI intelligence fetched with confidence: {ai_intelligence.confidence_overall:.2f}")

                except Exception as e:
                    logger.error(f"Failed to fetch AI intelligence: {str(e)}")
                    ai_error = str(e)
                    ai_intelligence = self._create_placeholder_intelligence(
                        make=vehicle_info.make,
                        model=vehicle_info.model,
                        year=vehicle_info.year,
                        vin=vehicle_info.vin,
                        error=e
                    )
            else:
                logger.info("AI processing disabled, skipping intelligence fetch")
                ai_intelligence = None

            # Step 4: Create combined response
            processing_time = (datetime.now() - start_time).total_seconds()

            combined_result = {
                # Standard PDF extraction
                "vehicle": {
                    "vin": vehicle_info.vin,
                    "year": vehicle_info.year,
                    "make": vehicle_info.make,
                    "model": vehicle_info.model,
                    "trim": vehicle_info.trim,
                    "odometer": vehicle_info.odometer,
                    "drivetrain": vehicle_info.drivetrain,
                    "transmission": vehicle_info.transmission,
                    "engine": vehicle_info.engine,
                    "exterior_color": vehicle_info.exterior_color,
                    "interior_color": vehicle_info.interior_color
                },
                "condition": {
                    "score": pdf_artifact.condition.score,
                    "grade": pdf_artifact.condition.grade,
                    "issues": pdf_artifact.condition.issues
                },
                "images": [
                    {
                        "description": img.description,
                        "category": img.category,
                        "quality_score": img.quality_score,
                        "vehicle_angle": img.vehicle_angle,
                        "suggested_alt": img.suggested_alt,
                        "visible_damage": img.visible_damage,
                        "page_number": img.page_number
                    }
                    for img in pdf_artifact.images
                ],
                "seller": {
                    "name": pdf_artifact.seller.name,
                    "type": pdf_artifact.seller.type
                },

                # AI Intelligence
                "ai_intelligence": self._convert_intelligence_to_dict(ai_intelligence) if ai_intelligence else None,
                "ai_error": ai_error,

                # Processing metadata
                "processing_metadata": {
                    "filename": filename,
                    "total_processing_time": processing_time,
                    "pdf_processing_time": pdf_artifact.processing_metadata.get("processing_time", 0),
                    "ai_processing_time": processing_time - pdf_artifact.processing_metadata.get("processing_time", 0),
                    "images_extracted": len(pdf_artifact.images),
                    "ai_confidence": ai_intelligence.confidence_overall if ai_intelligence else 0.0,
                    "ai_model_used": ai_intelligence.ai_model_used if ai_intelligence else None,
                    "ai_enabled": self._ai_processing_enabled
                },

                # Success flags
                "pdf_extraction_success": True,
                "ai_intelligence_success": ai_error is None
            }

            logger.info(f"Successfully processed {filename} with AI in {processing_time:.2f}s")
            return combined_result

        except Exception as e:
            logger.error(f"Enhanced PDF processing failed for {filename}: {str(e)}")
            # Return error response but preserve partial data if available
            return {
                "error": str(e),
                "filename": filename,
                "pdf_extraction_success": False,
                "ai_intelligence_success": False,
                "processing_metadata": {
                    "total_processing_time": (datetime.now() - start_time).total_seconds(),
                    "ai_enabled": self._ai_processing_enabled
                }
            }

    async def _get_intelligence_with_retry(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str],
        features: List[str],
        current_price: Optional[Decimal],
        force_refresh: bool,
        max_retries: int = 2
    ) -> VehicleIntelligence:
        """Get AI intelligence with retry logic and fallback strategies"""

        for attempt in range(max_retries + 1):
            try:
                # Check cache first (unless force refresh)
                if not force_refresh:
                    cached = await self.db_service.get_intelligence_from_cache(
                        make=make,
                        model=model,
                        year=year,
                        vin=vin
                    )

                    if cached:
                        logger.info(f"Using cached AI intelligence for {year} {make} {model}")
                        return self._convert_cache_to_intelligence(cached)

                # Fetch fresh intelligence
                intelligence = await self.ai_service.get_vehicle_intelligence(
                    make=make,
                    model=model,
                    year=year,
                    vin=vin,
                    features=features,
                    current_price=current_price,
                    force_refresh=force_refresh
                )

                # Cache the result for future use
                if intelligence.confidence_overall > 0.3:  # Only cache useful results
                    await self.db_service.cache_intelligence(intelligence)

                return intelligence

            except Exception as e:
                logger.warning(f"AI intelligence attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries:
                    # Exponential backoff with jitter
                    backoff_time = (2 ** attempt) + (hash(f"{make}_{model}_{year}") % 2)
                    logger.info(f"Retrying AI intelligence in {backoff_time}s...")
                    await asyncio.sleep(backoff_time)
                else:
                    # Final attempt failed, create placeholder
                    logger.error(f"All AI intelligence attempts failed for {year} {make} {model}")
                    raise e

    def _extract_vehicle_features(self, artifact: VehicleListingArtifact) -> List[str]:
        """Extract notable features from the PDF artifact for AI analysis"""

        features = []

        # Extract from vehicle specifications
        vehicle = artifact.vehicle

        if vehicle.drivetrain:
            features.append(f"{vehicle.drivetrain} drivetrain")

        if vehicle.transmission and vehicle.transmission.lower() != "automatic":
            features.append(vehicle.transmission)

        if vehicle.engine:
            features.append(vehicle.engine)

        # Extract from condition issues (notable positive features)
        condition = artifact.condition

        if condition.grade == "Clean":
            features.append("Clean condition")
        elif condition.score >= 4.0:
            features.append("Excellent condition")
        elif condition.score >= 3.5:
            features.append("Good condition")

        # Extract from image analysis
        image_categories = set()
        for img in artifact.images:
            image_categories.add(img.category)

        if "hero" in image_categories:
            features.append("Professional photography")

        # Check for damage-free status
        has_damage = any(
            img.visible_damage
            for img in artifact.images
        )

        if not has_damage:
            features.append("No visible damage")

        # Add exterior color as feature
        if vehicle.exterior_color:
            features.append(f"{vehicle.exterior_color} exterior")

        return features

    def _convert_intelligence_to_dict(self, intelligence: VehicleIntelligence) -> Dict[str, Any]:
        """Convert VehicleIntelligence to dictionary for JSON response"""

        return {
            "vehicle_id": intelligence.vehicle_id,
            "make": intelligence.make,
            "model": intelligence.model,
            "year": intelligence.year,
            "vin": intelligence.vin,

            # Market Analysis
            "market_price_range": {
                "min": float(intelligence.market_price_range[0]) if intelligence.market_price_range and intelligence.market_price_range[0] else None,
                "max": float(intelligence.market_price_range[1]) if intelligence.market_price_range and intelligence.market_price_range[1] else None
            } if intelligence.market_price_range else None,
            "market_average_price": float(intelligence.market_average_price) if intelligence.market_average_price else None,
            "price_confidence": intelligence.price_confidence,

            # Demand & Availability
            "market_demand": intelligence.market_demand,
            "availability_score": intelligence.availability_score,
            "days_on_market_avg": intelligence.days_on_market_avg,

            # Feature Intelligence
            "feature_popularity": intelligence.feature_popularity or {},
            "competitive_advantages": intelligence.competitive_advantages or [],
            "common_complaints": intelligence.common_complaints or [],

            # Market Insights
            "market_insights": [
                {
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "sources": [
                        {
                            "source_name": source.source_name,
                            "source_url": source.source_url,
                            "source_type": source.source_type,
                            "reliability_score": source.reliability_score
                        }
                        for source in insight.sources
                    ],
                    "data_points": insight.data_points,
                    "relevance_score": insight.relevance_score
                }
                for insight in (intelligence.insights or [])
            ],

            # Metadata
            "ai_model_used": intelligence.ai_model_used,
            "generated_at": intelligence.generated_at.isoformat(),
            "cache_expires_at": intelligence.cache_expires_at.isoformat() if intelligence.cache_expires_at else None,
            "confidence_overall": intelligence.confidence_overall
        }

    def _convert_cache_to_intelligence(self, cache_data: Dict[str, Any]) -> VehicleIntelligence:
        """Convert cached data back to VehicleIntelligence object"""

        from .vehicle_intelligence_service import MarketInsight, AISource

        # Convert market price range
        price_range = None
        if cache_data.get("market_price_min") and cache_data.get("market_price_max"):
            price_range = (
                Decimal(str(cache_data["market_price_min"])),
                Decimal(str(cache_data["market_price_max"]))
            )

        # Convert market insights
        insights = []
        if cache_data.get("market_insights"):
            for insight_data in cache_data["market_insights"]:
                sources = []
                if insight_data.get("sources"):
                    for source_data in insight_data["sources"]:
                        sources.append(AISource(
                            source_name=source_data["source_name"],
                            source_url=source_data.get("source_url"),
                            source_type=source_data["source_type"],
                            reliability_score=source_data["reliability_score"]
                        ))

                insights.append(MarketInsight(
                    insight_type=insight_data["insight_type"],
                    title=insight_data["title"],
                    description=insight_data["description"],
                    confidence=insight_data["confidence"],
                    sources=sources,
                    data_points=insight_data["data_points"],
                    relevance_score=insight_data.get("relevance_score", 1.0)
                ))

        return VehicleIntelligence(
            vehicle_id=cache_data["vehicle_key"],
            make=cache_data["make"],
            model=cache_data["model"],
            year=cache_data["year"],
            vin=cache_data.get("vin"),
            market_price_range=price_range,
            market_average_price=Decimal(str(cache_data["market_average_price"])) if cache_data.get("market_average_price") else None,
            price_confidence=cache_data.get("price_confidence", 0.0),
            market_demand=cache_data.get("market_demand", "unknown"),
            availability_score=cache_data.get("availability_score", 0.0),
            days_on_market_avg=cache_data.get("days_on_market_avg"),
            feature_popularity=cache_data.get("feature_popularity", {}),
            competitive_advantages=cache_data.get("competitive_advantages", []),
            common_complaints=cache_data.get("common_complaints", []),
            insights=insights,
            ai_model_used=cache_data.get("ai_model_used", ""),
            generated_at=datetime.fromisoformat(cache_data["generated_at"]) if cache_data.get("generated_at") else datetime.now(),
            cache_expires_at=datetime.fromisoformat(cache_data["expires_at"]) if cache_data.get("expires_at") else None,
            confidence_overall=cache_data.get("ai_confidence_overall", 0.0)
        )

    def _create_placeholder_intelligence(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str],
        error: Exception
    ) -> VehicleIntelligence:
        """Create placeholder intelligence when AI processing fails"""

        from .vehicle_intelligence_service import MarketInsight

        return VehicleIntelligence(
            vehicle_id=f"{make}_{model}_{year}_{vin or 'novin'}",
            make=make,
            model=model,
            year=year,
            vin=vin,
            confidence_overall=0.0,
            ai_model_used="failed",
            insights=[
                MarketInsight(
                    insight_type="error",
                    title="AI Intelligence Unavailable",
                    description=f"Unable to fetch market intelligence: {str(error)}",
                    confidence=0.0,
                    sources=[],
                    data_points={"error": str(error)}
                )
            ]
        )

    async def batch_process_pdfs_with_ai(
        self,
        pdf_files: List[Dict[str, Any]],  # List of {"bytes": bytes, "filename": str}
        force_refresh_ai: bool = False,
        concurrency_limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process multiple PDFs with AI intelligence in batch

        Args:
            pdf_files: List of PDF files to process
            force_refresh_ai: Force refresh of AI intelligence cache
            concurrency_limit: Max concurrent AI requests to avoid rate limiting
        """

        logger.info(f"Starting batch PDF processing with AI for {len(pdf_files)} files")
        start_time = datetime.now()

        # Process with semaphore to control concurrency
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_single_pdf(pdf_data):
            async with semaphore:
                return await self.process_condition_report_with_ai(
                    pdf_bytes=pdf_data["bytes"],
                    filename=pdf_data["filename"],
                    force_refresh_ai=force_refresh_ai
                )

        # Create tasks
        tasks = [process_single_pdf(pdf) for pdf in pdf_files]

        # Execute with concurrency control
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing error for {pdf_files[i]['filename']}: {str(result)}")
                processed_results.append({
                    "filename": pdf_files[i]["filename"],
                    "error": str(result),
                    "pdf_extraction_success": False,
                    "ai_intelligence_success": False
                })
            else:
                processed_results.append(result)

        total_time = (datetime.now() - start_time).total_seconds()
        successful_count = sum(1 for r in processed_results if r.get("pdf_extraction_success", False))
        ai_success_count = sum(1 for r in processed_results if r.get("ai_intelligence_success", False))

        logger.info(
            f"Batch processing completed in {total_time:.2f}s. "
            f"PDF success: {successful_count}/{len(pdf_files)}, "
            f"AI success: {ai_success_count}/{len(pdf_files)}"
        )

        return processed_results

    def toggle_ai_processing(self, enabled: bool):
        """Enable or disable AI processing (useful for testing)"""
        self._ai_processing_enabled = enabled
        logger.info(f"AI processing {'enabled' if enabled else 'disabled'}")

    async def get_ai_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about AI processing"""

        return await self.db_service.get_intelligence_statistics()

    async def cleanup_expired_cache(self):
        """Clean up expired AI intelligence cache entries"""
        return await self.db_service.clean_expired_cache()

    async def close(self):
        """Clean up resources"""
        await self.pdf_service.close()


# Export singleton instance
enhanced_pdf_ingestion_with_ai = EnhancedPDFIngestionWithAI()


async def get_enhanced_pdf_ingestion_with_ai() -> EnhancedPDFIngestionWithAI:
    """Get the singleton enhanced PDF ingestion service"""
    return enhanced_pdf_ingestion_with_ai