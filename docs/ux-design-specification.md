# Otto.AI UX Design Specification

**Implementation Status:** ⚠️ PARTIAL (5/13 stories)
**Last Verified:** 2026-01-19
**Note:** Epic 3 (Dynamic Vehicle Grid Interface) has 5/13 stories implemented. React 19.2.0 + TypeScript 5.9.3 frontend with 91 files (~2,283 lines) verified in codebase.

**Implemented Stories:**
- ✅ 3-1: Real-time Grid Infrastructure (React + TypeScript setup)
- ✅ 3-2: Responsive Vehicle Grid (3/2/1 column layout, 46 tests)
- ⚠️ 3-3/3-3b: Dynamic Cascade Updates (partial - SSE migration)
- ✅ 3-4: Vehicle Details Modal (image carousel, comprehensive tests)
- ✅ 3-5: Real-time Availability Status (status badges, notifications)
- ✅ 3-6: Vehicle Comparison Tools (table view, sessionStorage)
- ✅ 3-7: Grid Filtering & Sorting (multi-select, effective_price)

**Remaining Stories (3-8 through 3-13):** 📋 PLANNED

_Created on 2025-11-29 by BMad_
_Generated using BMad Method - Create UX Design Workflow v1.0_

---

## Executive Summary

Otto.AI is a revolutionary AI-powered vehicle discovery platform that transforms car shopping from transactional searching into conversational discovery. The platform serves dual customer groups:

**For Buyers**: An engaging, conversational experience where Otto AI acts as a knowledgeable friend who remembers preferences and builds genuine relationships through natural conversation.

**For Sellers**: Intelligence-rich leads with conversation insights, buyer psychology, and recommended sales approaches based on actual user interactions.

The core innovation replaces traditional "search and filter" interfaces with persistent memory conversations, creating a more human vehicle discovery experience while generating superior sales intelligence for the automotive marketplace.

**Key Differentiators:**
- Conversational AI with persistent memory via Zep Cloud
- Real-time market intelligence via Groq compound-beta
- Dynamic vehicle grid that updates based on conversation context
- One-click reservation system with social proof
- Comprehensive lead intelligence for sellers

**Platform Strategy:** Responsive web application built on React 19.2.0 + TypeScript 5.9.3 + Vite 7.2.4, supporting desktop, tablet, and mobile experiences with WCAG 2.1 AA accessibility compliance.

---

## 1. Design System Foundation

### 1.1 Design System Choice

**Selected System:** Custom Design System built on Tailwind CSS + Radix UI primitives

**Rationale:**
- The Otto.AI visual identity requires a distinctive glass-morphism aesthetic that isn't achievable with off-the-shelf component libraries
- Tailwind CSS provides the utility-first foundation for precise control over transparency, blur, and gradient treatments
- Radix UI provides accessible, unstyled primitives for interactive components (dialogs, popovers, dropdowns)
- Framer Motion handles the cascade animations and micro-interactions

**Design Tokens:**
```css
:root {
  /* Glass-morphism Base */
  --glass-bg-light: rgba(255, 255, 255, 0.85);
  --glass-bg-medium: rgba(255, 255, 255, 0.70);
  --glass-bg-dark: rgba(30, 41, 59, 0.80);
  --glass-blur: 20px;
  --glass-border: rgba(255, 255, 255, 0.18);

  /* Otto AI Accent */
  --otto-primary: #0EA5E9; /* Sky-500 */
  --otto-primary-glow: rgba(14, 165, 233, 0.4);
  --otto-gradient-start: #06B6D4; /* Cyan-500 */
  --otto-gradient-end: #3B82F6; /* Blue-500 */

  /* Match Score Colors */
  --match-excellent: #22C55E; /* Green-500 - 90%+ */
  --match-good: #84CC16; /* Lime-500 - 80-89% */
  --match-fair: #EAB308; /* Yellow-500 - 70-79% */
  --match-low: #F97316; /* Orange-500 - below 70% */

  /* Surface Hierarchy */
  --surface-base: #F8FAFC; /* Slate-50 */
  --surface-elevated: rgba(255, 255, 255, 0.95);
  --surface-modal: rgba(255, 255, 255, 0.92);

  /* Text */
  --text-primary: #0F172A; /* Slate-900 */
  --text-secondary: #475569; /* Slate-600 */
  --text-muted: #94A3B8; /* Slate-400 */
  --text-on-dark: #F8FAFC;

  /* CTA Colors */
  --cta-reserve: #DC2626; /* Red-600 */
  --cta-reserve-hover: #B91C1C;
  --cta-secondary: #475569;

  /* Shadows */
  --shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.08);
  --shadow-card: 0 4px 16px rgba(0, 0, 0, 0.06);
  --shadow-modal: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
```

---

## 2. Core User Experience

### 2.1 Defining Experience

**Primary Interface Pattern:** Split-Panel Conversational Discovery

The Otto.AI experience centers on a **persistent conversation companion** model where:

1. **Main Content Area (Left 70%):** Dynamic vehicle grid with cascade updates
2. **Companion Panel (Right 30%):** Contextual panels that adapt based on user journey:
   - New Arrivals sidebar
   - Community Activity feed
   - Market Insights
   - Otto AI Concierge (floating, expandable)

**Key Experience Principles:**

1. **Ambient Intelligence:** The vehicle grid responds to conversation without requiring explicit search actions
2. **Progressive Disclosure:** Information reveals naturally as users explore
3. **Social Proof Integration:** Real-time community activity creates urgency and trust
4. **Conversational Memory:** Otto remembers and references previous interactions naturally

### 2.2 Novel UX Patterns

**Pattern 1: Dynamic Cascade Discovery**
- As users chat with Otto, the vehicle grid updates with smooth top-to-bottom cascade animations
- Cards enter with subtle scale and opacity transitions (0.3s ease-out)
- Removed cards fade and compress before unmounting
- Match percentages update in real-time with color transitions

**Pattern 2: Floating Otto Concierge**
- Semi-transparent floating chat widget (bottom-right)
- Expands to full conversation view on interaction
- Otto avatar with subtle breathing animation (pulsing glow)
- Glass-morphism container with cyan/blue gradient border

**Pattern 3: Vehicle Detail Modal with Context Preservation**
- Opens as overlay preserving grid visibility (blurred background)
- Image carousel with thumbnail navigation
- Side panel with Otto's contextual recommendation
- Social proof indicators (viewers, offers, reservation status)

**Pattern 4: Contextual Quick Filters**
- Pill-style filter chips below hero section
- Icons + labels for common categories (SUVs, Electric, Luxury, Under $50k)
- Active state with filled background and subtle glow
- Horizontal scroll on mobile with fade indicators

---

## 3. Visual Foundation

### 3.1 Color System

**Primary Palette - Ocean Technology:**

| Color | Hex | Usage |
|-------|-----|-------|
| Otto Blue | #0EA5E9 | Primary brand, Otto avatar, links |
| Otto Cyan | #06B6D4 | Gradient accents, highlights |
| Slate 900 | #0F172A | Primary text, headings |
| Slate 600 | #475569 | Secondary text, labels |
| Slate 50 | #F8FAFC | Background base |

**Accent Palette - Status & Feedback:**

| Color | Hex | Usage |
|-------|-----|-------|
| Reserve Red | #DC2626 | CTA buttons, urgent actions |
| Match Green | #22C55E | High match scores (90%+) |
| Savings Green | #16A34A | Price savings indicators |
| Warning Amber | #F59E0B | Limited availability |

**Glass-morphism Specifications:**

```css
/* Light Glass Panel */
.glass-light {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

/* Dark Glass Panel (Otto Chat) */
.glass-dark {
  background: linear-gradient(135deg,
    rgba(30, 41, 59, 0.90) 0%,
    rgba(15, 23, 42, 0.95) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 40px rgba(14, 165, 233, 0.1);
}

/* Modal Overlay Glass */
.glass-modal {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(24px);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
```

---

## 4. Design Direction

### 4.1 Chosen Design Approach

**Direction: "Intelligent Clarity"**

A design language that balances:
- **Premium Automotive Aesthetics:** Clean lines, generous whitespace, high-quality imagery
- **AI-Native Interface:** Subtle animations, responsive feedback, ambient intelligence
- **Approachable Technology:** Warm gradients, friendly Otto persona, conversational tone

**Key Visual Characteristics:**

1. **Layered Depth:** Multiple glass surfaces create visual hierarchy
2. **Soft Geometry:** Rounded corners (8px cards, 12px modals, 24px pills)
3. **Subtle Motion:** 200-400ms transitions, spring physics for interactive elements
4. **Information Density:** Rich data presentation without overwhelming

**Typography Scale:**
```css
/* Headings - Inter */
--heading-1: 700 48px/1.1 'Inter';    /* Hero titles */
--heading-2: 600 32px/1.2 'Inter';    /* Section headers */
--heading-3: 600 20px/1.3 'Inter';    /* Card titles */
--heading-4: 500 16px/1.4 'Inter';    /* Subsections */

/* Body - Inter */
--body-large: 400 18px/1.6 'Inter';   /* Primary content */
--body-base: 400 16px/1.5 'Inter';    /* Standard text */
--body-small: 400 14px/1.5 'Inter';   /* Secondary info */
--caption: 500 12px/1.4 'Inter';      /* Labels, badges */
```

---

## 5. User Journey Flows

### 5.1 Critical User Paths

**Flow 1: First-Time Discovery**
```
Landing → Quick Filter Selection → Grid Updates →
Vehicle Card Hover → Detail Modal → Reserve CTA
```

**Flow 2: Conversational Search**
```
Otto Chat Open → Natural Language Query →
Preferences Extracted → Grid Cascade Update →
Otto Recommendation → Vehicle Selection → Reserve
```

**Flow 3: Return User with Memory**
```
Landing (Recognized) → Otto Greeting with Context →
"Last time you liked..." Suggestions →
Preference Refinement → Updated Results → Action
```

**Flow 4: Vehicle Comparison**
```
Select Vehicle 1 → Add to Compare →
Select Vehicle 2 → Comparison View Opens →
Feature Analysis → Otto Recommendation → Decision
```

---

## 6. Component Library

### 6.1 Component Strategy

**Atomic Design Hierarchy:**

**Atoms:**
- Badge (match percentage, status, feature tags)
- Button (primary, secondary, ghost, icon)
- Input (text, search with icon)
- Avatar (user, Otto with glow)
- Icon (Lucide React icons)

**Molecules:**
- FilterPill (icon + label + active state)
- PriceDisplay (current + savings + original)
- MatchScore (circular badge with percentage)
- VehicleSpec (icon + label + value)
- ChatMessage (avatar + bubble + timestamp)

**Organisms:**
- VehicleCard (image, title, specs, price, match, actions)
- VehicleDetailModal (carousel, specs, Otto recommendation, CTA)
- OttoConversation (expandable chat with history)
- FilterBar (scrollable pill container)
- SidebarPanel (glass container with sections)

**Templates:**
- DiscoveryPage (header, filters, grid, sidebars, floating Otto)
- VehicleDetailOverlay (modal with preserved background)
- SellerDashboard (navigation, analytics, lead cards)

---

## 7. UX Pattern Decisions

### 7.1 Consistency Rules

**Interaction States:**
```css
/* Hover - Subtle lift */
.interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
  transition: all 0.2s ease;
}

/* Active/Pressed - Slight scale */
.interactive:active {
  transform: scale(0.98);
}

/* Focus - Visible ring */
.interactive:focus-visible {
  outline: 2px solid var(--otto-primary);
  outline-offset: 2px;
}
```

**Loading States:**
- Skeleton screens with gradient shimmer animation
- Content placeholder maintains layout stability
- 1.5s animation cycle, left-to-right sweep

**Empty States:**
- Illustrated graphics (minimal, line-art style)
- Clear messaging with suggested action
- Otto offers to help find alternatives

**Error States:**
- Red accent border (not full background)
- Icon + message + retry action
- Graceful degradation with cached content

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

**Breakpoints:**
```css
--mobile: 375px;      /* Minimum supported */
--tablet: 768px;      /* Sidebar collapses */
--desktop: 1024px;    /* Full layout */
--wide: 1440px;       /* Maximum content width */
```

**Mobile Adaptations:**
- Vehicle grid: 1 column, full-width cards
- Sidebars: Collapse to bottom sheet drawers
- Otto Chat: Full-screen overlay mode
- Filters: Horizontal scroll, larger touch targets

**Accessibility Requirements (WCAG 2.1 AA):**
- Color contrast minimum 4.5:1 for text
- Touch targets minimum 44x44px
- Focus indicators visible on all interactive elements
- Screen reader announcements for dynamic content
- Reduced motion support via `prefers-reduced-motion`

---

## 9. Implementation Guidance

### 9.1 Completion Summary

**Component Priority for MVP:**

| Priority | Component | Complexity |
|----------|-----------|------------|
| P0 | VehicleCard | Medium |
| P0 | VehicleGrid | Medium |
| P0 | OttoChatWidget | High |
| P0 | SearchInput | Low |
| P1 | FilterPillBar | Medium |
| P1 | VehicleDetailModal | High |
| P1 | SidebarPanels | Medium |
| P2 | ComparisonView | High |
| P2 | MatchScoreBadge | Low |

**Animation Library:** Framer Motion
```typescript
// Cascade animation preset
const cascadeVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.05,
      duration: 0.3,
      ease: [0.25, 0.1, 0.25, 1]
    }
  }),
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } }
};
```

**Glass-morphism Tailwind Config:**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      backdropBlur: {
        'glass': '20px',
      },
      colors: {
        'glass-light': 'rgba(255, 255, 255, 0.85)',
        'glass-border': 'rgba(255, 255, 255, 0.18)',
        'otto-blue': '#0EA5E9',
        'otto-cyan': '#06B6D4',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.08)',
        'glass-dark': '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(14, 165, 233, 0.1)',
      }
    }
  }
}
```

---

## Appendix

### Related Documents

- Product Requirements: `{{prd_file}}`
- Product Brief: `{{brief_file}}`
- Brainstorming: `{{brainstorm_file}}`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: {{color_themes_html}}
  - Interactive HTML showing all color theme options explored
  - Live UI component examples in each theme
  - Side-by-side comparison and semantic color usage

- **Design Direction Mockups**: {{design_directions_html}}
  - Interactive HTML with 6-8 complete design approaches
  - Full-screen mockups of key screens
  - Design philosophy and rationale for each direction

### Optional Enhancement Deliverables

_This section will be populated if additional UX artifacts are generated through follow-up workflows._

<!-- Additional deliverables added here by other workflows -->

### Next Steps & Follow-Up Workflows

This UX Design Specification can serve as input to:

- **Wireframe Generation Workflow** - Create detailed wireframes from user flows
- **Figma Design Workflow** - Generate Figma files via MCP integration
- **Interactive Prototype Workflow** - Build clickable HTML prototypes
- **Component Showcase Workflow** - Create interactive component library
- **AI Frontend Prompt Workflow** - Generate prompts for v0, Lovable, Bolt, etc.
- **Solution Architecture Workflow** - Define technical architecture with UX context

### Version History

| Date     | Version | Changes                         | Author        |
| -------- | ------- | ------------------------------- | ------------- |
| 2025-11-29 | 1.0     | Initial UX Design Specification | BMad |
| 2026-01-19 | 1.1     | Updated implementation status to PARTIAL (5/13 stories). Corrected platform from Next.js 14 to React 19.2.0 + Vite 7.2.4 based on code verification. Added implemented story details. | Winston (Architect) |

---

_This UX Design Specification was created through collaborative design facilitation, not template generation. All decisions were made with user input and are documented with rationale._