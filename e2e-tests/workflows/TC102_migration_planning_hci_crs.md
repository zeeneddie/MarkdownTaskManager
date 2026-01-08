# TC102: Migration Planning Workflow - HCI-CRS

**ID**: TC102
**Category**: Workflow E2E
**Priority**: High
**Status**: ✅ PASSED (2025-12-16)
**Created**: 2025-12-16
**Week**: 70
**Dependency**: TC101 (requires completed assessment)

---

## Beschrijving

Test de complete Workflow 2 (Migration Planning) voor het HCI-CRS project.
Migratie van legacy ASP.NET/VB.NET naar moderne .NET 8 stack.

## Precondities

1. TC101 is succesvol uitgevoerd (assessment_id beschikbaar)
2. Backend server draait op `http://localhost:8000`
3. Ollama service draait

## Test Data

| Veld | Waarde |
|------|--------|
| Assessment ID | Van TC101 |
| Target Technology | `dotnet8` |
| Target Database | `postgresql` |
| Target Frontend | `angular` |
| Migration Strategy | `strangler_fig` (verwacht) |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/project-workflows/planning/run-sync` | POST | Start synchrone planning |
| `/api/project-workflows/planning/{id}/status` | GET | Check voortgang |
| `/api/project-workflows/planning/{id}` | GET | Volledige details |
| `/api/project-workflows/planning/{id}/report` | GET | Migration report |
| `/api/project-workflows/planning/{id}/approve` | POST | Plan goedkeuren |
| `/api/project-workflows/phases/plan/{id}` | GET | Fase tracking |

---

## Test Stappen

### Stap 1: Start Migration Planning (Sync)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/project-workflows/planning/run-sync \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_id": "<uuid-from-tc101>",
    "target_technology": "dotnet8",
    "target_database": "postgresql",
    "target_frontend": "angular"
  }'
```

**Verwacht Response**:
```json
{
  "success": true,
  "plan_id": "<uuid>",
  "status": "pending_review",
  "adjusted_fp": 500-2000,
  "total_weeks": 20-60,
  "migration_strategy": "strangler_fig|big_bang|parallel_run",
  "team_size_recommended": 3-8
}
```

**Assertions**:
- [ ] `success` == `true`
- [ ] `plan_id` is valid UUID
- [ ] `status` == `"pending_review"`
- [ ] `adjusted_fp` > 0 (Function Points)
- [ ] `total_weeks` > 0
- [ ] `migration_strategy` in bekende strategieen
- [ ] `team_size_recommended` >= 2

### Stap 2: Get Plan Details

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/planning/{plan_id}
```

**Verwacht**:
- [ ] `target_technology` == `"dotnet8"`
- [ ] `target_database` == `"postgresql"`
- [ ] `target_frontend` == `"angular"`
- [ ] `fp_breakdown` bevat categories (EI, EO, EQ, ILF, EIF)
- [ ] `risk_assessment` is object met risk factors
- [ ] `timeline_phases` is array met fases
- [ ] `architecture_recommendations` is array

### Stap 3: Get Migration Report

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/planning/{plan_id}/report
```

**Verwacht**:
- [ ] `report_type` == `"migration_plan"`
- [ ] `report` bevat Markdown formatted plan
- [ ] Report bevat secties: Executive Summary, Scope, Timeline, Risks, Resources

### Stap 4: Get Plan Phases

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/phases/plan/{plan_id}
```

**Verwacht**:
- [ ] 4 fasen geretourneerd (FP Estimation, Target Arch, Strategy, Report)
- [ ] Alle fasen hebben `status` == `"completed"`
- [ ] Fasen zijn genummerd 7-10 (continuation from assessment)

### Stap 5: Approve Plan

**API Call**:
```bash
curl -X POST http://localhost:8000/api/project-workflows/planning/{plan_id}/approve \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "E2E Test Runner",
    "notes": "Approved via TC102 E2E test"
  }'
```

**Verwacht**:
- [ ] `success` == `true`
- [ ] `status` == `"approved"`
- [ ] `reviewed_by` == `"E2E Test Runner"`
- [ ] `reviewed_at` is valid timestamp

---

## 4 Workflow Fasen

| # | Fase | Agent | Output |
|---|------|-------|--------|
| 7 | FP Estimation | Eliza | Function Points berekening |
| 8 | Target Architecture | Felix | Architectuur aanbevelingen |
| 9 | Migration Strategy | Felix | Strategie selectie |
| 10 | Migration Report | Diana | Volledig migration plan |

---

## Migration Strategies Reference

| Strategy | Risk | Best For |
|----------|------|----------|
| `strangler_fig` | Low | Large monoliths, gradual migration |
| `big_bang` | High | Small apps, complete rewrite |
| `parallel_run` | Medium | Critical systems, validation needed |
| `branch_by_abstraction` | Low | Library/framework upgrades |
| `feature_toggle` | Low | Incremental feature migration |
| `database_first` | Medium | Data-centric applications |

---

## Resultaten

### Run 1 - 2025-12-16 (Initial)

| Stap | Status | Opmerking |
|------|--------|-----------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Pytest Implementation

```python
# backend/tests/e2e/test_workflow_2_migration_planning.py

import pytest
from httpx import AsyncClient
from uuid import UUID

BASE_URL = "http://localhost:8000"

@pytest.fixture
async def completed_assessment():
    """Run TC101 first to get assessment_id"""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/api/project-workflows/analysis/run-sync",
            json={
                "project_name": "HCI-CRS",
                "directory_path": "/opt/projecten/hci-crs/src"
            }
        )
        data = response.json()
        return data["assessment_id"]

@pytest.mark.asyncio
async def test_tc102_migration_planning_hci_crs(completed_assessment):
    """TC102: Complete Migration Planning flow for HCI-CRS"""
    async with AsyncClient(base_url=BASE_URL) as client:
        # Step 1: Start planning
        response = await client.post(
            "/api/project-workflows/planning/run-sync",
            json={
                "assessment_id": completed_assessment,
                "target_technology": "dotnet8",
                "target_database": "postgresql",
                "target_frontend": "angular"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        plan_id = data["plan_id"]
        assert UUID(plan_id)
        assert data["status"] == "pending_review"
        assert data["adjusted_fp"] > 0
        assert data["total_weeks"] > 0
        assert data["migration_strategy"] in [
            "strangler_fig", "big_bang", "parallel_run",
            "branch_by_abstraction", "feature_toggle", "database_first"
        ]

        # Step 2: Get details
        response = await client.get(f"/api/project-workflows/planning/{plan_id}")
        assert response.status_code == 200
        details = response.json()

        assert details["target_technology"] == "dotnet8"
        assert "fp_breakdown" in details
        assert "risk_assessment" in details

        # Step 3: Get report
        response = await client.get(f"/api/project-workflows/planning/{plan_id}/report")
        assert response.status_code == 200
        report = response.json()

        assert report["report_type"] == "migration_plan"
        assert "report" in report
        assert len(report["report"]) > 100  # Substantive report

        # Step 4: Get phases
        response = await client.get(f"/api/project-workflows/phases/plan/{plan_id}")
        assert response.status_code == 200
        phases = response.json()

        assert len(phases) == 4
        for phase in phases:
            assert phase["status"] == "completed"

        # Step 5: Approve plan
        response = await client.post(
            f"/api/project-workflows/planning/{plan_id}/approve",
            json={
                "reviewer": "E2E Test Runner",
                "notes": "Approved via TC102"
            }
        )
        assert response.status_code == 200
        approval = response.json()

        assert approval["success"] == True
        assert approval["status"] == "approved"
```

---

## Verwachte Output voor HCI-CRS

**FP Breakdown (geschat)**:
- External Inputs (EI): ~150 FP
- External Outputs (EO): ~100 FP
- External Inquiries (EQ): ~80 FP
- Internal Logical Files (ILF): ~200 FP
- External Interface Files (EIF): ~50 FP
- **Total Unadjusted**: ~580 FP
- **Adjustment Factor**: 1.2-1.5 (complexity)
- **Adjusted FP**: ~700-870 FP

**Timeline (geschat)**:
- Met strangler_fig: 35-50 weken
- Team size: 4-6 developers

---

## Gerelateerde Code

- API: `backend/app/api/project_workflows.py`
- Orchestrator: `backend/app/services/migration_planning_orchestrator.py`
- FP Service: `backend/app/services/migration_estimation_service.py`
- Architecture Service: `backend/app/services/migration_architecture_service.py`
