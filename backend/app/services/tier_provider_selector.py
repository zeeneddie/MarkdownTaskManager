"""
Tier-Aware Provider Selector - Week 82

Selects LLM providers based on customer extraction tier.
Each tier has access to progressively more (and better) LLMs.

Tiers:
- FREE: 3 LLMs (Ollama only) - $0
- BASIC: 5 LLMs (+Groq, Qwen) - $5
- STANDARD: 7 LLMs (+Gemini) - $25
- PROFESSIONAL: 9 LLMs (+GPT-5.2) - $75
- PREMIUM: 10 LLMs (+Claude Opus) - $150
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio
import logging

from app.models.deep_extraction import ExtractionTier, TIER_CONFIG


logger = logging.getLogger(__name__)


# ============================================================================
# PROVIDER COST CONFIGURATION
# ============================================================================

@dataclass
class ProviderCost:
    """Cost configuration for a provider."""
    input_per_m_tokens: float  # Cost per million input tokens in USD
    output_per_m_tokens: float  # Cost per million output tokens in USD
    is_local: bool = False  # Local providers have no cost


# Provider costs (USD per million tokens)
PROVIDER_COSTS: Dict[str, ProviderCost] = {
    # Local (FREE)
    "ollama/qwen2.5-coder:7b": ProviderCost(0.0, 0.0, is_local=True),
    "ollama/deepseek-r1": ProviderCost(0.0, 0.0, is_local=True),
    "ollama/codellama": ProviderCost(0.0, 0.0, is_local=True),

    # Groq (very cheap, fast)
    "groq/llama-3.1-8b": ProviderCost(0.05, 0.08),
    "groq/llama-3.3-70b": ProviderCost(0.59, 0.79),
    "groq/qwen3-32b": ProviderCost(0.10, 0.15),

    # Alibaba Qwen (cheap, 1M context)
    "alibaba/qwen-turbo": ProviderCost(0.05, 0.10),
    "alibaba/qwen-plus": ProviderCost(0.20, 0.40),

    # Google Gemini
    "google/gemini-2.0-flash-lite": ProviderCost(0.075, 0.30),
    "google/gemini-2.5-flash": ProviderCost(0.15, 0.60),
    "google/gemini-2.5-pro": ProviderCost(1.25, 5.00),

    # OpenAI
    "openai/gpt-5.2": ProviderCost(1.75, 14.00),

    # Anthropic
    "anthropic/claude-haiku-3.5": ProviderCost(0.25, 1.25),
    "anthropic/claude-sonnet-4": ProviderCost(3.00, 15.00),
    "anthropic/claude-opus-4.5": ProviderCost(15.00, 75.00),

    # Moonshot (Kimi K2 - 1T parameter)
    "moonshot/kimi-k2": ProviderCost(1.00, 3.00),
}


# ============================================================================
# PROVIDER HEALTH STATUS
# ============================================================================

@dataclass
class ProviderHealth:
    """Health status for a provider."""
    provider_id: str
    is_healthy: bool = True
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    latency_ms: Optional[int] = None
    consecutive_failures: int = 0


# ============================================================================
# LLM CALL RESULT
# ============================================================================

@dataclass
class LLMCallResult:
    """Result of an LLM call with cost tracking."""
    provider_id: str
    model: str
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "success": self.success,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# TIER PROVIDER SELECTOR
# ============================================================================

class TierProviderSelector:
    """
    Selects and manages LLM providers based on customer tier.

    Features:
    - Tier-aware provider selection
    - Cost tracking per call
    - Provider health monitoring
    - Fallback to healthy providers
    - Parallel execution support

    Usage:
        selector = TierProviderSelector(tier=ExtractionTier.STANDARD)
        providers = selector.get_providers()

        # Execute with cost tracking
        result = await selector.execute_llm_call(
            provider_id="google/gemini-2.5-flash",
            prompt="Analyze this code...",
            system="You are a code analyst."
        )
        print(f"Cost: ${result.cost_usd:.4f}")
    """

    def __init__(self, tier: ExtractionTier = ExtractionTier.FREE):
        self.tier = tier
        self._health_status: Dict[str, ProviderHealth] = {}
        self._total_cost_usd: float = 0.0
        self._total_tokens: int = 0
        self._call_history: List[LLMCallResult] = []

        # Initialize health status for tier's providers
        for provider_id in self.get_provider_ids():
            self._health_status[provider_id] = ProviderHealth(provider_id=provider_id)

    # =========================================================================
    # TIER CONFIGURATION
    # =========================================================================

    def get_tier_config(self) -> Dict[str, Any]:
        """Get configuration for current tier."""
        return TIER_CONFIG.get(self.tier, TIER_CONFIG[ExtractionTier.FREE])

    def get_provider_ids(self) -> List[str]:
        """Get list of provider IDs available for current tier."""
        config = self.get_tier_config()
        return config.get("llms", [])

    def get_provider_count(self) -> int:
        """Get number of providers available for current tier."""
        return len(self.get_provider_ids())

    def get_price_usd(self) -> float:
        """Get customer price for current tier."""
        return self.get_tier_config().get("price_usd", 0.0)

    def get_confidence_target(self) -> float:
        """Get confidence target for current tier."""
        return self.get_tier_config().get("confidence_target", 0.60)

    def includes_human_review(self) -> bool:
        """Check if tier includes human review."""
        return self.get_tier_config().get("human_review", False)

    # =========================================================================
    # PROVIDER SELECTION
    # =========================================================================

    def get_providers_by_category(self) -> Dict[str, List[str]]:
        """
        Group providers by category for analysis type assignment.

        Returns dict with keys: local, fast, balanced, deep
        """
        providers = self.get_provider_ids()

        categories = {
            "local": [],      # Free, local (Ollama)
            "fast": [],       # Cheap, fast (Groq, Qwen)
            "balanced": [],   # Good balance (Gemini Flash)
            "deep": [],       # Deep reasoning (GPT-5.2, Opus, Gemini Pro)
        }

        for p in providers:
            if p.startswith("ollama/"):
                categories["local"].append(p)
            elif p.startswith("groq/") or p.startswith("alibaba/"):
                categories["fast"].append(p)
            elif "flash" in p.lower():
                categories["balanced"].append(p)
            else:
                categories["deep"].append(p)

        return categories

    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy provider IDs."""
        return [
            pid for pid in self.get_provider_ids()
            if self._health_status.get(pid, ProviderHealth(pid)).is_healthy
        ]

    def select_provider_for_analysis(self, analysis_type: str) -> str:
        """
        Select optimal provider for a specific analysis type.

        Analysis types:
        - architecture: Prefers deep reasoning (Opus, GPT-5.2)
        - business_logic: Prefers balanced (Gemini, Sonnet)
        - security: Prefers specialized (CodeLlama, GPT-5.2)
        - code_structure: Prefers fast coders (Qwen, Groq)
        """
        providers = self.get_provider_ids()
        categories = self.get_providers_by_category()
        healthy = self.get_healthy_providers()

        # Priority mapping
        priority_map = {
            "architecture": ["deep", "balanced", "fast", "local"],
            "business_logic": ["balanced", "deep", "fast", "local"],
            "security": ["deep", "balanced", "local", "fast"],
            "code_structure": ["fast", "local", "balanced", "deep"],
        }

        priority = priority_map.get(analysis_type, ["local", "fast", "balanced", "deep"])

        # Find first healthy provider in priority order
        for category in priority:
            for provider in categories.get(category, []):
                if provider in healthy:
                    return provider

        # Fallback to any healthy provider
        if healthy:
            return healthy[0]

        # Last resort: first provider (even if unhealthy)
        return providers[0] if providers else "ollama/qwen2.5-coder:7b"

    def get_providers_for_cycle(self, cycle: int) -> List[Tuple[str, str]]:
        """
        Get provider assignments for a specific cycle.

        Returns list of (provider_id, analysis_type) tuples.

        Cycle 1: Independent analysis (each LLM focuses on one aspect)
        Cycle 2: Cross-enrichment (LLMs review each other)
        Cycle 3: Conflict detection (orchestrator analyzes)
        Cycle 4: Human decision (no LLM)
        Cycle 5: Final synthesis (best LLM synthesizes)
        """
        providers = self.get_provider_ids()
        categories = self.get_providers_by_category()

        if cycle == 1:
            # Independent analysis - assign specializations
            analysis_types = ["architecture", "business_logic", "security", "code_structure"]
            assignments = []

            for i, provider in enumerate(providers):
                # Rotate through analysis types
                analysis = analysis_types[i % len(analysis_types)]
                assignments.append((provider, analysis))

            return assignments

        elif cycle == 2:
            # Cross-enrichment - all providers review
            return [(p, "enrichment") for p in providers]

        elif cycle == 3:
            # Conflict detection - use deep provider
            deep_providers = categories.get("deep", []) or categories.get("balanced", []) or providers[:1]
            return [(deep_providers[0] if deep_providers else providers[0], "conflict_detection")]

        elif cycle == 5:
            # Final synthesis - use best available
            if "anthropic/claude-opus-4.5" in providers:
                return [("anthropic/claude-opus-4.5", "synthesis")]
            elif "openai/gpt-5.2" in providers:
                return [("openai/gpt-5.2", "synthesis")]
            elif categories.get("deep"):
                return [(categories["deep"][0], "synthesis")]
            else:
                return [(providers[0], "synthesis")]

        return []  # Cycle 4 is human, no LLM assignments

    # =========================================================================
    # COST TRACKING
    # =========================================================================

    def calculate_cost(self, provider_id: str, tokens_input: int, tokens_output: int) -> float:
        """
        Calculate cost in USD for token usage.

        Args:
            provider_id: Full provider ID (e.g., "google/gemini-2.5-flash")
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens

        Returns:
            Cost in USD
        """
        cost_config = PROVIDER_COSTS.get(provider_id)
        if not cost_config:
            logger.warning(f"No cost config for {provider_id}, assuming free")
            return 0.0

        input_cost = (tokens_input / 1_000_000) * cost_config.input_per_m_tokens
        output_cost = (tokens_output / 1_000_000) * cost_config.output_per_m_tokens

        return input_cost + output_cost

    def track_call(self, result: LLMCallResult) -> None:
        """Track an LLM call for cost and statistics."""
        self._call_history.append(result)
        self._total_cost_usd += result.cost_usd
        self._total_tokens += result.tokens_input + result.tokens_output

    def get_total_cost(self) -> float:
        """Get total cost in USD for all calls."""
        return self._total_cost_usd

    def get_total_tokens(self) -> int:
        """Get total tokens used across all calls."""
        return self._total_tokens

    def get_margin(self) -> float:
        """Calculate margin (tier price - actual cost)."""
        return self.get_price_usd() - self._total_cost_usd

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by provider."""
        breakdown: Dict[str, float] = {}
        for call in self._call_history:
            provider = call.provider_id
            breakdown[provider] = breakdown.get(provider, 0.0) + call.cost_usd
        return breakdown

    def get_call_statistics(self) -> Dict[str, Any]:
        """Get statistics about LLM calls."""
        if not self._call_history:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "avg_latency_ms": 0,
                "cost_breakdown": {},
            }

        successful = [c for c in self._call_history if c.success]
        failed = [c for c in self._call_history if not c.success]
        latencies = [c.latency_ms for c in successful if c.latency_ms > 0]

        return {
            "total_calls": len(self._call_history),
            "successful_calls": len(successful),
            "failed_calls": len(failed),
            "total_cost_usd": self._total_cost_usd,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "cost_breakdown": self.get_cost_breakdown(),
            "margin_usd": self.get_margin(),
            "tier_price_usd": self.get_price_usd(),
        }

    # =========================================================================
    # HEALTH MONITORING
    # =========================================================================

    def update_health(
        self,
        provider_id: str,
        is_healthy: bool,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """Update health status for a provider."""
        if provider_id not in self._health_status:
            self._health_status[provider_id] = ProviderHealth(provider_id=provider_id)

        health = self._health_status[provider_id]
        health.last_check = datetime.now(timezone.utc)
        health.latency_ms = latency_ms

        if is_healthy:
            health.is_healthy = True
            health.consecutive_failures = 0
            health.last_error = None
        else:
            health.consecutive_failures += 1
            health.last_error = error
            # Mark unhealthy after 3 consecutive failures
            if health.consecutive_failures >= 3:
                health.is_healthy = False
                logger.warning(f"Provider {provider_id} marked unhealthy after {health.consecutive_failures} failures")

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all providers."""
        return {
            pid: {
                "is_healthy": h.is_healthy,
                "last_check": h.last_check.isoformat() if h.last_check else None,
                "last_error": h.last_error,
                "latency_ms": h.latency_ms,
                "consecutive_failures": h.consecutive_failures,
            }
            for pid, h in self._health_status.items()
        }

    async def healthcheck_provider(self, provider_id: str) -> bool:
        """
        Perform health check on a specific provider.

        This is a placeholder - actual implementation would call the provider's API.
        """
        # TODO: Implement actual health checks per provider type
        # For now, assume all providers are healthy
        self.update_health(provider_id, is_healthy=True, latency_ms=100)
        return True

    async def healthcheck_all(self) -> Dict[str, bool]:
        """Perform health checks on all providers."""
        results = {}
        for provider_id in self.get_provider_ids():
            results[provider_id] = await self.healthcheck_provider(provider_id)
        return results

    # =========================================================================
    # TIER UPGRADE
    # =========================================================================

    def upgrade_tier(self, new_tier: ExtractionTier) -> Dict[str, Any]:
        """
        Upgrade to a higher tier.

        Returns info about the upgrade including new providers and credit.
        """
        old_tier = self.tier
        old_providers = set(self.get_provider_ids())
        old_price = self.get_price_usd()

        # Update tier
        self.tier = new_tier

        new_providers = set(self.get_provider_ids())
        new_price = self.get_price_usd()

        # Calculate credit (what was already paid)
        credit = old_price
        amount_to_charge = new_price - credit

        # Initialize health for new providers
        added_providers = new_providers - old_providers
        for provider_id in added_providers:
            self._health_status[provider_id] = ProviderHealth(provider_id=provider_id)

        return {
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "old_price_usd": old_price,
            "new_price_usd": new_price,
            "credit_usd": credit,
            "amount_to_charge_usd": max(0, amount_to_charge),
            "providers_added": list(added_providers),
            "old_provider_count": len(old_providers),
            "new_provider_count": len(new_providers),
            "old_confidence_target": TIER_CONFIG[old_tier]["confidence_target"],
            "new_confidence_target": self.get_confidence_target(),
        }

    # =========================================================================
    # UTILITY
    # =========================================================================

    def get_provider_info(self, provider_id: str) -> Dict[str, Any]:
        """Get detailed info about a provider."""
        cost_config = PROVIDER_COSTS.get(provider_id)
        health = self._health_status.get(provider_id)

        return {
            "provider_id": provider_id,
            "is_local": cost_config.is_local if cost_config else False,
            "cost_input_per_m": cost_config.input_per_m_tokens if cost_config else 0.0,
            "cost_output_per_m": cost_config.output_per_m_tokens if cost_config else 0.0,
            "is_healthy": health.is_healthy if health else True,
            "available_in_tier": provider_id in self.get_provider_ids(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize selector state to dictionary."""
        return {
            "tier": self.tier.value,
            "tier_config": self.get_tier_config(),
            "providers": self.get_provider_ids(),
            "provider_count": self.get_provider_count(),
            "healthy_providers": self.get_healthy_providers(),
            "statistics": self.get_call_statistics(),
            "health_status": self.get_health_status(),
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_tier_selector(tier: str | ExtractionTier) -> TierProviderSelector:
    """
    Factory function to create a TierProviderSelector.

    Args:
        tier: Tier name (string) or ExtractionTier enum

    Returns:
        Configured TierProviderSelector
    """
    if isinstance(tier, str):
        tier = ExtractionTier(tier.upper())

    return TierProviderSelector(tier=tier)


# ============================================================================
# TIER COMPARISON
# ============================================================================

def compare_tiers() -> List[Dict[str, Any]]:
    """
    Get comparison of all tiers for onboarding UI.

    Returns list of tier info dicts.
    """
    comparison = []

    for tier in ExtractionTier:
        config = TIER_CONFIG[tier]
        selector = TierProviderSelector(tier)
        categories = selector.get_providers_by_category()

        comparison.append({
            "tier": tier.value,
            "price_usd": config["price_usd"],
            "confidence_target": config["confidence_target"],
            "llm_count": config["llm_count"],
            "human_review": config["human_review"],
            "llms": config["llms"],
            "categories": {
                "local": len(categories["local"]),
                "fast": len(categories["fast"]),
                "balanced": len(categories["balanced"]),
                "deep": len(categories["deep"]),
            },
            "recommended": tier == ExtractionTier.STANDARD,
        })

    return comparison
