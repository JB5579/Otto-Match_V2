# Otto.AI AI Intelligence Quick Start Guide

## Overview

Story 2-5 implements **Real-Time Vehicle Intelligence Using Groq Compound AI**, adding AI-powered market insights, pricing analysis, and vehicle intelligence to the Otto.AI platform.

## Architecture

The AI intelligence system consists of:

1. **Vehicle Intelligence Service** - Groq Compound AI client with web search + LLM reasoning
2. **Database Integration** - Extended schema with AI intelligence fields and caching
3. **PDF Pipeline Integration** - Automatic AI intelligence fetching after vehicle extraction
4. **Enhanced Search API** - AI-powered filtering and ranking options
5. **Enhanced Vehicle Models** - Comprehensive AI intelligence data structures

## Key Features

### 🤖 Groq Compound AI Integration
- **Models**: `groq/compound` (full) and `groq/compound-mini` (fast)
- **Web Search**: Real-time market data and pricing information
- **Tool-Use AI**: Structured data extraction with confidence scoring
- **Source Attribution**: Full source tracking and reliability scoring

### 📊 Market Intelligence
- **Pricing Analysis**: Market price ranges, averages, and confidence scores
- **Demand Insights**: Market demand levels and availability scoring
- **Feature Intelligence**: Feature popularity and competitive advantages
- **Market Insights**: AI-generated trends and analysis

### 🚀 Performance Features
- **Intelligent Caching**: 24-hour cache with automatic expiration
- **Batch Processing**: Efficient handling of multiple vehicles
- **Rate Limiting**: Built-in rate limiting for API cost management
- **Fallback Strategies**: Graceful degradation when AI is unavailable

## Quick Start

### 1. Environment Setup

Ensure your `.env` file contains:

```bash
# Required for AI Intelligence
GROQ_API_KEY=your_groq_api_key_here

# Existing requirements
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 2. Database Migration

Run the AI intelligence database migration:

```python
from src.services.ai_intelligence_db_migration import run_migration
import asyncio

asyncio.run(run_migration())
```

This creates:
- Extended `vehicle_listings` table with AI fields
- New `ai_intelligence_cache` table for performance
- Indexes and RLS policies for security

### 3. Basic AI Intelligence Usage

```python
from src.services.vehicle_intelligence_service import vehicle_intelligence_service
import asyncio
from decimal import Decimal

async def get_vehicle_intelligence():
    # Get intelligence for a single vehicle
    intelligence = await vehicle_intelligence_service.get_vehicle_intelligence(
        make="Toyota",
        model="Camry",
        year=2022,
        features=["Sedan", "Fuel efficient"],
        current_price=Decimal("25000")
    )

    print(f"Market Average: ${intelligence.market_average_price}")
    print(f"Market Demand: {intelligence.market_demand}")
    print(f"Confidence: {intelligence.confidence_overall:.2f}")
    print(f"Insights: {len(intelligence.insights)}")

# Run the example
asyncio.run(get_vehicle_intelligence())
```

### 4. Enhanced PDF Processing

```python
from src.services.enhanced_pdf_ingestion_with_ai import enhanced_pdf_ingestion_with_ai
import asyncio

async def process_pdf_with_ai():
    # Read PDF file
    with open("vehicle_report.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Process with AI intelligence
    result = await enhanced_pdf_ingestion_with_ai.process_condition_report_with_ai(
        pdf_bytes=pdf_bytes,
        filename="vehicle_report.pdf"
    )

    # Access both standard data and AI intelligence
    vehicle_data = result["vehicle"]
    ai_intelligence = result["ai_intelligence"]

    print(f"Vehicle: {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}")
    if ai_intelligence:
        print(f"AI Confidence: {ai_intelligence['confidence_overall']:.2f}")

# Run the example
asyncio.run(process_pdf_with_ai())
```

### 5. AI-Enhanced Search

```python
from src.services.vehicle_intelligence_service import vehicle_intelligence_service
import asyncio

async def ai_enhanced_search():
    # Get vehicles with high AI confidence
    intelligent_vehicles = await vehicle_intelligence_service.batch_get_intelligence([
        {"make": "Honda", "model": "CR-V", "year": 2023},
        {"make": "Toyota", "model": "RAV4", "year": 2023},
        {"make": "Ford", "model": "Escape", "year": 2023}
    ])

    # Filter by AI confidence
    high_confidence = [
        v for v in intelligent_vehicles
        if v.confidence_overall > 0.7
    ]

    print(f"Found {len(high_confidence)} vehicles with high AI confidence")

# Run the example
asyncio.run(ai_enhanced_search())
```

## API Integration

### Enhanced Search Endpoint

```http
POST /api/search/ai-enhanced
Content-Type: application/json

{
    "query": "reliable SUV under $30000",
    "filters": {
        "min_ai_confidence": 0.7,
        "market_demand": "high",
        "exclude_common_complaints": true
    },
    "include_ai_intelligence": true,
    "ai_priority_sorting": true,
    "limit": 20
}
```

### Response with AI Intelligence

```json
{
    "results": [
        {
            "id": "vehicle_123",
            "make": "Toyota",
            "model": "RAV4",
            "year": 2023,
            "price": 28500,
            "similarity_score": 0.92,
            "ai_intelligence": {
                "market_average_price": 29500,
                "price_confidence": 0.85,
                "market_demand": "high",
                "competitive_advantages": [
                    "Excellent reliability rating",
                    "Strong resale value"
                ],
                "ai_confidence_overall": 0.78
            },
            "price_vs_market_average": 0.97,
            "ai_confidence": 0.78
        }
    ],
    "ai_processing_metadata": {
        "ai_results_count": 15,
        "ai_avg_confidence": 0.72
    }
}
```

## Testing and Validation

Run the comprehensive validation test:

```bash
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" test_story_2_5_complete_validation.py
```

This validates:
- ✅ Vehicle Intelligence Service functionality
- ✅ Database integration and caching
- ✅ PDF pipeline integration
- ✅ AI models and data structures
- ✅ End-to-end flow and performance

## Performance Optimization

### Caching Strategy
- **Cache Duration**: 24 hours for market intelligence
- **Cache Hit Rate**: Monitor via `/ai-stats` endpoint
- **Cache Cleanup**: Automatic expired entry removal

### Rate Limiting
- **Groq API**: 30 requests/minute for compound models
- **Batch Processing**: 3 concurrent requests to avoid limits
- **Exponential Backoff**: Built-in retry logic with jitter

### Cost Management
- **Model Selection**: Use `compound-mini` for faster, cheaper processing
- **Batch Operations**: Process multiple vehicles efficiently
- **Cache Utilization**: Maximize cache hits to reduce API calls

## Monitoring

### Key Metrics
- AI confidence scores distribution
- Cache hit rates
- Processing time averages
- Error rates and fallback usage

### Health Check
```http
GET /health
```

Returns AI intelligence status and statistics.

### Statistics
```http
GET /ai-stats
```

Returns detailed AI processing statistics.

## Troubleshooting

### Common Issues

1. **Groq API Rate Limits**
   - Reduce concurrent requests
   - Implement longer delays between batches
   - Use `compound-mini` model

2. **Low AI Confidence**
   - Verify vehicle data accuracy
   - Check for typos in make/model
   - Try more recent vehicle years

3. **Cache Issues**
   - Check database connectivity
   - Verify cache table creation
   - Run cache cleanup

4. **PDF Processing Errors**
   - Verify PDF file integrity
   - Check OpenRouter API key
   - Review PDF parsing logs

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This provides detailed logging for:
- AI API requests/responses
- Cache operations
- Database queries
- Error details

## Next Steps

1. **Production Deployment**
   - Configure production API keys
   - Set up monitoring and alerts
   - Implement cost tracking

2. **Performance Tuning**
   - Optimize cache strategies
   - Fine-tune batch sizes
   - Monitor and adjust rate limits

3. **Feature Expansion**
   - Add more AI insight types
   - Implement custom AI prompts
   - Add competitor analysis

4. **Integration**
   - Connect to frontend UI
   - Implement real-time updates
   - Add user preferences

## Support

For issues or questions:
1. Check the validation test output
2. Review the debug logs
3. Consult the API documentation at `/docs`
4. Check the health endpoint at `/health`

---

**Story 2-5 Status**: ✅ **COMPLETE** - Real-Time Vehicle Intelligence Using Groq Compound AI successfully implemented and validated.