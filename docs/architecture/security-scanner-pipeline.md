# Security Scanner Pipeline Architecture

**Status:** COMPLETE (Fase 31, 41, 42) + PLANNED (Fase 34-40)
**Parent:** [Platform Architecture](../unified-architecture-diagram.md)
**Datum:** 2026-02-01

---

## Overzicht

De Security Scanner Pipeline is een meerlaags detectiesysteem dat broncode analyseert op kwetsbaarheden, gebaseerd op CWE Top 25 en OWASP Top 10 standaarden.

```
Source Code
    │
    v
+-------------------+     +-------------------+     +-------------------+
| LAAG 1            |     | LAAG 2            |     | LAAG 3            |
| CWE Scanner Suite | ──► | Injection         | ──► | False Negative    |
| (Fase 31)         |     | Scanners (F41)    |     | Detection (F42)   |
|                   |     |                   |     |                   |
| OpenGrep          |     | 13 categorieën    |     | AST Taint Track   |
| Bandit            |     | 79 regels         |     | 4 scanners        |
| Trivy             |     | 484 tests         |     | 468 tests         |
| Custom ASP        |     | 96% Top 25        |     | FN: 5% → <2%     |
+-------------------+     +-------------------+     +-------------------+
    │
    v
+-------------------+
| Security Report   |
| - Vulnerabilities |
| - CWE IDs         |
| - CVSS Severity   |
| - Remediation     |
+-------------------+
```

---

## Laag 1: CWE Scanner Suite (Fase 31)

**Status:** COMPLETE (Week 157)

De basis security scanner die meerdere tools orkestreert voor brede dekking.

### Componenten

| Component | Functie | Dekking |
|-----------|---------|---------|
| **SecurityOrchestrator** | Coördineert alle scanners, aggregeert resultaten | Centraal |
| **OpenGrep** | Pattern-based vulnerability detection | CWE patterns |
| **Bandit** | Python-specifieke security linting | Python code |
| **Trivy** | Dependency vulnerability scanning | Dependencies |
| **Custom ASP Scanner** | ASP.NET-specifieke kwetsbaarheden | .NET legacy |

### CWE Dekking

- **28/35 CWE's** uit SANS + 2019 Top 25 (80%)
- **4/10 OWASP** Top 10 categorieën
- Totaal: 288 findings bij eerste scan op HCI-CRS project

→ Specificatie: [fase-31-cwe-security-scanners.md](../roadmap/phases/fase-31-cwe-security-scanners.md)

---

## Laag 2: Injection Vulnerability Scanners (Fase 41)

**Status:** COMPLETE (Week 158)

Gespecialiseerde detectie voor injectie-kwetsbaarheden met 13 categorieën en 96% Top 25 CWE dekking.

### Scanner Categorieën

| # | Categorie | CWE | Regels | Tests |
|---|-----------|-----|--------|-------|
| 1 | XSS (Cross-Site Scripting) | CWE-79 | 8 | 40+ |
| 2 | SQL Injection | CWE-89 | 7 | 40+ |
| 3 | Command Injection | CWE-78 | 6 | 30+ |
| 4 | Path Traversal | CWE-22 | 5 | 30+ |
| 5 | Deserialization | CWE-502 | 5 | 25+ |
| 6 | SSRF | CWE-918 | 5 | 25+ |
| 7 | Code Injection | CWE-94 | 6 | 30+ |
| 8 | XXE | CWE-611 | 4 | 20+ |
| 9 | LDAP Injection | CWE-90 | 4 | 20+ |
| 10 | NoSQL Injection | CWE-943 | 5 | 25+ |
| 11 | SSTI | CWE-1336 | 5 | 25+ |
| 12 | CSRF | CWE-352 | 4 | 20+ |
| 13 | Upload Vulnerabilities | CWE-434 | 5 | 25+ |

### Architectuur

```
InjectionDetector (274 tests)
    ├── PatternMatcher (regex-based detection)
    ├── ContextAnalyzer (taint source → sink tracking)
    └── SeverityClassifier (CVSS scoring)

AuthLogicDetector (123 tests)
    ├── AuthBypassDetector
    ├── PrivilegeEscalationDetector
    └── SessionFixationDetector

False Negative Hunting (57 tests)
Integration Tests (30 tests)
```

→ Specificatie: [fase-41-injection-vulnerability-scanners.md](../roadmap/phases/fase-41-injection-vulnerability-scanners.md)

---

## Laag 3: Advanced False Negative Detection (Fase 42)

**Status:** COMPLETE (Week 159-160)

Reduceert ongedetecteerde kwetsbaarheden (false negatives) van 5% naar <2% via AST-gebaseerde taint tracking.

### 4 Scanners

| Scanner | Functie | Techniek |
|---------|---------|----------|
| **AST Taint Tracker** | Data flow analyse source → sink | Abstract Syntax Tree walking |
| **Inter-Procedural Analyzer** | Cross-functie taint propagatie | Call graph construction |
| **Sanitizer Validator** | Verifieert of sanitizers correct zijn | Pattern + semantic check |
| **Context-Sensitive Detector** | Context-afhankelijke kwetsbaarheden | Scope-aware analysis |

### Impact

| Metric | Voor | Na |
|--------|------|-----|
| False Negative Rate | 5% | <2% |
| Detection Confidence | Medium | High |
| CWE Top 25 Coverage | 80% | 96% |

→ Specificatie: [fase-42-advanced-fn-detection.md](../roadmap/phases/fase-42-advanced-fn-detection.md)

---

## Geplande Uitbreidingen

### Fase 34: Advanced Error Detectors (KW6-7)

| Detector | Doelstelling |
|----------|-------------|
| **Deadlock Detector** | Concurrent lock ordering analyse |
| **Performance Pattern Detector** | N+1 queries, memory leaks, hot loops |

→ Specificatie: [fase-34-advanced-error-detectors.md](../roadmap/phases/fase-34-advanced-error-detectors.md)

### Fase 35: Data Integrity Scanners (KW8-9)

| Scanner | Doelstelling |
|---------|-------------|
| **Race Condition Detector** | TOCTOU, shared state concurrency |
| **Resource Lifecycle Scanner** | Open/close matching, leak detection |

→ Specificatie: [fase-35-data-integrity-scanners.md](../roadmap/phases/fase-35-data-integrity-scanners.md)

### Fase 36: Logic & Crypto Scanner (KW10-14)

| Scanner | Doelstelling |
|---------|-------------|
| **Crypto Scanner** | Weak algorithms, hardcoded keys, improper IV |
| **Control Flow Scanner** | Unreachable code, infinite loops |
| **Boolean Logic Scanner** | Tautologies, contradictions |

→ Specificatie: [fase-36-logic-crypto-scanner.md](../roadmap/phases/fase-36-logic-crypto-scanner.md)

### Fase 37: Security Agent Integration (KW12-18)

Integreert alle scanners in de agent workflows via 6 touchpoints:
1. Pre-commit hook
2. PR review gate
3. Workflow fase integration
4. Dashboard reporting
5. Compliance mapping
6. Continuous monitoring

→ Specificatie: [fase-37-security-agent-integration.md](../roadmap/phases/fase-37-security-agent-integration.md)

### Fase 38-40: Advanced (Post-37)

| Fase | Focus |
|------|-------|
| **38** | Memory Safety Scanner (buffer overflow, concurrency) |
| **39** | ML-Based Novel Vulnerability Detection |
| **40** | Hybrid False Positive Reduction (regex + AST + semantic) |

---

## Integratie met Quality Harness (Fase 32E)

De security scanner pipeline wordt aangeroepen als onderdeel van de QA Gate:

```
QA Gate
    ├── Code Quality Check (pylint ≥ 7.0)
    ├── SECURITY CHECK ◄── Security Scanner Pipeline
    │       ├── bandit scan
    │       ├── Credential pattern detection
    │       ├── SQL injection patterns
    │       └── safety dependency audit
    │       HARD STOP op HIGH/CRITICAL findings
    ├── Tests + Coverage (≥ 80%)
    ├── Performance Check
    ├── Contract Verification
    ├── Dependency Impact
    └── Dead Code Check
```

→ Zie: [Quality Harness Pipeline](quality-harness-pipeline.md)

---

*Week 162 (2026-02-01)*
*Status: Fase 31 ✅ | Fase 41 ✅ | Fase 42 ✅ | Fase 34-40 PLANNED*
