/**
 * ConversationHistory Component
 *
 * Displays a chronological list of user's conversations with Otto AI.
 * Supports both authenticated users and guest users (session-based).
 *
 * AC1: Chronological Conversation List
 * AC3: Guest User Access (Session-Based History)
 *
 * Story: 2-7 (Implement Conversation History and Session Summaries)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Calendar, MessageCircle, Trash2, Download, Filter } from 'lucide-react';

// Types
interface ConversationItem {
  id: string;
  user_id: string | null;
  session_id: string;
  title: string;
  summary: string | null;
  started_at: string;
  last_message_at: string;
  message_count: number;
  journey_stage: string;
  evolution_detected: boolean;
  top_preferences: Array<{category: string; key: string; value: any}> | null;
  vehicles_mentioned_count: number;
  retention_days: number;
  expires_at: string | null;
  date_display: string;
  message_count_display: string;
}

interface ConversationHistoryResponse {
  conversations: ConversationItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ConversationHistoryProps {
  onSelectConversation?: (conversationId: string) => void;
  className?: string;
}

// Helper to format journey stage
const formatJourneyStage = (stage: string): string => {
  const stageMap: Record<string, string> = {
    discovery: 'Discovery',
    consideration: 'Comparing Options',
    decision: 'Narrowing Down',
    purchased: 'Purchased'
  };
  return stageMap[stage] || stage;
};

// Helper to get journey stage color
const getJourneyStageColor = (stage: string): string => {
  const colorMap: Record<string, string> = {
    discovery: 'bg-blue-100 text-blue-700',
    consideration: 'bg-purple-100 text-purple-700',
    decision: 'bg-orange-100 text-orange-700',
    purchased: 'bg-green-100 text-green-700'
  };
  return colorMap[stage] || 'bg-gray-100 text-gray-700';
};

export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  onSelectConversation,
  className = ''
}) => {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  // Fetch conversations
  const fetchConversations = useCallback(async (pageNum: number = 1, query: string = '') => {
    try {
      setLoading(true);
      setError(null);

      // Build query params
      const params = new URLSearchParams({
        page: pageNum.toString(),
        page_size: '20'
      });

      if (query) {
        params.append('query', query);
      }

      // Get session ID from cookie
      const sessionId = getSessionId();

      const headers: Record<string, string> = {
        'X-Session-ID': sessionId
      };

      // Add auth token if available
      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`/api/v1/conversations/history?${params}`, {
        headers
      });

      if (!response.ok) {
        throw new Error('Failed to fetch conversations');
      }

      const data: ConversationHistoryResponse = await response.json();

      setConversations(data.conversations);
      setTotal(data.total);
      setPage(data.page);

    } catch (err) {
      console.error('Error fetching conversations:', err);
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
      setConversations([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    setPage(1); // Reset to first page
    fetchConversations(1, query);
  }, [fetchConversations]);

  // Handle conversation selection
  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversation(conversationId);
    if (onSelectConversation) {
      onSelectConversation(conversationId);
    }
  };

  // Handle delete
  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();

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

      // Refresh list
      await fetchConversations(page, searchQuery);

    } catch (err) {
      console.error('Error deleting conversation:', err);
      alert('Failed to delete conversation');
    }
  };

  if (loading) {
    return (
      <div className={`conversation-history ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading conversations...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`conversation-history ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => fetchConversations()}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className={`conversation-history ${className}`}>
        <div className="text-center p-8">
          <MessageCircle className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No conversations yet</h3>
          <p className="text-gray-600">Start chatting with Otto to see your conversation history here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`conversation-history ${className}`}>
      {/* Header with search */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Conversations</h2>

        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Results count */}
        <p className="mt-2 text-sm text-gray-600">
          {total} conversation{total !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Conversation list */}
      <div className="space-y-4">
        <AnimatePresence>
          {conversations.map((conversation, index) => (
            <motion.div
              key={conversation.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => handleSelectConversation(conversation.id)}
              className={`
                border rounded-lg p-4 cursor-pointer transition-all
                ${selectedConversation === conversation.id
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }
              `}
            >
              {/* Conversation header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold text-gray-900">{conversation.title}</h3>
                    <span className={`
                      px-2 py-1 rounded-full text-xs font-medium
                      ${getJourneyStageColor(conversation.journey_stage)}
                    `}>
                      {formatJourneyStage(conversation.journey_stage)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{conversation.date_display}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle export
                    }}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    aria-label="Export conversation"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(conversation.id, e)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Summary */}
              {conversation.summary && (
                <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                  {conversation.summary}
                </p>
              )}

              {/* Metadata */}
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <MessageCircle className="h-4 w-4" />
                  <span>{conversation.message_count_display}</span>
                </div>

                {conversation.vehicles_mentioned_count > 0 && (
                  <div className="flex items-center gap-1">
                    <span>🚗</span>
                    <span>{conversation.vehicles_mentioned_count} vehicle{conversation.vehicles_mentioned_count !== 1 ? 's' : ''}</span>
                  </div>
                )}

                {conversation.evolution_detected && (
                  <div className="flex items-center gap-1">
                    <span>🔄</span>
                    <span>Preferences evolved</span>
                  </div>
                )}
              </div>

              {/* Top preferences */}
              {conversation.top_preferences && conversation.top_preferences.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {conversation.top_preferences.slice(0, 3).map((pref, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                    >
                      {pref.category}: {String(pref.value)}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => fetchConversations(page - 1, searchQuery)}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>

          <span className="text-gray-600">
            Page {page} of {Math.ceil(total / 20)}
          </span>

          <button
            onClick={() => fetchConversations(page + 1, searchQuery)}
            disabled={page >= Math.ceil(total / 20)}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

// Helper functions
function getSessionId(): string {
  // Get session ID from cookie
  const match = document.cookie.match(/otto_session_id=([^;]+)/);
  return match ? match[1] : '';
}

function getAuthToken(): string | null {
  // Get auth token from localStorage or cookie
  const token = localStorage.getItem('auth_token');
  if (token) return token;

  const match = document.cookie.match(/auth_token=([^;]+)/);
  return match ? match[1] : null;
}

export default ConversationHistory;
