# Fase 29: Quality-Functionality Impact Mapping (Week 148-150)

**Goal:** Link quality issues (security, performance, memory leaks, duplication, error handling) to the functionality they impact (Epic/Feature/Story level)
**Specification:** [docs/architecture/quality-functionality-impact-mapping.md](../../architecture/quality-functionality-impact-mapping.md)
**Status:** PLANNED
**Priority:** HIGH
**Origin:** User request - "Welke functionaliteit wordt geraakt door kwaliteitsissues?"

---

## Problem Statement

Bij kwaliteitsanalyses worden issues gedetecteerd maar niet gekoppeld aan de **functionaliteit** die erdoor wordt geraakt:

```
HUIDIGE STAAT:
├── Security Issue: "Unencrypted data transmission"     → Geen link naar functionaliteit
├── Performance Issue: "Missing index on Patient.BSN"  → Welke schermen traag?
├── Memory Leak: "Connection leak in SaveDeclaratie()" → Welke flows crashen?
├── Code Duplication: "CalculateTarief() in 5 files"   → Welke features inconsistent?
└── Error Handling: "Silent failure in Vecozo"         → Welke data corrupt?
```

---

## Solution: Quality-Functionality Impact Mapper

| Issue Type | Detection Source | Impact Mapping |
|------------|------------------|----------------|
| **Security/Privacy** | GhostCrew, StaticAnalysis | Data flow → Features → Users exposed → Compliance risk |
| **Performance** | SQLAnalyzer | Query → Table → CRUD → Features → Latency impact |
| **Memory Leaks** | StabilityAnalyzer | Function → Call graph → Entry points → Crash probability |
| **Duplication** | DuplicateDetector | Clones → Shared functionality → Inconsistency risk |
| **Error Handling** | ExceptionAnalyzer | Error patterns → User-facing errors → UX impact |

---

## Example Output

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

---

## Week-by-Week Deliverables

| Week | Focus | Deliverables |
|------|-------|--------------|
| **148** | Core & Security | `QualityImpactMappingService`, `CodeToFunctionalityMapper`, `SecurityImpactMapper` |
| **149** | Performance & Memory | `PerformanceImpactMapper`, `MemoryLeakImpactMapper`, `ImpactScoreCalculator` |
| **150** | Duplication, Errors & UI | `DuplicationImpactMapper`, `ErrorHandlingImpactMapper`, Dashboard, API |

---

## Dashboard Features

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

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quality-impact/analyze` | POST | Run quality-to-functionality mapping |
| `/api/quality-impact/project/{id}` | GET | Get all mappings for project |
| `/api/quality-impact/epic/{id}` | GET | Get issues affecting epic |
| `/api/quality-impact/feature/{id}` | GET | Get issues affecting feature |
| `/api/quality-impact/summary/{project_id}` | GET | Aggregated summary per functionality |
| `/api/quality-impact/critical/{project_id}` | GET | Critical issues with business impact |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Issue mapping accuracy | >85% correctly linked to functionality |
| Functionality coverage | 95% of issues mapped to Epic/Feature |
| User impact calculation | >80% accuracy on affected users |
| Dashboard usability | <30 sec to understand quality per feature |

---

## Total Effort: 90 hours (3 weeks)

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 21 (Stability Analyzer) | COMPLETE | Memory leak source |
| GhostCrew | COMPLETE | Security issue source |
| HierarchicalStoryExtraction | EXISTS | Code → functionality mapping |
| Brown Paper Enhanced | COMPLETE | Integration point |

---

← [Back to Overview](../phases-planned.md)
