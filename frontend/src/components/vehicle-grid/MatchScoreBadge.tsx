import React from 'react';
import { motion } from 'framer-motion';

interface MatchScoreBadgeProps {
  score: number;
  isOttoPick?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const MatchScoreBadge: React.FC<MatchScoreBadgeProps> = ({
  score,
  isOttoPick = false,
  size = 'medium',
}) => {
  const getScoreTier = (): { color: string; label: string } => {
    if (score >= 90) {
      return { color: '#22c55e', label: 'Excellent' }; // Green
    } else if (score >= 80) {
      return { color: '#84cc16', label: 'Great' }; // Lime
    } else if (score >= 70) {
      return { color: '#eab308', label: 'Good' }; // Yellow
    } else {
      return { color: '#f97316', label: 'Fair' }; // Orange
    }
  };

  const tier = getScoreTier();
  const displayScore = Math.round(score);

  const sizeStyles = {
    small: { width: 48, height: 48, fontSize: 12, iconSize: 16 },
    medium: { width: 64, height: 64, fontSize: 16, iconSize: 20 },
    large: { width: 80, height: 80, fontSize: 20, iconSize: 24 },
  };

  const currentSize = sizeStyles[size];

  if (isOttoPick) {
    // Otto's Pick Badge - Star variant with cyan glow
    return (
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        style={{
          width: currentSize.width,
          height: currentSize.height,
          borderRadius: '50%',
          background: `linear-gradient(135deg, #0EA5E9 0%, #06b6d4 100%)`,
          boxShadow: '0 0 20px rgba(14, 165, 233, 0.6), 0 0 40px rgba(6, 182, 212, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          animation: 'glow-pulse 2s ease-in-out infinite',
        }}
      >
        {/* Star Icon */}
        <svg
          width={currentSize.iconSize}
          height={currentSize.iconSize}
          viewBox="0 0 24 24"
          fill="white"
          style={{
            filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))',
          }}
        >
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>

        {/* Otto's Pick Label */}
        <div
          style={{
            position: 'absolute',
            bottom: -20,
            left: '50%',
            transform: 'translateX(-50%)',
            fontSize: '10px',
            fontWeight: 700,
            color: '#0EA5E9',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            whiteSpace: 'nowrap',
          }}
        >
          Otto's Pick
        </div>

        <style>{`
          @keyframes glow-pulse {
            0%, 100% {
              box-shadow: 0 0 20px rgba(14, 165, 233, 0.6), 0 0 40px rgba(6, 182, 212, 0.4);
            }
            50% {
              box-shadow: 0 0 30px rgba(14, 165, 233, 0.8), 0 0 60px rgba(6, 182, 212, 0.6);
            }
          }
        `}</style>
      </motion.div>
    );
  }

  // Standard Match Score Badge
  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      style={{
        width: currentSize.width,
        height: currentSize.height,
        borderRadius: '50%',
        background: tier.color,
        backdropFilter: 'blur(12px)',
        boxShadow: `0 4px 16px ${tier.color}40`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontWeight: 700,
        position: 'relative',
      }}
    >
      <span
        style={{
          fontSize: currentSize.fontSize,
          lineHeight: 1,
        }}
      >
        {displayScore}%
      </span>

      {/* Pulsing ring for high scores */}
      {score >= 95 && (
        <>
          <div
            style={{
              position: 'absolute',
              top: -4,
              left: -4,
              right: -4,
              bottom: -4,
              borderRadius: '50%',
              border: `2px solid ${tier.color}`,
              opacity: 0.5,
              animation: 'pulse-ring 2s ease-out infinite',
            }}
          />
          <style>{`
            @keyframes pulse-ring {
              0% {
                transform: scale(1);
                opacity: 0.5;
              }
              100% {
                transform: scale(1.4);
                opacity: 0;
              }
            }
          `}</style>
        </>
      )}

      {/* Tier Label */}
      <div
        style={{
          position: 'absolute',
          bottom: -20,
          left: '50%',
          transform: 'translateX(-50%)',
          fontSize: '10px',
          fontWeight: 600,
          color: tier.color,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          whiteSpace: 'nowrap',
        }}
      >
        {tier.label}
      </div>
    </motion.div>
  );
};

export default React.memo(MatchScoreBadge);
