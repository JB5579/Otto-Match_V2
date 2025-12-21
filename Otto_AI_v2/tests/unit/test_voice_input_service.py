"""
Unit tests for Voice Input Service
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.services.voice_input_service import (
    VoiceInputService,
    VoiceResult,
    VoiceConfig,
    VoiceState
)
from src.models.voice_models import (
    VoiceCommand,
    VoiceCommandType,
    parse_vehicle_command
)


class TestVoiceInputService:
    """Test cases for VoiceInputService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = VoiceInputService()

    def test_initialization(self):
        """Test service initialization"""
        assert self.service.state == VoiceState.IDLE
        assert self.service.is_listening == False
        assert self.service.confidence_threshold == 0.7
        assert self.service.noise_detection_enabled == True

    def test_config_initialization(self):
        """Test initialization with custom config"""
        config = VoiceConfig(
            language="en-GB",
            continuous=False,
            confidence_threshold=0.8
        )
        service = VoiceInputService(config)
        assert service.config.language == "en-GB"
        assert service.config.continuous == False

    @patch('src.services.voice_input_service.VoiceInputService.is_browser_supported')
    def test_initialize_browser_supported(self, mock_supported):
        """Test initialization when browser is supported"""
        mock_supported.return_value = True

        # Mock Web Speech API
        mock_recognition = Mock()
        mock_speech_recognition = Mock()
        mock_speech_recognition.return_value = mock_recognition

        with patch('js.window', {'SpeechRecognition': mock_speech_recognition}):
            result = self.service.initialize()

        assert result == True
        assert self.service.recognition == mock_recognition

    @patch('src.services.voice_input_service.VoiceInputService.is_browser_supported')
    def test_initialize_browser_not_supported(self, mock_supported):
        """Test initialization when browser is not supported"""
        mock_supported.return_value = False

        result = self.service.initialize()

        assert result == False

    def test_apply_noise_filtering(self):
        """Test noise filtering functionality"""
        # Test with high confidence
        result = VoiceResult(
            transcript="I need an SUV under 30000",
            confidence=0.9,
            is_final=True,
            timestamp=1234567890,
            state=VoiceState.SUCCESS
        )

        filtered = self.service._apply_noise_filtering(result)
        assert filtered.transcript == "I need an SUV under 30000"

        # Test with low confidence and noise
        result_noisy = VoiceResult(
            transcript="I need um uh an SUV with uh sunroof",
            confidence=0.5,
            is_final=True,
            timestamp=1234567890,
            state=VoiceState.SUCCESS
        )

        filtered = self.service._apply_noise_filtering(result_noisy)
        assert "um" not in filtered.transcript
        assert "uh" not in filtered.transcript

    def test_get_performance_stats_empty(self):
        """Test performance stats with no processing history"""
        stats = self.service.get_performance_stats()
        assert stats == {}

    def test_get_performance_stats_with_data(self):
        """Test performance stats with processing data"""
        # Add some processing times
        self.service.processing_times = [100, 200, 300]
        self.service.start_time = 1234567890

        stats = self.service.get_performance_stats()
        assert stats['average_processing_time'] == 200.0
        assert stats['max_processing_time'] == 300
        assert stats['min_processing_time'] == 100
        assert stats['total_recognitions'] == 3
        assert 0 < stats['success_rate'] <= 1

    def test_set_confidence_threshold(self):
        """Test setting confidence threshold"""
        self.service.set_confidence_threshold(0.85)
        assert self.service.confidence_threshold == 0.85

        # Test boundary values
        self.service.set_confidence_threshold(-0.5)
        assert self.service.confidence_threshold == 0.0

        self.service.set_confidence_threshold(1.5)
        assert self.service.confidence_threshold == 1.0

    def test_enable_noise_filtering(self):
        """Test enabling/disabling noise filtering"""
        self.service.enable_noise_filtering(False)
        assert self.service.noise_detection_enabled == False

        self.service.enable_noise_filtering(True)
        assert self.service.noise_detection_enabled == True

    def test_create_voice_command_grammar(self):
        """Test creation of voice command grammar"""
        grammar = self.service.create_voice_command_grammar()
        assert "grammar vehicle_commands" in grammar
        assert "<action>" in grammar
        assert "<vehicle_type>" in grammar
        assert "<price_qualifier>" in grammar


class TestVoiceModels:
    """Test cases for voice-related models"""

    def test_parse_vehicle_command_search(self):
        """Test parsing vehicle search commands"""
        command = parse_vehicle_command("search for an SUV under 30000", 0.9)
        assert command.command_type == VoiceCommandType.SEARCH
        assert "SUV" in command.vehicle_types
        assert command.price_range == {"max": 30000}
        assert command.confidence == 0.9

    def test_parse_vehicle_command_compare(self):
        """Test parsing vehicle comparison commands"""
        command = parse_vehicle_command("compare SUV and sedan", 0.8)
        assert command.command_type == VoiceCommandType.COMPARE
        assert "SUV" in command.vehicle_types
        assert "Sedan" in command.vehicle_types

    def test_parse_vehicle_command_with_features(self):
        """Test parsing commands with features"""
        command = parse_vehicle_command("show me a car with sunroof and navigation", 0.85)
        assert command.command_type == VoiceCommandType.SEARCH
        assert "sunroof" in command.features
        assert "navigation" in command.features or "gps" in command.features

    def test_parse_price_words(self):
        """Test parsing price with words"""
        command = parse_vehicle_command("truck under twenty thousand", 0.8)
        assert "Truck" in command.vehicle_types
        assert command.price_range == {"max": 20000}

    def test_parse_general_command(self):
        """Test parsing general (non-vehicle) commands"""
        command = parse_vehicle_command("hello how are you", 0.7)
        assert command.command_type == VoiceCommandType.GENERAL
        assert command.vehicle_types == []
        assert command.price_range is None


class TestVoiceWebSocketHandler:
    """Test cases for voice WebSocket handler"""

    def setup_method(self):
        """Setup test fixtures"""
        self.voice_service = VoiceInputService()
        self.connection_manager = Mock()
        self.handler = Mock(spec=self.voice_service.__class__)

    @pytest.mark.asyncio
    async def test_handle_voice_start_success(self):
        """Test successful voice session start"""
        from src.services.voice_input_service import VoiceWebSocketHandler

        handler = VoiceWebSocketHandler(self.voice_service, self.connection_manager)
        connection_id = "conn_123"
        user_id = "user_456"

        # Mock successful start
        self.voice_service.start_listening = Mock(return_value=True)
        self.connection_manager.send_message = Mock()

        await handler.handle_voice_start(connection_id, user_id)

        # Check session created
        assert user_id in handler.active_sessions

        # Check success message sent
        self.connection_manager.send_message.assert_called_with(
            connection_id,
            {
                "type": "voice_started",
                "event": "listening_started",
                "data": {
                    "message": "Listening... Speak now",
                    "timestamp": pytest.approx(asyncio.get_event_loop().time(), rel=1)
                }
            }
        )

    @pytest.mark.asyncio
    async def test_handle_voice_start_already_active(self):
        """Test voice start when session already active"""
        from src.services.voice_input_service import VoiceWebSocketHandler

        handler = VoiceWebSocketHandler(self.voice_service, self.connection_manager)
        connection_id = "conn_123"
        user_id = "user_456"

        # Create existing session
        handler.active_sessions[user_id] = {"connection_id": connection_id}
        self.connection_manager.send_message = Mock()

        await handler.handle_voice_start(connection_id, user_id)

        # Check error message sent
        self.connection_manager.send_message.assert_called_with(
            connection_id,
            {
                "type": "voice_error",
                "event": "session_exists",
                "data": {
                    "message": "Voice session already active",
                    "timestamp": pytest.approx(asyncio.get_event_loop().time(), rel=1)
                }
            }
        )

    @pytest.mark.asyncio
    async def test_handle_voice_stop(self):
        """Test stopping voice session"""
        from src.services.voice_input_service import VoiceWebSocketHandler

        handler = VoiceWebSocketHandler(self.voice_service, self.connection_manager)
        connection_id = "conn_123"
        user_id = "user_456"

        # Create active session
        handler.active_sessions[user_id] = {"connection_id": connection_id}
        self.voice_service.stop_listening = Mock(return_value=True)
        self.connection_manager.send_message = Mock()

        await handler.handle_voice_stop(connection_id, user_id)

        # Check session removed
        assert user_id not in handler.active_sessions

        # Check stop message sent
        self.connection_manager.send_message.assert_called_with(
            connection_id,
            {
                "type": "voice_stopped",
                "event": "listening_stopped",
                "data": {
                    "message": "Voice input stopped",
                    "timestamp": pytest.approx(asyncio.get_event_loop().time(), rel=1)
                }
            }
        )