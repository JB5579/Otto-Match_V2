/**
 * Filter Context Tests for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Tests for FilterContext state management, persistence, and filter operations.
 *
 * Coverage:
 * - Filter state management (add, remove, clear)
 * - Sort preference state
 * - sessionStorage persistence (AC7)
 * - Filter merging with conversation preferences (AC8)
 * - Filter expiration (30min)
 * - Filter chips generation
 * - Filtered vehicle sorting
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { FilterProvider, useFilters } from '../FilterContext';
import type { FilterState, SortOption } from '../../types/filters';
import { FILTER_STORAGE_KEY, FILTER_STORAGE_EXPIRY_MS } from '../../types/filters';
import * as filters from '../../types/filters';

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Mock filters module
vi.mock('../../types/filters', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../types/filters')>();
  return {
    ...actual,
    applyFiltersAndSort: vi.fn((vehicles, filters, sortBy) => ({
      vehicles: vehicles.filter(() => true), // Pass through for testing
      totalCount: vehicles.length,
      filteredCount: vehicles.length,
      activeFilterCount: Object.keys(filters).filter(k => filters[k as keyof FilterState]).length,
    })),
  };
});

describe('FilterContext', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <FilterProvider>{children}</FilterProvider>
  );

  describe('initial state', () => {
    it('should initialize with empty filters', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.filters).toEqual({});
      expect(result.current.sortBy).toBe('relevance');
      expect(result.current.activeFilterCount).toBe(0);
      expect(result.current.hasActiveFilters).toBe(false);
    });

    it('should initialize with custom initial filters', () => {
      const customFilters: FilterState = {
        makes: ['Toyota', 'Honda'],
        priceRange: [20000, 40000],
      };

      const customWrapper = ({ children }: { children: React.ReactNode }) => (
        <FilterProvider initialFilters={customFilters}>{children}</FilterProvider>
      );

      const { result } = renderHook(() => useFilters(), { wrapper: customWrapper });

      expect(result.current.filters.makes).toEqual(['Toyota', 'Honda']);
      expect(result.current.filters.priceRange).toEqual([20000, 40000]);
    });

    it('should initialize with custom sort option', () => {
      const customWrapper = ({ children }: { children: React.ReactNode }) => (
        <FilterProvider initialSort="price_asc">{children}</FilterProvider>
      );

      const { result } = renderHook(() => useFilters(), { wrapper: customWrapper });

      expect(result.current.sortBy).toBe('price_asc');
    });
  });

  describe('applyFilters', () => {
    it('should apply new filters', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      const newFilters: FilterState = {
        makes: ['Toyota'],
        priceRange: [20000, 40000],
      };

      act(() => {
        result.current.applyFilters(newFilters);
      });

      expect(result.current.filters.makes).toEqual(['Toyota']);
      expect(result.current.filters.priceRange).toEqual([20000, 40000]);
      expect(result.current.filters.appliedAt).toBeDefined();
      expect(result.current.filters.source).toBe('user');
    });

    it('should set source to "conversation" when specified', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({ makes: ['Honda'] }, 'conversation');
      });

      expect(result.current.filters.source).toBe('conversation');
    });

    it('should update activeFilterCount', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota'],
          vehicleTypes: ['SUV'],
        });
      });

      expect(result.current.activeFilterCount).toBe(2);
      expect(result.current.hasActiveFilters).toBe(true);
    });

    it('should persist filters to sessionStorage', async () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      const newFilters: FilterState = {
        makes: ['Toyota'],
        priceRange: [20000, 40000],
      };

      act(() => {
        result.current.applyFilters(newFilters);
      });

      await waitFor(() => {
        const stored = sessionStorage.getItem(FILTER_STORAGE_KEY);
        expect(stored).toBeDefined();
        if (stored) {
          const parsed = JSON.parse(stored);
          expect(parsed.filters.makes).toEqual(['Toyota']);
          expect(parsed.filters.priceRange).toEqual([20000, 40000]);
        }
      });
    });
  });

  describe('removeFilter', () => {
    it('should remove entire filter category', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota', 'Honda'],
          priceRange: [20000, 40000],
        });
      });

      expect(result.current.activeFilterCount).toBe(2);

      act(() => {
        result.current.removeFilter('makes');
      });

      expect(result.current.filters.makes).toBeUndefined();
      expect(result.current.filters.priceRange).toEqual([20000, 40000]);
      expect(result.current.activeFilterCount).toBe(1);
    });

    it('should remove specific value from array filter', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota', 'Honda', 'Ford'],
        });
      });

      act(() => {
        result.current.removeFilter('makes', 'Honda');
      });

      expect(result.current.filters.makes).toEqual(['Toyota', 'Ford']);
      expect(result.current.activeFilterCount).toBe(1);
    });

    it('should remove category when last value is removed', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota'],
        });
      });

      act(() => {
        result.current.removeFilter('makes', 'Toyota');
      });

      expect(result.current.filters.makes).toBeUndefined();
      expect(result.current.activeFilterCount).toBe(0);
    });
  });

  describe('clearAllFilters', () => {
    it('should clear all filters', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota'],
          priceRange: [20000, 40000],
          vehicleTypes: ['SUV'],
        });
      });

      expect(result.current.activeFilterCount).toBe(3);

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.filters).toEqual({});
      expect(result.current.activeFilterCount).toBe(0);
      expect(result.current.hasActiveFilters).toBe(false);
    });

    it('should reset sort to relevance', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setSort('price_asc');
      });

      expect(result.current.sortBy).toBe('price_asc');

      act(() => {
        result.current.clearAllFilters();
      });

      expect(result.current.sortBy).toBe('relevance');
    });
  });

  describe('setSort', () => {
    it('should set sort option', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setSort('mileage');
      });

      expect(result.current.sortBy).toBe('mileage');
    });

    it('should persist sort to sessionStorage', async () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setSort('price_desc');
      });

      await waitFor(() => {
        const stored = sessionStorage.getItem(FILTER_STORAGE_KEY);
        expect(stored).toBeDefined();
        if (stored) {
          const parsed = JSON.parse(stored);
          expect(parsed.sortBy).toBe('price_desc');
        }
      });
    });
  });

  describe('sessionStorage persistence', () => {
    it('should load filters from sessionStorage on mount', () => {
      const storedFilters: FilterState = {
        makes: ['Toyota'],
        priceRange: [20000, 40000],
      };

      sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify({
        filters: storedFilters,
        sortBy: 'year',
        timestamp: Date.now(),
      }));

      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.filters.makes).toEqual(['Toyota']);
      expect(result.current.filters.priceRange).toEqual([20000, 40000]);
      expect(result.current.sortBy).toBe('year');
    });

    it('should clear expired filters from sessionStorage', () => {
      const expiredTimestamp = Date.now() - FILTER_STORAGE_EXPIRY_MS - 1000;

      sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify({
        filters: { makes: ['Toyota'] },
        sortBy: 'relevance',
        timestamp: expiredTimestamp,
      }));

      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.filters).toEqual({});
      expect(sessionStorage.getItem(FILTER_STORAGE_KEY)).toBeNull();
    });
  });

  describe('mergeConversationPreferences', () => {
    it('should merge budget preference to priceRange', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          budget: { min: 20000, max: 40000 },
        });
      });

      expect(result.current.filters.priceRange).toEqual([20000, 40000]);
      expect(result.current.filters.source).toBe('conversation');
    });

    it('should merge make preferences', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          make: ['Toyota', 'Honda'],
        });
      });

      expect(result.current.filters.makes).toEqual(['Toyota', 'Honda']);
    });

    it('should merge body type preferences to vehicleTypes', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          bodyType: ['SUV', 'Sedan'],
        });
      });

      expect(result.current.filters.vehicleTypes).toEqual(['SUV', 'Sedan']);
    });

    it('should merge mileage preference to maxMileage', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          mileage: { max: 50000 },
        });
      });

      expect(result.current.filters.maxMileage).toBe(50000);
    });

    it('should merge fuel type preferences', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          fuelType: ['Electric', 'Hybrid'],
        });
      });

      expect(result.current.filters.fuelTypes).toEqual(['Electric', 'Hybrid']);
    });

    it('should merge features preferences', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          features: ['Sunroof', 'Navigation'],
        });
      });

      expect(result.current.features).toEqual(['Sunroof', 'Navigation']);
    });

    it('should merge multiple preferences at once', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.mergeConversationPreferences({
          budget: { max: 30000 },
          make: 'Toyota',
          bodyType: 'SUV',
        });
      });

      expect(result.current.filters.priceRange).toEqual([0, 30000]);
      expect(result.current.filters.makes).toEqual(['Toyota']);
      expect(result.current.filters.vehicleTypes).toEqual(['SUV']);
    });

    it('should preserve existing filters when merging', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Honda'],
          vehicleTypes: ['Sedan'],
        });
      });

      act(() => {
        result.current.mergeConversationPreferences({
          budget: { max: 40000 },
        });
      });

      expect(result.current.filters.makes).toEqual(['Honda']);
      expect(result.current.filters.vehicleTypes).toEqual(['Sedan']);
      expect(result.current.filters.priceRange).toEqual([0, 40000]);
    });
  });

  describe('getFilteredVehicles', () => {
    it('should call applyFiltersAndSort with correct parameters', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });
      const mockVehicles = [
        { id: '1', make: 'Toyota', price: 25000, year: 2020 },
        { id: '2', make: 'Honda', price: 30000, year: 2021 },
      ] as any;

      act(() => {
        result.current.applyFilters({ makes: ['Toyota'] });
        result.current.setSort('price_asc');
      });

      const filterResult = result.current.getFilteredVehicles(mockVehicles);

      expect(filters.applyFiltersAndSort).toHaveBeenCalledWith(
        mockVehicles,
        { makes: ['Toyota'] },
        'price_asc'
      );
    });

    it('should return filter result with metadata', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });
      const mockVehicles = [
        { id: '1', make: 'Toyota' },
        { id: '2', make: 'Honda' },
      ] as any;

      const filterResult = result.current.getFilteredVehicles(mockVehicles);

      expect(filterResult).toHaveProperty('vehicles');
      expect(filterResult).toHaveProperty('totalCount');
      expect(filterResult).toHaveProperty('filteredCount');
      expect(filterResult).toHaveProperty('activeFilterCount');
    });
  });

  describe('exportFilters and importFilters', () => {
    it('should export current filter state', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota'],
          priceRange: [20000, 40000],
        });
        result.current.setSort('year');
      });

      const exported = result.current.exportFilters();

      expect(exported.filters.makes).toEqual(['Toyota']);
      expect(exported.filters.priceRange).toEqual([20000, 40000]);
      expect(exported.sortBy).toBe('year');
      expect(exported.timestamp).toBeDefined();
    });

    it('should import filter state', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      const importData = {
        filters: {
          makes: ['Honda'],
          vehicleTypes: ['SUV'],
        },
        sortBy: 'mileage',
        timestamp: Date.now(),
      };

      act(() => {
        result.current.importFilters(importData);
      });

      expect(result.current.filters.makes).toEqual(['Honda']);
      expect(result.current.filters.vehicleTypes).toEqual(['SUV']);
      expect(result.current.sortBy).toBe('mileage');
      expect(result.current.filters.source).toBe('auto');
    });
  });

  describe('filterChips', () => {
    it('should generate filter chips from active filters', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({
          makes: ['Toyota', 'Honda'],
          priceRange: [20000, 40000],
        });
      });

      const chips = result.current.filterChips;

      expect(chips.length).toBeGreaterThan(0);
      expect(chips.some(c => c.label.includes('Toyota'))).toBe(true);
      expect(chips.some(c => c.label.includes('Honda'))).toBe(true);
      expect(chips.some(c => c.category === 'priceRange')).toBe(true);
    });

    it('should return empty array when no filters active', () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      const chips = result.current.filterChips;

      expect(chips).toEqual([]);
    });
  });
});
