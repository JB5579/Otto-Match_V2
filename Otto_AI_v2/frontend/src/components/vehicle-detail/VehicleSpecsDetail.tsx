import React from 'react';
import type { Vehicle } from '../../app/types/api';

interface VehicleSpecsDetailProps {
  vehicle: Vehicle;
}

interface SpecItem {
  label: string;
  value: string | undefined;
  icon: string;
}

/**
 * VehicleSpecsDetail - Detailed vehicle specifications display
 *
 * Features:
 * - Organized spec sections (Engine, Performance, Interior, Exterior)
 * - Icon-based visual presentation
 * - Responsive grid layout
 * - Highlighting key differentiators
 *
 * AC4: Vehicle specifications and details display
 *
 * @param props - Component props
 * @returns Vehicle specs detail component
 */
export const VehicleSpecsDetail: React.FC<VehicleSpecsDetailProps> = ({
  vehicle,
}) => {
  const engineSpecs: SpecItem[] = [
    { label: 'Transmission', value: vehicle.transmission, icon: '⚙️' },
    { label: 'Drivetrain', value: vehicle.drivetrain, icon: '🔄' },
    { label: 'Fuel Type', value: vehicle.fuel_type, icon: '⛽' },
  ];

  if (vehicle.range !== undefined) {
    engineSpecs.push({ label: 'Range', value: `${vehicle.range} mi`, icon: '🔋' });
  }

  const vehicleSpecs: SpecItem[] = [
    { label: 'Body Type', value: vehicle.body_type, icon: '🚗' },
    { label: 'Color', value: vehicle.color, icon: '🎨' },
    { label: 'Condition', value: vehicle.condition, icon: '✨' },
    { label: 'Trim', value: vehicle.trim, icon: '🏷️' },
  ];

  const specs = [
    { category: 'Engine & Performance', items: engineSpecs },
    { category: 'Vehicle Details', items: vehicleSpecs },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
      }}
    >
      {specs.map((section) => (
        <div key={section.category}>
          <h4
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: '#1a1a1a',
              margin: '0 0 16px 0',
              paddingBottom: '8px',
              borderBottom: '2px solid #f0f0f0',
            }}
          >
            {section.category}
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            {section.items.map((item, index) => (
              <div
                key={index}
                style={{
                  padding: '16px',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.5)',
                  border: '1px solid rgba(0, 0, 0, 0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <span
                  style={{
                    fontSize: '24px',
                    flexShrink: 0,
                  }}
                >
                  {item.icon}
                </span>
                <div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: '#666',
                      marginBottom: '4px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {item.label}
                  </div>
                  <div
                    style={{
                      fontSize: '16px',
                      fontWeight: 500,
                      color: '#1a1a1a',
                    }}
                  >
                    {item.value || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Mileage Highlight */}
      {vehicle.mileage !== undefined && (
        <div
          style={{
            padding: '20px',
            borderRadius: '12px',
            background: 'rgba(14, 165, 233, 0.1)',
            border: '1px solid rgba(14, 165, 233, 0.2)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '16px',
            }}
          >
            <div>
              <div
                style={{
                  fontSize: '12px',
                  color: '#0c4a6e',
                  marginBottom: '4px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Mileage
              </div>
              <div
                style={{
                  fontSize: '28px',
                  fontWeight: 700,
                  color: '#0c4a6e',
                }}
              >
                {vehicle.mileage.toLocaleString()}
                <span
                  style={{
                    fontSize: '16px',
                    fontWeight: 400,
                    marginLeft: '4px',
                  }}
                >
                  miles
                </span>
              </div>
            </div>
            <div
              style={{
                fontSize: '14px',
                color: '#0c4a6e',
              }}
            >
              {vehicle.mileage < 30000
                ? 'Low mileage - excellent condition'
                : vehicle.mileage < 60000
                ? 'Average mileage for this year'
                : 'Higher mileage - priced accordingly'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleSpecsDetail;
