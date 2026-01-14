"""Unit tests for BaseAgentExtension."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.confucius.extensions.base import (
    BaseAgentExtension,
    ExtensionMetadata,
    ExtensionResult,
)


class MockExtension(BaseAgentExtension):
    """Mock extension for testing."""

    def __init__(self, return_value: dict = None):
        super().__init__(ExtensionMetadata(
            name="MockAgent",
            description="Test mock agent",
            capabilities=["testing", "mocking"],
            domains=["test", "mock"],
            priority=5,
        ))
        self.return_value = return_value or {"result": "success"}

    async def execute(self, task: str, context: dict) -> dict:
        return self.return_value


class TestExtensionMetadata:
    """Tests for ExtensionMetadata."""

    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = ExtensionMetadata(
            name="Felix",
            description="Architecture agent",
            capabilities=["architecture_analysis", "dependency_mapping"],
            domains=["architecture", "design"],
            priority=1,
        )

        assert metadata.name == "Felix"
        assert metadata.priority == 1
        assert metadata.parallel_safe is True
        assert metadata.timeout_seconds == 60

    def test_matches_task_domain_match(self):
        """Test task matching by domain."""
        metadata = ExtensionMetadata(
            name="Felix",
            description="Architecture agent",
            capabilities=["architecture_analysis"],
            domains=["architecture", "design"],
        )

        score = metadata.matches_task("Analyze the architecture", {})
        assert score >= 0.3

    def test_matches_task_capability_match(self):
        """Test task matching by capability."""
        metadata = ExtensionMetadata(
            name="Quinn",
            description="Quality agent",
            capabilities=["code_review", "quality_analysis"],
            domains=["quality"],
        )

        score = metadata.matches_task("Do a code review", {})
        assert score >= 0.2

    def test_matches_task_no_match(self):
        """Test task matching with no match."""
        metadata = ExtensionMetadata(
            name="Felix",
            description="Architecture agent",
            capabilities=["architecture_analysis"],
            domains=["architecture"],
        )

        score = metadata.matches_task("Write documentation", {})
        assert score == 0.0


class TestBaseAgentExtension:
    """Tests for BaseAgentExtension."""

    def test_extension_properties(self):
        """Test extension properties."""
        ext = MockExtension()

        assert ext.name == "MockAgent"
        assert ext.priority == 5

    def test_set_orchestrator(self):
        """Test setting orchestrator reference."""
        ext = MockExtension()
        mock_orchestrator = MagicMock()

        ext.set_orchestrator(mock_orchestrator)

        assert ext._orchestrator == mock_orchestrator

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute method."""
        ext = MockExtension({"custom": "result"})

        result = await ext.execute("test task", {})

        assert result == {"custom": "result"}

    @pytest.mark.asyncio
    async def test_on_input_messages_default(self):
        """Test default on_input_messages (passthrough)."""
        ext = MockExtension()
        context = {"key": "value"}

        result = await ext.on_input_messages("task", context)

        assert result == context

    @pytest.mark.asyncio
    async def test_on_llm_output_default(self):
        """Test default on_llm_output (passthrough)."""
        ext = MockExtension()
        output = {"result": "test"}

        result = await ext.on_llm_output(output)

        assert result == output

    @pytest.mark.asyncio
    async def test_on_execute_default(self):
        """Test default on_execute (passthrough)."""
        ext = MockExtension()
        output = {"parsed": "data"}

        result = await ext.on_execute(output)

        assert result == output

    @pytest.mark.asyncio
    async def test_on_post_default(self):
        """Test default on_post (passthrough)."""
        ext = MockExtension()
        output = {"final": "output"}

        result = await ext.on_post(output, "entry-123")

        assert result == output

    def test_partial_result_management(self):
        """Test partial result management."""
        ext = MockExtension()

        ext.update_partial({"step1": "done"})
        ext.update_partial({"step2": "done"})

        partial = ext.get_partial()
        assert partial == {"step1": "done", "step2": "done"}

        ext.clear_partial()
        assert ext.get_partial() == {}

    def test_execution_timing(self):
        """Test execution timing."""
        ext = MockExtension()

        ext.start_execution()
        duration = ext.get_execution_duration_ms()

        assert duration >= 0

    @pytest.mark.asyncio
    async def test_run_full_lifecycle_success(self):
        """Test running full lifecycle successfully."""
        ext = MockExtension({"analysis": "complete"})

        result = await ext.run_full_lifecycle("analyze", {"context": "data"}, "entry-123")

        assert result.extension_name == "MockAgent"
        assert result.success is True
        assert result.output == {"analysis": "complete"}
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_run_full_lifecycle_failure(self):
        """Test running full lifecycle with failure."""

        class FailingExtension(MockExtension):
            async def execute(self, task, context):
                raise ValueError("Test error")

        ext = FailingExtension()

        result = await ext.run_full_lifecycle("fail", {}, "entry-123")

        assert result.success is False
        assert "Test error" in result.error

    def test_matches_task(self):
        """Test task matching delegation."""
        ext = MockExtension()

        score = ext.matches_task("Run a test with mock data", {})

        assert score > 0  # Should match "test" and "mock" domains


class TestExtensionResult:
    """Tests for ExtensionResult."""

    def test_result_creation(self):
        """Test creating an extension result."""
        result = ExtensionResult(
            extension_name="Felix",
            success=True,
            output={"architecture": "microservices"},
            duration_ms=1500,
        )

        assert result.extension_name == "Felix"
        assert result.success is True
        assert result.error is None

    def test_result_to_dict(self):
        """Test result serialization."""
        result = ExtensionResult(
            extension_name="Quinn",
            success=False,
            output={},
            duration_ms=500,
            error="Timeout",
        )

        data = result.to_dict()

        assert data["extension"] == "Quinn"
        assert data["success"] is False
        assert data["error"] == "Timeout"
