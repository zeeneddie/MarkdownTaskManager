"""
Groq Provider - Ultra-Fast LLM Inference

Groq provides blazing-fast inference (up to 840 tokens/second) at low cost.
Ideal for Cycle 1 validation and quick analysis tasks.

Supported Models:
- llama-3.1-8b-instant: $0.05/$0.08 per M tokens (128K context)
- llama-3.1-70b-versatile: $0.59/$0.79 per M tokens (128K context)
- llama-3.3-70b-versatile: $0.59/$0.79 per M tokens (128K context)
- qwen-qwq-32b: $0.29/$0.59 per M tokens (128K context)
- mixtral-8x7b-32768: $0.24/$0.24 per M tokens (32K context)

API Docs: https://console.groq.com/docs/api-reference
"""

import asyncio
import time
import os
from typing import List, Optional
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class GroqProvider(LLMProvider):
    """
    Groq Cloud provider for ultra-fast LLM inference.

    Benefits:
    - Blazing fast: 300-840 tokens/second
    - Low cost: $0.05-$0.79 per M tokens
    - Large context: 128K tokens
    - OpenAI-compatible API

    Best for:
    - Quick validation passes in Cycle 1
    - Fast code structure analysis
    - Real-time feedback loops
    """

    SUPPORTED_MODELS = {
        # Llama 3.1 - Fast inference
        "llama-3.1-8b-instant": {
            "cost_input": 0.05,
            "cost_output": 0.08,
            "context": 128000,
            "tps": 840,
        },
        "llama-3.1-70b-versatile": {
            "cost_input": 0.59,
            "cost_output": 0.79,
            "context": 128000,
            "tps": 300,
        },
        # Llama 3.3 - Latest
        "llama-3.3-70b-versatile": {
            "cost_input": 0.59,
            "cost_output": 0.79,
            "context": 128000,
            "tps": 300,
        },
        # Qwen - Reasoning
        "qwen-qwq-32b": {
            "cost_input": 0.29,
            "cost_output": 0.59,
            "context": 128000,
            "tps": 400,
        },
        # Mixtral - Balanced
        "mixtral-8x7b-32768": {
            "cost_input": 0.24,
            "cost_output": 0.24,
            "context": 32768,
            "tps": 500,
        },
    }

    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"

        model = model or self.DEFAULT_MODEL
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS[self.DEFAULT_MODEL])

        self.config = ProviderConfig(
            name="groq",
            tier="fast",
            model=model,
            cost_input_per_m=model_config["cost_input"],
            cost_output_per_m=model_config["cost_output"],
            is_local=False,
            is_active=bool(self.api_key),
            extras={
                "context_length": model_config["context"],
                "tokens_per_second": model_config["tps"],
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Groq Cloud API."""
        if not self.api_key:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="groq",
                success=False,
                error="GROQ_API_KEY not configured"
            )

        start_time = time.time()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = []
            if request.system:
                messages.append({"role": "system", "content": request.system})
            messages.append({"role": "user", "content": request.prompt})

            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            if request.temperature is not None:
                payload["temperature"] = request.temperature
            if request.top_p is not None:
                payload["top_p"] = request.top_p
            if request.stop:
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
                            provider="groq",
                            success=False,
                            error=f"Groq error {resp.status}: {error_text}"
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
                        provider="groq",
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
                provider="groq",
                success=False,
                error=f"Groq timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="groq",
                success=False,
                error=f"Groq error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Groq API is accessible."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

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
    def get_recommended_model(cls, task_type: str = "validation") -> str:
        """Get recommended model for task type."""
        recommendations = {
            "validation": "llama-3.1-8b-instant",  # Fastest
            "analysis": "llama-3.3-70b-versatile",  # Most capable
            "reasoning": "qwen-qwq-32b",  # Best reasoning
            "balanced": "mixtral-8x7b-32768",  # Good balance
        }
        return recommendations.get(task_type, cls.DEFAULT_MODEL)
