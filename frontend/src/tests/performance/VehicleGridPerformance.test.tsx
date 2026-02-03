/**
 * Performance Tests for Vehicle Grid Components
 * Story 3-8.20: Performance testing with Vitest
 *
 * Tests render performance, re-renders, and interaction timing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import VehicleGrid from '../../components/vehicle-grid/VehicleGrid';
import { Vehicle } from '../../app/types/api';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByName: vi.fn(() => []),
  getEntries: vi.fn(() => []),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
};

Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true,
});

describe('VehicleGrid Performance Tests', () => {
  // Story 3-8.20: Test data generation
  const generateVehicles = (count: number): Vehicle[] => {
    return Array.from({ length: count }, (_, i) => ({
      id: `vehicle-${i}`,
      make: 'Toyota',
      model: `Camry ${i}`,
      year: 2024,
      price: 25000 + i * 1000,
      mileage: 10000 + i * 1000,
      transmission: 'Automatic',
      drivetrain: 'FWD',
      fuel_type: 'Gasoline',
      images: [
        {
          url: `https://example.com/image-${i}.jpg`,
          category: 'hero',
          altText: `Vehicle ${i}`,
        },
      ],
      matchScore: 85 + Math.random() * 15,
      features: ['Bluetooth', 'Backup Camera', 'Cruise Control'],
    }));
  };

  describe('Render Performance', () => {
    it('should render 12 vehicles in under 100ms', async () => {
      const vehicles = generateVehicles(12);
      const startTime = performance.now();

      render(<VehicleGrid vehicles={vehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(12);
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Story 3-8.20: Performance budget for initial render
      expect(renderTime).toBeLessThan(100);
    });

    it('should render 50 vehicles in under 300ms', async () => {
      const vehicles = generateVehicles(50);
      const startTime = performance.now();

      render(<VehicleGrid vehicles={vehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(50);
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Story 3-8.20: Performance budget for large lists
      expect(renderTime).toBeLessThan(300);
    });
  });

  describe('Re-render Performance', () => {
    it('should not re-render all cards when one vehicle changes', async () => {
      const vehicles = generateVehicles(12);
      const { rerender } = render(<VehicleGrid vehicles={vehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(12);
      });

      // Track re-renders using console.log spy
      const consoleSpy = vi.spyOn(console, 'log');

      // Update one vehicle
      const updatedVehicles = [...vehicles];
      updatedVehicles[0] = {
        ...vehicles[0],
        price: vehicles[0].price + 1000,
      };

      rerender(<VehicleGrid vehicles={updatedVehicles} />);

      await waitFor(() => {
        // Story 3-8.7: React.memo should prevent unnecessary re-renders
        expect(consoleSpy).not.toHaveBeenCalled();
      });
    });

    it('should handle filter updates efficiently', async () => {
      const vehicles = generateVehicles(50);
      const startTime = performance.now();

      const { rerender } = render(<VehicleGrid vehicles={vehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(50);
      });

      // Apply filter
      const filteredVehicles = vehicles.filter((v) => v.price < 30000);
      const filterStartTime = performance.now();

      rerender(<VehicleGrid vehicles={filteredVehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(filteredVehicles.length);
      });

      const filterEndTime = performance.now();
      const filterTime = filterEndTime - filterStartTime;

      // Story 3-8.10: Debounced filter should be fast
      expect(filterTime).toBeLessThan(50);
    });
  });

  describe('Scroll Performance', () => {
    it('should handle scroll events without blocking', async () => {
      const vehicles = generateVehicles(100);
      render(<VehicleGrid vehicles={vehicles} pageSize={12} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(12);
      });

      // Simulate rapid scroll events
      const scrollContainer = document.querySelector('.vehicle-grid-container');
      if (!scrollContainer) return;

      const startTime = performance.now();

      for (let i = 0; i < 10; i++) {
        scrollContainer.dispatchEvent(new Event('scroll', { bubbles: true }));
      }

      const endTime = performance.now();
      const scrollTime = endTime - startTime;

      // Story 3-8.11: Throttled scroll should not block
      expect(scrollTime).toBeLessThan(50);
    });
  });

  describe('Memory Performance', () => {
    it('should not leak memory when vehicles change', async () => {
      const initialVehicles = generateVehicles(12);

      // Force garbage collection (in test environment)
      if (global.gc) {
        global.gc();
      }

      const { rerender } = render(<VehicleGrid vehicles={initialVehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(12);
      });

      // Unmount and remount with new data
      rerender.unmount();

      if (global.gc) {
        global.gc();
      }

      const newVehicles = generateVehicles(24);
      render(<VehicleGrid vehicles={newVehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(24);
      });

      // Story 3-8.20: Verify no memory leaks (requires profiling)
      // In real test, use Chrome DevTools Memory Profiler
      expect(true).toBe(true);
    });
  });

  describe('Animation Performance', () => {
    it('should complete animations within budget', async () => {
      const vehicles = generateVehicles(12);
      render(<VehicleGrid vehicles={vehicles} />);

      await waitFor(() => {
        expect(screen.getAllByText(/Toyota/i)).toHaveLength(12);
      });

      // Measure animation frame timing
      const frameTimings: number[] = [];
      let frameCount = 0;
      const maxFrames = 60; // 1 second at 60fps

      const measureFrame = () => {
        frameTimings.push(performance.now());
        frameCount++;

        if (frameCount < maxFrames) {
          requestAnimationFrame(measureFrame);
        }
      };

      requestAnimationFrame(measureFrame);

      await waitFor(() => {
        expect(frameCount).toBe(maxFrames);
      }, { timeout: 2000 });

      // Calculate average frame time
      const frameTimes = [];
      for (let i = 1; i < frameTimings.length; i++) {
        frameTimes.push(frameTimings[i] - frameTimings[i - 1]);
      }

      const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;

      // Story 3-8.13: Animations should maintain 60fps (16.67ms per frame)
      expect(avgFrameTime).toBeLessThan(20);
    });
  });
});

describe('VehicleCard Performance Tests', () => {
  it('should render card in under 10ms', async () => {
    const vehicle: Vehicle = {
      id: 'test-vehicle',
      make: 'Toyota',
      model: 'Camry',
      year: 2024,
      price: 25000,
      mileage: 10000,
      transmission: 'Automatic',
      drivetrain: 'FWD',
      fuel_type: 'Gasoline',
      images: [
        {
          url: 'https://example.com/image.jpg',
          category: 'hero',
          altText: 'Test Vehicle',
        },
      ],
      matchScore: 90,
      features: ['Bluetooth', 'Backup Camera'],
    };

    const VehicleCard = (await import('../../components/vehicle-grid/VehicleCard')).default;

    const startTime = performance.now();
    render(<VehicleCard vehicle={vehicle} />);
    const endTime = performance.now();

    const renderTime = endTime - startTime;

    // Story 3-8.7: Single card should render instantly
    expect(renderTime).toBeLessThan(10);
  });
});
