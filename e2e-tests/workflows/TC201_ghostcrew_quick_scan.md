# TC201: GhostCrew Quick Security Scan

**ID**: TC201
**Category**: Security E2E
**Priority**: High
**Status**: DRAFT
**Created**: 2025-12-17
**Week**: 80

---

## Beschrijving

Test de Quick Scan functionaliteit van GhostCrew voor snelle security vulnerability detectie.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. Database is up-to-date met GhostCrew migraties (034, 035)
3. Test project beschikbaar in `/home/eddie/Projects/MarkdownTaskManager`

## Test Data

| Veld | Waarde |
|------|--------|
| Scan Type | `quick` |
| Project ID | `1` (indien aanwezig) |
| Repo Path | `/home/eddie/Projects/MarkdownTaskManager/backend` |
| Expected Patterns | SQL Injection, XSS, Hardcoded Secrets, SSRF |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/ghostcrew/scan` | POST | Start autonome scan |
| `/api/ghostcrew/scans/{scan_id}` | GET | Get scan details |
| `/api/ghostcrew/scans/{scan_id}/findings` | GET | Get scan findings |
| `/api/ghostcrew/dashboard` | GET | Dashboard statistics |

---

## Test Stappen

### Stap 1: Start Quick Scan

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ghostcrew/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/home/eddie/Projects/MarkdownTaskManager/backend",
    "project_id": 1,
    "scan_type": "quick"
  }'
```

**Verwacht Response**:
```json
{
  "scan_id": "<uuid>",
  "status": "completed",
  "scan_type": "quick",
  "findings_count": ">= 0",
  "total_findings": ">= 0"
}
```

**Assertions**:
- [ ] Response status 200
- [ ] `scan_id` is valid UUID
- [ ] `status` == `"completed"` of `"in_progress"`
- [ ] `scan_type` == `"quick"`
- [ ] `findings_count` is integer >= 0

### Stap 2: Get Scan Details

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/scans/{scan_id}
```

**Verwacht**:
- [ ] `id` matches `scan_id`
- [ ] `scan_type` == `"quick"`
- [ ] `status` in `["pending", "running", "completed", "failed"]`
- [ ] `created_at` is valid timestamp
- [ ] `repo_path` matches input

### Stap 3: Get Scan Findings

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/scans/{scan_id}/findings?limit=50
```

**Verwacht**:
- [ ] Response is array
- [ ] Each finding has `id`, `finding_type`, `severity`, `file_path`
- [ ] `severity` in `["critical", "high", "medium", "low", "info"]`
- [ ] `owasp_category` follows format `A0X:2021`
- [ ] `cwe_id` follows format `CWE-XXX`

### Stap 4: Verify Dashboard Stats Updated

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/dashboard
```

**Verwacht**:
- [ ] `total_scans` >= 1
- [ ] `learning_stats.total_patterns` >= 0
- [ ] `recent_scans` is array containing the new scan

---

## Vulnerability Patterns Getest

| Pattern | OWASP | CWE | Expected Detection |
|---------|-------|-----|-------------------|
| SQL Injection | A03:2021 | CWE-89 | f-strings met SQL |
| XSS | A03:2021 | CWE-79 | innerHTML assignments |
| Hardcoded Secret | A02:2021 | CWE-798 | api_key, password vars |
| SSRF | A10:2021 | CWE-918 | User-controlled URLs |
| Path Traversal | A01:2021 | CWE-22 | File path manipulation |

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
# backend/tests/e2e/test_ghostcrew_quick_scan.py

import pytest
from httpx import AsyncClient
from uuid import UUID

BASE_URL = "http://localhost:8000"

@pytest.fixture
def scan_request():
    return {
        "repo_path": "/home/eddie/Projects/MarkdownTaskManager/backend",
        "project_id": 1,
        "scan_type": "quick"
    }

@pytest.mark.asyncio
async def test_tc201_ghostcrew_quick_scan(scan_request):
    """TC201: Quick Security Scan with GhostCrew"""
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Step 1: Start scan
        response = await client.post(
            "/api/ghostcrew/scan",
            json=scan_request
        )
        assert response.status_code == 200
        data = response.json()

        assert "scan_id" in data
        scan_id = data["scan_id"]
        assert UUID(scan_id)  # Valid UUID
        assert data["scan_type"] == "quick"

        # Step 2: Get scan details
        response = await client.get(f"/api/ghostcrew/scans/{scan_id}")
        assert response.status_code == 200
        details = response.json()

        assert details["scan_type"] == "quick"
        assert details["status"] in ["pending", "running", "completed", "failed"]

        # Step 3: Get findings
        response = await client.get(f"/api/ghostcrew/scans/{scan_id}/findings?limit=50")
        assert response.status_code == 200
        findings = response.json()

        assert isinstance(findings, list)
        for finding in findings:
            assert "id" in finding
            assert "finding_type" in finding
            assert "severity" in finding
            assert finding["severity"] in ["critical", "high", "medium", "low", "info"]

        # Step 4: Check dashboard
        response = await client.get("/api/ghostcrew/dashboard")
        assert response.status_code == 200
        dashboard = response.json()

        assert dashboard["total_scans"] >= 1
```

---

## Gerelateerde Code

- API: `backend/app/api/ghostcrew.py`
- Service: `backend/app/services/ghostcrew_service.py`
- Models: `backend/app/models/ghostcrew.py`
- Patterns: `VULNERABILITY_PATTERNS` in ghostcrew_service.py

---

## Notities

- Quick scan focust op high-severity patterns voor snelle feedback
- Gemiddelde scan tijd: < 30 seconden voor kleine projecten
- Findings worden automatisch naar ShadowGraph gestuurd voor learning
