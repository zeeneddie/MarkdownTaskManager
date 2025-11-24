# First Dogfood Feature Plan - Week 20

**Datum**: 2025-11-21
**Target Week**: Week 20 (Feb 10-16, 2026)
**Status**: PLANNED
**Milestone**: Systeem ontwikkelt eerste feature zelf!

---

## Executive Summary

In Week 20 gaat het Markdown Task Manager systeem voor het eerst een feature **voor zichzelf** ontwikkelen. Dit is de ultieme test: kan het systeem dat we bouwen, zichzelf verder bouwen?

---

## Kandidaat Feature: "Estimation History Export"

### Waarom Deze Feature?

| Criterium | Score | Reden |
|-----------|-------|-------|
| **Complexiteit** | Medium | Niet te simpel, niet te complex |
| **Zelfstandig** | Hoog | Geen externe dependencies |
| **Testbaar** | Hoog | Duidelijke success criteria |
| **Zichtbaar** | Hoog | Concreet resultaat (download) |
| **Relevant** | Hoog | Echte feature voor ons systeem |
| **Risico** | Laag | Als het faalt, geen productie impact |

### Feature Beschrijving

```
ALS gebruiker van de Estimation Dashboard
WIL IK mijn berekeningen kunnen exporteren naar CSV/JSON
ZODAT IK historische data kan analyseren en delen met stakeholders
```

### Acceptance Criteria

1. [ ] Export knop op Estimation Dashboard
2. [ ] Keuze tussen CSV en JSON format
3. [ ] Function Point exports bevatten: project, components, totals, datum
4. [ ] Story Point exports bevatten: story, factors, points, confidence, datum
5. [ ] Download start automatisch na klikken
6. [ ] Filename bevat datum (bijv. `estimation-export-2026-02-10.csv`)

---

## Dogfood Process Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FIRST DOGFOOD: WEEK 20                                │
│                                                                          │
│  ┌──────────────┐                                                        │
│  │ HUMAN INPUT  │  "Add export functionality to estimation dashboard"   │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ WORK TYPE    │  Classifies as: ENHANCEMENT                           │
│  │ CLASSIFIER   │  Confidence: >90%                                     │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ FELIX        │  Generates:                                           │
│  │ (Feature     │  - Constitution (business case)                       │
│  │  Architect)  │  - Specification (technical design)                   │
│  │              │  - Tasks (implementation steps)                       │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ ELIZA        │  Estimates:                                           │
│  │ (Estimation) │  - Function Points: ~15 FP                            │
│  │              │  - Story Points: 5 (Medium)                           │
│  │              │  - Effort: ~1 dag                                      │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ FELIX        │  Generates actual code:                               │
│  │ (Code Gen)   │  - JavaScript export functions                        │
│  │              │  - UI buttons + modal                                 │
│  │              │  - CSV/JSON formatters                                │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ VALIDATION   │  Validates code:                                      │
│  │ FRAMEWORK    │  Phase 1: Linting (eslint) ✓                         │
│  │              │  Phase 2: No TypeScript                               │
│  │              │  Phase 3: Style (prettier) ✓                         │
│  │              │  Phase 4: Unit tests ✓                               │
│  │              │  Phase 5: Manual E2E                                  │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ ITERATION    │  If validation fails:                                 │
│  │ LOOP         │  → Felix fixes automatically                         │
│  │              │  → Re-validate (max 3x)                              │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ QUINN        │  Security review:                                     │
│  │ (Quality)    │  - XSS check on filename                             │
│  │              │  - No sensitive data exposure                         │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ TESSA        │  Generates tests:                                     │
│  │ (Testing)    │  - Unit tests for formatters                         │
│  │              │  - Integration test for download                      │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ DIANA        │  Documents:                                           │
│  │ (Docs)       │  - Updated README section                            │
│  │              │  - Inline code comments                              │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ HUMAN        │  Final review:                                        │
│  │ REVIEW       │  - Code quality check                                │
│  │              │  - Manual testing                                     │
│  │              │  - Accept or request changes                         │
│  └──────┬───────┘                                                        │
│         ↓                                                                │
│  ┌──────────────┐                                                        │
│  │ MERGE        │  If accepted:                                         │
│  │              │  - Git commit (auto-generated message)               │
│  │              │  - Feature complete!                                  │
│  └──────────────┘                                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites (Must be done by Week 19)

### Week 17-18: Validation Foundation
- [ ] `ValidationService` operational
- [ ] 5-phase pipeline working
- [ ] Linting phase (eslint for JS)
- [ ] Style phase (prettier)

### Week 19: Workflow Integration
- [ ] ENHANCEMENT workflow has validation loop
- [ ] Felix can request fixes based on validation errors
- [ ] Iteration loop working (max 3 attempts)

### Week 19 (Additional):
- [ ] Work Type Classifier routes correctly to ENHANCEMENT
- [ ] Felix code generation working for frontend JS
- [ ] Basic test generation working

---

## Success Criteria for Dogfood

### Minimum Viable Dogfood (MVP)
```
□ System accepts natural language input
□ Correctly classifies as ENHANCEMENT
□ Felix generates working code
□ Validation catches errors
□ At least 1 successful iteration fix
□ Human review approves result
□ Feature works in production
```

### Full Success
```
□ All MVP criteria
□ Zero manual code edits needed
□ Tests pass automatically
□ Documentation generated
□ Total time < 2 hours
□ Estimation within 25% of actual
```

### Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Classification Accuracy | 100% | Did it pick ENHANCEMENT? |
| First-Pass Validation | >50% | Code passes validation first try |
| Iteration Success | 100% | Passes within 3 iterations |
| Human Edit Ratio | <20% | Lines changed by human / total lines |
| Time to Complete | <2h | Start to merge time |
| Estimation Accuracy | ±25% | Estimated vs actual hours |

---

## Fallback Plan

Als de dogfood faalt:

### Level 1: Minor Issues
- Human fixes small bugs
- Log issues for improvement
- Still count as partial success

### Level 2: Major Issues
- Human completes feature manually
- Detailed analysis of failure points
- Delay full dogfood to Week 22

### Level 3: Complete Failure
- Reassess Validation Framework
- Additional 2 weeks development
- Retry in Week 24

---

## Expected Output

### Generated Files

```
frontend/
├── estimation-dashboard.html  (MODIFIED - export buttons added)
└── js/
    └── estimation-export.js   (NEW - ~100 lines)

tests/
└── estimation-export.test.js  (NEW - ~50 lines)
```

### Sample Generated Code (Expected)

```javascript
// estimation-export.js (generated by Felix)

/**
 * Export estimation data to CSV or JSON
 * @param {string} type - 'function-points' or 'story-points'
 * @param {string} format - 'csv' or 'json'
 */
function exportEstimation(type, format) {
    const data = collectEstimationData(type);
    const filename = generateFilename(type, format);

    if (format === 'csv') {
        downloadCSV(data, filename);
    } else {
        downloadJSON(data, filename);
    }
}

function collectEstimationData(type) {
    // Collect data from DOM or API
    // ...
}

function generateFilename(type, format) {
    const date = new Date().toISOString().split('T')[0];
    return `${type}-export-${date}.${format}`;
}

function downloadCSV(data, filename) {
    // Convert to CSV and trigger download
    // ...
}

function downloadJSON(data, filename) {
    // Convert to JSON and trigger download
    // ...
}
```

---

## Timeline

### Week 20 Schedule

| Dag | Activiteit | Duur |
|-----|-----------|------|
| **Maandag** | Input feature request in system | 15 min |
| | System processes (classify, spec, estimate) | 30 min |
| | Felix generates code | 30 min |
| | Validation + iteration | 30 min |
| **Maandag** | Human review + testing | 1h |
| **Dinsdag** | Fixes if needed, merge | 1h |
| **Dinsdag** | Retrospective + documentation | 1h |

**Total Expected: 4-5 hours**

---

## Post-Dogfood Actions

### If Successful:
1. [ ] Celebrate! 🎉
2. [ ] Document learnings
3. [ ] Plan next dogfood feature (Week 21)
4. [ ] Announce milestone in PROJECT_STATUS_SUMMARY.md

### If Partial Success:
1. [ ] Identify failure points
2. [ ] Create improvement tasks
3. [ ] Adjust Week 21-22 plans
4. [ ] Retry with simpler feature

### Learning Capture:
```
DOGFOOD_RETROSPECTIVE.md:
- What worked well?
- What failed?
- Agent performance (per agent)
- Validation effectiveness
- Estimation accuracy
- Time spent per phase
- Human intervention points
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Validation not ready | High | Low | Week 17-19 focus |
| Felix generates bad code | Medium | Medium | Iteration loop |
| Classification wrong | Low | Low | Extensive testing |
| Export has security issues | Medium | Low | Quinn review |
| Takes too long | Low | Medium | Timeboxing |

---

## Long-term Vision

```
Week 20:  First dogfood (simple feature)
Week 22:  Second dogfood (medium feature)
Week 24:  Third dogfood (complex feature)
Week 26:  Multiple features in parallel
Week 28+: System develops itself primarily
Week 40:  Human = Product Owner only
```

---

**Document Status**: PLANNED
**Author**: Claude Code
**Created**: 2025-11-21
**Target**: Week 20 (Feb 10-16, 2026)
