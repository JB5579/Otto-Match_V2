"""
Zep Cloud Client for Otto.AI
Manages temporal memory and conversation context using Zep Cloud
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio

try:
    from zep_cloud import Zep, ZepClientError
    ZEP_AVAILABLE = True
except ImportError:
    ZEP_AVAILABLE = False
    Zep = None
    ZepClientError = Exception

from src.cache.multi_level_cache import MultiLevelCache

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class ConversationData:
    """Structured conversation data for Zep Cloud"""
    messages: List[Message]
    user_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """Retrieved conversation context with memory"""
    working_memory: List[Message]  # Last N messages
    episodic_memory: List[Dict[str, Any]]  # Relevant past conversations
    semantic_memory: Dict[str, Any]  # General knowledge context
    user_preferences: Dict[str, Any]  # Learned preferences


class ZepClient:
    """Client for interacting with Zep Cloud temporal memory"""

    def __init__(self, api_key: Optional[str] = None, cache: Optional[MultiLevelCache] = None):
        self.api_key = api_key or os.getenv('ZEP_API_KEY')
        self.cache = cache
        self.client = None
        self.initialized = False

        if not ZEP_AVAILABLE:
            logger.warning("Zep Cloud SDK not installed. Install with: pip install zep-python")
            return

        if not self.api_key:
            logger.warning("Zep API key not provided")
            return

    async def initialize(self) -> bool:
        """Initialize Zep Cloud client"""
        try:
            if not ZEP_AVAILABLE or not self.api_key:
                return False

            # Initialize Zep client
            self.client = Zep(api_key=self.api_key)

            # Test connection
            await self._test_connection()

            self.initialized = True
            logger.info("Zep Cloud client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Zep Cloud client: {e}")
            return False

    async def _test_connection(self):
        """Test connection to Zep Cloud"""
        # Try to list sessions to verify connection
        try:
            await self.client.session.list(limit=1)
            logger.debug("Zep Cloud connection test successful")
        except Exception as e:
            raise Exception(f"Zep Cloud connection test failed: {e}")

    async def create_session(self, user_id: str, session_id: Optional[str] = None, is_guest: bool = False) -> str:
        """Create or get a Zep session for a user

        Args:
            user_id: User identifier (or guest:session_id for guests)
            session_id: Optional explicit session ID
            is_guest: Whether this is a guest session (anonymous)

        Returns:
            The session ID that was created or retrieved
        """
        if not self.initialized:
            raise Exception("Zep client not initialized")

        try:
            # Use provided session_id or generate one
            if not session_id:
                if is_guest:
                    # For guests, use the user_id (which is the session_id) directly
                    session_id = user_id
                else:
                    session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Check if session exists
            try:
                existing_session = await self.client.session.get(session_id)
                if existing_session:
                    logger.debug(f"Using existing Zep session: {session_id}")
                    return session_id
            except:
                pass  # Session doesn't exist, create it

            # Create new session with metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'platform': 'otto-ai'
            }

            if is_guest:
                metadata['is_guest'] = True
                metadata['guest_session'] = True

            await self.client.session.add(
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )

            logger.info(f"Created Zep session: {session_id} for user: {user_id} (guest: {is_guest})")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create Zep session: {e}")
            raise

    async def store_conversation(self, user_id: str, conversation: ConversationData) -> bool:
        """Store conversation in Zep Cloud"""
        if not self.initialized:
            logger.warning("Zep client not initialized, skipping storage")
            return False

        try:
            # Ensure session exists
            session_id = await self.create_session(user_id, conversation.session_id)

            # Convert messages to Zep format
            zep_messages = []
            for msg in conversation.messages:
                zep_msg = {
                    'role': msg.role,
                    'content': msg.content,
                    'metadata': {
                        **(msg.metadata or {}),
                        'user_id': user_id,
                        'stored_at': datetime.now().isoformat()
                    }
                }
                if msg.created_at:
                    zep_msg['created_at'] = msg.created_at.isoformat()

                zep_messages.append(zep_msg)

            # Add messages to session
            await self.client.session.add(
                session_id=session_id,
                messages=zep_messages,
                metadata=conversation.metadata or {}
            )

            # Update cache
            if self.cache:
                cache_key = f"conversation:{user_id}:{session_id}"
                await self.cache.set(cache_key, {
                    'messages': zep_messages,
                    'updated_at': datetime.now().isoformat()
                }, ttl=3600)  # 1 hour TTL

            logger.debug(f"Stored {len(zep_messages)} messages in Zep session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """Retrieve conversation history from Zep"""
        if not self.initialized:
            return []

        try:
            # Check cache first
            cache_key = f"conversation:{user_id}:{session_id or 'latest'}"
            if self.cache:
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.debug(f"Retrieved conversation from cache: {cache_key}")
                    return [
                        Message(
                            role=msg['role'],
                            content=msg['content'],
                            metadata=msg.get('metadata')
                        )
                        for msg in cached['messages']
                    ]

            # Get session
            if not session_id:
                # Get latest session for user
                sessions = await self.client.session.list(user_id=user_id, limit=1)
                if not sessions:
                    return []
                session_id = sessions[0].session_id

            # Retrieve messages
            messages = await self.client.message.get(session_id, limit=limit)

            # Convert to Message objects
            conversation_messages = []
            for msg in messages:
                conversation_messages.append(Message(
                    role=msg.role,
                    content=msg.content,
                    metadata=msg.metadata,
                    created_at=msg.created_at
                ))

            # Update cache
            if self.cache and conversation_messages:
                await self.cache.set(cache_key, {
                    'messages': [asdict(msg) for msg in conversation_messages],
                    'updated_at': datetime.now().isoformat()
                }, ttl=3600)

            return conversation_messages

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        search_scope: str = 'messages'
    ) -> List[Dict[str, Any]]:
        """Search past conversations using semantic search"""
        if not self.initialized:
            return []

        try:
            # Perform search
            results = await self.client.memory.search(
                text=query,
                user_id=user_id,
                limit=limit,
                search_scope=search_scope
            )

            # Process results
            search_results = []
            for result in results:
                search_results.append({
                    'session_id': result.session_id,
                    'message': {
                        'role': result.role,
                        'content': result.content,
                        'created_at': result.created_at.isoformat() if result.created_at else None
                    },
                    'score': result.score,
                    'metadata': result.metadata
                })

            return search_results

        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []

    async def get_contextual_memory(self, user_id: str, current_query: str) -> ConversationContext:
        """Get contextual memory for conversation"""
        try:
            # Get working memory (last 10 messages)
            working_memory = await self.get_conversation_history(user_id, limit=10)

            # Get episodic memory (relevant past conversations)
            episodic_memory = await self.search_conversations(
                user_id=user_id,
                query=current_query,
                limit=5
            )

            # Get semantic memory (user preferences from metadata)
            semantic_memory = await self._extract_user_knowledge(user_id)

            # Extract user preferences from recent conversations
            user_preferences = await self._extract_user_preferences(working_memory)

            return ConversationContext(
                working_memory=working_memory,
                episodic_memory=episodic_memory,
                semantic_memory=semantic_memory,
                user_preferences=user_preferences
            )

        except Exception as e:
            logger.error(f"Failed to get contextual memory: {e}")
            return ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )

    async def _extract_user_knowledge(self, user_id: str) -> Dict[str, Any]:
        """Extract semantic knowledge about user from Zep"""
        # This would use Zep's knowledge graph features
        # For now, return basic structure
        return {
            'vehicle_preferences': {},
            'budget_range': None,
            'location': None,
            'family_size': None,
            'usage_patterns': {}
        }

    async def _extract_user_preferences(self, messages: List[Message]) -> Dict[str, Any]:
        """Extract preferences from conversation messages"""
        preferences = {}

        # Simple keyword extraction for demo
        # In production, this would use NLP/AI analysis
        for msg in messages:
            if msg.role == 'user':
                content_lower = msg.content.lower()

                # Budget preferences
                if 'under $' in content_lower or 'below $' in content_lower:
                    # Extract budget numbers
                    import re
                    budgets = re.findall(r'\$[0-9,]+', content_lower)
                    if budgets and 'budget' not in preferences:
                        preferences['budget'] = budgets[0]

                # Vehicle type preferences
                vehicle_types = ['suv', 'sedan', 'truck', 'electric', 'hybrid']
                for vt in vehicle_types:
                    if vt in content_lower:
                        preferences.setdefault('vehicle_types', []).append(vt)

                # Family size
                if 'family' in content_lower or 'kids' in content_lower:
                    if 'family of' in content_lower:
                        import re
                        family_size = re.search(r'family of (\d+)', content_lower)
                        if family_size:
                            preferences['family_size'] = int(family_size.group(1))

        return preferences

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        if not self.initialized:
            return False

        try:
            await self.client.session.delete(session_id)

            # Clear from cache
            if self.cache:
                # Delete all cache keys for this session
                # This is simplified - in production you'd track all keys
                await self.cache.delete(f"conversation:*:*{session_id}")

            logger.info(f"Deleted Zep session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """Update user-level metadata"""
        if not self.initialized:
            return False

        try:
            # Get all sessions for user
            sessions = await self.client.session.list(user_id=user_id)

            # Update metadata for each session
            for session in sessions:
                await self.client.session.update(
                    session_id=session.session_id,
                    metadata=metadata
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update user metadata: {e}")
            return False

    async def create_guest_session(self, session_id: str) -> str:
        """Create or retrieve a Zep session for an anonymous guest user

        Args:
            session_id: The UUID-based session ID from cookie

        Returns:
            The session ID

        Guest sessions are prefixed with 'guest:' to distinguish them from
        authenticated user sessions. This enables session-to-account merge
        when the guest signs up.
        """
        if not self.initialized:
            raise Exception("Zep client not initialized")

        try:
            # Use guest: prefix for anonymous sessions
            guest_user_id = f"guest:{session_id}"

            # Check if session already exists
            try:
                existing_session = await self.client.session.get(session_id)
                if existing_session:
                    logger.debug(f"Using existing guest session: {session_id}")
                    # Update last seen timestamp
                    await self.client.session.update(
                        session_id=session_id,
                        metadata={
                            'last_seen': datetime.now().isoformat(),
                            'is_guest': True
                        }
                    )
                    return session_id
            except:
                pass  # Session doesn't exist, create it

            # Create new guest session
            await self.client.session.add(
                session_id=session_id,
                user_id=guest_user_id,
                metadata={
                    'is_guest': True,
                    'guest_session': True,
                    'created_at': datetime.now().isoformat(),
                    'platform': 'otto-ai',
                    'last_seen': datetime.now().isoformat()
                }
            )

            logger.info(f"Created guest Zep session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create guest session: {e}")
            raise

    async def merge_session_to_user(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Transfer guest session memory to authenticated user account

        Args:
            session_id: The guest session ID to merge
            user_id: The authenticated user ID to merge into

        Returns:
            Merge result with messages_transferred count

        This method:
        1. Retrieves all messages from the guest session
        2. Creates a new session for the authenticated user
        3. Transfers all messages to the user session
        4. Marks the guest session for cleanup
        """
        if not self.initialized:
            raise Exception("Zep client not initialized")

        try:
            logger.info(f"Merging guest session {session_id} to user {user_id}")

            # 1. Retrieve guest session messages
            guest_messages = await self.client.message.get(session_id, limit=1000)

            if not guest_messages:
                logger.warning(f"No messages found in guest session {session_id}")
                return {
                    'success': True,
                    'messages_transferred': 0,
                    'preferences_preserved': []
                }

            # 2. Create user session (will use existing if present)
            user_session_id = await self.create_session(user_id)

            # 3. Transfer messages to user session
            # Convert Zep messages to dict format for transfer
            messages_to_transfer = []
            for msg in guest_messages:
                messages_to_transfer.append({
                    'role': msg.role,
                    'content': msg.content,
                    'metadata': {
                        **(msg.metadata or {}),
                        'merged_from_guest_session': session_id,
                        'transferred_at': datetime.now().isoformat()
                    }
                })

            # Add all messages to user session
            await self.client.session.add(
                session_id=user_session_id,
                messages=messages_to_transfer
            )

            # 4. Extract preferences from transferred messages
            preferences_preserved = []
            for msg in guest_messages:
                if msg.role == 'user':
                    # Simple preference extraction
                    content_lower = msg.content.lower()
                    if 'suv' in content_lower:
                        preferences_preserved.append('SUV preference')
                    if 'truck' in content_lower:
                        preferences_preserved.append('Truck preference')
                    if 'under $' in content_lower or 'below $' in content_lower:
                        import re
                        budgets = re.findall(r'\$[0-9,]+', content_lower)
                        if budgets:
                            preferences_preserved.append(f'Budget: {budgets[0]}')

            # 5. Mark guest session for cleanup (don't delete yet, for audit trail)
            await self.client.session.update(
                session_id=session_id,
                metadata={
                    'is_guest': True,
                    'status': 'merged',
                    'merged_to_user': user_id,
                    'merged_at': datetime.now().isoformat()
                }
            )

            logger.info(
                f"Successfully merged guest session {session_id} to user {user_id}. "
                f"Transferred {len(messages_to_transfer)} messages."
            )

            return {
                'success': True,
                'messages_transferred': len(messages_to_transfer),
                'preferences_preserved': list(set(preferences_preserved)),  # Deduplicate
                'guest_session_id': session_id,
                'user_session_id': user_session_id
            }

        except Exception as e:
            logger.error(f"Failed to merge guest session {session_id} to user {user_id}: {e}")
            raise

    async def get_last_visit_context(self, session_id: str) -> Dict[str, Any]:
        """Get context from guest's last visit for "Welcome back!" greeting

        Args:
            session_id: The guest session ID

        Returns:
            Dictionary with last_visit_date, previous_preferences, message_count
        """
        if not self.initialized:
            return {}

        try:
            # Get session details
            try:
                session = await self.client.session.get(session_id)
            except:
                return {}

            # Get messages from session
            messages = await self.client.message.get(session_id, limit=50)

            # Extract preferences from messages
            previous_preferences = []
            for msg in messages:
                if msg.role == 'user':
                    content_lower = msg.content.lower()
                    if 'suv' in content_lower:
                        previous_preferences.append('SUVs')
                    if 'truck' in content_lower:
                        previous_preferences.append('trucks')
                    if 'electric' in content_lower or 'ev' in content_lower:
                        previous_preferences.append('electric vehicles')
                    if 'under $' in content_lower:
                        import re
                        budgets = re.findall(r'\$[0-9,]+', content_lower)
                        if budgets:
                            previous_preferences.append(f'vehicles under {budgets[0]}')

            return {
                'last_visit_date': session.updated_at.isoformat() if session and session.updated_at else None,
                'created_date': session.created_at.isoformat() if session and session.created_at else None,
                'previous_preferences': list(set(previous_preferences)),  # Deduplicate
                'message_count': len(messages),
                'is_returning_visitor': len(messages) > 0
            }

        except Exception as e:
            logger.error(f"Failed to get last visit context for session {session_id}: {e}")
            return {}

    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's sessions"""
        if not self.initialized:
            return {}

        try:
            sessions = await self.client.session.list(user_id=user_id, limit=100)

            total_sessions = len(sessions)
            total_messages = 0
            last_activity = None

            for session in sessions:
                # Get message count for each session
                messages = await self.client.message.get(session.session_id, limit=1)
                if messages:
                    total_messages += len(messages)

                # Track last activity
                if session.updated_at:
                    if not last_activity or session.updated_at > last_activity:
                        last_activity = session.updated_at

            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'last_activity': last_activity.isoformat() if last_activity else None,
                'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}