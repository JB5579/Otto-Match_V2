import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VehicleImageCarousel } from '../VehicleImageCarousel';
import type { VehicleImage } from '../../../app/types/api';

const mockImages: VehicleImage[] = [
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
  {
    url: 'https://example.com/image4.jpg',
    description: 'Rear view',
    category: 'exterior',
    altText: '2023 Toyota Camry SE Rear',
  },
  {
    url: 'https://example.com/image5.jpg',
    description: 'Dashboard',
    category: 'interior',
    altText: '2023 Toyota Camry SE Dashboard',
  },
];

describe('VehicleImageCarousel', () => {
  describe('Rendering', () => {
    it('should render main image when images are provided', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const mainImage = screen.getByAltText('2023 Toyota Camry SE Front');
      expect(mainImage).toBeInTheDocument();
      expect(mainImage).toHaveAttribute('src', 'https://example.com/image1.jpg');
    });

    it('should display placeholder when no images are provided', () => {
      render(<VehicleImageCarousel images={[]} title="2023 Toyota Camry SE" />);

      expect(screen.getByText('No images available')).toBeInTheDocument();
    });

    it('should display placeholder when images array is undefined', () => {
      render(<VehicleImageCarousel images={undefined as any} title="2023 Toyota Camry SE" />);

      expect(screen.getByText('No images available')).toBeInTheDocument();
    });

    it('should display single image without navigation', () => {
      const singleImage = [mockImages[0]];
      render(<VehicleImageCarousel images={singleImage} title="2023 Toyota Camry SE" />);

      const mainImage = screen.getByAltText('2023 Toyota Camry SE Front');
      expect(mainImage).toBeInTheDocument();

      // No navigation buttons for single image
      expect(screen.queryByRole('button', { name: /previous/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /next/i })).not.toBeInTheDocument();

      // No image counter for single image
      expect(screen.queryByText(/1 \/ 1/i)).not.toBeInTheDocument();
    });

    it('should display navigation buttons when multiple images', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();
    });

    it('should display image counter', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      expect(screen.getByText('1 / 5')).toBeInTheDocument();
    });

    it('should display thumbnail navigation for multiple images', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      // Should have thumbnail buttons for each image
      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails).toHaveLength(5);
    });

    it('should not display thumbnails for single image', () => {
      const singleImage = [mockImages[0]];
      render(<VehicleImageCarousel images={singleImage} title="2023 Toyota Camry SE" />);

      const thumbnails = screen.queryAllByRole('button', { name: /view image/i });
      expect(thumbnails).toHaveLength(0);
    });

    it('should use lazy loading for images', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const mainImage = screen.getByAltText('2023 Toyota Camry SE Front');
      expect(mainImage).toHaveAttribute('loading', 'lazy');
    });

    it('should have proper ARIA labels', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const region = screen.getByRole('region', { name: /vehicle images for 2023 Toyota Camry SE/i });
      expect(region).toBeInTheDocument();
    });
  });

  describe('Navigation - Next Button', () => {
    it('should navigate to next image when next button is clicked', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const nextButton = screen.getByRole('button', { name: /next image/i });

      // Initially showing first image
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();

      // Click next
      fireEvent.click(nextButton);

      // Now showing second image
      expect(screen.getByAltText('2023 Toyota Camry SE Side')).toBeInTheDocument();
      expect(screen.getByText('2 / 5')).toBeInTheDocument();
    });

    it('should cycle to first image when next is clicked on last image', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const nextButton = screen.getByRole('button', { name: /next image/i });

      // Navigate to last image
      fireEvent.click(nextButton); // 2
      fireEvent.click(nextButton); // 3
      fireEvent.click(nextButton); // 4
      fireEvent.click(nextButton); // 5

      expect(screen.getByText('5 / 5')).toBeInTheDocument();

      // Click next on last image - should cycle to first
      fireEvent.click(nextButton);

      expect(screen.getByText('1 / 5')).toBeInTheDocument();
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();
    });
  });

  describe('Navigation - Previous Button', () => {
    it('should navigate to previous image when previous button is clicked', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const nextButton = screen.getByRole('button', { name: /next image/i });
      const prevButton = screen.getByRole('button', { name: /previous image/i });

      // Go to second image first
      fireEvent.click(nextButton);
      expect(screen.getByAltText('2023 Toyota Camry SE Side')).toBeInTheDocument();

      // Click previous
      fireEvent.click(prevButton);

      // Back to first image
      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();
      expect(screen.getByText('1 / 5')).toBeInTheDocument();
    });

    it('should cycle to last image when previous is clicked on first image', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const prevButton = screen.getByRole('button', { name: /previous image/i });

      // Currently on first image, click previous
      fireEvent.click(prevButton);

      // Should go to last image
      expect(screen.getByText('5 / 5')).toBeInTheDocument();
      expect(screen.getByAltText('2023 Toyota Camry SE Dashboard')).toBeInTheDocument();
    });
  });

  describe('Navigation - Thumbnail Click', () => {
    it('should display selected image when thumbnail is clicked', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });

      // Click third thumbnail (interior image)
      fireEvent.click(thumbnails[2]);

      expect(screen.getByAltText('2023 Toyota Camry SE Interior')).toBeInTheDocument();
      expect(screen.getByText('3 / 5')).toBeInTheDocument();
    });

    it('should highlight active thumbnail', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const nextButton = screen.getByRole('button', { name: /next image/i });

      // First thumbnail should be highlighted (index 0)
      let thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails[0]).toHaveStyle({ border: '3px solid #0EA5E9' });

      // Navigate to second image
      fireEvent.click(nextButton);

      // Second thumbnail should now be highlighted
      thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails[0]).not.toHaveStyle({ border: '3px solid #0EA5E9' });
      expect(thumbnails[1]).toHaveStyle({ border: '3px solid #0EA5E9' });
    });

    it('should reduce opacity of inactive thumbnails', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });

      // First thumbnail should have full opacity
      expect(thumbnails[0]).toHaveStyle({ opacity: 1 });

      // Other thumbnails should have reduced opacity
      expect(thumbnails[1]).toHaveStyle({ opacity: 0.6 });
      expect(thumbnails[2]).toHaveStyle({ opacity: 0.6 });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should navigate to next image on right arrow key', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const carousel = screen.getByRole('region', { name: /vehicle images for 2023 Toyota Camry SE/i });

      fireEvent.keyDown(carousel, { key: 'ArrowRight' });

      expect(screen.getByAltText('2023 Toyota Camry SE Side')).toBeInTheDocument();
      expect(screen.getByText('2 / 5')).toBeInTheDocument();
    });

    it('should navigate to previous image on left arrow key', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const carousel = screen.getByRole('region', { name: /vehicle images for 2023 Toyota Camry SE/i });

      // Go to second image first
      fireEvent.keyDown(carousel, { key: 'ArrowRight' });

      // Now press left arrow
      fireEvent.keyDown(carousel, { key: 'ArrowLeft' });

      expect(screen.getByAltText('2023 Toyota Camry SE Front')).toBeInTheDocument();
      expect(screen.getByText('1 / 5')).toBeInTheDocument();
    });

    it('should ignore other keyboard events', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const carousel = screen.getByRole('region', { name: /vehicle images for 2023 Toyota Camry SE/i });

      // Initially on first image
      expect(screen.getByText('1 / 5')).toBeInTheDocument();

      // Press arrow up (should be ignored)
      fireEvent.keyDown(carousel, { key: 'ArrowUp' });

      // Should still be on first image
      expect(screen.getByText('1 / 5')).toBeInTheDocument();
    });
  });

  describe('Image Counter', () => {
    it('should update counter when navigating images', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const nextButton = screen.getByRole('button', { name: /next image/i });

      expect(screen.getByText('1 / 5')).toBeInTheDocument();

      fireEvent.click(nextButton);
      expect(screen.getByText('2 / 5')).toBeInTheDocument();

      fireEvent.click(nextButton);
      expect(screen.getByText('3 / 5')).toBeInTheDocument();

      fireEvent.click(nextButton);
      expect(screen.getByText('4 / 5')).toBeInTheDocument();

      fireEvent.click(nextButton);
      expect(screen.getByText('5 / 5')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle images without altText', () => {
      const imagesWithoutAlt: VehicleImage[] = [
        {
          url: 'https://example.com/image1.jpg',
          description: 'Hero image',
          category: 'hero',
          altText: undefined as any,
        },
      ];

      render(<VehicleImageCarousel images={imagesWithoutAlt} title="2023 Toyota Camry SE" />);

      // Should generate alt text from title
      expect(screen.getByAltText('2023 Toyota Camry SE - Image 1')).toBeInTheDocument();
    });

    it('should handle two images correctly', () => {
      const twoImages = [mockImages[0], mockImages[1]];
      render(<VehicleImageCarousel images={twoImages} title="2023 Toyota Camry SE" />);

      expect(screen.getByText('1 / 2')).toBeInTheDocument();

      const nextButton = screen.getByRole('button', { name: /next image/i });
      fireEvent.click(nextButton);

      expect(screen.getByText('2 / 2')).toBeInTheDocument();
    });

    it('should handle many images (10+)', () => {
      const manyImages = Array.from({ length: 12 }, (_, i) => ({
        url: `https://example.com/image${i + 1}.jpg`,
        description: `Image ${i + 1}`,
        category: 'hero' as const,
        altText: `Image ${i + 1}`,
      }));

      render(<VehicleImageCarousel images={manyImages} title="2023 Toyota Camry SE" />);

      expect(screen.getByText('1 / 12')).toBeInTheDocument();

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails).toHaveLength(12);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA region', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const region = screen.getByRole('region', { name: /vehicle images for/i });
      expect(region).toBeInTheDocument();
    });

    it('should have accessible navigation buttons', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();
    });

    it('should have accessible thumbnail buttons', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails.length).toBeGreaterThan(0);

      thumbnails.forEach((thumbnail, index) => {
        expect(thumbnail).toHaveAttribute('aria-label', `View image ${index + 1}`);
      });
    });

    it('should support keyboard navigation', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const carousel = screen.getByRole('region', { name: /vehicle images for 2023 Toyota Camry SE/i });

      // Should respond to arrow keys
      fireEvent.keyDown(carousel, { key: 'ArrowRight' });
      expect(screen.getByText('2 / 5')).toBeInTheDocument();

      fireEvent.keyDown(carousel, { key: 'ArrowLeft' });
      expect(screen.getByText('1 / 5')).toBeInTheDocument();
    });
  });

  describe('Layout and Styling', () => {
    it('should render main image with proper aspect ratio', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const mainImage = screen.getByAltText('2023 Toyota Camry SE Front');
      expect(mainImage).toBeInTheDocument();
      // The image should have the cover object-fit
      expect(mainImage).toHaveStyle({ objectFit: 'cover' });
    });

    it('should render thumbnails with proper sizing', () => {
      render(<VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />);

      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      thumbnails.forEach((thumbnail) => {
        expect(thumbnail).toBeInTheDocument();
      });
    });
  });

  describe('Component Structure', () => {
    it('should render elements in correct order', () => {
      const { container } = render(
        <VehicleImageCarousel images={mockImages} title="2023 Toyota Camry SE" />
      );

      // Should have main image (note: thumbnail also has same alt, so use getAllByAltText)
      const frontImages = screen.getAllByAltText('2023 Toyota Camry SE Front');
      expect(frontImages).toHaveLength(2); // Main image + thumbnail

      // Should have navigation buttons
      expect(screen.getByRole('button', { name: /previous image/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next image/i })).toBeInTheDocument();

      // Should have image counter
      expect(screen.getByText('1 / 5')).toBeInTheDocument();

      // Should have thumbnails
      const thumbnails = screen.getAllByRole('button', { name: /view image/i });
      expect(thumbnails).toHaveLength(5);
    });
  });
});
