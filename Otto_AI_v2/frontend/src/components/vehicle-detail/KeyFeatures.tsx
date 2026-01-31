import React from 'react';
import { Check } from 'lucide-react';

interface KeyFeaturesProps {
  features?: string[];
  maxDisplay?: number;
}

/**
 * KeyFeatures - Display vehicle features with visual emphasis
 *
 * Features:
 * - Organized feature list with checkmarks
 * - Truncation with "show more" option
 * - Categorized display if possible
 *
 * AC4: Vehicle features display
 *
 * @param props - Component props
 * @returns Key features component
 */
export const KeyFeatures: React.FC<KeyFeaturesProps> = ({
  features = [],
  maxDisplay = 10,
}) => {
  const [showAll, setShowAll] = React.useState(false);
  const displayFeatures = showAll ? features : features.slice(0, maxDisplay);

  if (!features || features.length === 0) {
    return null;
  }

  return (
    <div>
      <h4
        style={{
          fontSize: '18px',
          fontWeight: 600,
          color: '#1a1a1a',
          margin: '0 0 16px 0',
        }}
      >
        Key Features
      </h4>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
          gap: '12px',
        }}
      >
        {displayFeatures.map((feature, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.5)',
              border: '1px solid rgba(0, 0, 0, 0.05)',
              fontSize: '14px',
              color: '#333',
            }}
          >
            <Check
              size={18}
              color="#0EA5E9"
              style={{ flexShrink: 0, strokeWidth: 3 }}
            />
            <span>{feature}</span>
          </div>
        ))}
      </div>

      {features.length > maxDisplay && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          style={{
            marginTop: '16px',
            padding: '10px 20px',
            borderRadius: '8px',
            background: 'transparent',
            border: '1px solid #0EA5E9',
            color: '#0EA5E9',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.2s ease-out',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#0EA5E9';
            e.currentTarget.style.color = 'white';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = '#0EA5E9';
          }}
        >
          Show {features.length - maxDisplay} more features
        </button>
      )}
    </div>
  );
};

export default KeyFeatures;
