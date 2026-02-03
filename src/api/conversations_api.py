"""
Otto.AI Conversations API
FastAPI endpoints for conversation history, session summaries, and journey tracking.
Supports both authenticated users and guest users (session-based).
Integrates with Zep Cloud for conversation storage and conversation_summary_service for AI summaries.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field

from ..services.supabase_client import get_supabase_client
from ..services.conversation_summary_service import (
    get_summary_service,
    ConversationSummary,
    ExtractedPreferences,
    VehicleMention
)
from ..memory.zep_client import ZepClient, get_zep_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for conversations endpoints
conversations_router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


# =================================================================
# Pydantic Models for API Requests/Responses
# =================================================================

class ConversationHistoryItem(BaseModel):
    """Single conversation in history list"""
    id: str
    user_id: Optional[str] = None
    session_id: str
    title: str
    summary: Optional[str] = None
    started_at: datetime
    last_message_at: datetime
    message_count: int
    journey_stage: str
    evolution_detected: bool
    top_preferences: Optional[List[Dict[str, Any]]] = None
    vehicles_mentioned_count: int
    retention_days: int
    expires_at: Optional[datetime] = None
    date_display: str
    message_count_display: str


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history list"""
    conversations: List[ConversationHistoryItem]
    total: int
    page: int
    page_size: int


class ConversationDetail(BaseModel):
    """Full conversation details"""
    id: str
    user_id: Optional[str] = None
    session_id: str
    zep_conversation_id: str
    title: str
    summary: str
    key_points: List[str]
    started_at: datetime
    last_message_at: datetime
    message_count: int
    duration_minutes: float

    # Preferences
    preferences: Dict[str, Any]

    # Vehicles discussed
    vehicles_discussed: List[Dict[str, Any]]

    # Journey tracking
    journey_stage: str
    evolution_detected: bool
    evolution_notes: List[str]

    # Metadata
    status: str
    retention_days: int
    expires_at: Optional[datetime] = None


class ConversationMessagesResponse(BaseModel):
    """Full conversation dialogue"""
    conversation_id: str
    session_id: str
    messages: List[Dict[str, Any]]
    total_messages: int


class JourneySummary(BaseModel):
    """User journey summary across all conversations"""
    identifier: str
    user_id: Optional[str] = None
    first_conversation: Optional[datetime] = None
    last_conversation: Optional[datetime] = None
    total_conversations: int
    total_messages: int

    # Journey progress
    stages_visited: List[str]
    current_stage: str

    # All vehicles discussed
    all_vehicles_discussed: List[Dict[str, Any]]

    # Current active preferences
    active_preferences: List[Dict[str, Any]]

    # Evolution tracking
    preferences_evolved: bool


class SearchFilters(BaseModel):
    """Search and filter options for conversations"""
    query: Optional[str] = None  # Full-text search
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    journey_stage: Optional[str] = None
    has_evolution: Optional[bool] = None


class DeleteConversationRequest(BaseModel):
    """Request to delete conversations"""
    conversation_ids: List[str]
    reason: Optional[str] = None  # GDPR compliance: why deleted


class DataRetentionPolicy(BaseModel):
    """Data retention settings"""
    default_retention_days: int = Field(default=90, ge=0, description="Days before auto-delete (0 = indefinite)")
    auto_delete_enabled: bool = True
    delete_on_account_closure: bool = True
    allow_anonymous_usage: bool = False
    share_conversations_with_sellers: bool = False


class ExportRequest(BaseModel):
    """Request to export conversation data"""
    export_type: str = Field(default="json", pattern="^(pdf|json|full_gdpr)$")
    conversation_ids: Optional[List[str]] = None  # Empty = all conversations


# =================================================================
# Helper Functions
# =================================================================

async def get_user_context(
    authorization: Optional[str] = None,
    x_session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Extract user context from request headers

    Supports both authenticated users (JWT) and guest users (session cookie)

    Args:
        authorization: Bearer token from Authorization header
        x_session_id: Session ID from X-Session-ID header (guest users)

    Returns:
        Dict with user_id (optional), session_id, is_guest flag
    """
    user_id = None
    session_id = None
    is_guest = False

    # Check for authenticated user
    if authorization:
        # Extract JWT token
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            # In production, validate JWT with Supabase auth
            # For now, simplified: token = user_id
            try:
                # TODO: Validate with Supabase JWT verification
                user_id = token  # Simplified - should decode JWT
                logger.debug(f"Authenticated user: {user_id}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT: {e}")

    # Check for guest session
    if x_session_id and not user_id:
        session_id = x_session_id
        is_guest = True
        logger.debug(f"Guest session: {session_id}")
    elif user_id:
        # Authenticated users also have session IDs
        session_id = x_session_id
        is_guest = False
    else:
        # No user context provided
        raise HTTPException(
            status_code=401,
            detail="Either Authorization header or X-Session-ID required"
        )

    return {
        "user_id": user_id,
        "session_id": session_id,
        "is_guest": is_guest
    }


# =================================================================
# API Endpoints
# =================================================================

@conversations_router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    journey_stage: Optional[str] = Query(None, description="Filter by journey stage"),
    has_evolution: Optional[bool] = Query(None, description="Filter by evolution detected"),
    authorization: Optional[str] = Header(None, description="Bearer token for authenticated users"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID", description="Session ID for guest users")
):
    """
    Get conversation history for the user

    AC1: Chronological Conversation List
    AC3: Guest User Access (Session-Based History)

    Returns a paginated list of conversations with summaries and key preferences.
    Supports both authenticated users (JWT) and guest users (session cookie).
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        is_guest = context.get("is_guest")

        supabase = get_supabase_client()

        # Build query
        query = supabase.table('conversation_history').select('*', count='exact')

        # Filter by user or session
        if is_guest:
            query = query.is_('user_id', 'null').eq('session_id', session_id)
        else:
            # Authenticated users: get their conversations OR their current guest session
            query = query.or_(f'user_id.eq.{user_id},and(user_id.is.null,session_id.eq.{session_id})')

        # Apply optional filters
        if journey_stage:
            query = query.eq('journey_stage', journey_stage)

        if has_evolution is not None:
            query = query.eq('evolution_detected', has_evolution)

        # Exclude deleted conversations
        query = query.not_eq('status', 'deleted')

        # Order by last message (newest first)
        query = query.order('last_message_at', desc=True)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        # Execute query
        result = query.execute()

        # Get total count
        total = result.count if result.count is not None else len(result.data)

        # Convert to response models
        conversations = []
        for row in result.data:
            conversations.append(ConversationHistoryItem(
                id=row.get('id', ''),
                user_id=row.get('user_id'),
                session_id=row.get('session_id', ''),
                title=row.get('title', 'Conversation'),
                summary=row.get('summary'),
                started_at=row.get('started_at'),
                last_message_at=row.get('last_message_at'),
                message_count=row.get('message_count', 0),
                journey_stage=row.get('journey_stage', 'discovery'),
                evolution_detected=row.get('evolution_detected', False),
                top_preferences=row.get('top_preferences'),  # From view
                vehicles_mentioned_count=row.get('vehicles_mentioned_count', 0),
                retention_days=row.get('retention_days', 90),
                expires_at=row.get('expires_at'),
                date_display=row.get('date_display', ''),
                message_count_display=row.get('message_count_display', '')
            ))

        return ConversationHistoryResponse(
            conversations=conversations,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")


@conversations_router.get("/history/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    conversation_id: str,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Get full conversation details

    AC1: Click into conversation to see full dialogue
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        is_guest = context.get("is_guest")

        supabase = get_supabase_client()

        # Build query with user/session filtering
        query = supabase.table('conversation_history').select('*').eq('id', conversation_id)

        if is_guest:
            query = query.is_('user_id', 'null').eq('session_id', session_id)
        else:
            query = query.or_(f'user_id.eq.{user_id},and(user_id.is.null,session_id.eq.{session_id})')

        result = query.execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        row = result.data[0]

        # Get vehicles discussed
        vehicles_discussed = row.get('vehicles_discussed', [])
        if isinstance(vehicles_discussed, str):
            import json
            vehicles_discussed = json.loads(vehicles_discussed)

        # Get preferences
        preferences_json = row.get('preferences_json', {})
        if isinstance(preferences_json, str):
            import json
            preferences_json = json.loads(preferences_json)

        return ConversationDetail(
            id=row.get('id', ''),
            user_id=row.get('user_id'),
            session_id=row.get('session_id', ''),
            zep_conversation_id=row.get('zep_conversation_id', ''),
            title=row.get('title', ''),
            summary=row.get('summary', ''),
            key_points=[],  # Would be populated from cached summary
            started_at=row.get('started_at'),
            last_message_at=row.get('last_message_at'),
            message_count=row.get('message_count', 0),
            duration_minutes=0,  # Would be calculated
            preferences=preferences_json,
            vehicles_discussed=vehicles_discussed,
            journey_stage=row.get('journey_stage', 'discovery'),
            evolution_detected=row.get('evolution_detected', False),
            evolution_notes=[],  # Would be populated
            status=row.get('status', 'active'),
            retention_days=row.get('retention_days', 90),
            expires_at=row.get('expires_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation detail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@conversations_router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Get full conversation dialogue from Zep Cloud

    AC1: Click into conversation to see full dialogue
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)

        # Get conversation record to find Zep conversation ID
        supabase = get_supabase_client()
        conversation_result = supabase.table('conversation_history').select('*').eq('id', conversation_id).execute()

        if not conversation_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation = conversation_result.data[0]
        zep_conversation_id = conversation.get('zep_conversation_id')

        # Fetch messages from Zep
        zep_client = get_zep_client()
        messages = await zep_client.get_conversation_history(
            user_id=context.get("user_id") or context.get("session_id"),
            session_id=conversation.get('session_id'),
            limit=1000
        )

        # Convert to dict format
        message_dicts = [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "metadata": msg.metadata
            }
            for msg in messages
        ]

        return ConversationMessagesResponse(
            conversation_id=conversation_id,
            session_id=conversation.get('session_id', ''),
            messages=message_dicts,
            total_messages=len(message_dicts)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@conversations_router.get("/summary", response_model=JourneySummary)
async def get_journey_summary(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Get comprehensive journey summary

    AC2: Journey Summary - Top categories, preferences, evolution, next steps
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")
        session_id = context.get("session_id")

        supabase = get_supabase_client()

        # Query journey timeline view
        query = supabase.table('conversation_journey_timeline').select('*')

        # Filter by user or session identifier
        if user_id:
            query = query.eq('user_id', user_id)
        else:
            query = query.is_('user_id', 'null').eq('session_id', session_id)

        result = query.execute()

        if not result.data:
            # No journey data yet - return empty summary
            return JourneySummary(
                identifier=session_id,
                user_id=user_id,
                first_conversation=None,
                last_conversation=None,
                total_conversations=0,
                total_messages=0,
                stages_visited=[],
                current_stage="discovery",
                all_vehicles_discussed=[],
                active_preferences=[],
                preferences_evolved=False
            )

        row = result.data[0]

        # Parse JSONB fields
        stages_visited = row.get('stages_visited', [])
        all_vehicles = row.get('all_vehicles_discussed', [])
        active_prefs = row.get('active_preferences', [])

        if isinstance(stages_visited, str):
            import json
            stages_visited = json.loads(stages_visited)
        if isinstance(all_vehicles, str):
            import json
            all_vehicles = json.loads(all_vehicles)
        if isinstance(active_prefs, str):
            import json
            active_prefs = json.loads(active_prefs)

        # Determine current stage (last in visited stages)
        current_stage = stages_visited[-1] if stages_visited else "discovery"

        return JourneySummary(
            identifier=row.get('identifier', ''),
            user_id=row.get('user_id'),
            first_conversation=row.get('first_conversation'),
            last_conversation=row.get('last_conversation'),
            total_conversations=row.get('total_conversations', 0),
            total_messages=row.get('total_messages', 0),
            stages_visited=stages_visited,
            current_stage=current_stage,
            all_vehicles_discussed=all_vehicles,
            active_preferences=active_prefs,
            preferences_evolved=row.get('preferences_evolved', False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get journey summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve journey summary: {str(e)}")


@conversations_router.get("/search", response_model=ConversationHistoryResponse)
async def search_conversations(
    query: str = Query(..., min_length=2, description="Search query"),
    vehicle_make: Optional[str] = Query(None, description="Filter by vehicle make"),
    vehicle_model: Optional[str] = Query(None, description="Filter by vehicle model"),
    date_from: Optional[date] = Query(None, description="Filter conversations from this date"),
    date_to: Optional[date] = Query(None, description="Filter conversations until this date"),
    journey_stage: Optional[str] = Query(None, description="Filter by journey stage"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Search and filter conversations

    AC4: Search and Filter Conversations
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        is_guest = context.get("is_guest")

        supabase = get_supabase_client()

        # Build query with full-text search
        q = supabase.table('conversation_history').select('*', count='exact')

        # User/session filter
        if is_guest:
            q = q.is_('user_id', 'null').eq('session_id', session_id)
        else:
            q = q.or_(f'user_id.eq.{user_id},and(user_id.is.null,session_id.eq.{session_id})')

        # Full-text search on summary and title
        if query:
            # Use PostgreSQL full-text search
            q = q.text_search('summary', query)

        # Vehicle filters (search in vehicles_discussed JSONB)
        if vehicle_make or vehicle_model:
            # This would require a more complex JSONB query
            # For now, simplified: filter on preferences_json containing the vehicle
            pass  # TODO: Implement JSONB containment query

        # Date range filter
        if date_from:
            q = q.gte('conversation_date', date_from.isoformat())
        if date_to:
            q = q.lte('conversation_date', date_to.isoformat())

        # Journey stage filter
        if journey_stage:
            q = q.eq('journey_stage', journey_stage)

        # Ordering and pagination
        offset = (page - 1) * page_size
        q = q.order('last_message_at', desc=True).range(offset, offset + page_size - 1)

        result = q.execute()
        total = result.count if result.count is not None else len(result.data)

        # Convert to response models
        conversations = []
        for row in result.data:
            conversations.append(ConversationHistoryItem(
                id=row.get('id', ''),
                user_id=row.get('user_id'),
                session_id=row.get('session_id', ''),
                title=row.get('title', 'Conversation'),
                summary=row.get('summary'),
                started_at=row.get('started_at'),
                last_message_at=row.get('last_message_at'),
                message_count=row.get('message_count', 0),
                journey_stage=row.get('journey_stage', 'discovery'),
                evolution_detected=row.get('evolution_detected', False),
                top_preferences=row.get('top_preferences'),
                vehicles_mentioned_count=row.get('vehicles_mentioned_count', 0),
                retention_days=row.get('retention_days', 90),
                expires_at=row.get('expires_at'),
                date_display=row.get('date_display', ''),
                message_count_display=row.get('message_count_display', '')
            ))

        return ConversationHistoryResponse(
            conversations=conversations,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to search conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@conversations_router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Delete a specific conversation

    AC6: Data Retention and Privacy - Manual deletion
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)

        supabase = get_supabase_client()

        # Soft delete (mark as deleted, don't actually remove)
        result = supabase.table('conversation_history').update({
            'status': 'deleted',
            'is_marked_for_deletion': True
        }).eq('id', conversation_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "message": "Conversation deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@conversations_router.delete("/history")
async def delete_all_conversations(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Clear all conversation history

    AC6: Data Retention and Privacy - Clear all history
    """
    try:
        # Get user context
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")
        session_id = context.get("session_id")

        supabase = get_supabase_client()

        # Mark all conversations as deleted
        query = supabase.table('conversation_history').update({
            'status': 'deleted',
            'is_marked_for_deletion': True
        })

        if user_id:
            query = query.eq('user_id', user_id)
        else:
            query = query.is_('user_id', 'null').eq('session_id', session_id)

        result = query.execute()

        return {
            "success": True,
            "message": f"Deleted {len(result.data)} conversations"
        }

    except Exception as e:
        logger.error(f"Failed to delete all conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@conversations_router.get("/privacy/retention", response_model=DataRetentionPolicy)
async def get_retention_policy(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Get current data retention policy"""
    try:
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")

        if not user_id:
            # Guest users get default policy
            return DataRetentionPolicy()

        supabase = get_supabase_client()
        result = supabase.table('data_retention_policies').select('*').eq('user_id', user_id).execute()

        if result.data:
            row = result.data[0]
            return DataRetentionPolicy(
                default_retention_days=row.get('default_retention_days', 90),
                auto_delete_enabled=row.get('auto_delete_enabled', True),
                delete_on_account_closure=row.get('delete_on_account_closure', True),
                allow_anonymous_usage=row.get('allow_anonymous_usage', False),
                share_conversations_with_sellers=row.get('share_conversations_with_sellers', False)
            )

        # Default policy if none set
        return DataRetentionPolicy()

    except Exception as e:
        logger.error(f"Failed to get retention policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@conversations_router.put("/privacy/retention")
async def update_retention_policy(
    policy: DataRetentionPolicy,
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Update data retention policy"""
    try:
        context = await get_user_context(authorization, x_session_id)
        user_id = context.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Must be authenticated to set retention policy")

        supabase = get_supabase_client()

        # Check if policy exists
        existing = supabase.table('data_retention_policies').select('*').eq('user_id', user_id).execute()

        policy_data = {
            'default_retention_days': policy.default_retention_days,
            'auto_delete_enabled': policy.auto_delete_enabled,
            'delete_on_account_closure': policy.delete_on_account_closure,
            'allow_anonymous_usage': policy.allow_anonymous_usage,
            'share_conversations_with_sellers': policy.share_conversations_with_sellers,
            'last_updated_at': datetime.now().isoformat()
        }

        if existing.data:
            # Update existing
            result = supabase.table('data_retention_policies').update(policy_data).eq('user_id', user_id).execute()
        else:
            # Create new
            policy_data['user_id'] = user_id
            result = supabase.table('data_retention_policies').insert(policy_data).execute()

        return {"success": True, "message": "Retention policy updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update retention policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export endpoints will be implemented in Task 2-7.5 (conversation_export_service)
# TODO: Implement GET /api/v1/conversations/export, POST /api/v1/conversations/export/request
