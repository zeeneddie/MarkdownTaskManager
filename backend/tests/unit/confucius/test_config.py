"""Unit tests for Confucius configuration."""

import pytest
import os
from app.confucius.config import (
    ConfuciusConfig,
    MemoryConfig,
    QualityConfig,
    ExtensionConfig,
    StreamingConfig,
    NoteTakingConfig,
    CompressionStrategy,
)


class TestCompressionStrategy:
    """Tests for CompressionStrategy enum."""

    def test_strategy_values(self):
        """Test compression strategy values."""
        assert CompressionStrategy.NONE.value == "none"
        assert CompressionStrategy.SUMMARIZE.value == "summarize"
        assert CompressionStrategy.TRUNCATE.value == "truncate"
        assert CompressionStrategy.ADAPTIVE.value == "adaptive"


class TestMemoryConfig:
    """Tests for MemoryConfig."""

    def test_default_values(self):
        """Test default memory config values."""
        config = MemoryConfig()

        assert config.session_retention_days == -1  # Permanent
        assert config.entry_retention_days == 30
        assert config.runnable_retention_days == 7
        assert config.compression_strategy == CompressionStrategy.ADAPTIVE
        assert config.compression_threshold_tokens == 100000

    def test_custom_values(self):
        """Test custom memory config values."""
        config = MemoryConfig(
            entry_retention_days=60,
            compression_strategy=CompressionStrategy.SUMMARIZE,
        )

        assert config.entry_retention_days == 60
        assert config.compression_strategy == CompressionStrategy.SUMMARIZE


class TestQualityConfig:
    """Tests for QualityConfig."""

    def test_default_values(self):
        """Test default quality config values."""
        config = QualityConfig()

        assert config.default_threshold == 0.85
        assert config.critical_threshold == 0.5
        assert config.max_iterations == 3

    def test_get_threshold(self):
        """Test getting domain-specific threshold."""
        config = QualityConfig()

        assert config.get_threshold("architecture") == 0.85
        assert config.get_threshold("estimation") == 0.90
        assert config.get_threshold("unknown") == 0.85  # Falls back to default

    def test_custom_domain_thresholds(self):
        """Test custom domain thresholds."""
        config = QualityConfig(
            domain_thresholds={"custom": 0.95}
        )

        assert config.get_threshold("custom") == 0.95


class TestExtensionConfig:
    """Tests for ExtensionConfig."""

    def test_default_values(self):
        """Test default extension config values."""
        config = ExtensionConfig()

        assert config.default_timeout_seconds == 60
        assert config.max_timeout_seconds == 300
        assert config.enable_parallel_execution is True
        assert config.max_parallel_extensions == 5
        assert config.min_match_score == 0.3


class TestStreamingConfig:
    """Tests for StreamingConfig."""

    def test_default_values(self):
        """Test default streaming config values."""
        config = StreamingConfig()

        assert config.enabled is True
        assert config.heartbeat_interval_seconds == 15
        assert config.buffer_size == 100


class TestNoteTakingConfig:
    """Tests for NoteTakingConfig."""

    def test_default_values(self):
        """Test default note-taking config values."""
        config = NoteTakingConfig()

        assert config.enabled is True
        assert config.auto_record_threshold == 0.7
        assert config.max_notes_per_session == 100


class TestConfuciusConfig:
    """Tests for main ConfuciusConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = ConfuciusConfig.default()

        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.memory is not None
        assert config.quality is not None

    def test_minimal_config(self):
        """Test minimal configuration."""
        config = ConfuciusConfig.minimal()

        assert config.memory.compression_strategy == CompressionStrategy.NONE
        assert config.quality.max_iterations == 1
        assert config.streaming.enabled is False
        assert config.note_taking.enabled is False

    def test_feature_flags(self):
        """Test feature flag checking."""
        config = ConfuciusConfig.default()

        assert config.is_feature_enabled("hierarchical_memory") is True
        assert config.is_feature_enabled("nonexistent_feature") is False

    def test_to_dict(self):
        """Test config serialization."""
        config = ConfuciusConfig.default()
        data = config.to_dict()

        assert "memory" in data
        assert "quality" in data
        assert "features" in data
        assert data["quality"]["default_threshold"] == 0.85

    def test_from_env(self, monkeypatch):
        """Test loading config from environment."""
        monkeypatch.setenv("CONFUCIUS_QUALITY_THRESHOLD", "0.90")
        monkeypatch.setenv("CONFUCIUS_MAX_ITERATIONS", "5")
        monkeypatch.setenv("CONFUCIUS_DEBUG", "true")

        config = ConfuciusConfig.from_env()

        assert config.quality.default_threshold == 0.90
        assert config.quality.max_iterations == 5
        assert config.debug_mode is True

    def test_custom_config(self):
        """Test fully custom configuration."""
        config = ConfuciusConfig(
            memory=MemoryConfig(entry_retention_days=90),
            quality=QualityConfig(default_threshold=0.95),
            extensions=ExtensionConfig(default_timeout_seconds=120),
            debug_mode=True,
            features={"custom_feature": True},
        )

        assert config.memory.entry_retention_days == 90
        assert config.quality.default_threshold == 0.95
        assert config.extensions.default_timeout_seconds == 120
        assert config.debug_mode is True
        assert config.is_feature_enabled("custom_feature") is True
