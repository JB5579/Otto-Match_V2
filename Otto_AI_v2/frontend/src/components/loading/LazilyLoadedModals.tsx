/**
 * Lazy loading wrappers for heavy components
 * Story 3-8.2: Implement React.lazy for VehicleDetailModal and ComparisonView
 *
 * Code splits heavy components into separate chunks:
 * - VehicleDetailModal (~30KB gzipped)
 * - ComparisonView (~20KB gzipped)
 *
 * Uses Suspense with loading skeleton fallbacks
 */

import { lazy, Suspense } from 'react';
import { DetailSkeleton, ImageSkeleton } from '../loading/DetailSkeleton';

/**
 * Lazy loaded VehicleDetailModal
 * Loads modal component only when needed (user clicks vehicle card)
 */
export const LazyVehicleDetailModal = lazy(() =>
  import('../components/vehicle-detail/VehicleDetailModal').then((module) => ({
    default: module.VehicleDetailModal,
  }))
);

/**
 * Lazy loaded ComparisonView
 * Loads comparison component only when user has 2+ vehicles selected
 */
export const LazyComparisonView = lazy(() =>
  import('../components/comparison/ComparisonView').then((module) => ({
    default: module.ComparisonView,
  }))
);

/**
 * Suspense wrapper with skeleton fallback for VehicleDetailModal
 */
export const SuspenseVehicleDetailModal: React.FC<any> = (props) => (
  <Suspense fallback={<DetailSkeleton />}>
    <LazyVehicleDetailModal {...props} />
  </Suspense>
);

/**
 * Suspense wrapper with skeleton fallback for ComparisonView
 */
export const SuspenseComparisonView: React.FC<any> = (props) => {
  // Simple loading state for comparison view
  const loadingSkeleton = (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '1200px',
          padding: '24px',
          background: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(24px)',
          borderRadius: '16px',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.2)',
        }}
      >
        <div
          style={{
            width: '60px',
            height: '60px',
            margin: '0 auto 24px',
            borderRadius: '50%',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            animation: 'pulse 1.5s infinite',
          }}
        />
        <div
          style={{
            textAlign: 'center',
            color: '#6b7280',
            fontSize: '16px',
          }}
        >
          Loading comparison...
        </div>
      </div>
    </div>
  );

  return (
    <Suspense fallback={loadingSkeleton}>
      <LazyComparisonView {...props} />
    </Suspense>
  );
};

export default SuspenseVehicleDetailModal;
