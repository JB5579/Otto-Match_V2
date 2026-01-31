# Story 3-7: Implementation Roadmap - Intelligent Grid Filtering and Sorting

**Story:** 3.7 - Add Intelligent Grid Filtering and Sorting
**Epic:** Epic 3 - Dynamic Vehicle Grid Interface
**Date:** 2026-01-19
**Status:** Backend Complete ✅ - Frontend Ready
**Estimated Effort:** ~9 hours remaining (Backend complete)
**Complexity:** Medium-High (6 new components, 2 modified, 6 test files)

---

## Executive Summary

This roadmap breaks down Story 3-7 into **5 sequential phases** with clear dependencies and validation checkpoints. Each phase builds upon the previous one, starting with foundational architecture and ending with polish/testing.

**Key Architectural Decision:** Follow the ComparisonContext pattern from Story 3-6 for consistency.

---

## Implementation Overview

### Phase Structure

| Phase | Focus | Components | Files | Est. Time |
|--------|-------|------------|-------|-----------|
| **Phase 1** | Foundation | FilterContext, types | 2 new | 1.5h |
| **Phase 2** | Filter UI | FilterBar, SortDropdown | 2 new | 2h |
| **Phase 3** | Filter Modal | FilterModal, FilterChips | 2 new | 2.5h |
| **Phase 4** | Integration | VehicleContext, SSE, EmptyState | 2 mod, 1 new | 1.5h |
| **Phase 5** | Testing & Polish | All test files, validation | 6 new | 2-3h |

**Total Estimated Time:** 9.5-10.5 hours

---

## Phase 0: Backend API Updates ✅ COMPLETE (2026-01-19)

**Objective:** Update backend APIs to support multi-select filters and handle nullable prices.

**Completed Tasks:**
- ✅ Verified asking_price, estimated_price, auction_forecast, effective_price columns exist in database
- ✅ Updated semantic_search_api.py with multi-select support (makes, vehicle_types)
- ✅ Updated vehicle_database_service.py to use .in_() clause for multi-select
- ✅ Updated vehicles_api.py with comma-separated multi-select parameters
- ✅ Implemented effective_price sorting with NULL handling
- ✅ Updated database schema documentation (database_schema.sql)
- ✅ Removed unsupported features: efficiency sort, features filter

**API Changes:**
1. SearchFilters model - Added makes: List[str] and vehicle_types: List[str]
2. Vehicles API - Added makes, vehicle_types query parameters (comma-separated)
3. Hybrid search - Uses PostgreSQL ANY clause for efficient multi-select
4. Price handling - Uses effective_price (COALESCE of asking > auction > estimated)

**Files Modified:**
- src/api/semantic_search_api.py (multi-select filters)
- src/semantic/vehicle_database_service.py (.in_() clause, effective_price)
- src/api/vehicles_api.py (comma-separated params, sorting)
- src/services/database_schema.sql (documentation)

**Frontend Can Now:**
- Send multi-select makes: ?makes=Toyota,Honda,Ford
- Send multi-select vehicle types: ?vehicle_types=SUV,Sedan
- Filter by price ranges (excludes NULL prices automatically)
- Sort by price with NULL values placed at end

**Remaining Work:** Frontend implementation (Phases 1-5)

---

## Phase 1: Foundation - FilterContext and Types (CRITICAL PATH)

**Objective:** Establish the core state management architecture that all other components depend on.

### Dependencies
- None (start here)

### Tasks

#### 1.1 Create Filter Types
**File:** `frontend/src/types/filters.ts`

```typescript
export interface FilterState {
  priceRange?: [number, number];  // [$0, $100000]
  makes?: string[];                  // ["Toyota", "Honda", "Ford"]
  vehicleTypes?: string[];           // ["SUV", "Sedan", "Truck", "EV", "Hybrid"]
  yearRange?: [number, number];     // [2015, 2024]
  maxMileage?: number;               // 0 - 200000
  // REMOVED: features?: string[]; (no database support) - 2026-01-19
}

export type SortOption =
  | "relevance"
  | "price-asc"
  | "price-desc"
  | "mileage-asc"
  | "year-desc"
  // REMOVED: "efficiency-desc" (no database support) - 2026-01-19

export type SortDirection = "asc" | "desc";

export interface FilterOptions {
  priceRange?: { min: number; max: number };
  makes?: string[];
  vehicleTypes?: string[];
  yearRange?: { min: number; max: number };
  maxMileage?: number;
  // REMOVED: features?: string[]; (no database support) - 2026-01-19
}
```

#### 1.2 Create FilterContext
**File:** `frontend/src/context/FilterContext.tsx`

**Key Patterns from Story 3-6:**
- sessionStorage with 30min expiry
- Context provider pattern
- useFilters hook
- STORAGE_KEY, STORAGE_EXPIRY_MS constants

**Implementation Requirements:**
```typescript
// State structure
interface FilterContextValue {
  filters: FilterState;
  sortBy: SortOption;
  applyFilters: (filters: FilterState) => void;
  removeFilter: (key: keyof FilterState) => void;
  clearAllFilters: () => void;
  setSort: (sort: SortOption) => void;
  activeFilterCount: number;
  filteredVehicles?: Vehicle[];
}

// Storage pattern from ComparisonContext
const STORAGE_KEY = 'otto_filters';
const STORAGE_EXPIRY_MS = 30 * 60 * 1000;

// Must integrate with VehicleContext later
```

**Acceptance Criteria:**
- [ ] Context compiles without errors
- [ ] useFilters hook exports correctly
- [ ] sessionStorage persists filters with 30min expiry
- [ ] activeFilterCount calculates correctly

**Validation:**
```bash
cd frontend
npm run type-check
```

---

## Phase 2: Filter Bar and Sort UI

**Objective:** Create the user-facing filter controls visible above the vehicle grid.

### Dependencies
- Phase 1 complete (FilterContext exists)

### Tasks

#### 2.1 Create FilterBar Component
**File:** `frontend/src/components/filters/FilterBar.tsx`

**UI Requirements:**
- Glass-morphism styled bar
- Three buttons: Filter Chips (opens modal), Sort Dropdown, Clear All
- Active filter count display
- Responsive: horizontal scroll on mobile, full width on desktop
- Clear All button hidden when no active filters

**Component Structure:**
```tsx
<div className="filter-bar glass">
  <button onClick={openFilterModal}>Filter Chips</button>
  <SortDropdown />
  <button onClick={clearAllFilters} hidden={!hasFilters}>
    Clear All ({activeCount})
  </button>
</div>
<div className="filter-chips horizontal-scroll">
  {/* FilterChips component renders here in Phase 3 */}
</div>
```

**Acceptance Criteria:**
- [ ] Renders above vehicle grid
- [ ] Glass-morphism styling consistent
- [ ] Responsive layout works
- [ ] Clear All button shows/hides correctly
- [ ] Active filter count accurate

#### 2.2 Create SortDropdown Component
**File:** `frontend/src/components/filters/SortDropdown.tsx`

**UI Requirements:**
- Radix UI Dropdown or custom dropdown
- Options: Relevance, Price, Mileage, Year, Efficiency
- Otto explanation text below selection
- ARIA role="combobox"
- Direction toggle for Price/Mileage (asc/desc)

**Sort Options:**
```typescript
const SORT_OPTIONS = [
  { value: "relevance", label: "Relevance", icon: "sparkles" },
  { value: "price-asc", label: "Price: Low to High", icon: "arrow-up" },
  { value: "price-desc", label: "Price: High to Low", icon: "arrow-down" },
  { value: "mileage-asc", label: "Lowest Mileage", icon: "gauge" },
  { value: "year-desc", label: "Newest First", icon: "calendar" },
  { value: "efficiency-desc", label: "Best MPGe/Range", icon: "zap" },
];
```

**Acceptance Criteria:**
- [ ] Dropdown displays all sort options
- [ ] Otto explanation displays ("Sorted by relevance to your preferences")
- [ ] ARIA attributes correct
- [ ] Keyboard navigation works
- [ ] Sort preference persists to sessionStorage
- [ ] Direction toggle appears for Price/Mileage

**Integration Points:**
- Calls `FilterContext.setSort()`
- Triggers VehicleContext re-sort via useFilters hook

---

## Phase 3: Filter Modal and Chips

**Objective:** Create the main filter UI and removable filter chips.

### Dependencies
- Phase 1 complete (FilterContext)
- Phase 2 complete (FilterBar exists)

### Tasks

#### 3.1 Create FilterModal Component
**File:** `frontend/src/components/filters/FilterModal.tsx`

**UI Requirements:**
- Modal with backdrop blur (reuse VehicleDetailModal pattern)
- Filter categories with controls:
  - **Price Range:** Dual-handle slider
  - **Make:** Multi-select dropdown with search
  - **Vehicle Type:** Checkbox group
  - **Year Range:** Dual-handle slider
  - **Mileage:** Single-handle slider
  - **Features:** Multi-select chips
- Apply Filters button (bottom-right)
- Cancel button (bottom-left)
- Selected count badges per category

**Component Structure:**
```tsx
<Dialog open={isOpen} onOpenChange={handleClose}>
  <div className="filter-modal glass">
    <div className="filter-header">
      <h2>Filters</h2>
      <button onClick={onClose}>✕</button>
    </div>

    <PriceRangeFilter />
    <MakeFilter />
    <VehicleTypeFilter />
    <YearRangeFilter />
    <MileageFilter />
    <FeaturesFilter />

    <div className="filter-footer">
      <button onClick={onCancel}>Cancel</button>
      <button onClick={applyFilters}>Apply Filters</button>
    </div>
  </div>
</Dialog>
```

**Slider Implementation Options:**
1. Use `rc-slider` if available
2. Create custom dual-handle slider
3. Use Radix UI Slider (if available)

**Acceptance Criteria:**
- [ ] Modal opens/closes correctly
- [ ] All filter categories render
- [ ] Multi-select works (Make, Features)
- [ ] Sliders have visual feedback
- [ ] Selected count badges accurate
- [ ] Apply Filters button triggers grid update
- [ ] Cancel button closes modal
- [ ] Escape key closes modal
- [ ] Backdrop click closes modal
- [ ] Focus trap within modal

#### 3.2 Create FilterChips Component
**File:** `frontend/src/components/filters/FilterChips.tsx`

**UI Requirements:**
- Horizontal scrollable row
- Removable pill chips
- Format: "Price: $20k-$40k", "Make: Toyota"
- Cyan glow border for active filters
- × button to remove

**Component Structure:**
```tsx
<div className="filter-chips horizontal-scroll">
  {filters.priceRange && (
    <FilterChip onRemove={() => removeFilter('priceRange')}>
      Price: ${formatPrice(filters.priceRange[0])} - ${formatPrice(filters.priceRange[1])}
    </FilterChip>
  )}
  {filters.makes?.map(make => (
    <FilterChip key={make} label={`Make: ${make}`} />
  ))}
  {/* ... other filters */}
</div>
```

**Acceptance Criteria:**
- [ ] Chips display for active filters
- [ ] × button removes individual filter
- [ ] Grid updates immediately on remove
- [ ] Chips reorder smoothly
- [ ] Horizontal scroll on mobile
- [ ] ARIA labels on × buttons
- [ ] Hide when no active filters

---

## Phase 4: Integration and Empty State

**Objective:** Connect filters to the vehicle grid and handle edge cases.

### Dependencies
- Phases 1-3 complete (all filter components exist)

### Tasks

#### 4.1 Modify VehicleContext
**File:** `frontend/src/context/VehicleContext.tsx` (MODIFY)

**Changes Required:**
1. Import FilterState and SortOption types
2. Add getFilteredVehicles() method:
   ```typescript
   getFilteredVehicles(
     vehicles: Vehicle[],
     filters: FilterState,
     sortBy: SortOption
   ): Vehicle[]
   ```
3. Apply filter logic:
   - Price range filter
   - Make inclusion filter
   - Vehicle type inclusion filter
   - Year range filter
   - Mileage max filter
   - Features inclusion filter (all features must match)
4. Apply sort logic:
   - Relevance: sortBy matchScore desc
   - Price-asc: sortBy price asc
   - Price-desc: sortBy price desc
   - Mileage-asc: sortBy mileage asc
   - Year-desc: sortBy year desc
   - Efficiency-desc: sortBy (mpge or range) desc

5. Memoize filtered list for performance

**Acceptance Criteria:**
- [ ] getFilteredVehicles() filters correctly
- [ ] getFilteredVehicles() sorts correctly
- [ ] Memoization prevents unnecessary recalculations
- [ ] Empty array returns when no vehicles match

#### 4.2 Modify useVehicleUpdates Hook
**File:** `frontend/src/hooks/useVehicleUpdates.ts` (MODIFY)

**Changes Required:**
1. Import FilterContext or useFilters hook
2. In SSE message handler, get current filters from FilterContext
3. Apply filters to new vehicle list before updating VehicleContext
4. Preserve filter state across SSE updates

**Implementation Pattern:**
```typescript
addEventListener('vehicle_update', (event) => {
  const { vehicles } = JSON.parse(event.data);

  // Get current filters from FilterContext
  const { filters, sortBy } = useFilters();

  // Apply filters and sort
  const filteredAndSorted = getFilteredVehicles(vehicles, filters, sortBy);

  // Update VehicleContext
  updateVehicles(filteredAndSorted);
});
```

**Acceptance Criteria:**
- [ ] Filters preserve when SSE updates arrive
- [ ] Only vehicles matching filters display
- [ } No infinite loops or re-renders

#### 4.3 Modify VehicleGrid
**File:** `frontend/src/components/vehicle-grid/VehicleGrid.tsx` (MODIFY)

**Changes Required:**
1. Import useFilters hook
2. Use filtered vehicles from FilterContext instead of raw vehicles
3. Handle empty state (zero vehicles)

**Implementation:**
```tsx
const { filters, sortBy } = useFilters();
const { vehicles, loading } = VehicleContext;

const displayVehicles = vehicles; // Already filtered/sorted by context
```

#### 4.4 Create EmptyState Component
**File:** `frontend/src/components/filters/FilterEmptyState.tsx` (NEW)

**UI Requirements:**
- Friendly message: "No vehicles match your filters"
- Illustration or icon
- CTA: "Clear All Filters" button
- Otto suggestion: "Try adjusting your filters to see more options"
- Glass-morphism styled panel

**Acceptance Criteria:**
- [ ] Displays when filtered vehicle count = 0
- [ ] Clear All Filters button prominent
- [ ] Otto suggestion displays
- [ ] No grid skeleton shown

---

## Phase 5: Testing and Validation

**Objective:** Ensure all components work correctly and meet acceptance criteria.

### Dependencies
- Phases 1-4 complete (all implementation done)

### Tasks

#### 5.1 Write FilterContext Unit Tests
**File:** `frontend/src/context/__tests__/FilterContext.test.tsx`

**Test Cases:**
- [ ] Filter state management (add, remove, clear)
- [ ] Sort preference state
- [ ] sessionStorage persistence (load, save, expiry)
- [ ] Filter merging with conversation preferences
- [ ] Active filter count calculation
- [ ] 80%+ code coverage

#### 5.2 Write FilterModal Unit Tests
**File:** `frontend/src/components/filters/__tests__/FilterModal.test.tsx`

**Test Cases:**
- [ ] Modal open/close
- [ ] Filter category rendering
- [ ] Multi-select behavior
- [ ] Slider interactions
- [ ] Apply Filters button
- [ ] Cancel button
- [ ] Keyboard navigation
- [ ] ARIA attributes

#### 5.3 Write FilterChips Unit Tests
**File:** `frontend/src/components/filters/__tests__/FilterChips.test.tsx`

**Test Cases:**
- [ ] Chip rendering for active filters
- [ ] Remove individual filter
- [ ] Chip reordering animation
- [ ] Hide when no filters
- [ ] ARIA labels

#### 5.4 Write Integration Tests
**File:** `frontend/src/components/filters/__tests__/FilterIntegration.test.tsx`

**Test Cases:**
- [ ] Apply filters → grid update
- [ ] Sort → grid reorder
- [ ] Filter + sort combination
- [ ] Clear all filters → reset
- [ ] Filter persistence across page reload
- [ ] Empty state for no results
- [ ] Filter + SSE update integration

#### 5.5 Write Visual Regression Tests
**Files:** Create snapshot tests for all filter components

**Test Breakpoints:**
- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px
- Wide: 1440px

**Components to Test:**
- [ ] FilterBar
- [ ] FilterModal
- [ ] FilterChips
- [ ] SortDropdown
- [ ] EmptyState

#### 5.6 Backend API Verification
**Action:** Verify backend supports filter/sort parameters

**Steps:**
1. Check `src/api/semantic_search_api.py`
2. Look for filter parameters in POST /api/search/semantic
3. Verify support for:
   - make, model, price_range, year_range, mileage_max, features
   - sort_by parameter
4. Test API endpoint with sample filters
5. Document any gaps if found

---

## Implementation Order (Step-by-Step)

### Week 1: Foundation (3.5h)

**Day 1 - Phase 1 (1.5h):**
1. Create `frontend/src/types/filters.ts` (30 min)
2. Create `frontend/src/context/FilterContext.tsx` (1h)
3. Test FilterContext compiles (10 min)

**Deliverable:** FilterContext and types complete

---

### Week 2: UI Components (4.5h)

**Day 2 - Phase 2 (2h):**
1. Create `FilterBar.tsx` (1h)
2. Create `SortDropdown.tsx` (1h)
3. Test basic rendering (10 min)

**Deliverable:** FilterBar and SortDropdown complete

**Day 3 - Phase 3 Part 1 (1.5h):**
1. Create `FilterModal.tsx` structure (1.5h)
2. Mock up filter category components (30 min)

**Deliverable:** FilterModal framework ready

---

### Week 3: Modal Components + Integration (4h)

**Day 4 - Phase 3 Part 2 + Phase 4 (2h):**
1. Complete FilterModal with all filter categories (1.5h)
2. Create `FilterChips.tsx` (30 min)
3. Modify VehicleContext.addFilterLogic (30 min)

**Deliverable:** All filter components complete

**Day 5 - Phase 4 Integration + Testing (2h):**
1. Modify useVehicleUpdates.ts (30 min)
2. Create FilterEmptyState.tsx (30 min)
3. Write initial tests (1h)

**Deliverable:** Integration complete, initial tests

---

### Week 4: Testing Completion (3h)

**Day 6 - Testing (3h):**
1. Complete all unit tests (2h)
2. Write integration tests (30 min)
3. Visual regression tests (30 min)

**Deliverable:** All tests passing

---

## File Creation Checklist

### New Files to Create (6 components, 6 tests, 1 types)

**Components:**
- [ ] `frontend/src/types/filters.ts`
- [ ] `frontend/src/context/FilterContext.tsx`
- [ ] `frontend/src/components/filters/FilterBar.tsx`
- [ ] `frontend/src/components/filters/SortDropdown.tsx`
- [ ] `frontend/src/components/filters/FilterModal.tsx`
- [ ] `frontend/src/components/filters/FilterChips.tsx`
- [ ] `frontend/src/components/filters/FilterEmptyState.tsx`

**Tests:**
- [ ] `frontend/src/context/__tests__/FilterContext.test.tsx`
- [ ] `frontend/src/components/filters/__tests__/FilterBar.test.tsx`
- [ ] `frontend/src/components/filters/__tests__/FilterModal.test.tsx`
- [ ] `frontend/src/components/filters/__tests__/FilterChips.test.tsx`
- [ ] `frontend/src/components/filters/__tests__/SortDropdown.test.tsx`
- [ ] `frontend/src/components/filters/__tests__/FilterIntegration.test.tsx`

### Files to Modify (2)

**Modified:**
- [ ] `frontend/src/context/VehicleContext.tsx` (add filter logic)
- [ ] `frontend/src/hooks/useVehicleUpdates.ts` (preserve filters)

---

## Dependency Graph

```
Phase 1: Foundation
├── FilterContext.tsx (NEW)
└── filters.ts (NEW)

Phase 2: Filter UI
├── FilterBar.tsx (NEW) ────────┐
└── SortDropdown.tsx (NEW)       │
                                    │
Phase 3: Modal + Chips              ↓
├── FilterModal.tsx (NEW) ◄─────┘
└── FilterChips.tsx (NEW)

Phase 4: Integration
├── VehicleContext.tsx (MODIFY) ◄───┐
├── useVehicleUpdates.ts (MODIFY) │
└── FilterEmptyState.tsx (NEW)     │
                                    │
Phase 5: Testing                  ↓
└── All test files (6 NEW) ────┘
```

---

## Validation Checkpoints

### After Phase 1
- [ ] TypeScript compiles: `npm run type-check`
- [ ] FilterContext story file updated with context reference

### After Phase 2
- [ ] FilterBar renders in story
- [ ] SortDropdown renders and changes state
- [ ] Both components integrated with FilterContext

### After Phase 3
- [ ] FilterModal opens/closes
- [ ] All filter categories render
- [ ] FilterChips display active filters

### After Phase 4
- [ ] Filters apply to VehicleGrid
- [ ] Empty state displays when zero results
- [ ] SSE updates preserve filters

### After Phase 5
- [ ] All unit tests pass: `npm test`
- [ ] Integration tests pass
- [ ] Visual regression tests pass
- [ ] Test coverage ≥80%

---

## Risk Mitigation

### Risk 1: Slider Component Complexity
**Risk:** Dual-handle sliders are complex to implement
**Mitigation:**
- Use `rc-slider` package if available
- Or create simplified range inputs (min/max text fields)
- Fallback to single-handle slider if dual-handle proves difficult

### Risk 2: Performance with Large Vehicle Sets
**Risk:** Filtering 50+ vehicles may cause lag
**Mitigation:**
- Memoize filtered vehicle list
- Debounce filter application (300ms)
- Consider virtual scrolling if >50 vehicles (react-window already in deps)

### Risk 3: SSE Update Conflicts
**Risk:** SSE updates may interfere with filter state
**Mitigation:**
- Read filter state before applying updates
- Always preserve filter state in SSE handler
- Test extensively with rapid SSE updates

### Risk 4: Filter/Sort Consistency
**Risk:** Filters and sorts may conflict or produce unexpected results
**Mitigation:**
- Apply filters FIRST, then sort
- Document sort behavior with active filters
- Add unit tests for edge cases

---

## Testing Strategy

### Unit Testing Approach
- Mock FilterContext for component tests
- Mock VehicleContext for integration tests
- Mock sessionStorage for persistence tests
- Test all edge cases (empty filters, all filters, invalid ranges)

### Integration Testing Approach
- Test full filter → sort → grid update flow
- Test filter persistence across page reload
- Test SSE update during active filters
- Test empty state scenarios

### Visual Regression Approach
- Snapshot tests for all components
- Compare across breakpoints
- Run on every PR (CI/CD)

### Accessibility Testing Approach
- axe-core for automated checks
- Manual keyboard navigation testing
- Screen reader testing (NVDA/VoiceOver)
- Color contrast validation

---

## Success Criteria

**Definition of Done Met When:**
- [ ] All 6 components created
- [ ] All 2 existing components modified
- [ ] All 6 test files created
- [ ] All tests passing (npm test)
- [ ] Test coverage ≥80%
- [ ] Visual regression tests pass
- [ ] Accessibility compliance (axe-core: 0 violations)
- [ ] Story file updated with implementation details
- [ ] Context reference added to story file
- [ ] sprint-status.yaml marked "done"

**Additional Validation:**
- [ ] Manual testing of filter/sort combinations
- [ ] SSE integration verified
- [ ] Performance benchmarks met (<500ms filter application)
- [ ] Bundle size within limits

---

## Next Steps

1. **Review this roadmap** and adjust if needed
2. **Start with Phase 1** (Foundation) - Create FilterContext and types
3. **Follow phases sequentially** - Each phase depends on the previous
4. **Validate at each checkpoint** - Don't proceed until phase passes validation
5. **Track progress** - Update story file with completion notes as you work

---

## References

- **Story File:** `docs/sprint-artifacts/stories/3-7-add-intelligent-grid-filtering-and-sorting.md`
- **Context File:** `docs/sprint-artifacts/stories/3-7-add-intelligent-grid-filtering-and-sorting.context.xml`
- **Previous Story:** Story 3-6 (Comparison Tools) - Pattern reference for sessionStorage, Context patterns
- **Architecture:** `docs/architecture.md` - Real-time communication, SSE patterns
- **Tech Spec:** `docs/sprint-artifacts/tech-spec-epic-3.md` - AC9 details, design tokens

---

**Prepared By:** BMAD Dev-Story Workflow
**Date:** 2026-01-19
**Status:** Backend Complete ✅ - Frontend Ready
