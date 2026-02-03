import React from 'react';
import { motion } from 'framer-motion';

interface ActionButtonsProps {
  onThumbsUp: (e: React.MouseEvent) => void;
  onThumbsDown: (e: React.MouseEvent) => void;
  onCompare: (e: React.MouseEvent) => void;
  onToggleExpand?: () => void;
  isExpanded?: boolean;
  showExpandButton?: boolean;
  isComparing?: boolean; // Story 3-6: Show if vehicle is in comparison list
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  onThumbsUp,
  onThumbsDown,
  onCompare,
  onToggleExpand,
  isExpanded = false,
  showExpandButton = true,
  isComparing = false,
}) => {
  const buttonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 14px',
    borderRadius: '8px',
    border: '1px solid rgba(0, 0, 0, 0.1)',
    background: 'white',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 0.2s ease-out',
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        marginTop: '12px',
        flexWrap: 'wrap',
      }}
    >
      {/* Thumbs Up Button */}
      <motion.button
        onClick={onThumbsUp}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={buttonStyle}
        aria-label="More like this"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth={2}>
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
        </svg>
        <span>More like this</span>
      </motion.button>

      {/* Thumbs Down Button */}
      <motion.button
        onClick={onThumbsDown}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={buttonStyle}
        aria-label="Fewer like this"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth={2}>
          <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
        </svg>
        <span>Fewer like this</span>
      </motion.button>

      {/* Compare Button */}
      <motion.button
        onClick={onCompare}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={{
          ...buttonStyle,
          background: isComparing
            ? 'rgba(34, 197, 94, 0.15)'
            : 'rgba(14, 165, 233, 0.1)',
          borderColor: isComparing
            ? 'rgba(34, 197, 94, 0.3)'
            : 'rgba(14, 165, 233, 0.3)',
          color: isComparing
            ? '#166534'
            : '#0369a1',
        }}
        aria-label={isComparing ? "Vehicle in comparison list" : "Add to comparison"}
        aria-pressed={isComparing}
      >
        {isComparing ? (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth={2}>
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <span>Added</span>
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" strokeWidth={2}>
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M9 3v18" />
              <path d="M15 3v18" />
            </svg>
            <span>Compare</span>
          </>
        )}
      </motion.button>

      {/* Expand/Collapse Button (mobile progressive disclosure) */}
      {showExpandButton && onToggleExpand && (
        <motion.button
          onClick={onToggleExpand}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            ...buttonStyle,
            marginLeft: 'auto', // Push to right
            padding: '8px 12px',
          }}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
          aria-expanded={isExpanded}
        >
          <span>{isExpanded ? 'Show less' : 'Show more'}</span>
          <motion.svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <path d="M6 9l6 6 6-6" />
          </motion.svg>
        </motion.button>
      )}
    </div>
  );
};

export default React.memo(ActionButtons);
