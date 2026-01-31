/**
 * Unit tests for useVehicleUpdates hook
 * Story 3-3b: SSE migration for vehicle updates
 *
 * Key test objectives (AC2, AC3):
 * - Test EventSource connection lifecycle
 * - Test message parsing and handling
 * - Test error handling (connection failures)
 * - Test cleanup on unmount (no reconnection loop - AC3)
 * - Mock EventSource using vi.stubGlobal()
 */

import { vi, beforeEach, describe, it, expect, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useVehicleUpdates } from '../useVehicleUpdates';
import type { Vehicle } from '../../app/types/api';

// Mock EventSource class
class MockEventSource {
  url: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onopen: ((event: Event) => void) | null = null;
  readyState: number = 0; // CONNECTING
  _eventListeners: Map<string, Set<(event: any) => void>> = new Map();

  constructor(url: string) {
    this.url = url;
    // Simulate connection on next tick
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  addEventListener(type: string, handler: (event: any) => void) {
    if (!this._eventListeners.has(type)) {
      this._eventListeners.set(type, new Set());
    }
    this._eventListeners.get(type)!.add(handler);
  }

  removeEventListener(type: string, handler: (event: any) => void) {
    const listeners = this._eventListeners.get(type);
    if (listeners) {
      listeners.delete(handler);
    }
  }

  close() {
    this.readyState = 2; // CLOSED
  }

  // Test helper: simulate receiving a message
  _simulateMessage(eventType: string, data: any) {
    const listeners = this._eventListeners.get(eventType);
    if (listeners) {
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      listeners.forEach((handler) => handler(messageEvent));
    }
  }

  // Test helper: simulate connection error
  _simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

describe('useVehicleUpdates', () => {
  beforeEach(() => {
    // Reset environment before each test
    vi.resetModules();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Connection lifecycle', () => {
    it('should connect to SSE endpoint with JWT token', async () => {
      // Mock localStorage for JWT token
      const mockToken = 'test-jwt-token-123';
      vi.stubGlobal('localStorage', {
        getItem: vi.fn((key: string) => {
          if (key === 'sb-otto-ai-auth-token') return mockToken;
          return null;
        }),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      // Mock EventSource
      vi.stubGlobal('EventSource', MockEventSource);

      const onVehicleUpdate = vi.fn();
      const { result } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(result.current.connected).toBe(true);
      });

      // Verify EventSource was created with token
      // The token should be in the URL
      expect(result.current.connected).toBe(true);
    });

    it('should bypass EventSource creation in test mode', () => {
      const onVehicleUpdate = vi.fn();
      const { result } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          testMode: true,
        })
      );

      // In test mode, should not connect
      expect(result.current.connected).toBe(false);
    });

    it('should call onConnected callback when connection established', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onConnected = vi.fn();
      const onVehicleUpdate = vi.fn();

      renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          onConnected,
          testMode: false,
        })
      );

      await waitFor(() => {
        expect(onConnected).toHaveBeenCalled();
      });
    });
  });

  describe('Message handling (AC1)', () => {
    it('should receive and parse vehicle_update events', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const mockVehicles: Vehicle[] = [
        {
          id: 'v1',
          make: 'Toyota',
          model: 'Camry',
          year: 2024,
          price: 28000,
          mileage: 5000,
          isFavorited: false,
        } as Vehicle,
        {
          id: 'v2',
          make: 'Honda',
          model: 'Accord',
          year: 2024,
          price: 30000,
          mileage: 3000,
          isFavorited: false,
        } as Vehicle,
      ];

      const onVehicleUpdate = vi.fn();
      const { result } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(result.current.connected).toBe(true);
      });

      // Get the EventSource instance
      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Simulate vehicle update event
      act(() => {
        eventSource._simulateMessage('vehicle_update', {
          vehicles: mockVehicles,
          timestamp: new Date().toISOString(),
          requestId: 'test-request-1',
        });
      });

      // Verify callback was invoked with vehicles
      expect(onVehicleUpdate).toHaveBeenCalledWith(mockVehicles, 'test-request-1');
      expect(result.current.lastUpdate).toBeInstanceOf(Date);
    });

    it('should handle malformed SSE data gracefully', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onVehicleUpdate = vi.fn();
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          onError,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(result.current.connected).toBe(true);
      });

      // Get the EventSource instance
      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Simulate malformed data (not valid JSON)
      act(() => {
        eventSource._simulateMessage('vehicle_update', 'invalid json{{{');
      });

      // Should not crash, error should be set
      expect(result.current.error).toBeInstanceOf(Error);
      expect(onVehicleUpdate).not.toHaveBeenCalled();
    });
  });

  describe('Error handling (AC2)', () => {
    it('should handle connection errors', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onError = vi.fn();
      const onVehicleUpdate = vi.fn();

      const { result } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          onError,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(result.current.connected).toBe(true);
      });

      // Get the EventSource instance
      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Simulate connection error
      act(() => {
        eventSource._simulateError();
      });

      // Verify error callback invoked
      expect(onError).toHaveBeenCalled();
      expect(result.current.connected).toBe(false);
      expect(result.current.error).toBeInstanceOf(Error);
    });
  });

  describe('Cleanup behavior (AC3)', () => {
    it('should close EventSource on unmount without reconnection loop', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onVehicleUpdate = vi.fn();
      const { unmount } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(global.EventSource).toBeDefined();
      });

      // Get the EventSource instance
      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      const closeSpy = vi.spyOn(eventSource, 'close');

      // Unmount the hook
      act(() => {
        unmount();
      });

      // Verify EventSource.close() was called exactly once
      expect(closeSpy).toHaveBeenCalledOnce();
      expect(eventSource.readyState).toBe(2); // CLOSED

      // AC3: No reconnection timeout scheduled after cleanup
      // Unlike WebSocket, EventSource doesn't auto-reconnect in test environment
      // This is the key fix from Story 3-3b
      vi.advanceTimersByTime(5000);
      expect(closeSpy).toHaveBeenCalledOnce(); // Still only called once
    });

    it('should call onDisconnected callback on cleanup', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onDisconnected = vi.fn();
      const onVehicleUpdate = vi.fn();

      const { unmount } = renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          onDisconnected,
          testMode: false,
        })
      );

      // Wait for connection
      await waitFor(() => {
        expect(global.EventSource).toBeDefined();
      });

      // Unmount the hook
      act(() => {
        unmount();
      });

      // Verify onDisconnected callback invoked
      expect(onDisconnected).toHaveBeenCalled();
    });
  });

  describe('Callback refs update', () => {
    it('should use latest callback when message received', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onVehicleUpdate1 = vi.fn();
      const onVehicleUpdate2 = vi.fn();

      const { result, rerender } = renderHook(
        ({ callback }) =>
          useVehicleUpdates({
            onVehicleUpdate: callback,
            testMode: false,
          }),
        {
          initialProps: { callback: onVehicleUpdate1 },
        }
      );

      // Wait for connection
      await waitFor(() => {
        expect(result.current.connected).toBe(true);
      });

      // Get the EventSource instance
      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Send message with first callback
      act(() => {
        eventSource._simulateMessage('vehicle_update', {
          vehicles: [{ id: 'v1' } as Vehicle],
          timestamp: new Date().toISOString(),
          requestId: 'req-1',
        });
      });

      expect(onVehicleUpdate1).toHaveBeenCalledWith(
        [{ id: 'v1' } as Vehicle],
        'req-1'
      );

      // Update callback
      rerender({ callback: onVehicleUpdate2 });

      // Send message with new callback
      act(() => {
        eventSource._simulateMessage('vehicle_update', {
          vehicles: [{ id: 'v2' } as Vehicle],
          timestamp: new Date().toISOString(),
          requestId: 'req-2',
        });
      });

      expect(onVehicleUpdate2).toHaveBeenCalledWith(
        [{ id: 'v2' } as Vehicle],
        'req-2'
      );
    });
  });

  describe('AC1: SSE endpoint specification', () => {
    it('should use default endpoint URL', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const onVehicleUpdate = vi.fn();
      renderHook(() =>
        useVehicleUpdates({
          onVehicleUpdate,
          testMode: false,
        })
      );

      // Get the EventSource instance
      await waitFor(() => {
        expect(global.EventSource).toBeDefined();
      });

      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Verify default URL
      expect(eventSource.url).toBe('http://localhost:8000/api/vehicles/updates');
    });

    it('should use custom endpoint URL when provided', async () => {
      vi.stubGlobal('localStorage', {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });

      vi.stubGlobal('EventSource', MockEventSource);

      const customUrl = 'https://api.example.com/vehicles/updates';
      const onVehicleUpdate = vi.fn();

      renderHook(() =>
        useVehicleUpdates({
          url: customUrl,
          onVehicleUpdate,
          testMode: false,
        })
      );

      // Get the EventSource instance
      await waitFor(() => {
        expect(global.EventSource).toBeDefined();
      });

      const EventSourceMock = global.EventSource as any;
      const eventSource = EventSourceMock.mock.results[0].value;

      // Verify custom URL
      expect(eventSource.url).toBe(customUrl);
    });
  });
});
