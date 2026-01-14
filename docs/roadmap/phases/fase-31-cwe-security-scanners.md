# Fase 31: CWE Top 25 Security Scanner Suite (Week 145-160) SECURITY

**Goal:** Implementatie van security scanners voor CWE Top 25 (SANS + 2019) kwetsbaarheden, specifiek voor Classic ASP
**Specification:** [docs/plans/cwe-top25-coverage-analysis.md](../../plans/cwe-top25-coverage-analysis.md)
**Status:** PLANNED
**Priority:** HIGH (security compliance essentieel voor healthcare/FysioOne)
**Origin:** MITRE/SANS CWE Top 25 programmeerfouten analyse

---

## Problem Statement

Van de 35 unieke CWE's uit SANS + 2019 Top 25 zijn er:
- 6 N/A voor Classic ASP (buffer/memory vulnerabilities)
- 2 gedetecteerd (CWE-400, CWE-772: ResourceLeakDetector)
- 1 deels gedetecteerd (CWE-798: hardcoded values, niet credentials)
- **26 niet gedetecteerd** - waarvan 8 CRITICAL

---

## Coverage Summary

```
HUIDIGE DEKKING:   2/35 CWE's (6%)
NA HET PROJECT:   28/35 CWE's (80%)
N/A VOOR ASP:      6/35 CWE's (17%)
DOELBEREIK:        93% van relevante CWE's
```

---

## Implementation Phases

| Phase | Week | Focus | CWE's | Effort |
|-------|------|-------|-------|--------|
| **31.1** | 145-147 | Injection | CWE-89, CWE-79, CWE-78, CWE-22, CWE-94 | 12 dagen |
| **31.2** | 148-150 | Authentication | CWE-287, CWE-306, CWE-352, CWE-285 | 14 dagen |
| **31.3** | 151-153 | Data Protection | CWE-311, CWE-327, CWE-798, CWE-200, CWE-209 | 11 dagen |
| **31.4** | 154-156 | Resources | CWE-434, CWE-732, CWE-601, CWE-426, CWE-295 | 10 dagen |
| **31.5** | 157-160 | Advanced | CWE-20, CWE-362, CWE-502, CWE-269, CWE-611 | 14 dagen |

---

## Phase 31.1: Injection Vulnerabilities (Week 145-147)

| CWE | Scanner | Description | Priority |
|-----|---------|-------------|----------|
| CWE-89 | SQLInjectionDetector | Dynamic SQL met Request() | P0 |
| CWE-79 | XSSDetector | Response.Write zonder encode | P0 |
| CWE-78 | OSCommandInjectionDetector | WScript.Shell met user input | P1 |
| CWE-22 | PathTraversalDetector | File paths met user input | P1 |
| CWE-94 | CodeInjectionDetector | Execute/Eval met user input | P1 |

---

## Phase 31.2: Authentication (Week 148-150)

| CWE | Scanner | Description | Priority |
|-----|---------|-------------|----------|
| CWE-287 | AuthenticationBypassDetector | Improper authentication | P0 |
| CWE-306 | MissingAuthDetector | Missing authentication | P0 |
| CWE-352 | CSRFDetector | Missing CSRF tokens | P1 |
| CWE-285 | AuthorizationDetector | Improper authorization | P1 |

---

## Phase 31.3: Data Protection (Week 151-153)

| CWE | Scanner | Description | Priority |
|-----|---------|-------------|----------|
| CWE-311 | EncryptionMissingDetector | Missing encryption | P0 |
| CWE-327 | WeakCryptoDetector | Broken/risky crypto | P1 |
| CWE-798 | HardcodedCredentialsDetector | Hardcoded passwords | P0 |
| CWE-200 | SensitiveDataExposureDetector | Sensitive data in logs | P1 |
| CWE-209 | ErrorMessageDetector | Detailed errors exposed | P2 |

---

## Phase 31.4: Resources (Week 154-156)

| CWE | Scanner | Description | Priority |
|-----|---------|-------------|----------|
| CWE-434 | FileUploadDetector | Unrestricted file upload | P0 |
| CWE-732 | PermissionsDetector | Incorrect permissions | P1 |
| CWE-601 | OpenRedirectDetector | URL redirect to untrusted | P1 |
| CWE-426 | UntrustedSearchPathDetector | Untrusted search path | P2 |
| CWE-295 | CertificateValidationDetector | Improper cert validation | P2 |

---

## Phase 31.5: Advanced (Week 157-160)

| CWE | Scanner | Description | Priority |
|-----|---------|-------------|----------|
| CWE-20 | InputValidationDetector | Improper input validation | P1 |
| CWE-362 | RaceConditionDetector | Race conditions | P2 |
| CWE-502 | DeserializationDetector | Untrusted deserialization | P1 |
| CWE-269 | PrivilegeEscalationDetector | Improper privilege management | P1 |
| CWE-611 | XXEDetector | XML external entities | P2 |

---

## Scanner Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  CWE SECURITY SCANNER SUITE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            BaseSecurityScanner (Abstract)                 │    │
│  │  - scan_file(content) -> List[SecurityFinding]           │    │
│  │  - get_cwe_id() -> str                                    │    │
│  │  - get_severity() -> Severity                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌──────────┬──────────┬────┴────┬──────────┬──────────┐       │
│  │Injection │  Auth    │  Data   │ Resource │ Advanced │       │
│  │Scanners  │ Scanners │Scanners │ Scanners │ Scanners │       │
│  └──────────┴──────────┴─────────┴──────────┴──────────┘       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            SecurityScanOrchestrator                       │    │
│  │  - run_all_scanners(project_path) -> SecurityReport      │    │
│  │  - run_category(category) -> List[SecurityFinding]       │    │
│  │  - integrate_with_brown_paper(session_id)                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/security/scan` | POST | Run full CWE security scan |
| `/api/security/scan/{category}` | POST | Scan specific category |
| `/api/security/findings/{project_id}` | GET | Get all findings |
| `/api/security/findings/{project_id}/cwe/{cwe_id}` | GET | Findings by CWE |
| `/api/security/coverage` | GET | CWE coverage statistics |
| `/api/security/compliance/{project_id}` | GET | Compliance status |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| CWE Coverage | 80%+ of Top 25 |
| Detection Accuracy | >90% per scanner |
| False Positive Rate | <10% |
| Scan Performance | <5 min for 1000 files |
| Integration | Brown Paper, Quality Gates |

---

## Total Effort: ~60 days (15 weeks)

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 21 (Stability) | COMPLETE | Shares resource leak detection |
| GhostCrew | COMPLETE | Security integration point |
| Brown Paper | COMPLETE | Integration target |

---

← [Back to Overview](../phases-planned.md)
