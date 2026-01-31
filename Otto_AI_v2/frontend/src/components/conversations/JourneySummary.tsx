/**
 * JourneySummary Component
 *
 * Displays user's vehicle discovery journey with visual dashboard,
 * top categories, preference evolution timeline, and recommended next steps.
 *
 * AC2: Journey Summary
 * Story: 2-7 (Implement Conversation History and Session Summaries)
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Calendar, MessageCircle, Target, ArrowRight } from 'lucide-react';

interface JourneySummaryData {
  identifier: string;
  user_id: string | null;
  first_conversation: string | null;
  last_conversation: string | null;
  total_conversations: number;
  total_messages: number;
  stages_visited: string[];
  current_stage: string;
  all_vehicles_discussed: Array<{
    make: string;
    model: string;
    year?: number;
  }>;
  active_preferences: Array<{
    category: string;
    key: string;
    value: any;
    confidence: number;
    last_confirmed: string;
  }>;
  preferences_evolved: boolean;
}

interface JourneySummaryProps {
  className?: string;
}

const STAGE_ORDER = ['discovery', 'consideration', 'decision', 'purchased'];

const STAGE_LABELS: Record<string, string> = {
  discovery: 'Discovery',
  consideration: 'Considering Options',
  decision: 'Making Decision',
  purchased: 'Purchased'
};

const STAGE_COLORS: Record<string, string> = {
  discovery: 'bg-blue-500',
  consideration: 'bg-purple-500',
  decision: 'bg-orange-500',
  purchased: 'bg-green-500'
};

export const JourneySummary: React.FC<JourneySummaryProps> = ({ className = '' }) => {
  const [journeyData, setJourneyData] = useState<JourneySummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJourneySummary();
  }, []);

  const fetchJourneySummary = async () => {
    try {
      setLoading(true);

      const sessionId = getSessionId();
      const headers: Record<string, string> = {
        'X-Session-ID': sessionId
      };

      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/v1/conversations/summary', { headers });

      if (!response.ok) {
        throw new Error('Failed to fetch journey summary');
      }

      const data: JourneySummaryData = await response.json();
      setJourneyData(data);

    } catch (err) {
      console.error('Error fetching journey summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to load journey summary');
    } finally {
      setLoading(false);
    }
  };

  const getNextSteps = (): string[] => {
    if (!journeyData) return [];

    const currentStageIdx = STAGE_ORDER.indexOf(journeyData.current_stage);
    const nextStage = STAGE_ORDER[currentStageIdx + 1];

    const steps: Record<string, string[]> = {
      discovery: [
        'Refine your vehicle preferences',
        'Set a budget range',
        'Compare different vehicle types'
      ],
      consideration: [
        'Test drive top contenders',
        'Compare ownership costs',
        'Check dealer inventory'
      ],
      decision: [
        'Schedule final test drive',
        'Review financing options',
        'Make your purchase'
      ],
      purchased: [
        'Leave a review',
        'Share your experience',
        'Explore accessories'
      ]
    };

    return steps[nextStage] || [];
  };

  if (loading) {
    return (
      <div className={`journey-summary ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`journey-summary ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!journeyData || journeyData.total_conversations === 0) {
    return (
      <div className={`journey-summary ${className}`}>
        <div className="text-center p-8">
          <Target className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Start your journey</h3>
          <p className="text-gray-600">Chat with Otto to begin your vehicle discovery journey.</p>
        </div>
      </div>
    );
  }

  const nextSteps = getNextSteps();

  return (
    <div className={`journey-summary ${className}`}>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Journey</h2>

      {/* Stats overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
      >
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageCircle className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Conversations</span>
          </div>
          <div className="text-3xl font-bold text-blue-600">{journeyData.total_conversations}</div>
          <div className="text-sm text-blue-700">total conversations</div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-5 w-5 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">Messages</span>
          </div>
          <div className="text-3xl font-bold text-purple-600">{journeyData.total_messages}</div>
          <div className="text-sm text-purple-700">messages exchanged</div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="h-5 w-5 text-green-600" />
            <span className="text-sm font-medium text-green-900">Active Since</span>
          </div>
          <div className="text-lg font-bold text-green-600">
            {journeyData.first_conversation
              ? new Date(journeyData.first_conversation).toLocaleDateString()
              : 'N/A'}
          </div>
        </div>
      </motion.div>

      {/* Journey stage timeline */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Progress</h3>

        <div className="relative">
          {/* Progress line */}
          <div className="absolute top-4 left-0 right-0 h-1 bg-gray-200 -z-10"></div>

          {/* Stages */}
          <div className="flex justify-between relative">
            {STAGE_ORDER.map((stage, idx) => {
              const visited = journeyData.stages_visited.includes(stage);
              const isCurrent = stage === journeyData.current_stage;

              return (
                <div key={stage} className="flex flex-col items-center">
                  <div className={`
                    w-8 h-8 rounded-full border-2 flex items-center justify-center
                    ${visited
                      ? `${STAGE_COLORS[stage]} border-transparent`
                      : 'bg-gray-100 border-gray-300'
                    }
                    ${isCurrent ? 'ring-4 ring-opacity-50 ring-blue-200' : ''}
                  `}>
                    {visited && (
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className={`
                    mt-2 text-xs font-medium text-center w-20
                    ${visited ? 'text-gray-900' : 'text-gray-400'}
                  `}>
                    {STAGE_LABELS[stage]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* Vehicles discussed */}
      {journeyData.all_vehicles_discussed.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-8"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vehicles You've Considered</h3>

          <div className="flex flex-wrap gap-2">
            {journeyData.all_vehicles_discussed.slice(0, 10).map((vehicle, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {vehicle.year && `${vehicle.year} `}
                {vehicle.make} {vehicle.model}
              </span>
            ))}
            {journeyData.all_vehicles_discussed.length > 10 && (
              <span className="px-3 py-1 text-gray-500 text-sm">
                +{journeyData.all_vehicles_discussed.length - 10} more
              </span>
            )}
          </div>
        </motion.div>
      )}

      {/* Active preferences */}
      {journeyData.active_preferences.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-8"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What We've Learned</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {journeyData.active_preferences.slice(0, 6).map((pref, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-600 capitalize">{pref.category}</div>
                <div className="font-medium text-gray-900">{String(pref.value)}</div>
                {pref.confidence && (
                  <div className="text-xs text-gray-500 mt-1">
                    Confidence: {Math.round(pref.confidence * 100)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Evolution indicator */}
      {journeyData.preferences_evolved && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-8 bg-green-50 border border-green-200 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-900">Your Preferences Have Evolved</span>
          </div>
          <p className="text-green-800 text-sm">
            We noticed that your vehicle preferences have changed throughout your conversations.
            This is completely normal as you learn more about what's available!
          </p>
        </motion.div>
      )}

      {/* Recommended next steps */}
      {nextSteps.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Next Steps</h3>

          <div className="space-y-2">
            {nextSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <ArrowRight className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <span className="text-gray-700">{step}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

// Helper functions
function getSessionId(): string {
  const match = document.cookie.match(/otto_session_id=([^;]+)/);
  return match ? match[1] : '';
}

function getAuthToken(): string | null {
  const token = localStorage.getItem('auth_token');
  if (token) return token;

  const match = document.cookie.match(/auth_token=([^;]+)/);
  return match ? match[1] : null;
}

export default JourneySummary;
