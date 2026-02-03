import React from 'react';
import { motion } from 'framer-motion';
import { Hand, GitCompare } from 'lucide-react';

interface ModalActionButtonsProps {
  vehicleId: string;
  availabilityStatus?: 'available' | 'reserved' | 'sold';
  onHold?: (vehicleId: string) => void;
  onCompare?: (vehicleId: string) => void;
}

/**
 * ModalActionButtons - Primary action buttons for vehicle detail modal
 *
 * Features:
 * - Hold/Reserve button (primary action)
 * - Add to Compare button
 * - Disabled state for unavailable vehicles
 *
 * AC7: Action buttons (Hold for 24h, Add to Compare)
 *
 * @param props - Component props
 * @returns Modal action buttons component
 */
export const ModalActionButtons: React.FC<ModalActionButtonsProps> = ({
  vehicleId,
  availabilityStatus = 'available',
  onHold,
  onCompare,
}) => {
  const isAvailable = availabilityStatus === 'available';

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap',
      }}
    >
      {/* Hold/Reserve Button */}
      <motion.button
        whileHover={{ scale: isAvailable ? 1.02 : 1 }}
        whileTap={{ scale: isAvailable ? 0.98 : 1 }}
        onClick={() => isAvailable && onHold?.(vehicleId)}
        disabled={!isAvailable}
        style={{
          flex: 1,
          minWidth: '200px',
          padding: '16px 24px',
          borderRadius: '12px',
          background: isAvailable ? '#0EA5E9' : '#ccc',
          color: 'white',
          border: 'none',
          fontSize: '16px',
          fontWeight: 600,
          cursor: isAvailable ? 'pointer' : 'not-allowed',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          opacity: isAvailable ? 1 : 0.6,
          transition: 'all 0.2s ease-out',
        }}
      >
        <Hand size={20} style={{ strokeWidth: 2 }} />
        {availabilityStatus === 'reserved' ? 'Reserved' : availabilityStatus === 'sold' ? 'Sold' : 'Hold for 24h'}
      </motion.button>

      {/* Compare Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onCompare?.(vehicleId)}
        style={{
          padding: '16px 24px',
          borderRadius: '12px',
          background: 'white',
          color: '#0EA5E9',
          border: '2px solid #0EA5E9',
          fontSize: '16px',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          transition: 'all 0.2s ease-out',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = '#0EA5E9';
          e.currentTarget.style.color = 'white';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'white';
          e.currentTarget.style.color = '#0EA5E9';
        }}
      >
        <GitCompare size={20} style={{ strokeWidth: 2 }} />
        Add to Compare
      </motion.button>

      {/* Helper Text */}
      {!isAvailable && (
        <div
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            fontSize: '14px',
            color: '#dc2626',
            textAlign: 'center',
          }}
        >
          {availabilityStatus === 'reserved'
            ? 'This vehicle is currently reserved. Check back soon for availability.'
            : 'This vehicle has been sold. Browse similar vehicles in our inventory.'}
        </div>
      )}

      {isAvailable && (
        <div
          style={{
            width: '100%',
            fontSize: '13px',
            color: '#666',
            textAlign: 'center',
            lineHeight: '1.5',
          }}
        >
          Hold this vehicle for 24 hours with no obligation. We'll contact you to arrange a test drive.
        </div>
      )}
    </div>
  );
};

export default ModalActionButtons;
