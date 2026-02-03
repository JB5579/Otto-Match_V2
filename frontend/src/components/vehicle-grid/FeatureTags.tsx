import React from 'react';

interface FeatureTagsProps {
  features: string[];
  maxTags?: number;
  compact?: boolean;
}

const FeatureTags: React.FC<FeatureTagsProps> = ({
  features,
  maxTags = 5,
  compact = false,
}) => {
  const displayTags = features.slice(0, maxTags);
  const remainingCount = features.length - maxTags;

  if (displayTags.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: compact ? '4px' : '6px',
        margin: compact ? '8px 0' : '12px 0',
      }}
    >
      {displayTags.map((feature, index) => (
        <span
          key={index}
          style={{
            display: 'inline-block',
            padding: compact ? '3px 8px' : '4px 10px',
            borderRadius: '12px',
            background: 'rgba(14, 165, 233, 0.1)',
            border: '1px solid rgba(14, 165, 233, 0.2)',
            color: '#0369a1',
            fontSize: compact ? '11px' : '12px',
            fontWeight: 500,
            whiteSpace: 'nowrap',
          }}
        >
          {feature}
        </span>
      ))}

      {remainingCount > 0 && (
        <span
          style={{
            display: 'inline-block',
            padding: compact ? '3px 8px' : '4px 10px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.04)',
            color: '#666',
            fontSize: compact ? '11px' : '12px',
            fontWeight: 500,
          }}
        >
          +{remainingCount} more
        </span>
      )}
    </div>
  );
};

export default React.memo(FeatureTags);
