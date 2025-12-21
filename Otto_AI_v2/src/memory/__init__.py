"""
Memory Module for Otto.AI
Handles temporal memory and context storage including:
- Zep Cloud integration
- Conversation history
- Context management
- Memory retrieval
"""

from .zep_client import ZepClient, ConversationData, ConversationContext

__all__ = [
    'ZepClient',
    'ConversationData',
    'ConversationContext'
]