# GhostCrew Security System - Architecture

**Version:** 1.0
**Week:** 80-82
**Status:** 95% Complete

---

## Overview

GhostCrew is the AI-powered security scanning system for the MarQed AI Agent Platform. It provides automated vulnerability detection, security knowledge integration, and continuous learning through the Shadow Graph pattern recognition system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GHOSTCREW SECURITY SYSTEM                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       3 SECURITY AGENTS                           │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐        │   │
│  │  │ SecurityAgent  │ │  AuditAgent    │ │ComplianceAgent │        │   │
│  │  │ - Vuln scan    │ │ - Code review  │ │ - OWASP check  │        │   │
│  │  │ - Pattern match│ │ - Access audit │ │ - Compliance   │        │   │
│  │  │ - Risk assess  │ │ - Log analysis │ │ - Policy check │        │   │
│  │  └────────────────┘ └────────────────┘ └────────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SHADOW GRAPH (Learning Layer)                  │   │
│  │  - Pattern recognition from scan results                          │   │
│  │  - False positive learning                                        │   │
│  │  - Accuracy improvement over time                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SECURITY KNOWLEDGE (RAG)                       │   │
│  │  - OWASP Top 10 guidance                                          │   │
│  │  - CWE database integration                                       │   │
│  │  - Remediation recommendations                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. GhostCrewService

Main service coordinating security operations.

**Location:** `backend/app/services/ghostcrew_service.py`

**Capabilities:**
- `assist()` - Security Q&A with knowledge integration
- `scan_autonomous()` - Full automated security scan
- `run_crew()` - Multi-agent security analysis
- `get_scan()`, `get_scan_findings()` - Scan result retrieval
- `mark_finding_false_positive()` - FP feedback for learning

**Performance Features (Week 80):**
- Compiled regex caching (LRU cache, 128 patterns)
- TTL cache for knowledge lookups (5 min)
- TTL cache for pattern lookups (10 min)
- Parallel file scanning with configurable batch size (10 files/batch)
- Large file skipping (>1MB)

### 2. ShadowGraphService

Pattern learning and recognition system.

**Location:** `backend/app/services/shadow_graph_service.py`

**Capabilities:**
- `get_patterns()` - Retrieve learned vulnerability patterns
- `get_learning_stats()` - Statistics on pattern accuracy
- `confirm_vulnerability()` - Positive feedback for true positives
- `get_recommendations()` - Pattern-based remediation

### 3. SecurityRAGService

Security knowledge retrieval system.

**Location:** `backend/app/services/security_rag_service.py`

**Capabilities:**
- `initialize_knowledge_base()` - Load OWASP/CWE data
- `get_owasp_guidance()` - OWASP Top 10 category info
- `get_cwe_guidance()` - CWE weakness details
- `get_remediation()` - Language-specific fix guidance
- `search_knowledge()` - Search security knowledge base

---

## API Endpoints (19)

### Security Scanning (4)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ghostcrew/assist` | POST | Security Q&A assistance |
| `/api/ghostcrew/scan` | POST | Start autonomous security scan |
| `/api/ghostcrew/crew/{project_id}` | POST | Run full security crew |
| `/api/ghostcrew/scans/{scan_id}` | GET | Get scan details |

### Scan Management (4)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ghostcrew/scans/{scan_id}/findings` | GET | Get scan findings |
| `/api/ghostcrew/projects/{project_id}/scans` | GET | List project scans |
| `/api/ghostcrew/findings/{finding_id}/false-positive` | POST | Mark as false positive |
| `/api/ghostcrew/dashboard` | GET | Dashboard data |

### Shadow Graph (6)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ghostcrew/shadow-graph/patterns` | GET | Get learned patterns |
| `/api/ghostcrew/shadow-graph/stats` | GET | Learning statistics |
| `/api/ghostcrew/shadow-graph/top-patterns` | GET | Most common patterns |
| `/api/ghostcrew/shadow-graph/confirm/{finding_id}` | POST | Confirm true positive |
| `/api/ghostcrew/shadow-graph/recommendations/{vuln}` | GET | Get recommendations |

### Security Knowledge (5)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ghostcrew/knowledge/initialize` | POST | Initialize knowledge base |
| `/api/ghostcrew/knowledge/owasp/{category}` | GET | OWASP guidance |
| `/api/ghostcrew/knowledge/cwe/{cwe_id}` | GET | CWE details |
| `/api/ghostcrew/knowledge/remediation` | POST | Get remediation steps |
| `/api/ghostcrew/knowledge/search` | GET | Search knowledge |
| `/api/ghostcrew/knowledge/checklist` | GET | Security checklist |

---

## Workflow Integration

GhostCrew integrates with 6 workflows:

| Workflow | Integration Type | Use Case |
|----------|------------------|----------|
| **QUALITY_AUDIT** | Primary | Full security analysis |
| **BROWN_PAPER** | Assessment | Legacy code security review |
| **MIGRATION** | Verification | Pre/post migration security |
| **NEW_FEATURE** | Review | New code security check |
| **BUG** | Investigation | Security-related bug analysis |
| **MAINTENANCE** | Scan | Periodic security scanning |

### Integration Service

**Location:** `backend/app/services/workflow_tool_integration_service.py`

**Class:** `WorkflowGhostCrewIntegration`

**Methods:**
- `security_scan()` - Run scan with workflow context
- `security_review()` - Feature-specific security review
- `security_assessment()` - Legacy system assessment
- `capture_vulnerabilities()` - Record findings to workflow
- `get_previous_findings()` - Context from prior scans

---

## Vulnerability Patterns

Built-in detection patterns:

| Pattern | Severity | Description |
|---------|----------|-------------|
| SQL Injection | CRITICAL | SQL query construction vulnerabilities |
| XSS (Cross-Site Scripting) | HIGH | Unescaped user input in output |
| Command Injection | CRITICAL | OS command execution with user input |
| Path Traversal | HIGH | Directory traversal vulnerabilities |
| Hardcoded Secrets | HIGH | Credentials in source code |
| Insecure Deserialization | CRITICAL | Unsafe object deserialization |
| CSRF | MEDIUM | Missing CSRF protection |
| Open Redirect | MEDIUM | Unvalidated redirects |

---

## Database Models

**Location:** `backend/app/models/ghostcrew.py`

| Model | Description |
|-------|-------------|
| `GhostCrewScan` | Scan session record |
| `GhostCrewFinding` | Individual vulnerability finding |
| `ShadowGraphPattern` | Learned pattern with accuracy |
| `FalsePositiveFeedback` | User feedback on false positives |

**Migration:** `backend/alembic/versions/035_add_ghostcrew_tables.py`

---

## Usage Examples

### Start a Security Scan

```bash
curl -X POST http://localhost:8000/api/ghostcrew/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/project",
    "scan_type": "full",
    "workflow_type": "QUALITY_AUDIT"
  }'
```

### Get Security Assistance

```bash
curl -X POST http://localhost:8000/api/ghostcrew/assist \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I prevent SQL injection in Python?",
    "include_knowledge": true
  }'
```

### Get Dashboard Data

```bash
curl http://localhost:8000/api/ghostcrew/dashboard?project_id=1
```

### Mark False Positive

```bash
curl -X POST http://localhost:8000/api/ghostcrew/findings/{finding_id}/false-positive \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Test code - not production",
    "marked_by": "security_team"
  }'
```

---

## Frontend Dashboard

**Location:** `frontend/ghostcrew-dashboard.html`

Features:
- Recent scans overview
- Findings by severity chart
- Shadow Graph learning stats
- Top vulnerability patterns
- Quick scan launcher

---

## Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_ghostcrew_service.py` | 17 | Service unit tests |
| `test_ghostcrew_api.py` | 27 | API integration tests |
| `test_workflow_ghostcrew_integration.py` | 13 | Workflow integration |
| **Total** | **57** | Full coverage |

### Run Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/services/week80/ tests/api/week80/test_ghostcrew_api.py -v
```

---

## E2E Test Cases

**Location:** `e2e-tests/workflows/`

| Test Case | Description |
|-----------|-------------|
| TC201 | Quick scan workflow |
| TC202 | Full crew scan |
| TC203 | Assist mode |
| TC204 | Workflow integration |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GHOSTCREW_ENABLED` | Enable GhostCrew | `true` |
| `SHADOW_GRAPH_LEARNING` | Enable pattern learning | `true` |
| `SECURITY_KB_PATH` | Knowledge base location | `/data/security-kb` |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | Platform architecture |
| [ROADMAP.md](../../ROADMAP.md) | Week 80-82 planning |
| [kanban-system.md](./kanban-system.md) | 9-Lane Kanban integration |
| [project-workflows-standard.md](./project-workflows-standard.md) | Workflow definitions |

---

**Last Updated:** 2025-12-18
**Status:** Production Ready (Week 80-82)
