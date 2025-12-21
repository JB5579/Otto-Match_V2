"""
Conversation Module for Otto.AI
Handles all conversational AI functionality including:
- WebSocket management
- Message processing
- Context management
- AI integration
"""

from .conversation_agent import ConversationAgent, ConversationResponse, ConversationContext

__all__ = [
    'ConversationAgent',
    'ConversationResponse',
    'ConversationContext'
]