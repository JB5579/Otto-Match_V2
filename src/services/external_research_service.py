"""
Otto.AI External Research Service - Phase 2

Uses Groq Compound to provide ownership research beyond inventory data.
This service enables Otto to make informed recommendations by pulling real-world
ownership costs, owner experiences, and financial analysis.

Research Types:
1. Ownership Costs - Insurance, maintenance, depreciation, 5-year TCO
2. Owner Experiences - Forum sentiment, common issues, satisfaction scores
3. Lease vs Buy Analysis - Financial comparison for user's situation
4. Insurance Delta - Premium change from current to new vehicle

Based on conversation simulation analysis where Otto explicitly offers:
"I can pull real ownership cost data from outside our listings"
"""

import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ResearchType(Enum):
    """Types of external research available"""
    OWNERSHIP_COSTS = "ownership_costs"
    OWNER_EXPERIENCES = "owner_experiences"
    LEASE_VS_BUY = "lease_vs_buy"
    INSURANCE_DELTA = "insurance_delta"


class OwnershipCostReport(BaseModel):
    """Total cost of ownership research"""
    # Annual costs
    insurance_annual: float = Field(0.0, description="Estimated annual insurance premium")
    maintenance_annual: float = Field(0.0, description="Average annual maintenance cost")
    fuel_annual: float = Field(0.0, description="Estimated annual fuel/energy cost")
    registration_annual: float = Field(0.0, description="Annual registration/tax")

    # Depreciation
    depreciation_year1: float = Field(0.0, description="First year depreciation")
    depreciation_5year: float = Field(0.0, description="5-year total depreciation")
    resale_value_5year: float = Field(0.0, description="Estimated value after 5 years")

    # Totals
    total_year1: float = Field(0.0, description="Total first year cost")
    total_5year: float = Field(0.0, description="Total 5-year ownership cost")
    cost_per_month: float = Field(0.0, description="Average monthly cost over 5 years")

    # Metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in estimates")
    sources_used: List[str] = Field(default_factory=list)
    reasoning: str = Field("", description="Explanation of cost breakdown")
    generated_at: datetime = Field(default_factory=datetime.now)


class OwnerExperienceReport(BaseModel):
    """Owner experience and satisfaction research"""
    # Ratings
    overall_satisfaction: float = Field(0.0, ge=0.0, le=5.0, description="Overall satisfaction (1-5)")
    reliability_rating: float = Field(0.0, ge=0.0, le=5.0, description="Reliability rating (1-5)")
    value_rating: float = Field(0.0, ge=0.0, le=5.0, description="Value for money (1-5)")

    # Common issues
    common_problems: List[str] = Field(default_factory=list, description="Frequently mentioned problems")
    common_praises: List[str] = Field(default_factory=list, description="Frequently mentioned positives")

    # Sentiment analysis
    positive_sentiment: float = Field(0.0, ge=0.0, le=1.0, description="% of positive reviews")
    negative_sentiment: float = Field(0.0, ge=0.0, le=1.0, description="% of negative reviews")
    review_count: int = Field(0, description="Number of reviews analyzed")

    # Key insights
    would_recommend: float = Field(0.0, ge=0.0, le=1.0, description="% who would recommend")
    key_insights: List[str] = Field(default_factory=list, description="Notable patterns or insights")

    # Metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    sources_used: List[str] = Field(default_factory=list)
    reasoning: str = Field("")
    generated_at: datetime = Field(default_factory=datetime.now)


class LeaseVsBuyReport(BaseModel):
    """Lease vs buy financial comparison"""
    # Purchase option
    purchase_total_5year: float = Field(0.0, description="Total cost to own for 5 years")
    purchase_monthly_avg: float = Field(0.0, description="Average monthly cost (financing + ownership)")
    purchase_equity_5year: float = Field(0.0, description="Equity built after 5 years")

    # Lease option
    lease_total_5year: float = Field(0.0, description="Total lease payments for 5 years")
    lease_monthly_avg: float = Field(0.0, description="Average monthly lease payment")
    lease_equity_5year: float = Field(0.0, description="Equity (typically $0)")

    # Comparison
    cost_difference: float = Field(0.0, description="Difference in total cost (lease - purchase)")
    breakeven_years: float = Field(0.0, description="Years until purchase becomes cheaper")
    recommendation: str = Field("", description="Recommendation based on user's situation")

    # Assumptions
    purchase_down_payment: float = Field(0.0)
    purchase_interest_rate: float = Field(0.0, description="APR as decimal")
    lease_down_payment: float = Field(0.0)
    lease_money_factor: float = Field(0.0)
    annual_mileage: int = Field(12000)
    lease_mileage_limit: int = Field(12000)

    # Metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    sources_used: List[str] = Field(default_factory=list)
    reasoning: str = Field("")
    generated_at: datetime = Field(default_factory=datetime.now)


class InsuranceDeltaReport(BaseModel):
    """Insurance premium change estimation"""
    current_vehicle_premium: float = Field(0.0, description="Estimated current vehicle premium")
    new_vehicle_premium: float = Field(0.0, description="Estimated new vehicle premium")
    annual_delta: float = Field(0.0, description="Difference in annual premium")
    monthly_delta: float = Field(0.0, description="Difference in monthly premium")
    percent_change: float = Field(0.0, description="% change in premium")

    # Factors affecting change
    factors: List[str] = Field(default_factory=list, description="Factors driving the change")

    # Metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    sources_used: List[str] = Field(default_factory=list)
    reasoning: str = Field("")
    generated_at: datetime = Field(default_factory=datetime.now)


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: Any
    timestamp: datetime


# ============================================================================
# External Research Service
# ============================================================================

class ExternalResearchService:
    """
    External research service using Groq Compound for real-world vehicle data.

    Otto explicitly offers this in conversations:
    - "I can pull real ownership cost data from outside our listings"
    - "Let me see what actual owners are saying about this vehicle"
    - "I can run a lease vs buy analysis for your situation"

    This service extends Groq Compound beyond pricing to provide comprehensive
    ownership research that influences buying decisions.
    """

    def __init__(self, cache_ttl_hours: int = 168):  # 7 days default
        self.api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        self.use_openrouter = not os.getenv('GROQ_API_KEY')

        # API endpoints
        if self.use_openrouter:
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "groq/compound"
        else:
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = "groq/compound"

        # Cache settings (longer TTL for ownership data that doesn't change daily)
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
            "ownership_cost_requests": 0,
            "owner_experience_requests": 0,
            "lease_vs_buy_requests": 0,
            "insurance_delta_requests": 0,
        }

    # ========================================================================
    # Ownership Costs Research
    # ========================================================================

    async def get_ownership_costs(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str] = None,
        purchase_price: Optional[float] = None,
        annual_mileage: int = 12000,
        location: Optional[str] = None
    ) -> OwnershipCostReport:
        """
        Research total cost of ownership including insurance, maintenance,
        depreciation, and fuel costs.

        This answers the question: "What will this vehicle actually cost me?"
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["ownership_cost_requests"] += 1

        cache_key = self._get_cache_key(
            "ownership", f"{year}:{make}:{model}:{trim}:{annual_mileage}"
        )

        if cached := self._get_from_cache(cache_key):
            self.stats["cache_hits"] += 1
            return cached

        try:
            self.stats["api_calls"] += 1

            prompt = self._build_ownership_cost_prompt(
                year, make, model, trim, purchase_price, annual_mileage, location
            )

            result = await self._call_groq_compound(prompt, "ownership cost research")

            report = self._parse_ownership_cost_response(result)
            report.generated_at = datetime.now()

            self._store_in_cache(cache_key, report)

            logger.info(
                f"Ownership cost research: {year} {make} {model} -> "
                f"${report.cost_per_month:,.0f}/mo over 5 years "
                f"(confidence: {report.confidence:.0%})"
            )

            return report

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Ownership cost research failed: {e}")
            return OwnershipCostReport(confidence=0.0, reasoning=f"Error: {str(e)}")

    def _build_ownership_cost_prompt(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str],
        purchase_price: Optional[float],
        annual_mileage: int,
        location: Optional[str]
    ) -> str:
        """Build prompt for ownership cost research"""

        vehicle_desc = f"{year} {make} {model}"
        if trim:
            vehicle_desc += f" {trim}"

        price_context = f"Purchase price: ${purchase_price:,.0f}. " if purchase_price else ""
        location_context = f" in {location}" if location else ""

        return f"""Research the total cost of ownership for a {vehicle_desc}{location_context}.

{price_context}Annual mileage: {annual_mileage:,} miles.

I need comprehensive ownership cost data:

1. **Insurance**: Average annual premium for this vehicle
2. **Maintenance**: Average annual maintenance and repair costs
3. **Fuel/Energy**: Estimated annual fuel or electricity cost (based on {annual_mileage} miles/year)
4. **Registration**: Average annual registration and taxes
5. **Depreciation**: First year and 5-year depreciation estimates

Calculate:
- Total first year cost (all costs + depreciation)
- Total 5-year cost of ownership
- Average monthly cost over 5 years
- Estimated resale value after 5 years

Search for real data from:
- Insurance cost databases
- Consumer Reports
- Edmunds TCO data
- Owner forums and surveys
- Manufacturer maintenance schedules

Return ONLY a JSON object with this structure:
{{
    "insurance_annual": <number>,
    "maintenance_annual": <number>,
    "fuel_annual": <number>,
    "registration_annual": <number>,
    "depreciation_year1": <number>,
    "depreciation_5year": <number>,
    "resale_value_5year": <number>,
    "total_year1": <number>,
    "total_5year": <number>,
    "cost_per_month": <number>,
    "sources": ["source1", "source2"],
    "reasoning": "<brief explanation of cost breakdown and data sources>"
}}"""

    def _parse_ownership_cost_response(self, content: str) -> OwnershipCostReport:
        """Parse Groq Compound response into OwnershipCostReport"""
        try:
            # Handle markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            data = json.loads(content.strip())

            # Calculate confidence based on data completeness
            fields_present = sum([
                bool(data.get('insurance_annual')),
                bool(data.get('maintenance_annual')),
                bool(data.get('fuel_annual')),
                bool(data.get('depreciation_5year')),
                bool(data.get('total_5year')),
            ])
            confidence = min(0.9, fields_present / 5.0)

            return OwnershipCostReport(
                insurance_annual=float(data.get('insurance_annual', 0)),
                maintenance_annual=float(data.get('maintenance_annual', 0)),
                fuel_annual=float(data.get('fuel_annual', 0)),
                registration_annual=float(data.get('registration_annual', 0)),
                depreciation_year1=float(data.get('depreciation_year1', 0)),
                depreciation_5year=float(data.get('depreciation_5year', 0)),
                resale_value_5year=float(data.get('resale_value_5year', 0)),
                total_year1=float(data.get('total_year1', 0)),
                total_5year=float(data.get('total_5year', 0)),
                cost_per_month=float(data.get('cost_per_month', 0)),
                confidence=confidence,
                sources_used=data.get('sources', []),
                reasoning=data.get('reasoning', '')
            )

        except Exception as e:
            logger.error(f"Failed to parse ownership cost response: {e}")
            return OwnershipCostReport(
                confidence=0.0,
                reasoning=f"Parse error: {str(e)}"
            )

    # ========================================================================
    # Owner Experience Research
    # ========================================================================

    async def get_owner_experiences(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str] = None
    ) -> OwnerExperienceReport:
        """
        Research real owner experiences from forums, reviews, and surveys.

        This answers: "What do actual owners say about this vehicle?"
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["owner_experience_requests"] += 1

        cache_key = self._get_cache_key("experience", f"{year}:{make}:{model}:{trim}")

        if cached := self._get_from_cache(cache_key):
            self.stats["cache_hits"] += 1
            return cached

        try:
            self.stats["api_calls"] += 1

            prompt = self._build_owner_experience_prompt(year, make, model, trim)
            result = await self._call_groq_compound(prompt, "owner experience research")
            report = self._parse_owner_experience_response(result)
            report.generated_at = datetime.now()

            self._store_in_cache(cache_key, report)

            logger.info(
                f"Owner experience research: {year} {make} {model} -> "
                f"{report.overall_satisfaction:.1f}/5.0 satisfaction, "
                f"{report.review_count} reviews analyzed"
            )

            return report

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Owner experience research failed: {e}")
            return OwnerExperienceReport(confidence=0.0, reasoning=f"Error: {str(e)}")

    def _build_owner_experience_prompt(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str]
    ) -> str:
        """Build prompt for owner experience research"""

        vehicle_desc = f"{year} {make} {model}"
        if trim:
            vehicle_desc += f" {trim}"

        return f"""Research real owner experiences and satisfaction for the {vehicle_desc}.

Search owner forums, review sites, Consumer Reports, J.D. Power, and automotive sites for:

1. **Overall Satisfaction**: Average owner satisfaction rating (1-5 scale)
2. **Reliability Rating**: How reliable owners find this vehicle (1-5 scale)
3. **Value Rating**: Value for money perception (1-5 scale)
4. **Common Problems**: Top 3-5 frequently mentioned issues or complaints
5. **Common Praises**: Top 3-5 frequently mentioned positive aspects
6. **Sentiment Analysis**: Percentage of positive vs negative reviews
7. **Recommendation**: What percentage would recommend to others
8. **Key Insights**: Notable patterns or important things buyers should know

Focus on finding real owner voices, not just professional reviews.

Return ONLY a JSON object with this structure:
{{
    "overall_satisfaction": <number 0-5>,
    "reliability_rating": <number 0-5>,
    "value_rating": <number 0-5>,
    "common_problems": ["problem1", "problem2", "problem3"],
    "common_praises": ["praise1", "praise2", "praise3"],
    "positive_sentiment": <0.0-1.0>,
    "negative_sentiment": <0.0-1.0>,
    "review_count": <number of reviews analyzed>,
    "would_recommend": <0.0-1.0>,
    "key_insights": ["insight1", "insight2"],
    "sources": ["source1", "source2"],
    "reasoning": "<brief explanation of findings>"
}}"""

    def _parse_owner_experience_response(self, content: str) -> OwnerExperienceReport:
        """Parse owner experience response"""
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            data = json.loads(content.strip())

            # Confidence based on review count and data completeness
            review_count = data.get('review_count', 0)
            if review_count >= 50:
                confidence = 0.9
            elif review_count >= 20:
                confidence = 0.75
            elif review_count >= 10:
                confidence = 0.6
            else:
                confidence = 0.4

            return OwnerExperienceReport(
                overall_satisfaction=float(data.get('overall_satisfaction', 0)),
                reliability_rating=float(data.get('reliability_rating', 0)),
                value_rating=float(data.get('value_rating', 0)),
                common_problems=data.get('common_problems', []),
                common_praises=data.get('common_praises', []),
                positive_sentiment=float(data.get('positive_sentiment', 0)),
                negative_sentiment=float(data.get('negative_sentiment', 0)),
                review_count=int(data.get('review_count', 0)),
                would_recommend=float(data.get('would_recommend', 0)),
                key_insights=data.get('key_insights', []),
                confidence=confidence,
                sources_used=data.get('sources', []),
                reasoning=data.get('reasoning', '')
            )

        except Exception as e:
            logger.error(f"Failed to parse owner experience response: {e}")
            return OwnerExperienceReport(
                confidence=0.0,
                reasoning=f"Parse error: {str(e)}"
            )

    # ========================================================================
    # Lease vs Buy Analysis
    # ========================================================================

    async def get_lease_vs_buy_analysis(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str] = None,
        msrp: Optional[float] = None,
        annual_mileage: int = 12000,
        credit_score: Optional[int] = None,
        down_payment: float = 0,
        user_situation: Optional[str] = None
    ) -> LeaseVsBuyReport:
        """
        Compare lease vs purchase options for user's specific situation.

        This answers: "Should I lease or buy this vehicle?"
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["lease_vs_buy_requests"] += 1

        # Don't cache this - it's user-situation specific
        try:
            self.stats["api_calls"] += 1

            prompt = self._build_lease_vs_buy_prompt(
                year, make, model, trim, msrp, annual_mileage,
                credit_score, down_payment, user_situation
            )

            result = await self._call_groq_compound(prompt, "lease vs buy analysis")
            report = self._parse_lease_vs_buy_response(result)
            report.generated_at = datetime.now()

            logger.info(
                f"Lease vs buy analysis: {year} {make} {model} -> "
                f"${report.cost_difference:,.0f} difference, "
                f"recommendation: {report.recommendation[:50]}..."
            )

            return report

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Lease vs buy analysis failed: {e}")
            return LeaseVsBuyReport(confidence=0.0, reasoning=f"Error: {str(e)}")

    def _build_lease_vs_buy_prompt(
        self,
        year: int,
        make: str,
        model: str,
        trim: Optional[str],
        msrp: Optional[float],
        annual_mileage: int,
        credit_score: Optional[int],
        down_payment: float,
        user_situation: Optional[str]
    ) -> str:
        """Build prompt for lease vs buy analysis"""

        vehicle_desc = f"{year} {make} {model}"
        if trim:
            vehicle_desc += f" {trim}"

        price_context = f"MSRP: ${msrp:,.0f}. " if msrp else ""
        credit_context = f"Credit score: {credit_score}. " if credit_score else "Assume good credit (720+). "
        situation_context = f"\n\nUser's situation: {user_situation}" if user_situation else ""

        return f"""Perform a lease vs buy financial analysis for a {vehicle_desc}.

{price_context}{credit_context}Down payment available: ${down_payment:,.0f}.
Annual mileage: {annual_mileage:,} miles.{situation_context}

Research current lease and financing offers for this vehicle. Calculate:

**Purchase Option (5-year financing):**
- Total 5-year cost (payments + ownership costs)
- Average monthly cost
- Equity after 5 years (resale value - remaining loan)

**Lease Option (3-year lease, then new lease):**
- Total 5-year cost (lease payments + fees)
- Average monthly payment
- Equity (typically $0)

**Comparison:**
- Which option costs less over 5 years?
- When does purchase become cheaper (breakeven)?
- Recommendation based on user's situation

Consider:
- Current interest rates and money factors
- Depreciation rates for this model
- Lease-end fees and restrictions
- User's mileage needs vs lease limits

Return ONLY a JSON object:
{{
    "purchase_total_5year": <number>,
    "purchase_monthly_avg": <number>,
    "purchase_equity_5year": <number>,
    "lease_total_5year": <number>,
    "lease_monthly_avg": <number>,
    "lease_equity_5year": 0,
    "cost_difference": <lease total - purchase total>,
    "breakeven_years": <number>,
    "recommendation": "<which option and why>",
    "purchase_down_payment": <number>,
    "purchase_interest_rate": <APR as decimal, e.g., 0.065>,
    "lease_down_payment": <number>,
    "lease_money_factor": <number>,
    "annual_mileage": {annual_mileage},
    "lease_mileage_limit": <typical limit>,
    "sources": ["source1", "source2"],
    "reasoning": "<explanation of analysis>"
}}"""

    def _parse_lease_vs_buy_response(self, content: str) -> LeaseVsBuyReport:
        """Parse lease vs buy response"""
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            data = json.loads(content.strip())

            return LeaseVsBuyReport(
                purchase_total_5year=float(data.get('purchase_total_5year', 0)),
                purchase_monthly_avg=float(data.get('purchase_monthly_avg', 0)),
                purchase_equity_5year=float(data.get('purchase_equity_5year', 0)),
                lease_total_5year=float(data.get('lease_total_5year', 0)),
                lease_monthly_avg=float(data.get('lease_monthly_avg', 0)),
                lease_equity_5year=float(data.get('lease_equity_5year', 0)),
                cost_difference=float(data.get('cost_difference', 0)),
                breakeven_years=float(data.get('breakeven_years', 0)),
                recommendation=data.get('recommendation', ''),
                purchase_down_payment=float(data.get('purchase_down_payment', 0)),
                purchase_interest_rate=float(data.get('purchase_interest_rate', 0)),
                lease_down_payment=float(data.get('lease_down_payment', 0)),
                lease_money_factor=float(data.get('lease_money_factor', 0)),
                annual_mileage=int(data.get('annual_mileage', 12000)),
                lease_mileage_limit=int(data.get('lease_mileage_limit', 12000)),
                confidence=0.8,  # Reasonable confidence for financial calculations
                sources_used=data.get('sources', []),
                reasoning=data.get('reasoning', '')
            )

        except Exception as e:
            logger.error(f"Failed to parse lease vs buy response: {e}")
            return LeaseVsBuyReport(
                confidence=0.0,
                reasoning=f"Parse error: {str(e)}"
            )

    # ========================================================================
    # Insurance Delta Estimation
    # ========================================================================

    async def get_insurance_delta(
        self,
        current_vehicle: Dict[str, Any],
        new_vehicle: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> InsuranceDeltaReport:
        """
        Estimate insurance premium change from current to new vehicle.

        This answers: "How much will my insurance change?"
        """
        self.stats["total_requests"] += 1
        self.stats["insurance_delta_requests"] += 1

        try:
            self.stats["api_calls"] += 1

            prompt = self._build_insurance_delta_prompt(
                current_vehicle, new_vehicle, user_profile
            )

            result = await self._call_groq_compound(prompt, "insurance delta research")
            report = self._parse_insurance_delta_response(result)
            report.generated_at = datetime.now()

            logger.info(
                f"Insurance delta: ${report.monthly_delta:+.0f}/mo "
                f"({report.percent_change:+.0%})"
            )

            return report

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Insurance delta research failed: {e}")
            return InsuranceDeltaReport(confidence=0.0, reasoning=f"Error: {str(e)}")

    def _build_insurance_delta_prompt(
        self,
        current_vehicle: Dict[str, Any],
        new_vehicle: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for insurance delta estimation"""

        current_desc = f"{current_vehicle.get('year')} {current_vehicle.get('make')} {current_vehicle.get('model')}"
        new_desc = f"{new_vehicle.get('year')} {new_vehicle.get('make')} {new_vehicle.get('model')}"

        profile_context = ""
        if user_profile:
            profile_context = f"\nDriver profile: {json.dumps(user_profile)}"

        return f"""Estimate the insurance premium change when switching vehicles.

Current vehicle: {current_desc}
New vehicle: {new_desc}{profile_context}

Research typical insurance premiums for both vehicles and calculate:
1. Estimated annual premium for current vehicle
2. Estimated annual premium for new vehicle
3. Annual and monthly difference
4. Percent change
5. Key factors driving the change (safety ratings, theft rates, repair costs, etc.)

Return ONLY a JSON object:
{{
    "current_vehicle_premium": <number>,
    "new_vehicle_premium": <number>,
    "annual_delta": <new - current>,
    "monthly_delta": <annual_delta / 12>,
    "percent_change": <decimal, e.g., 0.15 for 15% increase>,
    "factors": ["factor1", "factor2"],
    "sources": ["source1", "source2"],
    "reasoning": "<explanation>"
}}"""

    def _parse_insurance_delta_response(self, content: str) -> InsuranceDeltaReport:
        """Parse insurance delta response"""
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            data = json.loads(content.strip())

            return InsuranceDeltaReport(
                current_vehicle_premium=float(data.get('current_vehicle_premium', 0)),
                new_vehicle_premium=float(data.get('new_vehicle_premium', 0)),
                annual_delta=float(data.get('annual_delta', 0)),
                monthly_delta=float(data.get('monthly_delta', 0)),
                percent_change=float(data.get('percent_change', 0)),
                factors=data.get('factors', []),
                confidence=0.7,  # Moderate confidence for insurance estimates
                sources_used=data.get('sources', []),
                reasoning=data.get('reasoning', '')
            )

        except Exception as e:
            logger.error(f"Failed to parse insurance delta response: {e}")
            return InsuranceDeltaReport(
                confidence=0.0,
                reasoning=f"Parse error: {str(e)}"
            )

    # ========================================================================
    # Groq Compound API Integration
    # ========================================================================

    async def _call_groq_compound(
        self,
        prompt: str,
        research_type: str
    ) -> str:
        """Call Groq Compound API with web search capabilities"""

        headers = {
            "Content-Type": "application/json",
        }

        if self.use_openrouter:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["HTTP-Referer"] = "https://otto.ai"
            headers["X-Title"] = f"Otto.AI {research_type}"
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
                            "content": f"You are an automotive research expert performing {research_type}. Use web search to find accurate, current data. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=45  # Longer timeout for complex research
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")

            result = response.json()
            content = result['choices'][0]['message']['content']

            return content

    # ========================================================================
    # Caching and Utilities
    # ========================================================================

    def _get_cache_key(self, research_type: str, params: str) -> str:
        """Generate cache key"""
        key_data = f"{research_type}:{params}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get from cache if valid"""
        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]
        if datetime.now() - entry.timestamp > self.cache_ttl:
            del self.cache[cache_key]
            return None

        return entry.data

    def _store_in_cache(self, cache_key: str, data: Any):
        """Store in cache"""
        self.cache[cache_key] = CacheEntry(data=data, timestamp=datetime.now())

        # Limit cache size
        if len(self.cache) > 500:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest]

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


# Singleton instance
_research_service: Optional[ExternalResearchService] = None

def get_research_service() -> ExternalResearchService:
    """Get or create the external research service singleton"""
    global _research_service
    if _research_service is None:
        _research_service = ExternalResearchService()
    return _research_service
