import React, { useMemo } from 'react';
import { AvailabilityBadge, VehicleStatus } from './AvailabilityBadge';

export interface StatusIndicatorProps {
  status: VehicleStatus;
  position?: 'top-left' | 'top-right';
  isNewlyAvailable?: boolean;
  className?: string;
}

/**
 * StatusIndicator Component
 *
 * Displays availability status badge on vehicle cards with responsive positioning.
 *
 * @component
 * @example
 * ```tsx
 * <StatusIndicator status="available" position="top-right" />
 * ```
 *
 * @param {StatusIndicatorProps} props - Component props
 * @param {VehicleStatus} props.status - Current availability status
 * @param {'top-left' | 'top-right'} props.position - Badge position on card
 * @param {boolean} props.isNewlyAvailable - Whether to show "Newly Available" highlight
 * @param {string} props.className - Additional CSS classes
 *
 * Features:
 * - Positioned absolutely on vehicle card (top-left or top-right)
 * - Responsive badge sizing based on viewport:
 *   - Mobile: Compact badges with icon only
 *   - Tablet: Badges with icon + abbreviated text
 *   - Desktop: Full badges with icon + complete text
 * - "Newly Available" pulsing animation
 * - Glass-morphism styling
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = React.memo(({
  status,
  position = 'top-right',
  isNewlyAvailable = false,
  className = '',
}) => {
  const effectiveStatus = isNewlyAvailable && status === 'available'
    ? 'newlyAvailable'
    : status;

  const containerStyles: React.CSSProperties = useMemo(() => ({
    position: 'absolute',
    top: '12px',
    [position === 'top-right' ? 'right' : 'left']: '12px',
    zIndex: 10,
  }), [position]);

  return (
    <div
      className={`status-indicator status-indicator--${position} ${className}`}
      style={containerStyles}
    >
      {/* Mobile: Icon only */}
      <div className="status-indicator__mobile">
        <AvailabilityBadge
          status={effectiveStatus}
          size="compact"
          showLabel={false}
        />
      </div>

      {/* Tablet: Icon + abbreviated text */}
      <div className="status-indicator__tablet">
        <AvailabilityBadge
          status={effectiveStatus}
          size="compact"
          showLabel={true}
        />
      </div>

      {/* Desktop: Icon + full text */}
      <div className="status-indicator__desktop">
        <AvailabilityBadge
          status={effectiveStatus}
          size="default"
          showLabel={true}
        />
      </div>

      <style>{`
        /* Mobile (< 768px): Icon only */
        @media (max-width: 767px) {
          .status-indicator__mobile {
            display: block;
          }
          .status-indicator__tablet,
          .status-indicator__desktop {
            display: none;
          }
        }

        /* Tablet (768px - 1023px): Icon + abbreviated text */
        @media (min-width: 768px) and (max-width: 1023px) {
          .status-indicator__mobile {
            display: none;
          }
          .status-indicator__tablet {
            display: block;
          }
          .status-indicator__desktop {
            display: none;
          }
        }

        /* Desktop (>= 1024px): Icon + full text */
        @media (min-width: 1024px) {
          .status-indicator__mobile,
          .status-indicator__tablet {
            display: none;
          }
          .status-indicator__desktop {
            display: block;
          }
        }

        /* Ensure touch targets are 44x44px minimum on mobile */
        @media (max-width: 767px) {
          .status-indicator__mobile > div {
            min-width: 44px;
            min-height: 44px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
});

StatusIndicator.displayName = 'StatusIndicator';

export default StatusIndicator;
