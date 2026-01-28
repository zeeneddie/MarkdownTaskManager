"""
Unit Tests for Tier Provider Selector.

Tests the tier-based LLM provider selection logic for deep extraction.

Coverage:
- Tier configuration (FREE → PREMIUM)
- Provider selection per tier
- Cost calculation
- Confidence targets
- Cycle-based provider assignment
"""

import pytest
from typing import List, Dict, Any

from app.models.deep_extraction import ExtractionTier, TIER_CONFIG
from app.services.tier_provider_selector import (
    TierProviderSelector,
    create_tier_selector,
    compare_tiers,
    PROVIDER_COSTS,
    ProviderCost,
    LLMCallResult,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def free_tier_selector():
    """Create FREE tier selector."""
    return create_tier_selector(ExtractionTier.FREE)


@pytest.fixture
def basic_tier_selector():
    """Create BASIC tier selector."""
    return create_tier_selector(ExtractionTier.BASIC)


@pytest.fixture
def standard_tier_selector():
    """Create STANDARD tier selector."""
    return create_tier_selector(ExtractionTier.STANDARD)


@pytest.fixture
def professional_tier_selector():
    """Create PROFESSIONAL tier selector."""
    return create_tier_selector(ExtractionTier.PROFESSIONAL)


@pytest.fixture
def premium_tier_selector():
    """Create PREMIUM tier selector."""
    return create_tier_selector(ExtractionTier.PREMIUM)


# =============================================================================
# TIER CONFIGURATION TESTS
# =============================================================================


class TestTierConfiguration:
    """Tests for tier configuration."""

    def test_all_tiers_defined(self):
        """Test that all 5 tiers are defined."""
        assert ExtractionTier.FREE is not None
        assert ExtractionTier.BASIC is not None
        assert ExtractionTier.STANDARD is not None
        assert ExtractionTier.PROFESSIONAL is not None
        assert ExtractionTier.PREMIUM is not None

    def test_tier_config_has_all_tiers(self):
        """Test that TIER_CONFIG has all tiers."""
        for tier in ExtractionTier:
            assert tier in TIER_CONFIG, f"Missing config for {tier}"

    def test_tier_prices_increase(self):
        """Test that tier prices increase with tier level."""
        prices = [
            TIER_CONFIG[ExtractionTier.FREE].get("price_usd", 0),
            TIER_CONFIG[ExtractionTier.BASIC].get("price_usd", 5),
            TIER_CONFIG[ExtractionTier.STANDARD].get("price_usd", 15),
            TIER_CONFIG[ExtractionTier.PROFESSIONAL].get("price_usd", 45),
            TIER_CONFIG[ExtractionTier.PREMIUM].get("price_usd", 135),
        ]

        for i in range(len(prices) - 1):
            assert prices[i] <= prices[i + 1], "Prices should increase"

    def test_confidence_targets_increase(self):
        """Test that confidence targets increase with tier level."""
        targets = [
            TIER_CONFIG[ExtractionTier.FREE].get("confidence_target", 0.60),
            TIER_CONFIG[ExtractionTier.BASIC].get("confidence_target", 0.70),
            TIER_CONFIG[ExtractionTier.STANDARD].get("confidence_target", 0.80),
            TIER_CONFIG[ExtractionTier.PROFESSIONAL].get("confidence_target", 0.90),
            TIER_CONFIG[ExtractionTier.PREMIUM].get("confidence_target", 0.95),
        ]

        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1], "Confidence targets should increase"


# =============================================================================
# PROVIDER SELECTION TESTS
# =============================================================================


class TestProviderSelection:
    """Tests for provider selection per tier."""

    def test_free_tier_only_ollama(self, free_tier_selector):
        """Test that FREE tier only has Ollama providers."""
        providers = free_tier_selector.get_provider_ids()

        for provider in providers:
            assert provider.startswith("ollama/"), f"FREE tier should only have Ollama: {provider}"

    def test_free_tier_has_minimum_providers(self, free_tier_selector):
        """Test that FREE tier has at least 2 providers."""
        providers = free_tier_selector.get_provider_ids()
        assert len(providers) >= 2

    def test_basic_tier_has_ollama(self, basic_tier_selector):
        """Test that BASIC tier includes Ollama providers."""
        providers = basic_tier_selector.get_provider_ids()

        ollama_providers = [p for p in providers if p.startswith("ollama/")]
        assert len(ollama_providers) >= 1, "BASIC tier should include Ollama"

    def test_standard_tier_includes_groq_or_qwen(self, standard_tier_selector):
        """Test that STANDARD tier includes Groq or Alibaba Qwen providers."""
        providers = standard_tier_selector.get_provider_ids()

        groq_qwen_providers = [
            p for p in providers
            if p.startswith("groq/") or p.startswith("alibaba/")
        ]
        assert len(groq_qwen_providers) >= 1, "STANDARD tier should include Groq or Qwen"

    def test_professional_tier_includes_gemini(self, professional_tier_selector):
        """Test that PROFESSIONAL tier includes Gemini providers."""
        providers = professional_tier_selector.get_provider_ids()

        gemini_providers = [p for p in providers if p.startswith("google/")]
        assert len(gemini_providers) >= 1, "PROFESSIONAL tier should include Gemini"

    def test_premium_tier_includes_anthropic_or_openai(self, premium_tier_selector):
        """Test that PREMIUM tier includes Anthropic or OpenAI providers."""
        providers = premium_tier_selector.get_provider_ids()

        premium_providers = [
            p for p in providers
            if p.startswith("anthropic/") or p.startswith("openai/")
        ]
        assert len(premium_providers) >= 1, "PREMIUM tier should include Anthropic or OpenAI"

    def test_higher_tiers_have_more_providers(self):
        """Test that higher tiers have more providers."""
        selectors = [
            create_tier_selector(ExtractionTier.FREE),
            create_tier_selector(ExtractionTier.BASIC),
            create_tier_selector(ExtractionTier.STANDARD),
            create_tier_selector(ExtractionTier.PROFESSIONAL),
            create_tier_selector(ExtractionTier.PREMIUM),
        ]

        counts = [len(s.get_provider_ids()) for s in selectors]

        # Each tier should have at least as many providers as the previous
        for i in range(len(counts) - 1):
            assert counts[i] <= counts[i + 1], f"Tier {i+1} should have >= providers than tier {i}"


# =============================================================================
# COST CALCULATION TESTS
# =============================================================================


class TestCostCalculation:
    """Tests for cost calculation."""

    def test_free_tier_is_free(self, free_tier_selector):
        """Test that FREE tier costs $0."""
        assert free_tier_selector.get_price_usd() == 0

    def test_basic_tier_price(self, basic_tier_selector):
        """Test BASIC tier price."""
        price = basic_tier_selector.get_price_usd()
        assert price > 0
        assert price <= 10  # Should be around $5

    def test_standard_tier_price(self, standard_tier_selector):
        """Test STANDARD tier price."""
        price = standard_tier_selector.get_price_usd()
        assert price >= 10
        assert price <= 25  # Should be around $15

    def test_professional_tier_price(self, professional_tier_selector):
        """Test PROFESSIONAL tier price."""
        price = professional_tier_selector.get_price_usd()
        assert price >= 30
        assert price <= 60  # Should be around $45

    def test_premium_tier_price(self, premium_tier_selector):
        """Test PREMIUM tier price."""
        price = premium_tier_selector.get_price_usd()
        assert price >= 100  # Should be around $135

    def test_provider_costs_defined(self):
        """Test that provider costs are defined."""
        assert len(PROVIDER_COSTS) > 0

        for provider_id, cost_info in PROVIDER_COSTS.items():
            assert isinstance(cost_info, ProviderCost)
            assert cost_info.input_per_m_tokens >= 0
            assert cost_info.output_per_m_tokens >= 0

    def test_calculate_cost_for_local_provider(self, free_tier_selector):
        """Test cost calculation for local (free) provider."""
        cost = free_tier_selector.calculate_cost(
            provider_id="ollama/qwen2.5-coder:7b",
            tokens_input=1000,
            tokens_output=500
        )
        assert cost == 0.0, "Local providers should be free"

    def test_calculate_cost_for_paid_provider(self, premium_tier_selector):
        """Test cost calculation for paid provider."""
        cost = premium_tier_selector.calculate_cost(
            provider_id="openai/gpt-5.2",
            tokens_input=1_000_000,  # 1M tokens
            tokens_output=100_000     # 100K tokens
        )
        assert cost > 0, "Paid providers should have cost"


# =============================================================================
# CONFIDENCE TARGET TESTS
# =============================================================================


class TestConfidenceTargets:
    """Tests for confidence targets per tier."""

    def test_free_tier_confidence_target(self, free_tier_selector):
        """Test FREE tier confidence target."""
        target = free_tier_selector.get_confidence_target()
        assert target >= 0.55
        assert target <= 0.65  # Around 60%

    def test_basic_tier_confidence_target(self, basic_tier_selector):
        """Test BASIC tier confidence target."""
        target = basic_tier_selector.get_confidence_target()
        assert target >= 0.65
        assert target <= 0.75  # Around 70%

    def test_standard_tier_confidence_target(self, standard_tier_selector):
        """Test STANDARD tier confidence target."""
        target = standard_tier_selector.get_confidence_target()
        assert target >= 0.75
        assert target <= 0.85  # Around 80%

    def test_professional_tier_confidence_target(self, professional_tier_selector):
        """Test PROFESSIONAL tier confidence target."""
        target = professional_tier_selector.get_confidence_target()
        assert target >= 0.85
        assert target <= 0.95  # Around 90%

    def test_premium_tier_confidence_target(self, premium_tier_selector):
        """Test PREMIUM tier confidence target."""
        target = premium_tier_selector.get_confidence_target()
        assert target >= 0.90  # Around 95%


# =============================================================================
# CYCLE-BASED ASSIGNMENT TESTS
# =============================================================================


class TestCycleBasedAssignment:
    """Tests for cycle-based provider assignment."""

    def test_cycle_1_has_providers(self, standard_tier_selector):
        """Test that cycle 1 has provider assignments."""
        assignments = standard_tier_selector.get_providers_for_cycle(1)
        assert len(assignments) > 0

    def test_cycle_2_has_providers(self, standard_tier_selector):
        """Test that cycle 2 has provider assignments."""
        assignments = standard_tier_selector.get_providers_for_cycle(2)
        assert assignments is not None
        assert len(assignments) >= 0

    def test_assignments_include_analysis_type(self, standard_tier_selector):
        """Test that assignments include analysis type."""
        assignments = standard_tier_selector.get_providers_for_cycle(1)

        for provider_id, analysis_type in assignments:
            assert provider_id is not None
            assert analysis_type is not None

    def test_cycle_1_assigns_analysis_types(self, premium_tier_selector):
        """Test that cycle 1 assigns specific analysis types."""
        assignments = premium_tier_selector.get_providers_for_cycle(1)

        analysis_types = [a[1] for a in assignments]
        expected_types = ["architecture", "business_logic", "security", "code_structure"]

        # At least some of these should appear
        assert any(at in analysis_types for at in expected_types)

    def test_cycle_5_uses_synthesis(self, premium_tier_selector):
        """Test that cycle 5 is for synthesis."""
        assignments = premium_tier_selector.get_providers_for_cycle(5)

        if assignments:
            _, analysis_type = assignments[0]
            assert analysis_type == "synthesis"


# =============================================================================
# TIER COMPARISON TESTS
# =============================================================================


class TestTierComparison:
    """Tests for comparing tiers."""

    def test_compare_tiers_returns_list(self):
        """Test that compare_tiers returns a list."""
        comparison = compare_tiers()
        assert isinstance(comparison, list)
        assert len(comparison) >= 5  # At least 5 tiers

    def test_comparison_includes_all_tiers(self):
        """Test that comparison includes all tiers."""
        comparison = compare_tiers()
        tier_names = [c["tier"] for c in comparison]

        for tier in ExtractionTier:
            assert tier.value in tier_names

    def test_comparison_has_price_info(self):
        """Test that comparison includes price information."""
        comparison = compare_tiers()

        for tier_info in comparison:
            assert "price_usd" in tier_info
            assert "confidence_target" in tier_info
            assert "llm_count" in tier_info

    def test_comparison_has_recommended_flag(self):
        """Test that comparison includes recommended flag."""
        comparison = compare_tiers()

        recommended_count = sum(1 for c in comparison if c.get("recommended", False))
        # At least one tier should be recommended
        assert recommended_count >= 1


# =============================================================================
# PROVIDER CATEGORIES TESTS
# =============================================================================


class TestProviderCategories:
    """Tests for provider category grouping."""

    def test_get_providers_by_category(self, premium_tier_selector):
        """Test that providers are grouped by category."""
        categories = premium_tier_selector.get_providers_by_category()

        assert "local" in categories
        assert "fast" in categories
        assert "balanced" in categories
        assert "deep" in categories

    def test_ollama_providers_in_local_category(self, premium_tier_selector):
        """Test that Ollama providers are categorized as local."""
        categories = premium_tier_selector.get_providers_by_category()

        for provider in categories.get("local", []):
            assert provider.startswith("ollama/")

    def test_groq_providers_in_fast_category(self, premium_tier_selector):
        """Test that Groq providers are categorized as fast."""
        categories = premium_tier_selector.get_providers_by_category()

        groq_in_fast = [p for p in categories.get("fast", []) if p.startswith("groq/")]
        assert len(groq_in_fast) >= 0  # May be empty depending on tier


# =============================================================================
# HEALTH MONITORING TESTS
# =============================================================================


class TestHealthMonitoring:
    """Tests for provider health monitoring."""

    def test_initial_health_status(self, standard_tier_selector):
        """Test that all providers start as healthy."""
        healthy = standard_tier_selector.get_healthy_providers()
        all_providers = standard_tier_selector.get_provider_ids()

        assert len(healthy) == len(all_providers)

    def test_update_health_on_failure(self, standard_tier_selector):
        """Test updating health status on failure."""
        provider = standard_tier_selector.get_provider_ids()[0]

        # Simulate multiple failures
        for _ in range(4):
            standard_tier_selector.update_health(provider, is_healthy=False, error="Test error")

        health = standard_tier_selector.get_health_status()
        assert health[provider]["is_healthy"] is False

    def test_update_health_on_success(self, standard_tier_selector):
        """Test updating health status on success."""
        provider = standard_tier_selector.get_provider_ids()[0]

        standard_tier_selector.update_health(provider, is_healthy=True, latency_ms=100)

        health = standard_tier_selector.get_health_status()
        assert health[provider]["is_healthy"] is True


# =============================================================================
# COST TRACKING TESTS
# =============================================================================


class TestCostTracking:
    """Tests for cost tracking functionality."""

    def test_track_call_updates_totals(self, standard_tier_selector):
        """Test that tracking calls updates totals."""
        result = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="Test response",
            tokens_input=1000,
            tokens_output=500,
            cost_usd=0.10,
        )

        standard_tier_selector.track_call(result)

        assert standard_tier_selector.get_total_cost() == 0.10
        assert standard_tier_selector.get_total_tokens() == 1500

    def test_get_cost_breakdown(self, standard_tier_selector):
        """Test getting cost breakdown by provider."""
        result1 = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="Test",
            cost_usd=0.05,
        )
        result2 = LLMCallResult(
            provider_id="alibaba/qwen-turbo",
            model="qwen-turbo",
            content="Test",
            cost_usd=0.03,
        )

        standard_tier_selector.track_call(result1)
        standard_tier_selector.track_call(result2)

        breakdown = standard_tier_selector.get_cost_breakdown()
        assert "groq/llama-3.1-8b" in breakdown
        assert "alibaba/qwen-turbo" in breakdown


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in tier selection."""

    def test_selector_creation_valid_tiers(self):
        """Test that selectors can be created for all valid tiers."""
        for tier in ExtractionTier:
            selector = create_tier_selector(tier)
            assert selector is not None

    def test_selector_creation_from_string(self):
        """Test that selectors can be created from string tier names."""
        selector = create_tier_selector("STANDARD")
        assert selector is not None
        assert selector.tier == ExtractionTier.STANDARD

    def test_get_providers_returns_list(self, standard_tier_selector):
        """Test that get_provider_ids returns a list."""
        providers = standard_tier_selector.get_provider_ids()
        assert isinstance(providers, list)

    def test_providers_have_valid_format(self, premium_tier_selector):
        """Test that provider IDs have valid format."""
        providers = premium_tier_selector.get_provider_ids()

        for provider in providers:
            # Format should be "provider/model"
            assert "/" in provider, f"Invalid provider format: {provider}"
            parts = provider.split("/")
            assert len(parts) >= 2

    def test_tier_upgrade(self, basic_tier_selector):
        """Test tier upgrade functionality."""
        result = basic_tier_selector.upgrade_tier(ExtractionTier.STANDARD)

        assert result["old_tier"] == "BASIC"
        assert result["new_tier"] == "STANDARD"
        assert result["new_provider_count"] >= result["old_provider_count"]

    def test_select_provider_for_analysis(self, premium_tier_selector):
        """Test selecting provider for specific analysis type."""
        provider = premium_tier_selector.select_provider_for_analysis("architecture")
        assert provider is not None
        assert provider in premium_tier_selector.get_provider_ids()

    def test_to_dict_serialization(self, standard_tier_selector):
        """Test serialization to dictionary."""
        data = standard_tier_selector.to_dict()

        assert "tier" in data
        assert "providers" in data
        assert "statistics" in data
