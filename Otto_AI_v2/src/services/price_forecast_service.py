"""
Otto.AI Price Forecast Service

Uses Groq Compound to fetch real-time market prices and generate
price forecasts for vehicles without known prices.

Features:
- Real-time web search for comparable vehicle prices
- Statistical analysis using Wolfram Alpha
- Caching to minimize API calls
- Confidence scoring based on data availability

Usage:
    service = PriceForecastService()
    forecast = await service.get_price_forecast(
        year=2020, make="Ford", model="F-250",
        trim="Lariat", mileage=45000
    )
"""

import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PriceForecast(BaseModel):
    """Price forecast result"""
    estimated_price: float = Field(..., description="Estimated market price")
    price_low: float = Field(..., description="Lower bound (10th percentile)")
    price_high: float = Field(..., description="Upper bound (90th percentile)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    # Data sources
    sources_used: List[str] = Field(default_factory=list, description="Data sources consulted")
    comparable_count: int = Field(0, description="Number of comparables found")

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    cache_hit: bool = Field(False)
    latency_ms: float = Field(0.0)

    # Reasoning
    reasoning: str = Field("", description="Explanation of price estimate")


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: PriceForecast
    timestamp: datetime


class PriceForecastService:
    """
    Real-time vehicle price forecasting using Groq Compound.

    Groq Compound provides:
    - Web Search: Find current listings for comparable vehicles
    - Wolfram Alpha: Statistical calculations (mean, median, percentiles)
    - Code Execution: Data processing and analysis

    The service caches results for 24 hours to minimize API costs.
    """

    def __init__(self, cache_ttl_hours: int = 24):
        self.api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        self.use_openrouter = not os.getenv('GROQ_API_KEY')

        # API endpoints
        if self.use_openrouter:
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "groq/compound"  # via OpenRouter
        else:
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = "groq/compound"

        # Cache settings
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
            "avg_latency_ms": 0.0
        }

    async def get_price_forecast(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str] = None,
        mileage: Optional[int] = None,
        condition: Optional[str] = None,
        location: Optional[str] = None
    ) -> PriceForecast:
        """
        Get real-time price forecast for a vehicle.

        Args:
            year: Model year
            make: Vehicle make (e.g., "Ford")
            model: Vehicle model (e.g., "F-250")
            trim: Trim level (e.g., "Lariat")
            mileage: Current odometer reading
            condition: Vehicle condition (Clean/Average/Rough)
            location: Geographic location for regional pricing

        Returns:
            PriceForecast with estimated price and confidence
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Generate cache key
        cache_key = self._get_cache_key(year, make, model, trim, mileage)

        # Check cache first
        if cached := self._get_from_cache(cache_key):
            self.stats["cache_hits"] += 1
            cached.cache_hit = True
            cached.latency_ms = (time.time() - start_time) * 1000
            return cached

        try:
            self.stats["api_calls"] += 1

            # Build the prompt for Groq Compound
            prompt = self._build_price_prompt(
                year, make, model, trim, mileage, condition, location
            )

            # Call Groq Compound
            forecast = await self._call_groq_compound(prompt, year, make, model)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            forecast.latency_ms = latency_ms

            # Update average latency
            total_calls = self.stats["api_calls"]
            self.stats["avg_latency_ms"] = (
                (self.stats["avg_latency_ms"] * (total_calls - 1) + latency_ms) / total_calls
            )

            # Cache the result
            self._store_in_cache(cache_key, forecast)

            logger.info(
                f"Price forecast: {year} {make} {model} -> "
                f"${forecast.estimated_price:,.0f} "
                f"(confidence: {forecast.confidence:.0%}, {latency_ms:.0f}ms)"
            )

            return forecast

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Price forecast failed: {e}")

            # Return a low-confidence fallback
            return PriceForecast(
                estimated_price=0,
                price_low=0,
                price_high=0,
                confidence=0.0,
                sources_used=[],
                comparable_count=0,
                reasoning=f"Unable to generate forecast: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000
            )

    def _build_price_prompt(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str],
        mileage: Optional[int],
        condition: Optional[str],
        location: Optional[str]
    ) -> str:
        """Build the prompt for Groq Compound"""

        vehicle_desc = f"{year} {make} {model}"
        if trim:
            vehicle_desc += f" {trim}"

        mileage_info = f" with {mileage:,} miles" if mileage else ""
        condition_info = f" in {condition} condition" if condition else ""
        location_info = f" in the {location} area" if location else " in the United States"

        return f"""Search for current market prices of a {vehicle_desc}{mileage_info}{condition_info}{location_info}.

I need you to:
1. Search for current listings of comparable {year} {make} {model} vehicles for sale
2. Find at least 5-10 comparable listings if possible
3. Calculate the average, median, and price range (10th to 90th percentile)
4. Consider mileage adjustments (average mileage for this year model is approximately {12000 * (datetime.now().year - year):,} miles)

Return your analysis as a JSON object with this exact structure:
{{
    "estimated_price": <median price as number>,
    "price_low": <10th percentile price as number>,
    "price_high": <90th percentile price as number>,
    "comparable_count": <number of listings found>,
    "sources": ["source1", "source2"],
    "reasoning": "<brief explanation of how you arrived at this estimate>"
}}

Only return the JSON, no other text."""

    async def _call_groq_compound(
        self,
        prompt: str,
        year: int,
        make: str,
        model: str
    ) -> PriceForecast:
        """Call Groq Compound API"""

        headers = {
            "Content-Type": "application/json",
        }

        if self.use_openrouter:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["HTTP-Referer"] = "https://otto.ai"
            headers["X-Title"] = "Otto.AI Price Forecast"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a vehicle pricing expert. Use web search to find current market prices for vehicles. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                timeout=30  # Compound may take longer due to web searches
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Extract executed tools info if available
            executed_tools = result['choices'][0]['message'].get('executed_tools', [])
            sources = [tool.get('name', 'unknown') for tool in executed_tools]

            # Parse the JSON response
            try:
                # Handle markdown code blocks
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]

                data = json.loads(content.strip())

                # Calculate confidence based on data quality
                comparable_count = data.get('comparable_count', 0)
                if comparable_count >= 10:
                    confidence = 0.9
                elif comparable_count >= 5:
                    confidence = 0.75
                elif comparable_count >= 3:
                    confidence = 0.6
                elif comparable_count >= 1:
                    confidence = 0.4
                else:
                    confidence = 0.2

                return PriceForecast(
                    estimated_price=float(data.get('estimated_price', 0)),
                    price_low=float(data.get('price_low', 0)),
                    price_high=float(data.get('price_high', 0)),
                    confidence=confidence,
                    sources_used=data.get('sources', sources),
                    comparable_count=comparable_count,
                    reasoning=data.get('reasoning', '')
                )

            except json.JSONDecodeError:
                # Fallback: try to extract numbers from the response
                logger.warning(f"Could not parse JSON, attempting fallback extraction")
                return self._fallback_parse(content, year, make, model)

    def _fallback_parse(
        self,
        content: str,
        year: int,
        make: str,
        model: str
    ) -> PriceForecast:
        """Fallback parsing when JSON extraction fails"""
        import re

        # Try to find dollar amounts
        prices = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
        prices = [float(p.replace('$', '').replace(',', '')) for p in prices]

        if prices:
            prices.sort()
            estimated = sum(prices) / len(prices)
            return PriceForecast(
                estimated_price=estimated,
                price_low=min(prices),
                price_high=max(prices),
                confidence=0.3,  # Low confidence for fallback
                sources_used=["text_extraction"],
                comparable_count=len(prices),
                reasoning=f"Extracted {len(prices)} prices from response"
            )

        # Complete fallback - return zero with no confidence
        return PriceForecast(
            estimated_price=0,
            price_low=0,
            price_high=0,
            confidence=0.0,
            sources_used=[],
            comparable_count=0,
            reasoning="Could not extract pricing information"
        )

    def _get_cache_key(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str],
        mileage: Optional[int]
    ) -> str:
        """Generate cache key for vehicle"""
        # Bucket mileage into 10k increments for cache efficiency
        mileage_bucket = (mileage // 10000) * 10000 if mileage else 0

        key_data = f"{year}:{make.lower()}:{model.lower()}:{(trim or '').lower()}:{mileage_bucket}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[PriceForecast]:
        """Get from cache if valid"""
        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]
        if datetime.now() - entry.timestamp > self.cache_ttl:
            del self.cache[cache_key]
            return None

        return entry.data

    def _store_in_cache(self, cache_key: str, forecast: PriceForecast):
        """Store in cache"""
        self.cache[cache_key] = CacheEntry(data=forecast, timestamp=datetime.now())

        # Limit cache size
        if len(self.cache) > 1000:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest]

    async def enrich_vehicle_with_price(
        self,
        vehicle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich a vehicle record with price forecast if missing.

        Used during ingestion or on-demand when price is NULL.
        """
        # Skip if already has a price
        if vehicle.get('asking_price') or vehicle.get('estimated_price'):
            return vehicle

        forecast = await self.get_price_forecast(
            year=vehicle.get('year'),
            make=vehicle.get('make'),
            model=vehicle.get('model'),
            trim=vehicle.get('trim'),
            mileage=vehicle.get('odometer'),
            condition=vehicle.get('condition_grade')
        )

        if forecast.confidence >= 0.4:
            vehicle['estimated_price'] = forecast.estimated_price
            vehicle['price_source'] = 'ai_estimate'
            vehicle['price_confidence'] = forecast.confidence
            vehicle['price_updated_at'] = forecast.generated_at.isoformat()

        return vehicle

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            )
        }


# Singleton instance for easy access
_price_service: Optional[PriceForecastService] = None

def get_price_service() -> PriceForecastService:
    """Get or create the price forecast service singleton"""
    global _price_service
    if _price_service is None:
        _price_service = PriceForecastService()
    return _price_service
