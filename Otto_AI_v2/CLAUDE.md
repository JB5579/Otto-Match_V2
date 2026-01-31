# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Otto.AI is an AI-powered vehicle discovery platform with a functional semantic search and vehicle ingestion system. This project uses the **BMAD Method v6** framework for AI-driven agile development.

**Current Status**: Phase 4 (Implementation) in progress. Epic 1 (Semantic Vehicle Intelligence) complete, Epic 2 (Conversational Discovery) actively being developed.

**⚠️ CRITICAL - Documentation Accuracy:** This project underwent comprehensive documentation cleanup on 2026-01-02, correcting status inflation from claimed 95-98% to verified 22-42% completion. All documentation now uses evidence-based verification with required status markers (✅/⚠️/📋). See "Documentation Standards" section below for details.

## Working Style: Research & Validate, Don't Auto-Agree

**CRITICAL**: When the user proposes an idea, approach, or solution:
1. **RESEARCH FIRST** - Use Archon MCP to search documentation before agreeing
2. **CHALLENGE ASSUMPTIONS** - Question ideas that lack evidence or technical grounding
3. **NEVER SAY "sounds good"** without verification
4. **IDENTIFY RISKS** - Point out potential problems, dependencies, or conflicts
5. **PROVIDE EVIDENCE** - Base all opinions on planning documentation, code reality, or tested patterns

**Before agreeing to any implementation:**
- Search relevant docs: `rag_search_knowledge_base(query="...")`
- Check code reality: `ls -la`, `grep -r`, `Read` the actual files
- Identify conflicts with existing patterns
- Consider testing, maintenance, and technical debt

**Response Pattern:**
- ❌ "That's a great idea!" → **NEVER SAY THIS**
- ❌ "Sounds reasonable" → **DON'T AGREE WITHOUT RESEARCH**
- ❌ "I think that will work" → **VERIFY FIRST**
- ✅ "Let me research that approach first..." → **ALWAYS START HERE**
- ✅ "I found X potential issue with that approach..." → **IDENTIFY RISKS**
- ✅ "The documentation says Y, which suggests..." → **USE EVIDENCE**
- ✅ "The code actually shows Z, which conflicts with that idea..." → **CHECK CODE REALITY**

## Code Reality Checks

**Before making any claim about the codebase, verify it:**

```bash
# Check if file/path exists
ls -la [path]

# Count lines in a file
wc -l [file]

# Search for implementation
grep -r "[pattern]" src/ frontend/

# Find all files of a type
find . -name "*.tsx" -o -name "*.py"

# Check imports and dependencies
grep -r "import" [file]
```

**Common Reality Checks:**
- "Is frontend implemented?" → `find frontend/src -name "*.tsx" | wc -l`
- "Does this function exist?" → `grep -r "function_name" src/`
- "What's the actual state?" → Read the actual file, don't guess
- "Is this configured?" → Check config files, environment variables

**When user asks about implementation status:**
1. Use file commands to check reality
2. Read the actual code to confirm
3. Check sprint-status.yaml for claimed status
4. Report the VERIFIED reality, not assumptions

## Architecture

**Core Technology Stack (implemented)**:
- **Backend**: Python 3.11+ with FastAPI and Pydantic models
- **Database**: Supabase PostgreSQL with pgvector for vector similarity
- **Semantic Search**: RAG-Anything multimodal search with LightRAG
- **PDF Processing**: OpenRouter (Gemini) + PyMuPDF hybrid extraction
- **Real-time**: WebSockets for favorites/collections notifications
- **Memory**: Zep Cloud for conversation context and temporal memory
- **AI Models**: Groq (via OpenRouter) for conversation, OpenAI for embeddings
- **Frontend**: React 19.2.0 + TypeScript 5.9.3 (Epic 3 partial implementation)
  - 66 TypeScript/React source files (~2,283 lines)
  - Vite 7.2.4 build system
  - Framer Motion for animations
  - Radix UI for modal components
  - Vitest for testing

**Key Architectural Patterns**:
1. **Hybrid PDF Ingestion**: Parallel OpenRouter AI + PyMuPDF extraction (backend only, no seller UI)
2. **Multimodal Semantic Search**: RAG-Anything generates embeddings for text, images, and structured data
3. **Layered Services**: API → Service → Repository pattern with async throughout
4. **Advisory Intelligence** (NEW 2025-12-31): Lifestyle entity extraction, priority rankings, decision signals for consultative conversations
5. **External Research Service** (NEW 2025-12-31): Groq Compound integration for ownership costs, owner experiences, lease analysis

## BMAD Method Workflow

This project uses the BMAD Method framework with specialized AI agents and workflows:

### Current Workflow Status
- **Phase 1**: Analysis - Completed
- **Phase 2**: Planning - Completed
- **Phase 3**: Solutioning - Completed
- **Phase 4**: Implementation - In Progress (Epic 2 active)

### Sprint Management
- Sprint status tracked in: `docs/sprint-artifacts/sprint-status.yaml`
- Stories organized into 8 epics with BDD acceptance criteria
- All 82 functional requirements have implementing stories

### Using BMAD Workflows
Load appropriate agents via Claude Code slash commands:
- `/bmad:bmm:workflows:prd` - Product Requirements Document workflow (PM agent)
- `/bmad:bmm:workflows:architecture` - System architecture design (Architect agent)
- `/bmad:bmm:workflows:create-story` - Create user stories (SM agent)
- `/bmad:bmm:workflows:dev-story` - Implement stories (DEV agent)
- `/bmad:bmm:workflows:code-review` - Review implementations (SM agent)
- `/bmad:bmm:workflows:story-context` - Generate story context before development
- `/bmad:bmm:workflows:workflow-status` - Check current workflow status

### Archon MCP Research Workflow
**Research Before Implementation - Required for ALL decisions, not just development tasks**

**MANDATORY RESEARCH TRIGGERS** (Research before you agree or proceed):
- User suggests a new approach or pattern
- User asks "should I do X?" or "is Y a good idea?"
- Any technical decision about libraries, frameworks, or architecture
- Before suggesting code changes
- When user claims something "should work"
- When comparing different solutions

**Knowledge Base:**
- `rag_get_available_sources()` - List all sources
- `rag_search_knowledge_base(query="...", source_id="...")` - Search docs
- `rag_search_code_examples(query="...", source_id="...")` - Find code

**Searching Specific Documentation:**
1. Get sources → `rag_get_available_sources()` - Returns list with id, title, url
2. Find source ID → Match to documentation (e.g., "Supabase docs" → "src_abc123")
3. Search → `rag_search_knowledge_base(query="vector functions", source_id="src_abc123")`

**General Research:**
```bash
# Search knowledge base (2-5 keywords only!)
rag_search_knowledge_base(query="authentication JWT", match_count=5)

# Find code examples
rag_search_code_examples(query="React hooks", match_count=3)
```

## Project Structure

```
otto-ai/
├── main.py                        # FastAPI application entry point
├── src/
│   ├── api/                       # FastAPI endpoints and routers
│   │   ├── main_app.py           # Alternative app entry
│   │   ├── websocket_endpoints.py # Conversation WebSocket handler
│   │   ├── semantic_search_api.py # Semantic search endpoints
│   │   ├── auth_api.py           # **NEW** Authentication: session merge, guest management (8.7KB)
│   │   ├── vehicles_api.py       # **NEW** Vehicle search API with multi-select (11.1KB)
│   │   ├── vehicle_updates_sse.py # **NEW** SSE endpoint for vehicle updates (10KB)
│   │   └── admin/                # Admin-specific APIs
│   ├── conversation/              # Conversational AI (Otto agent)
│   │   ├── conversation_agent.py # Main conversation orchestrator
│   │   ├── advisory_extractors.py # **NEW** Lifestyle entities, priority rankings (Phase 1)
│   │   ├── groq_client.py        # Groq LLM client via OpenRouter
│   │   ├── nlu_service.py        # Natural language understanding
│   │   └── response_generator.py # Response generation
│   ├── semantic/                  # RAG-Anything integration
│   │   ├── vehicle_processing_service.py # Multimodal embeddings
│   │   └── vehicle_database_service.py   # Vector storage
│   ├── services/                  # Core business services
│   │   ├── supabase_client.py   # **NEW** Centralized Supabase client singleton (60 lines)
│   │   ├── external_research_service.py  # **NEW** Ownership research via Groq (Phase 2)
│   │   ├── pdf_ingestion_service.py     # OpenRouter+PyMuPDF pipeline
│   │   └── vehicle_image_enhancement_service.py
│   ├── repositories/              # **NEW** Repository pattern layer (24KB)
│   │   ├── image_repository.py   # Image data access (12.9KB)
│   │   └── listing_repository.py # Listing data access (11.2KB)
│   ├── intelligence/              # AI intelligence modules
│   │   ├── questioning_strategy.py      # Smart question generation
│   │   └── preference_engine.py         # Preference learning
│   ├── memory/                    # Zep-based memory
│   │   ├── zep_client.py         # Zep Cloud client
│   │   └── temporal_memory.py    # Temporal memory manager
│   ├── recommendation/            # Recommendation engine
│   ├── collections/               # Vehicle collections system
│   ├── realtime_services/         # WebSocket notification services
│   └── models/                    # Pydantic data models
├── frontend/                      # React 19.2.0 + TypeScript 5.9.3 frontend
│   ├── src/
│   │   ├── app/                   # React Router setup, auth pages
│   │   ├── components/            # UI components (vehicle-grid, vehicle-detail, otto-chat, availability, notifications)
│   │   ├── context/               # React contexts (VehicleContext, NotificationContext, ConversationContext)
│   │   ├── hooks/                 # Custom React hooks
│   │   └── main.tsx               # App entry point
│   ├── package.json               # NPM dependencies
│   └── vite.config.ts             # Vite configuration
├── tests/                         # Test suite (unit, integration, performance)
├── docs/                          # BMAD documentation and sprint artifacts
│   ├── sprint-artifacts/         # Sprint status and story files
│   ├── prd.md                    # Product Requirements
│   ├── architecture.md           # System architecture
│   └── epics.md                  # Epic and story breakdown
└── .bmad/                         # BMAD Method framework
```

## Development Commands

### BMAD Framework Commands
```bash
# Check workflow status
/bmad:bmm:workflows:workflow-status

# Story development workflow
/bmad:bmm:workflows:story-context <story-id>  # Generate context before dev
/bmad:bmm:workflows:dev-story <story-id>      # Implement story
/bmad:bmm:workflows:story-ready <story-id>    # Mark ready for dev
/bmad:bmm:workflows:story-done <story-id>     # Mark as completed

# Other workflows
/bmad:bmm:workflows:create-story     # Create new user story
/bmad:bmm:workflows:code-review      # Review implementation
/bmad:bmm:workflows:sprint-planning  # Plan sprint work
```

### Python Development Commands

**Critical**: Always use the conda environment Python path:
```bash
PYTHON="C:\Users\14045\miniconda3\envs\Otto-ai\python.exe"
```

**Testing**:
```bash
# Run all tests
$PYTHON -m pytest

# Run specific test file
$PYTHON -m pytest tests/test_api_endpoints.py

# Run tests by marker
$PYTHON -m pytest -m unit          # Unit tests only
$PYTHON -m pytest -m integration   # Integration tests
$PYTHON -m pytest -m performance   # Performance tests

# Run single test with verbose output
$PYTHON -m pytest tests/test_file.py::test_function -xvs

# Run with coverage (configured in pytest.ini, 80% threshold)
$PYTHON -m pytest --cov=src --cov-report=term-missing
```

**Application**:
```bash
# Run FastAPI server (default port 8000)
$PYTHON -m uvicorn main:app --reload

# API docs available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

**Linting & Formatting**:
```bash
$PYTHON -m black src/      # Format code
$PYTHON -m isort src/      # Sort imports
$PYTHON -m flake8 src/     # Lint code
```

**Known Issue**: There is a circular import in the test setup (`ProfileService` ↔ `conversation_agent`). Tests currently fail to collect. To run tests, fix the circular import first.

### Frontend Development Commands

**Frontend Location**: `frontend/` directory (React 19.2.0 + TypeScript 5.9.3)

**Development**:
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (Vite)
npm run dev
# Dev server at http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

**Testing**:
```bash
cd frontend

# Run tests (Vitest)
npm test

# Run tests with UI
npm run test:ui

# Run coverage
npm run test:coverage
```

**Linting & Formatting**:
```bash
cd frontend

# Lint code
npm run lint

# Fix lint issues
npm run lint:fix

# Format code (Prettier)
npm run format
```

### Project Status Tracking
- **Single Source of Truth**: `docs/sprint-artifacts/sprint-status.yaml`
- BMAD workflow status: `docs/bmm-workflow-status.yaml`
- Implementation verification: `docs/verification-evidence-2026-01-02.md`
- Documentation cleanup: `docs/documentation-cleanup-completion-2026-01-02.md`

## Documentation Standards

**CRITICAL - Last Updated:** 2026-01-02

This project maintains evidence-based documentation standards following a comprehensive cleanup that corrected status inflation from claimed 95-98% to verified 22-42% completion.

### Status Markers (Required)

All documentation MUST use these markers consistently:
- ✅ **IMPLEMENTED** - Code exists, tests pass, verified in codebase
- ⚠️ **PARTIAL** - Code exists but incomplete (e.g., backend only, no UI)
- 📋 **PLANNED** - Documented but no code implementation exists
- ❌ **DEPRECATED** - Superseded or obsolete

### Documentation Hierarchy (Update Priority)

1. **`sprint-status.yaml`** - SINGLE SOURCE OF TRUTH (update FIRST)
2. **`CLAUDE.md`** - Primary developer guide (update SECOND)
3. **`architecture.md`** - Technical reference (update THIRD)
4. **`prd.md`** - Requirements tracking (update FOURTH)
5. **Story files** - Implementation details (update LAST)

### Verification Requirements

Before marking anything as "IMPLEMENTED", you MUST verify:
1. **Code Existence**: `ls -la [file_path]` and `wc -l [file_path]`
2. **Tests Pass**: `pytest [test_file] -v` (if applicable)
3. **Integration**: `grep -r "[feature]" main.py src/api/`
4. **Frontend**: `find . -name "*.tsx" | grep [feature]` (for UI features)

### Prohibited Claims (Without Evidence)

❌ **NEVER claim without verification evidence:**
- Specific percentages ("99.5% success rate", "95% test coverage")
- Performance metrics ("sub-500ms queries", "handles 10K users")
- Production readiness ("production-ready", "enterprise-grade")

✅ **Instead use:**
- "Estimated >90% success rate (tested with 50 sample PDFs)"
- "Target: <500ms (not yet benchmarked)"
- "Core functionality implemented, deployment infrastructure pending"

### Monthly Documentation Review

**Schedule:** 1st of each month
**Process:** `docs/documentation-review-process.md`
**Checklist:** `docs/documentation-standards-checklist.md`

**Quick Verification:**
```bash
# Verify Epic 1 implementation
ls -la src/search/*.py && wc -l src/search/*.py

# Verify Epic 2 implementation
ls -la src/conversation/*.py src/intelligence/*.py

# Verify Epic 3 frontend implementation
find frontend/src -name "*.tsx" -o -name "*.ts" | wc -l

# Run tests
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --tb=short
```

### Story Completion Workflow

When completing a story, follow this exact order:

1. **Verify Implementation**
   ```bash
   # Check files exist
   ls -la [implemented files]
   wc -l [implemented files]

   # Run tests
   pytest tests/[related tests] -v
   ```

2. **Update sprint-status.yaml FIRST**
   ```yaml
   story-id: done  # VERIFIED YYYY-MM-DD - [implementation note]
   ```

3. **Update Story File**
   - Change badge to ✅ DONE
   - Add implementation file paths with sizes
   - Update "Last Verified" date

4. **Update CLAUDE.md** (if epic status changes)
   - Update epic completion counts
   - Update completion percentages
   - Update "Last Updated" date

5. **Create Verification Evidence** (if major milestone)
   - Save command outputs to `docs/verification-evidence-YYYY-MM-DD.md`

### Documentation Quality Checks

**Red Flags (Require Immediate Correction):**
- sprint-status.yaml contradicts CLAUDE.md
- "IMPLEMENTED" claim without file path
- Specific percentage without evidence file
- "Last Verified" date >60 days old
- Future dates in documentation

## Key Development Patterns

### Service Pattern
All services follow async patterns with dependency injection:
```python
class SomeService:
    def __init__(self, dependency: Optional[DependencyType] = None):
        self.dependency = dependency or DefaultDependency()

    async def process(self, data: DataModel) -> ResultModel:
        # Async processing
        pass
```

### API Router Pattern
FastAPI routers with typed responses:
```python
@router.post("/endpoint", response_model=ResponseModel)
async def endpoint(request: RequestModel) -> ResponseModel:
    result = await service.process(request)
    return ResponseModel(**result)
```

### Story Lifecycle
Stories follow this progression: `backlog → drafted → ready-for-dev → in-progress → review → done`

### Testing
- Tests are organized by type: `tests/unit/`, `tests/integration/`, `tests/performance/`
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.performance`
- Coverage threshold: 80% (configured in pytest.ini)

## Environment Configuration

### Development Environment Setup

**Required Conda Environment**: `otto-ai`

This project uses a dedicated conda environment to manage Python dependencies. All Python commands MUST use the `otto-ai` environment to ensure proper package versions and compatibility.

**Critical Usage Requirement**:
Always use the full path to the Python executable to ensure the correct environment is used:

```bash
# Correct way to execute Python commands
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" script.py
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pip install package_name
```

**Environment Setup**:
```bash
# Create environment (if not exists)
conda create -n otto-ai python=3.11
conda activate otto-ai

# Install dependencies
pip install -r requirements.txt
```

**Key Dependencies** (see requirements.txt):
- `raganything[all]` - Multimodal semantic search with LightRAG
- `fastapi`, `uvicorn[standard]` - API framework
- `pydantic` - Data validation
- `supabase`, `pgvector`, `psycopg[binary]` - Database
- `openai` - Embeddings and AI
- `zep-python` - Conversation memory
- `pytest`, `pytest-asyncio`, `httpx` - Testing (circular import issue exists - see Development Commands)

### Frontend Technology Stack

**Core Frontend Technologies:**
- **React 19.2.0**: UI library with latest features
- **TypeScript 5.9.3**: Type-safe JavaScript
- **Vite 7.2.4**: Fast build tool and dev server
- **Framer Motion 12.23.26**: Animation library for cascade effects
- **Radix UI 1.1.15**: Accessible modal/dialog components
- **Lucide React 0.562.0**: Icon library
- **React Router DOM 7.11.0**: Client-side routing
- **Supabase JS 2.89.0**: Database client

**Frontend Testing:**
- **Vitest 4.0.16**: Fast unit testing
- **Testing Library**: React testing utilities
- **MSW 2.7.2**: API mocking

### Configuration Files

Configuration managed through:
- **Environment variables**: `.env` (required API keys below)
- **BMAD config**: `.bmad/bmm/config.yaml`
- **pytest config**: `pytest.ini`

**Required Environment Variables** (in `.env`):
```
# Backend
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENROUTER_API_KEY=...    # For Groq/Gemini via OpenRouter
OPENAI_API_KEY=...        # For embeddings
ZEP_API_KEY=...           # For conversation memory

# Frontend (create frontend/.env)
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

## Current Development Focus

**Last Updated:** 2026-01-25 | **Status:** Phase 4 (Implementation) - Core ~62%, Backend ~55%, Frontend ~60%

### 🔍 Documentation Cleanup Completed (2026-01-02)

**IMPORTANT:** A comprehensive documentation cleanup was completed on 2026-01-02 that corrected significant status inflation:

- **Before Cleanup:** Documentation claimed 95-98% readiness, "99.5% PDF success", "production-ready"
- **After Verification:** Actual 22% stories complete (18/82), 42% weighted backend, 0% frontend (as of 2026-01-02)
- **Frontend Update (2026-01-14):** Epic 3 now 5/13 stories complete, 30% frontend implementation
- **Architecture Update (2026-01-19):** Updated architecture.md, ux-design-specification.md, test-design-system.md, CLAUDE.md based on code verification
- **Epic 3 Code Audit (2026-01-23):** Stories 3-9 through 3-13 corrected from "backlog" to actual status (3 done, 2 partial)
- **Epic 2 Strategic Deferral (2026-01-25):** 5 stories (2-6 through 2-10) deferred to future-features.md, Epic 2 core now 100% complete
- **Changes Made:** 15 documents updated (2026-01-02), 4 documents updated (2026-01-19), 3 documents updated (2026-01-25)
- **New Standards:** Evidence-based verification required for all implementation claims
- **Process Established:** Monthly documentation review on 1st of each month

**Key Corrections:**
- Epic 1: Verified ✅ COMPLETE (12/12 stories, all files confirmed)
- Epic 2: 5 stories deferred (2-6, 2-7, 2-8, 2-9, 2-10) - core 5 stories complete
- Epic 3: Updated 2026-01-25 - 11/13 complete, 2 partial (was 5/13 on 2026-01-14)
- Story 2-7: Deferred from "review" (blocked by circular import, retention feature not MVP-critical)
- Story 5-4: Corrected from "in-progress" to "partial" (backend only, no seller UI)

**Documentation Standards Now Enforced:**
- All claims must have verification evidence (file paths, command outputs)
- Status markers required: ✅ IMPLEMENTED, ⚠️ PARTIAL, 📋 PLANNED, ❌ DEPRECATED
- No specific percentages without evidence files
- "Last Verified" dates required on all technical documentation

**Reference Documents:**
- Cleanup Report: `docs/documentation-cleanup-completion-2026-01-02.md`
- Verification Evidence: `docs/verification-evidence-2026-01-02.md`
- Architecture Validation: `docs/validation-report-architecture-2026-01-19.md`
- Standards Checklist: `docs/documentation-standards-checklist.md`
- Review Process: `docs/documentation-review-process.md`

---

### Epic Status Overview

**Epic 1: Semantic Vehicle Intelligence** ✅ COMPLETE (12/12 stories)
- Original 8 stories (1-1 through 1-8): COMPLETE
- RAG Enhancement stories (1-9 through 1-12): COMPLETE (Added 2025-12-31)
  - 1-9: Hybrid Search with FTS
  - 1-10: Query Expansion Service
  - 1-11: Re-ranking Layer
  - 1-12: Contextual Embeddings
- Retrospective: COMPLETE (2025-12-31)
- Last verified: 2026-01-02

**Epic 2: Conversational Discovery Interface** ✅ CORE COMPLETE (5/5 core stories, 5 deferred)
- Stories 2-1 through 2-5: ✅ COMPLETE
  - 2-1: Conversational AI Infrastructure
  - 2-2: NLU & Response Generation
  - 2-3: Persistent Memory (Zep Cloud)
  - 2-4: Targeted Questioning
  - 2-5: Real-time Vehicle Information
- **Recent Enhancements** (2025-12-31):
  - ✅ Phase 1: Advisory extractors with lifestyle entity extraction (1,073 lines)
  - ✅ Phase 2: External research service for ownership data (871 lines)
  - See: `docs/phase1-phase2-implementation-summary.md`
- Stories 2-6 through 2-10: 🔄 DEFERRED (enhancement features)
  - 2-6: Voice input - code preserved (489 lines) - deferred 2026-01-22
  - 2-7: Conversation history - code preserved (~3,600 lines) - deferred 2026-01-25
  - 2-8: Multiple conversation threads - deferred 2026-01-22
  - 2-9: Performance optimization - deferred 2026-01-22
  - 2-10: Otto AI avatar system - deferred 2026-01-22
  - See: `docs/future-features.md` for reactivation criteria
- **Rationale for deferrals:** Focus on core single-session discovery journey validation. Deferred features are retention/enhancement, not acquisition-critical.
- Last verified: 2026-01-25

**Epic 3: Dynamic Vehicle Grid Interface** ⚠️ PARTIAL (11/13 complete, 2 partial)
- Stories 3-1 through 3-8: ✅ COMPLETE (React 19.2.0 + TypeScript 5.9.3)
  - 3-1: Grid infrastructure and responsive layout
  - 3-2: Vehicle card component with lazy loading
  - 3-3: Real-time availability integration (partial - some ACs blocked)
  - 3-3b: SSE migration for real-time updates
  - 3-4: Interactive grid features (favorites, quick view)
  - 3-5: Availability status components
  - 3-6: Vehicle comparison tools
  - 3-7: Intelligent filtering and sorting
  - 3-8: Performance optimization and edge caching
- Stories 3-11, 3-12, 3-13: ✅ COMPLETE (implemented without formal story files)
  - 3-11: Match score badge (MatchScoreBadge.tsx - 186 lines)
  - 3-12: Vehicle detail modal (VehicleDetailModal.tsx - 188 lines)
  - 3-13: Otto chat widget (OttoChatWidget.tsx - 394 lines)
- Stories 3-9, 3-10: ⚠️ PARTIAL (backend exists, no story files)
  - 3-9: Analytics - backend code exists (1,489 lines), no frontend dashboard
  - 3-10: Glass-morphism - styles scattered across components, no design system file
- Implementation: 104 TypeScript/React files (~25,500 lines)
- Last verified: 2026-01-25

**Epic 4: User Authentication & Profiles** 📋 PLANNED (0/9 stories)
- No authentication system implemented
- All stories in backlog
- Last verified: 2026-01-02

**Epic 5: Lead Intelligence Generation** ⚠️ PARTIAL (2/8 stories)
- Story 5-4: PARTIAL (backend only, no seller UI)
- Story 5-4b: COMPLETE (PDF pipeline + database persistence)
- What works: PDF processing, multimodal extraction, database storage
- What's missing: Seller upload UI, batch processing interface
- Stories 5-1, 5-2, 5-3, 5-5 to 5-8: PLANNED
- Last verified: 2026-01-02

**Epic 6: Seller Dashboard & Analytics** 📋 PLANNED (0/8 stories)
- Backend services exist but no UI implementation
- All stories in backlog
- Last verified: 2026-01-02

**Epic 7: Deployment Infrastructure** 📋 PLANNED (0/6 stories)
- No production infrastructure
- All stories in backlog
- Last verified: 2026-01-02

**Epic 8: Performance Optimization** 📋 PLANNED (0/7 stories)
- Some optimization code exists but not organized into stories
- All stories in backlog
- Last verified: 2026-01-02

### Overall Project Completion

**Total Stories:** 82 (original) + 4 (RAG) + 2 (Phase 1/2) = 88 story units
**Fully Complete:** 28 stories (Epic 1: 12, Epic 2: 5 core, Epic 3: 11)
**Partially Complete:** 4 stories (Epic 3: 2 partial, Epic 5: 2 backend-only)
**Deferred:** 5 stories (Epic 2: 2-6, 2-7, 2-8, 2-9, 2-10 - see docs/future-features.md)
**Not Started:** 51 stories (Epic 4: 9, Epic 5: 6, Epic 6-8: 36)

**Completion Rate:**
- By story count: 32 stories complete/partial (28 + 4) = 36% of active scope (88 - 5 deferred)
- Core MVP features: Epic 1 (100%) + Epic 2 Core (100%) + Epic 3 (85%) = **~62% of core user journey**
- Weighted backend implementation: ~55% (core functionality complete)
- Frontend implementation: React 19.2.0 + TypeScript 5.9.3 (104 files, ~25,500 lines) = ~60%
- Infrastructure: 0% (Epic 7 not started)

**Actual Overall Status:**
- Core discovery journey: ~62% complete (search, conversation, grid display working)
- Authentication/user accounts: 0% (Epic 4 backlog)
- Deployment infrastructure: 0% (Epic 7 backlog)
- **Assessment:** Working demo with core features, not production-ready

### Key Implementation Files

**Epic 1 (Semantic Search):**
- `src/search/search_orchestrator.py` - RAG pipeline orchestrator
- `src/search/query_expansion_service.py` - LLM query expansion
- `src/search/hybrid_search_service.py` - Vector + FTS hybrid search
- `src/search/reranking_service.py` - BGE cross-encoder re-ranking
- `src/search/contextual_embedding_service.py` - Category-aware embeddings

**Epic 2 (Conversation AI):**
- `src/conversation/conversation_agent.py` - Main Otto orchestrator (84KB)
- `src/conversation/advisory_extractors.py` - **NEW** Phase 1: Lifestyle entities (44KB, 1,073 lines)
- `src/services/external_research_service.py` - **NEW** Phase 2: Ownership research (34KB, 871 lines)
- `src/conversation/nlu_service.py` - Natural language understanding (40KB)
- `src/memory/zep_client.py` - Zep Cloud temporal memory
- `src/intelligence/questioning_strategy.py` - Smart question generation

**Epic 5 (Lead Intelligence - Partial):**
- `src/services/pdf_ingestion_service.py` - PDF processing pipeline (34KB)
- `src/semantic/vehicle_processing_service.py` - Multimodal processing (50KB)

**Epic 3 (Frontend - Partial):**
- `frontend/src/components/vehicle-grid/VehicleGrid.tsx` - Responsive vehicle grid (260 lines)
- `frontend/src/components/vehicle-grid/VehicleCard.tsx` - Vehicle card component
- `frontend/src/components/vehicle-detail/VehicleDetailModal.tsx` - Vehicle detail modal
- `frontend/src/components/availability/` - Real-time availability status components
- `frontend/src/context/VehicleContext.tsx` - Vehicle state management

### Next Development Steps

**Current State:**
- ✅ Epic 1: Semantic Search - 100% COMPLETE
- ✅ Epic 2: Conversational AI (Core) - 100% COMPLETE (5 stories deferred to future-features.md)
- ⚠️ Epic 3: Dynamic Vehicle Grid - 85% COMPLETE (11/13 done, 2 partial: 3-9 analytics, 3-10 design system)

**Strategic Decision Point:**

You have three paths forward:

**Option A: SHIP FOCUS** (Recommended for Production)
- Build Epic 7: Deployment Infrastructure (0/6 stories)
  - Production hosting, CI/CD, monitoring, security
- Build Epic 4: Authentication (minimum viable - 2-3 stories)
  - User accounts, session management, or leverage Supabase Auth
- **Goal:** Ship working product to real users

**Option B: VALIDATE FOCUS** (Recommended for Demo/Testing)
- Complete Epic 3 remaining stories (3-9, 3-10 partial)
- User test existing Epic 1-3 functionality
- Gather feedback on core discovery journey
- **Goal:** Validate product-market fit before infrastructure investment

**Option C: CONTINUE BUILD** (Feature Development)
- Acknowledge building demo/prototype, not production system
- Continue Epic 3 polish (analytics dashboard, design system)
- Defer infrastructure indefinitely
- **Goal:** Rich feature set for demonstration purposes

**Epic 2 Deferred Features** (see docs/future-features.md):
- 2-6: Voice input (489 lines preserved)
- 2-7: Conversation history (~3,600 lines preserved, blocked by circular import)
- 2-8: Multiple conversation threads
- 2-9: Performance optimization
- 2-10: Otto AI avatar system

**To continue development**:
1. Check workflow status: `/bmad:bmm:workflows:workflow-status`
2. Generate story context: `/bmad:bmm:workflows:story-context <story-id>`
3. Implement story: `/bmad:bmm:workflows:dev-story <story-id>`
4. Track progress: `docs/sprint-artifacts/sprint-status.yaml`

**Reference Documentation:**
- Sprint status (single source of truth): `docs/sprint-artifacts/sprint-status.yaml`
- Deferred features: `docs/future-features.md`
- Implementation verification: `docs/verification-evidence-2026-01-02.md`
- Phase 1/2 details: `docs/phase1-phase2-implementation-summary.md`
- Architecture analysis: `docs/conversation-architecture-analysis.md`
- Frontend architecture: `frontend/src/` (React 19.2.0, TypeScript 5.9.3, Vite 7.2.4)