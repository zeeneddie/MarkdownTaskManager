# Fase 21.5: Workflow Separation (Week 145-146)

**Goal:** 100% scheiding Brown Paper/Migration/Quality met clean AnalysisContract interface
**Specification:** [docs/architecture/workflow-separation-plan.md](../../architecture/workflow-separation-plan.md)
**Status:** APPROVED - Ready for implementation
**Priority:** HIGH

---

## Problem Statement

De huidige architectuur heeft tight coupling tussen Brown Paper en Migration:
- `StartMigrationRequest.brown_paper_session_id` - Directe dependency
- `MigrationEnhancedService._load_brown_paper_data()` - Laadt Brown Paper direct
- Stability is embedded in Brown Paper, niet herbruikbaar
- Quality kan niet onafhankelijk draaien

---

## Solution: Domain Separation via Contracts

```
+-------------------+     +-------------------+     +-------------------+
|    BROWN PAPER    |     |     MIGRATION     |     |      QUALITY      |
|  (Analysis)       |     |   (Execution)     |     |   (Validation)    |
+--------+----------+     +--------+----------+     +--------+----------+
         |                         |                         |
         v                         v                         v
+-----------------------------------------------------------------------+
|                       ANALYSIS CONTRACT                                |
| { analysis_id, source_type, project_info, domains, modules,           |
|   stability_info, epic_summaries, business_rules }                    |
+-----------------------------------------------------------------------+
```

---

## Week 145 Deliverables

| Task | Hours | Output |
|------|-------|--------|
| `contracts/` module | 6 | AnalysisContract, QualityContract, StabilityContract |
| `infrastructure/` module | 4 | Stability extracted to shared |
| `BrownPaperContractAdapter` | 4 | Brown Paper -> AnalysisContract |
| `AnalysisContractConsumer` | 4 | AnalysisContract -> MigrationContext |
| `ContractRepository` | 4 | Database persistence |
| Database migration | 2 | analysis_contracts table |
| Unit tests | 6 | 30+ tests |
| **Total** | **30** | |

---

## Week 146 Deliverables

| Task | Hours | Output |
|------|-------|--------|
| `/api/v2/migration/*` endpoints | 6 | New decoupled API |
| `/api/v2/quality/*` endpoints | 4 | Independent quality API |
| `QualitySchedulerService` | 4 | Daily/weekly/interval schedules |
| `QualityOrchestratorService` | 4 | 3 execution modes |
| Legacy endpoint wrapper | 2 | Backwards compatibility |
| Integration tests | 6 | E2E workflow tests |
| Documentation | 4 | API docs, user guide |
| **Total** | **30** | |

---

## API Changes

### New V2 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/migration/contracts/from-brown-paper` | POST | Create contract from Brown Paper |
| `/api/v2/migration/start` | POST | Start migration with `analysis_id` |
| `/api/v2/quality/scans/run` | POST | Run immediate quality scan |
| `/api/v2/quality/schedules` | POST/GET/DELETE | Manage scheduled scans |
| `/api/v2/quality/gates/{project_id}` | GET | Evaluate quality gate |

### Deprecated Endpoints

| Endpoint | Replacement |
|----------|-------------|
| `POST /api/migration/start` (with brown_paper_session_id) | `/api/v2/migration/start` (with analysis_id) |

---

## Quality Flow: 3 Execution Modes

| Mode | Trigger | Input | Output |
|------|---------|-------|--------|
| **Standalone** | API call | project_path | QualityScanResult |
| **Integrated** | Brown Paper | internal | AnalysisContract.stability |
| **Scheduled** | Scheduler | project_id | QualityScanResult + Audit |

---

## Database Schema

```sql
CREATE TABLE analysis_contracts (
    analysis_id VARCHAR(36) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    project_id VARCHAR(255),
    contract_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quality_schedules (
    schedule_id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL,
    schedule_config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    next_run_at TIMESTAMP
);
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Brown Paper/Migration coupling | 0 direct dependencies |
| Quality independent execution | 100% standalone capability |
| Backwards compatibility | 100% existing clients work |
| New API coverage | All core workflows via v2 |
| Test coverage | 90%+ for new code |

---

## Total Effort: 60 hours (2 weeks)

---

← [Back to Overview](../phases-planned.md)
