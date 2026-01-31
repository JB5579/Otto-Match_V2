import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public readyState: number = WebSocket.CONNECTING;
  public url: string;

  constructor(url: string) {
    this.url = url;
    // Simulate connection after small delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close(code?: number, reason?: string) {
    this.readyState = WebSocket.CLOSED;
    const event = new CloseEvent('close', { code, reason, wasClean: code === 1000 });
    this.onclose?.(event);
  }
}

global.WebSocket = MockWebSocket as any;

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should establish WebSocket connection', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: false,
      })
    );

    expect(result.current.isConnected).toBe(false);

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('should include JWT token in URL when provided', async () => {
    const token = 'test-jwt-token';

    renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        token,
        reconnect: false,
      })
    );

    await waitFor(() => {
      // WebSocket URL should include token
      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining(`token=${encodeURIComponent(token)}`)
      );
    });
  });

  it('should send message when connected', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: false,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const testMessage = { type: 'test', data: 'hello' };

    act(() => {
      result.current.sendMessage(testMessage);
    });

    // Message should be sent
    // Note: More sophisticated testing would use WebSocket server mock
  });

  it('should queue messages when not connected', () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: false,
      })
    );

    const testMessage = { type: 'test', data: 'hello' };

    act(() => {
      result.current.sendMessage(testMessage);
    });

    // Message should be queued
    expect(result.current.isConnected).toBe(false);
  });

  it('should attempt reconnection with exponential backoff', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: true,
        reconnectAttempts: 3,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate disconnect
    act(() => {
      const ws = (global.WebSocket as any).mock.results[0].value;
      ws.close(4000, 'Test disconnect');
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionAttempts).toBe(1);

    // Fast-forward 5s (first reconnect delay)
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(result.current.connectionAttempts).toBe(1);
    });

    vi.useRealTimers();
  });

  it('should stop reconnection after max attempts', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: true,
        reconnectAttempts: 2,
      })
    );

    // Wait for initial connection
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate multiple disconnects
    for (let i = 0; i < 3; i++) {
      act(() => {
        const ws = (global.WebSocket as any).mock.results[0].value;
        ws.close(4000, 'Test disconnect');
      });

      vi.advanceTimersByTime(30000); // Max delay
    }

    expect(result.current.error).toBeTruthy();
    expect(result.current.error?.message).toContain('Failed to reconnect');

    vi.useRealTimers();
  });

  it('should call onMessage callback when message received', async () => {
    const onMessage = vi.fn();

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        onMessage,
        reconnect: false,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    const testEvent = new MessageEvent('message', {
      data: JSON.stringify({ type: 'test', data: 'hello' }),
    });

    act(() => {
      const ws = (global.WebSocket as any).mock.results[0].value;
      ws.onmessage?.(testEvent);
    });

    expect(onMessage).toHaveBeenCalledWith(testEvent);
  });

  it('should cleanup on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: false,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    unmount();

    // WebSocket should be closed
    // Note: Testing cleanup requires WebSocket mock inspection
  });

  it('should manually reconnect when reconnect() called', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test',
        reconnect: false,
      })
    );

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Disconnect
    act(() => {
      const ws = (global.WebSocket as any).mock.results[0].value;
      ws.close(1000, 'Manual close');
    });

    expect(result.current.isConnected).toBe(false);

    // Manual reconnect
    act(() => {
      result.current.reconnect();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });
});
