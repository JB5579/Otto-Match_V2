import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Vehicle } from '../../app/types/api';
import { useVehicleContext } from '../../context/VehicleContext';
import { useFilters } from '../../context/FilterContext';
import { useVehicleCascade } from '../../hooks/useVehicleCascade';
import { throttle } from '../../utils/performance';
import VehicleCard from './VehicleCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { SuspenseVehicleDetailModal } from '../loading/LazilyLoadedModals';
import FilterEmptyState from '../filters/FilterEmptyState';

interface VehicleGridProps {
  vehicles: Vehicle[];
  loading?: boolean;
  error?: string | null;
  onFavorite?: (vehicleId: string) => void;
  onCompare?: (vehicleId: string) => void;
  onFeedback?: (vehicleId: string, type: 'more' | 'less') => void;
  onVehicleClick?: (vehicle: Vehicle) => void;
  emptyMessage?: string;
  pageSize?: number;
}

const VehicleGrid: React.FC<VehicleGridProps> = ({
  vehicles: propVehicles,
  loading: propLoading = false,
  error: propError = null,
  onFavorite,
  onCompare,
  onFeedback,
  onVehicleClick,
  emptyMessage = 'No vehicles found. Try adjusting your search criteria.',
  pageSize = 12,
}) => {
  // Use VehicleContext if available, otherwise fall back to props
  const vehicleContext = useVehicleContext();
  const filtersContext = useFilters();
  const vehicles = vehicleContext?.vehicles || propVehicles;
  const previousVehicles = vehicleContext?.previousVehicles || [];
  const loading = vehicleContext?.loading || propLoading;
  const error = vehicleContext?.error || propError;

  // Get filtered vehicles from FilterContext (Story 3-7)
  const filterResult = filtersContext?.getFilteredVehicles(vehicles) || {
    vehicles: vehicles,
    totalCount: vehicles.length,
    filteredCount: vehicles.length,
    activeFilterCount: 0,
  };
  const displayedVehiclesData = filterResult.vehicles;

  const [displayedVehicles, setDisplayedVehicles] = useState<Vehicle[]>([]);
  const [page, setPage] = useState(0);

  // Use cascade animation hook for delta calculation and animation props
  const { getVehicleAnimationProps } = useVehicleCascade(previousVehicles, vehicles);

  // Progressive loading - show vehicles in pages
  useEffect(() => {
    if (vehicles.length > 0) {
      const endIndex = (page + 1) * pageSize;
      setDisplayedVehicles(displayedVehiclesData.slice(0, endIndex));
    }
  }, [vehicles, page, pageSize]);

  // Use context's expanded card management if available
  const expandedCardIds = vehicleContext?.expandedCardIds || new Set<string>();
  const toggleCardExpanded = vehicleContext?.toggleExpandedCard || ((_vehicleId: string) => {
    // Fallback implementation (not used if context is available)
  });

  // Use context's favorite management if available
  const handleFavorite = vehicleContext?.toggleFavorite || onFavorite;

  // Modal integration (Task 3-4.9, 3-4.10)
  const handleVehicleClick = onVehicleClick || vehicleContext?.openModal;

  // Infinite scroll handler
  // Story 3-8.11: Throttled by 100ms to prevent performance issues
  const handleScroll = useMemo(
    () => throttle(() => {
      const scrollTop = window.scrollY;
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = window.innerHeight;

      if (scrollTop + clientHeight >= scrollHeight - 500) {
        // Load more if we haven't loaded all vehicles
        if (displayedVehicles.length < displayedVehiclesData.length) {
          setPage((prev) => prev + 1);
        }
      }
    }, 100),
    [displayedVehicles.length, displayedVehiclesData.length]
  );

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // Error state with retry option
  if (error) {
    return (
      <ErrorState
        message={error}
        onRetry={vehicleContext?.retryUpdate}
        showRetryButton={!!vehicleContext?.retryUpdate}
      />
    );
  }

  // Loading state (initial load with no vehicles yet)
  if (loading && vehicles.length === 0) {
    return <LoadingState message="Finding vehicles for you..." cardCount={pageSize / 2} />;
  }

  // Empty state
  if (vehicles.length === 0 && !loading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          padding: '40px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: '64px',
            marginBottom: '16px',
            opacity: 0.5,
          }}
        >
          🔍
        </div>
        <h3
          style={{
            fontSize: '18px',
            fontWeight: 600,
            color: '#333',
            margin: '0 0 8px 0',
          }}
        >
          {emptyMessage}
        </h3>
      </div>
    );
  }

  // Vehicle grid
  return (
    <div className="vehicle-grid-container">
      <div
        className="vehicle-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)', // 3 columns on desktop
          gap: '24px',
          padding: '24px',
          // Responsive breakpoints handled in CSS
        }}
      >
        <AnimatePresence mode="popLayout">
          {displayedVehiclesData.map((vehicle, index) => {
            // Get animation props from cascade hook
            const animationProps = getVehicleAnimationProps(vehicle.id, index);

            return (
              <motion.div
                key={vehicle.id}
                layout
                {...(animationProps as any)}
              >
                <VehicleCard
                  vehicle={vehicle}
                  onFavorite={handleFavorite}
                  onCompare={onCompare}
                  onFeedback={onFeedback}
                  onClick={handleVehicleClick}
                  isExpanded={expandedCardIds.has(vehicle.id)}
                  onToggleExpand={() => toggleCardExpanded(vehicle.id)}
                  animationProps={animationProps}
                />
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Loading more indicator */}
      {loading && displayedVehicles.length < vehicles.length && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            padding: '24px',
          }}
        >
          <div
            style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
            }}
          >
            {[...Array(3)].map((_, index) => (
              <motion.div
                key={index}
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: index * 0.2,
                }}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#0EA5E9',
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Responsive CSS */}
      <style>{`
        @media (max-width: 1199px) {
          .vehicle-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 20px !important;
            padding: 20px !important;
          }
        }

        @media (max-width: 767px) {
          .vehicle-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            padding: 16px !important;
          }
        }

        @media (max-width: 479px) {
          .vehicle-grid {
            padding: 12px !important;
            gap: 12px !important;
          }
        }
      `}</style>

      {/* Vehicle Detail Modal (Task 3-4.9, 3-4.10, 3-4.7) */}
      {/* Story 3-8.2: Lazy loaded with Suspense fallback */}
      {vehicleContext && (
        <SuspenseVehicleDetailModal
          vehicle={vehicleContext.selectedVehicle}
          isOpen={vehicleContext.isModalOpen}
          onClose={vehicleContext.closeModal}
          onHold={vehicleContext.holdVehicle}
          onCompare={vehicleContext.compareVehicle}
        />
      )}
    </div>
  );
};

export default React.memo(VehicleGrid);
