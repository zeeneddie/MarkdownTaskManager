"""
Anthropic Provider - Native API Integration

Direct Anthropic API integration for Claude models.
Used for PREMIUM tier in Deep Extraction Cycle 5 (Final Synthesis).

Supported Models:
- claude-3-5-sonnet-20241022: $3.00/$15.00 per M tokens (200K context)
- claude-3-5-haiku-20241022: $0.80/$4.00 per M tokens (200K context)
- claude-3-opus-20240229: $15.00/$75.00 per M tokens (200K context)
- claude-opus-4-5-20251101: $5.00/$25.00 per M tokens (200K context) - Latest

API Docs: https://docs.anthropic.com/en/api/getting-started
"""

import asyncio
import time
import os
from typing import List, Optional
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class AnthropicProvider(LLMProvider):
    """
    Anthropic provider for Claude models via native API.

    Benefits:
    - Best reasoning capabilities
    - Excellent at synthesis and summarization
    - Strong code understanding
    - 200K context window

    Best for:
    - Cycle 5: Final Synthesis (Claude Opus 4.5)
    - PREMIUM tier extraction
    - Complex reasoning and conflict resolution
    """

    SUPPORTED_MODELS = {
        # Claude Opus 4.5 - Latest and best
        "claude-opus-4-5-20251101": {
            "cost_input": 5.00,
            "cost_output": 25.00,
            "context": 200000,
            "tier": "deep",
        },
        # Claude 3.5 Sonnet - Balanced
        "claude-3-5-sonnet-20241022": {
            "cost_input": 3.00,
            "cost_output": 15.00,
            "context": 200000,
            "tier": "balanced",
        },
        # Claude 3.5 Haiku - Fast
        "claude-3-5-haiku-20241022": {
            "cost_input": 0.80,
            "cost_output": 4.00,
            "context": 200000,
            "tier": "fast",
        },
        # Claude 3 Opus - Previous flagship
        "claude-3-opus-20240229": {
            "cost_input": 15.00,
            "cost_output": 75.00,
            "context": 200000,
            "tier": "deep",
        },
    }

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    PREMIUM_MODEL = "claude-opus-4-5-20251101"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"

        model = model or self.DEFAULT_MODEL
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS[self.DEFAULT_MODEL])

        self.config = ProviderConfig(
            name="anthropic",
            tier=model_config["tier"],
            model=model,
            cost_input_per_m=model_config["cost_input"],
            cost_output_per_m=model_config["cost_output"],
            is_local=False,
            is_active=bool(self.api_key),
            extras={
                "context_length": model_config["context"],
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API."""
        if not self.api_key:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="anthropic",
                success=False,
                error="ANTHROPIC_API_KEY not configured"
            )

        start_time = time.time()

        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }

            messages = [{"role": "user", "content": request.prompt}]

            payload = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": request.max_tokens or 4096,
            }

            if request.system:
                payload["system"] = request.system
            if request.temperature is not None:
                payload["temperature"] = request.temperature
            if request.top_p is not None:
                payload["top_p"] = request.top_p
            if request.stop:
                payload["stop_sequences"] = request.stop

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return LLMResponse(
                            content="",
                            model=self.config.model,
                            provider="anthropic",
                            success=False,
                            error=f"Anthropic error {resp.status}: {error_text}"
                        )

                    data = await resp.json()
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Extract content
                    content = ""
                    if "content" in data and len(data["content"]) > 0:
                        content = data["content"][0].get("text", "")

                    # Extract usage
                    usage = data.get("usage", {})
                    token_input = usage.get("input_tokens", 0)
                    token_output = usage.get("output_tokens", 0)

                    return LLMResponse(
                        content=content,
                        model=self.config.model,
                        provider="anthropic",
                        token_input=token_input,
                        token_output=token_output,
                        duration_ms=duration_ms,
                        cost_cents=self.calculate_cost(token_input, token_output),
                        success=True,
                        raw=data
                    )

        except asyncio.TimeoutError:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="anthropic",
                success=False,
                error=f"Anthropic timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="anthropic",
                success=False,
                error=f"Anthropic error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Anthropic API is accessible."""
        if not self.api_key:
            return False

        try:
            # Anthropic doesn't have a models endpoint, so we'll do a minimal test
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }

            payload = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def supports_model(self, model: str) -> bool:
        """Check if model is supported."""
        return model in self.SUPPORTED_MODELS

    async def list_models(self) -> List[str]:
        """List available models."""
        return list(self.SUPPORTED_MODELS.keys())

    @classmethod
    def get_recommended_model(cls, tier: str = "standard") -> str:
        """Get recommended model for extraction tier."""
        recommendations = {
            "free": None,  # Not available for free tier
            "basic": None,  # Not available for basic tier
            "standard": "claude-3-5-haiku-20241022",  # Fast, affordable
            "professional": "claude-3-5-sonnet-20241022",  # Balanced
            "premium": "claude-opus-4-5-20251101",  # Best reasoning
        }
        return recommendations.get(tier, cls.DEFAULT_MODEL)

    @classmethod
    def get_synthesis_model(cls) -> str:
        """Get recommended model for Cycle 5 synthesis."""
        return cls.PREMIUM_MODEL
