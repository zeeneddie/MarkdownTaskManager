"""
Alibaba Qwen Provider - Cost-Effective LLM

Alibaba Cloud Qwen models offer excellent value with 1M context.
Used for BASIC tier in Deep Extraction.

Supported Models:
- qwen-turbo: $0.05/$0.20 per M tokens (1M context) - Ultra cheap
- qwen-plus: $0.40/$1.20 per M tokens (1M context) - Extended analysis
- qwen-max: $2.00/$6.00 per M tokens (32K context) - Best quality

API Docs: https://www.alibabacloud.com/help/en/model-studio/
"""

import asyncio
import time
import os
from typing import List, Optional
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class QwenProvider(LLMProvider):
    """
    Alibaba Qwen provider for cost-effective LLM inference.

    Benefits:
    - Ultra low cost: $0.05-$0.40 per M input tokens
    - Massive context: Up to 1M tokens
    - OpenAI-compatible API
    - Good multilingual support

    Best for:
    - Cycle 1: Bulk code analysis (qwen-turbo)
    - BASIC tier extraction
    - Integration point detection
    """

    SUPPORTED_MODELS = {
        # Qwen Turbo - Ultra cheap, 1M context
        "qwen-turbo": {
            "cost_input": 0.05,
            "cost_output": 0.20,
            "context": 1000000,
            "tier": "fast",
        },
        # Qwen Plus - Extended analysis
        "qwen-plus": {
            "cost_input": 0.40,
            "cost_output": 1.20,
            "context": 1000000,
            "tier": "balanced",
        },
        # Qwen Max - Best quality
        "qwen-max": {
            "cost_input": 2.00,
            "cost_output": 6.00,
            "context": 32768,
            "tier": "deep",
        },
        # Qwen Long - Long context specialized
        "qwen-long": {
            "cost_input": 0.05,
            "cost_output": 0.20,
            "context": 10000000,  # 10M context!
            "tier": "balanced",
        },
    }

    DEFAULT_MODEL = "qwen-turbo"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        model = model or self.DEFAULT_MODEL
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS[self.DEFAULT_MODEL])

        self.config = ProviderConfig(
            name="qwen",
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
        """Generate response using Alibaba DashScope API (OpenAI-compatible)."""
        if not self.api_key:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="qwen",
                success=False,
                error="DASHSCOPE_API_KEY or QWEN_API_KEY not configured"
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
                            provider="qwen",
                            success=False,
                            error=f"Qwen error {resp.status}: {error_text}"
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
                        provider="qwen",
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
                provider="qwen",
                success=False,
                error=f"Qwen timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="qwen",
                success=False,
                error=f"Qwen error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Qwen API is accessible."""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
    def get_recommended_model(cls, task_type: str = "bulk") -> str:
        """Get recommended model for task type."""
        recommendations = {
            "bulk": "qwen-turbo",  # Ultra cheap for bulk processing
            "analysis": "qwen-plus",  # Extended analysis
            "quality": "qwen-max",  # Best quality
            "long_context": "qwen-long",  # For very long documents
        }
        return recommendations.get(task_type, cls.DEFAULT_MODEL)
