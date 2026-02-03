/**
 * Filter Modal Component for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Modal with comprehensive filter options for vehicle discovery.
 *
 * Features:
 * - Modal overlay with backdrop blur (reuse VehicleDetailModal pattern)
 * - Filter categories: Price Range, Make, Vehicle Type, Year Range, Mileage, Features
 * - Price Range: Dual-handle slider
 * - Make: Multi-select dropdown with search
 * - Vehicle Type: Checkbox group (SUV, Sedan, Truck, EV, Hybrid)
 * - Year Range: Dual-handle slider
 * - Mileage: Single-handle slider (max value)
 * - Features: Multi-select chips
 * - Apply Filters button (bottom-right)
 * - Cancel button (bottom-left)
 * - Selected count badges per category
 * - Close on Escape key, backdrop click, or X button
 *
 * AC2: Filter Modal with Multi-Select Options
 * AC10: Accessibility Compliance
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Check } from 'lucide-react';
import { useFilters } from '../../context/FilterContext';
import type { FilterState, VehicleTypeFilter, VehicleFeatureFilter } from '../../types/filters';
import {
  AVAILABLE_MAKES,
  AVAILABLE_FUEL_TYPES,
  AVAILABLE_TRANSMISSIONS,
  AVAILABLE_DRIVETRAINS,
} from '../../types/filters';

/**
 * Filter Modal Props
 */
interface FilterModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal closes */
  onClose: () => void;
  /** Callback when filters are applied */
  onApply: (filters: FilterState) => void;
}

/**
 * Dual Range Slider Props
 */
interface DualRangeSliderProps {
  label: string;
  min: number;
  max: number;
  value: [number, number] | undefined;
  onChange: (value: [number, number]) => void;
  formatLabel?: (value: number) => string;
  step?: number;
}

/**
 * Dual Range Slider Component
 *
 * Handles price and year range filters with dual-handle slider.
 */
const DualRangeSlider: React.FC<DualRangeSliderProps> = ({
  label,
  min,
  max,
  value,
  onChange,
  formatLabel = (v) => v.toLocaleString(),
  step = 1,
}) => {
  const [localMin, setLocalMin] = useState(value?.[0] ?? min);
  const [localMax, setLocalMax] = useState(value?.[1] ?? max);

  useEffect(() => {
    if (value) {
      setLocalMin(value[0]);
      setLocalMax(value[1]);
    }
  }, [value]);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Math.min(Number(e.target.value), localMax - step);
    setLocalMin(newValue);
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Math.max(Number(e.target.value), localMin + step);
    setLocalMax(newValue);
  };

  const handleCommit = () => {
    onChange([localMin, localMax]);
  };

  const minPercent = ((localMin - min) / (max - min)) * 100;
  const maxPercent = ((localMax - min) / (max - min)) * 100;

  return (
    <div className="dual-range-slider" style={{ marginBottom: '20px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '8px',
          fontSize: '14px',
          fontWeight: 500,
          color: '#374151',
        }}
      >
        <span>{label}</span>
        {value && (
          <span style={{ color: '#0891b2' }}>
            {formatLabel(localMin)} - {formatLabel(localMax)}
          </span>
        )}
      </div>

      <div
        style={{
          position: 'relative',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {/* Track */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '6px',
            background: 'rgba(209, 213, 219, 0.5)',
            borderRadius: '3px',
          }}
        />

        {/* Active track */}
        <div
          style={{
            position: 'absolute',
            left: `${minPercent}%`,
            width: `${maxPercent - minPercent}%`,
            height: '6px',
            background: 'rgba(6, 182, 212, 0.5)',
            borderRadius: '3px',
          }}
        />

        {/* Min slider */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMin}
          onChange={handleMinChange}
          onMouseUp={handleCommit}
          onTouchEnd={handleCommit}
          aria-label={`${label} minimum`}
          style={{
            position: 'absolute',
            width: '100%',
            height: '6px',
            background: 'transparent',
            appearance: 'none',
            pointerEvents: 'auto',
            cursor: 'pointer',
          }}
        />

        {/* Max slider */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMax}
          onChange={handleMaxChange}
          onMouseUp={handleCommit}
          onTouchEnd={handleCommit}
          aria-label={`${label} maximum`}
          style={{
            position: 'absolute',
            width: '100%',
            height: '6px',
            background: 'transparent',
            appearance: 'none',
            pointerEvents: 'auto',
            cursor: 'pointer',
          }}
        />

        {/* Thumb indicators */}
        <div
          style={{
            position: 'absolute',
            left: `${minPercent}%`,
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            background: '#ffffff',
            border: '2px solid #06b6d4',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            transform: 'translate(-50%, 0)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: `${maxPercent}%`,
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            background: '#ffffff',
            border: '2px solid #06b6d4',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            transform: 'translate(-50%, 0)',
            pointerEvents: 'none',
          }}
        />
      </div>
    </div>
  );
};

/**
 * Single Range Slider Props
 */
interface SingleRangeSliderProps {
  label: string;
  min: number;
  max: number;
  value: number | undefined;
  onChange: (value: number) => void;
  formatLabel?: (value: number) => string;
  step?: number;
  /** Any value means "no limit" */
  allowAny?: boolean;
}

/**
 * Single Range Slider Component
 *
 * Handles mileage filter with single-handle slider (max value).
 */
const SingleRangeSlider: React.FC<SingleRangeSliderProps> = ({
  label,
  min,
  max,
  value,
  onChange,
  formatLabel = (v) => v.toLocaleString(),
  step = 1000,
  allowAny = true,
}) => {
  const [localValue, setLocalValue] = useState(value ?? max);
  const [isAny, setIsAny] = useState(value === undefined);

  useEffect(() => {
    if (value === undefined) {
      setIsAny(true);
    } else {
      setIsAny(false);
      setLocalValue(value);
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number(e.target.value);
    setLocalValue(newValue);
    if (!isAny) {
      onChange(newValue);
    }
  };

  const handleCommit = () => {
    if (isAny) {
      onChange(max);
    } else {
      onChange(localValue);
    }
  };

  const percent = ((localValue - min) / (max - min)) * 100;

  return (
    <div className="single-range-slider" style={{ marginBottom: '20px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
          fontSize: '14px',
          fontWeight: 500,
          color: '#374151',
        }}
      >
        <span>{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {allowAny && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px' }}>
              <input
                type="checkbox"
                checked={isAny}
                onChange={(e) => {
                  setIsAny(e.target.checked);
                  if (e.target.checked) {
                    onChange(max);
                  }
                }}
                style={{ cursor: 'pointer' }}
              />
              <span>Any</span>
            </label>
          )}
          {!isAny && <span style={{ color: '#0891b2' }}>{formatLabel(localValue)}</span>}
        </div>
      </div>

      <div
        style={{
          position: 'relative',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {/* Track */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '6px',
            background: isAny ? 'rgba(209, 213, 219, 0.3)' : 'rgba(209, 213, 219, 0.5)',
            borderRadius: '3px',
          }}
        />

        {/* Active track */}
        {!isAny && (
          <div
            style={{
              position: 'absolute',
              left: 0,
              width: `${percent}%`,
              height: '6px',
              background: 'rgba(6, 182, 212, 0.5)',
              borderRadius: '3px',
            }}
          />
        )}

        {/* Slider */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localValue}
          onChange={handleChange}
          onMouseUp={handleCommit}
          onTouchEnd={handleCommit}
          disabled={isAny}
          aria-label={`${label} maximum`}
          style={{
            position: 'absolute',
            width: '100%',
            height: '6px',
            background: 'transparent',
            appearance: 'none',
            pointerEvents: isAny ? 'none' : 'auto',
            cursor: isAny ? 'not-allowed' : 'pointer',
          }}
        />

        {/* Thumb indicator */}
        {!isAny && (
          <div
            style={{
              position: 'absolute',
              left: `${percent}%`,
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: '#ffffff',
              border: '2px solid #06b6d4',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
              transform: 'translate(-50%, 0)',
              pointerEvents: 'none',
            }}
          />
        )}
      </div>
    </div>
  );
};

/**
 * Multi-select Chips Component
 */
interface MultiSelectChipsProps {
  label: string;
  options: string[];
  selected: string[] | undefined;
  onChange: (selected: string[]) => void;
  limit?: number;
}

const MultiSelectChips: React.FC<MultiSelectChipsProps> = ({
  label,
  options,
  selected,
  onChange,
  limit,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleOption = (option: string) => {
    const currentSelected = selected ?? [];
    if (currentSelected.includes(option)) {
      onChange(currentSelected.filter(s => s !== option));
    } else if (!limit || currentSelected.length < limit) {
      onChange([...currentSelected, option]);
    }
  };

  const selectedCount = selected?.length ?? 0;

  return (
    <div className="multi-select-chips" style={{ marginBottom: '20px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
          fontSize: '14px',
          fontWeight: 500,
          color: '#374151',
        }}
      >
        <span>{label}</span>
        {selectedCount > 0 && (
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '10px',
              background: 'rgba(6, 182, 212, 0.15)',
              color: '#0891b2',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            {selectedCount}
          </span>
        )}
      </div>

      {/* Search input */}
      <div
        style={{
          position: 'relative',
          marginBottom: '8px',
        }}
      >
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#9ca3af',
          }}
        />
        <input
          type="text"
          placeholder={`Search ${label.toLowerCase()}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 10px 8px 36px',
            borderRadius: '8px',
            border: '1px solid rgba(209, 213, 219, 0.5)',
            fontSize: '13px',
            outline: 'none',
          }}
        />
      </div>

      {/* Chips grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
          gap: '8px',
          maxHeight: '200px',
          overflowY: 'auto',
        }}
      >
        {filteredOptions.map(option => {
          const isSelected = selected?.includes(option);
          return (
            <motion.button
              key={option}
              type="button"
              onClick={() => toggleOption(option)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px',
                padding: '8px 12px',
                borderRadius: '8px',
                background: isSelected
                  ? 'rgba(6, 182, 212, 0.15)'
                  : 'rgba(255, 255, 255, 0.5)',
                border: isSelected
                  ? '1px solid rgba(6, 182, 212, 0.3)'
                  : '1px solid rgba(209, 213, 219, 0.3)',
                color: isSelected ? '#0891b2' : '#4b5563',
                fontSize: '13px',
                fontWeight: isSelected ? 500 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {isSelected && <Check size={14} strokeWidth={2.5} />}
              <span style={{ textAlign: 'center' }}>{option}</span>
            </motion.button>
          );
        })}
      </div>

      {limit && selectedCount >= limit && (
        <p
          style={{
            marginTop: '4px',
            fontSize: '12px',
            color: '#f59e0b',
          }}
        >
          Maximum {limit} options selected
        </p>
      )}
    </div>
  );
};

/**
 * Filter Modal Component
 *
 * Modal with comprehensive filter options for vehicle discovery.
 * Glass-morphism styled overlay with backdrop blur.
 *
 * @example
 * <FilterModal
 *   isOpen={isModalOpen}
 *   onClose={() => setIsModalOpen(false)}
 *   onApply={(filters) => applyFilters(filters)}
 * />
 */
export const FilterModal: React.FC<FilterModalProps> = ({
  isOpen,
  onClose,
  onApply,
}) => {
  const { filters } = useFilters();
  const modalRef = useRef<HTMLDivElement>(null);

  // Local state for pending filters
  const [pendingFilters, setPendingFilters] = useState<FilterState>(filters);

  // Reset pending filters when modal opens
  useEffect(() => {
    if (isOpen) {
      setPendingFilters(filters);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, filters]);

  // Focus trap for accessibility
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleApply = () => {
    onApply(pendingFilters);
    onClose();
  };

  const handleCancel = () => {
    onClose();
  };

  // Vehicle types
  const vehicleTypes: VehicleTypeFilter[] = [
    'SUV', 'Sedan', 'Truck', 'EV', 'Hybrid',
    'Coupe', 'Convertible', 'Wagon', 'Van', 'Crossover',
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="filter-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={handleBackdropClick}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '16px',
          }}
        >
          <motion.div
            ref={modalRef}
            className="filter-modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: '20px',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
              maxWidth: '700px',
              width: '100%',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '20px 24px',
                borderBottom: '1px solid rgba(209, 213, 219, 0.3)',
              }}
            >
              <h2
                style={{
                  margin: 0,
                  fontSize: '20px',
                  fontWeight: 600,
                  color: '#111827',
                }}
              >
                Filter Vehicles
              </h2>
              <motion.button
                type="button"
                onClick={onClose}
                aria-label="Close filters"
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
              color: '#dc2626',
                  cursor: 'pointer',
                }}
              >
                <X size={20} strokeWidth={2} />
              </motion.button>
            </div>

            {/* Filter categories (scrollable) */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '20px 24px',
              }}
            >
              {/* Price Range */}
              <DualRangeSlider
                label="Price Range"
                min={0}
                max={100000}
                value={pendingFilters.priceRange}
                onChange={(value) =>
                  setPendingFilters((prev) => ({ ...prev, priceRange: value }))
                }
                formatLabel={(v) => `$${(v / 1000).toFixed(0)}k`}
                step={5000}
              />

              {/* Make */}
              <MultiSelectChips
                label="Make"
                options={AVAILABLE_MAKES}
                selected={pendingFilters.makes}
                onChange={(selected) =>
                  setPendingFilters((prev) => ({ ...prev, makes: selected }))
                }
              />

              {/* Vehicle Type */}
              <MultiSelectChips
                label="Vehicle Type"
                options={vehicleTypes}
                selected={pendingFilters.vehicleTypes}
                onChange={(selected) =>
                  setPendingFilters((prev) => ({ ...prev, vehicleTypes: selected }))
                }
              />

              {/* Year Range */}
              <DualRangeSlider
                label="Year Range"
                min={2015}
                max={new Date().getFullYear()}
                value={pendingFilters.yearRange}
                onChange={(value) =>
                  setPendingFilters((prev) => ({ ...prev, yearRange: value }))
                }
                step={1}
              />

              {/* Mileage */}
              <SingleRangeSlider
                label="Maximum Mileage"
                min={0}
                max={200000}
                value={pendingFilters.maxMileage}
                onChange={(value) =>
                  setPendingFilters((prev) => ({ ...prev, maxMileage: value }))
                }
                formatLabel={(v) => `${(v / 1000).toFixed(0)}k mi`}
                step={5000}
                allowAny
              />

              {/* Fuel Type */}
              <MultiSelectChips
                label="Fuel Type"
                options={AVAILABLE_FUEL_TYPES}
                selected={pendingFilters.fuelTypes}
                onChange={(selected) =>
                  setPendingFilters((prev) => ({ ...prev, fuelTypes: selected }))
                }
              />

              {/* Transmission */}
              <MultiSelectChips
                label="Transmission"
                options={AVAILABLE_TRANSMISSIONS}
                selected={pendingFilters.transmission}
                onChange={(selected) =>
                  setPendingFilters((prev) => ({ ...prev, transmission: selected }))
                }
              />

              {/* Drivetrain */}
              <MultiSelectChips
                label="Drivetrain"
                options={AVAILABLE_DRIVETRAINS}
                selected={pendingFilters.drivetrain}
                onChange={(selected) =>
                  setPendingFilters((prev) => ({ ...prev, drivetrain: selected }))
                }
              />
            </div>

            {/* Footer with Apply/Cancel buttons */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: '12px',
                padding: '16px 24px',
                borderTop: '1px solid rgba(209, 213, 219, 0.3)',
              }}
            >
              {/* Cancel button (bottom-left) */}
              <motion.button
                type="button"
                onClick={handleCancel}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                style={{
                  padding: '12px 24px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.8)',
                  border: '1px solid rgba(209, 213, 219, 0.4)',
                  color: '#4b5563',
                  fontSize: '15px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </motion.button>

              {/* Apply Filters button (bottom-right) */}
              <motion.button
                type="button"
                onClick={handleApply}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                style={{
                  padding: '12px 24px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
                  border: 'none',
                  color: '#ffffff',
                  fontSize: '15px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(6, 182, 212, 0.3)',
                }}
              >
                Apply Filters
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default FilterModal;
