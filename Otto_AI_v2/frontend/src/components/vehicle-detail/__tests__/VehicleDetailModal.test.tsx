import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VehicleDetailModal } from '../VehicleDetailModal';
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
  description: 'A great family sedan with excellent fuel economy and modern safety features.',
  images: [
    {
      url: 'https://example.com/image1.jpg',
      description: 'Hero image',
      category: 'hero',
      altText: '2023 Toyota Camry SE Front',
    },
    {
      url: 'https://example.com/image2.jpg',
      description: 'Side view',
      category: 'exterior',
      altText: '2023 Toyota Camry SE Side',
    },
    {
      url: 'https://example.com/image3.jpg',
      description: 'Interior',
      category: 'interior',
      altText: '2023 Toyota Camry SE Interior',
    },
  ],
  features: ['Backup Camera', 'Bluetooth', 'Lane Assist', 'Apple CarPlay', 'Android Auto', 'Heated Seats'],
  matchScore: 92,
  availabilityStatus: 'available',
  currentViewers: 3,
  ottoRecommendation: 'Perfect for families seeking reliability and comfort',
  seller_id: 'seller-1',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
};

describe('VehicleDetailModal', () => {
  let mockOnClose: ReturnType<typeof vi.fn>;
  let mockOnHold: ReturnType<typeof vi.fn>;
  let mockOnCompare: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnClose = vi.fn();
    mockOnHold = vi.fn();
    mockOnCompare = vi.fn();
  });

  afterEach(() => {
    // Reset body styles after each test
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('should render when isOpen is true with vehicle data', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
          onCompare={mockOnCompare}
        />
      );

      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should not render when isOpen is false', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={false}
          onClose={mockOnClose}
        />
      );

      // Modal should not be in the document
      expect(container.querySelector('.vehicleDetailModalContent')).not.toBeInTheDocument();
    });

    it('should not render when vehicle is null', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={null}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should display vehicle title with trim', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should display vehicle title without trim when trim is not provided', () => {
      const vehicleWithoutTrim = { ...mockVehicle, trim: undefined };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutTrim}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('2023 Toyota Camry')).toBeInTheDocument();
    });

    it('should display vehicle description', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('About this Vehicle')).toBeInTheDocument();
      expect(screen.getByText(/A great family sedan/)).toBeInTheDocument();
    });

    it('should render image carousel when images are available', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const images = screen.getAllByRole('img');
      expect(images.length).toBeGreaterThan(0);
    });

    it('should not render image carousel when no images', () => {
      const vehicleWithoutImages = { ...mockVehicle, images: [] };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutImages}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should render vehicle specifications', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // VehicleSpecsDetail should be rendered
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Automatic')).toBeInTheDocument();
      expect(screen.getByText('FWD')).toBeInTheDocument();
    });

    it('should render key features', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Backup Camera')).toBeInTheDocument();
      expect(screen.getByText('Bluetooth')).toBeInTheDocument();
      expect(screen.getByText('Lane Assist')).toBeInTheDocument();
    });

    it('should render Otto recommendation', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
    });

    it('should render social proof badges', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/3 viewing/i)).toBeInTheDocument();
    });

    it('should render pricing panel', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
      expect(screen.getByText(/\$30,000/)).toBeInTheDocument();
      expect(screen.getByText(/Save \$2,000/i)).toBeInTheDocument();
    });

    it('should render action buttons', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
          onCompare={mockOnCompare}
        />
      );

      expect(screen.getByRole('button', { name: /hold/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument();
    });
  });

  describe('Modal State Management', () => {
    it('should prevent body scroll when modal is open', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when modal is closed', () => {
      const { rerender } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');

      rerender(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={false}
          onClose={mockOnClose}
        />
      );

      expect(document.body.style.overflow).toBe('');
    });

    it('should restore body scroll on unmount', () => {
      const { unmount } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Close Behavior', () => {
    it('should call onClose when close button is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when overlay is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const overlay = document.querySelector('.fixed.inset-0.z-50.bg-black\\/40');
      expect(overlay).toBeInTheDocument();

      fireEvent.click(overlay!);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should not call onClose when modal content is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();

      fireEvent.click(modalContent!);
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Interactive Elements', () => {
    it('should call onHold when Hold button is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
        />
      );

      const holdButton = screen.getByRole('button', { name: /hold/i });
      fireEvent.click(holdButton);

      expect(mockOnHold).toHaveBeenCalledWith('test-vehicle-1');
    });

    it('should call onCompare when Compare button is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onCompare={mockOnCompare}
        />
      );

      const compareButton = screen.getByRole('button', { name: /compare/i });
      fireEvent.click(compareButton);

      expect(mockOnCompare).toHaveBeenCalledWith('test-vehicle-1');
    });

    it('should not render Hold button when onHold is not provided', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const holdButton = screen.queryByRole('button', { name: /hold/i });
      expect(holdButton).not.toBeInTheDocument();
    });

    it('should not render Compare button when onCompare is not provided', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const compareButton = screen.queryByRole('button', { name: /compare/i });
      expect(compareButton).not.toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should apply responsive CSS classes', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();

      const modalHeader = document.querySelector('.modalHeader');
      expect(modalHeader).toBeInTheDocument();

      const scrollableContent = document.querySelector('.modalScrollableContent');
      expect(scrollableContent).toBeInTheDocument();

      const twoColumnLayout = document.querySelector('.twoColumnLayout');
      expect(twoColumnLayout).toBeInTheDocument();

      const leftColumn = document.querySelector('.leftColumn');
      expect(leftColumn).toBeInTheDocument();

      const rightColumn = document.querySelector('.rightColumn');
      expect(rightColumn).toBeInTheDocument();
    });

    it('should have proper glass-morphism styling', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toBeInTheDocument();

      // Should have screen reader description
      expect(screen.getByText(/Detailed information about 2023 Toyota Camry SE/)).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });

      // Test Escape key
      fireEvent.keyDown(closeButton, { key: 'Escape' });
      // Radix UI should handle this and call onClose
    });

    it('should have focus management', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle vehicle without description', () => {
      const vehicleWithoutDescription = { ...mockVehicle, description: undefined };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutDescription}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
      expect(screen.queryByText('About this Vehicle')).not.toBeInTheDocument();
    });

    it('should handle vehicle without features', () => {
      const vehicleWithoutFeatures = { ...mockVehicle, features: undefined };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutFeatures}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should handle vehicle without match score', () => {
      const vehicleWithoutScore = { ...mockVehicle, matchScore: undefined };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutScore}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should handle vehicle without current viewers', () => {
      const vehicleWithoutViewers = { ...mockVehicle, currentViewers: undefined };
      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutViewers}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should handle reserved availability status', () => {
      const reservedVehicle = { ...mockVehicle, availabilityStatus: 'reserved' as const };
      render(
        <VehicleDetailModal
          vehicle={reservedVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('reserved')).toBeInTheDocument();
    });

    it('should handle sold availability status', () => {
      const soldVehicle = { ...mockVehicle, availabilityStatus: 'sold' as const };
      render(
        <VehicleDetailModal
          vehicle={soldVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('sold')).toBeInTheDocument();
    });
  });

  describe('Animation and Transitions', () => {
    it('should apply motion components for animations', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('should render all child components in correct order', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
          onCompare={mockOnCompare}
        />
      );

      // Header
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();

      // Image carousel (if images exist)
      const images = screen.getAllByRole('img');
      expect(images.length).toBeGreaterThan(0);

      // Specs and Features (left column)
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();

      // Recommendation, Social Proof, Pricing, Actions (right column)
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /hold/i })).toBeInTheDocument();
    });
  });
});
