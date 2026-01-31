/**
 * Sort Dropdown Tests for Story 3-7: Intelligent Grid Filtering and Sorting
 *
 * Tests for SortDropdown component display and interactions.
 *
 * Coverage:
 * - Dropdown open/close
 * - Sort option rendering
 * - Option selection
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - ARIA role="combobox" with expanded state
 * - Close on click outside
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SortDropdown } from '../SortDropdown';
import { FilterProvider, useFilters } from '../../../context/FilterContext';
import { SORT_LABELS } from '../../../types/filters';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <FilterProvider>{children}</FilterProvider>
);

describe('SortDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render sort dropdown button', () => {
      render(<SortDropdown />, { wrapper });

      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toHaveTextContent(SORT_LABELS.relevance);
    });

    it('should display current sort option', () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      expect(button).toHaveTextContent('Relevance');
    });

    it('should have correct ARIA attributes', () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      expect(button).toHaveAttribute('aria-haspopup', 'listbox');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-label');
    });
  });

  describe('dropdown menu', () => {
    it('should open dropdown when button is clicked', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'true');
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });
    });

    it('should render all sort options', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Price: Low to High')).toBeInTheDocument();
        expect(screen.getByText('Price: High to Low')).toBeInTheDocument();
        expect(screen.getByText('Mileage: Lowest First')).toBeInTheDocument();
        expect(screen.getByText('Year: Newest First')).toBeInTheDocument();
        expect(screen.getByText('Efficiency: Best First')).toBeInTheDocument();
      });
    });

    it('should close dropdown when option is selected', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      const option = screen.getByText('Price: Low to High');
      fireEvent.click(option);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });

    it('should close dropdown when clicking outside', async () => {
      render(
        <div>
          <SortDropdown />
          <div data-testid="outside">Outside</div>
        </div>,
        { wrapper }
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      const outside = screen.getByTestId('outside');
      fireEvent.mouseDown(outside);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });
  });

  describe('option selection', () => {
    it('should update sort when option is selected', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      const option = screen.getByText('Price: Low to High');
      fireEvent.click(option);

      await waitFor(() => {
        expect(button).toHaveTextContent('Price: Low to High');
      });
    });

    it('should mark selected option with checkmark', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      // Relevance is default, should have checkmark
      expect(screen.getAllByText('✓').length).toBeGreaterThan(0);
    });
  });

  describe('keyboard navigation', () => {
    it('should open dropdown on ArrowDown', () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.keyDown(button, { key: 'ArrowDown' });

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('should close dropdown on Escape', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      fireEvent.keyDown(button, { key: 'Escape' });

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });

    it('should select option on Enter', async () => {
      render(<SortDropdown />, { wrapper });

      const button = screen.getByRole('combobox');
      fireEvent.keyDown(button, { key: 'ArrowDown' });

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      fireEvent.keyDown(button, { key: 'Enter' });

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });
  });
});
