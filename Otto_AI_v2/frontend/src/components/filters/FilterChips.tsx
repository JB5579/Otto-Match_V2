/**
 * Filter Chips Component for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Displays active filters as removable pill chips with glass-morphism styling.
 *
 * Features:
 * - Horizontal scrollable row of removable filter pills
 * - Chip format: "Price: $20k-$40k", "Make: Toyota", "Type: SUV"
 * - Glass-morphism styling with cyan glow border
 * - × button to remove individual filter
 * - Smooth transition when chips added/removed
 * - Hide when no active filters
 * - ARIA labels for accessibility
 *
 * AC5: Filter Chips Display
 * AC10: Accessibility Compliance
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { useFilters } from '../../context/FilterContext';
import type { FilterChip } from '../../types/filters';

/**
 * Filter Chips Props
 */
interface FilterChipsProps {
  /** Optional className for additional styling */
  className?: string;
  /** Maximum number of chips to show before scrolling (default: all) */
  maxVisible?: number;
}

/**
 * Individual Filter Chip Props
 */
interface FilterChipProps {
  /** Chip data */
  chip: FilterChip;
  /** On remove callback */
  onRemove: (chip: FilterChip) => void;
  /** Chip index for animation delay */
  index: number;
}

/**
 * Individual Filter Chip Component
 *
 * Displays a single filter chip with remove button.
 *
 * @example
 * <FilterChip chip={chip} onRemove={handleRemove} index={0} />
 */
const FilterChipItem: React.FC<FilterChipProps> = ({ chip, onRemove, index }) => {
  const handleRemove = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onRemove(chip);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8, y: -10 }}
      transition={{
        duration: 0.25,
        delay: index * 0.05, // Stagger animation
        layout: { duration: 0.2 },
      }}
      className="filter-chip"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        borderRadius: '20px',
        // Glass-morphism styling with cyan glow border (AC5)
        background: 'rgba(6, 182, 212, 0.1)',
        border: '1px solid rgba(6, 182, 212, 0.3)',
        boxShadow: '0 0 12px rgba(6, 182, 212, 0.15)',
        color: '#0891b2',
        fontSize: '13px',
        fontWeight: 500,
        whiteSpace: 'nowrap',
        flexShrink: 0,
        cursor: 'default',
      }}
    >
      <span className="filter-chip-label">{chip.label}</span>
      <motion.button
        type="button"
        onClick={handleRemove}
        aria-label={`Remove ${chip.label}`}
        className="filter-chip-remove"
        whileHover={{ scale: 1.15 }}
        whileTap={{ scale: 0.85 }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '18px',
          height: '18px',
          borderRadius: '50%',
          background: 'rgba(6, 182, 212, 0.2)',
          border: 'none',
          color: '#0891b2',
          cursor: 'pointer',
          padding: '0',
          transition: 'all 0.15s ease',
        }}
      >
        <X size={12} strokeWidth={2.5} />
      </motion.button>
    </motion.div>
  );
};

/**
 * Filter Chips Component
 *
 * Displays active filters as a horizontal scrollable row of removable pills.
 * Smooth animations when chips are added or removed.
 *
 * @example
 * <FilterChips />
 */
export const FilterChips: React.FC<FilterChipsProps> = ({
  className = '',
  maxVisible,
}) => {
  const { filterChips, removeFilter } = useFilters();

  const handleRemove = (chip: FilterChip) => {
    removeFilter(chip.category, chip.value);
  };

  if (filterChips.length === 0) {
    // Hide when no active filters (AC5)
    return null;
  }

  const visibleChips = maxVisible ? filterChips.slice(0, maxVisible) : filterChips;
  const hasMore = maxVisible && filterChips.length > maxVisible;

  return (
    <div
      className={`filter-chips ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        // Horizontal scroll on mobile (AC1)
        overflowX: 'auto',
        overflowY: 'hidden',
        scrollbarWidth: 'none', // Firefox
        msOverflowStyle: 'none', // IE/Edge
        // Scroll snap for smooth mobile experience
        scrollSnapType: 'x mandatory',
        WebkitOverflowScrolling: 'touch',
        padding: '4px 0',
      }}
      // Hide scrollbar (CSS)
      onScroll={(e) => {
        // Optional: Add scroll indicator logic here
      }}
    >
      {/* CSS to hide scrollbar in Chrome/Safari */}
      <style>{`
        .filter-chips::-webkit-scrollbar {
          display: none;
        }
        .filter-chips > * {
          scroll-snap-align: start;
        }
      `}</style>

      <AnimatePresence mode="popLayout">
        {filterChips.map((chip, index) => (
          <FilterChipItem
            key={chip.key}
            chip={chip}
            onRemove={handleRemove}
            index={index}
          />
        ))}

        {/* Show "+N more" indicator if chips are truncated */}
        {hasMore && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="filter-chips-more"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '8px 12px',
              borderRadius: '20px',
              background: 'rgba(107, 114, 128, 0.1)',
              border: '1px solid rgba(107, 114, 128, 0.2)',
              color: '#6b7280',
              fontSize: '13px',
              fontWeight: 500,
              flexShrink: 0,
            }}
          >
            +{filterChips.length - maxVisible} more
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * Compact Filter Chips variant
 * Displays chips in a more compact format with ellipsis for long labels
 */
export const FilterChipsCompact: React.FC<FilterChipsProps> = (props) => {
  const { filterChips, removeFilter } = useFilters();

  const handleRemove = (chip: FilterChip) => {
    removeFilter(chip.category, chip.value);
  };

  if (filterChips.length === 0) {
    return null;
  }

  return (
    <div
      className={`filter-chips-compact ${props.className || ''}`}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px',
      }}
    >
      <AnimatePresence mode="popLayout">
        {filterChips.map((chip, index) => (
          <motion.div
            key={chip.key}
            layout
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
            className="filter-chip-compact"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: '16px',
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              color: '#0891b2',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            <span
              className="filter-chip-label"
              style={{
                maxWidth: '100px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {chip.label}
            </span>
            <button
              type="button"
              onClick={() => handleRemove(chip)}
              aria-label={`Remove ${chip.label}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: 'transparent',
                border: 'none',
                color: '#0891b2',
                cursor: 'pointer',
                padding: '0',
              }}
            >
              <X size={12} strokeWidth={2} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default FilterChips;
