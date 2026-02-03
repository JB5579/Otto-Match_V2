import React from 'react';
import { DollarSign, TrendingDown } from 'lucide-react';

interface PricingPanelProps {
  price?: number;
  originalPrice?: number;
  savings?: number;
  availabilityStatus?: 'available' | 'reserved' | 'sold';
}

/**
 * PricingPanel - Display pricing information with discount highlights
 *
 * Features:
 * - Current price prominent display
 * - Original price strikethrough if discount
 * - Savings amount highlighted
 * - Availability status
 *
 * AC4: Pricing information display
 *
 * @param props - Component props
 * @returns Pricing panel component
 */
export const PricingPanel: React.FC<PricingPanelProps> = ({
  price,
  originalPrice,
  savings,
  availabilityStatus = 'available',
}) => {
  if (price === undefined) {
    return null;
  }

  const hasDiscount = originalPrice !== undefined && originalPrice > price;
  const discountPercent = hasDiscount
    ? Math.round(((originalPrice! - price) / originalPrice!) * 100)
    : 0;

  const getStatusColor = () => {
    switch (availabilityStatus) {
      case 'sold':
        return { background: '#dc2626', color: 'white' };
      case 'reserved':
        return { background: '#f59e0b', color: 'white' };
      default:
        return { background: '#22c55e', color: 'white' };
    }
  };

  const statusStyle = getStatusColor();

  return (
    <div
      style={{
        padding: '20px',
        borderRadius: '12px',
        background: 'rgba(255, 255, 255, 0.6)',
        border: '1px solid rgba(0, 0, 0, 0.08)',
      }}
    >
      {/* Availability Status */}
      {availabilityStatus !== 'available' && (
        <div
          style={{
            display: 'inline-block',
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '13px',
            fontWeight: 600,
            textTransform: 'lowercase',
            letterSpacing: '0.5px',
            marginBottom: '16px',
            ...statusStyle,
          }}
        >
          {availabilityStatus}
        </div>
      )}

      {/* Price Display */}
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        {/* Current Price */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <DollarSign
            size={28}
            color="#0EA5E9"
            style={{ strokeWidth: 2.5 }}
          />
          <span
            style={{
              fontSize: '42px',
              fontWeight: 700,
              color: '#1a1a1a',
              letterSpacing: '-1px',
            }}
          >
            {price.toLocaleString()}
          </span>
        </div>

        {/* Original Price (if discount) */}
        {hasDiscount && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div
              style={{
                fontSize: '20px',
                color: '#999',
                textDecoration: 'line-through',
                fontWeight: 400,
              }}
            >
              ${originalPrice?.toLocaleString()}
            </div>
            <div
              style={{
                fontSize: '14px',
                color: '#22c55e',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <TrendingDown size={16} />
              Save {discountPercent}%
            </div>
          </div>
        )}
      </div>

      {/* Savings Highlight */}
      {hasDiscount && savings !== undefined && savings > 0 && (
        <div
          style={{
            marginTop: '16px',
            padding: '14px',
            borderRadius: '8px',
            background: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <TrendingDown
            size={20}
            color="#166534"
            style={{ strokeWidth: 2.5 }}
          />
          <div>
            <div
              style={{
                fontSize: '13px',
                color: '#166534',
                marginBottom: '2px',
              }}
            >
              You save
            </div>
            <div
              style={{
                fontSize: '20px',
                fontWeight: 700,
                color: '#166534',
              }}
            >
              ${savings.toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Market Position Text */}
      <div
        style={{
          marginTop: '16px',
          fontSize: '14px',
          color: '#666',
          lineHeight: '1.5',
        }}
      >
        {hasDiscount ? (
          <span>
            This vehicle is priced <strong>${savings?.toLocaleString()}</strong> below market value.
            Act fast — great deals like this don't last long!
          </span>
        ) : (
          <span>
            Fair market pricing based on current inventory and demand.
          </span>
        )}
      </div>
    </div>
  );
};

export default PricingPanel;
