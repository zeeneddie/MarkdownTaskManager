"""
LLM Context Adapters - Week 101

Provider-specific context transformations for multi-LLM support.
"""

from .base import BaseAdapter
from .claude_adapter import ClaudeAdapter
from .codex_adapter import CodexAdapter
from .ollama_adapter import OllamaAdapter
from .qwen_adapter import QwenAdapter
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter

__all__ = [
    "BaseAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "OllamaAdapter",
    "QwenAdapter",
    "GeminiAdapter",
    "GroqAdapter",
]
