"""
Week 90 Tests - GhostCrew & BigAGI Workflow Integration Extensions

Tests for:
- GhostCrew: GREEN_PAPER, TESTING, ENHANCEMENT, QUALITY_IMPROVEMENT
- BigAGI: GREEN_PAPER, BROWN_PAPER, NEW_FEATURE validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.services.workflow_tool_integration_service import (
    WorkflowToolIntegrationService,
    WorkflowGhostCrewIntegration,
    WorkflowBigAGIIntegration,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_ghostcrew_service():
    """Create mock GhostCrew service."""
    service = AsyncMock()
    service.assist = AsyncMock(return_value={
        "recommendations": ["Use parameterized queries", "Enable HTTPS"],
        "immediate_actions": ["Review authentication"],
        "severity_assessment": "medium",
        "knowledge_references": [{"type": "OWASP", "id": "A01:2021"}]
    })
    service.scan_autonomous = AsyncMock(return_value={
        "scan_id": str(uuid4()),
        "status": "completed",
        "total_findings": 3,
        "security_score": 85,
        "findings": [
            {"finding_type": "xss", "severity": "high", "file_path": "test.js"},
            {"finding_type": "sql_injection", "severity": "critical", "file_path": "db.py"},
            {"finding_type": "hardcoded_secret", "severity": "medium", "file_path": "config.py"},
        ],
        "recommendations": ["Fix XSS", "Parameterize queries"]
    })
    service.run_crew = AsyncMock(return_value={
        "scan_id": str(uuid4()),
        "status": "completed",
        "security_score": 80,
        "findings": [
            {"finding_type": "sensitive_file", "severity": "high", "file_path": ".env"}
        ],
        "recommendations": ["Remove .env from git"]
    })
    service._scan_code_snippet = AsyncMock(return_value=[
        {"finding_type": "xss", "severity": "high", "category": "injection"}
    ])
    return service


@pytest.fixture
def mock_bigagi_service():
    """Create mock BigAGI Beam service."""
    service = AsyncMock()

    # Mock validation object
    mock_validation = MagicMock()
    mock_validation.id = uuid4()
    service.create_validation = AsyncMock(return_value=mock_validation)

    # Mock validation result
    mock_result = MagicMock()
    mock_result.validation_id = uuid4()
    mock_result.consensus_reached = True
    mock_result.consensus_score = 0.85
    mock_result.recommendation = "accept"
    mock_result.final_answer = "Architecture validated successfully"
    mock_result.key_agreements = ["Technical soundness confirmed"]
    mock_result.key_disagreements = []
    mock_result.model_responses = {
        "qwen2.5-coder:7b": {"response": "Looks good", "confidence": 0.9}
    }
    service.run_validation = AsyncMock(return_value=mock_result)

    return service


@pytest.fixture
def integration_service(mock_db_session, mock_ghostcrew_service, mock_bigagi_service):
    """Create integration service with mocked dependencies."""
    service = WorkflowToolIntegrationService(mock_db_session)
    service._ghostcrew = mock_ghostcrew_service
    service._bigagi = mock_bigagi_service
    return service


# =============================================================================
# GHOSTCREW GREEN_PAPER TESTS
# =============================================================================

class TestGhostCrewGreenPaper:
    """Tests for GhostCrew GREEN_PAPER integration."""

    @pytest.mark.asyncio
    async def test_greenfield_audit_success(self, integration_service, mock_ghostcrew_service):
        """Test successful greenfield security audit."""
        project_spec = {
            "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
            "core_functionalities": [
                {"name": "User Authentication"},
                {"name": "API Gateway"}
            ],
            "stakeholders": [
                {"role": "Admin"},
                {"role": "User"}
            ],
            "technical_constraints": [
                {"constraint": "Must be GDPR compliant"}
            ]
        }

        result = await integration_service.ghostcrew_greenfield_audit(
            session_id="test-session-123",
            project_id=1,
            project_spec=project_spec
        )

        assert result["status"] == "completed"
        assert result["workflow"] == "GREEN_PAPER"
        assert result["audit_type"] == "greenfield_architecture"
        assert "security_recommendations" in result
        assert "checklist" in result
        assert len(result["security_patterns_recommended"]) > 0
        mock_ghostcrew_service.assist.assert_called_once()

    @pytest.mark.asyncio
    async def test_greenfield_audit_extracts_architecture_context(self, integration_service):
        """Test architecture context extraction from project spec."""
        project_spec = {
            "tech_stack": ["Python", "Flask"],
            "core_functionalities": [{"name": "Feature A"}, {"name": "Feature B"}]
        }

        context = integration_service._extract_architecture_context(project_spec)

        assert "Python" in context
        assert "Flask" in context
        assert "Feature A" in context

    @pytest.mark.asyncio
    async def test_greenfield_checklist_includes_tech_specific_items(self, integration_service):
        """Test checklist generation with tech-stack specific items."""
        project_spec = {
            "tech_stack": ["Python", "React", "REST API"]
        }

        checklist = integration_service._generate_greenfield_checklist(project_spec)

        # Should include base items
        categories = [item["category"] for item in checklist]
        assert "auth" in categories
        assert "crypto" in categories

        # Should include Python-specific items
        items = [item["item"] for item in checklist]
        assert any("SQLAlchemy" in item for item in items)
        assert any("XSS" in item for item in items)
        assert any("JWT" in item or "OAuth2" in item for item in items)


# =============================================================================
# GHOSTCREW TESTING WORKFLOW TESTS
# =============================================================================

class TestGhostCrewTesting:
    """Tests for GhostCrew TESTING workflow integration."""

    @pytest.mark.asyncio
    async def test_test_security_scan_success(self, integration_service, mock_ghostcrew_service):
        """Test successful test security scan."""
        result = await integration_service.ghostcrew_test_security(
            session_id="test-session-456",
            project_id=1,
            test_path="/path/to/tests"
        )

        assert result["workflow"] == "TESTING"
        assert result["test_security_analysis"] is True
        assert "test_specific_findings" in result
        assert "test_security_score" in result
        mock_ghostcrew_service.scan_autonomous.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_security_adds_recommendations(self, integration_service, mock_ghostcrew_service):
        """Test that test-specific recommendations are added."""
        result = await integration_service.ghostcrew_test_security(
            session_id="test-session-456",
            project_id=1,
            test_path="/path/to/tests"
        )

        recommendations = result["recommendations"]
        assert any("environment variables" in rec for rec in recommendations)
        assert any("random test data" in rec for rec in recommendations)


# =============================================================================
# GHOSTCREW ENHANCEMENT WORKFLOW TESTS
# =============================================================================

class TestGhostCrewEnhancement:
    """Tests for GhostCrew ENHANCEMENT workflow integration."""

    @pytest.mark.asyncio
    async def test_enhancement_scan_success(self, integration_service, mock_ghostcrew_service):
        """Test successful enhancement security scan."""
        diff_content = """
        +def login(username, password):
        +    query = f"SELECT * FROM users WHERE name='{username}'"
        +    return db.execute(query)
        """

        result = await integration_service.ghostcrew_enhancement_scan(
            session_id="test-session-789",
            project_id=1,
            diff_content=diff_content,
            enhancement_description="Add login functionality"
        )

        assert result["workflow"] == "ENHANCEMENT"
        assert result["status"] == "completed"
        assert "findings_in_changes" in result
        assert "approval_status" in result
        assert "is_security_sensitive" in result

    @pytest.mark.asyncio
    async def test_enhancement_detects_security_sensitive(self, integration_service, mock_ghostcrew_service):
        """Test detection of security-sensitive enhancements."""
        result = await integration_service.ghostcrew_enhancement_scan(
            session_id="test-session-789",
            project_id=1,
            diff_content="def authenticate(token):",
            enhancement_description="Add authentication system"
        )

        assert result["is_security_sensitive"] is True

    @pytest.mark.asyncio
    async def test_enhancement_approval_blocked_on_critical(self, integration_service, mock_ghostcrew_service):
        """Test that critical findings block approval."""
        # Mock returns a critical finding
        mock_ghostcrew_service._scan_code_snippet = AsyncMock(return_value=[
            {"finding_type": "sql_injection", "severity": "critical", "category": "injection"}
        ])

        result = await integration_service.ghostcrew_enhancement_scan(
            session_id="test-session-789",
            project_id=1,
            diff_content="query = f'SELECT * FROM {table}'",
            enhancement_description="Add query function"
        )

        assert result["approval_status"] == "blocked"


# =============================================================================
# GHOSTCREW QUALITY_IMPROVEMENT WORKFLOW TESTS
# =============================================================================

class TestGhostCrewQualityImprovement:
    """Tests for GhostCrew QUALITY_IMPROVEMENT workflow integration."""

    @pytest.mark.asyncio
    async def test_quality_security_combined_analysis(self, integration_service, mock_ghostcrew_service):
        """Test combined quality and security analysis."""
        result = await integration_service.ghostcrew_quality_security(
            session_id="test-session-101",
            project_id=1,
            target_path="/path/to/project"
        )

        assert result["workflow"] == "QUALITY_IMPROVEMENT"
        assert result["status"] == "completed"
        assert "security_scan" in result
        assert "crew_analysis" in result
        assert "combined_findings" in result
        assert "quality_security_matrix" in result
        assert "improvement_priorities" in result

        # Both scans should be called
        mock_ghostcrew_service.scan_autonomous.assert_called_once()
        mock_ghostcrew_service.run_crew.assert_called_once()

    @pytest.mark.asyncio
    async def test_quality_security_deduplicates_findings(self, integration_service):
        """Test that duplicate findings are removed."""
        findings = [
            {"file_path": "a.py", "line_number": 10, "finding_type": "xss"},
            {"file_path": "a.py", "line_number": 10, "finding_type": "xss"},  # Duplicate
            {"file_path": "b.py", "line_number": 20, "finding_type": "sql"},
        ]

        unique = integration_service._deduplicate_findings(findings)

        assert len(unique) == 2

    @pytest.mark.asyncio
    async def test_quality_security_matrix_categorization(self, integration_service):
        """Test quality vs security matrix categorization."""
        findings = [
            {"category": "injection", "severity": "critical"},
            {"category": "auth", "severity": "high"},
            {"category": "style", "severity": "low"},
            {"category": "performance", "severity": "medium"},
        ]

        matrix = integration_service._build_quality_security_matrix(findings)

        assert matrix["security"]["critical"] == 1
        assert matrix["security"]["high"] == 1
        assert matrix["quality"]["medium"] == 1
        assert matrix["quality"]["low"] == 1


# =============================================================================
# BIGAGI GREEN_PAPER TESTS
# =============================================================================

class TestBigAGIGreenPaper:
    """Tests for BigAGI GREEN_PAPER architecture validation."""

    @pytest.mark.asyncio
    async def test_validate_architecture_success(self, integration_service, mock_bigagi_service):
        """Test successful architecture validation."""
        result = await integration_service.bigagi_validate_architecture(
            session_id="test-session-201",
            project_id=1,
            architecture_doc="# Architecture\n\nMicroservices with API Gateway...",
            primary_model="felix"
        )

        assert result["workflow"] == "GREEN_PAPER"
        assert result["validation_type"] == "architecture"
        assert result["consensus_reached"] is True
        assert result["consensus_score"] == 0.85
        assert result["architecture_verdict"] == "approved"
        assert "next_steps" in result
        mock_bigagi_service.create_validation.assert_called_once()
        mock_bigagi_service.run_validation.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_architecture_verdict_review(self, integration_service, mock_bigagi_service):
        """Test architecture verdict when score is between 0.7 and 0.85."""
        # Mock lower consensus score
        mock_result = mock_bigagi_service.run_validation.return_value
        mock_result.consensus_score = 0.75

        result = await integration_service.bigagi_validate_architecture(
            session_id="test-session-202",
            project_id=1,
            architecture_doc="# Architecture\n\n...",
            primary_model="felix"
        )

        assert result["architecture_verdict"] == "review"

    @pytest.mark.asyncio
    async def test_validate_architecture_verdict_revise(self, integration_service, mock_bigagi_service):
        """Test architecture verdict when score is below 0.7."""
        mock_result = mock_bigagi_service.run_validation.return_value
        mock_result.consensus_score = 0.5
        mock_result.consensus_reached = False

        result = await integration_service.bigagi_validate_architecture(
            session_id="test-session-203",
            project_id=1,
            architecture_doc="# Architecture\n\n...",
            primary_model="felix"
        )

        assert result["architecture_verdict"] == "revise"


# =============================================================================
# BIGAGI BROWN_PAPER TESTS
# =============================================================================

class TestBigAGIBrownPaper:
    """Tests for BigAGI BROWN_PAPER migration validation."""

    @pytest.mark.asyncio
    async def test_validate_migration_plan_success(self, integration_service, mock_bigagi_service):
        """Test successful migration plan validation."""
        migration_plan = {
            "current_state": "Legacy PHP monolith",
            "target_state": "Python microservices",
            "phases": [
                {"name": "Phase 1: Analysis", "duration": "2 weeks"},
                {"name": "Phase 2: Migration", "duration": "8 weeks"}
            ],
            "risks": [
                {"name": "Data loss", "impact": "high"}
            ],
            "rollback_strategy": "Blue-green deployment with instant rollback"
        }

        result = await integration_service.bigagi_validate_migration_plan(
            session_id="test-session-301",
            project_id=1,
            migration_plan=migration_plan,
            primary_model="miguel"
        )

        assert result["workflow"] == "BROWN_PAPER"
        assert result["validation_type"] == "migration_plan"
        assert result["consensus_reached"] is True
        assert "migration_verdict" in result
        assert "recommended_actions" in result

    @pytest.mark.asyncio
    async def test_validate_migration_format_plan(self, integration_service):
        """Test migration plan formatting for validation."""
        plan = {
            "current_state": "Old system",
            "target_state": "New system",
            "phases": [{"name": "Phase 1", "duration": "1 week"}],
            "risks": [{"name": "Risk A", "impact": "high"}],
            "rollback_strategy": "Rollback to backup"
        }

        formatted = integration_service._format_migration_plan(plan)

        assert "# Migration Plan" in formatted
        assert "Current State" in formatted
        assert "Target State" in formatted
        assert "Phase 1" in formatted
        assert "Risk A" in formatted
        assert "Rollback Strategy" in formatted


# =============================================================================
# BIGAGI NEW_FEATURE TESTS
# =============================================================================

class TestBigAGINewFeature:
    """Tests for BigAGI NEW_FEATURE design validation."""

    @pytest.mark.asyncio
    async def test_validate_feature_design_success(self, integration_service, mock_bigagi_service):
        """Test successful feature design validation."""
        feature_design = {
            "name": "User Dashboard",
            "description": "Interactive dashboard with metrics",
            "user_stories": [
                "As a user, I want to see my statistics",
                "As a user, I want to export data"
            ],
            "technical_approach": "React with Chart.js",
            "api_changes": ["GET /api/dashboard/stats"],
            "dependencies": ["chart.js", "react-query"],
            "testing_strategy": "Unit tests + E2E with Playwright"
        }

        result = await integration_service.bigagi_validate_feature_design(
            session_id="test-session-401",
            project_id=1,
            feature_design=feature_design,
            primary_model="felix"
        )

        assert result["workflow"] == "NEW_FEATURE"
        assert result["validation_type"] == "feature_design"
        assert result["feature_name"] == "User Dashboard"
        assert "design_verdict" in result
        assert "implementation_ready" in result
        assert "design_feedback" in result

    @pytest.mark.asyncio
    async def test_validate_feature_format_design(self, integration_service):
        """Test feature design formatting for validation."""
        design = {
            "name": "Test Feature",
            "description": "A test feature",
            "user_stories": ["Story 1", "Story 2"],
            "technical_approach": "REST API",
            "api_changes": ["POST /api/test"],
            "dependencies": ["dep1", "dep2"],
            "testing_strategy": "Unit tests"
        }

        formatted = integration_service._format_feature_design(design)

        assert "# Feature: Test Feature" in formatted
        assert "Description" in formatted
        assert "User Stories" in formatted
        assert "Technical Approach" in formatted
        assert "API Changes" in formatted
        assert "Testing Strategy" in formatted

    @pytest.mark.asyncio
    async def test_validate_feature_implementation_ready(self, integration_service, mock_bigagi_service):
        """Test implementation_ready flag based on consensus score."""
        # High score
        mock_result = mock_bigagi_service.run_validation.return_value
        mock_result.consensus_score = 0.9

        result = await integration_service.bigagi_validate_feature_design(
            session_id="test-session-402",
            project_id=1,
            feature_design={"name": "Test"},
            primary_model="felix"
        )

        assert result["implementation_ready"] is True

        # Lower score
        mock_result.consensus_score = 0.6

        result = await integration_service.bigagi_validate_feature_design(
            session_id="test-session-403",
            project_id=1,
            feature_design={"name": "Test"},
            primary_model="felix"
        )

        assert result["implementation_ready"] is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestWeek90Integration:
    """Integration tests for Week 90 workflow extensions."""

    @pytest.mark.asyncio
    async def test_all_ghostcrew_methods_attached(self, integration_service):
        """Verify all GhostCrew Week 90 methods are attached to service."""
        assert hasattr(integration_service, 'ghostcrew_greenfield_audit')
        assert hasattr(integration_service, 'ghostcrew_test_security')
        assert hasattr(integration_service, 'ghostcrew_enhancement_scan')
        assert hasattr(integration_service, 'ghostcrew_quality_security')

    @pytest.mark.asyncio
    async def test_all_bigagi_methods_attached(self, integration_service):
        """Verify all BigAGI Week 90 methods are attached to service."""
        assert hasattr(integration_service, 'bigagi_validate_architecture')
        assert hasattr(integration_service, 'bigagi_validate_migration_plan')
        assert hasattr(integration_service, 'bigagi_validate_feature_design')

    @pytest.mark.asyncio
    async def test_helper_methods_attached(self, integration_service):
        """Verify helper methods are attached to service."""
        assert hasattr(integration_service, '_extract_architecture_context')
        assert hasattr(integration_service, '_generate_greenfield_checklist')
        assert hasattr(integration_service, '_count_severities')
        assert hasattr(integration_service, '_format_migration_plan')
        assert hasattr(integration_service, '_format_feature_design')


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestWeek90ErrorHandling:
    """Error handling tests for Week 90 components."""

    @pytest.mark.asyncio
    async def test_ghostcrew_greenfield_error_handling(self, integration_service, mock_ghostcrew_service):
        """Test error handling in greenfield audit."""
        mock_ghostcrew_service.assist.side_effect = Exception("Service unavailable")

        result = await integration_service.ghostcrew_greenfield_audit(
            session_id="test-error",
            project_id=1,
            project_spec={}
        )

        assert result["status"] == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_bigagi_validation_error_handling(self, integration_service, mock_bigagi_service):
        """Test error handling in BigAGI validation."""
        mock_bigagi_service.create_validation.side_effect = Exception("Validation failed")

        result = await integration_service.bigagi_validate_architecture(
            session_id="test-error",
            project_id=1,
            architecture_doc="test"
        )

        assert result["status"] == "failed"
        assert "error" in result
