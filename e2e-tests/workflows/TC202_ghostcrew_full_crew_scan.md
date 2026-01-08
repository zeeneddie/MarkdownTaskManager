# TC202: GhostCrew Full Crew Scan

**ID**: TC202
**Category**: Security E2E
**Priority**: High
**Status**: DRAFT
**Created**: 2025-12-17
**Week**: 80

---

## Beschrijving

Test de Full Crew Scan met alle drie security agents: SecurityAgent, AuditAgent, ComplianceAgent.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. Database is up-to-date met GhostCrew migraties
3. Test project beschikbaar

## Test Data

| Veld | Waarde |
|------|--------|
| Scan Type | `full` |
| Agents | SecurityAgent, AuditAgent, ComplianceAgent |
| Project ID | `1` |
| Expected Output | Security findings + Compliance checks |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/ghostcrew/crew/{project_id}` | POST | Run full crew |
| `/api/ghostcrew/scans/{scan_id}` | GET | Get scan details |
| `/api/ghostcrew/scans/{scan_id}/findings` | GET | Get findings |
| `/api/ghostcrew/shadow-graph/patterns` | GET | Learned patterns |

---

## Test Stappen

### Stap 1: Run Full Security Crew

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ghostcrew/crew/1 \
  -H "Content-Type: application/json" \
  -d '{
    "target_path": "/home/eddie/Projects/MarkdownTaskManager/backend",
    "agents": null
  }'
```

**Verwacht Response**:
```json
{
  "crew_run_id": "<uuid>",
  "status": "completed",
  "agents_run": ["SecurityAgent", "AuditAgent", "ComplianceAgent"],
  "total_findings": ">= 0",
  "security_score": 0-100
}
```

**Assertions**:
- [ ] Response status 200
- [ ] `crew_run_id` is valid UUID
- [ ] `agents_run` contains at least 1 agent
- [ ] `security_score` is integer 0-100

### Stap 2: Verify Each Agent Ran

**Verwacht**:
- [ ] SecurityAgent: OWASP Top 10 patterns scanned
- [ ] AuditAgent: Code audit completed
- [ ] ComplianceAgent: GDPR/SOC2 checks (if applicable)

### Stap 3: Get Aggregated Findings

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/scans/{crew_run_id}/findings?limit=100
```

**Verwacht**:
- [ ] Findings from all agents combined
- [ ] Each finding has `agent_source` field
- [ ] Deduplication applied (no exact duplicates)

### Stap 4: Verify Patterns Updated

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/shadow-graph/patterns?limit=20
```

**Verwacht**:
- [ ] New patterns recorded from scan
- [ ] `times_detected` incremented for matched patterns
- [ ] `accuracy_score` within valid range (0.0 - 1.0)

---

## Agent Responsibilities

| Agent | Focus | OWASP Categories |
|-------|-------|-----------------|
| SecurityAgent | Vulnerability patterns | A01-A10 |
| AuditAgent | Code quality + auth | A01, A07 |
| ComplianceAgent | Regulatory | GDPR, SOC2, HIPAA |

---

## Resultaten

### Run 1 - 2025-12-17

| Stap | Status | Opmerking |
|------|--------|-----------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |

---

## Pytest Implementation

```python
# backend/tests/e2e/test_ghostcrew_full_crew.py

import pytest
from httpx import AsyncClient
from uuid import UUID

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_tc202_ghostcrew_full_crew():
    """TC202: Full Crew Security Scan with all agents"""
    async with AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Step 1: Run full crew
        response = await client.post(
            "/api/ghostcrew/crew/1",
            json={
                "target_path": "/home/eddie/Projects/MarkdownTaskManager/backend"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert "crew_run_id" in data or "status" in data
        crew_run_id = data.get("crew_run_id")

        if crew_run_id:
            # Step 2: Verify agents ran
            assert "agents_run" in data
            assert len(data["agents_run"]) >= 1

            # Step 3: Get findings
            response = await client.get(
                f"/api/ghostcrew/scans/{crew_run_id}/findings?limit=100"
            )
            assert response.status_code == 200
            findings = response.json()
            assert isinstance(findings, list)

        # Step 4: Check patterns
        response = await client.get(
            "/api/ghostcrew/shadow-graph/patterns?limit=20"
        )
        assert response.status_code == 200
        patterns = response.json()
        assert isinstance(patterns, list)

        for pattern in patterns:
            if "accuracy_score" in pattern:
                assert 0.0 <= pattern["accuracy_score"] <= 1.0
```

---

## Gerelateerde Code

- Crew Runner: `backend/app/services/ghostcrew_service.py:run_crew()`
- SecurityAgent: `backend/app/services/security_agents.py`
- ShadowGraph: `backend/app/services/shadow_graph_service.py`

---

## Notities

- Full crew scan duurt langer (30-120 seconden)
- Agents werken parallel waar mogelijk
- Findings worden automatisch deduplicated
- ShadowGraph leert van elke crew run
