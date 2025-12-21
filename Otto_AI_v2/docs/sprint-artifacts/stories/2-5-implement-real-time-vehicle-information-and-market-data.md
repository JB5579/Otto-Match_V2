# Story 2-5: Implement Real-Time Vehicle Intelligence Using Groq Compound AI

**Epic:** Epic 2 - Conversational Discovery Interface (simplified to AI data integration)
**Status:** ready-for-dev → in-progress
**Date:** 2025-12-14

## Story

As a **vehicle buyer**, I want to see **real-time market intelligence and vehicle insights** powered by AI, so that I can make informed purchasing decisions based on current web-sourced information and AI analysis.

## Learning Objectives

**Primary Learning**: Modern AI Compound Systems
- Understand Groq Compound AI architecture (web search + LLM reasoning)
- Learn tool-use AI patterns and autonomous data gathering
- Master real-time AI-driven information retrieval
- Practice prompt engineering for structured data extraction

**Secondary Learning**: System Integration
- AI service integration patterns
- Data validation and sanitization
- Performance optimization for AI services
- Error handling and fallback strategies

## Acceptance Criteria

### AC1: AI-Powered Market Intelligence
- **GIVEN** the vehicle ingestion pipeline is operational (Story 5-4)
- **WHEN** a vehicle is processed and stored
- **THEN** Groq Compound AI should automatically search and analyze:
  - Current market prices from web sources
  - Similar vehicle listings across platforms
  - Regional market trends and pricing
  - Vehicle-specific insights and reviews

### AC2: Real-Time AI Analysis
- **GIVEN** Groq Compound AI system is integrated
- **WHEN** market intelligence is requested
- **THEN** the system should use AI tool-use to:
  - Search real-time web for current market data
  - Analyze multiple sources for price validation
  - Extract structured insights from unstructured web content
  - Provide confidence scores for data accuracy

### AC3: Enhanced Search Results with AI Insights
- **GIVEN** a user searches for vehicles
- **WHEN** search results are displayed
- **THEN** each vehicle should show AI-generated insights:
  - Market price analysis with web sources cited
  - AI confidence indicators for market data
  - Competitive positioning analysis
  - Real-time market sentiment

### AC4: AI Data Validation and Sanitization
- **GIVEN** AI-generated market intelligence
- **WHEN** data is processed and stored
- **THEN** the system should validate:
  - Reasonableness of AI price estimates
  - Consistency across multiple AI sources
  - Proper data sanitization and formatting
  - Fallback mechanisms for AI failures

### AC5: AI-Enhanced API Responses
- **GIVEN** the vehicle search API endpoint with AI integration
- **WHEN** called with market intelligence parameters
- **THEN** it should return AI-enriched vehicle data including:
  - Structured market analysis
  - Source attribution for AI findings
  - Confidence metrics
  - Real-time update timestamps

## Tasks/Subtasks

### Primary Tasks

- [x] **2-5.1**: Research Groq Compound AI capabilities
  - Study Groq Compound AI architecture and tool-use patterns
  - Understand web search + LLM reasoning integration
  - Review pricing, rate limits, and best practices
  - Design prompts for structured vehicle market data extraction

- [x] **2-5.2**: Design AI-enhanced database schema
  - Extend vehicle_listings table with AI market intelligence fields
  - Create ai_intelligence_cache table for storing AI responses
  - Design AI data validation and confidence tracking
  - Plan AI source attribution and audit trail

- [ ] **2-5.3**: Implement Groq Compound AI service
  - Create `src/services/vehicle_intelligence_service.py`
  - Implement Groq Compound AI client with structured prompts
  - Add AI response parsing and validation logic
  - Handle AI tool-use failures and fallback strategies

- [ ] **2-5.4**: Integrate AI intelligence with vehicle processing pipeline
  - Modify `src/services/pdf_ingestion_service.py` to call AI intelligence service
  - Add AI market intelligence fetching after vehicle data extraction
  - Implement AI retry logic and confidence validation
  - Log AI intelligence quality and source attribution

- [ ] **2-5.5**: Enhance search API with AI insights
  - Update `src/api/semantic_search_api.py` to include AI intelligence in responses
  - Add AI-powered filtering and ranking options
  - Implement AI intelligence caching strategies
  - Add performance monitoring for AI intelligence queries

- [ ] **2-5.6**: Add AI intelligence to vehicle models
  - Extend `src/models/vehicle_models.py` with AI intelligence fields
  - Add AI response validation Pydantic models
  - Implement AI source attribution and confidence tracking
  - Add AI intelligence indexing for enhanced search

### Testing Tasks

- [ ] **2-5.7**: Create AI intelligence test suite
  - Unit tests for AI intelligence service
  - Integration tests with Groq Compound AI
  - Performance tests for AI response times
  - AI confidence validation and error handling tests

- [ ] **2-5.8**: AI performance validation
  - Test AI intelligence response times with real vehicles
  - Validate AI confidence scoring accuracy
  - Check concurrent AI request handling
  - Monitor AI token usage and costs

## Dev Notes

### Technical Considerations

1. **Groq Compound AI Strategy**:
   - Use `groq/compound-mini` for single searches (3x faster)
   - Use `groq/compound` for multi-source analysis
   - Implement structured prompts for JSON output
   - Design fallback prompts for AI failures

2. **AI Data Storage Approach**:
   - Store AI intelligence in vehicle_listings with JSONB fields
   - Track AI confidence scores and source attribution
   - Cache AI responses for performance optimization
   - Implement AI response audit trails

3. **AI Performance Requirements**:
   - AI intelligence should not slow down existing search functionality
   - Target <500ms additional latency for AI enrichment
   - Cache AI intelligence for 6 hours minimum
   - Monitor AI token usage and costs

4. **AI Error Handling**:
   - Graceful degradation when Groq AI is unavailable
   - Fall back to cached AI intelligence during outages
   - Log AI confidence scores for monitoring
   - Implement AI response validation and sanitization

### Integration Points

- **Story 5-4**: PDF ingestion pipeline (vehicle data source)
- **Epic 1**: Semantic search (enhanced with AI intelligence)
- **Future Story 6-2**: Seller analytics (AI market insights)

### Dependencies

- **Required**: Story 5-4 completion (vehicle data available)
- **Required**: Supabase database access
- **External**: Groq API key for Compound AI access
- **Optional**: Redis for caching AI intelligence

## Dev Agent Record

### Debug Log

*Initial planning:*
- Research phase will identify best market data APIs for our use case
- Database schema needs to support flexible market data structures
- Integration should be incremental to avoid disrupting existing functionality

*Implementation Progress - 2025-12-14:*
- Created comprehensive market_data_service.py with multiple API integration strategies
- Implemented NHTSA API client with fallback to synthetic data generation
- Added intelligent caching system with 24-hour TTL
- Database schema successfully applied to Supabase:
  - Extended vehicle_listings with market data fields
  - Created market_data_updates table for tracking changes
  - Created market_data_cache table for API call optimization
  - Added automatic triggers for metric calculations
- Regional price multipliers implemented for market adjustments
- Price competitiveness calculation logic implemented

### Completion Notes

*Tasks 2-5.1 and 2-5.2 completed successfully*
- Market data service ready for integration with PDF ingestion pipeline
- Database schema supports real-time updates and historical tracking
- Performance optimizations in place with caching and indexes

## File List

*New files to be created:*
- src/services/market_data_service.py
- tests/test_market_data_service.py
- src/api/market_data_api.py (if needed)

*Files to be modified:*
- src/services/pdf_ingestion_service.py
- src/api/semantic_search_api.py
- src/models/vehicle_models.py (add market data fields)

## Change Log

- **2025-12-14**: Story created for Step 1 of learning roadmap
- Focus on real data integration rather than conversational AI
- Aligned with actual architecture and existing capabilities

## Status

**Current Status:** ready-for-dev → in-progress

**Ready for development:** This story is designed to build incrementally on our working vehicle ingestion pipeline while providing immediate value through market intelligence.