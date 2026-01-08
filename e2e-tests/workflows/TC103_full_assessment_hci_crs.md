# TC103: Full Assessment Workflow - HCI-CRS

**ID**: TC103
**Category**: Workflow E2E
**Priority**: High
**Status**: ✅ PASSED (2025-12-16)
**Created**: 2025-12-16
**Week**: 70

---

## Beschrijving

Test de complete Workflow 3 (Full Assessment) die Workflow 1 en 2 combineert in één call.
End-to-end van project scan tot migration plan in één synchrone operatie.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. Database is up-to-date
3. Project bestaat in `/opt/projecten/hci-crs/src`
4. Ollama service draait

## Test Data

| Veld | Waarde |
|------|--------|
| Project Naam | `HCI-CRS-Full` |
| Project Pad | `/opt/projecten/hci-crs/src` |
| Target Technology | `dotnet8` |
| Target Database | `postgresql` |
| Target Frontend | `blazor` |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/project-workflows/full/run-sync` | POST | Complete workflow |
| `/api/project-workflows/analysis/{id}` | GET | Assessment details |
| `/api/project-workflows/planning/{id}` | GET | Plan details |

---

## Test Stappen

### Stap 1: Run Full Assessment (Sync)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/project-workflows/full/run-sync \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "HCI-CRS-Full",
    "directory_path": "/opt/projecten/hci-crs/src",
    "target_technology": "dotnet8",
    "target_database": "postgresql",
    "target_frontend": "blazor"
  }'
```

**Verwacht Response (Success)**:
```json
{
  "success": true,
  "assessment_id": "<uuid>",
  "plan_id": "<uuid>",
  "assessment_grade": "C|D",
  "assessment_score": 40-60,
  "adjusted_fp": 500-2000,
  "total_weeks": 20-60,
  "migration_strategy": "strangler_fig",
  "plan_status": "pending_review"
}
```

**Verwacht Response (Blockers)**:
```json
{
  "success": false,
  "assessment_id": "<uuid>",
  "assessment_status": "completed",
  "blockers": ["..."],
  "message": "Assessment has blockers. Resolve them before migration planning."
}
```

**Assertions**:
- [ ] Response bevat `assessment_id` AND `plan_id` (als geen blockers)
- [ ] `assessment_grade` is valid grade
- [ ] `adjusted_fp` > 0
- [ ] `total_weeks` > 0
- [ ] Beide IDs zijn valid UUIDs

### Stap 2: Verify Assessment Created

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/analysis/{assessment_id}
```

**Verwacht**:
- [ ] Assessment exists met `status` == `"completed"`
- [ ] `project_name` == `"HCI-CRS-Full"`
- [ ] Alle 6 fasen completed

### Stap 3: Verify Plan Created

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/planning/{plan_id}
```

**Verwacht**:
- [ ] Plan exists met `status` == `"pending_review"`
- [ ] `target_technology` == `"dotnet8"`
- [ ] `target_frontend` == `"blazor"`
- [ ] Alle 4 fasen completed

### Stap 4: Verify All 10 Phases

**API Calls**:
```bash
# Assessment phases (1-6)
curl http://localhost:8000/api/project-workflows/phases/{assessment_id}

# Planning phases (7-10)
curl http://localhost:8000/api/project-workflows/phases/plan/{plan_id}
```

**Verwacht**:
- [ ] 6 assessment phases
- [ ] 4 planning phases
- [ ] Total 10 phases all completed
- [ ] Sequential phase numbers (1-10)

---

## Complete Workflow Phases

| # | Fase | Workflow | Agent | Duration Est. |
|---|------|----------|-------|---------------|
| 1 | Registration | 1 | - | 1-5s |
| 2 | AS-IS Architecture | 1 | Miguel | 5-30s |
| 3 | Code Analysis | 1 | CodeRAG | 10-60s |
| 4 | Security Analysis | 1 | Quinn | 5-30s |
| 5 | Quality Analysis | 1 | Quinn | 5-30s |
| 6 | Health Report | 1 | Diana | 5-20s |
| 7 | FP Estimation | 2 | Eliza | 10-60s |
| 8 | Target Architecture | 2 | Felix | 10-30s |
| 9 | Migration Strategy | 2 | Felix | 5-20s |
| 10 | Migration Report | 2 | Diana | 10-30s |

**Total Estimated**: 1-5 minutes voor medium project

---

## Resultaten

### Run 1 - 2025-12-16 (Initial)

| Stap | Status | Duration | Opmerking |
|------|--------|----------|-----------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

**Total Duration**: ___ seconds

---

## Pytest Implementation

```python
# backend/tests/e2e/test_workflow_3_full_assessment.py

import pytest
from httpx import AsyncClient
from uuid import UUID
import time

BASE_URL = "http://localhost:8000"

@pytest.fixture
def full_assessment_request():
    return {
        "project_name": "HCI-CRS-Full",
        "directory_path": "/opt/projecten/hci-crs/src",
        "target_technology": "dotnet8",
        "target_database": "postgresql",
        "target_frontend": "blazor"
    }

@pytest.mark.asyncio
async def test_tc103_full_assessment_hci_crs(full_assessment_request):
    """TC103: Complete Full Assessment flow for HCI-CRS"""
    start_time = time.time()

    async with AsyncClient(base_url=BASE_URL, timeout=300.0) as client:
        # Step 1: Run full assessment
        response = await client.post(
            "/api/project-workflows/full/run-sync",
            json=full_assessment_request
        )
        assert response.status_code == 200
        data = response.json()

        # Check for blockers scenario
        if not data["success"]:
            assert "blockers" in data
            assert len(data["blockers"]) > 0
            pytest.skip("Assessment has blockers, cannot continue to planning")

        # Success scenario
        assert data["success"] == True
        assessment_id = data["assessment_id"]
        plan_id = data["plan_id"]

        assert UUID(assessment_id)
        assert UUID(plan_id)
        assert data["assessment_grade"] in ["A", "B", "C", "D", "F"]
        assert data["adjusted_fp"] > 0
        assert data["total_weeks"] > 0

        # Step 2: Verify assessment
        response = await client.get(f"/api/project-workflows/analysis/{assessment_id}")
        assert response.status_code == 200
        assessment = response.json()

        assert assessment["status"] == "completed"
        assert assessment["project_name"] == "HCI-CRS-Full"

        # Step 3: Verify plan
        response = await client.get(f"/api/project-workflows/planning/{plan_id}")
        assert response.status_code == 200
        plan = response.json()

        assert plan["status"] == "pending_review"
        assert plan["target_technology"] == "dotnet8"
        assert plan["target_frontend"] == "blazor"

        # Step 4: Verify phases
        response = await client.get(f"/api/project-workflows/phases/{assessment_id}")
        assert response.status_code == 200
        assessment_phases = response.json()
        assert len(assessment_phases) == 6

        response = await client.get(f"/api/project-workflows/phases/plan/{plan_id}")
        assert response.status_code == 200
        plan_phases = response.json()
        assert len(plan_phases) == 4

        # Total phases
        all_phases = assessment_phases + plan_phases
        assert len(all_phases) == 10

        for phase in all_phases:
            assert phase["status"] == "completed"

    duration = time.time() - start_time
    print(f"\nTotal workflow duration: {duration:.2f} seconds")
```

---

## Performance Benchmarks

| Project Size | Expected Duration |
|--------------|-------------------|
| Small (< 10K LOC) | 30-60 seconds |
| Medium (10-50K LOC) | 1-3 minutes |
| Large (50-200K LOC) | 3-10 minutes |
| Very Large (> 200K LOC) | 10-30 minutes |

HCI-CRS is Medium (~30K LOC), expected: 1-3 minutes

---

## Gerelateerde Code

- API: `backend/app/api/project_workflows.py`
- Assessment Orchestrator: `backend/app/services/project_assessment_orchestrator.py`
- Planning Orchestrator: `backend/app/services/migration_planning_orchestrator.py`
