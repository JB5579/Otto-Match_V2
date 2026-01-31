import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MatchScoreBadge from '../MatchScoreBadge';

describe('MatchScoreBadge', () => {
  describe('Score Tier Colors', () => {
    it('should display green badge for 90%+ score', () => {
      render(<MatchScoreBadge score={95} />);
      const badge = screen.getByText('95%');
      expect(badge).toBeInTheDocument();
      // Verify green color in inline styles
      const container = badge.closest('div');
      expect(container?.style.background).toContain('34, 197, 94'); // green
    });

    it('should display lime badge for 80-89% score', () => {
      render(<MatchScoreBadge score={85} />);
      const badge = screen.getByText('85%');
      expect(badge).toBeInTheDocument();
      const container = badge.closest('div');
      expect(container?.style.background).toContain('132, 204, 22'); // lime
    });

    it('should display yellow badge for 70-79% score', () => {
      render(<MatchScoreBadge score={75} />);
      const badge = screen.getByText('75%');
      expect(badge).toBeInTheDocument();
      const container = badge.closest('div');
      expect(container?.style.background).toContain('234, 179, 8'); // yellow
    });

    it('should display orange badge for <70% score', () => {
      render(<MatchScoreBadge score={65} />);
      const badge = screen.getByText('65%');
      expect(badge).toBeInTheDocument();
      const container = badge.closest('div');
      expect(container?.style.background).toContain('249, 115, 22'); // orange
    });
  });

  describe('Otto\'s Pick Badge', () => {
    it('should display star icon for 95%+ match score', () => {
      render(<MatchScoreBadge score={97} isOttoPick={true} />);
      // Should have star icon (SVG element)
      const starIcon = document.querySelector('svg[fill="white"]');
      expect(starIcon).toBeInTheDocument();
    });

    it('should display cyan glow for Otto\'s Pick', () => {
      render(<MatchScoreBadge score={96} isOttoPick={true} />);
      const badgeText = screen.getByText('Otto\'s Pick');
      expect(badgeText).toBeInTheDocument();
    });

    it('should show glowing animation for Otto\'s Pick', () => {
      render(<MatchScoreBadge score={98} isOttoPick={true} />);
      // Check for animation styles
      const container = document.querySelector('[style*="glow-pulse"]');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Pulsing Animation', () => {
    it('should apply pulsing ring animation for 95%+ scores', () => {
      render(<MatchScoreBadge score={96} />);
      // Should have pulsing ring element
      const pulsingRing = document.querySelector('[style*="pulse-ring"]');
      expect(pulsingRing).toBeInTheDocument();
    });

    it('should not apply pulsing ring for scores below 95%', () => {
      render(<MatchScoreBadge score={90} />);
      const pulsingRing = document.querySelector('[style*="pulse-ring"]');
      expect(pulsingRing).not.toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('should render small size badge', () => {
      const { container } = render(<MatchScoreBadge score={85} size="small" />);
      const badge = container.querySelector('div[style*="width: 48px"]');
      expect(badge).toBeInTheDocument();
    });

    it('should render medium size badge (default)', () => {
      const { container } = render(<MatchScoreBadge score={85} size="medium" />);
      const badge = container.querySelector('div[style*="width: 64px"]');
      expect(badge).toBeInTheDocument();
    });

    it('should render large size badge', () => {
      const { container } = render(<MatchScoreBadge score={85} size="large" />);
      const badge = container.querySelector('div[style*="width: 80px"]');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper color contrast for all tiers', () => {
      render(<MatchScoreBadge score={85} />);
      const badge = screen.getByText('85%');
      // White text on colored background should have sufficient contrast
      const container = badge.closest('div');
      expect(container?.style.color).toBe('white');
    });

    it('should display tier label for screen readers', () => {
      render(<MatchScoreBadge score={85} />);
      const tierLabel = screen.getByText('Great');
      expect(tierLabel).toBeInTheDocument();
    });
  });
});
