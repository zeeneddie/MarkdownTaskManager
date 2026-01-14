"""Unit tests for ContextCompressor."""

import pytest
from app.confucius.memory.compressor import (
    ContextCompressor,
    CompressionResult,
    RelevanceLevel,
    RelevanceRule,
    AdaptiveCompressor,
)


class TestRelevanceLevel:
    """Tests for RelevanceLevel enum."""

    def test_levels(self):
        """Test relevance level values."""
        assert RelevanceLevel.CRITICAL.value == "critical"
        assert RelevanceLevel.HIGH.value == "high"
        assert RelevanceLevel.MEDIUM.value == "medium"
        assert RelevanceLevel.LOW.value == "low"


class TestCompressionResult:
    """Tests for CompressionResult."""

    def test_creation(self):
        """Test creating a compression result."""
        result = CompressionResult(
            original_tokens=1000,
            compressed_tokens=300,
            reduction_percent=70.0,
            compressed_context={"key": "value"},
            kept_keys=["key"],
            summarized_keys=[],
            dropped_keys=["other"],
        )

        assert result.original_tokens == 1000
        assert result.compressed_tokens == 300
        assert result.is_effective is True  # >20% reduction

    def test_not_effective(self):
        """Test ineffective compression."""
        result = CompressionResult(
            original_tokens=1000,
            compressed_tokens=900,
            reduction_percent=10.0,
            compressed_context={},
            kept_keys=[],
            summarized_keys=[],
            dropped_keys=[],
        )

        assert result.is_effective is False


class TestContextCompressor:
    """Tests for ContextCompressor."""

    @pytest.fixture
    def compressor(self):
        """Create a compressor for testing."""
        return ContextCompressor()

    @pytest.mark.asyncio
    async def test_no_compression_needed(self, compressor):
        """Test when context is already under target."""
        context = {"task": "test", "code": "small"}

        result = await compressor.compress(context, target_tokens=10000)

        assert result.reduction_percent == 0.0
        assert result.compressed_context == context

    @pytest.mark.asyncio
    async def test_keeps_critical_keys(self, compressor):
        """Test that critical keys are always kept."""
        context = {
            "task": "Important task",
            "error": "Some error occurred",
            "metadata": "Can be dropped" * 100,
        }

        result = await compressor.compress(context, target_tokens=200)

        assert "task" in result.kept_keys
        assert "error" in result.kept_keys

    @pytest.mark.asyncio
    async def test_drops_low_priority_keys(self, compressor):
        """Test that low priority keys are dropped when needed."""
        context = {
            "task": "Important",
            "_internal": "Internal data" * 100,
            "debug_info": "Debug data" * 100,
            "metadata": "Metadata" * 100,
        }

        result = await compressor.compress(context, target_tokens=100)

        # Low priority keys should be dropped
        assert "_internal" in result.dropped_keys or "debug_info" in result.dropped_keys

    @pytest.mark.asyncio
    async def test_summarizes_medium_keys(self, compressor):
        """Test that medium priority keys are summarized."""
        context = {
            "task": "Test",
            "context": "Very long context " * 100,
            "history": "Historical data " * 100,
        }

        result = await compressor.compress(context, target_tokens=300)

        # Medium keys should be summarized (appears as *_summary)
        has_summary = any(k.endswith("_summary") for k in result.compressed_context.keys())
        assert has_summary or "context" in result.dropped_keys

    @pytest.mark.asyncio
    async def test_preserve_keys(self, compressor):
        """Test preserving specific keys."""
        context = {
            "custom_key": "Important value" * 50,
            "other_key": "Less important" * 50,
        }

        result = await compressor.compress(
            context,
            target_tokens=200,
            preserve_keys=["custom_key"],
        )

        assert "custom_key" in result.kept_keys

    def test_relevance_score(self, compressor):
        """Test getting relevance score."""
        assert compressor.get_relevance_score("task") == 1.0  # Critical
        assert compressor.get_relevance_score("code") == 0.8  # High
        assert compressor.get_relevance_score("context") == 0.5  # Medium
        assert compressor.get_relevance_score("metadata") == 0.2  # Low

    def test_get_relevance_level(self, compressor):
        """Test getting relevance level for keys."""
        # Critical keys
        assert compressor._get_relevance_level("task") == RelevanceLevel.CRITICAL
        assert compressor._get_relevance_level("error_message") == RelevanceLevel.CRITICAL
        assert compressor._get_relevance_level("critical_findings") == RelevanceLevel.CRITICAL

        # High keys
        assert compressor._get_relevance_level("code") == RelevanceLevel.HIGH
        assert compressor._get_relevance_level("findings") == RelevanceLevel.HIGH

        # Medium keys
        assert compressor._get_relevance_level("context") == RelevanceLevel.MEDIUM
        assert compressor._get_relevance_level("history") == RelevanceLevel.MEDIUM
        assert compressor._get_relevance_level("related_items") == RelevanceLevel.MEDIUM

        # Low keys
        assert compressor._get_relevance_level("metadata") == RelevanceLevel.LOW
        assert compressor._get_relevance_level("debug_data") == RelevanceLevel.LOW
        assert compressor._get_relevance_level("_internal") == RelevanceLevel.LOW

    def test_custom_rules(self):
        """Test custom relevance rules."""
        custom_rules = [
            RelevanceRule("my_critical", RelevanceLevel.CRITICAL, "Custom critical"),
            RelevanceRule("project*", RelevanceLevel.HIGH, "Project data"),
        ]

        compressor = ContextCompressor(rules=custom_rules)

        assert compressor._get_relevance_level("my_critical") == RelevanceLevel.CRITICAL
        assert compressor._get_relevance_level("project_data") == RelevanceLevel.HIGH

    def test_token_estimation(self, compressor):
        """Test token estimation."""
        # Roughly 4 chars per token
        tokens = compressor._estimate_tokens({"key": "a" * 400})
        assert 80 <= tokens <= 120  # ~100 tokens

    @pytest.mark.asyncio
    async def test_intelligent_truncate(self, compressor):
        """Test intelligent truncation."""
        text = "First sentence. Second sentence. Third sentence. Fourth very long sentence that should be cut off."

        truncated = compressor._intelligent_truncate(text, max_length=60)

        # Should end at sentence boundary
        assert truncated.endswith(".") or truncated.endswith("[truncated]")


class TestAdaptiveCompressor:
    """Tests for AdaptiveCompressor."""

    @pytest.fixture
    def compressor(self):
        """Create an adaptive compressor."""
        return AdaptiveCompressor()

    def test_record_access(self, compressor):
        """Test recording key access."""
        compressor.record_key_access("important_key")
        compressor.record_key_access("important_key")
        compressor.record_key_access("important_key")

        assert compressor._access_counts["important_key"] == 3

    def test_record_quality_impact(self, compressor):
        """Test recording quality impact."""
        compressor.record_quality_impact("helpful_key", 0.2)
        compressor.record_quality_impact("helpful_key", 0.4)

        assert compressor._quality_impact["helpful_key"] > 0

    def test_boosted_relevance(self, compressor):
        """Test that frequently accessed keys get boosted relevance."""
        # Access key many times
        for _ in range(15):
            compressor.record_key_access("frequently_used")

        # Should be boosted from MEDIUM to HIGH
        level = compressor._get_relevance_level("frequently_used")
        assert level == RelevanceLevel.HIGH

    def test_quality_impact_boost(self, compressor):
        """Test that positive quality impact boosts relevance."""
        compressor.record_quality_impact("quality_key", 0.3)
        compressor.record_quality_impact("quality_key", 0.3)

        level = compressor._get_relevance_level("quality_key")
        assert level == RelevanceLevel.HIGH
