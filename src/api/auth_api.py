"""
Authentication API endpoints for Otto.AI

Handles:
- Session merge for guest-to-account transitions
- Guest session management
- Optional authentication middleware
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, Cookie
from pydantic import BaseModel, EmailStr, ValidationError

# Import Zep client for session management
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.zep_client import ZepClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize Zep client
zep_client: Optional[ZepClient] = None


async def get_zep_client() -> ZepClient:
    """Get or initialize Zep client"""
    global zep_client
    if zep_client is None:
        zep_client = ZepClient()
        await zep_client.initialize()
    return zep_client


# Request/Response Models
class MergeSessionRequest(BaseModel):
    """Request to merge guest session to user account"""
    session_id: str
    user_id: str


class MergeSessionResponse(BaseModel):
    """Response from session merge operation"""
    success: bool
    messages_transferred: int = 0
    preferences_preserved: list = []
    guest_session_id: Optional[str] = None
    user_session_id: Optional[str] = None
    error: Optional[str] = None


class SessionContextResponse(BaseModel):
    """Response with guest session context for welcome back greeting"""
    is_returning_visitor: bool = False
    last_visit_date: Optional[str] = None
    previous_preferences: list = []
    message_count: int = 0
    greeting: Optional[str] = None


@auth_router.post("/merge-session", response_model=MergeSessionResponse)
async def merge_session_to_account(
    request: MergeSessionRequest,
    http_request: Request
) -> MergeSessionResponse:
    """
    Merge guest session to authenticated user account

    This endpoint is called during signup/login to preserve conversation
    context from the anonymous session before authentication.

    Process:
    1. Retrieves all messages from guest session
    2. Creates or updates user's persistent session
    3. Transfers all messages to user session
    4. Marks guest session for cleanup (audit trail preserved)

    Example:
        POST /api/auth/merge-session
        {
            "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "user_id": "user@example.com"
        }

        Response:
        {
            "success": true,
            "messages_transferred": 15,
            "preferences_preserved": ["SUV preference", "Budget: $30000"],
            "guest_session_id": "a1b2c3d4...",
            "user_session_id": "user@example.com"
        }
    """
    try:
        client = await get_zep_client()

        # Validate request
        if not request.session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        logger.info(f"Merging session {request.session_id} to user {request.user_id}")

        # Perform merge
        result = await client.merge_session_to_user(
            session_id=request.session_id,
            user_id=request.user_id
        )

        logger.info(
            f"Session merge successful: {result['messages_transferred']} messages transferred, "
            f"{len(result.get('preferences_preserved', []))} preferences preserved"
        )

        # Set cookie to clear guest session (client will handle this)
        # But we also want to clear it server-side for security

        return MergeSessionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to merge session: {str(e)}"
        )


@auth_router.get("/session/{session_id}/context", response_model=SessionContextResponse)
async def get_session_context(session_id: str) -> SessionContextResponse:
    """
    Get guest session context for "Welcome back!" greeting

    Returns information about the guest's previous visit including:
    - Last visit date
    - Previous preferences extracted from conversations
    - Message count
    - Personalized greeting message

    Example:
        GET /api/auth/session/a1b2c3d4-e5f6-7890-abcd-ef1234567890/context

        Response:
        {
            "is_returning_visitor": true,
            "last_visit_date": "2025-01-10T14:30:00Z",
            "previous_preferences": ["SUVs", "Budget: $30000"],
            "message_count": 12,
            "greeting": "Welcome back! Last time you were looking at SUVs under $30000"
        }
    """
    try:
        client = await get_zep_client()

        # Get session context
        context = await client.get_last_visit_context(session_id)

        if not context:
            return SessionContextResponse(
                is_returning_visitor=False,
                greeting="Welcome! I'm Otto, your AI car shopping assistant. How can I help you today?"
            )

        # Generate personalized greeting
        greeting = None
        if context.get('is_returning_visitor') and context.get('previous_preferences'):
            prefs = context['previous_preferences']
            if prefs:
                if len(prefs) == 1:
                    greeting = f"Welcome back! Last time you were looking at {prefs[0]}"
                elif len(prefs) == 2:
                    greeting = f"Welcome back! Last time you were looking at {prefs[0]} and {prefs[1]}"
                else:
                    greeting = f"Welcome back! Last time you were exploring options like {prefs[0]}"

        return SessionContextResponse(
            is_returning_visitor=context.get('is_returning_visitor', False),
            last_visit_date=context.get('last_visit_date'),
            previous_preferences=context.get('previous_preferences', []),
            message_count=context.get('message_count', 0),
            greeting=greeting or "Welcome! I'm Otto, your AI car shopping assistant."
        )

    except Exception as e:
        logger.error(f"Failed to get session context: {e}", exc_info=True)
        # Return default context rather than error
        return SessionContextResponse(
            is_returning_visitor=False,
            greeting="Welcome! I'm Otto, your AI car shopping assistant."
        )


@auth_router.post("/session/create")
async def create_guest_session(request: Request) -> Dict[str, Any]:
    """
    Create a new guest session

    Generates a UUID-based session ID for anonymous users.
    The session ID will be stored in a cookie on the client.

    Example:
        POST /api/auth/session/create

        Response:
        {
            "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "created_at": "2025-01-12T10:00:00Z",
            "expires_at": "2025-02-11T10:00:00Z"
        }
    """
    import uuid
    from datetime import timedelta

    session_id = str(uuid.uuid4())
    created_at = datetime.now()
    expires_at = created_at + timedelta(days=30)

    try:
        client = await get_zep_client()
        await client.create_guest_session(session_id)

        logger.info(f"Created guest session: {session_id}")

        return {
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "message": "Guest session created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create guest session: {e}", exc_info=True)
        # Return session ID anyway (frontend can still function)
        return {
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "message": "Session created (Zep Cloud unavailable)"
        }


@auth_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for auth service"""
    return {
        "service": "authentication",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "zep_client_initialized": zep_client is not None and zep_client.initialized
    }
