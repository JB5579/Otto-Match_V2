"""
User Profile Service for Otto.AI
Manages user profiles with preference learning and evolution tracking
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio

from src.conversation.nlu_service import UserPreference
from src.intelligence.preference_engine import PreferenceEvolution, PreferenceCategory

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ProfileVersion:
    """Represents a version of user profile"""
    version: int
    timestamp: datetime
    changes: List[str]
    preferences: Dict[str, Any]
    created_by: str  # "user", "system", "learning"


@dataclass
class PreferenceChange:
    """Tracks a change in user preference"""
    category: str
    old_value: Any
    new_value: Any
    confidence_change: float
    timestamp: datetime
    source: str
    reason: str


@dataclass
class UserProfile:
    """Complete user profile with preferences and history"""
    user_id: str
    created_at: datetime
    updated_at: datetime
    preferences: Dict[str, Any]
    preference_history: List[PreferenceChange]
    versions: List[ProfileVersion]
    current_version: int
    privacy_settings: Dict[str, bool]
    notification_settings: Dict[str, bool]


class ProfileService:
    """Service for managing user profiles with preference learning"""

    def __init__(self, database_client=None, cache_client=None):
        self.db = database_client
        self.cache = cache_client
        self.initialized = False

        # In-memory storage for development
        self.profiles: Dict[str, UserProfile] = {}

    async def initialize(self) -> bool:
        """Initialize the profile service"""
        try:
            self.initialized = True
            logger.info("Profile service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize profile service: {e}")
            return False

    async def update_profile_preferences(
        self,
        user_id: str,
        new_preferences: List[UserPreference],
        source: str = "conversation"
    ) -> bool:
        """Update user profile with new preferences"""
        if not self.initialized:
            return False

        try:
            # Get or create profile
            profile = await self._get_or_create_profile(user_id)

            # Track changes
            changes = []
            old_preferences = profile.preferences.copy()

            # Apply new preferences
            for pref in new_preferences:
                key = f"pref_{pref.category}"
                old_value = old_preferences.get(key)
                new_value = {
                    "value": pref.value,
                    "strength": pref.weight,
                    "confidence": pref.confidence,
                    "source": pref.source,
                    "updated_at": datetime.now().isoformat()
                }

                # Check if this is a significant change
                if old_value and self._is_significant_change(old_value, new_value):
                    changes.append(PreferenceChange(
                        category=pref.category,
                        old_value=old_value.get("value"),
                        new_value=pref.value,
                        confidence_change=new_value["confidence"] - old_value.get("confidence", 0.5),
                        timestamp=datetime.now(),
                        source=source,
                        reason=f"Preference updated via {source}"
                    ))

                profile.preferences[key] = new_value

            # Update profile if there are changes
            if changes:
                # Create new version
                new_version = ProfileVersion(
                    version=profile.current_version + 1,
                    timestamp=datetime.now(),
                    changes=[f"Updated {c.category} preference" for c in changes],
                    preferences=profile.preferences.copy(),
                    created_by="system"
                )

                profile.versions.append(new_version)
                profile.current_version = new_version.version
                profile.preference_history.extend(changes)
                profile.updated_at = datetime.now()

                # Save profile
                await self._save_profile(user_id, profile)

                # Send notification if enabled
                if profile.notification_settings.get("profile_changes", False):
                    await self._send_profile_change_notification(user_id, changes)

            logger.info(f"Updated profile for user {user_id} with {len(new_preferences)} preferences")
            return True

        except Exception as e:
            logger.error(f"Failed to update profile preferences: {e}")
            return False

    async def create_preference_timeline(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Create a timeline of preference changes"""
        if not self.initialized:
            return []

        try:
            profile = await self._get_profile(user_id)
            if not profile:
                return []

            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter changes within date range
            recent_changes = [
                c for c in profile.preference_history
                if c.timestamp >= cutoff_date
            ]

            # Group by category
            timeline = []
            for change in recent_changes:
                timeline.append({
                    "date": change.timestamp.isoformat(),
                    "category": change.category,
                    "change": f"{change.old_value} → {change.new_value}",
                    "confidence": {
                        "old": change.confidence_change,
                        "new": change.confidence_change + 1.0  # Adjust for display
                    },
                    "source": change.source,
                    "reason": change.reason
                })

            # Sort by date
            timeline.sort(key=lambda x: x["date"], reverse=True)

            return timeline

        except Exception as e:
            logger.error(f"Failed to create preference timeline: {e}")
            return []

    async def update_behavior_patterns(
        self,
        user_id: str,
        behavior_data: Dict[str, Any]
    ) -> bool:
        """Update user behavior patterns from interaction data"""
        if not self.initialized:
            return False

        try:
            profile = await self._get_or_create_profile(user_id)

            # Initialize behavior patterns if not exists
            if not hasattr(profile, 'behavior_patterns'):
                profile.behavior_patterns = {
                    "click_patterns": {},
                    "view_time_patterns": {},
                    "search_patterns": {},
                    "comparison_patterns": {},
                    "interaction_frequency": {},
                    "last_updated": datetime.now()
                }

            # Update click patterns
            if "clicked_vehicles" in behavior_data:
                for vehicle in behavior_data["clicked_vehicles"]:
                    profile.behavior_patterns["click_patterns"][vehicle] = \
                        profile.behavior_patterns["click_patterns"].get(vehicle, 0) + 1

            # Update view time patterns
            if "view_durations" in behavior_data:
                for vehicle, duration in behavior_data["view_durations"].items():
                    if vehicle not in profile.behavior_patterns["view_time_patterns"]:
                        profile.behavior_patterns["view_time_patterns"][vehicle] = []
                    profile.behavior_patterns["view_time_patterns"][vehicle].append(duration)

            # Update search patterns
            if "search_terms" in behavior_data:
                for term in behavior_data["search_terms"]:
                    profile.behavior_patterns["search_patterns"][term] = \
                        profile.behavior_patterns["search_patterns"].get(term, 0) + 1

            # Update interaction frequency
            if "interaction_type" in behavior_data:
                interaction_type = behavior_data["interaction_type"]
                current_date = datetime.now().date().isoformat()

                if current_date not in profile.behavior_patterns["interaction_frequency"]:
                    profile.behavior_patterns["interaction_frequency"][current_date] = {}

                profile.behavior_patterns["interaction_frequency"][current_date][interaction_type] = \
                    profile.behavior_patterns["interaction_frequency"][current_date].get(interaction_type, 0) + 1

            # Update timestamp
            profile.behavior_patterns["last_updated"] = datetime.now()

            # Analyze patterns to infer implicit preferences
            await self._analyze_behavior_patterns(user_id, profile)

            # Save profile
            await self._save_profile(user_id, profile)
            return True

        except Exception as e:
            logger.error(f"Failed to update behavior patterns: {e}")
            return False

    async def _analyze_behavior_patterns(
        self,
        user_id: str,
        profile
    ) -> None:
        """Analyze behavior patterns to infer implicit preferences"""
        try:
            patterns = profile.behavior_patterns
            implicit_preferences = []

            # Analyze click patterns for brand preferences
            brand_clicks = {}
            for vehicle, clicks in patterns["click_patterns"].items():
                # Extract brand from vehicle name (simplified)
                if "Toyota" in vehicle:
                    brand_clicks["Toyota"] = brand_clicks.get("Toyota", 0) + clicks
                elif "Honda" in vehicle:
                    brand_clicks["Honda"] = brand_clicks.get("Honda", 0) + clicks
                elif "Ford" in vehicle:
                    brand_clicks["Ford"] = brand_clicks.get("Ford", 0) + clicks
                elif "Chevrolet" in vehicle or "Chevy" in vehicle:
                    brand_clicks["Chevrolet"] = brand_clicks.get("Chevrolet", 0) + clicks

            if brand_clicks:
                # Find most clicked brand
                top_brand = max(brand_clicks, key=brand_clicks.get)
                confidence = min(0.7, brand_clicks[top_brand] / 10)  # Normalize confidence

                if confidence > 0.3:  # Only add if significant pattern
                    implicit_preferences.append({
                        "category": "brand",
                        "value": top_brand,
                        "weight": confidence,
                        "source": "behavioral",
                        "confidence": confidence,
                        "evidence": f"Clicked {brand_clicks[top_brand]} times"
                    })

            # Analyze view time for feature preferences
            if patterns["view_time_patterns"]:
                # Calculate average view time per vehicle
                avg_times = {}
                for vehicle, times in patterns["view_time_patterns"].items():
                    if times:
                        avg_times[vehicle] = sum(times) / len(times)

                # Longer view times suggest higher interest
                if avg_times:
                    highest_avg = max(avg_times.values())
                    for vehicle, avg_time in avg_times.items():
                        if avg_time > highest_avg * 0.8:  # Top 20% of view times
                            # Infer feature preferences based on vehicle type
                            if "SUV" in vehicle or "Crossover" in vehicle:
                                implicit_preferences.append({
                                    "category": "vehicle_type",
                                    "value": "SUV",
                                    "weight": 0.6,
                                    "source": "behavioral",
                                    "confidence": 0.5,
                                    "evidence": f"Long view time on {vehicle}"
                                })

            # Analyze search patterns
            if patterns["search_patterns"]:
                search_terms = list(patterns["search_patterns"].keys())

                # Look for safety-related searches
                safety_terms = ["safety", "rating", "crash", "iihs", "nhtsa"]
                safety_searches = [term for term in search_terms
                                 if any(s_term in term.lower() for s_term in safety_terms)]

                if safety_searches:
                    implicit_preferences.append({
                        "category": "safety_priority",
                        "value": "high",
                        "weight": 0.7,
                        "source": "behavioral",
                        "confidence": 0.6,
                        "evidence": f"Safety-related searches: {safety_searches}"
                    })

            # Update profile with inferred preferences
            if implicit_preferences:
                from src.conversation.nlu_service import UserPreference
                user_prefs = []

                for pref_data in implicit_preferences:
                    user_pref = UserPreference(
                        category=pref_data["category"],
                        value=pref_data["value"],
                        weight=pref_data["weight"],
                        source=pref_data["source"],
                        confidence=pref_data["confidence"]
                    )
                    user_prefs.append(user_pref)

                await self.update_profile_preferences(
                    user_id,
                    user_prefs,
                    source="behavior_analysis"
                )

        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {e}")

    async def get_behavior_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get insights about user behavior patterns"""
        if not self.initialized:
            return {}

        try:
            profile = await self._get_profile(user_id)
            if not profile or not hasattr(profile, 'behavior_patterns'):
                return {}

            patterns = profile.behavior_patterns
            insights = {
                "most_viewed_brand": None,
                "preferred_features": [],
                "activity_level": "low",
                "engagement_score": 0,
                "pattern_summary": {}
            }

            # Find most viewed brand
            brand_counts = {}
            for vehicle in patterns["click_patterns"]:
                if "Toyota" in vehicle:
                    brand_counts["Toyota"] = brand_counts.get("Toyota", 0) + 1
                elif "Honda" in vehicle:
                    brand_counts["Honda"] = brand_counts.get("Honda", 0) + 1
                elif "Ford" in vehicle:
                    brand_counts["Ford"] = brand_counts.get("Ford", 0) + 1

            if brand_counts:
                insights["most_viewed_brand"] = max(brand_counts, key=brand_counts.get)

            # Calculate activity level
            total_interactions = sum(
                daily.get("total", 0)
                for daily in patterns["interaction_frequency"].values()
                for daily in [daily] if isinstance(daily, dict)
            )

            if total_interactions > 50:
                insights["activity_level"] = "high"
            elif total_interactions > 20:
                insights["activity_level"] = "medium"

            # Calculate engagement score (0-100)
            engagement_factors = {
                "click_diversity": len(set(patterns["click_patterns"].keys())),
                "search_diversity": len(set(patterns["search_patterns"].keys())),
                "interaction_consistency": len(patterns["interaction_frequency"]),
                "total_interactions": total_interactions
            }

            # Normalize and weight factors
            engagement_score = (
                min(100, engagement_factors["click_diversity"] * 5) * 0.3 +
                min(100, engagement_factors["search_diversity"] * 10) * 0.2 +
                min(100, engagement_factors["interaction_consistency"] * 2) * 0.3 +
                min(100, engagement_factors["total_interactions"]) * 0.2
            )
            insights["engagement_score"] = round(engagement_score, 1)

            return insights

        except Exception as e:
            logger.error(f"Failed to get behavior insights: {e}")
            return {}

    async def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user profile"""
        if not self.initialized:
            return {}

        try:
            profile = await self._get_profile(user_id)
            if not profile:
                return {}

            # Extract key preferences
            key_preferences = {}
            for key, value in profile.preferences.items():
                if key.startswith("pref_"):
                    category = key[5:]  # Remove "pref_" prefix
                    if value.get("confidence", 0) > 0.5:  # Only include confident preferences
                        key_preferences[category] = {
                            "value": value.get("value"),
                            "confidence": value.get("confidence"),
                            "strength": value.get("strength")
                        }

            # Calculate profile completeness
            expected_categories = [
                "budget", "vehicle_type", "brand", "feature",
                "family_size", "lifestyle", "commute"
            ]
            completeness = len(key_preferences) / len(expected_categories) * 100

            # Get recent activity
            recent_changes = len([
                c for c in profile.preference_history
                if c.timestamp >= datetime.now() - timedelta(days=7)
            ])

            return {
                "user_id": user_id,
                "created_at": profile.created_at.isoformat(),
                "last_updated": profile.updated_at.isoformat(),
                "version": profile.current_version,
                "completeness": round(completeness, 1),
                "key_preferences": key_preferences,
                "recent_changes": recent_changes,
                "total_changes": len(profile.preference_history),
                "privacy_enabled": profile.privacy_settings.get("data_collection", True)
            }

        except Exception as e:
            logger.error(f"Failed to get profile summary: {e}")
            return {}

    async def rollback_profile(
        self,
        user_id: str,
        target_version: int
    ) -> bool:
        """Rollback profile to a previous version"""
        if not self.initialized:
            return False

        try:
            profile = await self._get_profile(user_id)
            if not profile:
                return False

            # Find target version
            target = None
            for version in profile.versions:
                if version.version == target_version:
                    target = version
                    break

            if not target:
                logger.error(f"Version {target_version} not found for user {user_id}")
                return False

            # Create rollback version
            rollback_version = ProfileVersion(
                version=profile.current_version + 1,
                timestamp=datetime.now(),
                changes=[f"Rollback to version {target_version}"],
                preferences=target.preferences.copy(),
                created_by="user"
            )

            # Apply rollback
            profile.preferences = target.preferences.copy()
            profile.versions.append(rollback_version)
            profile.current_version = rollback_version.version
            profile.updated_at = datetime.now()

            # Save profile
            await self._save_profile(user_id, profile)

            logger.info(f"Rolled back profile for user {user_id} to version {target_version}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback profile: {e}")
            return False

    async def sync_profile_across_sessions(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """Synchronize profile data across multiple sessions"""
        if not self.initialized:
            return False

        try:
            profile = await self._get_or_create_profile(user_id)

            # Update session metadata
            if "sessions" not in profile.preferences:
                profile.preferences["sessions"] = {}

            session_id = session_data.get("session_id", "unknown")
            profile.preferences["sessions"][session_id] = {
                "last_active": datetime.now().isoformat(),
                "device": session_data.get("device", "unknown"),
                "location": session_data.get("location", None)
            }

            # Clean up old sessions (older than 30 days)
            cutoff = datetime.now() - timedelta(days=30)
            active_sessions = {
                sid: data for sid, data in profile.preferences["sessions"].items()
                if datetime.fromisoformat(data["last_active"]) >= cutoff
            }
            profile.preferences["sessions"] = active_sessions

            # Save profile
            profile.updated_at = datetime.now()
            await self._save_profile(user_id, profile)

            return True

        except Exception as e:
            logger.error(f"Failed to sync profile across sessions: {e}")
            return False

    async def get_profile_with_privacy(
        self,
        user_id: str,
        requester: str = "self"
    ) -> Optional[Dict[str, Any]]:
        """Get profile with privacy controls applied"""
        if not self.initialized:
            return None

        try:
            profile = await self._get_profile(user_id)
            if not profile:
                return None

            # Check privacy settings
            if requester != "self":
                # Apply privacy filters for non-self requests
                privacy_filtered = {
                    "user_id": profile.user_id,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                    "version": profile.current_version
                }

                # Only include public preferences
                if profile.privacy_settings.get("public_profile", False):
                    privacy_filtered["public_preferences"] = {
                        k: v for k, v in profile.preferences.items()
                        if k.startswith("pref_") and v.get("public", False)
                    }

                return privacy_filtered

            # Return full profile for self
            return asdict(profile)

        except Exception as e:
            logger.error(f"Failed to get profile with privacy: {e}")
            return None

    async def _get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one"""
        profile = await self._get_profile(user_id)
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                preferences={},
                preference_history=[],
                versions=[],
                current_version=0,
                privacy_settings={
                    "data_collection": True,
                    "public_profile": False,
                    "share_analytics": True,
                    "memory_retention": True
                },
                notification_settings={
                    "profile_changes": False,
                    "new_recommendations": True,
                    "price_alerts": True
                }
            )
            await self._save_profile(user_id, profile)

        return profile

    async def _get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from storage"""
        # Check cache first
        if self.cache:
            cached = await self.cache.get(f"profile:{user_id}")
            if cached:
                return UserProfile(**cached)

        # Check in-memory storage
        if user_id in self.profiles:
            return self.profiles[user_id]

        # Check database
        if self.db:
            try:
                result = await self.db.table("user_profiles").select(
                    "*"
                ).eq("user_id", user_id).single().execute()

                if result.data:
                    profile_data = result.data
                    # Convert to UserProfile object
                    profile = UserProfile(
                        user_id=profile_data["user_id"],
                        created_at=datetime.fromisoformat(profile_data["created_at"]),
                        updated_at=datetime.fromisoformat(profile_data["updated_at"]),
                        preferences=profile_data.get("preferences", {}),
                        preference_history=[
                            PreferenceChange(**c) for c in profile_data.get("preference_history", [])
                        ],
                        versions=[
                            ProfileVersion(**v) for v in profile_data.get("versions", [])
                        ],
                        current_version=profile_data.get("current_version", 0),
                        privacy_settings=profile_data.get("privacy_settings", {}),
                        notification_settings=profile_data.get("notification_settings", {})
                    )
                    self.profiles[user_id] = profile
                    return profile
            except Exception as e:
                logger.error(f"Failed to get profile from database: {e}")

        return None

    async def _save_profile(self, user_id: str, profile: UserProfile):
        """Save user profile to storage"""
        # Update in-memory storage
        self.profiles[user_id] = profile

        # Update cache
        if self.cache:
            await self.cache.set(
                f"profile:{user_id}",
                asdict(profile),
                ttl=3600  # 1 hour
            )

        # Update database
        if self.db:
            try:
                await self.db.table("user_profiles").upsert({
                    "user_id": profile.user_id,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                    "preferences": profile.preferences,
                    "preference_history": [asdict(c) for c in profile.preference_history],
                    "versions": [asdict(v) for v in profile.versions],
                    "current_version": profile.current_version,
                    "privacy_settings": profile.privacy_settings,
                    "notification_settings": profile.notification_settings
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save profile to database: {e}")

    def _is_significant_change(
        self,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any]
    ) -> bool:
        """Check if preference change is significant"""
        # Check value change
        if old_value.get("value") != new_value.get("value"):
            return True

        # Check confidence change (> 20%)
        old_conf = old_value.get("confidence", 0.5)
        new_conf = new_value.get("confidence", 0.5)
        if abs(new_conf - old_conf) > 0.2:
            return True

        # Check strength change (> 30%)
        old_strength = old_value.get("strength", 0.5)
        new_strength = new_value.get("strength", 0.5)
        if abs(new_strength - old_strength) > 0.3:
            return True

        return False

    async def _send_profile_change_notification(
        self,
        user_id: str,
        changes: List[PreferenceChange]
    ) -> None:
        """Send notification about profile changes"""
        # This would integrate with notification service
        # For now, just log
        logger.info(f"Profile change notification for {user_id}: {len(changes)} changes")
        for change in changes:
            logger.info(f"  - {change.category}: {change.old_value} → {change.new_value}")