/**
 * Filter Context for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Provides centralized filter and sort state management for the vehicle grid.
 *
 * Features:
 * - Filter state management (price, make, type, year, mileage, features, etc.)
 * - Sort options (relevance, price, mileage, year, efficiency)
 * - sessionStorage persistence (AC7 compliance, 30min expiry)
 * - Filter chips generation for UI display
 * - Integration with VehicleContext for filtered vehicle display
 * - Support for conversation-driven filter application (AC8)
 *
 * AC1: Filter Bar Component
 * AC3: Real-Time Filter Application
 * AC4: Intelligent Sort Options
 * AC6: Clear All Filters
 * AC7: Filter Persistence (30min expiry)
 * AC8: Integration with Conversation Preferences
 */

import React, { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import type { Vehicle } from '../app/types/api';
import type {
  FilterState,
  SortOption,
  FilterChip,
  FilterResult,
  FilterStorageSchema,
  FilterStateWithMeta,
} from '../types/filters';
import {
  DEFAULT_FILTER_STATE,
  DEFAULT_SORT_OPTION,
  FILTER_STORAGE_KEY,
  FILTER_STORAGE_EXPIRY_MS,
  isFilterEmpty,
  countActiveFilters,
  generateFilterChips,
  applyFiltersAndSort,
} from '../types/filters';
import { debounce } from '../utils/performance';

/**
 * Filter context value interface
 */
interface FilterContextValue {
  /** Current filter state */
  filters: FilterStateWithMeta;
  /** Current sort option */
  sortBy: SortOption;
  /** Active filter count */
  activeFilterCount: number;
  /** Filter chips for UI display */
  filterChips: FilterChip[];
  /** Whether filters are currently active */
  hasActiveFilters: boolean;
  /** Apply filters to state (immediate) */
  applyFilters: (filters: FilterState, source?: 'user' | 'conversation' | 'auto') => void;
  /** Apply filters to state (debounced by 300ms) - Story 3-8.10 */
  applyFiltersDebounced: (filters: FilterState, source?: 'user' | 'conversation' | 'auto') => void;
  /** Remove a single filter by category and value */
  removeFilter: (category: keyof FilterState, value?: unknown) => void;
  /** Clear all filters */
  clearAllFilters: () => void;
  /** Set sort option */
  setSort: (sortBy: SortOption) => void;
  /** Get filtered and sorted vehicles */
  getFilteredVehicles: (vehicles: Vehicle[]) => FilterResult;
  /** Merge conversation preferences with current filters (AC8) */
  mergeConversationPreferences: (preferences: Record<string, unknown>) => void;
  /** Export current filters for storage */
  exportFilters: () => FilterStorageSchema;
  /** Import filters from storage */
  importFilters: (schema: FilterStorageSchema) => void;
}

/**
 * Filter context
 */
const FilterContext = createContext<FilterContextValue | null>(null);

/**
 * Provider props
 */
export interface FilterProviderProps {
  children: React.ReactNode;
  /** Initial filter state (optional) */
  initialFilters?: FilterState;
  /** Initial sort option (optional) */
  initialSort?: SortOption;
}

/**
 * Load filter state from sessionStorage
 * AC7: Filter Persistence (30min expiry)
 */
const loadFromStorage = (): FilterStorageSchema | null => {
  try {
    const stored = sessionStorage.getItem(FILTER_STORAGE_KEY);
    if (stored) {
      const parsed: FilterStorageSchema = JSON.parse(stored);

      // Check expiry (AC7: 30-minute expiry)
      const now = Date.now();
      if (now - parsed.timestamp > FILTER_STORAGE_EXPIRY_MS) {
        console.log('[FilterContext] Filter state expired, clearing...');
        sessionStorage.removeItem(FILTER_STORAGE_KEY);
        return null;
      }

      console.log('[FilterContext] Loaded filter state from storage:', parsed);
      return parsed;
    }
  } catch (error) {
    console.error('[FilterContext] Failed to load from storage:', error);
  }
  return null;
};

/**
 * Save filter state to sessionStorage
 * AC7: Filter Persistence (30min expiry)
 */
const saveToStorage = (schema: FilterStorageSchema): void => {
  try {
    sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(schema));
  } catch (error) {
    console.error('[FilterContext] Failed to save to storage:', error);
  }
};

/**
 * Filter Provider component
 * Manages filter and sort state with sessionStorage persistence
 */
export const FilterProvider: React.FC<FilterProviderProps> = ({
  children,
  initialFilters = DEFAULT_FILTER_STATE,
  initialSort = DEFAULT_SORT_OPTION,
}) => {
  // Initialize state from storage or use initial props
  const storedState = loadFromStorage();

  const [filters, setFilters] = useState<FilterStateWithMeta>(() => {
    const initialFiltersToUse = storedState?.filters || initialFilters;
    return {
      ...initialFiltersToUse,
      appliedAt: storedState ? new Date(storedState.timestamp).toISOString() : undefined,
      source: storedState ? 'auto' : undefined,
    };
  });

  const [sortBy, setSortState] = useState<SortOption>(
    storedState?.sortBy || initialSort
  );

  /**
   * Persist filter state to sessionStorage whenever filters or sort changes
   * AC7: Filter Persistence (30min expiry)
   */
  useEffect(() => {
    const schema: FilterStorageSchema = {
      filters: {
        priceRange: filters.priceRange,
        makes: filters.makes,
        vehicleTypes: filters.vehicleTypes,
        yearRange: filters.yearRange,
        maxMileage: filters.maxMileage,
        features: filters.features,
        fuelTypes: filters.fuelTypes,
        transmission: filters.transmission,
        drivetrain: filters.drivetrain,
        colors: filters.colors,
      },
      sortBy,
      timestamp: Date.now(),
    };
    saveToStorage(schema);
  }, [filters, sortBy]);

  /**
   * Computed values
   */
  const activeFilterCount = useMemo(() => countActiveFilters(filters), [filters]);
  const filterChips = useMemo(() => generateFilterChips(filters), [filters]);
  const hasActiveFilters = useMemo(() => !isFilterEmpty(filters), [filters]);

  /**
   * Apply filters to state
   * AC3: Real-Time Filter Application
   * AC8: Integration with Conversation Preferences
   * Story 3-8.10: Debounced by 300ms to prevent excessive re-renders
   */
  const applyFilters = useCallback((newFilters: FilterState, source: 'user' | 'conversation' | 'auto' = 'user') => {
    console.log('[FilterContext] Applying filters:', { newFilters, source });

    setFilters({
      ...newFilters,
      appliedAt: new Date().toISOString(),
      source,
    });
  }, []);

  /**
   * Debounced version of applyFilters
   * Story 3-8.10: Delays filter application by 300ms
   * Use this for rapid filter changes (e.g., user typing in search)
   */
  const applyFiltersDebounced = useMemo(
    () => debounce(applyFilters, 300),
    [applyFilters]
  );

  /**
   * Remove a single filter by category and optional value
   * AC5: Filter chips display applied filters as removable pills
   */
  const removeFilter = useCallback((category: keyof FilterState, value?: unknown) => {
    console.log('[FilterContext] Removing filter:', { category, value });

    setFilters((prev) => {
      const updated = { ...prev };

      if (value === undefined) {
        // Remove entire category
        delete updated[category];
      } else {
        // Remove specific value from array
        const currentValue = updated[category];
        if (Array.isArray(currentValue)) {
          const filtered = currentValue.filter((v) => v !== value);
          if (filtered.length === 0) {
            delete updated[category];
          } else {
            updated[category] = filtered as any;
          }
        }
      }

      return {
        ...updated,
        appliedAt: new Date().toISOString(),
        source: 'user',
      };
    });
  }, []);

  /**
   * Clear all filters
   * AC6: Clear All Filters
   */
  const clearAllFilters = useCallback(() => {
    console.log('[FilterContext] Clearing all filters');

    setFilters({
      ...DEFAULT_FILTER_STATE,
      appliedAt: new Date().toISOString(),
      source: 'user',
    });

    // Reset sort to relevance (AC6: sort resets to "Relevance")
    setSortState(DEFAULT_SORT_OPTION);
  }, []);

  /**
   * Set sort option
   * AC4: Intelligent Sort Options
   */
  const setSort = useCallback((newSortBy: SortOption) => {
    console.log('[FilterContext] Setting sort option:', newSortBy);
    setSortState(newSortBy);
  }, []);

  /**
   * Get filtered and sorted vehicles
   * AC3: Real-Time Filter Application
   * AC4: Sorting applied within current filter constraints
   */
  const getFilteredVehicles = useCallback((vehicles: Vehicle[]): FilterResult => {
    return applyFiltersAndSort(vehicles, filters, sortBy);
  }, [filters, sortBy]);

  /**
   * Merge conversation preferences with current filters
   * AC8: Integration with Conversation Preferences
   * Otto extracts a preference (e.g., "Electric SUV under $50k") → filters auto-apply
   */
  const mergeConversationPreferences = useCallback((preferences: Record<string, unknown>) => {
    console.log('[FilterContext] Merging conversation preferences:', preferences);

    setFilters((prev) => {
      const merged: FilterState = { ...prev };

      // Map conversation preferences to filter categories
      // Budget → priceRange
      const budget = preferences.budget as { min?: number; max?: number } | undefined;
      if (budget?.max !== undefined) {
        const minPrice = budget.min || 0;
        merged.priceRange = [minPrice, budget.max];
      }

      // Make(s) → makes
      const makes = preferences.make as string[] | string | undefined;
      if (makes) {
        merged.makes = Array.isArray(makes) ? makes : [makes];
      }

      // Body type(s) → vehicleTypes
      const bodyTypes = preferences.bodyType as string[] | string | undefined;
      if (bodyTypes) {
        merged.vehicleTypes = Array.isArray(bodyTypes) ? bodyTypes as any : [bodyTypes as any];
      }

      // Year → yearRange
      const year = preferences.year as { min?: number; max?: number } | number | undefined;
      if (year) {
        if (typeof year === 'number') {
          merged.yearRange = [year, new Date().getFullYear()];
        } else {
          merged.yearRange = [year.min || 2015, year.max || new Date().getFullYear()];
        }
      }

      // Mileage → maxMileage
      const mileage = preferences.mileage as { max?: number } | number | undefined;
      if (mileage) {
        const maxMileage = typeof mileage === 'number' ? mileage : mileage.max;
        if (maxMileage !== undefined) {
          merged.maxMileage = maxMileage;
        }
      }

      // Fuel type → fuelTypes
      const fuelTypes = preferences.fuelType as string[] | string | undefined;
      if (fuelTypes) {
        merged.fuelTypes = Array.isArray(fuelTypes) ? fuelTypes : [fuelTypes];
      }

      // Features → features
      const features = preferences.features as string[] | undefined;
      if (features && features.length > 0) {
        merged.features = features as any;
      }

      // Transmission → transmission
      const transmission = preferences.transmission as string[] | string | undefined;
      if (transmission) {
        merged.transmission = Array.isArray(transmission) ? transmission : [transmission];
      }

      // Drivetrain → drivetrain
      const drivetrain = preferences.drivetrain as string[] | string | undefined;
      if (drivetrain) {
        merged.drivetrain = Array.isArray(drivetrain) ? drivetrain : [drivetrain];
      }

      // Color → colors
      const colors = preferences.color as string[] | string | undefined;
      if (colors) {
        merged.colors = Array.isArray(colors) ? colors : [colors];
      }

      return {
        ...merged,
        appliedAt: new Date().toISOString(),
        source: 'conversation',
      };
    });
  }, []);

  /**
   * Export current filters for storage
   */
  const exportFilters = useCallback((): FilterStorageSchema => {
    return {
      filters: {
        priceRange: filters.priceRange,
        makes: filters.makes,
        vehicleTypes: filters.vehicleTypes,
        yearRange: filters.yearRange,
        maxMileage: filters.maxMileage,
        features: filters.features,
        fuelTypes: filters.fuelTypes,
        transmission: filters.transmission,
        drivetrain: filters.drivetrain,
        colors: filters.colors,
      },
      sortBy,
      timestamp: Date.now(),
    };
  }, [filters, sortBy]);

  /**
   * Import filters from storage
   */
  const importFilters = useCallback((schema: FilterStorageSchema) => {
    console.log('[FilterContext] Importing filters:', schema);
    setFilters({
      ...schema.filters,
      appliedAt: new Date(schema.timestamp).toISOString(),
      source: 'auto',
    });
    setSortState(schema.sortBy);
  }, []);

  /**
   * Context value
   * Story 3-8.10: Exports both immediate and debounced filter application
   */
  const value: FilterContextValue = {
    filters,
    sortBy,
    activeFilterCount,
    filterChips,
    hasActiveFilters,
    applyFilters,
    applyFiltersDebounced, // Story 3-8.10: Debounced version for rapid changes
    removeFilter,
    clearAllFilters,
    setSort,
    getFilteredVehicles,
    mergeConversationPreferences,
    exportFilters,
    importFilters,
  };

  return (
    <FilterContext.Provider value={value}>
      {children}
    </FilterContext.Provider>
  );
};

/**
 * Hook to access filter context
 * Must be used within FilterProvider
 *
 * @example
 * const { filters, sortBy, applyFilters, clearAllFilters } = useFilters();
 */
export const useFilters = (): FilterContextValue => {
  const context = useContext(FilterContext);

  if (!context) {
    throw new Error('useFilters must be used within FilterProvider');
  }

  return context;
};

export default FilterContext;
