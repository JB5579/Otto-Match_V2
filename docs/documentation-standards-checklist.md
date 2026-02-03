# Documentation Standards Checklist - Otto.AI

**Created:** 2026-01-02
**Purpose:** Ensure all documentation remains accurate and synchronized with actual implementation

---

## Table of Contents

1. [Status Markers](#status-markers)
2. [Story File Standards](#story-file-standards)
3. [Core Documentation Standards](#core-documentation-standards)
4. [Verification Requirements](#verification-requirements)
5. [Prohibited Claims](#prohibited-claims)
6. [Update Checklist](#update-checklist)

---

## Status Markers

### Required Markers

All technical documentation MUST use these status markers consistently:

- ✅ **IMPLEMENTED** - Code exists, tests pass, verified in codebase
- ⚠️ **PARTIAL** - Code exists but incomplete (e.g., backend only, no UI, missing features)
- 📋 **PLANNED** - Documented but no code implementation exists
- ❌ **DEPRECATED** - Superseded or obsolete, kept for historical reference

### Usage Examples

```markdown
**Status:** ✅ IMPLEMENTED
**Last Verified:** 2026-01-02
**Implementation:** src/search/search_orchestrator.py (13.7 KB)
```

```markdown
**Status:** ⚠️ PARTIAL (Backend Only)
**Last Verified:** 2026-01-02
**Implemented:** PDF processing pipeline
**Missing:** Seller upload UI, batch processing interface
```

```markdown
**Status:** 📋 PLANNED
**Last Verified:** 2026-01-02
**Note:** Epic 3 requires React/TypeScript frontend stack (not started)
```

---

## Story File Standards

### Required Story Header Format

ALL story files in `docs/sprint-artifacts/` MUST have this header:

```markdown
# Story X-Y: [Story Title]

**Story Status:** [✅ DONE | ⚠️ PARTIAL | 📋 BACKLOG] | **Last Updated:** YYYY-MM-DD | **Implementation Verified:** [YES | NO]

**Epic**: [Epic Number] - [Epic Name]
**Story ID**: X-Y
**Status**: [done | partial | backlog]
**[Completed/Started]**: YYYY-MM-DD
**Verified**: YYYY-MM-DD
**Priority**: P[0-2] - [Critical/High/Medium]
**Actual Effort**: [X days/hours]

**Implementation:** [File paths and brief description]
```

### Example: Completed Story

```markdown
# Story 1-9: Implement Hybrid Search with FTS

**Story Status:** ✅ DONE | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 1 - Semantic Vehicle Intelligence
**Story ID**: 1-9
**Status**: done
**Completed**: 2025-12-31
**Verified**: 2026-01-02
**Priority**: P0 - Critical
**Actual Effort**: 2 days

**Implementation:** `src/search/hybrid_search_service.py` (14.5 KB), Supabase migration with `hybrid_search_vehicles()` function
```

### Example: Partial Story

```markdown
# Story 5-4: Create Seller Vehicle Listings Management

**Story Status:** ⚠️ PARTIAL (Backend Only) | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 5 - Lead Intelligence Generation
**Story ID**: 5-4
**Status**: partial
**Started**: 2025-12-14
**Verified**: 2026-01-02
**Priority**: P0 - Critical
**Actual Effort**: 3 days (backend)

**Implementation:** `src/services/pdf_ingestion_service.py` (34 KB), `src/semantic/vehicle_processing_service.py` (50 KB)
**Missing:** Seller upload UI, batch processing dashboard
```

### Example: Backlog Story

```markdown
# Story 2-6: Add Voice Input and Speech-to-Text Conversion

**Story Status:** 📋 BACKLOG | **Last Updated:** 2026-01-02 | **Implementation Verified:** NO

**Epic**: 2 - Conversational Discovery Interface
**Story ID**: 2-6
**Status**: backlog
**Created**: 2025-12-01
**Verified**: 2026-01-02
**Priority**: P1 - High
**Estimated Effort**: 3-4 days

**Note:** Not started - requires voice/STT library selection and integration
```

---

## Core Documentation Standards

### 1. CLAUDE.md

**Update Trigger:** Any epic or story status change
**Required Sections:**
- "Current Development Focus" with epic-by-epic status
- "Last Updated" timestamp
- Accurate completion percentages
- Implementation file paths for completed work

**Checklist:**
- [ ] Epic status matches sprint-status.yaml
- [ ] Completion percentages verified against codebase
- [ ] File paths point to actual existing files
- [ ] "Last Verified" date is current

### 2. docs/architecture.md

**Update Trigger:** New features implemented or major architectural changes
**Required Sections:**
- "Implemented Features Summary" with verification date
- Status markers for all major components
- "Recent Architectural Enhancements" for new work

**Checklist:**
- [ ] All features have ✅/⚠️/📋 markers
- [ ] File paths verified
- [ ] "Last Verified" dates added
- [ ] No speculative performance claims

### 3. docs/prd.md

**Update Trigger:** Any FR implementation milestone
**Required Sections:**
- "Implementation Status Summary" table
- Per-FR category tracking

**Checklist:**
- [ ] FR percentages match actual implementation
- [ ] Table shows breakdown by category
- [ ] "Last Updated" date current
- [ ] Links to verification evidence

### 4. docs/sprint-artifacts/sprint-status.yaml

**Update Trigger:** Story status changes (backlog → in-progress → done/partial)
**Critical:** This is the SINGLE SOURCE OF TRUTH

**Checklist:**
- [ ] Story status matches actual code implementation
- [ ] Verification notes added for "done" stories
- [ ] Format: `story-id: done  # VERIFIED YYYY-MM-DD - [note]`
- [ ] Epic status rolls up from story statuses

---

## Verification Requirements

### Before Marking Anything as "IMPLEMENTED"

**MUST verify:**

1. **Code Existence**
   ```bash
   ls -la [file_path]
   wc -l [file_path]
   ```

2. **Tests Pass** (if applicable)
   ```bash
   python -m pytest [test_file] -v
   ```

3. **Integration Status**
   ```bash
   grep -r "[feature_name]" main.py src/api/
   ```

4. **Frontend Verification** (for UI features)
   ```bash
   find . -name "*.tsx" -o -name "*.jsx" | grep [feature]
   ```

### Verification Evidence

Create evidence files for major milestones:
- Format: `docs/verification-evidence-YYYY-MM-DD.md`
- Contents: Command outputs, file lists, test results
- Purpose: Reference for documentation claims

---

## Prohibited Claims

### ❌ NEVER Include Without Evidence

**Specific Percentages:**
- ❌ "99.5% success rate"
- ❌ "95% test coverage"
- ❌ "98/100 readiness score"

**Use instead:**
- ✅ "Estimated >90% success rate (tested with 50 sample PDFs)"
- ✅ "Test coverage: See pytest --cov output"
- ✅ "Implementation: 22% stories complete (18/82)"

**Performance Claims:**
- ❌ "Sub-500ms query times"
- ❌ "Handles 10,000 concurrent users"

**Use instead:**
- ✅ "Target: <500ms (not yet benchmarked)"
- ✅ "Designed for 10K users (load testing pending)"

**Production Readiness:**
- ❌ "Production-ready"
- ❌ "Enterprise-grade"

**Use instead:**
- ✅ "Integration testing pending"
- ✅ "Core functionality implemented, deployment infrastructure pending"

---

## Update Checklist

### When Completing a Story

- [ ] 1. Update `sprint-status.yaml` with "done" and verification note
- [ ] 2. Update story file with ✅ DONE badge and implementation details
- [ ] 3. Update CLAUDE.md "Current Development Focus" if needed
- [ ] 4. Run verification commands and save output
- [ ] 5. Update epic status in sprint-status.yaml if all stories done
- [ ] 6. Update architecture.md if new components added
- [ ] 7. Update prd.md FR status if functional requirements completed

### When Starting a Story

- [ ] 1. Update `sprint-status.yaml`: backlog → in-progress
- [ ] 2. Update story file status badge to "in-progress"
- [ ] 3. Add "Started: YYYY-MM-DD" to story file

### When Archiving Documents

- [ ] 1. Add archive header with reason and date
- [ ] 2. Move to appropriate `docs/archive/` subdirectory
- [ ] 3. Update references in other documents
- [ ] 4. Create `.original-` backup if making substantial edits

### Monthly Documentation Review

- [ ] 1. Verify all "Last Verified" dates are <30 days old
- [ ] 2. Run verification commands for all "IMPLEMENTED" claims
- [ ] 3. Update sprint-status.yaml with current status
- [ ] 4. Archive status reports >30 days old
- [ ] 5. Check for contradictions between docs
- [ ] 6. Update completion percentages

---

## Quick Reference

### Story Status Flow

```
backlog → drafted → ready-for-dev → in-progress → review → done
                                                         ↓
                                                      partial
```

### Documentation Hierarchy (Update Priority)

1. **sprint-status.yaml** (SINGLE SOURCE OF TRUTH)
2. **CLAUDE.md** (Primary developer guide)
3. **architecture.md** (Technical reference)
4. **prd.md** (Requirements tracking)
5. **Story files** (Implementation details)

### File Paths for Verification

**Epic 1 (Search):**
- `src/search/search_orchestrator.py`
- `src/search/query_expansion_service.py`
- `src/search/hybrid_search_service.py`
- `src/search/reranking_service.py`
- `src/search/contextual_embedding_service.py`

**Epic 2 (Conversation):**
- `src/conversation/conversation_agent.py`
- `src/conversation/nlu_service.py`
- `src/conversation/advisory_extractors.py`
- `src/services/external_research_service.py`
- `src/memory/zep_client.py`
- `src/intelligence/questioning_strategy.py`

**Epic 5 (Partial):**
- `src/services/pdf_ingestion_service.py`
- `src/semantic/vehicle_processing_service.py`

---

## Enforcement

**Before ANY commit that claims implementation:**
1. Run verification commands
2. Update sprint-status.yaml FIRST
3. Update other docs to match
4. Add "Last Verified" date
5. No percentages without evidence

**Red Flags (Requires Review):**
- Specific percentages without evidence file
- "Production-ready" without deployment
- Future dates in documentation
- Contradictions between sprint-status.yaml and other docs
- Missing "Last Verified" dates

---

*This checklist was created during the 2026-01-02 documentation cleanup to prevent future documentation drift.*
