"""
Otto.AI Enhanced Market Data Service
Integrates web scraping with existing market data infrastructure
Provides real-time pricing without relying on paid APIs
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import json

from .grok_mini_web_scraper import get_grok_mini_scraper, MarketAnalysisResult
from .market_data_service import MarketDataService, MarketDataPoint

logger = logging.getLogger(__name__)


@dataclass
class VehicleMarketIntelligence:
    """Complete market intelligence for a vehicle"""
    vehicle_id: str
    scraped_data: MarketAnalysisResult
    cached_data: Optional[MarketDataPoint]
    blended_analysis: Dict[str, Any]
    last_updated: datetime
    confidence_score: float
    sources_count: int


class EnhancedMarketDataService:
    """
    Enhanced market data service that combines web scraping with existing data
    Uses Grok Mini web scraper for real-time data without API costs
    """

    def __init__(self):
        self.web_scraper = get_grok_mini_scraper()
        self.existing_service = MarketDataService()
        self.intelligence_cache = {}
        self.cache_ttl = timedelta(hours=6)

    async def get_comprehensive_market_intelligence(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: Optional[int] = None,
        mileage: Optional[int] = None,
        trim: Optional[str] = None,
        location: Optional[str] = None,
        use_cache: bool = True
    ) -> VehicleMarketIntelligence:
        """
        Get comprehensive market intelligence combining web scraping and existing data
        """
        logger.info(f"Getting market intelligence for {vehicle_id}: {year} {make} {model}")

        # Check cache first
        cache_key = f"{make}_{model}_{year}_{mileage}_{location}"
        if use_cache and cache_key in self.intelligence_cache:
            cached = self.intelligence_cache[cache_key]
            if datetime.now() - cached.last_updated < self.cache_ttl:
                logger.info("Using cached market intelligence")
                return cached

        # Get scraped data from web
        scraped_data = await self.web_scraper.scrape_vehicle_market_data(
            make=make,
            model=model,
            year=year,
            max_mileage=mileage,
            zip_code=location
        )

        # Try to get existing cached data
        cached_data = None
        try:
            # This would use the existing market_data_service
            # For now, we'll skip since we want to focus on web scraping
            pass
        except Exception as e:
            logger.debug(f"Could not get existing market data: {e}")

        # Blend the data sources
        blended_analysis = self._blend_data_sources(scraped_data, cached_data)

        # Calculate overall confidence
        confidence = self._calculate_confidence(scraped_data, cached_data)

        # Create intelligence object
        intelligence = VehicleMarketIntelligence(
            vehicle_id=vehicle_id,
            scraped_data=scraped_data,
            cached_data=cached_data,
            blended_analysis=blended_analysis,
            last_updated=datetime.now(),
            confidence_score=confidence,
            sources_count=len(scraped_data.sources_analyzed)
        )

        # Cache the result
        self.intelligence_cache[cache_key] = intelligence

        return intelligence

    def _blend_data_sources(
        self,
        scraped: MarketAnalysisResult,
        cached: Optional[MarketDataPoint]
    ) -> Dict[str, Any]:
        """
        Blend scraped data with existing cached data for comprehensive analysis
        """
        analysis = {
            'scraped_avg_price': scraped.avg_price,
            'scraped_price_range': scraped.price_range,
            'scraped_listings_count': scraped.total_listings,
            'price_trend': scraped.price_trend,
            'market_health': scraped.market_health,
            'sources_used': scraped.sources_analyzed,
            'confidence_from_scraping': scraped.confidence_score,
        }

        # Add cached data if available
        if cached:
            analysis.update({
                'cached_avg_price': cached.market_price_range[0] + cached.market_price_range[1] / 2,
                'cached_demand_indicator': cached.demand_indicator,
                'cached_regional_multiplier': cached.regional_multiplier,
                'cached_price_competitiveness': cached.price_competitiveness,
                'has_cached_data': True,
            })

            # Compare scraped vs cached prices
            scraped_mid = (scraped.price_range[0] + scraped.price_range[1]) / 2
            cached_mid = (cached.market_price_range[0] + cached.market_price_range[1]) / 2

            if scraped_mid > cached_mid * Decimal('1.1'):
                analysis['price_comparison'] = "Scraped prices are higher than cached data"
            elif scraped_mid < cached_mid * Decimal('0.9'):
                analysis['price_comparison'] = "Scraped prices are lower than cached data"
            else:
                analysis['price_comparison'] = "Scraped prices match cached data"
        else:
            analysis['has_cached_data'] = False
            analysis['price_comparison'] = "No cached data available for comparison"

        return analysis

    def _calculate_confidence(
        self,
        scraped: MarketAnalysisResult,
        cached: Optional[MarketDataPoint]
    ) -> float:
        """
        Calculate overall confidence score based on data sources
        """
        base_confidence = scraped.confidence_score

        # Boost confidence if we have multiple sources
        source_bonus = min(len(scraped.sources_analyzed) / 3, 0.2)

        # Boost confidence if cached data agrees
        data_agreement_bonus = 0.1 if cached else 0

        # Listing count bonus
        listing_bonus = min(scraped.total_listings / 50, 0.1)

        total_confidence = base_confidence + source_bonus + data_agreement_bonus + listing_bonus
        return min(total_confidence, 1.0)

    async def analyze_vehicle_competitiveness(
        self,
        vehicle_id: str,
        asking_price: Decimal,
        make: str,
        model: str,
        year: Optional[int] = None,
        mileage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze how competitively priced a vehicle is compared to market
        """
        intelligence = await self.get_comprehensive_market_intelligence(
            vehicle_id=vehicle_id,
            make=make,
            model=model,
            year=year,
            mileage=mileage
        )

        scraped = intelligence.scraped_data

        # Calculate percentile of asking price
        price_percentile = self._calculate_price_percentile(asking_price, scraped)

        # Determine competitiveness
        if price_percentile <= 25:
            competitiveness = "Excellent Deal - Below 25th percentile"
            competitiveness_score = 5
        elif price_percentile <= 50:
            competitiveness = "Good Deal - Below median"
            competitiveness_score = 4
        elif price_percentile <= 75:
            competitiveness = "Fair Price - Above median"
            competitiveness_score = 3
        else:
            competitiveness = "Overpriced - Above 75th percentile"
            competitiveness_score = 2

        return {
            'asking_price': asking_price,
            'market_avg': scraped.avg_price,
            'market_range': scraped.price_range,
            'price_percentile': price_percentile,
            'competitiveness': competitiveness,
            'competitiveness_score': competitiveness_score,
            'market_trend': scraped.price_trend,
            'analysis_confidence': intelligence.confidence_score,
            'recommendation': self._get_pricing_recommendation(price_percentile, scraped.price_trend)
        }

    def _calculate_price_percentile(
        self,
        price: Decimal,
        market_data: MarketAnalysisResult
    ) -> float:
        """
        Calculate what percentile a price falls into compared to market
        """
        # For simplicity, we'll use a linear interpolation
        min_price, max_price = market_data.price_range
        if max_price == min_price:
            return 50.0

        # Calculate position within range (0-100)
        position = float((price - min_price) / (max_price - min_price)) * 100
        return max(0, min(100, position))

    def _get_pricing_recommendation(
        self,
        price_percentile: float,
        market_trend: str
    ) -> str:
        """
        Get pricing recommendation based on percentile and trend
        """
        if price_percentile < 25:
            if market_trend == "Increasing":
                return "Great price! Market is trending up, so this deal won't last."
            else:
                return "Excellent price. Consider this a strong buy."
        elif price_percentile < 50:
            if market_trend == "Increasing":
                return "Good price. With market trending up, this could be a solid investment."
            else:
                return "Fair price. Room for negotiation."
        elif price_percentile < 75:
            if market_trend == "Increasing":
                return "Above average but market is trending up. Verify condition."
            else:
                return "Slightly overpriced. Try to negotiate down."
        else:
            if market_trend == "Increasing":
                return "Premium pricing. Market is supporting high prices but verify value."
            else:
                return "Significantly overpriced. Strong negotiation needed or walk away."


# Singleton instance
_enhanced_service = None

def get_enhanced_market_data_service() -> EnhancedMarketDataService:
    """Get singleton instance of the enhanced market data service"""
    global _enhanced_service
    if _enhanced_service is None:
        _enhanced_service = EnhancedMarketDataService()
    return _enhanced_service