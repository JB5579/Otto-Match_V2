import type { Vehicle } from '../app/types/api';
import type { VehicleStatus } from '../context/VehicleContext';

/**
 * WebSocket message types for real-time conversation updates
 * Story 3-3b: vehicle_update removed (now handled by SSE)
 */
export type WebSocketMessageType = 'conversation_message' | 'preference_change' | 'availability_status_update' | 'error' | 'ping' | 'pong';

/**
 * Base WebSocket message interface
 */
export interface BaseWebSocketMessage {
  type: WebSocketMessageType;
  timestamp: string;
  requestId?: string;
}

/**
 * User preferences extracted from conversation
 */
export interface UserPreferences {
  budget?: {
    min?: number;
    max?: number;
  };
  bodyType?: string[];
  make?: string[];
  model?: string[];
  year?: {
    min?: number;
    max?: number;
  };
  mileage?: {
    max?: number;
  };
  fuelType?: string[];
  transmission?: string[];
  drivetrain?: string[];
  features?: string[];
  color?: string[];
  location?: {
    city?: string;
    state?: string;
    radius?: number;
  };
}

/**
 * Conversation context from Otto AI
 */
export interface ConversationContext {
  sessionId: string;
  messageCount: number;
  userIntent?: string;
  confidenceScore?: number;
  extractedEntities?: Record<string, any>;
}

/**
 * Vehicle update message sent from backend when preferences change
 * Triggers cascade animation in vehicle grid
 * @deprecated Story 3-3b: Vehicle updates now use SSE (VehicleUpdateSSEEvent)
 */
export interface VehicleUpdateMessage extends BaseWebSocketMessage {
  type: 'vehicle_update';
  vehicles: Vehicle[];
  matchScores?: number[];
  conversationContext?: ConversationContext;
}

/**
 * Conversation message response from Otto AI
 * Contains the assistant's response to a user message
 */
export interface ConversationMessageResponse extends BaseWebSocketMessage {
  type: 'conversation_message';
  content: string;
  requestId: string;
  metadata?: {
    extractedPreferences?: UserPreferences;
    vehicleCount?: number;
    confidence?: number;
  };
}

/**
 * Preference change message sent when Otto extracts new preferences
 * Updates conversation context without necessarily changing vehicles
 */
export interface PreferenceChangeMessage extends BaseWebSocketMessage {
  type: 'preference_change';
  preferences: UserPreferences;
  extractionConfidence: number;
  changedFields?: string[];
}

/**
 * Availability status update message sent when vehicle status changes
 * Triggers real-time status updates in vehicle grid and notifications
 */
export interface AvailabilityStatusUpdateMessage extends BaseWebSocketMessage {
  type: 'availability_status_update';
  data: {
    vehicle_id: string;
    old_status: VehicleStatus;
    new_status: VehicleStatus;
    reservation_expiry?: string;
    priority_until?: string;
  };
}

/**
 * Error message for WebSocket communication failures
 */
export interface ErrorMessage extends BaseWebSocketMessage {
  type: 'error';
  errorCode: string;
  message: string;
  retryable: boolean;
  details?: Record<string, any>;
}

/**
 * Ping/Pong messages for connection health check
 */
export interface PingMessage extends BaseWebSocketMessage {
  type: 'ping';
}

export interface PongMessage extends BaseWebSocketMessage {
  type: 'pong';
}

/**
 * Union type of all WebSocket messages
 * Story 3-3b: VehicleUpdateMessage deprecated but kept for type compatibility
 */
export type WebSocketMessage =
  | ConversationMessageResponse
  | VehicleUpdateMessage
  | PreferenceChangeMessage
  | AvailabilityStatusUpdateMessage
  | ErrorMessage
  | PingMessage
  | PongMessage;

/**
 * Conversation message for chat display
 */
export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    extractedPreferences?: UserPreferences;
    vehicleCount?: number;
    confidence?: number;
  };
}

/**
 * Type guard for ConversationMessageResponse
 */
export function isConversationMessageResponse(msg: any): msg is ConversationMessageResponse {
  return msg?.type === 'conversation_message' && typeof msg.content === 'string';
}

/**
 * Type guard for VehicleUpdateMessage
 */
export function isVehicleUpdateMessage(msg: any): msg is VehicleUpdateMessage {
  return msg?.type === 'vehicle_update' && Array.isArray(msg.vehicles);
}

/**
 * Type guard for PreferenceChangeMessage
 */
export function isPreferenceChangeMessage(msg: any): msg is PreferenceChangeMessage {
  return msg?.type === 'preference_change' && msg.preferences !== undefined;
}

/**
 * Type guard for AvailabilityStatusUpdateMessage
 */
export function isAvailabilityStatusUpdateMessage(msg: any): msg is AvailabilityStatusUpdateMessage {
  return msg?.type === 'availability_status_update' && msg.data?.vehicle_id !== undefined;
}

/**
 * Type guard for ErrorMessage
 */
export function isErrorMessage(msg: any): msg is ErrorMessage {
  return msg?.type === 'error' && typeof msg.errorCode === 'string';
}

/**
 * Parse incoming WebSocket message with type validation
 */
export function parseWebSocketMessage(data: string | MessageEvent['data']): WebSocketMessage | null {
  try {
    const parsed = typeof data === 'string' ? JSON.parse(data) : data;

    // Validate has required fields
    if (!parsed.type || !parsed.timestamp) {
      console.error('[parseWebSocketMessage] Invalid message format:', parsed);
      return null;
    }

    return parsed as WebSocketMessage;
  } catch (error) {
    console.error('[parseWebSocketMessage] Failed to parse message:', error);
    return null;
  }
}

// ============================================================================
// SSE (Server-Sent Events) Types for Story 3-3b
// ============================================================================

/**
 * SSE event types for vehicle updates
 * After Story 3-3b migration, vehicle updates use SSE (not WebSocket)
 */
export type SSEEventType = 'vehicle_update' | 'availability_status_update';

/**
 * Base SSE event interface
 * Follows EventSource message format with event:, data:, id: fields
 */
export interface BaseSSEEvent {
  event: SSEEventType;
  data: unknown;
  id: string;
}

/**
 * Vehicle update event via SSE
 * Sent from backend at GET /api/vehicles/updates
 * Triggers cascade animation in vehicle grid
 */
export interface VehicleUpdateSSEEvent extends BaseSSEEvent {
  event: 'vehicle_update';
  data: {
    vehicles: Vehicle[];
    timestamp: string;
    requestId: string;
  };
}

/**
 * Availability status update event via SSE
 * Sent when vehicle status changes (available, reserved, sold)
 */
export interface AvailabilityStatusUpdateSSEEvent extends BaseSSEEvent {
  event: 'availability_status_update';
  data: {
    vehicle_id: string;
    old_status: VehicleStatus;
    new_status: VehicleStatus;
    reservation_expiry?: string;
    priority_until?: string;
    timestamp: string;
  };
}

/**
 * Union type of all SSE events
 */
export type SSEEvent = VehicleUpdateSSEEvent | AvailabilityStatusUpdateSSEEvent;

/**
 * Parse SSE message from EventSource
 * Validates SSE format (event:, data:, id:)
 */
export function parseSSEMessage(event: MessageEvent): SSEEvent | null {
  try {
    // EventSource already parses the data field as JSON
    // The event type is in event.type (event name)
    // The event ID is in event.lastEventId

    const eventType = event.type as SSEEventType;
    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
    const eventId = event.lastEventId;

    // Validate required fields
    if (!eventType || !data || !eventId) {
      console.error('[parseSSEMessage] Invalid SSE message format:', { eventType, data, eventId });
      return null;
    }

    return {
      event: eventType,
      data,
      id: eventId,
    } as SSEEvent;
  } catch (error) {
    console.error('[parseSSEMessage] Failed to parse SSE message:', error);
    return null;
  }
}

/**
 * Type guard for VehicleUpdateSSEEvent
 */
export function isVehicleUpdateSSEEvent(event: any): event is VehicleUpdateSSEEvent {
  return event?.event === 'vehicle_update' && Array.isArray(event.data?.vehicles);
}

/**
 * Type guard for AvailabilityStatusUpdateSSEEvent
 */
export function isAvailabilityStatusUpdateSSEEvent(event: any): event is AvailabilityStatusUpdateSSEEvent {
  return event?.event === 'availability_status_update' && event.data?.vehicle_id !== undefined;
}
