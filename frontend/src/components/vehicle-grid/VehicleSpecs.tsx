import React from 'react';

interface VehicleSpecsProps {
  mileage: number;
  transmission?: string;
  drivetrain?: string;
  fuelType?: string;
  range?: number; // For EVs
  compact?: boolean;
}

const VehicleSpecs: React.FC<VehicleSpecsProps> = ({
  mileage,
  transmission,
  drivetrain,
  fuelType,
  range,
  compact = false,
}) => {
  const formatMileage = (miles: number): string => {
    if (miles >= 1000) {
      return `${(miles / 1000).toFixed(1)}k miles`;
    }
    return `${miles.toLocaleString()} miles`;
  };

  const specs = [
    { label: formatMileage(mileage), icon: '🚗' },
    transmission && { label: transmission, icon: '⚙️' },
    drivetrain && { label: drivetrain, icon: '🔄' },
    fuelType && { label: fuelType, icon: '⛽' },
    range && { label: `${range} mi range`, icon: '🔋' },
  ].filter(Boolean) as Array<{ label: string; icon: string }>;

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: compact ? '6px' : '8px',
        margin: compact ? '8px 0' : '12px 0',
      }}
    >
      {specs.map((spec, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: compact ? '4px 8px' : '6px 10px',
            borderRadius: '6px',
            background: 'rgba(0, 0, 0, 0.04)',
            fontSize: compact ? '12px' : '13px',
            color: '#4a4a4a',
            fontWeight: 500,
          }}
        >
          <span role="img" aria-label={spec.label} style={{ fontSize: compact ? '12px' : '14px' }}>
            {spec.icon}
          </span>
          <span>{spec.label}</span>
        </div>
      ))}
    </div>
  );
};

export default React.memo(VehicleSpecs);
