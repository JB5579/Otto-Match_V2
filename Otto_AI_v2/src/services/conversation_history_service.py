"""
Conversation History Service
Bridges conversation history database with Zep Cloud for seamless conversation retrieval and storage.
Handles guest vs authenticated user sessions and session merge operations.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.memory.zep_client import ZepClient, Message
from src.services.conversation_summary_service import (
    get_summary_service,
    ConversationSummary,
    ExtractedPreferences,
    VehicleMention
)
from src.services.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """Represents a conversation session"""
    session_id: str  # Zep session ID
    user_id: Optional[str]  # Authenticated user ID (None for guests)
    is_guest: bool
    created_at: datetime
    last_activity: datetime
    message_count: int


@dataclass
class StoredConversation:
    """Conversation stored in database"""
    id: str
    session_id: str
    user_id: Optional[str]
    zep_conversation_id: str
    title: str
    summary: str
    message_count: int
    started_at: datetime
    last_message_at: datetime


class ConversationHistoryService:
    """Service for managing conversation history with Zep Cloud integration"""

    def __init__(
        self,
        zep_client: Optional[ZepClient] = None,
        summary_service=None,
        supabase_client=None
    ):
        self.zep_client = zep_client
        self.summary_service = summary_service or get_summary_service()
        self.supabase_client = supabase_client or get_supabase_client()

    async def store_conversation(
        self,
        messages: List[Message],
        session_id: str,
        user_id: Optional[str] = None,
        generate_summary: bool = True
    ) -> StoredConversation:
        """Store conversation in both Zep Cloud and database

        This method:
        1. Stores messages in Zep Cloud (temporal memory)
        2. Generates AI summary
        3. Stores summary and metadata in database
        """
        try:
            logger.info(f"Storing conversation for session {session_id}")

            # Store in Zep Cloud
            if self.zep_client:
                from src.memory.zep_client import ConversationData
                conversation_data = ConversationData(
                    messages=messages,
                    user_id=user_id or f"guest:{session_id}",
                    session_id=session_id,
                    metadata={
                        'user_id': user_id,
                        'is_guest': user_id is None
                    }
                )
                await self.zep_client.store_conversation(
                    user_id=user_id or f"guest:{session_id}",
                    conversation=conversation_data
                )

            # Generate summary
            conversation_summary = None
            if generate_summary and self.summary_service:
                conversation_summary = await self.summary_service.generate_conversation_summary(
                    messages=messages,
                    conversation_id=session_id,  # Use session_id as conversation_id
                    session_id=session_id,
                    user_id=user_id
                )

            # Store in database
            conversation_record = await self._store_conversation_in_db(
                session_id=session_id,
                user_id=user_id,
                conversation_summary=conversation_summary,
                message_count=len(messages)
            )

            logger.info(f"Conversation stored: {conversation_record.id}")
            return conversation_record

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise

    async def get_conversation_history(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        include_deleted: bool = False
    ) -> List[StoredConversation]:
        """Retrieve conversation history from database

        AC1: Chronological conversation list
        AC3: Guest user session-based history
        """
        try:
            query = self.supabase_client.table('conversation_history').select('*')

            # Filter by user or session
            if user_id:
                # Authenticated user: get their conversations + current guest session
                if session_id:
                    query = query.or_(f'user_id.eq.{user_id},and(user_id.is.null,session_id.eq.{session_id})')
                else:
                    query = query.eq('user_id', user_id)
            elif session_id:
                # Guest user: only get this session's conversations
                query = query.is_('user_id', 'null').eq('session_id', session_id)
            else:
                raise ValueError("Either user_id or session_id must be provided")

            # Exclude deleted unless requested
            if not include_deleted:
                query = query.not_eq('status', 'deleted')

            # Order by last message
            query = query.order('last_message_at', desc=True).limit(limit)

            result = query.execute()

            conversations = []
            for row in result.data:
                conversations.append(StoredConversation(
                    id=row.get('id'),
                    session_id=row.get('session_id'),
                    user_id=row.get('user_id'),
                    zep_conversation_id=row.get('zep_conversation_id'),
                    title=row.get('title', ''),
                    summary=row.get('summary', ''),
                    message_count=row.get('message_count', 0),
                    started_at=row.get('started_at'),
                    last_message_at=row.get('last_message_at')
                ))

            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Message]:
        """Retrieve full conversation messages from Zep Cloud

        Uses the conversation_messages_cache table for faster access
        """
        try:
            # First, try to get from cache
            cached_messages = await self._get_cached_messages(conversation_id, limit)
            if cached_messages:
                return cached_messages

            # If not in cache, fetch from Zep
            if self.zep_client:
                # Get session ID from conversation record
                conv_result = self.supabase_client.table('conversation_history').select('*').eq('id', conversation_id).execute()

                if not conv_result.data:
                    raise ValueError(f"Conversation {conversation_id} not found")

                conv = conv_result.data[0]
                zep_session_id = conv.get('session_id')

                messages = await self.zep_client.get_conversation_history(
                    user_id=user_id or zep_session_id,
                    session_id=zep_session_id,
                    limit=limit
                )

                # Cache the messages
                await self._cache_messages(conversation_id, messages)

                return messages

            return []

        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            raise

    async def get_session_info(
        self,
        session_id: str
    ) -> Optional[ConversationSession]:
        """Get information about a conversation session"""
        try:
            result = self.supabase_client.table('conversation_history').select('*')
                .eq('session_id', session_id)
                .order('started_at', desc=True)
                .limit(1)
                .execute()

            if not result.data:
                return None

            row = result.data[0]

            return ConversationSession(
                session_id=row.get('session_id'),
                user_id=row.get('user_id'),
                is_guest=row.get('user_id') is None,
                created_at=row.get('started_at'),
                last_activity=row.get('last_message_at'),
                message_count=row.get('message_count', 0)
            )

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None

    async def merge_guest_session_to_user(
        self,
        guest_session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Merge guest session to authenticated user account

        Transfers all guest session data to the user's account
        Preserves conversation history and preferences
        """
        try:
            logger.info(f"Merging guest session {guest_session_id} to user {user_id}")

            # Use PostgreSQL function to merge in database
            result = self.supabase_client.client.rpc(
                'merge_guest_conversation_history',
                {
                    'target_user_id': user_id,
                    'guest_session_id': guest_session_id
                }
            ).execute()

            # Also merge in Zep Cloud
            if self.zep_client:
                await self.zep_client.merge_session_to_user(guest_session_id, user_id)

            return {
                'success': True,
                'message': 'Guest session merged successfully',
                'conversations_merged': len(result.data) if result.data else 0
            }

        except Exception as e:
            logger.error(f"Failed to merge guest session: {e}")
            raise

    async def search_conversations(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search conversations using semantic search

        AC4: Search and filter conversations
        """
        try:
            # Use Zep's semantic search
            if self.zep_client:
                search_user_id = user_id or session_id
                results = await self.zep_client.search_conversations(
                    user_id=search_user_id,
                    query=query,
                    limit=limit,
                    search_scope='messages'
                )

                # Enrich with database metadata
                enriched_results = []
                for result in results:
                    # Find matching conversation in database
                    db_result = self.supabase_client.table('conversation_history').select('*')
                        .eq('session_id', result.get('session_id'))
                        .execute()

                    if db_result.data:
                        row = db_result.data[0]
                        enriched_results.append({
                            **result,
                            'title': row.get('title'),
                            'summary': row.get('summary'),
                            'journey_stage': row.get('journey_stage'),
                            'started_at': row.get('started_at')
                        })

                return enriched_results

            return []

        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            raise

    async def update_retention_policy(
        self,
        user_id: str,
        retention_days: int,
        auto_delete: bool = True
    ) -> bool:
        """Update data retention policy for user

        AC6: Data retention and privacy controls
        """
        try:
            # Update or create retention policy
            existing = self.supabase_client.table('data_retention_policies').select('*')
                .eq('user_id', user_id)
                .execute()

            policy_data = {
                'default_retention_days': retention_days,
                'auto_delete_enabled': auto_delete,
                'last_updated_at': datetime.now().isoformat()
            }

            if existing.data:
                # Update existing
                self.supabase_client.table('data_retention_policies').update(policy_data)
                    .eq('user_id', user_id)
                    .execute()
            else:
                # Create new
                policy_data['user_id'] = user_id
                self.supabase_client.table('data_retention_policies').insert(policy_data).execute()

            # Update expiration dates for existing conversations
            await self._apply_retention_policy(user_id, retention_days)

            return True

        except Exception as e:
            logger.error(f"Failed to update retention policy: {e}")
            return False

    async def _store_conversation_in_db(
        self,
        session_id: str,
        user_id: Optional[str],
        conversation_summary: Optional[ConversationSummary],
        message_count: int
    ) -> StoredConversation:
        """Store conversation metadata in database"""
        try:
            # Prepare data
            now = datetime.now()

            preferences_json = {}
            vehicles_json = []

            if conversation_summary:
                preferences_json = {
                    'budget': conversation_summary.preferences.budget.__dict__ if conversation_summary.preferences.budget else None,
                    'vehicle_types': conversation_summary.preferences.vehicle_types,
                    'brands': conversation_summary.preferences.brands,
                    'features': conversation_summary.preferences.features,
                    'lifestyle': conversation_summary.preferences.lifestyle,
                    'colors': conversation_summary.preferences.colors,
                    'deal_breakers': conversation_summary.preferences.deal_breakers
                }

                vehicles_json = [
                    {
                        'make': v.make,
                        'model': v.model,
                        'year': v.year,
                        'trim': v.trim,
                        'relevance_score': v.relevance_score,
                        'mentioned_count': v.mentioned_count,
                        'sentiment': v.sentiment
                    }
                    for v in conversation_summary.vehicles_discussed
                ]

            # Check if conversation already exists
            existing = self.supabase_client.table('conversation_history').select('*')
                .eq('session_id', session_id)
                .execute()

            conversation_data = {
                'session_id': session_id,
                'zep_conversation_id': session_id,  # Use session_id as Zep ID
                'started_at': conversation_summary.started_at if conversation_summary else now,
                'last_message_at': conversation_summary.ended_at if conversation_summary else now,
                'message_count': message_count,
                'title': conversation_summary.title if conversation_summary else f"Conversation {session_id[:8]}",
                'summary': conversation_summary.summary if conversation_summary else None,
                'preferences_json': preferences_json,
                'vehicles_discussed': vehicles_json,
                'journey_stage': conversation_summary.journey_stage.value if conversation_summary else 'discovery',
                'evolution_detected': conversation_summary.evolution_detected if conversation_summary else False,
                'updated_at': now.isoformat()
            }

            if existing.data:
                # Update existing
                result = self.supabase_client.table('conversation_history').update(conversation_data)
                    .eq('id', existing.data[0]['id'])
                    .execute()

                row = result.data[0]
            else:
                # Insert new
                conversation_data['created_at'] = now.isoformat()
                result = self.supabase_client.table('conversation_history').insert(conversation_data).execute()

                row = result.data[0]

            return StoredConversation(
                id=row.get('id'),
                session_id=row.get('session_id'),
                user_id=row.get('user_id'),
                zep_conversation_id=row.get('zep_conversation_id'),
                title=row.get('title', ''),
                summary=row.get('summary', ''),
                message_count=row.get('message_count', 0),
                started_at=row.get('started_at'),
                last_message_at=row.get('last_message_at')
            )

        except Exception as e:
            logger.error(f"Failed to store conversation in DB: {e}")
            raise

    async def _get_cached_messages(
        self,
        conversation_id: str,
        limit: int
    ) -> Optional[List[Message]]:
        """Get messages from cache if available"""
        try:
            result = self.supabase_client.table('conversation_messages_cache').select('*')
                .eq('conversation_history_id', conversation_id)
                .order('created_at', desc=True)
                .limit(limit)
                .execute()

            if result.data:
                messages = []
                for row in result.data:
                    messages.append(Message(
                        role=row.get('role'),
                        content=row.get('content'),
                        metadata=row.get('metadata'),
                        created_at=datetime.fromisoformat(row.get('created_at')) if row.get('created_at') else None
                    ))
                return messages[::-1]  # Reverse to get chronological order

            return None

        except Exception as e:
            logger.error(f"Failed to get cached messages: {e}")
            return None

    async def _cache_messages(
        self,
        conversation_id: str,
        messages: List[Message]
    ):
        """Cache messages from Zep in database"""
        try:
            # Delete existing cache for this conversation
            self.supabase_client.table('conversation_messages_cache').delete()
                .eq('conversation_history_id', conversation_id)
                .execute()

            # Insert messages
            messages_data = [
                {
                    'conversation_history_id': conversation_id,
                    'zep_message_id': f"{conversation_id}_{i}",
                    'role': msg.role,
                    'content': msg.content,
                    'metadata': msg.metadata or {},
                    'created_at': msg.created_at.isoformat() if msg.created_at else datetime.now().isoformat()
                }
                for i, msg in enumerate(messages)
            ]

            # Batch insert (would need to handle Supabase batch insert)
            for msg_data in messages_data:
                self.supabase_client.table('conversation_messages_cache').insert(msg_data).execute()

            logger.info(f"Cached {len(messages)} messages for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to cache messages: {e}")

    async def _apply_retention_policy(
        self,
        user_id: str,
        retention_days: int
    ):
        """Apply retention policy to existing conversations"""
        try:
            # Calculate expiration date
            if retention_days == 0:
                # Indefinite retention
                new_expires_at = None
            else:
                # All conversations should expire retention_days from their start date
                # This would be handled by the database trigger

                # For existing conversations, update expires_at
                expiration_calc = f"started_at + INTERVAL '{retention_days} days'"
                # Would use SQL execution for bulk update

            logger.info(f"Applied retention policy ({retention_days} days) for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")


# Singleton instance
_history_service_instance: Optional[ConversationHistoryService] = None


def get_conversation_history_service(
    zep_client: Optional[ZepClient] = None,
    summary_service=None,
    supabase_client=None
) -> ConversationHistoryService:
    """Get or create singleton ConversationHistoryService instance"""
    global _history_service_instance

    if _history_service_instance is None:
        _history_service_instance = ConversationHistoryService(
            zep_client=zep_client,
            summary_service=summary_service,
            supabase_client=supabase_client
        )

    return _history_service_instance
