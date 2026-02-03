/**
 * Filter Bar Component for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Displays the filter controls above the vehicle grid with glass-morphism styling.
 *
 * Features:
 * - Filter chips button (opens filter modal)
 * - Sort dropdown (Relevance, Price, Mileage, Year, Efficiency)
 * - Clear all filters button (hidden when no active filters)
 * - Active filter count display
 * - Filter chips row (horizontal scroll on mobile)
 * - Responsive layout: full width on mobile, centered on desktop
 * - ARIA labels and keyboard handlers
 *
 * AC1: Filter Bar Component
 * AC5: Filter Chips Display
 * AC6: Clear All Filters
 * AC10: Accessibility Compliance
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SlidersHorizontal, X, Filter } from 'lucide-react';
import { useFilters } from '../../context/FilterContext';
import { SORT_LABELS, SORT_EXPLANATIONS } from '../../types/filters';
import SortDropdown from './SortDropdown';
import FilterChips from './FilterChips';

/**
 * Filter Bar Props
 */
interface FilterBarProps {
  /** Callback when filter button is clicked (opens filter modal) */
  onOpenFilterModal?: () => void;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * Filter Bar Component
 *
 * Displays above the vehicle grid with filter controls and active filter chips.
 * Glass-morphism styled bar with responsive layout.
 *
 * @example
 * <FilterBar onOpenFilterModal={() => setIsModalOpen(true)} />
 */
export const FilterBar: React.FC<FilterBarProps> = ({
  onOpenFilterModal,
  className = '',
}) => {
  const {
    activeFilterCount,
    filterChips,
    hasActiveFilters,
    sortBy,
    clearAllFilters,
  } = useFilters();

  const handleClearAll = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    clearAllFilters();
  };

  return (
    <div
      className={`filter-bar ${className}`}
      style={{
        // Glass-morphism styling (AC1: consistent with other UI elements)
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        borderRadius: '16px',
        padding: '16px',
        marginBottom: '16px',
        // Responsive layout (AC1: full width on mobile, centered on desktop)
        width: '100%',
        maxWidth: '100%',
      }}
    >
      {/* Main filter controls row */}
      <div
        className="filter-controls"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        {/* Filter chips button (AC1: opens filter modal) */}
        <motion.button
          type="button"
          onClick={onOpenFilterModal}
          className="filter-button"
          aria-label={`Open filters${activeFilterCount > 0 ? ` (${activeFilterCount} active)` : ''}`}
          style={{
            // Glass-morphism button with cyan glow when active
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            borderRadius: '12px',
            background: hasActiveFilters
              ? 'rgba(6, 182, 212, 0.15)' // Cyan tint when active
              : 'rgba(255, 255, 255, 0.9)',
            border: hasActiveFilters
              ? '1px solid rgba(6, 182, 212, 0.4)'
              : '1px solid rgba(255, 255, 255, 0.3)',
            boxShadow: hasActiveFilters
              ? '0 0 12px rgba(6, 182, 212, 0.25)'
              : '0 2px 8px rgba(0, 0, 0, 0.05)',
            color: hasActiveFilters ? '#0891b2' : '#374151',
            fontWeight: hasActiveFilters ? 600 : 500,
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          whileHover={{ scale: 1.02, boxShadow: hasActiveFilters ? '0 0 16px rgba(6, 182, 212, 0.35)' : '0 4px 12px rgba(0, 0, 0, 0.1)' }}
          whileTap={{ scale: 0.98 }}
        >
          <SlidersHorizontal size={18} strokeWidth={2} />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="filter-count"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: '20px',
                height: '20px',
                padding: '0 6px',
                borderRadius: '10px',
                background: 'rgba(6, 182, 212, 0.25)',
                color: '#0891b2',
                fontSize: '12px',
                fontWeight: 700,
              }}
            >
              {activeFilterCount}
            </motion.span>
          )}
        </motion.button>

        {/* Sort dropdown (AC1: sort dropdown) */}
        <SortDropdown />

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Clear all filters button (AC1 & AC6: hidden when no active filters) */}
        <AnimatePresence>
          {hasActiveFilters && (
            <motion.button
              type="button"
              onClick={handleClearAll}
              className="clear-filters-button"
              aria-label="Clear all filters"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 16px',
                borderRadius: '12px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                color: '#dc2626',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              whileHover={{
                scale: 1.02,
                background: 'rgba(239, 68, 68, 0.15)',
                boxShadow: '0 2px 8px rgba(239, 68, 68, 0.2)',
              }}
              whileTap={{ scale: 0.98 }}
            >
              <X size={16} strokeWidth={2} />
              <span>Clear All</span>
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Filter chips row (AC1 & AC5: horizontal scroll on mobile) */}
      <AnimatePresence>
        {filterChips.length > 0 && (
          <motion.div
            className="filter-chips-row"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{
              marginTop: '12px',
              overflow: 'hidden',
            }}
          >
            <FilterChips />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Active filters count text (AC3: "Showing X of Y vehicles") */}
      {activeFilterCount > 0 && (
        <motion.div
          className="filters-summary"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            marginTop: '8px',
            fontSize: '13px',
            color: '#6b7280',
            textAlign: 'center',
          }}
        >
          {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
        </motion.div>
      )}
    </div>
  );
};

/**
 * Filter Bar with integrated sort explanation
 * Displays Otto's explanation of the current sort choice
 * AC4: Otto explains sorting choice
 */
export const FilterBarWithExplanation: React.FC<FilterBarProps> = (props) => {
  const { sortBy } = useFilters();

  return (
    <div>
      <FilterBar {...props} />
      <motion.p
        className="sort-explanation"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          marginTop: '8px',
          fontSize: '13px',
          color: '#6b7280',
          textAlign: 'center',
        }}
      >
        {SORT_EXPLANATIONS[sortBy]}
      </motion.p>
    </div>
  );
};

export default FilterBar;
