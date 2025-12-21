"""
Comprehensive Unit Tests for User Interaction Tracker

Tests for Story 1-5: Build Vehicle Comparison and Recommendation Engine
Covers all user interaction tracking and profile building functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.recommendation.interaction_tracker import (
    InteractionTracker, InteractionType, UserSession, UserBehaviorProfile
)


class TestInteractionTracker:
    """Test suite for InteractionTracker"""

    @pytest.fixture
    def interaction_tracker(self):
        """Create InteractionTracker instance"""
        return InteractionTracker()

    @pytest.fixture
    def sample_interaction_data(self):
        """Sample interaction data for testing"""
        return {
            'user_id': 'test_user_123',
            'session_id': 'session_456',
            'interaction_type': InteractionType.VIEW,
            'vehicle_ids': ['vehicle_1', 'vehicle_2'],
            'interaction_data': {
                'source': 'search_results',
                'duration': 30
            },
            'context': {
                'search_query': 'Toyota SUV',
                'page': 'search_results'
            },
            'timestamp': datetime.now()
        }

    @pytest.fixture
    def sample_comparison_interaction(self):
        """Sample comparison interaction data"""
        return {
            'user_id': 'test_user_123',
            'interaction_type': InteractionType.COMPARE,
            'vehicle_ids': ['vehicle_1', 'vehicle_2', 'vehicle_3'],
            'interaction_data': {
                'comparison_id': 'comp_789',
                'processing_time': 1.5,
                'vehicle_count': 3
            },
            'context': {
                'source': 'vehicle_details'
            }
        }

    @pytest.mark.asyncio
    async def test_track_interaction_success(self, interaction_tracker, sample_interaction_data):
        """Test successful interaction tracking"""
        await interaction_tracker.track_interaction(sample_interaction_data)

        # Verify session was created
        assert len(interaction_tracker.active_sessions) == 1
        assert 'session_456' in interaction_tracker.active_sessions

        session = interaction_tracker.active_sessions['session_456']
        assert session.user_id == 'test_user_123'
        assert session.session_id == 'session_456'
        assert len(session.interactions) == 1
        assert 'vehicle_1' in session.viewed_vehicles
        assert 'vehicle_2' in session.viewed_vehicles

    @pytest.mark.asyncio
    async def test_track_interaction_without_session_id(self, interaction_tracker, sample_interaction_data):
        """Test interaction tracking without provided session ID"""
        del sample_interaction_data['session_id']  # Remove session ID

        await interaction_tracker.track_interaction(sample_interaction_data)

        # Verify session was auto-created
        assert len(interaction_tracker.active_sessions) == 1
        session = list(interaction_tracker.active_sessions.values())[0]
        assert session.user_id == 'test_user_123'
        assert session.interactions[0]['type'] == InteractionType.VIEW

    @pytest.mark.asyncio
    async def test_track_interaction_missing_user_id(self, interaction_tracker, sample_interaction_data):
        """Test interaction tracking with missing user ID"""
        del sample_interaction_data['user_id']

        # Should handle gracefully without error
        await interaction_tracker.track_interaction(sample_interaction_data)

        # No session should be created
        assert len(interaction_tracker.active_sessions) == 0

    @pytest.mark.asyncio
    async def test_track_comparison_interaction(self, interaction_tracker, sample_comparison_interaction):
        """Test comparison interaction tracking"""
        await interaction_tracker.track_interaction(sample_comparison_interaction)

        # Verify session and comparison tracking
        assert len(interaction_tracker.active_sessions) == 1
        session = list(interaction_tracker.active_sessions.values())[0]
        assert len(session.comparisons) == 1
        assert len(session.comparisons[0]) == 3  # 3 vehicles compared

    @pytest.mark.asyncio
    async def test_track_comparison_specific_method(self, interaction_tracker):
        """Test dedicated comparison tracking method"""
        await interaction_tracker.track_comparison(
            user_id='test_user_123',
            vehicle_ids=['vehicle_1', 'vehicle_2'],
            comparison_id='comp_123',
            processing_time=1.2
        )

        assert len(interaction_tracker.active_sessions) == 1
        session = list(interaction_tracker.active_sessions.values())[0]
        assert len(session.comparisons) == 1
        assert session.comparisons[0] == ['vehicle_1', 'vehicle_2']

        # Check interaction record
        assert len(session.interactions) == 1
        interaction = session.interactions[0]
        assert interaction['type'] == InteractionType.COMPARE
        assert interaction['data']['comparison_id'] == 'comp_123'
        assert interaction['data']['processing_time'] == 1.2

    @pytest.mark.asyncio
    async def test_get_user_profile(self, interaction_tracker):
        """Test user profile generation"""
        user_id = 'test_user_123'
        profile = await interaction_tracker.get_user_profile(user_id)

        assert isinstance(profile, UserBehaviorProfile)
        assert profile.user_id == user_id
        assert profile.total_sessions == 0  # No sessions yet
        assert profile.last_updated is not None

    @pytest.mark.asyncio
    async def test_get_user_profile_with_sessions(self, interaction_tracker, sample_interaction_data):
        """Test user profile generation with existing sessions"""
        # Create some sessions first
        await interaction_tracker.track_interaction(sample_interaction_data)
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'interaction_type': InteractionType.SAVE,
            'vehicle_ids': ['vehicle_1']
        })

        profile = await interaction_tracker.get_user_profile('test_user_123')

        assert isinstance(profile, UserBehaviorProfile)
        assert profile.user_id == 'test_user_123'
        assert profile.total_sessions >= 1
        assert profile.total_views >= 1
        assert profile.total_saves >= 1
        assert profile.avg_session_duration >= 0

    @pytest.mark.asyncio
    async def test_multiple_interactions_same_session(self, interaction_tracker, sample_interaction_data):
        """Test multiple interactions in the same session"""
        session_id = 'session_456'
        user_id = 'test_user_123'

        # Track multiple interactions
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'interaction_type': InteractionType.VIEW,
            'vehicle_ids': ['vehicle_1']
        })

        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'interaction_type': InteractionType.SAVE,
            'vehicle_ids': ['vehicle_1']
        })

        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'interaction_type': InteractionType.SEARCH,
            'vehicle_ids': [],
            'interaction_data': {'query': 'Toyota SUV'}
        })

        # Verify all interactions were tracked
        session = interaction_tracker.active_sessions[session_id]
        assert len(session.interactions) == 3
        assert 'vehicle_1' in session.viewed_vehicles
        assert 'vehicle_1' in session.saved_vehicles
        assert len(session.search_queries) == 1
        assert session.search_queries[0] == 'Toyota SUV'

    @pytest.mark.asyncio
    async def test_session_timeout(self, interaction_tracker, sample_interaction_data):
        """Test session timeout handling"""
        session_id = 'session_timeout_test'
        user_id = 'test_user_timeout'

        # Create session with old timestamp
        old_timestamp = datetime.now() - timedelta(minutes=35)  # Beyond 30 min timeout

        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': old_timestamp
        })

        assert len(interaction_tracker.active_sessions) == 1

        # Try to get the session - should return None due to timeout
        session = await interaction_tracker._get_session(session_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, interaction_tracker, sample_interaction_data):
        """Test retrieving user session history"""
        user_id = 'test_user_sessions'

        # Create multiple sessions
        for i in range(3):
            await interaction_tracker.track_interaction({
                **sample_interaction_data,
                'user_id': user_id,
                'session_id': f'session_{i}',
                'timestamp': datetime.now() - timedelta(minutes=i * 10)
            })

        sessions = await interaction_tracker.get_user_sessions(user_id)

        assert isinstance(sessions, list)
        assert len(sessions) == 3

        # Check session structure
        for session_data in sessions:
            assert 'session_id' in session_data
            assert 'start_time' in session_data
            assert 'last_activity' in session_data
            assert 'duration_seconds' in session_data
            assert 'interaction_count' in session_data
            assert 'viewed_vehicles' in session_data
            assert 'saved_vehicles' in session_data
            assert 'search_count' in session_data
            assert 'comparison_count' in session_data

    @pytest.mark.asyncio
    async def test_get_interaction_stats(self, interaction_tracker, sample_interaction_data):
        """Test interaction statistics generation"""
        user_id = 'test_user_stats'

        # Create interactions over different days
        base_time = datetime.now() - timedelta(days=5)
        for i in range(10):
            await interaction_tracker.track_interaction({
                **sample_interaction_data,
                'user_id': user_id,
                'session_id': f'session_stats_{i}',
                'timestamp': base_time + timedelta(days=i // 2),
                'interaction_type': [InteractionType.VIEW, InteractionType.SAVE, InteractionType.SEARCH][i % 3],
                'vehicle_ids': [f'vehicle_{i}']
            })

        stats = await interaction_tracker.get_interaction_stats(user_id, days=10)

        assert isinstance(stats, dict)
        assert 'total_interactions' in stats
        assert 'interaction_types' in stats
        assert 'daily_activity' in stats
        assert 'vehicle_engagement' in stats

        assert stats['total_interactions'] == 10
        assert stats['vehicle_engagement']['unique_vehicles_viewed'] <= 10
        assert stats['vehicle_engagement']['total_vehicles_saved'] >= 0
        assert stats['vehicle_engagement']['total_comparisons'] >= 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, interaction_tracker, sample_interaction_data):
        """Test cleanup of expired sessions"""
        # Create sessions with different ages
        current_time = datetime.now()
        old_time = current_time - timedelta(minutes=35)  # Expired
        recent_time = current_time - timedelta(minutes=10)  # Active

        # Create expired session
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': 'user_expired',
            'session_id': 'expired_session',
            'timestamp': old_time
        })

        # Create active session
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': 'user_active',
            'session_id': 'active_session',
            'timestamp': recent_time
        })

        assert len(interaction_tracker.active_sessions) == 2

        # Run cleanup
        await interaction_tracker.cleanup_expired_sessions()

        # Only active session should remain
        assert len(interaction_tracker.active_sessions) == 1
        assert 'active_session' in interaction_tracker.active_sessions
        assert 'expired_session' not in interaction_tracker.active_sessions

    @pytest.mark.asyncio
    async def test_background_cleanup_task(self, interaction_tracker):
        """Test background cleanup task"""
        # Start background task
        await interaction_tracker.start_background_tasks()
        assert interaction_tracker.cleanup_task is not None

        # Create an expired session
        old_time = datetime.now() - timedelta(minutes=35)
        await interaction_tracker.track_interaction({
            'user_id': 'bg_test_user',
            'session_id': 'bg_expired_session',
            'interaction_type': InteractionType.VIEW,
            'vehicle_ids': ['vehicle_1'],
            'timestamp': old_time
        })

        assert len(interaction_tracker.active_sessions) == 1

        # Wait a bit for cleanup to run (in real scenario, cleanup runs every 5 minutes)
        # For testing, we'll trigger cleanup manually
        await interaction_tracker.cleanup_expired_sessions()

        assert len(interaction_tracker.active_sessions) == 0

        # Stop background task
        await interaction_tracker.stop_background_tasks()
        assert interaction_tracker.cleanup_task is None

    @pytest.mark.asyncio
    async def test_user_behavior_profile_creation(self, interaction_tracker):
        """Test UserBehaviorProfile creation and attributes"""
        profile = UserBehaviorProfile(user_id='test_profile')

        assert profile.user_id == 'test_profile'
        assert profile.total_sessions == 0
        assert profile.total_views == 0
        assert profile.total_saves == 0
        assert profile.total_comparisons == 0
        assert profile.total_searches == 0
        assert profile.avg_session_duration == 0.0
        assert isinstance(profile.preferred_brands, dict)
        assert isinstance(profile.preferred_vehicle_types, dict)
        assert isinstance(profile.price_range_preference, dict)
        assert isinstance(profile.feature_preferences, dict)
        assert isinstance(profile.interaction_patterns, dict)
        assert isinstance(profile.last_updated, datetime)

    @pytest.mark.asyncio
    async def test_user_session_creation_and_attributes(self, interaction_tracker):
        """Test UserSession creation and attributes"""
        session_id = 'test_session_123'
        user_id = 'test_user_456'
        start_time = datetime.now()

        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            start_time=start_time,
            last_activity=start_time
        )

        assert session.user_id == user_id
        assert session.session_id == session_id
        assert session.start_time == start_time
        assert session.last_activity == start_time
        assert isinstance(session.interactions, list)
        assert len(session.interactions) == 0
        assert isinstance(session.viewed_vehicles, set)
        assert isinstance(session.saved_vehicles, set)
        assert isinstance(session.search_queries, list)
        assert isinstance(session.comparisons, list)

    def test_interaction_type_enum(self):
        """Test InteractionType enum values"""
        assert InteractionType.VIEW.value == "view"
        assert InteractionType.SAVE.value == "save"
        assert InteractionType.COMPARE.value == "compare"
        assert InteractionType.SEARCH.value == "search"
        assert InteractionType.RECOMMENDATION_CLICK.value == "recommendation_click"
        assert InteractionType.FILTER_CHANGE.value == "filter_change"
        assert InteractionType.SESSION_START.value == "session_start"
        assert InteractionType.SESSION_END.value == "session_end"

    @pytest.mark.asyncio
    async def test_interaction_tracking_different_types(self, interaction_tracker):
        """Test tracking different types of interactions"""
        user_id = 'user_interaction_types'
        session_id = 'session_types_test'

        interactions_to_test = [
            {'type': InteractionType.VIEW, 'vehicle_ids': ['vehicle_1'], 'data': {'source': 'grid'}},
            {'type': InteractionType.SAVE, 'vehicle_ids': ['vehicle_1'], 'data': {'list': 'favorites'}},
            {'type': InteractionType.SEARCH, 'vehicle_ids': [], 'data': {'query': 'Toyota SUV'}},
            {'type': InteractionType.RECOMMENDATION_CLICK, 'vehicle_ids': ['vehicle_2'], 'data': {'source': 'recommendations'}},
            {'type': InteractionType.FILTER_CHANGE, 'vehicle_ids': [], 'data': {'filter': 'price_range'}},
        ]

        for i, interaction_config in enumerate(interactions_to_test):
            await interaction_tracker.track_interaction({
                'user_id': user_id,
                'session_id': session_id,
                'interaction_type': interaction_config['type'],
                'vehicle_ids': interaction_config['vehicle_ids'],
                'interaction_data': interaction_config['data'],
                'timestamp': datetime.now() + timedelta(seconds=i)
            })

        # Verify all interactions were tracked
        session = interaction_tracker.active_sessions[session_id]
        assert len(session.interactions) == len(interactions_to_test)

        # Verify specific tracking results
        assert 'vehicle_1' in session.viewed_vehicles
        assert 'vehicle_1' in session.saved_vehicles
        assert len(session.search_queries) == 1
        assert session.search_queries[0] == 'Toyota SUV'

        # Verify interaction data structure
        for i, interaction in enumerate(session.interactions):
            assert interaction['type'] == interactions_to_test[i]['type']
            assert interaction['vehicle_ids'] == interactions_to_test[i]['vehicle_ids']
            assert interaction['data'] == interactions_to_test[i]['data']

    @pytest.mark.asyncio
    async def test_error_handling_in_interaction_tracking(self, interaction_tracker):
        """Test error handling in interaction tracking"""
        # Test with malformed interaction data
        malformed_data = {
            'user_id': None,  # Invalid user_id
            'interaction_type': 'invalid_type',  # Invalid type
            'vehicle_ids': 'not_a_list',  # Invalid format
            'interaction_data': None,
            'timestamp': 'invalid_timestamp'
        }

        # Should not raise exception
        await interaction_tracker.track_interaction(malformed_data)

        # Should not create session
        assert len(interaction_tracker.active_sessions) == 0

    @pytest.mark.asyncio
    async def test_multiple_users_interactions(self, interaction_tracker, sample_interaction_data):
        """Test interactions from multiple users"""
        users = ['user_1', 'user_2', 'user_3']

        for user_id in users:
            await interaction_tracker.track_interaction({
                **sample_interaction_data,
                'user_id': user_id,
                'session_id': f'{user_id}_session',
                'vehicle_ids': [f'{user_id}_vehicle_1', f'{user_id}_vehicle_2']
            })

        # Verify sessions for all users
        assert len(interaction_tracker.active_sessions) == len(users)

        # Verify user sessions mapping
        for user_id in users:
            assert user_id in interaction_tracker.user_sessions
            assert len(interaction_tracker.user_sessions[user_id]) == 1

    @pytest.mark.asyncio
    async def test_session_activity_updates(self, interaction_tracker, sample_interaction_data):
        """Test session activity timestamp updates"""
        session_id = 'activity_test_session'
        user_id = 'activity_test_user'
        start_time = datetime.now()

        # Create initial session
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': start_time
        })

        session = interaction_tracker.active_sessions[session_id]
        initial_activity = session.last_activity
        assert initial_activity == start_time

        # Add another interaction later
        later_time = start_time + timedelta(minutes=5)
        await interaction_tracker.track_interaction({
            **sample_interaction_data,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': later_time,
            'interaction_type': InteractionType.SAVE
        })

        session = interaction_tracker.active_sessions[session_id]
        updated_activity = session.last_activity
        assert updated_activity == later_time
        assert updated_activity > initial_activity


class TestInteractionTrackerIntegration:
    """Integration tests for InteractionTracker"""

    @pytest.mark.asyncio
    async def test_complete_user_journey_tracking(self, interaction_tracker):
        """Test tracking a complete user journey"""
        user_id = 'journey_user'
        journey_interactions = [
            {
                'type': InteractionType.SESSION_START,
                'vehicle_ids': [],
                'data': {'source': 'direct_landing'},
                'timestamp_delta': 0
            },
            {
                'type': InteractionType.SEARCH,
                'vehicle_ids': [],
                'data': {'query': 'family SUV'},
                'timestamp_delta': 30
            },
            {
                'type': InteractionType.VIEW,
                'vehicle_ids': ['vehicle_1'],
                'data': {'source': 'search_results', 'duration': 45},
                'timestamp_delta': 60
            },
            {
                'type': InteractionType.VIEW,
                'vehicle_ids': ['vehicle_2'],
                'data': {'source': 'search_results', 'duration': 30},
                'timestamp_delta': 120
            },
            {
                'type': InteractionType.COMPARE,
                'vehicle_ids': ['vehicle_1', 'vehicle_2'],
                'data': {'comparison_id': 'comp_123'},
                'timestamp_delta': 180
            },
            {
                'type': InteractionType.SAVE,
                'vehicle_ids': ['vehicle_1'],
                'data': {'source': 'comparison_page'},
                'timestamp_delta': 240
            },
            {
                'type': InteractionType.RECOMMENDATION_CLICK,
                'vehicle_ids': ['vehicle_3'],
                'data': {'source': 'recommendations', 'position': 1},
                'timestamp_delta': 300
            },
            {
                'type': InteractionType.SESSION_END,
                'vehicle_ids': [],
                'data': {'duration': 360},
                'timestamp_delta': 360
            }
        ]

        base_time = datetime.now()
        session_id = None

        # Track complete journey
        for i, interaction_config in enumerate(journey_interactions):
            interaction_data = {
                'user_id': user_id,
                'interaction_type': interaction_config['type'],
                'vehicle_ids': interaction_config['vehicle_ids'],
                'interaction_data': interaction_config['data'],
                'context': {'step': i + 1}
            }

            # Set session ID after first interaction
            if i == 0:
                await interaction_tracker.track_interaction(interaction_data)
                session_id = list(interaction_tracker.active_sessions.keys())[0]
            else:
                interaction_data['session_id'] = session_id
                await interaction_tracker.track_interaction({
                    **interaction_data,
                    'timestamp': base_time + timedelta(seconds=interaction_config['timestamp_delta'])
                })

        # Verify journey was tracked completely
        assert session_id is not None
        session = interaction_tracker.active_sessions[session_id]
        assert len(session.interactions) == len(journey_interactions)

        # Verify specific journey milestones
        assert len(session.viewed_vehicles) == 3  # vehicle_1, vehicle_2, vehicle_3
        assert len(session.saved_vehicles) == 1  # vehicle_1
        assert len(session.search_queries) == 1  # "family SUV"
        assert len(session.comparisons) == 1  # [vehicle_1, vehicle_2]

        # Get user profile with journey data
        profile = await interaction_tracker.get_user_profile(user_id)
        assert profile.total_sessions >= 1
        assert profile.total_views >= 3
        assert profile.total_saves >= 1
        assert profile.total_searches >= 1
        assert profile.total_comparisons >= 1

    @pytest.mark.asyncio
    async def test_user_profile_evolution(self, interaction_tracker):
        """Test user profile evolution over multiple sessions"""
        user_id = 'evolution_user'
        sessions_data = [
            {
                'day_offset': 7,  # 7 days ago
                'interactions': [
                    {'type': InteractionType.SEARCH, 'query': 'Toyota Camry'},
                    {'type': InteractionType.VIEW, 'vehicles': ['vehicle_1', 'vehicle_2']},
                    {'type': InteractionType.SAVE, 'vehicles': ['vehicle_1']}
                ]
            },
            {
                'day_offset': 4,  # 4 days ago
                'interactions': [
                    {'type': InteractionType.SEARCH, 'query': 'Honda Accord'},
                    {'type': InteractionType.VIEW, 'vehicles': ['vehicle_3']},
                    {'type': InteractionType.SAVE, 'vehicles': ['vehicle_3']}
                ]
            },
            {
                'day_offset': 1,  # 1 day ago
                'interactions': [
                    {'type': InteractionType.SEARCH, 'query': 'sedan under 30000'},
                    {'type': InteractionType.VIEW, 'vehicles': ['vehicle_4', 'vehicle_5']},
                    {'type': InteractionType.COMPARE, 'vehicles': ['vehicle_4', 'vehicle_5']}
                ]
            }
        ]

        # Simulate sessions over time
        for session_config in sessions_data:
            session_time = datetime.now() - timedelta(days=session_config['day_offset'])
            session_id = f'{user_id}_session_{session_config["day_offset"]}'

            await interaction_tracker.track_interaction({
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': session_time,
                'interaction_type': InteractionType.SESSION_START,
                'vehicle_ids': [],
                'interaction_data': {},
                'context': {}
            })

            # Track interactions in this session
            for i, interaction_config in enumerate(session_config['interactions']):
                interaction_time = session_time + timedelta(minutes=i * 5)

                if interaction_config['type'] == InteractionType.SEARCH:
                    await interaction_tracker.track_interaction({
                        'user_id': user_id,
                        'session_id': session_id,
                        'timestamp': interaction_time,
                        'interaction_type': interaction_config['type'],
                        'vehicle_ids': [],
                        'interaction_data': {'query': interaction_config['query']},
                        'context': {}
                    })
                elif interaction_config['type'] in [InteractionType.VIEW, InteractionType.SAVE]:
                    await interaction_tracker.track_interaction({
                        'user_id': user_id,
                        'session_id': session_id,
                        'timestamp': interaction_time,
                        'interaction_type': interaction_config['type'],
                        'vehicle_ids': interaction_config['vehicles'],
                        'interaction_data': {},
                        'context': {}
                    })
                elif interaction_config['type'] == InteractionType.COMPARE:
                    await interaction_tracker.track_comparison(
                        user_id=user_id,
                        vehicle_ids=interaction_config['vehicles'],
                        comparison_id=f'comp_{session_config["day_offset"]}',
                        processing_time=1.0
                    )

        # Get final user profile
        profile = await interaction_tracker.get_user_profile(user_id)

        # Verify profile reflects user behavior evolution
        assert profile.total_sessions >= 3
        assert profile.total_views >= 5  # Multiple vehicle views
        assert profile.total_saves >= 2  # vehicle_1, vehicle_3
        assert profile.total_searches >= 3  # Multiple searches
        assert profile.total_comparisons >= 1

        # Verify interaction patterns were analyzed
        assert 'save_rate' in profile.interaction_patterns
        assert 'comparison_rate' in profile.interaction_patterns
        assert 'avg_interactions_per_session' in profile.interaction_patterns

    @pytest.mark.asyncio
    async def test_concurrent_user_interactions(self, interaction_tracker):
        """Test handling concurrent interactions from multiple users"""
        num_users = 10
        interactions_per_user = 5

        # Create concurrent tasks for multiple users
        async def track_user_interactions(user_index):
            user_id = f'concurrent_user_{user_index}'
            base_time = datetime.now()

            for i in range(interactions_per_user):
                await interaction_tracker.track_interaction({
                    'user_id': user_id,
                    'interaction_type': InteractionType.VIEW,
                    'vehicle_ids': [f'vehicle_{user_index}_{i}'],
                    'interaction_data': {'source': 'concurrent_test'},
                    'timestamp': base_time + timedelta(seconds=i),
                    'context': {'user_index': user_index, 'interaction_index': i}
                })

        # Run concurrent tracking
        tasks = [track_user_interactions(i) for i in range(num_users)]
        await asyncio.gather(*tasks)

        # Verify all interactions were tracked
        assert len(interaction_tracker.active_sessions) == num_users
        assert len(interaction_tracker.user_sessions) == num_users

        # Verify each user has their own session
        for i in range(num_users):
            user_id = f'concurrent_user_{i}'
            assert user_id in interaction_tracker.user_sessions
            assert len(interaction_tracker.user_sessions[user_id]) == 1

            session_id = interaction_tracker.user_sessions[user_id][0]
            session = interaction_tracker.active_sessions[session_id]
            assert len(session.interactions) == interactions_per_user
            assert session.user_id == user_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])