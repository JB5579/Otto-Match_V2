/**
 * Sort Dropdown Component for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Custom dropdown for selecting sort options with glass-morphism styling.
 *
 * Features:
 * - Sort options: Relevance, Price (asc/desc), Mileage, Year
 * - Otto explanation text for each sort option
 * - Glass-morphism styled dropdown
 * - ARIA role="combobox" with expanded state
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Toggle sort direction for Price options
 *
 * AC4: Intelligent Sort Options
 * AC10: Accessibility Compliance
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ArrowUpDown } from 'lucide-react';
import { useFilters } from '../../context/FilterContext';
import { SortOption, SORT_LABELS, SORT_EXPLANATIONS, isValidSortOption } from '../../types/filters';

/**
 * Sort Dropdown Props
 */
interface SortDropdownProps {
  /** Optional className for additional styling */
  className?: string;
}

/**
 * Sort Dropdown Component
 *
 * Displays a custom dropdown for selecting sort options.
 * Supports keyboard navigation and ARIA attributes for accessibility.
 *
 * @example
 * <SortDropdown />
 */
export const SortDropdown: React.FC<SortDropdownProps> = ({
  className = '',
}) => {
  const { sortBy, setSort } = useFilters();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Sort options with direction toggle for price
  const sortOptions: SortOption[] = [
    'relevance',
    'price_asc',
    'price_desc',
    'mileage',
    'year',
  ];

  /**
   * Handle keyboard navigation
   * AC10: Keyboard navigation (Arrow keys, Enter, Escape)
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) => (prev + 1) % sortOptions.length);
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex((prev) => (prev - 1 + sortOptions.length) % sortOptions.length);
        }
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (isOpen && focusedIndex >= 0) {
          handleSelectOption(sortOptions[focusedIndex]);
        } else {
          setIsOpen(!isOpen);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        buttonRef.current?.focus();
        break;
      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  }, [isOpen, focusedIndex]);

  /**
   * Handle option selection
   */
  const handleSelectOption = (option: SortOption) => {
    setSort(option);
    setIsOpen(false);
    setFocusedIndex(-1);
    buttonRef.current?.focus();
  };

  /**
   * Close dropdown when clicking outside
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Focus management for keyboard navigation
   */
  useEffect(() => {
    if (isOpen && focusedIndex >= 0) {
      const optionElements = containerRef.current?.querySelectorAll('[role="option"]');
      optionElements?.[focusedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [isOpen, focusedIndex]);

  const currentLabel = SORT_LABELS[sortBy];

  return (
    <div
      ref={containerRef}
      className={`sort-dropdown ${className}`}
      style={{ position: 'relative', minWidth: '200px' }}
    >
      {/* Sort dropdown button (AC4: sort dropdown) */}
      <motion.button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Sort by ${currentLabel}`}
        role="combobox"
        className="sort-dropdown-button"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          padding: '10px 16px',
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.9)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
          color: '#374151',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          width: '100%',
          textAlign: 'left',
        }}
        whileHover={{
          scale: 1.01,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
        }}
        whileTap={{ scale: 0.99 }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ArrowUpDown size={16} strokeWidth={2} style={{ color: '#6b7280' }} />
          <span>{currentLabel}</span>
        </span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={16} strokeWidth={2} style={{ color: '#6b7280' }} />
        </motion.div>
      </motion.button>

      {/* Dropdown menu (AC4: sort options displayed) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="sort-dropdown-menu"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            role="listbox"
            aria-label="Sort options"
            aria-activedescendant={focusedIndex >= 0 ? `sort-option-${focusedIndex}` : undefined}
            style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              right: 0,
              zIndex: 50,
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
              padding: '8px',
              maxHeight: '300px',
              overflowY: 'auto',
            }}
          >
            {sortOptions.map((option, index) => {
              const isSelected = option === sortBy;
              const isFocused = index === focusedIndex;
              const label = SORT_LABELS[option];
              const explanation = SORT_EXPLANATIONS[option];

              return (
                <motion.button
                  key={option}
                  id={`sort-option-${index}`}
                  type="button"
                  onClick={() => handleSelectOption(option)}
                  role="option"
                  aria-selected={isSelected}
                  className="sort-option"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '2px',
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    background: isSelected
                      ? 'rgba(6, 182, 212, 0.15)'
                      : isFocused
                      ? 'rgba(6, 182, 212, 0.08)'
                      : 'transparent',
                    border: isSelected
                      ? '1px solid rgba(6, 182, 212, 0.3)'
                      : '1px solid transparent',
                    color: isSelected ? '#0891b2' : '#374151',
                    fontSize: '14px',
                    fontWeight: isSelected ? 600 : 400,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                  }}
                  whileHover={{
                    background: isSelected
                      ? 'rgba(6, 182, 212, 0.2)'
                      : 'rgba(6, 182, 212, 0.1)',
                  }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isSelected && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        style={{ color: '#0891b2' }}
                      >
                        ✓
                      </motion.span>
                    )}
                    <span>{label}</span>
                  </span>
                  <span
                    style={{
                      fontSize: '12px',
                      color: isSelected ? '#0e7490' : '#6b7280',
                      fontWeight: 400,
                      marginLeft: isSelected ? '20px' : '0',
                    }}
                  >
                    {explanation}
                  </span>
                </motion.button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SortDropdown;
