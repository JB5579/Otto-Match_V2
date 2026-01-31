import React from 'react';
import { motion } from 'framer-motion';
import VehicleCardSkeleton from './VehicleCardSkeleton';

export interface LoadingStateProps {
  message?: string;
  cardCount?: number;
}

/**
 * LoadingState component displays skeleton cards during vehicle updates
 *
 * Features:
 * - Matches grid layout (3/2/1 columns responsive)
 * - Shimmer effect on skeleton cards
 * - Optional loading message
 * - Smooth fade-in animation
 * - Optimistic UI: preserves existing content if available
 *
 * @param props - Component props
 * @returns Loading state with skeleton cards
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Updating recommendations...',
  cardCount = 6,
}) => {
  return (
    <div className="loading-state">
      {/* Loading Message */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '16px',
            marginBottom: '8px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 24px',
              borderRadius: '24px',
              background: 'rgba(14, 165, 233, 0.1)',
              border: '1px solid rgba(14, 165, 233, 0.2)',
              fontSize: '14px',
              color: '#0c4a6e',
              fontWeight: 500,
            }}
          >
            {/* Loading Spinner */}
            <motion.div
              animate={{
                rotate: 360,
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'linear',
              }}
              style={{
                width: '16px',
                height: '16px',
                border: '2px solid rgba(14, 165, 233, 0.3)',
                borderTopColor: '#0ea5e9',
                borderRadius: '50%',
              }}
            />
            {message}
          </div>
        </motion.div>
      )}

      {/* Skeleton Grid */}
      <div
        className="vehicle-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '24px',
          padding: '24px',
        }}
      >
        {[...Array(cardCount)].map((_, index) => (
          <motion.div
            key={`skeleton-${index}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              delay: index * 0.05,
              duration: 0.3,
            }}
          >
            <VehicleCardSkeleton />
          </motion.div>
        ))}
      </div>

      {/* Responsive CSS */}
      <style>{`
        @media (max-width: 1199px) {
          .loading-state .vehicle-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 20px !important;
            padding: 20px !important;
          }
        }

        @media (max-width: 767px) {
          .loading-state .vehicle-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            padding: 16px !important;
          }
        }

        @media (max-width: 479px) {
          .loading-state .vehicle-grid {
            padding: 12px !important;
            gap: 12px !important;
          }
        }
      `}</style>
    </div>
  );
};

export default LoadingState;
