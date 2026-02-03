"""
Performance tests for memory and preference operations
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from src.memory.temporal_memory import TemporalMemoryManager
from src.intelligence.preference_engine import PreferenceEngine
from src.services.profile_service import ProfileService


@pytest.mark.performance
class TestPerformanceRequirements:
    """Test suite to verify performance requirements (<500ms retrieval)"""

    async def test_memory_retrieval_performance_large_dataset(self, mock_zep_client, mock_groq_client):
        """Test memory retrieval with large dataset"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        user_id = "perf_user_large"

        # Create large memory dataset (1000 fragments)
        for i in range(1000):
            await memory_manager.add_memory_fragment(
                user_id=user_id,
                content=f"Memory fragment {i} with detailed content about vehicle preferences",
                memory_type="semantic" if i % 3 == 0 else "episodic",
                importance=0.5 + (i % 5) * 0.1
            )

        # Measure retrieval time
        start_time = time.time()
        context = await memory_manager.get_contextual_memory(user_id, "Find my preferences")
        end_time = time.time()

        retrieval_time = (end_time - start_time) * 1000
        print(f"\nMemory retrieval time for 1000 fragments: {retrieval_time:.2f}ms")

        assert retrieval_time < 500, f"Retrieval took {retrieval_time:.2f}ms, expected < 500ms"
        assert context is not None
        assert len(context.semantic_memory) > 0

    async def test_preference_extraction_performance(self, mock_groq_client, temporal_memory_manager):
        """Test preference extraction performance"""
        preference_engine = PreferenceEngine(mock_groq_client, temporal_memory_manager)

        # Create complex message with multiple preferences
        complex_message = (
            "I'm looking for a reliable Japanese SUV under $30,000 with good safety ratings, "
            "excellent fuel economy, advanced driver assistance features, plenty of cargo space, "
            "comfortable seating for my family of five, a strong warranty, good resale value, "
            "available all-wheel drive, modern infotainment system with Apple CarPlay, "
            "and prefer dealerships near my location with good service ratings."
        )

        # Measure extraction time
        start_time = time.time()
        preferences = await preference_engine.extract_preferences(complex_message, [])
        end_time = time.time()

        extraction_time = (end_time - start_time) * 1000
        print(f"\nPreference extraction time: {extraction_time:.2f}ms")

        assert extraction_time < 100, f"Extraction took {extraction_time:.2f}ms, expected < 100ms"
        assert len(preferences) >= 5, "Should extract multiple preferences"

    async def test_profile_update_performance(self, profile_service):
        """Test profile update performance"""
        user_id = "perf_user_profile"

        # Create many preferences to update
        preferences = []
        for i in range(100):
            preferences.append(
                UserPreference(
                    category=f"category_{i}",
                    value=f"value_{i}",
                    weight=0.5 + (i % 10) * 0.05,
                    source="explicit",
                    confidence=0.8
                )
            )

        # Measure update time
        start_time = time.time()
        success = await profile_service.update_profile_preferences(user_id, preferences)
        end_time = time.time()

        update_time = (end_time - start_time) * 1000
        print(f"\nProfile update time for 100 preferences: {update_time:.2f}ms")

        assert update_time < 500, f"Update took {update_time:.2f}ms, expected < 500ms"
        assert success is True

    async def test_concurrent_memory_access(self, mock_zep_client, mock_groq_client):
        """Test concurrent memory access performance"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        user_count = 10
        operations_per_user = 50

        async def user_operations(user_id: int):
            """Simulate user memory operations"""
            # Add memories
            for i in range(operations_per_user):
                await memory_manager.add_memory_fragment(
                    user_id=f"user_{user_id}",
                    content=f"Memory {i} for user {user_id}",
                    memory_type="working",
                    importance=0.7
                )

            # Retrieve memories
            for i in range(10):
                await memory_manager.get_contextual_memory(f"user_{user_id}", f"Query {i}")

        # Measure concurrent execution time
        start_time = time.time()

        # Run operations concurrently
        tasks = [user_operations(i) for i in range(user_count)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        avg_time_per_user = total_time / user_count

        print(f"\nConcurrent operations time: {total_time:.2f}ms total, {avg_time_per_user:.2f}ms per user")

        assert avg_time_per_user < 500, f"Average time per user {avg_time_per_user:.2f}ms, expected < 500ms"

    async def test_memory_search_performance(self, mock_zep_client):
        """Test memory search performance with large dataset"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        user_id = "search_perf_user"

        # Create diverse memory content
        base_memories = [
            "Toyota Highlander is a reliable family SUV",
            "Honda CR-V offers great fuel economy",
            "Mazda CX-5 has excellent safety ratings",
            "Nissan Rogue provides good value for money",
            "Subaru Forester comes with standard AWD"
        ]

        # Create many variations
        for i in range(500):
            base_idx = i % len(base_memories)
            content = f"{base_memories[base_idx]} - Note {i} with additional context"
            await memory_manager.add_memory_fragment(
                user_id=user_id,
                content=content,
                memory_type="semantic",
                importance=0.6 + (i % 5) * 0.08
            )

        # Test different search queries
        search_queries = [
            "reliable SUV",
            "fuel economy",
            "safety ratings",
            "family vehicle",
            "all-wheel drive"
        ]

        search_times = []
        for query in search_queries:
            start_time = time.time()
            results = await memory_manager._search_semantic_memory(user_id, query)
            end_time = time.time()
            search_time = (end_time - start_time) * 1000
            search_times.append(search_time)
            print(f"Search '{query}': {search_time:.2f}ms, results: {len(results)}")

        avg_search_time = sum(search_times) / len(search_times)
        print(f"\nAverage search time: {avg_search_time:.2f}ms")

        assert avg_search_time < 100, f"Average search time {avg_search_time:.2f}ms, expected < 100ms"
        assert all(t < 200 for t in search_times), "All searches should complete in <200ms"

    async def test_preference_timeline_performance(self, profile_service):
        """Test preference timeline generation performance"""
        user_id = "timeline_perf_user"

        # Create preference history over time
        days = 365
        preferences_per_day = 3

        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            for pref_num in range(preferences_per_day):
                preference = UserPreference(
                    category=f"category_{pref_num}",
                    value=f"value_{day}_{pref_num}",
                    weight=0.5 + (pref_num * 0.1),
                    source="explicit" if day % 7 == 0 else "implicit",
                    timestamp=date
                )
                await profile_service.update_profile_preferences(user_id, [preference])

        # Measure timeline generation for different ranges
        ranges = [7, 30, 90, 365]

        for days_range in ranges:
            start_time = time.time()
            timeline = await profile_service.create_preference_timeline(user_id, days=days_range)
            end_time = time.time()

            generation_time = (end_time - start_time) * 1000
            print(f"\nTimeline generation for {days_range} days: {generation_time:.2f}ms, items: {len(timeline)}")

            assert generation_time < 500, f"Timeline for {days_range} days took {generation_time:.2f}ms, expected < 500ms"
            assert len(timeline) > 0, f"Should return timeline items for {days_range} days"

    async def test_memory_consolidation_performance(self, mock_zep_client, mock_groq_client):
        """Test memory consolidation performance"""
        memory_manager = TemporalMemoryManager(mock_zep_client, consolidation_threshold=50)
        user_id = "consolidation_perf_user"

        # Add memories to trigger consolidation
        for i in range(100):
            await memory_manager.add_memory_fragment(
                user_id=user_id,
                content=f"Working memory item {i}: Detailed vehicle preference information",
                memory_type="working",
                importance=0.5 + (i % 5) * 0.1
            )

        # Measure consolidation time
        start_time = time.time()
        await memory_manager.consolidate_memories(user_id)
        end_time = time.time()

        consolidation_time = (end_time - start_time) * 1000
        print(f"\nMemory consolidation time: {consolidation_time:.2f}ms")

        assert consolidation_time < 1000, f"Consolidation took {consolidation_time:.2f}ms, expected < 1000ms"

        # Verify consolidation worked
        memories = memory_manager.memory_cache.get(user_id, [])
        episodic_count = sum(1 for m in memories if m.type == "episodic")
        assert episodic_count > 0, "Should have episodic memories after consolidation"

    async def test_cache_performance_warm_vs_cold(self, mock_zep_client, mock_groq_client):
        """Test performance difference between warm and cold cache"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        user_id = "cache_perf_user"

        # Add memories
        for i in range(50):
            await memory_manager.add_memory_fragment(
                user_id=user_id,
                content=f"Cached memory {i}",
                memory_type="semantic",
                importance=0.7
            )

        # Cold cache retrieval
        memory_manager.memory_cache.clear()
        start_time = time.time()
        context1 = await memory_manager.get_contextual_memory(user_id, "Cold cache query")
        cold_time = (time.time() - start_time) * 1000

        # Warm cache retrieval
        start_time = time.time()
        context2 = await memory_manager.get_contextual_memory(user_id, "Warm cache query")
        warm_time = (time.time() - start_time) * 1000

        print(f"\nCold cache retrieval: {cold_time:.2f}ms")
        print(f"Warm cache retrieval: {warm_time:.2f}ms")
        print(f"Performance improvement: {((cold_time - warm_time) / cold_time * 100):.1f}%")

        assert cold_time < 500, f"Cold cache took {cold_time:.2f}ms, expected < 500ms"
        assert warm_time < cold_time, "Warm cache should be faster than cold cache"
        assert warm_time < 100, f"Warm cache took {warm_time:.2f}ms, expected < 100ms"

    @pytest.mark.slow
    async def test_stress_test_memory_operations(self, mock_zep_client, mock_groq_client):
        """Stress test for memory operations under load"""
        memory_manager = TemporalMemoryManager(mock_zep_client)
        preference_engine = PreferenceEngine(mock_groq_client, memory_manager)

        # Parameters for stress test
        user_count = 100
        operations_per_user = 20
        concurrent_users = 10

        async def simulate_user_session(user_id: int):
            """Simulate a complete user session"""
            session_preferences = []

            for op in range(operations_per_user):
                # Random-like operations
                message = f"I need a vehicle with preference {op}"
                preferences = await preference_engine.extract_preferences(message, [])
                session_preferences.extend(preferences)

                # Add memory
                await memory_manager.add_memory_fragment(
                    user_id=f"stress_user_{user_id}",
                    content=f"Session preference {op}",
                    memory_type="working",
                    importance=0.6
                )

            # Get context at end
            await memory_manager.get_contextual_memory(f"stress_user_{user_id}", "End of session")

            return len(session_preferences)

        # Run stress test
        print(f"\nRunning stress test: {user_count} users, {operations_per_user} ops each")
        start_time = time.time()

        # Execute in batches of concurrent users
        batch_size = concurrent_users
        total_preferences = 0

        for batch_start in range(0, user_count, batch_size):
            batch_end = min(batch_start + batch_size, user_count)
            tasks = [simulate_user_session(i) for i in range(batch_start, batch_end)]
            results = await asyncio.gather(*tasks)
            total_preferences += sum(results)

        total_time = time.time() - start_time
        total_ops = user_count * operations_per_user
        ops_per_second = total_ops / total_time

        print(f"Total operations: {total_ops}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Operations per second: {ops_per_second:.2f}")
        print(f"Average time per operation: {(total_time/total_ops)*1000:.2f}ms")
        print(f"Total preferences extracted: {total_preferences}")

        # Verify performance under stress
        avg_time_per_op = (total_time / total_ops) * 1000
        assert avg_time_per_op < 50, f"Average time per operation {avg_time_per_op:.2f}ms too high under stress"