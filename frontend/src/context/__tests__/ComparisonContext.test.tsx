import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { ComparisonProvider, useComparison } from '../ComparisonContext';
import type { Vehicle } from '../../app/types/api';

/**
 * Story 3-6: Unit Tests for ComparisonContext
 *
 * AC: Test comparison list management
 * AC: Test sessionStorage persistence (AC9 compliance)
 * AC: Test API integration
 * AC: Test edge cases (max 4 vehicles, duplicates)
 */

const mockVehicle: Vehicle = {
  id: 'test-vehicle-1',
  vin: 'TESTVIN123456789',
  make: 'Toyota',
  model: 'Camry',
  year: 2024,
  price: 28000,
  mileage: 15000,
  description: 'Test vehicle',
  features: ['Bluetooth', 'Backup Camera'],
  matchScore: 85,
  availabilityStatus: 'available',
  seller_id: 'seller-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockVehicle2: Vehicle = {
  ...mockVehicle,
  id: 'test-vehicle-2',
  make: 'Honda',
  model: 'Accord',
};

const mockVehicle3: Vehicle = {
  ...mockVehicle,
  id: 'test-vehicle-3',
  make: 'Nissan',
  model: 'Altima',
};

const mockVehicle4: Vehicle = {
  ...mockVehicle,
  id: 'test-vehicle-4',
  make: 'Hyundai',
  model: 'Sonata',
};

const mockVehicle5: Vehicle = {
  ...mockVehicle,
  id: 'test-vehicle-5',
  make: 'Kia',
  model: 'Optima',
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ComparisonProvider>{children}</ComparisonProvider>
);

describe('ComparisonContext', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test (AC9 compliance)
    sessionStorage.clear();
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('addToComparison', () => {
    it('should add a vehicle to comparison list', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      expect(result.current.comparisonList).toHaveLength(1);
      expect(result.current.comparisonList[0].id).toBe(mockVehicle.id);
      expect(result.current.canAddMore).toBe(true);
    });

    it('should prevent adding duplicate vehicles', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      expect(result.current.comparisonList).toHaveLength(1);
      expect(result.current.error).toBe('Vehicle already in comparison list');
    });

    it('should enforce maximum of 4 vehicles', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      // Add 4 vehicles
      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
        result.current.addToComparison(mockVehicle3);
        result.current.addToComparison(mockVehicle4);
      });

      expect(result.current.comparisonList).toHaveLength(4);
      expect(result.current.canAddMore).toBe(false);

      // Try to add 5th vehicle
      act(() => {
        result.current.addToComparison(mockVehicle5);
      });

      expect(result.current.comparisonList).toHaveLength(4);
      expect(result.current.error).toBe('Maximum 4 vehicles can be compared at once');
    });
  });

  describe('removeFromComparison', () => {
    it('should remove vehicle from comparison list', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
      });

      expect(result.current.comparisonList).toHaveLength(2);

      act(() => {
        result.current.removeFromComparison(mockVehicle.id);
      });

      expect(result.current.comparisonList).toHaveLength(1);
      expect(result.current.comparisonList[0].id).toBe(mockVehicle2.id);
    });

    it('should clear comparison result when list becomes empty', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      // Setup mock comparison result
      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
      });

      act(() => {
        result.current.removeFromComparison(mockVehicle.id);
        result.current.removeFromComparison(mockVehicle2.id);
      });

      expect(result.current.comparisonResult).toBeNull();
    });
  });

  describe('clearComparison', () => {
    it('should clear all vehicles from comparison list', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
        result.current.addToComparison(mockVehicle3);
      });

      expect(result.current.comparisonList).toHaveLength(3);

      act(() => {
        result.current.clearComparison();
      });

      expect(result.current.comparisonList).toHaveLength(0);
      expect(result.current.comparisonResult).toBeNull();
      expect(result.current.isComparing).toBe(false);
    });
  });

  describe('isVehicleInComparison', () => {
    it('should return true if vehicle is in comparison list', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      expect(result.current.isVehicleInComparison(mockVehicle.id)).toBe(true);
      expect(result.current.isVehicleInComparison(mockVehicle2.id)).toBe(false);
    });
  });

  describe('sessionStorage persistence', () => {
    it('should persist comparison list to sessionStorage', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
      });

      const stored = sessionStorage.getItem('otto_comparison_list');
      expect(stored).toBeTruthy();

      if (stored) {
        const parsed = JSON.parse(stored);
        expect(parsed).toHaveLength(2);
        expect(parsed[0].id).toBe(mockVehicle.id);
      }
    });

    it('should load comparison list from sessionStorage on mount', () => {
      // Pre-populate sessionStorage
      sessionStorage.setItem(
        'otto_comparison_list',
        JSON.stringify([
          { ...mockVehicle, addedAt: new Date().toISOString() },
          { ...mockVehicle2, addedAt: new Date().toISOString() },
        ])
      );

      const { result } = renderHook(() => useComparison(), { wrapper });

      expect(result.current.comparisonList).toHaveLength(2);
      expect(result.current.comparisonList[0].id).toBe(mockVehicle.id);
      expect(result.current.comparisonList[1].id).toBe(mockVehicle2.id);
    });

    it('should filter out expired entries (>30 minutes old)', () => {
      const expiredDate = new Date(Date.now() - 31 * 60 * 1000).toISOString();

      sessionStorage.setItem(
        'otto_comparison_list',
        JSON.stringify([
          { ...mockVehicle, addedAt: expiredDate }, // Expired
          { ...mockVehicle2, addedAt: new Date().toISOString() }, // Valid
        ])
      );

      const { result } = renderHook(() => useComparison(), { wrapper });

      expect(result.current.comparisonList).toHaveLength(1);
      expect(result.current.comparisonList[0].id).toBe(mockVehicle2.id);
    });
  });

  describe('openComparison API integration', () => {
    it('should call comparison API when opening comparison', async () => {
      const mockResponse = {
        comparison_id: 'test-comparison-1',
        vehicle_ids: [mockVehicle.id, mockVehicle2.id],
        comparison_results: [
          {
            vehicle_id: mockVehicle.id,
            vehicle_data: mockVehicle,
            specifications: [],
            features: [],
            price_analysis: {
              current_price: 28000,
              market_average: 29000,
              market_range: [25000, 32000],
              price_position: 'below_market',
              savings_amount: 1000,
              savings_percentage: 3.4,
              price_trend: 'stable',
              market_demand: 'medium',
            },
            overall_score: 0.85,
          },
          {
            vehicle_id: mockVehicle2.id,
            vehicle_data: mockVehicle2,
            specifications: [],
            features: [],
            price_analysis: {
              current_price: 27000,
              market_average: 28000,
              market_range: [24000, 31000],
              price_position: 'below_market',
              savings_amount: 1000,
              savings_percentage: 3.6,
              price_trend: 'stable',
              market_demand: 'medium',
            },
            overall_score: 0.88,
          },
        ],
        feature_differences: [],
        processing_time: 0.5,
        cached: false,
        timestamp: new Date().toISOString(),
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
      });

      await act(async () => {
        await result.current.openComparison();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/vehicles/compare'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: expect.stringContaining(mockVehicle.id),
        })
      );

      expect(result.current.comparisonResult).toEqual(mockResponse);
      expect(result.current.isComparing).toBe(true);
    });

    it('should handle API errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
      });

      await act(async () => {
        await result.current.openComparison();
      });

      expect(result.current.error).toBe('Network error');
      expect(result.current.loading).toBe(false);
    });

    it('should require at least 2 vehicles to open comparison', async () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      await act(async () => {
        await result.current.openComparison();
      });

      expect(result.current.error).toBe('Add at least 2 vehicles to compare');
      expect(result.current.isComparing).toBe(false);
    });
  });

  describe('closeComparison', () => {
    it('should close comparison view', () => {
      const { result } = renderHook(() => useComparison(), { wrapper });

      // Open comparison
      act(() => {
        result.current.addToComparison(mockVehicle);
        result.current.addToComparison(mockVehicle2);
        result.current.openComparison();
      });

      // Close comparison
      act(() => {
        result.current.closeComparison();
      });

      expect(result.current.isComparing).toBe(false);
    });
  });

  describe('error handling', () => {
    it('should clear error after 3 seconds', async () => {
      vi.useFakeTimers();

      // Pre-populate sessionStorage with a vehicle to trigger duplicate error
      sessionStorage.setItem(
        'otto_comparison_list',
        JSON.stringify([
          { ...mockVehicle, addedAt: new Date().toISOString() },
        ])
      );

      const { result } = renderHook(() => useComparison(), { wrapper });

      // Now adding the same vehicle should trigger duplicate error
      act(() => {
        result.current.addToComparison(mockVehicle);
      });

      expect(result.current.error).toBe('Vehicle already in comparison list');

      // Advance fake timers by 3000ms to trigger the setTimeout callback
      act(() => {
        vi.advanceTimersByTime(3000);
      });

      // Verify error was cleared by the setTimeout callback
      expect(result.current.error).toBeNull();

      vi.useRealTimers();
    });
  });
});
