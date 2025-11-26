"""
LLM Provider Registry - Multi-Model Support

Week 54: Provider abstraction layer for multi-LLM routing
Supports: Ollama (local), Claude CLI, Codex CLI

Usage:
    from app.providers import get_provider, ProviderRegistry

    # Get specific provider
    provider = get_provider("codex")
    response = await provider.generate(request)

    # Auto-route based on task
    registry = ProviderRegistry()
    provider = registry.route_task(task_type="architecture")
"""

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig
from .ollama_provider import OllamaProvider
from .codex_provider import CodexProvider
from .registry import ProviderRegistry, get_provider

__all__ = [
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ProviderConfig",
    "OllamaProvider",
    "CodexProvider",
    "ProviderRegistry",
    "get_provider",
]
