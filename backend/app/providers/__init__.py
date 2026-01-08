"""
LLM Provider Registry - Multi-Model Support

Week 54: Provider abstraction layer for multi-LLM routing
Week 90: Extended with 5 new cloud providers for Deep Extraction

Supports:
- Local: Ollama
- CLI-based: Claude CLI, Codex CLI
- Cloud APIs: Groq, Gemini, OpenAI, Anthropic, Qwen

Usage:
    from app.providers import get_provider, ProviderRegistry

    # Get specific provider
    provider = get_provider("groq")
    response = await provider.generate(request)

    # Auto-route based on task
    registry = ProviderRegistry()
    provider = registry.route_task(task_type="architecture")
"""

from .base import LLMProvider, LLMRequest, LLMResponse, ProviderConfig

# Original providers
from .ollama_provider import OllamaProvider
from .codex_provider import CodexProvider
from .claude_provider import ClaudeProvider

# Week 90: New cloud providers for Deep Extraction
from .groq_provider import GroqProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .qwen_provider import QwenProvider

from .registry import ProviderRegistry, get_provider, get_registry

__all__ = [
    # Base classes
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ProviderConfig",
    # Original providers
    "OllamaProvider",
    "CodexProvider",
    "ClaudeProvider",
    # Week 90: New providers
    "GroqProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "QwenProvider",
    # Registry
    "ProviderRegistry",
    "get_provider",
    "get_registry",
]
