import React from 'react';
import { motion } from 'framer-motion';

export interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  showRetryButton?: boolean;
}

/**
 * ErrorState component displays user-friendly error messages with retry options
 *
 * Features:
 * - Clear error messaging
 * - Optional retry button
 * - Smooth fade-in animation
 * - Preserves last known good state (handled by VehicleContext)
 * - Glass-morphism styling consistent with design system
 *
 * @param props - Component props
 * @returns Error state with retry option
 */
export const ErrorState: React.FC<ErrorStateProps> = ({
  message = 'Unable to update recommendations',
  onRetry,
  showRetryButton = true,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        padding: '40px 24px',
        textAlign: 'center',
      }}
    >
      {/* Error Icon */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{
          delay: 0.1,
          type: 'spring',
          stiffness: 200,
          damping: 15,
        }}
        style={{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '2px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '24px',
        }}
      >
        <svg
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
            stroke="#ef4444"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </motion.div>

      {/* Error Message */}
      <h3
        style={{
          fontSize: '20px',
          fontWeight: 600,
          color: '#1a1a1a',
          margin: '0 0 12px 0',
        }}
      >
        {message}
      </h3>

      {/* Sub Message */}
      <p
        style={{
          fontSize: '15px',
          color: '#666',
          margin: '0 0 32px 0',
          maxWidth: '400px',
        }}
      >
        {showRetryButton
          ? 'Please try again. If the problem persists, check your connection.'
          : 'We\'re working on getting things back to normal.'}
      </p>

      {/* Retry Button */}
      {showRetryButton && onRetry && (
        <motion.button
          onClick={onRetry}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            padding: '12px 32px',
            borderRadius: '8px',
            background: '#0ea5e9',
            color: 'white',
            border: 'none',
            fontSize: '15px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(14, 165, 233, 0.25)',
          }}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M1 4V10H7M23 20V14H17M20.49 9C19.9828 7.56678 19.1209 6.28539 17.9845 5.27542C16.8482 4.26546 15.4745 3.55976 13.9917 3.22426C12.5089 2.88875 10.9652 2.93434 9.50481 3.35677C8.04437 3.77921 6.71475 4.56471 5.64 5.64L1 10M23 14L18.36 18.36C17.2853 19.4353 15.9556 20.2208 14.4952 20.6432C13.0348 21.0657 11.4911 21.1112 10.0083 20.7757C8.52547 20.4402 7.1518 19.7345 6.01547 18.7246C4.87913 17.7146 4.01717 16.4332 3.51 15"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Retry
        </motion.button>
      )}
    </motion.div>
  );
};

export default ErrorState;
