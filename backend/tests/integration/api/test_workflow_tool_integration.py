"""
Tests for WorkflowToolIntegrationService - Week 79

Tests all workflow integrations:
- GREEN_PAPER: Claude-Mem + CCPM
- BROWN_PAPER: Claude-Mem + CCPM
- QUALITY_AUDIT: BigAGI + Claude-Mem
- Generic workflow observation capture
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.workflow_tool_integration_service import (
    WorkflowToolIntegrationService,
    get_workflow_integration_service
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_claude_mem():
    """Create mock ClaudeMemService."""
    mock = AsyncMock()
    mock.create_session.return_value = {
        "session_id": "test_session",
        "status": "created",
        "token_budget": 6000
    }
    mock.capture_observation.return_value = {
        "observation_id": "obs_123",
        "status": "captured"
    }
    mock.get_context_window.return_value = {
        "context_text": "Previous context here",
        "token_count": 500,
        "observation_count": 5
    }
    return mock


@pytest.fixture
def mock_ccpm():
    """Create mock CCPMOrchestrator."""
    mock = AsyncMock()
    mock.decompose_prd.return_value = {
        "decomposition_id": "decomp_456",
        "statistics": {
            "total_epics": 3,
            "total_features": 8,
            "total_stories": 25
        },
        "hierarchy": {
            "epics": [
                {"id": "EPIC-001", "title": "Core Feature"}
            ]
        }
    }
    mock.get_next_task.return_value = {
        "recommendations": [
            {"id": "TASK-001", "title": "First task", "priority": "high"}
        ]
    }
    return mock


@pytest.fixture
def mock_bigagi():
    """Create mock BigAGIBeamService."""
    mock = AsyncMock()

    # Mock validation creation
    validation_mock = MagicMock()
    validation_mock.id = "val_789"
    mock.create_validation.return_value = validation_mock

    # Mock validation result
    result_mock = MagicMock()
    result_mock.validation_id = "val_789"
    result_mock.consensus_reached = True
    result_mock.consensus_score = 0.85
    result_mock.recommendation = "accept"
    result_mock.final_answer = "Finding is valid"
    result_mock.key_agreements = ["All models agree on severity"]
    result_mock.key_disagreements = []
    mock.run_validation.return_value = result_mock

    return mock


@pytest.fixture
def service(mock_db, mock_claude_mem, mock_ccpm, mock_bigagi):
    """Create service with mocked dependencies."""
    svc = WorkflowToolIntegrationService(mock_db)
    svc._claude_mem = mock_claude_mem
    svc._ccpm = mock_ccpm
    svc._bigagi = mock_bigagi
    return svc


# =============================================================================
# GREEN_PAPER Tests (Option A: Claude-Mem)
# =============================================================================

class TestGreenPaperClaudeMem:
    """Tests for GREEN_PAPER Claude-Mem integration."""

    @pytest.mark.asyncio
    async def test_session_start_creates_claude_mem_session(self, service, mock_claude_mem):
        """Test that GREEN_PAPER session start creates Claude-Mem session."""
        result = await service.green_paper_session_start(
            session_id="gp_test_123",
            project_id=1,
            title="Test Project"
        )

        assert "session_id" in result or "status" in result
        mock_claude_mem.create_session.assert_called_once()
        mock_claude_mem.capture_observation.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_submitted_captures_observation(self, service, mock_claude_mem):
        """Test that answer submission captures observation with correct tags."""
        result = await service.green_paper_answer_submitted(
            session_id="gp_test_123",
            question_number=1,
            question_text="What problem are you solving?",
            answer="We need better task management."
        )

        assert result.get("observation_id") or result.get("status")

        # Check that capture was called with correct tags
        call_args = mock_claude_mem.capture_observation.call_args
        assert "problem_statement" in call_args.kwargs.get("tags", [])
        assert call_args.kwargs.get("priority") == "high"

    @pytest.mark.asyncio
    async def test_get_context_for_constitution(self, service, mock_claude_mem):
        """Test context retrieval for constitution generation."""
        result = await service.green_paper_get_context_for_constitution(
            session_id="gp_test_123"
        )

        assert "context_text" in result
        mock_claude_mem.get_context_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhance_prompt_with_context(self, service, mock_claude_mem):
        """Test prompt enhancement with context injection."""
        base_prompt = "Generate a project constitution."

        result = await service.green_paper_enhance_prompt_with_context(
            session_id="gp_test_123",
            base_prompt=base_prompt
        )

        assert "Session Context" in result
        assert base_prompt in result


# =============================================================================
# GREEN_PAPER Tests (Option B: CCPM)
# =============================================================================

class TestGreenPaperCCPM:
    """Tests for GREEN_PAPER CCPM integration."""

    @pytest.mark.asyncio
    async def test_constitution_approved_triggers_decomposition(self, service, mock_ccpm):
        """Test that constitution approval triggers PRD decomposition."""
        constitution = {
            "problem_statement": "Build a task management system",
            "stakeholders": [{"role": "Developer", "needs": ["task tracking"]}],
            "core_functionalities": [
                {"name": "Task Management", "priority": "high"}
            ],
            "success_criteria": [{"metric": "User adoption", "target": "80%"}],
            "technical_constraints": [],
            "timeline": {"total_duration_weeks": 12}
        }

        result = await service.green_paper_constitution_approved(
            project_id=1,
            constitution_id="const_123",
            constitution_content=constitution
        )

        assert result["status"] == "success"
        assert "statistics" in result
        mock_ccpm.decompose_prd.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_recommendations(self, service, mock_ccpm):
        """Test task recommendation retrieval after decomposition."""
        result = await service.green_paper_get_task_recommendations(
            project_id=1,
            limit=5
        )

        assert result["status"] == "success"
        assert "recommendations" in result
        mock_ccpm.get_next_task.assert_called_once()


# =============================================================================
# BROWN_PAPER Tests (Option A: Claude-Mem)
# =============================================================================

class TestBrownPaperClaudeMem:
    """Tests for BROWN_PAPER Claude-Mem integration."""

    @pytest.mark.asyncio
    async def test_session_start_creates_migration_session(self, service, mock_claude_mem):
        """Test that BROWN_PAPER session start creates Claude-Mem session."""
        result = await service.brown_paper_session_start(
            session_id="bp_test_456",
            project_id=2,
            title="Legacy Migration",
            application_name="OldApp"
        )

        assert result.get("session_id") or result.get("status")

        # Should have higher token budget for migration
        call_args = mock_claude_mem.create_session.call_args
        assert call_args.kwargs.get("token_budget") == 8000

    @pytest.mark.asyncio
    async def test_answer_submitted_with_scan_data(self, service, mock_claude_mem):
        """Test answer submission with scan data enrichment."""
        scan_data = {
            "violations": 150,
            "complexity_score": 75,
            "security_score": 60,
            "tech_debt_hours": 500
        }

        result = await service.brown_paper_answer_submitted(
            session_id="bp_test_456",
            question_number=2,
            question_text="What technical debt exists?",
            answer="High complexity in core modules.",
            scan_data=scan_data
        )

        assert result.get("observation_id") or result.get("status")

        # Check tags for Q2 (technical debt)
        call_args = mock_claude_mem.capture_observation.call_args
        tags = call_args.kwargs.get("tags", [])
        assert "technical_debt" in tags
        assert "scan_enriched" in tags
        assert call_args.kwargs.get("priority") == "critical"  # Q1-4 are critical

    @pytest.mark.asyncio
    async def test_migration_specific_tags_by_question(self, service, mock_claude_mem):
        """Test that migration-specific tags are applied per question."""
        question_tags = {
            1: ["current_state", "tech_stack", "architecture"],
            3: ["security", "vulnerabilities", "risk"],
            6: ["migration_strategy", "approach", "decision"],
            8: ["success_criteria", "checkpoints", "planning"]
        }

        for q_num, expected_tags in question_tags.items():
            mock_claude_mem.capture_observation.reset_mock()

            await service.brown_paper_answer_submitted(
                session_id="bp_test_456",
                question_number=q_num,
                question_text=f"Question {q_num}",
                answer=f"Answer {q_num}"
            )

            call_args = mock_claude_mem.capture_observation.call_args
            actual_tags = call_args.kwargs.get("tags", [])
            for tag in expected_tags:
                assert tag in actual_tags, f"Q{q_num} missing tag: {tag}"


# =============================================================================
# BROWN_PAPER Tests (Option B: CCPM)
# =============================================================================

class TestBrownPaperCCPM:
    """Tests for BROWN_PAPER CCPM integration."""

    @pytest.mark.asyncio
    async def test_analysis_approved_triggers_migration_decomposition(self, service, mock_ccpm):
        """Test that analysis approval triggers migration task decomposition."""
        analysis = {
            "current_state": {
                "tech_stack": ["PHP", "MySQL"],
                "architecture": "Monolith",
                "complexity": 85
            },
            "technical_debt": {
                "priority": "High",
                "categories": [{"name": "Code smell", "hours": 200}],
                "top_issues": ["No tests", "Magic numbers"]
            },
            "security_issues": {
                "score": 45,
                "vulnerabilities": [
                    {"severity": "high", "description": "SQL injection risk"}
                ]
            },
            "migration_strategy": {
                "type": "strangler-fig",
                "description": "Gradually replace modules",
                "phases": [
                    {"name": "Phase 1", "weeks": 4}
                ]
            },
            "preservation_needs": [
                {"name": "Core Algorithm", "reason": "Business critical"}
            ],
            "risks": [
                {"name": "Data loss", "impact": "high", "mitigation": "Backups"}
            ],
            "success_criteria": [
                {"metric": "Performance", "target": "2x faster"}
            ]
        }

        result = await service.brown_paper_analysis_approved(
            project_id=2,
            analysis_id="analysis_789",
            analysis_content=analysis
        )

        assert result["status"] == "success"
        mock_ccpm.decompose_prd.assert_called_once()

        # Check that migration type is included in context
        call_args = mock_ccpm.decompose_prd.call_args
        context = call_args.kwargs.get("decomposition_context", {})
        assert context.get("migration_type") == "strangler-fig"

    def test_migration_analysis_to_prd_conversion(self, service):
        """Test that migration analysis is correctly converted to PRD format."""
        analysis = {
            "current_state": {"tech_stack": ["Java", "Oracle"]},
            "technical_debt": {"top_issues": ["Legacy code"]},
            "migration_strategy": {"type": "big-bang"}
        }

        prd = service._migration_analysis_to_prd(analysis)

        assert "Migration Project" in prd
        assert "Tech Stack" in prd or "Java" in prd
        assert "Epic 1" in prd  # Technical Debt epic


# =============================================================================
# QUALITY_AUDIT Tests (Option C: BigAGI)
# =============================================================================

class TestQualityAuditBigAGI:
    """Tests for QUALITY_AUDIT BigAGI integration."""

    @pytest.mark.asyncio
    async def test_validate_high_severity_finding(self, service, mock_bigagi):
        """Test validation of high severity findings."""
        result = await service.quality_audit_validate_finding(
            task_description="Security audit of payment module",
            finding="SQL injection vulnerability in user input handling",
            agent_model="quinn",
            severity="high"
        )

        assert result["validated"] is True
        assert result["consensus_reached"] is True
        assert result["consensus_score"] == 0.85
        mock_bigagi.create_validation.assert_called_once()
        mock_bigagi.run_validation.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_low_severity_validation(self, service, mock_bigagi):
        """Test that low severity findings are skipped."""
        result = await service.quality_audit_validate_finding(
            task_description="Code review",
            finding="Minor style issue",
            severity="low"
        )

        assert result["validated"] is False
        assert "Skipped validation" in result["reason"]
        mock_bigagi.create_validation.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_validation(self, service, mock_bigagi):
        """Test batch validation of multiple findings."""
        findings = [
            {"content": "Critical vulnerability", "severity": "critical"},
            {"content": "High risk issue", "severity": "high"},
            {"content": "Minor issue", "severity": "low"},
            {"content": "Medium issue", "severity": "medium"}
        ]

        result = await service.quality_audit_validate_batch(
            task_description="Security audit",
            findings=findings
        )

        assert result["total_findings"] == 4
        assert result["validated_count"] == 2  # Only critical and high
        assert len(result["results"]) == 4

    @pytest.mark.asyncio
    async def test_enhance_audit_with_validation(self, service, mock_bigagi):
        """Test enhancing audit result with validation data."""
        audit_result = {
            "task": "Security Audit",
            "agent": "quinn",
            "security_issues": [
                {"description": "XSS vulnerability", "severity": "high"},
                {"description": "Missing CSRF token", "severity": "critical"}
            ],
            "code_quality_issues": [
                {"description": "Complex method", "severity": "medium"}
            ]
        }

        result = await service.quality_audit_enhance_with_validation(audit_result)

        assert "bigagi_validation" in result
        assert result["bigagi_validation"]["enabled"] is True
        assert "confidence_level" in result
        assert "validation_status" in result


# =============================================================================
# Generic Workflow Tests
# =============================================================================

class TestGenericWorkflowCapture:
    """Tests for generic workflow observation capture."""

    @pytest.mark.asyncio
    async def test_capture_observation_for_migration(self, service, mock_claude_mem):
        """Test observation capture for MIGRATION workflow."""
        result = await service.workflow_capture_observation(
            workflow_type="MIGRATION",
            session_id="mig_test_001",
            content="Completed data migration phase",
            observation_type="progress",
            priority="high",
            tags=["phase_complete"]
        )

        assert result.get("observation_id") or result.get("status")

        call_args = mock_claude_mem.capture_observation.call_args
        tags = call_args.kwargs.get("tags", [])
        assert "migration" in tags
        assert "progress" in tags
        assert "phase_complete" in tags

    @pytest.mark.asyncio
    async def test_capture_observation_for_bug(self, service, mock_claude_mem):
        """Test observation capture for BUG workflow."""
        result = await service.workflow_capture_observation(
            workflow_type="BUG",
            session_id="bug_test_001",
            content="Found root cause in authentication module",
            observation_type="finding",
            priority="high"
        )

        call_args = mock_claude_mem.capture_observation.call_args
        tags = call_args.kwargs.get("tags", [])
        assert "bug" in tags

    @pytest.mark.asyncio
    async def test_migration_phase_completed(self, service, mock_claude_mem):
        """Test migration phase completion hook."""
        phase_results = {
            "metrics": {"files_migrated": 50, "tables_converted": 10},
            "issues_resolved": ["issue1", "issue2"],
            "next_phase": "Testing"
        }

        result = await service.migration_phase_completed(
            session_id="mig_test_001",
            phase_name="Data Migration",
            phase_results=phase_results
        )

        call_args = mock_claude_mem.capture_observation.call_args
        content = call_args.kwargs.get("content", "")
        assert "Data Migration" in content
        assert "files_migrated" in content

    @pytest.mark.asyncio
    async def test_bug_root_cause_identified(self, service, mock_claude_mem):
        """Test bug root cause identification hook."""
        result = await service.bug_root_cause_identified(
            session_id="bug_test_001",
            bug_description="Login fails intermittently",
            root_cause="Race condition in session handling",
            affected_files=["auth.py", "session.py"],
            fix_approach="Add mutex lock"
        )

        call_args = mock_claude_mem.capture_observation.call_args
        content = call_args.kwargs.get("content", "")
        assert "Race condition" in content
        assert "auth.py" in content

    @pytest.mark.asyncio
    async def test_quality_audit_scan_complete(self, service, mock_claude_mem):
        """Test quality audit scan completion hook."""
        scan_results = {
            "score": 75,
            "issues_found": 15,
            "critical_count": 2,
            "high_count": 5,
            "recommendations": ["Add input validation", "Use parameterized queries"]
        }

        result = await service.quality_audit_scan_complete(
            session_id="qa_test_001",
            scan_type="security",
            scan_results=scan_results
        )

        call_args = mock_claude_mem.capture_observation.call_args
        assert call_args.kwargs.get("priority") == "critical"  # Has critical issues


# =============================================================================
# Cross-Workflow Context Tests
# =============================================================================

class TestCrossWorkflowContext:
    """Tests for cross-workflow context retrieval."""

    @pytest.mark.asyncio
    async def test_get_workflow_context(self, service, mock_claude_mem):
        """Test context retrieval for any workflow type."""
        result = await service.get_workflow_context(
            workflow_type="MIGRATION",
            session_id="mig_test_001",
            token_budget=3000
        )

        assert "context_text" in result
        mock_claude_mem.get_context_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_inject_workflow_context(self, service, mock_claude_mem):
        """Test context injection into prompts."""
        base_prompt = "Analyze the migration progress."

        result = await service.inject_workflow_context(
            workflow_type="MIGRATION",
            session_id="mig_test_001",
            base_prompt=base_prompt,
            token_budget=2000
        )

        assert "Workflow Context" in result
        assert "MIGRATION" in result
        assert base_prompt in result

    @pytest.mark.asyncio
    async def test_inject_context_handles_errors(self, service, mock_claude_mem):
        """Test that context injection returns base prompt on error."""
        mock_claude_mem.get_context_window.return_value = {"error": "Session not found"}

        base_prompt = "Original prompt."
        result = await service.inject_workflow_context(
            workflow_type="TESTING",
            session_id="test_001",
            base_prompt=base_prompt
        )

        assert result == base_prompt


# =============================================================================
# Factory Tests
# =============================================================================

class TestFactory:
    """Tests for factory function."""

    def test_get_workflow_integration_service(self, mock_db):
        """Test factory function creates service."""
        service = get_workflow_integration_service(mock_db)

        assert isinstance(service, WorkflowToolIntegrationService)
        assert service.db == mock_db


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in integrations."""

    @pytest.mark.asyncio
    async def test_green_paper_session_start_handles_error(self, service, mock_claude_mem):
        """Test error handling in session start."""
        mock_claude_mem.create_session.side_effect = Exception("Database error")

        result = await service.green_paper_session_start(
            session_id="gp_error_test",
            project_id=1
        )

        assert "error" in result
        assert "fallback" in result

    @pytest.mark.asyncio
    async def test_constitution_approved_handles_decomposition_error(self, service, mock_ccpm):
        """Test error handling in PRD decomposition."""
        mock_ccpm.decompose_prd.side_effect = Exception("LLM unavailable")

        result = await service.green_paper_constitution_approved(
            project_id=1,
            constitution_id="const_error",
            constitution_content={"problem_statement": "Test"}
        )

        assert result["status"] == "error"
        assert "retry manually" in result["message"]

    @pytest.mark.asyncio
    async def test_bigagi_validation_handles_error(self, service, mock_bigagi):
        """Test error handling in BigAGI validation."""
        mock_bigagi.create_validation.side_effect = Exception("Model unavailable")

        result = await service.quality_audit_validate_finding(
            task_description="Test audit",
            finding="Test finding",
            severity="critical"
        )

        assert result["validated"] is False
        assert "error" in result
