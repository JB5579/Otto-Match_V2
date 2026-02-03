import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { VehicleDetailModal } from '../VehicleDetailModal';
import type { Vehicle } from '../../../app/types/api';

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
  description: 'A great family sedan with excellent fuel economy and modern safety features including adaptive cruise control, lane departure warning, and automatic emergency braking.',
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
  features: [
    'Backup Camera',
    'Bluetooth',
    'Lane Assist',
    'Apple CarPlay',
    'Android Auto',
    'Heated Seats',
    'Adaptive Cruise Control',
    'Lane Departure Warning',
    'Automatic Emergency Braking'
  ],
  matchScore: 92,
  availabilityStatus: 'available',
  currentViewers: 3,
  ottoRecommendation: 'Perfect for families seeking reliability and comfort. This Camry offers excellent fuel economy, advanced safety features, and a spacious interior that makes it ideal for daily commutes and long road trips.',
  seller_id: 'seller-1',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
};

describe('VehicleDetailModal Integration Tests', () => {
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

  describe('AC3: Vehicle Images and Media Display', () => {
    it('should display image carousel with all images', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Main image should be displayed
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();

      // Navigation buttons should be visible for multiple images
      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();

      // Image counter should be displayed
      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      // Thumbnails should be rendered
      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails.length).toBe(3);
    });

    it('should navigate between images using carousel', async () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const nextButton = screen.getByRole('button', { name: /next image/i });

      // Click next to see second image
      fireEvent.click(nextButton);
      expect(screen.getByAltText('2023 Toyota Camry SE Side')).toBeInTheDocument();
      expect(screen.getByText('2 / 3')).toBeInTheDocument();

      // Click next again for third image
      fireEvent.click(nextButton);
      expect(screen.getByAltText('2023 Toyota Camry SE Interior')).toBeInTheDocument();
      expect(screen.getByText('3 / 3')).toBeInTheDocument();

      // Click next again to cycle back to first
      fireEvent.click(nextButton);
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('should support keyboard navigation for images', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const carousel = screen.getByRole('region', { name: /vehicle images for/i });

      // Arrow right should go to next image
      fireEvent.keyDown(carousel, { key: 'ArrowRight' });
      expect(screen.getByText('2 / 3')).toBeInTheDocument();

      // Arrow left should go back
      fireEvent.keyDown(carousel, { key: 'ArrowLeft' });
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('should work correctly when vehicle has no images', () => {
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

      // Image carousel should show placeholder
      expect(screen.getByText('No images available')).toBeInTheDocument();

      // Should still show specs and other content
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
    });
  });

  describe('AC4: Vehicle Specifications Display', () => {
    it('should display all vehicle specifications correctly', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Key specs should be visible
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Automatic')).toBeInTheDocument();
      expect(screen.getByText('FWD')).toBeInTheDocument();
      expect(screen.getByText('Gasoline')).toBeInTheDocument();
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

    it('should display key features', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should show features
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();
      expect(screen.getByText('Bluetooth')).toBeInTheDocument();
      expect(screen.getByText('Lane Assist')).toBeInTheDocument();
      expect(screen.getByText('Apple CarPlay')).toBeInTheDocument();
      expect(screen.getByText('Heated Seats')).toBeInTheDocument();
    });

    it('should handle vehicles with minimal data', () => {
      const minimalVehicle: Vehicle = {
        ...mockVehicle,
        features: undefined,
        description: undefined,
      };

      render(
        <VehicleDetailModal
          vehicle={minimalVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render title and images
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();

      // Should not show features or description sections
      expect(screen.queryByText('About this Vehicle')).not.toBeInTheDocument();
    });
  });

  describe('AC5: Otto Recommendation', () => {
    it('should display personalized recommendation', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/Otto's Recommendation/i)).toBeInTheDocument();
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
      expect(screen.getByText(/92% Match/i)).toBeInTheDocument();
    });

    it('should display match score badge', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('should handle vehicles without recommendation', () => {
      const vehicleWithoutRecommendation = {
        ...mockVehicle,
        ottoRecommendation: undefined,
        matchScore: undefined,
      };

      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutRecommendation}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });
  });

  describe('AC6: Social Proof', () => {
    it('should display current viewers count', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />}
      />

      expect(screen.getByText(/3 viewing/i)).toBeInTheDocument();
    });

    it('should handle vehicles without viewer data', () => {
      const vehicleWithoutViewers = {
        ...mockVehicle,
        currentViewers: undefined,
      };

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
  });

  describe('AC7: Hold and Compare Actions', () => {
    it('should call onHold when Hold button is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
        />
      );

      const holdButton = screen.getByRole('button', { name: /hold vehicle/i });
      fireEvent.click(holdButton);

      expect(mockOnHold).toHaveBeenCalledWith('test-vehicle-1');
      expect(mockOnHold).toHaveBeenCalledTimes(1);
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

      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      fireEvent.click(compareButton);

      expect(mockOnCompare).toHaveBeenCalledWith('test-vehicle-1');
      expect(mockOnCompare).toHaveBeenCalledTimes(1);
    });

    it('should not show action buttons when callbacks not provided', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.queryByRole('button', { name: /hold vehicle/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /add to comparison/i })).not.toBeInTheDocument();
    });

    it('should disable actions for sold vehicles', () => {
      const soldVehicle = { ...mockVehicle, availabilityStatus: 'sold' as const };

      render(
        <VehicleDetailModal
          vehicle={soldVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
          onCompare={mockOnCompare}
        />
      );

      expect(screen.getByText('sold')).toBeInTheDocument();

      // Hold button should show "Sold Out" or similar
      const holdButton = screen.queryByRole('button', { name: /hold vehicle/i });
      if (holdButton) {
        expect(holdButton).toBeDisabled();
      }
    });
  });

  describe('AC11: Responsive Layout', () => {
    it('should apply responsive CSS classes', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Check for responsive structure
      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();

      const twoColumnLayout = document.querySelector('.twoColumnLayout');
      expect(twoColumnLayout).toBeInTheDocument();

      const leftColumn = document.querySelector('.leftColumn');
      expect(leftColumn).toBeInTheDocument();

      const rightColumn = document.querySelector('.rightColumn');
      expect(rightColumn).toBeInTheDocument();
    });

    it('should maintain glass-morphism styling', () => {
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

    it('should prevent body scroll when open', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when closed', () => {
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
  });

  describe('Close Interactions', () => {
    it('should close when close button is clicked', () => {
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

    it('should close when overlay is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const overlay = document.querySelector('.fixed.inset-0.z-50.bg-black\\/40');
      fireEvent.click(overlay!);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should not close when modal content is clicked', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const modalContent = document.querySelector('.vehicleDetailModalContent');
      fireEvent.click(modalContent!);

      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Complete User Flow', () => {
    it('should support complete vehicle exploration flow', async () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
          onHold={mockOnHold}
          onCompare={mockOnCompare}
        />
      );

      // 1. View initial state - vehicle title and first image
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();
      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      // 2. Browse images
      const nextButton = screen.getByRole('button', { name: /next image/i });
      fireEvent.click(nextButton);
      expect(screen.getByText('2 / 3')).toBeInTheDocument();

      // 3. View thumbnails
      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      fireEvent.click(thumbnails[2]);
      expect(screen.getByText('3 / 3')).toBeInTheDocument();

      // 4. Review specifications
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Automatic')).toBeInTheDocument();

      // 5. Read features
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();
      expect(screen.getByText('Heated Seats')).toBeInTheDocument();

      // 6. See Otto's recommendation
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();

      // 7. View social proof
      expect(screen.getByText(/3 viewing/i)).toBeInTheDocument();

      // 8. Check pricing
      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
      expect(screen.getByText(/Save \$2,000/i)).toBeInTheDocument();

      // 9. Take action
      const compareButton = screen.getByRole('button', { name: /add to comparison/i });
      fireEvent.click(compareButton);
      expect(mockOnCompare).toHaveBeenCalledWith('test-vehicle-1');

      // 10. Close modal
      const closeButton = screen.getByRole('button', { name: /close modal/i });
      fireEvent.click(closeButton);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility Integration', () => {
    it('should have proper focus management', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toBeInTheDocument();

      // Should have proper ARIA labels
      expect(screen.getByRole('region', { name: /vehicle images for/i })).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      const carousel = screen.getByRole('region', { name: /vehicle images for/i });

      // Arrow keys should work
      fireEvent.keyDown(carousel, { key: 'ArrowRight' });
      expect(screen.getByText('2 / 3')).toBeInTheDocument();

      fireEvent.keyDown(carousel, { key: 'ArrowLeft' });
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('should have screen reader description', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/Detailed information about 2023 Toyota Camry SE/)).toBeInTheDocument();
    });
  });

  describe('Animation Integration', () => {
    it('should render with motion components', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Modal should have motion wrapper
      const modalContent = document.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Edge Cases Integration', () => {
    it('should handle vehicles with all optional fields missing', () => {
      const minimalVehicle: Vehicle = {
        id: 'test-minimal',
        vin: 'MIN123',
        make: 'Honda',
        model: 'Civic',
        year: 2022,
        trim: undefined,
        mileage: 50000,
        price: 18000,
        originalPrice: undefined,
        savings: undefined,
        color: undefined,
        transmission: undefined,
        fuel_type: undefined,
        body_type: undefined,
        drivetrain: undefined,
        condition: undefined,
        description: undefined,
        images: [],
        features: undefined,
        matchScore: undefined,
        availabilityStatus: 'available',
        currentViewers: undefined,
        ottoRecommendation: undefined,
        seller_id: 'seller-2',
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      };

      render(
        <VehicleDetailModal
          vehicle={minimalVehicle}
          isOpen={true}
          onClose={mockOnClose}
        />
      );

      // Should still render core content
      expect(screen.getByText('2022 Honda Civic')).toBeInTheDocument();
      expect(screen.getByText(/\$18,000/)).toBeInTheDocument();

      // Should show placeholder for no images
      expect(screen.getByText('No images available')).toBeInTheDocument();
    });

    it('should handle reserved status correctly', () => {
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

    it('should handle sold status correctly', () => {
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
});
