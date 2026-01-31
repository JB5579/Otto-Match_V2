import type {
  WebSocketMessage,
  PreferenceChangeMessage,
  UserPreferences,
} from '../types/conversation';
import { isPreferenceChangeMessage } from '../types/conversation';

/**
 * Preference extraction callback types
 * Story 3-3b: VehicleUpdateCallback deprecated (vehicles now use SSE)
 */
export type PreferenceChangeCallback = (preferences: UserPreferences, confidence: number) => void;

/**
 * PreferenceExtractor - Listens for WebSocket messages and extracts preference changes
 *
 * Story 3-3b: SSE Migration Notes:
 * - Vehicle updates now use SSE (useVehicleUpdates hook) instead of WebSocket
 * - This service now only handles preference_change messages from Otto chat
 * - VehicleUpdateMessage handling is deprecated and removed
 *
 * Features:
 * - Parses preference change messages from Otto AI conversation
 * - Triggers vehicle grid updates when preferences change
 * - Logs preference changes for analytics
 * - Validates extraction confidence
 * - Debounces rapid preference updates
 *
 * Integration:
 * - Works with ConversationContext WebSocket messages (Otto chat only)
 * - Updates VehicleContext when preferences change
 * - Provides callback interface for external consumers
 *
 * Usage:
 * ```typescript
 * const extractor = new PreferenceExtractor({
 *   onPreferenceChange: (prefs, confidence) => {
 *     console.log('Preferences updated:', prefs, confidence);
 *     updateVehicleGrid(prefs);
 *   }
 * });
 *
 * // In WebSocket message handler
 * extractor.handleMessage(websocketMessage);
 * ```
 */
export class PreferenceExtractor {
  private onPreferenceChange?: PreferenceChangeCallback;
  private debounceTimeout?: NodeJS.Timeout;
  private debounceDelay: number;
  private minConfidenceThreshold: number;

  constructor(options: {
    onPreferenceChange?: PreferenceChangeCallback;
    debounceDelay?: number;
    minConfidenceThreshold?: number;
  }) {
    this.onPreferenceChange = options.onPreferenceChange;
    this.debounceDelay = options.debounceDelay || 300; // 300ms debounce
    this.minConfidenceThreshold = options.minConfidenceThreshold || 0.5; // 50% confidence minimum
  }

  /**
   * Handle incoming WebSocket message
   * Story 3-3b: Only handles preference_change messages (vehicle updates use SSE)
   * Extracts preferences and triggers callbacks
   */
  public handleMessage(message: WebSocketMessage | string): void {
    try {
      // Parse message if string
      const parsedMessage: WebSocketMessage = typeof message === 'string'
        ? JSON.parse(message)
        : message;

      // Handle preference change messages
      if (isPreferenceChangeMessage(parsedMessage)) {
        this.handlePreferenceChange(parsedMessage);
      }

      // Story 3-3b: Vehicle updates now use SSE (useVehicleUpdates hook)
      // No longer handling vehicle_update messages here
    } catch (error) {
      console.error('[PreferenceExtractor] Failed to handle message:', error);
    }
  }

  /**
   * Handle preference change message
   * Validates confidence and debounces rapid updates
   */
  private handlePreferenceChange(message: PreferenceChangeMessage): void {
    const { preferences, extractionConfidence, timestamp, changedFields } = message;

    // Log preference change
    console.log('[PreferenceExtractor] Preference change detected', {
      preferences,
      confidence: extractionConfidence,
      changedFields,
      timestamp,
    });

    // Validate confidence threshold
    if (extractionConfidence < this.minConfidenceThreshold) {
      console.warn(
        '[PreferenceExtractor] Low extraction confidence',
        {
          confidence: extractionConfidence,
          threshold: this.minConfidenceThreshold,
        }
      );
      // Still process but log warning
    }

    // Debounce rapid updates
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }

    this.debounceTimeout = setTimeout(() => {
      // Trigger callback
      if (this.onPreferenceChange) {
        this.onPreferenceChange(preferences, extractionConfidence);
      }

      // Log analytics event (if analytics service exists)
      this.logPreferenceChange(preferences, extractionConfidence, changedFields);
    }, this.debounceDelay);
  }

  /**
   * Log preference change for analytics
   * In production, this would send to analytics service
   */
  private logPreferenceChange(
    preferences: UserPreferences,
    confidence: number,
    changedFields?: string[]
  ): void {
    // Analytics logging
    console.log('[Analytics] Preference Change', {
      event: 'preference_change',
      properties: {
        preferences,
        confidence,
        changedFields,
        timestamp: new Date().toISOString(),
      },
    });

    // In production:
    // analytics.track('preference_change', { preferences, confidence, changedFields });
  }

  /**
   * Update callbacks dynamically
   * Story 3-3b: Removed onVehicleUpdate callback (vehicles use SSE)
   */
  public setCallbacks(options: {
    onPreferenceChange?: PreferenceChangeCallback;
  }): void {
    if (options.onPreferenceChange) {
      this.onPreferenceChange = options.onPreferenceChange;
    }
  }

  /**
   * Cleanup
   */
  public destroy(): void {
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }
  }
}

/**
 * Singleton instance for global use
 */
let globalExtractor: PreferenceExtractor | null = null;

/**
 * Get or create global preference extractor instance
 * Story 3-3b: Removed onVehicleUpdate callback (vehicles use SSE)
 */
export function getPreferenceExtractor(
  callbacks?: {
    onPreferenceChange?: PreferenceChangeCallback;
  }
): PreferenceExtractor {
  if (!globalExtractor) {
    globalExtractor = new PreferenceExtractor(callbacks || {});
  } else if (callbacks) {
    globalExtractor.setCallbacks(callbacks);
  }

  return globalExtractor;
}
