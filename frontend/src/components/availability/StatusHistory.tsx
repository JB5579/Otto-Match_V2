import React from 'react';
import { motion } from 'framer-motion';
import { Check, Clock, X, ChevronDown, ChevronUp } from 'lucide-react';
import type { StatusChange } from '../../context/VehicleContext';
import { formatDuration } from '../../lib/availabilityApi';

export interface StatusHistoryProps {
  vehicleId: string;
  history: StatusChange[];
  className?: string;
}

const statusIcons = {
  available: Check,
  reserved: Clock,
  sold: X,
};

const statusColors = {
  available: '#16A34A',
  reserved: '#D97706',
  sold: '#6B7280',
};

/**
 * StatusHistory Component
 *
 * Displays a timeline of vehicle availability status changes.
 *
 * @component
 * @example
 * ```tsx
 * <StatusHistory vehicleId="vehicle-1" history={statusChanges} />
 * ```
 *
 * @param {StatusHistoryProps} props - Component props
 * @param {string} props.vehicleId - Vehicle ID
 * @param {StatusChange[]} props.history - Array of status changes
 * @param {string} props.className - Additional CSS classes
 *
 * Features:
 * - Visual timeline with status icons and colors
 * - Timestamps and duration for each status
 * - Collapse/expand for detailed history
 * - Smooth animations (Framer Motion)
 * - Responsive design
 */
export const StatusHistory: React.FC<StatusHistoryProps> = React.memo(({
  vehicleId,
  history,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // Show most recent 3 by default, expand to show all
  const visibleHistory = isExpanded ? history : history.slice(0, 3);
  const hasMore = history.length > 3;

  if (history.length === 0) {
    return (
      <div className={`status-history ${className}`} style={{ padding: '16px', color: '#9CA3AF' }}>
        No status history available
      </div>
    );
  }

  return (
    <div className={`status-history ${className}`} style={{ padding: '16px' }}>
      <h4 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600, color: '#1F2937' }}>
        Status History
      </h4>

      <div className="timeline" style={{ position: 'relative', paddingLeft: '32px' }}>
        {/* Timeline line */}
        <div
          style={{
            position: 'absolute',
            left: '12px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            background: 'rgba(0, 0, 0, 0.1)',
          }}
        />

        {visibleHistory.map((change, index) => {
          const Icon = statusIcons[change.to_status];
          const color = statusColors[change.to_status];

          return (
            <motion.div
              key={`${change.changed_at}-${index}`}
              className="timeline-item"
              style={{
                position: 'relative',
                marginBottom: '16px',
              }}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              {/* Timeline dot */}
              <div
                style={{
                  position: 'absolute',
                  left: '-26px',
                  top: '2px',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: 'white',
                  border: `2px solid ${color}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={12} color={color} strokeWidth={3} />
              </div>

              {/* Status change details */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: color, textTransform: 'capitalize' }}>
                    {change.to_status}
                  </span>
                  {change.duration_seconds !== undefined && (
                    <span style={{ fontSize: '12px', color: '#6B7280' }}>
                      ({formatDuration(change.duration_seconds)})
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: '#9CA3AF' }}>
                  {new Date(change.changed_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Expand/Collapse button */}
      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          style={{
            marginTop: '8px',
            padding: '6px 12px',
            background: 'transparent',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 600,
            color: '#6B7280',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLButtonElement).style.background = 'rgba(0, 0, 0, 0.05)';
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLButtonElement).style.background = 'transparent';
          }}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Show less history' : 'Show more history'}
        >
          {isExpanded ? (
            <>
              <ChevronUp size={14} />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown size={14} />
              Show More ({history.length - 3} more)
            </>
          )}
        </button>
      )}
    </div>
  );
});

StatusHistory.displayName = 'StatusHistory';

export default StatusHistory;
