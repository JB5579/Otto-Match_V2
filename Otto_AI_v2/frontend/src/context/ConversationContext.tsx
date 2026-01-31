import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../app/contexts/AuthContext';
import type {
  ConversationMessage,
  UserPreferences,
  PreferenceChangeMessage,
  ConversationMessageResponse,
} from '../types/conversation';
import {
  isConversationMessageResponse,
  isPreferenceChangeMessage,
  isErrorMessage,
  parseWebSocketMessage,
} from '../types/conversation';

interface ConversationContextValue {
  messages: ConversationMessage[];
  currentPreferences: UserPreferences;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  sendMessage: (text: string) => void;
  updatePreferences: (prefs: UserPreferences) => void;
  reconnect: () => void;
  clearError: () => void;
}

const ConversationContext = createContext<ConversationContextValue | null>(null);

export interface ConversationProviderProps {
  children: React.ReactNode;
  websocketUrl?: string;
}

/**
 * ConversationProvider manages global conversation state
 *
 * Features:
 * - WebSocket connection to backend for Otto chat messages ONLY
 * - Message history with timestamps
 * - User preference tracking from conversation
 * - Integration with AuthContext for JWT authentication
 * - Automatic reconnection handling
 *
 * Context Hierarchy:
 * AuthProvider → ConversationContext → VehicleContext → VehicleGrid
 *
 * **Story 3-3b SSE Migration:**
 * - WebSocket now handles ONLY chat messages (conversation_message type)
 * - Vehicle updates removed - now handled by SSE via VehicleContext
 * - No longer handles vehicle_update or availability_status_update messages
 * - Otto chat functionality unchanged
 */
export const ConversationProvider: React.FC<ConversationProviderProps> = ({
  children,
  websocketUrl = 'ws://localhost:8000/ws/conversation',
}) => {
  const { session } = useAuth();
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentPreferences, setCurrentPreferences] = useState<UserPreferences>({});
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Track sent messages awaiting responses
  const pendingMessagesRef = useRef<Set<string>>(new Set());

  // Get JWT token for WebSocket authentication
  const token = session?.access_token ?? undefined;

  // WebSocket connection for Otto chat ONLY
  const {
    isConnected,
    lastMessage,
    sendMessage: wsSendMessage,
    reconnect: wsReconnect,
    error: wsError,
  } = useWebSocket({
    url: websocketUrl,
    token,
    reconnect: true,
    reconnectAttempts: 3,
    onOpen: () => {
      console.log('[ConversationContext] WebSocket connected for chat');
      setLocalError(null);
    },
    onClose: () => {
      console.log('[ConversationContext] WebSocket disconnected');
    },
    onError: () => {
      setLocalError('Connection to Otto AI lost. Retrying...');
    },
  });

  /**
   * Handle incoming WebSocket messages
   * Story 3-3b: Only handles chat-related messages (conversation_message, preference_change, error)
   * Vehicle updates removed - now handled by SSE
   */
  useEffect(() => {
    if (!lastMessage) return;

    const message = parseWebSocketMessage(lastMessage.data);
    if (!message) return;

    if (isConversationMessageResponse(message)) {
      handleConversationResponse(message);
    } else if (isPreferenceChangeMessage(message)) {
      handlePreferenceChange(message);
    } else if (isErrorMessage(message)) {
      handleError(message);
    }
    // Note: vehicle_update messages no longer handled here (Story 3-3b SSE migration)
  }, [lastMessage]);

  /**
   * Handle conversation message responses from Otto
   */
  const handleConversationResponse = useCallback((message: ConversationMessageResponse) => {
    console.log('[ConversationContext] Otto response received', {
      content: message.content,
      requestId: message.requestId,
    });

    // Add Otto's response message to chat
    const ottoMessage: ConversationMessage = {
      id: message.requestId || `otto-${Date.now()}`,
      role: 'assistant',
      content: message.content,
      timestamp: message.timestamp,
      metadata: message.metadata,
    };

    setMessages((prev) => [...prev, ottoMessage]);
    setIsLoading(false);

    // Mark pending message as resolved
    if (message.requestId) {
      pendingMessagesRef.current.delete(message.requestId);
    }

    // Update preferences if included in response
    if (message.metadata?.extractedPreferences) {
      setCurrentPreferences((prev) => ({
        ...prev,
        ...message.metadata!.extractedPreferences,
      }));
    }
  }, []);

  /**
   * Handle preference change messages
   */
  const handlePreferenceChange = useCallback((message: PreferenceChangeMessage) => {
    console.log('[ConversationContext] Preference change received', {
      preferences: message.preferences,
      confidence: message.extractionConfidence,
    });

    setCurrentPreferences((prev) => ({
      ...prev,
      ...message.preferences,
    }));

    setIsLoading(false);
  }, []);

  /**
   * Handle error messages
   */
  const handleError = useCallback((message: any) => {
    console.error('[ConversationContext] Error message received', message);
    setLocalError(message.message || 'An error occurred');
    setIsLoading(false);
  }, []);

  /**
   * Send message to Otto AI
   * Story 3-3b: Handles only chat messages via WebSocket
   * Vehicle responses are now handled separately by SSE
   */
  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return;

      const messageId = `user-${Date.now()}`;
      const timestamp = new Date().toISOString();

      // Add user message to chat
      const userMessage: ConversationMessage = {
        id: messageId,
        role: 'user',
        content: text,
        timestamp,
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // Send via WebSocket
      wsSendMessage({
        type: 'conversation_message',
        content: text,
        requestId: messageId,
        timestamp,
      });

      // Track pending message
      pendingMessagesRef.current.add(messageId);

      console.log('[ConversationContext] Message sent to Otto', { text, messageId });
    },
    [wsSendMessage]
  );

  /**
   * Manually update preferences
   */
  const updatePreferences = useCallback((prefs: UserPreferences) => {
    setCurrentPreferences((prev) => ({
      ...prev,
      ...prefs,
    }));

    console.log('[ConversationContext] Preferences updated', prefs);
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setLocalError(null);
  }, []);

  /**
   * Reconnect to WebSocket
   */
  const reconnect = useCallback(() => {
    setLocalError(null);
    wsReconnect();
  }, [wsReconnect]);

  // Combine local and WebSocket errors
  const error = localError || (wsError ? wsError.message : null);

  const value: ConversationContextValue = {
    messages,
    currentPreferences,
    isConnected,
    isLoading,
    error,
    sendMessage,
    updatePreferences,
    reconnect,
    clearError,
  };

  return <ConversationContext.Provider value={value}>{children}</ConversationContext.Provider>;
};

/**
 * Hook to access conversation context
 * Must be used within ConversationProvider
 */
export const useConversation = (): ConversationContextValue => {
  const context = useContext(ConversationContext);

  if (!context) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }

  return context;
};
