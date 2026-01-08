"""
Base Thinking Extractor - Abstract interface for provider-specific extraction

Week 61: CCTrace Integration
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ThinkingBlockData:
    """
    Data structure for extracted thinking blocks.

    Provider-agnostic representation of LLM reasoning.
    """
    block_type: str  # thinking, reasoning, cot, reflection
    content: str
    token_count: int = 0
    sequence_number: int = 0
    signature: Optional[str] = None  # Claude native signature
    content_hash: Optional[str] = None  # SHA-256 hash
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate content hash if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(
                self.content.encode('utf-8')
            ).hexdigest()


class BaseThinkingExtractor(ABC):
    """
    Abstract base class for provider-specific thinking extractors.

    Each provider implements extraction differently:
    - Claude: Native `thinking` blocks in response JSON
    - Codex: Parse `<thinking>` tags from output
    - Ollama: CoT forcing with `<thinking>` prompt template
    """

    # Estimated tokens per character (conservative estimate)
    TOKENS_PER_CHAR = 0.25

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (claude, codex, ollama)."""
        pass

    @abstractmethod
    def extract(self, response_data: Dict[str, Any]) -> List[ThinkingBlockData]:
        """
        Extract thinking blocks from provider response.

        Args:
            response_data: The raw response from the LLM provider

        Returns:
            List of ThinkingBlockData objects
        """
        pass

    @abstractmethod
    def can_extract(self, response_data: Dict[str, Any]) -> bool:
        """
        Check if thinking can be extracted from this response.

        Args:
            response_data: The raw response from the LLM provider

        Returns:
            True if thinking blocks can be extracted
        """
        pass

    def _estimate_tokens(self, content: str) -> int:
        """
        Estimate token count from content.

        Uses a conservative estimate of ~4 characters per token.

        Args:
            content: The text content

        Returns:
            Estimated token count
        """
        if not content:
            return 0
        return int(len(content) * self.TOKENS_PER_CHAR)

    def _create_content_hash(self, content: str) -> str:
        """
        Create SHA-256 hash of content for verification.

        Args:
            content: The text content

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
