# Planned Phases (Fase 24+)

**Project:** MarQed AI Agent Software Platform
**Period:** KW5 [w158]+ (2026-01-31 onwards)
**Last Updated:** 2026-01-31 (KW5) — Fase 24 15/15 COMPLETE, Fase 41 COMPLETE (108 rules, 484 tests)
**KW-mapping:** KW = interne_week - 153 (KW6 = w159, KW7 = w160, etc.)

---

## Quick Navigation

| Document | Content |
|----------|---------|
| [ROADMAP.md](../../ROADMAP.md) | Executive summary |
| [phases-completed.md](phases-completed.md) | Completed phases (Fase 1-21) |
| [phases-current.md](phases-current.md) | Current work (KW5 [w158]) |
| **This file** | Planned work overview (Fase 22+) |
| [gap-analysis-complete-roadmap.md](gap-analysis-complete-roadmap.md) | Complete GAP analysis (75 items) |
| [tracer-bart-gap-analysis.md](tracer-bart-gap-analysis.md) | **NEW** Tracer/BART Gap Analyse (5 nieuwe fases) |
| [gap-analysis-agent-security.md](../research/gap-analysis-agent-security.md) | Agent↔Security service gap analysis (Fase 37) |
| [migration-pattern-catalog.md](migration-pattern-catalog.md) | 25 migration patterns reference |

---

## Q1 2026 Sprint Calendar (KW6-KW18)

**Beschikbaar:** ~40h/week | **Totaal Q1:** ~504 uur over 13 weken (~39h/week)

| KW | Intern | Datums | Focus |
|----|--------|--------|-------|
| **KW6-KW7** | w159-160 | 2-13 feb | Fase 42 (Adv. FN Detection) + Fase 34 (Error Detectors) |
| **KW8-KW9** | w161-162 | 16-27 feb | Fase 60 (Observability) + Fase 35 (Data Integrity) |
| **KW10-KW11** | w163-164 | 2-13 mrt | Fase 43 (Zero-Complaints) + Fase 36 start (Logic/Crypto) |
| **KW12-KW14** | w165-167 | 16 mrt - 3 apr | Fase 36 afronding + Fase 37 start (Security Integration) |
| **KW15-KW18** | w168-171 | 6-24 apr | Fase 37 afronding + Fase 32 start (Ralph Wiggum, doorloop Q2) |

**Backlog (Q2 2026+):** Fase 32 (doorloop), 33, 50, 61, 62, 63, 64, 25-28, GAP-29, 30

### Dependency Chain

```
Fase 41 ✅ ──► Fase 42 (KW6-7)
Fase 31 ✅ ──► Fase 34 (KW6-7) ──► Fase 35 (KW8-9) ──► Fase 36 (KW10-14)
Fase 23.5 ✅ ──► Fase 60 (KW8-9) ──► Fase 32 (KW15+, doorloop Q2)
Fase 23.5 ✅ ──► Fase 43 (KW10-11)
Fase 31 ✅ ──► Fase 37 (KW12-18) [34-36 nice-to-have]
```

---

## Phase Overview

### Recently Completed

| Fase | Week | Title | Status | Detail |
|------|------|-------|--------|--------|
| **20** | w128-129 | Brown Paper Enhanced | ✅ COMPLETE | [fase-20-brown-paper-enhanced.md](phases/fase-20-brown-paper-enhanced.md) |
| **21** | w143-146 | ASP Stability Analyzer | ✅ COMPLETE | [fase-21-asp-stability-analyzer.md](phases/fase-21-asp-stability-analyzer.md) |
| **21.5** | w145-146 | Workflow Separation | ✅ COMPLETE | [fase-21.5-workflow-separation.md](phases/fase-21.5-workflow-separation.md) |
| **22** | w146-147 | FP Methodology Overhaul | ✅ COMPLETE | [fase-22-fp-methodology.md](phases/fase-22-fp-methodology.md) |
| **23** | w155 | Context Engineering | ✅ COMPLETE | [fase-23-context-engineering.md](phases/fase-23-context-engineering.md) |
| **23.5** | w149-154 | Confucius Orchestrator | ✅ COMPLETE | [fase-23.5-confucius-orchestrator.md](phases/fase-23.5-confucius-orchestrator.md) |
| **29** | KW3-4 [w156-157] | Quality-Functionality Impact Mapping | ✅ COMPLETE | [fase-29-quality-impact-mapping.md](phases/fase-29-quality-impact-mapping.md) |
| **23.6** | KW4 [w157] | Stage Council Review (All Phases) | ✅ COMPLETE | [fase-23.6-stage-council-review.md](phases/fase-23.6-stage-council-review.md) |
| **31** | KW4 [w157] | CWE Security Scanner Suite | ✅ COMPLETE | [fase-31-cwe-security-scanners.md](phases/fase-31-cwe-security-scanners.md) |
| **24-A1** | KW4 [w157] | Legacy Quickscan (15-min assessment) | ✅ COMPLETE | [phases-current.md](phases-current.md#week-157-legacy-quickscan-a1-fase-24-a1--complete) |
| **41** | KW5 [w158] | Injection Vulnerability Scanners | ✅ COMPLETE | [fase-41-injection-vulnerability-scanners.md](phases/fase-41-injection-vulnerability-scanners.md) |

### Fase 24 Quick Wins - ✅ COMPLETE (KW4-5 [w157-158])

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
| **M1a** | 4.0 | CSV/Excel Export | ✅ COMPLETE | CSV + Excel (.xlsx) export via `openpyxl` (41 tests) |
| ~~**M1b**~~ | - | ~~ODS/OpenProject/LibrePlan/MS Project~~ | GESCHRAPT | Complexe XML-schema's, klein doelpubliek, hoge onderhoudskosten. OpenProject beter via API-koppeling (Fase 28). |
| **KB1** | 4.5 | Famous-Bugs Knowledge Base | ✅ COMPLETE | 32 bugs, FamousBugsLoader, KBContextProvider, API endpoints, workflow integratie (22 tests) |
| **KB2** | 5.0 | Python-Errors Patterns | ✅ MERGED | Patterns toegevoegd aan BooleanLogic/ControlFlow detectors (70% overlap) |
| **KB3** | 4.0 | Logical Errors C# Patterns | ✅ MERGED | Patterns toegevoegd aan bestaande scanners (80% overlap) |
| **KB4** | 4.0 | Logical Errors C/Python Patterns | ✅ MERGED | Patterns toegevoegd aan bestaande scanners (80% overlap) |
| **KB5** | 5.5 | Post-Mortems Knowledge Base | ✅ COMPLETE | 52 post-mortems, PostMortemsLoader, API endpoints, workflow integratie (24 tests) |

**Progress:** 15/15 items COMPLETE ✅. Alle Fase 24 Quick Wins afgerond. M1b (ODS/OpenProject/LibrePlan/MS Project) → GESCHRAPT (advies: complexe XML-schema's, klein doelpubliek, OpenProject beter via API in Fase 28)

### Unit Tests for New Services ✅ COMPLETE

**Target:** Write comprehensive unit tests for all KW5 [w158] services
**Status:** ✅ COMPLETE — 308+ tests written (exceeds 140+ target by 120%)

| Service | File | Est. Tests | Actual Tests | Status |
|---------|------|-----------|-------------|--------|
| LLM Collaboration | `llm_collaboration/*.py` | 40+ | ~80 | ✅ COMPLETE |
| SQL Analysis | `sql_analysis_service.py` | 25+ | ~65 | ✅ COMPLETE |
| Tech Radar | `tech_radar_service.py` | 20+ | ~60 | ✅ COMPLETE |
| Complexity Dashboard | `complexity_dashboard_service.py` | 30+ | ~40 | ✅ COMPLETE |
| API Inventory (extended) | `api_inventory_service.py` | 25+ | 63 | ✅ COMPLETE |

**Total delivered:** 308+ unit tests (target was 140+)

### GAP Analysis Implementation (Q2 2026+)

| Fase | Week | Title | Items | Detail |
|------|------|-------|-------|--------|
| **24** | w163-174 | GAP Quick Wins & Foundation | 15 | [gap-phases.md](phases/gap-phases.md#fase-24) |
| **25** | w175-190 | GAP Core Platform Enhancement | 18 | [gap-phases.md](phases/gap-phases.md#fase-25) |
| **26** | w191-204 | GAP AI & Automation | 12 | [gap-phases.md](phases/gap-phases.md#fase-26) |
| **27** | w205-214 | GAP Testing Excellence | 8 | [gap-phases.md](phases/gap-phases.md#fase-27) |
| **28** | w215-226 | GAP Advanced Integrations | 10 | [gap-phases.md](phases/gap-phases.md#fase-28) |
| **GAP-29** | w227-244 | GAP Innovation & Scale | 9 | [gap-phases.md](phases/gap-phases.md#fase-gap-29) |

### ✅ COMPLETE: Injection Vulnerability Scanners (Fase 41)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **41** | KW5 [w158] | **Injection Vulnerability Scanners** | 🔴 **HIGHEST** | 9.8 | [fase-41-injection-vulnerability-scanners.md](phases/fase-41-injection-vulnerability-scanners.md) |

**✅ COMPLETE:** 108 rules (79 injection + 29 auth logic), 484 tests (470 passed, 14 xfailed)

**CWE Top 25 coverage: 40% → 96%**

**Implementation status — ALL COMPLETE:**
- **Tier 1 (P0) ✅:** CWE-79 (XSS 12r), CWE-89 (SQLi 12r), CWE-78 (CMDi 8r), CWE-22 (Path 6r), CWE-502 (Deser 7r), CWE-918 (SSRF 6r) — 274 tests
- **Tier 2 (P1) ✅:** CWE-352 (CSRF 3r), CWE-434 (Upload 4r), CWE-94 (Code 5r), CWE-611 (XXE 5r), CWE-90 (LDAP 3r), CWE-943 (NoSQL 4r), CWE-1336 (SSTI 4r) — included in 274 tests
- **Tier 3 (P2) ✅:** CWE-862 (6r), CWE-863 (5r), CWE-287 (6r), CWE-269 (4r), CWE-306 (4r), CWE-20 (4r) — 123 tests
- **Fase 41B FN Hunting ✅:** 57 tests (43 pass, 14 xfail for known scanner limitations)
- **Integration Tests ✅:** 30 tests (orchestrator, multi-scanner, real-world code samples)

---

### 🟡 NEXT: Advanced False Negative Detection (KW6-KW7 [w159-160])

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **42** | KW6-KW7 [w159-160] | **Advanced FN Detection** | 🟡 **HIGH** | 8.5 | [fase-42-advanced-fn-detection.md](phases/fase-42-advanced-fn-detection.md) |

**Goal:** Reduce FN rate from **<5%** to **<2%**

---

### 🟢 Zero-Complaints Green Paper & Maintenance (KW10-KW11 [w163-164])

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **43** | KW10-KW11 [w163-164] | **Zero-Complaints Strategy** | 🟢 **HIGH** | 8.0 | [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](../plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) |

**Goal:** Reduce complaints from current baseline to **0 critical** (8 weeks), **<5% minor** (12 weeks)

**4 Strategic Pillars:**

| Pillar | Focus | Key Deliverables |
|--------|-------|------------------|
| **Preventie** | Schema hardening, input validatie | GP-001/002/003, Pydantic constraints |
| **Detectie** | Quality pre-checks, proactive scanning | QualityPrecheckService, Schema audit CI/CD |
| **Respons** | Graceful degradation, auto-retry | Fallback models, exponential backoff |
| **Feedback** | Quality metrics, user feedback | Metrics dashboard, feedback collection |

**Implementation Timeline:**

| KW [week] | Focus | Deliverables |
|------------|-------|--------------|
| KW10 [w163] | Foundation | Schema hardening (GP-001/002/003), CI/CD audit script |
| KW10 [w163] | Detection | QualityPrecheckService, proactive scanning |
| KW11 [w164] | Response | Graceful degradation, retry policies |
| KW11 [w164] | Feedback | Quality metrics endpoint, feedback system |

**Success Criteria:**

| Metric | Baseline | Target (8w) | Target (12w) |
|--------|----------|-------------|--------------|
| Critical complaints/week | 5+ | 0 | 0 |
| Minor complaints/week | 15+ | <5 | <2 |
| First-try approval rate | 60% | 85% | 95% |
| Session completion rate | 70% | 90% | 95% |
| LLM timeout rate | 15% | <5% | <2% |

**4 Detection Categories:**
- **AST Taint Tracking (KW6 [w159]):** Cross-function data flow analysis for Python/JS/Java
- **Dynamic Features (KW6-7 [w159-160]):** Detect eval(), reflection, getattr() with user input
- **Framework Plugins (KW7 [w160]):** Django, Flask, Express, Spring, Rails, Laravel, ASP.NET
- **Obfuscation Detection (KW7 [w160]):** String concat, Base64, Unicode escapes, entropy analysis

**Expected Results:**
- Cross-function FN: 2.0% → 0.5%
- Dynamic language FN: 1.25% → 0.5%
- Framework-specific FN: 1.0% → 0.2%
- Obfuscation FN: 0.5% → 0.3%

---

### Q1 2026 Phases (KW6-KW18) 🆕

| Fase | KW [week] | Title | Priority | ROI | Detail |
|------|-----------|-------|----------|-----|--------|
| **42** | KW6-KW7 [w159-160] | Advanced FN Detection | HIGH | 8.5 | [fase-42-advanced-fn-detection.md](phases/fase-42-advanced-fn-detection.md) |
| **34** | KW6-KW7 [w159-160] | Advanced Error Detectors | HIGH | 8.0 | [fase-34-advanced-error-detectors.md](phases/fase-34-advanced-error-detectors.md) |
| **60** | KW8-KW9 [w161-162] | **Observability Foundation (OTLP/Langfuse)** | 🔴 **P0** | 9.0 | [fase-60-observability-foundation.md](phases/fase-60-observability-foundation.md) |
| **35** | KW8-KW9 [w161-162] | Data Integrity Scanners | HIGH | 7.5 | [fase-35-data-integrity-scanners.md](phases/fase-35-data-integrity-scanners.md) |
| **43** | KW10-KW11 [w163-164] | **Zero-Complaints Strategy** | 🟢 HIGH | 8.0 | [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](../plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) |
| **36** | KW10-KW14 [w163-167] | Logic & Crypto Scanner | HIGH | 8.5 | [fase-36-logic-crypto-scanner.md](phases/fase-36-logic-crypto-scanner.md) |
| **37** | KW12-KW18 [w165-171] | Security Agent Integration | **CRITICAL** | 9.5 | [fase-37-security-agent-integration.md](phases/fase-37-security-agent-integration.md) |

### Q2 2026+ Phases (Backlog)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **32** | KW15+ [w168+] | Ralph Wiggum Autonomous Loop | HIGH | 8.5 | [fase-32-ralph-wiggum-loop.md](phases/fase-32-ralph-wiggum-loop.md) |
| **61** | Q2 2026 | **Progress Dashboard & Per-Ticket Cost** | **P1** | 8.0 | [fase-61-progress-dashboard.md](phases/fase-61-progress-dashboard.md) |
| **33** | Q2 2026 | DevStats Developer Metrics | MEDIUM-HIGH | 7.0 | [fase-33-devstats-dashboard.md](phases/fase-33-devstats-dashboard.md) |
| **62** | Q2 2026 | **Conversational Intake (Tracer Epic Mode)** | **P1** | 7.5 | [fase-62-conversational-intake.md](phases/fase-62-conversational-intake.md) |

### Tracer/BART Gap Analyse - Planned (Q2 2026+) 🆕

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **63** | Q2+ [w207-212] | **Statistical Drift Detection** | P2 | 7.0 | [fase-63-statistical-drift-detection.md](phases/fase-63-statistical-drift-detection.md) |
| **64** | Q3+ [w229-234] | **Self-Evolution Activation** | P3 | 7.5 | [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) |

**Source:** [Tracer/BART Gap Analyse](tracer-bart-gap-analysis.md) - 5 nieuwe fases uit OpenClaw video analyse

### 🧠 ML-Based Detection (Q2 2026+)

| Fase | Week | Title | Priority | ROI | Detail |
|------|------|-------|----------|-----|--------|
| **50** | Q2+ [w203-218] | **ML Novel Vulnerability Detection** | MEDIUM-HIGH | 7.5 | [fase-50-ml-novel-vulnerability-detection.md](phases/fase-50-ml-novel-vulnerability-detection.md) |

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

### Future Enhancements (Q3 2026+)

| Fase | Week | Title | Status | Detail |
|------|------|-------|--------|--------|
| **64** | Q3+ [w229-234] | **Self-Evolution Activation** | PLANNED | [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) |
| **30** | Q3+ [w233-235] | LLM Council Improvements | PLANNED | [fase-30-llm-council-improvements.md](phases/fase-30-llm-council-improvements.md) |
| **55** | Q3+ [w236+] | LLM-Explained Findings | FUTURE | GPT/Claude explains ML findings |
| **56** | Q4+ [w240+] | Real-time ML Inference | FUTURE | Lightweight model for in-flow scanning |

### Supporting Documentation

| Document | Content |
|----------|---------|
| [technical-debt-backlog.md](phases/technical-debt-backlog.md) | Tech debt items & Falcon H1R evaluation |

---

## Integrated Roadmap Timeline

```
t/m KW5 [w158]: CRITICAL FOUNDATION + ORCHESTRATOR + QUALITY ✅ COMPLETE
├── w143-146: Fase 21 Stability Analyzer ✅ COMPLETE
├── w145-146: Fase 21.5 Workflow Separation ✅ COMPLETE
├── w146-147: Fase 22 FP Methodology Overhaul ✅ COMPLETE
├── w149-154: Fase 23.5 Confucius Orchestrator Integration ✅ COMPLETE
├── w155: Fase 23 Context Engineering ✅ COMPLETE
├── KW3-4 [w156-157]: Fase 29 Quality-Functionality Impact Mapping ✅ COMPLETE (27 tests)
├── KW4 [w157]: Fase 23.6 Stage Council Review ✅ COMPLETE (44+ tests)
├── KW4 [w157]: Fase 31 CWE Security Scanner Suite ✅ COMPLETE (288+ findings)
└── KW4 [w157]: Fase 24-A1 Legacy Quickscan ✅ COMPLETE (23 tests)

KW4-5 [w157-158]: FASE 24 + FASE 41 ✅ COMPLETE
├── KW4 [w157]: Fase 24-K3 Secret Detection ✅ COMPLETE (50+ patterns, 18 tests)
├── KW5 [w158]: Fase 24-D1 Migration Pattern Library ✅ COMPLETE (25 patterns documented)
├── KW5 [w158]: Fase 24-D2 Database-First Pattern ✅ COMPLETE (55 tests, dual-write, validation)
├── KW5 [w158]: Fase 24-K1 OWASP Integration ✅ COMPLETE (30+ patterns, coverage reporting, 39 tests)
├── KW5 [w158]: Fase 24-K2 CVE Database Integration ✅ COMPLETE (NVD/OSV, CVSS scoring, 30 tests)
├── KW5 [w158]: Fase 24-A4 Risk Heat Map ✅ COMPLETE (D3.js format, aggregation, 30 tests)
├── KW5 [w158]: Fase 24-E1 Visual Dependency Graph ✅ COMPLETE (D3.js/Cytoscape/DOT/Mermaid, 35 tests)
├── KW5 [w158]: Fase 24-J1 Context-Aware Documentation ✅ COMPLETE (AST parsing, multi-format, 34 tests)
│
├── ✅ KW5 [w158]: Fase 41 - INJECTION VULNERABILITY SCANNERS ✅ COMPLETE (484 tests)
│   ├── Tier 1A - XSS (CWE-79) + SQL Injection (CWE-89) ✅ COMPLETE (86 tests)
│   ├── Tier 1B - CMDi (CWE-78), Path (CWE-22), Deser (CWE-502), SSRF (CWE-918) ✅ COMPLETE (78 tests)
│   ├── Tier 2A - Code (CWE-94), XXE (CWE-611), LDAP (CWE-90) ✅ COMPLETE (41 tests)
│   ├── Tier 2B - NoSQL (CWE-943), SSTI (CWE-1336), CSRF (CWE-352) ✅ COMPLETE (34 tests)
│   ├── Tier 2C - File Upload (CWE-434) ✅ COMPLETE (14 tests)
│   ├── Tier 3 - All Rules Metadata validation ✅ COMPLETE (16 tests)
│   ├── Boolean/ControlFlow detector test fixes ✅ COMPLETE (6 tests fixed)
│   ├── Tier 3A/3B - AuthLogicDetector (29 rules, 6 CWEs) ✅ COMPLETE (123 tests)
│   ├── Fase 41B - False Negative Hunting ✅ COMPLETE (57 tests, 14 xfail)
│   └── Integration Tests ✅ COMPLETE (30 tests)
│
├── w129: Fase 24-KB1 Famous-Bugs Knowledge Base ✅ COMPLETE (32 bugs, loader, API, workflow, 22 tests)
├── w129: Fase 24-KB2 Python-Errors Patterns ✅ MERGED (toegevoegd aan BooleanLogic/ControlFlow)
├── w129: Fase 24-KB3 Logical Errors C# Patterns ✅ MERGED (toegevoegd aan bestaande scanners)
├── w129: Fase 24-KB4 Logical Errors C/Python Patterns ✅ MERGED (toegevoegd aan bestaande scanners)
├── w129: Fase 24-KB5 Post-Mortems Knowledge Base ✅ COMPLETE (52 post-mortems, loader, API, workflow, 24 tests)
├── w129: Fase 24-B12 LLM Agent Collaboration ✅ COMPLETE (agent_router, context_sharing, result_aggregator)
├── w129: Fase 24-I1 API Endpoint Discovery ✅ COMPLETE (SOAP/GraphQL/gRPC toegevoegd aan api_inventory_service)
├── w129: Fase 24-F3 SQL Analysis ✅ COMPLETE (SQLAnalysisService: complexity scoring, multi-language)
└── KW4-5 [w157-158]: Fase 24 - Quick Wins & Foundation (20 items) ✅ COMPLETE (15/15 done)

Q1 2026: KW6-KW18 [w159-171] — PLANNED
├── KW6-KW7 [w159-160]: Fase 42 - Advanced FN Detection 🆕 PLANNED
├── KW6-KW7 [w159-160]: Fase 34 - Advanced Error Detectors (Deadlock + Performance) 🆕 PLANNED
│
├── ★ KW8-KW9 [w161-162]: Fase 60 - Observability Foundation (OTLP/Langfuse) 🆕 P0 [Tracer/BART]
│     └── Fundament voor Fase 32, 33, 48
├── KW8-KW9 [w161-162]: Fase 35 - Data Integrity Scanners (Race + Resource) 🆕 PLANNED
│
├── KW10-KW11 [w163-164]: Fase 43 - Zero-Complaints Green Paper & Maintenance 🆕 PLANNED
├── KW10-KW14 [w163-167]: Fase 36 - Logic & Crypto Scanner (Crypto + Control Flow + Boolean) 🆕 PLANNED
│
├── KW12-KW18 [w165-171]: Fase 37 - Security Agent Integration 🆕 CRITICAL (6 touchpoints, 130 tests)
└── KW15-KW18 [w168-171]: Fase 32 start - Ralph Wiggum Autonomous Loop (doorloop Q2) 🆕 PLANNED

Q2 2026+: BACKLOG
├── Fase 32 - Ralph Wiggum (doorloop uit Q1) 🆕 PLANNED
├── ★ Fase 61 - Progress Dashboard & Per-Ticket Cost 🆕 P1 [Tracer/BART]
│     └── Real-time voortgang per ticket, synergy met Ralph (32)
├── Fase 33 - DevStats Developer Metrics 🆕 PLANNED
├── Fase 25 - Core Platform Enhancement (18 items)
│
├── ★ Fase 62 - Conversational Intake (Tracer Epic Mode) 🆕 P1 [Tracer/BART]
│     └── Chat-based requirements → auto-ticket generatie
│
├── Fase 26 - AI & Automation (12 items)
│
├── ★ Fase 63 - Statistical Drift Detection 🆕 P2 [Tracer/BART]
│     └── Embedding-based drift naast keyword-based
│
├── Fase 27 - Testing Excellence (8 items)
├── Fase 28 - Advanced Integrations (10 items)
│
├── ★ Fase 64 - Self-Evolution Activation 🆕 P3 [Tracer/BART]
│     └── AgentEvolutionService activeren + Council Reviews
│
├── Fase 50 - ML Novel Vulnerability Detection
└── Fase GAP-29 - Innovation & Scale (9 items)
```

---

## Effort Summary

| Phase Group | Fase | Hours | KW [week] | Status |
|-------------|------|-------|-----------|--------|
| Workflow Separation | 21.5 | ~40 | t/m KW5 | ✅ COMPLETE |
| FP Methodology | 22 | ~24 | t/m KW5 | ✅ COMPLETE |
| Confucius Orchestrator | 23.5 | ~120 | t/m KW5 | ✅ COMPLETE |
| Context Engineering | 23 | ~24 | t/m KW5 | ✅ COMPLETE |
| Quality Impact Mapping | 29 | ~40 | KW3-4 | ✅ COMPLETE |
| Stage Council Review | 23.6 | ~120 | KW4 | ✅ COMPLETE |
| CWE Security Scanners | 31 | ~40 | KW4 | ✅ COMPLETE |
| Legacy Quickscan | 24-A1 | ~16 | KW4 | ✅ COMPLETE |
| **Injection Vulnerability Scanners** | 41 | ~200 | KW5 | ✅ **COMPLETE** (108 rules, 484 tests) |
| **Advanced FN Detection** | 42 | ~48 | KW6-7 | 🆕 Q1 PLANNED |
| **Advanced Error Detectors** | 34 | ~48 | KW6-7 | 🆕 Q1 PLANNED |
| **★ Observability Foundation** | 60 | ~48 | KW8-9 | 🆕 Q1 P0 [Tracer/BART] |
| **Data Integrity Scanners** | 35 | ~40 | KW8-9 | 🆕 Q1 PLANNED |
| **Zero-Complaints Strategy** | 43 | ~48 | KW10-11 | 🆕 Q1 PLANNED |
| **Logic & Crypto Scanner** | 36 | ~72 | KW10-14 | 🆕 Q1 PLANNED |
| **Security Agent Integration** | 37 | ~100 | KW12-18 | 🆕 Q1 **CRITICAL** |
| **Ralph Wiggum Loop** | 32 | ~160 | KW15+ → Q2 | 🆕 PLANNED |
| **★ Progress Dashboard** | 61 | ~64 | Q2 | 🆕 P1 [Tracer/BART] |
| **DevStats Dashboard** | 33 | ~152 | Q2 | 🆕 PLANNED |
| **★ Conversational Intake** | 62 | ~80 | Q2 | 🆕 P1 [Tracer/BART] |
| **★ Statistical Drift Detection** | 63 | ~72 | Q2+ | 🆕 P2 [Tracer/BART] |
| **★ Self-Evolution Activation** | 64 | ~80 | Q3+ | 🆕 P3 [Tracer/BART] |
| GAP Analysis (Rest) | 24-29 | ~1484 | Q2+ | 🔄 BACKLOG |
| Future | 30, 50 | ~144 | Q3+ | PLANNED |
| **Q1 2026 Totaal** | **7 fases** | **~504** | **KW6-18** | |
| **Totaal** | **23+ phases** | **~2800+** | | |

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
| [fase-41-injection-vulnerability-scanners.md](phases/fase-41-injection-vulnerability-scanners.md) | ✅ **COMPLETE** CWE Top 25 coverage 40%→96% — 108 rules, 484 tests |
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
