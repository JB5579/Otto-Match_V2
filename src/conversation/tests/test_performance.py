"""
Performance Tests for Conversation System
Tests response times and performance requirements
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.conversation.conversation_agent import ConversationAgent
from src.conversation.nlu_service import NLUService, NLUResult, Intent, Entity, UserPreference
from src.conversation.response_generator import ResponseGenerator
from src.conversation.groq_client import GroqClient
from src.memory.zep_client import ZepClient, ConversationContext


@pytest.fixture
async def performance_agent():
    """Create agent for performance testing"""
    # Mock clients
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    zep_client = Mock(spec=ZepClient)
    zep_client.initialized = True

    agent = ConversationAgent(groq_client=groq_client, zep_client=zep_client)

    # Initialize mocks with fast responses
    agent.groq_client.initialize = AsyncMock(return_value=True)
    agent.nlu_service.initialize = AsyncMock(return_value=True)
    agent.response_generator.initialize = AsyncMock(return_value=True)

    await agent.initialize()
    return agent


class TestPerformance:
    """Performance test cases"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time_under_2_seconds(self, performance_agent):
        """Test that responses are under 2 seconds"""
        user_id = "perf_test_user"
        message = "I'm looking for a safe family SUV under $30,000"

        # Mock fast responses
        performance_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )

        performance_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.95),
                entities=[],
                preferences=[],
                sentiment="neutral"
            )
        )

        performance_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        performance_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
        performance_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)
        performance_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="I'll help you find SUVs under $30,000.",
                response_type="text",
                suggestions=[],
                metadata={},
                needs_follow_up=True
            )
        )

        # Measure response time
        start_time = time.time()
        response = await performance_agent.process_message(user_id, message)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        # Verify under 2 seconds
        assert response_time_ms < 2000, f"Response took {response_time_ms:.2f}ms, must be under 2000ms"
        assert response.processing_time_ms == response_time_ms

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_user_handling(self, performance_agent):
        """Test handling multiple concurrent users"""
        num_users = 10
        messages_per_user = 5

        # Mock responses
        performance_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )

        performance_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.9),
                entities=[],
                preferences=[],
                sentiment="neutral"
            )
        )

        performance_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        performance_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
        performance_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)
        performance_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="Response",
                response_type="text",
                suggestions=[],
                metadata={},
                needs_follow_up=True
            )
        )

        # Create concurrent tasks
        tasks = []
        for user_idx in range(num_users):
            user_id = f"concurrent_user_{user_idx}"
            for msg_idx in range(messages_per_user):
                message = f"Message {msg_idx} from user {user_idx}"
                task = performance_agent.process_message(user_id, message)
                tasks.append(task)

        # Execute all tasks concurrently
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all responses completed
        assert len(responses) == num_users * messages_per_user
        for response in responses:
            assert response.response_type == "text"

        # Verify reasonable total time (should not be sum of all individual times)
        total_time = end_time - start_time
        avg_time_per_response = (total_time / (num_users * messages_per_user)) * 1000

        assert avg_time_per_response < 2000, f"Average response time {avg_time_per_response:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_stability(self, performance_agent):
        """Test that memory usage remains stable over many conversations"""
        import gc
        import sys

        # Initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Simulate many conversations
        num_conversations = 100
        messages_per_conversation = 10

        # Mock responses
        performance_agent.nlu_service._get_enhanced_context = AsyncMock(
            return_value=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            )
        )

        performance_agent.nlu_service.analyze_message = AsyncMock(
            return_value=NLUResult(
                intent=Intent(primary="search", confidence=0.9),
                entities=[],
                preferences=[],
                sentiment="neutral"
            )
        )

        performance_agent.entity_extractor.extract_entities = AsyncMock(return_value=[])
        performance_agent.preference_detector.detect_preferences = AsyncMock(return_value=[])
        performance_agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)
        performance_agent.response_generator.generate_response = AsyncMock(
            return_value=ConversationResponse(
                message="Response",
                response_type="text",
                suggestions=[],
                metadata={},
                needs_follow_up=True
            )
        )

        # Process conversations
        for conv_idx in range(num_conversations):
            user_id = f"memory_test_user_{conv_idx}"
            for msg_idx in range(messages_per_conversation):
                await performance_agent.process_message(user_id, f"Message {msg_idx}")

            # Clean up some conversations
            if conv_idx % 10 == 0:
                # Reset some conversations
                for clean_idx in range(conv_idx - 10, conv_idx):
                    clean_user_id = f"memory_test_user_{clean_idx}"
                    await performance_agent.reset_conversation(clean_user_id)

        # Check memory usage
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be reasonable (less than 2x)
        memory_growth = final_objects / initial_objects
        assert memory_growth < 2.0, f"Memory grew by {memory_growth:.2f}x, may indicate memory leak"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_nlu_processing_performance(self):
        """Test NLU service performance specifically"""
        groq_client = Mock(spec=GroqClient)
        groq_client.initialized = True

        nlu_service = NLUService(groq_client=groq_client)
        await nlu_service.initialize()

        # Mock fast Groq response
        nlu_service.groq_client.generate_response = AsyncMock(
            return_value={
                'success': True,
                'response': '{"primary_intent": "search", "confidence": 0.95, "requires_data": true}'
            }
        )

        # Test multiple messages
        num_messages = 50
        messages = [
            "I'm looking for a safe family SUV under $30,000",
            "Compare Toyota RAV4 vs Honda CR-V",
            "What's the most reliable sedan?",
            "Need something good on gas",
            "Show me electric vehicles with long range"
        ] * 10  # Repeat for multiple tests

        start_time = time.time()
        tasks = [
            nlu_service.analyze_message(f"user_{i}", msg, context=ConversationContext(
                working_memory=[],
                episodic_memory=[],
                semantic_memory={},
                user_preferences={}
            ))
            for i, msg in enumerate(messages)
        ]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all results
        assert len(results) == num_messages
        for result in results:
            assert isinstance(result, NLUResult)
            assert result.intent.primary == "search"

        # Check average time
        avg_time = ((end_time - start_time) / num_messages) * 1000
        assert avg_time < 500, f"NLU processing average {avg_time:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_entity_extraction_performance(self):
        """Test entity extraction performance"""
        from src.conversation.intent_models import EntityExtractor

        extractor = EntityExtractor()

        # Test messages with varying complexity
        test_messages = [
            "Simple: Toyota Camry",
            "Medium: I need a 2023 Honda CR-V with AWD under $30,000",
            "Complex: Looking for a certified pre-owned 2022 Tesla Model 3 Long Range with autopilot, premium interior, and full self-driving capability under $45,000 from a dealer in California"
        ] * 20

        start_time = time.time()
        tasks = [extractor.extract_entities(msg) for msg in test_messages]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify results
        assert len(results) == len(test_messages)
        for entities in results:
            assert isinstance(entities, list)

        # Check performance
        avg_time = ((end_time - start_time) / len(test_messages)) * 1000
        assert avg_time < 100, f"Entity extraction average {avg_time:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_generation_performance(self):
        """Test response generation performance"""
        groq_client = Mock(spec=GroqClient)
        groq_client.initialized = True

        generator = ResponseGenerator(groq_client=groq_client)
        await generator.initialize()

        # Mock fast Groq response
        generator.groq_client.generate_response = AsyncMock(
            return_value={
                'success': True,
                'response': 'Here\'s my response to your query about vehicles.'
            }
        )

        # Test multiple response generations
        num_responses = 50
        nlu_results = [
            NLUResult(
                intent=Intent(primary="search", confidence=0.9),
                entities=[],
                preferences=[],
                sentiment="neutral"
            )
        ] * num_responses

        start_time = time.time()
        tasks = [
            generator.generate_response(
                user_id=f"user_{i}",
                nlu_result=result,
                context=ConversationContext(
                    working_memory=[],
                    episodic_memory=[],
                    semantic_memory={},
                    user_preferences={}
                )
            )
            for i, result in enumerate(nlu_results)
        ]

        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify results
        assert len(responses) == num_responses
        for response in responses:
            assert response.message is not None
            assert len(response.suggestions) > 0

        # Check performance
        avg_time = ((end_time - start_time) / num_responses) * 1000
        assert avg_time < 1000, f"Response generation average {avg_time:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_context_retrieval_performance(self):
        """Test context retrieval performance"""
        groq_client = Mock(spec=GroqClient)
        zep_client = Mock(spec=ZepClient)
        zep_client.initialized = True

        nlu_service = NLUService(groq_client=groq_client, zep_client=zep_client)
        await nlu_service.initialize()

        # Mock Zep responses
        zep_client.get_conversation_history = AsyncMock(return_value=[])
        zep_client.search_conversations = AsyncMock(return_value=[])

        # Test context retrieval
        num_retrievals = 50
        start_time = time.time()
        tasks = [
            nlu_service._get_enhanced_context(
                user_id=f"user_{i}",
                current_query=f"Query {i}",
                session_id=f"session_{i}"
            )
            for i in range(num_retrievals)
        ]

        contexts = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify results
        assert len(contexts) == num_retrievals
        for context in contexts:
            assert isinstance(context, ConversationContext)

        # Check performance
        avg_time = ((end_time - start_time) / num_retrievals) * 1000
        assert avg_time < 200, f"Context retrieval average {avg_time:.2f}ms too high"


@pytest.mark.asyncio
async def test_system_under_load():
    """Test entire system under load"""
    # Create realistic load test
    num_concurrent_users = 20
    messages_per_user = 5

    # Mock system
    groq_client = Mock(spec=GroqClient)
    groq_client.initialized = True

    zep_client = Mock(spec=ZepClient)
    zep_client.initialized = True

    agent = ConversationAgent(groq_client=groq_client, zep_client=zep_client)

    # Initialize with realistic timing
    agent.groq_client.initialize = AsyncMock(return_value=True)
    agent.nlu_service.initialize = AsyncMock(return_value=True)
    agent.response_generator.initialize = AsyncMock(return_value=True)
    await agent.initialize()

    # Mock with realistic response times
    import random

    async def realistic_delay(*args, **kwargs):
        await asyncio.sleep(random.uniform(0.05, 0.15))  # 50-150ms delay
        return {
            'success': True,
            'response': '{"primary_intent": "search", "confidence": 0.9}'
        }

    agent.nlu_service._get_enhanced_context = AsyncMock(
        side_effect=lambda *args, **kwargs: asyncio.sleep(0.02) or ConversationContext(
            working_memory=[],
            episodic_memory=[],
            semantic_memory={},
            user_preferences={}
        )
    )

    agent.nlu_service.analyze_message = AsyncMock(side_effect=realistic_delay)
    agent.entity_extractor.extract_entities = AsyncMock(
        side_effect=lambda *args, **kwargs: asyncio.sleep(0.01) or []
    )
    agent.preference_detector.detect_preferences = AsyncMock(
        side_effect=lambda *args, **kwargs: asyncio.sleep(0.01) or []
    )
    agent.scenario_manager.detect_scenario = AsyncMock(return_value=None)
    agent.response_generator.generate_response = AsyncMock(
        side_effect=lambda *args, **kwargs: (
            asyncio.sleep(0.05) or
            ConversationResponse(
                message="Response",
                response_type="text",
                suggestions=[],
                metadata={},
                needs_follow_up=True
            )
        )
    )

    # Generate load
    all_tasks = []
    start_time = time.time()

    for user_idx in range(num_concurrent_users):
        user_id = f"load_user_{user_idx}"
        for msg_idx in range(messages_per_user):
            message = f"Load test message {msg_idx} from user {user_idx}"
            all_tasks.append(agent.process_message(user_id, message))

    # Execute with timeout
    responses = await asyncio.wait_for(
        asyncio.gather(*tasks),
        timeout=30  # 30 second timeout
    )

    end_time = time.time()

    # Verify all responses
    assert len(responses) == num_concurrent_users * messages_per_user

    # Check performance metrics
    total_time = end_time - start_time
    total_requests = num_concurrent_users * messages_per_user
    requests_per_second = total_requests / total_time

    # Should handle at least 10 requests per second
    assert requests_per_second > 10, f"System only handled {requests_per_second:.2f} req/s"

    # Check response times
    response_times = [r.processing_time_ms for r in responses if r.processing_time_ms]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 2000, f"Average response time {avg_response_time:.2f}ms too high"
        assert max_response_time < 3000, f"Max response time {max_response_time:.2f}ms too high"


if __name__ == "__main__":
    # Run performance tests with specific markers
    pytest.main([
        __file__,
        "-m",
        "performance",
        "-v",
        "--tb=short"
    ])