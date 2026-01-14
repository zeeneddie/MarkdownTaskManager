"""
Confucius Orchestrator Configuration.

Provides configuration management for the orchestrator including:
- Quality thresholds
- Memory settings
- Timeout configurations
- Feature flags
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import os


class CompressionStrategy(Enum):
    """Context compression strategies."""
    NONE = "none"
    SUMMARIZE = "summarize"  # LLM-based summarization
    TRUNCATE = "truncate"    # Simple truncation
    ADAPTIVE = "adaptive"    # Intelligent compression based on content


@dataclass
class MemoryConfig:
    """Memory subsystem configuration."""
    # Retention periods (days)
    session_retention_days: int = -1  # -1 = permanent
    entry_retention_days: int = 30
    runnable_retention_days: int = 7

    # Compression
    compression_strategy: CompressionStrategy = CompressionStrategy.ADAPTIVE
    compression_threshold_tokens: int = 100000
    max_summary_ratio: float = 0.3  # Target 30% of original size

    # Retrieval
    max_relevant_entries: int = 5
    max_relevant_runnables: int = 10
    max_session_insights: int = 10
    max_session_patterns: int = 5

    # Cleanup
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24


@dataclass
class QualityConfig:
    """Quality gate configuration."""
    # Thresholds
    default_threshold: float = 0.85
    critical_threshold: float = 0.5  # Below this = immediate failure

    # Iteration
    max_iterations: int = 3
    iteration_feedback_enabled: bool = True

    # Domain-specific thresholds
    domain_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "architecture": 0.85,
        "stability": 0.80,
        "estimation": 0.90,
        "quality": 0.85,
        "documentation": 0.75,
    })

    def get_threshold(self, domain: str) -> float:
        """Get threshold for a specific domain."""
        return self.domain_thresholds.get(domain, self.default_threshold)


@dataclass
class ExtensionConfig:
    """Extension subsystem configuration."""
    # Timeouts
    default_timeout_seconds: int = 60
    max_timeout_seconds: int = 300

    # Parallelism
    enable_parallel_execution: bool = True
    max_parallel_extensions: int = 5

    # Routing
    min_match_score: float = 0.3  # Minimum score to consider an extension
    max_extensions_per_task: int = 5


@dataclass
class StreamingConfig:
    """SSE streaming configuration."""
    enabled: bool = True
    heartbeat_interval_seconds: int = 15
    buffer_size: int = 100


@dataclass
class NoteTakingConfig:
    """Note-taking subsystem configuration."""
    enabled: bool = True
    auto_record_threshold: float = 0.7  # Auto-record notes above this quality
    max_notes_per_session: int = 100
    extract_insights_enabled: bool = True


@dataclass
class ConfuciusConfig:
    """
    Main configuration for Confucius Orchestrator.

    Can be loaded from environment variables or passed directly.
    """
    # Subsystem configs
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    extensions: ExtensionConfig = field(default_factory=ExtensionConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    note_taking: NoteTakingConfig = field(default_factory=NoteTakingConfig)

    # General settings
    debug_mode: bool = False
    log_level: str = "INFO"

    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "hierarchical_memory": True,
        "context_compression": True,
        "cross_session_learning": True,
        "quality_gates": True,
        "sse_streaming": True,
        "parallel_extensions": True,
    })

    @classmethod
    def from_env(cls) -> "ConfuciusConfig":
        """Load configuration from environment variables."""
        return cls(
            memory=MemoryConfig(
                compression_threshold_tokens=int(
                    os.getenv("CONFUCIUS_COMPRESSION_THRESHOLD", "100000")
                ),
                entry_retention_days=int(
                    os.getenv("CONFUCIUS_ENTRY_RETENTION_DAYS", "30")
                ),
            ),
            quality=QualityConfig(
                default_threshold=float(
                    os.getenv("CONFUCIUS_QUALITY_THRESHOLD", "0.85")
                ),
                max_iterations=int(
                    os.getenv("CONFUCIUS_MAX_ITERATIONS", "3")
                ),
            ),
            extensions=ExtensionConfig(
                default_timeout_seconds=int(
                    os.getenv("CONFUCIUS_EXTENSION_TIMEOUT", "60")
                ),
                enable_parallel_execution=os.getenv(
                    "CONFUCIUS_PARALLEL_EXTENSIONS", "true"
                ).lower() == "true",
            ),
            streaming=StreamingConfig(
                enabled=os.getenv(
                    "CONFUCIUS_STREAMING_ENABLED", "true"
                ).lower() == "true",
            ),
            debug_mode=os.getenv("CONFUCIUS_DEBUG", "false").lower() == "true",
            log_level=os.getenv("CONFUCIUS_LOG_LEVEL", "INFO"),
        )

    @classmethod
    def default(cls) -> "ConfuciusConfig":
        """Get default configuration."""
        return cls()

    @classmethod
    def minimal(cls) -> "ConfuciusConfig":
        """Get minimal configuration (for testing)."""
        return cls(
            memory=MemoryConfig(
                compression_strategy=CompressionStrategy.NONE,
                auto_cleanup_enabled=False,
            ),
            quality=QualityConfig(
                max_iterations=1,
                iteration_feedback_enabled=False,
            ),
            extensions=ExtensionConfig(
                enable_parallel_execution=False,
                default_timeout_seconds=30,
            ),
            streaming=StreamingConfig(enabled=False),
            note_taking=NoteTakingConfig(enabled=False),
        )

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.features.get(feature, False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "memory": {
                "compression_threshold_tokens": self.memory.compression_threshold_tokens,
                "compression_strategy": self.memory.compression_strategy.value,
                "entry_retention_days": self.memory.entry_retention_days,
            },
            "quality": {
                "default_threshold": self.quality.default_threshold,
                "max_iterations": self.quality.max_iterations,
            },
            "extensions": {
                "default_timeout_seconds": self.extensions.default_timeout_seconds,
                "enable_parallel_execution": self.extensions.enable_parallel_execution,
            },
            "streaming": {
                "enabled": self.streaming.enabled,
            },
            "features": self.features,
            "debug_mode": self.debug_mode,
        }
