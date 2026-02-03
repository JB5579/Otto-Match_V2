import { useEffect, useRef, useState, useCallback } from 'react';

export interface UseWebSocketOptions {
  url: string;
  token?: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  reconnectAttempts?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: MessageEvent | null;
  sendMessage: (message: any) => void;
  reconnect: () => void;
  error: Error | null;
  connectionAttempts: number;
}

/**
 * Custom hook for managing WebSocket connections with automatic reconnection
 *
 * Features:
 * - Automatic reconnection with exponential backoff (5s, 10s, 20s, 30s max)
 * - JWT token authentication in handshake
 * - Connection state management
 * - Message queue for offline messages
 * - Cleanup on unmount
 *
 * @param options - WebSocket configuration options
 * @returns WebSocket connection state and controls
 */
export const useWebSocket = ({
  url,
  token,
  reconnect = true,
  reconnectInterval: _reconnectInterval = 5000,
  reconnectAttempts = 3,
  onOpen,
  onClose,
  onMessage,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<any[]>([]);

  /**
   * Calculate exponential backoff delay
   * 5s, 10s, 20s, 30s (max)
   */
  const getReconnectDelay = useCallback((attempt: number): number => {
    const delays = [5000, 10000, 20000, 30000];
    return delays[Math.min(attempt, delays.length - 1)];
  }, []);

  /**
   * Connect to WebSocket server with JWT authentication
   */
  const connect = useCallback(() => {
    try {
      // Clean up existing connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      // Build WebSocket URL with token if provided
      const wsUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = (event) => {
        console.log('[useWebSocket] Connection established', { url });
        setIsConnected(true);
        setError(null);
        setConnectionAttempts(0);

        // Send queued messages
        while (messageQueueRef.current.length > 0) {
          const queuedMessage = messageQueueRef.current.shift();
          ws.send(JSON.stringify(queuedMessage));
        }

        onOpen?.(event);
      };

      ws.onmessage = (event) => {
        console.log('[useWebSocket] Message received', { data: event.data });
        setLastMessage(event);
        onMessage?.(event);
      };

      ws.onclose = (event) => {
        console.log('[useWebSocket] Connection closed', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        setIsConnected(false);
        wsRef.current = null;

        onClose?.(event);

        // Attempt reconnection if enabled and not intentional close
        if (reconnect && !event.wasClean && connectionAttempts < reconnectAttempts) {
          const delay = getReconnectDelay(connectionAttempts);
          console.log(`[useWebSocket] Reconnecting in ${delay}ms (attempt ${connectionAttempts + 1}/${reconnectAttempts})`);

          setConnectionAttempts((prev) => prev + 1);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (connectionAttempts >= reconnectAttempts) {
          const err = new Error(`Failed to reconnect after ${reconnectAttempts} attempts`);
          setError(err);
          console.error('[useWebSocket] Max reconnection attempts reached', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[useWebSocket] WebSocket error', event);
        const err = new Error('WebSocket connection error');
        setError(err);
        onError?.(event);
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create WebSocket connection');
      console.error('[useWebSocket] Connection failed', error);
      setError(error);
    }
  }, [url, token, reconnect, reconnectAttempts, connectionAttempts, getReconnectDelay, onOpen, onMessage, onClose, onError]);

  /**
   * Send message through WebSocket
   * Queues message if not connected
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(payload);
      console.log('[useWebSocket] Message sent', { message });
    } else {
      console.warn('[useWebSocket] Not connected, queuing message', { message });
      messageQueueRef.current.push(message);
    }
  }, []);

  /**
   * Manual reconnect function
   * Resets connection attempts counter
   */
  const manualReconnect = useCallback(() => {
    console.log('[useWebSocket] Manual reconnect triggered');
    setConnectionAttempts(0);
    setError(null);
    connect();
  }, [connect]);

  // Initialize connection on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      console.log('[useWebSocket] Cleaning up WebSocket connection');

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }

      messageQueueRef.current = [];
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    reconnect: manualReconnect,
    error,
    connectionAttempts,
  };
};
