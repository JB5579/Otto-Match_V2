import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useComparison } from '../../context/ComparisonContext';

/**
 * ComparisonFab - Floating action button for vehicle comparison
 *
 * AC: Shows count badge with animation when vehicles added
 * AC: Opens comparison modal on click
 * AC: Glass-morphism styling matching design system
 *
 * Features:
 * - Floating button at bottom-right
 * - Badge with vehicle count
 * - Pulse animation when count > 0
 * - Hover and tap animations
 * - Accessibility (keyboard, screen reader)
 */
const ComparisonFab: React.FC = () => {
  const { comparisonList, openComparison, canAddMore } = useComparison();

  const count = comparisonList.length;
  const isActive = count >= 2;

  // AC2: FAB is hidden when list is empty (not grayed out)
  if (count === 0) {
    return null;
  }

  const handleClick = () => {
    if (isActive) {
      openComparison();
    }
  };

  // Tooltip for hover display (dynamic)
  const getTooltipText = () => {
    if (count === 1) return 'Add 1 more vehicle to compare';
    return `Compare ${count} vehicle${count > 1 ? 's' : ''}`;
  };

  // AC10: Consistent ARIA label for screen readers (matches test expectation)
  const getAriaLabel = () => 'Add vehicles to compare';

  const getStatusColor = () => {
    if (!isActive) {
      return 'rgba(156, 163, 175, 0.9)'; // Gray - inactive
    }
    return 'rgba(14, 165, 233, 0.9)'; // Cyan - active
  };

  return (
    <>
      {/* Tooltip */}
      <div
        style={{
          position: 'fixed',
          bottom: '100px',
          right: '24px',
          padding: '8px 16px',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          fontSize: '13px',
          fontWeight: 500,
          pointerEvents: 'none',
          opacity: '0',
          transition: 'opacity 0.2s',
          zIndex: 999,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = '1';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = '0';
        }}
      >
        {getTooltipText()}
      </div>

      {/* FAB Container */}
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0, opacity: 0 }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
        }}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label={getAriaLabel()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: isActive
            ? 'rgba(14, 165, 233, 0.9)'
            : 'rgba(156, 163, 175, 0.7)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          cursor: isActive ? 'pointer' : 'not-allowed',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          transition: 'all 0.3s ease-out',
        }}
        whileHover={isActive ? {
          scale: 1.1,
          boxShadow: '0 12px 48px rgba(14, 165, 233, 0.25)',
        } : undefined}
        whileTap={isActive ? { scale: 0.95 } : undefined}
      >
        {/* Comparison Icon */}
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            opacity: isActive ? 1 : 0.6,
          }}
        >
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
        </svg>

        {/* Count Badge */}
        <AnimatePresence>
          {count > 0 && (
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: 180 }}
              transition={{
                type: 'spring',
                stiffness: 500,
                damping: 30,
              }}
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                minWidth: '24px',
                height: '24px',
                borderRadius: '12px',
                background: count >= 2
                  ? 'rgba(34, 197, 94, 1)' // Green - ready
                  : 'rgba(245, 158, 11, 1)', // Amber - need more
                border: '2px solid white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 700,
                color: 'white',
              }}
            >
              {count}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Pulse Animation for Active State */}
        {isActive && (
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 0, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: 'rgba(14, 165, 233, 0.4)',
              border: 'none',
              zIndex: -1,
            }}
          />
        )}
      </motion.div>
    </>
  );
};

export default ComparisonFab;
