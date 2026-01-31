import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type { Vehicle, VehicleCardVariant } from '../../app/types/api';
import { useComparison } from '../../context/ComparisonContext';
import MatchScoreBadge from './MatchScoreBadge';
import VehicleSpecs from './VehicleSpecs';
import PriceDisplay from './PriceDisplay';
import FeatureTags from './FeatureTags';
import ActionButtons from './ActionButtons';
import FavoriteButton from './FavoriteButton';
import LazyImage from '../loading/LazyImage';

interface VehicleCardProps {
  vehicle: Vehicle;
  variant?: VehicleCardVariant;
  onFavorite?: (vehicleId: string) => void;
  onCompare?: (vehicleId: string) => void;
  onFeedback?: (vehicleId: string, type: 'more' | 'less') => void;
  onClick?: (vehicle: Vehicle) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  // Animation props from cascade system (Task 3-3.7)
  animationProps?: {
    initial?: any;
    animate?: any;
    exit?: any;
    transition?: any;
  };
}

const VehicleCard: React.FC<VehicleCardProps> = ({
  vehicle,
  variant = 'default',
  onFavorite,
  onCompare,
  onFeedback,
  onClick,
  isExpanded = false,
  onToggleExpand,
  animationProps,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);

  // Story 3-6: Integrate with ComparisonContext
  const { addToComparison, isVehicleInComparison } = useComparison();
  const isInComparison = isVehicleInComparison(vehicle.id);

  const heroImage = vehicle.images?.find(img => img.category === 'hero') || vehicle.images?.[0];
  const matchScore = vehicle.matchScore || 0;
  const isOttoPick = matchScore >= 95;

  const handleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorited(!isFavorited);
    onFavorite?.(vehicle.id);
  };

  const handleCompare = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    // Story 3-6: Use ComparisonContext instead of prop callback
    addToComparison(vehicle);
    onCompare?.(vehicle.id);
  }, [vehicle.id, addToComparison, onCompare]);

  const handleFeedback = (type: 'more' | 'less', e: React.MouseEvent) => {
    e.stopPropagation();
    onFeedback?.(vehicle.id, type);
  };

  const handleCardClick = () => {
    onClick?.(vehicle);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.(vehicle);
    }
  };

  return (
    <motion.div
      className="vehicle-card"
      initial={animationProps?.initial || { opacity: 0, y: 20 }}
      animate={animationProps?.animate || { opacity: 1, y: 0 }}
      exit={animationProps?.exit}
      transition={animationProps?.transition || { duration: 0.3 }}
      layout
      whileHover={{ y: -8 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        borderRadius: '12px',
        boxShadow: isHovered
          ? '0 16px 48px rgba(0, 0, 0, 0.12)'
          : '0 8px 32px rgba(0, 0, 0, 0.08)',
        cursor: 'pointer',
        overflow: 'hidden',
        transition: 'all 0.3s ease-out',
        position: 'relative',
      }}
    >
      {/* Hero Image Container */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          paddingTop: '62.5%', // 16:10 aspect ratio
          overflow: 'hidden',
          backgroundColor: '#f5f5f5',
        }}
      >
        {heroImage && (
          <LazyImage
            src={heroImage.url}
            alt={heroImage.altText || vehicle.description || `${vehicle.make} ${vehicle.model}`}
            threshold={0.1}
            rootMargin="200px 0px"
            showSkeleton={true}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              transition: 'transform 0.3s ease-out',
              transform: isHovered ? 'scale(1.05)' : 'scale(1)',
            }}
          />
        )}

        {/* Badges Overlay */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 10,
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <MatchScoreBadge score={matchScore} isOttoPick={isOttoPick} />
          {vehicle.availabilityStatus && vehicle.availabilityStatus !== 'available' && (
            <div
              style={{
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 600,
                textTransform: 'lowercase',
                letterSpacing: '0.5px',
                background:
                  vehicle.availabilityStatus === 'sold'
                    ? 'rgba(239, 68, 68, 0.9)'
                    : 'rgba(245, 158, 11, 0.9)',
                color: 'white',
                backdropFilter: 'blur(8px)',
              }}
            >
              {vehicle.availabilityStatus}
            </div>
          )}
        </div>

        {/* Favorite Button */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            zIndex: 10,
          }}
        >
          <FavoriteButton
            isFavorited={isFavorited}
            onToggle={handleFavorite}
            size={40}
          />
        </div>

        {/* Social Proof - Viewers */}
        {vehicle.currentViewers !== undefined && vehicle.currentViewers > 0 && (
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              background: 'rgba(0, 0, 0, 0.6)',
              backdropFilter: 'blur(8px)',
              color: 'white',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#22c55e',
                animation: 'pulse 2s infinite',
              }}
            />
            {vehicle.currentViewers} viewing
          </div>
        )}
      </div>

      {/* Card Content */}
      <div style={{ padding: '16px' }}>
        {/* Title */}
        <h3
          style={{
            margin: '0 0 8px 0',
            fontSize: '18px',
            fontWeight: 600,
            color: '#1a1a1a',
            lineHeight: '1.3',
          }}
        >
          {vehicle.year} {vehicle.make} {vehicle.model}
          {vehicle.trim && ` ${vehicle.trim}`}
        </h3>

        {/* Vehicle Specs */}
        {vehicle.mileage !== undefined && (
          <VehicleSpecs
            mileage={vehicle.mileage}
            transmission={vehicle.transmission}
            drivetrain={vehicle.drivetrain}
            fuelType={vehicle.fuel_type}
            range={vehicle.range}
          />
        )}

        {/* Price */}
        {vehicle.price !== undefined && (
          <PriceDisplay
            price={vehicle.price}
            originalPrice={vehicle.originalPrice}
            savings={vehicle.savings}
          />
        )}

        {/* Feature Tags */}
        {vehicle.features && vehicle.features.length > 0 && (
          <FeatureTags features={vehicle.features} maxTags={3} />
        )}

        {/* Otto Recommendation */}
        {vehicle.ottoRecommendation && (
          <div
            style={{
              marginTop: '12px',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'rgba(14, 165, 233, 0.1)',
              border: '1px solid rgba(14, 165, 233, 0.2)',
              fontSize: '13px',
              color: '#0c4a6e',
              lineHeight: '1.4',
              fontStyle: 'italic',
            }}
          >
            "{vehicle.ottoRecommendation}"
          </div>
        )}

        {/* Action Buttons */}
        <ActionButtons
          onThumbsUp={(e) => handleFeedback('more', e)}
          onThumbsDown={(e) => handleFeedback('less', e)}
          onCompare={handleCompare}
          onToggleExpand={onToggleExpand}
          isExpanded={isExpanded}
          showExpandButton={variant === 'default'}
          isComparing={isInComparison}
        />
      </div>

      {/* Pulsing Animation Keyframes */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.2);
          }
        }
      `}</style>
    </motion.div>
  );
};

/**
 * Custom comparison function for React.memo optimization (Task 3-3.11)
 * Only re-render if critical vehicle data or state has changed
 */
const arePropsEqual = (prevProps: VehicleCardProps, nextProps: VehicleCardProps): boolean => {
  // Check vehicle data changes
  if (prevProps.vehicle.id !== nextProps.vehicle.id) return false;
  if (prevProps.vehicle.matchScore !== nextProps.vehicle.matchScore) return false;
  if (prevProps.vehicle.price !== nextProps.vehicle.price) return false;
  if (prevProps.vehicle.availabilityStatus !== nextProps.vehicle.availabilityStatus) return false;

  // Check state changes
  if (prevProps.isExpanded !== nextProps.isExpanded) return false;

  // Check variant changes
  if (prevProps.variant !== nextProps.variant) return false;

  // Props are equal, skip re-render
  return true;
};

export default React.memo(VehicleCard, arePropsEqual);
