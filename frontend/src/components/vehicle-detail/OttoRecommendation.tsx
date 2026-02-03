import React from 'react';
import { Sparkles } from 'lucide-react';

interface OttoRecommendationProps {
  recommendation?: string;
  matchScore?: number;
}

/**
 * OttoRecommendation - Display Otto's personalized recommendation
 *
 * Features:
 * - Prominent match score display
 * - Otto's reasoning in styled box
 * - Visual distinction for high matches (95%+)
 *
 * AC5: Otto's recommendation display
 *
 * @param props - Component props
 * @returns Otto recommendation component
 */
export const OttoRecommendation: React.FC<OttoRecommendationProps> = ({
  recommendation,
  matchScore = 0,
}) => {
  if (!recommendation && matchScore === 0) {
    return null;
  }

  const isOttoPick = matchScore >= 95;
  const matchTier = getMatchTier(matchScore);
  const matchColor = getMatchColor(matchTier);

  return (
    <div
      style={{
        padding: '24px',
        borderRadius: '16px',
        background: isOttoPick
          ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%)'
          : 'rgba(14, 165, 233, 0.08)',
        border: isOttoPick
          ? '2px solid rgba(14, 165, 233, 0.3)'
          : '1px solid rgba(14, 165, 233, 0.2)',
      }}
    >
      {/* Header with Match Score */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <Sparkles
            size={24}
            color={matchColor}
            style={{ strokeWidth: 2 }}
          />
          <h4
            style={{
              fontSize: '18px',
              fontWeight: 600,
              color: '#1a1a1a',
              margin: 0,
            }}
          >
            {isOttoPick ? "Otto's Top Pick" : "Otto's Recommendation"}
          </h4>
        </div>

        {matchScore > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '20px',
              background: matchColor,
              color: 'white',
              fontSize: '20px',
              fontWeight: 700,
            }}
          >
            {matchScore}%
            <span
              style={{
                fontSize: '12px',
                fontWeight: 500,
                opacity: 0.9,
              }}
            >
              Match
            </span>
          </div>
        )}
      </div>

      {/* Recommendation Text */}
      {recommendation && (
        <div
          style={{
            fontSize: '16px',
            lineHeight: '1.6',
            color: '#333',
            fontStyle: 'italic',
          }}
        >
          "{recommendation}"
        </div>
      )}

      {/* Match Tier Badge */}
      {matchScore > 0 && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.6)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
            fontSize: '14px',
            color: '#666',
          }}
        >
          <strong style={{ color: matchColor }}>
            {matchTier === 'excellent' && 'Excellent Match'}
            {matchTier === 'good' && 'Great Match'}
            {matchTier === 'fair' && 'Good Match'}
            {matchTier === 'low' && 'Fair Match'}
          </strong>
          {matchTier === 'excellent' && ' - This vehicle aligns perfectly with your preferences.'}
          {matchTier === 'good' && ' - This vehicle matches most of your criteria.'}
          {matchTier === 'fair' && ' - This vehicle has some of what you\'re looking for.'}
          {matchTier === 'low' && ' - Consider exploring other options first.'}
        </div>
      )}
    </div>
  );
};

function getMatchTier(score: number): 'excellent' | 'good' | 'fair' | 'low' {
  if (score >= 95) return 'excellent';
  if (score >= 80) return 'good';
  if (score >= 60) return 'fair';
  return 'low';
}

function getMatchColor(tier: string): string {
  switch (tier) {
    case 'excellent':
      return '#22c55e'; // green
    case 'good':
      return '#0EA5E9'; // blue
    case 'fair':
      return '#f59e0b'; // amber
    case 'low':
      return '#ef4444'; // red
    default:
      return '#0EA5E9';
  }
}

export default OttoRecommendation;
