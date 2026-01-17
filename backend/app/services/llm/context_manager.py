"""
Context Management Service - Week 104
CG-M-3: Token budget management and context prioritization

Manages LLM context windows efficiently by:
- Tracking token usage
- Prioritizing content by relevance
- Compressing/summarizing when needed
- Caching frequently used context
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timezone
import hashlib
import json


class ContextPriority(Enum):
    """Priority levels for context items."""
    CRITICAL = 1    # Always included (ground rules, security)
    HIGH = 2        # Included if space (current task context)
    MEDIUM = 3      # Included if space (related files)
    LOW = 4         # Compressed or excluded (historical)
    CACHED = 5      # Retrieved from cache only when needed


@dataclass
class ContextItem:
    """A single item in the context window."""
    content: str
    source: str
    priority: ContextPriority
    tokens: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    relevance_score: float = 1.0
    compressed: bool = False
    cache_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "priority": self.priority.name,
            "tokens": self.tokens,
            "timestamp": self.timestamp.isoformat(),
            "relevance_score": self.relevance_score,
            "compressed": self.compressed
        }


@dataclass
class ContextBudget:
    """Token budget configuration."""
    total_tokens: int = 128000        # Default context window
    reserved_output: int = 4000       # Reserve for response
    reserved_system: int = 2000       # Reserve for system prompt
    compression_threshold: float = 0.8  # Compress at 80% usage

    @property
    def available_tokens(self) -> int:
        return self.total_tokens - self.reserved_output - self.reserved_system


class ContextManager:
    """
    Manages LLM context window efficiently.

    Features:
    - Token tracking and budget management
    - Priority-based content selection
    - Automatic compression for low-priority items
    - Caching for frequently used context
    """

    def __init__(self, budget: Optional[ContextBudget] = None):
        self.budget = budget or ContextBudget()
        self.items: List[ContextItem] = []
        self.cache: Dict[str, ContextItem] = {}
        self._token_counter = self._create_token_counter()

    def _create_token_counter(self):
        """Create a token counting function."""
        # Simple approximation: ~4 chars per token for English
        # For production, use tiktoken or similar
        def count_tokens(text: str) -> int:
            return len(text) // 4 + 1
        return count_tokens

    def add_context(
        self,
        content: str,
        source: str,
        priority: ContextPriority = ContextPriority.MEDIUM,
        relevance_score: float = 1.0
    ) -> bool:
        """
        Add content to the context window.

        Returns True if added successfully, False if no space.
        """
        tokens = self._token_counter(content)

        item = ContextItem(
            content=content,
            source=source,
            priority=priority,
            tokens=tokens,
            relevance_score=relevance_score
        )

        # Check if we need to make space
        if self.used_tokens + tokens > self.budget.available_tokens:
            freed = self._free_space(tokens)
            if not freed:
                return False

        self.items.append(item)
        return True

    def add_critical(self, content: str, source: str) -> bool:
        """Add critical context (always included)."""
        return self.add_context(content, source, ContextPriority.CRITICAL)

    def add_high(self, content: str, source: str, relevance: float = 1.0) -> bool:
        """Add high-priority context."""
        return self.add_context(content, source, ContextPriority.HIGH, relevance)

    def add_cached(self, content: str, source: str) -> str:
        """
        Add content to cache and return cache key.

        Cached content is not included in the context window
        unless explicitly retrieved.
        """
        cache_key = hashlib.md5(content.encode()).hexdigest()[:12]
        tokens = self._token_counter(content)

        item = ContextItem(
            content=content,
            source=source,
            priority=ContextPriority.CACHED,
            tokens=tokens,
            cache_key=cache_key
        )

        self.cache[cache_key] = item
        return cache_key

    def get_cached(self, cache_key: str) -> Optional[str]:
        """Retrieve content from cache."""
        item = self.cache.get(cache_key)
        return item.content if item else None

    def promote_cached(self, cache_key: str, priority: ContextPriority = ContextPriority.HIGH) -> bool:
        """Move cached content into active context."""
        item = self.cache.get(cache_key)
        if not item:
            return False

        item.priority = priority
        return self.add_context(item.content, item.source, priority)

    @property
    def used_tokens(self) -> int:
        """Total tokens currently in use."""
        return sum(item.tokens for item in self.items if item.priority != ContextPriority.CACHED)

    @property
    def usage_ratio(self) -> float:
        """Current usage as ratio of available."""
        return self.used_tokens / self.budget.available_tokens

    def _free_space(self, needed_tokens: int) -> bool:
        """
        Free up space by compressing or removing low-priority items.

        Returns True if enough space was freed.
        """
        # Sort by priority (lowest first) then by relevance (lowest first)
        removable = [
            item for item in self.items
            if item.priority.value >= ContextPriority.MEDIUM.value
        ]
        removable.sort(key=lambda x: (-x.priority.value, x.relevance_score))

        freed = 0
        to_remove = []

        for item in removable:
            if freed >= needed_tokens:
                break

            # Try compression first for MEDIUM items
            if item.priority == ContextPriority.MEDIUM and not item.compressed:
                compressed_content = self._compress(item.content)
                old_tokens = item.tokens
                item.content = compressed_content
                item.tokens = self._token_counter(compressed_content)
                item.compressed = True
                freed += old_tokens - item.tokens
            # Remove LOW priority items
            elif item.priority == ContextPriority.LOW:
                to_remove.append(item)
                freed += item.tokens

        for item in to_remove:
            self.items.remove(item)

        return freed >= needed_tokens

    def _compress(self, content: str, ratio: float = 0.5) -> str:
        """
        Compress content to reduce token usage.

        In production, this would use LLM summarization.
        For now, we use a simple truncation.
        """
        # Simple compression: keep first and last parts
        if len(content) < 500:
            return content

        target_len = int(len(content) * ratio)
        half = target_len // 2

        return f"{content[:half]}\n...[compressed]...\n{content[-half:]}"

    def build_context(self) -> str:
        """
        Build the final context string for LLM consumption.

        Items are sorted by priority and concatenated.
        """
        # Sort by priority (CRITICAL first)
        sorted_items = sorted(self.items, key=lambda x: x.priority.value)

        parts = []
        for item in sorted_items:
            if item.priority != ContextPriority.CACHED:
                parts.append(f"<!-- Source: {item.source} -->\n{item.content}")

        return "\n\n---\n\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get context usage statistics."""
        by_priority = {}
        for priority in ContextPriority:
            items = [i for i in self.items if i.priority == priority]
            by_priority[priority.name] = {
                "count": len(items),
                "tokens": sum(i.tokens for i in items)
            }

        return {
            "total_items": len(self.items),
            "used_tokens": self.used_tokens,
            "available_tokens": self.budget.available_tokens,
            "usage_ratio": round(self.usage_ratio, 3),
            "cached_items": len(self.cache),
            "by_priority": by_priority
        }

    def clear(self, keep_critical: bool = True):
        """Clear context, optionally keeping critical items."""
        if keep_critical:
            self.items = [i for i in self.items if i.priority == ContextPriority.CRITICAL]
        else:
            self.items = []

    def export_state(self) -> Dict[str, Any]:
        """Export context state for persistence."""
        return {
            "items": [
                {
                    "content": item.content,
                    "source": item.source,
                    "priority": item.priority.name,
                    "tokens": item.tokens,
                    "relevance_score": item.relevance_score,
                    "compressed": item.compressed
                }
                for item in self.items
            ],
            "budget": {
                "total_tokens": self.budget.total_tokens,
                "reserved_output": self.budget.reserved_output
            },
            "stats": self.get_stats()
        }


class ContextBuilder:
    """
    Fluent builder for constructing context windows.

    Example:
        context = (ContextBuilder()
            .with_budget(128000)
            .add_ground_rules("path/to/rules.md")
            .add_project_context("path/to/context.md")
            .add_current_file("path/to/file.py", relevance=0.9)
            .build())
    """

    def __init__(self):
        self._manager = ContextManager()
        self._ground_rules: Optional[str] = None
        self._project_context: Optional[str] = None

    def with_budget(
        self,
        total_tokens: int = 128000,
        reserved_output: int = 4000
    ) -> "ContextBuilder":
        """Set the token budget."""
        self._manager.budget = ContextBudget(
            total_tokens=total_tokens,
            reserved_output=reserved_output
        )
        return self

    def add_ground_rules(self, content: str) -> "ContextBuilder":
        """Add ground rules (CRITICAL priority)."""
        self._manager.add_critical(content, "ground-rules")
        return self

    def add_project_context(self, content: str) -> "ContextBuilder":
        """Add project context (CRITICAL priority)."""
        self._manager.add_critical(content, "project-context")
        return self

    def add_current_task(self, content: str) -> "ContextBuilder":
        """Add current task description (HIGH priority)."""
        self._manager.add_high(content, "current-task", relevance=1.0)
        return self

    def add_file(
        self,
        content: str,
        path: str,
        relevance: float = 0.8
    ) -> "ContextBuilder":
        """Add a file to context (priority based on relevance)."""
        priority = (
            ContextPriority.HIGH if relevance >= 0.8
            else ContextPriority.MEDIUM if relevance >= 0.5
            else ContextPriority.LOW
        )
        self._manager.add_context(content, f"file:{path}", priority, relevance)
        return self

    def add_reference(self, content: str, source: str) -> "ContextBuilder":
        """Add reference material (MEDIUM priority)."""
        self._manager.add_context(content, f"reference:{source}", ContextPriority.MEDIUM)
        return self

    def cache(self, content: str, source: str) -> Tuple["ContextBuilder", str]:
        """Add to cache and return builder + cache key."""
        key = self._manager.add_cached(content, source)
        return self, key

    def build(self) -> str:
        """Build the final context string."""
        return self._manager.build_context()

    def get_manager(self) -> ContextManager:
        """Get the underlying context manager."""
        return self._manager

    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return self._manager.get_stats()


# Convenience functions
def create_context(
    ground_rules: str,
    project_context: str,
    current_task: str,
    files: Optional[List[Tuple[str, str, float]]] = None,
    budget: int = 128000
) -> str:
    """
    Create a context string with common configuration.

    Args:
        ground_rules: Ground rules content
        project_context: Project context content
        current_task: Current task description
        files: List of (content, path, relevance) tuples
        budget: Total token budget

    Returns:
        Constructed context string
    """
    builder = (ContextBuilder()
        .with_budget(budget)
        .add_ground_rules(ground_rules)
        .add_project_context(project_context)
        .add_current_task(current_task))

    if files:
        for content, path, relevance in files:
            builder.add_file(content, path, relevance)

    return builder.build()


def estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return len(text) // 4 + 1
