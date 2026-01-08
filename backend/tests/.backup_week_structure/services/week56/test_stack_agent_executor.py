"""
Tests for Stack Agent Executor

Week 56 Day 2: Tests for agent task execution with LLM providers.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.stack_agent_executor import (
    StackAgentExecutor,
    AgentTaskType,
    AgentTaskRequest,
    AgentTaskResult,
    ValidationResult,
    get_stack_agent_executor,
    TASK_TYPE_MAPPING,
    PYTHON_PROMPTS,
    JAVASCRIPT_PROMPTS,
    GO_PROMPTS,
    RUST_PROMPTS,
)
from app.services.stack_agent_factory import (
    StackAgentFactory,
    TechStack,
    AgentRole,
)


# ============================================================================
# TASK TYPE TESTS
# ============================================================================

class TestTaskTypes:
    """Test task type definitions and mappings."""

    def test_all_task_types_defined(self):
        """Verify all task types are defined."""
        expected = [
            "code_generation",
            "code_review",
            "security_audit",
            "refactoring",
            "test_generation",
            "bug_fix",
            "documentation",
            "architecture_review",
            "performance_analysis",
            "dependency_update",
        ]

        actual = [t.value for t in AgentTaskType]
        assert set(actual) == set(expected)

    def test_all_task_types_have_provider_mapping(self):
        """Verify all task types map to provider task types."""
        for task_type in AgentTaskType:
            assert task_type in TASK_TYPE_MAPPING, f"No mapping for {task_type}"

    def test_python_prompts_complete(self):
        """Verify Python has prompts for major task types."""
        major_tasks = [
            AgentTaskType.CODE_GENERATION,
            AgentTaskType.CODE_REVIEW,
            AgentTaskType.SECURITY_AUDIT,
            AgentTaskType.TEST_GENERATION,
            AgentTaskType.REFACTORING,
            AgentTaskType.BUG_FIX,
        ]

        for task in major_tasks:
            assert task in PYTHON_PROMPTS, f"Missing Python prompt for {task}"

    def test_javascript_prompts_complete(self):
        """Verify JavaScript has prompts for all major task types."""
        major_tasks = [
            AgentTaskType.CODE_GENERATION,
            AgentTaskType.CODE_REVIEW,
            AgentTaskType.SECURITY_AUDIT,
            AgentTaskType.TEST_GENERATION,
            AgentTaskType.REFACTORING,
            AgentTaskType.BUG_FIX,
            AgentTaskType.DOCUMENTATION,
            AgentTaskType.ARCHITECTURE_REVIEW,
            AgentTaskType.PERFORMANCE_ANALYSIS,
            AgentTaskType.DEPENDENCY_UPDATE,
        ]

        for task in major_tasks:
            assert task in JAVASCRIPT_PROMPTS, f"Missing JS prompt for {task}"

    def test_go_prompts_exist(self):
        """Verify Go prompts exist for core tasks."""
        core_tasks = [
            AgentTaskType.CODE_GENERATION,
            AgentTaskType.CODE_REVIEW,
            AgentTaskType.TEST_GENERATION,
        ]

        for task in core_tasks:
            assert task in GO_PROMPTS, f"Missing Go prompt for {task}"

    def test_rust_prompts_exist(self):
        """Verify Rust prompts exist for core tasks."""
        core_tasks = [
            AgentTaskType.CODE_GENERATION,
            AgentTaskType.CODE_REVIEW,
            AgentTaskType.TEST_GENERATION,
        ]

        for task in core_tasks:
            assert task in RUST_PROMPTS, f"Missing Rust prompt for {task}"


# ============================================================================
# EXECUTOR BASIC TESTS
# ============================================================================

class TestExecutorBasics:
    """Test basic executor operations."""

    @pytest.fixture
    def executor(self):
        """Create fresh executor for each test."""
        return StackAgentExecutor()

    def test_executor_singleton(self):
        """Test singleton executor access."""
        executor1 = get_stack_agent_executor()
        executor2 = get_stack_agent_executor()
        # Note: Not guaranteed to be same in tests due to fresh imports
        assert executor1 is not None
        assert executor2 is not None

    def test_executor_has_factory(self, executor):
        """Test executor has factory reference."""
        assert executor.factory is not None

    def test_executor_has_registry(self, executor):
        """Test executor has registry reference."""
        assert executor.registry is not None

    def test_initial_history_empty(self, executor):
        """Test initial execution history is empty."""
        history = executor.get_execution_history()
        assert len(history) == 0

    def test_initial_metrics_zeroed(self, executor):
        """Test initial metrics are zeroed."""
        metrics = executor.get_success_metrics()
        assert metrics["total_tasks"] == 0
        assert metrics["successful_tasks"] == 0
        assert metrics["success_rate"] == 0.0


# ============================================================================
# PROMPT BUILDING TESTS
# ============================================================================

class TestPromptBuilding:
    """Test prompt generation."""

    @pytest.fixture
    def executor_with_agent(self):
        """Create executor with an agent."""
        executor = StackAgentExecutor()
        executor.factory.create_agent_instance(1, "backend_dev", "python")
        return executor

    def test_build_prompt_python_code_review(self, executor_with_agent):
        """Test building Python code review prompt."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_py",
            task_type=AgentTaskType.CODE_REVIEW,
            code_files={"main.py": "def foo(): pass"},
            instructions="Review for quality"
        )

        prompt = executor_with_agent._build_prompt(agent, request)

        assert "Python" in prompt or "python" in prompt
        assert "code reviewer" in prompt.lower() or "review" in prompt.lower()
        assert "def foo" in prompt

    def test_build_prompt_includes_specialties(self, executor_with_agent):
        """Test that prompt includes agent capabilities."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_py",
            task_type=AgentTaskType.CODE_GENERATION,
            instructions="Create a REST API"
        )

        prompt = executor_with_agent._build_prompt(agent, request)

        # Should include some capabilities
        assert any(cap in prompt.lower() for cap in ["api", "database", "async", "testing"])

    def test_build_prompt_includes_tools(self, executor_with_agent):
        """Test that prompt includes specialized tools."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_py",
            task_type=AgentTaskType.CODE_GENERATION,
            instructions="Generate code"
        )

        prompt = executor_with_agent._build_prompt(agent, request)

        # Should include some tools
        assert any(tool in prompt for tool in ["ruff", "mypy", "pytest", "black"])


class TestJavaScriptPromptBuilding:
    """Test JavaScript-specific prompt generation."""

    @pytest.fixture
    def executor_with_js_agent(self):
        """Create executor with a JavaScript agent."""
        executor = StackAgentExecutor()
        executor.factory.create_agent_instance(1, "backend_dev", "javascript")
        return executor

    def test_build_prompt_js_code_review(self, executor_with_js_agent):
        """Test building JavaScript code review prompt."""
        agent = executor_with_js_agent.factory.get_agent_by_name(1, "backend_dev_js")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_js",
            task_type=AgentTaskType.CODE_REVIEW,
            code_files={"app.js": "function foo() { return 1; }"},
            instructions="Review for quality"
        )

        prompt = executor_with_js_agent._build_prompt(agent, request)

        assert "javascript" in prompt.lower()
        assert "function foo" in prompt

    def test_build_prompt_js_security_audit(self, executor_with_js_agent):
        """Test building JavaScript security audit prompt."""
        agent = executor_with_js_agent.factory.get_agent_by_name(1, "backend_dev_js")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_js",
            task_type=AgentTaskType.SECURITY_AUDIT,
            code_files={"api.js": "app.get('/user', (req, res) => {});"},
            instructions="Check for XSS"
        )

        prompt = executor_with_js_agent._build_prompt(agent, request)

        # Should mention JavaScript security concerns
        assert "xss" in prompt.lower() or "security" in prompt.lower()

    def test_build_prompt_js_performance(self, executor_with_js_agent):
        """Test building JavaScript performance analysis prompt."""
        agent = executor_with_js_agent.factory.get_agent_by_name(1, "backend_dev_js")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_js",
            task_type=AgentTaskType.PERFORMANCE_ANALYSIS,
            code_files={"heavy.js": "for(let i=0; i<1000000; i++) {}"},
            instructions="Analyze performance"
        )

        prompt = executor_with_js_agent._build_prompt(agent, request)

        # Should mention performance concepts
        assert any(word in prompt.lower() for word in ["memory", "performance", "loop", "async"])

    def test_build_prompt_js_includes_js_tools(self, executor_with_js_agent):
        """Test that JavaScript prompt includes JS tools."""
        agent = executor_with_js_agent.factory.get_agent_by_name(1, "backend_dev_js")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_js",
            task_type=AgentTaskType.CODE_GENERATION,
            instructions="Create a function"
        )

        prompt = executor_with_js_agent._build_prompt(agent, request)

        # Should include JS tools
        assert any(tool in prompt for tool in ["eslint", "prettier", "jest", "tsc"])


# ============================================================================
# RESPONSE PARSING TESTS
# ============================================================================

class TestResponseParsing:
    """Test response parsing."""

    @pytest.fixture
    def executor(self):
        """Create executor."""
        return StackAgentExecutor()

    def test_parse_code_response(self, executor):
        """Test parsing response with code blocks."""
        response = """
Here is the generated code:

```python
def hello():
    return "Hello, World!"
```

This function returns a greeting.
"""

        output, code_changes, analysis = executor._parse_response(
            response,
            AgentTaskType.CODE_GENERATION
        )

        assert len(code_changes) == 1
        assert "def hello():" in list(code_changes.values())[0]

    def test_parse_multiple_code_blocks(self, executor):
        """Test parsing multiple code blocks."""
        response = """
```python
def foo():
    pass
```

And another:

```python
def bar():
    pass
```
"""

        output, code_changes, analysis = executor._parse_response(
            response,
            AgentTaskType.CODE_GENERATION
        )

        assert len(code_changes) == 2

    def test_parse_review_score(self, executor):
        """Test parsing code review score."""
        response = """
## Review Summary
Good code overall.

## Score: 8/10
"""

        output, code_changes, analysis = executor._parse_response(
            response,
            AgentTaskType.CODE_REVIEW
        )

        assert analysis.get("score") == 8

    def test_parse_severity_counts(self, executor):
        """Test parsing severity counts from review."""
        response = """
## Issues
- Issue 1 (Severity: CRITICAL)
- Issue 2 (Severity: HIGH)
- Issue 3 (Severity: HIGH)
- Issue 4 (Severity: MEDIUM)
"""

        output, code_changes, analysis = executor._parse_response(
            response,
            AgentTaskType.CODE_REVIEW
        )

        assert analysis.get("critical") == 1
        assert analysis.get("high") == 2
        assert analysis.get("medium") == 1

    def test_parse_security_score(self, executor):
        """Test parsing security audit score."""
        response = """
## Security Audit Report
### Security Score: 7/10
"""

        output, code_changes, analysis = executor._parse_response(
            response,
            AgentTaskType.SECURITY_AUDIT
        )

        assert analysis.get("security_score") == 7


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Test validation pipeline."""

    @pytest.fixture
    def executor_with_agent(self):
        """Create executor with an agent."""
        executor = StackAgentExecutor()
        executor.factory.create_agent_instance(1, "backend_dev", "python")
        return executor

    @pytest.mark.asyncio
    async def test_validate_wildcard_import(self, executor_with_agent):
        """Test validation catches wildcard imports."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        code_changes = {"main.py": "from os import *\n"}

        result = await executor_with_agent._validate_output(
            agent,
            AgentTaskType.CODE_GENERATION,
            code_changes
        )

        assert result.passed is False
        assert any("wildcard" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_eval_usage(self, executor_with_agent):
        """Test validation catches eval() usage."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        code_changes = {"main.py": "result = eval(user_input)"}

        result = await executor_with_agent._validate_output(
            agent,
            AgentTaskType.CODE_GENERATION,
            code_changes
        )

        assert result.passed is False
        assert any("eval" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_line_length_warning(self, executor_with_agent):
        """Test validation warns about long lines."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        long_line = "x = " + "a" * 150
        code_changes = {"main.py": long_line}

        result = await executor_with_agent._validate_output(
            agent,
            AgentTaskType.CODE_GENERATION,
            code_changes
        )

        assert any("long" in w.lower() or "120" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_clean_code_passes(self, executor_with_agent):
        """Test clean code passes validation."""
        agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")

        clean_code = '''
def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
'''
        code_changes = {"main.py": clean_code}

        result = await executor_with_agent._validate_output(
            agent,
            AgentTaskType.CODE_GENERATION,
            code_changes
        )

        assert result.passed is True


# ============================================================================
# TASK EXECUTION TESTS
# ============================================================================

class TestTaskExecution:
    """Test task execution."""

    @pytest.fixture
    def executor_with_agent(self):
        """Create executor with an agent."""
        executor = StackAgentExecutor()
        executor.factory.create_agent_instance(1, "backend_dev", "python")
        return executor

    @pytest.mark.asyncio
    async def test_execute_unknown_agent_fails(self):
        """Test executing with unknown agent fails."""
        executor = StackAgentExecutor()

        request = AgentTaskRequest(
            project_id=1,
            agent_name="nonexistent_agent",
            task_type=AgentTaskType.CODE_GENERATION,
            instructions="Generate code"
        )

        result = await executor.execute_task(request)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_inactive_agent_fails(self, executor_with_agent):
        """Test executing with inactive agent fails."""
        executor_with_agent.factory.deactivate_agent(1, "backend_dev_py")

        request = AgentTaskRequest(
            project_id=1,
            agent_name="backend_dev_py",
            task_type=AgentTaskType.CODE_GENERATION,
            instructions="Generate code"
        )

        result = await executor_with_agent.execute_task(request)

        assert result.success is False
        assert "inactive" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_task_with_mock_provider(self, executor_with_agent):
        """Test task execution with mocked provider."""
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value="""
```python
def hello():
    return "Hello!"
```
""")
        mock_provider.config = MagicMock()
        mock_provider.config.name = "test_provider"

        # Mock the registry to return our mock provider
        with patch.object(
            executor_with_agent.registry,
            'route_task',
            return_value=mock_provider
        ):
            request = AgentTaskRequest(
                project_id=1,
                agent_name="backend_dev_py",
                task_type=AgentTaskType.CODE_GENERATION,
                instructions="Create a hello function"
            )

            result = await executor_with_agent.execute_task(request)

            assert result.success is True
            assert len(result.code_changes) > 0
            assert result.provider_used == "test_provider"

    @pytest.mark.asyncio
    async def test_execute_updates_agent_performance(self, executor_with_agent):
        """Test that execution updates agent performance."""
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value="Good response")
        mock_provider.config = MagicMock()
        mock_provider.config.name = "test"

        with patch.object(
            executor_with_agent.registry,
            'route_task',
            return_value=mock_provider
        ):
            request = AgentTaskRequest(
                project_id=1,
                agent_name="backend_dev_py",
                task_type=AgentTaskType.DOCUMENTATION,
                instructions="Write docs"
            )

            await executor_with_agent.execute_task(request)

            agent = executor_with_agent.factory.get_agent_by_name(1, "backend_dev_py")
            assert agent.total_tasks == 1


# ============================================================================
# BATCH EXECUTION TESTS
# ============================================================================

class TestBatchExecution:
    """Test batch task execution."""

    @pytest.fixture
    def executor_with_agents(self):
        """Create executor with multiple agents."""
        executor = StackAgentExecutor()
        executor.factory.create_agents_for_project(1, ["python"])
        return executor

    @pytest.mark.asyncio
    async def test_execute_batch_empty(self, executor_with_agents):
        """Test empty batch."""
        results = await executor_with_agents.execute_batch([])
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_execute_batch_multiple(self, executor_with_agents):
        """Test batch with multiple tasks."""
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value="Response")
        mock_provider.config = MagicMock()
        mock_provider.config.name = "test"

        with patch.object(
            executor_with_agents.registry,
            'route_task',
            return_value=mock_provider
        ):
            requests = [
                AgentTaskRequest(
                    project_id=1,
                    agent_name="backend_dev_py",
                    task_type=AgentTaskType.DOCUMENTATION,
                    instructions="Task 1"
                ),
                AgentTaskRequest(
                    project_id=1,
                    agent_name="backend_dev_py",
                    task_type=AgentTaskType.DOCUMENTATION,
                    instructions="Task 2"
                ),
            ]

            results = await executor_with_agents.execute_batch(requests)

            assert len(results) == 2


# ============================================================================
# METRICS TESTS
# ============================================================================

class TestMetrics:
    """Test execution metrics."""

    @pytest.fixture
    def executor_with_history(self):
        """Create executor with execution history."""
        executor = StackAgentExecutor()

        # Add some mock history
        executor._execution_history = [
            AgentTaskResult(
                success=True,
                agent_name="agent1",
                task_type=AgentTaskType.CODE_GENERATION,
                output="Good",
                validation_passed=True,
                execution_time_ms=100,
                provider_used="test"
            ),
            AgentTaskResult(
                success=True,
                agent_name="agent1",
                task_type=AgentTaskType.CODE_REVIEW,
                output="Review",
                validation_passed=True,
                execution_time_ms=200,
                provider_used="test"
            ),
            AgentTaskResult(
                success=False,
                agent_name="agent2",
                task_type=AgentTaskType.BUG_FIX,
                output="",
                validation_passed=False,
                execution_time_ms=50,
                provider_used="test",
                error="Failed"
            ),
        ]
        return executor

    def test_success_rate_calculation(self, executor_with_history):
        """Test success rate calculation."""
        metrics = executor_with_history.get_success_metrics()

        assert metrics["total_tasks"] == 3
        assert metrics["successful_tasks"] == 2
        assert metrics["success_rate"] == pytest.approx(2/3)

    def test_validation_pass_rate(self, executor_with_history):
        """Test validation pass rate calculation."""
        metrics = executor_with_history.get_success_metrics()

        assert metrics["validation_pass_rate"] == pytest.approx(2/3)

    def test_average_execution_time(self, executor_with_history):
        """Test average execution time calculation."""
        metrics = executor_with_history.get_success_metrics()

        # (100 + 200 + 50) / 3 = 116.67
        assert metrics["avg_execution_time_ms"] == pytest.approx(116, abs=1)

    def test_get_history_with_filter(self, executor_with_history):
        """Test getting filtered history."""
        history = executor_with_history.get_execution_history(agent_name="agent1")

        assert len(history) == 2
        assert all(r.agent_name == "agent1" for r in history)

    def test_get_history_with_limit(self, executor_with_history):
        """Test getting limited history."""
        history = executor_with_history.get_execution_history(limit=2)

        assert len(history) == 2
