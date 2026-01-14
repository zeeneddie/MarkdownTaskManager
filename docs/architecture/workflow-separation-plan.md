# Workflow Separation Plan: Brown Paper, Migration & Quality

**Document:** Architecture Decision Record
**Status:** ✅ IMPLEMENTED (Phases 1-4 Complete)
**Created:** Week 144 (2026-01-09)
**Completed:** Week 145-146 (2026-01-13)
**Phase:** Fase 21.5

---

## Executive Summary

Dit document beschrijft de architecturale scheiding van de drie hoofdworkflows:
1. **Brown Paper** (Analysis Domain) - Code analyse en project assessment
2. **Migration** (Execution Domain) - 7-fase migratie uitvoering
3. **Quality** (Validation Domain) - Kwaliteitsvalidatie en periodieke scans

**Doel:**
- 100% scheiding tussen Brown Paper en Migration (geen directe dependencies)
- 100% aansluiting via clean AnalysisContract interface
- Onafhankelijke Quality flow met eigen scheduler

---

## Workflow Hierarchy Rule (CRITICAL)

**NEW_FEATURE is NOT a top-level workflow.** Dit is een fundamentele architectuurregel.

### Correcte Hiërarchie

```
Level 0 (Intake):     GREEN_PAPER / BROWN_PAPER
                              ↓
Level 1 (Optional):   MIGRATION (legacy modernization)
                              ↓
Level 2 (Build):      KANBAN (implementation)
                              ↓
Level 3 (Lifecycle):  MAINTENANCE
                              ↓
Level 4 (From Maint): BUG / NEW_FEATURE / MIGRATION (restart)
```

### Regels

| Regel | Beschrijving |
|-------|--------------|
| **R1** | Een project MOET starten via GREEN_PAPER (nieuw) of BROWN_PAPER (bestaand) |
| **R2** | NEW_FEATURE is ALLEEN toegankelijk vanuit MAINTENANCE |
| **R3** | BUG is ALLEEN toegankelijk vanuit MAINTENANCE |
| **R4** | MIGRATION kan op 2 plekken: na intake (Level 1) OF vanuit MAINTENANCE (restart) |
| **R5** | KANBAN is de implementatiefase, komt NA intake en VOOR maintenance |

### Waarom deze regel?

1. **Context vereist**: NEW_FEATURE heeft project context nodig (architectuur, dependencies, codebase)
2. **Kwaliteitsborging**: MAINTENANCE fase zorgt voor quality gates voordat nieuwe features worden toegevoegd
3. **Lifecycle integriteit**: Voorkomt dat features worden toegevoegd aan niet-geïmplementeerde projecten

---

## Architecture Overview

```
                              +-------------------------+
                              |  Shared Infrastructure  |
                              |  (Stability, Metrics)   |
                              +-----------+-------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
        v                                 v                                 v
+-------------------+           +-------------------+           +-------------------+
|    BROWN PAPER    |           |     MIGRATION     |           |      QUALITY      |
|  (Analysis)       |           |   (Execution)     |           |   (Validation)    |
|                   |           |                   |           |                   |
| - Code Analysis   |           | - 7-Phase Workflow|           | - Quality Gates   |
| - Domain Extract  |           | - Agent Orchestr. |           | - 42 Rules        |
| - Constitution    |           | - Deployment      |           | - Periodic Scans  |
| - Epic Generation |           |                   |           | - Multi-Scanner   |
+---------+---------+           +---------+---------+           +---------+---------+
          |                               |                               |
          |    +--------------------------+---------------------------+   |
          |    |                                                      |   |
          v    v                                                      v   v
+-----------------------------------------------------------------------------+
|                         ANALYSIS CONTRACT (Interface)                        |
|                                                                              |
|  { analysis_id, source_type, project_info, domains, modules, stability,     |
|    epic_summaries, business_rules, created_at, version }                    |
+-----------------------------------------------------------------------------+
```

---

## Huidige Koppeling (Te Verbreken)

| Locatie | Probleem |
|---------|----------|
| `StartMigrationRequest.brown_paper_session_id` | Directe dependency op Brown Paper |
| `MigrationEnhancedService._load_brown_paper_data()` | Laadt Brown Paper session direct |
| `StabilityIntegration` in `brown_paper_integration.py` | Stability zit vast aan Brown Paper |
| Quality thresholds per workflow | Embedded, niet onafhankelijk |

---

## Nieuwe Directory Structuur

```
backend/app/
+-- contracts/                           # NIEUW: Shared interfaces
|   +-- __init__.py
|   +-- analysis_contract.py             # Core decoupling interface
|   +-- quality_contract.py              # Quality gate interfaces
|   +-- stability_contract.py            # Stability interfaces
|
+-- domains/                             # NIEUW: Domain modules
|   +-- brown_paper/                     # Analysis domain
|   |   +-- api/routes.py
|   |   +-- models/
|   |   +-- services/
|   |   |   +-- analysis_service.py
|   |   |   +-- contract_adapter.py      # NIEUW: -> AnalysisContract
|   |   +-- persistence/repository.py
|   |
|   +-- migration/                       # Execution domain
|   |   +-- api/routes.py
|   |   +-- models/
|   |   +-- services/
|   |   |   +-- migration_service.py     # Refactored
|   |   |   +-- contract_consumer.py     # NIEUW: <- AnalysisContract
|   |   +-- persistence/repository.py
|   |
|   +-- quality/                         # Validation domain
|       +-- api/routes.py
|       +-- models/
|       +-- services/
|       |   +-- quality_gate_service.py
|       |   +-- scan_orchestrator.py
|       |   +-- scheduler_service.py     # Onafhankelijke scheduler
|       +-- persistence/repository.py
|
+-- infrastructure/                      # NIEUW: Shared infrastructure
    +-- stability/                       # Extracted uit services/stability
    |   +-- detector_service.py
    |   +-- detectors/
    +-- metrics/
```

---

## Key Components

### 1. Analysis Contract (De Brug)

**File:** `backend/app/contracts/analysis_contract.py`

```python
@dataclass
class AnalysisContract:
    """Interface tussen Brown Paper en Migration."""
    analysis_id: str                      # Unieke ID (NIET brown_paper_session_id)
    source_type: AnalysisSourceType       # brown_paper, green_paper, manual_import
    source_id: Optional[str]              # Originele source ID

    project: ProjectInfo
    domains: List[DomainSummary]
    modules: List[ModuleSummary]
    stability: StabilityInfo
    epics: List[EpicSummary]
    business_rules: List[BusinessRuleSummary]

    created_at: datetime
    version: str = "1.0"
```

**Source Types:**
- `BROWN_PAPER` - Van Brown Paper workflow
- `GREEN_PAPER` - Van Green Paper (BMAD) workflow
- `MANUAL_IMPORT` - Handmatige JSON/YAML import
- `EXTERNAL_TOOL` - Third-party analysis tool

### 2. Brown Paper: Contract Adapter

**File:** `backend/app/domains/brown_paper/services/contract_adapter.py`

```python
class BrownPaperContractAdapter:
    def to_contract(
        self,
        session: BrownPaperSession,
        analysis: BrownPaperAnalysis,
        stability_result: Optional[StabilityAnalysisResult]
    ) -> AnalysisContract:
        # Converteert Brown Paper output naar standaard contract
```

### 3. Migration: Contract Consumer

**File:** `backend/app/domains/migration/services/contract_consumer.py`

```python
class AnalysisContractConsumer:
    def consume(self, contract: AnalysisContract) -> MigrationContext:
        # Consumeert contract, GEEN kennis van Brown Paper

    def validate_for_migration(self, contract) -> tuple[bool, list[str]]:
        # Valideert of contract voldoende data heeft
```

### 4. Migration Request (Breaking Change)

**Oud:**
```python
class StartMigrationRequest:
    brown_paper_session_id: str  # Direct gekoppeld
```

**Nieuw:**
```python
class StartMigrationRequest:
    analysis_id: str  # Via contract, source-agnostic
```

### 5. Quality Scheduler (Onafhankelijk)

**File:** `backend/app/domains/quality/services/scheduler_service.py`

```python
class QualitySchedulerService:
    def schedule_daily_scan(project_id, hour=2)
    def schedule_weekly_scan(project_id, day='mon', hour=2)
    def schedule_interval_scan(project_id, hours=24)
    def run_immediate_scan(project_id, project_path)
```

---

## Quality Flow: 3 Execution Modes

```
+-------------------------------------------------------------------+
|                    QUALITY FLOW (3 MODI)                           |
+-------------------------------------------------------------------+
|                                                                    |
|  MODE 1: Standalone (op project_path)                              |
|  -------------------------------------                              |
|  POST /api/v2/quality/scans/run                                   |
|  Body: { project_path: "/path/to/code" }                          |
|  - Draait direct op codebase                                      |
|  - Geen Brown Paper/Migration nodig                               |
|                                                                    |
|  MODE 2: Integrated in Brown Paper                                 |
|  -------------------------------------                              |
|  - Wordt AUTOMATISCH uitgevoerd tijdens Brown Paper analysis      |
|  - Results worden meegenomen in AnalysisContract.stability        |
|  - Onderdeel van Phase 1: Code Understanding                      |
|                                                                    |
|  MODE 3: Scheduled/Audit (periodiek)                               |
|  -------------------------------------                              |
|  POST /api/v2/quality/schedules                                   |
|  - Daily/Weekly/Interval execution                                |
|  - Audit trail in quality_scan_results                            |
|  - Kan op ALLE projecten draaien                                  |
|                                                                    |
+-------------------------------------------------------------------+
```

**Integration Matrix:**

| Trigger | Input | Output |
|---------|-------|--------|
| Standalone API | project_path | QualityScanResult |
| Brown Paper | project_path (internal) | AnalysisContract.stability |
| Scheduler | project_id -> project_path | QualityScanResult + Audit |
| Migration Phase 5 | AnalysisContract | ValidationGateResult |

---

## API Endpoint Changes

### Nieuwe V2 Endpoints

| Endpoint | Beschrijving |
|----------|--------------|
| `POST /api/v2/migration/contracts/from-brown-paper` | Maakt contract van Brown Paper session |
| `POST /api/v2/migration/start` | Start migration met `analysis_id` |
| `POST /api/v2/quality/scans/run` | Run immediate quality scan |
| `POST /api/v2/quality/schedules` | Maak scheduled scan |
| `GET /api/v2/quality/schedules` | List schedules |
| `DELETE /api/v2/quality/schedules/{id}` | Verwijder schedule |
| `GET /api/v2/quality/gates/{project_id}` | Evaluate quality gate |

### Backwards Compatibility

```python
@router.post("/start/legacy", deprecated=True)
async def start_migration_legacy(request):
    """DEPRECATED: Auto-creates contract from brown_paper_session_id."""
    # 1. Create contract from brown_paper_session_id
    # 2. Call new /start endpoint with analysis_id
```

---

## Database Changes

### Nieuwe Tabellen

```sql
-- Analysis Contracts (de brug)
CREATE TABLE analysis_contracts (
    analysis_id VARCHAR(36) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    project_id VARCHAR(255),
    contract_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Schedules
CREATE TABLE quality_schedules (
    schedule_id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL,
    schedule_config JSONB NOT NULL,
    focus_areas JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT TRUE,
    next_run_at TIMESTAMP
);

-- Quality Scan Results
CREATE TABLE quality_scan_results (
    scan_id VARCHAR(36) PRIMARY KEY,
    schedule_id VARCHAR(36),
    project_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    overall_score INTEGER,
    result_data JSONB NOT NULL
);
```

### Migration Script

```sql
-- Add analysis_id to migration_sessions
ALTER TABLE migration_sessions ADD COLUMN analysis_id VARCHAR(36);

-- Later: DROP COLUMN brown_paper_session_id
```

---

## Flow Diagrams

### Nieuwe Flow: Brown Paper -> Migration

```
1. Brown Paper Analysis
   POST /api/brown-paper/sessions/{id}/analyze
                    |
                    v
2. Create Contract (NIEUW)
   POST /api/v2/migration/contracts/from-brown-paper
   Body: { brown_paper_session_id: "..." }
   Response: { analysis_id: "abc-123", ... }
                    |
                    v
3. Start Migration (GEWIJZIGD)
   POST /api/v2/migration/start
   Body: { analysis_id: "abc-123", ... }  # NIET brown_paper_session_id!
```

---

## Implementation Phases

### Phase 1: Infrastructure (Non-Breaking) ✅ COMPLETE
- [x] Create `contracts/` module met interfaces
- [x] Create `infrastructure/` module
- [x] Create `domains/` module structure

### Phase 2: Adapters (Non-Breaking) ✅ COMPLETE
- [x] Implement `BrownPaperContractAdapter`
- [x] Implement `AnalysisContractConsumer`
- [x] Create `ContractRepository`
- [x] Add `analysis_contracts` tabel (Migration 070)

### Phase 3: New APIs (Non-Breaking) ✅ COMPLETE
- [x] Add `/api/v2/migration/*` endpoints (6 endpoints)
- [x] Add `/api/v2/quality/*` endpoints (6 endpoints)
- [x] Keep oude endpoints werkend (backwards compatible)
- [x] Register routers in main.py

### Phase 4: Update Services ✅ COMPLETE
- [x] Create `QualitySchedulerService` (APScheduler integration)
- [x] Create `QualityOrchestratorService` (3 scan modes)
- [x] Run parallel met oude services

### Phase 5: Client Migration ⏳ PENDING
- [ ] Update clients naar v2 endpoints
- [ ] Add deprecation warnings
- [ ] Monitor oude endpoint usage

### Phase 6: Cleanup ⏳ PENDING
- [ ] Remove oude endpoints
- [ ] Drop `brown_paper_session_id` column
- [ ] Update alle imports

---

## Verification

### Tests
1. **Unit Tests:**
   - `test_analysis_contract.py` - Contract serialization/deserialization
   - `test_contract_adapter.py` - Brown Paper -> Contract conversion
   - `test_contract_consumer.py` - Contract -> Migration context

2. **Integration Tests:**
   - Start migration from contract (niet brown_paper_session_id)
   - Quality scan zonder Brown Paper/Migration dependency
   - Scheduled quality scan execution

3. **Manual Verification:**
   ```bash
   # 1. Run Brown Paper analysis
   curl -X POST localhost:8000/api/brown-paper/sessions/123/analyze

   # 2. Create contract
   curl -X POST localhost:8000/api/v2/migration/contracts/from-brown-paper \
     -d '{"brown_paper_session_id": "123"}'
   # Returns: {"analysis_id": "abc-123", ...}

   # 3. Start migration with contract
   curl -X POST localhost:8000/api/v2/migration/start \
     -d '{"analysis_id": "abc-123"}'

   # 4. Schedule quality scan (independent)
   curl -X POST localhost:8000/api/v2/quality/schedules \
     -d '{"project_id": "proj-1", "schedule_type": "daily"}'
   ```

---

## Critical Files

| File | Purpose |
|------|---------|
| `contracts/analysis_contract.py` | Core interface die dependency breekt |
| `domains/brown_paper/services/contract_adapter.py` | Brown Paper -> Contract |
| `domains/migration/services/contract_consumer.py` | Contract -> Migration |
| `domains/migration/services/migration_service.py` | Refactored service |
| `domains/quality/services/scheduler_service.py` | Onafhankelijke scheduler |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [brown-paper-enhanced.md](brown-paper-enhanced.md) | Brown Paper 6-phase workflow |
| [migration-enhanced.md](migration-enhanced.md) | Migration 7-phase workflow |
| [quality-gates.md](quality-gates.md) | Quality gate configuration |
| [docs/workflows/](../workflows/) | Workflow documentation |

---

*Generated: Week 144 (2026-01-09)*
*Updated: Week 145-146 (2026-01-13) - Phases 1-3 Complete*
