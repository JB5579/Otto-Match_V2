/**
 * Test Setup File
 * Story 3-8.20: Configuration for performance and visual tests
 */

import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Story 3-8.20: Extend Vitest expectations with Testing Library
expect.extend(matchers);

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock Intersection Observer
// Story 3-8.4: Required for lazy loading tests
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];

  constructor(
    private readonly callback: IntersectionObserverCallback,
    options?: IntersectionObserverInit
  ) {
    if (options?.rootMargin) this.rootMargin = options.rootMargin;
    if (options?.threshold) this.thresholds = Array.isArray(options.threshold)
      ? options.threshold
      : [options.threshold];
  }

  disconnect() {
    // Mock implementation
  }

  observe(target: Element) {
    // Simulate element being visible immediately
    setTimeout(() => {
      this.callback([{
        target,
        isIntersecting: true,
        intersectionRatio: 1,
        boundingClientRect: target.getBoundingClientRect(),
        intersectionRect: target.getBoundingClientRect(),
        rootBounds: null,
        time: Date.now(),
      }], this);
    }, 0);
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  unobserve(target: Element) {
    // Mock implementation
  }
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});

// Mock Resize Observer
// Story 3-8.12: Required for responsive grid tests
class MockResizeObserver implements ResizeObserver {
  constructor(private readonly callback: ResizeObserverCallback) {}

  disconnect() {
    // Mock implementation
  }

  observe(target: Element, options?: ResizeObserverOptions) {
    // Mock implementation
  }

  unobserve(target: Element) {
    // Mock implementation
  }
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: MockResizeObserver,
});

// Mock Performance API
// Story 3-8.20: Mock performance.now() for consistent test timing
const mockPerformanceNow = vi.fn(() => Date.now());
Object.defineProperty(performance, 'now', {
  writable: true,
  value: mockPerformanceNow,
});

// Mock requestAnimationFrame
// Story 3-8.13: Required for animation tests
global.requestAnimationFrame = (callback: FrameRequestCallback) => {
  return setTimeout(() => callback(Date.now()), 16) as unknown as number;
};

global.cancelAnimationFrame = (id: number) => {
  clearTimeout(id);
};

// Mock ResizeObserver for responsive tests
global.ResizeObserver = MockResizeObserver;
