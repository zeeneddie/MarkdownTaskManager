# Fase 21: ASP Application Stability Analyzer Framework (Week 143-146) COMPLETE

**Goal:** Comprehensive stability analysis covering ALL crash causes, not just ADO leaks.
**Specification:**
- [docs/architecture/asp-stability-analyzer-framework.md](../../architecture/asp-stability-analyzer-framework.md)
- [docs/architecture/resource-leak-detection-framework.md](../../architecture/resource-leak-detection-framework.md)
**Status:** COMPLETE (Week 143 - Core Framework)
**Origin:** Week 142 FysioOne-Classic Stability Analysis (Codex + Claude Review)

---

## Week 143 Deliverables (COMPLETE)

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

---

## Peer Review Learnings (FysioOne Audit 2026-01-06)

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

---

## 8 Detection Categories

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

---

## FysioOne Findings Summary

| Category | Found Issues | Daily Impact |
|----------|--------------|--------------|
| ADO Leaks | 1700+ daily leaks | Connection pool exhaustion |
| COM Objects | 148 CreateObject calls | Memory exhaustion |
| XMLHTTP | 30+ external calls | Thread blocking |
| PDF Generation | 10+ instances | Memory spikes |
| File Operations | 39 in 17 files | Handle exhaustion |

---

## Architecture

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

---

## Generic Leak Patterns

| Pattern | Description | Severity |
|---------|-------------|----------|
| `NEVER_CLOSED` | Created but never released | HIGH |
| `LOOP_LEAK` | Created in loop without per-iteration cleanup | **CRITICAL++** |
| `FUNCTION_LEAK` | Created in function without cleanup before return | HIGH |
| `EARLY_EXIT_LEAK` | Orphaned by Response.End, return, throw | MEDIUM |
| `CONDITIONAL_LEAK` | Condition prevents closure | MEDIUM |
| `REOPEN_LEAK` | Open→Close→Open without final close (new!) | **HIGH** |
| `SET_WITHOUT_CLOSE` | Only `Set = Nothing` without `.Close()` | **HIGH** |

---

## Week-by-Week Implementation

### Week 143: Core Framework + ADO/COM Detectors (COMPLETE)

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

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stability/analyze` | POST | Full 8-category stability analysis |
| `/api/stability/report/{project_id}` | GET | Get stability report |
| `/api/stability/categories` | GET | List available categories |
| `/api/stability/findings/{project_id}` | GET | Individual findings |
| `/api/stability/findings/{project_id}/category/{cat}` | GET | Findings by category |
| `/api/stability/fix-suggestions/{finding_id}` | GET | AI-generated fix suggestions |
| `/api/stability/metrics/{project_id}` | GET | Stability score over time |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Detection accuracy | >90% per category |
| False positive rate | <5% |
| Analysis speed | <2s per file |
| Categories covered | 8 stability categories |
| Language coverage | 4 languages (ASP, PHP, VB.NET, Java) |
| Fix suggestion accuracy | >80% |

---

## Total Effort: 124 hours (4 weeks)

---

← [Back to Overview](../phases-planned.md)
