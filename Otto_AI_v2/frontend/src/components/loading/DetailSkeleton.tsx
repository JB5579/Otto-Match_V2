import React from 'react';
import { motion } from 'framer-motion';
import { useLazyImage } from '../../hooks/useLazyImage';

/**
 * DetailSkeleton - Loading skeleton for VehicleDetailModal
 *
 * Story 3-8.2: Suspense fallback for lazy loaded VehicleDetailModal
 *
 * Provides a placeholder UI while the modal component is loading
 * with pulse animation to indicate loading state
 */
export const DetailSkeleton: React.FC = () => {
  return (
    <div
      style={{
        position: 'fixed',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        width: '900px',
        maxWidth: '95vw',
        maxHeight: '90vh',
        background: 'rgba(255, 255, 255, 0.92)',
        backdropFilter: 'blur(24px)',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        padding: '24px',
        zIndex: 50,
      }}
    >
      {/* Header Skeleton */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <motion.div
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
          }}
          style={{
            width: '400px',
            height: '28px',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            borderRadius: '8px',
          }}
        />
        <motion.div
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: 0.2,
          }}
          style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            borderRadius: '50%',
          }}
        />
      </div>

      {/* Image Carousel Skeleton */}
      <motion.div
        animate={{
          opacity: [0.5, 1, 0.5],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          delay: 0.1,
        }}
        style={{
          width: '100%',
          height: '400px',
          background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize: '200% 100%',
          borderRadius: '12px',
          marginBottom: '24px',
        }}
      />

      {/* Two Column Layout Skeleton */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[...Array(4)].map((_, index) => (
            <motion.div
              key={index}
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: 0.1 + index * 0.1,
              }}
              style={{
                height: index === 0 ? '60px' : '80px',
                background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                backgroundSize: '200% 100%',
                borderRadius: '8px',
              }}
            />
          ))}
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[...Array(4)].map((_, index) => (
            <motion.div
              key={index}
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: 0.15 + index * 0.1,
              }}
              style={{
                height: index === 3 ? '60px' : '80px',
                background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                backgroundSize: '200% 100%',
                borderRadius: '8px',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * ImageSkeleton - Loading skeleton for images
 *
 * Story 3-8.6: Placeholder while lazy loading images
 *
 * @param props - Component props
 * @returns Image loading skeleton
 */
export interface ImageSkeletonProps {
  style?: React.CSSProperties;
  className?: string;
  width?: string | number;
  height?: string | number;
}

export const ImageSkeleton: React.FC<ImageSkeletonProps> = ({
  style,
  className,
  width = '100%',
  height = '100%',
}) => {
  return (
    <motion.div
      animate={{
        opacity: [0.5, 1, 0.5],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
      }}
      className={className}
      style={{
        width,
        height,
        background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
        backgroundSize: '200% 100%',
        borderRadius: '8px',
        ...style,
      }}
    />
  );
};

export default DetailSkeleton;
