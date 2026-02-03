# Story 3.2: Build Responsive Vehicle Grid Component (Core)

**Epic:** Epic 3 - Dynamic Vehicle Grid Interface
**Status:** ✅ DONE
**Date:** 2026-01-04
**Last Updated:** 2026-01-04
**Completion Date:** 2026-01-04

**Story Scope:** Core responsive grid with progressive disclosure for mobile-first UX.
**Advanced features** (gestures, viewed tracking, smart match score) moved to Story 3-3.

## Story

As a **user**,
I want to see **vehicles displayed in an attractive, responsive grid that works seamlessly on all devices**,
so that I can **browse vehicle inventory with optimal viewing experience regardless of screen size**.

━━━━━━━━━━━━━━━━━━━━━━━

## Requirements Context Summary

**Source Documents:**
- Tech Spec Epic 3: `docs/sprint-artifacts/tech-spec-epic-3.md`
- PRD: `docs/prd.md`
- Architecture: `docs/architecture.md`
- UX Design: `docs/ux-design-specification.md`
- Epics: `docs/epics.md`

**Epic 3 Overview:**
Delivers the primary user interface for Otto.AI - a dynamic, real-time responsive web application that transforms car shopping into conversational discovery. Story 3-2 specifically implements the responsive vehicle grid component system.

**Key Requirements from Tech Spec:**
- **O2: Build Vehicle Grid Component System** (Stories 3-2, 3-3, 3-7)
  - Implement responsive vehicle grid with dynamic cascade updates
  - Grid must react in real-time to Otto AI conversation context
  - Display vehicles with animated transitions as user preferences evolve

**Frontend Stack (from Story 3-1 - DONE):**
- React 19.2.0 + TypeScript 5.9.3
- Vite 7.2.4 build system
- Supabase Auth (`@supabase/supabase-js@^2.39.0`)
- AuthContext with `useAuth()` hook available
- API client with JWT authentication implemented

━━━━━━━━━━━━━━━━━━━━━━━

## Structure Alignment Summary

**Previous Story Learnings (Story 3-1 - DONE):**

**New Infrastructure Created:**
- ✅ React 19.2.0 + TypeScript 5.9.3 frontend initialized
- ✅ Supabase Auth client configured (`src/app/lib/supabaseClient.ts`)
- ✅ AuthContext implemented with `useAuth()` hook (`src/app/contexts/AuthContext.tsx`)
- ✅ API client with JWT authentication (`src/app/services/apiClient.ts`)
- ✅ TypeScript types defined (`src/app/types/api.ts`)

**Key Patterns to Reuse:**
- Use absolute imports from `src/app/` for cleaner paths
- Wrap API calls in try-catch with user-friendly error messages
- Use async/await throughout for consistent async handling
- Test components in isolation before integrating with pages
- Glass-morphism styling: `rgba(255,255,255,0.85)` background, 20px backdrop-filter blur

**Technical Debt:**
- None identified from Story 3-1
- Frontend is fresh implementation with no遗留 issues

**Architectural Decisions:**
- Supabase Auth for authentication (eliminates Epic 4 dependency)
- React Context + hooks for state management (Redux not needed for MVP)
- Glass-morphism design tokens from UX spec
- Framer Motion for animations (to be installed in this story)

━━━━━━━━━━━━━━━━━━━━━━━

## Acceptance Criteria

### AC1: Vehicle Grid Displays Vehicles on Desktop
- **GIVEN** I'm browsing vehicles on a desktop computer (viewport ≥ 1200px)
- **WHEN** the vehicle grid loads with 20+ vehicles from the backend API
- **THEN** I see vehicles displayed in a **3-column grid layout** (optimized for modern screens)
- **AND** each vehicle card shows key information: hero image, match score badge, title (year make model), specs (mileage, range, trim), price with savings, feature tags
- **AND** cards are sized consistently with proper aspect ratios for images (16:10)
- **AND** hover effects provide additional vehicle details (slight lift, enhanced shadow)
- **AND** the grid uses glass-morphism styling with white/transparent glass surface
- **AND** responsive layout adapts to viewport resize

### AC2: Vehicle Grid Adapts to Tablet View
- **GIVEN** I'm using the app on a tablet device (768px - 1199px)
- **WHEN** the vehicle grid loads
- **THEN** I see vehicles displayed in a 2-column grid layout
- **AND** all vehicle information remains readable without horizontal scrolling
- **AND** images maintain aspect ratio and quality
- **AND** touch interactions work smoothly (tap to view details)

### AC3: Vehicle Grid Adapts to Mobile View
- **GIVEN** I'm using the app on a mobile phone (viewport < 768px)
- **WHEN** the vehicle grid loads
- **THEN** I see vehicles displayed in a 1-column layout
- **AND** vehicle cards are optimized for vertical scrolling
- **AND** images are large enough to appreciate vehicle details
- **AND** key information (price, match score) is prominently displayed
- **AND** no horizontal scrolling is required

### AC4: Vehicle Card Displays Complete Information
- **GIVEN** a vehicle card is rendered in the grid
- **WHEN** viewing the card
- **THEN** I see the following elements:
  - Hero image with 16:10 aspect ratio
  - Match score badge (top-left, circular, color-coded: 90%+ green, 80-89% lime, 70-79% yellow, <70% orange)
  - **Otto's Pick badge** (for vehicles with 95%+ match score, special icon with subtle glow)
  - Vehicle title (semibold, year make model)
  - Spec line (mileage, range if EV, trim)
  - Price display with savings callout in green if applicable
  - Feature tags as small pills (max 3-4 visible)
  - "More like this" / "Less like this" quick feedback buttons
  - **"Add to compare" button** (adds vehicle to comparison buffer)
- **AND** Favorite button (heart icon) with toggle state
- **AND** All text is legible against the glass-morphism background

### AC5: Match Score Badge Visual Design
- **GIVEN** a vehicle has a match score calculated by the backend
- **WHEN** the vehicle card renders
- **THEN** the match score badge displays as a circular badge overlaid on the hero image
- **AND** the badge background color indicates score tier:
  - 90%+ = green (#22C55E) with white text
  - 80-89% = lime (#84CC16) with white text
  - 70-79% = yellow (#EAB308) with dark slate text
  - <70% = orange (#F97316) with white text
- **AND** scores ≥95% show a subtle pulsing animation
- **AND** scores ≥95% display an additional "Otto's Pick" badge below the match score (star icon with cyan glow)
- **AND** badge size is proportional: 48px (md), 56px (lg)
- **AND** percentage value is centered and bold

### AC6: Grid Integration with API Client
- **GIVEN** the user is authenticated and viewing the vehicle grid
- **WHEN** the grid component mounts
- **THEN** the API client fetches vehicles from `/api/vehicles` endpoint with JWT authentication
- **AND** loading state displays skeleton cards while fetching
- **AND** error state displays user-friendly message with retry option
- **AND** vehicles are sorted by match score (highest first)
- **AND** pagination or infinite scroll handles large inventories (>50 vehicles)

### AC7: Glass-Morphism Design System Applied
- **GIVEN** the vehicle grid is rendered
- **WHEN** viewing the grid and cards
- **THEN** vehicle cards use light glass styling:
  - Background: rgba(255, 255, 255, 0.85)
  - Backdrop-filter blur: 20px
  - Border: 1px solid rgba(255, 255, 255, 0.18)
  - Box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08)
  - Border-radius: 12px
- **AND** cards have smooth hover state transitions (200ms ease-out)
- **AND** the overall page background uses a subtle gradient to enhance glass effect

### AC8: Performance and Accessibility
- **GIVEN** the vehicle grid contains 20+ vehicles
- **WHEN** the page loads
- **THEN** initial page render completes within 1.5s (FCP < 1.5s)
- **AND** all images are lazy-loaded to improve initial load time
- **AND** vehicle cards use React.memo to prevent unnecessary re-renders
- **AND** keyboard navigation works (Tab to focus cards, Enter to select)
- **AND** all images have descriptive alt text
- **AND** ARIA labels are provided for interactive elements
- **AND** color contrast ratios meet WCAG 2.1 AA standards

### AC9: Progressive Disclosure of Information
- **GIVEN** a user is viewing vehicle cards on a mobile device
- **WHEN** the vehicle grid loads
- **THEN** cards show collapsed state: hero image, match score badge, title, price
- **AND** tapping "Show more" chevron expands card to reveal specs, features, tags
- **AND** desktop users see same information on hover (no tap needed)
- **AND** expanded state persists across page navigation
- **AND** collapse animation is smooth (200ms ease-out)

**Note:** Advanced features (Gesture Support, Viewed Tracking, Smart Match Score Display) moved to Story 3-3 to reduce complexity and enable iterative development based on user feedback.

━━━━━━━━━━━━━━━━━━━━━━━

## Tasks / Subtasks

### Project Setup and Dependencies

- [ ] **3-2.1**: Install Framer Motion for animations
  - Run `cd frontend && npm install framer-motion`
  - Verify installation in package.json
  - Test basic animation component

- [ ] **3-2.2**: Create TypeScript types for Vehicle grid
  - Extend `src/types/api.ts` with Vehicle interface
  - Add VehicleImage, VehicleSpecs interfaces
  - Add MatchScore, FilterOptions types
  - Ensure types match backend Pydantic models

### Core Components: VehicleCard

- [ ] **3-2.3**: Create VehicleCard component with glass-morphism styling
  - Create `src/components/vehicle-grid/VehicleCard.tsx`
  - Implement card layout with hero image, content sections
  - Apply light glass styling from design tokens
  - Add hover state with lift effect (whileHover={{ y: -4 }})
  - Implement responsive image aspect ratio (16:10)
  - **Add variant prop** ("default" | "compact" | "comparison") for future reuse in Stories 3-6

- [ ] **3-2.4**: Create MatchScoreBadge component
  - Create `src/components/vehicle-grid/MatchScoreBadge.tsx`
  - Implement circular badge with color tiers
  - Add pulsing animation for scores ≥95%
  - **Add "Otto's Pick" badge variant** (star icon with cyan glow for 95%+ matches)
  - Support size variants (sm, md, lg)
  - Add animated score transitions with Framer Motion

- [ ] **3-2.5**: Create VehicleSpecs display component
  - Create `src/components/vehicle-grid/VehicleSpecs.tsx`
  - Display mileage, range (if EV), trim
  - Use icons for visual clarity
  - Format numbers appropriately (commas for thousands)

- [ ] **3-2.6**: Create PriceDisplay component
  - Create `src/components/vehicle-grid/PriceDisplay.tsx`
  - Display current price formatted as currency
  - Show savings callout in green if applicable
  - Support original price strikethrough for discounted vehicles

- [ ] **3-2.7**: Create FeatureTags component
  - Create `src/components/vehicle-grid/FeatureTags.tsx`
  - Display up to 4 feature tags as small pills
  - Use consistent color scheme for tags
  - Truncate overflow tags with "N more" indicator

- [ ] **3-2.8**: Create FavoriteButton component
  - Create `src/components/vehicle-grid/FavoriteButton.tsx`
  - Heart icon with toggle state (filled/outline)
  - Smooth transition animation (scale effect)
  - Integrate with favorites API (POST /api/favorites/{id})
  - Handle error states gracefully

- [ ] **3-2.9**: Create ActionButtons component
  - Create `src/components/vehicle-grid/ActionButtons.tsx`
  - "More like this" / "Less like this" buttons
  - **"Add to compare" button** (adds to comparison buffer, shows visual counter)
  - Icon-based design with tooltips
  - Integrate with preference feedback API
  - Track user interactions for preference learning
  - **Note:** Otto AI integration for compare button deferred to Story 3-6 (conversational comparison)

### Core Components: VehicleGrid

- [ ] **3-2.10**: Create VehicleGrid component with responsive layout
  - Create `src/components/vehicle-grid/VehicleGrid.tsx`
  - Implement **3-column desktop, 2-column tablet, 1-column mobile** layout (optimized for modern screens)
  - Use CSS Grid with responsive breakpoints (Tailwind classes)
  - Add gap spacing for visual separation
  - Ensure smooth layout transitions on viewport resize

- [ ] **3-2.11**: Create useVehicleGrid custom hook
  - Create `src/components/vehicle-grid/useVehicleGrid.ts`
  - Fetch vehicles from API using VehicleAPIClient
  - Manage loading, error, and data states
  - Implement pagination or infinite scroll
  - Handle retry logic for failed requests

- [ ] **3-2.12**: Implement skeleton loading states
  - Create `src/components/vehicle-grid/VehicleCardSkeleton.tsx`
  - Match card layout with shimmer effect
  - Display 8-12 skeleton cards during initial load
  - Fade in actual cards when data arrives

### Page Integration

- [ ] **3-2.13**: Update HomePage to display VehicleGrid
  - Modify `src/app/pages/HomePage.tsx`
  - Replace placeholder content with VehicleGrid
  - Pass user authentication state to grid
  - Ensure ProtectedRoute wraps the page

- [ ] **3-2.14**: Add error boundary for VehicleGrid
  - Create `src/components/vehicle-grid/VehicleGridErrorBoundary.tsx`
  - Catch component errors gracefully
  - Display user-friendly error message
  - Provide retry button for recovery

### Styling and Design System

- [ ] **3-2.15**: Create glass-morphism utility styles
  - Create `src/styles/glass.ts` with design tokens
  - Define light, dark, modal glass variants
  - Export as Tailwind-compatible utility classes
  - Document usage in component comments

- [ ] **3-2.16**: Define responsive breakpoints
  - Configure Tailwind breakpoints in `tailwind.config.js`
  - Mobile: < 768px (1 column)
  - Tablet: 768px - 1199px (2 columns)
  - Desktop: ≥ 1200px (3 columns) - optimized for modern screens
  - Test layout transitions at each breakpoint

### Testing

- [ ] **3-2.17**: Write unit tests for VehicleCard
  - Test component renders with required props
  - Test match score badge color tiers
  - Test favorite button toggle state
  - Test hover interactions
  - Achieve 80%+ code coverage

- [ ] **3-2.18**: Write unit tests for VehicleGrid
  - Test responsive layout behavior
  - Test API integration and data fetching
  - Test loading and error states
  - Test pagination functionality

- [ ] **3-2.19**: Write accessibility tests
  - Test keyboard navigation (Tab, Enter, Escape)
  - Verify ARIA labels and roles
  - Test screen reader compatibility
  - Verify color contrast ratios

- [ ] **3-2.20**: Write visual regression tests
  - Capture screenshots at each breakpoint
  - Test glass-morphism styling consistency
  - Verify match score badge appearance
  - Test hover state visual changes

### Performance Optimization

- [ ] **3-2.21**: Implement image lazy loading
  - Use native loading="lazy" attribute
  - Add fade-in animation when images load
  - Handle image load errors with fallback
  - Preload critical above-fold images

- [ ] **3-2.22**: Optimize component rendering
  - Wrap VehicleCard in React.memo
  - Use useCallback for event handlers
  - Implement virtual scrolling for large inventories (>100 vehicles)
  - Add performance monitoring (render time metrics)

### Progressive Disclosure (AC9)

- [ ] **3-2.23**: Create ExpandableVehicleCard variant
  - Create `src/components/vehicle-grid/ExpandableVehicleCard.tsx`
  - Implement collapsed state (image, badge, title, price only)
  - Add "Show more" chevron button with rotation animation
  - Expand to show specs, features, tags on tap
  - Persist expanded state in component state
  - Desktop: Show all info on hover without tap

- [ ] **3-2.24**: Implement card collapse/expand animation
  - Use Framer Motion AnimatePresence for smooth height transition
  - Configure layout animation for fluid content reflow
  - Add opacity fade-in for revealed content (200ms delay)
  - Test performance on mobile devices

**Note:** Tasks for Gesture Support (3-2.25 to 3-2.28), Viewed State Tracking (3-2.29 to 3-2.31), and Smart Match Score Display (3-2.32 to 3-2.34) have been moved to Story 3-3 to reduce scope and enable iterative development.

━━━━━━━━━━━━━━━━━━━━━━━

## Dev Notes

### Story Split Rationale (Six Thinking Hats Analysis)

**Decision:** Split original Story 3-2 into two stories to reduce complexity and enable iterative development.

**Analysis Summary:**

**🎩 White Hat (Facts):**
- Original scope: 34 tasks, 12 acceptance criteria
- Complexity: HIGH (gestures, viewport detection, progressive disclosure)
- Risk level: MEDIUM (performance concerns, state management complexity)

**⚫ Black Hat (Risks):**
- 34 components rendering simultaneously could cause lag
- Gesture detection conflicts with scrolling risk
- State management complexity (expanded cards, viewed state, dismissed vehicles)
- Browser compatibility concerns (IntersectionObserver, haptics)

**💛 Yellow Hat (Benefits of Split):**
- Faster time-to-market for core grid functionality
- User feedback before investing in advanced features
- Reduced risk of over-engineering unproven UX patterns
- Clearer Definition of Done for each story

**🔵 Blue Hat (Process):**
- Story 3-2 (Core): Foundation first, validate responsive design
- Story 3-3 (Enhanced): Build on proven foundation, iterate based on data

**What Moved to Story 3-3:**
- Gesture Support (swipe-to-favorite, swipe-to-dismiss, pull-to-refresh)
- Viewed State Tracking (Intersection Observer, progress indicator)
- Smart Match Score Display (progress bar, tooltip, breakdown)
- Associated tasks: 3-2.25 through 3-2.34 (12 tasks)
- Associated components: MatchScoreProgress, MatchScoreTooltip, ViewedBadge, useViewedTracking

**What Remains in Story 3-2 (Core):**
- Responsive vehicle grid (4/2/1 column layout)
- Glass-morphism design system
- Progressive Disclosure (AC9) - kept as HIGH VALUE for mobile UX
- All performance and accessibility requirements
- Core acceptance criteria (AC1-AC9)
- Core tasks: 3-2.1 through 3-2.24 (24 tasks)

**Success Criteria:**
- Story 3-2: Grid displays, responsive works, progressive disclosure functional, Lighthouse score >90
- Story 3-3: Gestures work smoothly, tracking accurate, users delighted, built on 3-2 foundation

### Journey Mapping Insights

**User Journey Analysis: Mobile → Tablet → Desktop**

The vehicle browsing experience varies significantly across devices. Journey mapping revealed critical pain points and opportunities:

**Key Journey Stages:**
1. **Discovery & Initial Load** - First impression, performance perception
2. **Exploration & Filtering** - Scanning, comparing, narrowing down
3. **Decision & Action** - Favorites, comparison, reservation intent

**Cross-Device Patterns:**
- Mobile: Vertical scroll, tap interactions, gesture expectations
- Tablet: Hybrid touch/cursor, rotation considerations
- Desktop: Quick scanning, hover interactions, keyboard shortcuts

**Critical Pain Points Discovered:**
- Mobile images too small for evaluation → **Solution (in Story 3-2)**: 16:9 aspect ratio on mobile, tap-to-expand
- Match score not prominent while scrolling → **Solution (deferred to 3-3)**: Dual display (badge + footer progress bar)
- Hover-only info lost on mobile → **Solution (in Story 3-2)**: Progressive disclosure with expandable cards
- No progress feedback → **Solution (deferred to 3-3)**: "Viewed X of Y" tracking with visual badges
- Filters hide content → **Solution (future)**: Slide-out panel with visible grid underneath

**Enhancement Opportunities:**
- ✅ **Story 3-2**: Progressive disclosure for information density management
- ⏳ **Story 3-3**: Gesture support (swipe to favorite/dismiss, pull-to-refresh)
- ⏳ **Story 3-3**: Viewed state tracking for progress awareness
- ⏳ **Story 3-3**: Redundant match score display for visibility

### SCAMPER Analysis Insights

**Creative Exploration Applied:** SCAMPER method (Substitute, Combine, Adapt, Modify, Put to Other Uses, Eliminate, Reverse)

**Enhancements Applied to Story 3-2:**

1. **Modify: 3-Column Desktop Grid**
   - **Change:** Desktop layout from 4-column to 3-column
   - **Rationale:** Modern laptops (1366-1920px) display larger cards with better image visibility
   - **Impact:** Improved visual hierarchy, better aspect ratio for vehicle images
   - **Implementation:** Updated AC1, task 3-2.10, task 3-2.16

2. **Adapt: "Otto's Pick" Badge for 95%+ Matches**
   - **Pattern Borrowed:** Airbnb's "Superhost" badge equivalent
   - **Feature:** Star icon with cyan glow for exceptional matches (≥95%)
   - **Rationale:** Differentiates top-tier recommendations, creates excitement
   - **Impact:** Visual distinction for premium matches, reinforces Otto's intelligence
   - **Implementation:** Updated AC4, AC5, task 3-2.4

3. **Combine: "Add to Compare" Button in ActionButtons**
   - **Addition:** Third button (➕) alongside thumbs up/down
   - **Behavior:** Adds vehicle to local comparison buffer (no Otto integration yet)
   - **Otto Integration:** Deferred to Story 3-6 (conversational comparison tools)
   - **Rationale:** Quick visual action now, intelligent conversation later
   - **Implementation:** Updated AC4, task 3-2.9
   - **Future (Story 3-6):** Otto will proactively suggest: "Comparing [A] vs [B]. Want me to highlight the differences?"

4. **Put to Other Uses: VehicleCard Variant Prop**
   - **Feature:** Add `variant` prop ("default" | "compact" | "comparison")
   - **Rationale:** Future-proof component for reuse in:
     - Story 3-6: Comparison view (side-by-side cards)
     - Story 3-6: Favorites view (compact variant)
   - **Impact:** Code reuse, consistent UX across views
   - **Implementation:** Extended task 3-2.3

**Elimination Analysis:**
- **Decision:** No elements eliminated from Story 3-2
- **Rationale:** All current elements (feature tags, specs, images, favorites) serve validated user needs from Journey Mapping
- **Journey Finding:** Progressive Disclosure (AC9) specifically addresses critical mobile pain point

**Reversal Analysis:**
- **Rejected:** Match score in footer, price-first display, low-match-first loading
- **Reason:** Violates "visual-first" pattern, reduces at-a-glance scanning
- **Deferred:** "Exclude filters" (e.g., "No red cars") → Story 3-7 (Filtering & Sorting)

**Alternative Patterns Considered:**
- ❌ Masonry grid (variable heights) - rejected for consistency
- ❌ Horizontal scroll (mobile) - conflicts with Progressive Disclosure (AC9)
- ❌ Top carousel for 95%+ matches - deferred to Story 3-3 (enhanced UX)
- ❌ Otto avatar suggestions - deferred to Story 3-13 (Otto chat widget)

### Technical Considerations

1. **Frontend Infrastructure from Story 3-1 (DONE)**:
   - React 19.2.0 + TypeScript 5.9.3 + Vite 7.2.4 already configured
   - Supabase Auth client and API client available
   - AuthContext provides useAuth() hook for authenticated requests
   - ProtectedRoute component secures pages
   - Location: `frontend/` directory at project root

2. **Glass-Morphism Design Tokens** (from UX spec):
   - Light glass: `rgba(255,255,255,0.85)` background, 20px backdrop-filter blur
   - Border: `1px solid rgba(255, 255, 255, 0.18)`
   - Shadow: `0 8px 32px rgba(0, 0, 0, 0.08)`
   - Border-radius: 12px for cards
   - See [Source: docs/ux-design-specification.md#Glass-Morphism-UI-Treatment]

3. **API Integration Points**:
   - FastAPI backend runs on `http://localhost:8000`
   - Vehicles endpoint: `GET /api/vehicles` with JWT authentication
   - Favorites: `POST /api/favorites/{id}`
   - Feedback: `POST /api/feedback` (more/less like this)
   - All requests include `Authorization: Bearer <token>` header
   - Use `VehicleAPIClient` from `src/app/services/apiClient.ts`

4. **Responsive Breakpoints** (from PRD):
   - Mobile: < 768px (1 column, full-width cards)
   - Tablet: 768px - 1199px (2 columns, 50% width)
   - Desktop: ≥ 1200px (4 columns, 25% width)
   - Use Tailwind's responsive prefixes: `grid-cols-1`, `md:grid-cols-2`, `lg:grid-cols-4`
   - See [Source: docs/prd.md#Responsive-Design-Requirements]

5. **Framer Motion Animation Patterns**:
   - Card entry: `initial={{ opacity: 0, y: 20 }}` → `animate={{ opacity: 1, y: 0 }}`
   - Hover: `whileHover={{ y: -4, scale: 1.02 }}`
   - Staggered animations: Use `transition={{ delay: index * 0.05 }}`
   - Smooth transitions: `transition={{ type: 'spring', stiffness: 300, damping: 25 }}`
   - Cascade animation preset: See tech-spec-epic-3.md

6. **Match Score Color Coding** (from PRD):
   - Excellent (90%+): Green `#22C55E` with white text
   - Good (80-89%): Lime `#84CC16` with white text
   - Fair (70-79%): Yellow `#EAB308` with dark slate text
   - Low (<70%): Orange `#F97316` with white text
   - Scores ≥95%: Add pulsing animation
   - See [Source: docs/prd.md#Match-Score-Visualization]

### Integration Points

- **FastAPI Backend** (`src/api/`): Vehicle data from semantic search API [Source: docs/architecture.md#API-Contracts]
- **Supabase Auth**: User authentication via `useAuth()` hook from Story 3-1
- **API Client** (`src/app/services/apiClient.ts`): VehicleAPIClient for authenticated requests [Source: docs/sprint-artifacts/tech-spec-epic-3.md#REST-API-Clients]
- **Future WebSocket Integration** (Story 3-3): Real-time cascade updates from conversation

### Dependencies

- **Required**: Story 3-1 frontend infrastructure (completed 2026-01-04)
- **Required**: FastAPI backend running on localhost:8000 with vehicle data
- **Required**: Supabase environment variables configured (`VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY`)
- **Required**: Framer Motion installation (task 3-2.1) - for animations
- **Optional**: Tailwind CSS for responsive utility classes (consider if custom CSS becomes complex)

**Note:** @use-gesture/react and Popper.js dependencies moved to Story 3-3 with gesture features.

### Project Structure Notes

**New Files to Create** (14 components, hooks, utilities):
```
frontend/src/
├── components/
│   └── vehicle-grid/               # Vehicle grid components
│       ├── VehicleGrid.tsx         # Main grid container
│       ├── VehicleCard.tsx         # Individual vehicle card
│       ├── ExpandableVehicleCard.tsx # Progressive disclosure variant (NEW)
│       ├── MatchScoreBadge.tsx     # Circular score indicator badge
│       ├── VehicleSpecs.tsx        # Specs display (mileage, range)
│       ├── PriceDisplay.tsx        # Price with savings
│       ├── FeatureTags.tsx         # Feature pills
│       ├── FavoriteButton.tsx      # Heart icon toggle
│       ├── ActionButtons.tsx       # More/Less like buttons
│       ├── VehicleCardSkeleton.tsx # Loading skeleton
│       ├── VehicleGridErrorBoundary.tsx # Error handling
│       └── useVehicleGrid.ts       # Custom hook for data fetching
├── styles/
│   └── glass.ts                    # Glass-morphism design tokens
└── types/
    └── vehicle.ts                  # Vehicle type definitions (extend api.ts)
```

**Note:** Components moved to Story 3-3:
- MatchScoreProgress.tsx, MatchScoreTooltip.tsx, ViewedBadge.tsx
- useViewedTracking.ts hook

**Files to Modify**:
- `src/app/pages/HomePage.tsx` - Add VehicleGrid component
- `src/types/api.ts` - Extend with Vehicle types
- `frontend/package.json` - Add Framer Motion dependency

### Testing Standards Summary

- **Unit Tests**: Vitest + React Testing Library for components and hooks
- **Accessibility Tests**: @testing-library/jest-dom for a11y assertions
- **Visual Regression**: Playwright screenshots at each breakpoint
- **Coverage Target**: 80% for vehicle-grid components
- **Performance Tests**: Lighthouse CI for FCP, LCP metrics
- **Testing Infrastructure**: Already configured in Story 3-1 (vitest.config.ts)

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC2] - Vehicle grid displays vehicles
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#Data-Models-and-Contracts] - Vehicle interface definition
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#Services-and-Modules] - Frontend module structure
- [Source: docs/architecture.md#Frontend-Component-Architecture] - Glass-morphism utility system
- [Source: docs/architecture.md#Vehicle-Card-Component-Structure] - VehicleCard implementation pattern
- [Source: docs/architecture.md#Match-Score-Badge-Component] - MatchScoreBadge implementation pattern
- [Source: docs/ux-design-specification.md#Glass-Morphism-UI-Treatment] - Glass styling specifications
- [Source: docs/prd.md#Visual-Design-Requirements] - Glass-morphism UI treatment
- [Source: docs/prd.md#Match-Score-Visualization] - Score badge color coding
- [Source: docs/epics.md#Story-3.2] - Original story definition with acceptance criteria

### Learnings from Previous Story

**From Story 3-1 (Status: done - Completed 2026-01-04)**

**New Infrastructure Available:**
- React 19.2.0 + TypeScript 5.9.3 frontend initialized in `frontend/` directory
- Supabase Auth client configured and tested - useAuth() hook available at `src/app/contexts/AuthContext.tsx`
- API client with JWT authentication implemented - VehicleAPIClient class in `src/app/services/apiClient.ts` (195 lines)
- TypeScript types defined in `src/app/types/api.ts` (102 lines)
- ESLint + Prettier configured - maintain code quality standards
- Production build verified passing - TypeScript compilation succeeds

**Key Patterns Established:**
- Use absolute imports from `src/app/` for cleaner paths (e.g., `import { useAuth } from '@/app/contexts/AuthContext'`)
- Wrap API calls in try-catch with user-friendly error messages
- Use async/await throughout for consistent async handling
- Test components in isolation before integrating with pages
- Verify responsive behavior at actual breakpoints, not just browser resize

**Technical Notes:**
- Frontend location is `frontend/` at project root (separate from Python backend `src/`)
- All component files use `.tsx` extension
- Use `@/` alias for `src/app/` imports (configured in vite.config.ts)
- Glass-morphism design tokens defined in tech-spec-epic-3.md

**Files Created in Story 3-1 (Available for Reuse):**
- `frontend/package.json` - Dependencies and scripts
- `frontend/vite.config.ts` - Vite configuration with @ alias
- `frontend/vitest.config.ts` - Vitest testing configuration
- `frontend/eslint.config.js` - ESLint with Prettier
- `frontend/.prettierrc` - Code formatting rules
- `frontend/.env` - Supabase environment variables
- `src/app/contexts/AuthContext.tsx` - Auth context provider (89 lines)
- `src/app/components/ProtectedRoute.tsx` - Route protection
- `src/app/components/auth/LoginForm.tsx` - Login UI
- `src/app/components/auth/SignUpForm.tsx` - Registration UI
- `src/app/components/auth/SocialLoginButtons.tsx` - OAuth buttons
- `src/app/components/auth/AuthCallback.tsx` - OAuth callback handler
- `src/app/lib/supabaseClient.ts` - Supabase client + types
- `src/app/types/api.ts` - API type definitions
- `src/app/services/apiClient.ts` - API client with JWT auth
- `src/App.tsx` - Application routing setup
- `src/app/pages/HomePage.tsx` - Protected home page (update in this story)
- `src/test/setup.ts` - Test configuration
- `src/test/example.test.ts` - Example tests (passing)

**Warnings/Recommendations:**
- Ensure CORS is configured on FastAPI backend for frontend origin
- Test components with both authenticated and unauthenticated states
- Verify Supabase connection before integrating with grid components
- Use TypeScript strict mode - all props must be typed, no implicit any

**No Technical Debt from Story 3-1**
- All acceptance criteria met
- Production build passing
- Tests configured and passing
- Clean foundation for story 3-2

━━━━━━━━━━━━━━━━━━━━━━━

## Dev Agent Record

### Context Reference

- Context file: `docs/sprint-artifacts/stories/3-2-build-responsive-vehicle-grid-component.context.xml` (generated 2026-01-04)

### Agent Model Used

Claude Opus 4.5 (glm-4.7)

### Debug Log References

### Completion Notes List

### Completion Notes

**Updated:** 2026-01-04 (Enhanced via SCAMPER Analysis)
**Definition of Done:** Story document refined with three elicitation methods: Journey Mapping, Six Thinking Hats, and SCAMPER.

**Elicitation Methods Applied:**
1. ✅ Journey Mapping: Revealed mobile pain points (small images, match score visibility, hover info loss)
2. ✅ Six Thinking Hats: Identified risks of over-engineering, benefits of iterative approach, opportunity to split
3. ✅ SCAMPER: Applied 4 creative enhancements (3-column grid, Otto's Pick badge, compare button, variant prop)

**Story Split Decision (from Six Thinking Hats):**
After applying Six Thinking Hats elicitation method, the original Story 3-2 (34 tasks, 12 ACs) was split into two stories to reduce complexity and enable iterative development:

**Story 3-2 (This Story - Core):**
- 9 acceptance criteria (AC1-AC9)
- 24 implementation tasks (3-2.1 through 3-2.24)
- 14 components, hooks, and utilities
- Focus: Solid responsive grid with progressive disclosure for mobile-first UX
- Success criteria: Grid displays, responsive works, progressive disclosure functional, Lighthouse score >90

**Story 3-3 (NEW - Enhanced):**
- 3 acceptance criteria (AC10-AC12 from original)
- 12 implementation tasks (3-2.25 through 3-2.34 from original)
- 6 advanced components and hooks
- Focus: Gesture support, viewed tracking, smart match score display
- Dependencies: Story 3-2 complete, user feedback collected
- Success criteria: Gestures work smoothly, tracking accurate, users delighted

**SCAMPER Enhancements Applied (2026-01-04):**

| Enhancement | SCAMPER Letter | ACs Updated | Tasks Extended | Impact |
|-------------|---------------|-------------|----------------|--------|
| **3-Column Desktop Grid** | Modify | AC1 | 3-2.10, 3-2.16 | Better modern screen utilization |
| **Otto's Pick Badge (95%+)** | Adapt | AC4, AC5 | 3-2.4 | Differentiates top-tier matches |
| **Add to Compare Button** | Combine | AC4 | 3-2.9 | Quick comparison action |
| **VehicleCard Variant Prop** | Put to Other Uses | - | 3-2.3 | Future-proofing for reuse |

**Otto AI Integration Decision:**

**Story 3-2 (Core):**
- ✅ Thumbs up/down buttons send feedback to backend API
- ✅ Add to compare button adds to local comparison buffer
- ✅ Visual indicator: "Comparing: 2 vehicles"
- ❌ NO Otto WebSocket integration (deferred to keep story focused)

**Story 3-6 (Comparison Tools):**
- ✅ Build comparison modal with side-by-side table
- ✅ Add Otto WebSocket integration for compare context
- ✅ Otto provides conversational analysis: "Comparing [A] vs [B]. Want me to highlight the differences?"
- ✅ User can chat: "Focus on range and price" → Otto responds intelligently

**Rationale:** This hybrid approach keeps Story 3-2 focused on visual grid implementation while setting up Story 3-6 for the full conversational comparison experience that showcases Otto's true value.

**What Was Enhanced (Story 3-2):**

**Story 3-2 (This Story - Core):**
- 9 acceptance criteria (AC1-AC9)
- 24 implementation tasks (3-2.1 through 3-2.24)
- 14 components, hooks, and utilities
- Focus: Solid responsive grid with progressive disclosure for mobile-first UX
- Success criteria: Grid displays, responsive works, progressive disclosure functional, Lighthouse score >90

**Story 3-3 (NEW - Enhanced):**
- 3 acceptance criteria (AC10-AC12 from original)
- 12 implementation tasks (3-2.25 through 3-2.34 from original)
- 6 advanced components and hooks
- Focus: Gesture support, viewed tracking, smart match score display
- Dependencies: Story 3-2 complete, user feedback collected
- Success criteria: Gestures work smoothly, tracking accurate, users delighted

**Elicitation Methods Applied:**
1. ✅ Journey Mapping: Revealed mobile pain points (small images, match score visibility, hover info loss)
2. ✅ Six Thinking Hats: Identified risks of over-engineering, benefits of iterative approach, opportunity to split

**What Was Enhanced (Story 3-2):**
- Added AC9: Progressive Disclosure for mobile information density
- Added task 3-2.23: ExpandableVehicleCard component
- Added task 3-2.24: Collapse/expand animations
- Mobile-first UX: 16:9 aspect ratio images, tap-to-expand
- Glass-morphism design system throughout

**What Was Moved to Story 3-3:**
- AC10-AC12: Gesture Support, Viewed Tracking, Smart Match Score Display
- Tasks 3-2.25 to 3-2.34: Gesture implementation, viewport detection, tooltip
- Components: MatchScoreProgress, MatchScoreTooltip, ViewedBadge, useViewedTracking
- Dependencies: @use-gesture/react, Popper.js

**Rationale for Split:**
- Faster time-to-market for core grid functionality
- User feedback before investing in advanced features
- Reduced risk of over-engineering unproven UX patterns
- Performance first: validate Lighthouse score >90 before adding complexity
- Clearer Definition of Done for each story

**Next Steps:**
1. Run `/bmad:bmm:workflows:story-context 3-2` to generate technical context XML
2. Story moves to "ready-for-dev" status after context generation
3. Implementation begins via `/bmad:bmm:workflows:dev-story 3-2`
4. After 3-2 complete and tested, create Story 3-3 for advanced features

### File List

**Files to Create (14 components, hooks, and utilities):**

**Core Components (11):**
- `frontend/src/components/vehicle-grid/VehicleGrid.tsx` - Main grid container
- `frontend/src/components/vehicle-grid/VehicleCard.tsx` - Individual vehicle card
- `frontend/src/components/vehicle-grid/ExpandableVehicleCard.tsx` - Progressive disclosure variant (NEW from journey mapping)
- `frontend/src/components/vehicle-grid/MatchScoreBadge.tsx` - Circular score indicator badge
- `frontend/src/components/vehicle-grid/VehicleSpecs.tsx` - Specs display (mileage, range)
- `frontend/src/components/vehicle-grid/PriceDisplay.tsx` - Price with savings
- `frontend/src/components/vehicle-grid/FeatureTags.tsx` - Feature pills
- `frontend/src/components/vehicle-grid/FavoriteButton.tsx` - Heart icon toggle
- `frontend/src/components/vehicle-grid/ActionButtons.tsx` - More/Less like buttons
- `frontend/src/components/vehicle-grid/VehicleCardSkeleton.tsx` - Loading skeleton
- `frontend/src/components/vehicle-grid/VehicleGridErrorBoundary.tsx` - Error handling

**Custom Hooks (1):**
- `frontend/src/components/vehicle-grid/useVehicleGrid.ts` - Data fetching hook

**Utilities (1):**
- `frontend/src/styles/glass.ts` - Glass-morphism design tokens

**Types (1):**
- `frontend/src/types/vehicle.ts` - Vehicle type definitions (extend api.ts)

**Plus unit tests and visual regression tests for all components**

**Files to Modify:**
- `frontend/src/app/pages/HomePage.tsx` - Add VehicleGrid (created in Story 3-1)
- `frontend/src/types/api.ts` - Extend Vehicle types (created in Story 3-1)
- `frontend/package.json` - Add Framer Motion (created in Story 3-1)
- `docs/sprint-artifacts/sprint-status.yaml` - Already marked as drafted

**Existing Files from Story 3-1 (Reuse):**
- All authentication components (LoginForm, SignUpForm, SocialLoginButtons, etc.)
- AuthContext and useAuth() hook
- API client with JWT authentication
- TypeScript type definitions
- Testing infrastructure (Vitest, React Testing Library)

## Change Log

**2026-01-04**: Story created via create-story workflow (refresh mode)
- Refreshed requirements context with latest tech-spec-epic-3.md
- Incorporated Story 3-1 completion learnings with actual file paths
- Updated frontend version references (React 19.2.0, TS 5.9.3, Vite 7.2.4)
- Enhanced references with complete source citations
- Verified alignment with PRD and UX design specifications
- Ready for story-context generation

**2026-01-04**: Enhanced via Advanced Elicitation - Journey Mapping method
- Applied Journey Mapping elicitation to analyze cross-device user experience
- Added AC9: Progressive Disclosure based on journey insights
- Added 2 new implementation tasks (3-2.23, 3-2.24) for expandable cards
- Created ExpandableVehicleCard component for mobile-first UX
- Enhanced with mobile considerations: 16:9 aspect ratio, tap-to-expand

**2026-01-04**: Split via Six Thinking Hats analysis
- Applied Six Thinking Hats elicitation method (White, Red, Black, Yellow, Green, Blue)
- Identified risks: 34 tasks too complex, potential performance issues, state management challenges
- Decision: Split Story 3-2 into Core (this story) + Enhanced (new Story 3-3)
- Moved 12 tasks (3-2.25 to 3-2.34) and 6 components to Story 3-3
- Moved AC10-AC12 (Gesture Support, Viewed Tracking, Smart Match Score) to Story 3-3
- Rationale: Faster time-to-market, user feedback first, reduced over-engineering risk
- Current scope: 9 ACs, 24 tasks, 14 components - manageable for single sprint
- Success criteria: Lighthouse score >90 before adding advanced features

**2026-01-04**: Enhanced via SCAMPER creative analysis
- Applied SCAMPER elicitation method (Substitute, Combine, Adapt, Modify, Put to Other Uses, Eliminate, Reverse)
- **Modify (AC1, 3-2.10, 3-2.16):** Changed desktop from 4-column to 3-column grid for modern screens
- **Adapt (AC4, AC5, 3-2.4):** Added "Otto's Pick" badge for 95%+ matches (star icon with cyan glow)
- **Combine (AC4, 3-2.9):** Added "Add to compare" button to ActionButtons (Otto integration deferred to Story 3-6)
- **Put to Other Uses (3-2.3):** Added VehicleCard variant prop for future reuse in comparison/favorites views
- **Eliminate:** Analysis confirmed no elements should be removed - all serve validated user needs
- **Reverse:** Rejected footer match scores, price-first display, low-match-first loading (violates visual-first pattern)
- Otto AI integration decision: Keep Story 3-2 focused on visual grid, defer conversational comparison to Story 3-6

**Story 3-3 Preview** (to be created after 3-2 complete):
- Will include: Gesture Support (swipe-to-favorite, swipe-to-dismiss, pull-to-refresh)
- Will include: Viewed State Tracking (Intersection Observer, progress indicator)
- Will include: Smart Match Score Display (progress bar, tooltip, breakdown)
- Dependencies: Story 3-2 complete, user feedback collected, performance validated
