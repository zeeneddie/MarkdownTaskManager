"""
Context Compressor for Confucius orchestrator.

Provides adaptive context compression using LLM summarization
to reduce token usage while preserving important information.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class RelevanceLevel(Enum):
    """Relevance levels for context keys."""
    CRITICAL = "critical"  # Always keep verbatim
    HIGH = "high"          # Keep verbatim if space allows
    MEDIUM = "medium"      # Summarize
    LOW = "low"            # Drop if needed


@dataclass
class CompressionResult:
    """Result of context compression."""
    original_tokens: int
    compressed_tokens: int
    reduction_percent: float
    compressed_context: Dict[str, Any]
    kept_keys: List[str]
    summarized_keys: List[str]
    dropped_keys: List[str]

    @property
    def is_effective(self) -> bool:
        """Check if compression was effective (>20% reduction)."""
        return self.reduction_percent > 20.0


@dataclass
class RelevanceRule:
    """Rule for determining relevance of a context key."""
    key_pattern: str  # Exact match or prefix with *
    level: RelevanceLevel
    description: str


# Default relevance rules
DEFAULT_RELEVANCE_RULES = [
    # Critical - never compress
    RelevanceRule("task", RelevanceLevel.CRITICAL, "Main task description"),
    RelevanceRule("error*", RelevanceLevel.CRITICAL, "Error information"),
    RelevanceRule("critical*", RelevanceLevel.CRITICAL, "Critical findings"),

    # High - keep if possible
    RelevanceRule("code", RelevanceLevel.HIGH, "Source code"),
    RelevanceRule("findings", RelevanceLevel.HIGH, "Analysis findings"),
    RelevanceRule("architecture", RelevanceLevel.HIGH, "Architecture info"),
    RelevanceRule("requirements", RelevanceLevel.HIGH, "Requirements"),

    # Medium - summarize
    RelevanceRule("context", RelevanceLevel.MEDIUM, "General context"),
    RelevanceRule("history", RelevanceLevel.MEDIUM, "Historical data"),
    RelevanceRule("related*", RelevanceLevel.MEDIUM, "Related information"),
    RelevanceRule("previous*", RelevanceLevel.MEDIUM, "Previous results"),
    RelevanceRule("memory", RelevanceLevel.MEDIUM, "Memory context"),

    # Low - drop if needed
    RelevanceRule("metadata", RelevanceLevel.LOW, "Metadata"),
    RelevanceRule("debug*", RelevanceLevel.LOW, "Debug information"),
    RelevanceRule("raw*", RelevanceLevel.LOW, "Raw data"),
    RelevanceRule("_*", RelevanceLevel.LOW, "Internal keys"),
]


class ContextCompressor:
    """
    Adaptive context compression using relevance scoring and LLM summarization.

    Strategy:
    1. Score each context key by relevance rules
    2. Keep CRITICAL keys verbatim
    3. Keep HIGH keys if under budget
    4. Summarize MEDIUM keys
    5. Drop LOW keys if needed
    6. Maintain reasoning chains
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
        rules: Optional[List[RelevanceRule]] = None,
        max_summary_ratio: float = 0.3,
    ):
        """
        Initialize compressor.

        Args:
            llm_service: LLM service for summarization (optional)
            rules: Custom relevance rules (uses defaults if not provided)
            max_summary_ratio: Target ratio for summarization (0.3 = 30% of original)
        """
        self.llm_service = llm_service
        self.rules = rules or DEFAULT_RELEVANCE_RULES
        self.max_summary_ratio = max_summary_ratio

    async def compress(
        self,
        context: Dict[str, Any],
        target_tokens: int,
        preserve_keys: Optional[List[str]] = None,
    ) -> CompressionResult:
        """
        Compress context to target token count.

        Args:
            context: Context dictionary to compress
            target_tokens: Target maximum token count
            preserve_keys: Keys to always preserve (added to CRITICAL)

        Returns:
            CompressionResult with compressed context and metadata
        """
        original_tokens = self._estimate_tokens(context)

        # If already under target, return as-is
        if original_tokens <= target_tokens:
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                reduction_percent=0.0,
                compressed_context=context,
                kept_keys=list(context.keys()),
                summarized_keys=[],
                dropped_keys=[],
            )

        # Score relevance of each key
        scored_keys = self._score_all_keys(context, preserve_keys or [])

        # Build compressed context
        compressed = {}
        kept_keys = []
        summarized_keys = []
        dropped_keys = []
        current_tokens = 0

        # Phase 1: Keep all CRITICAL keys
        for key, (value, level) in scored_keys.items():
            if level == RelevanceLevel.CRITICAL:
                compressed[key] = value
                kept_keys.append(key)
                current_tokens += self._estimate_tokens({key: value})

        # Phase 2: Add HIGH keys if under budget
        high_budget = target_tokens * 0.6  # 60% for high priority
        for key, (value, level) in scored_keys.items():
            if level == RelevanceLevel.HIGH and key not in compressed:
                key_tokens = self._estimate_tokens({key: value})
                if current_tokens + key_tokens <= high_budget:
                    compressed[key] = value
                    kept_keys.append(key)
                    current_tokens += key_tokens

        # Phase 3: Summarize MEDIUM keys
        medium_budget = target_tokens * 0.3  # 30% for summaries
        for key, (value, level) in scored_keys.items():
            if level == RelevanceLevel.MEDIUM and key not in compressed:
                if current_tokens < target_tokens - 100:  # Leave some buffer
                    summary = await self._summarize_value(key, value)
                    summary_key = f"{key}_summary"
                    summary_tokens = self._estimate_tokens({summary_key: summary})

                    if current_tokens + summary_tokens <= target_tokens * 0.9:
                        compressed[summary_key] = summary
                        summarized_keys.append(key)
                        current_tokens += summary_tokens
                else:
                    dropped_keys.append(key)

        # Phase 4: Mark dropped LOW keys
        for key, (value, level) in scored_keys.items():
            if key not in compressed and key not in summarized_keys:
                dropped_keys.append(key)

        # Add compression metadata
        compressed["_compression_info"] = {
            "original_keys": list(context.keys()),
            "kept": kept_keys,
            "summarized": summarized_keys,
            "dropped": dropped_keys,
        }

        compressed_tokens = self._estimate_tokens(compressed)
        reduction = ((original_tokens - compressed_tokens) / original_tokens) * 100

        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_percent=reduction,
            compressed_context=compressed,
            kept_keys=kept_keys,
            summarized_keys=summarized_keys,
            dropped_keys=dropped_keys,
        )

    def _score_all_keys(
        self,
        context: Dict[str, Any],
        preserve_keys: List[str],
    ) -> Dict[str, tuple[Any, RelevanceLevel]]:
        """Score relevance of all context keys."""
        scored = {}

        for key, value in context.items():
            # Preserved keys are always CRITICAL
            if key in preserve_keys:
                scored[key] = (value, RelevanceLevel.CRITICAL)
                continue

            # Match against rules
            level = self._get_relevance_level(key)
            scored[key] = (value, level)

        return scored

    def _get_relevance_level(self, key: str) -> RelevanceLevel:
        """Get relevance level for a key based on rules."""
        key_lower = key.lower()

        for rule in self.rules:
            pattern = rule.key_pattern.lower()

            # Wildcard matching
            if pattern.endswith("*"):
                if key_lower.startswith(pattern[:-1]):
                    return rule.level
            # Exact matching
            elif key_lower == pattern:
                return rule.level

        # Default to MEDIUM
        return RelevanceLevel.MEDIUM

    async def _summarize_value(self, key: str, value: Any) -> str:
        """
        Summarize a context value.

        Uses LLM if available, otherwise falls back to truncation.
        """
        value_str = self._value_to_string(value)

        # If value is already short, return as-is
        if len(value_str) < 500:
            return value_str

        # Use LLM for summarization if available
        if self.llm_service:
            try:
                prompt = f"""Summarize the following {key} in 2-3 concise sentences,
preserving the most important information for code analysis and development tasks:

{value_str[:3000]}

Summary:"""
                summary = await self.llm_service.generate(prompt)
                return summary.strip()
            except Exception as e:
                logger.warning(f"LLM summarization failed: {e}")

        # Fallback: intelligent truncation
        return self._intelligent_truncate(value_str, max_length=500)

    def _intelligent_truncate(self, text: str, max_length: int = 500) -> str:
        """
        Truncate text intelligently at sentence boundaries.
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")

        # Use the later of period or newline
        boundary = max(last_period, last_newline)

        if boundary > max_length * 0.5:  # Only if we keep at least half
            return truncated[:boundary + 1] + " [truncated]"

        return truncated + "... [truncated]"

    def _value_to_string(self, value: Any) -> str:
        """Convert any value to string representation."""
        if isinstance(value, str):
            return value
        elif isinstance(value, (list, dict)):
            return json.dumps(value, indent=2, default=str)
        else:
            return str(value)

    def _estimate_tokens(self, data: Any) -> int:
        """
        Estimate token count for data.

        Uses rough approximation of 4 characters per token.
        """
        if isinstance(data, dict):
            text = json.dumps(data, default=str)
        else:
            text = str(data)

        return len(text) // 4

    def get_relevance_score(self, key: str) -> float:
        """
        Get numeric relevance score for a key (0.0 - 1.0).
        """
        level = self._get_relevance_level(key)
        scores = {
            RelevanceLevel.CRITICAL: 1.0,
            RelevanceLevel.HIGH: 0.8,
            RelevanceLevel.MEDIUM: 0.5,
            RelevanceLevel.LOW: 0.2,
        }
        return scores.get(level, 0.5)


class AdaptiveCompressor(ContextCompressor):
    """
    Enhanced compressor that learns from usage patterns.

    Tracks which keys are frequently accessed and adjusts relevance accordingly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._access_counts: Dict[str, int] = {}
        self._quality_impact: Dict[str, float] = {}

    def record_key_access(self, key: str) -> None:
        """Record that a key was accessed/used."""
        self._access_counts[key] = self._access_counts.get(key, 0) + 1

    def record_quality_impact(self, key: str, quality_delta: float) -> None:
        """Record impact of a key on quality score."""
        current = self._quality_impact.get(key, 0.0)
        # Running average
        self._quality_impact[key] = (current + quality_delta) / 2

    def _get_relevance_level(self, key: str) -> RelevanceLevel:
        """Override to consider usage patterns."""
        base_level = super()._get_relevance_level(key)

        # Boost frequently accessed keys
        access_count = self._access_counts.get(key, 0)
        if access_count > 10 and base_level == RelevanceLevel.MEDIUM:
            return RelevanceLevel.HIGH

        # Boost keys with positive quality impact
        quality_impact = self._quality_impact.get(key, 0.0)
        if quality_impact > 0.1 and base_level == RelevanceLevel.MEDIUM:
            return RelevanceLevel.HIGH

        return base_level
