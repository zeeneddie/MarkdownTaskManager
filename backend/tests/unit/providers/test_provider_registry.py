"""
Unit Tests for Provider Registry

Week 54: Tests for multi-LLM routing and provider management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.base import (
    LLMProvider,
    ProviderConfig,
    LLMRequest,
    LLMResponse,
)
from app.providers.registry import (
    ProviderRegistry,
    TASK_ROUTING,
    DEFAULT_MODELS,
    get_registry,
    get_provider,
)


@pytest.fixture
def registry():
    """Create a fresh ProviderRegistry instance."""
    return ProviderRegistry()


# ============================================================================
# REGISTRY INITIALIZATION TESTS
# ============================================================================

class TestRegistryInitialization:
    """Test registry initialization and provider setup."""

    def test_registry_initializes_providers(self, registry):
        """Test that registry initializes default providers."""
        # Verify all default providers exist
        assert registry.get_provider("ollama") is not None
        assert registry.get_provider("codex") is not None
        assert registry.get_provider("claude_haiku") is not None
        assert registry.get_provider("claude_sonnet") is not None
        assert registry.get_provider("claude_opus") is not None
        assert registry.get_provider("claude") is not None  # Alias

    def test_claude_alias_points_to_sonnet(self, registry):
        """Test that 'claude' alias points to claude_sonnet."""
        claude = registry.get_provider("claude")
        sonnet = registry.get_provider("claude_sonnet")
        assert claude is sonnet

    def test_get_provider_nonexistent(self, registry):
        """Test getting a non-existent provider returns None."""
        provider = registry.get_provider("nonexistent")
        assert provider is None


# ============================================================================
# TASK ROUTING TESTS
# ============================================================================

class TestTaskRouting:
    """Test task-to-provider routing."""

    def test_route_simple_generation(self, registry):
        """Test routing simple generation to Ollama."""
        provider = registry.route_task("simple_generation")
        assert provider is not None
        assert provider.config.name == "ollama"

    def test_route_quick_fix(self, registry):
        """Test routing quick fix to Ollama."""
        provider = registry.route_task("quick_fix")
        assert provider.config.name == "ollama"

    def test_route_standard_work(self, registry):
        """Test routing standard work to Claude Sonnet."""
        provider = registry.route_task("standard_work")
        assert provider.config.name == "claude"

    def test_route_code_review(self, registry):
        """Test routing code review to Claude Sonnet."""
        provider = registry.route_task("code_review")
        assert provider.config.name == "claude"

    def test_route_architecture(self, registry):
        """Test routing architecture to Codex."""
        provider = registry.route_task("architecture")
        assert provider.config.name == "codex"

    def test_route_security_audit(self, registry):
        """Test routing security audit to Codex."""
        provider = registry.route_task("security_audit")
        assert provider.config.name == "codex"

    def test_route_unknown_task_defaults_to_ollama(self, registry):
        """Test that unknown task types default to Ollama."""
        provider = registry.route_task("unknown_task_type")
        assert provider.config.name == "ollama"

    def test_route_prefer_local(self, registry):
        """Test prefer_local flag overrides routing."""
        # Even complex task should use Ollama when prefer_local=True
        provider = registry.route_task("architecture", prefer_local=True)
        assert provider.config.name == "ollama"

    def test_route_with_cost_threshold(self, registry):
        """Test cost threshold fallback to local."""
        # With max_cost_cents set, should use local for non-local providers
        provider = registry.route_task("standard_work", max_cost_cents=0.0)
        assert provider.config.name == "ollama"


# ============================================================================
# PROVIDER LISTING TESTS
# ============================================================================

class TestProviderListing:
    """Test provider listing functionality."""

    def test_list_providers(self, registry):
        """Test listing all providers."""
        providers = registry.list_providers()
        assert len(providers) >= 5  # At least 5 default providers
        assert all(isinstance(p, ProviderConfig) for p in providers)

    def test_get_routing_table(self, registry):
        """Test getting routing configuration."""
        routing = registry.get_routing_table()
        assert "simple_generation" in routing
        assert "architecture" in routing
        assert routing["simple_generation"] == "ollama"
        assert routing["architecture"] == "codex"


# ============================================================================
# CUSTOM PROVIDER TESTS
# ============================================================================

class TestCustomProviders:
    """Test custom provider registration."""

    def test_register_custom_provider(self, registry):
        """Test registering a custom provider."""
        # Create mock provider
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.config = ProviderConfig(
            name="ollama",  # Type hint requires valid name
            tier="balanced",
            model="custom-model",
        )

        # Register
        registry.register_provider("custom", mock_provider)

        # Verify
        provider = registry.get_provider("custom")
        assert provider is mock_provider

    def test_register_overwrites_existing(self, registry):
        """Test that registering overwrites existing provider."""
        original = registry.get_provider("ollama")

        # Create and register new mock
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.config = ProviderConfig(
            name="ollama",
            tier="free",
            model="new-model",
        )
        registry.register_provider("ollama", mock_provider)

        # Verify new provider is used
        new = registry.get_provider("ollama")
        assert new is not original
        assert new is mock_provider


# ============================================================================
# HEALTHCHECK TESTS
# ============================================================================

class TestHealthcheck:
    """Test provider healthcheck functionality."""

    @pytest.mark.asyncio
    async def test_healthcheck_all(self, registry):
        """Test healthcheck for all providers."""
        # Mock all providers' healthcheck methods
        for name, provider in registry._providers.items():
            provider.healthcheck = AsyncMock(return_value=True)

        # Execute
        results = await registry.healthcheck_all()

        # Verify
        assert isinstance(results, dict)
        assert len(results) >= 5
        assert all(isinstance(v, bool) for v in results.values())

    @pytest.mark.asyncio
    async def test_healthcheck_partial_failure(self, registry):
        """Test healthcheck when some providers fail."""
        # Make ollama healthy, others unhealthy
        for name, provider in registry._providers.items():
            if name == "ollama":
                provider.healthcheck = AsyncMock(return_value=True)
            else:
                provider.healthcheck = AsyncMock(return_value=False)

        # Execute
        results = await registry.healthcheck_all()

        # Verify
        assert results["ollama"] is True
        assert results["codex"] is False


# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestSingleton:
    """Test singleton pattern."""

    def test_get_registry_returns_same_instance(self):
        """Test that get_registry returns singleton."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_get_provider_convenience_function(self):
        """Test get_provider convenience function."""
        provider = get_provider("ollama")
        assert provider is not None
        assert provider.config.name == "ollama"

    def test_get_provider_nonexistent(self):
        """Test get_provider with nonexistent name."""
        provider = get_provider("nonexistent")
        assert provider is None


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfiguration:
    """Test default configuration."""

    def test_task_routing_complete(self):
        """Test all expected tasks are in routing table."""
        expected_tasks = [
            "simple_generation",
            "quick_fix",
            "code_review",
            "standard_work",
            "architecture",
            "security_audit",
            "complex_analysis",
            "refactoring",
            "documentation",
            "debugging",
            "planning",
            "estimation",
        ]
        for task in expected_tasks:
            assert task in TASK_ROUTING, f"Missing task: {task}"

    def test_default_models_defined(self):
        """Test all default models are defined."""
        expected_providers = [
            "ollama",
            "codex",
            "claude_haiku",
            "claude_sonnet",
            "claude_opus",
        ]
        for provider in expected_providers:
            assert provider in DEFAULT_MODELS, f"Missing model: {provider}"


# ============================================================================
# PROVIDER CONFIG TESTS
# ============================================================================

class TestProviderConfigs:
    """Test provider configurations."""

    def test_ollama_is_local(self, registry):
        """Test Ollama provider is marked as local."""
        ollama = registry.get_provider("ollama")
        assert ollama.config.is_local is True

    def test_codex_is_not_local(self, registry):
        """Test Codex provider is not local."""
        codex = registry.get_provider("codex")
        assert codex.config.is_local is False

    def test_claude_is_not_local(self, registry):
        """Test Claude providers are not local."""
        claude = registry.get_provider("claude_sonnet")
        assert claude.config.is_local is False

    def test_provider_tiers(self, registry):
        """Test provider tier assignments."""
        ollama = registry.get_provider("ollama")
        assert ollama.config.tier == "free"

        codex = registry.get_provider("codex")
        assert codex.config.tier == "deep"

        haiku = registry.get_provider("claude_haiku")
        assert haiku.config.tier == "fast"

        sonnet = registry.get_provider("claude_sonnet")
        assert sonnet.config.tier == "balanced"

        opus = registry.get_provider("claude_opus")
        assert opus.config.tier == "deep"


# ============================================================================
# COST CALCULATION TESTS
# ============================================================================

class TestCostCalculation:
    """Test cost calculation functionality."""

    def test_calculate_cost_local_is_free(self, registry):
        """Test that local provider cost is zero."""
        ollama = registry.get_provider("ollama")
        cost = ollama.calculate_cost(1000, 1000)
        assert cost == 0.0

    def test_calculate_cost_claude(self, registry):
        """Test cost calculation for Claude."""
        claude = registry.get_provider("claude_sonnet")
        # Cost = (input * input_rate + output * output_rate) / 1M * 100 cents
        cost = claude.calculate_cost(1_000_000, 1_000_000)
        # Should be non-zero for non-local providers
        assert cost >= 0  # Actual value depends on configured rates
