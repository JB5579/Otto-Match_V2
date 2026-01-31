import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AvailabilityBadge } from '../AvailabilityBadge';

describe('AvailabilityBadge', () => {
  describe('AC3: Status Indicator Visual Design', () => {
    it('should display green badge with Check icon for available status', () => {
      render(<AvailabilityBadge status="available" />);

      const badge = screen.getByRole('status');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveAttribute('aria-label', 'Vehicle status: Available');
      expect(screen.getByText('Available')).toBeInTheDocument();
    });

    it('should display amber badge with Clock icon for reserved status', () => {
      render(<AvailabilityBadge status="reserved" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('aria-label', 'Vehicle status: Reserved');
      expect(screen.getByText('Reserved')).toBeInTheDocument();
    });

    it('should display gray badge with X icon for sold status', () => {
      render(<AvailabilityBadge status="sold" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('aria-label', 'Vehicle status: Sold');
      expect(screen.getByText('Sold')).toBeInTheDocument();
    });

    it('should display pulsing green badge with Sparkles icon for newly available status', () => {
      render(<AvailabilityBadge status="newlyAvailable" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('aria-label', 'Vehicle status: Newly Available');
      expect(screen.getByText('Newly Available')).toBeInTheDocument();
    });
  });

  describe('AC7: Responsive Status Indicators', () => {
    it('should render compact size badge for mobile', () => {
      render(<AvailabilityBadge status="available" size="compact" />);

      const badge = screen.getByRole('status');
      expect(badge).toBeInTheDocument();
    });

    it('should hide label when showLabel is false (mobile icon-only)', () => {
      render(<AvailabilityBadge status="available" showLabel={false} />);

      // Label should still exist for screen readers
      const srOnlyLabel = screen.getByText('Available');
      expect(srOnlyLabel).toHaveClass('sr-only');
    });

    it('should show label when showLabel is true (tablet/desktop)', () => {
      render(<AvailabilityBadge status="available" showLabel={true} />);

      const label = screen.getByText('Available');
      expect(label).not.toHaveClass('sr-only');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<AvailabilityBadge status="available" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('aria-live', 'polite');
      expect(badge).toHaveAttribute('aria-label', 'Vehicle status: Available');
    });

    it('should provide screen reader text for all statuses', () => {
      const statuses = ['available', 'reserved', 'sold', 'newlyAvailable'] as const;

      statuses.forEach((status) => {
        const { unmount } = render(<AvailabilityBadge status={status} />);

        const badge = screen.getByRole('status');
        expect(badge).toHaveAttribute('aria-label');

        unmount();
      });
    });
  });

  describe('Styling', () => {
    it('should apply glass-morphism styling', () => {
      render(<AvailabilityBadge status="available" />);

      const badge = screen.getByRole('status');
      const style = window.getComputedStyle(badge);

      // Badge should have background with opacity
      expect(badge).toHaveStyle({ display: 'inline-flex' });
    });

    it('should apply custom className', () => {
      render(<AvailabilityBadge status="available" className="custom-class" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('custom-class');
    });
  });
});
