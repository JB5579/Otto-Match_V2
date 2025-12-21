"""
Otto.AI Vehicle Intelligence Service

Real-time vehicle intelligence using Groq Compound AI with web search + LLM reasoning.
Provides AI-powered market insights, pricing analysis, and vehicle intelligence.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal
import logging
from enum import Enum

import httpx
from pydantic import BaseModel, Field, validator
import backoff

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIModelType(Enum):
    """Groq AI model types"""
    COMPOUND = "groq/compound"
    COMPOUND_MINI = "groq/compound-mini"


class AIConfidenceLevel(Enum):
    """AI confidence levels for intelligence data"""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.6
    LOW = "low"        # >= 0.4
    VERY_LOW = "very_low"  # < 0.4


@dataclass
class AISource:
    """AI source attribution for intelligence data"""
    source_name: str
    source_url: Optional[str] = None
    source_type: str = "web_search"
    retrieval_date: datetime = Field(default_factory=datetime.now)
    reliability_score: float = 1.0


@dataclass
class MarketInsight:
    """AI-generated market insight"""
    insight_type: str  # "pricing", "demand", "feature_comparison", "market_trend"
    title: str
    description: str
    confidence: float
    sources: List[AISource]
    data_points: Dict[str, Any]
    relevance_score: float = 1.0


@dataclass
class VehicleIntelligence:
    """Complete AI intelligence for a vehicle"""
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: Optional[str] = None

    # Market Analysis
    market_price_range: Optional[Tuple[Decimal, Decimal]] = None
    market_average_price: Optional[Decimal] = None
    price_confidence: float = 0.0

    # Demand & Availability
    market_demand: str = "unknown"  # "high", "medium", "low", "unknown"
    availability_score: float = 0.0  # 0-1, higher = more available
    days_on_market_avg: Optional[int] = None

    # Feature Intelligence
    feature_popularity: Dict[str, float] = None  # feature -> popularity score
    competitive_advantages: List[str] = None
    common_complaints: List[str] = None

    # Market Insights
    insights: List[MarketInsight] = None

    # Metadata
    ai_model_used: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)
    cache_expires_at: Optional[datetime] = None
    confidence_overall: float = 0.0

    def __post_init__(self):
        if self.feature_popularity is None:
            self.feature_popularity = {}
        if self.competitive_advantages is None:
            self.competitive_advantages = []
        if self.common_complaints is None:
            self.common_complaints = []
        if self.insights is None:
            self.insights = []


class GroqCompoundAIClient:
    """Groq Compound AI client with web search + LLM reasoning"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

        self.base_url = "https://api.groq.com/openai/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

        # Request counts for rate limiting
        self.request_count = 0
        self.requests_reset_time = datetime.now() + timedelta(minutes=1)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        base=1,
        max_value=30
    )
    async def _check_rate_limit(self):
        """Check and handle rate limiting"""
        now = datetime.now()

        # Reset counter if minute passed
        if now >= self.requests_reset_time:
            self.request_count = 0
            self.requests_reset_time = now + timedelta(minutes=1)

        # Rate limit: 30 requests per minute for compound models
        if self.request_count >= 25:  # Buffer zone
            sleep_time = (self.requests_reset_time - now).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                self.request_count = 0

    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        base=1,
        max_value=30
    )
    async def _make_request(self, model: str, messages: List[Dict], **kwargs) -> Dict:
        """Make API request with retry logic"""
        await self._check_rate_limit()

        data = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "response_format": kwargs.get("response_format", {"type": "text"}),
            # Note: Groq Compound AI automatically uses web search when needed
            # No additional configuration required for web search
        }

        self.request_count += 1

        try:
            response = await self.client.post("/chat/completions", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException:
            logger.error("Groq API timeout")
            raise

    async def extract_vehicle_intelligence(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str] = None,
        features: Optional[List[str]] = None,
        current_price: Optional[Decimal] = None,
        model_type: AIModelType = AIModelType.COMPOUND_MINI
    ) -> VehicleIntelligence:
        """Extract comprehensive vehicle intelligence using Groq Compound AI"""

        logger.info(f"Extracting intelligence for {year} {make} {model}")

        # Construct the prompt for vehicle intelligence extraction
        prompt = self._construct_intelligence_prompt(
            make=make,
            model=model,
            year=year,
            vin=vin,
            features=features or [],
            current_price=current_price
        )

        messages = [
            {
                "role": "system",
                "content": """You are an expert automotive market analyst AI with real-time access to market data.
Your task is to provide comprehensive vehicle intelligence including pricing, demand, features, and market insights.
ALWAYS cite your sources and provide confidence scores for your analysis.
Use the web search tool to find current market data, pricing trends, and vehicle reviews."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            # Use compound mini for faster processing, fall back to compound if needed
            model_name = model_type.value

            response = await self._make_request(
                model=model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )

            # Parse the AI response
            content = response["choices"][0]["message"]["content"]
            intelligence = self._parse_ai_response(
                content=content,
                make=make,
                model=model,
                year=year,
                vin=vin,
                ai_model_used=model_name
            )

            logger.info(f"Successfully extracted intelligence for {year} {make} {model}")
            return intelligence

        except Exception as e:
            logger.error(f"Error extracting vehicle intelligence: {str(e)}")
            # Return basic intelligence with error state
            return VehicleIntelligence(
                vehicle_id=f"{make}_{model}_{year}",
                make=make,
                model=model,
                year=year,
                vin=vin,
                confidence_overall=0.0,
                ai_model_used=model_type.value,
                insights=[
                    MarketInsight(
                        insight_type="error",
                        title="AI Intelligence Unavailable",
                        description=f"Unable to fetch AI intelligence: {str(e)}",
                        confidence=0.0,
                        sources=[],
                        data_points={}
                    )
                ]
            )

    def _construct_intelligence_prompt(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str],
        features: List[str],
        current_price: Optional[Decimal]
    ) -> str:
        """Construct detailed prompt for vehicle intelligence extraction"""

        prompt = f"""
Analyze the following vehicle and provide comprehensive market intelligence:

VEHICLE DETAILS:
- Make: {make}
- Model: {model}
- Year: {year}
"""

        if vin:
            prompt += f"- VIN: {vin}\n"

        if current_price:
            prompt += f"- Current Price: ${current_price:,.2f}\n"

        if features:
            prompt += f"- Notable Features: {', '.join(features)}\n"

        prompt += """

REQUIRED ANALYSIS (provide specific data with sources):

1. MARKET PRICING:
   - Current market price range (based on recent sales)
   - Market average price
   - Price confidence level (0-1)
   - Price trend (increasing/decreasing/stable)

2. DEMAND & AVAILABILITY:
   - Market demand level (high/medium/low)
   - Average days on market
   - Availability score (0-1, higher = more available)

3. FEATURE INTELLIGENCE:
   - Feature popularity scores (0-1 for each notable feature)
   - Competitive advantages vs similar vehicles
   - Common complaints or issues

4. MARKET INSIGHTS:
   - 3-5 key insights about this vehicle in the current market
   - Each insight should include: title, description, confidence score (0-1), and sources

RESPONSE FORMAT:
Respond with structured data that can be easily parsed. Include specific numbers, confidence scores, and web sources for all claims.
Format your response clearly with sections for each analysis area.
"""

        return prompt

    def _parse_ai_response(
        self,
        content: str,
        make: str,
        model: str,
        year: int,
        vin: Optional[str],
        ai_model_used: str
    ) -> VehicleIntelligence:
        """Parse AI response and create VehicleIntelligence object"""

        intelligence = VehicleIntelligence(
            vehicle_id=f"{make}_{model}_{year}",
            make=make,
            model=model,
            year=year,
            vin=vin,
            ai_model_used=ai_model_used,
            cache_expires_at=datetime.now() + timedelta(hours=24)  # Cache for 24 hours
        )

        # Parse pricing information
        intelligence = self._parse_pricing_info(content, intelligence)

        # Parse demand and availability
        intelligence = self._parse_demand_info(content, intelligence)

        # Parse feature intelligence
        intelligence = self._parse_feature_intelligence(content, intelligence)

        # Parse market insights
        intelligence = self._parse_market_insights(content, intelligence)

        # Calculate overall confidence
        intelligence.confidence_overall = self._calculate_overall_confidence(intelligence)

        return intelligence

    def _parse_pricing_info(self, content: str, intelligence: VehicleIntelligence) -> VehicleIntelligence:
        """Parse pricing information from AI response"""
        lines = content.split('\n')

        for line in lines:
            line_lower = line.lower()

            # Look for price range
            if 'price range' in line_lower or 'market range' in line_lower:
                # Extract price range using various patterns
                import re
                price_range_match = re.search(r'\$?([\d,]+)\s*[-–to]\s*\$?([\d,]+)', line)
                if price_range_match:
                    try:
                        min_price = Decimal(price_range_match.group(1).replace(',', ''))
                        max_price = Decimal(price_range_match.group(2).replace(',', ''))
                        intelligence.market_price_range = (min_price, max_price)
                    except:
                        pass

            # Look for average price
            elif 'average price' in line_lower or 'market average' in line_lower:
                import re
                avg_price_match = re.search(r'\$?([\d,]+)', line)
                if avg_price_match:
                    try:
                        avg_price = Decimal(avg_price_match.group(1).replace(',', ''))
                        intelligence.market_average_price = avg_price
                    except:
                        pass

            # Look for confidence
            elif 'confidence' in line_lower and ('price' in line_lower or 'pricing' in line_lower):
                import re
                confidence_match = re.search(r'(\d+\.?\d*)', line)
                if confidence_match:
                    try:
                        confidence = float(confidence_match.group(1))
                        if confidence <= 1.0:
                            intelligence.price_confidence = confidence
                        elif confidence <= 100:
                            intelligence.price_confidence = confidence / 100
                    except:
                        pass

        return intelligence

    def _parse_demand_info(self, content: str, intelligence: VehicleIntelligence) -> VehicleIntelligence:
        """Parse demand and availability information"""
        lines = content.split('\n')

        for line in lines:
            line_lower = line.lower()

            # Parse demand level
            if 'demand' in line_lower:
                if 'high' in line_lower:
                    intelligence.market_demand = "high"
                elif 'medium' in line_lower or 'moderate' in line_lower:
                    intelligence.market_demand = "medium"
                elif 'low' in line_lower:
                    intelligence.market_demand = "low"

            # Parse days on market
            elif 'days on market' in line_lower or 'average days' in line_lower:
                import re
                days_match = re.search(r'(\d+)', line)
                if days_match:
                    try:
                        intelligence.days_on_market_avg = int(days_match.group(1))
                    except:
                        pass

            # Parse availability score
            elif 'availability' in line_lower and 'score' in line_lower:
                import re
                score_match = re.search(r'(\d+\.?\d*)', line)
                if score_match:
                    try:
                        score = float(score_match.group(1))
                        if score > 1.0:
                            score = score / 100
                        intelligence.availability_score = min(1.0, max(0.0, score))
                    except:
                        pass

        return intelligence

    def _parse_feature_intelligence(self, content: str, intelligence: VehicleIntelligence) -> VehicleIntelligence:
        """Parse feature intelligence from AI response"""
        lines = content.split('\n')
        current_section = None

        for line in lines:
            line_lower = line.lower()

            if 'competitive advantage' in line_lower or 'advantage' in line_lower:
                current_section = 'advantages'
            elif 'complaint' in line_lower or 'issue' in line_lower or 'problem' in line_lower:
                current_section = 'complaints'
            elif 'popular' in line_lower and 'feature' in line_lower:
                current_section = 'popularity'
            elif line.strip().startswith('-') or line.strip().startswith('•'):
                # Parse bullet points
                item = line.strip().lstrip('-•').strip()

                if current_section == 'advantages' and item:
                    intelligence.competitive_advantages.append(item)
                elif current_section == 'complaints' and item:
                    intelligence.common_complaints.append(item)
                elif current_section == 'popularity' and item:
                    # Try to extract feature name and score
                    if ':' in item:
                        feature_part, score_part = item.split(':', 1)
                        feature = feature_part.strip()
                        try:
                            score_str = score_part.strip().rstrip('%')
                            score = float(score_str)
                            if score > 1.0:
                                score = score / 100
                            intelligence.feature_popularity[feature] = score
                        except:
                            intelligence.feature_popularity[feature] = 0.5  # Default

        return intelligence

    def _parse_market_insights(self, content: str, intelligence: VehicleIntelligence) -> VehicleIntelligence:
        """Parse market insights from AI response"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        lines = content.split('\n')
        current_insight = {}

        for line in lines:
            line_lower = line.lower()

            if 'insight' in line_lower or ('trend' in line_lower and not 'price trend' in line_lower):
                if current_insight:
                    # Save previous insight
                    insight = MarketInsight(
                        insight_type="market_trend",
                        title=current_insight.get('title', ''),
                        description=current_insight.get('description', ''),
                        confidence=current_insight.get('confidence', 0.5),
                        sources=[],
                        data_points={}
                    )
                    intelligence.insights.append(insight)

                # Start new insight
                current_insight = {'title': line.strip()}
            elif current_insight and ('description' in line_lower or ':' in line):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key_lower = key.strip().lower()

                    if 'description' in key_lower or 'detail' in key_lower:
                        current_insight['description'] = value.strip()
                    elif 'confidence' in key_lower:
                        try:
                            conf_str = value.strip().rstrip('%')
                            confidence = float(conf_str)
                            if confidence > 1.0:
                                confidence = confidence / 100
                            current_insight['confidence'] = confidence
                        except:
                            current_insight['confidence'] = 0.5

        # Save last insight
        if current_insight:
            insight = MarketInsight(
                insight_type="market_trend",
                title=current_insight.get('title', ''),
                description=current_insight.get('description', ''),
                confidence=current_insight.get('confidence', 0.5),
                sources=[],
                data_points={}
            )
            intelligence.insights.append(insight)

        return intelligence

    def _calculate_overall_confidence(self, intelligence: VehicleIntelligence) -> float:
        """Calculate overall confidence score for the intelligence"""
        scores = []

        # Price confidence
        scores.append(intelligence.price_confidence)

        # Insight confidences
        for insight in intelligence.insights:
            scores.append(insight.confidence)

        # If we have no scores, return low confidence
        if not scores:
            return 0.1

        # Return average confidence
        return sum(scores) / len(scores)


class VehicleIntelligenceService:
    """Service for managing vehicle intelligence operations"""

    def __init__(self):
        self.client = None
        self._cache: Dict[str, VehicleIntelligence] = {}
        self.cache_ttl = timedelta(hours=24)

    async def get_vehicle_intelligence(
        self,
        make: str,
        model: str,
        year: int,
        vin: Optional[str] = None,
        features: Optional[List[str]] = None,
        current_price: Optional[Decimal] = None,
        force_refresh: bool = False
    ) -> VehicleIntelligence:
        """Get vehicle intelligence with caching"""

        vehicle_key = f"{make}_{model}_{year}_{vin or 'novin'}"

        # Check cache first
        if not force_refresh and vehicle_key in self._cache:
            cached = self._cache[vehicle_key]
            if cached.cache_expires_at and datetime.now() < cached.cache_expires_at:
                logger.info(f"Using cached intelligence for {vehicle_key}")
                return cached

        # Fetch fresh intelligence
        async with GroqCompoundAIClient() as client:
            intelligence = await client.extract_vehicle_intelligence(
                make=make,
                model=model,
                year=year,
                vin=vin,
                features=features,
                current_price=current_price,
                model_type=AIModelType.COMPOUND_MINI  # Use mini for speed
            )

            # Cache the result
            self._cache[vehicle_key] = intelligence

            # Clean old cache entries
            await self._clean_expired_cache()

            return intelligence

    async def _clean_expired_cache(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = [
            key for key, intelligence in self._cache.items()
            if intelligence.cache_expires_at and now >= intelligence.cache_expires_at
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")

    async def batch_get_intelligence(
        self,
        vehicles: List[Dict[str, Any]],
        force_refresh: bool = False
    ) -> List[VehicleIntelligence]:
        """Get intelligence for multiple vehicles in batch"""

        tasks = []
        for vehicle in vehicles:
            task = self.get_vehicle_intelligence(
                make=vehicle['make'],
                model=vehicle['model'],
                year=vehicle['year'],
                vin=vehicle.get('vin'),
                features=vehicle.get('features'),
                current_price=vehicle.get('price'),
                force_refresh=force_refresh
            )
            tasks.append(task)

        # Execute with concurrency limit to avoid rate limiting
        results = []
        batch_size = 3  # Conservative batch size for rate limiting

        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch intelligence error: {result}")
                    # Create placeholder intelligence
                    results.append(VehicleIntelligence(
                        vehicle_id="error",
                        make="unknown",
                        model="unknown",
                        year=2024,
                        confidence_overall=0.0
                    ))
                else:
                    results.append(result)

            # Rate limiting pause between batches
            if i + batch_size < len(tasks):
                await asyncio.sleep(2)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        valid_entries = sum(
            1 for intel in self._cache.values()
            if not intel.cache_expires_at or datetime.now() < intel.cache_expires_at
        )

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries
        }


# Export the service instance
vehicle_intelligence_service = VehicleIntelligenceService()


async def get_vehicle_intelligence_service() -> VehicleIntelligenceService:
    """Get the singleton vehicle intelligence service instance"""
    return vehicle_intelligence_service