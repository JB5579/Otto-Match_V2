import React from 'react';

/**
 * Performance Monitoring Utilities (Task 3-3.20)
 *
 * Features:
 * - Web Vitals tracking (CLS, FID, LCP)
 * - Animation frame rate monitoring
 * - WebSocket latency tracking
 * - Grid update duration measurement
 * - Memory usage monitoring
 * - Analytics integration
 */

export interface PerformanceMetrics {
  // Web Vitals
  cls?: number; // Cumulative Layout Shift
  fid?: number; // First Input Delay
  lcp?: number; // Largest Contentful Paint

  // Custom Metrics
  gridUpdateDuration?: number;
  animationFrameRate?: number;
  websocketLatency?: number;
  memoryUsage?: number;
}

export interface PerformanceEntry {
  metric: string;
  value: number;
  timestamp: string;
  context?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceEntry[]> = new Map();
  private isDebugMode: boolean = false;

  constructor() {
    this.initWebVitals();
  }

  /**
   * Initialize Web Vitals monitoring
   * Tracks CLS, FID, LCP automatically
   */
  private initWebVitals(): void {
    // Import web-vitals library dynamically
    // npm install web-vitals
    if (typeof window !== 'undefined') {
      import('web-vitals').then(({ onCLS, onFID, onLCP }) => {
        onCLS((metric) => {
          this.recordMetric('cls', metric.value, {
            rating: metric.rating,
            delta: metric.delta,
          });
        });

        onFID((metric) => {
          this.recordMetric('fid', metric.value, {
            rating: metric.rating,
            delta: metric.delta,
          });
        });

        onLCP((metric) => {
          this.recordMetric('lcp', metric.value, {
            rating: metric.rating,
            delta: metric.delta,
          });
        });
      }).catch(() => {
        console.warn('[PerformanceMonitor] web-vitals not available');
      });
    }
  }

  /**
   * Record a performance metric
   */
  public recordMetric(
    metric: string,
    value: number,
    context?: Record<string, any>
  ): void {
    const entry: PerformanceEntry = {
      metric,
      value,
      timestamp: new Date().toISOString(),
      context,
    };

    if (!this.metrics.has(metric)) {
      this.metrics.set(metric, []);
    }

    this.metrics.get(metric)!.push(entry);

    // Log in debug mode
    if (this.isDebugMode) {
      console.log(`[PerformanceMonitor] ${metric}:`, value, context);
    }

    // Send to analytics (if available)
    this.sendToAnalytics(entry);
  }

  /**
   * Measure grid update duration
   */
  public measureGridUpdate<T>(
    updateFn: () => T,
    vehicleCount: number
  ): T {
    const startTime = performance.now();

    const result = updateFn();

    const endTime = performance.now();
    const duration = endTime - startTime;

    this.recordMetric('grid_update_duration', duration, {
      vehicleCount,
      target: 500, // AC1 target: <500ms
      passed: duration < 500,
    });

    return result;
  }

  /**
   * Measure animation frame rate
   * Target: 60fps (16ms frame time)
   */
  public measureFrameRate(durationMs: number = 1000): Promise<number> {
    return new Promise((resolve) => {
      let frameCount = 0;
      const startTime = performance.now();

      const measureFrame = () => {
        frameCount++;
        const currentTime = performance.now();
        const elapsed = currentTime - startTime;

        if (elapsed < durationMs) {
          requestAnimationFrame(measureFrame);
        } else {
          const fps = (frameCount / elapsed) * 1000;

          this.recordMetric('animation_frame_rate', fps, {
            target: 60,
            passed: fps >= 60,
          });

          resolve(fps);
        }
      };

      requestAnimationFrame(measureFrame);
    });
  }

  /**
   * Track WebSocket message latency
   */
  public trackWebSocketLatency(
    sendTimestamp: string,
    receiveTimestamp: string
  ): void {
    const sendTime = new Date(sendTimestamp).getTime();
    const receiveTime = new Date(receiveTimestamp).getTime();
    const latency = receiveTime - sendTime;

    this.recordMetric('websocket_latency', latency, {
      target: 100, // AC3 target: <100ms
      passed: latency < 100,
    });
  }

  /**
   * Monitor memory usage
   * (Only available in Chrome/Edge with --enable-precise-memory-info flag)
   */
  public monitorMemory(): void {
    if ('memory' in performance && (performance as any).memory) {
      const memory = (performance as any).memory;

      const usedJSHeapSize = memory.usedJSHeapSize / 1048576; // Convert to MB

      this.recordMetric('memory_usage_mb', usedJSHeapSize, {
        totalJSHeapSize: memory.totalJSHeapSize / 1048576,
        jsHeapSizeLimit: memory.jsHeapSizeLimit / 1048576,
      });
    }
  }

  /**
   * Get metrics summary
   */
  public getMetricsSummary(metric: string): {
    count: number;
    average: number;
    min: number;
    max: number;
    latest: number;
  } | null {
    const entries = this.metrics.get(metric);

    if (!entries || entries.length === 0) {
      return null;
    }

    const values = entries.map((e) => e.value);

    return {
      count: values.length,
      average: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      latest: values[values.length - 1],
    };
  }

  /**
   * Get all metrics
   */
  public getAllMetrics(): Map<string, PerformanceEntry[]> {
    return this.metrics;
  }

  /**
   * Clear metrics
   */
  public clearMetrics(): void {
    this.metrics.clear();
  }

  /**
   * Enable debug mode (console logging)
   */
  public enableDebugMode(): void {
    this.isDebugMode = true;
  }

  /**
   * Disable debug mode
   */
  public disableDebugMode(): void {
    this.isDebugMode = false;
  }

  /**
   * Send metrics to analytics service
   * In production, integrate with your analytics platform
   */
  private sendToAnalytics(entry: PerformanceEntry): void {
    // Example: Google Analytics 4
    // if (window.gtag) {
    //   window.gtag('event', 'performance_metric', {
    //     metric_name: entry.metric,
    //     metric_value: entry.value,
    //     metric_context: JSON.stringify(entry.context),
    //   });
    // }

    // Example: Custom analytics endpoint
    // fetch('/api/analytics/performance', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(entry),
    // });

    // For now, just log to console in dev
    if (process.env.NODE_ENV === 'development' && this.isDebugMode) {
      console.log('[Analytics] Performance Metric:', entry);
    }
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * React Hook for performance monitoring
 */
export function usePerformanceMonitoring(componentName: string) {
  const startTime = performance.now();

  // Monitor component mount time
  React.useEffect(() => {
    const mountTime = performance.now() - startTime;
    performanceMonitor.recordMetric(`${componentName}_mount_time`, mountTime);

    return () => {
      // Monitor component unmount
      const unmountTime = performance.now();
      performanceMonitor.recordMetric(`${componentName}_lifetime`, unmountTime - startTime);
    };
  }, [componentName, startTime]);

  return performanceMonitor;
}

/**
 * Performance debugging tools (Task 3-3.21)
 */
export const PerformanceDebugger = {
  /**
   * Display FPS counter overlay
   */
  showFPSCounter(): void {
    if (typeof window === 'undefined') return;

    const fpsMeter = document.createElement('div');
    fpsMeter.id = 'fps-meter';
    fpsMeter.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: rgba(0, 0, 0, 0.8);
      color: #0ea5e9;
      padding: 8px 12px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 14px;
      z-index: 9999;
    `;
    document.body.appendChild(fpsMeter);

    let frameCount = 0;
    let lastTime = performance.now();

    const updateFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      const elapsed = currentTime - lastTime;

      if (elapsed >= 1000) {
        const fps = (frameCount / elapsed) * 1000;
        fpsMeter.textContent = `${fps.toFixed(1)} FPS`;
        fpsMeter.style.color = fps >= 60 ? '#22c55e' : fps >= 30 ? '#eab308' : '#ef4444';

        frameCount = 0;
        lastTime = currentTime;
      }

      requestAnimationFrame(updateFPS);
    };

    requestAnimationFrame(updateFPS);
  },

  /**
   * Log performance metrics to console
   */
  logMetrics(): void {
    console.table(
      Array.from(performanceMonitor.getAllMetrics().entries()).map(([metric, _entries]) => {
        const summary = performanceMonitor.getMetricsSummary(metric);
        return {
          Metric: metric,
          Count: summary?.count || 0,
          Average: summary?.average.toFixed(2) || 0,
          Min: summary?.min.toFixed(2) || 0,
          Max: summary?.max.toFixed(2) || 0,
          Latest: summary?.latest.toFixed(2) || 0,
        };
      })
    );
  },

  /**
   * Enable all debug features
   */
  enableAll(): void {
    performanceMonitor.enableDebugMode();
    this.showFPSCounter();
    console.log('[PerformanceDebugger] Debug mode enabled. Use PerformanceDebugger.logMetrics() to view stats.');
  },
};

// Global access for debugging
if (typeof window !== 'undefined') {
  (window as any).performanceMonitor = performanceMonitor;
  (window as any).PerformanceDebugger = PerformanceDebugger;
}
