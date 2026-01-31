import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useComparison } from '../../context/ComparisonContext';
import ComparisonTable from './ComparisonTable';

/**
 * ComparisonView - Modal for side-by-side vehicle comparison
 *
 * AC: Modal overlay with backdrop blur
 * AC: Displays comparison table with best value highlighting
 * AC: Otto's recommendation section
 * AC: Close on X button, Escape key, or backdrop click
 * AC: Remove vehicles from comparison
 *
 * Features:
 * - Glass-morphism design
 * - Responsive layout
 * - Accessibility (keyboard, screen reader, focus trap)
 */
const ComparisonView: React.FC = () => {
  const {
    comparisonList,
    isComparing,
    comparisonResult,
    loading,
    error,
    closeComparison,
    removeFromComparison,
    clearComparison,
  } = useComparison();

  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  /**
   * Focus trap for accessibility
   */
  useEffect(() => {
    if (isComparing) {
      // Store previous focused element
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Focus first focusable element in modal
      const focusableElements = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements && focusableElements.length > 0) {
        (focusableElements[0] as HTMLElement).focus();
      }

      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    } else {
      // Restore focus and scroll
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isComparing]);

  /**
   * Handle keyboard events
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      closeComparison();
    }
  };

  /**
   * Handle backdrop click
   */
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeComparison();
    }
  };

  /**
   * Get vehicle title
   */
  const getVehicleTitle = (vehicleId: string): string => {
    const vehicle = comparisonList.find((v) => v.id === vehicleId);
    if (!vehicle) return 'Unknown';

    return [vehicle.year, vehicle.make, vehicle.model, vehicle.trim]
      .filter(Boolean)
      .join(' ');
  };

  /**
   * Get vehicle image
   */
  const getVehicleImage = (vehicleId: string): string | undefined => {
    const vehicle = comparisonList.find((v) => v.id === vehicleId);
    if (!vehicle) return undefined;

    const heroImage = vehicle.images?.find((img) => img.category === 'hero');
    return heroImage?.url || vehicle.images?.[0]?.url;
  };

  if (!isComparing) return null;

  return (
    <AnimatePresence>
      {isComparing && (
        <motion.div
          ref={modalRef}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={handleBackdropClick}
          onKeyDown={handleKeyDown}
          role="dialog"
          aria-modal="true"
          aria-labelledby="comparison-title"
          style={{
            position: 'fixed',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
            padding: '24px',
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(8px)',
          }}
        >
          {/* Modal Content */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            transition={{
              type: 'spring',
              stiffness: 400,
              damping: 30,
            }}
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '1200px',
              maxHeight: '90vh',
              borderRadius: '16px',
              background: 'rgba(255, 255, 255, 0.92)',
              backdropFilter: 'blur(24px)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 24px 64px rgba(0, 0, 0, 0.2)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Header */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <h2
                id="comparison-title"
                style={{
                  margin: 0,
                  fontSize: '24px',
                  fontWeight: 600,
                  color: '#1a1a1a',
                }}
              >
                Vehicle Comparison
              </h2>

              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                {/* Clear All Button */}
                {comparisonList.length > 2 && (
                  <button
                    onClick={clearComparison}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      color: '#dc2626',
                      fontSize: '14px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                    }}
                  >
                    Clear All
                  </button>
                )}

                {/* Close Button */}
                <button
                  onClick={closeComparison}
                  aria-label="Close comparison"
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'rgba(0, 0, 0, 0.05)',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)';
                  }}
                >
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div
              style={{
                padding: '24px',
                overflow: 'auto',
                flex: 1,
              }}
            >
              {/* Loading State */}
              {loading && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '48px',
                    color: '#6b7280',
                  }}
                >
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      border: '4px solid rgba(14, 165, 233, 0.2)',
                      borderTopColor: '#0ea5e9',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                      marginBottom: '16px',
                    }}
                  />
                  <p style={{ margin: 0, fontSize: '16px' }}>
                    Loading comparison data...
                  </p>
                </div>
              )}

              {/* Error State */}
              {error && !loading && (
                <div
                  style={{
                    padding: '24px',
                    borderRadius: '12px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    color: '#dc2626',
                    textAlign: 'center',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '16px' }}>{error}</p>
                </div>
              )}

              {/* Empty State (AC8) */}
              {!loading && !error && !comparisonResult && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '48px 24px',
                    textAlign: 'center',
                    minHeight: '300px',
                  }}
                >
                  {/* Empty State Icon */}
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '50%',
                      background: 'rgba(14, 165, 233, 0.1)',
                      border: '2px solid rgba(14, 165, 233, 0.2)',
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
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      style={{ color: '#0ea5e9' }}
                    >
                      <path d="M9 17H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-4" />
                      <polyline points="9 12 12 15 15 12" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                  </motion.div>

                  {/* Empty State Title */}
                  <h3
                    style={{
                      margin: '0 0 12px 0',
                      fontSize: '20px',
                      fontWeight: 600,
                      color: '#1a1a1a',
                    }}
                  >
                    Add Vehicles to Compare
                  </h3>

                  {/* Empty State Description */}
                  <p
                    style={{
                      margin: '0 0 24px 0',
                      fontSize: '15px',
                      color: '#6b7280',
                      lineHeight: '1.6',
                      maxWidth: '400px',
                    }}
                  >
                    Select 2 or more vehicles from the grid to see a side-by-side comparison of specifications, features, and pricing.
                  </p>

                  {/* Visual Hints */}
                  <div
                    style={{
                      display: 'flex',
                      gap: '16px',
                      marginBottom: '24px',
                      flexWrap: 'wrap',
                      justifyContent: 'center',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 16px',
                        borderRadius: '20px',
                        background: 'rgba(14, 165, 233, 0.1)',
                        border: '1px solid rgba(14, 165, 233, 0.2)',
                        fontSize: '13px',
                        color: '#0c4a6e',
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 6v6l4 2" />
                      </svg>
                      Quick comparison
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 16px',
                        borderRadius: '20px',
                        background: 'rgba(34, 197, 94, 0.1)',
                        border: '1px solid rgba(34, 197, 94, 0.2)',
                        fontSize: '13px',
                        color: '#166534',
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                      </svg>
                      Best value highlights
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 16px',
                        borderRadius: '20px',
                        background: 'rgba(168, 85, 247, 0.1)',
                        border: '1px solid rgba(168, 85, 247, 0.2)',
                        fontSize: '13px',
                        color: '#6b21a8',
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                      Otto's recommendations
                    </div>
                  </div>

                  {/* CTA Button (AC8) */}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={closeComparison}
                    style={{
                      padding: '12px 24px',
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
                      border: 'none',
                      color: 'white',
                      fontSize: '15px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7" />
                      <rect x="14" y="3" width="7" height="7" />
                      <rect x="14" y="14" width="7" height="7" />
                      <rect x="3" y="14" width="7" height="7" />
                    </svg>
                    Browse Vehicles
                  </motion.button>
                </div>
              )}

              {/* Comparison Result */}
              {!loading && !error && comparisonResult && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Otto's Recommendation */}
                  {comparisonResult.recommendation_summary && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{
                        padding: '16px 20px',
                        borderRadius: '12px',
                        background: 'rgba(14, 165, 233, 0.1)',
                        border: '1px solid rgba(14, 165, 233, 0.2)',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px',
                        }}
                      >
                        {/* Otto Avatar Icon */}
                        <div
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontWeight: 700,
                            fontSize: '18px',
                            flexShrink: 0,
                          }}
                        >
                          O
                        </div>

                        {/* Recommendation Text */}
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              fontSize: '14px',
                              fontWeight: 600,
                              color: '#0c4a6e',
                              marginBottom: '4px',
                            }}
                          >
                            Otto's Recommendation
                          </div>
                          <div
                            style={{
                              fontSize: '15px',
                              color: '#1e3a5f',
                              lineHeight: '1.5',
                            }}
                          >
                            {comparisonResult.recommendation_summary}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Comparison Table */}
                  <ComparisonTable comparison={comparisonResult} />

                  {/* Quick Compare Cards */}
                  <div style={{ marginTop: '24px' }}>
                    <h3
                      style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        color: '#1a1a1a',
                        marginBottom: '16px',
                      }}
                    >
                      Quick Remove
                    </h3>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: `repeat(${Math.min(comparisonList.length, 4)}, 1fr)`,
                        gap: '16px',
                      }}
                    >
                      {comparisonList.map((vehicle) => (
                        <motion.button
                          key={vehicle.id}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => removeFromComparison(vehicle.id)}
                          style={{
                            padding: '12px',
                            borderRadius: '12px',
                            background: 'rgba(255, 255, 255, 0.85)',
                            backdropFilter: 'blur(20px)',
                            border: '1px solid rgba(255, 255, 255, 0.18)',
                            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            textAlign: 'left',
                          }}
                        >
                          {getVehicleImage(vehicle.id) && (
                            <img
                              src={getVehicleImage(vehicle.id)}
                              alt={getVehicleTitle(vehicle.id)}
                              style={{
                                width: '100%',
                                height: '80px',
                                objectFit: 'cover',
                                borderRadius: '8px',
                                marginBottom: '8px',
                              }}
                            />
                          )}
                          <div
                            style={{
                              fontSize: '13px',
                              fontWeight: 500,
                              color: '#1a1a1a',
                              marginBottom: '4px',
                            }}
                          >
                            {getVehicleTitle(vehicle.id)}
                          </div>
                          <div
                            style={{
                              fontSize: '12px',
                              color: '#dc2626',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18 6L6 18M6 6l12 12" />
                            </svg>
                            Remove
                          </div>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Add More Vehicles Prompt */}
              {!loading && !error && comparisonList.length < 4 && (
                <div
                  style={{
                    marginTop: '24px',
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'rgba(14, 165, 233, 0.1)',
                    border: '1px solid rgba(14, 165, 233, 0.2)',
                    textAlign: 'center',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '14px', color: '#0c4a6e' }}>
                    You can compare up to 4 vehicles. Add more from the grid to expand your comparison.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div
              style={{
                padding: '16px 24px',
                borderTop: '1px solid rgba(0, 0, 0, 0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '12px',
                color: '#6b7280',
              }}
            >
              <span>
                {comparisonList.length} vehicle{comparisonList.length > 1 ? 's' : ''} selected
              </span>
              <span>
                Press ESC or click outside to close
              </span>
            </div>

            {/* Spinner Animation Keyframes */}
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ComparisonView;
