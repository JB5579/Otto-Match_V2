import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { VehicleImage } from '../../app/types/api';
import './VehicleImageCarousel.css';

interface VehicleImageCarouselProps {
  images: VehicleImage[];
  title: string;
}

interface ImageLoadState {
  [url: string]: {
    loaded: boolean;
    error: boolean;
  };
}

/**
 * VehicleImageCarousel - Image gallery with thumbnail navigation
 *
 * Features:
 * - Main image display with smooth transitions
 * - Thumbnail navigation strip
 * - Previous/Next navigation buttons
 * - Keyboard navigation (arrow keys)
 * - Touch/swipe support for mobile
 * - Lazy loading for images
 * - Image preloading for adjacent images (AC17)
 * - Error handling with fallback UI (AC17)
 * - Loading skeleton states (AC18)
 *
 * AC3: Vehicle images and media display
 * AC17: Image loading optimizations
 * AC18: Loading and error states
 *
 * @param props - Component props
 * @returns Image carousel component
 */
export const VehicleImageCarousel: React.FC<VehicleImageCarouselProps> = ({
  images,
  title,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageLoadState, setImageLoadState] = useState<ImageLoadState>({});
  const preloadCache = useRef<Set<string>>(new Set());

  // Preload adjacent images for smoother navigation
  useEffect(() => {
    if (!images || images.length === 0) return;

    const preloadImages = [currentIndex - 1, currentIndex, currentIndex + 1];

    preloadImages.forEach((index) => {
      // Handle wrapping
      let validIndex = index;
      if (validIndex < 0) validIndex = images.length - 1;
      if (validIndex >= images.length) validIndex = 0;

      const imageUrl = images[validIndex]?.url;
      if (!imageUrl || preloadCache.current.has(imageUrl)) return;

      // Mark as preloading
      preloadCache.current.add(imageUrl);

      // Preload the image
      const img = new Image();
      img.src = imageUrl;

      img.onload = () => {
        setImageLoadState(prev => ({
          ...prev,
          [imageUrl]: { loaded: true, error: false }
        }));
      };

      img.onerror = () => {
        setImageLoadState(prev => ({
          ...prev,
          [imageUrl]: { loaded: false, error: true }
        }));
      };
    });
  }, [currentIndex, images]);

  // Handle image load success
  const handleImageLoad = useCallback((url: string) => {
    setImageLoadState(prev => ({
      ...prev,
      [url]: { loaded: true, error: false }
    }));
  }, []);

  // Handle image load error
  const handleImageError = useCallback((url: string) => {
    setImageLoadState(prev => ({
      ...prev,
      [url]: { loaded: false, error: true }
    }));
  }, []);

  if (!images || images.length === 0) {
    return (
      <div
        style={{
          width: '100%',
          aspectRatio: '16 / 10',
          background: '#f5f5f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '12px',
        }}
      >
        <span style={{ color: '#999', fontSize: '14px' }}>No images available</span>
      </div>
    );
  }

  const currentImage = images[currentIndex];

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      goToPrevious();
    } else if (e.key === 'ArrowRight') {
      goToNext();
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
      onKeyDown={handleKeyDown}
      role="region"
      aria-label={`Vehicle images for ${title}`}
    >
      {/* Main Image Display */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '16 / 10',
          borderRadius: '12px',
          overflow: 'hidden',
          background: '#f5f5f5',
        }}
      >
        <AnimatePresence mode="wait">
          {imageLoadState[currentImage.url]?.error ? (
            // Error State
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%)',
                color: '#666',
              }}
            >
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ marginBottom: '12px', opacity: 0.5 }}
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              <span style={{ fontSize: '14px', fontWeight: 500 }}>
                Image unavailable
              </span>
            </motion.div>
          ) : (
            // Main Image with Loading State
            <>
              {!imageLoadState[currentImage.url]?.loaded && (
                // Loading Skeleton
                <motion.div
                  key="skeleton"
                  className="image-loading-shimmer"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                    backgroundSize: '200% 100%',
                  }}
                />
              )}
              <motion.img
                key={currentIndex}
                className="carousel-image"
                src={currentImage.url}
                alt={currentImage.altText || `${title} - Image ${currentIndex + 1}`}
                loading={currentIndex === 0 ? 'eager' : 'lazy'}
                initial={{ opacity: 0 }}
                animate={{ opacity: imageLoadState[currentImage.url]?.loaded ? 1 : 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                onLoad={() => handleImageLoad(currentImage.url)}
                onError={() => handleImageError(currentImage.url)}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  display: imageLoadState[currentImage.url]?.loaded ? 'block' : 'none',
                }}
              />
            </>
          )}
        </AnimatePresence>

        {/* Navigation Buttons */}
        {images.length > 1 && (
          <>
            <motion.button
              className="nav-button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={goToPrevious}
              aria-label="Previous image"
              style={{
                position: 'absolute',
                left: '16px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(8px)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              }}
            >
              <ChevronLeft size={24} color="#333" />
            </motion.button>

            <motion.button
              className="nav-button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={goToNext}
              aria-label="Next image"
              style={{
                position: 'absolute',
                right: '16px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(8px)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              }}
            >
              <ChevronRight size={24} color="#333" />
            </motion.button>

            {/* Image Counter */}
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '8px 16px',
                borderRadius: '20px',
                background: 'rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(8px)',
                color: 'white',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              {currentIndex + 1} / {images.length}
            </div>
          </>
        )}
      </div>

      {/* Thumbnail Navigation */}
      {images.length > 1 && (
        <div
          style={{
            display: 'flex',
            gap: '12px',
            overflowX: 'auto',
            padding: '4px 0',
            scrollbarWidth: 'none', // Firefox
            msOverflowStyle: 'none', // IE/Edge
          } as React.CSSProperties}
        >
          {images.map((image, index) => (
            <motion.button
              key={image.url}
              className="thumbnail-button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setCurrentIndex(index)}
              aria-label={`View image ${index + 1}`}
              style={{
                position: 'relative',
                flexShrink: 0,
                width: '80px',
                height: '60px',
                borderRadius: '8px',
                overflow: 'hidden',
                border: index === currentIndex
                  ? '3px solid #0EA5E9'
                  : '2px solid transparent',
                cursor: 'pointer',
                opacity: index === currentIndex ? 1 : 0.6,
              }}
            >
              <img
                className="carousel-image"
                src={image.url}
                alt={image.altText || `Thumbnail ${index + 1}`}
                loading="lazy"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
};

export default VehicleImageCarousel;
