/**
 * ConversationDetail Component
 *
 * Displays full conversation dialogue with preference highlights.
 *
 * AC1: Click into conversation to see full dialogue
 * Story: 2-7 (Implement Conversation History and Session Summaries)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Share2, Trash2, Download, MessageCircle } from 'lucide-react';

interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string | null;
  metadata: Record<string, any> | null;
}

interface ConversationDetailProps {
  conversationId: string;
  onBack: () => void;
  className?: string;
}

interface ConversationDetailData {
  id: string;
  user_id: string | null;
  session_id: string;
  zep_conversation_id: string;
  title: string;
  summary: string;
  key_points: string[];
  started_at: string;
  last_message_at: string;
  message_count: number;
  duration_minutes: number;
  preferences: Record<string, any>;
  vehicles_discussed: Array<{
    make: string;
    model: string;
    year: number | null;
    relevance_score: number;
  }>;
  journey_stage: string;
  evolution_detected: boolean;
  evolution_notes: string[];
  status: string;
  retention_days: number;
  expires_at: string | null;
}

interface MessagesResponse {
  conversation_id: string;
  session_id: string;
  messages: ConversationMessage[];
  total_messages: number;
}

export const ConversationDetail: React.FC<ConversationDetailProps> = ({
  conversationId,
  onBack,
  className = ''
}) => {
  const [conversation, setConversation] = useState<ConversationDetailData | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversationDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const sessionId = getSessionId();
      const headers: Record<string, string> = {
        'X-Session-ID': sessionId
      };

      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Fetch conversation detail
      const [detailRes, messagesRes] = await Promise.all([
        fetch(`/api/v1/conversations/history/${conversationId}`, { headers }),
        fetch(`/api/v1/conversations/${conversationId}/messages`, { headers })
      ]);

      if (!detailRes.ok || !messagesRes.ok) {
        throw new Error('Failed to fetch conversation details');
      }

      const detailData: ConversationDetailData = await detailRes.json();
      const messagesData: MessagesResponse = await messagesRes.json();

      setConversation(detailData);
      setMessages(messagesData.messages);

    } catch (err) {
      console.error('Error fetching conversation detail:', err);
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    fetchConversationDetail();
  }, [fetchConversationDetail]);

  const handleExport = async () => {
    try {
      const sessionId = getSessionId();
      const headers: Record<string, string> = {
        'X-Session-ID': sessionId
      };

      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`/api/v1/conversations/export/request`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          export_type: 'json',
          conversation_ids: [conversationId]
        })
      });

      if (!response.ok) {
        throw new Error('Failed to export conversation');
      }

      const data = await response.json();
      // Trigger download
      if (data.download_url) {
        window.open(data.download_url, '_blank');
      }

    } catch (err) {
      console.error('Error exporting conversation:', err);
      alert('Failed to export conversation');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      const sessionId = getSessionId();
      const headers: Record<string, string> = {
        'X-Session-ID': sessionId
      };

      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`/api/v1/conversations/${conversationId}`, {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      onBack(); // Go back to list

    } catch (err) {
      console.error('Error deleting conversation:', err);
      alert('Failed to delete conversation');
    }
  };

  if (loading) {
    return (
      <div className={`conversation-detail ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className={`conversation-detail ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error || 'Conversation not found'}</p>
          <button
            onClick={onBack}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`conversation-detail ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to History</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
            aria-label="Export conversation"
          >
            <Download className="h-5 w-5" />
          </button>
          <button
            onClick={handleDelete}
            className="p-2 text-gray-600 hover:text-red-600 transition-colors"
            aria-label="Delete conversation"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Title and metadata */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{conversation.title}</h1>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>{conversation.date_display}</span>
          <span>•</span>
          <span>{conversation.message_count} messages</span>
          <span>•</span>
          <span>{conversation.duration_minutes.toFixed(0)} min</span>
        </div>
      </motion.div>

      {/* Summary */}
      {conversation.summary && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6"
        >
          <h2 className="text-lg font-semibold text-blue-900 mb-2">Summary</h2>
          <p className="text-blue-800">{conversation.summary}</p>
        </motion.div>
      )}

      {/* Key points */}
      {conversation.key_points && conversation.key_points.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Key Points</h2>
          <ul className="space-y-2">
            {conversation.key_points.map((point, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-600 mt-1">•</span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Preferences */}
      {Object.keys(conversation.preferences).length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Your Preferences</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(conversation.preferences).map(([category, value]) => (
              value && (
                <div key={category} className="bg-gray-50 rounded-lg p-3">
                  <div className="font-medium text-gray-700 capitalize">{category}</div>
                  <div className="text-gray-600 text-sm">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </div>
                </div>
              )
            ))}
          </div>
        </motion.div>
      )}

      {/* Vehicles discussed */}
      {conversation.vehicles_discussed.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Vehicles Discussed</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {conversation.vehicles_discussed.map((vehicle, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-3">
                <div className="font-medium text-gray-900">
                  {vehicle.year} {vehicle.make} {vehicle.model}
                </div>
                <div className="text-sm text-gray-600">
                  Relevance: {Math.round(vehicle.relevance_score * 100)}%
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Messages */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Conversation</h2>

        <div className="space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`
                max-w-[80%] rounded-lg px-4 py-2
                ${message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
                }
              `}>
                <div className="flex items-center gap-2 mb-1">
                  <MessageCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    {message.role === 'user' ? 'You' : 'Otto'}
                  </span>
                </div>
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.created_at && (
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(message.created_at).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
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

export default ConversationDetail;
