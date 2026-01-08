"""
Attribution API Tests
Week 21-22 Implementation
"""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.schemas.attribution import (
    TaskOutcomeInput,
    StepDataInput,
    QualityGateResultInput,
    ValidationResultInput,
    ValidationErrorInput,
    OutcomeType,
    ErrorSeverity
)


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_steps():
    """Sample step data for testing."""
    return [
        StepDataInput(
            id="step_1",
            name="Generate Specification",
            agent_id="felix_001",
            succeeded=True,
            duration=5000,
            expected_duration=4000,
            retry_count=0,
            experience_consulted=True,
            pattern_used="spec_template_v2",
            is_critical_path=True
        ),
        StepDataInput(
            id="step_2",
            name="Create Tasks",
            agent_id="felix_001",
            succeeded=True,
            duration=3000,
            expected_duration=3500,
            retry_count=1,
            experience_consulted=False,
            is_critical_path=True
        ),
        StepDataInput(
            id="step_3",
            name="Validate Output",
            agent_id="quinn_001",
            succeeded=True,
            duration=2000,
            expected_duration=2000,
            retry_count=0,
            experience_consulted=True,
            is_critical_path=False
        )
    ]


@pytest.fixture
def sample_quality_gates():
    """Sample quality gate results."""
    return [
        QualityGateResultInput(
            gate_type="ARCHITECTURE",
            gate_name="Architecture Review",
            passed=True,
            issues_caught=2,
            false_positives=0,
            total_checks=15
        ),
        QualityGateResultInput(
            gate_type="SECURITY",
            gate_name="Security Scan",
            passed=True,
            issues_caught=1,
            false_positives=1,
            total_checks=25
        )
    ]


@pytest.fixture
def sample_validations():
    """Sample validation results."""
    return [
        ValidationResultInput(
            phase="LINTING",
            iteration=1,
            passed=True,
            errors=[],
            fix_applied=None,
            time_to_fix=0
        ),
        ValidationResultInput(
            phase="TYPE_CHECK",
            iteration=1,
            passed=False,
            errors=[
                ValidationErrorInput(
                    code="E001",
                    message="Type mismatch",
                    file="src/index.ts",
                    line=42,
                    severity=ErrorSeverity.ERROR
                )
            ],
            fix_applied=None,
            time_to_fix=None
        ),
        ValidationResultInput(
            phase="TYPE_CHECK",
            iteration=2,
            passed=True,
            errors=[],
            fix_applied="Added type annotation",
            time_to_fix=30000
        )
    ]


@pytest.fixture
def sample_task_outcome(sample_steps, sample_quality_gates, sample_validations):
    """Complete task outcome for testing."""
    return TaskOutcomeInput(
        task_id=f"task_{uuid4().hex[:8]}",
        workflow_id=f"workflow_{uuid4().hex[:8]}",
        agent_id="felix_001",
        agent_name="Felix",
        outcome_type=OutcomeType.SUCCESS,
        steps=sample_steps,
        quality_gate_results=sample_quality_gates,
        validation_history=sample_validations,
        duration_ms=10000
    )


# =============================================================================
# API Tests
# =============================================================================

@pytest.mark.asyncio
async def test_record_task_outcome(sample_task_outcome):
    """Test recording a task outcome."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/attribution/outcomes",
            json=sample_task_outcome.model_dump(mode='json')
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert "outcome_id" in data
        assert data["task_id"] == sample_task_outcome.task_id


@pytest.mark.asyncio
async def test_analyze_task_outcome(sample_task_outcome):
    """Test analyzing a recorded task outcome."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First record the outcome
        record_response = await client.post(
            "/api/attribution/outcomes",
            json=sample_task_outcome.model_dump(mode='json')
        )
        outcome_id = record_response.json()["outcome_id"]

        # Then analyze it
        analyze_response = await client.post(
            f"/api/attribution/outcomes/{outcome_id}/analyze"
        )

        assert analyze_response.status_code == 200
        data = analyze_response.json()
        assert data["task_id"] == sample_task_outcome.task_id
        assert data["agent_id"] == sample_task_outcome.agent_id
        assert data["outcome"] == "SUCCESS"
        assert "key_steps" in data
        assert "causal_factors" in data
        assert "confidence" in data


@pytest.mark.asyncio
async def test_list_attributions():
    """Test listing attributions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


@pytest.mark.asyncio
async def test_list_attributions_with_filters():
    """Test listing attributions with filters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/attribution/",
            params={
                "agent_id": "felix_001",
                "outcome": "SUCCESS",
                "min_confidence": 0.5,
                "page": 1,
                "page_size": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_attribution_summary():
    """Test getting attribution summary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_attributions" in data
        assert "success_count" in data
        assert "failure_count" in data
        assert "average_confidence" in data


@pytest.mark.asyncio
async def test_generate_feedback(sample_task_outcome):
    """Test generating feedback from attribution."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Record and analyze
        record_response = await client.post(
            "/api/attribution/outcomes",
            json=sample_task_outcome.model_dump(mode='json')
        )
        outcome_id = record_response.json()["outcome_id"]

        analyze_response = await client.post(
            f"/api/attribution/outcomes/{outcome_id}/analyze"
        )
        attribution_id = analyze_response.json()["id"]

        # Generate feedback
        feedback_response = await client.post(
            f"/api/attribution/{attribution_id}/feedback"
        )

        assert feedback_response.status_code == 200
        data = feedback_response.json()
        assert data["status"] == "generated"
        assert "feedback_id" in data


@pytest.mark.asyncio
async def test_get_pending_feedback():
    """Test getting pending feedback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/feedback/pending")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_agent_summaries():
    """Test getting all agent summaries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/agents/summary")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_agent_metrics():
    """Test getting metrics for a specific agent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/agents/felix_001/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "felix_001"
        assert "total_tasks" in data
        assert "success_rate" in data
        assert "top_success_factors" in data
        assert "top_failure_patterns" in data


@pytest.mark.asyncio
async def test_health_check():
    """Test attribution service health check."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/attribution/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_batch_analyze():
    """Test batch analysis of outcomes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/attribution/batch/analyze",
            json={"outcome_ids": []}  # Empty list for basic test
        )

        assert response.status_code == 200
        data = response.json()
        assert "analyzed" in data
        assert "failed" in data


@pytest.mark.asyncio
async def test_batch_deliver_feedback():
    """Test batch delivery of feedback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/attribution/batch/deliver-feedback",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert "delivered" in data
        assert "failed" in data


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_full_attribution_workflow(sample_task_outcome):
    """Test complete attribution workflow: record -> analyze -> feedback -> deliver."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Record outcome
        record_response = await client.post(
            "/api/attribution/outcomes",
            json=sample_task_outcome.model_dump(mode='json')
        )
        assert record_response.status_code == 200
        outcome_id = record_response.json()["outcome_id"]

        # Step 2: Analyze
        analyze_response = await client.post(
            f"/api/attribution/outcomes/{outcome_id}/analyze"
        )
        assert analyze_response.status_code == 200
        attribution = analyze_response.json()
        attribution_id = attribution["id"]

        # Verify attribution has expected structure
        assert len(attribution["key_steps"]) > 0
        assert attribution["confidence"] >= 0.0
        assert attribution["confidence"] <= 1.0

        # Step 3: Generate feedback
        feedback_response = await client.post(
            f"/api/attribution/{attribution_id}/feedback"
        )
        assert feedback_response.status_code == 200
        feedback_id = feedback_response.json()["feedback_id"]

        # Step 4: Verify pending
        pending_response = await client.get("/api/attribution/feedback/pending")
        assert pending_response.status_code == 200
        pending = pending_response.json()
        assert any(f["feedback_id"] == feedback_id for f in pending)

        # Step 5: Deliver feedback
        deliver_response = await client.post(
            f"/api/attribution/feedback/{feedback_id}/deliver"
        )
        assert deliver_response.status_code == 200


@pytest.mark.asyncio
async def test_failure_attribution(sample_steps, sample_quality_gates):
    """Test attribution for a failed task."""
    # Create a failing task
    failed_steps = [
        StepDataInput(
            id="step_1",
            name="Generate Code",
            agent_id="felix_001",
            succeeded=False,
            duration=8000,
            expected_duration=4000,
            retry_count=3,
            experience_consulted=False,
            is_critical_path=True
        ),
        StepDataInput(
            id="step_2",
            name="Validate Output",
            agent_id="quinn_001",
            succeeded=False,
            duration=1000,
            expected_duration=2000,
            retry_count=0,
            experience_consulted=False,
            is_critical_path=True
        )
    ]

    failed_validations = [
        ValidationResultInput(
            phase="TYPE_CHECK",
            iteration=1,
            passed=False,
            errors=[
                ValidationErrorInput(
                    code="E001",
                    message="Critical type error",
                    file="src/main.ts",
                    line=10,
                    severity=ErrorSeverity.ERROR
                ),
                ValidationErrorInput(
                    code="E002",
                    message="Missing return type",
                    file="src/main.ts",
                    line=25,
                    severity=ErrorSeverity.ERROR
                )
            ]
        ),
        ValidationResultInput(
            phase="TYPE_CHECK",
            iteration=2,
            passed=False,
            errors=[
                ValidationErrorInput(
                    code="E001",
                    message="Critical type error",
                    file="src/main.ts",
                    line=10,
                    severity=ErrorSeverity.ERROR
                )
            ]
        ),
        ValidationResultInput(
            phase="TYPE_CHECK",
            iteration=3,
            passed=False,
            errors=[
                ValidationErrorInput(
                    code="E001",
                    message="Critical type error",
                    file="src/main.ts",
                    line=10,
                    severity=ErrorSeverity.ERROR
                )
            ]
        )
    ]

    failed_outcome = TaskOutcomeInput(
        task_id=f"task_fail_{uuid4().hex[:8]}",
        workflow_id=f"workflow_{uuid4().hex[:8]}",
        agent_id="felix_001",
        agent_name="Felix",
        outcome_type=OutcomeType.FAILURE,
        steps=failed_steps,
        quality_gate_results=sample_quality_gates,
        validation_history=failed_validations,
        duration_ms=15000
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Record
        record_response = await client.post(
            "/api/attribution/outcomes",
            json=failed_outcome.model_dump(mode='json')
        )
        outcome_id = record_response.json()["outcome_id"]

        # Analyze
        analyze_response = await client.post(
            f"/api/attribution/outcomes/{outcome_id}/analyze"
        )
        attribution = analyze_response.json()

        assert attribution["outcome"] == "FAILURE"
        # Failure should have negative impact scores
        negative_steps = [s for s in attribution["key_steps"] if s["impact_score"] < 0]
        assert len(negative_steps) > 0
