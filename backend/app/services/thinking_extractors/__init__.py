"""
Thinking Extractors - Provider-specific LLM reasoning extraction

Week 61: CCTrace Integration

Supports:
- Claude CLI: Native `thinking` blocks with cryptographic signature
- Codex CLI: Pseudo-thinking extracted from `<thinking>` tags
- Ollama: Chain-of-Thought (CoT) forcing with tag extraction
"""

from app.services.thinking_extractors.base import BaseThinkingExtractor, ThinkingBlockData
from app.services.thinking_extractors.claude_extractor import ClaudeThinkingExtractor
from app.services.thinking_extractors.codex_extractor import CodexThinkingExtractor
from app.services.thinking_extractors.ollama_extractor import OllamaThinkingExtractor

__all__ = [
    "BaseThinkingExtractor",
    "ThinkingBlockData",
    "ClaudeThinkingExtractor",
    "CodexThinkingExtractor",
    "OllamaThinkingExtractor",
]
