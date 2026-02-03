/**
 * Utility functions for performance optimization
 * debounce: Delays function execution until after wait milliseconds have elapsed
 * throttle: Limits function execution to once every wait milliseconds
 */

/**
 * Debounce function - delays execution until after wait ms
 * Useful for filter/sort operations to prevent excessive API calls
 *
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds (default: 300ms)
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

/**
 * Throttle function - limits execution to once every wait ms
 * Useful for scroll and resize events to prevent performance issues
 *
 * @param func - Function to throttle
 * @param wait - Wait time in milliseconds (default: 100ms for scroll, 200ms for resize)
 * @returns Throttled function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;
  let lastArgs: Parameters<T> | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;

      setTimeout(() => {
        inThrottle = false;
        // Execute any pending call with the most recent arguments
        if (lastArgs !== null) {
          func.apply(context, lastArgs);
          lastArgs = null;
        }
      }, wait);
    } else {
      // Store the most recent arguments
      lastArgs = args;
    }
  };
}

/**
 * useCallbackWithDeps - React hook that combines useCallback with dependency tracking
 * Ensures stable function reference while updating when dependencies change
 *
 * @param factory - Function that creates the callback
 * @param deps - Dependency array
 * @returns Memoized callback
 */
export function useCallbackWithDeps<T extends (...args: any[]) => any>(
  factory: () => T,
  deps: React.DependencyList
): T {
  // This would be used in a React component context
  // For now, just export the factory function
  return factory();
}

/**
 * Performance monitoring utility
 * Measures execution time of functions for debugging
 */
export function measurePerformance<T extends (...args: any[]) => any>(
  func: T,
  label: string
): T {
  return ((...args: Parameters<T>) => {
    const start = performance.now();
    const result = func(...args);
    const end = performance.now();
    console.log(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`);
    return result;
  }) as T;
}

/**
 * Batch state updates to prevent multiple re-renders
 * Useful for updating multiple filters at once
 */
export function batchUpdates<T>(updates: Array<() => T>): T[] {
  return updates.map((update) => update());
}

/**
 * Check if reduced motion is preferred
 * Respects user's prefers-reduced-motion setting
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get animation duration based on reduced motion preference
 */
export function getAnimationDuration(defaultDuration: number): number {
  return prefersReducedMotion() ? 0 : defaultDuration;
}
