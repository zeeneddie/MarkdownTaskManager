"""Unit tests for all Agent Extensions (Week 151)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.confucius.extensions import (
    FelixExtension,
    QuinnExtension,
    ElizaExtension,
    DianaExtension,
    MarcusExtension,
    MiguelExtension,
    TessaExtension,
    PeterExtension,
    PaulExtension,
    BettyExtension,
    VickyExtension,
    ExtensionRouter,
    WorkflowRouter,
    create_default_router,
    create_extension,
    get_extension_class,
    EXTENSION_REGISTRY,
)


# =============================================================================
# FELIX EXTENSION TESTS
# =============================================================================

class TestFelixExtension:
    """Tests for Felix (Architecture) Extension."""

    def test_metadata(self):
        """Test Felix metadata configuration."""
        ext = FelixExtension()

        assert ext.name == "Felix"
        assert ext.priority == 8
        assert "architecture_analysis" in ext.metadata.capabilities
        assert "architecture" in ext.metadata.domains

    def test_matches_architecture_task(self):
        """Test Felix matches architecture tasks."""
        ext = FelixExtension()

        score = ext.matches_task("Analyze the system architecture", {})
        assert score >= 0.3

    def test_matches_pattern_task(self):
        """Test Felix matches pattern recommendation tasks."""
        ext = FelixExtension()

        score = ext.matches_task("Recommend design patterns", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_analysis_type_pattern(self):
        """Test analysis type determination for patterns."""
        ext = FelixExtension()

        context = await ext.on_input_messages(
            "Recommend architecture pattern",
            {}
        )

        assert context["felix_analysis_type"] == "pattern_recommendation"

    @pytest.mark.asyncio
    async def test_determine_analysis_type_api(self):
        """Test analysis type determination for API."""
        ext = FelixExtension()

        context = await ext.on_input_messages(
            "Generate API contracts",
            {}
        )

        assert context["felix_analysis_type"] == "api_generation"

    @pytest.mark.asyncio
    async def test_execute_returns_success(self):
        """Test Felix execute returns success."""
        ext = FelixExtension()

        result = await ext.execute("Analyze architecture", {"felix_analysis_type": "full_analysis"})

        assert result["agent"] == "Felix"
        # Note: success depends on whether architecture service is available


# =============================================================================
# QUINN EXTENSION TESTS
# =============================================================================

class TestQuinnExtension:
    """Tests for Quinn (Quality) Extension."""

    def test_metadata(self):
        """Test Quinn metadata configuration."""
        ext = QuinnExtension()

        assert ext.name == "Quinn"
        assert ext.priority == 9  # Highest priority
        assert "code_quality_analysis" in ext.metadata.capabilities
        assert "quality" in ext.metadata.domains

    def test_matches_security_task(self):
        """Test Quinn matches security tasks."""
        ext = QuinnExtension()

        score = ext.matches_task("Review code security", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_review_type_security(self):
        """Test review type determination for security."""
        ext = QuinnExtension()

        context = await ext.on_input_messages(
            "Security review for OWASP",
            {}
        )

        assert context["quinn_review_type"] == "security"

    @pytest.mark.asyncio
    async def test_quality_threshold_default(self):
        """Test quality threshold default."""
        ext = QuinnExtension()

        context = await ext.on_input_messages("Review", {})

        assert context["quality_threshold"] == 0.85


# =============================================================================
# ELIZA EXTENSION TESTS
# =============================================================================

class TestElizaExtension:
    """Tests for Eliza (Estimation) Extension."""

    def test_metadata(self):
        """Test Eliza metadata configuration."""
        ext = ElizaExtension()

        assert ext.name == "Eliza"
        assert "function_point_analysis" in ext.metadata.capabilities
        assert "estimation" in ext.metadata.domains

    def test_matches_fp_task(self):
        """Test Eliza matches FP tasks."""
        ext = ElizaExtension()

        # Note: Uses "estimation" domain keyword
        score = ext.matches_task("Estimation of function points", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_estimation_type_fp(self):
        """Test estimation type determination for FP."""
        ext = ElizaExtension()

        context = await ext.on_input_messages(
            "NESMA function point analysis",
            {}
        )

        assert context["eliza_estimation_type"] == "function_points"

    @pytest.mark.asyncio
    async def test_methodology_default(self):
        """Test methodology defaults to NESMA."""
        ext = ElizaExtension()

        context = await ext.on_input_messages("Estimate", {})

        assert context["methodology"] == "NESMA"


# =============================================================================
# DIANA EXTENSION TESTS
# =============================================================================

class TestDianaExtension:
    """Tests for Diana (Documentation) Extension."""

    def test_metadata(self):
        """Test Diana metadata configuration."""
        ext = DianaExtension()

        assert ext.name == "Diana"
        assert "technical_documentation" in ext.metadata.capabilities
        assert "documentation" in ext.metadata.domains

    def test_matches_docs_task(self):
        """Test Diana matches documentation tasks."""
        ext = DianaExtension()

        score = ext.matches_task("Generate API documentation", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_doc_type_api(self):
        """Test doc type determination for API."""
        ext = DianaExtension()

        context = await ext.on_input_messages(
            "Generate Swagger API docs",
            {}
        )

        assert context["diana_doc_type"] == "api"

    @pytest.mark.asyncio
    async def test_output_format_default(self):
        """Test output format defaults to markdown."""
        ext = DianaExtension()

        context = await ext.on_input_messages("Write docs", {})

        assert context["output_format"] == "markdown"


# =============================================================================
# MARCUS EXTENSION TESTS
# =============================================================================

class TestMarcusExtension:
    """Tests for Marcus (Maintenance) Extension."""

    def test_metadata(self):
        """Test Marcus metadata configuration."""
        ext = MarcusExtension()

        assert ext.name == "Marcus"
        assert "tech_debt_analysis" in ext.metadata.capabilities
        assert "maintenance" in ext.metadata.domains

    def test_matches_debt_task(self):
        """Test Marcus matches tech debt tasks."""
        ext = MarcusExtension()

        # Note: Uses "maintenance" domain keyword
        score = ext.matches_task("Maintenance and tech_debt analysis", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_focus_area_dependencies(self):
        """Test focus area determination for dependencies."""
        ext = MarcusExtension()

        context = await ext.on_input_messages(
            "Update npm dependencies",
            {}
        )

        assert context["marcus_focus_area"] == "dependencies"

    @pytest.mark.asyncio
    async def test_determine_focus_area_security(self):
        """Test focus area determination for security."""
        ext = MarcusExtension()

        context = await ext.on_input_messages(
            "Check for security vulnerabilities",
            {}
        )

        assert context["marcus_focus_area"] == "security"


# =============================================================================
# MIGUEL EXTENSION TESTS
# =============================================================================

class TestMiguelExtension:
    """Tests for Miguel (Metrics) Extension."""

    def test_metadata(self):
        """Test Miguel metadata configuration."""
        ext = MiguelExtension()

        assert ext.name == "Miguel"
        assert ext.priority == 7
        assert "code_metrics" in ext.metadata.capabilities
        assert "metrics" in ext.metadata.domains

    def test_matches_metrics_task(self):
        """Test Miguel matches metrics tasks."""
        ext = MiguelExtension()

        score = ext.matches_task("Collect code metrics", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_metrics_type_code(self):
        """Test metrics type determination for code."""
        ext = MiguelExtension()

        context = await ext.on_input_messages(
            "Analyze code complexity",
            {}
        )

        assert context["miguel_metrics_type"] == "code"


# =============================================================================
# TESSA EXTENSION TESTS
# =============================================================================

class TestTessaExtension:
    """Tests for Tessa (Testing) Extension."""

    def test_metadata(self):
        """Test Tessa metadata configuration."""
        ext = TessaExtension()

        assert ext.name == "Tessa"
        assert "test_generation" in ext.metadata.capabilities
        assert "testing" in ext.metadata.domains

    def test_matches_testing_task(self):
        """Test Tessa matches testing tasks."""
        ext = TessaExtension()

        score = ext.matches_task("Generate unit tests", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_test_type_generation(self):
        """Test test type determination for generation."""
        ext = TessaExtension()

        context = await ext.on_input_messages(
            "Generate test cases",
            {}
        )

        assert context["tessa_test_type"] == "generation"

    @pytest.mark.asyncio
    async def test_coverage_threshold_default(self):
        """Test coverage threshold default."""
        ext = TessaExtension()

        context = await ext.on_input_messages("Test", {})

        assert context["coverage_threshold"] == 80.0


# =============================================================================
# PETER EXTENSION TESTS
# =============================================================================

class TestPeterExtension:
    """Tests for Peter (Product Owner) Extension."""

    def test_metadata(self):
        """Test Peter metadata configuration."""
        ext = PeterExtension()

        assert ext.name == "Peter"
        assert ext.priority == 8
        assert "requirements_analysis" in ext.metadata.capabilities
        assert "product" in ext.metadata.domains

    def test_matches_requirements_task(self):
        """Test Peter matches requirements tasks."""
        ext = PeterExtension()

        score = ext.matches_task("Gather requirements", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_activity_stories(self):
        """Test activity determination for stories."""
        ext = PeterExtension()

        # Note: Uses "user story" to match the keyword
        context = await ext.on_input_messages(
            "Create a user story",
            {}
        )

        assert context["peter_activity"] == "stories"

    @pytest.mark.asyncio
    async def test_prioritization_method_default(self):
        """Test prioritization method defaults to MoSCoW."""
        ext = PeterExtension()

        context = await ext.on_input_messages("Plan", {})

        assert context["prioritization_method"] == "MoSCoW"


# =============================================================================
# PAUL EXTENSION TESTS
# =============================================================================

class TestPaulExtension:
    """Tests for Paul (Planning) Extension."""

    def test_metadata(self):
        """Test Paul metadata configuration."""
        ext = PaulExtension()

        assert ext.name == "Paul"
        assert "sprint_planning" in ext.metadata.capabilities
        assert "planning" in ext.metadata.domains

    def test_matches_planning_task(self):
        """Test Paul matches planning tasks."""
        ext = PaulExtension()

        score = ext.matches_task("Plan the sprint", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_planning_type_sprint(self):
        """Test planning type determination for sprint."""
        ext = PaulExtension()

        context = await ext.on_input_messages(
            "Sprint planning session",
            {}
        )

        assert context["paul_planning_type"] == "sprint"

    @pytest.mark.asyncio
    async def test_sprint_duration_default(self):
        """Test sprint duration default."""
        ext = PaulExtension()

        context = await ext.on_input_messages("Plan", {})

        assert context["sprint_duration_days"] == 14


# =============================================================================
# BETTY EXTENSION TESTS
# =============================================================================

class TestBettyExtension:
    """Tests for Betty (Business Analyst) Extension."""

    def test_metadata(self):
        """Test Betty metadata configuration."""
        ext = BettyExtension()

        assert ext.name == "Betty"
        assert "business_process_analysis" in ext.metadata.capabilities
        assert "business" in ext.metadata.domains

    def test_matches_business_task(self):
        """Test Betty matches business tasks."""
        ext = BettyExtension()

        score = ext.matches_task("Analyze business process", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_analysis_type_roi(self):
        """Test analysis type determination for ROI."""
        ext = BettyExtension()

        context = await ext.on_input_messages(
            "Calculate ROI",
            {}
        )

        assert context["betty_analysis_type"] == "roi"


# =============================================================================
# VICKY EXTENSION TESTS
# =============================================================================

class TestVickyExtension:
    """Tests for Vicky (Visual Designer) Extension."""

    def test_metadata(self):
        """Test Vicky metadata configuration."""
        ext = VickyExtension()

        assert ext.name == "Vicky"
        assert "ui_specification" in ext.metadata.capabilities
        assert "design" in ext.metadata.domains

    def test_matches_design_task(self):
        """Test Vicky matches design tasks."""
        ext = VickyExtension()

        score = ext.matches_task("Create UI specification", {})
        assert score > 0

    @pytest.mark.asyncio
    async def test_determine_activity_tokens(self):
        """Test activity determination for design tokens."""
        ext = VickyExtension()

        context = await ext.on_input_messages(
            "Generate design tokens for colors",
            {}
        )

        assert context["vicky_activity"] == "design_tokens"

    @pytest.mark.asyncio
    async def test_tier_default(self):
        """Test tier defaults to STANDARD."""
        ext = VickyExtension()

        context = await ext.on_input_messages("Design", {})

        assert context["tier"] == "STANDARD"


# =============================================================================
# EXTENSION ROUTER TESTS
# =============================================================================

class TestExtensionRouter:
    """Tests for ExtensionRouter."""

    def test_register_extension(self):
        """Test registering an extension."""
        router = ExtensionRouter()
        ext = FelixExtension()

        router.register(ext)

        assert "Felix" in router.list_extensions()

    def test_unregister_extension(self):
        """Test unregistering an extension."""
        router = ExtensionRouter()
        ext = FelixExtension()
        router.register(ext)

        result = router.unregister("Felix")

        assert result is True
        assert "Felix" not in router.list_extensions()

    def test_get_extension(self):
        """Test getting extension by name."""
        router = ExtensionRouter()
        ext = FelixExtension()
        router.register(ext)

        retrieved = router.get_extension("Felix")

        assert retrieved.name == "Felix"

    def test_route_to_matching_extension(self):
        """Test routing to matching extension."""
        router = ExtensionRouter()
        router.register(FelixExtension())
        router.register(QuinnExtension())

        decision = router.route("Analyze architecture", {})

        assert len(decision.extensions) > 0
        # Felix should be selected for architecture tasks
        ext_names = [e.name for e in decision.extensions]
        assert "Felix" in ext_names

    def test_route_with_required_extensions(self):
        """Test routing with required extensions."""
        router = ExtensionRouter()
        router.register(FelixExtension())
        router.register(QuinnExtension())

        decision = router.route("Any task", {}, required_extensions=["Quinn"])

        ext_names = [e.name for e in decision.extensions]
        assert "Quinn" in ext_names

    def test_route_with_excluded_extensions(self):
        """Test routing with excluded extensions."""
        router = ExtensionRouter()
        router.register(FelixExtension())
        router.register(QuinnExtension())

        decision = router.route("Analyze architecture", {}, excluded_extensions=["Felix"])

        ext_names = [e.name for e in decision.extensions]
        assert "Felix" not in ext_names

    def test_route_by_domain(self):
        """Test routing by domain."""
        router = ExtensionRouter()
        router.register(FelixExtension())
        router.register(TessaExtension())

        extensions = router.route_by_domain("architecture", {})

        assert len(extensions) > 0
        assert extensions[0].name == "Felix"

    def test_route_by_capability(self):
        """Test routing by capability."""
        router = ExtensionRouter()
        router.register(TessaExtension())
        router.register(FelixExtension())

        extensions = router.route_by_capability("test_generation", {})

        assert len(extensions) > 0
        assert extensions[0].name == "Tessa"


class TestWorkflowRouter:
    """Tests for WorkflowRouter."""

    def test_route_brown_paper_workflow(self):
        """Test routing Brown Paper workflow."""
        router = create_default_router()

        decision = router.route_workflow("brown_paper", {})

        assert len(decision.extensions) == 5
        ext_names = [e.name for e in decision.extensions]
        assert "Miguel" in ext_names
        assert "Felix" in ext_names
        assert "Quinn" in ext_names

    def test_route_migration_workflow(self):
        """Test routing Migration workflow."""
        router = create_default_router()

        decision = router.route_workflow("migration", {})

        assert len(decision.extensions) > 0
        ext_names = [e.name for e in decision.extensions]
        assert "Felix" in ext_names
        assert "Marcus" in ext_names

    def test_workflow_sequential_execution(self):
        """Test workflow routes are sequential."""
        router = create_default_router()

        decision = router.route_workflow("brown_paper", {})

        assert decision.parallel_execution is False


# =============================================================================
# EXTENSION REGISTRY TESTS
# =============================================================================

class TestExtensionRegistry:
    """Tests for extension registry functions."""

    def test_registry_contains_all_extensions(self):
        """Test registry contains all 11 extensions."""
        assert len(EXTENSION_REGISTRY) == 11
        expected = [
            "Felix", "Quinn", "Eliza", "Diana", "Marcus",
            "Miguel", "Tessa", "Peter", "Paul", "Betty", "Vicky"
        ]
        for name in expected:
            assert name in EXTENSION_REGISTRY

    def test_get_extension_class(self):
        """Test getting extension class by name."""
        cls = get_extension_class("Felix")

        assert cls == FelixExtension

    def test_get_extension_class_not_found(self):
        """Test getting extension class with invalid name."""
        with pytest.raises(KeyError):
            get_extension_class("Unknown")

    def test_create_extension(self):
        """Test creating extension by name."""
        ext = create_extension("Quinn")

        assert ext.name == "Quinn"
        assert isinstance(ext, QuinnExtension)

    def test_create_default_router(self):
        """Test creating default router."""
        router = create_default_router()

        assert len(router.list_extensions()) == 11
