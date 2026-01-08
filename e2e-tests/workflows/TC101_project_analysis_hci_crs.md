# TC101: Project Analysis Workflow - HCI-CRS

**ID**: TC101
**Category**: Workflow E2E
**Priority**: High
**Status**: ✅ PASSED (2025-12-16)
**Created**: 2025-12-16
**Week**: 70

---

## Beschrijving

Test de complete Workflow 1 (Project Analysis) met het HCI-CRS healthcare EPD systeem als demo project.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. Database is up-to-date (alembic upgrade head)
3. Project bestaat in `/opt/projecten/hci-crs/src`
4. Ollama service draait (voor agent LLM calls)

## Test Data

| Veld | Waarde |
|------|--------|
| Project Naam | `HCI-CRS` |
| Project Pad | `/opt/projecten/hci-crs/src` |
| Verwachte Stacks | `asp_classic`, `aspnet`, `vbnet` |
| Verwachte Grade | `C` of `D` (legacy codebase) |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/project-workflows/analysis/run-sync` | POST | Start synchrone analyse |
| `/api/project-workflows/analysis/{id}/status` | GET | Check voortgang |
| `/api/project-workflows/analysis/{id}` | GET | Volledige details |
| `/api/project-workflows/analysis/{id}/report` | GET | Health report |
| `/api/project-workflows/phases/{id}` | GET | Fase tracking |

---

## Test Stappen

### Stap 1: Start Project Analysis (Sync)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/project-workflows/analysis/run-sync \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "HCI-CRS",
    "directory_path": "/opt/projecten/hci-crs/src"
  }'
```

**Verwacht Response**:
```json
{
  "success": true,
  "assessment_id": "<uuid>",
  "status": "completed",
  "overall_grade": "C|D",
  "overall_health_score": 40-60,
  "architecture_score": 30-50,
  "security_grade": "C|D",
  "quality_grade": "C|D",
  "recommendations_count": "> 0",
  "blockers_count": ">= 0"
}
```

**Assertions**:
- [ ] `success` == `true`
- [ ] `assessment_id` is valid UUID
- [ ] `status` == `"completed"`
- [ ] `overall_grade` in `["A", "B", "C", "D", "F"]`
- [ ] `overall_health_score` is integer 0-100
- [ ] `recommendations_count` > 0 (legacy code heeft altijd aanbevelingen)

### Stap 2: Get Assessment Details

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/analysis/{assessment_id}
```

**Verwacht**:
- [ ] `primary_stack` bevat `"aspnet"` of `"vbnet"`
- [ ] `detected_stacks` is array met >= 1 items
- [ ] `architecture_analysis` is niet leeg
- [ ] `security_findings` is array
- [ ] `quality_findings` is array
- [ ] `health_summary` is Markdown string

### Stap 3: Get Health Report

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/analysis/{assessment_id}/report
```

**Verwacht**:
- [ ] `report` bevat Markdown formatted health report
- [ ] `recommendations` is array met concrete aanbevelingen
- [ ] `blockers` is array (kan leeg zijn)

### Stap 4: Get Phase Details

**API Call**:
```bash
curl http://localhost:8000/api/project-workflows/phases/{assessment_id}
```

**Verwacht**:
- [ ] 6 fasen geretourneerd (Registration, AS-IS, Code, Security, Quality, Report)
- [ ] Alle fasen hebben `status` == `"completed"`
- [ ] Elke fase heeft `duration_ms` > 0
- [ ] Fasen zijn genummerd 1-6

---

## 6 Workflow Fasen

| # | Fase | Agent | Output |
|---|------|-------|--------|
| 1 | Registration | - | ApplicationRegistry scan |
| 2 | AS-IS Architecture | Miguel | Architecture patterns |
| 3 | Code Analysis | CodeRAG | Code embeddings |
| 4 | Security Analysis | Quinn | Security findings |
| 5 | Quality Analysis | Quinn | Quality findings |
| 6 | Health Report | Diana | Markdown report |

---

## Resultaten

### Run 1 - 2025-12-16 (Initial)

| Stap | Status | Opmerking |
|------|--------|-----------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |

---

## Pytest Implementation

```python
# backend/tests/e2e/test_workflow_1_project_analysis.py

import pytest
from httpx import AsyncClient
from uuid import UUID

BASE_URL = "http://localhost:8000"

@pytest.fixture
def hci_crs_project():
    return {
        "project_name": "HCI-CRS",
        "directory_path": "/opt/projecten/hci-crs/src"
    }

@pytest.mark.asyncio
async def test_tc101_project_analysis_hci_crs(hci_crs_project):
    """TC101: Complete Project Analysis flow for HCI-CRS"""
    async with AsyncClient(base_url=BASE_URL) as client:
        # Step 1: Start analysis
        response = await client.post(
            "/api/project-workflows/analysis/run-sync",
            json=hci_crs_project
        )
        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assessment_id = data["assessment_id"]
        assert UUID(assessment_id)  # Valid UUID
        assert data["status"] == "completed"
        assert data["overall_grade"] in ["A", "B", "C", "D", "F"]
        assert 0 <= data["overall_health_score"] <= 100

        # Step 2: Get details
        response = await client.get(f"/api/project-workflows/analysis/{assessment_id}")
        assert response.status_code == 200
        details = response.json()

        assert details["primary_stack"] is not None
        assert "architecture_analysis" in details

        # Step 3: Get report
        response = await client.get(f"/api/project-workflows/analysis/{assessment_id}/report")
        assert response.status_code == 200
        report = response.json()

        assert "report" in report
        assert isinstance(report["recommendations"], list)

        # Step 4: Get phases
        response = await client.get(f"/api/project-workflows/phases/{assessment_id}")
        assert response.status_code == 200
        phases = response.json()

        assert len(phases) == 6
        for phase in phases:
            assert phase["status"] == "completed"
```

---

## Gerelateerde Code

- API: `backend/app/api/project_workflows.py`
- Orchestrator: `backend/app/services/project_assessment_orchestrator.py`
- AS-IS Service: `backend/app/services/asis_architecture_service.py`
- Models: `backend/app/models/project_assessment.py`

---

## Notities

- HCI-CRS is een healthcare EPD systeem met VB.NET, C#, ASP Classic
- Verwacht legacy patterns: WebForms, ASMX, Windows Auth
- Security issues verwacht: hardcoded credentials, SQL injection patterns
