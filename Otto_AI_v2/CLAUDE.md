# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Otto.AI is an AI-powered vehicle discovery platform currently in the design and planning phase. This is a **greenfield project** using the **BMAD Method v6** framework for AI-driven agile development.

**Current Status**: Phase 3 (Solutioning) complete, ready for Phase 4 (Implementation) with 95/100 implementation readiness score.

## Architecture

**Core Technology Stack (planned)**:
- **Backend**: Python with Pydantic models (not LangChain)
- **Database**: Supabase PostgreSQL with pgvector for vector similarity
- **Semantic Search**: RAG-Anything multimodal search system
- **Real-time**: Hybrid SSE + WebSockets for live updates
- **Caching**: Cloudflare Edge + Redis + Supabase hybrid
- **Temporal Memory**: Zep Cloud for conversation context
- **Deployment**: Render.com intelligent autoscaling
- **Frontend**: Planned React/TypeScript with glass-morphism design system

**Key Innovation**: Dynamic cascade discovery where conversational AI insights trigger real-time vehicle grid updates, creating a living inventory that responds to conversation context.

## BMAD Method Workflow

This project uses the BMAD Method framework with specialized AI agents and workflows:

### Current Workflow Status
- **Phase 1**: Analysis (optional) - Completed
- **Phase 2**: Planning (required) - Completed
- **Phase 3**: Solutioning - Completed
- **Phase 4**: Implementation - Ready to begin

### Sprint Management
- Sprint status tracked in: `docs/sprint-artifacts/sprint-status.yaml`
- Stories organized into 8 epics with BDD acceptance criteria
- All 82 functional requirements have implementing stories

### Using BMAD Workflows
Load appropriate agents via Claude Code slash commands:
- `\*prd` - Product Requirements Document workflow (PM agent)
- `\*architecture` - System architecture design (Architect agent)
- `\*create-story` - Create user stories (SM agent)
- `\*dev-story` - Implement stories (DEV agent)
- `\*code-review` - Review implementations (SM agent)

### Archon MCP Research Workflow
**Research Before Implementation - Required for all development tasks**

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
├── docs/                           # All project documentation
│   ├── prd.md                     # Product Requirements Document
│   ├── architecture.md            # System architecture decisions
│   ├── epics.md                   # Epic and story breakdown
│   ├── sprint-artifacts/          # Sprint tracking and status
│   └── implementation-readiness-report-*.md
├── .bmad/                         # BMAD Method framework
│   ├── bmm/                       # BMAD Method module
│   └── core/                      # Core BMAD workflows
└── .claude/                       # Claude Code integration commands
```

**Note**: Source code (`src/`) will be created during Phase 4 implementation.

## Development Commands

### BMAD Framework Commands
```bash
# Install BMAD Method (if needed)
npx bmad-method@alpha install

# Initialize project workflow
*workflow-init

# Common development workflows
*create-story          # Create new user story
*dev-story            # Implement existing story
*code-review          # Review implementation
*sprint-planning      # Plan sprint work
*story-ready          # Mark story as ready for development
*story-done           # Mark story as completed
```

### Python Development Commands

**Testing with Correct Environment**:
```bash
# Run tests using otto-ai environment
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest

# Run specific test file
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest tests/test_semantic_search.py

# Run with coverage
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pytest --cov=src
```

**Package Management**:
```bash
# Install new packages to otto-ai environment
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pip install package_name

# List installed packages
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m pip list
```

**Application Execution**:
```bash
# Run FastAPI application
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" -m uvicorn main:app --reload

# Run semantic search scripts
"C:\Users\14045\miniconda3\envs\Otto-ai\python.exe" src/semantic/setup_database.py
```

### Project Status Tracking
- Sprint artifacts: `docs/sprint-artifacts/sprint-status.yaml`
- BMAD workflow status: `docs/bmm-workflow-status.yaml`
- Implementation readiness: Latest report in `docs/`

## Key Development Principles

### Dynamic Cascade Discovery
The core architecture pattern where:
1. Otto AI converses with buyers, learning preferences
2. Real-time vehicle grid updates cascade based on conversation insights
3. Semantic search powers contextual vehicle understanding

### Story Lifecycle
Stories follow this progression: `backlog → drafted → ready → in-progress → review → done`

### Multi-Agent Collaboration
Use party mode for complex decisions involving multiple specialized agents (PM, Architect, DEV, UX, etc.)

## Testing Strategy

Planned comprehensive testing approach:
- **System-level**: ATDD framework with comprehensive test design
- **Performance**: Edge caching and global content delivery
- **Real-time**: WebSocket and SSE testing
- **AI/ML**: Semantic search and conversational AI validation

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

# Install dependencies
conda activate otto-ai
pip install raganything[all] fastapi pydantic supabase pgvector openai uvicorn pytest pytest-asyncio
```

**Installed Key Packages**:
- `raganything v1.2.8` - Multimodal semantic search
- `fastapi` - API framework
- `pydantic` - Data validation
- `supabase` - Database client
- `pgvector` - Vector similarity
- `openai` - AI model integration
- `uvicorn` - ASGI server
- `pytest` - Testing framework

### Configuration Files

Configuration managed through:
- **Environment variables**: `.env` (contains API keys for Supabase, Groq, Mistral, Zep)
- **BMAD config**: `.bmad/bmm/config.yaml`
- **Claude settings**: `.claude/settings.local.json`

## Documentation Standards

All documentation follows BMAD Method standards with:
- Cross-referenced artifacts
- Traceability matrix from requirements to stories
- Comprehensive acceptance criteria
- Architecture decision records

## Next Steps for Implementation

1. Begin Phase 4: Implementation using sprint artifacts
2. Start with Epic 1: Semantic Vehicle Intelligence
3. Use DEV agent with `\*dev-story` workflow for each story
4. Track progress via `docs/sprint-artifacts/sprint-status.yaml`
5. Follow established patterns for real-time updates and semantic search