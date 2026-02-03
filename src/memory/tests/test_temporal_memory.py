"""
Unit tests for Temporal Memory Manager
"""

import pytest
from datetime import datetime, timedelta
from src.memory.temporal_memory import TemporalMemoryManager, MemoryType, MemoryFragment
from src.memory.zep_client import ConversationContext


@pytest.mark.unit
class TestTemporalMemoryManager:
    """Test suite for TemporalMemoryManager"""

    async def test_initialization(self, mock_zep_client):
        """Test temporal memory manager initialization"""
        manager = TemporalMemoryManager(mock_zep_client)

        assert manager.zep_client == mock_zep_client
        assert manager.consolidation_threshold == 20
        assert manager.working_memory_size == 10
        assert isinstance(manager.memory_cache, dict)

    async def test_add_memory_fragment(self, temporal_memory_manager):
        """Test adding memory fragments"""
        user_id = "test_user_123"
        content = "User prefers Japanese brands for reliability"
        memory_type = MemoryType.SEMANTIC

        await temporal_memory_manager.add_memory_fragment(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            importance=0.8
        )

        # Verify memory was added to cache
        assert user_id in temporal_memory_manager.memory_cache
        memories = temporal_memory_manager.memory_cache[user_id]
        assert len(memories) == 1
        assert memories[0].content == content
        assert memories[0].type == memory_type
        assert memories[0].importance == 0.8

    async def test_get_contextual_memory(self, temporal_memory_manager, sample_conversation_turns):
        """Test retrieving contextual memory"""
        user_id = "test_user_123"

        # Add conversation history
        for turn in sample_conversation_turns:
            await temporal_memory_manager.zep_client.add_conversation_turn(
                user_id,
                turn["message"],
                turn["response"]
            )

        # Add some memory fragments
        await temporal_memory_manager.add_memory_fragment(
            user_id=user_id,
            content="Prefers Toyota vehicles",
            memory_type=MemoryType.SEMANTIC,
            importance=0.9
        )

        # Get contextual memory
        context = await temporal_memory_manager.get_contextual_memory(user_id, "What about SUVs?")

        assert isinstance(context, ConversationContext)
        assert len(context.working_memory) > 0
        assert len(context.episodic_memory) > 0
        assert len(context.semantic_memory) > 0

    async def test_consolidate_memories(self, temporal_memory_manager):
        """Test memory consolidation"""
        user_id = "test_user_123"

        # Add multiple working memory fragments
        for i in range(25):  # Exceeds consolidation threshold
            await temporal_memory_manager.add_memory_fragment(
                user_id=user_id,
                content=f"Working memory fragment {i}",
                memory_type=MemoryType.WORKING,
                importance=0.5
            )

        # Check that memories are consolidated
        memories = temporal_memory_manager.memory_cache.get(user_id, [])

        # Should have consolidated into episodic memory
        episodic_count = sum(1 for m in memories if m.type == MemoryType.EPISODIC)
        assert episodic_count > 0

    async def test_memory_relevance_decay(self, temporal_memory_manager):
        """Test memory relevance decay over time"""
        user_id = "test_user_123"

        # Add an old memory
        old_timestamp = datetime.now() - timedelta(days=30)
        await temporal_memory_manager.add_memory_fragment(
            user_id=user_id,
            content="Old preference",
            memory_type=MemoryType.SEMANTIC,
            importance=0.8
        )

        # Manually set old timestamp
        if user_id in temporal_memory_manager.memory_cache:
            temporal_memory_manager.memory_cache[user_id][0].timestamp = old_timestamp

        # Calculate decayed importance
        memories = temporal_memory_manager.memory_cache.get(user_id, [])
        if memories:
            decayed_importance = temporal_memory_manager._calculate_decayed_importance(memories[0])
            assert decayed_importance < 0.8  # Should be decayed

    async def test_cross_session_context_reconstruction(self, temporal_memory_manager):
        """Test reconstructing context across sessions"""
        user_id = "test_user_123"
        session_id = "session_456"

        # Add memories from previous session
        await temporal_memory_manager.add_memory_fragment(
            user_id=user_id,
            content="User has a family of 4",
            memory_type=MemoryType.SEMANTIC,
            importance=0.9,
            session_id=session_id
        )

        # Reconstruct context for new session
        context = await temporal_memory_manager.reconstruct_cross_session_context(user_id)

        assert context is not None
        assert "family of 4" in str(context.semantic_memory)

    async def test_memory_performance(self, temporal_memory_manager):
        """Test memory retrieval performance (<500ms requirement)"""
        import time

        user_id = "test_user_123"

        # Add 100 memory fragments
        for i in range(100):
            await temporal_memory_manager.add_memory_fragment(
                user_id=user_id,
                content=f"Memory fragment {i}",
                memory_type=MemoryType.SEMANTIC,
                importance=0.5
            )

        # Measure retrieval time
        start_time = time.time()
        context = await temporal_memory_manager.get_contextual_memory(user_id, "test query")
        end_time = time.time()

        retrieval_time = (end_time - start_time) * 1000  # Convert to ms
        assert retrieval_time < 500, f"Memory retrieval took {retrieval_time}ms, expected < 500ms"
        assert context is not None

    async def test_memory_fragment_validation(self, temporal_memory_manager):
        """Test memory fragment validation"""
        user_id = "test_user_123"

        # Test with empty content
        with pytest.raises(ValueError):
            await temporal_memory_manager.add_memory_fragment(
                user_id=user_id,
                content="",
                memory_type=MemoryType.SEMANTIC
            )

        # Test with invalid memory type
        with pytest.raises(ValueError):
            await temporal_memory_manager.add_memory_fragment(
                user_id=user_id,
                content="Valid content",
                memory_type="invalid_type"
            )

        # Test with invalid importance
        with pytest.raises(ValueError):
            await temporal_memory_manager.add_memory_fragment(
                user_id=user_id,
                content="Valid content",
                memory_type=MemoryType.SEMANTIC,
                importance=1.5  # Over max value
            )