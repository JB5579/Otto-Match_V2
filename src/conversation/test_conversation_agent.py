"""
Test Suite for Conversation Agent
Tests for the Otto AI conversation processing system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.conversation.conversation_agent import (
    ConversationAgent,
    ConversationResponse,
    DialogueState
)
from src.memory.zep_client import ZepClient, ConversationContext, Message
from src.conversation.groq_client import GroqClient
from src.cache.multi_level_cache import MultiLevelCache


class TestConversationAgent:
    """Test conversation agent functionality"""

    @pytest.fixture
    def mock_zep_client(self):
        """Create mock Zep client"""
        client = AsyncMock(spec=ZepClient)
        client.initialize.return_value = True
        client.initialized = True
        client.store_conversation.return_value = True
        client.get_contextual_memory.return_value = ConversationContext(
            working_memory=[],
            episodic_memory=[],
            semantic_memory={},
            user_preferences={}
        )
        return client

    @pytest.fixture
    def mock_groq_client(self):
        """Create mock Groq client"""
        client = AsyncMock(spec=GroqClient)
        client.initialize.return_value = True
        client.initialized = True
        client.analyze_message_intent.return_value = {
            'success': True,
            'analysis': {
                'intent': 'search',
                'entities': {
                    'vehicle_types': ['suv'],
                    'budget': {'max': 30000}
                },
                'confidence': 0.95
            }
        }
        client.format_conversation_response.return_value = "I found some great SUVs for you!"
        client.generate_vehicle_search_query.return_value = "SUV under 30000"
        return client

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache"""
        cache = AsyncMock(spec=MultiLevelCache)
        cache.initialize.return_value = True
        cache.get.return_value = None
        cache.set.return_value = True
        return cache

    @pytest.fixture
    def conversation_agent(self, mock_zep_client, mock_groq_client, mock_cache):
        """Create conversation agent with mocked dependencies"""
        return ConversationAgent(
            zep_client=mock_zep_client,
            groq_client=mock_groq_client,
            cache=mock_cache
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self, conversation_agent):
        """Test agent initialization"""
        # Should initialize successfully with mocked dependencies
        result = await conversation_agent.initialize()
        assert result == True
        assert conversation_agent.initialized == True

    @pytest.mark.asyncio
    async def test_process_greeting_message(self, conversation_agent):
        """Test processing greeting messages"""
        # Initialize agent
        await conversation_agent.initialize()

        # Process greeting
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="Hello Otto!",
            session_id="test_session"
        )

        assert isinstance(response, ConversationResponse)
        assert response.response_type == 'text'
        assert "Welcome" in response.message or "Hello" in response.message
        assert response.needs_follow_up == True
        assert response.processing_time_ms is not None

    @pytest.mark.asyncio
    async def test_process_search_message(self, conversation_agent):
        """Test processing search messages"""
        # Initialize agent
        await conversation_agent.initialize()

        # Process search intent
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="I'm looking for an SUV under $30,000",
            session_id="test_session"
        )

        assert isinstance(response, ConversationResponse)
        assert response.response_type in ['text', 'vehicle_results']
        assert "search" in response.message.lower() or "suv" in response.message.lower()
        assert response.needs_follow_up == True

    @pytest.mark.asyncio
    async def test_conversation_state_tracking(self, conversation_agent):
        """Test conversation state tracking"""
        # Initialize agent
        await conversation_agent.initialize()

        # Process first message
        await conversation_agent.process_message(
            user_id="test_user",
            message="Hi Otto!",
            session_id="test_session"
        )

        # Check dialogue state
        state = conversation_agent.dialogue_states.get("test_user")
        assert state is not None
        assert state.stage == 'discovery'

        # Process second message
        await conversation_agent.process_message(
            user_id="test_user",
            message="Show me SUVs",
            session_id="test_session"
        )

        # Check updated state
        state = conversation_agent.dialogue_states.get("test_user")
        assert state.stage in ['recommendation', 'refinement']
        assert state.last_query == "Show me SUVs"

    @pytest.mark.asyncio
    async def test_conversation_summary(self, conversation_agent):
        """Test conversation summary generation"""
        # Initialize agent
        await conversation_agent.initialize()

        # Add some dialogue state
        conversation_agent.dialogue_states["test_user"] = DialogueState(
            stage='recommendation',
            user_intent='search',
            collected_info={'vehicle_types': ['suv'], 'budget': 30000},
            last_query='Show me SUVs',
            conversation_summary='Looking for SUVs'
        )

        # Get summary
        summary = await conversation_agent.get_conversation_summary("test_user")

        assert 'dialogue_stage' in summary
        assert summary['dialogue_stage'] == 'recommendation'
        assert summary['user_intent'] == 'search'
        assert 'collected_preferences' in summary
        assert summary['collected_preferences']['vehicle_types'] == ['suv']

    @pytest.mark.asyncio
    async def test_reset_conversation(self, conversation_agent):
        """Test conversation reset"""
        # Initialize agent
        await conversation_agent.initialize()

        # Add dialogue state
        conversation_agent.dialogue_states["test_user"] = DialogueState(
            stage='recommendation',
            user_intent='search'
        )

        # Reset conversation
        result = await conversation_agent.reset_conversation("test_user")
        assert result == True
        assert "test_user" not in conversation_agent.dialogue_states

    @pytest.mark.asyncio
    async def test_health_check(self, conversation_agent):
        """Test health check functionality"""
        # Initialize agent
        await conversation_agent.initialize()

        # Check health
        health = await conversation_agent.health_check()

        assert 'initialized' in health
        assert health['initialized'] == True
        assert 'zep_client' in health
        assert 'groq_client' in health
        assert 'active_dialogues' in health

    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_agent):
        """Test error handling in message processing"""
        # Initialize agent
        await conversation_agent.initialize()

        # Mock Groq client to raise error
        conversation_agent.groq_client.analyze_message_intent.side_effect = Exception("API Error")

        # Process message
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="Test message",
            session_id="test_session"
        )

        assert response.response_type == 'error'
        assert "trouble processing" in response.message.lower()

    @pytest.mark.asyncio
    async def test_with_no_zep(self, mock_groq_client, mock_cache):
        """Test agent behavior without Zep client"""
        # Create agent with Zep client that fails to initialize
        mock_zep_client = AsyncMock(spec=ZepClient)
        mock_zep_client.initialize.return_value = False
        mock_zep_client.initialized = False

        agent = ConversationAgent(
            zep_client=mock_zep_client,
            groq_client=mock_groq_client,
            cache=mock_cache
        )

        # Should still initialize without Zep
        result = await agent.initialize()
        assert result == True  # Groq is the critical dependency

        # Process message should still work
        response = await agent.process_message(
            user_id="test_user",
            message="Hello",
            session_id="test_session"
        )

        assert isinstance(response, ConversationResponse)
        assert response.message is not None

    @pytest.mark.asyncio
    async def test_with_no_groq(self, mock_zep_client, mock_cache):
        """Test agent behavior without Groq client"""
        # Create agent with Groq client that fails to initialize
        mock_groq_client = AsyncMock(spec=GroqClient)
        mock_groq_client.initialize.return_value = False
        mock_groq_client.initialized = False

        agent = ConversationAgent(
            zep_client=mock_zep_client,
            groq_client=mock_groq_client,
            cache=mock_cache
        )

        # Should fail to initialize without Groq
        result = await agent.initialize()
        assert result == False

    @pytest.mark.asyncio
    async def test_conversation_memory_storage(self, conversation_agent, mock_zep_client):
        """Test that messages are stored in Zep"""
        await conversation_agent.initialize()

        # Process message
        await conversation_agent.process_message(
            user_id="test_user",
            message="Test message",
            session_id="test_session"
        )

        # Verify Zep store_conversation was called
        mock_zep_client.store_conversation.assert_called()

        # Check the call arguments
        call_args = mock_zep_client.store_conversation.call_args
        assert call_args[0][0] == "test_user"  # user_id
        assert call_args[0][1].user_id == "test_user"  # conversation_data.user_id

    @pytest.mark.asyncio
    async def test_performance_timing(self, conversation_agent):
        """Test performance timing is recorded"""
        await conversation_agent.initialize()

        # Process message
        start = datetime.now()
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="Test performance",
            session_id="test_session"
        )
        end = datetime.now()

        # Verify processing time is recorded
        assert response.processing_time_ms is not None
        assert response.processing_time_ms > 0
        # Should be close to actual time (allowing for test overhead)
        actual_ms = (end - start).total_seconds() * 1000
        assert abs(response.processing_time_ms - actual_ms) < 100  # Within 100ms

    @pytest.mark.asyncio
    async def test_vehicle_search_integration(self, conversation_agent):
        """Test integration with vehicle search (mocked)"""
        await conversation_agent.initialize()

        # Configure mock for search intent
        conversation_agent.groq_client.analyze_message_intent.return_value = {
            'success': True,
            'analysis': {
                'intent': 'search',
                'entities': {
                    'vehicle_types': ['sedan', 'electric'],
                    'brands': ['tesla'],
                    'features': ['autopilot']
                },
                'confidence': 0.90
            }
        }

        # Process search query
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="I want an electric Tesla sedan with autopilot",
            session_id="test_session"
        )

        assert response.response_type == 'vehicle_results'
        assert response.metadata is not None
        assert 'search_query' in response.metadata
        assert 'criteria' in response.metadata


# Run tests if executed directly
if __name__ == "__main__":
    print("Running Conversation Agent Tests...")
    pytest.main([__file__, "-v"])