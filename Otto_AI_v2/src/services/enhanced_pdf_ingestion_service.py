"""
Enhanced PDF Ingestion Service with Market Data Integration
Extends the base PDF ingestion service to fetch and store market intelligence
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional

from .pdf_ingestion_service import (
    PDFIngestionService,
    VehicleListingArtifact,
    get_pdf_ingestion_service
)
from .market_data_service import (
    MarketDataService,
    MarketDataRequest,
    MarketDataPoint,
    get_market_data_service
)
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class EnhancedPDFIngestionService:
    """
    Enhanced PDF ingestion service that adds market data intelligence
    to the vehicle processing pipeline
    """

    def __init__(self):
        # Initialize base services
        self.pdf_service = PDFIngestionService()
        self.market_service = MarketDataService()
        self.supabase = get_supabase_client()

    async def process_condition_report_with_market_data(
        self,
        pdf_bytes: bytes,
        filename: str,
        region: Optional[str] = None,
        zip_code: Optional[str] = None
    ) -> VehicleListingArtifact:
        """
        Process PDF and enrich with market data intelligence

        This extends the base process_condition_report to:
        1. Extract vehicle data from PDF
        2. Fetch market data for the vehicle
        3. Store market data in Supabase
        4. Return enhanced artifact with market intelligence
        """
        logger.info(f"Starting enhanced PDF processing for {filename}")

        # Step 1: Process PDF using base service
        artifact = await self.pdf_service.process_condition_report(pdf_bytes, filename)

        # Step 2: Fetch market data for the vehicle
        try:
            market_data = await self._fetch_market_data_for_vehicle(
                artifact.vehicle,
                region=region,
                zip_code=zip_code
            )

            # Step 3: Store market data in database
            if market_data:
                vehicle_id = await self._store_vehicle_data(artifact)
                await self._store_market_data(vehicle_id, market_data, artifact.vehicle)

                # Step 4: Enrich artifact with market data
                artifact = self._enrich_artifact_with_market_data(artifact, market_data)

            logger.info(f"Successfully processed {filename} with market data enrichment")
            return artifact

        except Exception as e:
            logger.error(f"Market data processing failed for {filename}: {str(e)}")
            # Still return the base artifact even if market data fails
            logger.info(f"Returning base artifact without market data for {filename}")
            return artifact

    async def _fetch_market_data_for_vehicle(
        self,
        vehicle_info,
        region: Optional[str] = None,
        zip_code: Optional[str] = None
    ) -> Optional[MarketDataPoint]:
        """Fetch market data for a vehicle"""
        try:
            request = MarketDataRequest(
                make=vehicle_info.make,
                model=vehicle_info.model,
                year=vehicle_info.year,
                mileage=getattr(vehicle_info, 'mileage', None),
                trim=getattr(vehicle_info, 'trim', None),
                exterior_color=getattr(vehicle_info, 'exterior_color', None),
                region=region,
                zip_code=zip_code
            )

            market_data = await self.market_service.fetch_market_data(request)

            # Calculate price competitiveness based on dealer price
            if hasattr(vehicle_info, 'price') and vehicle_info.price:
                competitiveness = self.market_service.calculate_price_competitiveness(
                    Decimal(str(vehicle_info.price)),
                    market_data
                )
                market_data.price_competitiveness = competitiveness

            logger.info(f"Fetched market data for {vehicle_info.year} {vehicle_info.make} {vehicle_info.model}")
            return market_data

        except Exception as e:
            logger.error(f"Failed to fetch market data: {str(e)}")
            return None

    async def _store_vehicle_data(self, artifact: VehicleListingArtifact) -> str:
        """Store vehicle data in Supabase and return vehicle_id"""
        try:
            # Prepare vehicle data for Supabase
            vehicle_data = {
                "make": artifact.vehicle.make,
                "model": artifact.vehicle.model,
                "year": artifact.vehicle.year,
                "vin": artifact.vehicle.vin or "",
                "color": getattr(artifact.vehicle, 'color', None),
                "mileage": getattr(artifact.vehicle, 'mileage', None),
                "trim": getattr(artifact.vehicle, 'trim', None),
                "asking_price": float(getattr(artifact.vehicle, 'price', 0)) if getattr(artifact.vehicle, 'price', None) else None,
                "rich_description": artifact.condition.description or "",
                "key_features": {
                    "drivetrain": getattr(artifact.vehicle, 'drivetrain', None),
                    "transmission": getattr(artifact.vehicle, 'transmission', None),
                    "engine": getattr(artifact.vehicle, 'engine', None),
                    "fuel_type": getattr(artifact.vehicle, 'fuel_type', None)
                },
                "seo_title": f"{artifact.vehicle.year} {artifact.vehicle.make} {artifact.vehicle.model}",
                "seo_keywords": [
                    artifact.vehicle.make.lower(),
                    artifact.vehicle.model.lower(),
                    str(artifact.vehicle.year),
                    "vehicle",
                    "car"
                ],
                "processing_status": "completed",
                "mse_version": "1.0",
                "version_number": 1,
                "is_active": True,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "processing_metadata": {
                    **artifact.processing_metadata,
                    "enhanced_with_market_data": True,
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }
            }

            # Insert into Supabase
            result = self.supabase.table('vehicle_listings').insert(vehicle_data).execute()

            if result.data and len(result.data) > 0:
                vehicle_id = result.data[0]['id']
                logger.info(f"Stored vehicle data with ID: {vehicle_id}")
                return vehicle_id
            else:
                raise Exception("No data returned from Supabase insert")

        except Exception as e:
            logger.error(f"Failed to store vehicle data: {str(e)}")
            raise

    async def _store_market_data(
        self,
        vehicle_id: str,
        market_data: MarketDataPoint,
        vehicle_info
    ) -> None:
        """Store market data in the vehicle listing"""
        try:
            # Update vehicle listing with market data
            update_data = {
                "market_price_min": float(market_data.market_price_range[0]),
                "market_price_max": float(market_data.market_price_range[1]),
                "market_price_average": float(
                    (market_data.market_price_range[0] + market_data.market_price_range[1]) / 2
                ),
                "days_on_market_average": market_data.average_days_on_market,
                "regional_multiplier": float(market_data.regional_multiplier),
                "demand_indicator": market_data.demand_indicator,
                "price_competitiveness_label": market_data.price_competitiveness,
                "market_confidence_score": market_data.confidence_score,
                "market_data_source": market_data.source,
                "market_data_updated_at": datetime.now(timezone.utc).isoformat()
            }

            # Update the vehicle listing
            result = self.supabase.table('vehicle_listings').update(update_data).eq(
                'id', vehicle_id
            ).execute()

            # Also store in cache for future use
            await self._store_in_market_cache(vehicle_info, market_data)

            logger.info(f"Stored market data for vehicle ID: {vehicle_id}")

        except Exception as e:
            logger.error(f"Failed to store market data: {str(e)}")
            raise

    async def _store_in_market_cache(
        self,
        vehicle_info,
        market_data: MarketDataPoint
    ) -> None:
        """Store market data in cache for future lookups"""
        try:
            cache_key = f"{vehicle_info.make}_{vehicle_info.model}_{vehicle_info.year}_default"

            cache_data = {
                "cache_key": cache_key,
                "make": vehicle_info.make,
                "model": vehicle_info.model,
                "year": vehicle_info.year,
                "region": "default",
                "market_data": {
                    "market_price_range": [
                        float(market_data.market_price_range[0]),
                        float(market_data.market_price_range[1])
                    ],
                    "average_days_on_market": market_data.average_days_on_market,
                    "regional_multiplier": float(market_data.regional_multiplier),
                    "demand_indicator": market_data.demand_indicator,
                    "confidence_score": market_data.confidence_score,
                    "source": market_data.source
                },
                "confidence_score": market_data.confidence_score,
                "data_source": market_data.source,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            }

            # Try to insert into cache (ignore if already exists)
            try:
                self.supabase.table('market_data_cache').insert(cache_data).execute()
            except Exception:
                # Cache entry might already exist, that's OK
                pass

        except Exception as e:
            logger.warning(f"Failed to store in market cache: {str(e)}")
            # Cache storage failure is not critical

    def _enrich_artifact_with_market_data(
        self,
        artifact: VehicleListingArtifact,
        market_data: MarketDataPoint
    ) -> VehicleListingArtifact:
        """Enrich the artifact with market data information"""
        # Add market data to processing metadata
        artifact.processing_metadata.update({
            "market_data": {
                "price_range": {
                    "min": float(market_data.market_price_range[0]),
                    "max": float(market_data.market_price_range[1]),
                    "average": float(
                        (market_data.market_price_range[0] + market_data.market_price_range[1]) / 2
                    )
                },
                "days_on_market_average": market_data.average_days_on_market,
                "demand_indicator": market_data.demand_indicator,
                "price_competitiveness": market_data.price_competitiveness,
                "confidence_score": market_data.confidence_score,
                "data_source": market_data.source
            },
            "market_data_enhanced": True,
            "market_data_fetched_at": datetime.now(timezone.utc).isoformat()
        })

        return artifact

    async def update_market_data_for_existing_vehicle(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: int,
        price: Optional[float] = None,
        region: Optional[str] = None
    ) -> bool:
        """
        Update market data for an existing vehicle in the database
        Useful for manual updates or periodic refreshes
        """
        try:
            # Fetch current vehicle data
            result = self.supabase.table('vehicle_listings').select('*').eq('id', vehicle_id).execute()

            if not result.data or len(result.data) == 0:
                logger.error(f"Vehicle with ID {vehicle_id} not found")
                return False

            vehicle = result.data[0]

            # Fetch fresh market data
            market_request = MarketDataRequest(
                make=make,
                model=model,
                year=year,
                mileage=vehicle.get('mileage'),
                trim=vehicle.get('trim'),
                region=region
            )

            market_data = await self.market_service.fetch_market_data(market_request)

            if market_data:
                # Update with new market data
                update_data = {
                    "market_price_min": float(market_data.market_price_range[0]),
                    "market_price_max": float(market_data.market_price_range[1]),
                    "market_price_average": float(
                        (market_data.market_price_range[0] + market_data.market_price_range[1]) / 2
                    ),
                    "days_on_market_average": market_data.average_days_on_market,
                    "demand_indicator": market_data.demand_indicator,
                    "market_confidence_score": market_data.confidence_score,
                    "market_data_source": market_data.source,
                    "market_data_updated_at": datetime.now(timezone.utc).isoformat()
                }

                if price:
                    update_data["asking_price"] = price
                    update_data["price_competitiveness_label"] = (
                        self.market_service.calculate_price_competitiveness(
                            Decimal(str(price)),
                            market_data
                        )
                    )

                # Perform update
                self.supabase.table('vehicle_listings').update(update_data).eq('id', vehicle_id).execute()

                logger.info(f"Updated market data for vehicle ID: {vehicle_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update market data for vehicle {vehicle_id}: {str(e)}")
            return False

    async def close(self):
        """Clean up resources"""
        await self.pdf_service.close()
        await self.market_service.close()


# Singleton instance
enhanced_pdf_ingestion_service = EnhancedPDFIngestionService()


async def get_enhanced_pdf_ingestion_service() -> EnhancedPDFIngestionService:
    """Get the singleton enhanced PDF ingestion service instance"""
    return enhanced_pdf_ingestion_service