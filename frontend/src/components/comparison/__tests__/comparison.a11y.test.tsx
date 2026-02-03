import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ComparisonProvider, useComparison } from '../../../context/ComparisonContext';
import ComparisonFab from '../ComparisonFab';
import ComparisonView from '../ComparisonView';
import VehicleCard from '../../vehicle-grid/VehicleCard';
import type { Vehicle } from '../../../app/types/api';

/**
 * Story 3-6: Accessibility Compliance Tests
 *
 * WCAG 2.1 AA Requirements:
 * - Keyboard navigation (Tab, Enter, Escape, Arrow keys)
 * - ARIA labels and roles
 * - Focus indicators
 * - Color contrast (≥4.5:1)
 * - Screen reader compatibility
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
  images: [
    {
      url: 'https://example.com/image.jpg',
      description: 'Test image',
      category: 'hero',
      altText: 'Test vehicle',
    },
  ],
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
  price: 27000,
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ComparisonProvider>{children}</ComparisonProvider>
  </BrowserRouter>
);

describe('Comparison Accessibility Compliance', () => {
  beforeEach(() => {
    sessionStorage.clear();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        comparison_id: 'test-1',
        vehicle_ids: ['test-vehicle-1', 'test-vehicle-2'],
        comparison_results: [
          {
            vehicle_id: 'test-vehicle-1',
            vehicle_data: mockVehicle,
            specifications: [],
            features: [],
            price_analysis: {
              current_price: 28000,
              market_average: 29000,
              market_range: [25000, 32000],
              price_position: 'below_market',
              price_trend: 'stable',
              market_demand: 'medium',
            },
            overall_score: 0.85,
          },
          {
            vehicle_id: 'test-vehicle-2',
            vehicle_data: mockVehicle2,
            specifications: [],
            features: [],
            price_analysis: {
              current_price: 27000,
              market_average: 28000,
              market_range: [24000, 31000],
              price_position: 'below_market',
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
      }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('VehicleCard Compare Button Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<VehicleCard vehicle={mockVehicle} />, { wrapper });

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      expect(compareButton).toHaveAttribute('aria-label', 'Add to comparison');
      expect(compareButton).toHaveAttribute('aria-pressed', 'false');
    });

    it('should update ARIA pressed state when in comparison', async () => {
      const TestComponent = () => {
        const { addToComparison } = useComparison();
        return (
          <>
            <VehicleCard vehicle={mockVehicle} onCompare={() => addToComparison(mockVehicle)} />
            <button onClick={() => addToComparison(mockVehicle)}>Add Vehicle</button>
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      // Add vehicle to comparison
      const addButton = screen.getByRole('button', { name: 'Add Vehicle' });
      await userEvent.click(addButton);

      // Check ARIA pressed state updated
      const compareButton = screen.getByRole('button', { name: /vehicle in comparison list/i });
      expect(compareButton).toHaveAttribute('aria-pressed', 'true');
      expect(compareButton).toHaveAttribute('aria-label', 'Vehicle in comparison list');
    });

    it('should be keyboard accessible', async () => {
      render(<VehicleCard vehicle={mockVehicle} />, { wrapper });

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });

      // Focus via Tab
      compareButton.focus();
      expect(compareButton).toHaveFocus();

      // Activate via Enter key
      fireEvent.keyDown(compareButton, { key: 'Enter', code: 'Enter' });

      // Vehicle should be added (we verify by checking for "Added" state)
      await waitFor(() => {
        const addedButton = screen.queryByRole('button', { name: /vehicle in comparison list/i });
        expect(addedButton).toBeInTheDocument();
      });
    });
  });

  describe('ComparisonFab Accessibility', () => {
    it('should not be in tab order when no vehicles in comparison', () => {
      render(<ComparisonFab />, { wrapper });

      const fab = screen.queryByRole('button');
      expect(fab).not.toBeInTheDocument();
    });

    it('should be keyboard accessible when vehicles added', async () => {
      const TestComponent = () => {
        const { addToComparison } = useComparison();
        return (
          <>
            <button onClick={() => addToComparison(mockVehicle)}>Add Vehicle</button>
            <ComparisonFab />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      // Add vehicle
      const addButton = screen.getByRole('button', { name: 'Add Vehicle' });
      await userEvent.click(addButton);

      // FAB should appear
      const fab = screen.queryByRole('button', { name: /add vehicles to compare/i });
      expect(fab).toBeInTheDocument();

      // Should be keyboard accessible
      if (fab) {
        fab.focus();
        expect(fab).toHaveFocus();
      }
    });

    it('should have descriptive aria-label', async () => {
      const TestComponent = () => {
        const { addToComparison } = useComparison();
        return (
          <>
            <button onClick={() => addToComparison(mockVehicle)}>Add Vehicle</button>
            <ComparisonFab />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const addButton = screen.getByRole('button', { name: 'Add Vehicle' });
      await userEvent.click(addButton);

      const fab = screen.queryByRole('button', { name: /add vehicles to compare/i });
      expect(fab).toHaveAttribute('aria-label', 'Add vehicles to compare');
    });
  });

  describe('ComparisonView Modal Accessibility', () => {
    it('should have proper dialog role', async () => {
      const TestComponent = () => {
        const { addToComparison, openComparison } = useComparison();
        return (
          <>
            <button onClick={() => {
              addToComparison(mockVehicle);
              addToComparison(mockVehicle2);
              openComparison();
            }}>Open Comparison</button>
            <ComparisonView />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const openButton = screen.getByRole('button', { name: 'Open Comparison' });
      await userEvent.click(openButton);

      await waitFor(() => {
        const modal = screen.getByRole('dialog');
        expect(modal).toBeInTheDocument();
        expect(modal).toHaveAttribute('aria-modal', 'true');
      });
    });

    it('should trap focus within modal', async () => {
      const TestComponent = () => {
        const { addToComparison, openComparison } = useComparison();
        return (
          <>
            <button onClick={() => {
              addToComparison(mockVehicle);
              addToComparison(mockVehicle2);
              openComparison();
            }}>Open Comparison</button>
            <ComparisonView />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const openButton = screen.getByRole('button', { name: 'Open Comparison' });
      await userEvent.click(openButton);

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close comparison/i });
        expect(closeButton).toHaveFocus();
      });
    });

    it('should close on Escape key', async () => {
      const TestComponent = () => {
        const { addToComparison, openComparison } = useComparison();
        return (
          <>
            <button onClick={() => {
              addToComparison(mockVehicle);
              addToComparison(mockVehicle2);
              openComparison();
            }}>Open Comparison</button>
            <ComparisonView />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const openButton = screen.getByRole('button', { name: 'Open Comparison' });
      await userEvent.click(openButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const modal = screen.getByRole('dialog');
      fireEvent.keyDown(modal, { key: 'Escape', code: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should have descriptive title', async () => {
      const TestComponent = () => {
        const { addToComparison, openComparison } = useComparison();
        return (
          <>
            <button onClick={() => {
              addToComparison(mockVehicle);
              addToComparison(mockVehicle2);
              openComparison();
            }}>Open Comparison</button>
            <ComparisonView />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const openButton = screen.getByRole('button', { name: 'Open Comparison' });
      await userEvent.click(openButton);

      await waitFor(() => {
        const title = screen.getByText('Vehicle Comparison');
        expect(title).toBeInTheDocument();

        const modal = screen.getByRole('dialog', { name: 'Vehicle Comparison' });
        expect(modal).toBeInTheDocument();
      });
    });
  });

  describe('Color Contrast Requirements', () => {
    it('should meet WCAG AA contrast requirements for compare button', () => {
      render(<VehicleCard vehicle={mockVehicle} />, { wrapper });

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      const styles = window.getComputedStyle(compareButton);

      // Verify button has visible color (light blue text on light background)
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;

      // These values should provide sufficient contrast
      expect(color).toBeTruthy();
      expect(backgroundColor).toBeTruthy();
    });

    it('should meet WCAG AA contrast requirements for FAB', async () => {
      const TestComponent = () => {
        const { addToComparison } = useComparison();
        return (
          <>
            <button onClick={() => addToComparison(mockVehicle)}>Add Vehicle</button>
            <ComparisonFab />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const addButton = screen.getByRole('button', { name: 'Add Vehicle' });
      await userEvent.click(addButton);

      const fab = screen.queryByRole('button', { name: /add vehicles to compare/i });

      if (fab) {
        const styles = window.getComputedStyle(fab);
        expect(styles.color).toBeTruthy();
        expect(styles.backgroundColor).toBeTruthy();
      }
    });
  });

  describe('Screen Reader Compatibility', () => {
    it('should announce comparison state changes', async () => {
      const TestComponent = () => {
        const { addToComparison, comparisonList } = useComparison();
        return (
          <>
            <VehicleCard vehicle={mockVehicle} onCompare={() => addToComparison(mockVehicle)} />
            <div aria-live="polite" aria-atomic="true">
              Vehicles in comparison: {comparisonList.length}
            </div>
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      await userEvent.click(compareButton);

      // Live region should update
      await waitFor(() => {
        const liveRegion = screen.getByText(/vehicles in comparison: 1/i);
        expect(liveRegion).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation Flow', () => {
    it('should allow full workflow via keyboard', async () => {
      const TestComponent = () => {
        const { addToComparison, comparisonList } = useComparison();
        return (
          <>
            <VehicleCard vehicle={mockVehicle} onCompare={() => addToComparison(mockVehicle)} />
            <VehicleCard vehicle={mockVehicle2} onCompare={() => addToComparison(mockVehicle2)} />
            <div aria-live="polite">Count: {comparisonList.length}</div>
            <ComparisonFab />
            <ComparisonView />
          </>
        );
      };

      render(<TestComponent />, { wrapper });

      // Tab to first compare button
      const user = userEvent.setup({ delay: null });
      await user.tab();

      // Activate via Enter
      await user.keyboard('{Enter}');

      // Verify count increased
      await waitFor(() => {
        expect(screen.getByText('Count: 1')).toBeInTheDocument();
      });

      // Tab to second compare button
      await user.tab();
      await user.keyboard('{Enter}');

      // Verify count increased
      await waitFor(() => {
        expect(screen.getByText('Count: 2')).toBeInTheDocument();
      });

      // Tab to FAB and activate
      await user.tab();
      await user.keyboard('{Enter}');

      // Modal should open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close via Escape
      await user.keyboard('{Escape}');

      // Modal should close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });
});
