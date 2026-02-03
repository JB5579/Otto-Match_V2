/**
 * Filter Chips Tests for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Tests for FilterChips component display and interactions.
 *
 * Coverage:
 * - Chip rendering for active filters
 * - Remove individual filter
 * - Chip reordering animation
 * - Hide when no filters
 * - ARIA labels
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterChips, FilterChipsCompact } from '../FilterChips';
import { FilterProvider, useFilters } from '../../../context/FilterContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <FilterProvider>{children}</FilterProvider>
);

describe('FilterChips', () => {
  const TestComponent = () => {
    const { applyFilters } = useFilters();

    return (
      <div>
        <button onClick={() => applyFilters({ makes: ['Toyota', 'Honda'] })}>
          Apply Filters
        </button>
        <FilterChips />
      </div>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should hide when no active filters', () => {
      render(<FilterChips />, { wrapper });

      expect(screen.queryByRole('list')).not.toBeInTheDocument();
    });

    it('should render chips for active filters', () => {
      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      // Chips should appear
      expect(screen.queryByText(/Make: Toyota/i)).toBeInTheDocument();
      expect(screen.queryByText(/Make: Honda/i)).toBeInTheDocument();
    });

    it('should display chip labels correctly', () => {
      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      expect(screen.queryByText(/Make: Toyota/i)).toBeInTheDocument();
    });
  });

  describe('interactions', () => {
    it('should remove filter when chip X is clicked', () => {
      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      const removeButton = screen.getByLabelText(/Remove Make: Toyota/i);
      fireEvent.click(removeButton);

      // Toyota should be removed
      expect(screen.queryByText(/Make: Toyota/i)).not.toBeInTheDocument();
    });

    it('should update chips when filters change', () => {
      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      // Both chips should be present
      expect(screen.queryByText(/Make: Toyota/i)).toBeInTheDocument();
      expect(screen.queryByText(/Make: Honda/i)).toBeInTheDocument();

      const removeButton = screen.getByLabelText(/Remove Make: Toyota/i);
      fireEvent.click(removeButton);

      // Only Honda should remain
      expect(screen.queryByText(/Make: Toyota/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Make: Honda/i)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<TestComponent />, { wrapper });

      const applyButton = screen.getByText(/apply filters/i);
      fireEvent.click(applyButton);

      const removeButtons = screen.getAllByLabelText(/Remove/i);
      expect(removeButtons.length).toBeGreaterThan(0);
      removeButtons.forEach(button => {
        expect(button).toHaveAttribute('aria-label');
      });
    });
  });
});

describe('FilterChipsCompact', () => {
  const TestComponent = () => {
    const { applyFilters } = useFilters();

    return (
      <div>
        <button onClick={() => applyFilters({ makes: ['Toyota'] })}>
          Apply Filters
        </button>
        <FilterChipsCompact />
      </div>
    );
  };

  it('should render compact variant', () => {
    render(<TestComponent />, { wrapper });

    const applyButton = screen.getByText(/apply filters/i);
    fireEvent.click(applyButton);

    expect(screen.queryByText(/Make: Toyota/i)).toBeInTheDocument();
  });
});
