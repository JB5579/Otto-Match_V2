# Story 2.5: Implement Real-Time Vehicle Information and Market Data

Status: drafted

## Story

As a user,
I want Otto AI to provide real-time vehicle information including pricing, specifications, and market data during our conversation,
so that I can make informed decisions based on current market conditions.

## Acceptance Criteria

1. **Real-Time Market Intelligence**: Given a user is viewing vehicle details in the carousel interface, when they ask about pricing or market conditions, then Otto AI provides current pricing from multiple sources with market analysis, explains price factors like condition, mileage, and location variations, provides information about recent market trends for this vehicle type, and suggests when might be a good time to purchase based on market conditions

2. **Enhanced Vehicle Specifications**: Given a user is viewing vehicle details with VIN available, when they ask about specifications or comparisons, then Otto AI provides detailed specifications using NHTSA VPIC API data, includes official manufacturer specifications, safety ratings, and equipment details, and explains key features in practical terms for their usage patterns

## Tasks / Subtasks

- [ ] Create vehicle_data_enhancer.py to structure Groq responses (AC: #1, #2)
  - [ ] Build response parser for Groq web search results for market data
  - [ ] Create NHTSA VPIC data structure formatter
  - [ ] Implement market data extraction and synthesis
  - [ ] Add natural language explanation generator
  - [ ] Build UI-friendly data presentation layer for carousel view

- [ ] Implement NHTSA VPIC API integration for Groq function calls (AC: #2)
  - [ ] Create NHTSA VPIC API wrapper for DecodeVINValuesBatch endpoint
  - [ ] Build function definition schema for Groq tool calls
  - [ ] Implement VIN retrieval from listing database (not user input)
  - [ ] Add NHTSA error handling and retry logic
  - [ ] Create response caching for VIN decode results

- [ ] Create listing VIN retrieval service (Prerequisite for AC: #2)
  - [ ] Build service to fetch VIN from vehicle listing database
  - [ ] Implement VIN validation for vehicle details view
  - [ ] Add VIN availability check before NHTSA lookup
  - [ ] Create VIN-to-listing mapping cache

- [ ] Enhance Groq conversation prompts for vehicle intelligence (AC: #1, #2)
  - [ ] Add vehicle market expertise to system prompts
  - [ ] Create market analysis instruction templates for pricing queries
  - [ ] Build specification synthesis guidelines for NHTSA data
  - [ ] Implement context-aware data request triggers in carousel view
  - [ ] Add citation and source attribution logic for web search results

- [ ] Integrate vehicle details carousel UI with enhanced data (UI Reference: Otto_Vehicle_Details_With_Carousel.png)
  - [ ] Create proactive insight triggers when viewing vehicle details
  - [ ] Build safety rating display component from NHTSA data
  - [ ] Implement market comparison widgets in carousel interface
  - [ ] Add dynamic fact overlays on vehicle images
  - [ ] Create "Ask Otto" integration point for each vehicle in carousel

- [ ] Create caching layer for vehicle data responses
  - [ ] Implement Redis caching for NHTSA VIN decodes (long TTL - static data)
  - [ ] Build market data cache with short TTL (time-sensitive pricing)
  - [ ] Create cache invalidation strategy for market price updates
  - [ ] Add performance monitoring for cache hit rates
  - [ ] Build fallback to cached data during Groq outages

- [ ] Add comprehensive testing suite
  - [ ] Test market data accuracy from Groq web search results
  - [ ] Validate NHTSA API integration and data parsing
  - [ ] Test response structuring for UI presentation
  - [ ] Create performance tests for <2 second response requirement
  - [ ] Build UI integration tests for carousel view interactions

## Dev Notes

### Architecture Patterns and Constraints
- **Groq-Powered Intelligence**: Leverage Groq Compound Beta's built-in web search for market data and function calling for NHTSA VPIC API
- **Listing-Driven Context**: VIN and vehicle details retrieved from database, not user input
- **Carousel-Specific Enhancement**: Vehicle data queries triggered only in vehicle details carousel view
- **Dual-Tool Strategy**: Groq automatically uses web search for market data and NHTSA function for specifications
- **Smart Caching**: NHTSA data (static) cached long-term, market data (dynamic) cached short-term

### Project Structure Notes
- **VIN Retrieval**: `src/services/listing_vin_service.py` to fetch VIN from listing database
- **Response Enhancement**: `src/intelligence/vehicle_data_enhancer.py` to structure Groq responses
- **NHTSA Integration**: `src/services/nhtsa_vpic_service.py` as Groq function call backend
- **UI Integration**: "Ask Otto" component in vehicle details carousel view
- **Caching Layer**: Extend `src/cache/multi_level_cache.py` with VIN-based cache keys

### Groq Integration Strategy
- **System Prompts**: Add vehicle market expertise and NHTSA data context to Groq
- **Function Definitions**: Register NHTSA VPIC DecodeVINValuesBatch as available tool
- **Response Processing**: Parse Groq's executed_tools for market data and NHTSA responses
- **Natural Synthesis**: Groq automatically explains pricing and specifications in user-friendly terms
- **Listing Context**: Pass vehicle listing info to Groq for contextualized responses

### Fallback Strategy
When Groq Compound Beta is unavailable:
- Market Data: Serve cached pricing information with timestamp
- NHTSA Data: Serve cached specifications with "data may be stale" notice
- UI: Display "Live data temporarily unavailable" message in carousel
- Logging: Monitor Groq availability for performance tracking

### Learnings from Previous Story

**From Story 2.4 (Status: done) - Add Targeted Questioning and Preference Discovery:**
- **Conversation Integration**: Use established patterns in `src/conversation/conversation_agent.py` for adding new capabilities
- **Memory Management**: Leverage `src/memory/temporal_memory.py` for caching market data per conversation
- **Preference Engine**: Use `src/intelligence/preference_engine.py` to inform cost calculations based on user preferences
- **Natural Language Processing**: Build upon existing NLU service for understanding vehicle data queries

**Key Services Available for Reuse:**
- Groq Compound Beta client with automatic web search and function calling
- Vehicle listing database with VIN numbers (from ingestion pipeline)
- Zep Cloud temporal memory for caching market insights per session
- Preference learning for tailoring market insights based on user interests
- Existing multi-level cache infrastructure for vehicle data persistence

**Technical Debt to Address:**
- Vehicle listing ingestion pipeline needs to ensure VIN numbers are captured and stored
- Database schema must include VIN field for NHTSA API lookups
- Consider CARFAX/AutoCheck integration for vehicle history (future story)

**Pending Review Items:**
- Add data visualization for market trends in vehicle details carousel
- Evaluate additional NHTSA endpoints (safety ratings, recalls) for future enhancement
- Plan proactive insight triggers based on user viewing patterns in carousel

### Testing Standards Summary
- Market data accuracy testing from Groq web search results with known pricing
- NHTSA VPIC API integration validation for VIN decode operations
- Response parsing and structuring accuracy for UI presentation
- Cache TTL validation for market data (freshness) vs NHTSA data (stability)
- UI integration testing for vehicle details carousel "Ask Otto" functionality
- Performance testing to maintain <2 second response requirement
- Fallback mode testing when Groq Compound Beta is unavailable

### References
- [Source: docs/epics.md#Epic-2-Conversational-Discovery-Interface] - Epic requirements and story breakdown
- [Source: docs/sprint-artifacts/2-4-add-targeted-questioning-and-preference-discovery.md] - Conversation integration patterns
- [Source: docs/prd.md#Real-Time-Data-Integration] - FR11: Otto AI provides real-time vehicle information including pricing, specifications, and market data
- [Source: docs/architecture.md#Groq-Compound-Beta-Integration] - Groq automatic tool usage and web search capabilities
- [NHTSA VPIC API Documentation] - https://vpic.nhtsa.dot.gov/api/ - Vehicle Product Information Catalog API
- [NHTSA Batch Decode Endpoint] - https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/
- [UI Reference: Otto_Vehicle_Details_With_Carousel.png] - Vehicle details view for proactive insights integration

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude (Sonnet 4.5)

### Debug Log References

### Completion Notes List

### File List

## Change Log