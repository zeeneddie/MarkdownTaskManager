"""
Integration Tests for Extraction Tier Integration.

Tests tier selection, pricing, and integration across extraction services.

Coverage:
- Tier upgrade flows
- Cost estimation vs actual costs
- Provider selection across services
- Confidence target adherence
- Human review integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    TIER_CONFIG,
)
from app.services.tier_provider_selector import (
    TierProviderSelector,
    create_tier_selector,
    compare_tiers,
    PROVIDER_COSTS,
    LLMCallResult,
)
from app.services.deep_extraction_service import DeepExtractionService


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def all_tier_selectors():
    """Create selectors for all tiers."""
    return {
        tier: create_tier_selector(tier)
        for tier in ExtractionTier
    }


# =============================================================================
# TIER COMPARISON AND ONBOARDING TESTS
# =============================================================================


class TestTierComparisonOnboarding:
    """Tests for tier comparison used in onboarding flow."""

    def test_compare_tiers_for_onboarding(self):
        """Test that tier comparison provides all onboarding data."""
        comparison = compare_tiers()

        assert isinstance(comparison, list)
        assert len(comparison) == len(ExtractionTier)

        for tier_info in comparison:
            assert "tier" in tier_info
            assert "price_usd" in tier_info
            assert "confidence_target" in tier_info
            assert "llm_count" in tier_info
            assert "human_review" in tier_info
            assert "llms" in tier_info

    def test_standard_tier_is_recommended(self):
        """Test that STANDARD tier is marked as recommended."""
        comparison = compare_tiers()

        recommended = [c for c in comparison if c.get("recommended", False)]
        assert len(recommended) == 1
        assert recommended[0]["tier"] == ExtractionTier.STANDARD.value

    def test_tier_comparison_shows_llm_categories(self):
        """Test that tier comparison shows LLM categories."""
        comparison = compare_tiers()

        for tier_info in comparison:
            assert "categories" in tier_info
            categories = tier_info["categories"]
            assert "local" in categories
            assert "fast" in categories
            assert "balanced" in categories
            assert "deep" in categories

    def test_price_progression_makes_sense(self):
        """Test that price progression is logical."""
        comparison = compare_tiers()

        # Sort by price
        sorted_tiers = sorted(comparison, key=lambda x: x["price_usd"])

        # Prices should increase
        for i in range(len(sorted_tiers) - 1):
            assert sorted_tiers[i]["price_usd"] <= sorted_tiers[i + 1]["price_usd"]

        # Value proposition: more LLMs for higher price
        for i in range(len(sorted_tiers) - 1):
            if sorted_tiers[i + 1]["price_usd"] > sorted_tiers[i]["price_usd"]:
                assert sorted_tiers[i + 1]["llm_count"] >= sorted_tiers[i]["llm_count"]


# =============================================================================
# TIER UPGRADE FLOW TESTS
# =============================================================================


class TestTierUpgradeFlow:
    """Tests for tier upgrade functionality."""

    def test_upgrade_from_basic_to_standard(self):
        """Test upgrading from BASIC to STANDARD tier."""
        selector = create_tier_selector(ExtractionTier.BASIC)
        result = selector.upgrade_tier(ExtractionTier.STANDARD)

        assert result["old_tier"] == "BASIC"
        assert result["new_tier"] == "STANDARD"
        assert result["new_price_usd"] > result["old_price_usd"]
        assert result["new_provider_count"] > result["old_provider_count"]

    def test_upgrade_calculates_credit(self):
        """Test that upgrade calculates credit from previous tier."""
        selector = create_tier_selector(ExtractionTier.BASIC)
        old_price = selector.get_price_usd()

        result = selector.upgrade_tier(ExtractionTier.STANDARD)

        assert result["credit_usd"] == old_price
        assert result["amount_to_charge_usd"] == result["new_price_usd"] - old_price

    def test_upgrade_unlocks_new_providers(self):
        """Test that upgrade unlocks new LLM providers."""
        selector = create_tier_selector(ExtractionTier.BASIC)
        old_providers = set(selector.get_provider_ids())

        result = selector.upgrade_tier(ExtractionTier.STANDARD)

        new_providers = set(selector.get_provider_ids())
        added = new_providers - old_providers

        assert len(result["providers_added"]) == len(added)

    def test_upgrade_improves_confidence_target(self):
        """Test that upgrade improves confidence target."""
        selector = create_tier_selector(ExtractionTier.BASIC)
        old_target = selector.get_confidence_target()

        result = selector.upgrade_tier(ExtractionTier.PROFESSIONAL)

        assert result["new_confidence_target"] > result["old_confidence_target"]
        assert selector.get_confidence_target() == result["new_confidence_target"]

    def test_upgrade_to_same_tier_no_charge(self):
        """Test that upgrading to same tier costs nothing extra."""
        selector = create_tier_selector(ExtractionTier.STANDARD)
        result = selector.upgrade_tier(ExtractionTier.STANDARD)

        assert result["amount_to_charge_usd"] == 0


# =============================================================================
# COST ESTIMATION TESTS
# =============================================================================


class TestCostEstimation:
    """Tests for cost estimation functionality."""

    def test_estimate_cost_per_provider(self):
        """Test cost estimation for individual providers."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)

        # Test local provider (free)
        local_cost = selector.calculate_cost("ollama/qwen2.5-coder:7b", 10000, 5000)
        assert local_cost == 0.0

        # Test paid provider
        paid_cost = selector.calculate_cost("openai/gpt-5.2", 10000, 5000)
        assert paid_cost > 0

    def test_cost_proportional_to_tokens(self):
        """Test that cost is proportional to token usage."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)

        cost_1k = selector.calculate_cost("openai/gpt-5.2", 1000, 500)
        cost_10k = selector.calculate_cost("openai/gpt-5.2", 10000, 5000)

        # 10x tokens should cost ~10x
        assert abs(cost_10k / cost_1k - 10) < 0.1

    def test_tier_margin_calculation(self):
        """Test margin calculation across tiers."""
        for tier in ExtractionTier:
            selector = create_tier_selector(tier)

            # Simulate some usage
            call = LLMCallResult(
                provider_id=selector.get_provider_ids()[0],
                model="test",
                content="test",
                cost_usd=1.0,
            )
            selector.track_call(call)

            margin = selector.get_margin()
            expected_margin = selector.get_price_usd() - 1.0

            assert margin == expected_margin


# =============================================================================
# PROVIDER AVAILABILITY TESTS
# =============================================================================


class TestProviderAvailability:
    """Tests for provider availability across tiers."""

    def test_each_tier_has_minimum_providers(self, all_tier_selectors):
        """Test that each tier has minimum required providers."""
        min_providers = {
            ExtractionTier.FREE: 3,
            ExtractionTier.BASIC: 3,
            ExtractionTier.STANDARD: 5,
            ExtractionTier.PROFESSIONAL: 7,
            ExtractionTier.PREMIUM: 10,
        }

        for tier, selector in all_tier_selectors.items():
            provider_count = len(selector.get_provider_ids())
            assert provider_count >= min_providers[tier], \
                f"{tier.value} should have >= {min_providers[tier]} providers"

    def test_higher_tiers_include_lower_tier_providers(self, all_tier_selectors):
        """Test that higher tiers include all lower tier providers."""
        tier_order = [
            ExtractionTier.FREE,
            ExtractionTier.BASIC,
            ExtractionTier.STANDARD,
            ExtractionTier.PROFESSIONAL,
            ExtractionTier.PREMIUM,
        ]

        for i in range(len(tier_order) - 1):
            lower_providers = set(all_tier_selectors[tier_order[i]].get_provider_ids())
            higher_providers = set(all_tier_selectors[tier_order[i + 1]].get_provider_ids())

            # Higher tier should include all lower tier providers
            assert lower_providers.issubset(higher_providers), \
                f"{tier_order[i+1].value} should include all {tier_order[i].value} providers"

    def test_premium_has_all_providers(self, all_tier_selectors):
        """Test that PREMIUM tier has all available providers."""
        premium_providers = set(all_tier_selectors[ExtractionTier.PREMIUM].get_provider_ids())

        # Should have providers from each major vendor
        assert any(p.startswith("ollama/") for p in premium_providers)
        assert any(p.startswith("openai/") or p.startswith("anthropic/") for p in premium_providers)


# =============================================================================
# CONFIDENCE TARGET ADHERENCE TESTS
# =============================================================================


class TestConfidenceTargetAdherence:
    """Tests for confidence target functionality."""

    def test_confidence_targets_increase_with_tier(self, all_tier_selectors):
        """Test that confidence targets increase with tier level."""
        tier_order = [
            ExtractionTier.FREE,
            ExtractionTier.BASIC,
            ExtractionTier.STANDARD,
            ExtractionTier.PROFESSIONAL,
            ExtractionTier.PREMIUM,
        ]

        targets = [
            all_tier_selectors[tier].get_confidence_target()
            for tier in tier_order
        ]

        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1], \
                f"Confidence should increase from {tier_order[i].value} to {tier_order[i+1].value}"

    def test_confidence_targets_are_reasonable(self, all_tier_selectors):
        """Test that confidence targets are in reasonable range."""
        for tier, selector in all_tier_selectors.items():
            target = selector.get_confidence_target()
            assert 0.5 <= target <= 1.0, f"{tier.value} has unreasonable target: {target}"


# =============================================================================
# HUMAN REVIEW INTEGRATION TESTS
# =============================================================================


class TestHumanReviewIntegration:
    """Tests for human review integration with tiers."""

    def test_human_review_tier_settings(self, all_tier_selectors):
        """Test human review settings per tier."""
        # Only PROFESSIONAL and PREMIUM include human review
        assert TIER_CONFIG[ExtractionTier.FREE]["human_review"] is False
        assert TIER_CONFIG[ExtractionTier.BASIC]["human_review"] is False
        assert TIER_CONFIG[ExtractionTier.STANDARD]["human_review"] is False
        assert TIER_CONFIG[ExtractionTier.PROFESSIONAL]["human_review"] is True
        assert TIER_CONFIG[ExtractionTier.PREMIUM]["human_review"] is True

    def test_human_review_affects_workflow(self):
        """Test that human review setting affects workflow execution."""
        # Tiers with human review require Cycle 4 completion
        for tier in [ExtractionTier.PROFESSIONAL, ExtractionTier.PREMIUM]:
            config = TIER_CONFIG[tier]
            assert config["human_review"] is True
            # These tiers also have higher confidence targets
            assert config["confidence_target"] >= 0.90


# =============================================================================
# CROSS-SERVICE INTEGRATION TESTS
# =============================================================================


class TestCrossServiceIntegration:
    """Tests for integration across extraction services."""

    @pytest.mark.asyncio
    async def test_deep_extraction_uses_tier_selector(self, mock_db):
        """Test that DeepExtractionService uses TierProviderSelector."""
        service = DeepExtractionService(mock_db)

        # Service should be able to create selectors
        assert hasattr(service, '_selectors')

    def test_selector_provides_analysis_assignments(self, all_tier_selectors):
        """Test that selectors provide analysis type assignments."""
        for tier, selector in all_tier_selectors.items():
            # Get cycle 1 assignments
            assignments = selector.get_providers_for_cycle(1)

            # Should have assignments
            assert len(assignments) > 0

            # Each assignment should have provider and type
            for provider_id, analysis_type in assignments:
                assert provider_id is not None
                assert analysis_type is not None

    def test_provider_info_includes_cost_and_health(self, all_tier_selectors):
        """Test that provider info includes cost and health data."""
        premium_selector = all_tier_selectors[ExtractionTier.PREMIUM]
        provider = premium_selector.get_provider_ids()[0]

        info = premium_selector.get_provider_info(provider)

        assert "provider_id" in info
        assert "is_local" in info
        assert "cost_input_per_m" in info
        assert "cost_output_per_m" in info
        assert "is_healthy" in info
        assert "available_in_tier" in info


# =============================================================================
# STATISTICS AND REPORTING TESTS
# =============================================================================


class TestStatisticsReporting:
    """Tests for statistics and reporting functionality."""

    def test_call_statistics_tracking(self):
        """Test that call statistics are tracked correctly."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Make some calls
        for i in range(3):
            call = LLMCallResult(
                provider_id="groq/llama-3.1-8b",
                model="llama-3.1-8b",
                content="test",
                tokens_input=1000 * (i + 1),
                tokens_output=500 * (i + 1),
                cost_usd=0.01 * (i + 1),
                latency_ms=100 * (i + 1),
                success=True,
            )
            selector.track_call(call)

        stats = selector.get_call_statistics()

        assert stats["total_calls"] == 3
        assert stats["successful_calls"] == 3
        assert stats["failed_calls"] == 0
        assert stats["total_cost_usd"] > 0
        assert stats["total_tokens"] > 0

    def test_cost_breakdown_by_provider(self):
        """Test cost breakdown by provider."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Calls to different providers
        call1 = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="test",
            cost_usd=0.10,
        )
        call2 = LLMCallResult(
            provider_id="alibaba/qwen-turbo",
            model="qwen-turbo",
            content="test",
            cost_usd=0.05,
        )

        selector.track_call(call1)
        selector.track_call(call2)

        breakdown = selector.get_cost_breakdown()

        assert "groq/llama-3.1-8b" in breakdown
        assert "alibaba/qwen-turbo" in breakdown
        assert breakdown["groq/llama-3.1-8b"] == 0.10
        assert breakdown["alibaba/qwen-turbo"] == 0.05

    def test_selector_serialization(self):
        """Test that selector state can be serialized."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Add some data
        call = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="test",
            cost_usd=0.05,
        )
        selector.track_call(call)

        data = selector.to_dict()

        assert "tier" in data
        assert "providers" in data
        assert "statistics" in data
        assert "health_status" in data

        # Should be JSON-serializable
        import json
        json_str = json.dumps(data, default=str)
        assert len(json_str) > 0


# =============================================================================
# EDGE CASES AND ERROR SCENARIOS
# =============================================================================


class TestEdgeCasesErrorScenarios:
    """Tests for edge cases and error scenarios."""

    def test_unknown_provider_cost_is_zero(self):
        """Test that unknown provider returns zero cost."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        cost = selector.calculate_cost("unknown/model", 1000, 500)
        assert cost == 0.0

    def test_provider_recovery_after_health_restoration(self):
        """Test that provider recovers after health is restored."""
        selector = create_tier_selector(ExtractionTier.STANDARD)
        provider = selector.get_provider_ids()[0]

        # Mark unhealthy
        for _ in range(4):
            selector.update_health(provider, is_healthy=False, error="Error")

        assert provider not in selector.get_healthy_providers()

        # Mark healthy again
        selector.update_health(provider, is_healthy=True, latency_ms=50)

        assert provider in selector.get_healthy_providers()

    def test_all_providers_unhealthy_fallback(self):
        """Test fallback when all providers are unhealthy."""
        selector = create_tier_selector(ExtractionTier.BASIC)

        # Mark all unhealthy
        for provider in selector.get_provider_ids():
            for _ in range(4):
                selector.update_health(provider, is_healthy=False)

        # Should still select a provider for analysis (fallback)
        selected = selector.select_provider_for_analysis("architecture")
        assert selected is not None

    def test_empty_cycle_assignments(self):
        """Test handling of cycles without assignments."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Cycle 4 is human review - no LLM assignments
        assignments = selector.get_providers_for_cycle(4)
        assert assignments == []
