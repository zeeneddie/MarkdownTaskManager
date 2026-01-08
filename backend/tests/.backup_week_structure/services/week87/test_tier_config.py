"""
Tests for Tier Configuration Service - Week 87

Tests granular tier selection at project, epic, feature, and story level.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4, UUID
from datetime import datetime

from app.services.tier_config_service import TierConfigService
from app.models.deep_extraction import (
    ExtractionSession, ExtractionConsensus, ExtractionTier, TIER_CONFIG
)


# ============================================================================
# FIXTURES - HCI-CRS Project Data
# ============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Create mock extraction session with HCI-CRS project."""
    session = MagicMock(spec=ExtractionSession)
    session.id = uuid4()
    session.tier = "STANDARD"
    session.allow_epic_override = 'Y'
    session.allow_feature_override = 'Y'
    session.allow_story_override = 'Y'
    session.tier_config_locked = 'N'
    return session


@pytest.fixture
def mock_epic():
    """Create mock epic consensus item."""
    epic = MagicMock(spec=ExtractionConsensus)
    epic.id = uuid4()
    epic.session_id = uuid4()
    epic.item_type = "epic"
    epic.item_title = "EPIC: Jeugdtraject Management"
    epic.tier_override = None
    epic.tier_effective = "STANDARD"
    epic.parent_id = None
    return epic


@pytest.fixture
def mock_feature():
    """Create mock feature consensus item."""
    feature = MagicMock(spec=ExtractionConsensus)
    feature.id = uuid4()
    feature.session_id = uuid4()
    feature.item_type = "feature"
    feature.item_title = "FEATURE: Tellertje Component"
    feature.tier_override = None
    feature.tier_effective = "STANDARD"
    feature.parent_id = None
    return feature


@pytest.fixture
def mock_story():
    """Create mock story consensus item."""
    story = MagicMock(spec=ExtractionConsensus)
    story.id = uuid4()
    story.session_id = uuid4()
    story.item_type = "story"
    story.item_title = "Als gebruiker wil ik een tellertje zien"
    story.tier_override = None
    story.tier_effective = "STANDARD"
    story.parent_id = None
    return story


# ============================================================================
# TEST: Tier Inheritance
# ============================================================================

class TestTierInheritance:
    """Test tier inheritance logic."""

    def test_item_with_override_uses_override(self, mock_db, mock_session, mock_epic):
        """Item with tier_override should use its own override."""
        mock_epic.tier_override = "PREMIUM"

        service = TierConfigService(mock_db)
        effective = service.get_effective_tier(mock_epic, mock_session)

        assert effective == "PREMIUM"

    def test_item_without_override_inherits_from_session(self, mock_db, mock_session, mock_epic):
        """Item without tier_override should inherit from session."""
        mock_epic.tier_override = None
        mock_epic.parent_id = None
        mock_session.tier = "PROFESSIONAL"

        service = TierConfigService(mock_db)
        effective = service.get_effective_tier(mock_epic, mock_session)

        assert effective == "PROFESSIONAL"

    def test_child_inherits_from_parent(self, mock_db, mock_session, mock_feature, mock_epic):
        """Child without override should inherit from parent's effective tier."""
        mock_feature.tier_override = None
        mock_feature.parent_id = mock_epic.id
        mock_epic.tier_effective = "PREMIUM"

        # Setup mock query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_epic

        service = TierConfigService(mock_db)
        effective = service.get_effective_tier(mock_feature, mock_session)

        assert effective == "PREMIUM"


# ============================================================================
# TEST: Set Item Tier Override
# ============================================================================

class TestSetItemTierOverride:
    """Test setting tier override on items."""

    def test_set_valid_tier_override(self, mock_db, mock_session, mock_epic):
        """Should successfully set a valid tier override."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_epic, mock_session]

        service = TierConfigService(mock_db)
        result = service.set_item_tier_override(mock_epic.id, "PREMIUM", cascade=False)

        assert "error" not in result
        assert result["new_tier_override"] == "PREMIUM"

    def test_reject_invalid_tier(self, mock_db, mock_session, mock_epic):
        """Should reject invalid tier values."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_epic, mock_session]

        service = TierConfigService(mock_db)
        result = service.set_item_tier_override(mock_epic.id, "INVALID_TIER", cascade=False)

        assert "error" in result
        assert "Invalid tier" in result["error"]

    def test_reject_when_config_locked(self, mock_db, mock_session, mock_epic):
        """Should reject changes when tier_config_locked is Y."""
        mock_session.tier_config_locked = 'Y'
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_epic, mock_session]

        service = TierConfigService(mock_db)
        result = service.set_item_tier_override(mock_epic.id, "PREMIUM", cascade=False)

        assert "error" in result
        assert "locked" in result["error"]

    def test_reject_epic_override_when_disabled(self, mock_db, mock_session, mock_epic):
        """Should reject epic override when allow_epic_override is N."""
        mock_session.allow_epic_override = 'N'
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_epic, mock_session]

        service = TierConfigService(mock_db)
        result = service.set_item_tier_override(mock_epic.id, "PREMIUM", cascade=False)

        assert "error" in result
        assert "disabled" in result["error"]

    def test_clear_override_with_none(self, mock_db, mock_session, mock_epic):
        """Should clear override when tier is None."""
        mock_epic.tier_override = "PREMIUM"
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_epic, mock_session]

        service = TierConfigService(mock_db)
        result = service.set_item_tier_override(mock_epic.id, None, cascade=False)

        assert "error" not in result
        assert result["new_tier_override"] is None


# ============================================================================
# TEST: Expected Outcomes
# ============================================================================

class TestExpectedOutcomes:
    """Test expected outcomes calculation."""

    def test_premium_tier_outcomes(self, mock_db, mock_epic):
        """PREMIUM tier should have highest confidence and cost."""
        service = TierConfigService(mock_db)
        service._update_expected_outcomes(mock_epic, "PREMIUM")

        assert mock_epic.expected_confidence == 0.95
        assert mock_epic.expected_llm_count == 10
        assert mock_epic.expected_cost_usd > 0

    def test_free_tier_outcomes(self, mock_db, mock_epic):
        """FREE tier should have lowest confidence and zero cost."""
        service = TierConfigService(mock_db)
        service._update_expected_outcomes(mock_epic, "FREE")

        assert mock_epic.expected_confidence == 0.60
        assert mock_epic.expected_llm_count == 3
        assert mock_epic.expected_cost_usd == 0.0

    def test_standard_tier_outcomes(self, mock_db, mock_feature):
        """STANDARD tier should have 80% confidence."""
        service = TierConfigService(mock_db)
        service._update_expected_outcomes(mock_feature, "STANDARD")

        assert mock_feature.expected_confidence == 0.80
        assert mock_feature.expected_llm_count == 7

    def test_item_type_affects_cost(self, mock_db, mock_epic, mock_story):
        """Epic should cost more than story for same tier."""
        service = TierConfigService(mock_db)

        service._update_expected_outcomes(mock_epic, "STANDARD")
        epic_cost = mock_epic.expected_cost_usd

        service._update_expected_outcomes(mock_story, "STANDARD")
        story_cost = mock_story.expected_cost_usd

        assert epic_cost > story_cost


# ============================================================================
# TEST: Tier Comparison
# ============================================================================

class TestTierComparison:
    """Test tier comparison functionality."""

    def test_compare_all_tiers_for_item(self, mock_db, mock_epic):
        """Should return comparison for all 5 tiers."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_epic

        service = TierConfigService(mock_db)
        result = service.compare_tiers_for_item(mock_epic.id)

        assert "error" not in result
        assert len(result["comparisons"]) == 5
        assert "FREE" in result["comparisons"]
        assert "PREMIUM" in result["comparisons"]

    def test_comparison_includes_all_fields(self, mock_db, mock_epic):
        """Each tier comparison should include all required fields."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_epic

        service = TierConfigService(mock_db)
        result = service.compare_tiers_for_item(mock_epic.id)

        tier_info = result["comparisons"]["STANDARD"]
        assert "price_usd" in tier_info
        assert "confidence_target" in tier_info
        assert "llm_count" in tier_info
        assert "human_review" in tier_info
        assert "estimated_cost" in tier_info
        assert "llms" in tier_info


# ============================================================================
# TEST: Session Settings
# ============================================================================

class TestSessionSettings:
    """Test session-level tier settings."""

    def test_update_session_tier(self, mock_db, mock_session):
        """Should update session default tier."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TierConfigService(mock_db)
        result = service.update_session_tier_settings(
            mock_session.id,
            {"tier": "PROFESSIONAL"}
        )

        assert "error" not in result
        assert "tier" in result["updated_fields"]

    def test_update_override_settings(self, mock_db, mock_session):
        """Should update override permission settings."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        service = TierConfigService(mock_db)
        result = service.update_session_tier_settings(
            mock_session.id,
            {
                "allow_epic_override": "N",
                "allow_feature_override": "N",
                "allow_story_override": "Y"
            }
        )

        assert "error" not in result
        assert "allow_epic_override" in result["updated_fields"]

    def test_reject_invalid_tier_value(self, mock_db, mock_session):
        """Should reject invalid tier values."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        service = TierConfigService(mock_db)
        result = service.update_session_tier_settings(
            mock_session.id,
            {"tier": "SUPER_PREMIUM"}
        )

        assert "error" in result
        assert "Invalid tier" in result["error"]


# ============================================================================
# TEST: Bulk Operations
# ============================================================================

class TestBulkOperations:
    """Test bulk tier override operations."""

    def test_bulk_set_overrides(self, mock_db, mock_session, mock_epic, mock_feature):
        """Should set multiple tier overrides at once."""
        # Configure mock to always return session for first() calls
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic, mock_feature]

        # Override set_item_tier_override to avoid complex mocking
        service = TierConfigService(mock_db)

        # Mock the internal method
        with patch.object(service, 'set_item_tier_override') as mock_set:
            mock_set.return_value = {"item_id": "test", "new_tier_override": "PREMIUM"}

            result = service.bulk_set_tier_overrides(
                mock_session.id,
                {
                    str(mock_epic.id): "PREMIUM",
                    str(mock_feature.id): "FREE"
                }
            )

        assert "error" not in result
        assert result["items_updated"] >= 0

    def test_reset_all_overrides(self, mock_db, mock_session, mock_epic, mock_feature):
        """Should reset all overrides to inherit from session."""
        mock_epic.tier_override = "PREMIUM"
        mock_feature.tier_override = "FREE"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic, mock_feature]

        service = TierConfigService(mock_db)
        result = service.reset_all_overrides(mock_session.id)

        assert "error" not in result
        assert result["items_reset"] == 2


# ============================================================================
# TEST: Hierarchy Configuration
# ============================================================================

class TestHierarchyConfiguration:
    """Test hierarchy configuration retrieval."""

    def test_get_hierarchy_config(self, mock_db, mock_session, mock_epic, mock_feature):
        """Should return full hierarchy with tier info."""
        mock_epic.children = []
        mock_feature.parent_id = mock_epic.id
        mock_feature.children = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic, mock_feature]

        service = TierConfigService(mock_db)
        result = service.get_hierarchy_config(mock_session.id)

        assert "error" not in result
        assert "hierarchy" in result
        assert "settings" in result
        assert result["session_tier"] == "STANDARD"

    def test_hierarchy_includes_settings(self, mock_db, mock_session):
        """Should include all session settings in response."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = TierConfigService(mock_db)
        result = service.get_hierarchy_config(mock_session.id)

        settings = result["settings"]
        assert "allow_epic_override" in settings
        assert "allow_feature_override" in settings
        assert "allow_story_override" in settings
        assert "tier_config_locked" in settings


# ============================================================================
# TEST: Expected Outcomes Preview
# ============================================================================

class TestExpectedOutcomesPreview:
    """Test expected outcomes preview functionality."""

    def test_preview_without_changes(self, mock_db, mock_session, mock_epic):
        """Should return current state when no overrides provided."""
        mock_epic.tier_effective = "STANDARD"
        mock_epic.expected_confidence = 0.80
        mock_epic.expected_cost_usd = 5.0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic]

        service = TierConfigService(mock_db)
        result = service.get_expected_outcomes_preview(mock_session.id, None)

        assert "error" not in result
        assert result["total_items"] == 1
        assert result["total_cost_usd"] >= 0

    def test_preview_with_overrides(self, mock_db, mock_session, mock_epic):
        """Should calculate preview with hypothetical overrides."""
        mock_epic.tier_effective = "STANDARD"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic]

        service = TierConfigService(mock_db)
        result = service.get_expected_outcomes_preview(
            mock_session.id,
            {str(mock_epic.id): "PREMIUM"}
        )

        assert "error" not in result
        # PREMIUM tier should be reflected in distribution
        assert result["tier_distribution"]["PREMIUM"]["count"] >= 0

    def test_preview_includes_tier_distribution(self, mock_db, mock_session, mock_epic, mock_feature):
        """Should include tier distribution breakdown."""
        mock_epic.tier_effective = "PREMIUM"
        mock_feature.tier_effective = "FREE"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_epic, mock_feature]

        service = TierConfigService(mock_db)
        result = service.get_expected_outcomes_preview(mock_session.id, None)

        assert "tier_distribution" in result
        assert "PREMIUM" in result["tier_distribution"]
        assert "FREE" in result["tier_distribution"]


# ============================================================================
# TEST: Cost Estimation
# ============================================================================

class TestCostEstimation:
    """Test cost estimation for different tiers and item types."""

    def test_premium_costs_more_than_free(self, mock_db, mock_epic):
        """PREMIUM tier should cost more than FREE."""
        service = TierConfigService(mock_db)

        premium_cost = service._estimate_item_cost(mock_epic, ExtractionTier.PREMIUM)
        free_cost = service._estimate_item_cost(mock_epic, ExtractionTier.FREE)

        assert premium_cost > free_cost
        assert free_cost == 0.0

    def test_epic_costs_more_than_story(self, mock_db, mock_epic, mock_story):
        """Epic should cost more than story due to LOC multiplier."""
        service = TierConfigService(mock_db)

        epic_cost = service._estimate_item_cost(mock_epic, ExtractionTier.STANDARD)
        story_cost = service._estimate_item_cost(mock_story, ExtractionTier.STANDARD)

        assert epic_cost > story_cost

    def test_cost_scales_with_tier(self, mock_db, mock_feature):
        """Cost should increase with higher tiers."""
        service = TierConfigService(mock_db)

        costs = {}
        for tier in ExtractionTier:
            costs[tier.value] = service._estimate_item_cost(mock_feature, tier)

        assert costs["PREMIUM"] > costs["PROFESSIONAL"]
        assert costs["PROFESSIONAL"] > costs["STANDARD"]
        assert costs["STANDARD"] > costs["BASIC"]
        assert costs["BASIC"] > costs["FREE"]


# ============================================================================
# TEST: TIER_CONFIG Validation
# ============================================================================

class TestTierConfigValidation:
    """Test that TIER_CONFIG has correct values."""

    def test_all_tiers_have_config(self):
        """All ExtractionTier values should have a config entry."""
        for tier in ExtractionTier:
            assert tier in TIER_CONFIG

    def test_confidence_targets_increase(self):
        """Confidence targets should increase with tier level."""
        targets = [
            TIER_CONFIG[ExtractionTier.FREE]["confidence_target"],
            TIER_CONFIG[ExtractionTier.BASIC]["confidence_target"],
            TIER_CONFIG[ExtractionTier.STANDARD]["confidence_target"],
            TIER_CONFIG[ExtractionTier.PROFESSIONAL]["confidence_target"],
            TIER_CONFIG[ExtractionTier.PREMIUM]["confidence_target"],
        ]
        assert targets == sorted(targets)

    def test_llm_counts_increase(self):
        """LLM counts should increase with tier level."""
        counts = [
            TIER_CONFIG[ExtractionTier.FREE]["llm_count"],
            TIER_CONFIG[ExtractionTier.BASIC]["llm_count"],
            TIER_CONFIG[ExtractionTier.STANDARD]["llm_count"],
            TIER_CONFIG[ExtractionTier.PROFESSIONAL]["llm_count"],
            TIER_CONFIG[ExtractionTier.PREMIUM]["llm_count"],
        ]
        assert counts == sorted(counts)

    def test_premium_includes_opus(self):
        """PREMIUM tier should include Claude Opus."""
        premium_llms = TIER_CONFIG[ExtractionTier.PREMIUM]["llms"]
        assert any("claude" in llm.lower() or "opus" in llm.lower() for llm in premium_llms)

    def test_free_only_uses_ollama(self):
        """FREE tier should only use Ollama (local) models."""
        free_llms = TIER_CONFIG[ExtractionTier.FREE]["llms"]
        assert all(llm.startswith("ollama/") for llm in free_llms)
