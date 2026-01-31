import React from 'react';
import { motion } from 'framer-motion';
import { Check, Clock, X, Sparkles } from 'lucide-react';

export type VehicleStatus = 'available' | 'reserved' | 'sold' | 'newlyAvailable';

export interface AvailabilityBadgeProps {
  status: VehicleStatus;
  size?: 'compact' | 'default';
  showLabel?: boolean;
  className?: string;
}

const statusConfig = {
  available: {
    bg: 'rgba(34, 197, 94, 0.15)',
    text: '#16A34A',
    border: 'rgba(34, 197, 94, 0.3)',
    icon: Check,
    label: 'Available',
    ariaLabel: 'Vehicle status: Available',
  },
  reserved: {
    bg: 'rgba(245, 158, 11, 0.15)',
    text: '#D97706',
    border: 'rgba(245, 158, 11, 0.3)',
    icon: Clock,
    label: 'Reserved',
    ariaLabel: 'Vehicle status: Reserved',
  },
  sold: {
    bg: 'rgba(107, 114, 128, 0.15)',
    text: '#6B7280',
    border: 'rgba(107, 114, 128, 0.3)',
    icon: X,
    label: 'Sold',
    ariaLabel: 'Vehicle status: Sold',
  },
  newlyAvailable: {
    bg: 'rgba(34, 197, 94, 0.2)',
    text: '#16A34A',
    border: 'rgba(34, 197, 94, 0.4)',
    icon: Sparkles,
    label: 'Newly Available',
    ariaLabel: 'Vehicle status: Newly Available',
  },
} as const;

const statusChangeVariants = {
  initial: {
    scale: 0.8,
    opacity: 0,
  },
  animate: {
    scale: [0.8, 1.05, 1],
    opacity: [0, 1, 1],
    transition: { duration: 0.4, ease: 'easeOut' },
  },
};

const newlyAvailablePulse = {
  scale: [1, 1.05, 1],
  opacity: [1, 0.8, 1],
  boxShadow: [
    '0 0 0 0 rgba(34, 197, 94, 0.4)',
    '0 0 0 10px rgba(34, 197, 94, 0)',
  ],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

/**
 * AvailabilityBadge Component
 *
 * Displays vehicle availability status with color-coded badges, icons, and animations.
 *
 * @component
 * @example
 * ```tsx
 * <AvailabilityBadge status="available" size="default" showLabel={true} />
 * ```
 *
 * @param {AvailabilityBadgeProps} props - Component props
 * @param {VehicleStatus} props.status - Current availability status
 * @param {'compact' | 'default'} props.size - Badge size (compact for mobile, default for tablet/desktop)
 * @param {boolean} props.showLabel - Whether to show text label alongside icon
 * @param {string} props.className - Additional CSS classes
 *
 * Features:
 * - Color-coded status indicators (green/amber/gray)
 * - Status-specific icons (Check/Clock/X/Sparkles)
 * - Smooth status change animations (Framer Motion)
 * - Pulsing animation for newly available vehicles
 * - Responsive sizing (compact/default)
 * - Accessible with ARIA attributes
 * - Glass-morphism styling consistent with design system
 */
export const AvailabilityBadge: React.FC<AvailabilityBadgeProps> = React.memo(({
  status,
  size = 'default',
  showLabel = true,
  className = '',
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const badgeStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: size === 'compact' ? '4px' : '6px',
    padding: size === 'compact' ? '4px 8px' : '6px 12px',
    borderRadius: '8px',
    background: config.bg,
    border: `1px solid ${config.border}`,
    color: config.text,
    fontSize: size === 'compact' ? '12px' : '13px',
    fontWeight: 600,
    lineHeight: 1.2,
    whiteSpace: 'nowrap',
  };

  const iconSize = size === 'compact' ? 14 : 16;

  return (
    <motion.div
      role="status"
      aria-live="polite"
      aria-label={config.ariaLabel}
      className={className}
      style={badgeStyles}
      variants={statusChangeVariants}
      initial="initial"
      animate={status === 'newlyAvailable' ? newlyAvailablePulse : 'animate'}
      key={status}
    >
      <Icon size={iconSize} aria-hidden="true" strokeWidth={2.5} />
      {showLabel && (
        <span>{config.label}</span>
      )}
      {!showLabel && (
        <span className="sr-only">{config.label}</span>
      )}
    </motion.div>
  );
});

AvailabilityBadge.displayName = 'AvailabilityBadge';

export default AvailabilityBadge;
