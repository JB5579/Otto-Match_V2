import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '../../../test/test-utils';
import VehicleCard from '../VehicleCard';
import { Vehicle } from '../../../app/types/api';

const mockVehicle: Vehicle = {
  id: 'test-vehicle-1',
  vin: 'TEST123',
  make: 'Toyota',
  model: 'Camry',
  year: 2023,
  trim: 'SE',
  mileage: 15000,
  price: 28000,
  originalPrice: 30000,
  savings: 2000,
  color: 'Blue',
  transmission: 'Automatic',
  fuel_type: 'Gasoline',
  body_type: 'Sedan',
  drivetrain: 'FWD',
  condition: 'Excellent',
  description: 'A great family sedan',
  images: [
    {
      url: 'https://example.com/image.jpg',
      description: 'Hero image',
      category: 'hero',
      altText: '2023 Toyota Camry SE',
    },
  ],
  features: ['Backup Camera', 'Bluetooth', 'Lane Assist', 'Apple CarPlay'],
  matchScore: 92,
  availabilityStatus: 'available',
  currentViewers: 3,
  ottoRecommendation: 'Perfect for families seeking reliability',
  seller_id: 'seller-1',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
};

describe('VehicleCard', () => {
  beforeEach(() => {
    // Clear comparison state before each test
    localStorage.clear();
  });

  describe('Rendering', () => {
    it('should render vehicle title correctly', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should display hero image', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      const image = screen.getByAltText('2023 Toyota Camry SE');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/image.jpg');
      expect(image).toHaveAttribute('loading', 'lazy');
    });

    it('should display match score badge', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      // MatchScoreBadge should show 92%
      const badge = screen.getByText('92%');
      expect(badge).toBeInTheDocument();
    });

    it('should display vehicle specs', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Automatic')).toBeInTheDocument();
      expect(screen.getByText('FWD')).toBeInTheDocument();
    });

    it('should display price with original price strikethrough', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
      // Original price should be present and struck through
      const originalPrice = screen.getByText(/\$30,000/);
      expect(originalPrice).toBeInTheDocument();
      expect(originalPrice).toHaveStyle({ textDecoration: 'line-through' });
    });

    it('should display savings callout', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText(/below market/i)).toBeInTheDocument();
    });

    it('should display feature tags', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();
      expect(screen.getByText('Bluetooth')).toBeInTheDocument();
      expect(screen.getByText('Lane Assist')).toBeInTheDocument();
    });

    it('should display social proof - current viewers', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText(/3 viewing/)).toBeInTheDocument();
    });

    it('should display Otto recommendation', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
    });

    it('should not display availability badge for available status', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      // Available status should not show a badge (only reserved/sold show badges)
      expect(screen.queryByText('available')).not.toBeInTheDocument();
    });

    it('should show "reserved" status badge', () => {
      const reservedVehicle = { ...mockVehicle, availabilityStatus: 'reserved' as const };
      render(<VehicleCard vehicle={reservedVehicle} />);
      expect(screen.getByText('reserved')).toBeInTheDocument();
    });

    it('should show "sold" status badge', () => {
      const soldVehicle = { ...mockVehicle, availabilityStatus: 'sold' as const };
      render(<VehicleCard vehicle={soldVehicle} />);
      expect(screen.getByText('sold')).toBeInTheDocument();
    });
  });

  describe('Otto\'s Pick Badge', () => {
    it('should display Otto\'s Pick badge for 95%+ match score', () => {
      const ottoPickVehicle = { ...mockVehicle, matchScore: 97 };
      render(<VehicleCard vehicle={ottoPickVehicle} />);
      expect(screen.getByText('Otto\'s Pick')).toBeInTheDocument();
    });

    it('should not display Otto\'s Pick badge for lower scores', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      expect(screen.queryByText('Otto\'s Pick')).not.toBeInTheDocument();
    });
  });

  describe('Interactive Elements', () => {
    it('should call onFavorite when favorite button clicked', () => {
      const onFavorite = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onFavorite={onFavorite} />);

      const favoriteButton = document.querySelector('button[aria-label*="favorite"]');
      expect(favoriteButton).toBeInTheDocument();

      fireEvent.click(favoriteButton!);
      expect(onFavorite).toHaveBeenCalledWith('test-vehicle-1');
    });

    it('should call onCompare when compare button clicked', () => {
      const onCompare = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onCompare={onCompare} />);

      const compareButton = screen.getByText('Compare');
      fireEvent.click(compareButton);

      expect(onCompare).toHaveBeenCalledWith('test-vehicle-1');
    });

    it('should call onFeedback with "more" when thumbs up clicked', () => {
      const onFeedback = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onFeedback={onFeedback} />);

      const thumbsUp = screen.getByText('More like this');
      fireEvent.click(thumbsUp);

      expect(onFeedback).toHaveBeenCalledWith('test-vehicle-1', 'more');
    });

    it('should call onFeedback with "less" when thumbs down clicked', () => {
      const onFeedback = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onFeedback={onFeedback} />);

      const thumbsDown = screen.getByText('Fewer like this');
      fireEvent.click(thumbsDown);

      expect(onFeedback).toHaveBeenCalledWith('test-vehicle-1', 'less');
    });

    it('should call onClick when card clicked', () => {
      const onClick = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onClick={onClick} />);

      const card = screen.getByText('2023 Toyota Camry SE').closest('.vehicle-card');
      fireEvent.click(card!);

      expect(onClick).toHaveBeenCalledWith(mockVehicle);
    });

    it('should call onToggleExpand when expand button clicked', () => {
      const onToggleExpand = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onToggleExpand={onToggleExpand} />);

      const expandButton = screen.getByText('Show more');
      fireEvent.click(expandButton);

      expect(onToggleExpand).toHaveBeenCalled();
    });
  });

  describe('Glass-Morphism Styling', () => {
    it('should apply glass-morphism background', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      const card = screen.getByText('2023 Toyota Camry SE').closest('.vehicle-card');
      expect(card).toBeInTheDocument();
      // Check for glass-morphism class
      expect(card).toHaveClass('vehicle-card');
      // Verify it's interactive with role
      expect(card).toHaveAttribute('role', 'button');
    });

    it('should apply hover lift effect', () => {
      render(<VehicleCard vehicle={mockVehicle} />);
      const card = screen.getByText('2023 Toyota Camry SE').closest('.vehicle-card');

      // Simulate hover
      fireEvent.mouseEnter(card!);

      // Card should have transform animation
      expect(card).toHaveClass('vehicle-card');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<VehicleCard vehicle={mockVehicle} />);

      const favoriteButton = document.querySelector('button[aria-label*="favorite"]');
      expect(favoriteButton).toBeInTheDocument();

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      expect(compareButton).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      const onClick = vi.fn();
      render(<VehicleCard vehicle={mockVehicle} onClick={onClick} />);

      const card = screen.getByText('2023 Toyota Camry SE').closest('.vehicle-card');
      expect(card).toHaveAttribute('tabIndex', '0');

      // Test Enter key
      fireEvent.keyDown(card!, { key: 'Enter' });
      expect(onClick).toHaveBeenCalledWith(mockVehicle);
    });
  });

  describe('Variant Prop', () => {
    it('should accept default variant', () => {
      const { container } = render(
        <VehicleCard vehicle={mockVehicle} variant="default" />
      );
      expect(container).toBeInTheDocument();
    });

    it('should accept compact variant', () => {
      const { container } = render(
        <VehicleCard vehicle={mockVehicle} variant="compact" />
      );
      expect(container).toBeInTheDocument();
    });

    it('should accept comparison variant', () => {
      const { container } = render(
        <VehicleCard vehicle={mockVehicle} variant="comparison" />
      );
      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle vehicle without images', () => {
      const vehicleNoImage = { ...mockVehicle, images: undefined };
      render(<VehicleCard vehicle={vehicleNoImage} />);
      // Should still render title
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should handle vehicle without features', () => {
      const vehicleNoFeatures = { ...mockVehicle, features: undefined };
      render(<VehicleCard vehicle={vehicleNoFeatures} />);
      // Should still render other elements
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should handle vehicle without match score', () => {
      const vehicleNoScore = { ...mockVehicle, matchScore: undefined };
      render(<VehicleCard vehicle={vehicleNoScore} />);
      // Should still render other elements
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });
  });
});
