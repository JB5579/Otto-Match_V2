/**
 * LazyImage - Image component with advanced lazy loading
 *
 * Story 3-8.6: Uses Intersection Observer for viewport-based loading
 * - Loads images before they enter viewport (rootMargin: 200px)
 * - Shows skeleton placeholder while loading
 * - Supports all standard img attributes
 * - Improves performance by deferring off-screen image loads
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useLazyImage } from '../../hooks/useLazyImage';
import { ImageSkeleton } from './DetailSkeleton';

export interface LazyImageProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'loading'> {
  /** Image source URL */
  src: string;
  /** Alt text for accessibility */
  alt: string;
  /** Intersection Observer threshold (0-1) */
  threshold?: number;
  /** Root margin for pre-loading (default: '200px 0px') */
  rootMargin?: string;
  /** Additional CSS styles */
  style?: React.CSSProperties;
  /** CSS class name */
  className?: string;
  /** Whether to show skeleton placeholder */
  showSkeleton?: boolean;
  /** Skeleton background color */
  skeletonColor?: string;
}

/**
 * Lazy loaded image component with Intersection Observer
 *
 * Story 3-8.6: Advanced lazy loading for better performance
 *
 * @param props - Image props and lazy loading options
 * @returns Lazy loaded image with optional skeleton placeholder
 */
const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  threshold = 0.1,
  rootMargin = '200px 0px',
  style,
  className,
  showSkeleton = true,
  skeletonColor = '#f5f5f5',
  ...imgProps
}) => {
  const [hasError, setHasError] = useState(false);
  const { imageSrc, isLoading, isVisible } = useLazyImage(src, threshold, rootMargin);

  const handleError = () => {
    setHasError(true);
  };

  // Show skeleton if not visible or still loading
  if (showSkeleton && (!isVisible || isLoading)) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: skeletonColor,
          position: 'relative',
          overflow: 'hidden',
          ...style,
        }}
        className={className}
      >
        <ImageSkeleton style={{ width: '100%', height: '100%' }} />
      </div>
    );
  }

  // Show error state
  if (hasError) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#f5f5f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
          fontSize: '14px',
          ...style,
        }}
        className={className}
      >
        Image not available
      </div>
    );
  }

  // Show image when loaded
  return (
    <motion.img
      src={imageSrc || src}
      alt={alt}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      onError={handleError}
      style={{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        ...style,
      }}
      className={className}
      {...imgProps}
    />
  );
};

export default LazyImage;
