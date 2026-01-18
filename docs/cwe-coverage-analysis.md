# CWE Coverage Analysis

## Executive Summary

| Metric | Value |
|--------|-------|
| **CWEs Currently Implemented** | 71 |
| **CWEs in Top 25 (2024)** | 25 |
| **Top 25 Coverage** | 14/25 (56%) |
| **CWEs Tested for False Negatives** | 25 |
| **False Negatives Found** | 52 |

---

## Part 1: Current CWE Coverage by Scanner

### Scanner Inventory

| Scanner | CWEs | Rules | Focus Area |
|---------|------|-------|------------|
| Memory Safety Detector | 17 | 16 | Buffer overflows, memory corruption |
| Concurrency Detector | 9 | 8 | Race conditions, deadlocks |
| Crypto Error Detector | 8 | 12 | Weak crypto, hardcoded keys |
| Control Flow Detector | 9 | 12 | Loops, exceptions, switch |
| Boolean Logic Detector | 8 | 12 | Operator errors, null checks |
| Web Security Detector | 6 | 12 | Prototype pollution, CSV injection |
| Path Security Detector | 6 | 10 | Path traversal, ReDoS |
| Generic Security Scanner | 9 | 9 | Credentials, redirects |
| Secret Scanner | 1 | 1 | Hardcoded secrets |
| **TOTAL** | **71 unique** | **92** | |

### Complete CWE List by Scanner

#### Memory Safety Detector (17 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-119 | Buffer Overflow | MS001, MS002, MS003, MS004, MS012, MS013, MS016 |
| CWE-122 | Heap-based Buffer Overflow | MS008 |
| CWE-125 | Out-of-bounds Read | MS014 |
| CWE-134 | Format String | MS010 |
| CWE-190 | Integer Overflow | MS008 |
| CWE-195 | Signed/Unsigned Comparison | MS009 |
| CWE-242 | Dangerous Function | MS002 |
| CWE-401 | Memory Leak | MS015 |
| CWE-415 | Double Free | MS006 |
| CWE-416 | Use After Free | MS005, MS013, MS015 |
| CWE-457 | Uninitialized Variable | MS011 |
| CWE-562 | Return Stack Address | MS007 |
| CWE-697 | Incorrect Comparison | MS009 |
| CWE-770 | Resource Allocation | MS016 |
| CWE-787 | Out-of-bounds Write | MS001-MS004, MS014 |
| CWE-805 | Buffer Access Wrong Length | MS004 |
| CWE-824 | Uninitialized Pointer | MS011 |

#### Concurrency Detector (9 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-362 | Race Condition | CC001, CC002, CC003 |
| CWE-366 | Race in Thread | CC001 |
| CWE-367 | TOCTOU | CC002 |
| CWE-479 | Signal Handler Race | CC003 |
| CWE-764 | Multiple Locks | CC004, CC005 |
| CWE-765 | Multiple Unlocks | CC005 |
| CWE-820 | Missing Sync | CC006, CC007, CC008 |
| CWE-821 | Incorrect Sync | CC008 |
| CWE-833 | Deadlock | CC004 |

#### Crypto Error Detector (8 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-208 | Timing Attack | CR009 |
| CWE-295 | Certificate Validation | CR010, CR011 |
| CWE-321 | Hardcoded Crypto Key | CR001 |
| CWE-326 | Inadequate Encryption | CR012 |
| CWE-327 | Weak Crypto Algorithm | CR006, CR007 |
| CWE-328 | Weak Hash | CR004, CR005 |
| CWE-330 | Weak PRNG | CR008 |
| CWE-798 | Hardcoded Credentials | CR002, CR003 |

#### Control Flow Detector (9 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-193 | Off-by-One | CF001 |
| CWE-459 | Incomplete Cleanup | CF031 |
| CWE-478 | Missing Default Case | CF021, CF022 |
| CWE-481 | Assign vs Compare | CF010 |
| CWE-483 | Dangling Else | CF003, CF011 |
| CWE-484 | Missing Break | CF020 |
| CWE-755 | Exception Handling | CF032 |
| CWE-835 | Infinite Loop | CF002, CF004 |
| CWE-1069 | Empty Exception | CF030 |

#### Boolean Logic Detector (8 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-476 | NULL Pointer Deref | BL030 |
| CWE-480 | Incorrect Operator | BL001, BL002, BL022, BL023 |
| CWE-570 | Always False | BL041 |
| CWE-571 | Always True | BL040 |
| CWE-768 | Short Circuit Error | BL031 |
| CWE-783 | Operator Precedence | BL010, BL011 |
| CWE-843 | Type Confusion | BL020 |
| CWE-1077 | Float Comparison | BL021 |

#### Web Security Detector (6 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-129 | Array Index Validation | WS020 |
| CWE-606 | Loop Input | WS021 |
| CWE-789 | Memory Allocation Size | WS022 |
| CWE-1236 | CSV Injection | WS010-WS013 |
| CWE-1284 | Invalid Quantity | WS020-WS023 |
| CWE-1321 | Prototype Pollution | WS001-WS004 |

#### Path Security Detector (6 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-185 | Incorrect Regex | PS023 |
| CWE-400 | Resource Consumption | PS020 |
| CWE-426 | Untrusted Search Path | PS001 |
| CWE-427 | Uncontrolled Search Path | PS001-PS003 |
| CWE-428 | Unquoted Search Path | PS010-PS012 |
| CWE-1333 | ReDoS | PS020-PS023 |

#### Generic Security Scanner (9 CWEs)
| CWE | Name | Rules |
|-----|------|-------|
| CWE-200 | Information Exposure | GEN-CWE-200-001 |
| CWE-259 | Hardcoded Password | GEN-CWE-798-001 |
| CWE-330 | Weak Random | GEN-CWE-337-001/002 |
| CWE-337 | Predictable Seed | GEN-CWE-337-001/002 |
| CWE-521 | Weak Password | GEN-CWE-521-001/002 |
| CWE-522 | Insufficient Credential Protection | GEN-CWE-200-001 |
| CWE-601 | Open Redirect | GEN-CWE-601-001 |
| CWE-602 | Client-Side Security | GEN-CWE-602-001 |
| CWE-841 | Workflow Enforcement | GEN-CWE-841-001 |

---

## Part 2: CWE Top 25 (2024) Coverage

### Coverage Status

| Rank | CWE | Name | Score | Status |
|------|-----|------|-------|--------|
| 1 | CWE-79 | Cross-site Scripting (XSS) | 56.92 | ❌ **MISSING** |
| 2 | CWE-787 | Out-of-bounds Write | 45.20 | ✅ Memory Safety |
| 3 | CWE-89 | SQL Injection | 35.88 | ❌ **MISSING** |
| 4 | CWE-352 | CSRF | 19.57 | ❌ **MISSING** |
| 5 | CWE-22 | Path Traversal | 12.74 | ❌ **MISSING** |
| 6 | CWE-125 | Out-of-bounds Read | 11.42 | ✅ Memory Safety |
| 7 | CWE-78 | OS Command Injection | 11.30 | ❌ **MISSING** |
| 8 | CWE-416 | Use After Free | 10.19 | ✅ Memory Safety |
| 9 | CWE-862 | Missing Authorization | 10.11 | ❌ **MISSING** |
| 10 | CWE-434 | Unrestricted File Upload | 10.03 | ❌ **MISSING** |
| 11 | CWE-94 | Code Injection | 7.13 | ❌ **MISSING** |
| 12 | CWE-20 | Input Validation | 6.78 | ❌ **MISSING** |
| 13 | CWE-77 | Command Injection | 6.74 | ❌ **MISSING** |
| 14 | CWE-287 | Improper Authentication | 5.94 | ❌ **MISSING** |
| 15 | CWE-269 | Privilege Management | 5.22 | ❌ **MISSING** |
| 16 | CWE-502 | Deserialization | 5.07 | ❌ **MISSING** |
| 17 | CWE-200 | Information Exposure | 5.07 | ✅ Generic |
| 18 | CWE-863 | Incorrect Authorization | 4.05 | ❌ **MISSING** |
| 19 | CWE-918 | SSRF | 4.05 | ❌ **MISSING** |
| 20 | CWE-119 | Buffer Overflow | 3.69 | ✅ Memory Safety |
| 21 | CWE-476 | NULL Pointer Deref | 3.58 | ✅ Boolean Logic |
| 22 | CWE-798 | Hardcoded Credentials | 3.46 | ✅ Crypto + Generic |
| 23 | CWE-190 | Integer Overflow | 3.37 | ✅ Memory Safety |
| 24 | CWE-400 | Resource Consumption | 3.23 | ✅ Path Security |
| 25 | CWE-306 | Missing Auth for Function | 2.73 | ❌ **MISSING** |

### Summary: Top 25 Coverage

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Covered | 10 | 40% |
| ❌ Missing | 15 | 60% |

### Critical Missing CWEs (Top 10 Priority)

| Priority | CWE | Name | Score | Impact |
|----------|-----|------|-------|--------|
| 1 | CWE-79 | XSS | 56.92 | #1 most exploited |
| 2 | CWE-89 | SQL Injection | 35.88 | #3 most exploited |
| 3 | CWE-352 | CSRF | 19.57 | #4 most exploited |
| 4 | CWE-22 | Path Traversal | 12.74 | File system access |
| 5 | CWE-78 | OS Command Injection | 11.30 | RCE risk |
| 6 | CWE-862 | Missing Authorization | 10.11 | Access control |
| 7 | CWE-434 | File Upload | 10.03 | RCE risk |
| 8 | CWE-94 | Code Injection | 7.13 | RCE risk |
| 9 | CWE-502 | Deserialization | 5.07 | RCE risk |
| 10 | CWE-918 | SSRF | 4.05 | Internal access |

---

## Part 3: False Negative Testing Status

### CWEs Tested for False Negatives

| CWE | Name | Scanner | Tests | False Negatives |
|-----|------|---------|-------|-----------------|
| CWE-119 | Buffer Overflow | Memory Safety | 3 | 3 |
| CWE-190 | Integer Overflow | Memory Safety | 1 | 1 |
| CWE-208 | Timing Attack | Generic | 1 | 1 |
| CWE-327 | Weak Crypto | Crypto | 3 | 3 |
| CWE-329 | Static IV | Crypto | 1 | 1 |
| CWE-330 | Weak PRNG | Generic | 2 | 1 |
| CWE-362 | Race Condition | Concurrency | 5 | 5 |
| CWE-390 | Empty Exception | Control Flow | 1 | 0 (partial) |
| CWE-416 | Use After Free | Memory Safety | 1 | 0 (detected) |
| CWE-427 | Uncontrolled Path | Path Security | 5 | 5 |
| CWE-428 | Unquoted Path | Path Security | 4 | 4 |
| CWE-476 | Null Deref | Boolean Logic | 1 | 1 |
| CWE-480 | Operator Error | Boolean Logic | 3 | 3 |
| CWE-484 | Missing Break | Control Flow | 1 | 0 (detected) |
| CWE-570 | Always False | Boolean Logic | 1 | 1 |
| CWE-602 | Auth Bypass | Generic | 2 | 2 |
| CWE-835 | Infinite Loop | Control Flow | 1 | 1 |
| CWE-916 | Weak Hash | Crypto | 1 | 1 |
| CWE-1236 | CSV Injection | Web Security | 5 | 3 |
| CWE-1284 | Invalid Quantity | Web Security | 5 | 3 |
| CWE-1321 | Prototype Pollution | Web Security | 6 | 5 |
| CWE-1333 | ReDoS | Path Security | 5 | 4 |

### Summary: False Negative Testing

| Metric | Value |
|--------|-------|
| CWEs Tested | 22 |
| Total Test Cases | 60 |
| False Negatives Found | 52 |
| Detection Rate | 13.3% |

### CWEs NOT Yet Tested for False Negatives

These CWEs are implemented but haven't been tested for false negatives:

| Scanner | Untested CWEs |
|---------|---------------|
| Memory Safety | CWE-122, CWE-125, CWE-134, CWE-195, CWE-242, CWE-401, CWE-415, CWE-457, CWE-562, CWE-697, CWE-770, CWE-805, CWE-824 |
| Concurrency | CWE-366, CWE-367, CWE-479, CWE-764, CWE-765, CWE-820, CWE-821, CWE-833 |
| Crypto | CWE-295, CWE-321, CWE-326, CWE-798 |
| Control Flow | CWE-193, CWE-459, CWE-478, CWE-481, CWE-483, CWE-755, CWE-1069 |
| Boolean Logic | CWE-571, CWE-768, CWE-783, CWE-843, CWE-1077 |
| Web Security | CWE-129, CWE-606, CWE-789 |
| Path Security | CWE-185, CWE-400, CWE-426 |
| Generic | CWE-200, CWE-259, CWE-337, CWE-521, CWE-522, CWE-601, CWE-841 |

**Total Untested CWEs: 49**

---

## Part 4: Missing CWEs for Evaluation

### High Priority: OWASP/Top 25 Missing

| CWE | Name | SAST Detectable | Languages | Priority |
|-----|------|-----------------|-----------|----------|
| CWE-79 | XSS | Yes | JS, TS, PHP, Java, Python, C# | CRITICAL |
| CWE-89 | SQL Injection | Yes | All | CRITICAL |
| CWE-352 | CSRF | Partial | Java, PHP, Python | HIGH |
| CWE-22 | Path Traversal | Yes | All | HIGH |
| CWE-78 | OS Command Injection | Yes | All | HIGH |
| CWE-77 | Command Injection | Yes | All | HIGH |
| CWE-94 | Code Injection | Partial | JS, Python, PHP | HIGH |
| CWE-434 | File Upload | Partial | All | HIGH |
| CWE-502 | Deserialization | Yes | Java, Python, PHP, C# | HIGH |
| CWE-918 | SSRF | Yes | All | HIGH |
| CWE-862 | Missing Authorization | Partial | All | MEDIUM |
| CWE-863 | Incorrect Authorization | Partial | All | MEDIUM |
| CWE-287 | Improper Authentication | Partial | All | MEDIUM |
| CWE-269 | Privilege Management | Partial | All | MEDIUM |
| CWE-306 | Missing Auth for Function | Partial | All | MEDIUM |
| CWE-20 | Input Validation | Partial | All | MEDIUM |

### Medium Priority: SAST-Relevant Missing

| CWE | Name | Languages |
|-----|------|-----------|
| CWE-90 | LDAP Injection | Java, C#, Python |
| CWE-113 | HTTP Response Splitting | Java, Python, PHP |
| CWE-611 | XXE | Java, Python, PHP, C# |
| CWE-643 | XPath Injection | Java, C#, Python |
| CWE-917 | Expression Language Injection | Java |
| CWE-943 | NoSQL Injection | JS, Python |
| CWE-1336 | Template Injection | Python, C# |

### Lower Priority: Language-Specific

| CWE | Name | Languages |
|-----|------|-----------|
| CWE-98 | PHP File Inclusion | PHP |
| CWE-384 | Session Fixation | PHP |
| CWE-470 | Unsafe Reflection | Java |
| CWE-501 | Trust Boundary Violation | Java, C# |
| CWE-614 | Insecure Cookie | C#, JS |
| CWE-1004 | Missing HttpOnly | Java, PHP, C# |

---

## Sources

- [CWE Top 25 2024](https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html)
- [CISA 2025 CWE Top 25](https://www.cisa.gov/news-events/alerts/2025/12/11/2025-cwe-top-25-most-dangerous-software-weaknesses)
- [Mend.io SAST CWE List](https://docs.mend.io/platform/latest/sast-cwe-list)
- [Synopsys CWE Top 25 SAST](https://www.synopsys.com/software-integrity/static-analysis-tools-sast/cwe-top25.html)
