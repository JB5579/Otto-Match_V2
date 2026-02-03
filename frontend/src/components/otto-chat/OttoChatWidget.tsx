import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useConversation } from '../../context/ConversationContext';

export interface OttoChatWidgetProps {
  initialExpanded?: boolean;
  position?: 'bottom-right' | 'bottom-left';
}

/**
 * OttoChatWidget - Floating chat interface for Otto AI conversation
 *
 * Features:
 * - Expandable from FAB (Floating Action Button) to full panel
 * - Message list with auto-scroll
 * - Message input with send button
 * - Typing indicator during Otto responses
 * - Connection status indicator
 * - Glass-morphism design
 * - Smooth animations with Framer Motion
 *
 * Integration:
 * - Uses ConversationContext for WebSocket messaging
 * - Triggers vehicle updates via preference extraction
 * - Real-time bi-directional communication
 *
 * @param props - Component props
 * @returns Floating chat widget
 */
export const OttoChatWidget: React.FC<OttoChatWidgetProps> = ({
  initialExpanded = false,
  position = 'bottom-right',
}) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [inputValue, setInputValue] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    isConnected,
    isLoading,
    error,
    sendMessage,
    reconnect,
    clearError,
  } = useConversation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isExpanded && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isExpanded]);

  // Focus input when expanded
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleSend = () => {
    if (!inputValue.trim() || !isConnected) return;

    sendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const positionStyles = position === 'bottom-right'
    ? { bottom: '24px', right: '24px' }
    : { bottom: '24px', left: '24px' };

  return (
    <>
      {/* FAB (Collapsed State) */}
      <AnimatePresence>
        {!isExpanded && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsExpanded(true)}
            style={{
              position: 'fixed',
              ...positionStyles,
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
              border: 'none',
              boxShadow: '0 8px 24px rgba(14, 165, 233, 0.4)',
              cursor: 'pointer',
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {/* Otto Icon */}
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="2" />
              <circle cx="9" cy="10" r="1.5" fill="white" />
              <circle cx="15" cy="10" r="1.5" fill="white" />
              <path d="M8 14.5C8 14.5 9.5 16.5 12 16.5C14.5 16.5 16 14.5 16 14.5" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>

            {/* Connection Status Indicator */}
            {!isConnected && (
              <div
                style={{
                  position: 'absolute',
                  top: '4px',
                  right: '4px',
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: '#ef4444',
                  border: '2px solid white',
                }}
              />
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Expanded Chat Panel */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            style={{
              position: 'fixed',
              ...positionStyles,
              width: '400px',
              height: '600px',
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              borderRadius: '16px',
              boxShadow: '0 16px 48px rgba(0, 0, 0, 0.15)',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Header */}
            <div
              style={{
                padding: '20px',
                borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Otto Avatar */}
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 600,
                  }}
                >
                  O
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Otto AI</h3>
                  <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                    {isConnected ? 'Online' : 'Reconnecting...'}
                  </p>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setIsExpanded(false)}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  border: 'none',
                  background: 'rgba(0, 0, 0, 0.05)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                ✕
              </button>
            </div>

            {/* Error Banner */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  padding: '12px 20px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderBottom: '1px solid rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  color: '#dc2626',
                }}
              >
                <span>{error}</span>
                <button
                  onClick={() => {
                    clearError();
                    reconnect();
                  }}
                  style={{
                    border: 'none',
                    background: 'none',
                    color: '#0ea5e9',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  Retry
                </button>
              </motion.div>
            )}

            {/* Messages List */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              {messages.length === 0 && (
                <div
                  style={{
                    textAlign: 'center',
                    color: '#999',
                    fontSize: '14px',
                    marginTop: '40px',
                  }}
                >
                  <p>👋 Hi! I'm Otto, your vehicle discovery assistant.</p>
                  <p style={{ marginTop: '8px' }}>What kind of vehicle are you looking for?</p>
                </div>
              )}

              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    display: 'flex',
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '75%',
                      padding: '12px 16px',
                      borderRadius: '16px',
                      background: message.role === 'user'
                        ? 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)'
                        : 'rgba(0, 0, 0, 0.05)',
                      color: message.role === 'user' ? 'white' : '#1a1a1a',
                      fontSize: '14px',
                      lineHeight: '1.5',
                    }}
                  >
                    {message.content}

                    {message.metadata?.vehicleCount !== undefined && (
                      <div style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                        {message.metadata.vehicleCount} vehicles found
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Typing Indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  style={{ display: 'flex', gap: '4px', padding: '12px 16px' }}
                >
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: '#0ea5e9',
                      }}
                    />
                  ))}
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div
              style={{
                padding: '16px 20px',
                borderTop: '1px solid rgba(0, 0, 0, 0.1)',
                display: 'flex',
                gap: '12px',
                alignItems: 'center',
              }}
            >
              <input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isConnected ? "Tell me what you're looking for..." : "Connecting..."}
                disabled={!isConnected}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  borderRadius: '24px',
                  border: '1px solid rgba(0, 0, 0, 0.1)',
                  fontSize: '14px',
                  outline: 'none',
                  background: 'white',
                }}
              />
              <motion.button
                onClick={handleSend}
                disabled={!inputValue.trim() || !isConnected}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  border: 'none',
                  background: inputValue.trim() && isConnected
                    ? 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)'
                    : 'rgba(0, 0, 0, 0.1)',
                  color: 'white',
                  cursor: inputValue.trim() && isConnected ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                ↑
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default OttoChatWidget;
