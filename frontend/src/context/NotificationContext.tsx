import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { Notification, NotificationType } from '../components/notifications/AvailabilityNotification';

export interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'dismissed'>) => void;
  dismissNotification: (id: string) => void;
  dismissAll: () => void;
  notificationsByType: (type: NotificationType) => Notification[];
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const STORAGE_KEY = 'otto-ai-notifications';
const MAX_NOTIFICATIONS = 50; // Maximum total notifications to store

/**
 * NotificationProvider Component
 *
 * Provides notification state management with localStorage persistence.
 *
 * @component
 * @example
 * ```tsx
 * <NotificationProvider>
 *   <App />
 * </NotificationProvider>
 * ```
 *
 * Features:
 * - Create and manage notification queue
 * - Persist notifications to localStorage
 * - Auto-prune old notifications (keep last 50)
 * - Filter notifications by type
 * - Dismiss individual or all notifications
 * - Collapse similar notifications (same vehicle + type within 5 seconds)
 */
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Load notifications from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Filter out old notifications (> 24 hours)
        const now = Date.now();
        const oneDayAgo = now - 24 * 60 * 60 * 1000;
        const recent = parsed.filter((n: Notification) =>
          new Date(n.timestamp).getTime() > oneDayAgo
        );
        setNotifications(recent);
      }
    } catch (error) {
      console.error('Failed to load notifications from localStorage:', error);
    }
  }, []);

  // Save notifications to localStorage when they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } catch (error) {
      console.error('Failed to save notifications to localStorage:', error);
    }
  }, [notifications]);

  const addNotification = useCallback((
    notification: Omit<Notification, 'id' | 'timestamp' | 'dismissed'>
  ) => {
    setNotifications((prev) => {
      const now = new Date().toISOString();
      const id = `notification-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

      // Check for similar recent notifications (collapse duplicates)
      const fiveSecondsAgo = Date.now() - 5000;
      const hasSimilar = prev.some(
        (n) =>
          n.type === notification.type &&
          n.vehicleId === notification.vehicleId &&
          new Date(n.timestamp).getTime() > fiveSecondsAgo &&
          !n.dismissed
      );

      // Don't add if similar notification exists
      if (hasSimilar) {
        console.log('Collapsed duplicate notification:', notification.title);
        return prev;
      }

      const newNotification: Notification = {
        ...notification,
        id,
        timestamp: now,
        dismissed: false,
      };

      // Add to front of queue, limit total count
      const updated = [newNotification, ...prev].slice(0, MAX_NOTIFICATIONS);
      return updated;
    });
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, dismissed: true } : n))
    );
  }, []);

  const dismissAll = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, dismissed: true })));
  }, []);

  const notificationsByType = useCallback(
    (type: NotificationType) => {
      return notifications.filter((n) => n.type === type);
    },
    [notifications]
  );

  const value: NotificationContextType = {
    notifications,
    addNotification,
    dismissNotification,
    dismissAll,
    notificationsByType,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

/**
 * useNotifications Hook
 *
 * Access notification context and methods.
 *
 * @returns {NotificationContextType} Notification context value
 * @throws {Error} If used outside NotificationProvider
 *
 * @example
 * ```tsx
 * const { notifications, addNotification, dismissNotification } = useNotifications();
 *
 * addNotification({
 *   type: 'availability',
 *   vehicleId: '123',
 *   title: '2024 Tesla Model 3',
 *   message: 'This vehicle is now available!',
 *   vehicleThumbnail: '/path/to/image.jpg',
 *   vehicleName: '2024 Tesla Model 3',
 * });
 * ```
 */
export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

export default NotificationContext;
