/**
 * useReducedMotion - Custom hook for respecting user's motion preferences
 *
 * Story 3-8.13: Optimize Framer Motion animations for accessibility
 * - Detects prefers-reduced-motion setting
 * - Disables animations for users who prefer reduced motion
 * - Improves performance for users with motion sensitivity
 */

import { useState, useEffect } from 'react';

export interface UseReducedMotionResult {
  /** Whether user prefers reduced motion */
  prefersReduced: boolean;
  /** Should animations be disabled */
  disableAnimations: boolean;
}

/**
 * Hook to detect and track prefers-reduced-motion setting
 *
 * @returns Object with reduced motion preference
 */
export function useReducedMotion(): UseReducedMotionResult {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    // Check initial preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mediaQuery.matches);

    // Listen for changes
    const listener = (event: MediaQueryListEvent) => {
      setPrefersReduced(event.matches);
    };

    mediaQuery.addEventListener('change', listener);

    return () => {
      mediaQuery.removeEventListener('change', listener);
    };
  }, []);

  return {
    prefersReduced,
    disableAnimations: prefersReduced,
  };
}

/**
 * Get animation props that respect reduced motion preference
 * Story 3-8.13: Return disabled animation for users who prefer reduced motion
 *
 * @param defaultAnimationProps - Default animation props
 * @returns Animation props (disabled if reduced motion preferred)
 */
export function getAnimationProps(
  defaultAnimationProps: {
    initial?: any;
    animate?: any;
    exit?: any;
    transition?: any;
  }
): {
  initial?: any;
  animate?: any;
  exit?: any;
  transition?: any;
} {
  // Check if reduced motion is preferred
  if (typeof window !== 'undefined') {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReduced) {
      // Return disabled animation (no transition, immediate state)
      return {
        initial: undefined,
        animate: defaultAnimationProps.animate || { opacity: 1 },
        exit: undefined,
        transition: { duration: 0 },
      };
    }
  }

  return defaultAnimationProps;
}

/**
 * Optimized animation variants for Framer Motion
 * Story 8.8.13: Uses GPU-accelerated properties (transform, opacity) only
 *
 * @param delay - Stagger delay in milliseconds
 * @returns Optimized animation variants
 */
export function createOptimizedVariants(delay: number = 0) {
  return {
    initial: {
      opacity: 0,
      y: 20,
      scale: 0.95,
    },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: {
        duration: 0.2,
      },
    },
    transition: {
      delay: delay / 1000, // Convert ms to seconds
      type: 'spring' as const,
      stiffness: 300,
      damping: 25,
    },
  };
}

/**
 * GPU-accelerated animation layout prop
 * Story 3-8.13: Use layout="position" for hardware acceleration
 *
 * This should be used on motion.div elements that animate
 * position, as it enables GPU acceleration via transform
 */
export const GPU_LAYOUT_PROP = 'position';

export default useReducedMotion;
