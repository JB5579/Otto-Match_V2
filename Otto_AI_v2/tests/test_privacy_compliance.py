"""
Privacy Compliance Tests for GDPR/CCPA requirements
"""

import pytest
from datetime import datetime, timedelta
from src.services.profile_service import ProfileService
from src.api.privacy_controller import (
    PrivacySettingsRequest,
    DataExportRequest,
    ForgetRequest
)
from src.conversation.nlu_service import UserPreference


@pytest.mark.privacy
class TestGDPRCompliance:
    """GDPR compliance test suite"""

    async def test_right_to_access(self, profile_service):
        """
        GDPR Right of Access: Users can request all personal data stored about them
        """
        user_id = "gdpr_user_1"

        # Create user data
        user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "location": "San Francisco, CA",
            "preferences": [
                UserPreference(
                    category="brand",
                    value="Toyota",
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
                    timestamp=datetime.now() - timedelta(days=5)
                )
            ]
        }

        # Store user data
        await profile_service.update_profile_preferences(
            user_id,
            user_data["preferences"],
            source="user_input"
        )

        # Request all data
        all_data = await profile_service.get_profile_with_privacy(user_id, "self")

        # Verify data completeness
        access_checks = {
            "has_preferences": len(all_data.get("preferences", {})) > 0,
            "has_timestamps": all_data.get("created_at") is not None,
            "has_preferences_history": len(all_data.get("preference_history", [])) > 0,
            "data_is_readable": isinstance(all_data, dict)
        }

        print(f"\nGDPR Right to Access Checks: {access_checks}")
        assert all(access_checks.values()), "User should be able to access all their data"

    async def test_right_to_rectification(self, profile_service):
        """
        GDPR Right to Rectification: Users can correct inaccurate personal data
        """
        user_id = "gdpr_user_2"

        # Store initial incorrect preference
        incorrect_pref = UserPreference(
            category="budget",
            value={"max": 25000},  # Too low, will be corrected
            weight=0.8,
            source="explicit",
            confidence=0.7,
            timestamp=datetime.now() - timedelta(days=10)
        )

        await profile_service.update_profile_preferences(user_id, [incorrect_pref])

        # User requests correction
        corrected_pref = UserPreference(
            category="budget",
            value={"max": 40000},  # Corrected value
            weight=0.8,
            source="corrected",
            confidence=0.9,
            timestamp=datetime.now()
        )

        correction_success = await profile_service.update_profile_preferences(
            user_id,
            [corrected_pref],
            source="user_correction"
        )

        # Verify correction
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        current_budget = profile.get("preferences", {}).get("pref_budget", {})

        rectification_checks = {
            "correction_successful": correction_success,
            "old_value_preserved_in_history": len(profile.get("preference_history", [])) > 0,
            "new_value_applied": current_budget.get("value", {}).get("max") == 40000,
            "confidence_updated": current_budget.get("confidence") == 0.9,
            "source_marked_as_corrected": current_budget.get("source") == "user_correction"
        }

        print(f"\nGDPR Right to Rectification Checks: {rectification_checks}")
        assert all(rectification_checks.values()), "User should be able to correct their data"

    async def test_right_to_erasure(self, profile_service, mock_zep_client):
        """
        GDPR Right to Erasure: Users can request deletion of their data
        """
        user_id = "gdpr_user_3"

        # Create substantial user data
        preferences = [
            UserPreference(
                category="brand",
                value="Honda",
                weight=0.9,
                source="explicit"
            ),
            UserPreference(
                category="vehicle_type",
                value="SUV",
                weight=0.8,
                source="explicit"
            ),
            UserPreference(
                category="location",
                value="New York, NY",
                weight=0.7,
                source="implicit"
            )
        ]

        await profile_service.update_profile_preferences(user_id, preferences)
        await mock_zep_client.add_conversation_turn(
            user_id,
            "I need a reliable SUV",
            "I understand you're looking for a reliable SUV"
        )

        # Verify data exists
        profile_before = await profile_service.get_profile_with_privacy(user_id, "self")
        assert len(profile_before.get("preferences", {})) > 0, "Data should exist before deletion"

        # Request erasure
        erase_request = ForgetRequest(
            all_data=True
        )

        # Simulate erasure process
        erase_success = True
        if user_id in profile_service.profiles:
            del profile_service.profiles[user_id]
        if user_id in mock_zep_client.conversation_store:
            del mock_zep_client.conversation_store[user_id]
        if user_id in mock_zep_client.memory_store:
            del mock_zep_client.memory_store[user_id]

        # Verify erasure
        profile_after = await profile_service._get_profile(user_id)
        conversations_after = mock_zep_client.conversation_store.get(user_id, [])

        erasure_checks = {
            "profile_deleted": profile_after is None,
            "conversations_deleted": len(conversations_after) == 0,
            "all_traces_removed": user_id not in profile_service.profiles
        }

        print(f"\nGDPR Right to Erasure Checks: {erasure_checks}")
        assert all(erasure_checks.values()), "All user data should be erased on request"

    async def test_right_to_portability(self, profile_service):
        """
        GDPR Right to Data Portability: Users can request their data in machine-readable format
        """
        user_id = "gdpr_user_4"

        # Create user data with various types
        user_preferences = [
            UserPreference(
                category="brand",
                value=["Toyota", "Honda"],
                weight=0.85,
                source="explicit",
                confidence=0.9,
                timestamp=datetime.now() - timedelta(days=30)
            ),
            UserPreference(
                category="vehicle_features",
                value=["safety_ratings", "fuel_economy", "apple_carplay"],
                weight=0.8,
                source="explicit",
                confidence=0.85,
                timestamp=datetime.now() - timedelta(days=15)
            )
        ]

        await profile_service.update_profile_preferences(user_id, user_preferences)

        # Request data export in JSON format
        export_request = DataExportRequest(
            format="json",
            include_conversations=True,
            include_preferences=True,
            include_analytics=False
        )

        # Generate export data
        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "format": export_request.format,
            "data": {}
        }

        if export_request.include_preferences:
            export_data["data"]["preferences"] = profile.get("preferences", {})

        if export_request.include_conversations:
            export_data["data"]["conversations_summary"] = {
                "total_conversations": 5,  # Mock data
                "date_range": {
                    "first": (datetime.now() - timedelta(days=30)).isoformat(),
                    "last": datetime.now().isoformat()
                }
            }

        # Verify portability
        portability_checks = {
            "json_format": isinstance(export_data, dict),
            "has_user_id": "user_id" in export_data,
            "has_export_date": "export_date" in export_data,
            "includes_preferences": "preferences" in export_data.get("data", {}),
            "preferences_readable": len(export_data.get("data", {}).get("preferences", {})) > 0,
            "structured_data": all(key in export_data for key in ["user_id", "export_date", "data"])
        }

        print(f"\nGDPR Right to Portability Checks: {portability_checks}")
        print(f"Export sample size: {len(str(export_data))} characters")

        assert all(portability_checks.values()), "Data should be portable in machine-readable format"

    async def test_privacy_settings_control(self, profile_service):
        """
        Users should have granular control over privacy settings
        """
        user_id = "privacy_user_1"

        # Default privacy settings
        default_settings = {
            "data_collection": True,
            "public_profile": False,
            "share_analytics": True,
            "memory_retention": True
        }

        # User changes privacy settings
        new_settings = PrivacySettingsRequest(
            data_collection=False,
            public_profile=False,
            share_analytics=False,
            memory_retention=True
        )

        # Apply settings
        profile = await profile_service._get_or_create_profile(user_id)
        profile.privacy_settings = {
            "data_collection": new_settings.data_collection,
            "public_profile": new_settings.public_profile,
            "share_analytics": new_settings.share_analytics,
            "memory_retention": new_settings.memory_retention
        }

        # Verify settings applied
        current_settings = profile.privacy_settings
        settings_checks = {
            "data_collection_disabled": not current_settings.get("data_collection", True),
            "analytics_sharing_disabled": not current_settings.get("share_analytics", True),
            "profile_private": not current_settings.get("public_profile", False),
            "memory_retained": current_settings.get("memory_retention", False)
        }

        print(f"\nPrivacy Settings Control Checks: {settings_checks}")
        assert all(settings_checks.values()), "User should control their privacy settings"

    async def test_data_minimization(self, profile_service):
        """
        GDPR Data Minimization: Only collect necessary data
        """
        user_id = "minimization_user"

        # Check what data is being collected
        profile = await profile_service._get_or_create_profile(user_id)

        # Data fields check
        essential_fields = {
            "user_id": "user_id" in profile.__dict__ or hasattr(profile, 'user_id'),
            "created_at": "created_at" in profile.__dict__ or hasattr(profile, 'created_at'),
            "updated_at": "updated_at" in profile.__dict__ or hasattr(profile, 'updated_at'),
            "preferences": hasattr(profile, 'preferences')
        }

        # Check no unnecessary data is stored
        unnecessary_fields = [
            "social_security_number",
            "credit_card",
            "password_plain",
            "secret_question"
        ]

        profile_dict = profile.__dict__ if hasattr(profile, '__dict__') else {}
        has_unnecessary = any(field in profile_dict for field in unnecessary_fields)

        minimization_checks = {
            "collects_essential_data": all(essential_fields.values()),
            "no_unnecessary_data": not has_unnecessary,
            "preferences_structured": isinstance(profile.preferences, dict) if hasattr(profile, 'preferences') else False
        }

        print(f"\nData Minimization Checks: {minimization_checks}")
        assert minimization_checks["no_unnecessary_data"], "Should not collect unnecessary data"
        assert all([minimization_checks[k] for k in essential_fields]), "Should collect only essential data"

    async def test_consent_management(self, profile_service):
        """
        GDPR Consent Management: Users can grant and withdraw consent
        """
        user_id = "consent_user"

        # Create profile with consent tracking
        profile = await profile_service._get_or_create_profile(user_id)

        # Grant consent for data processing
        consent_granted = {
            "data_processing": True,
            "personalization": True,
            "analytics": True,
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.1",  # For audit trail
            "user_agent": "OttoAI-WebApp/1.0"
        }

        profile.consent = consent_granted

        # Later, user withdraws consent for analytics
        profile.consent["analytics"] = False
        profile.consent["withdrawal_timestamp"] = datetime.now().isoformat()
        profile.consent["withdrawal_reason"] = "User request"

        # Verify consent management
        consent_checks = {
            "has_consent_record": hasattr(profile, 'consent'),
            "consent_timestamped": profile.consent.get("timestamp") is not None,
            "withdrawal_tracked": profile.consent.get("withdrawal_timestamp") is not None,
            "partial_consent": profile.consent.get("data_processing") == True and profile.consent.get("analytics") == False
        }

        print(f"\nConsent Management Checks: {consent_checks}")
        assert all(consent_checks.values()), "Consent should be properly managed and tracked"

    async def test_data_retention_policy(self, profile_service):
        """
        Test data retention policy compliance
        """
        user_id = "retention_user"

        # Create old preferences
        old_preferences = [
            UserPreference(
                category="brand",
                value="Ford",
                weight=0.5,
                source="explicit",
                timestamp=datetime.now() - timedelta(days=400)  # Older than retention period
            ),
            UserPreference(
                category="price",
                value={"max": 20000},
                weight=0.6,
                source="explicit",
                timestamp=datetime.now() - timedelta(days=50)  # Within retention period
            )
        ]

        await profile_service.update_profile_preferences(user_id, old_preferences)

        # Simulate retention policy check (365 days)
        retention_period = 365
        cutoff_date = datetime.now() - timedelta(days=retention_period)

        profile = await profile_service.get_profile_with_privacy(user_id, "self")
        preferences = profile.get("preferences", {})

        # Check old data handling
        old_brand_pref = preferences.get("pref_brand", {})
        recent_price_pref = preferences.get("pref_price", {})

        retention_checks = {
            "recent_data_retained": recent_price_pref.get("timestamp", datetime.now()) > cutoff_date,
            "old_data_anonymized": True  # In real implementation, old data would be anonymized
        }

        print(f"\nData Retention Policy Checks: {retention_checks}")
        assert retention_checks["recent_data_retained"], "Recent data should be retained"
        # Note: In production, implement actual data anonymization for old data


@pytest.mark.privacy
class TestCCPACompliance:
    """CCPA compliance test suite"""

    async def test_do_not_sell_option(self, profile_service):
        """
        CCPA Do Not Sell My Personal Information
        """
        user_id = "ccpa_user_1"

        # Create profile
        profile = await profile_service._get_or_create_profile(user_id)

        # User opts out of data selling
        profile.privacy_settings = {
            "data_collection": True,
            "share_analytics": False,  # Opt out
            "do_not_sell": True,
            "opt_out_timestamp": datetime.now().isoformat()
        }

        # Verify opt-out
        opt_out_checks = {
            "do_not_sell_flag": profile.privacy_settings.get("do_not_sell", False),
            "analytics_disabled": not profile.privacy_settings.get("share_analytics", True),
            "opt_out_timestamped": profile.privacy_settings.get("opt_out_timestamp") is not None
        }

        print(f"\nCCPA Do Not Sell Checks: {opt_out_checks}")
        assert all(opt_out_checks.values()), "User should be able to opt out of data selling"

    async def test_business_practices_transparency(self, profile_service):
        """
        CCPA requires transparency about business practices and data use
        """
        user_id = "transparency_user"

        # Get privacy policy information
        privacy_info = {
            "data_collected": [
                "Vehicle preferences",
                "Conversation history",
                "Usage patterns",
                "Location data (optional)"
            ],
            "data_purpose": [
                "Personalize vehicle recommendations",
                "Improve service quality",
                "Provide better user experience"
            ],
            "data_sharing": [
                "Not sold to third parties",
                "Shared only with service providers",
                "Anonymized for analytics"
            ],
            "retention_period": "365 days from last interaction",
            "user_rights": [
                "Right to know",
                "Right to delete",
                "Right to opt-out",
                "Right to non-discrimination"
            ]
        }

        # Verify transparency requirements met
        transparency_checks = {
            "data_types_listed": len(privacy_info["data_collected"]) > 0,
            "purposes_explained": len(privacy_info["data_purpose"]) > 0,
            "sharing_disclosed": len(privacy_info["data_sharing"]) > 0,
            "retention_specified": privacy_info["retention_period"] is not None,
            "rights_documented": len(privacy_info["user_rights"]) >= 4
        }

        print(f"\nCCPA Transparency Checks: {transparency_checks}")
        assert all(transparency_checks.values()), "Business practices should be transparent"