"""
Google Gemini Provider - Advanced AI Models

Gemini provides powerful models with up to 1M token context windows.
Essential for STANDARD and PROFESSIONAL tiers in Deep Extraction.

Supported Models:
- gemini-2.0-flash-lite: $0.075/$0.30 per M tokens (1M context) - Fast, cheap
- gemini-2.5-flash: $0.30/$2.50 per M tokens (1M context) - Balanced
- gemini-2.5-pro: $1.25/$10.00 per M tokens (1M context) - High quality
- gemini-3-pro: $2.00/$12.00 per M tokens (200K+ context) - Best agentic

API Docs: https://ai.google.dev/gemini-api/docs
"""

import asyncio
import time
import os
from typing import List, Optional, Dict, Any
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider for advanced AI tasks.

    Benefits:
    - Massive context: Up to 1M tokens
    - Multimodal: Text, code, images
    - Cost-effective: Context caching available
    - Strong coding: Excellent at code understanding

    Best for:
    - Cycle 2: Cross-enrichment (1M context fits all Cycle 1 outputs)
    - Cycle 3: Conflict detection with Gemini Pro
    - Cycle 5: Final synthesis (agentic tasks)
    """

    SUPPORTED_MODELS = {
        # Flash-Lite - Ultra cheap, fast
        "gemini-2.0-flash-lite": {
            "cost_input": 0.075,
            "cost_output": 0.30,
            "cost_cached_input": 0.01875,  # 75% discount on cached
            "context": 1000000,
            "tier": "fast",
        },
        # Flash - Balanced
        "gemini-2.5-flash": {
            "cost_input": 0.30,
            "cost_output": 2.50,
            "cost_cached_input": 0.075,
            "context": 1000000,
            "tier": "balanced",
        },
        # Pro - High quality reasoning
        "gemini-2.5-pro": {
            "cost_input": 1.25,
            "cost_output": 10.00,
            "cost_cached_input": 0.3125,
            "context": 1000000,
            "tier": "deep",
        },
        # 3 Pro - Best for agentic tasks
        "gemini-3-pro": {
            "cost_input": 2.00,
            "cost_output": 12.00,
            "cost_cached_input": 0.50,
            "context": 200000,
            "tier": "deep",
        },
    }

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        model = model or self.DEFAULT_MODEL
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS[self.DEFAULT_MODEL])

        self.config = ProviderConfig(
            name="gemini",
            tier=model_config["tier"],
            model=model,
            cost_input_per_m=model_config["cost_input"],
            cost_output_per_m=model_config["cost_output"],
            is_local=False,
            is_active=bool(self.api_key),
            extras={
                "context_length": model_config["context"],
                "cached_input_cost": model_config["cost_cached_input"],
            }
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Google Gemini API."""
        if not self.api_key:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="gemini",
                success=False,
                error="GOOGLE_API_KEY or GEMINI_API_KEY not configured"
            )

        start_time = time.time()

        try:
            # Build contents
            contents = []

            if request.system:
                # Gemini uses system_instruction for system prompts
                contents.append({
                    "role": "user",
                    "parts": [{"text": request.prompt}]
                })
            else:
                contents.append({
                    "role": "user",
                    "parts": [{"text": request.prompt}]
                })

            payload = {
                "contents": contents,
                "generationConfig": {}
            }

            if request.system:
                payload["systemInstruction"] = {
                    "parts": [{"text": request.system}]
                }

            if request.max_tokens:
                payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
            if request.temperature is not None:
                payload["generationConfig"]["temperature"] = request.temperature
            if request.top_p is not None:
                payload["generationConfig"]["topP"] = request.top_p
            if request.stop:
                payload["generationConfig"]["stopSequences"] = request.stop

            url = f"{self.base_url}/models/{self.config.model}:generateContent?key={self.api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return LLMResponse(
                            content="",
                            model=self.config.model,
                            provider="gemini",
                            success=False,
                            error=f"Gemini error {resp.status}: {error_text}"
                        )

                    data = await resp.json()
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Extract content from response
                    content = ""
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            content = candidate["content"]["parts"][0].get("text", "")

                    # Extract usage metadata
                    usage = data.get("usageMetadata", {})
                    token_input = usage.get("promptTokenCount", 0)
                    token_output = usage.get("candidatesTokenCount", 0)

                    return LLMResponse(
                        content=content,
                        model=self.config.model,
                        provider="gemini",
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
                provider="gemini",
                success=False,
                error=f"Gemini timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="gemini",
                success=False,
                error=f"Gemini error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Gemini API is accessible."""
        if not self.api_key:
            return False

        try:
            url = f"{self.base_url}/models?key={self.api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
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
    def get_recommended_model(cls, cycle: int = 1) -> str:
        """Get recommended model for extraction cycle."""
        recommendations = {
            1: "gemini-2.0-flash-lite",  # Fast, cheap for parallel analysis
            2: "gemini-2.5-flash",  # 1M context for cross-enrichment
            3: "gemini-2.5-pro",  # Deep reasoning for conflict detection
            5: "gemini-3-pro",  # Best agentic for final synthesis
        }
        return recommendations.get(cycle, cls.DEFAULT_MODEL)

    async def generate_with_cache(
        self,
        request: LLMRequest,
        cache_key: str = None
    ) -> LLMResponse:
        """
        Generate with context caching for cost savings.

        Gemini offers 75% discount on cached input tokens.
        Useful for repeated analysis of same codebase.
        """
        # TODO: Implement context caching when Gemini adds full API support
        # For now, use regular generation
        return await self.generate(request)
