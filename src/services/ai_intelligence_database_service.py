"""
Otto.AI AI Intelligence Database Service

Manages AI intelligence data operations in Supabase database.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from supabase import create_client, Client
from .vehicle_intelligence_service import VehicleIntelligence, MarketInsight, AISource

logger = logging.getLogger(__name__)


class AIIntelligenceDatabaseService:
    """Service for AI intelligence database operations"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    async def save_vehicle_intelligence(
        self,
        vehicle_id: str,
        intelligence: VehicleIntelligence
    ) -> bool:
        """Save AI intelligence for a vehicle"""

        try:
            # Convert to database format
            intelligence_data = self._convert_intelligence_to_db(intelligence)

            # Update vehicle_listings table
            update_result = self.supabase.table("vehicle_listings").update(
                intelligence_data
            ).eq("id", vehicle_id).execute()

            if not update_result.data:
                logger.warning(f"Vehicle {vehicle_id} not found for intelligence update")
                return False

            # Also cache in dedicated table
            await self._cache_intelligence(intelligence)

            logger.info(f"Saved AI intelligence for vehicle {vehicle_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving vehicle intelligence: {str(e)}")
            return False

    async def get_vehicle_intelligence(
        self,
        vehicle_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get AI intelligence for a specific vehicle"""

        try:
            result = self.supabase.table("vehicle_listings").select(
                """
                market_price_min,
                market_price_max,
                market_average_price,
                price_confidence,
                market_demand,
                availability_score,
                days_on_market_avg,
                feature_popularity,
                competitive_advantages,
                common_complaints,
                market_insights,
                ai_model_used,
                ai_confidence_overall,
                ai_intelligence_generated_at,
                ai_intelligence_expires_at,
                ai_processing_status,
                ai_processing_error,
                ai_last_processed_at
                """
            ).eq("id", vehicle_id).single().execute()

            if result.data:
                # Check if intelligence is expired
                expires_at = result.data.get("ai_intelligence_expires_at")
                if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                    logger.info(f"Intelligence expired for vehicle {vehicle_id}")
                    return None

                return result.data

            return None

        except Exception as e:
            logger.error(f"Error getting vehicle intelligence: {str(e)}")
            return None

    async def get_intelligence_from_cache(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get intelligence from cache table"""

        try:
            query = self.supabase.table("ai_intelligence_cache").select("*").eq(
                "make", make
            ).eq("model", model).eq("year", year)

            if vin:
                query = query.eq("vin", vin)
            else:
                query = query.is_("vin", "null")

            # Check if not expired
            query = query.or_(
                "expires_at.is.null,expires_at.gt." + datetime.now().isoformat()
            )

            result = query.limit(1).execute()

            if result.data:
                # Update last accessed
                self.supabase.table("ai_intelligence_cache").update({
                    "last_accessed_at": datetime.now().isoformat(),
                    "request_count": self.supabase.rpc(
                        "increment", {"x": "request_count"}
                    )
                }).eq("vehicle_key", result.data[0]["vehicle_key"]).execute()

                return result.data[0]

            return None

        except Exception as e:
            logger.error(f"Error getting intelligence from cache: {str(e)}")
            return None

    async def cache_intelligence(
        self,
        intelligence: VehicleIntelligence
    ) -> bool:
        """Cache intelligence data"""

        try:
            return await self._cache_intelligence(intelligence)

        except Exception as e:
            logger.error(f"Error caching intelligence: {str(e)}")
            return False

    async def _cache_intelligence(self, intelligence: VehicleIntelligence) -> bool:
        """Internal method to cache intelligence"""

        vehicle_key = f"{intelligence.make}_{intelligence.model}_{intelligence.year}_{intelligence.vin or 'novin'}"

        cache_data = {
            "vehicle_key": vehicle_key,
            "make": intelligence.make,
            "model": intelligence.model,
            "year": intelligence.year,
            "vin": intelligence.vin,
            "market_price_min": intelligence.market_price_range[0] if intelligence.market_price_range else None,
            "market_price_max": intelligence.market_price_range[1] if intelligence.market_price_range else None,
            "market_average_price": intelligence.market_average_price,
            "price_confidence": intelligence.price_confidence,
            "market_demand": intelligence.market_demand,
            "availability_score": intelligence.availability_score,
            "days_on_market_avg": intelligence.days_on_market_avg,
            "feature_popularity": intelligence.feature_popularity or {},
            "competitive_advantages": intelligence.competitive_advantages,
            "common_complaints": intelligence.common_complaints,
            "market_insights": self._convert_insights_to_json(intelligence.insights),
            "ai_model_used": intelligence.ai_model_used,
            "ai_confidence_overall": intelligence.confidence_overall,
            "generated_at": intelligence.generated_at.isoformat(),
            "expires_at": intelligence.cache_expires_at.isoformat() if intelligence.cache_expires_at else None
        }

        try:
            # Use upsert to handle both insert and update
            result = self.supabase.table("ai_intelligence_cache").upsert(
                cache_data,
                on_conflict="vehicle_key"
            ).execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error in cache upsert: {str(e)}")
            return False

    async def batch_update_intelligence_status(
        self,
        vehicle_ids: List[str],
        status: str,
        error: Optional[str] = None
    ) -> int:
        """Batch update AI processing status"""

        try:
            update_data = {
                "ai_processing_status": status,
                "ai_last_processed_at": datetime.now().isoformat()
            }

            if error:
                update_data["ai_processing_error"] = error

            # Update in batches of 50 to avoid limits
            batch_size = 50
            updated_count = 0

            for i in range(0, len(vehicle_ids), batch_size):
                batch_ids = vehicle_ids[i:i + batch_size]

                result = self.supabase.table("vehicle_listings").update(
                    update_data
                ).in_("id", batch_ids).execute()

                updated_count += len(result.data) if result.data else 0

            logger.info(f"Updated AI status for {updated_count} vehicles to {status}")
            return updated_count

        except Exception as e:
            logger.error(f"Error batch updating intelligence status: {str(e)}")
            return 0

    async def get_vehicles_needing_intelligence(
        self,
        limit: int = 100,
        force_refresh_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get vehicles that need AI intelligence processing"""

        try:
            # Find vehicles without intelligence or with expired intelligence
            cutoff_time = datetime.now() - timedelta(hours=force_refresh_hours)

            result = self.supabase.table("vehicle_listings").select(
                """
                id, make, model, year, vin, price, mileage,
                ai_processing_status, ai_intelligence_generated_at,
                ai_processing_error
                """
            ).or_(
                f"ai_processing_status.eq.pending,"
                f"ai_processing_status.eq.error,"
                f"ai_intelligence_generated_at.is.null,"
                f"ai_intelligence_generated_at.lt.{cutoff_time.isoformat()}"
            ).limit(limit).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting vehicles needing intelligence: {str(e)}")
            return []

    async def get_intelligence_statistics(self) -> Dict[str, Any]:
        """Get intelligence processing statistics"""

        try:
            # Get counts by status
            status_result = self.supabase.table("vehicle_listings").select(
                "ai_processing_status",
                count="id"
            ).execute()

            status_counts = {}
            for row in status_result.data or []:
                status_counts[row["ai_processing_status"]] = row["count"]

            # Get cache statistics
            cache_result = self.supabase.table("ai_intelligence_cache").select(
                "count",
                count="id"
            ).execute()

            cache_count = cache_result.data[0]["count"] if cache_result.data else 0

            # Get average confidence scores
            confidence_result = self.supabase.table("vehicle_listings").select(
                "ai_confidence_overall"
            ).not_("ai_confidence_overall", "is", "null").execute()

            confidences = [
                row["ai_confidence_overall"]
                for row in (confidence_result.data or [])
                if row["ai_confidence_overall"] is not None
            ]

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "status_counts": status_counts,
                "cache_entries": cache_count,
                "average_confidence": avg_confidence,
                "total_with_intelligence": sum(
                    count for status, count in status_counts.items()
                    if status in ["completed", "success"]
                )
            }

        except Exception as e:
            logger.error(f"Error getting intelligence statistics: {str(e)}")
            return {}

    async def clean_expired_cache(self) -> int:
        """Clean expired cache entries"""

        try:
            result = self.supabase.table("ai_intelligence_cache").delete().lt(
                "expires_at", datetime.now().isoformat()
            ).execute()

            deleted_count = len(result.data) if result.data else 0

            if deleted_count > 0:
                logger.info(f"Cleaned {deleted_count} expired cache entries")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning expired cache: {str(e)}")
            return 0

    async def search_intelligent_vehicles(
        self,
        min_confidence: float = 0.5,
        market_demand: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search vehicles with AI intelligence filters"""

        try:
            query = self.supabase.table("vehicle_listings").select(
                """
                id, make, model, year, price, mileage,
                market_price_min, market_price_max, market_average_price,
                price_confidence, market_demand, availability_score,
                competitive_advantages, common_complaints,
                ai_confidence_overall, ai_model_used
                """
            ).gte("ai_confidence_overall", min_confidence)

            if market_demand:
                query = query.eq("market_demand", market_demand)

            if max_price:
                query = query.lte("price", max_price)

            result = query.limit(limit).order(
                "ai_confidence_overall",
                desc=True
            ).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error searching intelligent vehicles: {str(e)}")
            return []

    def _convert_intelligence_to_db(self, intelligence: VehicleIntelligence) -> Dict[str, Any]:
        """Convert VehicleIntelligence to database format"""

        return {
            "market_price_min": intelligence.market_price_range[0] if intelligence.market_price_range else None,
            "market_price_max": intelligence.market_price_range[1] if intelligence.market_price_range else None,
            "market_average_price": intelligence.market_average_price,
            "price_confidence": intelligence.price_confidence,
            "market_demand": intelligence.market_demand,
            "availability_score": intelligence.availability_score,
            "days_on_market_avg": intelligence.days_on_market_avg,
            "feature_popularity": intelligence.feature_popularity or {},
            "competitive_advantages": intelligence.competitive_advantages,
            "common_complaints": intelligence.common_complaints,
            "market_insights": self._convert_insights_to_json(intelligence.insights),
            "ai_model_used": intelligence.ai_model_used,
            "ai_confidence_overall": intelligence.confidence_overall,
            "ai_intelligence_generated_at": intelligence.generated_at.isoformat(),
            "ai_intelligence_expires_at": intelligence.cache_expires_at.isoformat() if intelligence.cache_expires_at else None,
            "ai_processing_status": "completed",
            "ai_processing_error": None,
            "ai_last_processed_at": datetime.now().isoformat()
        }

    def _convert_insights_to_json(self, insights: List[MarketInsight]) -> List[Dict[str, Any]]:
        """Convert MarketInsight list to JSON format"""

        return [
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
            for insight in insights
        ]


# Export the service instance
ai_intelligence_db_service = AIIntelligenceDatabaseService()