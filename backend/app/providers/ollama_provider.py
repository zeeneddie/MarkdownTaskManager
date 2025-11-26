"""
Ollama Provider - Local LLM Support

Wraps the local Ollama server for free, private inference.
Supports: qwen2.5-coder, deepseek-r1, codellama, mistral, etc.
"""

import asyncio
import time
from typing import List, Optional
import aiohttp

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig


class OllamaProvider(LLMProvider):
    """
    Local Ollama provider for free, private LLM inference.

    Benefits:
    - Zero cost (runs locally)
    - Complete privacy (no data leaves machine)
    - Works offline
    - Multiple model support

    Models:
    - qwen2.5-coder:7b - Code generation & refactoring
    - deepseek-r1:latest - Reasoning & analysis
    - codellama:latest - Debugging
    - mistral:latest - Documentation
    - qwen2.5:7b - Planning
    """

    SUPPORTED_MODELS = [
        "qwen2.5-coder:7b",
        "qwen2.5-coder:14b",
        "deepseek-r1:latest",
        "deepseek-r1:7b",
        "codellama:latest",
        "codellama:7b",
        "mistral:latest",
        "qwen2.5:7b",
        "llama3.2:latest",
    ]

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b"
    ):
        self.base_url = base_url
        self.config = ProviderConfig(
            name="ollama",
            tier="free",
            model=model,
            cost_input_per_m=0.0,
            cost_output_per_m=0.0,
            is_local=True,
            is_active=True,
            extras={"base_url": base_url}
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using local Ollama server."""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.config.model,
                    "prompt": request.prompt,
                    "stream": False,
                }

                if request.system:
                    payload["system"] = request.system
                if request.temperature is not None:
                    payload["options"] = payload.get("options", {})
                    payload["options"]["temperature"] = request.temperature
                if request.max_tokens:
                    payload["options"] = payload.get("options", {})
                    payload["options"]["num_predict"] = request.max_tokens

                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return LLMResponse(
                            content="",
                            model=self.config.model,
                            provider="ollama",
                            success=False,
                            error=f"Ollama error {resp.status}: {error_text}"
                        )

                    data = await resp.json()
                    duration_ms = int((time.time() - start_time) * 1000)

                    return LLMResponse(
                        content=data.get("response", ""),
                        model=self.config.model,
                        provider="ollama",
                        token_input=data.get("prompt_eval_count", 0),
                        token_output=data.get("eval_count", 0),
                        duration_ms=duration_ms,
                        cost_cents=0.0,  # Local = free
                        success=True,
                        raw=data
                    )

        except asyncio.TimeoutError:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="ollama",
                success=False,
                error=f"Ollama timeout after {request.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider="ollama",
                success=False,
                error=f"Ollama error: {str(e)}"
            )

    async def healthcheck(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def supports_model(self, model: str) -> bool:
        """Check if model is in supported list."""
        return model in self.SUPPORTED_MODELS

    async def list_models(self) -> List[str]:
        """List available models from Ollama server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
