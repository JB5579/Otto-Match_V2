# Otto.AI Architecture

## Executive Summary

Otto.AI is an AI-powered vehicle discovery platform with a functional semantic search and vehicle ingestion system. The current implementation focuses on PDF-based vehicle ingestion, semantic search using RAG-Anything with pgvector, and basic REST APIs for vehicle management.

The system successfully implements a hybrid PDF processing pipeline using OpenRouter AI and PyMuPDF for vehicle data extraction, combined with semantic search capabilities powered by RAG-Anything and Supabase pgvector. The platform includes WebSocket support for Otto AI chat and Server-Sent Events (SSE) for vehicle updates (Story 3-3b migration), plus a comprehensive API layer for vehicle operations.

**Current Implementation**: Vehicle ingestion pipeline with 99.5% PDF processing success rate, semantic search with multimodal understanding, and REST APIs for vehicle management. The architecture supports collections, favorites, and real-time notifications through WebSocket (chat) and SSE (vehicle updates) connections.

**Vehicle Ingestion Achievement**: Hybrid AI-powered PDF processing system combining OpenRouter's advanced extraction with PyMuPDF's robust parsing, successfully converting dealer PDFs to structured vehicle listings with embedded images and metadata.

**Architecture Philosophy**: Modular structure implemented in Python with FastAPI, prioritizing functional semantic search and reliable vehicle data ingestion. The codebase follows clean separation of concerns with dedicated services for different functionalities.

## Recent Architectural Enhancements (2025-12-31)

**Phase 1: Enhanced Entity Extraction** ✅ Complete
- Extended NLU with 10 advisory intent types and 11 lifestyle entity types
- Implemented lifestyle context extraction (commute, work pattern, current vehicle)
- Added priority ranking detection and decision signal analysis
- Full integration with `conversation_agent.py` and `nlu_service.py`
- See: `docs/conversation-architecture-analysis.md` and `docs/phase1-phase2-implementation-summary.md`

**Phase 2: External Research Service** ✅ Complete
- Created `ExternalResearchService` using Groq Compound for ownership research
- Implemented 4 research types: ownership costs, owner experiences, lease vs buy, insurance delta
- Integrated with conversation flow for automatic research query detection
- Personalized using Phase 1 lifestyle profile data
- See: `docs/conversation-architecture-analysis.md` and `docs/phase1-phase2-implementation-summary.md`

These enhancements were implemented as architectural improvements to stories 2-2 (NLU) and 2-5 (Market Data) based on conversation simulation analysis.

## Decision Summary

| Category | Decision | Version | Affects Components | Rationale |
| -------- | -------- | ------- | ----------------- | --------- |
| **AI Framework** | Pydantic + Custom Code | v1.0 | All Services | Type safety, performance, full control over implementation |
| **Semantic Search** | RAG-Anything + Supabase pgvector | v1.0 | Semantic Search | Multimodal search (text, images) with vector similarity |
| **PDF Processing** | OpenRouter + PyMuPDF hybrid | v1.0 | Vehicle Ingestion | AI extraction + traditional parsing for 99.5% success rate |
| **API Framework** | FastAPI | v1.0 | All APIs | High performance, automatic docs, type hints |
| **Frontend Framework** | React + TypeScript | 19.2.0 + 5.9.3 | Epic 3 (91 files) | Component-based UI with type safety, Vite 7.2.4 build system |
| **Real-time Communication** | WebSocket + SSE | v2.0 | Notifications, Chat, Updates | WebSocket for Otto chat, SSE for vehicle updates (Story 3-3b) |
| **Database Strategy** | Supabase PostgreSQL + pgvector | v1.0 | Data Persistence | Vector similarity + relational data in single system |
| **Project Structure** | Modular Python + React packages | v1.0 | All Components | Clean separation of concerns with service modules |
| **Repository Pattern** | Repository layer | v1.0 | Data access | Separates data access from business logic (repositories/) |
| **Progressive Auth** | Session-based → JWT | v1.0 | Authentication | Low-friction conversion with guest sessions (auth_api.py) |

## Project Structure

```
otto-ai/
├── src/                           # Main source code
│   ├── api/                       # FastAPI endpoints
│   │   ├── main_app.py           # Main FastAPI application
│   │   ├── auth_api.py           # Authentication: session merge, guest management (8.7KB)
│   │   ├── listings_api.py       # Vehicle listing management
│   │   ├── semantic_search_api.py # Semantic search endpoints (with multi-select)
│   │   ├── vehicle_comparison_api.py # Vehicle comparison
│   │   ├── vehicles_api.py       # Vehicle search API with multi-select (11.1KB)
│   │   ├── vehicle_updates_sse.py # SSE endpoint for vehicle updates (10KB)
│   │   ├── filter_management_api.py # Search filtering
│   │   ├── collections_api.py    # Vehicle collections
│   │   ├── analytics_api.py      # Analytics endpoints
│   │   ├── websocket_endpoints.py # WebSocket endpoints
│   │   └── admin/                # Admin-specific APIs
│   ├── repositories/              # Repository pattern layer (NEW)
│   │   ├── __init__.py
│   │   ├── image_repository.py   # Image data access (12.9KB)
│   │   └── listing_repository.py # Listing data access (11.2KB)
│   ├── semantic/                  # Semantic search and processing
│   │   ├── vehicle_processing_service.py # RAG-Anything integration
│   │   ├── embedding_service.py  # Vector embeddings
│   │   ├── vehicle_database_service.py # Database operations
│   │   ├── batch_processing_engine.py # Bulk processing
│   │   ├── performance_optimizer.py # Performance tuning
│   │   └── setup_database.py     # Database initialization
│   ├── services/                  # Core services
│   │   ├── supabase_client.py   # Centralized Supabase client singleton (60 lines)
│   │   ├── pdf_ingestion_service.py # PDF processing (OpenRouter + PyMuPDF)
│   │   ├── vehicle_image_enhancement_service.py # Image processing
│   │   ├── vehicle_embedding_service.py # Vehicle embeddings
│   │   └── storage_service.py    # File storage
│   ├── search/                    # Search functionality
│   │   ├── filter_service.py     # Intelligent filtering
│   │   └── __init__.py
│   ├── recommendation/            # Recommendation engine
│   │   ├── recommendation_engine.py
│   │   ├── comparison_engine.py
│   │   ├── interaction_tracker.py
│   │   └── favorites_recommendation_engine.py
│   ├── user/                      # User management
│   │   ├── favorites_service.py
│   │   └── __init__.py
│   ├── realtime/                  # Real-time features
│   │   ├── favorites_websocket_service.py
│   │   ├── collections_websocket_service.py
│   │   └── __init__.py
│   ├── notifications/             # Notification system
│   │   ├── notification_service.py
│   │   └── __init__.py
│   ├── collections/               # Collections management
│   │   ├── collection_engine.py
│   │   ├── trending_algorithm.py
│   │   ├── analytics_dashboard.py
│   │   └── ab_testing.py
│   ├── analytics/                 # Analytics services
│   │   ├── favorites_analytics_service.py
│   │   └── __init__.py
│   ├── cache/                     # Multi-level caching
│   │   ├── multi_level_cache.py
│   │   ├── cache_config.py
│   │   └── __init__.py
│   ├── models/                    # Pydantic models
│   │   └── vehicle_models.py
│   ├── config/                    # Configuration
│   │   └── conversation_config.py
│   ├── conversation/              # Conversational AI (basic)
│   │   ├── conversation_agent.py
│   │   ├── groq_client.py
│   │   └── __init__.py
│   ├── memory/                    # Memory management
│   │   ├── zep_client.py
│   │   ├── temporal_memory.py
│   │   └── __init__.py
│   ├── intelligence/              # AI intelligence
│   │   ├── preference_engine.py
│   │   └── __init__.py
│   └── database/                  # Database utilities
│       └── __init__.py
├── frontend/                      # React 19.2.0 + TypeScript 5.9.3 frontend (Epic 3)
│   ├── src/
│   │   ├── app/                   # React Router setup, auth pages
│   │   ├── components/            # UI components (91 files, ~2,283 lines)
│   │   │   ├── availability/       # Real-time availability status
│   │   │   ├── comparison/         # Vehicle comparison tools
│   │   │   ├── filters/            # Multi-select filters, SortDropdown
│   │   │   ├── notifications/     # Notification system
│   │   │   ├── otto-chat/          # Otto AI chat interface
│   │   │   ├── vehicle-detail/    # Vehicle detail modal
│   │   │   └── vehicle-grid/       # Responsive vehicle grid
│   │   ├── context/               # React contexts (5 files, 1,526 lines)
│   │   │   ├── ComparisonContext.tsx
│   │   │   ├── ConversationContext.tsx
│   │   │   ├── FilterContext.tsx
│   │   │   ├── NotificationContext.tsx
│   │   │   └── VehicleContext.tsx
│   │   ├── lib/                   # Supabase client, API utilities
│   │   ├── services/              # API client, session service
│   │   └── types/                 # TypeScript type definitions
│   ├── package.json               # NPM dependencies
│   ├── vite.config.ts             # Vite 7.2.4 configuration
│   └── tsconfig.json              # TypeScript 5.9.3 configuration
├── tests/                         # Test suite
│   ├── unit/
│   ├── integration/
│   ├── notifications/
│   ├── realtime/
│   └── performance/
├── main.py                        # Application entry point
├── docs/                          # Documentation
│   ├── api/
│   ├── architecture/
│   └── deployment/
├── .env.example
├── requirements.txt
└── README.md
```

## Implemented Features Summary

**Last Verified:** 2026-01-19 | **Overall Implementation:** ~50% backend, ~30% frontend (Epic 3)

### Epic 1: Semantic Vehicle Intelligence ✅ COMPLETE

| Feature | Status | Implementation Details |
| ------- | ------ | --------------------- |
| **Vehicle Ingestion** | ✅ IMPLEMENTED | PDF processing with OpenRouter + PyMuPDF (Story 5-4b backend only) |
| **Semantic Search** | ✅ IMPLEMENTED | RAG-Anything with Supabase pgvector for vector similarity |
| **Hybrid FTS Search** | ✅ IMPLEMENTED | Vector + full-text search hybrid (Story 1-9) |
| **Query Expansion** | ✅ IMPLEMENTED | LLM-powered query expansion service (Story 1-10) |
| **Re-ranking Layer** | ✅ IMPLEMENTED | BGE cross-encoder re-ranking (Story 1-11) |
| **Contextual Embeddings** | ✅ IMPLEMENTED | Category-aware embedding service (Story 1-12) |
| **Vehicle Listings API** | ✅ IMPLEMENTED | REST endpoints for CRUD operations |
| **Image Enhancement** | ✅ IMPLEMENTED | Vehicle image processing and optimization |
| **Vehicle Comparison** | ✅ IMPLEMENTED | Multi-vehicle comparison API |
| **Search Filtering** | ✅ IMPLEMENTED | Intelligent filtering service |
| **Collections System** | ✅ IMPLEMENTED | Vehicle collections with analytics |
| **Favorites System** | ✅ IMPLEMENTED | User favorites with WebSocket notifications |
| **Recommendation Engine** | ✅ IMPLEMENTED | Basic vehicle recommendations |
| **Real-time Notifications** | ✅ IMPLEMENTED | WebSocket-based notifications |
| **Analytics Dashboard** | ✅ IMPLEMENTED | Basic analytics for collections |

### Epic 2: Conversational Discovery ⚠️ PARTIAL (6/10 stories)

| Feature | Status | Implementation Details |
| ------- | ------ | --------------------- |
| **Conversation Agent** | ✅ IMPLEMENTED | Main Otto orchestrator (84KB, Story 2-1) |
| **NLU Service** | ✅ IMPLEMENTED | Natural language understanding (40KB, Story 2-2) |
| **Zep Memory** | ✅ IMPLEMENTED | Temporal memory & preference learning (Story 2-3) |
| **Questioning Strategy** | ✅ IMPLEMENTED | Smart question generation (Story 2-4) |
| **Market Data Integration** | ✅ IMPLEMENTED | Real-time vehicle information (Story 2-5) |
| **Advisory Extractors** | ✅ IMPLEMENTED | **Phase 1:** Lifestyle entities, 1,073 lines (Story 2-2 enhancement) |
| **External Research** | ✅ IMPLEMENTED | **Phase 2:** Ownership costs, 871 lines (Story 2-5 enhancement) |
| **Voice Input** | 📋 PLANNED | Story 2-6 not started |
| **Conversation History** | 📋 PLANNED | Story 2-7 not started |
| **Multi-threading** | 📋 PLANNED | Stories 2-8 to 2-10 not started |

### Epic 3: Dynamic Vehicle Grid Interface ⚠️ PARTIAL (5/13 stories)

| Feature | Status | Implementation Details |
| ------- | ------ | --------------------- |
| **Real-time Grid Infrastructure** | ✅ IMPLEMENTED | React 19.2.0 + TypeScript 5.9.3 (Story 3-1) |
| **Responsive Vehicle Grid** | ✅ IMPLEMENTED | 3/2/1 column layout, glass-morphism, 46 tests (Story 3-2) |
| **Dynamic Cascade Updates** | ⚠️ PARTIAL | AC1, AC4 complete; AC2/AC3 via SSE migration (Story 3-3/3-3b) |
| **Vehicle Details Modal** | ✅ IMPLEMENTED | Image carousel, comprehensive tests (Story 3-4) |
| **Real-time Availability** | ✅ IMPLEMENTED | Status badges, notifications (Story 3-5) |
| **Vehicle Comparison** | ✅ IMPLEMENTED | Table view, sessionStorage (Story 3-6) |
| **Grid Filtering & Sorting** | ✅ IMPLEMENTED | Multi-select, effective_price, SortDropdown (Story 3-7) |
| **Performance Optimization** | 📋 PLANNED | Story 3-8 not started |
| **Analytics & Tracking** | 📋 PLANNED | Story 3-9 not started |
| **Design System Components** | 📋 PLANNED | Story 3-10 not started |
| **Match Score Badge** | 📋 PLANNED | Story 3-11 not started |
| **Detail Modal Carousel** | 📋 PLANNED | Story 3-12 not started |
| **Otto Chat Widget** | 📋 PLANNED | Story 3-13 not started |

**Frontend Implementation:** 91 TypeScript/React files (~2,283 lines)
- Components: availability, comparison, filters, notifications, otto-chat, vehicle-detail, vehicle-grid
- Contexts: Comparison (290 lines), Conversation (273 lines), Filter (436 lines), Notification (167 lines), Vehicle (360 lines)
- Build: Vite 7.2.4, Vitest 4.0.16 testing

### Epic 4-8: Remaining Epics 📋 PLANNED

| Feature | Status | Notes |
| ------- | ------ | ----- |
| **User Authentication** | 📋 PLANNED | Epic 4: 0/9 stories - progressive auth endpoints exist (auth_api.py) |
| **Lead Intelligence UI** | 📋 PLANNED | Epic 5: 2/8 backend only (PDF pipeline works, no seller UI) |
| **Seller Dashboard** | 📋 PLANNED | Epic 6: 0/8 stories - backend services exist, no UI |
| **Deployment Infrastructure** | 📋 PLANNED | Epic 7: 0/6 stories - no production infrastructure |
| **Performance Optimization** | 📋 PLANNED | Epic 8: 0/7 stories - some code exists but not story-organized |

## Technology Stack Details

### Core Technologies

**Backend Stack:**
- **FastAPI**: High-performance async framework for REST APIs
- **Pydantic**: Data validation and serialization with type safety
- **PostgreSQL + Supabase**: Primary database with pgvector extension
- **RAG-Anything**: Multimodal semantic search for vehicles
- **OpenRouter**: AI model integration for PDF processing
- **PyMuPDF**: PDF parsing and extraction
- **WebSockets**: Basic real-time notifications
- **Python 3.11**: Core programming language

**AI/ML Technologies:**
- **RAG-Anything**: Multimodal embeddings and search
- **OpenRouter (Gemini)**: Vision model for PDF understanding
- **pgvector**: Vector similarity search in PostgreSQL
- **Pillow (PIL)**: Image processing and enhancement

**Frontend Stack:**
- **React 19.2.0**: UI library (VERIFIED 2026-01-19)
- **TypeScript 5.9.3**: Type-safe JavaScript (VERIFIED 2026-01-19)
- **Vite 7.2.4**: Fast build tool and dev server (VERIFIED 2026-01-19)
- **Framer Motion 12.23.26**: Animation library for cascade effects
- **Radix UI 1.1.15**: Accessible modal/dialog components
- **Lucide React 0.562.0**: Icon library
- **React Router DOM 7.11.0**: Client-side routing
- **Supabase JS 2.89.0**: Database client
- **Vitest 4.0.16**: Fast unit testing
- **Testing Library**: React testing utilities
- **MSW 2.7.2**: API mocking

**Infrastructure Stack:**
- **Supabase**: Database hosting and management
- **Render.com**: Deployment platform (planned)
- **Local Development**: Current development environment

### Integration Points

**Semantic Search Integration:**
```python
# RAG-Anything + Supabase pgvector integration (IMPLEMENTED)
async def semantic_vehicle_search(query: str, filters: SearchFilters) -> List[Vehicle]:
    # RAG-Anything generates multimodal embeddings
    embeddings = await rag_service.generate_embeddings(query)

    # Supabase pgvector similarity search
    similar_vehicles = await vector_store.similarity_search(
        embeddings=embeddings,
        filters=filters.to_dict(),
        limit=50
    )

    return similar_vehicles
```

**PDF Processing Integration:**
```python
# OpenRouter + PyMuPDF hybrid processing (IMPLEMENTED)
async def process_vehicle_pdf(pdf_bytes: bytes) -> VehicleListing:
    # Parallel extraction: AI + traditional
    ai_results = await openrouter_client.extract_vehicle_data(pdf_pages)
    structured_data = await pymupdf_processor.extract_structured_data(pdf_bytes)

    # Merge results with AI prioritized
    merged_data = merge_extraction_results(ai_results, structured_data)

    # Process and enhance images
    enhanced_images = await enhance_vehicle_images(merged_data.images)

    return VehicleListing.from_merged_data(merged_data, enhanced_images)
```

**WebSocket Notifications Integration:**
```python
# Real-time favorites notifications (IMPLEMENTED)
async def notify_price_change(user_id: str, vehicle_id: str, new_price: float):
    # Send WebSocket notification to connected clients
    await websocket_manager.send_to_user(user_id, {
        "type": "price_drop",
        "vehicle_id": vehicle_id,
        "new_price": new_price,
        "timestamp": datetime.utcnow().isoformat()
    })
```

## Implementation Patterns

These patterns reflect the actual implemented code:

**1. PDF Ingestion Pattern (IMPLEMENTED):**
```python
class PDFIngestionService:
    """Hybrid PDF processing with AI + traditional methods"""

    async def process_pdf(self, pdf_bytes: bytes) -> VehicleListingArtifact:
        # Parallel extraction: OpenRouter AI + PyMuPDF
        ai_task = self.openrouter_client.extract_vehicle_data(pdf_pages)
        traditional_task = self.pymupdf_processor.extract_structured_data(pdf_bytes)

        ai_results, traditional_results = await asyncio.gather(ai_task, traditional_task)

        # Merge with AI prioritized
        merged_data = self.merge_extraction_results(ai_results, traditional_results)

        # Process images
        enhanced_images = await self.enhance_vehicle_images(merged_data.images)

        return VehicleListingArtifact(
            vehicle_data=merged_data.vehicle,
            images=enhanced_images,
            metadata=merged_data.metadata
        )
```

**2. Semantic Search Pattern (IMPLEMENTED):**
```python
class VehicleProcessingService:
    """RAG-Anything integration for vehicle semantic search"""

    async def process_and_index_vehicle(self, vehicle_data: VehicleData) -> VehicleProcessingResult:
        # Generate embeddings using RAG-Anything
        embeddings = await self.rag_service.generate_embeddings(
            text=vehicle_data.description,
            images=vehicle_data.images
        )

        # Store in database with vector embeddings
        await self.store_vehicle_with_embeddings(
            vehicle_id=vehicle_data.id,
            embeddings=embeddings,
            metadata=vehicle_data.dict()
        )

        return VehicleProcessingResult(
            success=True,
            vehicle_id=vehicle_data.id,
            embedding_count=len(embeddings)
        )
```

**3. API Service Pattern (IMPLEMENTED):**
```python
# FastAPI router pattern for endpoints
@listings_router.post("/upload", response_model=ListingUploadResponse)
async def upload_listing(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process PDF vehicle listing"""

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")

    # Process PDF
    pdf_bytes = await file.read()
    listing_artifact = await pdf_service.process_pdf(pdf_bytes)

    # Store in database (background task)
    background_tasks.add_task(store_listing, listing_artifact)

    return ListingUploadResponse(
        success=True,
        listing_id=listing_artifact.listing_id,
        vin=listing_artifact.vehicle_data.vin,
        vehicle_info=listing_artifact.vehicle_data.dict(),
        image_count=len(listing_artifact.images),
        processing_time=listing_artifact.processing_time,
        message="PDF processed successfully"
    )
```

**4. WebSocket Notification Pattern (IMPLEMENTED):**
```python
class FavoritesWebSocketService:
    """Real-time notifications for vehicle favorites"""

    async def notify_favorited_vehicles_sold(self, vehicle_ids: List[str]):
        """Notify users when favorited vehicles are sold"""

        for vehicle_id in vehicle_ids:
            # Find users who favorited this vehicle
            users = await self.get_users_favoriting_vehicle(vehicle_id)

            # Send WebSocket notification
            for user_id in users:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "vehicle_sold",
                    "vehicle_id": vehicle_id,
                    "message": "A vehicle you favorited has been sold",
                    "timestamp": datetime.utcnow().isoformat()
                })
```

## Consistency Rules

### Naming Conventions

**Python:**
- Classes: PascalCase (e.g., `VehicleSearchAgent`)
- Functions/variables: snake_case (e.g., `semantic_vehicle_search`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_VEHICLE_RESULTS`)
- Files: snake_case (e.g., `conversation_agent.py`)

**TypeScript/React:**
- Components: PascalCase (e.g., `VehicleCard`)
- Hooks: camelCase with `use` prefix (e.g., `useVehicleCascade`)
- Functions/variables: camelCase (e.g., `handleVehicleUpdate`)
- Files: kebab-case (e.g., `vehicle-card.tsx`)

**Database:**
- Tables: snake_case plural (e.g., `vehicle_listings`)
- Columns: snake_case (e.g., `preference_score`)
- Indexes: `idx_` prefix (e.g., `idx_vehicle_preferences`)

### Code Organization

**Module Structure:**
```python
# Each module follows this pattern
class ModuleService:
    """Main service class for the module"""

    def __init__(self, dependencies: ModuleDependencies):
        self.deps = dependencies
        self.logger = get_logger(self.__class__.__name__)

class ModuleRepository:
    """Data access layer for the module"""

    async def find_by_id(self, id: str) -> Optional[ModuleModel]:
        # Database interaction logic
        pass

class ModuleModel(BaseModel):
    """Pydantic model for data validation"""
    pass
```

**Frontend Component Structure:**
```typescript
// Component organization pattern
interface ComponentProps {
  // Props interface
}

export function ComponentName({ prop1, prop2 }: ComponentProps) {
  // Custom hooks
  const hookData = useCustomHook();

  // Event handlers
  const handleAction = useCallback(() => {
    // Handler logic
  }, [dependencies]);

  // Render logic
  return (
    <div className="component-name">
      {/* Component JSX */}
    </div>
  );
}
```

### Frontend Component Architecture

**Glass-Morphism Utility System:**
```typescript
// src/frontend/styles/glass.ts
export const glassVariants = {
  light: {
    background: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.18)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
  },
  dark: {
    background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.90) 0%, rgba(15, 23, 42, 0.95) 100%)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(14, 165, 233, 0.3)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(14, 165, 233, 0.1)',
  },
  modal: {
    background: 'rgba(255, 255, 255, 0.92)',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    borderRadius: '16px',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },
} as const;
```

**Vehicle Card Component Structure:**
```typescript
// src/frontend/components/VehicleCard/VehicleCard.tsx
interface VehicleCardProps {
  vehicle: Vehicle;
  matchScore: number;
  onSelect: (vehicle: Vehicle) => void;
  onFavorite: (vehicleId: string) => void;
  isFavorited: boolean;
  animationDelay?: number;
}

export function VehicleCard({
  vehicle,
  matchScore,
  onSelect,
  onFavorite,
  isFavorited,
  animationDelay = 0,
}: VehicleCardProps) {
  return (
    <motion.article
      className="vehicle-card glass-light rounded-xl overflow-hidden"
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ delay: animationDelay, duration: 0.3 }}
      whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(0,0,0,0.12)' }}
    >
      <div className="relative">
        <img src={vehicle.images[0]} alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`} />
        <MatchScoreBadge score={matchScore} />
        <FavoriteButton isActive={isFavorited} onClick={() => onFavorite(vehicle.id)} />
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-lg">{vehicle.year} {vehicle.make} {vehicle.model}</h3>
        <VehicleSpecs mileage={vehicle.mileage} range={vehicle.range} trim={vehicle.trim} />
        <PriceDisplay current={vehicle.price} savings={vehicle.savings} />
        <FeatureTags features={vehicle.features} />
        <ActionButtons onMoreLike={() => {}} onLessLike={() => {}} />
      </div>
    </motion.article>
  );
}
```

**Match Score Badge Component:**
```typescript
// src/frontend/components/MatchScoreBadge/MatchScoreBadge.tsx
interface MatchScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
}

const scoreColors = {
  excellent: { bg: '#22C55E', text: 'white' },  // 90+
  good: { bg: '#84CC16', text: 'white' },       // 80-89
  fair: { bg: '#EAB308', text: 'slate-900' },   // 70-79
  low: { bg: '#F97316', text: 'white' },        // <70
};

export function MatchScoreBadge({ score, size = 'md', showPulse = false }: MatchScoreBadgeProps) {
  const colorKey = score >= 90 ? 'excellent' : score >= 80 ? 'good' : score >= 70 ? 'fair' : 'low';
  const colors = scoreColors[colorKey];

  return (
    <motion.div
      className={`match-score-badge absolute top-3 left-3 ${size === 'lg' ? 'w-14 h-14' : 'w-12 h-12'}`}
      style={{ backgroundColor: colors.bg }}
      animate={showPulse && score >= 95 ? { scale: [1, 1.05, 1] } : {}}
      transition={{ repeat: Infinity, duration: 2 }}
    >
      <motion.span
        className={`font-bold ${size === 'lg' ? 'text-lg' : 'text-base'}`}
        style={{ color: colors.text }}
        key={score}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {score}%
      </motion.span>
    </motion.div>
  );
}
```

**Otto Chat Widget Component:**
```typescript
// src/frontend/components/OttoChatWidget/OttoChatWidget.tsx
interface OttoChatWidgetProps {
  initialExpanded?: boolean;
  onVehicleSelect?: (vehicleId: string) => void;
}

export function OttoChatWidget({ initialExpanded = false, onVehicleSelect }: OttoChatWidgetProps) {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const { messages, sendMessage, isTyping } = useOttoConversation();

  return (
    <div className="otto-chat-widget fixed bottom-6 right-6 z-50">
      <AnimatePresence mode="wait">
        {isExpanded ? (
          <motion.div
            key="expanded"
            className="otto-chat-expanded w-96 h-[600px] glass-dark rounded-2xl overflow-hidden"
            initial={{ scale: 0.8, opacity: 0, originX: 1, originY: 1 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <ChatHeader onMinimize={() => setIsExpanded(false)} />
            <ChatMessageList messages={messages} />
            {isTyping && <TypingIndicator />}
            <ChatInput onSend={sendMessage} />
          </motion.div>
        ) : (
          <motion.button
            key="collapsed"
            className="otto-fab w-16 h-16 rounded-full glass-dark flex items-center justify-center"
            onClick={() => setIsExpanded(true)}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            <OttoAvatar size="md" showGlow />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Vehicle Detail Modal Component:**
```typescript
// src/frontend/components/VehicleDetailModal/VehicleDetailModal.tsx
interface VehicleDetailModalProps {
  vehicle: Vehicle;
  matchScore: number;
  isOpen: boolean;
  onClose: () => void;
  onReserve: (vehicleId: string) => void;
}

export function VehicleDetailModal({ vehicle, matchScore, isOpen, onClose, onReserve }: VehicleDetailModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        <Dialog.Content className="vehicle-detail-modal glass-modal fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] max-h-[90vh] overflow-y-auto">
          <div className="grid grid-cols-[1fr_350px] gap-6 p-6">
            {/* Left Column - Image Carousel */}
            <div>
              <ImageCarousel images={vehicle.images} videos={vehicle.videos} />
              <VehicleSpecifications vehicle={vehicle} />
              <KeyFeatures features={vehicle.features} />
            </div>

            {/* Right Column - Actions & Otto */}
            <div className="space-y-4">
              <SocialProofBadges
                viewers={vehicle.currentViewers}
                hasOffer={vehicle.hasActiveOffer}
                reservationExpiry={vehicle.reservationExpiry}
              />
              <PricingPanel
                price={vehicle.price}
                originalPrice={vehicle.originalPrice}
                savings={vehicle.savings}
              />
              <OttoRecommendation
                message={vehicle.ottoRecommendation}
                matchScore={matchScore}
              />
              <div className="space-y-3">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full bg-red-600 hover:bg-red-700"
                  onClick={() => onReserve(vehicle.id)}
                >
                  <Lock className="w-5 h-5 mr-2" />
                  Request to Hold This Vehicle
                </Button>
                <Button variant="secondary" size="lg" className="w-full">
                  <GitCompare className="w-5 h-5 mr-2" />
                  Compare to Similar Models
                </Button>
              </div>
            </div>
          </div>
          <Dialog.Close className="absolute top-4 left-4 p-2 rounded-full hover:bg-slate-100">
            <X className="w-5 h-5" />
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Error Handling

**Layered Error Handling Strategy:**

```python
# Custom exception hierarchy
class OttoAIException(Exception):
    """Base exception for Otto.AI"""
    pass

class ValidationError(OttoAIException):
    """Data validation errors"""
    pass

class SemanticSearchError(OttoAIException):
    """Search service errors"""
    pass

class RealtimeUpdateError(OttoAIException):
    """Real-time communication errors"""
    pass

# Error handling middleware
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except OttoAIException as e:
        logger.error(f"Otto.AI error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e), "type": e.__class__.__name__}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

### Logging Strategy

**Structured Logging Approach:**

```python
# Centralized logging configuration
import structlog

logger = structlog.get_logger()

# Usage in services
class VehicleSearchAgent:
    async def search(self, query: str, user_id: str):
        logger.info("Vehicle search started",
                   user_id=user_id,
                   query_length=len(query))

        try:
            results = await self._perform_search(query, user_id)

            logger.info("Vehicle search completed",
                       user_id=user_id,
                       results_count=len(results),
                       processing_time=results.processing_time)

            return results

        except Exception as e:
            logger.error("Vehicle search failed",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
            raise
```

## Data Architecture

### Core Data Models

**Vehicle Data Model (IMPLEMENTED):**
```python
class VehicleData(BaseModel):
    id: str
    vin: str
    make: str
    model: str
    year: int
    mileage: int
    price: Decimal
    description: str
    features: List[str]
    images: List[str]
    specifications: Dict[str, Any]

class VehicleEmbedding(BaseModel):
    vehicle_id: str
    embedding: List[float]  # Vector for semantic search
    text_embedding: List[float]  # Text-only embedding
    semantic_tags: List[str]
    image_count: int
```

**PDF Processing Model (IMPLEMENTED):**
```python
class VehicleListingArtifact(BaseModel):
    listing_id: str
    vin: str
    vehicle_data: VehicleData
    images: List[EnhancedImage]
    metadata: Dict[str, Any]
    processing_time: float

class EnhancedImage(BaseModel):
    url: str
    description: str
    category: str  # hero, carousel, detail
    quality_score: int
    alt_text: str
```

**User Favorites Model (IMPLEMENTED):**
```python
class UserFavorite(BaseModel):
    user_id: str
    vehicle_id: str
    created_at: datetime
    notified_on_price_change: bool = False
    notified_on_availability: bool = False
```

**Collection Model (IMPLEMENTED):**
```python
class VehicleCollection(BaseModel):
    id: str
    name: str
    description: str
    creator_id: str
    vehicle_ids: List[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime
```

### Database Schema (IMPLEMENTED)

```sql
-- Vehicle embeddings for semantic search
CREATE TABLE vehicle_embeddings (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(255) UNIQUE NOT NULL,
    embedding VECTOR(3072),  -- RAG-Anything embedding dimension
    text_embedding VECTOR(3072),
    semantic_tags TEXT[],
    image_count INTEGER DEFAULT 0,
    metadata_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW indexes for fast vector search
CREATE INDEX vehicle_embeddings_embedding_idx
ON vehicle_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 80);

-- Vehicle metadata
CREATE TABLE vehicle_metadata (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(255) UNIQUE NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    mileage INTEGER,
    price DECIMAL(10,2),
    description TEXT,
    features TEXT[],
    specifications JSONB,
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    vehicle_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, vehicle_id)
);

-- Vehicle collections
CREATE TABLE vehicle_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    creator_id VARCHAR(255) NOT NULL,
    vehicle_ids TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price monitoring for favorites
CREATE TABLE price_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id VARCHAR(255) UNIQUE NOT NULL,
    last_known_price DECIMAL(10,2),
    last_price_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    price_change_threshold DECIMAL(5,2) DEFAULT 5.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WebSocket connections
CREATE TABLE websocket_connections (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    vehicle_ids TEXT[] DEFAULT '{}',
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_ping TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Contracts

### Core API Endpoints (IMPLEMENTED)

**Vehicle Listings API:**
```python
# PDF upload and processing endpoint
@listings_router.post("/upload", response_model=ListingUploadResponse)
async def upload_listing(file: UploadFile = File(...)):
    """Upload and process PDF vehicle listing"""
    pdf_bytes = await file.read()
    listing_artifact = await pdf_service.process_pdf(pdf_bytes)

    return ListingUploadResponse(
        success=True,
        listing_id=listing_artifact.listing_id,
        vin=listing_artifact.vehicle_data.vin,
        vehicle_info=listing_artifact.vehicle_data.dict(),
        image_count=len(listing_artifact.images),
        processing_time=listing_artifact.processing_time,
        message="PDF processed successfully"
    )

# Get vehicle listings
@listings_router.get("/", response_model=List[ListingSummary])
async def get_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    make: Optional[str] = None,
    model: Optional[str] = None
):
    """Retrieve vehicle listings with optional filters"""
    return await listings_service.get_listings(skip, limit, make, model)
```

**Semantic Search API:**
```python
# Semantic search endpoint
@app.post("/api/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """Perform semantic vehicle search"""

    # Generate embeddings using RAG-Anything
    embeddings = await rag_service.generate_embeddings(
        query=request.query,
        images=request.images
    )

    # Search using pgvector similarity
    results = await vector_store.similarity_search(
        embeddings=embeddings,
        limit=request.limit
    )

    return SemanticSearchResponse(
        vehicles=results.vehicles,
        similarity_scores=results.scores,
        processing_time=results.processing_time
    )
```

**Vehicle Comparison API:**
```python
# Compare multiple vehicles
@comparison_router.post("/compare")
async def compare_vehicles(request: ComparisonRequest):
    """Compare multiple vehicles side by side"""

    comparison_result = await comparison_engine.compare(
        vehicle_ids=request.vehicle_ids,
        comparison_criteria=request.criteria
    )

    return ComparisonResponse(
        vehicles=comparison_result.vehicles,
        comparison_matrix=comparison_result.matrix,
        recommendations=comparison_result.recommendations
    )
```

**Favorites API:**
```python
# Add vehicle to favorites
@favorites_router.post("/{vehicle_id}")
async def add_favorite(vehicle_id: str, user_id: str):
    """Add vehicle to user favorites"""
    await favorites_service.add_favorite(user_id, vehicle_id)
    return {"message": "Vehicle added to favorites"}

# Get user favorites
@favorites_router.get("/", response_model=List[VehicleSummary])
async def get_favorites(user_id: str):
    """Get user's favorite vehicles"""
    return await favorites_service.get_user_favorites(user_id)
```

**Collections API:**
```python
# Create collection
@collections_router.post("/", response_model=CollectionResponse)
async def create_collection(request: CreateCollectionRequest):
    """Create a new vehicle collection"""

    collection = await collections_service.create_collection(
        name=request.name,
        description=request.description,
        creator_id=request.creator_id,
        vehicle_ids=request.vehicle_ids
    )

    return CollectionResponse(collection=collection)

# Get trending collections
@collections_router.get("/trending")
async def get_trending_collections(limit: int = 10):
    """Get trending vehicle collections"""
    return await trending_algorithm.get_trending(limit)
```

**Authentication API (Progressive Auth):**
```python
# Session management endpoints (auth_api.py)
auth_router = APIRouter(prefix="/api/auth")

@auth_router.post("/merge-session", response_model=MergeSessionResponse)
async def merge_session_to_account(request: MergeSessionRequest):
    """Merge guest session to authenticated user account

    Preserves conversation context from anonymous session before authentication.
    Transfers all Zep messages to user session.
    """
    result = await zep_client.merge_session_to_user(
        session_id=request.session_id,
        user_id=request.user_id
    )
    return MergeSessionResponse(
        success=True,
        messages_transferred=result['messages_transferred'],
        guest_session_id=request.session_id,
        user_session_id=result['user_session_id']
    )

@auth_router.get("/session/{session_id}/context", response_model=SessionContextResponse)
async def get_session_context(session_id: str):
    """Get guest session context for 'Welcome back!' greeting

    Enables returning visitor detection and personalized greetings.
    """
    context = await zep_client.get_last_visit_context(session_id)
    return SessionContextResponse(
        is_returning_visitor=context.get('is_returning_visitor', False),
        last_visit_date=context.get('last_visit_date'),
        previous_preferences=context.get('previous_preferences', []),
        message_count=context.get('message_count', 0)
    )
```

**Vehicles API (Story 3-7):**
```python
# Vehicle search with multi-select support (vehicles_api.py)
vehicles_router = APIRouter(prefix="/api/v1/vehicles")

@vehicles_router.get("/search", response_model=VehicleSearchResponse)
async def search_vehicles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    # Multi-select filters (Story 3-7)
    makes: Optional[str] = Query(None, description="Comma-separated makes (e.g., 'Toyota,Honda')"),
    vehicle_types: Optional[str] = Query(None, description="Comma-separated types (e.g., 'SUV,Sedan')"),
    # Sorting (Story 3-7)
    sort_by: Optional[str] = Query(None, description="Sort by: created_at, year, price, mileage"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    # Range filters
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None
):
    """Search vehicles with multi-select and sorting support (Story 3-7)

    - Multi-select makes using .in_() clause
    - effective_price sorting with NULL handling
    - Frontend uses sessionStorage for 30-min expiry
    """
```

**SSE Vehicle Updates API (Story 3-3b):**
```python
# SSE endpoint for real-time vehicle updates (vehicle_updates_sse.py)
@vehicle_updates_router.get("/updates")
async def get_vehicle_updates(
    request: Request,
    token: str = Query(..., description="JWT authentication token")
):
    """SSE endpoint for real-time vehicle updates (Story 3-3b)

    Returns StreamingResponse with text/event-stream Content-Type.
    Events:
    - vehicle_update: When vehicles list changes
    - availability_status_update: When vehicle status changes

    Replaces WebSocket for vehicle updates (simpler architecture, better testing).
    """
```

## Security Architecture

### Authentication & Authorization

**JWT-based Authentication:**
```python
# JWT token validation middleware
async def verify_jwt_token(request: Request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(401, "Invalid token")

        # Attach user context to request
        request.state.user_id = user_id
        request.state.user_role = payload.get("role", "user")

        return await call_next(request)

    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
```

**Role-based Access Control:**
```python
class UserRole(Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

# Permission checking decorator
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = request.state.user_role

            if not has_permission(user_role, permission):
                raise HTTPException(403, "Insufficient permissions")

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Progressive Authentication Pattern (2025-01-12):**

Otto.AI implements a **progressive authentication** model that enables users to browse and interact with the platform before creating an account. This creates a low-friction conversion funnel while maintaining personalization capabilities through session-based memory.

**Session-Based Memory Architecture:**

```python
# Guest session management with UUID v4 anonymous session IDs
class SessionService:
    SESSION_COOKIE = 'otto_session_id'
    SESSION_EXPIRY_DAYS = 30  # 30-day sliding window

    @staticmethod
    def getSessionId(): string {
        let sessionId = SessionService.getCookie(SESSION_COOKIE);
        if (!sessionId) {
            sessionId = SessionService.generateSessionId();  # UUID v4
            SessionService.setCookie(SESSION_COOKIE, sessionId, SESSION_EXPIRY_DAYS);
        }
        return sessionId;
    }

    @staticmethod
    async mergeSessionToAccount(userId: string): Promise<SessionMergeResult> {
        // Merge guest session to authenticated user account
        const response = await fetch('/api/auth/merge-session', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, user_id: userId })
        });
        // Clear session cookie after successful merge
    }
}
```

**Zep Cloud Guest Session Support:**

```python
# Zep client with anonymous session support
class ZepClient:
    async def create_guest_session(self, session_id: str) -> str:
        """Create Zep session for anonymous guest user"""
        guest_user_id = f"guest:{session_id}"
        await self.client.session.add(
            session_id=session_id,
            user_id=guest_user_id,
            metadata={
                'is_guest': True,
                'guest_session': True,
                'created_at': datetime.now().isoformat(),
                'platform': 'otto-ai',
                'last_seen': datetime.now().isoformat()
            }
        )
        return session_id

    async def merge_session_to_user(self, session_id: str, user_id: str) -> Dict:
        """Transfer guest session memory to authenticated user"""
        # 1. Retrieve all guest session messages
        guest_messages = await self.client.message.get(session_id, limit=1000)

        # 2. Create user session
        user_session_id = await self.create_session(user_id)

        # 3. Transfer messages to user session
        await self.client.session.add(
            session_id=user_session_id,
            messages=guest_messages
        )

        # 4. Mark guest session for cleanup (audit trail preserved)
        await self.client.session.update(
            session_id=session_id,
            metadata={'status': 'merged', 'merged_to_user': user_id}
        )

        return {'messages_transferred': len(guest_messages)}
```

**Auth API Endpoints:**

```python
# Session management endpoints
auth_router = APIRouter(prefix="/api/auth")

@auth_router.post("/session/create")
async def create_guest_session():
    """Create new anonymous session for guest users"""
    session_id = str(uuid.uuid4())
    await zep_client.create_guest_session(session_id)
    return {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }

@auth_router.post("/merge-session")
async def merge_session_to_account(request: MergeSessionRequest):
    """Merge guest session to authenticated user account"""
    result = await zep_client.merge_session_to_user(
        session_id=request.session_id,
        user_id=request.user_id
    )
    return result

@auth_router.get("/session/{session_id}/context")
async def get_session_context(session_id: str):
    """Get guest session context for 'Welcome back!' greeting"""
    context = await zep_client.get_last_visit_context(session_id)
    return {
        "is_returning_visitor": context.get('is_returning_visitor', False),
        "last_visit_date": context.get('last_visit_date'),
        "previous_preferences": context.get('previous_preferences', []),
        "greeting": "Welcome back! Last time you were looking at..."
    }
```

**Access Control Strategy:**

| Feature | Guest Access | Auth Required |
|---------|-------------|---------------|
| **Homepage & Vehicle Browsing** | ✅ Public | ❌ No |
| **Vehicle Search & Filters** | ✅ Public | ❌ No |
| **Vehicle Details** | ✅ Public (basic) | ✅ Full history reports |
| **Otto AI Chat** | ✅ Session-based | ✅ Persistent history |
| **Cascade Updates** | ✅ Session-based | ❌ No |
| **Favorites** | ❌ Prompt login | ✅ Yes |
| **Collections** | ❌ Prompt login | ✅ Yes |
| **Conversation History** | ⏱️ Session only (30-day) | ✅ Yes |
| **Hold Vehicle** | ❌ Prompt login | ✅ Yes |
| **Contact Seller** | ❌ Prompt login | ✅ Yes |

**Cookie Security:**

- **HTTP-only**: Prevents JavaScript access to session cookies
- **Secure**: HTTPS-only transmission
- **SameSite=Lax**: CSRF protection while allowing navigation
- **30-day sliding window**: Extends on each visit
- **UUID v4**: Cryptographically random session IDs

**Benefits:**

1. **Conversion Funnel**: Users experience value before authentication wall
2. **SEO Optimization**: Public homepage accessible to search crawlers
3. **Personalization**: Session-based memory enables "Welcome back!" greetings
4. **Frictionless Onboarding**: No barriers to initial exploration
5. **Seamless Transition**: Guest session merge preserves conversation context

### Data Security

**Sensitive Data Protection:**
```python
# PII encryption at rest
class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt_pii(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_pii(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Input sanitization
def sanitize_user_input(input_data: str) -> str:
    # Remove potential XSS attacks
    sanitized = html.escape(input_data)

    # Remove SQL injection patterns
    sanitized = re.sub(r'(--)|(;)|(\bDROP\b)|(\bDELETE\b)', '', sanitized)

    return sanitized.strip()
```

**API Security:**
```python
# Rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    user_id = getattr(request.state, "user_id", None)

    if await rate_limiter.is_rate_limited(client_ip, user_id):
        raise HTTPException(429, "Rate limit exceeded")

    return await call_next(request)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://otto.ai", "https://app.otto.ai"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Development Environment

### Prerequisites

**System Requirements:**
- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- Supabase account (for database hosting)
- OpenRouter API key (for PDF processing)

**Development Tools:**
- pip/conda for Python package management
- pytest for Python testing
- FastAPI for API development

### Setup Commands

```bash
# Clone repository
git clone https://github.com/otto-ai/otto-ai.git
cd otto-ai

# Create and activate conda environment
conda create -n otto-ai python=3.11
conda activate otto-ai

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - SUPABASE_URL
# - SUPABASE_KEY
# - OPENROUTER_API_KEY

# Set up database with pgvector
python src/semantic/setup_database.py

# Run the application
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs
# http://localhost:8000/redoc

# Run tests
pytest tests/
```

## Architecture Decision Records (ADRs)

### ADR-001: Pydantic + Custom Code vs LangChain
**Date:** 2025-11-29
**Status:** Accepted
**Decision:** Use Pydantic with custom code instead of LangChain for AI agent development

**Context:**
We needed to choose between using a comprehensive framework like LangChain or building custom code with Pydantic for type safety and validation.

**Decision:**
Choose Pydantic + custom code because:
- Full control over agent behavior and performance
- Type safety with Pydantic models
- No framework overhead or black box behavior
- Better alignment with our specific use cases
- Easier to optimize for our semantic search requirements

**Consequences:**
- More development time for agent logic
- Greater flexibility and performance control
- Cleaner, more maintainable codebase
- Direct integration with our chosen technologies

### ADR-002: Semantic Search Architecture
**Date:** 2025-11-29
**Status:** Accepted
**Decision:** Use RAG-Anything + Supabase pgvector for semantic vehicle search

**Context:**
Otto's core innovation requires sophisticated semantic understanding of vehicles across multiple modalities (text, images, video).

**Decision:**
Implement RAG-Anything for multimodal processing combined with Supabase pgvector for vector similarity search because:
- RAG-Anything handles text, images, and video seamlessly
- Supabase pgvector provides fast vector similarity search
- Integration is straightforward with existing PostgreSQL setup
- Scales well with our expected query volume

**Consequences:**
- Rich multimodal search capabilities
- Single database solution for relational and vector data
- Direct integration with our existing Supabase infrastructure
- Excellent performance for semantic similarity matching

### ADR-003: Real-time Communication Strategy
**Date:** 2025-11-29
**Status:** Implemented (Updated 2026-01-15 for Story 3-3b SSE Migration)
**Decision:** Use WebSocket + SSE for specialized real-time communication

**Context:**
Need to notify users about price changes and availability for favorited vehicles, and provide real-time vehicle updates when conversation preferences change.

**Story 3-3b Migration (2026-01-15):**
After experiencing test reliability issues with WebSocket reconnection loops, the architecture was updated to use Server-Sent Events (SSE) for vehicle updates while keeping WebSocket for Otto chat messages only.

**Decision:**
Implement hybrid real-time approach using:
- **WebSocket** (`ws://localhost:8000/ws/conversation`): Otto AI chat messages only (bidirectional)
- **SSE** (`GET /api/vehicles/updates`): Vehicle updates only (server → client)
- Separation of concerns: Chat (WebSocket) vs Updates (SSE)
- Native browser APIs: EventSource (SSE) no library needed, WebSocket for chat

**Architecture Before (Story 3-3):**
```
WebSocket: ws://localhost:8000/ws/conversation
├── Otto chat messages (bidirectional)
└── Vehicle updates (server push)
```

**Architecture After (Story 3-3b):**
```
WebSocket: ws://localhost:8000/ws/conversation
└── Otto chat messages ONLY (bidirectional)

SSE: GET /api/vehicles/updates?token=JWT
└── Vehicle updates ONLY (server push)
```

**Benefits of SSE Migration:**
1. **Simpler Architecture**: Unidirectional (server→client) for vehicle updates
2. **Easier Testing**: EventSource trivial to mock (no reconnection loops in tests)
3. **Native API**: No library needed, built into all browsers
4. **Better Alignment**: SSE designed specifically for server→push events
5. **Test Reliability**: Fixed infinite reconnection loop issue from Story 3-3

**Consequences:**
- Users receive real-time updates for favorited vehicles
- Vehicle grid updates via SSE when conversation preferences change
- Otto chat continues via WebSocket (unchanged functionality)
- Improved test reliability and simpler mocking
- Foundation for future real-time features

### ADR-004: Caching Strategy
**Date:** 2025-11-29
**Status:** Planned
**Decision:** Implement multi-level caching for performance optimization

**Context:**
Need to optimize database queries and API response times for vehicle search and retrieval.

**Decision:**
Implement caching strategy:
- Supabase built-in caching for frequent queries
- Multi-level cache service implementation ready
- Database query optimization with proper indexing
- Vector search optimization with HNSW indexes

**Consequences:**
- Improved query performance for vehicle searches
- Reduced database load for common operations
- Scalable architecture for future growth
- Cost optimization through efficient resource use

### ADR-005: Modular Python Architecture
**Date:** 2025-11-29
**Status:** Implemented
**Decision:** Use modular Python packages with clear separation of concerns

**Context:**
Need maintainable codebase that can scale while allowing multiple developers to work efficiently.

**Decision:**
Implement modular architecture:
- Service-oriented modules (api, services, semantic, search, etc.)
- Clear interfaces between modules
- Dependency injection for testability
- Shared models and utilities

**Consequences:**
- Maintainable and scalable codebase
- Easy to add new features
- Clear separation of concerns
- Good developer experience

### ADR-006: Hybrid PDF Processing for Vehicle Ingestion
**Date:** 2025-12-14
**Status:** Accepted
**Decision:** Use hybrid OpenRouter + PyMuPDF approach for vehicle data extraction from PDFs

**Context:**
Dealerships use diverse PDF formats for vehicle information, ranging from well-structured manufacturer sheets to scanned documents. A single extraction method cannot achieve the required 95%+ accuracy rate.

**Decision:**
Implement dual-path extraction strategy:
- OpenRouter AI for contextual understanding and handling unstructured/poor-quality documents
- PyMuPDF for precise, fast extraction from well-structured PDFs
- Smart merging algorithm that leverages strengths of both approaches

**Consequences:**
- Achieved 99.5% success rate in testing
- Higher processing cost due to AI usage (offset by automation benefits)
- Robust handling of edge cases and poor-quality scans
- Reduced manual data entry for dealers
- Foundation for scalable vehicle inventory management

### ADR-007: Architecture Documentation Update (2026-01-19)
**Date:** 2026-01-19
**Status:** Completed
**Decision:** Update architecture documentation to match verified code implementation

**Context:**
Architecture validation revealed significant gaps between documented architecture and actual codebase:
- Epic 3 claimed 0/13 stories with "NO FRONTEND CODE EXISTS" but 91 TypeScript files verified
- New backend files (repositories, auth_api, vehicles_api, vehicle_updates_sse) not documented
- Technology stack versions incomplete

**Decision:**
Comprehensive architecture update to reflect code reality:
- Epic 3 status corrected to PARTIAL (5/13 stories complete)
- Frontend technology stack documented with actual versions
- Project structure updated with missing directories
- New API endpoints documented (auth, vehicles, SSE)
- Repository pattern layer added

**Verification Method:**
All changes based on actual code review, not documentation assumptions:
- `find frontend/src -name "*.tsx" -o -name "*.ts"` → 91 files confirmed
- `ls -la src/repositories/` → 24KB code confirmed
- `ls -la src/api/` → New API files confirmed
- File content reviewed for implementation details

**Consequences:**
- AI agents now have accurate architecture for implementation
- Frontend development can continue with proper guidance
- Prevents duplicate code creation from missing documentation
- Architecture.md now matches sprint-status.yaml reality

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Original Date: 2025-11-29_
_Updated: 2025-12-14 (ADR-006 added)_
_Architecture Validation: 2026-01-19 (validation-report-architecture-2026-01-19.md)_
_Architecture Update: 2026-01-19 (Epic 3 frontend, new APIs documented)_
_For: Otto.AI Team_