import { useState, useEffect, useCallback } from 'react';
import type { Vehicle, SearchFilters } from '../../app/types/api';
import { VehicleAPIClient } from '../../app/services/apiClient';

interface UseVehicleGridOptions {
  initialFilters?: SearchFilters;
  pageSize?: number;
  autoFetch?: boolean;
}

interface UseVehicleGridResult {
  vehicles: Vehicle[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  hasMore: boolean;
  fetchVehicles: (filters?: SearchFilters) => Promise<void>;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
  favoriteVehicle: (vehicleId: string) => Promise<void>;
  compareVehicle: (vehicleId: string) => Promise<void>;
  submitFeedback: (vehicleId: string, type: 'more' | 'less') => Promise<void>;
}

const useVehicleGrid = (
  options: UseVehicleGridOptions = {}
): UseVehicleGridResult => {
  const {
    initialFilters = {},
    pageSize = 50,
    autoFetch = true,
  } = options;

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [currentFilters, setCurrentFilters] = useState<SearchFilters>(initialFilters);
  const [offset, setOffset] = useState<number>(0);

  const apiClient = new VehicleAPIClient();

  const fetchVehicles = useCallback(
    async (filters?: SearchFilters) => {
      setLoading(true);
      setError(null);

      try {
        const appliedFilters = filters || currentFilters;
        setCurrentFilters(appliedFilters);

        const response = await apiClient.getVehicles({
          ...appliedFilters,
          limit: pageSize,
          offset: 0,
        });

        setVehicles(response.vehicles);
        setTotalCount(response.total || response.vehicles.length);
        setOffset(0);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to fetch vehicles';
        setError(errorMessage);
        console.error('Error fetching vehicles:', err);
      } finally {
        setLoading(false);
      }
    },
    [apiClient, currentFilters, pageSize]
  );

  const loadMore = useCallback(async () => {
    if (loading || vehicles.length >= totalCount) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const newOffset = offset + pageSize;
      const response = await apiClient.getVehicles({
        ...currentFilters,
        limit: pageSize,
        offset: newOffset,
      });

      setVehicles((prev) => [...prev, ...response.vehicles]);
      setOffset(newOffset);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load more vehicles';
      setError(errorMessage);
      console.error('Error loading more vehicles:', err);
    } finally {
      setLoading(false);
    }
  }, [apiClient, currentFilters, offset, pageSize, loading, vehicles.length, totalCount]);

  const refresh = useCallback(async () => {
    await fetchVehicles(currentFilters);
  }, [fetchVehicles, currentFilters]);

  const favoriteVehicle = useCallback(
    async (vehicleId: string) => {
      try {
        await apiClient.addFavorite(vehicleId);
        // Optionally update local state to reflect favorited status
        setVehicles((prev) =>
          prev.map((v) =>
            v.id === vehicleId ? { ...v, isFavorited: true } : v
          )
        );
      } catch (err) {
        console.error('Error favoriting vehicle:', err);
        throw err;
      }
    },
    [apiClient]
  );

  const compareVehicle = useCallback(
    async (vehicleId: string) => {
      try {
        // Add to local comparison buffer (Story 3-2: no Otto integration yet)
        const comparisonVehicles = JSON.parse(
          localStorage.getItem('comparisonVehicles') || '[]'
        );

        if (!comparisonVehicles.includes(vehicleId)) {
          comparisonVehicles.push(vehicleId);
          localStorage.setItem(
            'comparisonVehicles',
            JSON.stringify(comparisonVehicles)
          );
        }

        // Update local state
        setVehicles((prev) =>
          prev.map((v) =>
            v.id === vehicleId ? { ...v, isComparing: true } : v
          )
        );
      } catch (err) {
        console.error('Error adding vehicle to comparison:', err);
        throw err;
      }
    },
    []
  );

  const submitFeedback = useCallback(
    async (vehicleId: string, type: 'more' | 'less') => {
      try {
        await apiClient.submitFeedback(vehicleId, type);
        // Optionally show success message
      } catch (err) {
        console.error('Error submitting feedback:', err);
        throw err;
      }
    },
    [apiClient]
  );

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchVehicles(initialFilters);
    }
  }, []); // Only run on mount

  const hasMore = vehicles.length < totalCount;

  return {
    vehicles,
    loading,
    error,
    totalCount,
    hasMore,
    fetchVehicles,
    loadMore,
    refresh,
    favoriteVehicle,
    compareVehicle,
    submitFeedback,
  };
};

export default useVehicleGrid;
