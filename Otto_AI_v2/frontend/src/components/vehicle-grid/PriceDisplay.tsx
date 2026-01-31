import React from 'react';

interface PriceDisplayProps {
  price: number;
  originalPrice?: number;
  savings?: number;
  compact?: boolean;
}

const PriceDisplay: React.FC<PriceDisplayProps> = ({
  price,
  originalPrice,
  savings,
  compact = false,
}) => {
  const formatPrice = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatSavings = (amount: number): string => {
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(1)}k below market`;
    }
    return `$${amount.toLocaleString()} below market`;
  };

  return (
    <div
      style={{
        margin: compact ? '8px 0' : '12px 0',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '8px',
          flexWrap: 'wrap',
        }}
      >
        {/* Main Price */}
        <span
          style={{
            fontSize: compact ? '20px' : '24px',
            fontWeight: 700,
            color: '#0EA5E9',
            lineHeight: 1,
          }}
        >
          {formatPrice(price)}
        </span>

        {/* Original Price (strikethrough) */}
        {originalPrice && originalPrice > price && (
          <span
            style={{
              fontSize: compact ? '14px' : '16px',
              fontWeight: 500,
              color: '#999',
              textDecoration: 'line-through',
              lineHeight: 1,
            }}
          >
            {formatPrice(originalPrice)}
          </span>
        )}
      </div>

      {/* Savings Callout */}
      {savings !== undefined && savings > 0 && (
        <div
          style={{
            display: 'inline-block',
            padding: '4px 10px',
            borderRadius: '12px',
            background: 'rgba(34, 197, 94, 0.15)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            color: '#16a34a',
            fontSize: compact ? '11px' : '12px',
            fontWeight: 600,
            alignSelf: 'flex-start',
          }}
        >
          🎉 {formatSavings(savings)}
        </div>
      )}
    </div>
  );
};

export default React.memo(PriceDisplay);
