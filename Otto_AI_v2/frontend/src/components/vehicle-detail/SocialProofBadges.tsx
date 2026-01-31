import React from 'react';
import { Eye, Hand, Clock } from 'lucide-react';

interface SocialProofBadgesProps {
  currentViewers?: number;
  offers?: number;
  reservations?: number;
  daysListed?: number;
}

/**
 * SocialProofBadges - Display social proof and urgency indicators
 *
 * Features:
 * - Current viewers count
 * - Active offers indicator
 * - Reservation count
 * - Days on market
 *
 * AC6: Social proof and availability display
 *
 * @param props - Component props
 * @returns Social proof badges component
 */
export const SocialProofBadges: React.FC<SocialProofBadgesProps> = ({
  currentViewers = 0,
  offers = 0,
  reservations = 0,
  daysListed,
}) => {
  const badges = [];

  // Current Viewers
  if (currentViewers > 0) {
    badges.push({
      icon: <Eye size={16} color="#22c55e" />,
      text: `${currentViewers} viewing`,
      variant: 'success' as const,
      pulsing: true,
    });
  }

  // Active Offers
  if (offers > 0) {
    badges.push({
      icon: <Hand size={16} color="#f59e0b" />,
      text: `${offers} offer${offers > 1 ? 's' : ''}`,
      variant: 'warning' as const,
      pulsing: false,
    });
  }

  // Reservations
  if (reservations > 0) {
    badges.push({
      icon: <Clock size={16} color="#0EA5E9" />,
      text: `${reservations} reserved`,
      variant: 'info' as const,
      pulsing: false,
    });
  }

  // Days Listed
  if (daysListed !== undefined && daysListed > 0) {
    badges.push({
      icon: <Clock size={16} color="#666" />,
      text: `Listed ${daysListed} day${daysListed > 1 ? 's' : ''} ago`,
      variant: 'neutral' as const,
      pulsing: false,
    });
  }

  if (badges.length === 0) {
    return null;
  }

  const getBadgeStyle = (variant: string) => {
    switch (variant) {
      case 'success':
        return {
          background: 'rgba(34, 197, 94, 0.1)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
          color: '#166534',
        };
      case 'warning':
        return {
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#b45309',
        };
      case 'info':
        return {
          background: 'rgba(14, 165, 233, 0.1)',
          border: '1px solid rgba(14, 165, 233, 0.3)',
          color: '#0c4a6e',
        };
      default:
        return {
          background: 'rgba(0, 0, 0, 0.05)',
          border: '1px solid rgba(0, 0, 0, 0.1)',
          color: '#333',
        };
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      {badges.map((badge, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            borderRadius: '20px',
            fontSize: '13px',
            fontWeight: 500,
            ...getBadgeStyle(badge.variant),
          }}
        >
          {badge.pulsing && (
            <span
              style={{
                position: 'relative',
                display: 'inline-flex',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  borderRadius: '50%',
                  background: '#22c55e',
                  opacity: 0.5,
                  animation: 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
                }}
              />
              {badge.icon}
            </span>
          )}
          {!badge.pulsing && badge.icon}
          <span>{badge.text}</span>
        </div>
      ))}

      <style>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default SocialProofBadges;
