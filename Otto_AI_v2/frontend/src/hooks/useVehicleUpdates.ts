import { useEffect, useState, useCallback, useRef } from 'react';
import type { Vehicle } from '../app/types/api';

/**
 * SSE event types for vehicle updates
 */
export interface VehicleUpdateEvent {
  type: 'vehicle_update';
  data: {
    vehicles: Vehicle[];
    timestamp: string;
    requestId: string;
  };
  id: string;
  event: string;
}

/**
 * Return type for useVehicleUpdates hook
 */
export interface UseVehicleUpdatesReturn {
  connected: boolean;
  lastUpdate: Date | null;
  error: Error | null;
}

/**
 * Options for useVehicleUpdates hook
 */
export interface UseVehicleUpdatesOptions {
  /**
   * SSE endpoint URL
   * @default 'http://localhost:8000/api/vehicles/updates'
   */
  url?: string;

  /**
   * Callback invoked when vehicle update is received
   */
  onVehicleUpdate: (vehicles: Vehicle[], eventId: string) => void;

  /**
   * Callback invoked when connection is established
   */
  onConnected?: () => void;

  /**
   * Callback invoked when connection is closed
   */
  onDisconnected?: () => void;

  /**
   * Callback invoked when connection error occurs
   */
  onError?: (error: Error) => void;

  /**
   * Bypass EventSource creation for testing
   * When true, hook returns early without connecting
   */
  testMode?: boolean;
}

/**
 * Custom hook for Server-Sent Events (SSE) vehicle updates
 *
 * Features:
 * - Native EventSource API (no library needed)
 * - JWT authentication via query parameter
 * - Automatic reconnection (browser built-in)
 * - Clean connection lifecycle (no reconnection loops in tests)
 * - Test mode bypass for easy mocking
 *
 * **Critical Test Behavior:**
 * In test mode (testMode=true or import.meta.env.TEST_MODE),
 * EventSource is NOT created. This prevents reconnection loops
 * that occurred with WebSocket in Story 3-3.
 *
 * @example
 * ```tsx
 * const { connected, lastUpdate, error } = useVehicleUpdates({
 *   onVehicleUpdate: (vehicles) => {
 *     console.log('Vehicles updated:', vehicles.length);
 *   }
 * });
 * ```
 *
 * @param options - Hook configuration options
 * @returns Connection state and metadata
 */
export function useVehicleUpdates({
  url = 'http://localhost:8000/api/vehicles/updates',
  onVehicleUpdate,
  onConnected,
  onDisconnected,
  onError,
  testMode = import.meta.env.TEST_MODE,
}: UseVehicleUpdatesOptions): UseVehicleUpdatesReturn {
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const onVehicleUpdateRef = useRef(onVehicleUpdate);
  const onConnectedRef = useRef(onConnected);
  const onDisconnectedRef = useRef(onDisconnected);
  const onErrorRef = useRef(onError);

  // Keep callback refs updated
  useEffect(() => {
    onVehicleUpdateRef.current = onVehicleUpdate;
    onConnectedRef.current = onConnected;
    onDisconnectedRef.current = onDisconnected;
    onErrorRef.current = onError;
  }, [onVehicleUpdate, onConnected, onDisconnected, onError]);

  useEffect(() => {
    // Bypass EventSource creation in test mode
    // This prevents reconnection loops in tests (AC3)
    if (testMode) {
      console.log('[useVehicleUpdates] Test mode: skipping EventSource creation');
      return;
    }

    // Get JWT token for authentication
    // Using dynamic import to avoid circular dependencies with AuthContext
    const getAuthToken = async (): Promise<string | null> => {
      try {
        // Dynamically import Supabase client to avoid circular deps
        const { createClient } = await import('@supabase/supabase-js');
        // Check for token in localStorage (set by Supabase auth)
        const token = localStorage.getItem('sb-otto-ai-auth-token');
        return token;
      } catch (err) {
        console.warn('[useVehicleUpdates] Failed to get auth token:', err);
        return null;
      }
    };

    let eventSource: EventSource | null = null;
    let cleanupCalled = false;

    const connect = async () => {
      if (cleanupCalled) return;

      try {
        const token = await getAuthToken();
        const sseUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;

        console.log('[useVehicleUpdates] Connecting to SSE endpoint:', sseUrl);

        eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          if (cleanupCalled) return;
          console.log('[useVehicleUpdates] SSE connection established');
          setConnected(true);
          setError(null);
          onConnectedRef.current?.();
        };

        // Listen for vehicle_update events
        eventSource.addEventListener('vehicle_update', (event: MessageEvent) => {
          if (cleanupCalled) return;

          try {
            const parsedData = JSON.parse(event.data) as VehicleUpdateEvent['data'];
            console.log('[useVehicleUpdates] Vehicle update received:', {
              count: parsedData.vehicles.length,
              eventId: event.lastEventId,
            });

            // Invoke callback with vehicles and event ID
            onVehicleUpdateRef.current(parsedData.vehicles, event.lastEventId);
            setLastUpdate(new Date(parsedData.timestamp));
          } catch (err) {
            console.error('[useVehicleUpdates] Failed to parse vehicle update:', err);
            setError(err instanceof Error ? err : new Error('Failed to parse vehicle update'));
          }
        });

        eventSource.onerror = (err) => {
          if (cleanupCalled) return;

          console.error('[useVehicleUpdates] SSE connection error:', err);
          setConnected(false);

          // EventSource will automatically attempt to reconnect
          // We set error state but don't close the connection
          const errorObj = new Error('SSE connection error');
          setError(errorObj);
          onErrorRef.current?.(errorObj);
        };

      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error('Failed to create EventSource');
        console.error('[useVehicleUpdates] Connection failed:', errorObj);
        setError(errorObj);
        onErrorRef.current?.(errorObj);
      }
    };

    connect();

    // Cleanup function
    return () => {
      console.log('[useVehicleUpdates] Cleaning up SSE connection');
      cleanupCalled = true;

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      setConnected(false);
      onDisconnectedRef.current?.();
    };
  }, [url, testMode]);

  return {
    connected,
    lastUpdate,
    error,
  };
}

/**
 * Hook default export
 */
export default useVehicleUpdates;
