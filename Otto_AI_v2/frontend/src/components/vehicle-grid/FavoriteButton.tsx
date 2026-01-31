import React from 'react';
import { motion } from 'framer-motion';

interface FavoriteButtonProps {
  isFavorited: boolean;
  onToggle: (e: React.MouseEvent) => void;
  size?: number;
}

const FavoriteButton: React.FC<FavoriteButtonProps> = ({
  isFavorited,
  onToggle,
  size = 40,
}) => {
  return (
    <motion.button
      onClick={(e) => onToggle(e)}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '50%',
        border: 'none',
        background: isFavorited
          ? 'rgba(239, 68, 68, 0.9)'
          : 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.3s ease-out',
        padding: 0,
      }}
    >
      <svg
        width={size * 0.5}
        height={size * 0.5}
        viewBox="0 0 24 24"
        fill={isFavorited ? 'white' : 'none'}
        stroke={isFavorited ? 'white' : '#ef4444'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          transition: 'all 0.3s ease-out',
        }}
      >
        <motion.path
          d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
          initial={isFavorited ? { scale: 1 } : { scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        />
      </svg>
    </motion.button>
  );
};

export default React.memo(FavoriteButton);
