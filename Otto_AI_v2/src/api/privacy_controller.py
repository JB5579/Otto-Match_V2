"""
Privacy Controller for Otto.AI
Provides endpoints for users to manage their memory and preferences
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.services.profile_service import ProfileService
from src.memory.temporal_memory import TemporalMemoryManager
from src.memory.zep_client import ZepClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/privacy", tags=["privacy"])


# Request/Response models
class PrivacySettingsRequest(BaseModel):
    data_collection: bool = Field(default=True, description="Allow data collection for personalization")
    public_profile: bool = Field(default=False, description="Make profile visible to others")
    share_analytics: bool = Field(default=True, description="Share anonymous analytics")
    memory_retention: bool = Field(default=True, description="Retain conversation memory")


class PreferenceUpdateRequest(BaseModel):
    category: str = Field(..., description="Preference category")
    value: Any = Field(..., description="New preference value")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in preference")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Strength of preference")


class ForgetRequest(BaseModel):
    category: Optional[str] = Field(None, description="Specific category to forget")
    timeframe_days: Optional[int] = Field(None, description="Forget data older than X days")
    all_data: bool = Field(default=False, description="Forget all personal data")


class DataExportRequest(BaseModel):
    format: str = Field(default="json", regex="^(json|csv)$", description="Export format")
    include_conversations: bool = Field(default=True, description="Include conversation history")
    include_preferences: bool = Field(default=True, description="Include learned preferences")
    include_analytics: bool = Field(default=False, description="Include analytics data")


# Dependency injection
async def get_profile_service() -> ProfileService:
    """Get profile service instance"""
    # In production, this would be properly injected
    return ProfileService()


async def get_memory_manager() -> TemporalMemoryManager:
    """Get memory manager instance"""
    # In production, this would be properly injected
    from src.memory.zep_client import ZepClient
    zep_client = ZepClient()
    await zep_client.initialize()
    return TemporalMemoryManager(zep_client)


@router.get("/profile/{user_id}")
async def get_privacy_profile(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Get user's privacy profile"""
    try:
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Extract privacy-relevant information
        privacy_profile = {
            "user_id": profile["user_id"],
            "privacy_settings": profile.get("privacy_settings", {}),
            "data_retention": {
                "created_at": profile["created_at"],
                "last_updated": profile["updated_at"],
                "total_preferences": len(profile.get("preferences", {})),
                "preference_history": len(profile.get("preference_history", []))
            },
            "data_categories": {
                "conversations": bool(profile.get("privacy_settings", {}).get("memory_retention", True)),
                "preferences": bool(profile.get("privacy_settings", {}).get("data_collection", True)),
                "analytics": bool(profile.get("privacy_settings", {}).get("share_analytics", True))
            }
        }

        return privacy_profile

    except Exception as e:
        logger.error(f"Failed to get privacy profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/preferences/{user_id}")
async def get_learned_preferences(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Get all learned preferences for a user"""
    try:
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Extract and format preferences
        preferences = {}
        for key, value in profile.get("preferences", {}).items():
            if key.startswith("pref_"):
                category = key[5:]  # Remove "pref_" prefix
                preferences[category] = {
                    "value": value.get("value"),
                    "confidence": round(value.get("confidence", 0) * 100, 1),
                    "strength": round(value.get("strength", 0) * 100, 1),
                    "source": value.get("source", "unknown"),
                    "last_updated": value.get("updated_at")
                }

        return {
            "user_id": user_id,
            "preferences": preferences,
            "total_count": len(preferences),
            "last_updated": profile.get("updated_at")
        }

    except Exception as e:
        logger.error(f"Failed to get learned preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/preferences/{user_id}")
async def update_preference(
    user_id: str,
    request: PreferenceUpdateRequest,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Update or correct a learned preference"""
    try:
        from src.conversation.nlu_service import UserPreference

        # Create UserPreference object
        pref = UserPreference(
            category=request.category,
            value=request.value,
            weight=request.strength,
            source="corrected",
            confidence=request.confidence
        )

        # Update profile
        success = await profile_service.update_profile_preferences(
            user_id,
            [pref],
            source="user_correction"
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update preference")

        return {
            "message": "Preference updated successfully",
            "category": request.category,
            "new_value": request.value,
            "confidence": request.confidence
        }

    except Exception as e:
        logger.error(f"Failed to update preference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/timeline/{user_id}")
async def get_preference_evolution(
    user_id: str,
    days: int = 30,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Get timeline of how preferences have evolved"""
    try:
        timeline = await profile_service.create_preference_timeline(user_id, days)

        # Group changes by category
        by_category = {}
        for change in timeline:
            category = change["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(change)

        return {
            "user_id": user_id,
            "timeframe_days": days,
            "total_changes": len(timeline),
            "changes_by_category": by_category,
            "timeline": timeline
        }

    except Exception as e:
        logger.error(f"Failed to get preference evolution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/forget/{user_id}")
async def forget_data(
    user_id: str,
    request: ForgetRequest,
    background_tasks: BackgroundTasks,
    profile_service: ProfileService = Depends(get_profile_service),
    memory_manager: TemporalMemoryManager = Depends(get_memory_manager)
):
    """Request forgetting of specific or all data"""
    try:
        if request.all_data:
            # Queue complete data deletion
            background_tasks.add_task(
                _delete_all_user_data,
                user_id,
                profile_service,
                memory_manager
            )
            return {
                "message": "Data deletion request queued",
                "user_id": user_id,
                "deletion_type": "all_data"
            }

        else:
            # Partial data deletion
            deleted_items = []

            # Delete specific category
            if request.category:
                success = await _delete_preference_category(
                    user_id,
                    request.category,
                    profile_service
                )
                if success:
                    deleted_items.append(f"Preferences in category: {request.category}")

            # Delete old data
            if request.timeframe_days:
                cutoff_date = datetime.now() - timedelta(days=request.timeframe_days)
                success = await _delete_old_data(
                    user_id,
                    cutoff_date,
                    profile_service,
                    memory_manager
                )
                if success:
                    deleted_items.append(f"Data older than {request.timeframe_days} days")

            return {
                "message": "Selective data deletion completed",
                "user_id": user_id,
                "deleted_items": deleted_items
            }

    except Exception as e:
        logger.error(f"Failed to process forget request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/export/{user_id}")
async def export_user_data(
    user_id: str,
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    profile_service: ProfileService = Depends(get_profile_service),
    memory_manager: TemporalMemoryManager = Depends(get_memory_manager)
):
    """Export user's data in requested format"""
    try:
        # Generate export ID
        export_id = f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Queue export task
        background_tasks.add_task(
            _generate_user_export,
            export_id,
            user_id,
            request.dict(),
            profile_service,
            memory_manager
        )

        return {
            "message": "Export request queued",
            "export_id": export_id,
            "user_id": user_id,
            "format": request.format,
            "estimated_completion": "5 minutes"
        }

    except Exception as e:
        logger.error(f"Failed to queue export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export/{export_id}/status")
async def get_export_status(export_id: str):
    """Get status of data export"""
    # This would check export status from storage
    # For now, return placeholder
    return {
        "export_id": export_id,
        "status": "processing",
        "progress": 50,
        "estimated_completion": datetime.now().isoformat(),
        "download_url": None
    }


@router.put("/settings/{user_id}")
async def update_privacy_settings(
    user_id: str,
    request: PrivacySettingsRequest,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Update user's privacy settings"""
    try:
        profile = await profile_service._get_or_create_profile(user_id)

        # Update privacy settings
        profile.privacy_settings = {
            "data_collection": request.data_collection,
            "public_profile": request.public_profile,
            "share_analytics": request.share_analytics,
            "memory_retention": request.memory_retention
        }

        # Save profile
        await profile_service._save_profile(user_id, profile)

        return {
            "message": "Privacy settings updated successfully",
            "settings": profile.privacy_settings
        }

    except Exception as e:
        logger.error(f"Failed to update privacy settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/settings/{user_id}")
async def get_privacy_settings(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Get user's current privacy settings"""
    try:
        profile = await profile_service._get_profile(user_id)
        if not profile:
            # Return default settings
            default_settings = {
                "data_collection": True,
                "public_profile": False,
                "share_analytics": True,
                "memory_retention": True
            }
            return {"user_id": user_id, "settings": default_settings}

        return {
            "user_id": user_id,
            "settings": profile.privacy_settings
        }

    except Exception as e:
        logger.error(f"Failed to get privacy settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Background tasks
async def _delete_all_user_data(
    user_id: str,
    profile_service: ProfileService,
    memory_manager: TemporalMemoryManager
):
    """Delete all user data (background task)"""
    try:
        # Delete from profile service
        if user_id in profile_service.profiles:
            del profile_service.profiles[user_id]

        # Delete from memory manager
        if user_id in memory_manager.memory_cache:
            del memory_manager.memory_cache[user_id]

        # Delete from Zep
        # (Implementation depends on Zep API)

        logger.info(f"Deleted all data for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to delete all data for {user_id}: {e}")


async def _delete_preference_category(
    user_id: str,
    category: str,
    profile_service: ProfileService
):
    """Delete preferences in specific category"""
    try:
        profile = await profile_service._get_profile(user_id)
        if not profile:
            return False

        # Remove preferences with matching category
        keys_to_delete = [
            k for k in profile.preferences.keys()
            if k == f"pref_{category}" or k.startswith(f"pref_{category}_")
        ]

        for key in keys_to_delete:
            del profile.preferences[key]

        # Save updated profile
        await profile_service._save_profile(user_id, profile)
        return True

    except Exception as e:
        logger.error(f"Failed to delete preference category {category}: {e}")
        return False


async def _delete_old_data(
    user_id: str,
    cutoff_date: datetime,
    profile_service: ProfileService,
    memory_manager: TemporalMemoryManager
):
    """Delete data older than cutoff date"""
    try:
        # Filter preference history
        profile = await profile_service._get_profile(user_id)
        if profile:
            profile.preference_history = [
                p for p in profile.preference_history
                if p.timestamp >= cutoff_date
            ]
            await profile_service._save_profile(user_id, profile)

        # Filter memory fragments
        if user_id in memory_manager.memory_cache:
            memory_manager.memory_cache[user_id] = [
                m for m in memory_manager.memory_cache[user_id]
                if m.timestamp >= cutoff_date
            ]

        logger.info(f"Deleted old data for user {user_id} before {cutoff_date}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete old data: {e}")
        return False


async def _generate_user_export(
    export_id: str,
    user_id: str,
    request: Dict[str, Any],
    profile_service: ProfileService,
    memory_manager: TemporalMemoryManager
):
    """Generate user data export (background task)"""
    try:
        export_data = {
            "export_id": export_id,
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "format": request["format"],
            "data": {}
        }

        # Export preferences
        if request.get("include_preferences", True):
            profile = await profile_service.get_profile_with_privacy(user_id, "self")
            if profile:
                export_data["data"]["preferences"] = profile.get("preferences", {})

        # Export conversation summaries
        if request.get("include_conversations", True):
            context = await memory_manager.get_contextual_memory(user_id, "")
            export_data["data"]["conversation_summary"] = {
                "episodic_count": len(context.episodic_memory),
                "semantic_categories": list(context.semantic_memory.keys()),
                "working_memory_size": len(context.working_memory)
            }

        # Export analytics
        if request.get("include_analytics", False):
            export_data["data"]["analytics"] = {
                "message": "Analytics data would be included here"
            }

        # Save export (in production, to secure storage)
        # export_path = f"exports/{export_id}.{request['format']}"
        # with open(export_path, "w") as f:
        #     json.dump(export_data, f, indent=2)

        logger.info(f"Generated export {export_id} for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to generate export: {e}")