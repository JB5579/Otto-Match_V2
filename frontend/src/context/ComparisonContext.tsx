import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { Vehicle } from '../app/types/api';

/**
 * Comparison Context for managing vehicle comparison state
 *
 * Features:
 * - Add/remove vehicles from comparison list (max 4)
 * - Persist comparison list to sessionStorage (AC9 compliance)
 * - Track comparison state across page navigation
 * - Integration with backend comparison API
 *
 * AC1: Side-by-side vehicle comparison (2-4 vehicles)
 * AC2: Comparison list persistence (sessionStorage, 30min expiry)
 */

export interface ComparisonVehicle extends Vehicle {
  addedAt: string;
}

export interface ComparisonResult {
  comparison_id: string;
  vehicle_ids: string[];
  comparison_results: Array<{
    vehicle_id: string;
    vehicle_data: Record<string, unknown>;
    specifications: Array<{
      category: string;
      name: string;
      value: string | number | boolean;
      unit?: string;
      importance_score: number;
    }>;
    features: Array<{
      category: string;
      features: string[];
      included: boolean;
      value_score: number;
    }>;
    price_analysis: {
      current_price: number;
      market_average: number;
      market_range: [number, number];
      price_position: string;
      savings_amount?: number;
      savings_percentage?: number;
      price_trend: string;
      market_demand: string;
    };
    overall_score: number;
  }>;
  feature_differences: Array<{
    feature_name: string;
    feature_type: string;
    vehicle_a_value: string | number | boolean;
    vehicle_b_value: string | number | boolean;
    difference_type: string;
    importance_weight: number;
    description: string;
  }>;
  semantic_similarity?: Record<string, {
    similarity_score: number;
    shared_features: string[];
    unique_features_a: string[];
    unique_features_b: string[];
    similarity_explanation: string;
  }>;
  recommendation_summary?: string;
  processing_time: number;
  cached: boolean;
  timestamp: string;
}

interface ComparisonContextValue {
  comparisonList: ComparisonVehicle[];
  isComparing: boolean;
  comparisonResult: ComparisonResult | null;
  loading: boolean;
  error: string | null;
  addToComparison: (vehicle: Vehicle) => void;
  removeFromComparison: (vehicleId: string) => void;
  clearComparison: () => void;
  openComparison: () => Promise<void>;
  closeComparison: () => void;
  isVehicleInComparison: (vehicleId: string) => boolean;
  canAddMore: boolean;
}

const ComparisonContext = createContext<ComparisonContextValue | null>(null);

const STORAGE_KEY = 'otto_comparison_list';
const MAX_COMPARISON_VEHICLES = 4;
// AC9: 30-minute expiry (spec compliance)
const STORAGE_EXPIRY_MS = 30 * 60 * 1000;

const loadFromStorage = (): ComparisonVehicle[] => {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Validate and filter expired entries (older than 30 minutes)
      const now = new Date().getTime();
      const valid = parsed.filter((v: ComparisonVehicle) => {
        const addedTime = new Date(v.addedAt).getTime();
        return now - addedTime < STORAGE_EXPIRY_MS;
      });
      return valid;
    }
  } catch (error) {
    console.error('[ComparisonContext] Failed to load from storage:', error);
  }
  return [];
};

const saveToStorage = (vehicles: ComparisonVehicle[]) => {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(vehicles));
  } catch (error) {
    console.error('[ComparisonContext] Failed to save to storage:', error);
  }
};

export interface ComparisonProviderProps {
  children: React.ReactNode;
}

export const ComparisonProvider: React.FC<ComparisonProviderProps> = ({ children }) => {
  const [comparisonList, setComparisonList] = useState<ComparisonVehicle[]>(() => loadFromStorage());
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // Persist comparison list to sessionStorage (AC9 compliance)
  useEffect(() => {
    saveToStorage(comparisonList);
  }, [comparisonList]);

  /**
   * Check if vehicle is already in comparison list
   */
  const isVehicleInComparison = useCallback((vehicleId: string): boolean => {
    return comparisonList.some(v => v.id === vehicleId);
  }, [comparisonList]);

  /**
   * Check if more vehicles can be added (max 4)
   */
  const canAddMore = comparisonList.length < MAX_COMPARISON_VEHICLES;

  /**
   * Add vehicle to comparison list
   * AC: Maximum 4 vehicles, prevent duplicates
   */
  const addToComparison = useCallback((vehicle: Vehicle) => {
    if (comparisonList.length >= MAX_COMPARISON_VEHICLES) {
      setError(`Maximum ${MAX_COMPARISON_VEHICLES} vehicles can be compared at once`);
      setTimeout(() => setError(null), 3000);
      return;
    }

    if (isVehicleInComparison(vehicle.id)) {
      setError('Vehicle already in comparison list');
      setTimeout(() => setError(null), 3000);
      return;
    }

    const comparisonVehicle: ComparisonVehicle = {
      ...vehicle,
      addedAt: new Date().toISOString(),
    };

    setComparisonList(prev => [...prev, comparisonVehicle]);
    setError(null);
  }, [comparisonList, isVehicleInComparison]);

  /**
   * Remove vehicle from comparison list
   */
  const removeFromComparison = useCallback((vehicleId: string) => {
    setComparisonList(prev => prev.filter(v => v.id !== vehicleId));
    // Clear comparison result if list becomes empty
    setComparisonList(prevList => {
      if (prevList.length <= 1) {
        setComparisonResult(null);
        setIsOpen(false);
      }
      return prevList;
    });
  }, []);

  /**
   * Clear all vehicles from comparison list
   */
  const clearComparison = useCallback(() => {
    setComparisonList([]);
    setComparisonResult(null);
    setIsOpen(false);
  }, []);

  /**
   * Open comparison view and fetch comparison data from backend
   * AC: Integrate with /api/vehicles/compare endpoint
   */
  const openComparison = useCallback(async () => {
    if (comparisonList.length < 2) {
      setError('Add at least 2 vehicles to compare');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
      const vehicleIds = comparisonList.map(v => v.id);

      const response = await fetch(`${API_BASE}/api/vehicles/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vehicle_ids: vehicleIds,
          include_semantic_similarity: true,
          include_price_analysis: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Comparison API error: ${response.statusText}`);
      }

      const result: ComparisonResult = await response.json();
      setComparisonResult(result);
      setIsOpen(true);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch comparison data';
      setError(errorMsg);
      console.error('[ComparisonContext] Comparison API error:', err);
    } finally {
      setLoading(false);
    }
  }, [comparisonList]);

  /**
   * Close comparison view
   */
  const closeComparison = useCallback(() => {
    setIsOpen(false);
  }, []);

  const value: ComparisonContextValue = {
    comparisonList,
    isComparing: isOpen,
    comparisonResult,
    loading,
    error,
    addToComparison,
    removeFromComparison,
    clearComparison,
    openComparison,
    closeComparison,
    isVehicleInComparison,
    canAddMore,
  };

  return (
    <ComparisonContext.Provider value={value}>
      {children}
    </ComparisonContext.Provider>
  );
};

/**
 * Hook to access comparison context
 * Must be used within ComparisonProvider
 */
export const useComparison = (): ComparisonContextValue => {
  const context = useContext(ComparisonContext);

  if (!context) {
    throw new Error('useComparison must be used within a ComparisonProvider');
  }

  return context;
};

export default ComparisonContext;
