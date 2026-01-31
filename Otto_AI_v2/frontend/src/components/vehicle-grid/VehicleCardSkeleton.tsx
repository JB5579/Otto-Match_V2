import React from 'react';
import { motion } from 'framer-motion';

interface VehicleCardSkeletonProps {
  variant?: 'default' | 'compact';
}

const VehicleCardSkeleton: React.FC<VehicleCardSkeletonProps> = () => {
  const skeletonStyle = {
    background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
  };

  return (
    <motion.div
      className="vehicle-card-skeleton"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        borderRadius: '12px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
        overflow: 'hidden',
      }}
    >
      {/* Hero Image Skeleton */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          paddingTop: '62.5%', // 16:10 aspect ratio
          backgroundColor: '#f5f5f5',
        }}
      >
        {/* Badge Skeleton */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            ...skeletonStyle,
          } as any}
        />

        {/* Favorite Button Skeleton */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            ...skeletonStyle,
          } as any}
        />
      </div>

      {/* Card Content */}
      <div style={{ padding: '16px' }}>
        {/* Title Skeleton */}
        <div
          style={{
            height: '22px',
            width: '70%',
            borderRadius: '4px',
            marginBottom: '12px',
            ...skeletonStyle,
          } as any}
        />

        {/* Specs Skeleton */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          {[...Array(3)].map((_, index) => (
            <div
              key={index}
              style={{
                height: '24px',
                width: '80px',
                borderRadius: '6px',
                ...skeletonStyle,
              } as any}
            />
          ))}
        </div>

        {/* Price Skeleton */}
        <div
          style={{
            height: '28px',
            width: '50%',
            borderRadius: '4px',
            marginBottom: '12px',
            ...skeletonStyle,
          } as any}
        />

        {/* Feature Tags Skeleton */}
        <div
          style={{
            display: 'flex',
            gap: '6px',
            marginBottom: '12px',
          }}
        >
          {[...Array(3)].map((_, index) => (
            <div
              key={index}
              style={{
                height: '22px',
                width: '60px',
                borderRadius: '12px',
                ...skeletonStyle,
              } as any}
            />
          ))}
        </div>

        {/* Action Buttons Skeleton */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
          }}
        >
          {[...Array(3)].map((_, index) => (
            <div
              key={index}
              style={{
                height: '36px',
                width: '100px',
                borderRadius: '8px',
                ...skeletonStyle,
              } as any}
            />
          ))}
        </div>
      </div>

      {/* Shimmer Animation */}
      <style>{`
        @keyframes shimmer {
          0% {
            background-position: 200% 0;
          }
          100% {
            background-position: -200% 0;
          }
        }
      `}</style>
    </motion.div>
  );
};

export default VehicleCardSkeleton;
