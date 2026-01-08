"""
OpenAI Provider - Native API Integration

Direct OpenAI API integration for GPT models.
Used for PROFESSIONAL/PREMIUM tiers in Deep Extraction Cycle 3.

Supported Models:
- gpt-4o: $2.50/$10.00 per M tokens (128K context) - Best overall
- gpt-4o-mini: $0.15/$0.60 per M tokens (128K context) - Fast, cheap
- gpt-4-turbo: $10.00/$30.00 per M tokens (128K context) - High quality
- o1-preview: $15.00/$60.00 per M tokens - Advanced reasoning
- o1-mini: $3.00/$12.00 per M tokens - Efficient reasoning

API Docs: https://platform.openai.com/docs/api-reference
"""

import asyncio
import time
import os
from typing import List, Optional
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider for GPT models via native API.

    Benefits:
    - Industry standard models
    - Excellent code generation
    - Strong reasoning capabilities
    - Wide context windows

    Best for:
    - Cycle 3: Conflict detection (GPT-4o for coding)
    - PROFESSIONAL tier extraction
    - Complex reasoning tasks
    """

    SUPPORTED_MODELS = {
        # GPT-4o - Best overall
        "gpt-4o": {
            "cost_input": 2.50,
            "cost_output": 10.00,
            "context": 128000,
            "tier": "deep",
        },
        # GPT-4o Mini - Fast and cheap
        "gpt-4o-mini": {
            "cost_input": 0.15,
            "cost_output": 0.60,
            "context": 128000,
            "tier": "fast",
        },
        # GPT-4 Turbo - High quality
        "gpt-4-turbo": {
            "cost_input": 10.00,
            "cost_output": 30.00,
            "context": 128000,
            "tier": "deep",
        },
        # o1-preview - Advanced reasoning
        "o1-preview": {
            "cost_input": 15.00,
            "cost_output": 60.00,
            "context": 128000,
            "tier": "deep",
        },
        # o1-mini - Efficient reasoning
        "o1-mini": {
            "cost_input": 3.00,
            "cost_output": 12.00,
            "context": 128000,
            "tier": "balanced",
        },
        # GPT-3.5 Turbo - Legacy, very cheap
        "gpt-3.5-turbo": {
            "cost_input": 0.50,
            "cost_output": 1.50,
            "context": 16385,
            "tier": "fast",
        },
    }

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        organization: str = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORG_ID")
        self.base_url = "https://api.openai.com/v1"

        model = model or self.DEFAULT_MODEL
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS[self.DEFAULT_MODEL])

        self.config = ProviderConfig(
            name="openai",
            tier=model_config["tier"],
            model=model,
            cost_input_per_m=model_config["cost_input"],
            cost_output_per_m=model_config["cost_output"],
            is_local=False,
            is_active=bool(self.api_key),
            extras={
                "context_length": model_config["context"],
                "organization": self.organization,
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API."""
        if not self.api_key:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="openai",
                success=False,
                error="OPENAI_API_KEY not configured"
            )

        start_time = time.time()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization

            messages = []
            if request.system:
                messages.append({"role": "system", "content": request.system})
            messages.append({"role": "user", "content": request.prompt})

            payload = {
                "model": self.config.model,
                "messages": messages,
            }

            # o1 models don't support some parameters
            is_o1_model = self.config.model.startswith("o1")

            if request.max_tokens and not is_o1_model:
                payload["max_tokens"] = request.max_tokens
            if request.temperature is not None and not is_o1_model:
                payload["temperature"] = request.temperature
            if request.top_p is not None and not is_o1_model:
                payload["top_p"] = request.top_p
            if request.stop and not is_o1_model:
                payload["stop"] = request.stop

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return LLMResponse(
                            content="",
                            model=self.config.model,
                            provider="openai",
                            success=False,
                            error=f"OpenAI error {resp.status}: {error_text}"
                        )

                    data = await resp.json()
                    duration_ms = int((time.time() - start_time) * 1000)

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    token_input = usage.get("prompt_tokens", 0)
                    token_output = usage.get("completion_tokens", 0)

                    return LLMResponse(
                        content=content,
                        model=self.config.model,
                        provider="openai",
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
                provider="openai",
                success=False,
                error=f"OpenAI timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="openai",
                success=False,
                error=f"OpenAI error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            if self.organization:
                headers["OpenAI-Organization"] = self.organization

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
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
    def get_recommended_model(cls, task_type: str = "coding") -> str:
        """Get recommended model for task type."""
        recommendations = {
            "coding": "gpt-4o",  # Best for code
            "reasoning": "o1-mini",  # Good reasoning, lower cost
            "fast": "gpt-4o-mini",  # Fast and cheap
            "premium": "o1-preview",  # Best reasoning
        }
        return recommendations.get(task_type, cls.DEFAULT_MODEL)
