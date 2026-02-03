import { useState, useEffect, useRef } from 'react';

/**
 * useLazyImage - Custom hook for lazy loading images with Intersection Observer
 *
 * Story 3-8.4: Implements advanced lazy loading with Intersection Observer
 * - Loads images only when within viewport threshold (±200px)
 * - Fade-in animation for loaded images (150ms ease-in)
 * - Handles error states with placeholder fallback
 * - Throttled callback (100ms) for performance (Story 3-8.11)
 *
 * @param src - Image source URL
 * @param threshold - Intersection Observer threshold (0-1, default: 0.1)
 * @param rootMargin - Root margin for viewport expansion (default: '200px 0px')
 * @returns Object with imageSrc, imgRef, isLoading, isError
 */
export interface UseLazyImageResult {
  /** Current image source (null until loaded) */
  imageSrc: string | null;
  /** Ref to attach to img element */
  imgRef: React.RefObject<HTMLImageElement>;
  /** Whether image is currently loading */
  isLoading: boolean;
  /** Whether image failed to load */
  isError: boolean;
  /** Whether image has been loaded */
  isLoaded: boolean;
}

export function useLazyImage(
  src: string,
  threshold: number = 0.1,
  rootMargin: string = '200px 0px'
): UseLazyImageResult {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    // Reset state when src changes
    setImageSrc(null);
    setIsLoading(true);
    setIsError(false);
    setIsLoaded(false);

    // Create Intersection Observer
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Image is in viewport, load it
            setImageSrc(src);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );

    const imgElement = imgRef.current;
    if (imgElement) {
      observer.observe(imgElement);
    }

    return () => {
      observer.disconnect();
    };
  }, [src, threshold, rootMargin]);

  useEffect(() => {
    // Handle image load events
    const imgElement = imgRef.current;

    const handleLoad = () => {
      setIsLoading(false);
      setIsLoaded(true);
      setIsError(false);
    };

    const handleError = () => {
      setIsLoading(false);
      setIsError(true);
      setIsLoaded(false);
    };

    if (imgElement && imageSrc) {
      imgElement.addEventListener('load', handleLoad);
      imgElement.addEventListener('error', handleError);

      return () => {
        imgElement.removeEventListener('load', handleLoad);
        imgElement.removeEventListener('error', handleError);
      };
    }
  }, [imageSrc]);

  return {
    imageSrc,
    imgRef,
    isLoading,
    isError,
    isLoaded,
  };
}

/**
 * LazyImage component - Wraps img with lazy loading functionality
 *
 * Story 3-8.6: Update VehicleCard to use lazy images
 *
 * @param props - Component props
 * @returns Lazy loaded image component
 */
export interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  style?: React.CSSProperties;
  placeholder?: React.ReactNode;
  onClick?: () => void;
  threshold?: number;
  rootMargin?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className,
  style,
  placeholder,
  onClick,
  threshold = 0.1,
  rootMargin = '200px 0px',
  onLoad,
  onError,
}) => {
  const { imageSrc, imgRef, isLoading, isError } = useLazyImage(src, threshold, rootMargin);

  const handleLoad = () => {
    onLoad?.();
  };

  const handleError = () => {
    onError?.();
  };

  if (isError && placeholder) {
    return <>{placeholder}</>;
  }

  return (
    <>
      {isLoading && placeholder && (
        <div style={style} className={className}>
          {placeholder}
        </div>
      )}
      <img
        ref={imgRef}
        src={imageSrc || undefined}
        alt={alt}
        className={className}
        style={{
          ...style,
          opacity: isLoading ? 0 : 1,
          transition: 'opacity 150ms ease-in',
          display: isLoading && placeholder ? 'none' : 'block',
        }}
        onClick={onClick}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
      />
    </>
  );
};

export default useLazyImage;
