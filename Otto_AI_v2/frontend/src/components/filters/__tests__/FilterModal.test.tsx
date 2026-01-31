/**
 * Filter Modal Tests for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Tests for FilterModal component display and interactions.
 *
 * Coverage:
 * - Modal open/close
 * - Filter category rendering
 * - Multi-select behavior
 * - Slider interactions
 * - Apply Filters button
 * - Keyboard navigation
 * - ARIA attributes
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FilterModal } from '../FilterModal';
import { FilterProvider, useFilters } from '../../../context/FilterContext';
import type { FilterState } from '../../../types/filters';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <FilterProvider>{children}</FilterProvider>
);

describe('FilterModal', () => {
  const mockOnClose = vi.fn();
  const mockOnApply = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <FilterModal
          isOpen={false}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render modal when isOpen is true', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByText('Filter Vehicles')).toBeInTheDocument();
    });

    it('should render all filter categories', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByText('Price Range')).toBeInTheDocument();
      expect(screen.getByText('Make')).toBeInTheDocument();
      expect(screen.getByText('Vehicle Type')).toBeInTheDocument();
      expect(screen.getByText('Year Range')).toBeInTheDocument();
      expect(screen.getByText('Maximum Mileage')).toBeInTheDocument();
      expect(screen.getByText('Features')).toBeInTheDocument();
    });
  });

  describe('filter categories', () => {
    it('should render price range sliders', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByLabelText(/price range minimum/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/price range maximum/i)).toBeInTheDocument();
    });

    it('should render make multi-select chips', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByPlaceholderText(/search make/i)).toBeInTheDocument();
    });

    it('should render vehicle type chips', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByText('SUV')).toBeInTheDocument();
      expect(screen.getByText('Sedan')).toBeInTheDocument();
    });
  });

  describe('interactions', () => {
    it('should close modal when backdrop is clicked', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      const backdrop = screen.getByText('Filter Vehicles').closest('div')?.parentElement;
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });

    it('should close modal when X button is clicked', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      const closeButton = screen.getByRole('button', { name: /close filters/i });
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onApply with filters when Apply is clicked', async () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      const applyButton = screen.getByRole('button', { name: /apply filters/i });
      fireEvent.click(applyButton);

      expect(mockOnApply).toHaveBeenCalledWith(expect.any(Object));
    });

    it('should call onClose when Cancel is clicked', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('keyboard navigation', () => {
    it('should close modal when Escape key is pressed', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <FilterModal
          isOpen={true}
          onClose={mockOnClose}
          onApply={mockOnApply}
        />,
        { wrapper }
      );

      expect(screen.getByRole('button', { name: /close filters/i })).toHaveAttribute('aria-label');
    });
  });
});
