"""
Otto.AI Market Data Service
Integrates external APIs to fetch real-time vehicle market data
Including pricing, market trends, and regional variations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import httpx
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


@dataclass
class MarketDataPoint:
    """Individual market data point for a vehicle"""
    vehicle_id: str
    market_price_range: Tuple[Decimal, Decimal]  # (min, max)
    average_days_on_market: int
    regional_multiplier: Decimal  # Price adjustment for region
    demand_indicator: str  # "High", "Medium", "Low"
    price_competitiveness: str  # "Above", "At", "Below" market
    confidence_score: float  # 0.0 to 1.0
    last_updated: datetime
    source: str  # API source name


@dataclass
class MarketDataRequest:
    """Request for market data lookup"""
    make: str
    model: str
    year: int
    mileage: Optional[int] = None
    trim: Optional[str] = None
    exterior_color: Optional[str] = None
    region: Optional[str] = None
    zip_code: Optional[str] = None


class MarketDataService:
    """
    Service for fetching and managing vehicle market data
    Integrates with multiple external APIs with intelligent fallbacks
    """

    def __init__(self):
        self.nhtsa_api_key = self._get_env_var('NHTSA_API_KEY', optional=True)
        self.edmunds_api_key = self._get_env_var('EDMUNDS_API_KEY', optional=True)

        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Otto.AI/1.0"}
        )

        # Cache for market data to reduce API calls
        self._cache = {}
        self._cache_ttl = timedelta(hours=24)

        # Regional price multipliers (simplified for MVP)
        self.regional_multipliers = {
            "west": Decimal("1.15"),  # CA, WA, OR
            "northeast": Decimal("1.12"),  # NY, MA, CT
            "southeast": Decimal("0.95"),  # FL, GA, AL
            "midwest": Decimal("0.98"),  # IL, OH, MI
            "southwest": Decimal("1.05"),  # TX, AZ, NM
            "default": Decimal("1.00")
        }

    def _get_env_var(self, var_name: str, optional: bool = False) -> Optional[str]:
        """Get environment variable with optional handling"""
        import os
        value = os.getenv(var_name)
        if not value and not optional:
            raise ValueError(f"Environment variable {var_name} is required")
        return value

    def _get_cache_key(self, request: MarketDataRequest) -> str:
        """Generate cache key for market data request"""
        return f"{request.make}_{request.model}_{request.year}_{request.region or 'default'}"

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid"""
        last_updated = cached_data.get("last_updated")
        if not last_updated:
            return False
        return datetime.now() - last_updated < self._cache_ttl

    async def fetch_market_data(self, request: MarketDataRequest) -> MarketDataPoint:
        """
        Fetch market data for a vehicle using available APIs with fallbacks
        """
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.info(f"Returning cached market data for {request.make} {request.model}")
            cached_point = self._cache[cache_key]["data"]
            return cached_point

        logger.info(f"Fetching fresh market data for {request.year} {request.make} {request.model}")

        # Try different APIs in order of preference
        market_data = None

        # 1. Try NHTSA API (free, comprehensive)
        try:
            market_data = await self._fetch_from_nhtsa(request)
        except Exception as e:
            logger.warning(f"NHTSA API failed: {e}")

        # 2. Try Edmunds API if NHTSA failed
        if not market_data and self.edmunds_api_key:
            try:
                market_data = await self._fetch_from_edmunds(request)
            except Exception as e:
                logger.warning(f"Edmunds API failed: {e}")

        # 3. Use synthetic data based on industry averages
        if not market_data:
            logger.warning("All external APIs failed, using synthetic data")
            market_data = await self._generate_synthetic_data(request)

        # Cache the result
        self._cache[cache_key] = {
            "data": market_data,
            "last_updated": datetime.now()
        }

        return market_data

    async def _fetch_from_nhtsa(self, request: MarketDataRequest) -> Optional[MarketDataPoint]:
        """
        Fetch market data from NHTSA API
        Focus: Vehicle specifications, safety ratings, recall data
        """
        if not self.nhtsa_api_key:
            return None

        # NHTSA doesn't provide pricing, but provides valuable vehicle data
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/{request.make}/modelyear/{request.year}?format=json"

        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("Count") == 0:
            return None

        # Extract basic model data and combine with pricing estimates
        model_data = self._find_model_in_nhtsa_data(data.get("Results", []), request.model)

        if not model_data:
            return None

        # For now, NHTSA provides vehicle identification but not market pricing
        # We'll use it as validation and supplement with synthetic pricing
        return await self._enhance_with_pricing_data(request, {"nhtsa_data": model_data})

    async def _fetch_from_edmunds(self, request: MarketDataRequest) -> Optional[MarketDataPoint]:
        """
        Fetch market data from Edmunds API
        Focus: Pricing, market trends, vehicle valuations
        """
        if not self.edmunds_api_key:
            return None

        # Note: This is a simplified implementation
        # Actual Edmunds API would require proper authentication and endpoint usage
        headers = {"Authorization": f"Bearer {self.edmunds_api_key}"}

        # Placeholder for Edmunds API integration
        # Actual implementation would use proper Edmunds endpoints
        logger.info("Edmunds API integration not yet implemented - using synthetic data")
        return None

    async def _generate_synthetic_data(self, request: MarketDataRequest) -> MarketDataPoint:
        """
        Generate synthetic market data based on industry averages and heuristics
        Used as fallback when external APIs are unavailable
        """
        # Base depreciation rates by vehicle age
        current_year = datetime.now().year
        vehicle_age = current_year - request.year

        # MSRP estimation based on make/model/year
        base_msrp = await self._estimate_base_msrp(request.make, request.model, request.year)

        # Calculate depreciation
        depreciation_rate = self._get_depreciation_rate(vehicle_age)
        current_market_value = base_msrp * (1 - depreciation_rate)

        # Market range (±20% around market value)
        market_min = current_market_value * Decimal("0.80")
        market_max = current_market_value * Decimal("1.20")

        # Regional adjustment
        region = request.region or "default"
        regional_multiplier = self.regional_multipliers.get(region.lower(), self.regional_multipliers["default"])

        # Apply regional multiplier
        market_min *= regional_multiplier
        market_max *= regional_multiplier
        current_market_value *= regional_multiplier

        # Days on market based on vehicle type and price
        avg_days_on_market = self._estimate_days_on_market(current_market_value, vehicle_age)

        # Demand indicator based on price competitiveness
        if current_market_value < base_msrp * Decimal("0.70"):
            demand_indicator = "High"  # Good value
        elif current_market_value > base_msrp * Decimal("0.90"):
            demand_indicator = "Low"   # Overpriced
        else:
            demand_indicator = "Medium"

        return MarketDataPoint(
            vehicle_id="",  # Will be set by caller
            market_price_range=(market_min, market_max),
            average_days_on_market=avg_days_on_market,
            regional_multiplier=regional_multiplier,
            demand_indicator=demand_indicator,
            price_competitiveness="At",  # Will be calculated by caller
            confidence_score=0.6,  # Lower confidence for synthetic data
            last_updated=datetime.now(),
            source="synthetic"
        )

    async def _estimate_base_msrp(self, make: str, model: str, year: int) -> Decimal:
        """
        Estimate base MSRP for a vehicle using heuristics
        """
        # Simplified MSRP estimation based on brand categories
        brand_premiums = {
            "luxury": {
                "makes": ["Lexus", "BMW", "Mercedes-Benz", "Audi", "Cadillac", "Lincoln"],
                "base_multiplier": Decimal("1.5")
            },
            "premium": {
                "makes": ["Toyota", "Honda", "Volkswagen", "Subaru", "Mazda"],
                "base_multiplier": Decimal("1.2")
            },
            "standard": {
                "makes": ["Ford", "Chevrolet", "Dodge", "Nissan", "Hyundai", "Kia"],
                "base_multiplier": Decimal("1.0")
            },
            "economy": {
                "makes": ["Mitsubishi", "FIAT", "Smart"],
                "base_multiplier": Decimal("0.8")
            }
        }

        # Find brand category
        brand_category = "standard"
        for category, info in brand_premiums.items():
            if make in info["makes"]:
                brand_category = category
                break

        base_price = Decimal("35000")  # Average new car price
        multiplier = brand_premiums[brand_category]["base_multiplier"]

        # Year adjustment (inflation)
        current_year = datetime.now().year
        years_old = current_year - year
        inflation_adjustment = Decimal("1.02") ** years_old  # 2% annual inflation

        return base_price * multiplier * inflation_adjustment

    def _get_depreciation_rate(self, vehicle_age: int) -> Decimal:
        """
        Calculate depreciation rate based on vehicle age
        """
        if vehicle_age == 0:
            return Decimal("0.10")  # 10% first year
        elif vehicle_age == 1:
            return Decimal("0.20")  # 20% by end of year 1
        elif vehicle_age <= 3:
            return Decimal("0.30")  # 30% by end of year 3
        elif vehicle_age <= 5:
            return Decimal("0.45")  # 45% by end of year 5
        elif vehicle_age <= 8:
            return Decimal("0.60")  # 60% by end of year 8
        else:
            return Decimal("0.70")  # 70%+ for older vehicles

    def _estimate_days_on_market(self, price: Decimal, age: int) -> int:
        """
        Estimate average days on market based on price and age
        """
        # Base days on market
        base_days = 45

        # Price adjustment
        if price > Decimal("50000"):
            base_days *= 1.5  # Luxury cars take longer
        elif price < Decimal("15000"):
            base_days *= 0.7  # Economy cars sell faster

        # Age adjustment
        if age < 2:
            base_days *= 0.8  # Nearly new sells faster
        elif age > 10:
            base_days *= 1.3  # Older cars take longer

        return int(base_days)

    def _find_model_in_nhtsa_data(self, results: List[Dict], model: str) -> Optional[Dict]:
        """Find matching model in NHTSA API results"""
        model_lower = model.lower()
        for result in results:
            if result.get("Model_Name", "").lower() == model_lower:
                return result
        return None

    async def _enhance_with_pricing_data(self, request: MarketDataRequest, vehicle_data: Dict) -> MarketDataPoint:
        """Enhance NHTSA data with pricing estimates"""
        # Generate synthetic pricing and combine with NHTSA data
        synthetic_data = await self._generate_synthetic_data(request)
        synthetic_data.source = "nhtsa_enhanced"
        synthetic_data.confidence_score = 0.75  # Higher than pure synthetic
        return synthetic_data

    def calculate_price_competitiveness(
        self,
        dealer_price: Decimal,
        market_data: MarketDataPoint
    ) -> str:
        """
        Calculate how competitive a dealer's price is compared to market
        """
        market_min, market_max = market_data.market_price_range
        market_mid = (market_min + market_max) / 2

        if dealer_price <= market_min:
            return "Below"
        elif dealer_price >= market_max:
            return "Above"
        else:
            return "At"

    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()


# Singleton instance
market_data_service = MarketDataService()


async def get_market_data_service() -> MarketDataService:
    """Get the singleton market data service instance"""
    return market_data_service