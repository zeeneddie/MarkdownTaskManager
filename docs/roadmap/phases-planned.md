# Planned Phases (Fase 23.6+)

**Project:** MarQed AI Agent Software Platform
**Period:** Week 158+ (2026-01-XX onwards)
**Last Updated:** 2026-01-13 (Fase 29 + Fase 23.6 Phase 24.1 Complete)

---

## Quick Navigation

| Document | Content |
|----------|---------|
| [ROADMAP.md](../../ROADMAP.md) | Executive summary |
| [phases-completed.md](phases-completed.md) | Completed phases (Fase 1-21) |
| [phases-current.md](phases-current.md) | Current work (Week 144) |
| **This file** | Planned work overview (Fase 22+) |
| [gap-analysis-complete-roadmap.md](gap-analysis-complete-roadmap.md) | Complete GAP analysis (75 items) |

---

## Phase Overview

### Recently Completed

| Fase | Week | Title | Status | Detail |
|------|------|-------|--------|--------|
| **20** | 128-129 | Brown Paper Enhanced | ✅ COMPLETE | [fase-20-brown-paper-enhanced.md](phases/fase-20-brown-paper-enhanced.md) |
| **21** | 143-146 | ASP Stability Analyzer | ✅ COMPLETE | [fase-21-asp-stability-analyzer.md](phases/fase-21-asp-stability-analyzer.md) |
| **21.5** | 145-146 | Workflow Separation | ✅ COMPLETE | [fase-21.5-workflow-separation.md](phases/fase-21.5-workflow-separation.md) |
| **22** | 146-147 | FP Methodology Overhaul | ✅ COMPLETE | [fase-22-fp-methodology.md](phases/fase-22-fp-methodology.md) |
| **23** | 155 | Context Engineering | ✅ COMPLETE | [fase-23-context-engineering.md](phases/fase-23-context-engineering.md) |
| **23.5** | 149-154 | Confucius Orchestrator | ✅ COMPLETE | [fase-23.5-confucius-orchestrator.md](phases/fase-23.5-confucius-orchestrator.md) |
| **29** | 156-157 | Quality-Functionality Impact Mapping | ✅ COMPLETE | [fase-29-quality-impact-mapping.md](phases/fase-29-quality-impact-mapping.md) |
| **23.6** | 157 | Stage Council Review (All Phases) | ✅ COMPLETE | [fase-23.6-stage-council-review.md](phases/fase-23.6-stage-council-review.md) |

### Quality & Security Focus (Week 158-165)

| Fase | Week | Title | Status | Priority | Detail |
|------|------|-------|--------|----------|--------|
| **31** | 158-165 | CWE Top 25 Security Scanner Suite | PLANNED | HIGH | [fase-31-cwe-security-scanners.md](phases/fase-31-cwe-security-scanners.md) |

### GAP Analysis Implementation (Week 163-244)

| Fase | Week | Title | Items | Detail |
|------|------|-------|-------|--------|
| **24** | 163-174 | GAP Quick Wins & Foundation | 15 | [gap-phases.md](phases/gap-phases.md#fase-24) |
| **25** | 175-190 | GAP Core Platform Enhancement | 18 | [gap-phases.md](phases/gap-phases.md#fase-25) |
| **26** | 191-204 | GAP AI & Automation | 12 | [gap-phases.md](phases/gap-phases.md#fase-26) |
| **27** | 205-214 | GAP Testing Excellence | 8 | [gap-phases.md](phases/gap-phases.md#fase-27) |
| **28** | 215-226 | GAP Advanced Integrations | 10 | [gap-phases.md](phases/gap-phases.md#fase-28) |
| **GAP-29** | 227-244 | GAP Innovation & Scale | 9 | [gap-phases.md](phases/gap-phases.md#fase-gap-29) |

### Future Enhancements (Week 233+)

| Fase | Week | Title | Status | Detail |
|------|------|-------|--------|--------|
| **30** | 233-235 | LLM Council Improvements | PLANNED | [fase-30-llm-council-improvements.md](phases/fase-30-llm-council-improvements.md) |

### Supporting Documentation

| Document | Content |
|----------|---------|
| [technical-debt-backlog.md](phases/technical-debt-backlog.md) | Tech debt items & Falcon H1R evaluation |

---

## Integrated Roadmap Timeline

```
WEEK 144-165: CRITICAL FOUNDATION + ORCHESTRATOR + QUALITY
├── Week 143-146: Fase 21 Stability Analyzer ✅ COMPLETE
├── Week 145-146: Fase 21.5 Workflow Separation ✅ COMPLETE
├── Week 146-147: Fase 22 FP Methodology Overhaul ✅ COMPLETE
├── Week 149-154: Fase 23.5 Confucius Orchestrator Integration ✅ COMPLETE
├── Week 155: Fase 23 Context Engineering ✅ COMPLETE
├── Week 156-157: Fase 29 Quality-Functionality Impact Mapping ✅ COMPLETE (27 tests)
├── Week 157: Fase 23.6 Stage Council Review ✅ COMPLETE (All 4 Phases - 44+ tests)
└── Week 158-165: Fase 31 CWE Top 25 Security Scanners 🔐 SECURITY (PLANNED)

WEEK 163-244: GAP ANALYSIS IMPLEMENTATION
├── Week 163-174: Fase 24 - Quick Wins & Foundation (15 items)
├── Week 175-190: Fase 25 - Core Platform Enhancement (18 items)
├── Week 191-204: Fase 26 - AI & Automation (12 items)
├── Week 205-214: Fase 27 - Testing Excellence (8 items)
├── Week 215-226: Fase 28 - Advanced Integrations (10 items)
└── Week 227-244: Fase GAP-29 - Innovation & Scale (9 items)
```

---

## Effort Summary

| Phase Group | Phases | Total Hours | Weeks | Status |
|-------------|--------|-------------|-------|--------|
| Workflow Separation | 21.5 | ~40 | 2 | ✅ COMPLETE |
| FP Methodology | 22 | ~24 | 1 | ✅ COMPLETE |
| Confucius Orchestrator | 23.5 | ~120 | 6 | ✅ COMPLETE |
| Context Engineering | 23 | ~24 | 1 | ✅ COMPLETE |
| Quality Impact Mapping | 29 | ~40 | 2 | ✅ COMPLETE |
| Stage Council Review | 23.6 | ~120 | 4 | ✅ COMPLETE |
| CWE Security Scanners | 31 | ~150 | 8 | PLANNED |
| GAP Analysis | 24-29 | ~1500 | 82 | PLANNED |
| Future | 30 | 72 | 2 | PLANNED |
| **Total** | **14 phases** | **~2074** | **~110** | |

---

## Key Design Principles

1. **Small, Specialized Analyzers** - COBOL items (B2, B3, B4) blijven apart: kwaliteit boven snelheid
2. **LLM Agent Collaboration** - Agents werken autonoom samen via B12 framework
3. **Human-in-Loop** - Alleen voor review en escalatie, niet voor standaard werk
4. **No Marketplace** - Templates lokaal, geen externe marketplace
5. **Multi-format Export** - H8: CSV, Excel, ODS, OpenProject, LibrePlan, MS Project

---

## Dependencies Graph

```
                    ┌──────────────────┐
                    │   Fase 21.5      │
                    │ Workflow Separation│
                    │   ✅ COMPLETE    │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│    Fase 22      │  │   Fase 23    │  │    Fase 29      │
│ FP Methodology  │  │Context Eng.  │  │ Quality Impact  │
│  ✅ COMPLETE    │  │  ✅ COMPLETE │  │  ✅ COMPLETE    │
└─────────────────┘  └──────┬───────┘  └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   Fase 23.5     │
                   │   Confucius     │
                   │   ✅ COMPLETE   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   Fase 23.6     │
                   │ Stage Council   │
                   │   ✅ COMPLETE   │
                   └─────────────────┘
```

---

## Detail Documents Index

| File | Description |
|------|-------------|
| [fase-20-brown-paper-enhanced.md](phases/fase-20-brown-paper-enhanced.md) | 6-phase enhanced workflow |
| [fase-21-asp-stability-analyzer.md](phases/fase-21-asp-stability-analyzer.md) | 8-category stability detection |
| [fase-21.5-workflow-separation.md](phases/fase-21.5-workflow-separation.md) | Domain separation via contracts |
| [fase-22-fp-methodology.md](phases/fase-22-fp-methodology.md) | IFPUG/NESMA compliance fix |
| [fase-23-context-engineering.md](phases/fase-23-context-engineering.md) | PIV Loop & reference-on-demand |
| [fase-23.5-confucius-orchestrator.md](phases/fase-23.5-confucius-orchestrator.md) | Central agent orchestrator |
| [fase-23.6-stage-council-review.md](phases/fase-23.6-stage-council-review.md) | Auto-review per development stage |
| [fase-29-quality-impact-mapping.md](phases/fase-29-quality-impact-mapping.md) | Quality-to-functionality linking |
| [fase-30-llm-council-improvements.md](phases/fase-30-llm-council-improvements.md) | Streaming, timeouts, tracking |
| [fase-31-cwe-security-scanners.md](phases/fase-31-cwe-security-scanners.md) | CWE Top 25 security scanning |
| [gap-phases.md](phases/gap-phases.md) | GAP Analysis Fasen 24-29 |
| [technical-debt-backlog.md](phases/technical-debt-backlog.md) | Tech debt & Falcon H1R |
