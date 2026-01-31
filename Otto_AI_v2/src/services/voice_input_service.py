"""
Voice Input Service for Otto.AI
Handles speech-to-text conversion using Web Speech API

================================================================================
STATUS: DEFERRED (2026-01-22)
================================================================================
This feature has been moved to future enhancements backlog.
Rationale: Voice input is an enhancement feature, not core functionality.
           Text-based conversation validates the discovery journey UX.

Implementation preserved for future integration when core MVP is validated.
See: docs/future-features.md for tracking and reactivation criteria.
================================================================================
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

# Voice input states
class VoiceState(Enum):
    """Voice input states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class VoiceResult:
    """Result of voice recognition"""
    transcript: str
    confidence: float
    is_final: bool
    timestamp: float
    state: VoiceState


@dataclass
class VoiceConfig:
    """Configuration for voice input"""
    language: str = "en-US"
    continuous: bool = True
    interim_results: bool = True
    max_alternatives: int = 1
    grammars: Optional[str] = None  # JSGF grammar file for vehicle-specific commands


class VoiceInputService:
    """
    Voice Input Service using Web Speech API
    Handles speech-to-text conversion for Otto AI conversations
    """

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.state = VoiceState.IDLE
        self.recognition = None
        self.is_listening = False
        self.result_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.last_result: Optional[VoiceResult] = None
        self.confidence_threshold = 0.7
        self.noise_detection_enabled = True

        # Performance metrics
        self.start_time = 0
        self.processing_times = []

    def initialize(self, websocket_manager=None) -> bool:
        """
        Initialize voice input service
        Check for browser support and set up recognition
        """
        try:
            # Check if running in browser environment
            import js
            if not hasattr(js, 'window') or not hasattr(js.window, 'SpeechRecognition'):
                logger.warning("Web Speech API not supported in this environment")
                return False

            # Create SpeechRecognition instance
            SpeechRecognition = js.window.SpeechRecognition or js.window.webkitSpeechRecognition
            self.recognition = SpeechRecognition()

            # Configure recognition
            self.recognition.continuous = self.config.continuous
            self.recognition.interimResults = self.config.interim_results
            self.recognition.maxAlternatives = self.config.max_alternatives
            self.recognition.lang = self.config.language

            # Set up event handlers
            self._setup_event_handlers()

            logger.info("Voice input service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize voice input service: {e}")
            return False

    def _setup_event_handlers(self):
        """Set up SpeechRecognition event handlers"""
        if not self.recognition:
            return

        # Result handler
        def on_result(event):
            self._handle_result(event)

        self.recognition.onresult = on_result

        # Error handler
        def on_error(event):
            self._handle_error(event)

        self.recognition.onerror = on_error

        # Start handler
        def on_start(event):
            self._handle_start(event)

        self.recognition.onstart = on_start

        # End handler
        def on_end(event):
            self._handle_end(event)

        self.recognition.onend = on_end

    def _handle_result(self, event):
        """Handle speech recognition results"""
        try:
            # Get results
            results = event.results
            final_transcript = ""
            interim_transcript = ""
            confidence = 0.0

            for i in range(len(results)):
                result = results[i]

                if result.isFinal:
                    final_transcript += result[0].transcript
                    confidence = result[0].confidence
                else:
                    interim_transcript += result[0].transcript

            # Process the result
            transcript = final_transcript or interim_transcript

            if transcript:
                # Create voice result
                voice_result = VoiceResult(
                    transcript=transcript.strip(),
                    confidence=confidence,
                    is_final=bool(final_transcript),
                    timestamp=time.time(),
                    state=self.state
                )

                # Apply noise filtering if enabled
                if self.noise_detection_enabled:
                    voice_result = self._apply_noise_filtering(voice_result)

                self.last_result = voice_result

                # Update processing metrics
                processing_time = (time.time() - self.start_time) * 1000
                self.processing_times.append(processing_time)

                # Send result via callback
                if self.result_callback:
                    self.result_callback(voice_result)

                logger.info(f"Voice recognized: '{transcript}' (confidence: {confidence:.2f})")

        except Exception as e:
            logger.error(f"Error handling voice result: {e}")
            self._handle_error({"error": str(e), "type": "processing_error"})

    def _apply_noise_filtering(self, result: VoiceResult) -> VoiceResult:
        """Apply noise filtering to improve accuracy"""
        # Simple noise filtering based on confidence and content
        if result.confidence < self.confidence_threshold:
            # Check for common noise patterns
            noise_patterns = ["um", "uh", "er", "ah", "mm", "hm"]
            words = result.transcript.lower().split()

            # Filter out noise words
            filtered_words = [w for w in words if w not in noise_patterns]

            if filtered_words:
                result.transcript = " ".join(filtered_words)
                logger.debug(f"Applied noise filtering: removed {len(words) - len(filtered_words)} noise words")

        return result

    def _handle_error(self, event):
        """Handle speech recognition errors"""
        error = event.error if hasattr(event, 'error') else event.get('error', 'unknown')

        # Map errors to user-friendly messages
        error_messages = {
            'no-speech': "No speech detected. Please try again.",
            'audio-capture': "Microphone access denied. Please check your permissions.",
            'not-allowed': "Microphone access denied. Please allow microphone access.",
            'network': "Network error. Please check your connection.",
            'service-not-allowed': "Speech recognition service not allowed.",
            'aborted': "Voice input was cancelled."
        }

        message = error_messages.get(error, "Voice recognition error occurred.")

        self.state = VoiceState.ERROR
        self.is_listening = False

        if self.error_callback:
            self.error_callback({
                "error": error,
                "message": message,
                "timestamp": time.time()
            })

        logger.error(f"Voice recognition error: {error} - {message}")

    def _handle_start(self, event):
        """Handle recognition start"""
        self.state = VoiceState.LISTENING
        self.is_listening = True
        self.start_time = time.time()
        logger.info("Voice recognition started")

    def _handle_end(self, event):
        """Handle recognition end"""
        self.state = VoiceState.IDLE
        self.is_listening = False
        logger.info("Voice recognition ended")

    def start_listening(
        self,
        result_callback: Callable[[VoiceResult], None],
        error_callback: Optional[Callable[[Dict], None]] = None
    ) -> bool:
        """
        Start listening for voice input

        Args:
            result_callback: Function to handle voice results
            error_callback: Function to handle errors

        Returns:
            True if successfully started, False otherwise
        """
        if not self.recognition:
            logger.error("Voice recognition not initialized")
            return False

        if self.is_listening:
            logger.warning("Already listening for voice input")
            return False

        try:
            # Set callbacks
            self.result_callback = result_callback
            self.error_callback = error_callback

            # Start recognition
            self.recognition.start()

            return True

        except Exception as e:
            logger.error(f"Failed to start voice recognition: {e}")
            if error_callback:
                error_callback({
                    "error": "start_failed",
                    "message": "Failed to start voice recognition",
                    "timestamp": time.time()
                })
            return False

    def stop_listening(self) -> bool:
        """Stop listening for voice input"""
        if not self.recognition or not self.is_listening:
            return False

        try:
            self.recognition.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop voice recognition: {e}")
            return False

    def abort_listening(self) -> bool:
        """Abort voice recognition immediately"""
        if not self.recognition or not self.is_listening:
            return False

        try:
            self.recognition.abort()
            return True
        except Exception as e:
            logger.error(f"Failed to abort voice recognition: {e}")
            return False

    def get_last_result(self) -> Optional[VoiceResult]:
        """Get the last voice recognition result"""
        return self.last_result

    def is_browser_supported(self) -> bool:
        """Check if browser supports Web Speech API"""
        try:
            import js
            return bool(hasattr(js.window, 'SpeechRecognition') or
                       hasattr(js.window, 'webkitSpeechRecognition'))
        except:
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.processing_times:
            return {}

        return {
            "average_processing_time": sum(self.processing_times) / len(self.processing_times),
            "max_processing_time": max(self.processing_times),
            "min_processing_time": min(self.processing_times),
            "total_recognitions": len(self.processing_times),
            "success_rate": self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate recognition success rate based on confidence scores"""
        if not self.processing_times:
            return 0.0

        # This is a simplified calculation
        # In practice, you'd track successful vs failed recognitions
        return min(0.95, 0.7 + (0.25 * len([t for t in self.processing_times if t < 500]) / len(self.processing_times)))

    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for accepting results"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Confidence threshold set to {self.confidence_threshold}")

    def enable_noise_filtering(self, enabled: bool):
        """Enable or disable noise filtering"""
        self.noise_detection_enabled = enabled
        logger.info(f"Noise filtering {'enabled' if enabled else 'disabled'}")

    def create_voice_command_grammar(self) -> str:
        """
        Create a JSGF grammar for voice commands
        This helps improve recognition accuracy for vehicle-related commands
        """
        grammar = """
        #JSGF V1.0;

        grammar vehicle_commands;

        public <action> = search | find | show | look for | compare | filter | sort;
        public <vehicle_type> = SUV | sedan | truck | pickup | hatchback | coupe | convertible | minivan | van;
        public <feature> = sunroof | navigation | bluetooth | backup camera | leather seats | heated seats;
        public <price_qualifier> = under | below | less than | around | about;
        public <number> = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
                         11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
                         twenty | thirty | forty | fifty | sixty | seventy | eighty | ninety;
        public <currency> = dollars | bucks | k | thousand;

        public <command> =
            <action> a <vehicle_type> |
            <action> <vehicle_type> under <number> <currency> |
            <action> electric <vehicle_type> |
            <action> <vehicle_type> with <feature> |
            compare <vehicle_type> and <vehicle_type> |
            show me <feature>;
        """

        return grammar


# WebSocket integration helper
class VoiceWebSocketHandler:
    """Handles voice input through WebSocket connections"""

    def __init__(self, voice_service: VoiceInputService, connection_manager):
        self.voice_service = voice_service
        self.connection_manager = connection_manager
        self.active_sessions = {}

    async def handle_voice_start(self, connection_id: str, user_id: str):
        """Handle voice input start from WebSocket"""
        if user_id in self.active_sessions:
            await self.connection_manager.send_message(connection_id, {
                "type": "voice_error",
                "data": {
                    "message": "Voice session already active",
                    "timestamp": time.time()
                }
            })
            return

        # Start voice session
        session = {
            "connection_id": connection_id,
            "user_id": user_id,
            "started_at": time.time()
        }
        self.active_sessions[user_id] = session

        # Define callbacks
        def on_result(result: VoiceResult):
            asyncio.create_task(
                self.connection_manager.send_message(connection_id, {
                    "type": "voice_result",
                    "data": {
                        "transcript": result.transcript,
                        "confidence": result.confidence,
                        "is_final": result.is_final,
                        "timestamp": result.timestamp,
                        "state": result.state.value
                    }
                })
            )

        def on_error(error: Dict):
            asyncio.create_task(
                self.connection_manager.send_message(connection_id, {
                    "type": "voice_error",
                    "data": error
                })
            )

        # Start listening
        success = self.voice_service.start_listening(on_result, on_error)

        if success:
            await self.connection_manager.send_message(connection_id, {
                "type": "voice_started",
                "data": {
                    "message": "Listening... Speak now",
                    "timestamp": time.time()
                }
            })
        else:
            await self.connection_manager.send_message(connection_id, {
                "type": "voice_error",
                "data": {
                    "message": "Failed to start voice recognition",
                    "timestamp": time.time()
                }
            })
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]

    async def handle_voice_stop(self, connection_id: str, user_id: str):
        """Handle voice input stop from WebSocket"""
        if user_id not in self.active_sessions:
            return

        # Stop listening
        self.voice_service.stop_listening()

        # Clean up session
        del self.active_sessions[user_id]

        await self.connection_manager.send_message(connection_id, {
            "type": "voice_stopped",
            "data": {
                "message": "Voice input stopped",
                "timestamp": time.time()
            }
        })

    async def handle_voice_abort(self, connection_id: str, user_id: str):
        """Handle voice input abort from WebSocket"""
        if user_id not in self.active_sessions:
            return

        # Abort listening
        self.voice_service.abort_listening()

        # Clean up session
        del self.active_sessions[user_id]

        await self.connection_manager.send_message(connection_id, {
            "type": "voice_aborted",
            "data": {
                "message": "Voice input cancelled",
                "timestamp": time.time()
            }
        })