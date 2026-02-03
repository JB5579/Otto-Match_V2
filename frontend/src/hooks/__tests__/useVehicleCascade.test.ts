import { renderHook } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useVehicleCascade } from '../useVehicleCascade';
import type { Vehicle } from '../../app/types/api';

// Mock vehicle data
const createMockVehicle = (id: string, matchScore: number = 85): Vehicle => ({
  id,
  make: 'Toyota',
  model: 'Camry',
  year: 2022,
  price: 25000,
  mileage: 15000,
  matchScore,
  images: [],
});

describe('useVehicleCascade', () => {
  it('should identify entering vehicles', () => {
    const oldVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
    ];

    const newVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'), // New vehicle
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    expect(result.current.delta.entering).toHaveLength(1);
    expect(result.current.delta.entering[0].id).toBe('v3');
  });

  it('should identify exiting vehicles', () => {
    const oldVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'),
    ];

    const newVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      // v3 removed
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    expect(result.current.delta.exiting).toHaveLength(1);
    expect(result.current.delta.exiting[0].id).toBe('v3');
  });

  it('should identify persisting vehicles', () => {
    const oldVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
    ];

    const newVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'),
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    expect(result.current.delta.persisting).toHaveLength(2);
    expect(result.current.delta.persisting.map(v => v.id)).toEqual(['v1', 'v2']);
  });

  it('should detect position changes', () => {
    const oldVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'),
    ];

    const newVehicles: Vehicle[] = [
      createMockVehicle('v3'), // Moved from position 2 to 0
      createMockVehicle('v1'), // Moved from position 0 to 1
      createMockVehicle('v2'), // Moved from position 1 to 2
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    expect(result.current.delta.positionChanged.size).toBeGreaterThan(0);
    expect(result.current.delta.positionChanged.has('v3')).toBe(true);
  });

  it('should generate stagger delays based on position', () => {
    const oldVehicles: Vehicle[] = [];
    const newVehicles: Vehicle[] = [
      createMockVehicle('v1'),
      createMockVehicle('v2'),
      createMockVehicle('v3'),
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    const delays = result.current.animationDelays;
    const delay1 = delays.get('v1');
    const delay2 = delays.get('v2');
    const delay3 = delays.get('v3');

    expect(delay1).toBe(0); // First card, no delay
    expect(delay2).toBe(50); // Second card, 50ms delay (0.05s)
    expect(delay3).toBe(100); // Third card, 100ms delay
  });

  it('should cap maximum stagger delay at 500ms', () => {
    const oldVehicles: Vehicle[] = [];
    // Create 20 vehicles
    const newVehicles: Vehicle[] = Array.from({ length: 20 }, (_, i) =>
      createMockVehicle(`v${i}`)
    );

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    const lastDelay = result.current.animationDelays.get('v19');
    expect(lastDelay).toBeLessThanOrEqual(500); // Capped at 500ms
  });

  it('should generate animation props for entering vehicles', () => {
    const oldVehicles: Vehicle[] = [];
    const newVehicles: Vehicle[] = [
      createMockVehicle('v1'),
    ];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    const animationProps = result.current.getVehicleAnimationProps('v1', 0);

    expect(animationProps.initial).toEqual({
      opacity: 0,
      y: 20,
      scale: 0.95,
    });

    expect(animationProps.animate).toEqual({
      opacity: 1,
      y: 0,
      scale: 1,
    });

    expect(animationProps.exit).toHaveProperty('opacity', 0);
    expect(animationProps.exit).toHaveProperty('scale', 0.95);
  });

  it('should use spring configuration from constraints', () => {
    const oldVehicles: Vehicle[] = [];
    const newVehicles: Vehicle[] = [createMockVehicle('v1')];

    const { result } = renderHook(() => useVehicleCascade(oldVehicles, newVehicles));

    const animationProps = result.current.getVehicleAnimationProps('v1', 0);

    expect(animationProps.transition).toHaveProperty('type', 'spring');
    expect(animationProps.transition).toHaveProperty('stiffness', 300);
    expect(animationProps.transition).toHaveProperty('damping', 25);
  });

  it('should handle empty arrays gracefully', () => {
    const { result } = renderHook(() => useVehicleCascade([], []));

    expect(result.current.delta.entering).toHaveLength(0);
    expect(result.current.delta.exiting).toHaveLength(0);
    expect(result.current.delta.persisting).toHaveLength(0);
    expect(result.current.delta.positionChanged.size).toBe(0);
  });

  it('should recalculate delta when vehicles change', () => {
    const initialOld: Vehicle[] = [createMockVehicle('v1')];
    const initialNew: Vehicle[] = [createMockVehicle('v1'), createMockVehicle('v2')];

    const { result, rerender } = renderHook(
      ({ old, newVehicles }) => useVehicleCascade(old, newVehicles),
      { initialProps: { old: initialOld, newVehicles: initialNew } }
    );

    expect(result.current.delta.entering).toHaveLength(1);

    // Update vehicles
    const updatedOld = initialNew;
    const updatedNew = [createMockVehicle('v1')]; // v2 removed

    rerender({ old: updatedOld, newVehicles: updatedNew });

    expect(result.current.delta.entering).toHaveLength(0);
    expect(result.current.delta.exiting).toHaveLength(1);
    expect(result.current.delta.exiting[0].id).toBe('v2');
  });

  it('should handle custom animation config', () => {
    const customConfig = {
      staggerDelay: 100, // 100ms instead of 50ms
      springConfig: {
        stiffness: 400,
        damping: 30,
      },
    };

    const oldVehicles: Vehicle[] = [];
    const newVehicles: Vehicle[] = [createMockVehicle('v1'), createMockVehicle('v2')];

    const { result } = renderHook(() =>
      useVehicleCascade(oldVehicles, newVehicles, customConfig)
    );

    const delay2 = result.current.animationDelays.get('v2');
    expect(delay2).toBe(100); // Custom stagger delay

    const animationProps = result.current.getVehicleAnimationProps('v1', 0);
    expect(animationProps.transition).toHaveProperty('stiffness', 400);
    expect(animationProps.transition).toHaveProperty('damping', 30);
  });
});
