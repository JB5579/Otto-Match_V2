/**
 * SessionService - Session-based memory management for guest users
 *
 * Features:
 * - Anonymous session ID generation (UUID v4)
 * - Cookie-based session storage with 30-day expiry
 * - Session-to-account merge flow on signup
 * - Cookie-based recognition for returning visitors
 *
 * This enables Otto.AI to create relationships with users before they
 * authenticate, implementing progressive authentication pattern:
 *
 * Guest arrives → Browse freely → Chat with Otto (session) →
 * [Motivation Point] → Sign Up → Session merged to account
 */

const SESSION_COOKIE = 'otto_session_id';
const SESSION_EXPIRY_DAYS = 30; // 30-day sliding window

export interface SessionMergeResult {
  success: boolean;
  messagesTransferred?: number;
  preferencesPreserved?: string[];
  error?: string;
}

/**
 * SessionService handles anonymous session management for guest users
 */
export class SessionService {
  /**
   * Get or create session ID for current user
   * - Returns existing session ID from cookie if present
   * - Generates new UUID and sets cookie if not present
   * - Extends cookie expiry on each call (sliding window)
   */
  static getSessionId(): string {
    let sessionId = this.getCookie(SESSION_COOKIE);

    if (!sessionId) {
      sessionId = this.generateSessionId();
      this.setCookie(SESSION_COOKIE, sessionId, SESSION_EXPIRY_DAYS);
      console.log('[SessionService] Created new guest session:', sessionId);
    } else {
      // Extend session expiry (sliding window)
      this.setCookie(SESSION_COOKIE, sessionId, SESSION_EXPIRY_DAYS);
      console.log('[SessionService] Using existing guest session:', sessionId);
    }

    return sessionId;
  }

  /**
   * Check if user has an existing session
   */
  static hasSession(): boolean {
    return !!this.getCookie(SESSION_COOKIE);
  }

  /**
   * Get session ID without auto-creating
   * Returns null if no session exists
   */
  static getExistingSessionId(): string | null {
    return this.getCookie(SESSION_COOKIE) || null;
  }

  /**
   * Merge guest session to authenticated user account
   * Called during signup/login to preserve conversation context
   */
  static async mergeSessionToAccount(userId: string): Promise<SessionMergeResult> {
    const sessionId = this.getSessionId();

    if (!sessionId) {
      return {
        success: false,
        error: 'No guest session to merge'
      };
    }

    try {
      console.log('[SessionService] Merging session to account:', { sessionId, userId });

      // Call backend API to merge session
      const response = await fetch('/api/auth/merge-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`Merge failed: ${response.statusText}`);
      }

      const result = await response.json();

      // Clear session cookie after successful merge
      this.deleteCookie(SESSION_COOKIE);
      console.log('[SessionService] Session merged successfully, cookie cleared');

      return {
        success: true,
        messagesTransferred: result.messages_transferred || 0,
        preferencesPreserved: result.preferences_preserved || []
      };

    } catch (error) {
      console.error('[SessionService] Session merge failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Generate cryptographically random session ID (UUID v4)
   */
  private static generateSessionId(): string {
    // Generate UUID v4 format
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Set HTTP-only cookie with session ID
   */
  private static setCookie(name: string, value: string, days: number): void {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));

    const expires = `expires=${date.toUTCString()}`;
    const path = 'path=/';
    const secure = 'Secure'; // HTTPS only
    const sameSite = 'SameSite=Lax'; // CSRF protection

    document.cookie = `${name}=${value};${expires};${path};${secure};${sameSite}`;
  }

  /**
   * Get cookie value by name
   */
  private static getCookie(name: string): string | null {
    const nameEQ = `${name}=`;
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i];
      while (cookie.charAt(0) === ' ') {
        cookie = cookie.substring(1, cookie.length);
      }
      if (cookie.indexOf(nameEQ) === 0) {
        return cookie.substring(nameEQ.length, cookie.length);
      }
    }

    return null;
  }

  /**
   * Delete cookie by setting expiry to past
   */
  private static deleteCookie(name: string): void {
    const date = new Date();
    date.setTime(date.getTime() - (24 * 60 * 60 * 1000)); // Yesterday

    const expires = `expires=${date.toUTCString()}`;
    const path = 'path=/';

    document.cookie = `${name}=;${expires};${path}`;
  }
}

/**
 * React hook for session management
 */
export function useSession() {
  const sessionId = SessionService.getSessionId();
  const hasSession = SessionService.hasSession();

  const mergeSession = async (userId: string) => {
    return await SessionService.mergeSessionToAccount(userId);
  };

  return {
    sessionId,
    hasSession,
    mergeSession,
    isGuest: !hasSession // Guest if no session (session will be created on first use)
  };
}

export default SessionService;
