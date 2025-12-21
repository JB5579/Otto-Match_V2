"""
Otto.AI Conversation Market Data Enhancer
Enhances conversation responses with real-time market intelligence
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.enhanced_market_data_service import get_enhanced_market_data_service
from ..services.grok_mini_web_scraper import MarketAnalysisResult

logger = logging.getLogger(__name__)


class ConversationMarketDataEnhancer:
    """
    Enhances conversation responses with market data insights
    """

    def __init__(self):
        self.market_service = get_enhanced_market_data_service()
        self.recent_queries = {}  # Cache recent market queries

    async def enhance_with_market_intelligence(
        self,
        conversation_context: Dict[str, Any],
        extracted_entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Enhance conversation with market intelligence based on extracted vehicle entities
        """
        # Look for vehicle entities in the conversation
        vehicle_entities = self._extract_vehicle_entities(extracted_entities)

        if not vehicle_entities:
            return None

        # Get market intelligence for the first/most relevant vehicle
        primary_vehicle = vehicle_entities[0]

        try:
            intelligence = await self.market_service.get_comprehensive_market_intelligence(
                vehicle_id=primary_vehicle.get('id', 'conversation_vehicle'),
                make=primary_vehicle['make'],
                model=primary_vehicle['model'],
                year=primary_vehicle.get('year'),
                mileage=primary_vehicle.get('mileage'),
                location=conversation_context.get('user_location')
            )

            # Format for conversation
            return self._format_for_conversation(intelligence, primary_vehicle)

        except Exception as e:
            logger.error(f"Failed to get market intelligence: {e}")
            return None

    async def analyze_price_query(
        self,
        query: str,
        vehicle_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a price-related query with market intelligence
        """
        # Check if query is about pricing
        pricing_keywords = ['price', 'cost', 'worth', 'value', 'deal', 'expensive', 'cheap']
        if not any(keyword in query.lower() for keyword in pricing_keywords):
            return None

        try:
            # Get market intelligence
            intelligence = await self.market_service.get_comprehensive_market_intelligence(
                vehicle_id=vehicle_info.get('id', 'query_vehicle'),
                make=vehicle_info['make'],
                model=vehicle_info['model'],
                year=vehicle_info.get('year'),
                mileage=vehicle_info.get('mileage')
            )

            # If there's an asking price, analyze competitiveness
            if 'asking_price' in vehicle_info:
                competitiveness = await self.market_service.analyze_vehicle_competitiveness(
                    vehicle_id=vehicle_info.get('id', 'query_vehicle'),
                    asking_price=vehicle_info['asking_price'],
                    make=vehicle_info['make'],
                    model=vehicle_info['model'],
                    year=vehicle_info.get('year'),
                    mileage=vehicle_info.get('mileage')
                )
                return self._format_pricing_analysis(intelligence, competitiveness)
            else:
                return self._format_market_overview(intelligence)

        except Exception as e:
            logger.error(f"Failed to analyze price query: {e}")
            return None

    def _extract_vehicle_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract vehicle-related entities from conversation
        """
        vehicle_entities = []

        for entity in entities:
            if entity.get('type') in ['vehicle', 'car', 'truck', 'suv']:
                vehicle_entities.append(entity)
            elif entity.get('category') == 'vehicle':
                vehicle_entities.append(entity)

        return vehicle_entities

    def _format_for_conversation(
        self,
        intelligence: Dict[str, Any],
        vehicle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format market intelligence for conversation response
        """
        scraped = intelligence.scraped_data

        response = {
            'type': 'market_intelligence',
            'vehicle': {
                'make': vehicle['make'],
                'model': vehicle['model'],
                'year': vehicle.get('year')
            },
            'market_data': {
                'average_price': float(scraped.avg_price),
                'price_range': [float(scraped.price_range[0]), float(scraped.price_range[1])],
                'median_price': float(scraped.median_price),
                'total_listings': scraped.total_listings,
                'price_trend': scraped.price_trend,
                'market_health': scraped.market_health,
                'confidence': intelligence.confidence_score,
                'sources': scraped.sources_analyzed
            },
            'insights': [
                f"Based on {scraped.total_listings} similar vehicles",
                f"Market is {scraped.market_trend.lower()}",
                f"Current market health: {scraped.market_health}"
            ]
        }

        if scraped.days_on_market_avg:
            response['market_data']['days_on_market'] = scraped.days_on_market_avg
            response['insights'].append(f"Average time on market: {scraped.days_on_market_avg} days")

        return response

    def _format_pricing_analysis(
        self,
        intelligence: Dict[str, Any],
        competitiveness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format pricing analysis for conversation
        """
        return {
            'type': 'pricing_analysis',
            'analysis': {
                'asking_price': float(competitiveness['asking_price']),
                'market_average': float(competitiveness['market_avg']),
                'price_percentile': competitiveness['price_percentile'],
                'competitiveness': competitiveness['competitiveness'],
                'score': competitiveness['competitiveness_score'],
                'recommendation': competitiveness['recommendation']
            },
            'market_context': {
                'trend': competitiveness['market_trend'],
                'confidence': competitiveness['analysis_confidence']
            },
            'summary': f"This vehicle is priced at the {competitiveness['price_percentile']:.0f}th percentile. {competitiveness['competitiveness']}"
        }

    def _format_market_overview(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format general market overview for conversation
        """
        scraped = intelligence.scraped_data

        return {
            'type': 'market_overview',
            'overview': {
                'average_price': float(scraped.avg_price),
                'price_range': [float(scraped.price_range[0]), float(scraped.price_range[1])],
                'listings_analyzed': scraped.total_listings,
                'price_trend': scraped.price_trend,
                'market_health': scraped.market_health
            },
            'sources': scraped.sources_analyzed,
            'confidence': intelligence.confidence_score
        }


# Singleton instance
_enhancer = None

def get_market_data_enhancer() -> ConversationMarketDataEnhancer:
    """Get singleton instance of the market data enhancer"""
    global _enhancer
    if _enhancer is None:
        _enhancer = ConversationMarketDataEnhancer()
    return _enhancer