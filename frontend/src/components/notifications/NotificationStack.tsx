import React from 'react';
import { AnimatePresence } from 'framer-motion';
import { AvailabilityNotification, Notification } from './AvailabilityNotification';

export interface NotificationStackProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
  onViewVehicle: (vehicleId: string) => void;
  maxVisible?: number;
}

/**
 * NotificationStack Component
 *
 * Renders a stack of notifications with automatic queuing and dismissal.
 *
 * @component
 * @example
 * ```tsx
 * <NotificationStack
 *   notifications={notifications}
 *   onDismiss={handleDismiss}
 *   onViewVehicle={handleViewVehicle}
 *   maxVisible={10}
 * />
 * ```
 *
 * @param {NotificationStackProps} props - Component props
 * @param {Notification[]} props.notifications - Array of active notifications
 * @param {(id: string) => void} props.onDismiss - Callback when notification is dismissed
 * @param {(vehicleId: string) => void} props.onViewVehicle - Callback when "View Vehicle" is clicked
 * @param {number} props.maxVisible - Maximum number of visible notifications (default: 10)
 *
 * Features:
 * - Stacks notifications vertically from bottom-right
 * - Limits visible notifications (default: 10)
 * - Smooth enter/exit animations (Framer Motion AnimatePresence)
 * - Responsive positioning (adjusts for mobile)
 * - Auto-collapses similar notifications
 */
export const NotificationStack: React.FC<NotificationStackProps> = React.memo(({
  notifications,
  onDismiss,
  onViewVehicle,
  maxVisible = 10,
}) => {
  // Limit visible notifications to maxVisible
  const visibleNotifications = notifications
    .filter(n => !n.dismissed)
    .slice(0, maxVisible);

  const containerStyles: React.CSSProperties = {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column-reverse',
    gap: '12px',
    maxHeight: 'calc(100vh - 48px)',
    overflowY: 'auto',
    pointerEvents: 'none',
  };

  // Responsive styles for mobile
  const mobileContainerStyles: React.CSSProperties = {
    ...containerStyles,
    left: '24px',
    right: '24px',
    bottom: '12px',
  };

  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div
      className="notification-stack"
      style={isMobile ? mobileContainerStyles : containerStyles}
    >
      <AnimatePresence mode="popLayout">
        {visibleNotifications.map((notification) => (
          <div
            key={notification.id}
            style={{ pointerEvents: 'auto' }}
          >
            <AvailabilityNotification
              notification={notification}
              onDismiss={() => onDismiss(notification.id)}
              onViewVehicle={onViewVehicle}
            />
          </div>
        ))}
      </AnimatePresence>

      {/* Show "more notifications" indicator if queue exceeds max */}
      {notifications.filter(n => !n.dismissed).length > maxVisible && (
        <div
          style={{
            padding: '8px 16px',
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(12px)',
            borderRadius: '8px',
            color: '#FFFFFF',
            fontSize: '12px',
            fontWeight: 600,
            textAlign: 'center',
            pointerEvents: 'auto',
          }}
          role="status"
          aria-live="polite"
        >
          +{notifications.filter(n => !n.dismissed).length - maxVisible} more notifications
        </div>
      )}
    </div>
  );
});

NotificationStack.displayName = 'NotificationStack';

export default NotificationStack;
