"""
Otto.AI User Interaction Tracker

Tracks user interactions with vehicles for personalization and analytics.
Part of Story 1-5: Build Vehicle Comparison and Recommendation Engine
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class InteractionType(str, Enum):
    """Types of user interactions"""
    VIEW = "view"
    SAVE = "save"
    COMPARE = "compare"
    SEARCH = "search"
    RECOMMENDATION_CLICK = "recommendation_click"
    FILTER_CHANGE = "filter_change"
    SESSION_START = "session_start"
    SESSION_END = "session_end"

@dataclass
class UserSession:
    """User session tracking"""
    user_id: str
    session_id: str
    start_time: datetime
    last_activity: datetime
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    viewed_vehicles: Set[str] = field(default_factory=set)
    saved_vehicles: Set[str] = field(default_factory=set)
    search_queries: List[str] = field(default_factory=list)
    comparisons: List[List[str]] = field(default_factory=list)

@dataclass
class UserBehaviorProfile:
    """Aggregated user behavior profile"""
    user_id: str
    total_sessions: int = 0
    total_views: int = 0
    total_saves: int = 0
    total_comparisons: int = 0
    total_searches: int = 0
    avg_session_duration: float = 0.0
    preferred_brands: Dict[str, int] = field(default_factory=dict)
    preferred_vehicle_types: Dict[str, int] = field(default_factory=dict)
    price_range_preference: Dict[str, float] = field(default_factory=dict)
    feature_preferences: Dict[str, float] = field(default_factory=dict)
    interaction_patterns: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

class InteractionTracker:
    """Service for tracking and analyzing user interactions"""

    def __init__(self):
        """Initialize interaction tracker"""
        # Active user sessions
        self.active_sessions: Dict[str, UserSession] = {}  # session_id -> UserSession
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]

        # Aggregated user profiles
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}

        # Configuration
        self.session_timeout = timedelta(minutes=30)
        self.profile_update_interval = timedelta(minutes=5)

        # Background tasks
        self.cleanup_task = None

    async def track_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """
        Track a user interaction

        Args:
            interaction_data: Dictionary containing interaction information
                - user_id: User identifier
                - session_id: Session identifier (optional)
                - interaction_type: Type of interaction
                - vehicle_ids: List of vehicle IDs (if applicable)
                - interaction_data: Additional interaction data
                - timestamp: Interaction timestamp (optional)
        """
        try:
            user_id = interaction_data.get('user_id')
            if not user_id:
                logger.warning("Interaction data missing user_id")
                return

            interaction_type = interaction_data.get('interaction_type')
            timestamp = interaction_data.get('timestamp', datetime.now())
            session_id = interaction_data.get('session_id')

            # Get or create session
            if not session_id:
                session_id = await self._get_or_create_session(user_id)

            session = await self._get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return

            # Update session activity
            session.last_activity = timestamp

            # Create interaction record
            interaction_record = {
                'type': interaction_type,
                'timestamp': timestamp,
                'vehicle_ids': interaction_data.get('vehicle_ids', []),
                'data': interaction_data.get('interaction_data', {}),
                'context': interaction_data.get('context', {})
            }

            session.interactions.append(interaction_record)

            # Process specific interaction types
            await self._process_interaction(session, interaction_record)

            logger.debug(f"Tracked {interaction_type} interaction for user {user_id}")

        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")

    async def track_comparison(
        self,
        user_id: str,
        vehicle_ids: List[str],
        comparison_id: str,
        processing_time: float
    ) -> None:
        """
        Track vehicle comparison interaction

        Args:
            user_id: User identifier
            vehicle_ids: Vehicle IDs being compared
            comparison_id: Unique comparison identifier
            processing_time: Comparison processing time
        """
        try:
            session_id = await self._get_or_create_session(user_id)
            session = await self._get_session(session_id)

            if session:
                # Track comparison
                session.comparisons.append(vehicle_ids.copy())

                interaction_record = {
                    'type': InteractionType.COMPARE,
                    'timestamp': datetime.now(),
                    'vehicle_ids': vehicle_ids.copy(),
                    'data': {
                        'comparison_id': comparison_id,
                        'processing_time': processing_time,
                        'vehicle_count': len(vehicle_ids)
                    },
                    'context': {}
                }

                session.interactions.append(interaction_record)
                await self._process_interaction(session, interaction_record)

                logger.info(f"Tracked comparison for user {user_id}: {len(vehicle_ids)} vehicles")

        except Exception as e:
            logger.error(f"Error tracking comparison: {str(e)}")

    async def get_user_profile(self, user_id: str) -> UserBehaviorProfile:
        """Get or create user behavior profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id=user_id)
            await self._update_user_profile(user_id)
        else:
            # Check if profile needs updating
            profile = self.user_profiles[user_id]
            if datetime.now() - profile.last_updated > self.profile_update_interval:
                await self._update_user_profile(user_id)

        return self.user_profiles[user_id]

    async def _get_or_create_session(self, user_id: str) -> str:
        """Get existing session or create new one"""
        # Find active session for user
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                session = self.active_sessions.get(session_id)
                if session and (datetime.now() - session.last_activity) < self.session_timeout:
                    return session_id

        # Create new session
        session_id = f"session_{user_id}_{int(time.time() * 1000)}"
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now(),
            last_activity=datetime.now()
        )

        self.active_sessions[session_id] = session

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)

        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id

    async def _get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self.active_sessions.get(session_id)
        if session:
            # Check if session has expired
            if datetime.now() - session.last_activity > self.session_timeout:
                await self._end_session(session_id)
                return None
        return session

    async def _process_interaction(self, session: UserSession, interaction: Dict[str, Any]) -> None:
        """Process specific interaction types"""
        interaction_type = interaction.get('type')
        vehicle_ids = interaction.get('vehicle_ids', [])

        if interaction_type == InteractionType.VIEW:
            for vehicle_id in vehicle_ids:
                session.viewed_vehicles.add(vehicle_id)

        elif interaction_type == InteractionType.SAVE:
            for vehicle_id in vehicle_ids:
                session.saved_vehicles.add(vehicle_id)

        elif interaction_type == InteractionType.SEARCH:
            search_query = interaction.get('data', {}).get('query', '')
            if search_query:
                session.search_queries.append(search_query)

        elif interaction_type == InteractionType.COMPARE:
            if vehicle_ids:
                session.comparisons.append(vehicle_ids.copy())

    async def _update_user_profile(self, user_id: str) -> None:
        """Update user behavior profile from session data"""
        try:
            if user_id not in self.user_sessions:
                return

            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = UserBehaviorProfile(user_id=user_id)
                self.user_profiles[user_id] = profile

            # Aggregate data from all user sessions
            all_sessions = []
            for session_id in self.user_sessions[user_id]:
                session = self.active_sessions.get(session_id)
                if session:
                    all_sessions.append(session)

            if not all_sessions:
                return

            # Update basic metrics
            profile.total_sessions = len(all_sessions)
            profile.total_views = sum(len(session.viewed_vehicles) for session in all_sessions)
            profile.total_saves = sum(len(session.saved_vehicles) for session in all_sessions)
            profile.total_comparisons = sum(len(session.comparisons) for session in all_sessions)
            profile.total_searches = sum(len(session.search_queries) for session in all_sessions)

            # Calculate average session duration
            total_duration = sum(
                (session.last_activity - session.start_time).total_seconds()
                for session in all_sessions
            )
            profile.avg_session_duration = total_duration / len(all_sessions) if all_sessions else 0

            # Aggregate vehicle data for preferences
            await self._analyze_vehicle_preferences(user_id, all_sessions, profile)

            # Analyze interaction patterns
            await self._analyze_interaction_patterns(all_sessions, profile)

            profile.last_updated = datetime.now()
            logger.debug(f"Updated profile for user {user_id}")

        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {str(e)}")

    async def _analyze_vehicle_preferences(
        self,
        user_id: str,
        sessions: List[UserSession],
        profile: UserBehaviorProfile
    ) -> None:
        """Analyze vehicle preferences from session data"""
        try:
            # This would integrate with vehicle database service
            # For now, create mock preference analysis
            all_viewed_vehicles = set()
            for session in sessions:
                all_viewed_vehicles.update(session.viewed_vehicles)

            # Mock brand preferences (would be calculated from actual vehicle data)
            profile.preferred_brands = {
                'Toyota': 5,
                'Honda': 3,
                'Ford': 2,
                'BMW': 4
            }

            # Mock vehicle type preferences
            profile.preferred_vehicle_types = {
                'SUV': 6,
                'Sedan': 4,
                'Truck': 2
            }

            # Mock price range preference
            profile.price_range_preference = {
                'min': 25000.0,
                'max': 45000.0,
                'preferred_midpoint': 35000.0
            }

            # Mock feature preferences
            profile.feature_preferences = {
                'safety_features': 0.9,
                'technology_features': 0.7,
                'comfort_features': 0.6,
                'performance_features': 0.5
            }

        except Exception as e:
            logger.error(f"Error analyzing vehicle preferences: {str(e)}")

    async def _analyze_interaction_patterns(
        self,
        sessions: List[UserSession],
        profile: UserBehaviorProfile
    ) -> None:
        """Analyze user interaction patterns"""
        try:
            # Calculate interaction ratios
            if profile.total_views > 0:
                profile.interaction_patterns['save_rate'] = profile.total_saves / profile.total_views
            else:
                profile.interaction_patterns['save_rate'] = 0.0

            if profile.total_views > 0:
                profile.interaction_patterns['comparison_rate'] = profile.total_comparisons / profile.total_views
            else:
                profile.interaction_patterns['comparison_rate'] = 0.0

            # Session engagement metrics
            profile.interaction_patterns['avg_interactions_per_session'] = (
                sum(len(session.interactions) for session in sessions) / len(sessions) if sessions else 0
            )

            # Time-based patterns
            profile.interaction_patterns['most_active_hour'] = 14  # Mock data (2 PM)
            profile.interaction_patterns['most_active_day'] = 'Saturday'  # Mock data

            # Search behavior
            all_searches = []
            for session in sessions:
                all_searches.extend(session.search_queries)

            if all_searches:
                profile.interaction_patterns['avg_search_length'] = sum(len(s.split()) for s in all_searches) / len(all_searches)
                profile.interaction_patterns['unique_search_terms'] = len(set(' '.join(all_searches).split()))
            else:
                profile.interaction_patterns['avg_search_length'] = 0
                profile.interaction_patterns['unique_search_terms'] = 0

        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {str(e)}")

    async def _end_session(self, session_id: str) -> None:
        """End a user session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            user_id = session.user_id

            # Update user profile with session data
            await self._update_user_profile(user_id)

            # Remove from active sessions
            del self.active_sessions[session_id]

            logger.info(f"Ended session {session_id} for user {user_id}")

    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user session history"""
        sessions_data = []

        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id][-limit:]:
                session = self.active_sessions.get(session_id)
                if session:
                    sessions_data.append({
                        'session_id': session_id,
                        'start_time': session.start_time.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'duration_seconds': (session.last_activity - session.start_time).total_seconds(),
                        'interaction_count': len(session.interactions),
                        'viewed_vehicles': list(session.viewed_vehicles),
                        'saved_vehicles': list(session.saved_vehicles),
                        'search_count': len(session.search_queries),
                        'comparison_count': len(session.comparisons)
                    })

        return sessions_data

    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self._end_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def start_background_tasks(self) -> None:
        """Start background cleanup tasks"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._background_cleanup())

    async def _background_cleanup(self) -> None:
        """Background task for periodic cleanup"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in background cleanup: {str(e)}")

    async def stop_background_tasks(self) -> None:
        """Stop background tasks"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None

    async def get_interaction_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get interaction statistics for a user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            stats = {
                'total_interactions': 0,
                'interaction_types': {},
                'daily_activity': {},
                'vehicle_engagement': {
                    'unique_vehicles_viewed': set(),
                    'total_vehicles_saved': set(),
                    'total_comparisons': 0
                }
            }

            if user_id not in self.user_sessions:
                return stats

            # Aggregate data from sessions
            for session_id in self.user_sessions[user_id]:
                session = self.active_sessions.get(session_id)
                if session and session.start_time >= cutoff_date:
                    for interaction in session.interactions:
                        interaction_type = interaction.get('type', 'unknown')
                        stats['total_interactions'] += 1
                        stats['interaction_types'][interaction_type] = stats['interaction_types'].get(interaction_type, 0) + 1

                        # Track vehicle engagement
                        if interaction_type == InteractionType.VIEW:
                            stats['vehicle_engagement']['unique_vehicles_viewed'].update(interaction.get('vehicle_ids', []))
                        elif interaction_type == InteractionType.SAVE:
                            stats['vehicle_engagement']['total_vehicles_saved'].update(interaction.get('vehicle_ids', []))
                        elif interaction_type == InteractionType.COMPARE:
                            stats['vehicle_engagement']['total_comparisons'] += 1

                        # Daily activity
                        date_key = interaction.get('timestamp', datetime.now()).date().isoformat()
                        stats['daily_activity'][date_key] = stats['daily_activity'].get(date_key, 0) + 1

            # Convert sets to counts
            stats['vehicle_engagement']['unique_vehicles_viewed'] = len(stats['vehicle_engagement']['unique_vehicles_viewed'])
            stats['vehicle_engagement']['total_vehicles_saved'] = len(stats['vehicle_engagement']['total_vehicles_saved'])

            return stats

        except Exception as e:
            logger.error(f"Error getting interaction stats for {user_id}: {str(e)}")
            return {}