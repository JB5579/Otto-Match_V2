"""
Pytest fixtures for Otto AI testing
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import tempfile
import os

from src.memory.temporal_memory import TemporalMemoryManager
from src.intelligence.preference_engine import PreferenceEngine
from src.services.profile_service import ProfileService
from src.conversation.nlu_service import UserPreference, Entity


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_zep_client():
    """Mock Zep client for testing"""
    class MockZepClient:
        def __init__(self):
            self.memory_store = {}
            self.conversation_store = {}

        async def initialize(self):
            return True

        async def health_check(self):
            return {"initialized": True, "status": "healthy"}

        async def add_conversation_turn(self, user_id: str, message: str, response: str):
            if user_id not in self.conversation_store:
                self.conversation_store[user_id] = []

            self.conversation_store[user_id].append({
                "message": message,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })

        async def get_conversation_history(self, user_id: str, limit: int = 50):
            history = self.conversation_store.get(user_id, [])
            # Return as list of dicts with role and content
            messages = []
            for turn in history[-limit:]:
                messages.append({
                    "uuid": f"msg_{len(messages)}",
                    "role": "user",
                    "content": turn["message"],
                    "created_at": turn["timestamp"]
                })
                messages.append({
                    "uuid": f"msg_{len(messages)}",
                    "role": "assistant",
                    "content": turn["response"],
                    "created_at": turn["timestamp"]
                })
            return messages

        async def add_memory_fragment(self, user_id: str, content: str, memory_type: str):
            if user_id not in self.memory_store:
                self.memory_store[user_id] = []

            self.memory_store[user_id].append({
                "content": content,
                "type": memory_type,
                "timestamp": datetime.now()
            })

        async def search_memory(self, user_id: str, query: str):
            memories = self.memory_store.get(user_id, [])
            # Simple mock search - return all memories containing query
            results = []
            for mem in memories:
                if query.lower() in mem["content"].lower():
                    results.append(mem)
            return results

    return MockZepClient()


@pytest.fixture
async def mock_groq_client():
    """Mock Groq client for testing"""
    class MockGroqClient:
        async def health_check(self):
            return {"initialized": True, "status": "healthy"}

        async def generate_response(self, prompt: str, context: Dict[str, Any] = None):
            # Simple mock response based on content
            if "preference" in prompt.lower():
                return "I understand you prefer Japanese brands for reliability."
            elif "family" in prompt.lower():
                return "What size family do you have? This will help me recommend appropriate vehicles."
            else:
                return "I'm here to help you find the perfect vehicle!"

    return MockGroqClient()


@pytest.fixture
async def temporal_memory_manager(mock_zep_client):
    """Create temporal memory manager with mock dependencies"""
    manager = TemporalMemoryManager(mock_zep_client)
    return manager


@pytest.fixture
async def preference_engine(mock_groq_client, temporal_memory_manager):
    """Create preference engine with mock dependencies"""
    engine = PreferenceEngine(mock_groq_client, temporal_memory_manager)
    return engine


@pytest.fixture
async def profile_service():
    """Create profile service with temporary storage"""
    service = ProfileService()
    # Use in-memory storage for testing
    service.profiles = {}
    return service


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing"""
    return [
        UserPreference(
            category="brand",
            value=["Toyota", "Honda", "Nissan"],
            weight=0.8,
            source="explicit",
            confidence=0.9,
            timestamp=datetime.now()
        ),
        UserPreference(
            category="price_range",
            value={"min": 20000, "max": 35000},
            weight=0.7,
            source="explicit",
            confidence=0.8,
            timestamp=datetime.now()
        ),
        UserPreference(
            category="vehicle_type",
            value="SUV",
            weight=0.6,
            source="implicit",
            confidence=0.5,
            timestamp=datetime.now()
        )
    ]


@pytest.fixture
def sample_entities():
    """Sample NLU entities for testing"""
    return [
        Entity(
            text="Toyota",
            label="BRAND",
            confidence=0.95,
            start=0,
            end=6
        ),
        Entity(
            text="SUV",
            label="VEHICLE_TYPE",
            confidence=0.90,
            start=20,
            end=23
        ),
        Entity(
            text="$30,000",
            label="PRICE",
            confidence=0.85,
            start=30,
            end=37
        )
    ]


@pytest.fixture
def sample_conversation_turns():
    """Sample conversation turns for testing"""
    return [
        {
            "message": "I'm looking for a reliable SUV under $30,000",
            "response": "I understand you're looking for a reliable SUV within that budget. Japanese brands like Toyota and Honda are known for reliability.",
            "timestamp": datetime.now() - timedelta(days=2)
        },
        {
            "message": "I prefer Toyota specifically",
            "response": "Toyota is an excellent choice known for reliability and resale value. What features are most important to you?",
            "timestamp": datetime.now() - timedelta(days=1)
        },
        {
            "message": "Good fuel economy and safety features",
            "response": "Toyota RAV4 and Highlander both offer excellent fuel economy and top safety ratings. Do you have a family size consideration?",
            "timestamp": datetime.now()
        }
    ]


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


# Test markers for different test categories
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "acceptance: mark test as an acceptance test"
    )
    config.addinivalue_line(
        "markers", "privacy: mark test as a privacy compliance test"
    )