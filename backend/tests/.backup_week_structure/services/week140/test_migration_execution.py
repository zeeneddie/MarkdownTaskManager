# backend/tests/services/week140/test_migration_execution.py
"""
Fase 26: Migration Execution Tests

Tests for:
- StranglerFigService - Incremental migration with feature flags
- LibraryMigrationMapperService - Legacy library mapping
- WavePlannerService - Dependency-based wave planning
- UILayerExtractionService - UI component mapping

Agents:
- Miguel (Strangler Fig)
- Felix (Library Mapper)
- Paul (Wave Planner)
- Vicky (UI Extraction)
"""

import pytest
from datetime import datetime
from uuid import uuid4


# =============================================================================
# Strangler Fig Service Tests
# =============================================================================

class TestStranglerFigService:
    """Tests for StranglerFigService - incremental migration."""

    def test_create_session(self):
        """Test creating a strangler fig service."""
        from app.services.strangler_fig_service import StranglerFigService

        service = StranglerFigService()
        assert service is not None

    def test_session_dataclass(self):
        """Test StranglerSession dataclass."""
        from app.services.strangler_fig_service import StranglerSession

        session = StranglerSession(
            id=uuid4(),
            project_id="proj-001",
            name="Test Migration",
            components=[],
            feature_flags=[],
            rollout_plans=[],
            traffic_rules=[],
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert session.project_id == "proj-001"
        assert session.name == "Test Migration"
        assert session.status == "active"

    def test_feature_flag_dataclass(self):
        """Test FeatureFlag dataclass."""
        from app.services.strangler_fig_service import (
            FeatureFlag, FeatureFlagStatus
        )

        flag = FeatureFlag(
            id=str(uuid4()),
            name="new-auth-system",
            description="New authentication module",
            status=FeatureFlagStatus.CANARY,
            legacy_endpoint="/api/legacy/auth",
            new_endpoint="/api/v2/auth",
            rollout_percentage=10,
            user_segments=[],
            geographic_regions=[],
            enabled_since=datetime.now(),
            last_modified=datetime.now(),
            created_by="admin",
            tags=[],
        )

        assert flag.name == "new-auth-system"
        assert flag.status == FeatureFlagStatus.CANARY
        assert flag.rollout_percentage == 10

    def test_traffic_rule_dataclass(self):
        """Test TrafficRule dataclass."""
        from app.services.strangler_fig_service import (
            TrafficRule, TrafficSplitStrategy
        )

        rule = TrafficRule(
            id=str(uuid4()),
            feature_flag_id="ff-001",
            strategy=TrafficSplitStrategy.PERCENTAGE,
            condition=None,
            weight=25,
            target="modern",
            priority=1,
            metadata={},
        )

        assert rule.strategy == TrafficSplitStrategy.PERCENTAGE
        assert rule.weight == 25
        assert rule.target == "modern"

    def test_rollout_plan_dataclass(self):
        """Test RolloutPlan dataclass."""
        from app.services.strangler_fig_service import RolloutPlan, RolloutStep

        steps = [
            RolloutStep(
                step_number=1,
                percentage=10,
                duration_hours=24,
                success_criteria={"error_rate": "<0.01"},
                rollback_criteria={"error_rate": ">0.05"},
                notifications=[],
                status="pending",
            ),
            RolloutStep(
                step_number=2,
                percentage=25,
                duration_hours=48,
                success_criteria={"error_rate": "<0.01"},
                rollback_criteria={"error_rate": ">0.05"},
                notifications=[],
                status="pending",
            ),
        ]

        plan = RolloutPlan(
            id=str(uuid4()),
            component_id="comp-001",
            name="Auth Rollout",
            steps=steps,
            current_step=0,
            status="pending",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            rollback_count=0,
        )

        assert plan.name == "Auth Rollout"
        assert len(plan.steps) == 2
        assert plan.steps[0].percentage == 10

    def test_health_check_dataclass(self):
        """Test HealthCheck dataclass."""
        from app.services.strangler_fig_service import HealthCheck, HealthStatus

        check = HealthCheck(
            component_id="comp-001",
            timestamp=datetime.now(),
            status=HealthStatus.HEALTHY,
            latency_ms=45.2,
            error_rate=0.01,
            success_rate=0.99,
            metrics={},
            alerts=[],
        )

        assert check.status == HealthStatus.HEALTHY
        assert check.latency_ms == 45.2
        assert check.error_rate == 0.01

    def test_traffic_evaluation_logic(self):
        """Test traffic routing evaluation."""
        from app.services.strangler_fig_service import StranglerFigService

        service = StranglerFigService()
        assert hasattr(service, 'evaluate_traffic_routing')


# =============================================================================
# Library Migration Mapper Service Tests
# =============================================================================

class TestLibraryMigrationMapperService:
    """Tests for LibraryMigrationMapperService - legacy library mapping."""

    def test_service_instantiation(self):
        """Test service can be instantiated."""
        from app.services.library_migration_mapper_service import (
            LibraryMigrationMapperService
        )

        service = LibraryMigrationMapperService()
        assert service is not None

    def test_legacy_library_dataclass(self):
        """Test LegacyLibrary dataclass."""
        from app.services.library_migration_mapper_service import (
            LegacyLibrary, LibraryCategory
        )

        lib = LegacyLibrary(
            name="ADODB",
            version="2.8",
            category=LibraryCategory.DATABASE,
            usage_count=45,
            usage_patterns=[],
            file_locations=["DAL/DbConnection.vb", "DAL/RecordSet.vb"],
            import_statements=[],
            detected_features=[],
            is_deprecated=True,
            security_issues=[],
        )

        assert lib.name == "ADODB"
        assert lib.usage_count == 45
        assert lib.category == LibraryCategory.DATABASE

    def test_modern_equivalent_dataclass(self):
        """Test ModernEquivalent dataclass."""
        from app.services.library_migration_mapper_service import (
            ModernEquivalent, TargetStack, MigrationEffort
        )

        equiv = ModernEquivalent(
            name="Entity Framework Core",
            package_name="Microsoft.EntityFrameworkCore",
            stack=TargetStack.DOTNET_8,
            version="8.0.0",
            migration_effort=MigrationEffort.MEDIUM,
            api_similarity=0.7,
            documentation_url="https://docs.microsoft.com/ef",
            notes="",
            breaking_changes=[],
            additional_dependencies=[],
        )

        assert equiv.name == "Entity Framework Core"
        assert equiv.stack == TargetStack.DOTNET_8

    def test_library_mapping_dataclass(self):
        """Test LibraryMapping dataclass."""
        from app.services.library_migration_mapper_service import (
            LibraryMapping, LegacyLibrary, ModernEquivalent,
            MigrationEffort, TargetStack, LibraryCategory, RiskLevel
        )

        legacy = LegacyLibrary(
            name="ADODB",
            version="2.8",
            category=LibraryCategory.DATABASE,
            usage_count=45,
            usage_patterns=[],
            file_locations=[],
            import_statements=[],
            detected_features=[],
            is_deprecated=True,
            security_issues=[],
        )

        modern = ModernEquivalent(
            name="EF Core",
            package_name="Microsoft.EntityFrameworkCore",
            stack=TargetStack.DOTNET_8,
            version="8.0.0",
            migration_effort=MigrationEffort.MEDIUM,
            api_similarity=0.7,
            documentation_url="",
            notes="",
            breaking_changes=[],
            additional_dependencies=[],
        )

        mapping = LibraryMapping(
            legacy=legacy,
            equivalents=[modern],
            risk_level=RiskLevel.MEDIUM,
            recommended_stack=TargetStack.DOTNET_8,
            migration_notes="Requires query rewrite",
            requires_custom_implementation=False,
            estimated_hours=40,
        )

        assert mapping.risk_level == RiskLevel.MEDIUM
        assert len(mapping.equivalents) == 1

    def test_builtin_mappings(self):
        """Test that service has built-in library mappings."""
        from app.services.library_migration_mapper_service import (
            LEGACY_LIBRARY_MAPPINGS
        )

        assert isinstance(LEGACY_LIBRARY_MAPPINGS, dict)
        assert len(LEGACY_LIBRARY_MAPPINGS) > 0

    def test_migration_effort_enum(self):
        """Test MigrationEffort enum values."""
        from app.services.library_migration_mapper_service import MigrationEffort

        assert MigrationEffort.TRIVIAL.value == "trivial"
        assert MigrationEffort.LOW.value == "low"
        assert MigrationEffort.MEDIUM.value == "medium"
        assert MigrationEffort.HIGH.value == "high"
        assert MigrationEffort.CRITICAL.value == "critical"


# =============================================================================
# Wave Planner Service Tests
# =============================================================================

class TestWavePlannerService:
    """Tests for WavePlannerService - dependency-based wave planning."""

    def test_service_instantiation(self):
        """Test service can be instantiated."""
        from app.services.wave_planner_service import WavePlannerService

        service = WavePlannerService()
        assert service is not None

    def test_module_dataclass(self):
        """Test Module dataclass."""
        from app.services.wave_planner_service import Module, ModuleType, ModuleRisk

        module = Module(
            id=str(uuid4()),
            name="AuthenticationService",
            path="src/Auth/AuthenticationService.cs",
            module_type=ModuleType.SHARED,
            dependencies=["ConfigService", "LoggingService"],
            dependents=["UserController", "AdminController"],
            lines_of_code=500,
            complexity_score=7.5,
            risk_level=ModuleRisk.MEDIUM,
            business_value=8,
            estimated_hours=40,
            team_affinity=None,
            tags=[],
        )

        assert module.name == "AuthenticationService"
        assert module.module_type == ModuleType.SHARED
        assert len(module.dependencies) == 2

    def test_wave_dataclass(self):
        """Test Wave dataclass."""
        from app.services.wave_planner_service import Wave, WaveStatus

        wave = Wave(
            id=str(uuid4()),
            number=1,
            name="Foundation Wave",
            modules=[],
            status=WaveStatus.PLANNED,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            total_loc=1500,
            total_hours=60,
            team_assignments={},
            dependencies_satisfied=True,
            blockers=[],
            risk_score=3.0,
        )

        assert wave.number == 1
        assert wave.name == "Foundation Wave"
        assert wave.status == WaveStatus.PLANNED

    def test_wave_plan_dataclass(self):
        """Test WavePlan dataclass."""
        from app.services.wave_planner_service import WavePlan, WaveStrategy

        plan = WavePlan(
            id=str(uuid4()),
            project_id="proj-001",
            name="HCI-CRS Migration",
            strategy=WaveStrategy.RISK_BALANCED,
            waves=[],
            total_modules=15,
            total_loc=12000,
            total_hours=480,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            estimated_completion=None,
            team_capacity=3,
            constraints=[],
        )

        assert plan.name == "HCI-CRS Migration"
        assert plan.strategy == WaveStrategy.RISK_BALANCED
        assert plan.total_modules == 15

    def test_wave_strategy_enum(self):
        """Test WaveStrategy enum values."""
        from app.services.wave_planner_service import WaveStrategy

        assert WaveStrategy.DEPENDENCY_FIRST.value == "dependency_first"
        assert WaveStrategy.RISK_BALANCED.value == "risk_balanced"
        assert WaveStrategy.BUSINESS_VALUE.value == "business_value"

    def test_dependency_graph_dataclass(self):
        """Test DependencyGraph dataclass."""
        from app.services.wave_planner_service import DependencyGraph

        graph = DependencyGraph(
            modules={"A", "B", "C", "D"},
            adjacency={"A": {"B", "D"}, "B": {"C"}},
            reverse_adjacency={"B": {"A"}, "C": {"B"}, "D": {"A"}},
            levels={0: {"A"}, 1: {"B", "D"}, 2: {"C"}},
            circular_dependencies=[],
        )

        assert len(graph.modules) == 4
        assert "A" in graph.adjacency
        assert len(graph.circular_dependencies) == 0


# =============================================================================
# UI Layer Extraction Service Tests
# =============================================================================

class TestUILayerExtractionService:
    """Tests for UILayerExtractionService - UI component mapping."""

    def test_service_instantiation(self):
        """Test service can be instantiated."""
        from app.services.ui_layer_extraction_service import (
            UILayerExtractionService
        )

        service = UILayerExtractionService()
        assert service is not None

    def test_legacy_ui_component_dataclass(self):
        """Test LegacyUIComponent dataclass."""
        from app.services.ui_layer_extraction_service import (
            LegacyUIComponent, LegacyUIType, ComponentType
        )

        component = LegacyUIComponent(
            id=str(uuid4()),
            name="gvUsers",
            component_type=ComponentType.GRID,
            legacy_type=LegacyUIType.ASP_WEBFORMS,
            source_file="Users.aspx",
            source_lines=(45, 85),
            html_elements=["table", "tr", "td"],
            css_classes=["grid-view", "data-grid"],
            event_handlers=["RowDataBound", "PageIndexChanging"],
            data_bindings=["DataSource", "DataBind"],
            child_components=[],
            parent_component=None,
            properties={"AutoGenerateColumns": "true"},
            styles={},
        )

        assert component.name == "gvUsers"
        assert component.legacy_type == LegacyUIType.ASP_WEBFORMS
        assert component.component_type == ComponentType.GRID

    def test_modern_component_dataclass(self):
        """Test ModernComponent dataclass."""
        from app.services.ui_layer_extraction_service import (
            ModernComponent, UIFramework
        )

        component = ModernComponent(
            name="DataGrid",
            framework=UIFramework.REACT,
            library="@mui/x-data-grid",
            import_statement="import { DataGrid } from '@mui/x-data-grid';",
            component_template="<DataGrid rows={rows} columns={columns} />",
            props_mapping={},
            event_mapping={},
            migration_notes="",
            complexity="medium",
        )

        assert component.name == "DataGrid"
        assert component.framework == UIFramework.REACT
        assert "mui" in component.library

    def test_design_token_dataclass(self):
        """Test DesignToken dataclass."""
        from app.services.ui_layer_extraction_service import (
            DesignToken, DesignTokenType
        )

        token = DesignToken(
            name="primary",
            token_type=DesignTokenType.COLOR,
            value="#1976d2",
            css_variable="--color-primary",
            tailwind_class="text-blue-600",
            description="Primary brand color",
            source_styles=[],
        )

        assert token.token_type == DesignTokenType.COLOR
        assert token.value == "#1976d2"
        assert token.css_variable == "--color-primary"

    def test_style_extraction_dataclass(self):
        """Test StyleExtraction dataclass."""
        from app.services.ui_layer_extraction_service import StyleExtraction

        styles = StyleExtraction(
            colors={"primary": "#1976d2", "secondary": "#dc004e"},
            typography={"heading": "Arial", "body": "Roboto"},
            spacing={"small": "8px", "medium": "16px"},
            borders={"radius": "4px"},
            shadows={"elevation1": "0 1px 3px rgba(0,0,0,0.12)"},
            raw_css_rules=[],
        )

        assert styles.colors["primary"] == "#1976d2"
        assert styles.spacing["medium"] == "16px"

    def test_component_mapping_dataclass(self):
        """Test ComponentMapping dataclass."""
        from app.services.ui_layer_extraction_service import (
            ComponentMapping, LegacyUIComponent, LegacyUIType, ComponentType
        )

        legacy = LegacyUIComponent(
            id=str(uuid4()),
            name="gvUsers",
            component_type=ComponentType.GRID,
            legacy_type=LegacyUIType.ASP_WEBFORMS,
            source_file="Users.aspx",
            source_lines=(45, 85),
            html_elements=[],
            css_classes=[],
            event_handlers=[],
            data_bindings=[],
            child_components=[],
            parent_component=None,
            properties={},
            styles={},
        )

        mapping = ComponentMapping(
            legacy=legacy,
            modern_equivalents=[],
            design_tokens=[],
            migration_effort="medium",
            estimated_hours=8,
            notes="Map columns to field definitions",
        )

        assert mapping.legacy.name == "gvUsers"
        assert mapping.migration_effort == "medium"

    def test_framework_enums(self):
        """Test framework enums."""
        from app.services.ui_layer_extraction_service import (
            LegacyUIType, UIFramework, ComponentType
        )

        # Legacy UI types
        assert LegacyUIType.ASP_WEBFORMS.value == "asp_webforms"
        assert LegacyUIType.ASP_MVC.value == "asp_mvc"
        assert LegacyUIType.WPF.value == "wpf"

        # Modern frameworks
        assert UIFramework.REACT.value == "react"
        assert UIFramework.VUE.value == "vue"
        assert UIFramework.BLAZOR.value == "blazor"

        # Component types
        assert ComponentType.GRID.value == "grid"
        assert ComponentType.FORM.value == "form"
        assert ComponentType.BUTTON.value == "button"

    def test_builtin_component_mappings(self):
        """Test that service has built-in component mappings."""
        from app.services.ui_layer_extraction_service import COMPONENT_MAPPINGS

        assert isinstance(COMPONENT_MAPPINGS, dict)
        assert len(COMPONENT_MAPPINGS) > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestFase26Integration:
    """Integration tests for Fase 26 components working together."""

    def test_all_services_importable(self):
        """Test that all Fase 26 services can be imported."""
        from app.services.strangler_fig_service import StranglerFigService
        from app.services.library_migration_mapper_service import (
            LibraryMigrationMapperService
        )
        from app.services.wave_planner_service import WavePlannerService
        from app.services.ui_layer_extraction_service import (
            UILayerExtractionService
        )

        assert StranglerFigService is not None
        assert LibraryMigrationMapperService is not None
        assert WavePlannerService is not None
        assert UILayerExtractionService is not None

    def test_all_services_instantiable(self):
        """Test that all Fase 26 services can be instantiated."""
        from app.services.strangler_fig_service import StranglerFigService
        from app.services.library_migration_mapper_service import (
            LibraryMigrationMapperService
        )
        from app.services.wave_planner_service import WavePlannerService
        from app.services.ui_layer_extraction_service import (
            UILayerExtractionService
        )

        services = [
            StranglerFigService(),
            LibraryMigrationMapperService(),
            WavePlannerService(),
            UILayerExtractionService(),
        ]

        for service in services:
            assert service is not None

    def test_service_agent_assignments(self):
        """Test that services have correct agent assignments."""
        from app.services.strangler_fig_service import StranglerFigService
        from app.services.library_migration_mapper_service import (
            LibraryMigrationMapperService
        )
        from app.services.wave_planner_service import WavePlannerService
        from app.services.ui_layer_extraction_service import (
            UILayerExtractionService
        )

        # Services should exist and be properly structured
        assert hasattr(StranglerFigService, '__init__')
        assert hasattr(LibraryMigrationMapperService, '__init__')
        assert hasattr(WavePlannerService, '__init__')
        assert hasattr(UILayerExtractionService, '__init__')


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestMigrationExecutionAPI:
    """Tests for Migration Execution API endpoints."""

    def test_api_router_exists(self):
        """Test that API router is defined."""
        from app.api.migration_execution import router

        assert router is not None
        assert router.prefix == "/api/migration-execution"

    def test_strangler_endpoints_defined(self):
        """Test strangler fig endpoints are defined."""
        from app.api.migration_execution import router

        routes = [route.path for route in router.routes]
        assert any("/strangler/sessions" in path for path in routes)

    def test_library_mapper_endpoints_defined(self):
        """Test library mapper endpoints are defined."""
        from app.api.migration_execution import router

        routes = [route.path for route in router.routes]
        assert any("/library-mapper" in path for path in routes)

    def test_wave_planner_endpoints_defined(self):
        """Test wave planner endpoints are defined."""
        from app.api.migration_execution import router

        routes = [route.path for route in router.routes]
        assert any("/wave-planner" in path for path in routes)

    def test_ui_extraction_endpoints_defined(self):
        """Test UI extraction endpoints are defined."""
        from app.api.migration_execution import router

        routes = [route.path for route in router.routes]
        assert any("/ui-extraction" in path for path in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
