# MarQed Platform Roadmap

**Project:** MarQed AI Agent Software Platform
**Last Updated:** Week 144 (2026-01-08)
**Total Phases:** 29 | **Timeline:** Week 144-232

---

## Executive Summary

De MarQed roadmap combineert de bestaande geplande fases met een uitgebreide gap-analyse van 12 externe bronnen (6 Nederlandse consultancies, 5 GitHub repos, 1 gist).

### Roadmap Overview

```
WEEK 144-150: CRITICAL FOUNDATION (7 weken)
├── Fase 21: Stability Analyzer (remaining detectors)
├── Fase 22: FP Methodology Overhaul 🚨 CRITICAL
├── Fase 23: Context Engineering & PIV Loop
└── Quality-Functionality Impact Mapping

WEEK 151-232: GAP ANALYSIS IMPLEMENTATION (82 weken)
├── Fase 24: Quick Wins & Foundation (15 items)
├── Fase 25: Core Platform Enhancement (18 items)
├── Fase 26: AI & Automation (12 items)
├── Fase 27: Testing Excellence (8 items)
├── Fase 28: Advanced Integrations (10 items)
└── Fase 29: Innovation & Scale (9 items)
```

---

## Current Focus (Week 144)

| Area | Status | Details |
|------|--------|---------|
| **Stability Analyzers** | IN PROGRESS | SessionAnalyzer, MemoryAnalyzer, ExternalServiceAnalyzer |
| **GAP Analysis** | COMPLETE | 75 items identified, 6 phases planned |
| **Documentation** | COMPLETE | Roadmap synchronized |

See: [phases-current.md](docs/roadmap/phases-current.md)

---

## Critical Path (Week 146-150)

### Fase 22: FP Methodology Overhaul 🚨

**Priority:** CRITICAL
**Problem:** Current IFPUG/NESMA implementation has serious methodology errors
**Fix:** Enhancement FP calculator, work type classifier, component validators

| Issue | Impact | Fix |
|-------|--------|-----|
| EIF for source files | -17 FP overcounting | Validate EIF rules |
| ILF for code patterns | -14 FP overcounting | Validate ILF rules |
| Missing maintenance FP | Wrong methodology | Enhancement FP calculator |

See: [phases-planned.md#fase-22](docs/roadmap/phases-planned.md#fase-22-fp-methodology-overhaul-week-146-147--critical)

### Fase 23: Context Engineering & PIV Loop

**Goal:** Intelligent reference loading and quality gates for agent output
**Benefit:** 60-80% token reduction, >85% first-pass quality

### Quality-Functionality Impact Mapping

**Goal:** Link quality issues to Epic/Feature/Story level
**Benefit:** Business impact visibility for all findings

---

## GAP Analysis Phases (Week 151-232)

### Phase Summary

| Fase | Focus | Items | Weken | Key Deliverables |
|------|-------|-------|-------|------------------|
| **24** | Quick Wins | 15 | 12 | Legacy Quickscan, Secret Detection, Migration Patterns |
| **25** | Core Enhancement | 18 | 16 | COBOL Analyzer, UI Wrapper, Knowledge Graph |
| **26** | AI & Automation | 12 | 14 | LLM Collaboration, Natural Language Query |
| **27** | Testing | 8 | 10 | Characterization Tests, Mutation Testing |
| **28** | Integrations | 10 | 12 | Jira, GitLab, ServiceNow |
| **29** | Innovation | 9 | 16 | Multi-language Translation, Microservices |

### Top 10 Highest ROI Items

| Rank | Item | ROI | Description |
|------|------|-----|-------------|
| 1 | A1 | 8.0 | Legacy Quickscan (15-min assessment) |
| 2 | K3 | 8.0 | Secret Detection |
| 3 | D1 | 7.5 | Migration Pattern Library |
| 4 | D2 | 7.5 | Strangler Fig Implementation |
| 5 | K1 | 6.7 | OWASP Integration |
| 6 | K2 | 6.0 | CVE Database Integration |
| 7 | A4 | 6.0 | Risk Heat Map |
| 8 | E1 | 5.3 | Visual Dependency Graph |
| 9 | J1 | 5.3 | Context-Aware Documentation |
| 10 | B12 | 5.0 | LLM Agent Collaboration Framework |

See: [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md)

---

## Design Principles

1. **Small, Specialized Analyzers** - COBOL items (B2, B3, B4) blijven apart: kwaliteit boven snelheid
2. **LLM Agent Collaboration** - Agents werken autonoom samen via B12 framework
3. **Human-in-Loop** - Alleen voor review en escalatie, niet voor standaard werk
4. **No Marketplace** - Templates lokaal, geen externe marketplace
5. **Multi-format Export** - CSV, Excel, ODS, OpenProject, LibrePlan, MS Project

---

## Documentation Links

| Document | Description |
|----------|-------------|
| [phases-current.md](docs/roadmap/phases-current.md) | Week 144 status |
| [phases-planned.md](docs/roadmap/phases-planned.md) | Fase 22-29 details |
| [phases-completed.md](docs/roadmap/phases-completed.md) | Fase 1-21 archive |
| [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md) | Full 75-item specs |

---

## Milestones

| Milestone | Week | Deliverable |
|-----------|------|-------------|
| **Stability Framework Complete** | 146 | All 8 detection categories |
| **FP Methodology Fixed** | 147 | NESMA/IFPUG compliant |
| **PIV Loop Active** | 148 | Quality gates operational |
| **GAP Phase 1 Start** | 151 | Quick wins implementation |
| **COBOL Support** | 163 | B1 Analyzer complete |
| **LLM Collaboration** | 184 | B12 Framework active |
| **Full Platform** | 232 | All 75 items complete |

---

*Generated: Week 144 (2026-01-08)*
