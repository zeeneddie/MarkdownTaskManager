"""
Base LLM Provider Interface

Abstract base class and data structures for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime, timezone


ProviderName = Literal[
    "ollama", "codex", "claude",  # Original providers
    "groq", "gemini", "openai", "anthropic", "qwen"  # Week 90: New providers
]
ModelTier = Literal["free", "fast", "balanced", "deep"]


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: ProviderName
    tier: ModelTier
    model: str
    cost_input_per_m: float = 0.0  # Cost per million input tokens
    cost_output_per_m: float = 0.0  # Cost per million output tokens
    is_local: bool = False
    is_active: bool = True
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    prompt: str
    system: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None
    timeout: int = 120  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    provider: ProviderName
    token_input: int = 0
    token_output: int = 0
    duration_ms: int = 0
    cost_cents: float = 0.0
    success: bool = True
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers (Ollama, Codex, Claude) implement this interface
    for consistent usage across the platform.
    """

    config: ProviderConfig

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            request: LLMRequest with prompt and parameters

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    async def healthcheck(self) -> bool:
        """
        Check if the provider is available and working.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """
        Check if this provider supports a specific model.

        Args:
            model: Model name to check

        Returns:
            True if model is supported
        """
        pass

    def calculate_cost(self, token_input: int, token_output: int) -> float:
        """
        Calculate cost in cents for token usage.

        Args:
            token_input: Number of input tokens
            token_output: Number of output tokens

        Returns:
            Cost in cents
        """
        input_cost = (token_input / 1_000_000) * self.config.cost_input_per_m * 100
        output_cost = (token_output / 1_000_000) * self.config.cost_output_per_m * 100
        return input_cost + output_cost
