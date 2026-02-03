/**
 * Filter Empty State Component for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Friendly empty state displayed when no vehicles match the applied filters.
 *
 * Features:
 * - Friendly message: "No vehicles match your filters"
 * - Illustration or icon
 * - CTA button: "Clear All Filters"
 * - Otto suggestion: "Try adjusting your filters to see more options"
 * - Glass-morphism styled panel
 *
 * AC9: Empty State for No Results
 */

import React from 'react';
import { motion } from 'framer-motion';
import { SearchX, RefreshCcw } from 'lucide-react';
import { useFilters } from '../../context/FilterContext';

/**
 * Filter Empty State Props
 */
interface FilterEmptyStateProps {
  /** Optional custom message */
  message?: string;
  /** Optional className for additional styling */
  className?: string;
  /** Optional callback for clear filters (uses context if not provided) */
  onClearFilters?: () => void;
}

/**
 * Filter Empty State Component
 *
 * Friendly empty state displayed when no vehicles match the applied filters.
 * Shows illustration, message, and CTA button to clear filters.
 *
 * @example
 * <FilterEmptyState />
 */
export const FilterEmptyState: React.FC<FilterEmptyStateProps> = ({
  message = 'No vehicles match your filters',
  className = '',
  onClearFilters,
}) => {
  const { clearAllFilters, activeFilterCount } = useFilters();

  const handleClearFilters = () => {
    if (onClearFilters) {
      onClearFilters();
    } else {
      clearAllFilters();
    }
  };

  return (
    <motion.div
      className={`filter-empty-state ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 24px',
        textAlign: 'center',
        // Glass-morphism styled panel (AC9)
        background: 'rgba(255, 255, 255, 0.7)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        borderRadius: '20px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
        minHeight: '400px',
      }}
    >
      {/* Illustration / Icon (AC9: illustration + CTA) */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '120px',
          height: '120px',
          borderRadius: '50%',
          background: 'rgba(6, 182, 212, 0.1)',
          border: '2px solid rgba(6, 182, 212, 0.2)',
          marginBottom: '24px',
        }}
      >
        <SearchX size={64} strokeWidth={1.5} style={{ color: '#06b6d4' }} />
      </motion.div>

      {/* Main message (AC9: friendly message) */}
      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.3 }}
        style={{
          margin: '0 0 12px 0',
          fontSize: '24px',
          fontWeight: 600,
          color: '#111827',
        }}
      >
        {message}
      </motion.h2>

      {/* Active filter count */}
      {activeFilterCount > 0 && (
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.3 }}
          style={{
            margin: '0 0 8px 0',
            fontSize: '15px',
            color: '#6b7280',
          }}
        >
          {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} currently applied
        </motion.p>
      )}

      {/* Otto suggestion (AC9: Otto suggestion) */}
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.3 }}
        style={{
          margin: '0 0 32px 0',
          fontSize: '14px',
          color: '#6b7280',
          maxWidth: '400px',
        }}
      >
        Try adjusting your filters to see more options
      </motion.p>

      {/* CTA button (AC9: "Clear All Filters" button prominent) */}
      <motion.button
        type="button"
        onClick={handleClearFilters}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        whileHover={{ scale: 1.05, boxShadow: '0 8px 20px rgba(6, 182, 212, 0.4)' }}
        whileTap={{ scale: 0.95 }}
        className="clear-filters-cta"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '14px 28px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
          border: 'none',
          color: '#ffffff',
          fontSize: '16px',
          fontWeight: 600,
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(6, 182, 212, 0.3)',
          transition: 'all 0.2s ease',
        }}
      >
        <RefreshCcw size={20} strokeWidth={2} />
        <span>Clear All Filters</span>
      </motion.button>

      {/* Optional: Filter suggestions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.4 }}
        style={{
          marginTop: '32px',
          padding: '16px 20px',
          borderRadius: '12px',
          background: 'rgba(6, 182, 212, 0.08)',
          border: '1px solid rgba(6, 182, 212, 0.15)',
        }}
      >
        <p
          style={{
            margin: '0 0 8px 0',
            fontSize: '13px',
            fontWeight: 500,
            color: '#0891b2',
          }}
        >
          💡 Tip: Try widening your price range or selecting fewer makes
        </p>
      </motion.div>
    </motion.div>
  );
};

/**
 * Compact Filter Empty State variant
 * Smaller version for use in constrained spaces
 */
export const FilterEmptyStateCompact: React.FC<FilterEmptyStateProps> = ({
  message = 'No results found',
  className = '',
  onClearFilters,
}) => {
  const { clearAllFilters } = useFilters();

  const handleClearFilters = () => {
    if (onClearFilters) {
      onClearFilters();
    } else {
      clearAllFilters();
    }
  };

  return (
    <motion.div
      className={`filter-empty-state-compact ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        textAlign: 'center',
        minHeight: '250px',
      }}
    >
      <SearchX size={48} strokeWidth={1.5} style={{ color: '#9ca3af', marginBottom: '16px' }} />
      <h3
        style={{
          margin: '0 0 8px 0',
          fontSize: '18px',
          fontWeight: 500,
          color: '#374151',
        }}
      >
        {message}
      </h3>
      <button
        type="button"
        onClick={handleClearFilters}
        style={{
          marginTop: '16px',
          padding: '10px 20px',
          borderRadius: '8px',
          background: 'rgba(6, 182, 212, 0.1)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          color: '#0891b2',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
        }}
      >
        Clear Filters
      </button>
    </motion.div>
  );
};

export default FilterEmptyState;
