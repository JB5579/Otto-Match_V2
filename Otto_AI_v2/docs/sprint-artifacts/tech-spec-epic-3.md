# Epic Technical Specification: Dynamic Vehicle Grid Interface

Date: 2026-01-03
Author: BMad
Epic ID: 3
Status: Contexted (Supabase Auth Integration Complete)

---

## Overview

Epic 3 delivers the primary user interface for Otto.AI's vehicle discovery experience - a dynamic, real-time responsive web application that transforms traditional car shopping into conversational discovery. This epic implements the frontend infrastructure and components necessary to display vehicles in an intelligent grid that updates seamlessly based on Otto AI conversation context.

The epic builds upon the solid backend foundation established in Epic 1 (Semantic Vehicle Intelligence) and Epic 2 (Conversational Discovery Interface), creating the visual layer through which users interact with Otto's recommendations. As of 2026-01-02, zero frontend code exists in the codebase - this epic represents the complete frontend implementation from scratch.

**Current State:**
- Backend semantic search fully operational (Epic 1: 12/12 stories complete)
- Conversational AI infrastructure implemented (Epic 2: 6/10 stories complete)
- Zero React/TypeScript components exist
- All 13 stories in backlog status
- Supabase database + pgvector already configured (used in Epic 1)

**Target State:**
- Modern React 18+ frontend with TypeScript for type safety
- **Supabase Authentication** for secure user login/signup with JWT sessions
- Real-time vehicle grid with cascade animations
- Glass-morphism design system matching PRD specifications
- Responsive layout (desktop/tablet/mobile)
- Integration with existing FastAPI backend
- Row Level Security (RLS) for buyer/seller data isolation
- WCAG 2.1 AA accessibility compliance

## Objectives and Scope

### Primary Objectives

**O1: Establish Frontend Infrastructure with Supabase Auth (Story 3-1)**
Create the foundational React 18+ application structure with TypeScript, build tooling (Vite), and development environment. This includes:
- Project scaffolding with `@supabase/supabase-js` client library
- **Supabase Authentication setup** with email/password and social login (Google, GitHub)
- AuthContext with `useAuth()` hook for session management
- Login and registration UI components
- Linting configuration (ESLint, Prettier)
- Integration with existing FastAPI backend
- Row Level Security (RLS) policies for user data isolation

**O2: Build Vehicle Grid Component System (Stories 3-2, 3-3, 3-7)**
Implement responsive vehicle grid with dynamic cascade updates, filtering, and sorting capabilities. The grid must react in real-time to Otto AI conversation context, displaying vehicles with animated transitions as user preferences evolve.

**O3: Implement Vehicle Detail Experience (Story 3-4, 3-12)**
Create comprehensive vehicle detail modal with image carousel, specifications, pricing, Otto's personalized recommendation, and reservation CTA. Preserves grid visibility through blur overlay effect.

**O4: Real-Time Features & Social Proof (Story 3-5)**
Display vehicle availability status, current viewer counts, and reservation indicators. Integrates with WebSocket infrastructure for live updates.

**O5: Comparison & Analytics Tools (Stories 3-6, 3-9)**
Enable side-by-side vehicle comparison with feature-by-feature analysis. Implement user behavior tracking for analytics and optimization.

**O6: Performance & Caching (Story 3-8)**
Optimize rendering performance with edge caching, lazy loading, and efficient state management. Target <2s Time to Interactive.

**O7: Glass-Morphism Design System (Story 3-10)**
Build reusable component library implementing Otto.AI's distinctive layered glass aesthetic with proper backdrop blur, transparency, and shadow treatments.

**O8: Match Score Visualization (Story 3-11)**
Create animated match percentage badges with color coding (90%+ green, 80-89% lime, 70-79% yellow, <70% orange) and subtle pulsing for 95%+ scores.

**O9: Otto AI Chat Integration (Story 3-13)**
Implement floating chat widget with expandable conversation interface, Otto avatar with breathing animation, and seamless integration with conversation backend.

### In Scope

- ✅ React 18+ with TypeScript and Vite build system
- ✅ **Supabase Authentication** (`@supabase/supabase-js`) with email/password and social login
- ✅ **AuthContext with `useAuth()` hook** for session management
- ✅ **Login/Signup UI components** with glass-morphism styling
- ✅ **JWT token management** for secure API communication
- ✅ **Row Level Security (RLS)** for buyer/seller data isolation
- ✅ Tailwind CSS + Radix UI primitives for accessible components
- ✅ Framer Motion for cascade animations and micro-interactions
- ✅ Glass-morphism design tokens and component variants
- ✅ Responsive breakpoints (mobile: 375px, tablet: 768px, desktop: 1024px, wide: 1440px)
- ✅ Integration with existing FastAPI backend endpoints
- ✅ WebSocket connection for real-time updates
- ✅ WCAG 2.1 AA compliance (screen reader, keyboard nav, high contrast)
- ✅ Component testing with React Testing Library
- ✅ E2E testing with Playwright

### Out of Scope

- ❌ Seller dashboard interface (Epic 6)
- ❌ Payment processing UI (Epic 5)
- ❌ Native mobile applications (iOS/Android)
- ❌ PWA offline capabilities (post-MVP)
- ❌ Advanced personalization dashboards
- ❌ Multi-language support
- ❌ Video vehicle tours integration
- ❌ Advanced auth features (MFA, SSO, identity linking) - post-MVP

### Technical Boundaries

- **Framework:** React 18+ (no Next.js SSR for MVP - pure client-side SPA)
- **State Management:** React Context + hooks (Redux not required for MVP scope)
- **Styling:** Tailwind CSS utility-first (no CSS-in-JS libraries)
- **Component Library:** Custom implementation using Radix UI primitives (no MUI/Chakra)
- **Animation:** Framer Motion only (no GSAP or animation.css)
- **API Communication:** Fetch API + WebSocket (no GraphQL)
- **Testing:** Vitest + React Testing Library (no Jest migration needed)

### Dependencies

**Critical Path Dependencies:**
- Must complete Epic 1 (Semantic Search) - backend APIs ready ✅
- Must complete Epic 2 Stories 2-1 through 2-5 - conversation infrastructure ready ✅
- **Supabase project already configured** - Database URL and anon key available ✅
- Epic 5 (Reservations) required for reservation CTA functionality (can mock for MVP)

**Authentication Integration:**
- **No Epic 4 dependency:** Supabase Auth eliminates need for custom authentication
- **JWT validation:** FastAPI backend will validate Supabase JWT tokens from frontend
- **RLS policies:** Enable Row Level Security for user favorites, profiles, and collections

## System Architecture Alignment

### Connection to Backend Services

**Semantic Search Integration (Epic 1)**
The frontend grid consumes the semantic search API at `/api/search/semantic` implemented in `src/api/semantic_search_api.py`. This endpoint returns vehicle data with match scores calculated via RAG-Anything embeddings and pgvector similarity search.

**Conversation Context Integration (Epic 2)**
Real-time grid updates consume WebSocket messages from `src/api/websocket_endpoints.py`. The frontend maintains WebSocket connection to receive preference changes that trigger grid re-sorting and filtering.

**API Contract Alignment**
All existing FastAPI endpoints defined in `src/api/` remain unchanged. Frontend implements client-side REST consumers for:
- Vehicle listings: `GET /api/listings`
- Semantic search: `POST /api/search/semantic`
- Vehicle comparison: `POST /api/compare`
- Favorites: `POST /api/favorites/{vehicle_id}`
- Collections: `GET /api/collections/trending`

### Architecture Decision Compliance

**ADR-002: Semantic Search Architecture** ✅
Frontend displays vehicles ranked by semantic similarity scores. No changes to RAG-Anything + pgvector backend architecture.

**ADR-003: Real-time Communication** ✅
Frontend WebSocket client integrates with existing `FavoritesWebSocketService` and `CollectionsWebSocketService` in `src/realtime/`.

**ADR-005: Modular Python Architecture** ✅
Frontend mirrors backend modular structure with atomic design pattern (atoms → molecules → organisms → templates).

### Data Flow Architecture

```
User → Otto Chat Widget → WebSocket → FastAPI → Zep Cloud → Groq LLM
                                              ↓
                                         Semantic Search
                                              ↓
                                      Vehicle Grid Updates
                                              ↓
                                          User View
```

**Cascade Update Flow:**
1. User expresses preference in Otto conversation
2. Backend extracts entities via `advisory_extractors.py`
3. New search query executed via `search_orchestrator.py`
4. Updated vehicle list with new match scores sent via WebSocket
5. Frontend receives update → triggers cascade animation
6. Vehicles re-sorted with smooth transitions (Framer Motion)

## Detailed Design

### Services and Modules

**Frontend Module Structure:**

```
src/frontend/
├── app/
│   ├── main.tsx                 # Application entry point
│   ├── App.tsx                  # Root component with routing
│   ├── styles/globals.css       # Global styles and Tailwind directives
│   ├── lib/api.ts               # API client (fetch + WebSocket wrapper)
│   └── lib/supabaseClient.ts   # Supabase client (auth + database)
├── components/
│   ├── auth/                    # Authentication components
│   │   ├── AuthProvider.tsx     # Supabase Auth context provider
│   │   ├── LoginForm.tsx        # Email/password login form
│   │   ├── SignUpForm.tsx      # Registration form
│   │   ├── ProtectedRoute.tsx   # Route wrapper for authenticated users
│   │   ├── SocialLoginButtons.tsx # Google, GitHub login buttons
│   │   └── PasswordReset.tsx    # Password reset flow
│   ├── vehicle-grid/            # Vehicle grid display
│   │   ├── VehicleGrid.tsx
│   │   ├── VehicleCard.tsx
│   │   ├── GridFilters.tsx
│   │   └── useVehicleCascade.ts # Custom hook for cascade updates
│   ├── vehicle-detail/          # Vehicle detail modal
│   │   ├── VehicleDetailModal.tsx
│   │   ├── ImageCarousel.tsx
│   │   ├── VehicleSpecs.tsx
│   │   └── OttoRecommendation.tsx
│   ├── otto-chat/               # Otto AI chat widget
│   │   ├── OttoChatWidget.tsx
│   │   ├── ChatMessageList.tsx
│   │   ├── ChatInput.tsx
│   │   ├── OttoAvatar.tsx
│   │   └── useOttoConversation.ts
│   ├── comparison/               # Vehicle comparison
│   │   ├── ComparisonView.tsx
│   │   ├── ComparisonTable.tsx
│   │   └── useComparison.ts
│   ├── design-system/           # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Badge.tsx
│   │   ├── MatchScoreBadge.tsx
│   │   ├── FilterPill.tsx
│   │   └── glass-variants.ts    # Glass-morphism style utilities
│   └── shared/                  # Shared utilities
│       ├── LoadingState.tsx
│       ├── ErrorState.tsx
│       └── EmptyState.tsx
├── hooks/
│   ├── useWebSocket.ts          # WebSocket connection management
│   ├── useVehicleSearch.ts      # Semantic search hook
│   ├── useFavorites.ts          # Favorites management
│   ├── useAnalytics.ts          # Analytics tracking
│   └── useAuth.ts              # Supabase Auth hook (from AuthProvider)
├── context/
│   ├── VehicleContext.tsx       # Global vehicle state
│   ├── ConversationContext.tsx  # Otto conversation state
│   └── AuthContext.tsx          # User authentication (Supabase-based)
├── types/
│   ├── vehicle.ts               # Vehicle type definitions
│   ├── conversation.ts          # Conversation message types
│   ├── api.ts                   # API response types
│   └── auth.ts                 # Supabase Auth type definitions
└── utils/
    ├── animations.ts            # Framer Motion animation presets
    ├── formatters.ts            # Price, mileage, date formatting
    └── validators.ts            # Input validation helpers
```

**Component Responsibilities:**

| Component | Responsibility | Inputs | Outputs |
|-----------|---------------|--------|---------|
| **AuthProvider** | Supabase Auth context with session management | children | user, session, signIn, signUp, signOut |
| **LoginForm** | Email/password authentication UI | onLogin | - |
| **SocialLoginButtons** | Google/GitHub OAuth login buttons | onSocialLogin | - |
| **ProtectedRoute** | Route wrapper requiring authentication | children | Redirects to login if unauthenticated |
| **VehicleGrid** | Render responsive grid with cascade animations | vehicles[], filters, sort | onSelect, onFavorite |
| **VehicleCard** | Single vehicle display with match badge | vehicle, matchScore, animationDelay | onSelect, onFavorite |
| **MatchScoreBadge** | Animated circular percentage badge | score, size, showPulse | - |
| **OttoChatWidget** | Floating expandable chat interface | initialExpanded | onVehicleSelect |
| **VehicleDetailModal** | Comprehensive vehicle info overlay | vehicle, matchScore, isOpen | onClose, onReserve |
| **ImageCarousel** | Multi-image gallery with thumbnails | images[], videos[] | - |
| **ComparisonView** | Side-by-side vehicle comparison | vehicles[] | onClose |

### Data Models and Contracts

**Frontend Vehicle Type (mirrors Pydantic `VehicleData`):**

```typescript
// src/types/vehicle.ts
export interface Vehicle {
  id: string;
  vin: string;
  make: string;
  model: string;
  year: number;
  trim?: string;
  mileage: number;
  price: number;
  originalPrice?: number;
  savings?: number;
  description: string;
  features: string[];
  images: VehicleImage[];
  specifications: Record<string, unknown>;
  matchScore?: number;          // Calculated by backend
  availabilityStatus: 'available' | 'reserved' | 'sold';
  currentViewers?: number;      // Real-time social proof
  reservationExpiry?: string;   // ISO timestamp
  ottoRecommendation?: string;  // Personalized message from Otto
}

export interface VehicleImage {
  url: string;
  description: string;
  category: 'hero' | 'carousel' | 'detail';
  altText: string;
}

export interface SearchFilters {
  make?: string;
  model?: string;
  priceRange?: [number, number];
  yearRange?: [number, number];
  mileageMax?: number;
  features?: string[];
  location?: string;
}

export interface SearchResponse {
  vehicles: Vehicle[];
  totalCount: number;
  processingTime: number;  // milliseconds
}
```

**Authentication Types (Supabase-based):**

```typescript
// src/types/auth.ts
import { User, Session } from '@supabase/supabase-js';

export interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignUpData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface SocialLoginProvider {
  provider: 'google' | 'github';
}

export interface PasswordResetRequest {
  email: string;
}

export interface UserProfile {
  id: string;  // Supabase auth.uid()
  email: string;
  firstName: string;
  lastName: string;
  avatarUrl?: string;
  createdAt: string;
  updatedAt: string;
}
```

**Conversation Message Types (mirrors Epic 2):**

```typescript
// src/types/conversation.ts
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  vehicleSuggestions?: string[];  // Vehicle IDs referenced
  metadata?: Record<string, unknown>;
}

export interface ConversationState {
  messages: ChatMessage[];
  isTyping: boolean;
  connected: boolean;
  userPreferences: UserPreferenceProfile;
}

export interface WebSocketUpdate {
  type: 'vehicle_update' | 'preference_change' | 'new_search';
  vehicles: Vehicle[];
  timestamp: string;
}
```

### APIs and Interfaces

**Supabase Client Setup:**

```typescript
// src/app/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Helper to get authenticated user's JWT token for backend API calls
export async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

// Auth state change listener for session management
export function onAuthStateChange(callback: (event: string, session: any) => void) {
  return supabase.auth.onAuthStateChange(callback);
}
```

**AuthContext Implementation:**

```typescript
// src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase, onAuthStateChange } from '@/app/lib/supabaseClient';
import { LoginCredentials, SignUpData, SocialLoginProvider } from '@/types/auth';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (credentials: LoginCredentials) => Promise<{ error: AuthError | null }>;
  signUp: (data: SignUpData) => Promise<{ error: AuthError | null }>;
  signInWithSocial: (provider: SocialLoginProvider) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = onAuthStateChange((event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async ({ email, password }: LoginCredentials) => {
    return await supabase.auth.signInWithPassword({ email, password });
  };

  const signUp = async ({ email, password, firstName, lastName }: SignUpData) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { firstName, lastName }
      }
    });
    return { error };
  };

  const signInWithSocial = async ({ provider }: SocialLoginProvider) => {
    return await supabase.auth.signInWithOAuth({ provider });
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signInWithSocial, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

**REST API Clients (with JWT authentication):**

```typescript
// src/app/lib/api.ts
import { Vehicle, SearchFilters, SearchResponse } from '@/types/vehicle';
import { getAuthToken } from './supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Helper to include JWT token in API requests
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export class VehicleAPIClient {
  async searchVehicles(
    query: string,
    filters?: SearchFilters
  ): Promise<SearchResponse> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/api/search/semantic`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ query, filters }),
    });
    if (!response.ok) throw new Error('Search failed');
    return response.json();
  }

  async getVehicle(vehicleId: string): Promise<Vehicle> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/api/vehicles/${vehicleId}`, {
      headers,
    });
    if (!response.ok) throw new Error('Vehicle not found');
    return response.json();
  }

  async compareVehicles(vehicleIds: string[]): Promise<ComparisonResult> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE}/api/compare`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ vehicle_ids: vehicleIds }),
    });
    return response.json();
  }

  async toggleFavorite(vehicleId: string): Promise<void> {
    const headers = await getAuthHeaders();
    await fetch(`${API_BASE}/api/favorites/${vehicleId}`, {
      method: 'POST',
      headers,
    });
  }
}
```

**WebSocket Client:**

```typescript
// src/hooks/useWebSocket.ts
export function useWebSocket(vehicleUpdateCallback: (vehicles: Vehicle[]) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/vehicles`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const update: WebSocketUpdate = JSON.parse(event.data);
      if (update.type === 'vehicle_update') {
        vehicleUpdateCallback(update.vehicles);
      }
    };

    return () => ws.close();
  }, []);

  return { connected };
}
```

### Workflows and Sequencing

**Workflow 0: Authentication Flow (Supabase)**

```
1. User navigates to app.otto.ai
2. React app mounts (App.tsx) wrapped with AuthProvider
3. AuthContext initializes and checks Supabase session:
   - If valid session exists → user auto-signed in
   - If no session → show login/signup options
4. User authentication paths:
   a) Email/Password Login:
      - User enters email + password in LoginForm
      - AuthContext.signIn() calls supabase.auth.signInWithPassword()
      - On success: session stored in Supabase, user redirected to discovery page
      - On failure: error message displayed
   b) Social Login (Google/GitHub):
      - User clicks "Continue with Google" button
      - AuthContext.signInWithSocial() triggers OAuth popup
      - User grants permissions on provider's site
      - Redirect back with OAuth token → Supabase creates session
      - User redirected to discovery page
   c) Sign Up:
      - User fills registration form (email, password, name)
      - AuthContext.signUp() calls supabase.auth.signUp()
      - Supabase sends email verification (if enabled)
      - User confirms email → session created
5. Authenticated user state:
   - JWT token stored in Supabase client (handled automatically)
   - All API calls include Authorization: Bearer <token> header
   - FastAPI backend validates JWT token via Supabase
   - RLS policies enforce user data isolation (favorites, profiles)
6. Session persistence:
   - Supabase maintains session across page refreshes
   - AuthContext listens to auth state changes
   - On signOut: session cleared, user redirected to login
```

**Workflow 1: Initial Page Load**

```
1. User navigates to app.otto.ai
2. React app mounts (App.tsx)
3. AuthContext initializes (checks Supabase session)
4. If authenticated → proceed to step 5
5. If not authenticated → show login/signup page
6. VehicleContext loads initial vehicles via VehicleAPIClient.searchVehicles("")
7. WebSocket connection established for real-time updates
8. VehicleGrid renders with skeleton loading state
9. API responds → VehicleGrid renders with cascade animation
10. OttoChatWidget initializes in collapsed state
```

**Workflow 2: Otto Conversation → Grid Cascade**

```
1. User types message in OttoChatWidget
2. ChatInput sends message via WebSocket to backend
3. Backend processes via conversation_agent.py
4. NLU extracts preferences (advisory_extractors.py)
5. New search executed (search_orchestrator.py)
6. Backend sends WebSocket message with updated vehicles
7. Frontend useWebSocket hook receives message
8. VehicleContext updates vehicles state
9. VehicleGrid detects vehicle array change
10. Framer Motion AnimatePresence triggers:
    - Exiting vehicles: fade out + scale down (0.2s)
    - New vehicles: fade in + slide up with stagger (0.05s delay per card)
    - Match score updates: number transition (0.3s)
```

**Workflow 3: Vehicle Selection → Detail Modal**

```
1. User clicks VehicleCard
2. VehicleGrid calls onSelect(vehicle)
3. Parent component opens VehicleDetailModal
4. Modal renders with:
    - Backdrop blur overlay (preserves grid visibility)
    - ImageCarousel loads images lazily
    - OttoRecommendation fetches personalized message
    - SocialProofBadges show current viewers (WebSocket)
5. User clicks "Request to Hold This Vehicle"
6. Check authentication status via useAuth():
   - If authenticated (user exists) → call reservation API (Epic 5)
   - If not authenticated → redirect to login page with return URL
7. After successful login → return to detail modal and complete reservation
```

**Workflow 4: Vehicle Comparison**

```
1. User clicks "Add to Compare" on VehicleCard (2-3 vehicles)
2. ComparisonContext adds vehicles to comparison list
3. ComparisonFab appears with count badge
4. User clicks fab → ComparisonView opens as modal
5. ComparisonTable renders feature-by-feature matrix:
    - Rows: Price, Mileage, Range, Acceleration, Features
    - Columns: Selected vehicles
    - Highlight best values in green
6. OttoRecommendation shows: "Based on your need for [lifestyle], I recommend [vehicle]"
```

## Non-Functional Requirements

### Performance

**Page Load Targets (from PRD NFRs):**
- First Contentful Paint (FCP): <1.5s
- Largest Contentful Paint (LCP): <2.5s
- Time to Interactive (TTI): <3s
- Cumulative Layout Shift (CLS): <0.1
- First Input Delay (FID): <100ms

**Runtime Performance:**
- Grid cascade animation: 60fps with <16ms frame time
- WebSocket message processing: <100ms latency
- Vehicle card hover effects: <200ms transition
- Image lazy loading: Intersection Observer API
- Search response display: <500ms from API response to render

**Optimization Strategies:**
- Code splitting with React.lazy() for heavy components (VehicleDetailModal, ComparisonView)
- Image optimization: WebP format with responsive srcset, lazy loading
- Virtual scrolling for grid with >50 vehicles (react-window)
- Memoization: React.memo for VehicleCard, useMemo for expensive computations
- Service Worker for asset caching (post-MVP)

**Bundle Size Budgets:**
- Initial JS bundle: <200KB gzipped
- Per-route chunk: <100KB gzipped
- Total CSS: <50KB gzipped (Tailwind purge)
- Framer Motion: <80KB gzipped

### Security

**Authentication Security (Supabase):**
- JWT tokens managed by Supabase client (automatic storage in browser)
- Token refresh handled automatically by Supabase SDK
- Social login via OAuth 2.0 (Google, GitHub) with secure token exchange
- Email verification required for new user registrations (configurable)
- Row Level Security (RLS) policies enforce data isolation at database level
- Password reset flow via Supabase Auth (time-limited reset tokens)

**Client-Side Security:**
- Content Security Policy (CSP) header restricting script sources
- XSS prevention: React's built-in escaping, no dangerouslySetInnerHTML
- HTTPS-only communication (no mixed content)
- Secure WebSocket (wss://) protocol
- Environment variable protection (Vite env prefix: VITE_SUPABASE_*)
- No sensitive data in localStorage/sessionStorage (Supabase handles auth state)

**API Security:**
- JWT validation in FastAPI backend via Supabase
- Authorization: Bearer <token> header in all API requests
- CSRF tokens for state-changing operations
- Rate limiting per user/session
- Input sanitization for search queries

**Data Protection:**
- User data isolated via RLS policies (favorites, profiles, collections)
- PII stored in Supabase with encryption at rest
- Secure transmission of reservation/payment info (TLS 1.2+)

### Reliability/Availability

**Error Handling:**
- Error boundaries for React component failures
- Graceful degradation for WebSocket disconnection (retry with exponential backoff)
- API failure recovery: retry 3x with fallback to cached data
- Optimistic UI updates for favorite toggles with rollback on error

**Resilience:**
- Offline support for cached vehicle data (post-MVP)
- Skeleton screens during loading (no blank states)
- Retry logic for failed image loads (placeholder fallback)
- WebSocket reconnection with 5-second retry interval

**Browser Compatibility:**
- Chrome 90+, Safari 14+, Firefox 88+, Edge 90+
- Progressive enhancement for older browsers
- Polyfills for Intersection Observer, ResizeObserver (if needed)

### Observability

**Frontend Logging:**
- Error tracking: Sentry integration for production errors
- Performance monitoring: Web Vitals tracking (CLS, FID, LCP)
- User behavior analytics: custom events for grid interactions, filter usage, modal opens
- API response time logging: percentile tracking (p50, p95, p99)

**Debugging Support:**
- Development mode: React DevTools, Redux DevTools (if used)
- Network tab: clear API call labeling with request IDs
- Console logging: structured logs with context (vehicle count, processing time)
- Feature flags: easy toggling of experimental features

**Monitoring Metrics:**
- Page view tracking per route
- User engagement: session duration, scroll depth
- Feature usage: chat interactions, filter combinations, comparison usage
- Error rates: API failures, WebSocket disconnects, component crashes

## Dependencies and Integrations

### Frontend Framework Dependencies

**Core (Required):**
```json
{
  "react": "^18.3.0",
  "react-dom": "^18.3.0",
  "typescript": "^5.3.0",
  "vite": "^5.0.0",
  "@vitejs/plugin-react": "^4.2.0"
}
```

**Styling & UI:**
```json
{
  "tailwindcss": "^3.4.0",
  "autoprefixer": "^10.4.0",
  "postcss": "^8.4.0",
  "@radix-ui/react-dialog": "^1.0.0",
  "@radix-ui/react-popover": "^1.0.0",
  "@radix-ui/react-dropdown-menu": "^2.0.0",
  "@radix-ui/react-tabs": "^1.0.0"
}
```

**Animation:**
```json
{
  "framer-motion": "^11.0.0"
}
```

**Development Tools:**
```json
{
  "eslint": "^8.56.0",
  "prettier": "^3.1.0",
  "@typescript-eslint/eslint-plugin": "^6.19.0",
  "@typescript-eslint/parser": "^6.19.0",
  "vitest": "^1.1.0",
  "@testing-library/react": "^14.1.0",
  "@testing-library/user-event": "^14.5.0",
  "playwright": "^1.40.0"
}
```

**Authentication:**
```json
{
  "@supabase/supabase-js": "^2.39.0"
}
```

**Utilities:**
```json
{
  "date-fns": "^3.0.0",
  "clsx": "^2.1.0",
  "zustand": "^4.5.0"  // Lightweight state management
}
```

### Backend Integration Points

**FastAPI Endpoints (Already Implemented):**
- `POST /api/search/semantic` - Semantic vehicle search (Epic 1)
- `GET /api/vehicles/{id}` - Single vehicle details
- `POST /api/compare` - Vehicle comparison (Epic 1)
- `POST /api/favorites/{id}` - Toggle favorites (Epic 1)
- `GET /api/collections/trending` - Trending collections (Epic 1)
- `WS /ws/vehicles` - Real-time vehicle updates (Epic 1)

**WebSocket Message Schema:**
```typescript
interface VehicleUpdateMessage {
  type: 'vehicle_update' | 'preference_change' | 'new_search';
  vehicles: Vehicle[];
  timestamp: string;
  requestId: string;
}
```

### Third-Party Services (Post-MVP)

**Error Tracking (Recommended):**
- Sentry: Frontend error monitoring and performance tracking
- Plan: Implement after MVP for production readiness

**Analytics (Recommended):**
- Google Analytics 4: User behavior tracking
- Plan: Implement after MVP for data-driven optimization

**CDN (Recommended):**
- Cloudflare or CloudFront: Static asset delivery
- Plan: Implement before production deployment

## Acceptance Criteria (Authoritative)

**Epic-level acceptance criteria derived from PRD Functional Requirements:**

**AC1: Frontend Infrastructure Established with Supabase Auth**
- GIVEN: Developer sets up new React 18+ project with Vite and TypeScript
- WHEN: Installing dependencies including @supabase/supabase-js
- THEN: Application builds without errors, TypeScript compilation succeeds, HMR works
- AND: ESLint and Prettier configured with no violations
- AND: Integration test confirms connection to FastAPI backend at localhost:8000
- AND: Supabase client configured with VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY
- AND: AuthProvider wraps application root with session management
- AND: useAuth() hook provides signIn, signUp, signOut, and user state
- AND: Login and signup forms render with glass-morphism styling
- AND: Social login buttons (Google, GitHub) trigger OAuth flow
- AND: JWT token automatically included in API request headers

**AC1b: Authentication and Session Management**
- GIVEN: User visits application for first time
- WHEN: Page loads
- THEN: Login/signup page displayed with email/password and social login options
- GIVEN: User enters valid credentials
- WHEN: Clicking "Sign In" button
- THEN: Supabase authenticates user, creates session, redirects to discovery page
- AND: Session persists across page refreshes
- AND: API calls include Authorization header with JWT token
- GIVEN: Authenticated user clicks "Sign Out"
- WHEN: SignOut completes
- THEN: Session cleared, redirected to login page

**AC2: Vehicle Grid Displays Vehicles**
- GIVEN: User navigates to discovery page
- WHEN: Page loads with 20+ vehicles from backend API
- THEN: Grid displays 4 columns on desktop, 2 on tablet, 1 on mobile
- AND: Each vehicle card shows: hero image, match score badge, title, specs, price, features
- AND: Cards render with cascade animation (0.05s stagger, top-to-bottom)
- AND: Responsive layout adapts to viewport resize

**AC3: Real-Time Grid Updates from Conversation**
- GIVEN: User has Otto chat open and vehicle grid displayed
- WHEN: User expresses preference in chat ("I want a red SUV under $40k")
- THEN: Backend sends WebSocket message with updated vehicles within 2 seconds
- AND: Grid animates cascade update: exiting cards fade out, new cards slide in
- AND: Match score badges update with color transitions
- AND: No jarring layout shifts (CLS <0.1)

**AC4: Vehicle Detail Modal**
- GIVEN: User clicks vehicle card
- WHEN: Detail modal opens
- THEN: Modal displays as overlay with backdrop blur (grid visibility preserved)
- AND: Shows: image carousel (5+ images), specifications, Otto's personalized recommendation, social proof badges
- AND: Reservation CTA button prominent ("Request to Hold This Vehicle")
- AND: User can close modal via X button, Escape key, or clicking outside

**AC5: Match Score Visualization**
- GIVEN: Vehicles have match scores from backend (70-95%)
- WHEN: Displaying vehicle cards
- THEN: Match score badge shows circular percentage with color coding:
  - 90%+ = green (#22C55E)
  - 80-89% = lime (#84CC16)
  - 70-79% = yellow (#EAB308)
  - <70% = orange (#F97316)
- AND: Scores 95%+ have subtle pulsing animation
- AND: Score updates animate number transition (0.3s duration)

**AC6: Glass-Morphism Design System**
- GIVEN: Component library implements design tokens
- WHEN: Rendering vehicle cards, modals, and chat widget
- THEN: Glass surfaces have: rgba(255,255,255,0.85) background, 20px backdrop-filter blur, 1px white/18% border
- AND: Otto chat uses dark glass with cyan glow border
- AND: Modals use enhanced glass (92% opacity, 24px blur)
- AND: All glass treatments consistent across components

**AC7: Otto Chat Widget Integration**
- GIVEN: User on discovery page
- WHEN: Page loads
- THEN: Otto chat widget visible as floating FAB (bottom-right, 64px circular)
- AND: FAB shows Otto avatar with breathing animation (3s pulse cycle)
- WHEN: User clicks FAB
- THEN: Widget expands to 384px wide, 600px tall chat interface
- AND: Chat shows: message history, typing indicator, input field
- AND: Messages send via WebSocket to backend conversation API

**AC8: Vehicle Comparison**
- GIVEN: User has 2-3 vehicles selected for comparison
- WHEN: Opening comparison view
- THEN: Modal displays side-by-side comparison table
- AND: Table rows: Price, Mileage, Range (if EV), Acceleration, Key Features
- AND: Best values highlighted in green
- AND: Otto's recommendation shown: "Based on your need for [lifestyle], I recommend..."
- AND: User can remove vehicles from comparison

**AC9: Filtering and Sorting**
- GIVEN: Grid displaying 50+ vehicles
- WHEN: User applies filter (e.g., "Electric SUVs under $50k")
- THEN: Grid updates to show matching vehicles only
- AND: Cascade animation triggers for filtered results
- AND: Filter pills show active state (filled background, glow)
- AND: User can clear filters with one click

**AC10: Performance Targets Met**
- GIVEN: Production build deployed
- WHEN: Measuring Core Web Vitals via Lighthouse
- THEN: FCP <1.5s, LCP <2.5s, TTI <3s, CLS <0.1
- AND: Bundle sizes: initial JS <200KB gzipped, total CSS <50KB gzipped
- AND: Grid maintains 60fps during cascade animations

**AC11: Accessibility Compliance**
- GIVEN: User using screen reader or keyboard navigation
- WHEN: Navigating vehicle grid and modals
- THEN: All interactive elements keyboard-accessible (Tab, Enter, Escape)
- AND: ARIA labels on all buttons and inputs
- AND: Focus indicators visible (2px outline ring)
- AND: Color contrast ratio ≥4.5:1 for text
- AND: Alt text on all vehicle images

**AC12: WebSocket Reliability**
- GIVEN: User with active session
- WHEN: WebSocket disconnects (network interruption)
- THEN: Client attempts reconnection with exponential backoff (5s, 10s, 20s, 30s max)
- AND: UI shows "Reconnecting..." indicator
- AND: On reconnect, state syncs with latest vehicle data
- AND: Graceful fallback to polling if WebSocket unavailable (after 3 failed attempts)

**AC13: Analytics Tracking**
- GIVEN: User interacts with grid, chat, filters, modals
- WHEN: Events occur (page load, vehicle click, filter apply, comparison view)
- THEN: Analytics events logged with context (vehicle ID, filter values, session ID)
- AND: Performance metrics captured (API response times, render durations)
- AND: Error events logged (API failures, WebSocket disconnects)

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component/API | Test Idea |
|---------------------|--------------|---------------|-----------|
| **AC1: Frontend Infrastructure + Supabase Auth** | Services & Modules, Dependencies | Vite config, package.json, supabaseClient.ts | Smoke test: `npm run dev` starts successfully, Supabase client initialized |
| **AC1b: Authentication & Session Management** | APIs, Workflows | AuthProvider, LoginForm, SignUpForm, SocialLoginButtons | Integration test: signIn → verify session → signOut → verify redirect |
| **AC2: Vehicle Grid Displays** | Services & Modules, Workflows | VehicleGrid, VehicleCard | Visual regression test across breakpoints |
| **AC3: Real-Time Cascade Updates** | Workflows, APIs | useWebSocket, useVehicleCascade | Integration test: mock WebSocket, verify animation |
| **AC4: Vehicle Detail Modal** | Workflows, Data Models | VehicleDetailModal, ImageCarousel | E2E: click card → verify modal content |
| **AC5: Match Score Visualization** | Design System, Services | MatchScoreBadge | Unit test: color mapping for score ranges |
| **AC6: Glass-Morphism Design** | Design System, NFR | glass-variants.ts | Visual test: compare snapshots to design tokens |
| **AC7: Otto Chat Widget** | Services & Modules, APIs | OttoChatWidget, useOttoConversation | E2E: send message → verify WebSocket payload |
| **AC8: Vehicle Comparison** | Workflows, Data Models | ComparisonView, ComparisonTable | Unit test: verify best value highlighting logic |
| **AC9: Filtering and Sorting** | Workflows, APIs | GridFilters, useVehicleSearch | Integration test: apply filter → verify grid update |
| **AC10: Performance Targets** | NFR Performance | All components | Lighthouse CI: enforce thresholds in pipeline |
| **AC11: Accessibility** | NFR Security | All components | axe-core testing: 0 violations |
| **AC12: WebSocket Reliability** | NFR Reliability, APIs | useWebSocket | Chaos test: kill WS → verify reconnection logic |
| **AC13: Analytics Tracking** | NFR Observability | useAnalytics | Unit test: verify event logging with payload |

**Epic-to-Functional Requirements Traceability:**

- **FR24-FR30** (Vehicle Information & Content) → AC2, AC4
- **FR20** (Vehicle Comparison) → AC8
- **FR22** (Favorites) → AC2, AC4 (favorite button)
- **FR19** (Match Scores) → AC5
- **FR8-FR12** (Conversation AI) → AC3, AC7
- **FR16-FR18** (Search & Filtering) → AC9
- **PRD Visual Design** → AC6
- **PRD Performance NFRs** → AC10
- **PRD Accessibility NFRs** → AC11

## Risks, Assumptions, Open Questions

### Risks

**R1: Learning Curve for New Tech Stack**
- **Risk:** Team unfamiliar with React 18+ features, TypeScript strict mode, Framer Motion
- **Impact:** Development velocity slower than estimated
- **Mitigation:** Allocate 1 week for spike/construction phase, pair programming, code reviews
- **Probability:** Medium

**R2: WebSocket Connection Stability**
- **Risk:** WebSocket frequent disconnections causing poor UX
- **Impact:** Real-time features fail, cascade updates don't work
- **Mitigation:** Implement robust reconnection logic, polling fallback, connection health monitoring
- **Probability:** Low (backend WebSocket infrastructure already tested)

**R3: Performance Budget Exceeded**
- **Risk:** Bundle sizes exceed targets due to Framer Motion, Radix UI overhead
- **Impact:** Slow page loads, poor Core Web Vitals scores
- **Mitigation:** Code splitting, lazy loading, bundle analysis in CI/CD, consider lighter animation library
- **Probability:** Medium

**R4: Browser Compatibility Issues**
- **Risk:** Glass-morphism backdrop-filter not supported in older browsers
- **Impact:** Design degraded in Safari 14-, Firefox 88-
- **Mitigation:** Progressive enhancement, fallback CSS for no backdrop-filter support
- **Probability:** Low (modern browser requirements documented)

**R5: Backend API Changes During Development**
- **Risk:** FastAPI endpoints evolve while frontend built in parallel
- **Impact:** Integration failures, contract mismatches
- **Mitigation:** OpenAPI spec frozen, TypeScript types generated from OpenAPI, contract testing
- **Probability:** Medium

### Assumptions

**A1: Backend APIs Stable and Documented**
- Assumption: FastAPI endpoints in `src/api/` remain stable, OpenAPI docs accurate
- Validation: Review API docs before starting Story 3-2

**A2: Supabase Authentication Ready for Integration**
- Assumption: Supabase project configured, Auth enabled, email provider active
- Validation: Check Supabase Dashboard → Authentication → Providers before Story 3-1
- Environment variables: VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY required

**A3: WebSocket Endpoint Production-Ready**
- Assumption: `ws://localhost:8000/ws/vehicles` stable and handles reconnections
- Validation: Load test WebSocket with 100 concurrent connections

**A4: Vehicle Data Available in Database**
- Assumption: 50+ sample vehicles in Supabase for testing
- Validation: Query database during Story 3-1 setup

**A5: Design Tokens Finalized**
- Assumption: UX design specification (glass-morphism tokens) won't change significantly
- Validation: Design review with stakeholder before Story 3-10

### Open Questions

**Q1: Authentication Strategy for MVP** ✅ **RESOLVED**
- **Decision:** Use Supabase Authentication (`@supabase/supabase-js`) for Epic 3
- **Implementation:**
  - Email/password authentication via Supabase Auth
  - Social login (Google, GitHub) via OAuth
  - AuthContext with useAuth() hook for session management
  - JWT token validation in FastAPI backend
  - Row Level Security (RLS) for user data isolation
- **Rationale:** Eliminates Epic 4 dependency, enables real authentication from Story 3-1, provides secure user sessions for favorites/profiles
- **Status:** ✅ DECIDED 2026-01-03 - Supabase integration added to tech spec

**Q2: Image CDN Strategy**
- Question: Where to host vehicle images? Supabase storage or external CDN?
- Status: Technical decision required
- Proposed Answer: Use Supabase storage for MVP, migrate to CloudFlare CDN post-MVP

**Q3: State Management Approach**
- Question: Is React Context + hooks sufficient, or need Redux/Zustand?
- Status: Technical decision pending
- Proposed Answer: Start with React Context (simpler), migrate to Zustand if complexity grows

**Q4: Testing Requirements**
- Question: What % test coverage required for Epic 3 completion?
- Status: Definition required
- Proposed Answer: 80% coverage for critical components (VehicleGrid, OttoChatWidget), 60% for utilities

**Q5: Deployment Strategy**
- Question: Where to host frontend? Vercel, Netlify, or same server as FastAPI?
- Status: Infrastructure decision pending
- Proposed Answer: Deploy to Vercel for MVP (easiest static hosting), FastAPI on Render

## Test Strategy Summary

### Testing Levels

**Unit Testing (Vitest + React Testing Library):**
- **Target:** 80% coverage for business logic components
- **Scope:** Individual components, hooks, utilities in isolation
- **Examples:**
  - MatchScoreBadge: Verify color mapping for score ranges
  - formatters: Verify price formatting ($45,000, mileage: "25k mi")
  - useVehicleSearch: Mock API, verify state updates
  - ComparisonTable: Verify best value highlighting logic

**Integration Testing (Vitest + MSW):**
- **Target:** All API client functions, WebSocket hooks
- **Scope:** Component interactions with mocked backend
- **Examples:**
  - VehicleGrid + mock API: Verify rendering with API response
  - OttoChatWidget + mock WebSocket: Verify message sending/receiving
  - FilterPillBar + useVehicleSearch: Verify filter application triggers search

**Visual Regression Testing (Playwright + Chromatic):**
- **Target:** All visual components across breakpoints
- **Scope:** Component screenshots compared to baseline
- **Examples:**
  - VehicleCard: Mobile (375px), Tablet (768px), Desktop (1440px)
  - VehicleDetailModal: Verify glass-morphism backdrop blur
  - OttoChatWidget: Verify avatar glow animation

**E2E Testing (Playwright):**
- **Target:** Critical user journeys
- **Scope:** Full user flows from page load to conversion
- **Test Cases:**
  1. **Discovery Journey:** Navigate → Grid loads → Click vehicle → View detail → Close modal
  2. **Conversational Search:** Chat "SUV under $40k" → Verify grid updates → Check match scores
  3. **Comparison Flow:** Select 2 vehicles → Open comparison → Verify table → Close
  4. **Filtering:** Apply "Electric" filter → Verify results → Clear filter → Verify reset
  5. **Accessibility:** Keyboard navigate grid → Tab through modals → Verify focus indicators

**Performance Testing (Lighthouse CI):**
- **Target:** Core Web Vitals thresholds enforced in CI/CD
- **Metrics:**
  - FCP <1.5s, LCP <2.5s, TTI <3s, CLS <0.1
  - Bundle size checks: initial JS <200KB, CSS <50KB
  - Run on every PR, block merge if thresholds exceeded

**Accessibility Testing (axe-core):**
- **Target:** Zero WCAG 2.1 AA violations
- **Tools:** axe DevTools, jest-axe
- **Automated checks:** Color contrast, ARIA labels, keyboard accessibility
- **Manual testing:** Screen reader (NVDA/VoiceOver), keyboard-only navigation

### Testing Pyramid

```
        E2E (5%)     - Critical journeys only
       /            \
      /              \
     /    Visual (10%)   - Component snapshots
    /    /            \
   /    /              \
  /    Integration (20%) - API + WebSocket mocks
 /    /    /            \
/    /    /              \
Unit (65%) - Components, hooks, utils
```

### Test Data Strategy

**Fixtures:**
- `mockVehicles.ts`: 50 sample vehicles covering all score ranges (70-95%)
- `mockChatMessages.ts`: Sample conversation transcripts
- `mockWebSocketMessages.ts`: Vehicle update scenarios

**Test Utilities:**
- `renderWithProviders()`: Wraps components with Context providers
- `mockWebSocket()`: MSW handler for WebSocket connections
- `waitForLoadingState()`: Waits for skeleton screens to resolve

### CI/CD Integration

**Pre-commit Hooks:**
- ESLint: `eslint src/ --fix`
- Prettier: `prettier --write src/`
- Type check: `tsc --noEmit`
- Unit tests: `vitest run`

**PR Checks:**
- All unit tests pass
- Integration tests pass
- Visual regression: Chromatic review required
- Lighthouse CI: Performance thresholds
- Bundle size: Limit check (bundlewatch)

**Deployment Pipeline:**
- E2E tests run on deploy preview (Vercel/Netlify)
- Manual QA on staging environment
- Production smoke tests after deployment

### Definition of Done for Epic 3

1. All 13 stories marked "done" in sprint-status.yaml
2. Unit test coverage ≥80% for critical components
3. Zero accessibility violations (axe-core)
4. Performance targets met (Lighthouse score ≥90)
5. Visual regression tests passing
6. E2E tests passing for 5 critical journeys
7. Code review approved by 2 developers
8. Documentation updated (component stories, API integration guide)
9. Deployed to staging environment
10. Product owner (BMad) acceptance testing complete

