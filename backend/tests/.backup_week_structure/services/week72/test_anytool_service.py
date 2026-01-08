"""
Week 72: AnyTool Universal Tool Calling Service Tests

Tests for intelligent tool orchestration with:
- Multi-stage filtering
- Semantic search
- Automatic failover
- Quality tracking
- Learning from feedback
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.anytool_service import AnyToolService, ToolBackend


class TestToolBackendConstants:
    """Tests for ToolBackend enumeration."""

    def test_mcp_backend(self):
        assert ToolBackend.MCP == "mcp"

    def test_shell_backend(self):
        assert ToolBackend.SHELL == "shell"

    def test_gui_backend(self):
        assert ToolBackend.GUI == "gui"

    def test_web_backend(self):
        assert ToolBackend.WEB == "web"

    def test_system_backend(self):
        assert ToolBackend.SYSTEM == "system"


class TestAnyToolServiceInit:
    """Tests for AnyToolService initialization."""

    def test_init_creates_service(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)
        assert service.db == mock_db
        assert isinstance(service._embedding_cache, dict)
        assert isinstance(service._tool_rankings, dict)
        assert isinstance(service._failover_history, dict)

    def test_semantic_thresholds(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)
        assert service.SEMANTIC_THRESHOLD_HIGH == 0.85
        assert service.SEMANTIC_THRESHOLD_MEDIUM == 0.65
        assert service.SEMANTIC_THRESHOLD_LOW == 0.45

    def test_category_keywords_exist(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)
        assert "file" in service.CATEGORY_KEYWORDS
        assert "code" in service.CATEGORY_KEYWORDS
        assert "browser" in service.CATEGORY_KEYWORDS
        assert "search" in service.CATEGORY_KEYWORDS
        assert "system" in service.CATEGORY_KEYWORDS

    def test_backend_config_exists(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)
        assert ToolBackend.MCP in service.BACKEND_CONFIG
        assert "timeout" in service.BACKEND_CONFIG[ToolBackend.MCP]
        assert "retry_count" in service.BACKEND_CONFIG[ToolBackend.MCP]


class TestNameBasedFiltering:
    """Tests for name-based tool filtering."""

    def test_filter_by_exact_name_match(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Create mock tools
        tool1 = MagicMock()
        tool1.tool_name = "read_file"
        tool1.description = "Read a file from disk"
        tool1.category = "file"
        tool1.tags = ["file", "read"]

        tool2 = MagicMock()
        tool2.tool_name = "write_file"
        tool2.description = "Write to a file"
        tool2.category = "file"
        tool2.tags = ["file", "write"]

        tools = [tool1, tool2]
        filtered = service._filter_by_name(tools, "read_file")

        assert len(filtered) >= 1
        assert filtered[0].tool_name == "read_file"

    def test_filter_by_word_match(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "browser_navigate"
        tool1.description = "Navigate to URL"
        tool1.category = "browser"
        tool1.tags = ["web", "navigate"]

        tools = [tool1]
        filtered = service._filter_by_name(tools, "navigate to page")

        assert len(filtered) >= 1
        assert filtered[0].tool_name == "browser_navigate"

    def test_filter_returns_empty_for_no_match(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "database_query"
        tool1.description = "Execute SQL query"
        tool1.category = "database"
        tool1.tags = ["sql", "query"]

        tools = [tool1]
        filtered = service._filter_by_name(tools, "xyz123notexist")

        assert len(filtered) == 0

    def test_filter_by_category_match(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "some_file_tool"
        tool1.description = "A tool for files"
        tool1.category = "file"
        tool1.tags = []

        tools = [tool1]
        # "read" is in file category keywords
        filtered = service._filter_by_name(tools, "read something")

        assert len(filtered) >= 1

    def test_filter_by_tag_match(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "generic_tool"
        tool1.description = "Generic description"
        tool1.category = None
        tool1.tags = ["special_tag"]

        tools = [tool1]
        filtered = service._filter_by_name(tools, "special_tag query")

        assert len(filtered) >= 1


class TestSemanticSimilarity:
    """Tests for semantic similarity scoring."""

    @pytest.mark.asyncio
    async def test_score_semantic_similarity_basic(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "read_file"
        tool1.description = "Read contents from a file"
        tool1.tags = ["file", "read"]
        tool1.category = "file"

        tools = [tool1]
        scored = await service._score_semantic_similarity(tools, "read file contents")

        assert len(scored) == 1
        assert scored[0][0] == tool1
        assert 0 <= scored[0][1] <= 1.0

    @pytest.mark.asyncio
    async def test_score_semantic_similarity_ordering(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.tool_name = "read_file"
        tool1.description = "Read contents from a file"
        tool1.tags = ["file", "read"]
        tool1.category = "file"

        tool2 = MagicMock()
        tool2.tool_name = "database_query"
        tool2.description = "Execute SQL query"
        tool2.tags = ["sql", "database"]
        tool2.category = "database"

        tools = [tool2, tool1]
        scored = await service._score_semantic_similarity(tools, "read file")

        # File tool should score higher for "read file" query
        assert len(scored) == 2
        file_tool_score = next(s[1] for s in scored if s[0].tool_name == "read_file")
        db_tool_score = next(s[1] for s in scored if s[0].tool_name == "database_query")
        assert file_tool_score > db_tool_score


class TestQualityRanking:
    """Tests for quality-based ranking."""

    def test_rank_by_quality_basic(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.id = uuid4()
        tool1.server_id = uuid4()
        tool1.tool_name = "fast_tool"
        tool1.description = "Fast tool"
        tool1.category = "file"
        tool1.success_rate = 0.95
        tool1.total_executions = 100
        tool1.avg_latency_ms = 100

        scored_tools = [(tool1, 0.8)]
        ranked = service._rank_by_quality(scored_tools)

        assert len(ranked) == 1
        assert "final_score" in ranked[0]
        assert "quality_score" in ranked[0]
        assert "semantic_score" in ranked[0]

    def test_rank_by_quality_with_context(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool1 = MagicMock()
        tool1.id = uuid4()
        tool1.server_id = uuid4()
        tool1.tool_name = "file_tool"
        tool1.description = "File tool"
        tool1.category = "file"
        tool1.success_rate = 0.9
        tool1.total_executions = 50
        tool1.avg_latency_ms = 200

        scored_tools = [(tool1, 0.7)]
        context = {"preferred_category": "file", "recent_tools": ["file_tool"]}
        ranked = service._rank_by_quality(scored_tools, context)

        assert len(ranked) == 1
        # Context boost should increase score
        assert ranked[0]["final_score"] > 0.5

    def test_rank_by_quality_latency_penalty(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Fast tool - MagicMock with spec to avoid hasattr returning True for to_dict
        tool1 = MagicMock(spec=['id', 'server_id', 'tool_name', 'description', 'category', 'success_rate', 'total_executions', 'avg_latency_ms'])
        tool1.id = uuid4()
        tool1.server_id = uuid4()
        tool1.tool_name = "fast_tool"
        tool1.description = "Fast"
        tool1.category = "file"
        tool1.success_rate = 0.9
        tool1.total_executions = 100
        tool1.avg_latency_ms = 100

        # Slow tool
        tool2 = MagicMock(spec=['id', 'server_id', 'tool_name', 'description', 'category', 'success_rate', 'total_executions', 'avg_latency_ms'])
        tool2.id = uuid4()
        tool2.server_id = uuid4()
        tool2.tool_name = "slow_tool"
        tool2.description = "Slow"
        tool2.category = "file"
        tool2.success_rate = 0.9
        tool2.total_executions = 100
        tool2.avg_latency_ms = 6000

        scored_tools = [(tool1, 0.8), (tool2, 0.8)]
        ranked = service._rank_by_quality(scored_tools)

        # Find scores by checking tool dict
        fast_score = None
        slow_score = None
        for r in ranked:
            tool_name = r["tool"].get("tool_name")
            if tool_name == "fast_tool":
                fast_score = r["final_score"]
            elif tool_name == "slow_tool":
                slow_score = r["final_score"]

        assert fast_score is not None
        assert slow_score is not None
        assert fast_score > slow_score

    def test_rank_by_quality_confidence_calculation(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # New tool (low confidence)
        tool1 = MagicMock(spec=['id', 'server_id', 'tool_name', 'description', 'category', 'success_rate', 'total_executions', 'avg_latency_ms'])
        tool1.id = uuid4()
        tool1.server_id = uuid4()
        tool1.tool_name = "new_tool"
        tool1.description = "New"
        tool1.category = "file"
        tool1.success_rate = 1.0
        tool1.total_executions = 5
        tool1.avg_latency_ms = 100

        # Established tool (high confidence)
        tool2 = MagicMock(spec=['id', 'server_id', 'tool_name', 'description', 'category', 'success_rate', 'total_executions', 'avg_latency_ms'])
        tool2.id = uuid4()
        tool2.server_id = uuid4()
        tool2.tool_name = "established_tool"
        tool2.description = "Established"
        tool2.category = "file"
        tool2.success_rate = 0.95
        tool2.total_executions = 200
        tool2.avg_latency_ms = 100

        scored_tools = [(tool1, 0.8), (tool2, 0.8)]
        ranked = service._rank_by_quality(scored_tools)

        # Find confidence values by checking tool dict
        new_confidence = None
        est_confidence = None
        for r in ranked:
            tool_name = r["tool"].get("tool_name")
            if tool_name == "new_tool":
                new_confidence = r["confidence"]
            elif tool_name == "established_tool":
                est_confidence = r["confidence"]

        assert new_confidence is not None
        assert est_confidence is not None
        assert new_confidence < est_confidence


class TestFailoverTracking:
    """Tests for failover tracking."""

    def test_record_failover_creates_entry(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool_id = uuid4()
        service._record_failover(tool_id)

        assert str(tool_id) in service._failover_history
        assert len(service._failover_history[str(tool_id)]) == 1

    def test_record_failover_accumulates(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool_id = uuid4()
        service._record_failover(tool_id)
        service._record_failover(tool_id)
        service._record_failover(tool_id)

        assert len(service._failover_history[str(tool_id)]) == 3

    def test_record_failover_prunes_old_entries(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool_id = uuid4()
        tool_key = str(tool_id)

        # Add an old entry
        old_time = datetime.now() - timedelta(hours=48)
        service._failover_history[tool_key] = [old_time]

        # Record new failover
        service._record_failover(tool_id)

        # Old entry should be pruned
        assert len(service._failover_history[tool_key]) == 1
        assert service._failover_history[tool_key][0] > datetime.now() - timedelta(hours=24)


class TestToolDiscovery:
    """Tests for tool discovery."""

    @pytest.mark.asyncio
    async def test_discover_tools_empty_when_no_tools(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Mock empty tool list
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await service.discover_tools("read file")
        assert tools == []

    @pytest.mark.asyncio
    async def test_discover_tools_with_max_results(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Create mock tools
        tools_list = []
        for i in range(10):
            tool = MagicMock()
            tool.id = uuid4()
            tool.server_id = uuid4()
            tool.tool_name = f"tool_{i}"
            tool.description = f"Description {i}"
            tool.category = "file"
            tool.tags = ["test"]
            tool.success_rate = 0.9
            tool.total_executions = 50
            tool.avg_latency_ms = 100
            tools_list.append(tool)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tools_list
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await service.discover_tools("tool", max_results=5)
        assert len(tools) <= 5


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_no_tools_found(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Mock empty tool discovery
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.execute_tool(
            query="nonexistent tool",
            params={"key": "value"}
        )

        assert result["status"] == "failed"
        assert "No tools found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_single_tool_not_found(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._execute_single_tool(
            tool_id=uuid4(),
            params={"key": "value"}
        )

        assert result["status"] == "failed"
        assert "Tool not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_single_tool_server_unavailable(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Mock tool exists but server is inactive
        mock_tool = MagicMock()
        mock_tool.server_id = uuid4()

        mock_server = MagicMock()
        mock_server.is_active = False

        mock_tool_result = MagicMock()
        mock_tool_result.scalar_one_or_none.return_value = mock_tool

        mock_server_result = MagicMock()
        mock_server_result.scalar_one_or_none.return_value = mock_server

        mock_db.execute = AsyncMock(side_effect=[mock_tool_result, mock_server_result])

        result = await service._execute_single_tool(
            tool_id=uuid4(),
            params={"key": "value"}
        )

        assert result["status"] == "failed"
        assert "Server unavailable" in result["error"]


class TestStdioExecution:
    """Tests for stdio tool execution."""

    @pytest.mark.asyncio
    async def test_execute_stdio_tool_placeholder(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_server = MagicMock()
        mock_server.name = "test_server"

        mock_tool = MagicMock()
        mock_tool.tool_name = "test_tool"

        result = await service._execute_stdio_tool(mock_server, mock_tool, {"key": "value"})

        assert result["status"] == "success"
        assert "Simulated" in result["result"]
        assert result["backend"] == ToolBackend.MCP


class TestHttpExecution:
    """Tests for HTTP tool execution."""

    @pytest.mark.asyncio
    async def test_execute_http_tool_placeholder(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_server = MagicMock()
        mock_server.name = "http_server"

        mock_tool = MagicMock()
        mock_tool.tool_name = "http_tool"

        result = await service._execute_http_tool(mock_server, mock_tool, {"url": "test"})

        assert result["status"] == "success"
        assert "HTTP call" in result["result"]
        assert result["backend"] == ToolBackend.MCP


class TestDockerExecution:
    """Tests for Docker tool execution."""

    @pytest.mark.asyncio
    async def test_execute_docker_tool_placeholder(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_server = MagicMock()
        mock_server.name = "docker_server"

        mock_tool = MagicMock()
        mock_tool.tool_name = "docker_tool"

        result = await service._execute_docker_tool(mock_server, mock_tool, {"container": "test"})

        assert result["status"] == "success"
        assert "Docker execution" in result["result"]
        assert result["backend"] == ToolBackend.MCP


class TestReliabilityStats:
    """Tests for reliability statistics."""

    @pytest.mark.asyncio
    async def test_get_reliability_stats_empty(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_reliability_stats(hours=24)

        assert stats["period_hours"] == 24
        assert stats["tools"] == {}
        assert stats["total_executions"] == 0

    @pytest.mark.asyncio
    async def test_get_reliability_stats_with_data(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        tool_id = uuid4()
        mock_row1 = MagicMock(tool_id=tool_id, status="success", count=80)
        mock_row2 = MagicMock(tool_id=tool_id, status="failed", count=20)

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_reliability_stats(hours=24)

        assert stats["period_hours"] == 24
        assert str(tool_id) in stats["tools"]
        assert stats["tools"][str(tool_id)]["success"] == 80
        assert stats["tools"][str(tool_id)]["failed"] == 20
        assert stats["tools"][str(tool_id)]["success_rate"] == 0.8


class TestToolSuggestions:
    """Tests for tool suggestions."""

    @pytest.mark.asyncio
    async def test_get_tool_suggestions_empty(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        suggestions = await service.get_tool_suggestions(task_type="code_analysis")

        assert suggestions == []

    @pytest.mark.asyncio
    async def test_get_tool_suggestions_with_results(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_row = MagicMock(tool_name="popular_tool", usage_count=100, avg_success=0.95)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)

        suggestions = await service.get_tool_suggestions(task_type="code_analysis")

        assert len(suggestions) == 1
        assert suggestions[0]["tool_name"] == "popular_tool"
        assert suggestions[0]["usage_count"] == 100
        assert suggestions[0]["success_rate"] == 0.95


class TestFeedbackLearning:
    """Tests for learning from feedback."""

    @pytest.mark.asyncio
    async def test_learn_from_feedback_tool_not_found(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.learn_from_feedback(
            tool_id=uuid4(),
            feedback="Great tool",
            rating=5
        )

        assert result["status"] == "error"
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_learn_from_feedback_positive(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_tool = MagicMock()
        mock_tool.tool_name = "test_tool"
        mock_tool.success_rate = 0.9

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tool
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.learn_from_feedback(
            tool_id=uuid4(),
            feedback="Great tool",
            rating=5
        )

        assert result["status"] == "success"
        assert result["tool_name"] == "test_tool"
        # Success rate should increase
        assert mock_tool.success_rate > 0.9

    @pytest.mark.asyncio
    async def test_learn_from_feedback_negative(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_tool = MagicMock()
        mock_tool.tool_name = "test_tool"
        mock_tool.success_rate = 0.9

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tool
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.learn_from_feedback(
            tool_id=uuid4(),
            feedback="Tool failed me",
            rating=1
        )

        assert result["status"] == "success"
        # Success rate should decrease
        assert mock_tool.success_rate < 0.9

    @pytest.mark.asyncio
    async def test_learn_from_feedback_neutral(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_tool = MagicMock()
        mock_tool.tool_name = "test_tool"
        mock_tool.success_rate = 0.9

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tool
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await service.learn_from_feedback(
            tool_id=uuid4(),
            feedback="It's okay",
            rating=3
        )

        assert result["status"] == "success"
        # Success rate should remain the same for neutral rating
        assert mock_tool.success_rate == 0.9


class TestSystemStatus:
    """Tests for system status."""

    @pytest.mark.asyncio
    async def test_get_system_status_healthy(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Mock server stats
        mock_server_row = MagicMock(total=5, active=4, healthy=3)
        mock_server_result = MagicMock()
        mock_server_result.one.return_value = mock_server_row

        # Mock tool stats
        mock_tool_row = MagicMock(total=50, enabled=45)
        mock_tool_result = MagicMock()
        mock_tool_result.one.return_value = mock_tool_row

        # Mock reliability stats
        mock_reliability_result = MagicMock()
        mock_reliability_result.all.return_value = []

        mock_db.execute = AsyncMock(
            side_effect=[mock_server_result, mock_tool_result, mock_reliability_result]
        )

        status = await service.get_system_status()

        assert status["status"] == "healthy"
        assert status["servers"]["total"] == 5
        assert status["servers"]["active"] == 4
        assert status["servers"]["healthy"] == 3
        assert status["tools"]["total"] == 50
        assert status["tools"]["enabled"] == 45
        assert "multi_stage_filtering" in status["features"]
        assert status["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_system_status_degraded(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # Mock server stats with no healthy servers
        mock_server_row = MagicMock(total=5, active=2, healthy=0)
        mock_server_result = MagicMock()
        mock_server_result.one.return_value = mock_server_row

        # Mock tool stats
        mock_tool_row = MagicMock(total=50, enabled=10)
        mock_tool_result = MagicMock()
        mock_tool_result.one.return_value = mock_tool_row

        # Mock reliability stats
        mock_reliability_result = MagicMock()
        mock_reliability_result.all.return_value = []

        mock_db.execute = AsyncMock(
            side_effect=[mock_server_result, mock_tool_result, mock_reliability_result]
        )

        status = await service.get_system_status()

        assert status["status"] == "degraded"


class TestExecutionRecording:
    """Tests for execution recording."""

    @pytest.mark.asyncio
    async def test_record_execution_success(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_tool = MagicMock()
        mock_tool.id = uuid4()
        mock_tool.total_executions = 10
        mock_tool.success_rate = 0.9

        mock_server = MagicMock()
        mock_server.id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = {"status": "success", "result": "test output"}

        await service._record_execution(
            tool=mock_tool,
            server=mock_server,
            params={"key": "value"},
            result=result,
            agent_id="felix",
            task_id=uuid4()
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        assert mock_tool.total_executions == 11

    @pytest.mark.asyncio
    async def test_record_execution_failure(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        mock_tool = MagicMock()
        mock_tool.id = uuid4()
        mock_tool.total_executions = 10
        mock_tool.success_rate = 0.9

        mock_server = MagicMock()
        mock_server.id = uuid4()

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = {"status": "failed", "error": "test error"}

        await service._record_execution(
            tool=mock_tool,
            server=mock_server,
            params={"key": "value"},
            result=result
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        assert mock_tool.total_executions == 11
        # Success rate should decrease
        assert mock_tool.success_rate < 0.9


class TestCategoryKeywords:
    """Tests for category keyword matching."""

    def test_file_category_keywords(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        file_keywords = service.CATEGORY_KEYWORDS["file"]
        assert "read" in file_keywords
        assert "write" in file_keywords
        assert "file" in file_keywords

    def test_code_category_keywords(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        code_keywords = service.CATEGORY_KEYWORDS["code"]
        assert "analyze" in code_keywords
        assert "parse" in code_keywords
        assert "test" in code_keywords

    def test_browser_category_keywords(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        browser_keywords = service.CATEGORY_KEYWORDS["browser"]
        assert "navigate" in browser_keywords
        assert "click" in browser_keywords
        assert "screenshot" in browser_keywords

    def test_database_category_keywords(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        db_keywords = service.CATEGORY_KEYWORDS["database"]
        assert "sql" in db_keywords
        assert "query" in db_keywords
        assert "table" in db_keywords


class TestBackendConfiguration:
    """Tests for backend configuration."""

    def test_mcp_backend_timeout(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        assert service.BACKEND_CONFIG[ToolBackend.MCP]["timeout"] == 30
        assert service.BACKEND_CONFIG[ToolBackend.MCP]["retry_count"] == 2

    def test_shell_backend_timeout(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        assert service.BACKEND_CONFIG[ToolBackend.SHELL]["timeout"] == 60

    def test_gui_backend_timeout(self):
        mock_db = MagicMock()
        service = AnyToolService(mock_db)

        # GUI has longer timeout
        assert service.BACKEND_CONFIG[ToolBackend.GUI]["timeout"] == 120
