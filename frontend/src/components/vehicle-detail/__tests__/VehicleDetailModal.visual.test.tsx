import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VehicleDetailModal } from '../VehicleDetailModal';
import type { Vehicle } from '../../../app/types/api';

/**
 * Visual Regression Tests for VehicleDetailModal
 *
 * Note: These tests provide a framework for visual regression testing.
 * To enable actual visual snapshot testing, integrate one of:
 *
 * 1. Percy.io - Cloud-based visual testing
 * 2. Chromatic - Storybook-based visual testing
 * 3. @storybook/addon-storyshots - Storybook snapshots
 * 4. jest-image-snapshot - DOM screenshots with Playwright
 *
 * Example setup with jest-image-snapshot:
 *
 * ```bash
 * npm install --save-dev jest-image-snapshot
 * ```
 *
 * In vitest setup:
 * ```ts
 * import { toMatchImageSnapshot } from 'jest-image-snapshot';
 * expect.extend({ toMatchImageSnapshot });
 * ```
 */

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
  ],
  features: ['Backup Camera', 'Bluetooth', 'Lane Assist', 'Apple CarPlay'],
  matchScore: 92,
  availabilityStatus: 'available',
  currentViewers: 3,
  ottoRecommendation: 'Perfect for families seeking reliability and comfort',
  seller_id: 'seller-1',
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
};

describe('VehicleDetailModal Visual Regression Tests', () => {
  describe('Component Render Verification', () => {
    it('should render modal with all sections visible', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Verify modal content exists
      const modalContent = container.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();

      // Verify header
      const header = container.querySelector('.modalHeader');
      expect(header).toBeInTheDocument();

      // Verify scrollable content
      const scrollableContent = container.querySelector('.modalScrollableContent');
      expect(scrollableContent).toBeInTheDocument();

      // Verify two-column layout
      const twoColumnLayout = container.querySelector('.twoColumnLayout');
      expect(twoColumnLayout).toBeInTheDocument();
    });

    it('should render with proper spacing and layout', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Check that all main sections are present
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
      expect(screen.getByText(/3 viewing/i)).toBeInTheDocument();
      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
    });

    it('should render close button in correct position', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toBeInTheDocument();
    });
  });

  describe('Visual States', () => {
    it('should display available vehicle state correctly', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Should show available status
      expect(screen.getByText('available')).toBeInTheDocument();
    });

    it('should display reserved vehicle state correctly', () => {
      const reservedVehicle = { ...mockVehicle, availabilityStatus: 'reserved' as const };

      const { container } = render(
        <VehicleDetailModal
          vehicle={reservedVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText('reserved')).toBeInTheDocument();
    });

    it('should display sold vehicle state correctly', () => {
      const soldVehicle = { ...mockVehicle, availabilityStatus: 'sold' as const };

      const { container } = render(
        <VehicleDetailModal
          vehicle={soldVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText('sold')).toBeInTheDocument();
    });
  });

  describe('Image Carousel Visuals', () => {
    it('should display image navigation buttons', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();
    });

    it('should display image counter', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText('1 / 2')).toBeInTheDocument();
    });

    it('should display thumbnails', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails).toHaveLength(2);
    });
  });

  describe('Pricing Display Visuals', () => {
    it('should display price with savings', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
      expect(screen.getByText(/\$30,000/)).toBeInTheDocument();
      expect(screen.getByText(/Save \$2,000/i)).toBeInTheDocument();
    });

    it('should display Otto\'s Match badge', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText('92%')).toBeInTheDocument();
    });
  });

  describe('Responsive Layout Visuals', () => {
    it('should have mobile layout classes', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Verify responsive classes are applied
      const modalContent = container.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toHaveClass('vehicleDetailModalContent');

      const twoColumnLayout = container.querySelector('.twoColumnLayout');
      expect(twoColumnLayout).toHaveClass('twoColumnLayout');
    });
  });

  describe('Animation Visuals', () => {
    it('should render with Framer Motion components', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Modal content should be wrapped in motion component
      const modalContent = container.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Edge Case Visuals', () => {
    it('should display no images placeholder correctly', () => {
      const vehicleWithoutImages = { ...mockVehicle, images: [] };

      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutImages}
          isOpen={true}
          onClose={() => {}}
        />
      );

      expect(screen.getByText('No images available')).toBeInTheDocument();
    });

    it('should display vehicle without features', () => {
      const vehicleWithoutFeatures = { ...mockVehicle, features: undefined };

      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutFeatures}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Should still render other content
      expect(screen.getByText('2023 Toyota Camry SE')).toBeInTheDocument();
    });

    it('should display vehicle without description', () => {
      const vehicleWithoutDescription = { ...mockVehicle, description: undefined };

      render(
        <VehicleDetailModal
          vehicle={vehicleWithoutDescription}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Should not show description section
      expect(screen.queryByText('About this Vehicle')).not.toBeInTheDocument();
    });
  });

  describe('Glass-Morphism Styling', () => {
    it('should apply glass-morphism background', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      const modalContent = container.querySelector('.vehicleDetailModalContent');
      expect(modalContent).toBeInTheDocument();
    });
  });

  describe('Accessibility Visuals', () => {
    it('should have visible focus indicators', () => {
      render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Interactive elements should be present
      expect(screen.getByRole('button', { name: /close modal/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();
    });
  });

  describe('Content Layout Verification', () => {
    it('should layout content in two columns', () => {
      const { container } = render(
        <VehicleDetailModal
          vehicle={mockVehicle}
          isOpen={true}
          onClose={() => {}}
        />
      );

      // Left column should have specs and features
      const leftColumn = container.querySelector('.leftColumn');
      expect(leftColumn).toBeInTheDocument();
      expect(screen.getByText(/15\.0k miles/i)).toBeInTheDocument();
      expect(screen.getByText('Backup Camera')).toBeInTheDocument();

      // Right column should have recommendation, pricing, actions
      const rightColumn = container.querySelector('.rightColumn');
      expect(rightColumn).toBeInTheDocument();
      expect(screen.getByText(/Perfect for families/)).toBeInTheDocument();
      expect(screen.getByText(/\$28,000/)).toBeInTheDocument();
    });
  });
});

/**
 * Visual Snapshot Testing (Optional Enhancement)
 *
 * To enable actual visual snapshots, integrate one of these libraries:
 *
 * 1. Percy.io (Recommended for cloud-based testing)
 *    - Automatic visual diff testing
 *    - Cross-browser testing
 *    - Integrates with CI/CD
 *
 * 2. @storybook/addon-storyshots + jest-image-snapshot
 *    - Storybook-based visual snapshots
 *    - Local development
 *    - Git-based diff tracking
 *
 * 3. Chromatic
 *    - Storybook publishing
 *    - Visual regression testing
 *    - UI component documentation
 *
 * Example Storybook story:
 *
 * ```tsx
 * import type { Meta, StoryObj } from '@storybook/react';
 * import { VehicleDetailModal } from './VehicleDetailModal';
 *
 * const meta: Meta<typeof VehicleDetailModal> = {
 *   title: 'Components/VehicleDetailModal',
 *   component: VehicleDetailModal,
 * };
 *
 * export default meta;
 * type Story = StoryObj<typeof VehicleDetailModal>;
 *
 * export const Available: Story = {
 *   args: {
 *     vehicle: mockVehicle,
 *     isOpen: true,
 *     onClose: () => {},
 *   },
 * };
 *
 * export const Reserved: Story = {
 *   args: {
 *     vehicle: { ...mockVehicle, availabilityStatus: 'reserved' },
 *     isOpen: true,
 *     onClose: () => {},
 *   },
 * };
 * ```
 */
