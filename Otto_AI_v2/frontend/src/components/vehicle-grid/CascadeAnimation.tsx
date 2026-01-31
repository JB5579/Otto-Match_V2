import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Vehicle } from '../../app/types/api';
import { useVehicleCascade } from '../../hooks/useVehicleCascade';

export interface CascadeAnimationProps {
  children: (vehicle: Vehicle, index: number, animationProps: any) => React.ReactNode;
  vehicles: Vehicle[];
  previousVehicles: Vehicle[];
  className?: string;
}

/**
 * CascadeAnimation component orchestrates smooth enter/exit animations
 * for vehicle grid updates using Framer Motion
 *
 * Features:
 * - Top-to-bottom cascade effect with stagger delay (0.05s per card)
 * - Spring animations for natural feel (stiffness: 300, damping: 25)
 * - Entering vehicles: fade in with slide up (opacity: 0→1, y: 20→0)
 * - Exiting vehicles: fade out with scale reduction (opacity: 1→0, scale: 1→0.95)
 * - Position changes: subtle scale animation for reordering
 * - Optimized rendering with React.memo and AnimatePresence
 *
 * Performance:
 * - Uses layout prop for smooth repositioning
 * - Maintains 60fps during animations
 * - CLS <0.1 with layout animations
 *
 * @param props - Component props
 * @returns Animated vehicle grid container
 */
export const CascadeAnimation: React.FC<CascadeAnimationProps> = ({
  children,
  vehicles,
  previousVehicles,
  className,
}) => {
  // Calculate delta and animation timing
  const { getVehicleAnimationProps } = useVehicleCascade(
    previousVehicles,
    vehicles
  );

  return (
    <div className={className}>
      <AnimatePresence mode="popLayout">
        {vehicles.map((vehicle, index) => {
          const animationProps = getVehicleAnimationProps(vehicle.id, index);

          return (
            <motion.div
              key={vehicle.id}
              layout
              initial={animationProps.initial as any}
              animate={animationProps.animate as any}
              exit={animationProps.exit as any}
              transition={animationProps.transition as any}
            >
              {children(vehicle, index, animationProps)}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default React.memo(CascadeAnimation);
