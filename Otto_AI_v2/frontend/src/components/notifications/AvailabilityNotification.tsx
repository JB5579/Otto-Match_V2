import React from 'react';
import { motion } from 'framer-motion';
import { X, ExternalLink } from 'lucide-react';

export type NotificationType = 'availability' | 'price' | 'message' | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  vehicleId?: string;
  title: string;
  message: string;
  timestamp: string;
  actionUrl?: string;
  actionLabel?: string;
  dismissed: boolean;
  vehicleThumbnail?: string;
  vehicleName?: string;
}

export interface AvailabilityNotificationProps {
  notification: Notification;
  onDismiss: () => void;
  onViewVehicle: (vehicleId: string) => void;
}

const notificationVariants = {
  enter: {
    x: 400,
    opacity: 0,
    scale: 0.9,
  },
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 25,
    },
  },
  exit: {
    x: 400,
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.2 },
  },
};

/**
 * AvailabilityNotification Component
 *
 * Toast notification for vehicle availability status changes.
 *
 * @component
 * @example
 * ```tsx
 * <AvailabilityNotification
 *   notification={notification}
 *   onDismiss={() => handleDismiss(notification.id)}
 *   onViewVehicle={(id) => handleViewVehicle(id)}
 * />
 * ```
 *
 * @param {AvailabilityNotificationProps} props - Component props
 * @param {Notification} props.notification - Notification data
 * @param {() => void} props.onDismiss - Callback when notification is dismissed
 * @param {(vehicleId: string) => void} props.onViewVehicle - Callback when "View Vehicle" is clicked
 *
 * Features:
 * - Vehicle thumbnail with fallback
 * - Status change message with vehicle info
 * - "View Vehicle" action button
 * - Dismiss button (X)
 * - Auto-dismiss after 30 seconds
 * - Slide-in animation from right (Framer Motion)
 * - Glass-morphism styling
 * - Keyboard navigation support (Tab, Enter, Escape)
 * - Accessible with ARIA attributes
 */
export const AvailabilityNotification: React.FC<AvailabilityNotificationProps> = React.memo(({
  notification,
  onDismiss,
  onViewVehicle,
}) => {
  const { id, vehicleId, title, message, vehicleThumbnail, vehicleName, actionLabel = 'View Vehicle' } = notification;

  React.useEffect(() => {
    // Auto-dismiss after 30 seconds
    const timer = setTimeout(() => {
      onDismiss();
    }, 30000);

    return () => clearTimeout(timer);
  }, [onDismiss]);

  // Handle keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onDismiss();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onDismiss]);

  const handleViewVehicle = () => {
    if (vehicleId) {
      onViewVehicle(vehicleId);
      onDismiss();
    }
  };

  const notificationStyles: React.CSSProperties = {
    width: '380px',
    maxWidth: 'calc(100vw - 48px)',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(24px)',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    padding: '16px',
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-start',
    position: 'relative',
  };

  return (
    <motion.div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      aria-labelledby={`notification-title-${id}`}
      aria-describedby={`notification-message-${id}`}
      className="availability-notification"
      style={notificationStyles}
      variants={notificationVariants}
      initial="enter"
      animate="center"
      exit="exit"
      layout
    >
      {/* Vehicle Thumbnail */}
      {vehicleThumbnail && (
        <div
          style={{
            width: '60px',
            height: '60px',
            borderRadius: '8px',
            overflow: 'hidden',
            flexShrink: 0,
            background: 'rgba(0, 0, 0, 0.05)',
          }}
        >
          <img
            src={vehicleThumbnail}
            alt={vehicleName || 'Vehicle'}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Notification Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <h4
          id={`notification-title-${id}`}
          style={{
            margin: 0,
            fontSize: '14px',
            fontWeight: 600,
            color: '#1F2937',
            marginBottom: '4px',
          }}
        >
          {title}
        </h4>
        <p
          id={`notification-message-${id}`}
          style={{
            margin: 0,
            fontSize: '13px',
            color: '#6B7280',
            lineHeight: 1.4,
            marginBottom: '12px',
          }}
        >
          {message}
        </p>

        {/* Action Button */}
        {vehicleId && (
          <button
            onClick={handleViewVehicle}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: '#3B82F6',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLButtonElement).style.background = '#2563EB';
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.background = '#3B82F6';
            }}
            aria-label={`${actionLabel} - ${vehicleName || 'vehicle'}`}
          >
            {actionLabel}
            <ExternalLink size={14} />
          </button>
        )}
      </div>

      {/* Dismiss Button */}
      <button
        onClick={onDismiss}
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          width: '24px',
          height: '24px',
          padding: 0,
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '4px',
          color: '#9CA3AF',
          transition: 'background 0.2s, color 0.2s',
        }}
        onMouseEnter={(e) => {
          (e.target as HTMLButtonElement).style.background = 'rgba(0, 0, 0, 0.05)';
          (e.target as HTMLButtonElement).style.color = '#1F2937';
        }}
        onMouseLeave={(e) => {
          (e.target as HTMLButtonElement).style.background = 'transparent';
          (e.target as HTMLButtonElement).style.color = '#9CA3AF';
        }}
        aria-label="Dismiss notification"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
});

AvailabilityNotification.displayName = 'AvailabilityNotification';

export default AvailabilityNotification;
