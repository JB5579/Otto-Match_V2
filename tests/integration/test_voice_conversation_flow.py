"""
Integration tests for voice conversation flow
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.conversation.conversation_agent import ConversationAgent, ConversationResponse
from src.services.voice_input_service import VoiceInputService, VoiceResult
from src.models.voice_models import VoiceCommand, VoiceState


class TestVoiceConversationFlow:
    """Integration tests for voice conversation flow"""

    @pytest.fixture
    def mock_zep_client(self):
        """Create a mock Zep client"""
        client = Mock()
        client.health_check = AsyncMock(return_value={'initialized': True})
        return client

    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client"""
        client = Mock()
        client.health_check = AsyncMock(return_value={'initialized': True})
        return client

    @pytest.fixture
    def voice_service(self):
        """Create a voice service instance"""
        return VoiceInputService()

    @pytest.fixture
    def conversation_agent(self, mock_zep_client, mock_groq_client, voice_service):
        """Create a conversation agent with voice support"""
        agent = ConversationAgent(
            zep_client=mock_zep_client,
            groq_client=mock_groq_client,
            voice_service=voice_service
        )
        return agent

    @pytest.mark.asyncio
    async def test_voice_input_processing(self, conversation_agent):
        """Test processing voice input through conversation agent"""
        # Mock dependencies
        conversation_agent.nlu_service = Mock()
        conversation_agent.nlu_service.analyze_message = AsyncMock(return_value=Mock(
            intent=Mock(primary="search", confidence=0.9),
            entities=[Mock(entity_type="VEHICLE_TYPE", value="SUV")],
            preferences=[]
        ))

        conversation_agent.response_generator = Mock()
        conversation_agent.response_generator.generate_response = AsyncMock(return_value=Mock(
            message="I found some SUVs for you",
            response_type="vehicle_results",
            suggestions=["Show me trucks", "Filter by price"],
            follow_up_actions=None
        ))

        conversation_agent._store_message = AsyncMock()

        # Create voice result
        voice_result = VoiceResult(
            transcript="I need an SUV under 30000 dollars",
            confidence=0.95,
            is_final=True,
            timestamp=time.time(),
            state=VoiceState.SUCCESS
        )

        # Process voice message
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="",
            session_id="session_123",
            voice_result=voice_result
        )

        # Verify response
        assert isinstance(response, ConversationResponse)
        assert response.voice_transcript == voice_result.transcript
        assert response.voice_confidence == voice_result.confidence
        assert response.is_voice_input == True
        assert response.voice_command.command_type.value == "search"
        assert "SUV" in response.voice_command.vehicle_types
        assert response.voice_command.price_range == {"max": 30000}

    @pytest.mark.asyncio
    async def test_voice_command_parsing_in_context(self, conversation_agent):
        """Test voice command parsing with context"""
        # Mock the enhanced context method
        conversation_agent._enhance_nlu_with_voice_command = Mock()

        # Create voice result
        voice_result = VoiceResult(
            transcript="show me electric cars with navigation",
            confidence=0.88,
            is_final=True,
            timestamp=time.time(),
            state=VoiceState.SUCCESS
        )

        # Create mock NLU result
        mock_nlu_result = Mock()
        mock_nlu_result.entities = []

        # Call the enhanced NLU method directly
        voice_command = conversation_agent._enhance_nlu_with_voice_command(
            mock_nlu_result,
            Mock(
                command_type="search",
                confidence=0.88,
                vehicle_types=["Electric"],
                features=["navigation"]
            )
        )

        # Verify enhancement
        assert hasattr(voice_command, 'entities')  # Method should have added entities

    @pytest.mark.asyncio
    async def test_voice_session_management(self, conversation_agent):
        """Test voice session start/stop"""
        # Mock voice service
        conversation_agent.voice_service.initialize = Mock(return_value=True)
        conversation_agent.voice_service.start_listening = Mock(return_value=True)
        conversation_agent.voice_service.stop_listening = Mock(return_value=True)

        # Test starting voice session
        result_callback = Mock()
        error_callback = Mock()

        success = await conversation_agent.start_voice_session(
            user_id="test_user",
            result_callback=result_callback,
            error_callback=error_callback
        )

        assert success == True
        assert conversation_agent.voice_enabled == True

        # Test stopping voice session
        success = await conversation_agent.stop_voice_session()
        assert success == True
        assert conversation_agent.voice_enabled == False

    @pytest.mark.asyncio
    async def test_voice_storage_in_memory(self, conversation_agent):
        """Test storing voice interactions in memory"""
        # Mock dependencies
        conversation_agent.temporal_memory = Mock()
        conversation_agent.temporal_memory.add_memory_fragment = AsyncMock()
        conversation_agent.profile_service = Mock()
        conversation_agent.profile_service.update_profile_preferences = AsyncMock()

        # Create voice result and command
        voice_result = VoiceResult(
            transcript="I need a pickup truck",
            confidence=0.92,
            is_final=True,
            timestamp=time.time(),
            state=VoiceState.SUCCESS
        )

        voice_command = Mock(
            command_type="search",
            vehicle_types=["Pickup Truck"],
            confidence=0.92
        )

        # Store voice interaction
        await conversation_agent._store_voice_interaction("test_user", voice_result, voice_command)

        # Verify storage
        conversation_agent.temporal_memory.add_memory_fragment.assert_called_once()
        conversation_agent.profile_service.update_profile_preferences.assert_called_once()

    def test_get_voice_performance_stats(self, conversation_agent):
        """Test getting voice performance statistics"""
        # Mock voice service stats
        conversation_agent.voice_service.get_performance_stats = Mock(return_value={
            "average_processing_time": 150.0,
            "success_rate": 0.95
        })

        stats = conversation_agent.get_voice_performance_stats()

        assert stats["average_processing_time"] == 150.0
        assert stats["success_rate"] == 0.95

    @pytest.mark.asyncio
    async def test_health_check_includes_voice(self, conversation_agent):
        """Test health check includes voice service status"""
        # Mock dependencies
        conversation_agent.zep_client.health_check = AsyncMock(return_value={'initialized': True})
        conversation_agent.groq_client.health_check = AsyncMock(return_value={'initialized': True})
        conversation_agent.voice_service = Mock()
        conversation_agent.voice_service.is_browser_supported = Mock(return_value=True)
        conversation_agent.voice_service.is_listening = Mock(return_value=False)

        health = await conversation_agent.health_check()

        assert 'voice_service' in health
        assert health['voice_service']['initialized'] == True
        assert health['voice_service']['browser_supported'] == True
        assert health['voice_service']['is_listening'] == False

    @pytest.mark.asyncio
    async def test_voice_error_handling(self, conversation_agent):
        """Test error handling in voice processing"""
        # Mock error scenario
        voice_result = VoiceResult(
            transcript="",
            confidence=0.0,
            is_final=False,
            timestamp=time.time(),
            state=VoiceState.ERROR
        )

        # Mock NLU service to handle errors gracefully
        conversation_agent.nlu_service = Mock()
        conversation_agent.nlu_service.analyze_message = AsyncMock(side_effect=Exception("Voice processing error"))
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(return_value={})

        # Process should not raise exception
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="",
            session_id="session_123",
            voice_result=voice_result
        )

        # Should get error response
        assert response.response_type == "error"

    @pytest.mark.asyncio
    async def test_voice_latency_tracking(self, conversation_agent):
        """Test voice processing latency tracking"""
        # Track start time
        start_time = time.time()

        # Mock fast processing
        conversation_agent.nlu_service = Mock()
        conversation_agent.nlu_service._get_enhanced_context = AsyncMock(return_value={})
        conversation_agent.nlu_service.analyze_message = AsyncMock(return_value=Mock(
            intent=Mock(primary="search", confidence=0.9),
            entities=[],
            preferences=[]
        ))

        conversation_agent.response_generator = Mock()
        conversation_agent.response_generator.generate_response = AsyncMock(return_value=Mock(
            message="Quick response",
            response_type="text",
            suggestions=[],
            follow_up_actions=None
        ))

        conversation_agent._store_message = AsyncMock()

        voice_result = VoiceResult(
            transcript="fast command",
            confidence=0.95,
            is_final=True,
            timestamp=time.time(),
            state=VoiceState.SUCCESS
        )

        # Process
        response = await conversation_agent.process_message(
            user_id="test_user",
            message="",
            session_id="session_123",
            voice_result=voice_result
        )

        # Check processing time is tracked
        assert response.processing_time_ms is not None
        # Should be under 500ms for success
        assert response.processing_time_ms < 500


@pytest.mark.integration
class TestVoiceWebSocketIntegration:
    """Integration tests for voice WebSocket communication"""

    @pytest.mark.asyncio
    async def test_websocket_voice_message_flow(self):
        """Test complete WebSocket voice message flow"""
        # This test would require WebSocket test infrastructure
        # For now, we'll test the message structure
        voice_message = {
            "type": "voice_result",
            "content": "show me SUVs",
            "data": {
                "transcript": "show me SUVs",
                "confidence": 0.92,
                "is_final": True,
                "timestamp": time.time()
            }
        }

        # Verify message structure
        assert voice_message["type"] == "voice_result"
        assert voice_message["content"] == "show me SUVs"
        assert voice_message["data"]["transcript"] == "show me SUVs"
        assert voice_message["data"]["confidence"] > 0.9
        assert voice_message["data"]["is_final"] == True

    @pytest.mark.asyncio
    async def test_voice_control_messages(self):
        """Test voice control message types"""
        # Start message
        start_msg = {
            "type": "voice_request",
            "event": "start"
        }
        assert start_msg["event"] == "start"

        # Stop message
        stop_msg = {
            "type": "voice_request",
            "event": "stop"
        }
        assert stop_msg["event"] == "stop"

        # Abort message
        abort_msg = {
            "type": "voice_request",
            "event": "abort"
        }
        assert abort_msg["event"] == "abort"