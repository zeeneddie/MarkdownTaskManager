# CWE Coverage Matrix - Complete Analysis

**Doel:** Overzicht van alle CWE detectie capaciteit in MarQed
**Datum:** 2026-01-16
**Status:** Research Document

---

## Executive Summary

| Metric | Huidig (Fase 31) | Na Fase 34-36 | Totaal |
|--------|------------------|---------------|--------|
| **Unieke CWEs** | 150+ | +31 | 180+ |
| **Scanners** | 12 | +6 modules | 18 |
| **Talen** | 30+ | +0 (uitbreiding bestaande) | 30+ |
| **CWE Top 25** | 100% | 100% | 100% |
| **OWASP Top 10** | 100% | 100% | 100% |

---

## 1. HUIDIGE SCANNER DEKKING (Fase 31)

### 1.1 Scanner Overzicht

| Scanner | Type | Talen | CWEs | Bron |
|---------|------|-------|------|------|
| **OpenGrep** | External | 30+ (agnostisch) | 100+ | OpenGrep/Semgrep rules |
| **Bandit** | External | Python | 69 | Python-specific |
| **Gosec** | External | Go | 37 | Go-specific |
| **Trivy** | External | Dependencies | CVE-based | NVD/OSV |
| **Secret Scanner** | Custom | Agnostisch | 1 (CWE-798) | Pattern matching |
| **OWASP Scanner** | Custom | Multi (12) | 130+ | OWASP mapping |
| **Generic Scanner** | Custom | Multi (12) | 8 | Cross-language |
| **ASP Scanner** | Custom | Classic ASP | 13 | ASP-specific |
| **CVE Scanner** | Custom | Dependencies | Dynamic | NVD/OSV lookup |
| **Code Quality** | Custom | Multi | N/A (quality) | Best practices |

### 1.2 Taal-Specifiek vs Taal-Agnostisch

```
TAAL-AGNOSTISCH (werkt voor alle talen):
├── OpenGrep (30+ talen, pattern-based)
├── Secret Scanner (regex patterns)
├── Generic Scanner (common patterns)
├── Trivy (dependency scanning)
└── CVE Scanner (dependency lookup)

TAAL-SPECIFIEK:
├── Bandit → Python only
├── Gosec → Go only
├── ASP Scanner → Classic ASP/VBScript only
├── OWASP Scanner → Per-taal patterns (12 talen)
└── Security Patterns YAML → Per-taal configs
```

---

## 2. CWE TOP 25 (2024) DEKKING

| Rank | CWE | Naam | Scanner(s) | Taal | Status |
|------|-----|------|------------|------|--------|
| 1 | **CWE-79** | XSS | OpenGrep, Bandit, OWASP, ASP | Multi | ✅ |
| 2 | **CWE-89** | SQL Injection | OpenGrep, Bandit, OWASP, ASP, Gosec | Multi | ✅ |
| 3 | **CWE-352** | CSRF | OpenGrep, OWASP, ASP | Multi | ✅ |
| 4 | **CWE-22** | Path Traversal | OpenGrep, Bandit, OWASP, ASP, Gosec | Multi | ✅ |
| 5 | **CWE-125** | Out-of-bounds Read | OpenGrep | C/C++ | ✅ |
| 6 | **CWE-78** | OS Command Injection | OpenGrep, Bandit, OWASP, ASP, Gosec | Multi | ✅ |
| 7 | **CWE-416** | Use After Free | OpenGrep | C/C++ | ✅ |
| 8 | **CWE-787** | Out-of-bounds Write | OpenGrep | C/C++ | ✅ |
| 9 | **CWE-20** | Improper Input Validation | OpenGrep, OWASP | Multi | ✅ |
| 10 | **CWE-476** | NULL Pointer Deref | OpenGrep, **Fase 35** | C/C++, Multi | ✅ |
| 11 | **CWE-434** | Unrestricted Upload | OpenGrep, OWASP, ASP | Multi | ✅ |
| 12 | **CWE-502** | Deserialization | OpenGrep, Bandit, OWASP | Multi | ✅ |
| 13 | **CWE-190** | Integer Overflow | OpenGrep, **Fase 34** | C/C++, Multi | ✅ |
| 14 | **CWE-287** | Improper Auth | OpenGrep, OWASP, ASP | Multi | ✅ |
| 15 | **CWE-798** | Hardcoded Credentials | Secret Scanner, Bandit, OWASP, **Fase 36** | Agnostisch | ✅ |
| 16 | **CWE-862** | Missing Authorization | OpenGrep, OWASP | Multi | ✅ |
| 17 | **CWE-306** | Missing Auth Critical | OpenGrep, OWASP | Multi | ✅ |
| 18 | **CWE-269** | Improper Privilege | OpenGrep, OWASP | Multi | ✅ |
| 19 | **CWE-94** | Code Injection | OpenGrep, Bandit, OWASP, ASP | Multi | ✅ |
| 20 | **CWE-863** | Incorrect Authorization | OpenGrep, OWASP | Multi | ✅ |
| 21 | **CWE-77** | Command Injection | OpenGrep, Bandit | Multi | ✅ |
| 22 | **CWE-276** | Incorrect Permissions | OpenGrep, Gosec | Multi | ✅ |
| 23 | **CWE-918** | SSRF | OpenGrep, OWASP | Multi | ✅ |
| 24 | **CWE-362** | Race Condition | **Fase 35** | Multi | 🆕 |
| 25 | **CWE-119** | Buffer Overflow | OpenGrep | C/C++ | ✅ |

**Legenda:** ✅ = Geïmplementeerd | 🆕 = Nieuw in Fase 34-36

---

## 3. NIEUWE CWEs IN FASE 34-36

### Fase 34: Advanced Error Detectors

| CWE | Naam | Scanner Module | Taal |
|-----|------|----------------|------|
| **CWE-833** | Deadlock | DeadlockDetector | Multi (agnostisch) |
| **CWE-1088** | Missing Timeout | DeadlockDetector | Multi |
| **CWE-1073** | N+1 Query | PerformancePatternDetector | Multi (ORM) |
| **CWE-407** | Algorithmic Complexity | PerformancePatternDetector | Agnostisch |
| **CWE-770** | Unbounded Allocation | PerformancePatternDetector | Agnostisch |
| **CWE-1333** | ReDoS | PerformancePatternDetector | Agnostisch |

### Fase 35: Data Integrity Scanners

| CWE | Naam | Scanner Module | Taal |
|-----|------|----------------|------|
| **CWE-362** | Race Condition | DataIntegrityDetector | Multi |
| **CWE-367** | TOCTOU | DataIntegrityDetector | Multi |
| **CWE-609** | Double-Checked Locking | DataIntegrityDetector | Java, C++ |
| **CWE-772** | Missing Release | ResourceLifecycleDetector | Multi |
| **CWE-459** | Incomplete Cleanup | ResourceLifecycleDetector | Multi |
| **CWE-908** | Uninitialized Resource | ResourceLifecycleDetector | Multi |
| **CWE-416** | Use After Free | ResourceLifecycleDetector | C/C++ |

### Fase 36: Logic & Crypto Scanner

| CWE | Naam | Scanner Module | Taal |
|-----|------|----------------|------|
| **CWE-321** | Hardcoded Crypto Key | CryptoErrorDetector | Agnostisch |
| **CWE-327** | Broken Crypto | CryptoErrorDetector | Multi |
| **CWE-328** | Weak Hash (MD5/SHA1) | CryptoErrorDetector | Multi |
| **CWE-329** | Weak IV | CryptoErrorDetector | Multi |
| **CWE-330** | Weak PRNG | CryptoErrorDetector | Multi |
| **CWE-208** | Timing Attack | CryptoErrorDetector | Multi |
| **CWE-295** | Cert Validation | CryptoErrorDetector | Multi |
| **CWE-326** | Weak Encryption | CryptoErrorDetector | Multi |
| **CWE-193** | Off-by-One | ControlFlowLogicDetector | Agnostisch |
| **CWE-835** | Infinite Loop | ControlFlowLogicDetector | Agnostisch |
| **CWE-481** | Assignment vs Compare | ControlFlowLogicDetector | C, C++, Java |
| **CWE-483** | Dangling Else | ControlFlowLogicDetector | C, C++, Java |
| **CWE-484** | Missing Break | ControlFlowLogicDetector | C, C++, Java, JS |
| **CWE-478** | Missing Default | ControlFlowLogicDetector | Multi |
| **CWE-1069** | Empty Exception | ControlFlowLogicDetector | Multi |
| **CWE-480** | Incorrect Operator | BooleanLogicDetector | Multi |
| **CWE-783** | Operator Precedence | BooleanLogicDetector | Multi |
| **CWE-843** | Type Confusion | BooleanLogicDetector | JS, Python |
| **CWE-1077** | Float Comparison | BooleanLogicDetector | Agnostisch |
| **CWE-570** | Always False | BooleanLogicDetector | Agnostisch |
| **CWE-571** | Always True | BooleanLogicDetector | Agnostisch |
| **CWE-768** | Short-Circuit | BooleanLogicDetector | Multi |

---

## 4. COMPLETE CWE MATRIX PER SCANNER

### 4.1 OpenGrep (Taal-Agnostisch, 30+ talen)

```
INJECTION:        CWE-78, CWE-79, CWE-89, CWE-94, CWE-917
AUTH:             CWE-287, CWE-306, CWE-352, CWE-862, CWE-863
CRYPTO:           CWE-295, CWE-327, CWE-328, CWE-330
DATA:             CWE-22, CWE-434, CWE-502, CWE-611, CWE-918
MEMORY:           CWE-119, CWE-125, CWE-416, CWE-787
OTHER:            CWE-20, CWE-200, CWE-269, CWE-276, CWE-798
```

### 4.2 Bandit (Python-Specifiek)

```
INJECTION:        CWE-78, CWE-79, CWE-89, CWE-94
CRYPTO:           CWE-295, CWE-327, CWE-328, CWE-330, CWE-338
DESERIALIZATION:  CWE-502
FILES:            CWE-22, CWE-377, CWE-732
CREDENTIALS:      CWE-798, CWE-259
SUBPROCESS:       CWE-78
NETWORK:          CWE-295
TEMPLATES:        CWE-79
```

### 4.3 OWASP Scanner (Multi-Taal, 12 talen)

```
A01 (Access):     CWE-22, CWE-284, CWE-352, CWE-601, CWE-862 (+26 meer)
A02 (Crypto):     CWE-327, CWE-330, CWE-338, CWE-337 (+31 meer)
A03 (Injection):  CWE-78, CWE-79, CWE-89, CWE-94 (+31 meer)
A04 (Design):     CWE-434, CWE-502, CWE-522, CWE-841 (+37 meer)
A05 (Config):     CWE-611, CWE-942, CWE-1004 (+15 meer)
A06 (Components): CWE-1104, CWE-829, CWE-937
A07 (Auth):       CWE-287, CWE-295, CWE-521, CWE-798 (+17 meer)
A08 (Integrity):  CWE-502, CWE-829, CWE-830 (+7 meer)
A09 (Logging):    CWE-532, CWE-778, CWE-223, CWE-779
A10 (SSRF):       CWE-918
```

### 4.4 Custom Scanners (Fase 34-36)

```
FASE 34 - DeadlockDetector:
├── CWE-833   Deadlock                    [Multi]
└── CWE-1088  Missing Timeout             [Multi]

FASE 34 - PerformancePatternDetector:
├── CWE-1073  N+1 Query                   [Python, Java, C#, JS]
├── CWE-407   Algorithmic Complexity      [Agnostisch]
├── CWE-770   Unbounded Allocation        [Agnostisch]
└── CWE-1333  ReDoS                       [Agnostisch]

FASE 35 - DataIntegrityDetector:
├── CWE-362   Race Condition              [Multi]
├── CWE-367   TOCTOU                      [Multi]
└── CWE-609   Double-Checked Locking      [Java, C++]

FASE 35 - ResourceLifecycleDetector:
├── CWE-772   Missing Release             [Multi]
├── CWE-459   Incomplete Cleanup          [Multi]
├── CWE-908   Uninitialized Resource      [Multi]
└── CWE-416   Use After Free              [C/C++]

FASE 36 - CryptoErrorDetector:
├── CWE-321   Hardcoded Crypto Key        [Agnostisch]
├── CWE-327   Broken Crypto               [Multi]
├── CWE-328   Weak Hash                   [Multi]
├── CWE-329   Weak IV                     [Multi]
├── CWE-330   Weak PRNG                   [Multi]
├── CWE-208   Timing Attack               [Multi]
├── CWE-295   Cert Validation             [Multi]
└── CWE-326   Weak Encryption             [Multi]

FASE 36 - ControlFlowLogicDetector:
├── CWE-193   Off-by-One                  [Agnostisch]
├── CWE-835   Infinite Loop               [Agnostisch]
├── CWE-481   Assignment vs Compare       [C, C++, Java]
├── CWE-483   Dangling Else               [C, C++, Java]
├── CWE-484   Missing Break               [C, C++, Java, JS]
├── CWE-478   Missing Default             [Multi]
└── CWE-1069  Empty Exception             [Multi]

FASE 36 - BooleanLogicDetector:
├── CWE-480   Incorrect Operator          [Multi]
├── CWE-783   Operator Precedence         [Multi]
├── CWE-843   Type Confusion              [JS, Python]
├── CWE-1077  Float Comparison            [Agnostisch]
├── CWE-570   Always False                [Agnostisch]
├── CWE-571   Always True                 [Agnostisch]
└── CWE-768   Short-Circuit               [Multi]
```

---

## 5. TAAL COVERAGE MATRIX

| Taal | Scanners | Dekking | Specifieke CWEs |
|------|----------|---------|-----------------|
| **Python** | OpenGrep, Bandit, OWASP, Generic, Fase 34-36 | 90+ CWEs | CWE-502, CWE-94, CWE-78 |
| **Java** | OpenGrep, OWASP, Generic, Fase 34-36 | 80+ CWEs | CWE-502, CWE-609, CWE-481 |
| **JavaScript** | OpenGrep, OWASP, Generic, Fase 34-36 | 70+ CWEs | CWE-79, CWE-843, CWE-94 |
| **C#** | OpenGrep, OWASP, Generic, Fase 34-36 | 75+ CWEs | CWE-89, CWE-611, CWE-502 |
| **Go** | OpenGrep, Gosec, OWASP, Generic | 60+ CWEs | CWE-78, CWE-89, CWE-295 |
| **C/C++** | OpenGrep, Fase 35-36 | 50+ CWEs | CWE-119, CWE-416, CWE-787 |
| **PHP** | OpenGrep, OWASP, Generic | 50+ CWEs | CWE-89, CWE-79, CWE-78 |
| **Ruby** | OpenGrep, OWASP, Generic | 45+ CWEs | CWE-89, CWE-79, CWE-94 |
| **Classic ASP** | ASP Scanner, Generic | 13 CWEs | CWE-89, CWE-79, CWE-78 |
| **VB.NET** | OpenGrep, OWASP, Generic | 40+ CWEs | Similar to C# |
| **Rust** | OpenGrep, Generic | 30+ CWEs | Memory-safe by design |
| **Swift** | OpenGrep, Generic | 30+ CWEs | iOS/macOS specific |
| **Kotlin** | OpenGrep, OWASP, Generic | 40+ CWEs | Similar to Java |

---

## 6. GAPS & RECOMMENDATIONS

### 6.1 Goed Gedekt (8+ bronnen)

| CWE | Naam | Bronnen |
|-----|------|---------|
| CWE-79 | XSS | OpenGrep, Bandit, OWASP, ASP, Generic, Fase 36 |
| CWE-89 | SQL Injection | OpenGrep, Bandit, OWASP, ASP, Gosec, Generic |
| CWE-78 | Command Injection | OpenGrep, Bandit, OWASP, ASP, Gosec |
| CWE-798 | Hardcoded Credentials | Secret, Bandit, OWASP, Generic, Fase 36 |
| CWE-22 | Path Traversal | OpenGrep, Bandit, OWASP, ASP, Gosec |

### 6.2 Matig Gedekt (3-7 bronnen)

| CWE | Naam | Actie |
|-----|------|-------|
| CWE-327 | Weak Crypto | ✅ Versterkt in Fase 36 |
| CWE-502 | Deserialization | Voldoende |
| CWE-295 | Cert Validation | ✅ Versterkt in Fase 36 |
| CWE-362 | Race Condition | ✅ Nieuw in Fase 35 |

### 6.3 Nieuw Gedekt (Fase 34-36)

| CWE | Naam | Scanner |
|-----|------|---------|
| CWE-833 | Deadlock | Fase 34 |
| CWE-1073 | N+1 Query | Fase 34 |
| CWE-1333 | ReDoS | Fase 34 |
| CWE-367 | TOCTOU | Fase 35 |
| CWE-193 | Off-by-One | Fase 36 |
| CWE-481 | Assignment in Condition | Fase 36 |
| CWE-783 | Operator Precedence | Fase 36 |

### 6.4 Potentiële Gaps (Overweeg voor Fase 37+)

| CWE | Naam | Reden | Prioriteit |
|-----|------|-------|------------|
| CWE-400 | Resource Exhaustion | DoS prevention | MEDIUM |
| CWE-732 | Incorrect Permission | File permissions | LOW |
| CWE-611 | XXE | XML-specifiek | LOW |
| CWE-1021 | Improper UI Restriction | Clickjacking | LOW |
| CWE-384 | Session Fixation | Web-specifiek | MEDIUM |

---

## 7. SCANNER SELECTIE FLOWCHART

```
                    ┌─────────────────────┐
                    │   Incoming Code     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Detect Language    │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   ┌─────────┐           ┌─────────┐           ┌─────────┐
   │ Python  │           │  Java   │           │  C/C++  │
   └────┬────┘           └────┬────┘           └────┬────┘
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐           ┌─────────┐           ┌─────────┐
   │ Bandit  │           │OpenGrep │           │OpenGrep │
   │OpenGrep │           │ OWASP   │           │ Fase 35 │
   │ OWASP   │           │Fase 34-6│           │Fase 36  │
   │Fase 34-6│           └─────────┘           └─────────┘
   └─────────┘

   ALTIJD (alle talen):
   ├── Secret Scanner (CWE-798)
   ├── Generic Scanner (common patterns)
   ├── Trivy (dependencies)
   └── CVE Scanner (known vulns)
```

---

## 8. SAMENVATTING

### Totaal CWE Dekking

| Categorie | CWEs | Status |
|-----------|------|--------|
| CWE Top 25 (2024) | 25/25 | ✅ 100% |
| OWASP Top 10 | 10/10 | ✅ 100% |
| Memory Safety | 8 | ✅ (C/C++ only) |
| Injection | 12 | ✅ |
| Crypto | 15 | ✅ (versterkt Fase 36) |
| Auth/Access | 18 | ✅ |
| Logic Errors | 12 | 🆕 Fase 36 |
| Concurrency | 8 | 🆕 Fase 34-35 |
| Performance | 6 | 🆕 Fase 34 |

### Scanner Type Verdeling

| Type | Scanners | CWEs | Talen |
|------|----------|------|-------|
| External (Open Source) | 4 | 150+ | 30+ |
| Custom (MarQed) | 8 | 80+ | 12 |
| Planned (Fase 34-36) | 6 | 31 | Multi |
| **Totaal** | **18** | **180+** | **30+** |
