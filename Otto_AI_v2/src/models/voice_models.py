"""
Voice-related data models for Otto.AI
Pydantic models for voice input processing and WebSocket messages
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class VoiceState(str, Enum):
    """Voice input states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"
    SUCCESS = "success"


class VoiceCommandType(str, Enum):
    """Types of voice commands"""
    SEARCH = "search"
    COMPARE = "compare"
    FILTER = "filter"
    NAVIGATE = "navigate"
    HELP = "help"
    GENERAL = "general"


class VoiceRecognitionResult(BaseModel):
    """Result from speech recognition"""
    transcript: str = Field(..., description="The recognized text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    is_final: bool = Field(default=True, description="Whether this is a final result")
    alternatives: List[str] = Field(default_factory=list, description="Alternative transcriptions")
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = Field(None, description="Time taken for processing")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceCommand(BaseModel):
    """Parsed voice command"""
    command_type: VoiceCommandType = Field(..., description="Type of command")
    original_text: str = Field(..., description="Original spoken text")
    parsed_intent: Optional[str] = Field(None, description="Parsed intent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Command confidence")

    # Vehicle-specific fields
    vehicle_types: List[str] = Field(default_factory=list, description="Vehicle types mentioned")
    makes: List[str] = Field(default_factory=list, description="Vehicle makes mentioned")
    models: List[str] = Field(default_factory=list, description="Vehicle models mentioned")
    price_range: Optional[Dict[str, float]] = Field(None, description="Price range mentioned")
    features: List[str] = Field(default_factory=list, description="Features mentioned")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceSession(BaseModel):
    """Active voice session"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User ID")
    connection_id: str = Field(..., description="WebSocket connection ID")
    state: VoiceState = Field(default=VoiceState.IDLE, description="Current state")
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    total_recognitions: int = Field(default=0, description="Total recognitions in session")
    successful_recognitions: int = Field(default=0, description="Successful recognitions")

    # Performance metrics
    average_processing_time: Optional[float] = Field(None, description="Average processing time (ms)")
    max_latency: Optional[float] = Field(None, description="Maximum latency observed (ms)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceWebSocketMessage(BaseModel):
    """WebSocket message for voice communication"""
    type: str = Field(..., description="Message type")
    event: str = Field(..., description="Event name")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceSettings(BaseModel):
    """User voice settings"""
    user_id: str = Field(..., description="User ID")
    language: str = Field(default="en-US", description="Preferred language")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    noise_filtering_enabled: bool = Field(default=True)
    auto_punctuation: bool = Field(default=True)
    continuous_mode: bool = Field(default=True)
    haptic_feedback: bool = Field(default=True)
    voice_feedback: bool = Field(default=True)

    # Privacy settings
    store_voice_data: bool = Field(default=False)
    retention_days: Optional[int] = Field(None, description="Days to retain voice data")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceAnalytics(BaseModel):
    """Voice usage analytics"""
    date: datetime = Field(..., description="Analytics date")
    total_sessions: int = Field(default=0)
    total_duration_seconds: float = Field(default=0.0)
    average_session_length: float = Field(default=0.0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    error_types: Dict[str, int] = Field(default_factory=dict)
    top_commands: List[Dict[str, Any]] = Field(default_factory=list)

    # Performance metrics
    average_latency_ms: Optional[float] = Field(None)
    peak_concurrent_sessions: int = Field(default=0)

    # Browser/device breakdown
    browser_stats: Dict[str, int] = Field(default_factory=dict)
    device_type: Dict[str, int] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VoiceFeedbackData(BaseModel):
    """User feedback on voice recognition"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    recognition_id: str = Field(..., description="Recognition ID")
    original_text: str = Field(..., description="What was recognized")
    user_correction: Optional[str] = Field(None, description="User's correction")
    feedback_type: str = Field(..., description="Type of feedback: correction, rating, etc.")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating 1-5")
    comment: Optional[str] = Field(None, description="Additional comments")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# WebSocket message schemas
class VoiceStartMessage(VoiceWebSocketMessage):
    """Message to start voice recognition"""
    type: str = "voice_request"
    event: str = "start"
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "timestamp": datetime.now().isoformat()
    })


class VoiceStopMessage(VoiceWebSocketMessage):
    """Message to stop voice recognition"""
    type: str = "voice_request"
    event: str = "stop"
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "timestamp": datetime.now().isoformat()
    })


class VoiceResultMessage(VoiceWebSocketMessage):
    """Message with voice recognition result"""
    type: str = "voice_result"
    event: str = "recognition_complete"
    data: Dict[str, Any]  # Will contain VoiceRecognitionResult


class VoiceErrorMessage(VoiceWebSocketMessage):
    """Message for voice recognition errors"""
    type: str = "voice_error"
    event: str = "error_occurred"
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "error": "unknown_error",
        "message": "An error occurred during voice recognition"
    })


class VoiceStateMessage(VoiceWebSocketMessage):
    """Message for voice state updates"""
    type: str = "voice_state"
    event: str = "state_changed"
    data: Dict[str, Any]  # Will contain state information


# Helper functions for voice command parsing
def parse_vehicle_command(text: str, confidence: float) -> VoiceCommand:
    """Parse spoken text into a vehicle-related command"""
    text_lower = text.lower().strip()

    # Default to general command
    command_type = VoiceCommandType.GENERAL
    entities = {}
    parameters = {}

    # Extract command type
    if any(word in text_lower for word in ["search", "find", "look for", "show"]):
        command_type = VoiceCommandType.SEARCH
    elif "compare" in text_lower:
        command_type = VoiceCommandType.COMPARE
    elif any(word in text_lower for word in ["filter", "with", "has"]):
        command_type = VoiceCommandType.FILTER
    elif "help" in text_lower:
        command_type = VoiceCommandType.HELP

    # Extract vehicle types
    vehicle_types = []
    vehicle_type_map = {
        "suv": "SUV",
        "sedan": "Sedan",
        "truck": "Truck",
        "pickup": "Pickup Truck",
        "hatchback": "Hatchback",
        "coupe": "Coupe",
        "convertible": "Convertible",
        "minivan": "Minivan",
        "van": "Van",
        "electric": "Electric",
        "hybrid": "Hybrid"
    }

    for term, vt in vehicle_type_map.items():
        if term in text_lower:
            vehicle_types.append(vt)

    # Extract price information
    price_numbers = []
    price_words = {
        "twenty": 20000,
        "thirty": 30000,
        "forty": 40000,
        "fifty": 50000,
        "sixty": 60000,
        "seventy": 70000,
        "eighty": 80000,
        "ninety": 90000
    }

    # Check for dollar amounts
    import re
    price_matches = re.findall(r'\$?(\d+)(?:k| thousand)?', text_lower)
    for match in price_matches:
        try:
            value = int(match)
            if "k" in text_lower or "thousand" in text_lower:
                value *= 1000
            price_numbers.append(value)
        except:
            pass

    # Check for price words
    for word, value in price_words.items():
        if word in text_lower:
            price_numbers.append(value * 1000)

    # Extract features
    features = []
    feature_keywords = [
        "sunroof", "navigation", "gps", "bluetooth", "backup camera",
        "leather seats", "heated seats", "cruise control", "all wheel drive",
        "awd", "four wheel drive", "4wd", "apple carplay", "android auto"
    ]

    for feature in feature_keywords:
        if feature in text_lower:
            features.append(feature)

    # Build command object
    command = VoiceCommand(
        command_type=command_type,
        original_text=text,
        parsed_intent=text_lower,
        entities=entities,
        parameters=parameters,
        confidence=confidence,
        vehicle_types=vehicle_types,
        price_range={"max": max(price_numbers)} if price_numbers else None,
        features=features
    )

    return command


# Voice quality metrics
class VoiceQualityMetrics(BaseModel):
    """Metrics for voice input quality"""
    signal_to_noise_ratio: Optional[float] = Field(None, description="SNR in dB")
    background_noise_level: Optional[float] = Field(None, description="Background noise level")
    speech_clarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Speech clarity score")
    word_error_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Word error rate")
    latency_ms: Optional[float] = Field(None, description="End-to-end latency")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }