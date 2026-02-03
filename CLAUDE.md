# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Otto.AI is an AI-powered vehicle discovery platform using **BMAD Method v6** for AI-driven agile development.

**Current Status**: Phase 4 (Implementation) - Core MVP ~62% complete
- Epic 1: Semantic Vehicle Intelligence ✅ COMPLETE
- Epic 2: Conversational Discovery (Core) ✅ COMPLETE
- Epic 3: Dynamic Vehicle Grid ⚠️ 85% complete (11/13 done, 2 partial)
- Epic 4-8: PLANNED (0% complete)

**Git Repository**: https://github.com/JB5579/Otto-Match_V2.git

## Architecture Overview

### Technology Stack

**Backend:**
- Python 3.11+ with FastAPI and Pydantic v2
- Supabase PostgreSQL with pgvector for vector similarity
- RAG-Anything + LightRAG for multimodal semantic search
- OpenRouter (Groq/Gemini) + PyMuPDF hybrid PDF extraction
- Zep Cloud for conversation memory
- WebSockets for chat, SSE for vehicle updates

**Frontend:**
- React 19.2.0 + TypeScript 5.9.3
- Vite 7.2.4 build system
- Radix UI for components, Framer Motion for animations
- Vitest for testing, MSW for API mocking

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  VehicleGrid | VehicleDetail | OttoChat | Filters | Compare │
└───────────────────────────┬─────────────────────────────────┘
                            │ SSE + WebSocket
┌───────────────────────────▼─────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  /vehicles/search | /vehicles/updates | /chat | /collections │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────┐
│   Services   │  │ Semantic Search  │  │ Conversation│
│  PDF Ingest  │  │ RAG-Anything     │  │ NLU + Zep   │
│  Supabase    │  │ pgvector         │  │ Groq LLM    │
└──────────────┘  └──────────────────┘  └─────────────┘
```

### Key Architectural Patterns

1. **Service-Repository Pattern**: `API → Service → Repository → Database`
   - Services in `src/services/` contain business logic
   - Repositories in `src/repositories/` handle data access
   - All async with dependency injection

2. **Hybrid PDF Processing**: OpenRouter AI + PyMuPDF parallel extraction
   - `src/services/pdf_ingestion_service.py` - Main pipeline
   - `src/semantic/vehicle_processing_service.py` - Multimodal embeddings
   - Images uploaded to Supabase Storage via `scripts/reprocess_pdf_images.py`

3. **Semantic Search Pipeline**:
   - `src/search/query_expansion_service.py` - LLM query expansion
   - `src/search/hybrid_search_service.py` - Vector + FTS hybrid
   - `src/search/reranking_service.py` - BGE cross-encoder re-ranking
   - `src/search/contextual_embedding_service.py` - Category-aware embeddings

4. **Advisory Intelligence** (Phase 1):
   - `src/conversation/advisory_extractors.py` - Lifestyle entities, priorities (1,073 lines)
   - `src/intelligence/questioning_strategy.py` - Smart question generation

5. **External Research** (Phase 2):
   - `src/services/external_research_service.py` - Ownership costs, experiences (871 lines)

6. **Real-time Updates**:
   - `src/api/websocket_endpoints.py` - WebSocket for Otto chat
   - `src/api/vehicle_updates_sse.py` - SSE for vehicle grid updates with images

## Project Structure

```
otto-ai/
├── src/
│   ├── api/                      # FastAPI endpoints
│   │   ├── main_app.py          # Main FastAPI app (include all routers)
│   │   ├── vehicles_api.py      # Vehicle search with batch image fetching
│   │   ├── vehicle_updates_sse.py  # SSE endpoint for real-time updates
│   │   ├── semantic_search_api.py  # Semantic search endpoints
│   │   ├── websocket_endpoints.py  # WebSocket for Otto chat
│   │   └── auth_api.py          # Authentication (session merge, guest)
│   ├── search/                   # Enhanced semantic search
│   │   ├── query_expansion_service.py
│   │   ├── hybrid_search_service.py
│   │   ├── reranking_service.py
│   │   └── contextual_embedding_service.py
│   ├── semantic/                 # RAG-Anything integration
│   │   ├── vehicle_processing_service.py
│   │   └── vehicle_database_service.py
│   ├── conversation/             # Conversational AI
│   │   ├── conversation_agent.py  # Main Otto orchestrator (84KB)
│   │   ├── advisory_extractors.py  # Phase 1: Lifestyle entities
│   │   ├── groq_client.py
│   │   └── nlu_service.py
│   ├── services/                 # Core services
│   │   ├── supabase_client.py    # Centralized Supabase singleton
│   │   ├── external_research_service.py  # Phase 2: Ownership research
│   │   └── pdf_ingestion_service.py
│   ├── repositories/             # Repository pattern layer
│   │   ├── image_repository.py
│   │   └── listing_repository.py
│   ├── memory/                   # Zep-based memory
│   │   ├── zep_client.py
│   │   └── temporal_memory.py
│   ├── intelligence/             # AI modules
│   │   ├── questioning_strategy.py
│   │   └── preference_engine.py
│   ├── collections/              # Collections system
│   │   └── collection_engine.py
│   ├── realtime_services/        # WebSocket notifications
│   └── models/                   # Pydantic models
├── frontend/                     # React 19.2.0 + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── vehicle-grid/     # Responsive grid (3/2/1 columns)
│   │   │   ├── vehicle-detail/   # Modal with image carousel
│   │   │   ├── otto-chat/        # Floating chat widget
│   │   │   ├── availability/     # Real-time status
│   │   │   ├── filters/          # Multi-select filters
│   │   │   └── comparison/       # Vehicle comparison
│   │   ├── context/              # React contexts (Vehicle, Filter, etc.)
│   │   └── hooks/                # Custom hooks (useVehicleUpdates, etc.)
│   └── package.json
├── scripts/                      # Utility scripts
│   └── reprocess_pdf_images.py   # Upload PDF images to Supabase Storage
├── docs/                         # BMAD documentation
│   ├── sprint-artifacts/
│   │   └── sprint-status.yaml    # Single source of truth for status
│   ├── prd.md
│   ├── architecture.md
│   └── future-features.md        # Deferred Epic 2 features
├── tests/                        # Test suite
├── main.py                       # FastAPI entry point (Flask legacy in root)
└── requirements.txt
```

## Development Commands

### Environment Setup

**Critical**: Use the conda environment `otto-ai`:
```bash
# Activate environment
conda activate otto-ai

# Install dependencies
pip install -r requirements.txt
```

**Required Environment Variables** (`.env`):
```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENROUTER_API_KEY=...    # For Groq/Gemini via OpenRouter
OPENAI_API_KEY=...        # For embeddings
ZEP_API_KEY=...           # For conversation memory
```

### Python Backend

**Run Server:**
```bash
# Using full Python path (Windows)
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m uvicorn main:app --reload

# Or after activating conda environment
python -m uvicorn main:app --reload
```

**Testing:**
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_file.py::test_function -xvs

# Run by marker
pytest -m unit
pytest -m integration

# Coverage
pytest --cov=src --cov-report=term-missing
```

**Linting:**
```bash
black src/
isort src/
flake8 src/
```

**Known Issue**: Circular import in test setup (`ProfileService` ↔ `conversation_agent`)

### Frontend (React + TypeScript)

**Location:** `frontend/` directory

**Development:**
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Testing:**
```bash
npm test              # Run tests
npm run test:ui       # UI mode
npm run test:coverage # Coverage
```

**Linting:**
```bash
npm run lint          # Check
npm run lint:fix      # Fix
npm run format        # Prettier
```

## Key Development Patterns

### Service Pattern (async with DI)
```python
class SomeService:
    def __init__(self, dependency: Optional[DependencyType] = None):
        self.dependency = dependency or DefaultDependency()

    async def process(self, data: DataModel) -> ResultModel:
        # Async processing
        pass
```

### API Router Pattern
```python
@router.post("/endpoint", response_model=ResponseModel)
async def endpoint(request: RequestModel) -> ResponseModel:
    result = await service.process(request)
    return ResponseModel(**result)
```

### Pydantic v2 Settings Pattern
```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    field: str
    class Config:
        env_file = ".env"
```

### TYPE_CHECKING for Imports (avoid circular imports)
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .some_module import SomeClass
```

## Critical Files to Understand

**Semantic Search Pipeline:**
- `src/search/search_orchestrator.py` - Main orchestrator
- `src/search/query_expansion_service.py` - LLM query expansion
- `src/search/hybrid_search_service.py` - Vector + FTS
- `src/search/reranking_service.py` - BGE cross-encoder

**Conversation AI:**
- `src/conversation/conversation_agent.py` - Main Otto agent (84KB)
- `src/conversation/advisory_extractors.py` - Lifestyle entities (Phase 1)
- `src/services/external_research_service.py` - Ownership research (Phase 2)

**Vehicle APIs:**
- `src/api/vehicles_api.py` - REST API with batch image fetching
- `src/api/vehicle_updates_sse.py` - SSE endpoint with image support

**Frontend Core:**
- `frontend/src/components/vehicle-grid/VehicleGrid.tsx` - Main grid
- `frontend/src/context/VehicleContext.tsx` - Vehicle state
- `frontend/src/hooks/useVehicleUpdates.ts` - SSE hook

## BMAD Method Framework

This project uses BMAD Method v6 for AI-driven agile development.

**Workflow Status:** Phase 4 (Implementation) - In Progress

**Key Commands:**
```bash
# Check workflow status
/bmad:bmm:workflows:workflow-status

# Story development
/bmad:bmm:workflows:story-context <story-id>  # Generate context
/bmad:bmm:workflows:dev-story <story-id>      # Implement story
/bmad:bmm:workflows:story-done <story-id>     # Mark complete
```

**Status Tracking:** `docs/sprint-artifacts/sprint-status.yaml` (single source of truth)

## Documentation Standards

**Evidence-based verification required:**
- ✅ **IMPLEMENTED** - Code exists, tests pass, verified
- ⚠️ **PARTIAL** - Code exists but incomplete
- 📋 **PLANNED** - Documented, no code
- ❌ **DEPRECATED** - Superseded

**Before claiming "IMPLEMENTED", verify:**
```bash
ls -la [file_path]
wc -l [file_path]
pytest [test_file] -v
```

**No unverified claims:**
- ❌ "99.5% success rate"
- ✅ "Tested with 50 sample PDFs, >90% success"

## Recent Bug Fixes (2026-02-01)

1. **Pydantic v2**: `from pydantic_settings import BaseSettings`
2. **Circular imports**: Use `TYPE_CHECKING` pattern
3. **Dataclass field ordering**: Non-default args before default args
4. **Batch image fetching**: `vehicle_images` table queries in API responses
5. **SSE endpoint**: Returns vehicles with Supabase Storage image URLs

## Current Development Focus

**Completed:**
- Epic 1: Semantic Search (12/12 stories)
- Epic 2 Core: Conversational AI (5/5 stories, 5 deferred)
- Epic 3: Vehicle Grid (11/13 stories, 2 partial)

**Next Steps:**
- Option A: Build Epic 7 (Deployment) + Epic 4 (Auth) → Ship product
- Option B: Complete Epic 3 remaining stories → User testing
- Option C: Continue Epic 3 polish → Rich demo

**Deferred Features** (`docs/future-features.md`):
- Epic 2: Voice input, conversation history, multi-thread, performance, avatar

## Working Directory

**Git Repository Root:** `D:\Otto_AI_v2`
**Python Environment:** `otto-ai` conda environment
**Frontend:** `frontend/` subdirectory

**Previous Git Issue (Fixed 2026-02-03):**
- Was incorrectly initialized at `D:/` (entire drive)
- Re-initialized to `D:/Otto_AI_v2` (correct project directory)
- Pushed to `https://github.com/JB5579/Otto-Match_V2.git`
