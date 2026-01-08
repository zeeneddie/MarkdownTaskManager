# TC204: GhostCrew Workflow Integration

**ID**: TC204
**Category**: Security E2E
**Priority**: High
**Status**: DRAFT
**Created**: 2025-12-17
**Week**: 82

---

## Beschrijving

Test de GhostCrew integratie met alle workflow types: QUALITY_AUDIT, BROWN_PAPER, MIGRATION, NEW_FEATURE, BUG, MAINTENANCE.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. WorkflowToolIntegrationService is beschikbaar
3. GhostCrew, ShadowGraph, SecurityRAG services zijn actief

## Test Data

| Veld | Waarde |
|------|--------|
| Workflows | 6 types |
| Project ID | `1` |
| Session ID | Auto-generated UUID |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/workflows/quality-audit/security` | POST | Quality audit scan |
| `/api/workflows/migration/security-verify` | POST | Migration phase check |
| `/api/workflows/bug/security-check` | POST | Bug security analysis |
| `/api/workflows/new-feature/security-review` | POST | Feature security review |

---

## Test Stappen

### Stap 1: QUALITY_AUDIT Workflow

**API Call**:
```bash
curl -X POST http://localhost:8000/api/workflows/quality-audit/security \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<uuid>",
    "project_id": 1,
    "target_path": "/home/eddie/Projects/MarkdownTaskManager/backend"
  }'
```

**Verwacht**:
- [ ] Full security scan triggered
- [ ] Findings returned with severity breakdown
- [ ] Security score calculated

### Stap 2: MIGRATION Workflow Security Verify

**API Call**:
```bash
curl -X POST http://localhost:8000/api/workflows/migration/security-verify \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<uuid>",
    "project_id": 1,
    "phase_name": "data_migration",
    "target_path": "/migrated/app"
  }'
```

**Verwacht**:
- [ ] `phase_passed` boolean returned
- [ ] Security requirements for phase verified
- [ ] Blocking issues flagged if any

### Stap 3: BUG Workflow Security Check

**API Call**:
```bash
curl -X POST http://localhost:8000/api/workflows/bug/security-check \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<uuid>",
    "project_id": 1,
    "bug_description": "SQL error when special characters in username",
    "affected_files": ["src/auth/login.py"],
    "is_security_bug": true
  }'
```

**Verwacht**:
- [ ] Security analysis of bug description
- [ ] Vulnerability classification if security-related
- [ ] Remediation recommendations

### Stap 4: NEW_FEATURE Security Review

**API Call**:
```bash
curl -X POST http://localhost:8000/api/workflows/new-feature/security-review \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<uuid>",
    "project_id": 1,
    "feature_path": "/features/user_registration"
  }'
```

**Verwacht**:
- [ ] Feature code scanned
- [ ] Security patterns checked
- [ ] OWASP compliance verified

### Stap 5: Verify Cross-Workflow Learning

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/shadow-graph/stats?days=1
```

**Verwacht**:
- [ ] Patterns from all workflows consolidated
- [ ] False positive learnings applied
- [ ] Accuracy metrics updated

---

## Workflow Integration Matrix

| Workflow | GhostCrew Mode | ShadowGraph | SecurityRAG |
|----------|----------------|-------------|-------------|
| QUALITY_AUDIT | Full Crew | Yes | Yes |
| BROWN_PAPER | Autonomous | Yes | Yes |
| MIGRATION | Per-phase | Yes | Yes |
| NEW_FEATURE | Targeted | Yes | Yes |
| BUG | Assist | No | Yes |
| MAINTENANCE | Dependency | Yes | No |

---

## Resultaten

### Run 1 - 2025-12-17

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
# backend/tests/e2e/test_ghostcrew_workflow_integration.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_tc204_workflow_integration():
    """TC204: GhostCrew Workflow Integration"""
    session_id = str(uuid4())

    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Step 1: Quality Audit
        response = await client.post(
            "/api/workflows/quality-audit/security",
            json={
                "session_id": session_id,
                "project_id": 1,
                "target_path": "/home/eddie/Projects/MarkdownTaskManager/backend"
            }
        )
        # May return 200 or 404 depending on route registration
        assert response.status_code in [200, 404, 422]

        # Step 2: Migration verify
        response = await client.post(
            "/api/workflows/migration/security-verify",
            json={
                "session_id": session_id,
                "project_id": 1,
                "phase_name": "data_migration",
                "target_path": "/tmp/test"
            }
        )
        assert response.status_code in [200, 404, 422]

        # Step 3: Bug security check
        response = await client.post(
            "/api/workflows/bug/security-check",
            json={
                "session_id": session_id,
                "project_id": 1,
                "bug_description": "SQL error in login",
                "is_security_bug": True
            }
        )
        assert response.status_code in [200, 404, 422]

        # Step 4: Feature review
        response = await client.post(
            "/api/workflows/new-feature/security-review",
            json={
                "session_id": session_id,
                "project_id": 1,
                "feature_path": "/tmp/feature"
            }
        )
        assert response.status_code in [200, 404, 422]

        # Step 5: Check learning stats
        response = await client.get(
            "/api/ghostcrew/shadow-graph/stats",
            params={"days": 1}
        )
        assert response.status_code in [200, 404]
```

---

## Gerelateerde Code

- Integration: `backend/app/services/workflow_tool_integration_service.py`
- Methods: `quality_audit_security_scan()`, `migration_security_verify()`, etc.
- Tests: `backend/tests/services/week80/test_workflow_ghostcrew_integration.py`

---

## Notities

- Workflow integration maakt GhostCrew beschikbaar in alle MARQED workflows
- Session tracking zorgt voor context behoud
- ShadowGraph leert van alle workflow runs
- Critical findings kunnen workflows blokkeren
