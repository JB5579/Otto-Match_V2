"""
Test Suite for Zep Cloud Client
Tests for temporal memory and conversation context management
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.memory.zep_client import (
    ZepClient,
    Message,
    ConversationData,
    ConversationContext
)


class TestZepClient:
    """Test Zep Cloud client functionality"""

    @pytest.fixture
    def zep_client(self):
        """Create Zep client instance"""
        return ZepClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful client initialization"""
        with patch('src.memory.zep_client.Zep') as mock_zep:
            # Setup mock
            mock_client = AsyncMock()
            mock_client.session.list = AsyncMock(return_value=[])
            mock_zep.return_value = mock_client

            # Initialize client
            client = ZepClient(api_key="test_key")
            result = await client.initialize()

            assert result == True
            assert client.initialized == True
            assert client.client is not None

    @pytest.mark.asyncio
    async def test_initialization_no_api_key(self):
        """Test initialization failure without API key"""
        client = ZepClient(api_key=None)
        result = await client.initialize()
        assert result == False

    @pytest.mark.asyncio
    async def test_initialization_no_zep_sdk(self):
        """Test initialization without Zep SDK"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', False):
            client = ZepClient(api_key="test_key")
            result = await client.initialize()
            assert result == False

    @pytest.mark.asyncio
    async def test_create_session(self, zep_client):
        """Test session creation"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_zep.session.get = AsyncMock(side_effect=Exception("Not found"))
                mock_zep.session.add = AsyncMock()
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Create session
                session_id = await zep_client.create_session("user123")

                assert session_id is not None
                assert "user123" in session_id
                assert "session_" in session_id

                # Verify session.add was called
                mock_zep.session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_conversation(self, zep_client):
        """Test conversation storage"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_zep.session.add = AsyncMock()
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Create conversation data
                messages = [
                    Message(role="user", content="Hello"),
                    Message(role="assistant", content="Hi there!")
                ]
                conversation_data = ConversationData(
                    messages=messages,
                    user_id="user123",
                    session_id="session123"
                )

                # Store conversation
                result = await zep_client.store_conversation("user123", conversation_data)

                assert result == True
                mock_zep.session.add.assert_called_once()

                # Verify the call arguments
                call_args = mock_zep.session.add.call_args
                assert call_args[1]["session_id"] == "session123"
                assert call_args[1]["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, zep_client):
        """Test conversation history retrieval"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_message = MagicMock()
                mock_message.role = "user"
                mock_message.content = "Hello"
                mock_message.created_at = datetime.now()
                mock_message.metadata = {"test": "data"}
                mock_zep.message.get = AsyncMock(return_value=[mock_message])
                mock_zep.session.list = AsyncMock(return_value=[
                    MagicMock(session_id="session123")
                ])
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Get history
                messages = await zep_client.get_conversation_history("user123")

                assert len(messages) == 1
                assert messages[0].role == "user"
                assert messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_search_conversations(self, zep_client):
        """Test conversation search"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_result = MagicMock()
                mock_result.session_id = "session123"
                mock_result.role = "user"
                mock_result.content = "Looking for SUV"
                mock_result.score = 0.95
                mock_result.created_at = datetime.now()
                mock_result.metadata = {}
                mock_zep.memory.search = AsyncMock(return_value=[mock_result])
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Search conversations
                results = await zep_client.search_conversations(
                    user_id="user123",
                    query="SUV",
                    limit=5
                )

                assert len(results) == 1
                assert results[0]["session_id"] == "session123"
                assert results[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_get_contextual_memory(self, zep_client):
        """Test contextual memory retrieval"""
        # Mock the methods
        zep_client.get_conversation_history = AsyncMock(return_value=[
            Message(role="user", content="I like SUVs"),
            Message(role="assistant", content="I found some SUVs for you")
        ])
        zep_client.search_conversations = AsyncMock(return_value=[
            {"session_id": "session1", "content": "User likes electric vehicles"}
        ])
        zep_client._extract_user_knowledge = AsyncMock(return_value={})
        zep_client._extract_user_preferences = AsyncMock(return_value={
            "vehicle_types": ["SUV", "electric"]
        })

        # Get contextual memory
        context = await zep_client.get_contextual_memory("user123", "SUV search")

        assert isinstance(context, ConversationContext)
        assert len(context.working_memory) == 2
        assert len(context.episodic_memory) == 1
        assert context.user_preferences["vehicle_types"] == ["SUV", "electric"]

    @pytest.mark.asyncio
    async def test_extract_user_preferences(self, zep_client):
        """Test user preference extraction from messages"""
        messages = [
            Message(role="user", content="I want an SUV under $30,000"),
            Message(role="user", content="It needs to be electric and have autopilot"),
            Message(role="user", content="My family has 4 people")
        ]

        # Extract preferences
        preferences = await zep_client._extract_user_preferences(messages)

        assert "budget" in preferences
        assert "vehicle_types" in preferences
        assert "features" in preferences
        assert "family_size" in preferences
        assert preferences["family_size"] == 4

    @pytest.mark.asyncio
    async def test_delete_session(self, zep_client):
        """Test session deletion"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_zep.session.delete = AsyncMock()
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Delete session
                result = await zep_client.delete_session("session123")

                assert result == True
                mock_zep.session.delete.assert_called_once_with("session123")

    @pytest.mark.asyncio
    async def test_get_session_stats(self, zep_client):
        """Test session statistics retrieval"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock
                mock_zep = AsyncMock()
                mock_session = MagicMock()
                mock_session.updated_at = datetime.now()
                mock_zep.session.list = AsyncMock(return_value=[mock_session])
                mock_zep.message.get = AsyncMock(return_value=[
                    MagicMock(), MagicMock(), MagicMock()
                ])
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Get stats
                stats = await zep_client.get_session_stats("user123")

                assert "total_sessions" in stats
                assert "total_messages" in stats
                assert "average_messages_per_session" in stats
                assert stats["total_sessions"] == 1

    @pytest.mark.asyncio
    async def test_cache_integration(self, zep_client):
        """Test cache integration for conversation data"""
        mock_cache = AsyncMock()
        zep_client.cache = mock_cache

        # Test cache miss
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        # Store conversation
        conversation_data = ConversationData(
            messages=[Message(role="user", content="Test")],
            user_id="user123"
        )

        await zep_client.store_conversation("user123", conversation_data)

        # Verify cache set was called
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, zep_client):
        """Test error handling in Zep operations"""
        with patch('src.memory.zep_client.ZEP_AVAILABLE', True):
            with patch('src.memory.zep_client.Zep') as mock_zep_class:
                # Setup mock to raise error
                mock_zep = AsyncMock()
                mock_zep.session.add = AsyncMock(side_effect=Exception("Zep Error"))
                mock_zep_class.return_value = mock_zep

                # Initialize client
                zep_client.client = mock_zep
                zep_client.initialized = True

                # Try to store conversation (should handle error gracefully)
                conversation_data = ConversationData(
                    messages=[Message(role="user", content="Test")],
                    user_id="user123"
                )

                result = await zep_client.store_conversation("user123", conversation_data)
                assert result == False

    @pytest.mark.asyncio
    async def test_health_check(self, zep_client):
        """Test health check functionality"""
        # Test not initialized
        health = await zep_client.health_check()
        assert health["initialized"] == False

        # Test initialized without SDK
        with patch('src.memory.zep_client.ZEP_AVAILABLE', False):
            health = await zep_client.health_check()
            assert health["initialized"] == False
            assert health["zep_available"] == False

        # Test initialized with SDK but no key
        zep_client.api_key = None
        health = await zep_client.health_check()
        assert health["api_key_configured"] == False


# Run tests if executed directly
if __name__ == "__main__":
    print("Running Zep Client Tests...")
    pytest.main([__file__, "-v"])