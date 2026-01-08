# TC203: GhostCrew Assist Mode (Interactive)

**ID**: TC203
**Category**: Security E2E
**Priority**: Medium
**Status**: DRAFT
**Created**: 2025-12-17
**Week**: 80

---

## Beschrijving

Test de interactieve Assist mode van GhostCrew voor security vragen en code analyse.

## Precondities

1. Backend server draait op `http://localhost:8000`
2. SecurityRAG knowledge base is geinitialiseerd

## Test Data

| Veld | Waarde |
|------|--------|
| Mode | `assist` |
| Query Types | Security questions, Code review |
| Expected | Recommendations, OWASP/CWE references |

---

## API Endpoints Onder Test

| Endpoint | Method | Beschrijving |
|----------|--------|--------------|
| `/api/ghostcrew/assist` | POST | Interactive assist |
| `/api/ghostcrew/knowledge/search` | GET | Search knowledge base |
| `/api/ghostcrew/knowledge/owasp/{category}` | GET | OWASP guidance |
| `/api/ghostcrew/knowledge/cwe/{cwe_id}` | GET | CWE guidance |

---

## Test Stappen

### Stap 1: Security Question (No Code)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ghostcrew/assist \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I prevent SQL injection in Python?",
    "context": null,
    "include_knowledge": true
  }'
```

**Verwacht Response**:
```json
{
  "response": "<markdown with recommendations>",
  "recommendations": ["Use parameterized queries", "..."],
  "owasp_references": ["A03:2021"],
  "cwe_references": ["CWE-89"]
}
```

**Assertions**:
- [ ] Response status 200
- [ ] `response` is non-empty string
- [ ] Contains SQL injection prevention advice
- [ ] References OWASP A03 or CWE-89

### Stap 2: Code Context Analysis

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ghostcrew/assist \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Is this code secure?",
    "context": "query = f\"SELECT * FROM users WHERE id = {user_id}\"\ncursor.execute(query)",
    "include_knowledge": true
  }'
```

**Verwacht**:
- [ ] Identifies SQL injection vulnerability
- [ ] Provides secure alternative (parameterized query)
- [ ] References CWE-89

### Stap 3: OWASP Knowledge Lookup

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/knowledge/owasp/A03
```

**Verwacht**:
```json
{
  "category": "A03:2021",
  "name": "Injection",
  "description": "...",
  "prevention": ["...", "..."]
}
```

**Assertions**:
- [ ] `name` == "Injection"
- [ ] `prevention` is non-empty array
- [ ] `description` explains the vulnerability

### Stap 4: CWE Knowledge Lookup

**API Call**:
```bash
curl http://localhost:8000/api/ghostcrew/knowledge/cwe/CWE-79
```

**Verwacht**:
```json
{
  "cwe_id": "CWE-79",
  "name": "Cross-site Scripting (XSS)",
  "description": "...",
  "mitigation": "...",
  "example": "..."
}
```

**Assertions**:
- [ ] `name` contains "XSS" or "Cross-site"
- [ ] `mitigation` is non-empty
- [ ] `example` shows vulnerable code

### Stap 5: Knowledge Base Search

**API Call**:
```bash
curl "http://localhost:8000/api/ghostcrew/knowledge/search?query=authentication%20bypass&limit=5"
```

**Verwacht**:
- [ ] Returns array of results
- [ ] Results relevant to authentication
- [ ] Each result has `title` and `content`

---

## Query Types Getest

| Query Type | Example | Expected Response |
|------------|---------|-------------------|
| Prevention | "How to prevent XSS?" | Recommendations + OWASP |
| Code Review | "Is this secure?" + code | Vulnerability + fix |
| Best Practice | "Authentication best practices" | Checklist |
| Vulnerability | "What is SSRF?" | Definition + examples |

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
# backend/tests/e2e/test_ghostcrew_assist.py

import pytest
from httpx import AsyncClient

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_tc203_ghostcrew_assist_mode():
    """TC203: Interactive Assist Mode"""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Security question
        response = await client.post(
            "/api/ghostcrew/assist",
            json={
                "query": "How do I prevent SQL injection?",
                "include_knowledge": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "message" in data

        # Step 2: Code analysis
        vulnerable_code = '''
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        '''
        response = await client.post(
            "/api/ghostcrew/assist",
            json={
                "query": "Is this code secure?",
                "context": vulnerable_code,
                "include_knowledge": True
            }
        )
        assert response.status_code == 200

        # Step 3: OWASP lookup
        response = await client.get("/api/ghostcrew/knowledge/owasp/A03")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data

        # Step 4: CWE lookup
        response = await client.get("/api/ghostcrew/knowledge/cwe/CWE-79")
        assert response.status_code == 200
        data = response.json()
        assert "cwe_id" in data or "name" in data

        # Step 5: Search
        response = await client.get(
            "/api/ghostcrew/knowledge/search",
            params={"query": "authentication", "limit": 5}
        )
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
```

---

## Gerelateerde Code

- Assist: `backend/app/services/ghostcrew_service.py:assist()`
- SecurityRAG: `backend/app/services/security_rag_service.py`
- Knowledge Base: `OWASP_TOP_10_2021`, `CWE_KNOWLEDGE`

---

## Notities

- Assist mode is stateless (geen sessie nodig)
- Kennis komt uit ingebouwde OWASP/CWE databases
- Context (code) wordt geanalyseerd voor vulnerabilities
- Responses bevatten actionable recommendations
