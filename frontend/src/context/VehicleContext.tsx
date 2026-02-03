import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { useVehicleUpdates } from '../hooks/useVehicleUpdates';
import type { Vehicle } from '../app/types/api';
import type { FilterResult } from '../types/filters';
import { applyFiltersAndSort, type FilterState, type SortOption } from '../types/filters';

export type VehicleStatus = 'available' | 'reserved' | 'sold';

export interface StatusChange {
  from_status: VehicleStatus;
  to_status: VehicleStatus;
  changed_at: string;
  duration_seconds?: number;
}

interface VehicleContextValue {
  vehicles: Vehicle[];
  previousVehicles: Vehicle[];
  loading: boolean;
  error: string | null;
  updateVehicles: (newVehicles: Vehicle[]) => void;
  retryUpdate: () => void;
  clearError: () => void;
  // State preservation
  expandedCardIds: Set<string>;
  toggleExpandedCard: (vehicleId: string) => void;
  favoriteIds: Set<string>;
  toggleFavorite: (vehicleId: string) => void;
  // Modal state (Task 3-4.9, 3-4.10)
  selectedVehicle: Vehicle | null;
  isModalOpen: boolean;
  openModal: (vehicle: Vehicle) => void;
  closeModal: () => void;
  // Modal actions (Task 3-4.7)
  holdVehicle: (vehicleId: string) => void;
  compareVehicle: (vehicleId: string) => void;
  // Availability status management (Task 3-5.6)
  updateVehicleStatus: (vehicleId: string, newStatus: VehicleStatus) => void;
  getStatusHistory: (vehicleId: string) => Promise<StatusChange[]>;
  favoritesWithAvailability: Vehicle[];
  monitorFavoritesAvailability: boolean;
  setMonitorFavoritesAvailability: (enabled: boolean) => void;
  // Story 3-7: Filter integration
  getFilteredVehicles: (filters?: FilterState, sortBy?: SortOption) => FilterResult;
}

const VehicleContext = createContext<VehicleContextValue | null>(null);

export interface VehicleProviderProps {
  children: React.ReactNode;
  initialVehicles?: Vehicle[];
}

/**
 * VehicleProvider manages global vehicle state with cascade update logic
 *
 * Features:
 * - Vehicle list management with delta calculation
 * - SSE integration for real-time vehicle updates (Story 3-3b)
 * - State preservation (favorites, expanded cards) across updates
 * - Loading and error states
 * - Retry logic for failed updates
 * - Filter integration for Story 3-7
 *
 * Context Hierarchy:
 * AuthProvider → VehicleContext → VehicleGrid
 *
 * **Story 3-3b SSE Migration:**
 * - Vehicle updates now use SSE (not WebSocket)
 * - SSE endpoint: GET /api/vehicles/updates
 * - useVehicleUpdates hook replaces ConversationContext dependency
 * - Otto chat WebSocket is isolated to ConversationContext (chat only)
 *
 * **Story 3-7 Filter Integration:**
 * - getFilteredVehicles() returns vehicles filtered and sorted by FilterContext
 * - Filters applied before displaying in VehicleGrid
 * - Empty state handled when no vehicles match filters
 */
export const VehicleProvider: React.FC<VehicleProviderProps> = ({
  children,
  initialVehicles = [],
}) => {
  const [vehicles, setVehicles] = useState<Vehicle[]>(initialVehicles);
  const [previousVehicles, setPreviousVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State preservation across updates
  const [expandedCardIds, setExpandedCardIds] = useState<Set<string>>(new Set());
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());

  // Modal state (Task 3-4.9, 3-4.10)
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Availability monitoring (Task 3-5.6)
  const [monitorFavoritesAvailability, setMonitorFavoritesAvailability] = useState(true);

  // Track last failed update for retry (Story 3-3b: now stores SSE event data)
  const lastFailedUpdateRef = useRef<Vehicle[] | null>(null);

  /**
   * Story 3-3b: SSE connection for vehicle updates
   * Replaces WebSocket vehicle updates from ConversationContext
   */
  const { connected: sseConnected, lastUpdate, error: sseError } = useVehicleUpdates({
    onVehicleUpdate: useCallback((updatedVehicles: Vehicle[], eventId: string) => {
      console.log('[VehicleContext] SSE vehicle update received', {
        count: updatedVehicles.length,
        eventId,
      });
      updateVehicles(updatedVehicles);
    }, []),
    onConnected: () => {
      console.log('[VehicleContext] SSE connection established');
      setError(null);
    },
    onDisconnected: () => {
      console.log('[VehicleContext] SSE connection closed');
    },
    onError: (error) => {
      console.error('[VehicleContext] SSE connection error:', error);
      setError('Real-time updates disconnected. Retrying...');
    },
  });

  /**
   * Update vehicles with delta calculation
   * Preserves expanded states and favorites
   */
  const updateVehicles = useCallback((newVehicles: Vehicle[]) => {
    console.log('[VehicleContext] Updating vehicles', {
      oldCount: vehicles.length,
      newCount: newVehicles.length,
    });

    // Store previous vehicles for delta calculation
    setPreviousVehicles(vehicles);

    // Preserve favorite states
    // If a vehicle remains in the new list, keep its favorite status
    const updatedVehicles = newVehicles.map((vehicle) => {
      const wasFavorited = favoriteIds.has(vehicle.id);
      return wasFavorited ? { ...vehicle, isFavorited: true } as Vehicle : vehicle;
    });

    setVehicles(updatedVehicles);
    setLoading(false);
    setError(null);

    console.log('[VehicleContext] Vehicles updated successfully');
  }, [vehicles, favoriteIds]);

  /**
   * Retry last failed update
   * Story 3-3b: Updated to retry SSE vehicle updates
   */
  const retryUpdate = useCallback(() => {
    if (!lastFailedUpdateRef.current) {
      console.warn('[VehicleContext] No failed update to retry');
      return;
    }

    console.log('[VehicleContext] Retrying failed update');
    setError(null);
    setLoading(true);

    try {
      updateVehicles(lastFailedUpdateRef.current);
      lastFailedUpdateRef.current = null;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update vehicles';
      setError(errorMsg);
      setLoading(false);
    }
  }, [updateVehicles]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Toggle expanded state for mobile progressive disclosure
   * Preserved across grid updates (AC7)
   */
  const toggleExpandedCard = useCallback((vehicleId: string) => {
    setExpandedCardIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(vehicleId)) {
        newSet.delete(vehicleId);
      } else {
        newSet.add(vehicleId);
      }
      return newSet;
    });
  }, []);

  /**
   * Toggle favorite status
   * Preserved across grid updates (AC7)
   */
  const toggleFavorite = useCallback((vehicleId: string) => {
    setFavoriteIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(vehicleId)) {
        newSet.delete(vehicleId);
      } else {
        newSet.add(vehicleId);
      }
      return newSet;
    });

    // Update vehicle in current list (update the isFavorited flag)
    setVehicles((prev) =>
      prev.map((v) =>
        v.id === vehicleId ? { ...v, isFavorited: !v.isFavorited } as Vehicle : v
      )
    );
  }, []);

  /**
   * Open modal with selected vehicle (Task 3-4.9, 3-4.10)
   * Preserves modal state during grid updates
   */
  const openModal = useCallback((vehicle: Vehicle) => {
    setSelectedVehicle(vehicle);
    setIsModalOpen(true);
  }, []);

  /**
   * Close modal (Task 3-4.9, 3-4.10)
   */
  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    // Clear selected vehicle after animation completes
    setTimeout(() => setSelectedVehicle(null), 300);
  }, []);

  /**
   * Hold vehicle for 24 hours (Task 3-4.7)
   */
  const holdVehicle = useCallback((vehicleId: string) => {
    console.log('[VehicleContext] Hold vehicle:', vehicleId);
    // TODO: Implement hold API call
    // This will integrate with the backend reservation system
  }, []);

  /**
   * Add vehicle to comparison list (Task 3-4.7)
   */
  const compareVehicle = useCallback((vehicleId: string) => {
    console.log('[VehicleContext] Compare vehicle:', vehicleId);
    // TODO: Implement comparison logic
    // This will add the vehicle to a comparison state
  }, []);

  /**
   * Update vehicle availability status (Task 3-5.6)
   * Called when WebSocket availability_status_update message arrives
   */
  const updateVehicleStatus = useCallback((vehicleId: string, newStatus: VehicleStatus) => {
    console.log('[VehicleContext] Updating vehicle status:', vehicleId, newStatus);

    setVehicles((prev) =>
      prev.map((v) =>
        v.id === vehicleId ? { ...v, availabilityStatus: newStatus } as Vehicle : v
      )
    );
  }, []);

  /**
   * Get status change history for a vehicle (Task 3-5.6)
   * Fetches from backend API
   */
  const getStatusHistory = useCallback(async (vehicleId: string): Promise<StatusChange[]> => {
    console.log('[VehicleContext] Fetching status history for:', vehicleId);

    try {
      // Import availability API dynamically to avoid circular dependencies
      const { fetchStatusHistory } = await import('../lib/availabilityApi');
      return await fetchStatusHistory(vehicleId);
    } catch (error) {
      console.error('[VehicleContext] Failed to fetch status history:', error);
      return [];
    }
  }, []);

  /**
   * Get favorites with availability monitoring enabled (Task 3-5.6)
   */
  const favoritesWithAvailability = vehicles.filter((v) => favoriteIds.has(v.id));

  /**
   * Story 3-7: Get filtered and sorted vehicles
   * Accepts filter state and sort option, returns filtered results
   * AC3: Grid updates to show only matching vehicles
   * AC4: Sorting applied within current filter constraints
   *
   * Note: This method accepts filter parameters rather than using FilterContext directly
   * to avoid circular dependencies. Components should get filters from FilterContext
   * and pass them to this method.
   *
   * @example
   * const { filters, sortBy } = useFilters();
   * const { getFilteredVehicles } = useVehicleContext();
   * const result = getFilteredVehicles(filters, sortBy);
   */
  const getFilteredVehicles = useCallback((filters?: FilterState, sortBy?: SortOption): FilterResult => {
    return applyFiltersAndSort(
      vehicles,
      filters || {},
      sortBy || 'relevance'
    );
  }, [vehicles]);

  const value: VehicleContextValue = {
    vehicles,
    previousVehicles,
    loading,
    error,
    updateVehicles,
    retryUpdate,
    clearError,
    expandedCardIds,
    toggleExpandedCard,
    favoriteIds,
    toggleFavorite,
    selectedVehicle,
    isModalOpen,
    openModal,
    closeModal,
    holdVehicle,
    compareVehicle,
    updateVehicleStatus,
    getStatusHistory,
    favoritesWithAvailability,
    monitorFavoritesAvailability,
    setMonitorFavoritesAvailability,
    getFilteredVehicles,
  };

  return <VehicleContext.Provider value={value}>{children}</VehicleContext.Provider>;
};

/**
 * Hook to access vehicle context
 * Must be used within VehicleProvider
 */
export const useVehicleContext = (): VehicleContextValue => {
  const context = useContext(VehicleContext);

  if (!context) {
    throw new Error('useVehicleContext must be used within a VehicleProvider');
  }

  return context;
};
