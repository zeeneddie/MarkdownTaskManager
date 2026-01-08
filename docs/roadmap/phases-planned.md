# Planned Phases (Fase 22+)

**Project:** MarQed AI Agent Software Platform
**Period:** Week 144+ (2026-01-XX onwards)
**Last Updated:** 2026-01-08

---

## Quick Navigation

| Document | Content |
|----------|---------|
| [ROADMAP.md](../../ROADMAP.md) | Executive summary |
| [phases-completed.md](phases-completed.md) | Completed phases (Fase 1-21) |
| [phases-current.md](phases-current.md) | Current work (Week 143) |
| **This file** | Planned work (Fase 22+) |

---

## Fase 20: Brown Paper Enhanced (Week 128-129) COMPLETE

**Goal:** Integration of all available deep analysis services in BrownPaperService for complete legacy code analysis.
**Specification:** [docs/architecture/brown-paper-enhanced.md](../architecture/brown-paper-enhanced.md)
**Status:** COMPLETE
**Origin:** Week 125 HCI-CRS Afspraak module analysis

### Problem Statement

BrownPaperService has its own simple regex-based analysis while 5 rich analysis services were developed in parallel:

```
BrownPaperService (CURRENT):
├── application_registry_service  ✅ (metadata)
├── brown_paper_estimation_service ✅ (FP/SP)
└── OWN regex analysis            ⚠️ (duplication)

AVAILABLE BUT NOT USED:
├── CodeAnalysisAggregatorService ❌ (complexity, coupling, cohesion)
├── DeepExtractionService         ❌ (multi-LLM council, INVEST)
├── HierarchicalStoryExtractionService ❌ (multi-level, CiRA)
├── LayeredAnalysisService        ❌ (VBScript, SWOT, stored procs)
└── DependencyGraphService        ❌ (graph structure, circular deps)
```

### 6-Phase Enhanced Workflow

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    BROWN PAPER ENHANCED WORKFLOW                                │
│                                                                                 │
│  PHASE 1: CODE UNDERSTANDING                                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┐                       │
│  │ DependencyGraph │ CodeAnalysis    │ LayeredAnalysis │                       │
│  │ Service         │ Aggregator      │ Service         │                       │
│  ├─────────────────┼─────────────────┼─────────────────┤                       │
│  │ • Graph struct  │ • Complexity    │ • VBScript      │                       │
│  │ • Circular deps │ • Coupling      │ • Stored procs  │                       │
│  │ • Fan-in/out    │ • Cohesion      │ • ASP patterns  │                       │
│  └─────────────────┴─────────────────┴─────────────────┘                       │
│                             │                                                   │
│  PHASE 2: DOMAIN EXTRACTION │ Agent: Peter (Product Owner)                      │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ • Identify business domains from code patterns           │                  │
│  │ • Map to CAFCR categories                                │                  │
│  │ • Determine module boundaries                            │                  │
│  │ • Extract business rules (hybrid extractors)             │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 3: HIERARCHICAL EXTRACTION │ Agent: Felix (Architect)                   │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ HierarchicalStoryExtractionService:                      │                  │
│  │ • System-level → Epic                                    │                  │
│  │ • Module-level → Feature                                 │                  │
│  │ • Class-level → User Story                               │                  │
│  │ • Function-level → Task                                  │                  │
│  │ • CiRA causality relations                               │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 4: DEEP EXTRACTION   │ Agent: Quinn (Quality) + LLM Council             │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ DeepExtractionService:                                   │                  │
│  │ • Multi-tier LLM analysis (tier-aware)                   │                  │
│  │ • INVEST validation per story                            │                  │
│  │ • Conflict detection across extractors                   │                  │
│  │ • Confidence scoring                                     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 5: ESTIMATION        │ Agent: Eliza (Estimation)                        │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ brown_paper_estimation_service (existing):               │                  │
│  │ • Function Points (IFPUG)                                │                  │
│  │ • Story Points                                           │                  │
│  │ • Effort estimation                                      │                  │
│  │ • Risk assessment (enhanced with complexity metrics)     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 6: OUTPUT            │ Agent: Diana (Documentation)                     │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ Consolidated Output:                                     │                  │
│  │ • Dependency graph visualization data                    │                  │
│  │ • Epic/Feature/Story hierarchy                           │                  │
│  │ • Traceability matrix                                    │                  │
│  │ • Migration roadmap                                      │                  │
│  │ • Risk register                                          │                  │
│  │ • Estimation breakdown                                   │                  │
│  └──────────────────────────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Assignments

| Phase | Primary Agent | Supporting Agents | Output |
|-------|---------------|-------------------|--------|
| **1. Code Understanding** | Miguel | Quinn | Metrics, graphs, patterns |
| **2. Domain Extraction** | Peter | Miguel | Business domains, CAFCR mapping |
| **3. Hierarchical Extraction** | Felix | Peter | Epic/Feature/Story/Task |
| **4. Deep Extraction** | Quinn | LLM Council | Validated, conflict-free backlog |
| **5. Estimation** | Eliza | Paul | FP, SP, effort, risk |
| **6. Output** | Diana | All | Consolidated documentation |

### Tier-Aware Analysis

| Tier | Services Used | Confidence Target |
|------|---------------|-------------------|
| **FREE** | DependencyGraph + CodeAnalysis (Ollama) | 60% |
| **BASIC** | + LayeredAnalysis (Groq, Qwen) | 70% |
| **STANDARD** | + HierarchicalExtraction (Gemini) | 80% |
| **PROFESSIONAL** | + DeepExtraction (GPT-5.2) | 90% |
| **PREMIUM** | + Human Review + Opus synthesis | 95% |

### Week 128 Deliverables

| Component | Location | Description |
|-----------|----------|-------------|
| **BrownPaperService refactor** | `brown_paper_service.py` | Add service imports, orchestration |
| **Phase 1 Integration** | `brown_paper_service.py` | DependencyGraph + CodeAnalysis calls |
| **Phase 2-3 Integration** | `brown_paper_service.py` | Hierarchical extraction calls |
| **Unit Tests** | `tests/services/week128/` | 30+ tests |

### Week 129 Deliverables

| Component | Location | Description |
|-----------|----------|-------------|
| **Phase 4 Integration** | `brown_paper_service.py` | DeepExtraction + LLM Council |
| **Phase 5-6 Integration** | `brown_paper_service.py` | Estimation enhancement, output consolidation |
| **API Updates** | `brown_paper.py` | New endpoints for enhanced analysis |
| **Dashboard Updates** | `frontend/` | Visualization for enhanced output |
| **Integration Tests** | `tests/services/week129/` | E2E workflow tests |

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/brown-paper/bmad/{id}/enhanced-analyze` | POST | Full 6-phase analysis |
| `/api/brown-paper/bmad/{id}/dependency-graph` | GET | Graph visualization data |
| `/api/brown-paper/bmad/{id}/hierarchy` | GET | Epic/Feature/Story tree |
| `/api/brown-paper/bmad/{id}/conflicts` | GET | Detected conflicts |
| `/api/brown-paper/bmad/{id}/metrics` | GET | Code quality metrics |

### Success Criteria

| Criterion | Target |
|-----------|--------|
| **Service Integration** | 5 services connected |
| **Agent Coverage** | 6 agents in workflow |
| **Confidence Increase** | +20% vs current |
| **New Endpoints** | 5 new API endpoints |
| **Tests** | 60+ unit/integration tests |

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 18 (CiRA) | COMPLETE | CiRA relations in hierarchical extraction |
| Fase 19 (Metrics) | COMPLETE | 5 HCI metrics analyzers with 5-star ratings |
| DeepExtractionService | EXISTS | Ready for integration |
| HierarchicalStoryExtractionService | EXISTS | Ready for integration |

---

## Fase 21: ASP Application Stability Analyzer Framework (Week 143-146) COMPLETE

**Goal:** Comprehensive stability analysis covering ALL crash causes, not just ADO leaks.
**Specification:**
- [docs/architecture/asp-stability-analyzer-framework.md](../architecture/asp-stability-analyzer-framework.md)
- [docs/architecture/resource-leak-detection-framework.md](../architecture/resource-leak-detection-framework.md)
**Status:** COMPLETE (Week 143 - Core Framework)
**Origin:** Week 142 FysioOne-Classic Stability Analysis (Codex + Claude Review)

### Week 143 Deliverables (COMPLETE)

| Component | Status | Description |
|-----------|--------|-------------|
| Core Framework | DONE | types.py, base_detector.py, detector_service.py |
| ClassicASPLeakDetector | DONE | ADO Connection/Recordset detection |
| ClassicASPCOMDetector | DONE | XMLHTTP, ABCpdf, XMLDOM detection |
| ClassicASPFileDetector | DONE | FSO, TextStream detection |
| API Endpoints | DONE | 8 REST endpoints in stability.py |
| Database Migration | DONE | Migration 069 - 4 tables |
| Unit Tests | DONE | 25/25 passed |
| Integration Tests | DONE | 9 passed, 6 skipped |

### ⚠️ Peer Review Learnings (FysioOne Audit 2026-01-06)

**Kritieke bevindingen uit 2-ronde LLM peer review:**

| Issue | Problem | Solution |
|-------|---------|----------|
| **Case Sensitivity** | VBScript is case-insensitive, grep missed `rs.close()` | Use `(?i)` flag or `grep -i` always |
| **Set ≠ Close** | `Set obj = Nothing` does NOT release connection! | Require `.Close()` before `Set = Nothing` |
| **Reopen Pattern** | RS.Open → RS.Close → RS.Open (no 2nd close) | Track state machine: CREATED→CLOSED→REOPENED |
| **Connection Priority** | Connection leaks = pool exhaustion = CRASH | Connection > Recordset in severity |
| **Peer Review Essential** | Initial audit accuracy was 40%, post-review 98% | Built-in dual-LLM verification |

**Structural Fix Approach:**
1. **SafeEnd/SafeRedirect helpers** - Global include for all exit points
2. **CleanupAllResources pattern** - Standard template per file
3. **CI/CD Quality Gates** - Block CRITICAL leaks on PR
4. **Monitoring Dashboard** - Track regression over time

See: [resource-leak-detection-framework.md](../architecture/resource-leak-detection-framework.md#11-lessons-learned-from-peer-review-fysioone-audit-2026-01-06)

### Expanded Scope (8 Detection Categories)

| # | Category | Detectors | Risk Level |
|---|----------|-----------|------------|
| 1 | **ADO Connection/Recordset Leaks** | CreateRecordset, CreateCusCon, .Close() | CRITICAL |
| 2 | **COM Object Leaks** | XMLHTTP, ABCpdf, XMLDOM, Custom COM | HIGH |
| 3 | **External Service Risks** | Timeout, Retry, Error Handling | HIGH |
| 4 | **Memory Intensive Operations** | PDF Gen, Large Arrays, String Concat | MEDIUM |
| 5 | **File Handle Leaks** | FileSystemObject, TextStream | MEDIUM |
| 6 | **Session State Issues** | Large Objects, Timeout | LOW |
| 7 | **Exception Handling** | On Error Resume Next analysis | MEDIUM |
| 8 | **SQL Performance** | N+1, Deadlocks, Blocking | MEDIUM |

### FysioOne Findings Summary

| Category | Found Issues | Daily Impact |
|----------|--------------|--------------|
| ADO Leaks | 1700+ daily leaks | Connection pool exhaustion |
| COM Objects | 148 CreateObject calls | Memory exhaustion |
| XMLHTTP | 30+ external calls | Thread blocking |
| PDF Generation | 10+ instances | Memory spikes |
| File Operations | 39 in 17 files | Handle exhaustion |

### Problem Statement

Classic ASP codebase (FysioOne) showed severe stability issues:
- **6,541 ADO object creations** across 1,861 files
- **47% of files** have potential leaks (opens > closes)
- Loop leaks cause **1000+ connection leaks per batch operation**
- No automated detection in MarQed platform

### Architecture

```
                    ┌─────────────────────────────┐
                    │  ResourceLeakDetectorService │
                    │  (Orchestrator)              │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  BaseResourceLeakDetector   │
                    │  (Abstract Base Class)      │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────┬───────────┬───┴───┬───────────┬──────────┐
        ▼          ▼           ▼       ▼           ▼          ▼
   ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ClassicASP│ │  PHP   │ │ Java   │ │ VB.NET │ │  C#    │ │ Python │
   │Detector │ │Detector│ │Detector│ │Detector│ │Detector│ │Detector│
   └─────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### Generic Resource Types

| Type | Description | Languages |
|------|-------------|-----------|
| `DATABASE_CONNECTION` | DB connections | All |
| `RECORDSET` | Query results, cursors | ASP, PHP, Java, .NET |
| `FILE_HANDLE` | File I/O | All |
| `HTTP_CONNECTION` | HTTP/REST clients | All |
| `COM_OBJECT` | COM/ActiveX objects | ASP, VB |
| `STREAM` | Data streams | Java, .NET, Python |

### Generic Leak Patterns

| Pattern | Description | Severity |
|---------|-------------|----------|
| `NEVER_CLOSED` | Created but never released | HIGH |
| `LOOP_LEAK` | Created in loop without per-iteration cleanup | **CRITICAL++** |
| `FUNCTION_LEAK` | Created in function without cleanup before return | HIGH |
| `EARLY_EXIT_LEAK` | Orphaned by Response.End, return, throw | MEDIUM |
| `CONDITIONAL_LEAK` | Condition prevents closure | MEDIUM |
| `REOPEN_LEAK` ⚠️ | Open→Close→Open without final close (new!) | **HIGH** |
| `SET_WITHOUT_CLOSE` ⚠️ | Only `Set = Nothing` without `.Close()` | **HIGH** |

### Language-Specific Patterns

#### Classic ASP (Priority - FysioOne)
```vbscript
' OPEN patterns:
Set con = CreateCusCon()
Set rs = CreateRecordset()
Set obj = Server.CreateObject("ADODB.Connection")

' CLOSE patterns:
con.Close()
Call TryCloseConnection(con)
Set obj = Nothing
```

#### PHP (FRM Project)
```php
// OPEN patterns:
$conn = mysqli_connect(...)
$result = mysqli_query(...)
$file = fopen(...)

// CLOSE patterns:
mysqli_close($conn)
mysqli_free_result($result)
fclose($file)
```

#### Java
```java
// OPEN patterns:
Connection con = DriverManager.getConnection(...)
ResultSet rs = stmt.executeQuery(...)

// CLOSE patterns:
con.close()
// OR: try-with-resources (auto-close)
```

#### C#/VB.NET
```csharp
// OPEN patterns:
SqlConnection con = new SqlConnection(...)
con.Open()

// CLOSE patterns:
con.Close()
con.Dispose()
// OR: using block (auto-dispose)
```

### Week 143: Core Framework + ADO/COM Detectors

| Task | Hours | Output |
|------|-------|--------|
| `ASPStabilityAnalyzerService` orchestrator | 4 | Main service |
| `BaseResourceLeakDetector` abstract class | 4 | Core framework |
| `ADOLeakDetector` (Cat 1) with wrapper analysis | 8 | ADO support |
| `COMObjectLeakDetector` (Cat 2) | 6 | XMLHTTP, PDF, XMLDOM |
| API endpoints `/api/stability/*` | 4 | REST API |
| Database migration (stability tables) | 2 | Tables |
| Unit tests | 6 | 30+ tests |
| **Total** | **34** | |

### Week 144: Service & Memory Detectors

| Task | Hours | Output |
|------|-------|--------|
| `ExternalServiceAnalyzer` (Cat 3) | 6 | Timeout, retry analysis |
| `MemoryAnalyzer` (Cat 4) | 6 | PDF gen, arrays, strings |
| `FileHandleDetector` (Cat 5) | 4 | FSO, TextStream |
| `SessionAnalyzer` (Cat 6) | 4 | Size, timeout issues |
| Include file resolver | 4 | Cross-file analysis |
| Unit tests | 6 | 40+ tests |
| **Total** | **30** | |

### Week 145: Exception & SQL + Additional Languages

| Task | Hours | Output |
|------|-------|--------|
| `ExceptionAnalyzer` (Cat 7) | 6 | On Error patterns |
| `SQLAnalyzer` (Cat 8) | 6 | N+1, deadlock detection |
| `PHPLeakDetector` | 4 | PHP support |
| `DotNetLeakDetector` | 4 | C#/VB.NET support |
| Multi-language wrapper analysis | 4 | Unified approach |
| Unit tests | 6 | 40+ tests |
| **Total** | **30** | |

### Week 146: Integration & Dashboard

| Task | Hours | Output |
|------|-------|--------|
| Brown Paper integration | 4 | Stability phase in BMAD |
| Quality Gate integration | 4 | Block on CRITICAL |
| Technical Debt auto-linkage | 4 | Auto-create debt items |
| GhostCrew security integration | 2 | DoS vulnerability scan |
| Stability Dashboard | 8 | `stability-dashboard.html` |
| E2E tests | 6 | 20+ tests |
| Documentation | 2 | User guide |
| **Total** | **30** | |

### Total Effort: 124 hours (4 weeks)

### Success Metrics

| Metric | Target |
|--------|--------|
| Detection accuracy | >90% per category |
| False positive rate | <5% |
| Analysis speed | <2s per file |
| Categories covered | 8 stability categories |
| Language coverage | 4 languages (ASP, PHP, VB.NET, Java) |
| Fix suggestion accuracy | >80% |

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stability/analyze` | POST | Full 8-category stability analysis |
| `/api/stability/report/{project_id}` | GET | Get stability report |
| `/api/stability/categories` | GET | List available categories |
| `/api/stability/findings/{project_id}` | GET | Individual findings |
| `/api/stability/findings/{project_id}/category/{cat}` | GET | Findings by category |
| `/api/stability/fix-suggestions/{finding_id}` | GET | AI-generated fix suggestions |
| `/api/stability/metrics/{project_id}` | GET | Stability score over time |

### Database Schema

```sql
CREATE TABLE stability_scans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    scan_date TIMESTAMP DEFAULT NOW(),
    total_files INTEGER,
    categories_analyzed TEXT[],  -- ['ado_leaks', 'com_objects', ...]
    overall_risk VARCHAR(20),    -- CRITICAL, HIGH, MEDIUM, LOW
    overall_score INTEGER        -- 0-100
);

CREATE TABLE stability_findings (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES stability_scans(id),
    category VARCHAR(50),        -- ado_leaks, com_objects, external_services, etc.
    file_path TEXT,
    line_number INTEGER,
    finding_type VARCHAR(100),   -- LOOP_LEAK, NO_TIMEOUT, PDF_NO_CLEAR, etc.
    severity VARCHAR(20),
    description TEXT,
    suggested_fix TEXT,
    fixed_at TIMESTAMP,
    fixed_by INTEGER REFERENCES users(id)
);

CREATE TABLE stability_metrics (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    metric_date DATE,
    ado_leak_count INTEGER,
    com_leak_count INTEGER,
    external_service_issues INTEGER,
    memory_issues INTEGER,
    file_leak_count INTEGER,
    session_issues INTEGER,
    exception_issues INTEGER,
    sql_issues INTEGER,
    overall_score INTEGER        -- 0-100
);
```

### Integration Points

| System | Integration | Benefit |
|--------|-------------|---------|
| **Brown Paper** | Phase 1 analysis | Stability assessment |
| **Quality Gates** | Deployment blocker | Prevent leaky releases |
| **Technical Debt** | Auto-create items | Track fixes |
| **GhostCrew** | DoS detection | Security perspective |
| **Dashboards** | Visualization | Monitoring |

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 20 (Brown Paper Enhanced) | PLANNED | Integration target |
| `ClassicASPExtractor` | EXISTS | Pattern reference |
| GhostCrew | COMPLETE | Security integration |

---

## Fase 22: FP Methodology Overhaul (Week 146-147) 🚨 CRITICAL

**Goal:** Fix fundamental IFPUG/NESMA methodology violations in Function Point calculation module
**Status:** PLANNED - HIGH PRIORITY
**Origin:** FysioOne ADO Leak Audit review (2026-01-06) - External expert feedback
**Risk:** Current implementation would fail NESMA/IFPUG certification review

### Problem Statement

The current `brown_paper_estimation_service.py` and `estimation/function_points.py` modules contain **serious methodological errors** that make FP calculations indefensible:

```
CURRENT STATE (BROKEN):
├── EIF misuse: Counting source files as EIF         ❌ -17 FP overcounting
├── ILF misuse: Counting code patterns as ILF        ❌ -14 FP overcounting
├── VAF usage: Still applied despite CPM 4.3.1      ⚠️  Not recommended
├── Double counting: Fixes AND output counted        ❌ -5 FP overcounting
├── No maintenance FP: Using development counting    ❌ Wrong methodology
└── Productivity anomaly: 3.8 FP/hour vs 0.5-1.5    🚩 Red flag
```

### Methodology Violations (Expert Feedback)

| Issue | Current Implementation | IFPUG/NESMA Standard | Impact |
|-------|----------------------|----------------------|--------|
| **EIF for source files** | ASP files counted as EIF (10+7 FP) | EIF = external DATA maintained by other systems | -17 FP |
| **ILF for code patterns** | Helper functions as ILF (7+7 FP) | ILF = logical DATA groups within boundary | -14 FP |
| **VAF still applied** | VAF 1.04-1.09 multiplier | CPM 4.3.1: Report UFP only, VAF in appendix | Complexity |
| **Double counting** | "Modified files" EO + fixes EI | One transaction = one count | -5 FP |
| **Missing maintenance FP** | Development counting for fixes | Enhancement FP = ADD + CHNG + DEL | Wrong method |

### Root Cause Analysis

```python
# WRONG - Current implementation
eifs=[
    ComponentInput(name="ASP Source Files", dets=50, rets=10),  # NOT an EIF!
],
ilfs=[
    ComponentInput(name="CleanupResources() Helper", dets=8, rets=1),  # NOT an ILF!
],

# RIGHT - What should be counted
# Analysis work has NO FP - it's not software development
# Maintenance fixes use Enhancement FP counting:
# - ADD: New functions added
# - CHNG: Functions modified
# - DEL: Functions deleted
```

### Solution Architecture

#### Phase 1: Core FP Methodology Fix (Week 146)

**1.1 Component Type Validation**
```python
class FPComponentValidator:
    """Validate components against IFPUG CPM 4.3.1 rules."""

    @staticmethod
    def validate_ilf(component: ComponentInput) -> ValidationResult:
        """
        ILF Rules (CPM 4.3.1):
        1. Must be user-identifiable group of logically related data
        2. Must reside entirely within application boundary
        3. Must be maintained through External Inputs

        NOT an ILF:
        - Code patterns, helper functions, templates
        - Configuration files (unless user-maintained)
        - Source code being analyzed
        """
        errors = []
        if is_code_pattern(component):
            errors.append("Code patterns are not ILFs")
        if is_external_data(component):
            errors.append("External data should be EIF, not ILF")
        return ValidationResult(valid=len(errors)==0, errors=errors)

    @staticmethod
    def validate_eif(component: ComponentInput) -> ValidationResult:
        """
        EIF Rules (CPM 4.3.1):
        1. Must be user-identifiable group of logically related data
        2. Must reside entirely OUTSIDE application boundary
        3. Referenced for read-only purposes
        4. Maintained by another application

        NOT an EIF:
        - Source code being analyzed (that's input to YOUR process)
        - Configuration files you maintain
        - Data you can modify
        """
        errors = []
        if is_source_code(component):
            errors.append("Source code is not an EIF")
        if is_internally_maintained(component):
            errors.append("Internally maintained data is ILF, not EIF")
        return ValidationResult(valid=len(errors)==0, errors=errors)
```

**1.2 Maintenance FP Counting (Enhancement Projects)**
```python
class EnhancementFPCalculator:
    """
    IFPUG Enhancement FP counting for maintenance/bug fix work.

    Formula: EFP = (ADD + CHNG + CFP + DEL) × VAF

    Where:
    - ADD: FP of functions ADDED
    - CHNG: FP of functions CHANGED (count AFTER change)
    - CFP: FP of conversion functions (one-time data migration)
    - DEL: FP of functions DELETED (40% of original FP)
    """

    def calculate_enhancement_fp(
        self,
        added: List[ComponentInput],
        changed: List[ComponentInput],
        deleted: List[ComponentInput],
    ) -> EnhancementFPResult:
        add_fp = sum(self._calculate_component(c) for c in added)
        chng_fp = sum(self._calculate_component(c) for c in changed)
        del_fp = sum(self._calculate_component(c) * 0.4 for c in deleted)  # 40% rule

        return EnhancementFPResult(
            add_fp=add_fp,
            chng_fp=chng_fp,
            del_fp=del_fp,
            total_efp=add_fp + chng_fp + del_fp,
            methodology="IFPUG CPM 4.3.1 Enhancement Counting"
        )
```

**1.3 VAF Deprecation**
```python
class FunctionPointRequest(BaseModel):
    # ... existing fields ...

    use_vaf: bool = Field(
        False,
        description="DEPRECATED: CPM 4.3.1 recommends UFP only. VAF moved to appendix.",
        deprecated=True
    )

    @model_validator(mode='after')
    def warn_vaf_usage(self):
        if self.use_vaf:
            logger.warning(
                "VAF usage deprecated since IFPUG CPM 4.3.1 (2010). "
                "Consider reporting UFP only for NESMA/IFPUG compliance."
            )
        return self
```

#### Phase 2: Analysis vs Development Distinction (Week 146)

**Key Insight:** The audit work we did has **NO Function Points** in IFPUG terms.

```python
class WorkTypeClassifier:
    """Classify work to determine appropriate estimation method."""

    WORK_TYPES = {
        "analysis": {
            "description": "Code review, audit, documentation",
            "fp_applicable": False,
            "recommended_method": "time_and_materials",
            "examples": ["ADO leak audit", "Security review", "Architecture assessment"]
        },
        "development": {
            "description": "New software creation",
            "fp_applicable": True,
            "recommended_method": "development_fp",
            "examples": ["New feature", "New module", "Greenfield project"]
        },
        "enhancement": {
            "description": "Changes to existing software",
            "fp_applicable": True,
            "recommended_method": "enhancement_fp",
            "examples": ["Bug fixes", "Performance improvements", "Refactoring"]
        },
        "maintenance": {
            "description": "Keeping software operational",
            "fp_applicable": False,
            "recommended_method": "support_hours",
            "examples": ["Monitoring", "Patching", "User support"]
        }
    }

    def classify(self, work_description: str) -> WorkType:
        """Classify work and recommend estimation method."""
        # LLM-based classification with validation
        pass
```

#### Phase 3: Corrected FysioOne Calculation (Week 147)

**Correct Estimation for FysioOne ADO Fixes:**

```python
# ANALYSIS WORK - No FP (time & materials)
analysis_estimate = TimeAndMaterialsEstimate(
    description="ADO Leak Audit + Documentation",
    hours_spent=8,
    deliverables=["Audit reports", "Peer review docs", "Framework updates"],
    fp_count=0,  # Analysis has no FP!
    estimation_method="actual_hours"
)

# FIX WORK - Enhancement FP
fix_estimate = EnhancementFPCalculator().calculate_enhancement_fp(
    added=[
        # NEW functions added
        ComponentInput(name="CleanupResources()", dets=4, ftrs=1),  # EI: 3 FP
        ComponentInput(name="SafeEnd()", dets=3, ftrs=1),           # EI: 3 FP
    ],
    changed=[
        # MODIFIED functions (count AFTER change)
        ComponentInput(name="Declaratie_verzenden loop", dets=5, ftrs=1),  # EI: 3 FP
        ComponentInput(name="groep_info cleanup", dets=4, ftrs=1),          # EI: 3 FP
        ComponentInput(name="Persoon_Update cleanup", dets=4, ftrs=1),      # EI: 3 FP
        # ... more changed functions
    ],
    deleted=[]  # No functions deleted
)

# CORRECT RESULT:
# Analysis: 0 FP (8 hours actual)
# Fixes: ~15-20 EFP (Enhancement FP)
# Total: ~15-20 FP (not 122!)
```

### Validation Criteria

| Criterion | Test | Expected |
|-----------|------|----------|
| **NESMA Review** | External certified reviewer validates | Pass |
| **Productivity Check** | FP/hour within 0.5-1.5 range | Pass |
| **No EIF for source** | Source files rejected as EIF | Error thrown |
| **No ILF for code** | Code patterns rejected as ILF | Error thrown |
| **VAF warning** | Using VAF shows deprecation warning | Warning logged |
| **Work type routing** | Analysis work → T&M, not FP | Correct routing |

### API Changes

```python
# NEW ENDPOINTS

@router.post("/estimate/work-type")
async def classify_work_type(description: str) -> WorkTypeClassification:
    """Classify work and recommend estimation method."""

@router.post("/estimate/enhancement")
async def calculate_enhancement_fp(request: EnhancementFPRequest) -> EnhancementFPResponse:
    """Calculate Enhancement FP for maintenance/fix work."""

@router.post("/estimate/validate")
async def validate_fp_components(request: FPValidationRequest) -> FPValidationResponse:
    """Validate FP components against IFPUG CPM 4.3.1 rules."""

# MODIFIED ENDPOINTS

@router.post("/analyze")  # Existing
async def analyze_directory(request: AnalyzeRequest) -> AnalysisResponse:
    """
    Analyze directory for FP estimation.

    CHANGED: Now includes validation warnings for methodology issues.
    CHANGED: Separates development FP from enhancement FP.
    CHANGED: VAF disabled by default with deprecation notice.
    """
```

### Deliverables

| Week | Deliverable | Hours |
|------|-------------|-------|
| 146 | Component type validators (ILF/EIF/EI/EO/EQ rules) | 8 |
| 146 | Enhancement FP calculator | 6 |
| 146 | VAF deprecation + warnings | 2 |
| 146 | Work type classifier | 4 |
| 147 | API endpoint updates | 4 |
| 147 | FysioOne recalculation example | 2 |
| 147 | NESMA/IFPUG compliance documentation | 4 |
| 147 | Unit tests for all validators | 6 |
| **Total** | | **36 hours** |

### Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| NESMA/IFPUG compliance | 40% | 95%+ | Certification-ready |
| False FP (overcounting) | ~36 FP | 0 FP | Zero methodology errors |
| Productivity ratio | 3.8 FP/hr | 0.8 FP/hr | Within normal range |
| User confidence | Low | High | Defensible estimates |

### References

| Source | Usage |
|--------|-------|
| IFPUG CPM 4.3.1 (2010) | Primary methodology reference |
| NESMA Guidelines | Dutch/EU compliance |
| ISO/IEC 20926:2003 | International standard |
| [FysioOne Audit](../../opt/projecten/paramedi/FYSIOONE_AUDIT_RESULTS.md) | Case study for validation |

---

## Fase 23: Context Engineering & Reference-on-Demand (Week 147-148)

**Goal:** Implement PIV Loop (Plan-Implement-Validate) with intelligent reference loading and quality gates
**Specification:** [docs/architecture/context-engineering-architecture.md](../architecture/context-engineering-architecture.md)
**Status:** PLANNED
**Origin:** Cole Medin's Top 1% Agentic Engineering analysis (2026-01-08)
**Reference Structure:** [.claude/reference/](.claude/reference/) + [.claude/examples/](.claude/examples/)

### Problem Statement

Current agent workflows load full context regardless of task needs:
- Token waste on irrelevant references
- No quality gates on agent output
- No automatic iteration when quality is insufficient
- Manual review required for all outputs

### Solution: PIV Loop with Quality Gates

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        PIV LOOP ARCHITECTURE                                  │
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │   ROUTER    │───▶│  REFERENCE  │───▶│   AGENT     │───▶│   QUALITY   │  │
│   │   SERVICE   │    │  SELECTOR   │    │  EXECUTOR   │    │    GATE     │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │           │
│         ▼                  ▼                  ▼                  ▼           │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │ Task        │    │ Semantic    │    │ PIV Loop    │    │ Threshold   │  │
│   │ Classifier  │    │ Matching    │    │ Iteration   │    │ Checker     │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                               │
│   QUALITY GATES:                                                              │
│   ├── Score >= 0.85                                                           │
│   ├── Critical Issues == 0                                                    │
│   ├── Max Iterations == 3                                                     │
│   └── Escalate on failure                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Reference Structure (Created)

```
.claude/
├── reference/                    # Small focused docs (~2k words each)
│   ├── asp-vbscript-patterns.md  # Case-insensitive, ADO cleanup
│   ├── fastapi-conventions.md    # Router structure, error handling
│   ├── testing-patterns.md       # 70/20/10 pyramid, fixtures
│   ├── security-patterns.md      # OWASP, SQL injection
│   ├── stability-analysis.md     # 8 categories, leak patterns
│   └── python-best-practices.md  # Type hints, async patterns
│
└── examples/                     # Copy-paste templates
    ├── service-template.py       # ServiceResult pattern
    ├── api-endpoint-template.py  # CRUD operations
    ├── test-template.py          # Fixtures, parameterized
    └── detector-template.py      # BaseResourceLeakDetector
```

### Week 147: Core Services

| Task | Hours | Output |
|------|-------|--------|
| `ReferenceSelector` service | 6 | Semantic matching for references |
| `TaskRouter` service | 4 | Route to appropriate agent |
| `QualityGateEvaluator` service | 6 | Score calculation, threshold checking |
| `PIVLoopOrchestrator` service | 6 | Iteration management |
| Unit tests | 6 | 40+ tests |
| **Total** | **28** | |

### Week 148: Integration & Web Analysis

| Task | Hours | Output |
|------|-------|--------|
| Agent executor integration | 4 | Connect to existing agents |
| Quality metrics collection | 4 | Track iteration counts, scores |
| Web analysis scheduler | 4 | Weekly best practices scan |
| Reference update workflow | 4 | Human review for new references |
| API endpoints | 4 | `/api/context-engineering/*` |
| Dashboard | 4 | Quality gate statistics |
| E2E tests | 6 | Integration tests |
| **Total** | **30** | |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/context-engineering/analyze` | POST | Analyze task for reference needs |
| `/api/context-engineering/references` | GET | List available references |
| `/api/context-engineering/quality-gates` | GET | Quality gate statistics |
| `/api/context-engineering/iterations/{task_id}` | GET | Get iteration history |
| `/api/context-engineering/web-analysis/trigger` | POST | Trigger web analysis |

### Success Metrics

| Metric | Target |
|--------|--------|
| Token reduction | 60-80% fewer tokens loaded |
| Quality gate pass rate | >85% on first iteration |
| Max iterations before escalation | ≤3 |
| Reference matching accuracy | >90% |
| Web analysis updates | 2-4 new references/month |

### Total Effort: 58 hours (2 weeks)

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Reference files | CREATED | 6 reference files + 4 templates |
| Architecture doc | CREATED | context-engineering-architecture.md |
| Agent system | EXISTS | 11 agents available |

---

## Fase 29: Quality-Functionality Impact Mapping (Week 148-150)

**Goal:** Link quality issues (security, performance, memory leaks, duplication, error handling) to the functionality they impact (Epic/Feature/Story level)
**Specification:** [docs/architecture/quality-functionality-impact-mapping.md](../architecture/quality-functionality-impact-mapping.md)
**Status:** PLANNED
**Priority:** HIGH
**Origin:** User request - "Welke functionaliteit wordt geraakt door kwaliteitsissues?"

### Problem Statement

Bij kwaliteitsanalyses worden issues gedetecteerd maar niet gekoppeld aan de **functionaliteit** die erdoor wordt geraakt:

```
HUIDIGE STAAT:
├── Security Issue: "Unencrypted data transmission"     → Geen link naar functionaliteit
├── Performance Issue: "Missing index on Patient.BSN"  → Welke schermen traag?
├── Memory Leak: "Connection leak in SaveDeclaratie()" → Welke flows crashen?
├── Code Duplication: "CalculateTarief() in 5 files"   → Welke features inconsistent?
└── Error Handling: "Silent failure in Vecozo"         → Welke data corrupt?
```

### Solution: Quality-Functionality Impact Mapper

| Issue Type | Detection Source | Impact Mapping |
|------------|------------------|----------------|
| **Security/Privacy** | GhostCrew, StaticAnalysis | Data flow → Features → Users exposed → Compliance risk |
| **Performance** | SQLAnalyzer | Query → Table → CRUD → Features → Latency impact |
| **Memory Leaks** | StabilityAnalyzer | Function → Call graph → Entry points → Crash probability |
| **Duplication** | DuplicateDetector | Clones → Shared functionality → Inconsistency risk |
| **Error Handling** | ExceptionAnalyzer | Error patterns → User-facing errors → UX impact |

### Example Output

```json
{
  "issue_id": "SEC-001",
  "type": "unencrypted_transmission",
  "location": {"file": "Vecozo_Send.asp", "line": 145},
  "data_exposed": ["BSN", "diagnose_code"],
  "impact": {
    "epic": "Declaratieverwerking",
    "feature": "Vecozo Declaratie Verzending",
    "story": "Declaratie naar verzekeraar sturen",
    "users_affected_daily": 2500,
    "regulatory_risk": ["GDPR", "WGBO", "NEN7510"],
    "business_impact": "Mogelijke boete tot 4% omzet"
  },
  "severity": "CRITICAL"
}
```

### Week-by-Week Deliverables

| Week | Focus | Deliverables |
|------|-------|--------------|
| **148** | Core & Security | `QualityImpactMappingService`, `CodeToFunctionalityMapper`, `SecurityImpactMapper` |
| **149** | Performance & Memory | `PerformanceImpactMapper`, `MemoryLeakImpactMapper`, `ImpactScoreCalculator` |
| **150** | Duplication, Errors & UI | `DuplicationImpactMapper`, `ErrorHandlingImpactMapper`, Dashboard, API |

### Dashboard Features

```
┌─────────────────────────────────────────────────────────────────────┐
│  EPIC: Declaratieverwerking                       HEALTH: ⚠️ 45%   │
├─────────────────────────────────────────────────────────────────────┤
│  🔴 CRITICAL (3): SEC-001, LEAK-001, ERR-001                       │
│  🟠 HIGH (5): PERF-002, DUP-001, ...                               │
│                                                                     │
│  FEATURES AFFECTED:                                                 │
│  ├── Vecozo Declaratie Verzending    [🔴🔴🟠]                       │
│  ├── Batch Declaratie Verwerking     [🔴🟠🟠🟠]                     │
│  └── Declaratie Status Tracking      [🟠🟡]                         │
│                                                                     │
│  IMPACT: 2,500 users/day | €50K/day risk | NEN7510 compliance ⚠️   │
└─────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quality-impact/analyze` | POST | Run quality-to-functionality mapping |
| `/api/quality-impact/project/{id}` | GET | Get all mappings for project |
| `/api/quality-impact/epic/{id}` | GET | Get issues affecting epic |
| `/api/quality-impact/feature/{id}` | GET | Get issues affecting feature |
| `/api/quality-impact/summary/{project_id}` | GET | Aggregated summary per functionality |
| `/api/quality-impact/critical/{project_id}` | GET | Critical issues with business impact |

### Success Metrics

| Metric | Target |
|--------|--------|
| Issue mapping accuracy | >85% correctly linked to functionality |
| Functionality coverage | 95% of issues mapped to Epic/Feature |
| User impact calculation | >80% accuracy on affected users |
| Dashboard usability | <30 sec to understand quality per feature |

### Total Effort: 90 hours (3 weeks)

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 21 (Stability Analyzer) | PLANNED | Memory leak source |
| GhostCrew | COMPLETE | Security issue source |
| HierarchicalStoryExtraction | EXISTS | Code → functionality mapping |
| Brown Paper Enhanced | PLANNED | Integration point |

---

---

## GAP Analysis Phases (Week 151-232)

**Origin:** Gap Analysis van 12 externe bronnen (Week 144)
**Document:** [gap-analysis-complete-roadmap.md](gap-analysis-complete-roadmap.md)
**Total Items:** 75 gaps | **Duration:** 82 weken (~1.6 jaar)

### Fase 24: GAP Quick Wins & Foundation (Week 151-162)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **A1** | Legacy Quickscan (15-min assessment) | 8.0 | 4.5 |
| **K3** | Secret Detection | 8.0 | 2 |
| **D1** | Migration Pattern Library | 7.5 | 3 |
| **D2** | Strangler Fig Pattern Implementation | 7.5 | 3 |
| **K1** | OWASP Integration | 6.7 | 1.5 |
| **K2** | CVE Database Integration | 6.0 | 2 |
| **A4** | Risk Heat Map | 6.0 | 2 |
| **E1** | Visual Dependency Graph | 5.3 | 3 |
| **J1** | Context-Aware Documentation | 5.3 | 3 |
| **D4** | Database Migration Patterns | 5.0 | 4 |
| **K4** | Compliance Mapping (NEN7510/GDPR) | 5.0 | 4 |
| **B5** | ASP.NET Core Analyzer | 4.8 | 4 |
| **B6** | PHP Analyzer | 4.8 | 4 |
| **A2** | Brown Paper Technical Debt View | 4.5 | 3 |
| **A3** | Architecture Assessment Matrix | 4.5 | 3 |

### Fase 25: GAP Core Platform Enhancement (Week 163-178)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **E2** | Interactive Migration Roadmap | 4.8 | 4 |
| **B1** | COBOL Analyzer | 4.7 | 5 |
| **G3** | Knowledge Graph Enhancement | 4.7 | 5 |
| **A5** | Maintainability Index | 4.5 | 2 |
| **D3** | API Wrapper Generator (incl. UI Wrapper) | 4.5 | 4 |
| **B8** | UI Field Mapping Engine | 4.5 | 3 |
| **B9** | UI Action Recorder (Playwright) | 4.3 | 4 |
| **J2** | Decision Log System | 4.3 | 3 |
| **H1** | Azure DevOps Deep Integration | 4.0 | 4 |
| **H4** | GitLab Integration | 4.0 | 3 |
| **G1** | Business Rule Extractor Enhanced | 4.0 | 4 |
| **G2** | Domain Model Generator | 4.0 | 4 |
| **K5** | Security Hotspot Prioritization | 4.0 | 3 |
| **B10** | UI Wrapper Orchestrator | 3.8 | 4 |
| **A6** | Technical Debt Forecasting | 3.8 | 4 |
| **E3** | Cost-Benefit Analyzer | 3.8 | 4 |
| **H8** | Project Export Suite (CSV/Excel/ODS/OpenProject/LibrePlan/MS Project) | 4.5 | 3 |
| **A7** | Cost Anomaly Detection | 4.2 | 3 |

### Fase 26: GAP AI & Automation (Week 179-192)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **B12** | LLM Agent Collaboration Framework | 5.0 | 5 |
| **I1** | Natural Language Query Interface | 4.8 | 4 |
| **I2** | Intelligent Code Suggestions | 4.5 | 4 |
| **I4** | Pattern Learning from History | 3.8 | 5 |
| **I5** | Automated Impact Analysis | 3.8 | 4 |
| **E4** | Progress Tracking Dashboard | 3.6 | 3 |
| **E5** | Milestone Predictor | 3.5 | 4 |
| **B2** | RPG Analyzer | 3.5 | 5 |
| **B3** | Natural Analyzer | 3.5 | 4 |
| **B4** | CICS Analyzer | 3.5 | 4 |
| **D5** | Containerization Assistant | 3.5 | 4 |
| **B11** | UI Sync Monitor | 3.5 | 3 |

### Fase 27: GAP Testing Excellence (Week 193-202)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **F1** | Characterization Test Generator Enhanced | 4.5 | 4 |
| **F2** | Test Gap Analyzer | 4.3 | 3 |
| **F3** | Regression Test Suite | 4.0 | 4 |
| **F4** | Performance Baseline System | 3.8 | 4 |
| **F5** | Contract Testing Framework | 3.8 | 4 |
| **F6** | Mutation Testing | 3.5 | 4 |
| **K6** | Penetration Test Integration | 3.5 | 4 |
| **B7** | Delphi Analyzer | 3.5 | 5 |

### Fase 28: GAP Advanced Integrations (Week 203-214)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **H3** | Jira Deep Integration | 4.0 | 4 |
| **H5** | ServiceNow Integration | 3.8 | 4 |
| **H6** | Slack/Teams Bot | 3.8 | 3 |
| **H7** | Custom Webhook Framework | 3.5 | 3 |
| **G4** | Legacy API Discovery | 3.5 | 4 |
| **G5** | Data Flow Mapper | 3.5 | 4 |
| **G6** | Screen Flow Analyzer | 3.5 | 4 |
| **J3** | Migration Playbook Generator | 3.5 | 4 |
| **J4** | Knowledge Transfer Portal | 3.5 | 4 |
| **J5** | Video Tutorial Generator | 3.5 | 4 |

### Fase 29: GAP Innovation & Scale (Week 215-232)

| Item | Beschrijving | ROI | Weken |
|------|-------------|-----|-------|
| **I6** | Multi-language Code Translation | 4.0 | 6 |
| **D6** | Microservice Decomposer | 3.8 | 5 |
| **D7** | Event Sourcing Migrator | 3.8 | 4 |
| **G7** | State Machine Extractor | 3.5 | 4 |
| **G8** | Workflow Pattern Detector | 3.5 | 4 |
| **E6** | Resource Optimization Advisor | 3.5 | 4 |
| **E7** | What-If Scenario Planner | 3.5 | 5 |
| **J6** | Stakeholder Report Generator | 3.5 | 3 |
| **J7** | Executive Summary Dashboard | 3.5 | 3 |

---

## Integrated Roadmap Timeline

```
WEEK 144-150: CRITICAL FOUNDATION
├── Week 144-146: Fase 21 Stability Analyzer (remaining detectors)
├── Week 146-147: Fase 22 FP Methodology Overhaul 🚨 CRITICAL
├── Week 147-148: Fase 23 Context Engineering & PIV Loop
└── Week 148-150: Quality-Functionality Impact Mapping

WEEK 151-232: GAP ANALYSIS IMPLEMENTATION
├── Week 151-162: Fase 24 - Quick Wins & Foundation (15 items)
├── Week 163-178: Fase 25 - Core Platform Enhancement (18 items)
├── Week 179-192: Fase 26 - AI & Automation (12 items)
├── Week 193-202: Fase 27 - Testing Excellence (8 items)
├── Week 203-214: Fase 28 - Advanced Integrations (10 items)
└── Week 215-232: Fase 29 - Innovation & Scale (9 items)
```

### Key Design Principles (User Requirements)

1. **Small, Specialized Analyzers** - COBOL items (B2, B3, B4) blijven apart: kwaliteit boven snelheid
2. **LLM Agent Collaboration** - Agents werken autonoom samen via B12 framework
3. **Human-in-Loop** - Alleen voor review en escalatie, niet voor standaard werk
4. **No Marketplace** - Templates lokaal, geen externe marketplace
5. **Multi-format Export** - H8: CSV, Excel, ODS, OpenProject, LibrePlan, MS Project

### Excluded Items (ROI < 3.5)

| Item | Beschrijving | ROI | Reden |
|------|-------------|-----|-------|
| C3 | Realtime Collaboration | 2.5 | Alleen voor LLM agents (zie B12) |
| C7 | Team Performance Analytics | 3.0 | Niet prioriteit |
| C8 | Resource Allocation Optimizer | 3.2 | Te complex voor ROI |
| I7 | Self-Learning Recommendations | 3.2 | Experimenteel |
| H2 | GitHub Actions Templates | 3.3 | Beperkte scope |
| I3 | Automated Refactoring Suggestions | 3.4 | Net onder threshold |

---

## Technical Debt Backlog

| Task | Effort | Priority | Notes |
|------|--------|----------|-------|
| **FP Methodology Fix** 🚨 | 36 uur | **CRITICAL** | See Fase 22 - NESMA/IFPUG violations make estimates indefensible |
| **Pydantic V2 Migration** | 8-16 uur | Medium | Breaking changes in validators, model_validator etc. |
| **FastAPI Lifespan Handlers** | 2 uur | Low | Replace deprecated on_event with lifespan context manager |
| **datetime.utcnow() deprecation** | 2 uur | Low | Use timezone-aware datetimes (datetime.now(UTC)) |

---

## Related Documentation

| Topic | Document |
|-------|----------|
| **GAP Analysis Complete** | [gap-analysis-complete-roadmap.md](gap-analysis-complete-roadmap.md) |
| Brown Paper Enhanced Spec | [docs/architecture/brown-paper-enhanced.md](../architecture/brown-paper-enhanced.md) |
| Deep Extraction Pipeline | [docs/architecture/deep-extraction-pipeline.md](../architecture/deep-extraction-pipeline.md) |
| CiRA Causality | [docs/architecture/cira-causality-detection.md](../architecture/cira-causality-detection.md) |
| Business Model | [docs/BUSINESS_MODEL.md](../BUSINESS_MODEL.md) |
| **FP Methodology (IFPUG CPM 4.3.1)** | [estimation/function_points.py](../../backend/estimation/function_points.py) |
| **FysioOne Audit (Case Study)** | [FysioOne Audit Results](/opt/projecten/paramedi/FYSIOONE_AUDIT_RESULTS.md) |
| **Quality-Functionality Impact Mapping** | [docs/architecture/quality-functionality-impact-mapping.md](../architecture/quality-functionality-impact-mapping.md) |
