# CWE Top 25 Coverage Analysis (SANS + 2019 Combined)

**Datum:** 2026-01-13
**Doel:** Inventarisatie van huidige detectie-dekking voor CWE Top 25 programmeringsfouten
**Focus:** Classic ASP, .NET, en legacy codebases
**Bronnen:** SANS Top 25 + CWE 2019 Top 25

---

## Coverage Matrix - Combined CWE Top 25

### 2019 CWE Top 25 (Score-based)

| Rank | CWE | Naam | Score | Classic ASP? | Detectie | Priority |
|------|-----|------|-------|--------------|----------|----------|
| 1 | CWE-119 | Buffer Boundary Operations | 75.56 | ❌ Nee | N/A | - |
| 2 | CWE-79 | Cross-site Scripting (XSS) | 45.69 | ✅ Ja | ❌ Niet | CRITICAL |
| 3 | CWE-20 | Improper Input Validation | 43.61 | ✅ Ja | ❌ Niet | CRITICAL |
| 4 | CWE-200 | Information Exposure | 32.12 | ✅ Ja | ❌ Niet | HIGH |
| 5 | CWE-125 | Out-of-bounds Read | 26.53 | ❌ Nee | N/A | - |
| 6 | CWE-89 | SQL Injection | 24.54 | ✅ Ja | ❌ Niet | CRITICAL |
| 7 | CWE-416 | Use After Free | 17.94 | ❌ Nee | N/A | - |
| 8 | CWE-190 | Integer Overflow | 17.35 | ❌ Nee | N/A | - |
| 9 | CWE-352 | Cross-Site Request Forgery | 15.54 | ✅ Ja | ❌ Niet | HIGH |
| 10 | CWE-22 | Path Traversal | 14.10 | ✅ Ja | ❌ Niet | CRITICAL |
| 11 | CWE-78 | OS Command Injection | 11.47 | ✅ Ja | ❌ Niet | CRITICAL |
| 12 | CWE-787 | Out-of-bounds Write | 11.08 | ❌ Nee | N/A | - |
| 13 | CWE-287 | Improper Authentication | 10.78 | ✅ Ja | ❌ Niet | CRITICAL |
| 14 | CWE-476 | NULL Pointer Dereference | 9.74 | ❌ Nee | N/A | - |
| 15 | CWE-732 | Permission Assignment | 6.33 | ✅ Ja | ❌ Niet | HIGH |
| 16 | CWE-434 | Unrestricted File Upload | 5.50 | ✅ Ja | ❌ Niet | CRITICAL |
| 17 | CWE-611 | XML External Entity (XXE) | 5.48 | ✅ Ja | ❌ Niet | HIGH |
| 18 | CWE-94 | Code Injection | 5.36 | ✅ Ja | ❌ Niet | CRITICAL |
| 19 | CWE-798 | Hard-coded Credentials | 5.12 | ✅ Ja | 🟡 Deels | CRITICAL |
| 20 | CWE-400 | Resource Consumption | 5.04 | ✅ Ja | 🟢 Ja | MEDIUM |
| 21 | CWE-772 | Missing Resource Release | 5.04 | ✅ Ja | 🟢 Ja | MEDIUM |
| 22 | CWE-426 | Untrusted Search Path | 4.40 | ✅ Ja | ❌ Niet | MEDIUM |
| 23 | CWE-502 | Deserialization | 4.30 | ✅ Ja | ❌ Niet | HIGH |
| 24 | CWE-269 | Privilege Management | 4.23 | ✅ Ja | ❌ Niet | HIGH |
| 25 | CWE-295 | Certificate Validation | 4.06 | ✅ Ja | ❌ Niet | MEDIUM |

### Additional SANS Top 25 CWEs (niet in 2019 lijst)

| CWE | Naam | Classic ASP? | Detectie | Priority |
|-----|------|--------------|----------|----------|
| CWE-285 | Improper Access Control | ✅ Ja | ❌ Niet | HIGH |
| CWE-306 | Missing Authentication | ✅ Ja | ❌ Niet | CRITICAL |
| CWE-311 | Missing Encryption | ✅ Ja | ❌ Niet | HIGH |
| CWE-327 | Risky Cryptography | ✅ Ja | ❌ Niet | HIGH |
| CWE-362 | Race Condition | ✅ Ja | ❌ Niet | MEDIUM |
| CWE-601 | Open Redirect | ✅ Ja | ❌ Niet | HIGH |
| CWE-807 | Untrusted Inputs | ✅ Ja | ❌ Niet | HIGH |
| CWE-209 | Error Message Exposure | ✅ Ja | ❌ Niet | HIGH |
| CWE-129 | Array Index Validation | ✅ Ja | ❌ Niet | MEDIUM |
| CWE-754 | Exceptional Conditions | ✅ Ja | ❌ Niet | MEDIUM |

---

## Huidige Detectie-status

### ✅ Volledig Gedetecteerd (1/25)

| CWE | Detector | Beschrijving |
|-----|----------|--------------|
| CWE-400 | ResourceLeakDetector | ADO, COM, File handle leaks |

### 🟡 Deels Gedetecteerd (1/25)

| CWE | Detector | Wat wel | Wat niet |
|-----|----------|---------|----------|
| CWE-798 | Magic Numbers | Hardcoded OmgevingIds | Credentials |

### ❌ Niet Gedetecteerd (18/25 relevant)

```
CRITICAL (6):  CWE-79, CWE-89, CWE-22, CWE-434, CWE-78, CWE-306
HIGH (7):      CWE-352, CWE-285, CWE-807, CWE-311, CWE-209, CWE-732, CWE-601, CWE-327
MEDIUM (5):    CWE-129, CWE-754, CWE-494, CWE-362, CWE-798 (credentials deel)
```

### N/A voor Classic ASP (5/25)

- CWE-120: Buffer Overflow (compiled languages)
- CWE-805: Buffer Access (compiled languages)
- CWE-98: PHP File Inclusion
- CWE-190: Integer Overflow (compiled languages)
- CWE-131: Buffer Size (compiled languages)

---

## Implementation Roadmap

### Phase 1: Critical Injection Vulnerabilities (Week 145-147)

**Files:** [security-scanners-injection.md](security-scanners-injection.md)

| CWE | Scanner | Priority | Effort |
|-----|---------|----------|--------|
| CWE-89 | SQLInjectionDetector | P0 | 3 days |
| CWE-79 | XSSDetector | P0 | 3 days |
| CWE-78 | OSCommandInjectionDetector | P1 | 2 days |
| CWE-22 | PathTraversalDetector | P1 | 2 days |

### Phase 2: Authentication & Authorization (Week 148-150)

**Files:** [security-scanners-authentication.md](security-scanners-authentication.md)

| CWE | Scanner | Priority | Effort |
|-----|---------|----------|--------|
| CWE-306 | MissingAuthenticationDetector | P0 | 3 days |
| CWE-285 | AccessControlDetector | P1 | 3 days |
| CWE-352 | CSRFDetector | P1 | 2 days |
| CWE-807 | UntrustedInputDetector | P2 | 2 days |

### Phase 3: Data Protection (Week 151-153)

**Files:** [security-scanners-data-protection.md](security-scanners-data-protection.md)

| CWE | Scanner | Priority | Effort |
|-----|---------|----------|--------|
| CWE-311 | MissingEncryptionDetector | P1 | 2 days |
| CWE-327 | WeakCryptoDetector | P1 | 2 days |
| CWE-798 | HardcodedCredentialsDetector | P0 | 2 days |
| CWE-209 | ErrorMessageExposureDetector | P2 | 1 day |

### Phase 4: File & Resource Security (Week 154-156)

**Files:** [security-scanners-resources.md](security-scanners-resources.md)

| CWE | Scanner | Priority | Effort |
|-----|---------|----------|--------|
| CWE-434 | FileUploadDetector | P0 | 3 days |
| CWE-732 | PermissionDetector | P1 | 2 days |
| CWE-601 | OpenRedirectDetector | P2 | 1 day |
| CWE-494 | CodeIntegrityDetector | P2 | 1 day |

### Phase 5: Advanced Detection (Week 157-160)

**Files:** [security-scanners-advanced.md](security-scanners-advanced.md)

| CWE | Scanner | Priority | Effort |
|-----|---------|----------|--------|
| CWE-362 | RaceConditionDetector | P2 | 3 days |
| CWE-129 | ArrayIndexDetector | P2 | 2 days |
| CWE-754 | ExceptionalConditionDetector | P3 | 2 days |

---

## Integration Points

### Brown Paper Workflow

```python
# Phase 1: Code Understanding
result.security_scan = await run_cwe_top25_scan(project_path)

# Returns:
{
    "cwe_coverage": {
        "detected": 18,
        "total": 25,
        "percentage": 72
    },
    "findings_by_cwe": {...},
    "risk_score": 7.2
}
```

### Quality Gate

```python
SECURITY_GATE = {
    "critical_cwe_allowed": 0,  # CWE-89, CWE-79, etc.
    "high_cwe_max": 10,
    "overall_risk_max": 5.0
}
```

---

## Related Documents

- [security-scanners-injection.md](security-scanners-injection.md) - Injection scanners spec
- [security-scanners-authentication.md](security-scanners-authentication.md) - Auth scanners spec
- [security-scanners-data-protection.md](security-scanners-data-protection.md) - Data protection spec
- [security-scanners-resources.md](security-scanners-resources.md) - Resource security spec
- [security-scanners-advanced.md](security-scanners-advanced.md) - Advanced detection spec

---

*Generated by MarQed AI Agent Platform - Week 144*
