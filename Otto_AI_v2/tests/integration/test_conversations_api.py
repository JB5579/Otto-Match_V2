"""
Integration tests for Conversations API endpoints

Story: 2-7.13 - Create backend test suite
Tests conversation history API endpoints with mocked dependencies
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import Mock, AsyncMock, patch

from src.api.conversations_api import conversations_router
from src.services.conversation_summary_service import ConversationSummary
from src.memory.zep_client import Message


# Create test app
@pytest.fixture
def test_app():
    """Create test FastAPI app"""
    app = FastAPI()
    app.include_router(conversations_router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create test HTTP client"""
    return AsyncClient(app=test_app, base_url="http://test")


@pytest.fixture
def mock_session_id():
    """Mock session ID for guest users"""
    return "test-session-123"


@pytest.fixture
def mock_user_id():
    """Mock user ID for authenticated users"""
    return "test-user-123"


@pytest.fixture
def mock_conversation_history():
    """Mock conversation history data"""
    return [
        {
            "id": "conv-1",
            "user_id": None,
            "session_id": "test-session-123",
            "title": "Family SUV Search",
            "summary": "Looking for Toyota RAV4 under $30000",
            "started_at": "2026-01-15T10:00:00",
            "last_message_at": "2026-01-15T10:30:00",
            "message_count": 15,
            "journey_stage": "consideration",
            "evolution_detected": False,
            "top_preferences": [
                {"category": "budget", "key": "max", "value": 30000},
                {"category": "vehicle_types", "key": "SUV", "value": "SUV"}
            ],
            "vehicles_mentioned_count": 3,
            "retention_days": 90,
            "expires_at": "2026-04-15T10:00:00",
            "date_display": "Jan 15, 2026",
            "message_count_display": "15 messages"
        },
        {
            "id": "conv-2",
            "user_id": None,
            "session_id": "test-session-123",
            "title": "Electric Vehicle Research",
            "summary": "Exploring Tesla and Rivian options",
            "started_at": "2026-01-10T14:00:00",
            "last_message_at": "2026-01-10T15:30:00",
            "message_count": 8,
            "journey_stage": "discovery",
            "evolution_detected": True,
            "top_preferences": [],
            "vehicles_mentioned_count": 2,
            "retention_days": 90,
            "expires_at": "2026-04-10T14:00:00",
            "date_display": "Jan 10, 2026",
            "message_count_display": "8 messages"
        }
    ]


# =================================================================
# Conversation History Endpoint Tests
# =================================================================

@pytest.mark.asyncio
class TestConversationHistoryEndpoint:

    async def test_get_conversation_history_guest_user(
        self,
        test_client,
        mock_session_id,
        mock_conversation_history
    ):
        """Test GET /api/v1/conversations/history for guest users"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            # Mock Supabase response
            mock_result = Mock()
            mock_result.data = mock_conversation_history
            mock_result.count = len(mock_conversation_history)
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/history",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert "conversations" in data
            assert len(data["conversations"]) == 2
            assert data["total"] == 2
            assert data["page"] == 1

            # Verify first conversation
            conv = data["conversations"][0]
            assert conv["title"] == "Family SUV Search"
            assert conv["session_id"] == mock_session_id

    async def test_get_conversation_history_missing_session_header(
        self,
        test_client
    ):
        """Test that missing session header returns 401"""
        response = await test_client.get("/api/v1/conversations/history")

        assert response.status_code == 401

    async def test_get_conversation_history_with_filters(
        self,
        test_client,
        mock_session_id,
        mock_conversation_history
    ):
        """Test filtering by journey stage"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = [mock_conversation_history[0]]  # Only first conv matches
            mock_result.count = 1
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/history?journey_stage=consideration",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["conversations"]) == 1
            assert data["conversations"][0]["journey_stage"] == "consideration"


# =================================================================
# Conversation Detail Endpoint Tests
# =================================================================

@pytest.mark.asyncio
class TestConversationDetailEndpoint:

    async def test_get_conversation_detail(
        self,
        test_client,
        mock_session_id
    ):
        """Test GET /api/v1/conversations/history/{id}"""
        conversation_data = {
            "id": "conv-1",
            "session_id": mock_session_id,
            "user_id": None,
            "title": "Test Conversation",
            "summary": "Test summary",
            "started_at": "2026-01-15T10:00:00",
            "last_message_at": "2026-01-15T10:30:00",
            "message_count": 5,
            "preferences_json": {"budget": {"max": 30000}},
            "vehicles_discussed": [],
            "journey_stage": "discovery",
            "evolution_detected": False,
            "status": "active",
            "retention_days": 90,
            "expires_at": "2026-04-15T10:00:00"
        }

        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = [conversation_data]
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/history/conv-1",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == "conv-1"
            assert data["title"] == "Test Conversation"
            assert data["preferences"]["budget"]["max"] == 30000

    async def test_get_conversation_detail_not_found(
        self,
        test_client,
        mock_session_id
    ):
        """Test that non-existent conversation returns 404"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = []
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/history/non-existent",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 404


# =================================================================
# Journey Summary Endpoint Tests
# =================================================================

@pytest.mark.asyncio
class TestJourneySummaryEndpoint:

    async def test_get_journey_summary(
        self,
        test_client,
        mock_session_id
    ):
        """Test GET /api/v1/conversations/summary"""
        journey_data = {
            "identifier": mock_session_id,
            "user_id": None,
            "first_conversation": "2026-01-10T14:00:00",
            "last_conversation": "2026-01-15T10:30:00",
            "total_conversations": 5,
            "total_messages": 42,
            "stages_visited": ["discovery", "consideration"],
            "current_stage": "consideration",
            "all_vehicles_discussed": [
                {"make": "Toyota", "model": "RAV4"},
                {"make": "Honda", "model": "CR-V"}
            ],
            "active_preferences": [
                {"category": "budget", "key": "max", "value": 30000, "confidence": 0.9}
            ],
            "preferences_evolved": True
        }

        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = [journey_data]
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/summary",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_conversations"] == 5
            assert data["total_messages"] == 42
            assert data["current_stage"] == "consideration"
            assert data["preferences_evolved"] is True
            assert len(data["all_vehicles_discussed"]) == 2

    async def test_get_journey_summary_empty(self, test_client, mock_session_id):
        """Test journey summary for user with no conversations"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = []
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/summary",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_conversations"] == 0
            assert data["total_messages"] == 0


# =================================================================
# Delete Conversation Endpoint Tests
# =================================================================

@pytest.mark.asyncio
class TestDeleteConversationEndpoint:

    async def test_delete_conversation(
        self,
        test_client,
        mock_session_id
    ):
        """Test DELETE /api/v1/conversations/{id}"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = [{"id": "conv-1"}]
            mock_supabase.return_value.table.return_value.update.return_value.execute.return_value = mock_result

            response = await test_client.delete(
                "/api/v1/conversations/history/conv-1",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "deleted" in data["message"].lower()

    async def test_delete_conversation_not_found(self, test_client, mock_session_id):
        """Test deleting non-existent conversation"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = []
            mock_supabase.return_value.table.return_value.update.return_value.execute.return_value = mock_result

            response = await test_client.delete(
                "/api/v1/conversations/history/non-existent",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 404


# =================================================================
# Search Endpoint Tests
# =================================================================

@pytest.mark.asyncio
class TestSearchConversationsEndpoint:

    async def test_search_conversations(
        self,
        test_client,
        mock_session_id,
        mock_conversation_history
    ):
        """Test GET /api/v1/conversations/search"""
        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            mock_result = Mock()
            mock_result.data = [mock_conversation_history[0]]  # Only SUV conv matches "SUV"
            mock_result.count = 1
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result

            response = await test_client.get(
                "/api/v1/conversations/search?query=SUV",
                headers={"X-Session-ID": mock_session_id}
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["conversations"]) == 1
            assert data["conversations"][0]["title"] == "Family SUV Search"

    async def test_search_conversations_min_query_length(self, test_client, mock_session_id):
        """Test that search query must be at least 2 characters"""
        response = await test_client.get(
            "/api/v1/conversations/search?query=X",
            headers={"X-Session-ID": mock_session_id}
        )

        # Should fail validation (422) or return empty
        assert response.status_code in [400, 422]


# =================================================================
# Privacy Settings Tests
# =================================================================

@pytest.mark.asyncio
class TestPrivacySettingsEndpoint:

    async def test_get_retention_policy(
        self,
        test_client,
        mock_session_id
    ):
        """Test GET /api/v1/conversations/privacy/retention"""
        response = await test_client.get(
            "/api/v1/conversations/privacy/retention",
            headers={"X-Session-ID": mock_session_id}
        )

        # Guest users get default policy
        assert response.status_code == 200
        data = response.json()

        assert "default_retention_days" in data
        assert data["default_retention_days"] == 90

    async def test_update_retention_policy(
        self,
        test_client,
        mock_session_id,
        mock_user_id
    ):
        """Test PUT /api/v1/conversations/privacy/retention"""
        policy_data = {
            "default_retention_days": 180,
            "auto_delete_enabled": False
        }

        with patch('src.api.conversations_api.get_supabase_client') as mock_supabase:
            # For authenticated users
            mock_result = Mock()
            mock_result.data = []
            mock_supabase.return_value.table.return_value.select.return_value.execute.return_value = mock_result
            mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = mock_result

            response = await test_client.put(
                "/api/v1/conversations/privacy/retention",
                headers={
                    "Authorization": f"Bearer {mock_user_id}",
                    "X-Session-ID": mock_session_id
                },
                json=policy_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
