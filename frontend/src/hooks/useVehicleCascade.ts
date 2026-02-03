import { useMemo } from 'react';
import type { Vehicle } from '../app/types/api';

/**
 * Vehicle delta types for animation orchestration
 */
export interface VehicleDelta {
  entering: Vehicle[]; // New vehicles not in old list
  exiting: Vehicle[]; // Old vehicles not in new list
  persisting: Vehicle[]; // Vehicles in both lists
  positionChanged: Set<string>; // IDs of vehicles that changed position
}

/**
 * Animation timing configuration
 */
export interface CascadeAnimationConfig {
  staggerDelay: number; // Delay between each card (ms)
  enterDuration: number; // Enter animation duration (ms)
  exitDuration: number; // Exit animation duration (ms)
  springConfig: {
    stiffness: number;
    damping: number;
  };
}

/**
 * Default animation configuration
 * From context constraints: stagger 0.05s, spring stiffness 300, damping 25
 * Story 3-8.9: Frozen to prevent unnecessary re-renders
 */
const DEFAULT_CONFIG: CascadeAnimationConfig = Object.freeze({
  staggerDelay: 50, // 0.05s in ms
  enterDuration: 300,
  exitDuration: 200,
  springConfig: Object.freeze({
    stiffness: 300,
    damping: 25,
  }),
});

/**
 * Memoized animation variants cache
 * Story 3-8.9: Pre-computed variants for common animation states
 * Reduces object creation during re-renders
 */
const ANIMATION_VARIANTS = Object.freeze({
  entering: Object.freeze({
    initial: Object.freeze({
      opacity: 0,
      y: 20,
      scale: 0.95,
    }),
    animate: Object.freeze({
      opacity: 1,
      y: 0,
      scale: 1,
    }),
  }),
  persisting: Object.freeze({
    initial: Object.freeze({}),
    animate: Object.freeze({
      opacity: 1,
      y: 0,
      scale: 1,
    }),
  }),
  positionChanged: Object.freeze({
    initial: Object.freeze({
      scale: 0.98,
    }),
    animate: Object.freeze({
      opacity: 1,
      y: 0,
      scale: 1,
    }),
  }),
  exit: Object.freeze({
    opacity: 0,
    scale: 0.95,
  }),
});

/**
 * Return type for useVehicleCascade hook
 */
export interface UseVehicleCascadeReturn {
  delta: VehicleDelta;
  animationDelays: Map<string, number>;
  config: CascadeAnimationConfig;
  getVehicleAnimationProps: (
    vehicleId: string,
    index: number
  ) => {
    initial: object;
    animate: object;
    exit: object;
    transition: object;
  };
}

/**
 * Calculate delta between old and new vehicle arrays
 * Identifies entering, exiting, and persisting vehicles
 */
function calculateVehicleDelta(
  oldVehicles: Vehicle[],
  newVehicles: Vehicle[]
): VehicleDelta {
  const oldIds = new Set(oldVehicles.map((v) => v.id));
  const newIds = new Set(newVehicles.map((v) => v.id));

  // Create maps for efficient lookup
  const oldPositions = new Map(oldVehicles.map((v, i) => [v.id, i]));
  const newPositions = new Map(newVehicles.map((v, i) => [v.id, i]));

  // Entering vehicles: in new but not in old
  const entering = newVehicles.filter((v) => !oldIds.has(v.id));

  // Exiting vehicles: in old but not in new
  const exiting = oldVehicles.filter((v) => !newIds.has(v.id));

  // Persisting vehicles: in both lists
  const persisting = newVehicles.filter((v) => oldIds.has(v.id));

  // Position changes: vehicles that moved
  const positionChanged = new Set<string>();
  persisting.forEach((v) => {
    const oldPos = oldPositions.get(v.id);
    const newPos = newPositions.get(v.id);
    if (oldPos !== newPos && oldPos !== undefined && newPos !== undefined) {
      positionChanged.add(v.id);
    }
  });

  return {
    entering,
    exiting,
    persisting,
    positionChanged,
  };
}

/**
 * Generate stagger delays for cascade animation
 * Top-to-bottom effect: delay increases with position index
 */
function generateAnimationDelays(
  vehicles: Vehicle[],
  staggerDelay: number
): Map<string, number> {
  const delays = new Map<string, number>();

  vehicles.forEach((vehicle, index) => {
    // Stagger delay based on position
    // Max delay cap at 0.5s (10 cards * 0.05s)
    const delay = Math.min(index * staggerDelay, 500);
    delays.set(vehicle.id, delay);
  });

  return delays;
}

/**
 * Custom hook for vehicle cascade animations
 *
 * Calculates the delta between old and new vehicle arrays and generates
 * animation timing for smooth cascade effects.
 *
 * Features:
 * - Delta calculation (entering/exiting/persisting vehicles)
 * - Position change detection
 * - Stagger delay calculation (0.05s per card)
 * - Framer Motion animation variants generation
 * - Performance optimized with useMemo
 *
 * @param oldVehicles - Previous vehicle list
 * @param newVehicles - New vehicle list
 * @param config - Optional animation configuration
 * @returns Delta, delays, and animation props generator
 */
export const useVehicleCascade = (
  oldVehicles: Vehicle[],
  newVehicles: Vehicle[],
  config: Partial<CascadeAnimationConfig> = {}
): UseVehicleCascadeReturn => {
  const animationConfig = { ...DEFAULT_CONFIG, ...config };

  /**
   * Calculate vehicle delta
   * Only recalculates when vehicle arrays change
   */
  const delta = useMemo(() => {
    return calculateVehicleDelta(oldVehicles, newVehicles);
  }, [oldVehicles, newVehicles]);

  /**
   * Generate animation delays for new vehicles
   * Stagger top-to-bottom cascade effect
   */
  const animationDelays = useMemo(() => {
    return generateAnimationDelays(newVehicles, animationConfig.staggerDelay);
  }, [newVehicles, animationConfig.staggerDelay]);

  /**
   * Generate Framer Motion animation props for a vehicle
   * Story 3-8.9: Uses pre-computed variants for better performance
   * Varies based on whether vehicle is entering, exiting, or persisting
   */
  const getVehicleAnimationProps = useMemo(() => {
    return (vehicleId: string, _index: number) => {
      const delay = animationDelays.get(vehicleId) || 0;
      const isEntering = delta.entering.some((v) => v.id === vehicleId);
      const hasPositionChanged = delta.positionChanged.has(vehicleId);

      // Story 3-8.9: Use pre-computed variants based on vehicle state
      let initial;
      if (isEntering) {
        initial = ANIMATION_VARIANTS.entering.initial;
      } else if (hasPositionChanged) {
        initial = ANIMATION_VARIANTS.positionChanged.initial;
      } else {
        initial = ANIMATION_VARIANTS.persisting.initial;
      }

      const animate = ANIMATION_VARIANTS.entering.animate;

      // Exit animation: fade out with scale reduction
      const exit = {
        ...ANIMATION_VARIANTS.exit,
        transition: {
          duration: animationConfig.exitDuration / 1000, // Convert to seconds
          ease: 'easeOut' as const,
        },
      };

      // Transition configuration
      const transition = {
        delay: delay / 1000, // Convert to seconds
        type: 'spring' as const,
        stiffness: animationConfig.springConfig.stiffness,
        damping: animationConfig.springConfig.damping,
      };

      return {
        initial,
        animate,
        exit,
        transition,
      };
    };
  }, [animationDelays, delta, animationConfig]);

  return {
    delta,
    animationDelays,
    config: animationConfig,
    getVehicleAnimationProps,
  };
};
