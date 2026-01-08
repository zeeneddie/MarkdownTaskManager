# Migration Strategy: Rebuild from Specs (Not Code Migration)

**Author:** Claude Code (Week 136 - Fase 24)
**Date:** 2026-01-01
**Status:** Approved Architecture Decision

---

## Executive Summary

We kiezen voor **Rebuild from Specs** in plaats van **Code Migration (Lift-and-Shift)**.

Dit betekent:
- Geen code conversie (VB.NET → C#)
- Wél: Specs/Stories uit Brown Paper Enhanced gebruiken als basis voor nieuwe implementatie
- Clean architecture mogelijk met moderne patterns
- 100% user journey match (tenzij expliciet overruled door Eddie)

---

## Waarom Rebuild (Niet Lift-and-Shift)

| Aspect | ❌ Code Migratie | ✅ Rebuild from Specs |
|--------|-----------------|----------------------|
| **Tech Debt** | Brengt legacy patterns mee | Clean slate, zero tech debt |
| **Architecture** | VB.NET idioom in C# | Native C#/.NET 8 of Python/Django |
| **Patterns** | Legacy patterns behouden | CQRS, Event Sourcing, DDD mogelijk |
| **Testbaarheid** | Moeilijk te testen | TDD from start, 100% testable |
| **UI** | 1:1 conversie | UI journey match, betere UX mogelijk |
| **Maintainability** | Complex legacy code | Clean, maintainable code |

---

## De Twee Strategieën

### Strategie A: Code Migration (NIET GEKOZEN)

```
┌─────────────────────┐         ┌─────────────────────┐
│  LEGACY CODEBASE    │         │  NEW CODEBASE       │
│  (VB.NET/ASP.NET)   │ ──────► │  (C#/.NET 8)        │
└─────────────────────┘         └─────────────────────┘
        │                               │
        │   CodeTransformationService   │
        │   - Regex patterns            │
        │   - Syntax conversion         │
        │   - Type mapping              │
        └───────────────────────────────┘

Probleem: Legacy patterns worden meegenomen
         Tech debt blijft bestaan
         Moeilijk om modern te maken
```

### Strategie B: Rebuild from Specs (GEKOZEN)

```
┌─────────────────────┐         ┌─────────────────────────────────────────┐
│  LEGACY CODEBASE    │         │  SPECS + STORIES + TESTS                │
│  (VB.NET/ASP.NET)   │ ──────► │  ├── Epics (uit Hierarchical Extraction)│
└─────────────────────┘         │  ├── Features (uit Domain Extraction)   │
        │                       │  ├── User Stories (INVEST validated)    │
        │                       │  ├── Acceptance Criteria                │
   BROWN PAPER                  │  ├── Golden Master Tests (baseline)     │
   ENHANCED                     │  └── Business Rules (CiRA causality)    │
   (6-fase analyse)             └─────────────────────────────────────────┘
                                          │
                                          ▼
                                ┌─────────────────────────────────────────┐
                                │  TDD DEVELOPMENT                         │
                                │  ├── Write test (from Golden Master)     │
                                │  ├── Build feature (clean architecture)  │
                                │  ├── Compare UI (Visual Regression)      │
                                │  └── Validate journey (Dual-Run)         │
                                └─────────────────────────────────────────┘
                                          │
                                          ▼
                                ┌─────────────────────────────────────────┐
                                │  NEW CODEBASE (Clean Architecture)       │
                                │  ├── Domain Layer (Entities, Value Obj)  │
                                │  ├── Application Layer (Use Cases)       │
                                │  ├── Infrastructure (DB, APIs)           │
                                │  └── Presentation (UI, API)              │
                                └─────────────────────────────────────────┘
```

---

## Voordelen van Onze Investering in Functionaliteit Ontdekking

We hebben fors geïnvesteerd in Brown Paper Enhanced (6-fase analyse):

| Phase | Output | Waarde voor Rebuild |
|-------|--------|---------------------|
| Phase 1: Code Understanding | Dependency graph, complexity metrics | Bepaalt module volgorde |
| Phase 2: Domain Extraction | Business domains, boundaries | Clean DDD bounded contexts |
| Phase 3: Hierarchical Extraction | Epics, Features, Stories | Backlog voor nieuwe implementatie |
| Phase 4: Deep Extraction | INVEST validated stories | Directe user stories |
| Phase 5: Estimation | Function Points, Story Points | Accurate planning |
| Phase 6: Output | Traceability matrix | Volledige traceerbaarheid |

**Deze investering maakt Rebuild mogelijk en betrouwbaar.**

---

## Dual-System E2E Testing

De user journey moet 100% gelijk zijn (tenzij Eddie een override goedkeurt).

### Test Harness Architectuur

```
┌─────────────────┐                              ┌─────────────────┐
│  LEGACY SYSTEM  │                              │  NEW SYSTEM     │
│  (Production)   │                              │  (Staging)      │
└────────┬────────┘                              └────────┬────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  E2E TEST HARNESS                                                        │
│                                                                          │
│  1. JOURNEY RECORDER                                                     │
│     └── Playwright captures: clicks, inputs, navigation, API calls       │
│                                                                          │
│  2. PARALLEL EXECUTOR                                                    │
│     ├── Run journey on LEGACY → capture screenshots + responses          │
│     └── Run journey on NEW    → capture screenshots + responses          │
│                                                                          │
│  3. COMPARISON ENGINE                                                    │
│     ├── Visual: screenshot diff (VisualRegressionService)               │
│     ├── Data: response diff (DualRunComparisonService)                  │
│     ├── Journey: step-by-step match (JourneyComparisonService)          │
│     └── Override rules: Eddie's exceptions                               │
│                                                                          │
│  4. REPORT                                                               │
│     ├── ✅ Match: 47/50 steps identical                                  │
│     ├── ⚠️ Override: 2 steps (approved by Eddie)                        │
│     └── ❌ Mismatch: 1 step (needs fix)                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Override Rules (Eddie's Control)

```json
{
  "journey": "appointment_booking",
  "step": 5,
  "override_type": "improved_ux",
  "legacy_behavior": "3-click date picker",
  "new_behavior": "1-click calendar",
  "reason": "Improved UX, approved in sprint review",
  "approved_by": "eddie",
  "approved_at": "2026-01-15"
}
```

### Override Types

| Type | Beschrijving | Voorbeeld |
|------|-------------|-----------|
| `improved_ux` | Nieuwe systeem heeft betere UX | 3-click → 1-click |
| `intentional_change` | Business-approved wijziging | Nieuw validatie regel |
| `known_difference` | Acceptabel technisch verschil | Date format NL → ISO |
| `temporary` | Tijdelijke exception, wordt gefixed | Bug in legacy |

---

## Fase 24: Data Architecture Services

De services voor Rebuild Strategy:

### 1. DataLineageService

Trackeert de volledige keten: Brown Paper → Spec → Story → Test → Code

```
Brown Paper Session
    └── Domain
        └── Entity
            └── Field
                └── Epic
                    └── Feature
                        └── User Story
                            └── Acceptance Criteria
                                └── Test Case
                                    └── Code Implementation
```

**Key capabilities:**
- Import from Brown Paper Enhanced output
- Field mapping (legacy → new)
- Impact analysis ("als dit verandert, wat breekt er?")
- Traceability reports

### 2. ERDGeneratorService

Genereert TARGET ERD (niet legacy copy):
- Input: Extracted entities uit Brown Paper
- Output: Mermaid/PlantUML voor nieuwe clean architecture
- Normalization suggestions (3NF, DDD aggregates)
- Bounded context mapping

### 3. CDCIntegrationService

Change Data Capture voor dual-system sync:
- Shadow mode: nieuwe systeem ontvangt data, geen writes
- Mirror mode: full sync, writes allowed
- Cutover support: switch van legacy naar new

### 4. JourneyComparisonService

E2E journey comparison:
- Record user journey (Playwright)
- Replay on both systems
- Compare step-by-step (visual + data)
- Override management (Eddie's goedkeuringen)

---

## Development Workflow (TDD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TDD WORKFLOW MET DUAL-SYSTEM VALIDATION                                     │
│                                                                              │
│  STEP 1: Write Test (from Golden Master)                                    │
│  ├── Get acceptance criteria from Brown Paper                               │
│  ├── Create characterization test (legacy behavior)                         │
│  └── Define expected behavior                                               │
│                                                                              │
│  STEP 2: Build Feature (Clean Architecture)                                 │
│  ├── Domain layer first (entities, value objects)                           │
│  ├── Application layer (use cases)                                          │
│  ├── Infrastructure (repositories, APIs)                                    │
│  └── Presentation (UI components)                                           │
│                                                                              │
│  STEP 3: Run Tests                                                          │
│  ├── Unit tests (new code)                                                  │
│  ├── Integration tests (new code)                                           │
│  └── E2E journey tests (legacy vs new)                                      │
│                                                                              │
│  STEP 4: Compare Journey                                                    │
│  ├── Record journey on legacy                                               │
│  ├── Replay journey on new                                                  │
│  ├── Compare step-by-step                                                   │
│  └── Flag mismatches for review                                             │
│                                                                              │
│  STEP 5: Review & Approve                                                   │
│  ├── Match? → Continue to next feature                                      │
│  ├── Mismatch (bug)? → Fix and re-run                                      │
│  └── Mismatch (intentional)? → Eddie creates override rule                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Services Summary

| Service | Agent | Purpose | Status |
|---------|-------|---------|--------|
| **DataLineageService** | Miguel | Track specs → code traceability | ✅ COMPLETE |
| **JourneyComparisonService** | Tessa | E2E journey comparison | ✅ COMPLETE |
| **ERDGeneratorService** | Felix | Generate target architecture ERD | 📋 PLANNED |
| **CDCIntegrationService** | Miguel | Dual-system data sync | 📋 PLANNED |

---

## Key Principles

1. **100% Journey Match** - Unless explicitly overridden by Eddie
2. **Specs as Source of Truth** - Not legacy code
3. **Clean Architecture** - Modern patterns, no legacy baggage
4. **TDD First** - Tests before code
5. **Traceability** - Full lineage from Brown Paper to code
6. **Eddie's Control** - All overrides require explicit approval

---

## Related Documentation

| Document | Content |
|----------|---------|
| [brown-paper-enhanced.md](brown-paper-enhanced.md) | 6-phase deep analysis |
| [migration-enhanced.md](migration-enhanced.md) | 7-phase migration execution |
| [deep-extraction-pipeline.md](deep-extraction-pipeline.md) | LLM extraction pipeline |
| [AGENTS.md](../../AGENTS.md) | Agent system reference |
