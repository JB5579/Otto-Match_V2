import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { VehicleStatus } from './AvailabilityBadge';

export interface VehicleStatusOverlayProps {
  status: VehicleStatus;
  isVisible?: boolean;
  className?: string;
}

/**
 * VehicleStatusOverlay Component
 *
 * Displays a semi-transparent overlay on unavailable vehicle cards (sold/reserved).
 *
 * @component
 * @example
 * ```tsx
 * <VehicleStatusOverlay status="sold" isVisible={true} />
 * ```
 *
 * @param {VehicleStatusOverlayProps} props - Component props
 * @param {VehicleStatus} props.status - Current availability status
 * @param {boolean} props.isVisible - Whether to show the overlay
 * @param {string} props.className - Additional CSS classes
 *
 * Features:
 * - Semi-transparent overlay (50-60% opacity) for unavailable vehicles
 * - "Sold" or "Reserved" stamp text overlay
 * - Prevents click interactions (pointer-events: none)
 * - Smooth fade in/out transition (Framer Motion)
 * - Glass-morphism blur effect
 * - Responsive stamp sizing
 */
export const VehicleStatusOverlay: React.FC<VehicleStatusOverlayProps> = React.memo(({
  status,
  isVisible = true,
  className = '',
}) => {
  const isUnavailable = status === 'sold' || status === 'reserved';
  const shouldShow = isUnavailable && isVisible;

  const stampText = status === 'sold' ? 'SOLD' : 'RESERVED';
  const stampColor = status === 'sold' ? '#6B7280' : '#D97706';

  const overlayVariants = {
    hidden: {
      opacity: 0,
      scale: 1,
    },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.3,
        ease: 'easeIn',
      },
    },
    exit: {
      opacity: 0,
      scale: 1,
      transition: {
        duration: 0.3,
        ease: 'easeOut',
      },
    },
  };

  const stampVariants = {
    hidden: {
      opacity: 0,
      scale: 0.8,
      rotate: -12,
    },
    visible: {
      opacity: 1,
      scale: 1,
      rotate: -12,
      transition: {
        delay: 0.1,
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1],
      },
    },
  };

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          className={`vehicle-status-overlay ${className}`}
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.4)',
            backdropFilter: 'blur(2px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 5,
            pointerEvents: 'none',
            borderRadius: 'inherit',
          }}
          aria-hidden="true"
        >
          <motion.div
            className="status-stamp"
            variants={stampVariants}
            initial="hidden"
            animate="visible"
            style={{
              fontSize: 'clamp(32px, 5vw, 48px)',
              fontWeight: 900,
              letterSpacing: '0.15em',
              color: stampColor,
              textShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              opacity: 0.7,
              transform: 'rotate(-12deg)',
              userSelect: 'none',
              border: `3px solid ${stampColor}`,
              padding: '12px 32px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.6)',
            }}
          >
            {stampText}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});

VehicleStatusOverlay.displayName = 'VehicleStatusOverlay';

export default VehicleStatusOverlay;
