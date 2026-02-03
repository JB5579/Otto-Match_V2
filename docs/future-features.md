# Future Features Backlog

> **Last Updated:** 2026-01-22
> **Purpose:** Track deferred features for post-MVP consideration
> **Decision Authority:** Product Manager + Team consensus

## Overview

This document tracks features that have been intentionally deferred from the current MVP scope. These features are **not cancelled** - they are preserved for future implementation once core functionality is validated with users.

**Deferral Criteria:**
- Feature is enhancement, not core functionality
- Core user journey can be validated without it
- No technical debt created by deferring
- Implementation can be cleanly added later

---

## Deferred Features

### From Epic 2: Conversational Discovery Interface

| Story | Feature | Deferred Date | Rationale | Code Status |
|-------|---------|---------------|-----------|-------------|
| 2-6 | Voice Input & Speech-to-Text | 2026-01-22 | Enhancement feature. Text conversation validates discovery UX. | **489 lines preserved** in `src/services/voice_input_service.py` |
| 2-7 | Conversation History & Session Summaries | 2026-01-25 | Retention feature, not acquisition. Core discovery validates in single session. Blocked by circular import. | **~3,600 lines preserved** - Backend (3,030), Frontend (910), Tests (700) |
| 2-8 | Multiple Conversation Threads | 2026-01-22 | Single thread validates UX. Multi-thread is post-MVP enhancement. | No code yet |
| 2-9 | Conversation Performance Optimization | 2026-01-22 | Premature optimization. Address when user load demands it. | No code yet |
| 2-10 | Otto AI Avatar System | 2026-01-22 | Visual polish, not core UX validation. | No code yet |

---

## Reactivation Criteria

Features should be reconsidered when:

1. **Core MVP Validated** - Discovery journey proves effective with real users
2. **User Feedback Demands** - Users explicitly request the feature
3. **Business Case Clear** - ROI or competitive need justifies investment
4. **Technical Foundation Ready** - No blockers from core architecture

### Reactivation Process

1. Product Manager creates reactivation proposal
2. Team reviews technical readiness
3. Story moves from `deferred` → `backlog` in sprint-status.yaml
4. Normal story workflow resumes (draft → ready-for-dev → implementation)

---

## Feature Details

### 2-6: Voice Input & Speech-to-Text

**What it does:** Allows users to speak to Otto instead of typing.

**Why deferred:** Text-based conversation is sufficient to validate the discovery journey UX. Voice is a convenience enhancement.

**Preserved code:**
- `src/services/voice_input_service.py` (489 lines)
- VoiceInputService class with Web Speech API integration
- VoiceState enum, VoiceResult/VoiceConfig dataclasses

**To reactivate:**
- Remove deferral header from service file
- Create frontend integration (WebSocket or REST endpoint)
- Add microphone UI component
- Test across browsers (Web Speech API support varies)

---

### 2-7: Conversation History & Session Summaries

**What it does:** Allows users to review past conversations, see journey summaries, search/filter history, export data, and manage privacy settings.

**Why deferred:** This is a **retention feature, not an acquisition feature**. It's valuable for return visits and long-term research spanning days/weeks, but NOT required to validate the core discovery journey in a single session.

**Key capabilities:**
- Chronological conversation list with summaries
- Journey dashboard showing research progress over time
- Search by vehicle/date/keywords
- Export to PDF/JSON
- GDPR compliance (data retention, deletion, export)
- Guest session support (cookie-based, 30-day persistence)

**Additional blocker:** Currently blocked by circular import between `ProfileService` and `ConversationAgent` via package `__init__.py`. Tests cannot run until this architectural issue is fixed.

**Preserved code (~3,600 lines):**
- Backend: `conversation_summary_service.py`, `conversation_export_service.py`, `conversation_history_service.py`, `conversations_api.py` (~3,030 lines)
- Frontend: `ConversationHistory.tsx` (403 lines), `ConversationDetail.tsx` (389 lines), `JourneySummary.tsx` (360 lines)
- Tests: `test_conversations_api.py`, `test_conversation_summary_service.py` (~700 lines - cannot run due to circular import)
- Database: Schema for `conversation_history` table with GDPR retention policies

**To reactivate:**
1. **Fix circular import first** - Remove `ConversationAgent` from `src/conversation/__init__.py` or use lazy imports
2. Verify tests pass: `pytest tests/integration/test_conversations_api.py`
3. Verify GDPR compliance (data retention, export, deletion)
4. Test guest→auth session merge functionality
5. Validate conversation summarization with GPT-4
6. Test export generation (PDF/JSON formats)

**Business case for reactivation:**
- User testing shows demand for conversation history
- Users are conducting multi-day/week research
- Return visit rate justifies retention features
- GDPR requirements become mandatory

---

### 2-8: Multiple Conversation Threads

**What it does:** Allows users to have separate conversation contexts (e.g., one for SUVs, one for sedans).

**Why deferred:** Single conversation thread proves the core UX. Users can start fresh by clearing context if needed.

**No code exists yet.**

**To reactivate:**
- Design thread management UX
- Extend Zep memory to support multiple sessions per user
- Add thread selector UI component

---

### 2-9: Conversation Performance Optimization

**What it does:** Caching, response streaming, latency optimization for conversations.

**Why deferred:** Premature optimization. Current performance is acceptable for validation. Optimize when scale demands it.

**No code exists yet.**

**To reactivate:**
- Benchmark current performance under load
- Identify bottlenecks with real usage data
- Implement targeted optimizations

---

### 2-10: Otto AI Avatar System

**What it does:** Visual avatar representation of Otto with expressions/animations.

**Why deferred:** Visual polish that doesn't affect core UX validation. Text responses work fine.

**No code exists yet.**

**To reactivate:**
- Design avatar visual system
- Create animation states (thinking, speaking, listening)
- Integrate with conversation flow

---

## Decision Log

| Date | Decision | Participants | Rationale |
|------|----------|--------------|-----------|
| 2026-01-22 | Defer 2-6, 2-8, 2-9, 2-10 | PM, Architect, SM, Dev, Analyst, UX | Focus on core discovery journey validation. Voice, multi-thread, performance, and avatar are enhancements, not core functionality. |
| 2026-01-25 | Defer 2-7 (Conversation History) | PM, Architect, SM, Dev, Analyst, UX, Test | Retention feature, not acquisition. Core discovery journey validates in single session without history. Also blocked by circular import (ProfileService ↔ ConversationAgent). Epic 2 now 100% core complete (5 stories). |

---

## Notes

- Deferred features remain in sprint-status.yaml with `deferred` status
- Code files (where they exist) are preserved with deferral headers
- This document is the single source of truth for future feature rationale
- Review this backlog quarterly or when planning new epics
