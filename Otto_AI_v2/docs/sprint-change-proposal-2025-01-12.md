# Sprint Change Proposal: Remove Forced Login for Public Vehicle Discovery

**Date:** 2025-01-12
**Status:** Draft - Awaiting Approval
**Priority:** HIGH - Blocks Story 3-4 testing completion
**Change Scope:** Moderate (Documentation updates + targeted code changes)

---

## Executive Summary

**Issue:** Homepage requires authentication before users can browse vehicles or interact with Otto AI, blocking all public access and defeating the platform's conversion funnel.

**Root Cause:** Product strategy ambiguity in requirements - Otto.AI was implemented as "walled garden" requiring authentication at entry, rather than "public discovery platform with authentication as a layer for personalization."

**Recommended Solution:** Remove authentication requirement from homepage and vehicle browsing, implement session-based memory for guest users, and add progressive authentication (browse freely → sign up for memory persistence).

**Impact:**
- **Epic Impact:** Low - No epics invalidated. Epic 2, 3, 4 need acceptance criteria additions for guest users.
- **Timeline Impact:** Minimal - ~8 hours implementation, no sprint resequencing.
- **Code Impact:** Low - Targeted changes to route protection, navigation, and session management.

**Estimated Effort:** ~8 hours (2 hours code, 3 hours session infrastructure, 3 hours documentation)

---

## 1. Issue Summary

### 1.1 Trigger

**Discovered During:** Story 3-4 (Vehicle Detail Modal) testing
**Discoverer:** Frontend Developer running dev server
**Timestamp:** 2025-01-12

**Observation:**
> "I am unable to view your results because I am blocked by a signin auth screen that doesn't resolve to anywhere. So, Why am I forced to login or sign up to simply view the main page?"

### 1.2 Problem Statement

**Current Behavior:**
- Visit `/` → Redirected to `/login` → Cannot browse vehicles
- 100% of platform functionality blocked behind authentication wall
- Otto AI chat inaccessible without login
- Vehicle discovery, search, and filtering require authentication

**Expected Behavior:**
- Visit `/` → Browse vehicles, search, view details, chat with Otto (guest session)
- Login only required for: favorites, conversation history, hold vehicles, contact sellers
- "Sign In" button visible in navigation for guests
- Progressive authentication: browse freely → [motivation point] → sign up

**Business Impact:**
- **Conversion Funnel Killer:** No value can be demonstrated before login wall
- **SEO Incompatible:** Search crawlers cannot index homepage or vehicle listings
- **Competitive Disadvantage:** Industry standard (Carvana, Vroom) is public browsing → account at purchase
- **Zep-Cloud Underutilized:** Guest personalization strategy not implemented

### 1.3 Root Cause Analysis

**Technical Root Cause:**
```typescript
// frontend/src/App.tsx lines 16-23
<Route
  path="/"
  element={
    <ProtectedRoute>  // ← Problem: forces authentication
      <HomePage />
    </ProtectedRoute>
  }
/>
```

**Strategic Root Cause:**
1. **PRD Ambiguity:** FR16-FR23 state "Users can search/browse..." without specifying guest vs. authenticated
2. **Missing Auth Strategy:** No documentation of public vs. private access boundaries
3. **Incomplete User Journeys:** UX flows show "Return User with Memory" but don't explain guest recognition
4. **Architecture Gap:** Zep-cloud integration doesn't document anonymous session support

---

## 2. Epic and Artifact Impact Documentation

### 2.1 Epic Impact Assessment

| Epic | Status | Impact | Required Changes |
|------|--------|--------|------------------|
| **Epic 1: Semantic Vehicle Intelligence** | ✅ COMPLETE | NONE | No changes required |
| **Epic 2: Conversational Discovery** | ⚠️ PARTIAL (6/10) | MODERATE | Add guest user ACs to stories 2-1 through 2-5 |
| **Epic 3: Dynamic Vehicle Grid** | 📋 IN PROGRESS (Story 3-4) | MODERATE | Add public access ACs to stories 3-1 through 3-4 |
| **Epic 4: User Authentication** | 📋 BACKLOG | LOW | Clarify auth scope in stories 4-1 through 4-9 |
| **Epic 5-8** | 📋 BACKLOG | NONE | Enabled by removing access barriers |

**Epic Sequencing:** No changes required. Current sprint plan remains valid.

**Story Invalidation:** NONE. All stories remain valid; acceptance criteria require additions, not rewrites.

### 2.2 Artifact Conflict Analysis

#### **PRD (docs/prd.md)** - 41 KB, 768 lines

**Conflicts Identified:**
1. No "Public/Guest Access Requirements" section
2. SEO strategy (lines 289-295) requires server-rendered homepage for search crawlers → **implicitly conflicts with forced login**
3. FR16-FR23 ambiguous about "Users" scope (guest vs authenticated)
4. Conversation flow examples show immediate Otto engagement without any login step
5. Missing "Authentication Gates" documentation
6. No "Progressive Authentication" pattern documented

**Required Updates:**
```markdown
## NEW SECTION: Access Control & Authentication Strategy

### Public Access (No Authentication Required)
- Homepage and vehicle browsing
- Natural language search and semantic discovery
- Vehicle detail views with photos, specs, pricing
- Otto AI conversational assistance (session-based memory)
- Category browsing and curated collections

### Authenticated Features (Sign In Required)
- Save vehicles to favorites
- Conversation history and preference learning
- User profile with saved searches and preferences
- Hold/reserve vehicles
- Seller tools and lead management

### Progressive Authentication Pattern
1. Guest arrives → Browse freely, chat with Otto (session ID)
2. Engages → Clicks favorite/reserve → Prompt: "Sign In to save"
3. Signs up → Session memory merged to account
4. Returns → Cookie-based recognition + "Welcome back!"
```

**Updated FRs (examples):**
- FR16: "Users **(including guests)** can search for vehicles using natural language queries..."
- FR22: "Authenticated users can save vehicles to favorites..."

---

#### **Architecture (docs/architecture.md)** - 47 KB, 1,302 lines

**Conflicts Identified:**
1. Zep Cloud integration (lines 111-113) doesn't specify anonymous session ID support
2. JWT authentication middleware (lines 1023-1046) described as mandatory, no public route bypass
3. No session ID architecture documented
4. No session-to-account merge flow

**Required Updates:**

Add new section after Zep Cloud configuration:

```markdown
### Session-Based Memory for Guest Users

**Anonymous Session Strategy:**
- Generate UUID-based session ID on first visit
- Store session in HTTP-only cookie (otto_session_id)
- Zep Cloud sessions keyed by session_id for guests
- Cookie expiry: 30 days

**Session-to-Account Merge:**
```python
async def merge_session_to_account(session_id: str, user_id: str):
    # Transfer Zep Cloud session memory to user account
    await zep_client.transfer_session(session_id, user_id)
    # Update conversation history ownership
    await update_conversation_ownership(session_id, user_id)
```

**Cookie-Based Recognition:**
```javascript
// Check for returning visitor
const sessionId = getCookie('otto_session_id')
if (sessionId) {
  const lastVisit = await getLastVisitDate(session_id)
  ottoGreeting = `Welcome back! Last time you were looking at ${lastPreferences}`
}
```

**Optional Authentication Middleware:**
```python
# JWT verification bypass for public routes
async def optional_auth(request: Request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY)
            request.state.user_id = payload.get("user_id")
        except jwt.PyJWTError:
            pass  # Allow unauthenticated access

    # Always proceed - auth is optional
    return await call_next(request)
```

---

#### **UX Design Specification (docs/ux-design-specification.md)** - 16 KB, 480 lines

**Conflicts Identified:**
1. "First-Time Discovery" flow (lines 239-243) assumes authenticated access
2. "Return User with Memory" flow (lines 252-257) shows `Landing (Recognized)` but doesn't explain recognition without login
3. No "Guest Experience" flows documented
4. No progressive authentication patterns
5. Navigation components (lines 376-388) don't show guest-state variants

**Required Updates:**

Add new user journey flows:

```markdown
### Flow 5: Guest Discovery Journey (NEW)
```
Landing (Anonymous) → Browse Vehicles → Chat with Otto (Session) →
Engage with Features → [Motivation Point: Favorite/Reserve] → Sign Up Prompt →
Account Created → Session Memory Merged → Full Personalization
```

**Flow 6: Returning Guest Recognition (NEW)**
```
Cookie Detected → Retrieve Last Session → Otto Greeting: "Welcome back!" →
"Last time you liked..." → Continue Conversation → Session Extended
```

**Component Updates:**
- Add `GuestNavigation` component (Sign In button, no email/logout)
- Add `AuthenticatedNavigation` component (email + Sign Out button)
- Document conditional rendering: `{user ? <AuthenticatedNav /> : <GuestNav />}`
```

---

#### **Epics (docs/epics.md)** - 142 KB, 2,991 lines

**Story-Level Conflicts:**

**Epic 2: Conversational Discovery**

| Story | Line | Conflict | Required AC Addition |
|-------|------|----------|---------------------|
| 2.1 | 622 | WebSocket `/ws/conversation/{user_id}` requires auth | Add: `/ws/conversation/session/{session_id}` for guests |
| 2.2 | 656 | No guest chat scenarios | "Given I'm a guest user with anonymous session ID..." |
| 2.3 | 690 | "When I return" assumes auth | Document session-based return recognition |
| 2.4 | 724 | No guest questioning | Add guest questioning ACs |
| 2.5 | 758 | Market data access undefined | Clarify guest vs auth access |

**Epic 3: Dynamic Vehicle Grid**

| Story | Line | Conflict | Required AC Addition |
|-------|------|----------|---------------------|
| 3.1 | 982 | SSE `/sse/vehicle-updates/{user_id}` requires auth | Add: `/sse/vehicle-updates/session/{session_id}` for guests |
| 3.2 | 1016 | "As a user" browsing | "Given I'm browsing without logging in..." |
| 3.3 | 1052 | Cascade updates for guests? | Clarify session-based cascade for guests |
| 3.4 | 1086 | Vehicle details public? | "Given I'm viewing vehicle details as a guest..." |
| 3.5 | 1124 | Favorites require auth | "Given I click favorite as guest → Sign In prompt appears" |
| 3.7 | 1192 | Saved filters require auth | "Given I try to save filters as guest → Sign In prompt" |

**Epic 4: User Authentication**

All stories need clarifying text: "Authentication is a layer for personalization (favorites, history), not a wall for access"

**Example AC Addition for Story 2.1:**
```gherkin
# NEW AC for Guest Users:
Given I'm a guest user on the homepage
When I start chatting with Otto AI
Then the system generates an anonymous session ID (UUID)
And stores session ID in browser cookie (otto_session_id)
And conversation works via WebSocket without authentication
And Otto responds with "Welcome! I'm Otto, your AI car shopping assistant"
```

---

## 3. Recommended Path Forward

### 3.1 Selected Approach: Option 1 - Direct Adjustment

**Decision:** Proceed with targeted changes within current epic structure.

**Rationale:**
1. ✅ Minimal disruption - Epic 3 development continues; ACs updated, not stories invalidated
2. ✅ Low risk - Changes are additive (public access + optional auth), not destructive
3. ✅ Aligned with user intent - User explicitly approved session-based memory strategy
4. ✅ Evidence-based - PRD SEO requirements, conversation flows, industry standards support public discovery
5. ✅ Efficient - ~8 hours vs. 1-2 week delay for rollback or PRD review

**Alternatives Considered and Rejected:**
- **Option 2 (Rollback):** Rejected - Destroys Story 3-4 work, contradicts user intent, significant timeline impact
- **Option 3 (PRD Review):** Rejected as blocking gate - PRD refinement can occur in parallel with implementation

### 3.2 User Strategy Alignment

**User's Key Insight (Quote):**
> "The key point is how does Otto-ai create a relationship with the user when they arrive for the first time and return during the car buying journey. This is why ZEP-cloud is important. I am not sure how we create that type of user personalization without forcing people to login."

**Approved Solution: Session-Based Memory**
- Anonymous session IDs for guest conversations (Zep-cloud)
- Cookie-based recognition for returning visitors ("Welcome back!")
- Progressive authentication pattern (browse freely → sign up for memory persistence)
- Session-to-account merge on signup (preserves conversation context)

**Conversion Funnel Strategy:**
```
Anonymous → Browse → Engage with Otto (Session) → [Motivation Point] → Sign Up
                ↓                    ↓                            ↓
           Value Demonstrated   Relationship Built    Memory Preserved
```

---

## 4. Implementation Handoff Plan

### 4.1 Code Changes (2 hours)

**File 1: `frontend/src/App.tsx`** (15 minutes)
```typescript
// BEFORE:
<Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />

// AFTER:
<Route path="/" element={<HomePage />} />
```

**File 2: `frontend/src/app/pages/HomePage.tsx`** (30 minutes)
```typescript
// Navigation component - lines 42-49
// BEFORE:
<span className="mr-4 text-sm text-gray-700">{user?.email}</span>
<button onClick={signOut}>Sign Out</button>

// AFTER:
{user ? (
  <>
    <span className="mr-4 text-sm text-gray-700">{user.email}</span>
    <button onClick={signOut} className="...">Sign Out</button>
  </>
) : (
  <a href="/login" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
    Sign In
  </a>
)}
```

**File 3: `frontend/src/app/components/ProtectedRoute.tsx`** (NO CHANGES)
- Keep component for future protected routes (favorites, profile)

**File 4: Session ID Service** (45 minutes)
```typescript
// frontend/src/services/sessionService.ts
export class SessionService {
  private static SESSION_COOKIE = 'otto_session_id';
  private static SESSION_EXPIRY = 30; // days

  static getSessionId(): string {
    let sessionId = getCookie(this.SESSION_COOKIE);

    if (!sessionId) {
      sessionId = crypto.randomUUID();
      setCookie(this.SESSION_COOKIE, sessionId, this.SESSION_EXPIRY);
    }

    return sessionId;
  }

  static async mergeSessionToAccount(userId: string): Promise<void> {
    const sessionId = this.getSessionId();
    await fetch('/api/auth/merge-session', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, user_id: userId })
    });
    deleteCookie(this.SESSION_COOKIE);
  }
}
```

**File 5: Zep Cloud Configuration** (30 minutes)
```python
# src/memory/zep_client.py - Add anonymous session support
class ZepClient:
    async def create_guest_session(self, session_id: str) -> str:
        """Create or retrieve Zep session for guest user"""
        session = await self.zep_client.session_get(session_id)
        if not session:
            session = await self.zep_client.session_create(
                session_id=session_id,
                user_id=f"guest:{session_id}",
                metadata={"is_guest": True}
            )
        return session.session_id

    async def merge_session_to_user(self, session_id: str, user_id: str):
        """Transfer guest session memory to user account"""
        # Get all memories from guest session
        memories = await self.zep_client.memory_get(session_id)

        # Create user session and transfer memories
        await self.zep_client.session_create(session_id=user_id, user_id=user_id)
        await self.zep_client.memory_add(user_id, memories.messages)

        # Mark guest session for cleanup
        await self.zep_client.session_update(session_id, metadata={"merged_to": user_id})
```

### 4.2 Documentation Updates (3 hours)

| Document | Changes | Time |
|----------|---------|------|
| `docs/prd.md` | Add "Access Control & Authentication Strategy" section | 30 min |
| `docs/prd.md` | Update FR16-FR23 with "Users (including guests)" | 15 min |
| `docs/architecture.md` | Add session-based memory architecture section | 30 min |
| `docs/ux-design-specification.md` | Add guest experience flows (Flow 5, 6) | 30 min |
| `docs/ux-design-specification.md` | Add GuestNav/AuthenticatedNav components | 30 min |
| `docs/epics.md` | Add guest ACs to Epic 2 stories (2-1 through 2-5) | 30 min |
| `docs/epics.md` | Add public access ACs to Epic 3 stories (3-1 through 3-4) | 15 min |
| `docs/epics.md` | Clarify auth scope in Epic 4 stories (4-1 through 4-9) | 30 min |

### 4.3 Verification Steps (1 hour)

**Test as Guest User (not logged in):**
1. ✅ Visit `http://localhost:5173/` → Should see vehicle grid (no login redirect)
2. ✅ Can search/filter vehicles
3. ✅ Can click vehicle cards to view detail modal
4. ✅ Can chat with Otto (session-based, no persistence)
5. ✅ Navigation shows "Sign In" button
6. ✅ Session ID cookie created
7. ✅ Returning visit shows "Welcome back!" message

**Test as Authenticated User:**
1. ✅ Sign in via `/login`
2. ✅ Homepage shows personalized features
3. ✅ Can save favorites
4. ✅ Navigation shows email + "Sign Out" button
5. ✅ Session memory merged to account on signup

**Test Progressive Authentication:**
1. ✅ Guest clicks favorite → Prompt: "Sign In to save favorites"
2. ✅ Guest clicks "Hold Vehicle" → Prompt: "Sign In to reserve vehicles"
3. ✅ Signup → Previous conversation context preserved
4. ✅ Session ID cookie cleared after merge

---

## 5. Detailed Change Proposals

### 5.1 PRD Edit Proposal

**File:** `docs/prd.md`
**Location:** After "Product Scope" section (approximately line 120)
**Action:** INSERT new section

```markdown
## Access Control & Authentication Strategy

### Public Access Features (No Authentication Required)

Otto.AI provides open access to core discovery features to maximize user engagement and SEO visibility:

**Available to All Visitors:**
- Homepage and vehicle browsing
- Natural language search and semantic discovery
- Vehicle detail views with photos, specifications, and pricing
- Otto AI conversational assistance with session-based memory
- Category browsing and curated collections
- Market data and vehicle comparisons

**Rationale:**
- **SEO Optimization:** Search crawlers index homepage and vehicle listings
- **Conversion Funnel:** Users experience value before authentication gate
- **Competitive Parity:** Industry standard (Carvana, Vroom, CarMax) is public browsing
- **Viral Discovery:** Users can share vehicle links without requiring recipient login

### Authenticated Features (Sign In Required)

Authentication enables persistent personalization and transactional capabilities:

**Available to Registered Users:**
- Save vehicles to favorites with price/drop notifications
- Conversation history and preference learning across sessions
- User profile with saved searches and preferences
- Hold/reserve vehicles with deposit processing
- Seller tools and lead management
- Cross-device synchronization

**Rationale:**
- **Value Exchange:** Users commit to account creation after experiencing value
- **Data Persistence:** Personalization requires persistent user identity
- **Transaction Security:** Reservations and seller tools need verified identity
- **Compliance:** User data access and GDPR rights require account linkage

### Progressive Authentication Pattern

**Step 1: Guest Discovery (No Account)**
- User arrives via organic search, referral, or direct navigation
- Browse vehicles, search, filter, view details
- Chat with Otto using anonymous session ID (UUID + cookie)
- Session stored in browser cookie (30-day expiry)

**Step 2: Engagement Point**
- User attempts gated action (favorite, hold vehicle, save history)
- System prompts: "Sign In to save favorites" (not required to continue browsing)
- Clear value proposition: "Create an account to save your preferences and pick up where you left off"

**Step 3: Account Creation**
- User completes signup (email/password or social auth)
- **Critical:** Anonymous session memory merged to user account
- Zep-cloud session transferred from session_id to user_id
- Previous conversation context preserved and accessible

**Step 4: Return Visit Recognition**
- Cookie detection: `otto_session_id` present
- Retrieve last session: "Welcome back! Last time you were looking at family SUVs under $30k"
- Seamless continuation: Otto remembers preferences without requiring login

**Step 5: Authenticated Experience**
- All features available
- Cross-device sync
- Persistent memory across sessions
- Conversation history accessible
```

### 5.2 Epic 2 Story AC Additions

**File:** `docs/epics.md`
**Location:** Each Epic 2 story (2-1 through 2-5)
**Action:** ADD acceptance criteria for guest users

**Example for Story 2.1:**
```gherkin
### Story 2.1: Initialize Conversational AI Infrastructure

# NEW AC for Guest Users:

Given I'm a guest user on the homepage
When I start chatting with Otto AI for the first time
Then the system generates an anonymous session ID (UUID v4)
And stores the session ID in an HTTP-only cookie (otto_session_id, 30-day expiry)
And the WebSocket connection uses `/ws/conversation/session/{session_id}` endpoint
And Otto responds with "Welcome! I'm Otto, your AI car shopping assistant. How can I help you today?"
And the conversation is stored in Zep Cloud keyed by session_id
And no authentication is required

Given I'm a returning guest with existing otto_session_id cookie
When I start a new conversation
Then Otto greets me with context from my previous session
And the existing session_id is reused (not regenerated)
And conversation history is preserved from previous visits
```

### 5.3 Epic 3 Story AC Additions

**File:** `docs/epics.md`
**Location:** Each Epic 3 story (3-1 through 3-4)
**Action:** ADD acceptance criteria for public access

**Example for Story 3.2:**
```gherkin
### Story 3.2: Build Responsive Vehicle Grid Component

# NEW AC for Guest Browsing:

Given I'm a guest user (not logged in)
When I visit the homepage
Then I see vehicles displayed in an attractive grid without any authentication prompt
And I can browse, filter, and search vehicles
And vehicle cards show all information (image, make/model, price, specs)
And the navigation bar shows a "Sign In" button
And no login redirect occurs

Given I'm a guest user viewing vehicles
When I click on a vehicle card
Then the vehicle detail modal opens with full information
And I can view photos, specifications, and pricing
And I can chat with Otto about this vehicle
And I am NOT prompted to login until I attempt a gated action (favorite, reserve)
```

### 5.4 Architecture Section Addition

**File:** `docs/architecture.md`
**Location:** After "Zep Cloud" section (approximately line 113)
**Action:** INSERT new architecture section

```markdown
### Session-Based Memory for Guest Users

Otto.AI implements progressive authentication with session-based memory for anonymous users, enabling relationship building without requiring immediate account creation.

**Anonymous Session Architecture:**

```python
# Session ID Generation
class SessionManager:
    def generate_session_id() -> str:
        """Generate UUID v4 for anonymous session"""
        return uuid.uuid4()

    def create_session_cookie(session_id: str):
        """Set HTTP-only cookie with 30-day expiry"""
        return SetCookie(
            name="otto_session_id",
            value=session_id,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            secure=True,  # HTTPS only
            samesite="lax"  # CSRF protection
        )
```

**Zep Cloud Session Strategy:**

```python
# Guest session in Zep Cloud
guest_session = {
    "session_id": "uuid-v4-here",
    "user_id": "guest:uuid-v4-here",  # Prefix for guest sessions
    "metadata": {
        "is_guest": True,
        "created_at": "2025-01-12T10:00:00Z",
        "last_seen": "2025-01-12T14:30:00Z"
    }
}

# Authenticated user session in Zep Cloud
user_session = {
    "session_id": "user@email.com",
    "user_id": "auth0|user-id-here",
    "metadata": {
        "is_guest": False,
        "merged_from_guest_session": "uuid-v4-here",  # Session merge history
        "created_at": "2025-01-12T15:00:00Z"
    }
}
```

**Session-to-Account Merge Flow:**

```python
async def merge_guest_session_to_account(
    session_id: str,
    user_id: str
) -> MergeResult:
    """
    Transfer guest session memory to authenticated user account.

    Preserves conversation context, preferences, and vehicle interactions
    from anonymous session to persistent user account.
    """

    # 1. Retrieve guest session from Zep Cloud
    guest_session = await zep_client.session_get(session_id)
    guest_memories = await zep_client.memory_get(session_id)

    # 2. Create or update user session
    await zep_client.session_create(
        session_id=user_id,
        user_id=user_id,
        metadata={
            "merged_from_guest_session": session_id,
            "merge_timestamp": datetime.utcnow().isoformat()
        }
    )

    # 3. Transfer memories to user account
    await zep_client.memory_add(
        session_id=user_id,
        messages=guest_memories.messages
    )

    # 4. Update conversation ownership in database
    await update_conversation_ownership(
        old_session_id=session_id,
        new_user_id=user_id
    )

    # 5. Mark guest session for cleanup (async)
    await zep_client.session_update(
        session_id=session_id,
        metadata={"status": "merged", "merged_to": user_id}
    )

    # 6. Clear session cookie
    response.delete_cookie("otto_session_id")

    return MergeResult(
        success=True,
        messages_transferred=len(guest_memories.messages),
        preferences_preserved=extract_preferences(guest_memories)
    )
```

**Cookie-Based Recognition:**

```typescript
// Frontend: Check for returning guest
const sessionId = getCookie('otto_session_id');

if (sessionId) {
  // Retrieve last session data
  const lastSession = await fetch(`/api/session/${sessionId}`)
    .then(res => res.json());

  // Personalized greeting
  const ottoGreeting = lastSession.previousPreferences
    ? `Welcome back! Last time you were looking at ${lastSession.previousPreferences.join(', ')}`
    : `Welcome back! Ready to continue your car search?`;

  // Extend session expiry (sliding window)
  setCookie('otto_session_id', sessionId, {
    maxAge: 30 * 24 * 60 * 60  // Reset 30-day timer
  });
} else {
  // New guest - generate session ID
  const newSessionId = crypto.randomUUID();
  setCookie('otto_session_id', newSessionId, {
    maxAge: 30 * 24 * 60 * 60
  });
}
```

**Optional Authentication Middleware:**

```python
# Backend: Bypass JWT verification for public routes
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class OptionalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Attempt to extract and verify JWT token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                request.state.user_id = payload.get("user_id")
                request.state.is_authenticated = True
            except JWTError:
                # Invalid token - treat as unauthenticated
                request.state.is_authenticated = False
        else:
            # No token provided
            request.state.is_authenticated = False

        # Check for guest session cookie
        session_id = request.cookies.get("otto_session_id")
        if session_id:
            request.state.session_id = session_id

        # Always proceed - authentication is optional
        response = await call_next(request)
        return response
```

**API Endpoint Changes:**

```python
# WebSocket endpoint - support both user_id and session_id
@router.websocket("/ws/conversation/{identifier}")
async def conversation_websocket(
    websocket: WebSocket,
    identifier: str,  # Can be user_id or session_id
    auth_required: bool = False
):
    await websocket.accept()

    # Determine if identifier is user_id or session_id
    if identifier.startswith("guest:") or len(identifier.split("-")) == 5:  # UUID format
        # Guest session
        session_id = identifier
        user_id = f"guest:{session_id}"
        is_authenticated = False
    else:
        # Authenticated user
        user_id = identifier
        session_id = None
        is_authenticated = True

    # Initialize Zep Cloud session
    await zep_client.get_or_create_session(session_id or user_id, user_id)

    # Handle WebSocket messages
    try:
        while True:
            message = await websocket.receive_text()
            response = await process_conversation(
                message=message,
                session_id=session_id or user_id,
                user_id=user_id,
                is_authenticated=is_authenticated
            )
            await websocket.send_json(response)
    finally:
        await websocket.close()
```
```

---

## 6. Approval and Routing

### 6.1 Change Scope Classification

**Scope:** MODERATE
- Requires backlog reorganization (AC updates)
- Requires documentation updates (4 artifacts)
- Requires targeted code changes (5 files)
- NO sprint resequencing
- NO story invalidation

### 6.2 Stakeholder Approval Required

| Role | Name | Approval | Date |
|------|------|----------|------|
| **Product Owner** | BMad | ⏳ Pending | |
| **Scrum Master** | | ⏳ Pending | |
| **Tech Lead** | | ⏳ Pending | |
| **UX Designer** | | ⏳ Pending | |

### 6.3 Implementation Assignment

| Task | Owner | Estimated Time | Dependencies |
|------|-------|----------------|--------------|
| Remove ProtectedRoute wrapper | Frontend Dev | 15 min | Approval |
| Update navigation component | Frontend Dev | 30 min | Approval |
| Session ID service | Frontend Dev | 45 min | Approval |
| Zep Cloud guest support | Backend Dev | 1 hour | Approval |
| PRD updates | PM/BA | 30 min | Approval |
| Story AC updates | PM/BA | 1 hour | Approval |
| Architecture documentation | Architect | 1 hour | Approval |
| UX flow documentation | UX Designer | 30 min | Approval |
| Verification testing | QA | 1 hour | Implementation complete |

**Total Implementation Time:** ~8 hours (1 business day with parallel work)

---

## 7. Success Criteria

### 7.1 Functional Requirements

✅ **Public Access Validated:**
- [ ] Homepage accessible without authentication (no redirect to `/login`)
- [ ] Vehicle grid loads and displays vehicles for guests
- [ ] Search and filter functionality works for guests
- [ ] Vehicle detail modal opens and displays full information
- [ ] Otto AI chat works for guests (session-based)
- [ ] Navigation shows "Sign In" button for guests

✅ **Session-Based Memory Working:**
- [ ] Anonymous session ID generated on first visit
- [ ] Session ID stored in HTTP-only cookie (30-day expiry)
- [ ] Zep Cloud stores guest conversations keyed by session_id
- [ ] Returning guests recognized with "Welcome back!" message
- [ ] Otto references previous session context

✅ **Progressive Authentication:**
- [ ] Favorite button prompts "Sign In to save" for guests
- [ ] "Hold Vehicle" button prompts "Sign In to reserve" for guests
- [ ] Signup process merges session memory to user account
- [ ] Previous conversation context accessible after signup
- [ ] Session ID cookie cleared after successful merge

✅ **Authenticated Experience Unchanged:**
- [ ] Signed-in users see email in navigation
- [ ] Favorites work without prompts
- [ ] Conversation history accessible
- [ ] All existing functionality preserved

### 7.2 Non-Functional Requirements

✅ **Performance:**
- [ ] Homepage load time < 2 seconds (no regression)
- [ ] Session ID generation < 50ms
- [ ] Zep Cloud session lookup < 200ms

✅ **Security:**
- [ ] Session IDs are UUID v4 (cryptographically random)
- [ ] Session cookies are HTTP-only and Secure flag set
- [ ] Session-to-account merge requires valid authentication
- [ ] Guest sessions expire after 30 days of inactivity

✅ **SEO:**
- [ ] Homepage is crawlable by search bots (no authentication gate)
- [ ] Vehicle listing pages are indexed
- [ ] Meta tags and structured data accessible

✅ **Accessibility:**
- [ ] "Sign In" button meets WCAG AA contrast requirements
- [ ] Guest experience works with screen readers
- [ ] Keyboard navigation functional for all guest features

---

## 8. Risk Mitigation

### 8.1 Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Session merge bugs** | Medium | Medium | Comprehensive testing of merge flow, rollback plan prepared |
| **Cookie blocking** | Low | Low | Fallback to localStorage, graceful degradation |
| **Zep Cloud rate limits** | Low | Medium | Implement request batching, error handling |
| **SEO indexing issues** | Low | High | Verify with Google Search Console, test crawl bots |
| **User confusion** | Low | Low | Clear CTAs, help text, progressive disclosure |

### 8.2 Rollback Plan

If critical issues discovered after implementation:

1. **Immediate Rollback (5 minutes):**
   - Revert `App.tsx` to add `<ProtectedRoute>` wrapper back
   - Deploy previous version

2. **Data Preservation:**
   - Guest session data preserved in Zep Cloud
   - No user data lost (guest sessions only)

3. **Communication:**
   - Notify users of temporary maintenance
   - Document issue and fix timeline

### 8.3 Monitoring Plan

Post-implementation metrics to track:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Homepage conversion** | Increase > 20% | Guests who sign up after browsing |
| **Time to first chat** | < 30 seconds | Guest engagement speed |
| **Session merge success** | > 98% | Successful account creation with memory transfer |
| **SEO impressions** | Increase > 30% | Google Search Console |
| **Bounce rate** | Decrease > 15% | Analytics comparison |

---

## 9. Appendix: Related Documents

### 9.1 Referenced Artifacts

- `frontend/src/App.tsx` - Route configuration with ProtectedRoute wrapper
- `frontend/src/app/contexts/AuthContext.tsx` - Authentication state management
- `frontend/src/app/components/ProtectedRoute.tsx` - Route guard component
- `frontend/src/app/pages/HomePage.tsx` - Homepage navigation component
- `docs/prd.md` - Product Requirements Document
- `docs/architecture.md` - System architecture documentation
- `docs/ux-design-specification.md` - UX patterns and design system
- `docs/epics.md` - Epic and story breakdown
- `docs/sprint-artifacts/sprint-status.yaml` - Story tracking

### 9.2 Supporting Analysis

- Conversation summary with user insight on Zep-cloud personalization strategy
- SEO strategy requirements in PRD (lines 289-295)
- Industry competitive analysis (Carvana, Vroom, CarMax)
- Zep Cloud documentation for anonymous sessions

---

## 10. Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-12 | 1.0 | Initial sprint change proposal | Claude (BMad Workflow) |

---

**Next Steps:**

1. ✅ Review and approve proposal
2. ✅ Assign implementation tasks
3. ✅ Execute code changes (Phase 1)
4. ✅ Implement session infrastructure (Phase 2)
5. ✅ Update documentation (Phase 3)
6. ✅ Verify and test (Phase 4)
7. ✅ Deploy to production
8. ✅ Monitor metrics and optimization

---

**Prepared by:** BMad Method - Correct Course Workflow
**Date:** 2025-01-12
**Workflow Version:** 4-implementation/correct-course

