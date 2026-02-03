/**
 * Filter Integration Tests for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Integration tests for filter + sort functionality with VehicleContext.
 *
 * Coverage:
 * - Apply filters → grid update
 * - Sort → grid reorder
 * - Filter + sort combination
 * - Clear all filters → reset
 * - Filter persistence across page reload
 * - Empty state for no results
 * - Filter + SSE update integration
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import { FilterProvider, useFilters } from '../../../context/FilterContext';
import { VehicleProvider, useVehicleContext } from '../../../context/VehicleContext';
import { FilterBar } from '../FilterBar';
import { FilterEmptyState } from '../FilterEmptyState';
import type { Vehicle } from '../../../app/types/api';
import type { FilterState, SortOption } from '../../../types/filters';

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

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <FilterProvider>
    <VehicleProvider>{children}</VehicleProvider>
  </FilterProvider>
);

const mockVehicles: Vehicle[] = [
  {
    id: '1',
    vin: 'VIN1',
    make: 'Toyota',
    model: 'Camry',
    year: 2020,
    price: 25000,
    mileage: 30000,
    body_type: 'Sedan',
    fuel_type: 'Gasoline',
    transmission: 'Automatic',
    drivetrain: 'FWD',
    color: 'Blue',
    features: ['Bluetooth', 'Backup Camera'],
    matchScore: 85,
    seller_id: 'seller1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: '2',
    vin: 'VIN2',
    make: 'Honda',
    model: 'CR-V',
    year: 2021,
    price: 30000,
    mileage: 25000,
    body_type: 'SUV',
    fuel_type: 'Gasoline',
    transmission: 'Automatic',
    drivetrain: 'AWD',
    color: 'Red',
    features: ['Sunroof', 'Navigation'],
    matchScore: 78,
    seller_id: 'seller1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: '3',
    vin: 'VIN3',
    make: 'Toyota',
    model: 'RAV4',
    year: 2022,
    price: 35000,
    mileage: 15000,
    body_type: 'SUV',
    fuel_type: 'Hybrid',
    transmission: 'Automatic',
    drivetrain: 'AWD',
    color: 'White',
    features: ['Sunroof', 'Leather Seats'],
    matchScore: 92,
    seller_id: 'seller1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
];

describe('Filter Integration', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  describe('apply filters → grid update', () => {
    it('should update filtered vehicles when filters are applied', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.applyFilters({ makes: ['Toyota'] });
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should return 2 Toyota vehicles
      expect(filteredResult.vehicles.length).toBe(2);
      expect(filteredResult.activeFilterCount).toBe(1);
    });

    it('should update vehicle count display', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.applyFilters({ makes: ['Toyota'] });
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      expect(filteredResult.totalCount).toBe(3);
      expect(filteredResult.filteredCount).toBe(2);
    });
  });

  describe('sort → grid reorder', () => {
    it('should reorder vehicles by price ascending', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('price_asc');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should be ordered by price: 25000, 30000, 35000
      expect(filteredResult.vehicles[0].price).toBe(25000);
      expect(filteredResult.vehicles[1].price).toBe(30000);
      expect(filteredResult.vehicles[2].price).toBe(35000);
    });

    it('should reorder vehicles by price descending', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('price_desc');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should be ordered by price: 35000, 30000, 25000
      expect(filteredResult.vehicles[0].price).toBe(35000);
      expect(filteredResult.vehicles[1].price).toBe(30000);
      expect(filteredResult.vehicles[2].price).toBe(25000);
    });

    it('should reorder vehicles by year newest first', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('year');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should be ordered by year: 2022, 2021, 2020
      expect(filteredResult.vehicles[0].year).toBe(2022);
      expect(filteredResult.vehicles[1].year).toBe(2021);
      expect(filteredResult.vehicles[2].year).toBe(2020);
    });

    it('should reorder vehicles by mileage lowest first', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('mileage');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should be ordered by mileage: 15000, 25000, 30000
      expect(filteredResult.vehicles[0].mileage).toBe(15000);
      expect(filteredResult.vehicles[1].mileage).toBe(25000);
      expect(filteredResult.vehicles[2].mileage).toBe(30000);
    });

    it('should reorder vehicles by relevance (match score)', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('relevance');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should be ordered by match score: 92, 85, 78
      expect(filteredResult.vehicles[0].matchScore).toBe(92);
      expect(filteredResult.vehicles[1].matchScore).toBe(85);
      expect(filteredResult.vehicles[2].matchScore).toBe(78);
    });
  });

  describe('filter + sort combination', () => {
    it('should apply filters and sort together', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.applyFilters({ makes: ['Toyota'] });
        result.current.filters.setSort('price_asc');
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should return 2 Toyota vehicles sorted by price
      expect(filteredResult.vehicles.length).toBe(2);
      expect(filteredResult.vehicles[0].make).toBe('Toyota');
      expect(filteredResult.vehicles[0].price).toBe(25000);
      expect(filteredResult.vehicles[1].make).toBe('Toyota');
      expect(filteredResult.vehicles[1].price).toBe(35000);
    });

    it('should apply filters within sorted results', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.setSort('price_desc');
        result.current.filters.applyFilters({ vehicleTypes: ['SUV'] });
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should return 2 SUVs sorted by price descending
      expect(filteredResult.vehicles.length).toBe(2);
      expect(filteredResult.vehicles[0].price).toBe(35000); // RAV4
      expect(filteredResult.vehicles[1].price).toBe(30000); // CR-V
    });
  });

  describe('clear all filters → reset', () => {
    it('should clear all filters and reset sort', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      act(() => {
        result.current.filters.applyFilters({
          makes: ['Toyota'],
          vehicleTypes: ['SUV'],
        });
        result.current.filters.setSort('price_desc');
      });

      expect(result.current.filters.activeFilterCount).toBe(2);
      expect(result.current.filters.sortBy).toBe('price_desc');

      act(() => {
        result.current.filters.clearAllFilters();
      });

      expect(result.current.filters.activeFilterCount).toBe(0);
      expect(result.current.filters.sortBy).toBe('relevance');

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should return all vehicles
      expect(filteredResult.vehicles.length).toBe(3);
      expect(filteredResult.activeFilterCount).toBe(0);
    });
  });

  describe('filter persistence across page reload', () => {
    it('should persist filters to sessionStorage', async () => {
      const { result, unmount } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.applyFilters({ makes: ['Toyota', 'Honda'] });
        result.current.setSort('price_asc');
      });

      unmount();

      // Check sessionStorage
      const stored = sessionStorage.getItem('otto_vehicle_filters');
      expect(stored).toBeDefined();

      if (stored) {
        const parsed = JSON.parse(stored);
        expect(parsed.filters.makes).toEqual(['Toyota', 'Honda']);
        expect(parsed.sortBy).toBe('price_asc');
      }
    });

    it('should restore filters from sessionStorage on mount', () => {
      // Set up sessionStorage with filters
      sessionStorage.setItem('otto_vehicle_filters', JSON.stringify({
        filters: {
          makes: ['Toyota'],
          vehicleTypes: ['SUV'],
        },
        sortBy: 'mileage',
        timestamp: Date.now(),
      }));

      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.filters.makes).toEqual(['Toyota']);
      expect(result.current.filters.vehicleTypes).toEqual(['SUV']);
      expect(result.current.sortBy).toBe('mileage');
    });
  });

  describe('empty state for no results', () => {
    it('should show empty state when filters match zero vehicles', () => {
      const TestComponent = () => {
        const { applyFilters, getFilteredVehicles } = useFilters();
        const { getFilteredVehicles: getVehicles } = useVehicleContext();

        return (
          <div>
            <button onClick={() => applyFilters({ makes: ['NonExistentMake'] })}>
              Apply Filters
            </button>
            <div>
              {getVehicles(getFilteredVehicles().filters, getFilteredVehicles().sortBy).vehicles.length === 0 && (
                <FilterEmptyState />
              )}
            </div>
          </div>
        );
      };

      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      // Empty state should appear
      expect(screen.getByText(/no vehicles match your filters/i)).toBeInTheDocument();
    });

    it('should not show empty state when vehicles match filters', () => {
      const TestComponent = () => {
        const { getFilteredVehicles } = useFilters();
        const { getFilteredVehicles: getVehicles } = useVehicleContext();

        const result = getVehicles(getFilteredVehicles().filters, getFilteredVehicles().sortBy);

        return (
          <div>
            {result.vehicles.length === 0 && <FilterEmptyState />}
            <div data-testid="vehicle-count">{result.vehicles.length}</div>
          </div>
        );
      };

      render(<TestComponent />, { wrapper });

      expect(screen.queryByText(/no vehicles match your filters/i)).not.toBeInTheDocument();
      expect(screen.getByTestId('vehicle-count')).toHaveTextContent('3');
    });
  });

  describe('FilterBar integration', () => {
    it('should show active filter count in FilterBar', () => {
      const TestComponent = () => {
        const { applyFilters, activeFilterCount } = useFilters();

        return (
          <div>
            <button onClick={() => applyFilters({ makes: ['Toyota', 'Honda'] })}>
              Apply Filters
            </button>
            <div data-testid="filter-count">{activeFilterCount}</div>
          </div>
        );
      };

      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      expect(screen.getByTestId('filter-count')).toHaveTextContent('1');
    });

    it('should display filter chips in FilterBar', () => {
      const TestComponent = () => {
        const { applyFilters, filterChips } = useFilters();

        return (
          <div>
            <button onClick={() => applyFilters({ makes: ['Toyota'] })}>
              Apply Filters
            </button>
            <div>
              {filterChips.map(chip => (
                <div key={chip.key}>{chip.label}</div>
              ))}
            </div>
          </div>
        );
      };

      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      expect(screen.getByText(/Make: Toyota/i)).toBeInTheDocument();
    });
  });

  describe('SSE update integration', () => {
    it('should preserve filters when SSE updates arrive', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      // Apply filters
      act(() => {
        result.current.filters.applyFilters({ makes: ['Toyota'] });
      });

      // Simulate SSE update
      const newVehicles: Vehicle[] = [
        ...mockVehicles,
        {
          id: '4',
          vin: 'VIN4',
          make: 'Nissan', // Different make
          model: 'Altima',
          year: 2021,
          price: 28000,
          seller_id: 'seller1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      act(() => {
        result.current.vehicles.updateVehicles(newVehicles);
      });

      // Filters should still be active
      expect(result.current.filters.activeFilterCount).toBe(1);
      expect(result.current.filters.makes).toEqual(['Toyota']);

      // Filtered result should still only show Toyota vehicles
      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      expect(filteredResult.vehicles.length).toBe(2); // Still 2 Toyotas
      expect(filteredResult.vehicles.every(v => v.make === 'Toyota')).toBe(true);
    });

    it('should apply filters to new vehicles from SSE', () => {
      const { result } = renderHook(() => ({
        filters: useFilters(),
        vehicles: useVehicleContext(),
      }), { wrapper });

      // Apply filters for SUV
      act(() => {
        result.current.filters.applyFilters({ vehicleTypes: ['SUV'] });
      });

      // Simulate SSE update with new vehicle
      const newVehicles: Vehicle[] = [
        ...mockVehicles,
        {
          id: '4',
          vin: 'VIN4',
          make: 'Ford',
          model: 'Escape',
          year: 2022,
          price: 32000,
          body_type: 'SUV', // Matches filter
          seller_id: 'seller1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ];

      act(() => {
        result.current.vehicles.updateVehicles(newVehicles);
      });

      const filteredResult = result.current.vehicles.getFilteredVehicles(
        result.current.filters.filters,
        result.current.filters.sortBy
      );

      // Should show 3 SUVs (2 original + 1 new)
      expect(filteredResult.vehicles.length).toBe(3);
      expect(filteredResult.vehicles.every(v => v.body_type === 'SUV')).toBe(true);
    });
  });
});
