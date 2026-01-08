"""
Test Deep Extraction Cycles 1 & 2 - Week 83

Tests for the 5-cycle extraction pipeline:
- Cycle 1: Independent Analysis
- Cycle 2: Cross-Enrichment

Uses mocked LLM responses to test the pipeline logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
import json

from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    RunStatus,
    TIER_CONFIG,
)
from app.services.tier_provider_selector import (
    TierProviderSelector,
    LLMCallResult,
    create_tier_selector,
    compare_tiers,
    PROVIDER_COSTS,
)
from app.services.extraction_llm_adapter import (
    ExtractionLLMAdapter,
    ExtractionPrompts,
    create_extraction_adapter,
)


# ============================================================================
# TIER PROVIDER SELECTOR TESTS
# ============================================================================

class TestTierProviderSelector:
    """Test the tier-aware provider selection."""

    def test_create_free_tier_selector(self):
        """FREE tier should only have Ollama providers."""
        selector = create_tier_selector(ExtractionTier.FREE)
        providers = selector.get_provider_ids()

        # FREE tier should have 3 Ollama models
        assert len(providers) == 3
        for provider in providers:
            assert provider.startswith("ollama/")

    def test_create_standard_tier_selector(self):
        """STANDARD tier should have multiple providers."""
        selector = create_tier_selector(ExtractionTier.STANDARD)
        providers = selector.get_provider_ids()

        # STANDARD tier should have at least 5 providers
        assert len(providers) >= 5

        # Should include multiple providers
        provider_types = set(p.split("/")[0] for p in providers)
        assert "ollama" in provider_types  # Local
        assert "groq" in provider_types    # Fast

    def test_create_premium_tier_selector(self):
        """PREMIUM tier should have more providers than STANDARD."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        providers = selector.get_provider_ids()

        # PREMIUM tier should have more providers
        assert len(providers) >= 5

        # Get standard for comparison
        standard_selector = create_tier_selector(ExtractionTier.STANDARD)
        standard_providers = standard_selector.get_provider_ids()

        # Premium should have at least as many as standard
        assert len(providers) >= len(standard_providers)

    def test_tier_price_configuration(self):
        """Verify tier prices match configuration."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # STANDARD tier price and confidence target
        assert selector.get_price_usd() == 15.0
        assert selector.get_confidence_target() == 0.80

    def test_cycle_provider_assignment(self):
        """Test that providers are assigned to correct cycles."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Cycle 1 should have multiple analysis types
        cycle_1_assignments = selector.get_providers_for_cycle(1)
        assert len(cycle_1_assignments) > 0

        # Each assignment should be (provider_id, analysis_type)
        for provider_id, analysis_type in cycle_1_assignments:
            assert "/" in provider_id
            assert analysis_type in ["architecture", "business_logic", "security", "code_structure"]

    def test_cost_tracking(self):
        """Test cost tracking for LLM calls."""
        selector = create_tier_selector(ExtractionTier.BASIC)

        # Track a call
        result = LLMCallResult(
            provider_id="ollama/qwen2.5-coder:7b",
            model="qwen2.5-coder:7b",
            content="Test response",
            tokens_input=100,
            tokens_output=200,
            latency_ms=1500,
            cost_usd=0.0,  # Ollama is free
            success=True,
        )
        selector.track_call(result)

        stats = selector.get_call_statistics()
        assert stats["total_calls"] == 1
        assert stats["total_tokens"] == 300  # 100 + 200

    def test_tier_comparison(self):
        """Test comparing all tiers."""
        comparison = compare_tiers()

        assert len(comparison) == 5  # FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM

        # Verify ascending prices
        prices = [t["price_usd"] for t in comparison]
        assert prices == sorted(prices)  # Should be ascending

        # Verify ascending confidence targets
        confidences = [t["confidence_target"] for t in comparison]
        assert confidences == sorted(confidences)  # Should be ascending

    def test_upgrade_tier(self):
        """Test tier upgrade with credit calculation."""
        selector = create_tier_selector(ExtractionTier.BASIC)

        # Upgrade from BASIC to STANDARD
        upgrade_info = selector.upgrade_tier(ExtractionTier.STANDARD)

        assert upgrade_info["old_tier"] == "BASIC"  # Uppercase enum value
        assert upgrade_info["new_tier"] == "STANDARD"
        assert upgrade_info["credit_usd"] == 5.0  # BASIC price
        assert upgrade_info["amount_to_charge_usd"] == 10.0  # STANDARD - BASIC = 15 - 5


# ============================================================================
# EXTRACTION PROMPTS TESTS
# ============================================================================

class TestExtractionPrompts:
    """Test extraction prompt generation."""

    def test_architecture_prompt(self):
        """Test architecture analysis prompt."""
        code_summary = "Test project with 10 files"
        file_list = ["src/main.py", "src/models/user.py"]

        prompt = ExtractionPrompts.get_architecture_prompt(code_summary, file_list)

        assert "ARCHITECTURE" in prompt
        assert "Test project" in prompt
        assert "src/main.py" in prompt
        assert "epics" in prompt  # Output schema

    def test_business_logic_prompt(self):
        """Test business logic analysis prompt."""
        code_summary = "E-commerce platform"
        file_list = ["src/cart.py", "src/checkout.py"]

        prompt = ExtractionPrompts.get_business_logic_prompt(code_summary, file_list)

        assert "BUSINESS LOGIC" in prompt
        assert "user-facing features" in prompt.lower()

    def test_security_prompt(self):
        """Test security analysis prompt."""
        code_summary = "API backend"
        file_list = ["src/auth.py", "src/api.py"]

        prompt = ExtractionPrompts.get_security_prompt(code_summary, file_list)

        assert "SECURITY" in prompt
        assert "vulnerabilities" in prompt.lower()

    def test_enrichment_prompt(self):
        """Test cross-enrichment prompt."""
        original_analysis = {
            "epics": [{"title": "User Auth", "description": "Handle login"}]
        }

        prompt = ExtractionPrompts.get_enrichment_prompt(original_analysis, "architecture")

        assert "architecture" in prompt.lower()
        assert "User Auth" in prompt
        assert "additions" in prompt.lower()
        assert "modifications" in prompt.lower()


# ============================================================================
# EXTRACTION LLM ADAPTER TESTS
# ============================================================================

class TestExtractionLLMAdapter:
    """Test the unified LLM adapter."""

    def test_create_adapter(self):
        """Test adapter creation."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = create_extraction_adapter(selector)

        assert adapter is not None
        assert adapter.selector is selector

    def test_parse_json_clean(self):
        """Test parsing clean JSON."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        content = '{"epics": [{"title": "Test"}]}'
        success, parsed = adapter.parse_json_response(content)

        assert success is True
        assert parsed["epics"][0]["title"] == "Test"

    def test_parse_json_markdown_wrapped(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        content = '''Here is the analysis:
```json
{"epics": [{"title": "Test Epic"}]}
```
That's the result.'''

        success, parsed = adapter.parse_json_response(content)

        assert success is True
        assert parsed["epics"][0]["title"] == "Test Epic"

    def test_parse_json_invalid(self):
        """Test parsing invalid JSON."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        content = "This is not JSON at all"
        success, error = adapter.parse_json_response(content)

        assert success is False
        assert "Could not parse" in error

    def test_parse_json_empty(self):
        """Test parsing empty content."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        success, error = adapter.parse_json_response("")

        assert success is False
        assert error == "Empty response"

    @pytest.mark.asyncio
    async def test_call_llm_invalid_provider(self):
        """Test calling with invalid provider format."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        result = await adapter.call_llm("invalid", "test prompt")

        assert result.success is False
        assert "Invalid provider_id format" in result.error

        await adapter.close()

    @pytest.mark.asyncio
    async def test_call_llm_unknown_provider(self):
        """Test calling with unknown provider."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        result = await adapter.call_llm("unknown/model", "test prompt")

        assert result.success is False
        assert "Unknown provider" in result.error

        await adapter.close()


# ============================================================================
# MOCK LLM RESPONSE FIXTURES
# ============================================================================

MOCK_ARCHITECTURE_RESPONSE = json.dumps({
    "epics": [
        {
            "title": "User Management System",
            "description": "Handle user registration and authentication",
            "business_value": "Essential for user access control",
            "estimated_complexity": "medium",
            "features": ["Login", "Registration", "Password Reset"]
        },
        {
            "title": "Task Management",
            "description": "Core task tracking functionality",
            "business_value": "Primary product value",
            "estimated_complexity": "high",
            "features": ["Create Task", "Edit Task", "Delete Task", "Task Lists"]
        }
    ],
    "architecture_notes": {
        "patterns": ["MVC", "Repository Pattern"],
        "layers": ["Presentation", "Business Logic", "Data Access"],
        "key_components": ["TaskController", "TaskService", "TaskRepository"]
    }
})

MOCK_BUSINESS_LOGIC_RESPONSE = json.dumps({
    "features": [
        {
            "title": "User Registration",
            "description": "Allow new users to create accounts",
            "user_type": "End User",
            "priority": "high",
            "stories": [
                {"title": "Register with email", "estimated_points": 3, "acceptance_criteria": ["Email validation", "Password strength"]}
            ]
        }
    ]
})

MOCK_ENRICHMENT_RESPONSE = json.dumps({
    "additions": [
        {
            "item_type": "feature",
            "item": {
                "title": "Two-Factor Authentication",
                "description": "Add 2FA for enhanced security"
            }
        }
    ],
    "modifications": [
        {
            "original_title": "User Management System",
            "suggested_changes": {
                "estimated_complexity": "high"
            },
            "reasoning": "2FA adds complexity"
        }
    ],
    "concerns": [],
    "confidence_adjustments": {
        "User Management System": 0.85
    }
})


# ============================================================================
# DEEP EXTRACTION SERVICE CYCLE TESTS
# ============================================================================

class TestDeepExtractionCycle1:
    """Test Cycle 1: Independent Analysis."""

    @pytest.mark.asyncio
    async def test_cycle_1_parallel_calls(self):
        """Test that Cycle 1 makes parallel LLM calls."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        # Mock the call_llm method
        call_count = 0
        async def mock_call_llm(provider_id, prompt, system=None, timeout=300):
            nonlocal call_count
            call_count += 1
            return LLMCallResult(
                provider_id=provider_id,
                model=provider_id.split("/")[1],
                content=MOCK_ARCHITECTURE_RESPONSE,
                tokens_input=100,
                tokens_output=500,
                latency_ms=1500,
                cost_usd=0.0,
                success=True,
            )

        adapter.call_llm = mock_call_llm

        # Make parallel calls
        calls = [
            ("ollama/qwen2.5-coder:7b", "test prompt 1", "architecture"),
            ("ollama/deepseek-r1", "test prompt 2", "business_logic"),
            ("ollama/codellama", "test prompt 3", "security"),
        ]

        results = await adapter.call_llms_parallel(calls)

        # Should have made 3 calls
        assert call_count == 3
        assert len(results) == 3

        # All should be successful
        for analysis_type, result in results:
            assert result.success is True
            assert analysis_type in ["architecture", "business_logic", "security"]

        await adapter.close()

    @pytest.mark.asyncio
    async def test_cycle_1_handles_failures(self):
        """Test that Cycle 1 handles LLM failures gracefully."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        # Mock with one failure
        call_index = 0
        async def mock_call_llm(provider_id, prompt, system=None, timeout=300):
            nonlocal call_index
            call_index += 1
            if call_index == 2:  # Second call fails
                return LLMCallResult(
                    provider_id=provider_id,
                    model=provider_id.split("/")[1],
                    content="",
                    success=False,
                    error="Connection timeout"
                )
            return LLMCallResult(
                provider_id=provider_id,
                model=provider_id.split("/")[1],
                content=MOCK_ARCHITECTURE_RESPONSE,
                tokens_input=100,
                tokens_output=500,
                latency_ms=1500,
                cost_usd=0.0,
                success=True,
            )

        adapter.call_llm = mock_call_llm

        calls = [
            ("ollama/qwen2.5-coder:7b", "prompt 1", "architecture"),
            ("ollama/deepseek-r1", "prompt 2", "business_logic"),
        ]

        results = await adapter.call_llms_parallel(calls)

        # Should have 2 results
        assert len(results) == 2

        # One should be successful, one failed
        successes = sum(1 for _, r in results if r.success)
        failures = sum(1 for _, r in results if not r.success)
        assert successes == 1
        assert failures == 1

        await adapter.close()


class TestDeepExtractionCycle2:
    """Test Cycle 2: Cross-Enrichment."""

    @pytest.mark.asyncio
    async def test_cycle_2_enrichment(self):
        """Test cross-enrichment between LLM outputs."""
        selector = create_tier_selector(ExtractionTier.FREE)
        adapter = ExtractionLLMAdapter(selector)

        # Mock call_llm for enrichment
        async def mock_call_llm(provider_id, prompt, system=None, timeout=300):
            return LLMCallResult(
                provider_id=provider_id,
                model=provider_id.split("/")[1],
                content=MOCK_ENRICHMENT_RESPONSE,
                tokens_input=150,
                tokens_output=400,
                latency_ms=2000,
                cost_usd=0.0,
                success=True,
            )

        adapter.call_llm = mock_call_llm

        # Run enrichment
        original_analysis = json.loads(MOCK_ARCHITECTURE_RESPONSE)
        result, enrichment_data = await adapter.run_enrichment(
            reviewer_provider_id="ollama/deepseek-r1",
            original_analysis=original_analysis,
            original_analysis_type="architecture",
        )

        assert result.success is True
        assert enrichment_data is not None
        assert "additions" in enrichment_data
        assert len(enrichment_data["additions"]) > 0

        # Check addition content
        addition = enrichment_data["additions"][0]
        assert addition["item_type"] == "feature"
        assert "Two-Factor Authentication" in addition["item"]["title"]

        await adapter.close()

    @pytest.mark.asyncio
    async def test_cycle_2_multiple_reviewers(self):
        """Test that multiple reviewers can enrich the same analysis."""
        selector = create_tier_selector(ExtractionTier.BASIC)  # Has more providers
        providers = selector.get_provider_ids()

        # Filter for different providers
        original_provider = providers[0]
        reviewer_candidates = [p for p in providers if p != original_provider]

        # Should have multiple reviewers available
        assert len(reviewer_candidates) >= 2


# ============================================================================
# INTEGRATION TESTS (with mocked database)
# ============================================================================

class TestDeepExtractionIntegration:
    """Integration tests for the full pipeline."""

    def test_provider_costs_defined(self):
        """Verify all expected providers have cost definitions."""
        expected_providers = [
            "ollama/qwen2.5-coder:7b",
            "ollama/deepseek-r1",
            "groq/llama-3.1-8b",
            "google/gemini-2.5-flash",
        ]

        for provider in expected_providers:
            assert provider in PROVIDER_COSTS, f"Missing cost for {provider}"

    def test_tier_configs_complete(self):
        """Verify all tier configurations are complete."""
        for tier in ExtractionTier:
            assert tier in TIER_CONFIG, f"Missing config for {tier}"

            config = TIER_CONFIG[tier]
            assert "llms" in config  # Provider list
            assert "price_usd" in config
            assert "confidence_target" in config
            assert "human_review" in config

    def test_analysis_types_coverage(self):
        """Verify all analysis types have prompts."""
        analysis_types = ["architecture", "business_logic", "security", "code_structure"]

        code_summary = "Test project"
        file_list = ["test.py"]

        for analysis_type in analysis_types:
            prompt_method = getattr(ExtractionPrompts, f"get_{analysis_type}_prompt", None)
            assert prompt_method is not None, f"Missing prompt for {analysis_type}"

            prompt = prompt_method(code_summary, file_list)
            assert len(prompt) > 100  # Should be a substantial prompt
            assert "JSON" in prompt or "json" in prompt  # Should request JSON output


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
