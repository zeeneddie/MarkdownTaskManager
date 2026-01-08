# backend/tests/services/week116/test_business_rule_workflow_integration.py
"""
Tests for Week 116 Phase 5: Business Rule Workflow Integration

Tests the integration between:
- TierOrchestrator (hybrid extraction)
- RuleCorrelationService (entity/workflow detection)
- BusinessRuleWorkflowIntegration (agent context preparation)
- AgentService (workflow execution with rule context)
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Import the services being tested
from app.services.orchestration.business_rule_workflow_integration import (
    BusinessRuleWorkflowIntegration,
    RuleExtractionContext,
    WorkflowIntegrationResult,
    get_rule_context_for_agent,
    is_rule_integrated_workflow,
    RULE_INTEGRATED_WORKFLOWS,
)


class TestRuleExtractionContext:
    """Tests for RuleExtractionContext dataclass."""

    def test_basic_context_creation(self):
        """Test creating a basic extraction context."""
        context = RuleExtractionContext(
            total_rules=50,
            high_confidence_rules=35,
            average_confidence=0.78,
            detected_languages=["VB.NET", "T-SQL"],
            database_patterns=["Microsoft SQL Server"],
        )

        assert context.total_rules == 50
        assert context.high_confidence_rules == 35
        assert context.average_confidence == 0.78
        assert "VB.NET" in context.detected_languages
        assert "Microsoft SQL Server" in context.database_patterns

    def test_miguel_agent_context(self):
        """Test generating Miguel-specific context for migration work."""
        context = RuleExtractionContext(
            total_rules=100,
            high_confidence_rules=75,
            average_confidence=0.82,
            entities=[
                {"name": "Customer", "rule_count": 15, "crud_coverage": "CRUD"},
                {"name": "Order", "rule_count": 12, "crud_coverage": "CRU"},
            ],
            workflows=[
                {"name": "Customer Management", "total_rules": 10},
            ],
            detected_languages=["VB.NET", "Classic ASP"],
            detected_frameworks=[],
            database_patterns=["Microsoft SQL Server"],
            validation_rules=[{"description": "Customer must have email"}],
            authorization_rules=[{"description": "intCanEdit check"}],
            data_access_rules=[{"condition": "SELECT FROM taCustomer"}],
        )

        miguel_context = context.to_agent_context("miguel")

        # Check summary is present
        assert "rule_extraction" in miguel_context
        assert miguel_context["rule_extraction"]["summary"]["total_rules"] == 100

        # Check migration-specific context
        assert "migration_context" in miguel_context
        assert "VB.NET" in miguel_context["migration_context"]["detected_languages"]
        assert "Microsoft SQL Server" in miguel_context["migration_context"]["database_patterns"]

        # Check legacy analysis
        assert "legacy_analysis" in miguel_context
        assert len(miguel_context["legacy_analysis"]["authorization_patterns"]) > 0

    def test_peter_agent_context(self):
        """Test generating Peter-specific context for backlog generation."""
        context = RuleExtractionContext(
            total_rules=80,
            high_confidence_rules=60,
            average_confidence=0.80,
            entities=[
                {"name": "Product", "rule_count": 20, "crud_coverage": "CRUD"},
                {"name": "Cart", "rule_count": 8, "crud_coverage": "CRU"},
            ],
            workflows=[
                {
                    "name": "Product Catalog Management",
                    "workflow_type": "CRUD",
                    "operations": ["CREATE", "READ", "UPDATE", "DELETE"],
                    "total_rules": 15,
                },
            ],
            validation_rules=[
                {"description": "Product price must be positive", "source_file": "Product.vb"},
            ],
            authorization_rules=[
                {"description": "Admin can edit products", "pattern": "intCanEdit"},
            ],
        )

        peter_context = context.to_agent_context("peter")

        # Check summary is present
        assert "rule_extraction" in peter_context
        assert peter_context["rule_extraction"]["summary"]["total_rules"] == 80

        # Check story generation context
        assert "story_generation" in peter_context
        assert len(peter_context["story_generation"]["entities_for_epics"]) > 0
        assert peter_context["story_generation"]["entities_for_epics"][0]["name"] == "Product"
        assert "Manage Product" in peter_context["story_generation"]["entities_for_epics"][0]["suggested_epic"]

        # Check workflows for features
        assert len(peter_context["story_generation"]["workflows_for_features"]) > 0

        # Check priority indicators
        assert "priority_indicators" in peter_context

    def test_felix_agent_context(self):
        """Test generating Felix-specific context for architecture."""
        context = RuleExtractionContext(
            total_rules=60,
            high_confidence_rules=45,
            average_confidence=0.75,
            entities=[
                {"name": "User", "files_referenced": ["User.vb", "UserRepository.vb"], "rule_count": 10},
            ],
            workflows=[
                {"name": "User Management", "source_files": ["UserController.vb"], "auth_pattern": "intCanEdit"},
            ],
            detected_languages=["VB.NET"],
            detected_frameworks=["ASP.NET"],
            database_patterns=["Microsoft SQL Server"],
        )

        felix_context = context.to_agent_context("felix")

        # Check architecture context
        assert "architecture_context" in felix_context
        assert "VB.NET" in felix_context["architecture_context"]["detected_patterns"]["languages"]

        # Check module boundaries
        assert len(felix_context["architecture_context"]["module_boundaries"]) > 0

        # Check technical debt indicators
        assert "technical_debt_indicators" in felix_context

    def test_quinn_agent_context(self):
        """Test generating Quinn-specific context for quality audit."""
        context = RuleExtractionContext(
            total_rules=40,
            high_confidence_rules=30,
            average_confidence=0.85,
            validation_rules=[{"description": "Validate email format"}] * 10,
            authorization_rules=[{"description": "Check user permission"}] * 5,
            entities=[{"name": "Order"}],
            workflows=[{"name": "Order Processing", "auth_rules": ["rule1"]}],
        )

        quinn_context = context.to_agent_context("quinn")

        # Check quality context
        assert "quality_context" in quinn_context
        assert quinn_context["quality_context"]["validation_coverage"]["total_validation_rules"] == 10
        assert quinn_context["quality_context"]["authorization_coverage"]["total_auth_rules"] == 5

        # Check rule quality metrics
        assert quinn_context["quality_context"]["rule_quality"]["average_confidence"] == 0.85


class TestBusinessRuleWorkflowIntegration:
    """Tests for BusinessRuleWorkflowIntegration service."""

    def test_supports_workflow(self):
        """Test workflow support detection."""
        service = BusinessRuleWorkflowIntegration()

        # Should support rule-integrated workflows
        assert service.supports_workflow("BROWN_PAPER") is True
        assert service.supports_workflow("MIGRATION") is True
        assert service.supports_workflow("BACKLOG_GENERATION") is True
        assert service.supports_workflow("QUALITY_AUDIT") is True

        # Should not support other workflows
        assert service.supports_workflow("NEW_FEATURE") is False
        assert service.supports_workflow("BUG") is False
        assert service.supports_workflow("MAINTENANCE") is False

    def test_is_rule_integrated_workflow_helper(self):
        """Test the helper function for checking workflow support."""
        assert is_rule_integrated_workflow("BROWN_PAPER") is True
        assert is_rule_integrated_workflow("brown_paper") is True  # Case insensitive
        assert is_rule_integrated_workflow("NEW_FEATURE") is False

    def test_rule_integrated_workflows_constant(self):
        """Test the RULE_INTEGRATED_WORKFLOWS constant."""
        assert "BROWN_PAPER" in RULE_INTEGRATED_WORKFLOWS
        assert "MIGRATION" in RULE_INTEGRATED_WORKFLOWS
        assert "BACKLOG_GENERATION" in RULE_INTEGRATED_WORKFLOWS
        assert "QUALITY_AUDIT" in RULE_INTEGRATED_WORKFLOWS

    @pytest.mark.asyncio
    async def test_extract_for_unsupported_workflow(self):
        """Test extraction for unsupported workflow returns error."""
        service = BusinessRuleWorkflowIntegration()

        result = await service.extract_for_workflow(
            workflow_type="NEW_FEATURE",
            source_path="/tmp/test",
        )

        assert result.success is False
        assert len(result.errors) > 0
        assert "does not support rule integration" in result.errors[0]

    @pytest.mark.asyncio
    async def test_extract_for_workflow_caching(self):
        """Test that extraction results are cached."""
        service = BusinessRuleWorkflowIntegration()

        # Mock the extraction context
        mock_context = RuleExtractionContext(
            total_rules=10,
            entities=[{"name": "Test"}],
        )

        # Manually set cache
        cache_key = "BROWN_PAPER:/tmp/test:None:STANDARD"
        service._extraction_cache[cache_key] = mock_context

        # Should return cached result
        result = await service.extract_for_workflow(
            workflow_type="BROWN_PAPER",
            source_path="/tmp/test",
            tier="STANDARD",
        )

        assert result.success is True
        assert result.extraction_context is mock_context

    def test_clear_cache(self):
        """Test cache clearing."""
        service = BusinessRuleWorkflowIntegration()

        # Add some cached items
        service._extraction_cache["key1:project:1:STANDARD"] = RuleExtractionContext()
        service._extraction_cache["key2:project:2:STANDARD"] = RuleExtractionContext()
        service._extraction_cache["key3:project:1:BASIC"] = RuleExtractionContext()

        # Clear all
        service.clear_cache()
        assert len(service._extraction_cache) == 0

        # Add again and clear by project
        service._extraction_cache["key1:project:1:STANDARD"] = RuleExtractionContext()
        service._extraction_cache["key2:project:2:STANDARD"] = RuleExtractionContext()

        service.clear_cache(project_id=1)
        assert len(service._extraction_cache) == 1
        assert "key2:project:2:STANDARD" in service._extraction_cache

    def test_get_agent_context_from_cache(self):
        """Test getting agent context from cache."""
        service = BusinessRuleWorkflowIntegration()

        # Set up cache with a context
        mock_context = RuleExtractionContext(
            total_rules=50,
            entities=[{"name": "Customer", "rule_count": 10}],
            detected_languages=["VB.NET"],
        )
        service._extraction_cache["BROWN_PAPER:/opt/project:123:STANDARD"] = mock_context

        # Get agent context
        miguel_context = service.get_agent_context(
            agent_name="miguel",
            workflow_type="BROWN_PAPER",
            source_path="/opt/project",
            project_id=123,
        )

        assert miguel_context is not None
        assert "rule_extraction" in miguel_context
        assert "migration_context" in miguel_context


class TestAgentContextPreparation:
    """Tests for agent context preparation for different workflows."""

    @pytest.fixture
    def sample_context(self):
        """Create a sample extraction context for testing."""
        return RuleExtractionContext(
            total_rules=100,
            high_confidence_rules=75,
            average_confidence=0.82,
            entities=[
                {"name": "Customer", "rule_count": 20, "crud_coverage": "CRUD", "files_referenced": ["Customer.vb"]},
                {"name": "Order", "rule_count": 15, "crud_coverage": "CRU", "files_referenced": ["Order.vb"]},
                {"name": "Product", "rule_count": 12, "crud_coverage": "CR", "files_referenced": ["Product.vb"]},
            ],
            workflows=[
                {
                    "name": "Customer Management",
                    "workflow_type": "CRUD",
                    "operations": ["CREATE", "READ", "UPDATE", "DELETE"],
                    "total_rules": 15,
                    "source_files": ["CustomerController.vb"],
                    "auth_pattern": "intCanEdit",
                },
                {
                    "name": "Order Processing",
                    "workflow_type": "CRUD",
                    "operations": ["CREATE", "READ"],
                    "total_rules": 10,
                    "source_files": ["OrderController.vb"],
                    "auth_pattern": None,
                },
            ],
            validation_rules=[
                {"description": "Customer email is required", "source_file": "Customer.vb"},
                {"description": "Order total must be positive", "source_file": "Order.vb"},
            ],
            authorization_rules=[
                {"description": "Admin can edit customers", "pattern": "intCanEdit"},
            ],
            business_logic_rules=[
                {"condition": "Order.Total > 1000", "action": "Apply discount"},
            ],
            data_access_rules=[
                {"condition": "SELECT FROM taCustomer"},
            ],
            detected_languages=["VB.NET", "T-SQL"],
            detected_frameworks=["ASP.NET WebForms"],
            database_patterns=["Microsoft SQL Server"],
            rule_relationships=[
                {"source": "BR-001", "target": "BR-002", "type": "guards"},
            ],
            extraction_tier="STANDARD",
            extraction_time_ms=1500,
            extraction_cost_cents=0.05,
        )

    def test_brown_paper_agents(self, sample_context):
        """Test context preparation for BROWN_PAPER workflow agents."""
        service = BusinessRuleWorkflowIntegration()

        agent_contexts = service._prepare_all_agent_contexts(sample_context, "BROWN_PAPER")

        # BROWN_PAPER uses miguel, peter, felix
        assert "miguel" in agent_contexts
        assert "peter" in agent_contexts
        assert "felix" in agent_contexts

        # Verify Miguel gets migration context
        assert "migration_context" in agent_contexts["miguel"]

        # Verify Peter gets story generation context
        assert "story_generation" in agent_contexts["peter"]

        # Verify Felix gets architecture context
        assert "architecture_context" in agent_contexts["felix"]

    def test_migration_agents(self, sample_context):
        """Test context preparation for MIGRATION workflow agents."""
        service = BusinessRuleWorkflowIntegration()

        agent_contexts = service._prepare_all_agent_contexts(sample_context, "MIGRATION")

        # MIGRATION uses miguel, felix, marcus
        assert "miguel" in agent_contexts
        assert "felix" in agent_contexts
        assert "marcus" in agent_contexts

    def test_backlog_generation_agents(self, sample_context):
        """Test context preparation for BACKLOG_GENERATION workflow agents."""
        service = BusinessRuleWorkflowIntegration()

        agent_contexts = service._prepare_all_agent_contexts(sample_context, "BACKLOG_GENERATION")

        # BACKLOG_GENERATION uses peter, felix, paul
        assert "peter" in agent_contexts
        assert "felix" in agent_contexts
        assert "paul" in agent_contexts

        # Peter should have story generation context
        peter_ctx = agent_contexts["peter"]
        assert "story_generation" in peter_ctx
        assert len(peter_ctx["story_generation"]["entities_for_epics"]) > 0

    def test_quality_audit_agents(self, sample_context):
        """Test context preparation for QUALITY_AUDIT workflow agents."""
        service = BusinessRuleWorkflowIntegration()

        agent_contexts = service._prepare_all_agent_contexts(sample_context, "QUALITY_AUDIT")

        # QUALITY_AUDIT uses quinn, betty, marcus
        assert "quinn" in agent_contexts
        assert "betty" in agent_contexts
        assert "marcus" in agent_contexts

        # Quinn should have quality context
        assert "quality_context" in agent_contexts["quinn"]


class TestWorkflowIntegrationResult:
    """Tests for WorkflowIntegrationResult dataclass."""

    def test_success_result(self):
        """Test successful workflow integration result."""
        context = RuleExtractionContext(total_rules=50)

        result = WorkflowIntegrationResult(
            success=True,
            workflow_type="BROWN_PAPER",
            extraction_context=context,
            agent_contexts={"miguel": {"test": "data"}},
            processing_time_ms=1200,
        )

        assert result.success is True
        assert result.workflow_type == "BROWN_PAPER"
        assert result.extraction_context.total_rules == 50
        assert "miguel" in result.agent_contexts
        assert result.processing_time_ms == 1200
        assert len(result.errors) == 0

    def test_failure_result(self):
        """Test failed workflow integration result."""
        result = WorkflowIntegrationResult(
            success=False,
            workflow_type="UNKNOWN",
            errors=["Unsupported workflow type"],
        )

        assert result.success is False
        assert result.extraction_context is None
        assert len(result.errors) == 1


# Integration test with mocked extraction services
class TestEndToEndIntegration:
    """End-to-end integration tests with mocked extraction services."""

    @pytest.mark.asyncio
    async def test_full_extraction_flow(self):
        """Test full extraction flow with mocked services."""
        from unittest.mock import patch

        # Mock the TierOrchestrator
        mock_extraction_result = MagicMock()
        mock_extraction_result.rules = []
        mock_extraction_result.metrics = MagicMock()
        mock_extraction_result.metrics.total_rules = 25
        mock_extraction_result.metrics.high_confidence_rules = 20
        mock_extraction_result.metrics.average_confidence = 0.85
        mock_extraction_result.metrics.total_ms = 500
        mock_extraction_result.metrics.total_cost_cents = 0.02
        mock_extraction_result.synthesis_result = None
        mock_extraction_result.errors = []
        mock_extraction_result.warnings = []

        # Mock the CorrelationResult
        mock_correlation_result = MagicMock()
        mock_correlation_result.entities = []
        mock_correlation_result.workflows = []
        mock_correlation_result.relationships = []

        with patch("app.services.orchestration.business_rule_workflow_integration.TierOrchestrator") as MockOrch, \
             patch("app.services.orchestration.business_rule_workflow_integration.RuleCorrelationService") as MockCorr:

            # Configure mocks
            mock_orch_instance = AsyncMock()
            mock_orch_instance.extract_from_directory = AsyncMock(return_value=mock_extraction_result)
            MockOrch.return_value = mock_orch_instance

            mock_corr_instance = MagicMock()
            mock_corr_instance.correlate = MagicMock(return_value=mock_correlation_result)
            MockCorr.return_value = mock_corr_instance

            # Run the integration
            service = BusinessRuleWorkflowIntegration()
            result = await service.extract_for_workflow(
                workflow_type="BROWN_PAPER",
                source_path="/tmp/test_project",
                project_id=123,
                tier="STANDARD",
            )

            assert result.success is True
            assert result.extraction_context is not None
            assert "miguel" in result.agent_contexts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
