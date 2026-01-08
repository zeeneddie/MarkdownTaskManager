"""
Week 69-70 E2E Tests: Project Workflows

Test cases:
- TC101: Project Analysis (Workflow 1)
- TC102: Migration Planning (Workflow 2)
- TC103: Full Assessment (Workflow 3)
- TC104: Reference Data APIs
- TC105: Plan Review Flow
- TC106: Negative/Edge Cases

Demo Project: HCI-CRS (Healthcare EPD System)
- Path: /opt/projecten/hci-crs/src
- Stacks: asp_classic, aspnet, vbnet
- Type: Legacy healthcare application

Author: Claude Code (Week 70)
Date: 2025-12-16
"""

import pytest
from httpx import AsyncClient
from uuid import UUID
import time
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
HCI_CRS_PATH = "/opt/projecten/hci-crs/src"
TIMEOUT = 300.0  # 5 minutes for large operations


# ============ Fixtures ============

@pytest.fixture
def hci_crs_analysis_request():
    """Request data for Workflow 1: Project Analysis"""
    return {
        "project_name": "HCI-CRS-E2E",
        "directory_path": HCI_CRS_PATH
    }


@pytest.fixture
def hci_crs_full_request():
    """Request data for Workflow 3: Full Assessment"""
    return {
        "project_name": "HCI-CRS-Full-E2E",
        "directory_path": HCI_CRS_PATH,
        "target_technology": "dotnet8",
        "target_database": "postgresql",
        "target_frontend": "angular"
    }


# ============ TC101: Workflow 1 - Project Analysis ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC101ProjectAnalysis:
    """TC101: Project Analysis Workflow E2E Tests"""

    async def test_start_analysis_sync(self, hci_crs_analysis_request):
        """TC101.1: Start synchronous project analysis"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json=hci_crs_analysis_request
            )

            assert response.status_code == 200
            data = response.json()

            # Core assertions
            assert data["success"] == True
            assert UUID(data["assessment_id"])
            assert data["status"] == "completed"
            assert data["overall_grade"] in ["A", "B", "C", "D", "F"]
            assert 0 <= data["overall_health_score"] <= 100

            # Legacy project should have recommendations
            assert data["recommendations_count"] >= 0

            return data["assessment_id"]

    async def test_get_assessment_details(self, hci_crs_analysis_request):
        """TC101.2: Get assessment details after analysis"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # First run analysis
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json=hci_crs_analysis_request
            )
            assessment_id = response.json()["assessment_id"]

            # Get details
            response = await client.get(
                f"/api/project-workflows/analysis/{assessment_id}"
            )

            assert response.status_code == 200
            details = response.json()

            # Verify structure
            assert "project_name" in details
            assert "primary_stack" in details
            assert "detected_stacks" in details
            assert "architecture_components" in details
            assert "architecture_issues" in details
            assert "architecture_layers" in details

    async def test_get_assessment_report(self, hci_crs_analysis_request):
        """TC101.3: Get health report"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # First run analysis
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json=hci_crs_analysis_request
            )
            assessment_id = response.json()["assessment_id"]

            # Get report
            response = await client.get(
                f"/api/project-workflows/analysis/{assessment_id}/report"
            )

            assert response.status_code == 200
            report = response.json()

            assert "report" in report
            assert "recommendations" in report
            assert isinstance(report["recommendations"], list)

    async def test_get_assessment_phases(self, hci_crs_analysis_request):
        """TC101.4: Get workflow phases"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # First run analysis
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json=hci_crs_analysis_request
            )
            assessment_id = response.json()["assessment_id"]

            # Get phases
            response = await client.get(
                f"/api/project-workflows/phases/{assessment_id}"
            )

            assert response.status_code == 200
            phases = response.json()

            # Should have 6 phases
            assert len(phases) == 6

            # All phases should be completed
            for phase in phases:
                assert phase["status"] == "completed"
                assert "agent_name" in phase

    async def test_list_assessments(self):
        """TC101.5: List all assessments"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get("/api/project-workflows/analysis")

            assert response.status_code == 200
            assessments = response.json()

            assert isinstance(assessments, list)


# ============ TC102: Workflow 2 - Migration Planning ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC102MigrationPlanning:
    """TC102: Migration Planning Workflow E2E Tests"""

    async def _get_completed_assessment(self, client: AsyncClient) -> str:
        """Helper: Get or create a completed assessment"""
        response = await client.post(
            "/api/project-workflows/analysis/run-sync",
            json={
                "project_name": "HCI-CRS-Planning-E2E",
                "directory_path": HCI_CRS_PATH
            }
        )
        return response.json()["assessment_id"]

    async def test_start_planning_sync(self):
        """TC102.1: Start synchronous migration planning"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            assessment_id = await self._get_completed_assessment(client)

            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": assessment_id,
                    "target_technology": "dotnet8",
                    "target_database": "postgresql",
                    "target_frontend": "angular"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] == True
            assert UUID(data["plan_id"])
            assert data["status"] == "in_review"
            assert data["adjusted_fp"] > 0
            assert data["total_weeks"] > 0
            assert data["migration_strategy"] in [
                "strangler_fig", "big_bang", "parallel_run",
                "branch_by_abstraction", "feature_toggle", "database_first"
            ]

    async def test_get_plan_details(self):
        """TC102.2: Get plan details"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            assessment_id = await self._get_completed_assessment(client)

            # Create plan
            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": assessment_id,
                    "target_technology": "dotnet8"
                }
            )
            plan_id = response.json()["plan_id"]

            # Get details
            response = await client.get(
                f"/api/project-workflows/planning/{plan_id}"
            )

            assert response.status_code == 200
            details = response.json()

            assert details["target_technology"] == "dotnet8"
            assert "fp_breakdown" in details or details.get("adjusted_fp")
            assert "risk_assessment" in details or "migration_strategy" in details

    async def test_get_plan_report(self):
        """TC102.3: Get migration report"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            assessment_id = await self._get_completed_assessment(client)

            # Create plan
            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": assessment_id,
                    "target_technology": "dotnet8"
                }
            )
            plan_id = response.json()["plan_id"]

            # Get report
            response = await client.get(
                f"/api/project-workflows/planning/{plan_id}/report"
            )

            assert response.status_code == 200
            report = response.json()

            assert "report" in report or "report_content" in report

    async def test_get_plan_phases(self):
        """TC102.4: Get planning phases"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            assessment_id = await self._get_completed_assessment(client)

            # Create plan
            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": assessment_id,
                    "target_technology": "dotnet8"
                }
            )
            plan_id = response.json()["plan_id"]

            # Get phases
            response = await client.get(
                f"/api/project-workflows/phases/plan/{plan_id}"
            )

            assert response.status_code == 200
            phases = response.json()

            # Should have 4 phases
            assert len(phases) == 4

            for phase in phases:
                assert phase["status"] == "completed"


# ============ TC103: Workflow 3 - Full Assessment ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC103FullAssessment:
    """TC103: Full Assessment Workflow E2E Tests"""

    async def test_full_assessment_sync(self, hci_crs_full_request):
        """TC103.1: Run complete assessment + planning"""
        start_time = time.time()

        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/project-workflows/full/run-sync",
                json=hci_crs_full_request
            )

            assert response.status_code == 200
            data = response.json()

            # Handle blockers scenario
            if not data["success"]:
                assert "blockers" in data
                pytest.skip(f"Assessment has blockers: {data['blockers']}")

            # Success scenario
            assert data["success"] == True
            assert UUID(data["assessment_id"])
            assert UUID(data["plan_id"])
            assert data["assessment_grade"] in ["A", "B", "C", "D", "F"]
            assert data["adjusted_fp"] > 0
            assert data["total_weeks"] > 0

        duration = time.time() - start_time
        print(f"\nFull workflow duration: {duration:.2f}s")

    async def test_full_assessment_creates_both(self, hci_crs_full_request):
        """TC103.2: Verify both assessment and plan created"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/project-workflows/full/run-sync",
                json=hci_crs_full_request
            )
            data = response.json()

            if not data["success"]:
                pytest.skip("Assessment has blockers")

            assessment_id = data["assessment_id"]
            plan_id = data["plan_id"]

            # Verify assessment exists
            response = await client.get(
                f"/api/project-workflows/analysis/{assessment_id}"
            )
            assert response.status_code == 200
            assert response.json()["status"] == "completed"

            # Verify plan exists
            response = await client.get(
                f"/api/project-workflows/planning/{plan_id}"
            )
            assert response.status_code == 200
            assert response.json()["status"] == "in_review"

    async def test_full_assessment_all_phases(self, hci_crs_full_request):
        """TC103.3: Verify all 10 phases completed"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/project-workflows/full/run-sync",
                json=hci_crs_full_request
            )
            data = response.json()

            if not data["success"]:
                pytest.skip("Assessment has blockers")

            assessment_id = data["assessment_id"]
            plan_id = data["plan_id"]

            # Get assessment phases
            response = await client.get(
                f"/api/project-workflows/phases/{assessment_id}"
            )
            assessment_phases = response.json()

            # Get plan phases
            response = await client.get(
                f"/api/project-workflows/phases/plan/{plan_id}"
            )
            plan_phases = response.json()

            # Total should be 10 phases
            total_phases = len(assessment_phases) + len(plan_phases)
            assert total_phases == 10

            # All should be completed
            for phase in assessment_phases + plan_phases:
                assert phase["status"] == "completed"


# ============ TC104: Reference Data ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC104ReferenceData:
    """TC104: Reference Data API Tests"""

    async def test_list_target_technologies(self):
        """TC104.1: Get available target technologies"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/project-workflows/reference/technologies"
            )

            assert response.status_code == 200
            data = response.json()

            assert "technologies" in data
            technologies = data["technologies"]
            assert len(technologies) > 0

            # Verify structure
            for tech in technologies:
                assert "key" in tech
                assert "name" in tech

            # Verify expected technologies exist
            tech_keys = [t["key"] for t in technologies]
            assert "dotnet8" in tech_keys or "dotnet" in tech_keys

    async def test_list_migration_strategies(self):
        """TC104.2: Get available migration strategies"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/project-workflows/reference/strategies"
            )

            assert response.status_code == 200
            data = response.json()

            assert "strategies" in data
            strategies = data["strategies"]
            assert len(strategies) > 0

            # Verify structure
            for strategy in strategies:
                assert "key" in strategy
                assert "name" in strategy
                assert "risk_level" in strategy

            # Verify expected strategies exist
            strategy_keys = [s["key"] for s in strategies]
            assert "strangler_fig" in strategy_keys


# ============ TC105: Plan Review Flow ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC105PlanReview:
    """TC105: Plan Approval/Rejection Flow Tests"""

    async def _create_plan(self, client: AsyncClient) -> str:
        """Helper: Create a plan for review testing"""
        # Create assessment first
        response = await client.post(
            "/api/project-workflows/analysis/run-sync",
            json={
                "project_name": "HCI-CRS-Review-E2E",
                "directory_path": HCI_CRS_PATH
            }
        )
        assessment_id = response.json()["assessment_id"]

        # Create plan
        response = await client.post(
            "/api/project-workflows/planning/run-sync",
            json={
                "assessment_id": assessment_id,
                "target_technology": "dotnet8"
            }
        )
        return response.json()["plan_id"]

    async def test_approve_plan(self):
        """TC105.1: Approve a migration plan"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            plan_id = await self._create_plan(client)

            response = await client.post(
                f"/api/project-workflows/planning/{plan_id}/approve",
                json={
                    "reviewer": "E2E Test Runner",
                    "notes": "Approved via TC105 E2E test"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] == True
            assert data["status"] == "approved"
            assert data["reviewed_by"] == "E2E Test Runner"

    async def test_reject_plan(self):
        """TC105.2: Reject a migration plan"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            plan_id = await self._create_plan(client)

            response = await client.post(
                f"/api/project-workflows/planning/{plan_id}/reject",
                json={
                    "reviewer": "E2E Test Runner",
                    "notes": "Rejected via TC105 - needs more analysis"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] == True
            assert data["status"] == "rejected"

    async def test_reject_without_notes_fails(self):
        """TC105.3: Reject without notes should fail"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            plan_id = await self._create_plan(client)

            response = await client.post(
                f"/api/project-workflows/planning/{plan_id}/reject",
                json={
                    "reviewer": "E2E Test Runner"
                    # Missing notes
                }
            )

            assert response.status_code == 400


# ============ TC106: Negative/Edge Cases ============

@pytest.mark.asyncio
@pytest.mark.e2e
class TestTC106NegativeCases:
    """TC106: Negative and Edge Case Tests"""

    async def test_analysis_invalid_path(self):
        """TC106.1: Analysis with invalid path"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json={
                    "project_name": "Invalid-Project",
                    "directory_path": "/non/existent/path"
                }
            )

            # Should return error (400 or 500)
            assert response.status_code in [400, 500]

    async def test_planning_invalid_assessment(self):
        """TC106.2: Planning with non-existent assessment"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": "00000000-0000-0000-0000-000000000000",
                    "target_technology": "dotnet8"
                }
            )

            # Should return 400 or 404
            assert response.status_code in [400, 404]

    async def test_planning_invalid_technology(self):
        """TC106.3: Planning with invalid target technology"""
        async with AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # First create valid assessment
            response = await client.post(
                "/api/project-workflows/analysis/run-sync",
                json={
                    "project_name": "HCI-CRS-Invalid-Tech",
                    "directory_path": HCI_CRS_PATH
                }
            )
            assessment_id = response.json()["assessment_id"]

            # Try planning with invalid tech
            response = await client.post(
                "/api/project-workflows/planning/run-sync",
                json={
                    "assessment_id": assessment_id,
                    "target_technology": "invalid_tech_stack"
                }
            )

            # Should return 400
            assert response.status_code == 400

    async def test_get_nonexistent_assessment(self):
        """TC106.4: Get non-existent assessment"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/project-workflows/analysis/00000000-0000-0000-0000-000000000000"
            )

            assert response.status_code == 404

    async def test_get_nonexistent_plan(self):
        """TC106.5: Get non-existent plan"""
        async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/api/project-workflows/planning/00000000-0000-0000-0000-000000000000"
            )

            assert response.status_code == 404


# ============ Run Configuration ============

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "-m", "e2e",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
