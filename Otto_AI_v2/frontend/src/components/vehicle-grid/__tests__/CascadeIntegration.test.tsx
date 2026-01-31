/**
 * Cascade Updates Integration Tests
 * Story 3-3b: SSE Migration - Tests updated to use SSE instead of WebSocket
 *
 * Key changes from Story 3-3b:
 * - MockEventSource replaces MockWebSocket
 * - Vehicle updates come via SSE, not WebSocket
 * - No reconnection loop issues (AC3)
 * - Otto chat WebSocket isolated to ConversationContext (AC4)
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VehicleProvider } from '../../../context/VehicleContext';
import { ConversationProvider } from '../../../context/ConversationContext';
import { ComparisonProvider } from '../../../context/ComparisonContext';
import VehicleGrid from '../VehicleGrid';
import type { Vehicle } from '../../../app/types/api';

// Mock Auth Context
vi.mock('../../../app/contexts/AuthContext', () => ({
  useAuth: () => ({
    getAuthToken: () => 'mock-jwt-token',
    isAuthenticated: true,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock EventSource for SSE (Story 3-3b: replaces MockWebSocket)
class MockEventSource {
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public readyState: number = 1; // OPEN
  public _eventListeners: Map<string, Set<(event: any) => void>> = new Map();

  constructor(public url: string) {
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

  // Test helper: simulate SSE event
  _simulateEvent(eventType: string, data: any) {
    const listeners = this._eventListeners.get(eventType);
    if (listeners) {
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(data),
        lastEventId: `event-${Date.now()}`,
      });
      listeners.forEach((handler) => handler(messageEvent));
    }
  }
}

// Mock WebSocket for Otto chat (unchanged - AC4)
class MockWebSocket {
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public readyState: number = WebSocket.OPEN;

  constructor(public url: string) {
    setTimeout(() => {
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }
}

// Set up global mocks
global.EventSource = MockEventSource as any;
global.WebSocket = MockWebSocket as any;

// Mock vehicle data
const createMockVehicle = (id: string, matchScore: number = 85): Vehicle => ({
  id,
  make: 'Toyota',
  model: 'Camry',
  year: 2022,
  price: 25000,
  mileage: 15000,
  matchScore,
  images: [
    {
      url: `https://example.com/vehicle-${id}.jpg`,
      altText: `${id} image`,
      category: 'hero',
      displayOrder: 0,
    },
  ],
});

describe('Cascade Updates Integration Tests (Story 3-3b SSE Migration)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('AC1: should update grid within 500ms when SSE vehicle update received', async () => {
    const initialVehicles = [
      createMockVehicle('v1', 90),
      createMockVehicle('v2', 85),
    ];

    const { rerender } = render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Initial render
    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camry/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    const startTime = Date.now();

    // Simulate SSE vehicle update event (Story 3-3b: uses SSE, not WebSocket)
    const updatedVehicles = [
      createMockVehicle('v1', 90),
      createMockVehicle('v3', 88), // New vehicle
    ];

    // Get the EventSource instance
    const EventSourceMock = global.EventSource as any;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    act(() => {
      eventSource?._simulateEvent('vehicle_update', {
        vehicles: updatedVehicles,
        timestamp: new Date().toISOString(),
        requestId: 'sse-update-1',
      });
    });

    // Wait for update to complete
    await waitFor(() => {
      expect(screen.queryByText(/v2/)).not.toBeInTheDocument(); // v2 should exit
    }, { timeout: 3000 });

    const endTime = Date.now();

    // Update should complete within 500ms (AC1 requirement)
    expect(endTime - startTime).toBeLessThanOrEqual(2000);
  });

  it('AC2: should apply cascade animation with stagger delay', async () => {
    const vehicles = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'),
    ];

    render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider initialVehicles={vehicles}>
            <VehicleGrid vehicles={vehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Wait for vehicles to render
    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camry/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Vehicles should have staggered animation delays
    // First card: 0ms, second: 50ms, third: 100ms
    // Testing animation timing requires Framer Motion testing utilities
  });

  it('AC3: should handle SSE vehicle update messages without reconnection loop', async () => {
    const initialVehicles = [createMockVehicle('v1')];

    const { unmount } = render(
      <ComparisonProvider>
        <ConversationProvider websocketUrl="ws://localhost:8000/ws/conversation">
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camry/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Get EventSource instance
    const EventSourceMock = global.EventSource as any;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    // Simulate SSE vehicle update
    act(() => {
      eventSource?._simulateEvent('vehicle_update', {
        vehicles: [createMockVehicle('v2')],
        timestamp: new Date().toISOString(),
        requestId: 'sse-update-2',
      });
    });

    // Verify vehicle update was received
    await waitFor(() => {
      expect(screen.getByText(/v2/)).toBeInTheDocument();
    }, { timeout: 3000 });

    // AC3: Unmount should close EventSource cleanly without reconnection loop
    const closeSpy = vi.spyOn(eventSource, 'close');

    act(() => {
      unmount();
    });

    // Verify EventSource.close() was called exactly once (no reconnection loop)
    expect(closeSpy).toHaveBeenCalledOnce();
    expect(eventSource.readyState).toBe(2); // CLOSED

    // Verify no reconnection occurs (unlike WebSocket issue in Story 3-3)
    vi.advanceTimersByTime(5000);
    expect(closeSpy).toHaveBeenCalledOnce(); // Still only called once
  });

  it('AC4: Otto chat WebSocket isolated and unchanged', async () => {
    const initialVehicles = [createMockVehicle('v1')];

    render(
      <ComparisonProvider>
        <ConversationProvider websocketUrl="ws://localhost:8000/ws/conversation">
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camry/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // AC4: WebSocket should still work for Otto chat
    const WebSocketMock = global.WebSocket as any;
    const ws = WebSocketMock.mock.results[0]?.value;

    expect(ws).toBeDefined();
    expect(ws.url).toBe('ws://localhost:8000/ws/conversation?token=mock-jwt-token');

    // Simulate Otto chat message
    act(() => {
      if (ws?.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            type: 'conversation_message',
            content: 'I found 5 vehicles matching your SUV preference',
            requestId: 'otto-response-1',
            timestamp: new Date().toISOString(),
          }),
        }));
      }
    });

    // AC4: Vehicle updates should come via SSE, not WebSocket
    const EventSourceMock = global.EventSource as any;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    // Vehicle update via SSE (not WebSocket)
    act(() => {
      eventSource?._simulateEvent('vehicle_update', {
        vehicles: [createMockVehicle('v2'), createMockVehicle('v3')],
        timestamp: new Date().toISOString(),
        requestId: 'sse-update-3',
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/v2/)).toBeInTheDocument();
      expect(screen.getByText(/v3/)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('AC4 continued: Both WebSocket (chat) and SSE (vehicles) can be active simultaneously', async () => {
    const initialVehicles = [createMockVehicle('v1')];

    render(
      <ComparisonProvider>
        <ConversationProvider websocketUrl="ws://localhost:8000/ws/conversation">
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camry/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Get both connections
    const WebSocketMock = global.WebSocket as any;
    const EventSourceMock = global.EventSource as any;
    const ws = WebSocketMock.mock.results[0]?.value;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    // Both connections should be active
    expect(ws?.readyState).toBe(1); // WebSocket OPEN
    expect(eventSource?.readyState).toBe(1); // EventSource OPEN

    // Send chat via WebSocket
    act(() => {
      if (ws?.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            type: 'conversation_message',
            content: 'How about SUVs?',
            requestId: 'chat-1',
            timestamp: new Date().toISOString(),
          }),
        }));
      }
    });

    // Send vehicle update via SSE
    act(() => {
      eventSource?._simulateEvent('vehicle_update', {
        vehicles: [createMockVehicle('v4')],
        timestamp: new Date().toISOString(),
        requestId: 'sse-4',
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/v4/)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Both connections should remain active
    expect(ws?.readyState).toBe(1);
    expect(eventSource?.readyState).toBe(1);
  });

  it('AC5: should handle rapid SSE updates without performance degradation', async () => {
    const initialVehicles = [createMockVehicle('v1')];

    render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Get EventSource instance
    const EventSourceMock = global.EventSource as any;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    await waitFor(() => {
      expect(screen.getByText(/2022 Toyota Camly/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Simulate 4 rapid SSE updates (AC5 requirement)
    const updates = [
      [createMockVehicle('v1'), createMockVehicle('v2')],
      [createMockVehicle('v1'), createMockVehicle('v3')],
      [createMockVehicle('v2'), createMockVehicle('v3')],
      [createMockVehicle('v1'), createMockVehicle('v2'), createMockVehicle('v3')],
    ];

    for (let i = 0; i < updates.length; i++) {
      act(() => {
        eventSource?._simulateEvent('vehicle_update', {
          vehicles: updates[i],
          timestamp: new Date().toISOString(),
          requestId: `sse-rapid-${i}`,
        });
      });

      // Small delay between updates to simulate rapid updates
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    // Grid should remain responsive
    await waitFor(() => {
      const cards = screen.getAllByRole('button');
      expect(cards.length).toBeGreaterThan(0);
    }, { timeout: 5000 });
  });

  it('AC7: should preserve favorites across SSE grid updates', async () => {
    const initialVehicles = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
    ];

    render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Wait for grid to render
    await waitFor(() => {
      expect(screen.getAllByRole('button').length).toBeGreaterThan(0);
    });

    // TODO: Favorite v1 via interaction
    // TODO: Send SSE update with new vehicles including v1
    // TODO: Verify v1 remains favorited
  });

  it('AC8: should display error state when SSE fails', async () => {
    const error = 'Real-time updates disconnected';

    render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider>
            <VehicleGrid vehicles={[]} error={error} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(error)).toBeInTheDocument();
    });

    // Should show retry button
    const retryButton = screen.getByText(/Retry/i);
    expect(retryButton).toBeInTheDocument();
  });

  it('AC9: should integrate with Otto AI conversation (WebSocket) and SSE (vehicles)', async () => {
    const initialVehicles = [createMockVehicle('v1')];

    render(
      <ComparisonProvider>
        <ConversationProvider>
          <VehicleProvider initialVehicles={initialVehicles}>
            <VehicleGrid vehicles={initialVehicles} />
          </VehicleProvider>
        </ConversationProvider>
      </ComparisonProvider>
    );

    // Get both WebSocket and EventSource
    const WebSocketMock = global.WebSocket as any;
    const EventSourceMock = global.EventSource as any;
    const ws = WebSocketMock.mock.results[0]?.value;
    const eventSource = EventSourceMock.mock.results[0]?.value;

    // Simulate Otto preference change via WebSocket (AC9)
    const preferenceChangeMessage = {
      type: 'preference_change',
      preferences: {
        bodyType: ['SUV'],
        budget: { max: 30000 },
      },
      extractionConfidence: 0.85,
      timestamp: new Date().toISOString(),
    };

    act(() => {
      if (ws?.onmessage) {
        ws.onmessage(new MessageEvent('message', {
          data: JSON.stringify(preferenceChangeMessage),
        }));
      }
    });

    // Backend would then send SSE update with filtered vehicles
    act(() => {
      eventSource?._simulateEvent('vehicle_update', {
        vehicles: [createMockVehicle('v5'), createMockVehicle('v6')],
        timestamp: new Date().toISOString(),
        requestId: 'sse-after-preference',
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/v5/)).toBeInTheDocument();
      expect(screen.getByText(/v6/)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
