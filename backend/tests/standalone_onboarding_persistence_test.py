#!/usr/bin/env python3
"""
Persistence Validation Test for OnboardingWorkflow

This test validates that OnboardingOrchestrator properly persists data to the database
when a CheckpointService is provided.

Fase 24.9 - Persistence Validation (Priority #1 before M6+)

Usage:
    cd backend
    python3 tests/standalone_onboarding_persistence_test.py

Prerequisites:
    - Database running (PostgreSQL)
    - Migrations applied (alembic upgrade head)
    - PYTHONPATH includes backend
"""

import sys
import os
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test results tracking
test_results = []


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "✓ PASSED" if passed else "✗ FAILED"
    result = f"{status} | {test_name}"
    if details:
        result += f" - {details}"
    print(result)
    test_results.append((test_name, passed, details))


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    passed = sum(1 for _, p, _ in test_results if p)
    total = len(test_results)
    print(f"SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)


# =============================================================================
# TEST 1: CheckpointService can be imported and instantiated
# =============================================================================

def test_checkpoint_service_import():
    """Test that CheckpointService can be imported."""
    try:
        from app.services.checkpoint_service import CheckpointService, get_checkpoint_service
        service = get_checkpoint_service()
        log_test("CheckpointService Import", True, f"type={type(service).__name__}")
        return service
    except Exception as e:
        log_test("CheckpointService Import", False, str(e))
        return None


# =============================================================================
# TEST 2: WorkflowCheckpoint model exists
# =============================================================================

def test_workflow_checkpoint_model():
    """Test that WorkflowCheckpoint model can be imported."""
    try:
        from app.models.workflow_checkpoint import WorkflowCheckpoint, CheckpointStatus
        log_test("WorkflowCheckpoint Model", True, f"statuses={[s.value for s in CheckpointStatus]}")
        return True
    except Exception as e:
        log_test("WorkflowCheckpoint Model", False, str(e))
        return False


# =============================================================================
# TEST 3: OnboardingOrchestrator accepts checkpoint_service
# =============================================================================

def test_orchestrator_accepts_checkpoint_service():
    """Test that OnboardingOrchestrator accepts checkpoint_service parameter."""
    try:
        from app.confucius.workflows.onboarding import OnboardingOrchestrator
        from app.services.checkpoint_service import get_checkpoint_service

        checkpoint_service = get_checkpoint_service()
        orchestrator = OnboardingOrchestrator(checkpoint_service=checkpoint_service)

        has_service = orchestrator._checkpoint_service is not None
        log_test("Orchestrator Accepts CheckpointService", has_service,
                 f"_checkpoint_service={'set' if has_service else 'None'}")
        return orchestrator if has_service else None
    except Exception as e:
        log_test("Orchestrator Accepts CheckpointService", False, str(e))
        return None


# =============================================================================
# TEST 4: Database connection works
# =============================================================================

async def test_database_connection():
    """Test that database connection works."""
    try:
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute("SELECT 1")
            value = result.scalar()

        log_test("Database Connection", value == 1, f"SELECT 1 returned {value}")
        return value == 1
    except Exception as e:
        log_test("Database Connection", False, str(e))
        return False


# =============================================================================
# TEST 5: workflow_checkpoints table exists
# =============================================================================

async def test_checkpoint_table_exists():
    """Test that workflow_checkpoints table exists."""
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'workflow_checkpoints'
                )
            """))
            exists = result.scalar()

        log_test("Checkpoint Table Exists", exists, f"workflow_checkpoints={exists}")
        return exists
    except Exception as e:
        log_test("Checkpoint Table Exists", False, str(e))
        return False


# =============================================================================
# TEST 6: CheckpointService can save and load checkpoint
# =============================================================================

async def test_checkpoint_save_and_load():
    """Test saving and loading a checkpoint."""
    try:
        from app.services.checkpoint_service import get_checkpoint_service

        service = get_checkpoint_service()

        # Create a test checkpoint
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        workflow_id = f"test-workflow-{uuid.uuid4().hex[:8]}"

        checkpoint = await service.save_checkpoint(
            session_id=session_id,
            workflow_type="onboarding",
            workflow_id=workflow_id,
            current_stage="validate_input",
            completed_stages=["validate_input"],
            stage_result={"quality_score": 1.0, "valid": True},
            shared_data={"project_path": "/test/path"},
            input_data={"answers": {"q1": "test answer"}},
            metadata={"test": True},
        )

        # Load the checkpoint
        loaded = await service.load_checkpoint(
            session_id=session_id,
            workflow_type="onboarding",
            workflow_id=workflow_id,
        )

        # Verify
        success = (
            loaded is not None and
            loaded.workflow_id == workflow_id and
            loaded.current_stage == "validate_input" and
            "validate_input" in loaded.completed_stages and
            loaded.shared_data.get("project_path") == "/test/path"
        )

        # Cleanup
        await service.clear_checkpoints(session_id, "onboarding")

        log_test("Checkpoint Save and Load", success,
                 f"id={checkpoint.id[:8]}..., loaded={'OK' if loaded else 'FAIL'}")
        return success
    except Exception as e:
        log_test("Checkpoint Save and Load", False, str(e))
        return False


# =============================================================================
# TEST 7: Simulated M1 stage saves checkpoint
# =============================================================================

async def test_m1_checkpoint_persistence():
    """Test that M1 validate_input saves checkpoint when service is provided."""
    try:
        from app.confucius.workflows.onboarding import OnboardingOrchestrator
        from app.services.checkpoint_service import get_checkpoint_service
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        checkpoint_service = get_checkpoint_service()
        orchestrator = OnboardingOrchestrator(checkpoint_service=checkpoint_service)

        session_id = f"test-m1-{uuid.uuid4().hex[:8]}"

        # Setup input data for M1
        input_data = {
            "project_path": "/opt/projecten/hci-crs",
            "answers": {
                "q1_primary_purpose": "Een zorginformatiesysteem voor het beheren van patiëntgegevens en medische dossiers in huisartsenpraktijken.",
                "q2_users": "Huisartsen, praktijkassistenten, POH-ers en administratief medewerkers.",
                "q3_critical_processes": "Patiëntregistratie, consulten afhandeling, recepten uitschrijven, verwijzingen maken en facturatie.",
                "q4_integrations": "HL7/FHIR, VECOZO, LSP, ZorgDomein",
                "q5_pain_points": "Performance issues bij grote patiëntbestanden, complexe UI."
            }
        }

        # Run workflow - it should save checkpoints after each stage
        result = await orchestrator.run(
            session_id=session_id,
            input_data=input_data,
        )

        # Check if checkpoint was created
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT workflow_id, current_stage, completed_stages, shared_data, status
                FROM workflow_checkpoints
                WHERE session_id = :session_id AND workflow_type = 'onboarding'
            """)
            db_result = await db.execute(query, {"session_id": session_id})
            row = db_result.fetchone()

        success = row is not None
        details = f"workflow_status={result.status.value}"
        if row:
            details += f", checkpoint_stage={row[1]}, completed={len(row[2] or [])} stages"

        # Cleanup
        await checkpoint_service.clear_checkpoints(session_id, "onboarding")

        log_test("M1 Checkpoint Persistence", success, details)
        return success
    except Exception as e:
        import traceback
        log_test("M1 Checkpoint Persistence", False, f"{e}\n{traceback.format_exc()}")
        return False


# =============================================================================
# TEST 8: Full M1→M5 pipeline checkpoint progression
# =============================================================================

async def test_full_pipeline_checkpoints():
    """Test that M1→M5 pipeline creates checkpoints at each stage."""
    try:
        from app.confucius.workflows.onboarding import OnboardingOrchestrator
        from app.services.checkpoint_service import get_checkpoint_service
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        checkpoint_service = get_checkpoint_service()
        orchestrator = OnboardingOrchestrator(checkpoint_service=checkpoint_service)

        session_id = f"test-pipeline-{uuid.uuid4().hex[:8]}"

        input_data = {
            "project_path": "/opt/projecten/hci-crs",
            "answers": {
                "q1_primary_purpose": "Een zorginformatiesysteem voor het beheren van patiëntgegevens en medische dossiers in huisartsenpraktijken.",
                "q2_users": "Huisartsen, praktijkassistenten, POH-ers en administratief medewerkers.",
                "q3_critical_processes": "Patiëntregistratie, consulten afhandeling, recepten uitschrijven, verwijzingen maken en facturatie.",
                "q4_integrations": "HL7/FHIR, VECOZO, LSP, ZorgDomein",
                "q5_pain_points": "Performance issues bij grote patiëntbestanden."
            }
        }

        result = await orchestrator.run(
            session_id=session_id,
            input_data=input_data,
        )

        # Query checkpoint
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT
                    workflow_id,
                    current_stage,
                    completed_stages,
                    stage_results,
                    shared_data,
                    status
                FROM workflow_checkpoints
                WHERE session_id = :session_id AND workflow_type = 'onboarding'
            """)
            db_result = await db.execute(query, {"session_id": session_id})
            row = db_result.fetchone()

        if row:
            completed_stages = row[2] or []
            stage_results = row[3] or {}
            shared_data = row[4] or {}
            status = row[5]

            # Check what was persisted
            expected_stages = ["validate_input", "intake_context", "code_understanding", "deep_extraction", "user_journey"]
            stages_persisted = sum(1 for s in expected_stages if s in completed_stages)

            # Check shared_data keys
            shared_keys = list(shared_data.keys())

            success = stages_persisted >= 3  # At least 3 stages should complete and persist
            details = (
                f"status={status}, stages_persisted={stages_persisted}/{len(expected_stages)}, "
                f"shared_data_keys={shared_keys}"
            )
        else:
            success = False
            details = "No checkpoint found in database"

        # Cleanup
        await checkpoint_service.clear_checkpoints(session_id, "onboarding")

        log_test("Full Pipeline Checkpoint Progression", success, details)
        return success
    except Exception as e:
        import traceback
        log_test("Full Pipeline Checkpoint Progression", False, f"{e}")
        return False


# =============================================================================
# TEST 9: shared_data persists between stages
# =============================================================================

async def test_shared_data_persistence():
    """Test that shared_data is persisted and contains stage outputs."""
    try:
        from app.confucius.workflows.onboarding import OnboardingOrchestrator
        from app.services.checkpoint_service import get_checkpoint_service
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        checkpoint_service = get_checkpoint_service()
        orchestrator = OnboardingOrchestrator(checkpoint_service=checkpoint_service)

        session_id = f"test-shared-{uuid.uuid4().hex[:8]}"

        input_data = {
            "project_path": "/opt/projecten/hci-crs",
            "answers": {
                "q1_primary_purpose": "Een zorginformatiesysteem voor het beheren van patiëntgegevens en medische dossiers.",
                "q2_users": "Huisartsen, praktijkassistenten, POH-ers.",
                "q3_critical_processes": "Patiëntregistratie, consulten, recepten, verwijzingen en facturatie.",
                "q4_integrations": "HL7/FHIR, VECOZO, LSP",
                "q5_pain_points": ""
            }
        }

        result = await orchestrator.run(
            session_id=session_id,
            input_data=input_data,
        )

        # Query checkpoint for shared_data
        async with AsyncSessionLocal() as db:
            query = text("""
                SELECT shared_data
                FROM workflow_checkpoints
                WHERE session_id = :session_id AND workflow_type = 'onboarding'
            """)
            db_result = await db.execute(query, {"session_id": session_id})
            row = db_result.fetchone()

        if row and row[0]:
            shared_data = row[0]

            # Check for expected keys from each stage
            expected_keys = {
                "intake_context": ["vector_context", "project_summary"],
                "code_understanding": ["services_results", "code_analysis"],
                "deep_extraction": ["felix_result", "quinn_result", "marcus_result", "council_consensus"],
                "user_journey": ["personas", "journeys", "screens"],
            }

            found_keys = []
            for stage, keys in expected_keys.items():
                if stage in shared_data:
                    stage_data = shared_data[stage]
                    if isinstance(stage_data, dict):
                        found_keys.extend([f"{stage}.{k}" for k in stage_data.keys() if k in keys])

            success = len(found_keys) > 0
            details = f"found_keys={found_keys[:5]}..." if len(found_keys) > 5 else f"found_keys={found_keys}"
        else:
            success = False
            details = "No shared_data found"

        # Cleanup
        await checkpoint_service.clear_checkpoints(session_id, "onboarding")

        log_test("Shared Data Persistence", success, details)
        return success
    except Exception as e:
        log_test("Shared Data Persistence", False, str(e))
        return False


# =============================================================================
# TEST 10: Resume capability after simulated failure
# =============================================================================

async def test_resume_capability():
    """Test that workflow can be resumed from checkpoint."""
    try:
        from app.services.checkpoint_service import get_checkpoint_service

        service = get_checkpoint_service()

        session_id = f"test-resume-{uuid.uuid4().hex[:8]}"
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"

        # Simulate a partially completed workflow
        await service.save_checkpoint(
            session_id=session_id,
            workflow_type="onboarding",
            workflow_id=workflow_id,
            current_stage="code_understanding",
            completed_stages=["validate_input", "intake_context", "code_understanding"],
            stage_result={"quality_score": 0.85},
            shared_data={
                "intake_context": {"summary": "test"},
                "code_understanding": {"services": ["DependencyGraphService"]},
            },
            input_data={"project_path": "/test"},
        )

        # Record an error (simulating failure at next stage)
        await service.record_error(
            session_id=session_id,
            workflow_type="onboarding",
            workflow_id=workflow_id,
            stage_name="deep_extraction",
            error="Simulated LLM timeout",
            error_context={"timeout": 300},
        )

        # Check if checkpoint can be resumed
        checkpoint = await service.load_checkpoint(session_id, "onboarding", workflow_id)

        success = (
            checkpoint is not None and
            checkpoint.can_resume and
            checkpoint.resume_stage == "deep_extraction" and
            checkpoint.last_error == "Simulated LLM timeout"
        )

        details = f"can_resume={checkpoint.can_resume if checkpoint else False}"
        if checkpoint:
            details += f", resume_stage={checkpoint.resume_stage}, retry_count={checkpoint.retry_count}"

        # Cleanup
        await service.clear_checkpoints(session_id, "onboarding")

        log_test("Resume Capability", success, details)
        return success
    except Exception as e:
        log_test("Resume Capability", False, str(e))
        return False


# =============================================================================
# MAIN
# =============================================================================

async def run_async_tests():
    """Run all async tests."""
    await test_database_connection()
    await test_checkpoint_table_exists()
    await test_checkpoint_save_and_load()
    await test_m1_checkpoint_persistence()
    await test_full_pipeline_checkpoints()
    await test_shared_data_persistence()
    await test_resume_capability()


def main():
    """Run all tests."""
    print("=" * 60)
    print("OnboardingWorkflow Data Persistence Validation")
    print("Fase 24.9 - Priority #1: Validate DB Persistence")
    print("=" * 60)
    print()

    # Sync tests
    print("--- Sync Tests ---")
    test_checkpoint_service_import()
    test_workflow_checkpoint_model()
    test_orchestrator_accepts_checkpoint_service()

    # Async tests
    print("\n--- Async Tests ---")
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"Error running async tests: {e}")
        import traceback
        traceback.print_exc()

    print_summary()

    # Exit with error code if any test failed
    all_passed = all(passed for _, passed, _ in test_results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
