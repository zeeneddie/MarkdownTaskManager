# Planned Phases (Fase 24+)

**Project:** MarQed AI Agent Software Platform
**Period:** Week 158+ (2026-01-XX onwards)
**Last Updated:** 2026-01-31 (M1 opgesplitst: M1a CSV/Excel → Fase 25, M1b geschrapt)

---

## Quick Navigation

| Document | Content |
|----------|---------|
| [ROADMAP.md](../../ROADMAP.md) | Executive summary |
| [phases-completed.md](phases-completed.md) | Completed phases (Fase 1-21) |
| [phases-current.md](phases-current.md) | Current work (Week 144) |
| **This file** | Planned work overview (Fase 22+) |
| [gap-analysis-complete-roadmap.md](gap-analysis-complete-roadmap.md) | Complete GAP analysis (75 items) |
| [tracer-bart-gap-analysis.md](tracer-bart-gap-analysis.md) | **NEW** Tracer/BART Gap Analyse (5 nieuwe fases) |
| [gap-analysis-agent-security.md](../research/gap-analysis-agent-security.md) | Agent↔Security service gap analysis (Fase 37) |
| [migration-pattern-catalog.md](migration-pattern-catalog.md) | 25 migration patterns reference |

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
| **31** | 157 | CWE Security Scanner Suite | ✅ COMPLETE | [fase-31-cwe-security-scanners.md](phases/fase-31-cwe-security-scanners.md) |
| **24-A1** | 157 | Legacy Quickscan (15-min assessment) | ✅ COMPLETE | [phases-current.md](phases-current.md#week-157-legacy-quickscan-a1-fase-24-a1--complete) |

### Fase 24 Quick Wins - In Progress (Week 157-174)

| Item | ROI | Title | Status | Description |
|------|-----|-------|--------|-------------|
| **A1** | 8.0 | Legacy Quickscan | ✅ COMPLETE | 15-min automated assessment, Go/No-Go |
| **K3** | 8.0 | Secret Detection | ✅ COMPLETE | 50+ patterns, entropy detection, false positive filter |
| **D1** | 7.5 | Migration Pattern Library | ✅ COMPLETE | [25 patterns documented](migration-pattern-catalog.md) |
| **D2** | 7.5 | Database-First Pattern | ✅ COMPLETE | Schema-first migration, dual-write, validation (55 tests) |
| **K1** | 6.7 | OWASP Integration | ✅ COMPLETE | 30+ patterns, all 10 OWASP categories, coverage reporting (39 tests) |
| **K2** | 6.0 | CVE Database Integration | ✅ COMPLETE | NVD/OSV integration, CVSS scoring, dependency parsing (30 tests) |
| **A4** | 6.0 | Risk Heat Map | ✅ COMPLETE | RiskHeatMapService, D3.js format, severity aggregation (30 tests) |
| **E1** | 5.3 | Visual Dependency Graph | ✅ COMPLETE | D3.js/Cytoscape/DOT/Mermaid export, clustering (35 tests) |
| **J1** | 5.3 | Context-Aware Documentation | ✅ COMPLETE | AST parsing, docstring extraction, multi-format (34 tests) |
| **B12** | 5.0 | LLM Agent Collaboration | ✅ COMPLETE | Multi-agent framework: agent_router, context_sharing, result_aggregator (4 modules) |
| **I1** | 4.5 | API Endpoint Discovery | ✅ COMPLETE | Extended api_inventory_service with SOAP/GraphQL/gRPC detection |
| **F3** | 4.0 | SQL Analysis (Basic) | ✅ COMPLETE | SQLAnalysisService: complexity scoring, multi-language extraction |
| **A3** | 3.7 | Technology Radar | ✅ COMPLETE | TechRadarService: EOL database, risk assessment, upgrade recommendations |
| **A5** | 3.5 | Complexity Dashboard | ✅ COMPLETE | ComplexityDashboardService: module-level aggregation, trend tracking, hotspot identification |
| **M1a** | 4.0 | CSV/Excel Export | PLANNED | CSV + Excel (.xlsx) export via `openpyxl`. Dekt 80% use cases. Meeliften met Fase 25. ~4-8h |
| ~~**M1b**~~ | - | ~~ODS/OpenProject/LibrePlan/MS Project~~ | GESCHRAPT | Complexe XML-schema's, klein doelpubliek, hoge onderhoudskosten. OpenProject beter via API-koppeling (Fase 28). |
| **KB1** | 4.5 | Famous-Bugs Knowledge Base | ✅ READY | ChromaDB collectie + API toegevoegd aan chroma_service.py - data loading pending |
| **KB2** | 5.0 | Python-Errors Patterns | ✅ MERGED | Patterns toegevoegd aan BooleanLogic/ControlFlow detectors (70% overlap) |
| **KB3** | 4.0 | Logical Errors C# Patterns | ✅ MERGED | Patterns toegevoegd aan bestaande scanners (80% overlap) |
| **KB4** | 4.0 | Logical Errors C/Python Patterns | ✅ MERGED | Patterns toegevoegd aan bestaande scanners (80% overlap) |
| **KB5** | 5.5 | Post-Mortems Knowledge Base | ✅ READY | ChromaDB collectie + API toegevoegd aan chroma_service.py - data loading pending |

**Progress:** 14/15 items COMPLETE. M1 opgesplitst: M1a (CSV/Excel) → Fase 25, M1b (ODS/OpenProject/LibrePlan/MS Project) → GESCHRAPT (Week 162 advies: complexe XML-schema's, klein doelpubliek, OpenProject beter via API in Fase 28)

### Unit Tests for New Services ✅ COMPLETE

**Target:** Write comprehensive unit tests for all Week 158 services
**Status:** ✅ COMPLETE — 308+ tests written (exceeds 140+ target by 120%)

| Service | File | Est. Tests | Actual Tests | Status |
|---------|------|-----------|-------------|--------|
| LLM Collaboration | `llm_collaboration/*.py` | 40+ | ~80 | ✅ COMPLETE |
| SQL Analysis | `sql_analysis_service.py` | 25+ | ~65 | ✅ COMPLETE |
| Tech Radar | `tech_radar_service.py` | 20+ | ~60 | ✅ COMPLETE |
| Complexity Dashboard | `complexity_dashboard_service.py` | 30+ | ~40 | ✅ COMPLETE |
| API Inventory (extended) | `api_inventory_service.py` | 25+ | 63 | ✅ COMPLETE |

**Total delivered:** 308+ unit tests (target was 140+)

### GAP Analysis Implementation (Week 163-244)

| Fase | Week | Title | Items | Detail |
|------|------|-------|-------|--------|
| **24** | 163-174 | GAP Quick Wins & Foundation | 15 | [gap-phases.md](phases/gap-phases.md#fase-24) |
| **25** | 175-190 | GAP Core Platform Enhancement | 18 | [gap-phases.md](phases/gap-phases.md#fase-25) |
| **26** | 191-204 | GAP AI & Automation | 12 | [gap-phases.md](phases/gap-phases.md#fase-26) |
| **27** | 205-214 | GAP Testing Excellence | 8 | [gap-phases.md](phases/gap-phases.md#fase-27) |
| **28** | 215-226 | GAP Advanced Integrations | 10 | [gap-phases.md](phases/gap-phases.md#fase-28) |
| **GAP-29** | 227-244 | GAP Innovation & Scale | 9 | [gap-phases.md](phases/gap-phases.md#fase-gap-29) |

### 🔴 NEXT: Injection Vulnerability Scanners (Week 159-168)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **41** | 159-168 | **Injection Vulnerability Scanners** | 🔴 **HIGHEST** | 9.8 | [fase-41-injection-vulnerability-scanners.md](phases/fase-41-injection-vulnerability-scanners.md) |

**Critical Gap:** CWE Top 25 coverage currently at 40%. After Fase 41: **96%**

**23 Missing CWEs to implement:**
- **Tier 1 (P0):** CWE-79 (XSS), CWE-89 (SQLi), CWE-78 (CMDi), CWE-22 (Path), CWE-502 (Deser), CWE-918 (SSRF)
- **Tier 2 (P1):** CWE-352 (CSRF), CWE-434 (Upload), CWE-94 (Code), CWE-77 (Cmd), CWE-611 (XXE), CWE-90 (LDAP), CWE-943 (NoSQL), CWE-1336 (SSTI)
- **Tier 3 (P2):** CWE-862, CWE-863, CWE-287, CWE-269, CWE-20, CWE-306, CWE-643, CWE-113, CWE-917

**Fase 41B: Iterative False Negative Cycle (included):**
- Week 161, 164, 167: False negative hunting after each tier
- Week 166: FNRemediationDetector (taint analysis scanner)
- Week 168: Final FN hunt + stabilization
- Target: False negative rate from ~30% → **<5%**

---

### 🟡 THEN: Advanced False Negative Detection (Week 169-176)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **42** | 169-176 | **Advanced FN Detection** | 🟡 **HIGH** | 8.5 | [fase-42-advanced-fn-detection.md](phases/fase-42-advanced-fn-detection.md) |

**Goal:** Reduce FN rate from **<5%** to **<2%**

---

### 🟢 NEW: Zero-Complaints Green Paper & Maintenance (Week 177-184)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **43** | 177-184 | **Zero-Complaints Strategy** | 🟢 **HIGH** | 8.0 | [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](../plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) |

**Goal:** Reduce complaints from current baseline to **0 critical** (8 weeks), **<5% minor** (12 weeks)

**4 Strategic Pillars:**

| Pillar | Focus | Key Deliverables |
|--------|-------|------------------|
| **Preventie** | Schema hardening, input validatie | GP-001/002/003, Pydantic constraints |
| **Detectie** | Quality pre-checks, proactive scanning | QualityPrecheckService, Schema audit CI/CD |
| **Respons** | Graceful degradation, auto-retry | Fallback models, exponential backoff |
| **Feedback** | Quality metrics, user feedback | Metrics dashboard, feedback collection |

**Implementation Timeline:**

| Week | Focus | Deliverables |
|------|-------|--------------|
| 177-178 | Foundation | Schema hardening (GP-001/002/003), CI/CD audit script |
| 179-180 | Detection | QualityPrecheckService, proactive scanning |
| 181-182 | Response | Graceful degradation, retry policies |
| 183-184 | Feedback | Quality metrics endpoint, feedback system |

**Success Criteria:**

| Metric | Baseline | Target (8w) | Target (12w) |
|--------|----------|-------------|--------------|
| Critical complaints/week | 5+ | 0 | 0 |
| Minor complaints/week | 15+ | <5 | <2 |
| First-try approval rate | 60% | 85% | 95% |
| Session completion rate | 70% | 90% | 95% |
| LLM timeout rate | 15% | <5% | <2% |

**4 Detection Categories:**
- **AST Taint Tracking (Week 169-172):** Cross-function data flow analysis for Python/JS/Java
- **Dynamic Features (Week 170-172):** Detect eval(), reflection, getattr() with user input
- **Framework Plugins (Week 173-175):** Django, Flask, Express, Spring, Rails, Laravel, ASP.NET
- **Obfuscation Detection (Week 175-176):** String concat, Base64, Unicode escapes, entropy analysis

**Expected Results:**
- Cross-function FN: 2.0% → 0.5%
- Dynamic language FN: 1.25% → 0.5%
- Framework-specific FN: 1.0% → 0.2%
- Obfuscation FN: 0.5% → 0.3%

---

### New Phases (Week 177-202) 🆕

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **34** | 177-181 | Advanced Error Detectors | HIGH | 8.0 | [fase-34-advanced-error-detectors.md](phases/fase-34-advanced-error-detectors.md) |
| **35** | 181-185 | Data Integrity Scanners | HIGH | 7.5 | [fase-35-data-integrity-scanners.md](phases/fase-35-data-integrity-scanners.md) |
| **43** | 177-184 | **Zero-Complaints Strategy** | 🟢 HIGH | 8.0 | [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](../plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) |
| **60** | 179-182 | **Observability Foundation (OTLP/Langfuse)** | 🔴 **P0** | 9.0 | [fase-60-observability-foundation.md](phases/fase-60-observability-foundation.md) |
| **61** | 183-188 | **Progress Dashboard & Per-Ticket Cost** | **P1** | 8.0 | [fase-61-progress-dashboard.md](phases/fase-61-progress-dashboard.md) |
| **36** | 186-192 | Logic & Crypto Scanner | HIGH | 8.5 | [fase-36-logic-crypto-scanner.md](phases/fase-36-logic-crypto-scanner.md) |
| **37** | 195-202 | Security Agent Integration | **CRITICAL** | 9.5 | [fase-37-security-agent-integration.md](phases/fase-37-security-agent-integration.md) |
| **32** | 183-188 | Ralph Wiggum Autonomous Loop | HIGH | 8.5 | [fase-32-ralph-wiggum-loop.md](phases/fase-32-ralph-wiggum-loop.md) |
| **33** | 189-194 | DevStats Developer Metrics | MEDIUM-HIGH | 7.0 | [fase-33-devstats-dashboard.md](phases/fase-33-devstats-dashboard.md) |
| **62** | 193-198 | **Conversational Intake (Tracer Epic Mode)** | **P1** | 7.5 | [fase-62-conversational-intake.md](phases/fase-62-conversational-intake.md) |

### Tracer/BART Gap Analyse - Planned (Week 207-234) 🆕

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **63** | 207-212 | **Statistical Drift Detection** | P2 | 7.0 | [fase-63-statistical-drift-detection.md](phases/fase-63-statistical-drift-detection.md) |
| **64** | 229-234 | **Self-Evolution Activation** | P3 | 7.5 | [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) |

**Source:** [Tracer/BART Gap Analyse](tracer-bart-gap-analysis.md) - 5 nieuwe fases uit OpenClaw video analyse

### 🧠 ML-Based Detection (Week 203-218)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **50** | 203-218 | **ML Novel Vulnerability Detection** | MEDIUM-HIGH | 7.5 | [fase-50-ml-novel-vulnerability-detection.md](phases/fase-50-ml-novel-vulnerability-detection.md) |

**Doel:** Detecteer de laatste 0.25% "novel patterns" (zero-days) die regex niet kan vangen.

**Architectuur:** NIET in scan flow, maar als **separate learning pipeline**:
- **Continuous Learning**: GitHub crawler + CVE monitor → train modellen 24/7
- **Batch Analysis**: Nightly scan van hele codebase met ML → pre-computed findings
- **Integration**: Orchestrator merged SAST + ML findings (geen performance impact)

**Key Components:**
- CodeBERT encoder voor code embeddings
- Autoencoder voor anomaly detection
- FAISS index voor similarity search tegen known vulnerabilities
- Feedback loop voor continuous improvement

**Expected Results:** FN rate van 2% → 1% (50% reductie van resterende gaps)

---

### Future Enhancements (Week 229+)

| Fase | Week | Title | Status | Detail |
|------|------|-------|--------|--------|
| **64** | 229-234 | **Self-Evolution Activation** | PLANNED | [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) |
| **30** | 233-235 | LLM Council Improvements | PLANNED | [fase-30-llm-council-improvements.md](phases/fase-30-llm-council-improvements.md) |
| **55** | 236+ | LLM-Explained Findings | FUTURE | GPT/Claude explains ML findings |
| **56** | 240+ | Real-time ML Inference | FUTURE | Lightweight model for in-flow scanning |

### Supporting Documentation

| Document | Content |
|----------|---------|
| [technical-debt-backlog.md](phases/technical-debt-backlog.md) | Tech debt items & Falcon H1R evaluation |

---

## Integrated Roadmap Timeline

```
WEEK 144-157: CRITICAL FOUNDATION + ORCHESTRATOR + QUALITY ✅ COMPLETE
├── Week 143-146: Fase 21 Stability Analyzer ✅ COMPLETE
├── Week 145-146: Fase 21.5 Workflow Separation ✅ COMPLETE
├── Week 146-147: Fase 22 FP Methodology Overhaul ✅ COMPLETE
├── Week 149-154: Fase 23.5 Confucius Orchestrator Integration ✅ COMPLETE
├── Week 155: Fase 23 Context Engineering ✅ COMPLETE
├── Week 156-157: Fase 29 Quality-Functionality Impact Mapping ✅ COMPLETE (27 tests)
├── Week 157: Fase 23.6 Stage Council Review ✅ COMPLETE (44+ tests)
├── Week 157: Fase 31 CWE Security Scanner Suite ✅ COMPLETE (288+ findings)
└── Week 157: Fase 24-A1 Legacy Quickscan ✅ COMPLETE (23 tests)

WEEK 157-244: GAP ANALYSIS IMPLEMENTATION (IN PROGRESS)
├── Week 157: Fase 24-K3 Secret Detection ✅ COMPLETE (50+ patterns, 18 tests)
├── Week 158: Fase 24-D1 Migration Pattern Library ✅ COMPLETE (25 patterns documented)
├── Week 158: Fase 24-D2 Database-First Pattern ✅ COMPLETE (55 tests, dual-write, validation)
├── Week 158: Fase 24-K1 OWASP Integration ✅ COMPLETE (30+ patterns, coverage reporting, 39 tests)
├── Week 158: Fase 24-K2 CVE Database Integration ✅ COMPLETE (NVD/OSV, CVSS scoring, 30 tests)
├── Week 158: Fase 24-A4 Risk Heat Map ✅ COMPLETE (D3.js format, aggregation, 30 tests)
├── Week 158: Fase 24-E1 Visual Dependency Graph ✅ COMPLETE (D3.js/Cytoscape/DOT/Mermaid, 35 tests)
├── Week 158: Fase 24-J1 Context-Aware Documentation ✅ COMPLETE (AST parsing, multi-format, 34 tests)
│
├── 🔴 Week 159-166: Fase 41 - INJECTION VULNERABILITY SCANNERS 🆕 HIGHEST PRIORITY
│   ├── Week 159: Tier 1A - XSS (CWE-79) + SQL Injection (CWE-89)
│   ├── Week 160: Tier 1B - CMDi (CWE-78), Path (CWE-22), Deser (CWE-502), SSRF (CWE-918)
│   ├── Week 161: Tier 2A - Code (CWE-94), XXE (CWE-611), LDAP (CWE-90)
│   ├── Week 162: Tier 2B - NoSQL (CWE-943), SSTI (CWE-1336), CSRF (CWE-352)
│   ├── Week 163: Tier 2C - File Upload (CWE-434), Command (CWE-77)
│   ├── Week 164: Tier 3A - Auth logic (CWE-862, CWE-863, CWE-287)
│   ├── Week 165: Tier 3B - Privilege (CWE-269, CWE-20, CWE-306)
│   └── Week 166: Integration + Testing
│
├── Week 129: Fase 24-KB1 Famous-Bugs Knowledge Base ✅ READY (collectie + API in chroma_service.py)
├── Week 129: Fase 24-KB2 Python-Errors Patterns ✅ MERGED (toegevoegd aan BooleanLogic/ControlFlow)
├── Week 129: Fase 24-KB3 Logical Errors C# Patterns ✅ MERGED (toegevoegd aan bestaande scanners)
├── Week 129: Fase 24-KB4 Logical Errors C/Python Patterns ✅ MERGED (toegevoegd aan bestaande scanners)
├── Week 129: Fase 24-KB5 Post-Mortems Knowledge Base ✅ READY (collectie + API in chroma_service.py)
├── Week 129: Fase 24-B12 LLM Agent Collaboration ✅ COMPLETE (agent_router, context_sharing, result_aggregator)
├── Week 129: Fase 24-I1 API Endpoint Discovery ✅ COMPLETE (SOAP/GraphQL/gRPC toegevoegd aan api_inventory_service)
├── Week 129: Fase 24-F3 SQL Analysis ✅ COMPLETE (SQLAnalysisService: complexity scoring, multi-language)
├── Week 157-174: Fase 24 - Quick Wins & Foundation (20 items) 🔄 IN PROGRESS (12/20 done)
├── Week 167-171: Fase 34 - Advanced Error Detectors (Deadlock + Performance) 🆕 PLANNED
├── Week 171-175: Fase 35 - Data Integrity Scanners (Race + Resource) 🆕 PLANNED
├── Week 176-182: Fase 36 - Logic & Crypto Scanner (Crypto + Control Flow + Boolean) 🆕 PLANNED
├── Week 177-184: Fase 43 - Zero-Complaints Green Paper & Maintenance 🆕 PLANNED
│
├── ★ Week 179-182: Fase 60 - Observability Foundation (OTLP/Langfuse) 🆕 P0 [Tracer/BART]
│     └── Fundament voor Fase 32, 33, 48
│
├── Week 183-188: Fase 32 - Ralph Wiggum Autonomous Loop 🆕 PLANNED
├── ★ Week 183-188: Fase 61 - Progress Dashboard & Per-Ticket Cost 🆕 P1 [Tracer/BART]
│     └── Real-time voortgang per ticket, synergy met Ralph (32)
│
├── Week 185-192: Fase 37 - Security Agent Integration 🆕 CRITICAL (6 touchpoints, 130 tests)
├── Week 187-192: Fase 33 - DevStats Developer Metrics 🆕 PLANNED
├── Week 185-200: Fase 25 - Core Platform Enhancement (18 items)
│
├── ★ Week 193-198: Fase 62 - Conversational Intake (Tracer Epic Mode) 🆕 P1 [Tracer/BART]
│     └── Chat-based requirements → auto-ticket generatie
│
├── Week 201-214: Fase 26 - AI & Automation (12 items)
│
├── ★ Week 207-212: Fase 63 - Statistical Drift Detection 🆕 P2 [Tracer/BART]
│     └── Embedding-based drift naast keyword-based
│
├── Week 215-224: Fase 27 - Testing Excellence (8 items)
├── Week 225-236: Fase 28 - Advanced Integrations (10 items)
│
├── ★ Week 229-234: Fase 64 - Self-Evolution Activation 🆕 P3 [Tracer/BART]
│     └── AgentEvolutionService activeren + Council Reviews
│
└── Week 237-254: Fase GAP-29 - Innovation & Scale (9 items)
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
| CWE Security Scanners | 31 | ~40 | 1 | ✅ COMPLETE |
| Legacy Quickscan | 24-A1 | ~16 | 1 | ✅ COMPLETE |
| **🔴 Injection Vulnerability Scanners** | 41 | ~200 | 8 | 🔴 **NEXT** |
| **Advanced Error Detectors** | 34 | ~48 | 5 | 🆕 PLANNED |
| **Data Integrity Scanners** | 35 | ~40 | 5 | 🆕 PLANNED |
| **Logic & Crypto Scanner** | 36 | ~72 | 7 | 🆕 PLANNED |
| **Security Agent Integration** | 37 | ~100 | 8 | 🆕 **CRITICAL** |
| **Ralph Wiggum Loop** | 32 | ~160 | 5 | 🆕 PLANNED |
| **DevStats Dashboard** | 33 | ~152 | 5 | 🆕 PLANNED |
| **★ Observability Foundation** | 47 | ~48 | 4 | 🆕 P0 [Tracer/BART] |
| **★ Progress Dashboard** | 48 | ~64 | 5 | 🆕 P1 [Tracer/BART] |
| **★ Conversational Intake** | 49 | ~80 | 5 | 🆕 P1 [Tracer/BART] |
| **★ Statistical Drift Detection** | 52 | ~72 | 5 | 🆕 P2 [Tracer/BART] |
| **★ Self-Evolution Activation** | 53 | ~80 | 5 | 🆕 P3 [Tracer/BART] |
| GAP Analysis (Rest) | 24-29 | ~1484 | 80 | 🔄 IN PROGRESS |
| Future | 30 | 72 | 2 | PLANNED |
| **Total** | **23 phases** | **~2736** | **~142** | |

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
                   └────────┬────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│    Fase 31      │                   │   Fase 24-A1    │
│ CWE Security    │                   │ Legacy Quickscan│
│   ✅ COMPLETE   │◄──────────────────│   ✅ COMPLETE   │
└────────┬────────┘  (uses security)  └────────┬────────┘
         │                                     │
         ├─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│    Fase 37      │
│ Security Agent  │◄───── 6 workflow touchpoints
│ Integration     │       (Quinn, Brown/Green Paper,
│   🆕 CRITICAL   │        Kanban, Maintenance, Migration)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Fase 24       │
│ Quick Wins (K3) │
│   🔄 NEXT       │
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
| [fase-32-ralph-wiggum-loop.md](phases/fase-32-ralph-wiggum-loop.md) | 🆕 Ralph Wiggum autonomous coding loop |
| [fase-33-devstats-dashboard.md](phases/fase-33-devstats-dashboard.md) | 🆕 DevStats developer metrics dashboard |
| [fase-34-advanced-error-detectors.md](phases/fase-34-advanced-error-detectors.md) | 🆕 Deadlock + Performance pattern detection |
| [fase-35-data-integrity-scanners.md](phases/fase-35-data-integrity-scanners.md) | 🆕 Race condition + Resource lifecycle detection |
| [fase-36-logic-crypto-scanner.md](phases/fase-36-logic-crypto-scanner.md) | 🆕 Crypto + Control flow + Boolean logic detection |
| [fase-37-security-agent-integration.md](phases/fase-37-security-agent-integration.md) | 🆕 **CRITICAL** SecurityScanOrchestrator → Agent workflows (6 touchpoints) |
| [fase-41-injection-vulnerability-scanners.md](phases/fase-41-injection-vulnerability-scanners.md) | 🔴 **HIGHEST** Complete CWE Top 25 coverage - 23 missing CWEs (XSS, SQLi, CMDi, etc.) |
| [fase-24-kb-knowledge-base-integration.md](phases/fase-24-kb-knowledge-base-integration.md) | 🆕 KB1-KB5 Knowledge Base ChromaDB integration |
| [fase-43-zero-complaints-strategy.md](../plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) | 🆕 Zero-Complaints Green Paper & Maintenance (4 pillars, 8 weken) |
| [fase-60-observability-foundation.md](phases/fase-60-observability-foundation.md) | ★ **P0** OTLP/Langfuse integratie, CCTrace → OTLP spans [Tracer/BART] |
| [fase-61-progress-dashboard.md](phases/fase-61-progress-dashboard.md) | ★ **P1** Real-time per-ticket voortgangsdashboard [Tracer/BART] |
| [fase-62-conversational-intake.md](phases/fase-62-conversational-intake.md) | ★ **P1** Chat-based requirements → auto-ticket generatie (Tracer Epic Mode) [Tracer/BART] |
| [fase-63-statistical-drift-detection.md](phases/fase-63-statistical-drift-detection.md) | ★ **P2** Embedding-based drift detectie (Arize Phoenix) [Tracer/BART] |
| [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) | ★ **P3** AgentEvolutionService activeren + Stage Council Reviews [Tracer/BART] |
| [tracer-bart-gap-analysis.md](tracer-bart-gap-analysis.md) | ★ Tracer/BART vs MarQed Gap Analyse & Verbeterplan (master doc) |
| [gap-phases.md](phases/gap-phases.md) | GAP Analysis Fasen 24-29 |
| [technical-debt-backlog.md](phases/technical-debt-backlog.md) | Tech debt & Falcon H1R |
