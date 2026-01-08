"""
Tests for Graph Workflow Service - Week 88

Tests for:
1. Impact Analysis (NEW_FEATURE, MAINTENANCE)
2. Dependency Check (BUG)
3. Coupling Metrics (QUALITY_AUDIT, QUALITY_IMPROVEMENT)
4. Test Coverage Map (TESTING)
5. Enhancement Scope (ENHANCEMENT)
6. CodeWiki Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.services.graph_workflow_service import (
    GraphWorkflowService,
    WorkflowType,
    get_graph_workflow_service
)


class TestGraphWorkflowServiceInit:
    """Test service initialization."""

    def test_service_creation(self, async_db_session):
        """Test service can be created."""
        service = GraphWorkflowService(async_db_session)
        assert service.db == async_db_session
        assert service._graph_service is None
        assert service._codewiki_service is None

    def test_factory_function(self, async_db_session):
        """Test factory function returns service."""
        service = get_graph_workflow_service(async_db_session)
        assert isinstance(service, GraphWorkflowService)


class TestWorkflowType:
    """Test WorkflowType enum."""

    def test_workflow_types_exist(self):
        """Test all workflow types are defined."""
        assert WorkflowType.GREEN_PAPER == "GREEN_PAPER"
        assert WorkflowType.BROWN_PAPER == "BROWN_PAPER"
        assert WorkflowType.NEW_FEATURE == "NEW_FEATURE"
        assert WorkflowType.BUG == "BUG"
        assert WorkflowType.MAINTENANCE == "MAINTENANCE"
        assert WorkflowType.MIGRATION == "MIGRATION"
        assert WorkflowType.QUALITY_AUDIT == "QUALITY_AUDIT"
        assert WorkflowType.QUALITY_IMPROVEMENT == "QUALITY_IMPROVEMENT"
        assert WorkflowType.TESTING == "TESTING"
        assert WorkflowType.ENHANCEMENT == "ENHANCEMENT"
        assert WorkflowType.PROJECT_DEFINITION == "PROJECT_DEFINITION"


class TestImpactAnalysis:
    """Test graph_impact_analysis for NEW_FEATURE and MAINTENANCE."""

    @pytest.mark.asyncio
    async def test_impact_analysis_basic(self, async_db_session):
        """Test basic impact analysis call."""
        service = GraphWorkflowService(async_db_session)

        # Mock graph service
        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 100,
            "total_relations": 200,
            "total_files": 50,
        })
        mock_graph.search_entities = AsyncMock(return_value=[])
        service._graph_service = mock_graph

        result = await service.graph_impact_analysis(
            project_id=1,
            changes=["UserService"],
            workflow_type="NEW_FEATURE"
        )

        assert result["workflow_type"] == "NEW_FEATURE"
        assert result["project_id"] == 1
        assert result["changes_analyzed"] == 1
        assert "impact_summary" in result
        assert "risk_assessment" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_impact_analysis_with_entities(self, async_db_session):
        """Test impact analysis with found entities."""
        service = GraphWorkflowService(async_db_session)

        entity_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 100,
        })
        mock_graph.search_entities = AsyncMock(return_value=[
            {"id": str(entity_id), "name": "UserService", "type": "class"}
        ])
        mock_graph.get_impact_analysis = AsyncMock(return_value={
            "affected_entities": [
                {"id": str(uuid4()), "name": "UserController", "depth": 1}
            ],
            "affected_files": ["user_controller.py"],
            "depth": 1
        })
        service._graph_service = mock_graph

        result = await service.graph_impact_analysis(
            project_id=1,
            changes=["UserService"],
            workflow_type="MAINTENANCE"
        )

        assert result["impact_summary"]["total_affected"] == 1
        assert len(result["affected_files"]) == 1
        assert "user_controller.py" in result["affected_files"]

    @pytest.mark.asyncio
    async def test_impact_analysis_empty_graph(self, async_db_session):
        """Test impact analysis with empty graph."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 0,
        })
        service._graph_service = mock_graph

        result = await service.graph_impact_analysis(
            project_id=1,
            changes=["UserService"]
        )

        assert "warning" in result
        assert "Graph not synced" in result["warning"]


class TestRiskCalculation:
    """Test risk calculation methods."""

    def test_calculate_impact_risk_low(self, async_db_session):
        """Test low risk calculation."""
        service = GraphWorkflowService(async_db_session)

        risk = service._calculate_impact_risk(
            total_affected=2,
            affected_files=2,
            max_depth=1,
            project_total=100
        )

        assert risk["level"] == "low"
        assert risk["score"] < 25

    def test_calculate_impact_risk_medium(self, async_db_session):
        """Test medium risk calculation."""
        service = GraphWorkflowService(async_db_session)

        risk = service._calculate_impact_risk(
            total_affected=8,
            affected_files=6,
            max_depth=2,
            project_total=100
        )

        assert risk["level"] == "medium"
        assert 25 <= risk["score"] < 50

    def test_calculate_impact_risk_high(self, async_db_session):
        """Test high risk calculation."""
        service = GraphWorkflowService(async_db_session)

        risk = service._calculate_impact_risk(
            total_affected=30,
            affected_files=25,
            max_depth=4,
            project_total=100
        )

        assert risk["level"] in ("high", "critical")
        assert risk["score"] >= 50


class TestDependencyCheck:
    """Test graph_dependency_check for BUG workflow."""

    @pytest.mark.asyncio
    async def test_dependency_check_basic(self, async_db_session):
        """Test basic dependency check."""
        service = GraphWorkflowService(async_db_session)

        entity_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.search_entities = AsyncMock(return_value=[
            {"id": str(entity_id), "name": "buggy_function", "type": "function"}
        ])
        mock_graph.get_direct_dependencies = AsyncMock(return_value={
            "dependencies": [
                {"id": str(uuid4()), "name": "helper_func", "type": "function"}
            ]
        })
        mock_graph.get_dependents = AsyncMock(return_value={
            "dependents": [
                {"id": str(uuid4()), "name": "caller_func", "type": "function"}
            ]
        })
        mock_graph.detect_circular_dependencies = AsyncMock(return_value={
            "cycles": []
        })
        service._graph_service = mock_graph

        result = await service.graph_dependency_check(
            project_id=1,
            entity_name="buggy_function"
        )

        assert result["workflow_type"] == "BUG"
        assert result["entity_found"] is True
        assert len(result["upstream_dependencies"]) == 1
        assert len(result["downstream_dependents"]) == 1
        assert "investigation_hints" in result

    @pytest.mark.asyncio
    async def test_dependency_check_entity_not_found(self, async_db_session):
        """Test dependency check when entity not found."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.search_entities = AsyncMock(return_value=[])
        service._graph_service = mock_graph

        result = await service.graph_dependency_check(
            project_id=1,
            entity_name="nonexistent"
        )

        assert result["entity_found"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_dependency_check_with_circular(self, async_db_session):
        """Test dependency check with circular dependency."""
        service = GraphWorkflowService(async_db_session)

        entity_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.search_entities = AsyncMock(return_value=[
            {"id": str(entity_id), "name": "circular_entity", "type": "class"}
        ])
        mock_graph.get_direct_dependencies = AsyncMock(return_value={"dependencies": []})
        mock_graph.get_dependents = AsyncMock(return_value={"dependents": []})
        mock_graph.detect_circular_dependencies = AsyncMock(return_value={
            "cycles": [
                {"entities": [{"name": "circular_entity"}, {"name": "other"}]}
            ]
        })
        service._graph_service = mock_graph

        result = await service.graph_dependency_check(
            project_id=1,
            entity_name="circular_entity"
        )

        assert len(result["circular_dependencies"]) == 1
        assert any("CIRCULAR" in hint for hint in result["investigation_hints"])


class TestCouplingMetrics:
    """Test graph_coupling_metrics for QUALITY_AUDIT and QUALITY_IMPROVEMENT."""

    @pytest.mark.asyncio
    async def test_coupling_metrics_basic(self, async_db_session):
        """Test basic coupling metrics."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_module_coupling = AsyncMock(return_value={
            "total_modules": 10,
            "total_connections": 25,
            "total_coupling_strength": 100,
            "average_coupling": 4.0,
        })
        mock_graph.get_highly_coupled_modules = AsyncMock(return_value=[])
        mock_graph.detect_circular_dependencies = AsyncMock(return_value={
            "cycles": [],
            "cycles_found": 0
        })
        service._graph_service = mock_graph

        result = await service.graph_coupling_metrics(
            project_id=1,
            coupling_threshold=10
        )

        assert result["workflow_type"] == "QUALITY_AUDIT"
        assert result["coupling_summary"]["total_modules"] == 10
        assert result["quality_score"] >= 70  # No high coupling or circular deps
        assert "improvement_suggestions" in result

    @pytest.mark.asyncio
    async def test_coupling_metrics_with_issues(self, async_db_session):
        """Test coupling metrics with quality issues."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_module_coupling = AsyncMock(return_value={
            "total_modules": 10,
            "average_coupling": 20.0,  # High coupling
        })
        mock_graph.get_highly_coupled_modules = AsyncMock(return_value=[
            {"source_module": "module_a", "target_module": "module_b", "coupling_count": 50}
        ])
        mock_graph.detect_circular_dependencies = AsyncMock(return_value={
            "cycles": [{"entities": []}],
            "cycles_found": 1
        })
        service._graph_service = mock_graph

        result = await service.graph_coupling_metrics(project_id=1)

        assert result["quality_score"] < 70
        assert len(result["high_coupling_modules"]) > 0
        assert len(result["circular_dependencies"]) > 0
        assert len(result["improvement_suggestions"]) > 0


class TestTestCoverageMap:
    """Test graph_test_coverage_map for TESTING workflow."""

    @pytest.mark.asyncio
    async def test_coverage_map_basic(self, async_db_session):
        """Test basic test coverage map."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 100,
            "top_referenced_entities": [
                {"id": str(uuid4()), "name": "UserService", "type": "class", "references": 15},
                {"id": str(uuid4()), "name": "AuthService", "type": "class", "references": 10},
            ]
        })
        mock_graph.search_entities = AsyncMock(return_value=[
            {"name": "test_UserService", "file_path": "tests/test_user.py"}
        ])
        service._graph_service = mock_graph

        result = await service.graph_test_coverage_map(project_id=1)

        assert result["workflow_type"] == "TESTING"
        assert "coverage_summary" in result
        assert "test_priorities" in result

    @pytest.mark.asyncio
    async def test_coverage_map_empty_graph(self, async_db_session):
        """Test coverage map with empty graph."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 0
        })
        service._graph_service = mock_graph

        result = await service.graph_test_coverage_map(project_id=1)

        assert "warning" in result


class TestEnhancementScope:
    """Test graph_enhancement_scope for ENHANCEMENT workflow."""

    @pytest.mark.asyncio
    async def test_enhancement_scope_basic(self, async_db_session):
        """Test basic enhancement scope."""
        service = GraphWorkflowService(async_db_session)

        entity_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.search_entities = AsyncMock(return_value=[
            {"id": str(entity_id), "name": "PaymentService", "file_path": "services/payment.py"}
        ])
        mock_graph.get_direct_dependencies = AsyncMock(return_value={
            "dependencies": []
        })
        mock_graph.get_dependents = AsyncMock(return_value={
            "dependents": []
        })
        service._graph_service = mock_graph

        result = await service.graph_enhancement_scope(
            project_id=1,
            feature_name="payment_improvements"
        )

        assert result["workflow_type"] == "ENHANCEMENT"
        assert result["feature_name"] == "payment_improvements"
        assert "scope_analysis" in result
        assert "dependency_analysis" in result
        assert "risk_assessment" in result
        assert "enhancement_plan" in result

    @pytest.mark.asyncio
    async def test_enhancement_scope_large(self, async_db_session):
        """Test enhancement scope with large scope."""
        service = GraphWorkflowService(async_db_session)

        # Generate many entities
        entities = [
            {"id": str(uuid4()), "name": f"Entity{i}", "file_path": f"module{i % 5}/file.py"}
            for i in range(25)
        ]

        mock_graph = MagicMock()
        mock_graph.search_entities = AsyncMock(return_value=entities)
        mock_graph.get_direct_dependencies = AsyncMock(return_value={
            "dependencies": [{"name": "dep", "file_path": "other/module.py"}]
        })
        mock_graph.get_dependents = AsyncMock(return_value={
            "dependents": [{"name": "dependent", "file_path": "caller/module.py"}]
        })
        service._graph_service = mock_graph

        result = await service.graph_enhancement_scope(
            project_id=1,
            feature_name="big_refactor"
        )

        assert result["risk_assessment"]["level"] in ("medium", "high")
        assert len(result["enhancement_plan"]) > 0


class TestCodeWikiIntegration:
    """Test CodeWiki integration methods."""

    @pytest.mark.asyncio
    async def test_sync_and_document(self, async_db_session):
        """Test sync and document integration."""
        service = GraphWorkflowService(async_db_session)

        # Mock graph service
        mock_graph = MagicMock()
        mock_graph.sync_project_graph = AsyncMock(return_value={
            "success": True,
            "entities_added": 50,
            "relations_added": 100
        })
        service._graph_service = mock_graph

        # Mock codewiki service
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.status = MagicMock()
        mock_analysis.status.value = "completed"
        mock_analysis.total_modules = 10
        mock_analysis.total_files = 50
        mock_analysis.languages_detected = ["python"]

        mock_codewiki = MagicMock()
        mock_codewiki.create_analysis = MagicMock(return_value=mock_analysis)
        mock_codewiki.run_analysis = AsyncMock(return_value=mock_analysis)
        service._codewiki_service = mock_codewiki

        result = await service.sync_and_document(
            project_id=1,
            repo_path="/path/to/repo"
        )

        assert "graph_sync" in result
        assert "codewiki_analysis" in result
        assert result["graph_sync"]["success"] is True
        assert result["codewiki_analysis"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_workflow_context(self, async_db_session):
        """Test workflow context retrieval."""
        service = GraphWorkflowService(async_db_session)

        mock_graph = MagicMock()
        mock_graph.get_project_statistics = AsyncMock(return_value={
            "total_entities": 100,
            "total_relations": 200,
            "total_files": 50,
            "top_referenced_entities": []
        })
        mock_graph.get_module_coupling = AsyncMock(return_value={
            "total_modules": 10,
            "average_coupling": 5.0
        })
        service._graph_service = mock_graph

        mock_codewiki = MagicMock()
        mock_codewiki.get_latest_analysis = MagicMock(return_value=None)
        service._codewiki_service = mock_codewiki

        result = await service.get_workflow_context(
            project_id=1,
            workflow_type="QUALITY_AUDIT"
        )

        assert "graph_context" in result
        assert "codewiki_context" in result
        assert result["graph_context"]["total_entities"] == 100


class TestBugHints:
    """Test bug investigation hint generation."""

    def test_generate_bug_hints_circular(self, async_db_session):
        """Test hints for circular dependency."""
        service = GraphWorkflowService(async_db_session)

        hints = service._generate_bug_hints(
            entity={"name": "test", "type": "class"},
            upstream=[],
            downstream=[],
            circular=[{"entities": []}]
        )

        assert any("CIRCULAR" in hint for hint in hints)

    def test_generate_bug_hints_high_deps(self, async_db_session):
        """Test hints for high dependency count."""
        service = GraphWorkflowService(async_db_session)

        hints = service._generate_bug_hints(
            entity={"name": "test", "type": "function"},
            upstream=[{} for _ in range(15)],  # 15 upstream deps
            downstream=[],
            circular=[]
        )

        assert any("HIGH DEPENDENCY" in hint for hint in hints)

    def test_generate_bug_hints_high_dependents(self, async_db_session):
        """Test hints for many dependents."""
        service = GraphWorkflowService(async_db_session)

        hints = service._generate_bug_hints(
            entity={"name": "test", "type": "class"},
            upstream=[],
            downstream=[{} for _ in range(15)],  # 15 dependents
            circular=[]
        )

        assert any("HIGH DEPENDENTS" in hint for hint in hints)


class TestEnhancementPlan:
    """Test enhancement plan generation."""

    def test_generate_plan_low_risk(self, async_db_session):
        """Test plan for low risk enhancement."""
        service = GraphWorkflowService(async_db_session)

        scope = {
            "entities_in_scope": [{"name": "entity1"}],
            "files_affected": ["file1.py"],
            "modules_affected": ["module1"]
        }
        risk = {"level": "low", "score": 10, "factors": []}

        plan = service._generate_enhancement_plan(scope, risk, "small_change")

        assert len(plan) >= 2  # At least write tests and integration
        assert plan[0]["action"] == "Write Tests First"

    def test_generate_plan_high_risk(self, async_db_session):
        """Test plan for high risk enhancement."""
        service = GraphWorkflowService(async_db_session)

        scope = {
            "entities_in_scope": [{"name": f"entity{i}"} for i in range(10)],
            "files_affected": [f"file{i}.py" for i in range(10)],
            "modules_affected": ["module1", "module2", "module3"]
        }
        risk = {"level": "high", "score": 70, "factors": ["Large scope"]}

        plan = service._generate_enhancement_plan(scope, risk, "big_refactor")

        # High risk should include feature branch step
        assert any("Feature Branch" in step["action"] for step in plan)
        assert any("Incrementally" in step["action"] for step in plan)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def async_db_session():
    """Mock async database session."""
    return AsyncMock()
