"""
Integration tests for cross-session memory persistence
"""

import pytest
from datetime import datetime, timedelta
from src.memory.temporal_memory import TemporalMemoryManager
from src.intelligence.preference_engine import PreferenceEngine
from src.services.profile_service import ProfileService
from src.conversation.nlu_service import UserPreference


@pytest.mark.integration
class TestCrossSessionMemory:
    """Test suite for cross-session memory persistence"""

    async def test_full_conversation_memory_flow(self, mock_zep_client, mock_groq_client):
        """Test complete flow: conversation → memory → retrieval → new session"""
        # Initialize components
        memory_manager = TemporalMemoryManager(mock_zep_client)
        preference_engine = PreferenceEngine(mock_groq_client, memory_manager)
        profile_service = ProfileService()

        user_id = "test_user_123"
        session1_id = "session_1"
        session2_id = "session_2"

        # === Session 1: Initial conversation ===
        conversation1 = [
            {
                "message": "I'm looking for a reliable family SUV",
                "entities": [
                    {"text": "family", "label": "FAMILY_SIZE", "confidence": 0.9},
                    {"text": "SUV", "label": "VEHICLE_TYPE", "confidence": 0.95}
                ]
            },
            {
                "message": "I prefer Japanese brands like Toyota",
                "entities": [
                    {"text": "Toyota", "label": "BRAND", "confidence": 0.95}
                ]
            },
            {
                "message": "Budget around $30,000",
                "entities": [
                    {"text": "$30,000", "label": "PRICE", "confidence": 0.9}
                ]
            }
        ]

        # Process conversation 1
        for turn in conversation1:
            # Store in Zep
            await mock_zep_client.add_conversation_turn(
                user_id,
                turn["message"],
                "I understand your preference for a reliable family SUV."
            )

            # Extract preferences
            preferences = await preference_engine.extract_preferences(
                turn["message"],
                turn["entities"]
            )

            # Update profile
            if preferences:
                await profile_service.update_profile_preferences(
                    user_id,
                    preferences,
                    source="conversation"
                )

            # Add to memory
            for pref in preferences:
                await memory_manager.add_memory_fragment(
                    user_id=user_id,
                    content=f"User prefers {pref.category}: {pref.value}",
                    memory_type="semantic",
                    importance=pref.weight,
                    session_id=session1_id
                )

        # === Simulate time gap ===
        await memory_manager._simulate_time_passage(days=2)

        # === Session 2: Return with context ===
        # Get contextual memory
        context = await memory_manager.get_contextual_memory(user_id, "What do you have for me?")

        # Verify context reconstruction
        assert len(context.working_memory) > 0, "Should have working memory from previous session"
        assert len(context.semantic_memory) > 0, "Should have semantic preferences"

        # Verify specific preferences remembered
        semantic_content = " ".join([m.content for m in context.semantic_memory])
        assert "family" in semantic_content.lower(), "Should remember family preference"
        assert "SUV" in semantic_content, "Should remember SUV preference"
        assert "Toyota" in semantic_content, "Should remember brand preference"

        # Verify profile persistence
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        assert profile is not None, "Profile should persist across sessions"
        assert len(profile.get("preferences", {})) > 0, "Should have saved preferences"

        # === Test evolution in new session ===
        # User changes preference
        new_preference = UserPreference(
            category="brand",
            value=["Honda", "Mazda"],
            weight=0.8,
            source="explicit",
            confidence=0.9
        )

        await profile_service.update_profile_preferences(
            user_id,
            [new_preference],
            source="user_correction"
        )

        # Verify preference evolution
        updated_profile = await profile_service.get_profile_with_privacy(user_id, "self")
        assert updated_profile is not None

        # Check preference history
        timeline = await profile_service.create_preference_timeline(user_id, days=30)
        assert len(timeline) > 0, "Should have preference evolution history"

    async def test_memory_consolidation_across_sessions(self, mock_zep_client, mock_groq_client):
        """Test memory consolidation across multiple sessions"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        preference_engine = PreferenceEngine(mock_groq_client, memory_manager)

        user_id = "test_user_456"

        # Create multiple conversations over time
        sessions = [
            ("Day 1", ["I need a compact car", "Good fuel economy is important"]),
            ("Day 3", ["Safety ratings matter to me", "I have two kids"]),
            ("Day 5", ["Actually, need more space", "Looking at SUVs now"]),
            ("Day 7", ["Consider Japanese brands", "Reliability is key"])
        ]

        for session_day, messages in sessions:
            for message in messages:
                # Store conversation
                await mock_zep_client.add_conversation_turn(
                    user_id,
                    message,
                    "Noted your preference."
                )

                # Extract and store as memory
                preferences = await preference_engine.extract_preferences(message, [])
                for pref in preferences:
                    await memory_manager.add_memory_fragment(
                        user_id=user_id,
                        content=f"Prefers {pref.category}: {pref.value}",
                        memory_type="working",
                        importance=pref.weight
                    )

        # Trigger consolidation
        await memory_manager.consolidate_memories(user_id)

        # Verify consolidation happened
        memories = memory_manager.memory_cache.get(user_id, [])
        episodic_count = sum(1 for m in memories if m.type == "episodic")
        assert episodic_count > 0, "Should have episodic memories after consolidation"

        # Test retrieval of consolidated memories
        context = await memory_manager.get_contextual_memory(user_id, "What do you remember?")
        assert len(context.episodic_memory) > 0, "Should retrieve episodic memories"

    async def test_preference_evolution_tracking(self, mock_zep_client, mock_groq_client):
        """Test preference evolution tracking accuracy"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        profile_service = ProfileService()

        user_id = "test_user_789"

        # Simulate evolving preferences
        preference_timeline = [
            (datetime.now() - timedelta(days=7), UserPreference(
                category="vehicle_type",
                value="sedan",
                weight=0.8,
                source="explicit"
            )),
            (datetime.now() - timedelta(days=5), UserPreference(
                category="vehicle_type",
                value="SUV",
                weight=0.9,
                source="explicit"
            )),
            (datetime.now() - timedelta(days=3), UserPreference(
                category="vehicle_type",
                value="minivan",
                weight=0.7,
                source="explicit"
            )),
            (datetime.now() - timedelta(days=1), UserPreference(
                category="vehicle_type",
                value="SUV",
                weight=0.9,
                source="explicit"
            ))
        ]

        # Add preferences to profile
        for timestamp, preference in preference_timeline:
            preference.timestamp = timestamp
            await profile_service.update_profile_preferences(
                user_id,
                [preference],
                source="conversation"
            )

        # Create timeline
        timeline = await profile_service.create_preference_timeline(user_id, days=10)

        # Verify evolution tracking
        assert len(timeline) >= 3, "Should track preference changes"

        # Check for patterns
        changes = [t for t in timeline if t["change_type"] == "modified"]
        assert len(changes) >= 1, "Should detect preference modifications"

        # Verify final preference
        current_profile = await profile_service.get_profile_with_privacy(user_id, "self")
        current_prefs = current_profile.get("preferences", {})
        vehicle_pref = current_prefs.get("pref_vehicle_type", {})
        assert vehicle_pref.get("value") == "SUV", "Should have latest preference"

    async def test_cross_device_memory_sync(self, mock_zep_client, mock_groq_client):
        """Test memory synchronization across devices"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        profile_service = ProfileService()

        user_id = "test_user_multi_device"

        # Device 1: Phone conversation
        phone_preferences = [
            UserPreference(
                category="budget",
                value={"max": 25000},
                weight=0.8,
                source="explicit"
            ),
            UserPreference(
                category="fuel_type",
                value="hybrid",
                weight=0.7,
                source="explicit"
            )
        ]

        for pref in phone_preferences:
            await profile_service.update_profile_preferences(
                user_id,
                [pref],
                source="mobile_app"
            )

        # Device 2: Desktop conversation (later)
        desktop_preferences = [
            UserPreference(
                category="brand",
                value="Toyota",
                weight=0.9,
                source="explicit"
            )
        ]

        for pref in desktop_preferences:
            await profile_service.update_profile_preferences(
                user_id,
                [pref],
                source="web_app"
            )

        # Verify synchronization
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        all_prefs = profile.get("preferences", {})

        # Should have preferences from both devices
        assert "pref_budget" in all_prefs, "Should have budget preference from phone"
        assert "pref_fuel_type" in all_prefs, "Should have fuel preference from phone"
        assert "pref_brand" in all_prefs, "Should have brand preference from desktop"

        # Verify device tracking
        pref_history = profile.get("preference_history", [])
        devices = set(h.get("source") for h in pref_history)
        assert "mobile_app" in devices, "Should track mobile device"
        assert "web_app" in devices, "Should track desktop device"

    async def test_memory_recovery_after_error(self, mock_zep_client, mock_groq_client):
        """Test memory recovery after errors"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        profile_service = ProfileService()

        user_id = "test_user_recovery"

        # Add some preferences
        preferences = [
            UserPreference(
                category="brand",
                value="Honda",
                weight=0.8,
                source="explicit"
            )
        ]

        await profile_service.update_profile_preferences(user_id, preferences)

        # Simulate partial memory loss
        original_cache = memory_manager.memory_cache.copy()
        memory_manager.memory_cache = {}

        # Test recovery from profile
        recovered_profile = await profile_service.get_profile_with_privacy(user_id, "self")
        assert recovered_profile is not None, "Should recover profile from storage"

        # Test memory reconstruction
        context = await memory_manager.get_contextual_memory(user_id, "Recover memory")
        # Should attempt to reconstruct from stored data
        assert context is not None, "Should provide context even after cache loss"

    async def test_performance_cross_session_operations(self, mock_zep_client, mock_groq_client):
        """Test performance of cross-session operations (<500ms requirement)"""
        import time

        memory_manager = TemporalMemoryManager(mock_zep_client)
        profile_service = ProfileService()

        user_id = "perf_test_user"

        # Set up extensive history
        for day in range(30):
            date = datetime.now() - timedelta(days=day)
            for hour in range(5):
                timestamp = date.replace(hour=hour)
                pref = UserPreference(
                    category=f"category_{day}_{hour}",
                    value=f"value_{day}_{hour}",
                    weight=0.5,
                    source="implicit",
                    timestamp=timestamp
                )
                await profile_service.update_profile_preferences(user_id, [pref])

        # Test retrieval performance
        start_time = time.time()
        timeline = await profile_service.create_preference_timeline(user_id, days=30)
        end_time = time.time()

        retrieval_time = (end_time - start_time) * 1000
        assert retrieval_time < 500, f"Timeline retrieval took {retrieval_time}ms, expected < 500ms"

        # Test context retrieval performance
        start_time = time.time()
        context = await memory_manager.get_contextual_memory(user_id, "Performance test")
        end_time = time.time()

        context_time = (end_time - start_time) * 1000
        assert context_time < 500, f"Context retrieval took {context_time}ms, expected < 500ms"