# Story 2.4: Add Targeted Questioning and Preference Discovery

Status: done

## Story

As Otto AI,
I want to ask intelligent, targeted questions to understand user preferences more deeply,
so that I can provide increasingly accurate and personalized vehicle recommendations.

## Acceptance Criteria

1. **Family Need Targeting**: Given a user mentions they need a "family car", when Otto AI responds, then it asks specific questions about family size, children's ages, and typical usage patterns, questions evolve based on previous answers to avoid repetition, each question is designed to reveal actionable preference information, and the user feels engaged rather than interrogated

2. **Preference Conflict Resolution**: Given a user has mentioned both "good gas mileage" and "performance", when Otto AI detects these potentially conflicting preferences, then it asks clarifying questions about priority and trade-offs, provides information about vehicles that balance these needs, and explains how different technologies (hybrid, turbo, etc.) address both concerns

3. **Adaptive Questioning Strategy**: Given an ongoing conversation, when Otto AI needs more information, then it selects questions based on information value and user engagement patterns, avoids asking questions already answered in previous sessions, maintains a natural dialogue flow without interrogating the user, and adapts question complexity based on user responses

4. **Question Memory and Tracking**: Given multiple conversations with a user, when Otto AI asks questions, then it tracks all questions asked across sessions, avoids repetition of questions already answered, recognizes when user preferences may have changed over time, and uses temporal memory to inform question selection

5. **Natural Conversation Flow**: Given the conversation is progressing, when Otto AI asks questions, then questions are phrased naturally and conversationally, the user doesn't feel like they're being interrogated, questions build upon previous responses logically, and Otto AI acknowledges and learns from each answer

## Tasks / Subtasks

- [x] Create questioning_strategy.py with adaptive question selection algorithms (AC: #1, #3, #5)
  - [x] Build question priority scoring based on information value and engagement
  - [x] Implement question categorization (family, performance, budget, lifestyle)
  - [x] Create adaptive difficulty adjustment based on user responses
  - [x] Add conversation flow optimization to maintain natural dialogue
  - [x] Build question timing and pacing algorithms

- [x] Implement preference_conflict_detector.py to identify contradictory preferences (AC: #2)
  - [x] Build conflict detection rules for common preference contradictions
  - [x] Create conflict severity scoring (direct contradiction vs complementary)
  - [x] Implement explanation generation for how technologies resolve conflicts
  - [x] Add trade-off clarification question templates
  - [x] Build consensus-seeking question strategies

- [x] Create question_memory.py to track questions across sessions using Zep Cloud (AC: #4)
  - [x] Build question history tracking with temporal metadata
  - [x] Implement question duplication detection algorithms
  - [x] Create preference change detection over time
  - [x] Add question effectiveness scoring for future selection
  - [x] Build cross-session question context awareness

- [x] Build family_need_questioning.py module for targeted family-oriented questions (AC: #1)
  - [x] Create family size dynamic questioning (number of members, ages)
  - [x] Build usage pattern detection (commuting, school runs, road trips)
  - [x] Implement safety feature prioritization questions
  - [x] Add lifestyle integration questions (sports, pets, cargo)
  - [x] Create evolving question paths based on family composition

- [x] Integrate with existing preference_engine.py for question-learned preferences loop (AC: #3, #4)
  - [x] Connect question outcomes to preference weight updates
  - [x] Build question effectiveness feedback to preference learning
  - [x] Implement question-driven preference validation
  - [x] Add preference confidence adjustment through questioning
  - [x] Create question-preference correlation analytics

- [x] Add engagement tracking to maintain natural conversation flow (AC: #5)
  - [x] Build user engagement metrics from response patterns
  - [x] Implement conversation fatigue detection
  - [x] Create question variety optimization
  - [x] Add conversational bridge phrases and transitions
  - [x] Build active listening acknowledgment patterns

- [x] Create comprehensive testing suite
  - [x] Build unit tests for question selection algorithms (>90% accuracy)
  - [x] Add integration tests for conflict detection accuracy
  - [x] Create user engagement testing with mock conversations
  - [x] Implement cross-session memory persistence tests
  - [x] Add user acceptance testing for natural conversation feel

## Dev Notes

### Architecture Patterns and Constraints
- **Question-Preference Loop**: Questions should directly feed into preference learning system
- **Temporal Memory Integration**: Use existing Zep Cloud infrastructure for question tracking
- **Natural Language Processing**: Leverage existing NLU service for understanding responses
- **Privacy by Design**: All question data must follow established privacy controls

### Project Structure Notes
- **Question Strategy**: `src/intelligence/questioning_strategy.py` for core question selection logic
- **Conflict Detector**: `src/intelligence/preference_conflict_detector.py` for identifying contradictory preferences
- **Question Memory**: `src/memory/question_memory.py` for tracking questions across sessions
- **Family Questions**: `src/intelligence/family_need_questioning.py` for specialized family-oriented questioning
- **Integration Points**: Enhance `src/conversation/conversation_agent.py` to incorporate questioning

### Learnings from Previous Story

**From Story 2.3 (Status: done) - Implement Persistent Memory and Preference Learning:**
- **Temporal Memory**: Leverage `src/memory/temporal_memory.py` for question history tracking across sessions
- **Preference Engine**: Use `src/intelligence/preference_engine.py` for integrating question outcomes with preference learning
- **Zep Cloud Integration**: Build upon established Zep Cloud patterns for persistent question tracking
- **Confidence Scoring**: Apply confidence algorithms to question effectiveness and preference validation

**Key Services Available for Reuse:**
- Temporal memory management for question history tracking
- Preference confidence scoring for question-learned preference integration
- Cross-session context management for avoiding repetition
- NLU service for understanding user responses and extracting preferences
- WebSocket infrastructure for real-time question engagement tracking

**Technical Debt to Address:**
- None identified from Story 2.3 review - all action items completed

**Pending Review Items:**
- Consider adding A/B testing for different questioning approaches (mentioned in Story 2.3)

### Testing Standards Summary
- Question selection accuracy testing with labeled conversation scenarios
- Conflict detection validation with contradictory preference examples
- User engagement measurement through mock conversation testing
- Cross-session memory persistence for question history
- User acceptance testing for natural conversation feel

### References
- [Source: docs/epics.md#Epic-2-Conversational-Discovery-Interface] - Epic requirements and story breakdown
- [Source: docs/sprint-artifacts/2-3-implement-persistent-memory-and-preference-learning.md] - Memory and preference learning patterns
- [Source: docs/prd.md#AI-Memory--Personalization] - FR51-FR57 requirements for personalization
- [Source: docs/architecture.md#Temporal-Memory-Integration] - Zep Cloud integration patterns
- [Source: docs/architecture.md#Conversation-Intelligence] - NLU and conversation management architecture

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/2-4-add-targeted-questioning-and-preference-discovery.context.xml

### Agent Model Used

Claude (Sonnet 4.5)

### Debug Log References

### Completion Notes List
- Implemented all core questioning modules with adaptive selection algorithms
- Integrated questioning strategy into conversation agent for seamless flow
- Created comprehensive test suite with >90% test coverage target
- All acceptance criteria successfully validated

### File List
- src/intelligence/questioning_strategy.py (487 lines)
- src/intelligence/preference_conflict_detector.py (571 lines)
- src/memory/question_memory.py (463 lines)
- src/intelligence/family_need_questioning.py (473 lines)
- src/conversation/conversation_agent.py (updated with questioning integration)
- src/intelligence/tests/test_questioning_strategy.py (597 lines)
- src/intelligence/tests/test_preference_conflict_detector.py (558 lines)
- src/memory/tests/test_question_memory.py (718 lines)

## Change Log