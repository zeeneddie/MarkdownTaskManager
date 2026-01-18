# Complete Software Error Taxonomy

**Doel:** Uitgebreide classificatie van software errors voor detectie in MarQed platform
**Auteur:** Claude Analysis
**Datum:** 2026-01-15
**Status:** Research Document

---

## Executive Summary

Dit document definieert een **multi-dimensionale taxonomie** voor software errors, georganiseerd naar:
1. **Impact Type** - Wat is het gevolg? (crash, data loss, deadlock, performance)
2. **Root Cause Category** - Wat is de fundamentele oorzaak?
3. **Detection Phase** - Wanneer kan het gedetecteerd worden?
4. **Language Affinity** - Welke talen zijn gevoelig?
5. **CWE/Standards Mapping** - Formele classificaties

---

## 1. IMPACT-BASED TAXONOMY

### 1.1 CRASHES (System/Application Termination)

| Sub-Category | Description | Detection | CWE |
|--------------|-------------|-----------|-----|
| **Null Dereference** | Access via null/nil/None pointer | Static analysis | CWE-476 |
| **Unhandled Exception** | Exception zonder catch | Static + Runtime | CWE-248 |
| **Stack Overflow** | Recursie zonder base case | Static analysis | CWE-121 |
| **Heap Corruption** | Invalid memory write | Runtime (ASAN) | CWE-122 |
| **Use After Free** | Access freed memory | Static + Runtime | CWE-416 |
| **Double Free** | Free same memory twice | Static + Runtime | CWE-415 |
| **Buffer Overflow** | Write beyond bounds | Static analysis | CWE-120 |
| **Integer Overflow** | Arithmetic overflow | Static analysis | CWE-190 |
| **Division by Zero** | Divide by zero | Static analysis | CWE-369 |
| **Assertion Failure** | assert() fails | Runtime | CWE-617 |
| **Segmentation Fault** | Invalid memory access | Runtime | CWE-787 |
| **Signal Handling** | Improper signal handler | Static analysis | CWE-479 |
| **Resource Exhaustion** | OOM, file descriptors | Runtime monitoring | CWE-400 |

### 1.2 DATA LOSS / CORRUPTION

| Sub-Category | Description | Detection | CWE |
|--------------|-------------|-----------|-----|
| **Race Condition (Data)** | Concurrent write without sync | Static + Dynamic | CWE-362 |
| **TOCTOU** | Time-of-check to time-of-use | Static analysis | CWE-367 |
| **Incomplete Transaction** | Partial commit/rollback | Code review | CWE-665 |
| **Missing Atomicity** | Non-atomic multi-step ops | Static analysis | CWE-362 |
| **Buffer Over-read** | Read beyond bounds | Static analysis | CWE-126 |
| **Buffer Over-write** | Write beyond bounds | Static analysis | CWE-787 |
| **Type Confusion** | Wrong type interpretation | Static analysis | CWE-843 |
| **Serialization Error** | Corrupt serialize/deserialize | Testing | CWE-502 |
| **Encoding Error** | Character encoding mismatch | Testing | CWE-838 |
| **Truncation** | Data truncated silently | Static analysis | CWE-197 |
| **Precision Loss** | Float/int conversion | Static analysis | CWE-681 |
| **Missing Backup** | No recovery point | Architecture review | N/A |
| **Cascade Delete** | Unintended related deletes | Code review | N/A |

### 1.3 DEADLOCKS / HANGS

| Sub-Category | Description | Detection | CWE |
|--------------|-------------|-----------|-----|
| **Lock Order Violation** | Inconsistent lock acquisition | Static analysis | CWE-833 |
| **Nested Lock** | Lock within lock same thread | Static analysis | CWE-833 |
| **Database Deadlock** | Circular DB row locks | Runtime monitoring | CWE-833 |
| **Thread Starvation** | Low-priority never runs | Runtime profiling | CWE-410 |
| **Resource Starvation** | Pool exhausted | Runtime monitoring | CWE-400 |
| **Infinite Loop** | Loop never terminates | Static + Timeout | CWE-835 |
| **Infinite Recursion** | Recursion never ends | Static analysis | CWE-674 |
| **Blocking I/O** | Sync I/O blocks thread | Code review | N/A |
| **Missing Timeout** | Network call without timeout | Static analysis | CWE-1088 |
| **Livelock** | Threads busy but no progress | Runtime profiling | CWE-833 |
| **Priority Inversion** | High-prio waits on low-prio | Runtime analysis | N/A |
| **Convoy Effect** | Serial bottleneck | Profiling | N/A |

### 1.4 PERFORMANCE DEGRADATION

| Sub-Category | Description | Detection | CWE |
|--------------|-------------|-----------|-----|
| **N+1 Query** | Query per item in loop | Static analysis | CWE-1073 |
| **Cartesian Join** | Missing WHERE clause | Query analysis | CWE-1049 |
| **Missing Index** | Full table scan | EXPLAIN analysis | N/A |
| **Memory Leak** | Allocated never freed | Runtime (Valgrind) | CWE-401 |
| **Connection Leak** | DB/HTTP conn not closed | Runtime monitoring | CWE-772 |
| **File Handle Leak** | Files not closed | Static + Runtime | CWE-775 |
| **Unbounded Growth** | Collection grows forever | Code review | CWE-770 |
| **Algorithmic Complexity** | O(n²) where O(n) possible | Code review | CWE-407 |
| **Thundering Herd** | Mass concurrent requests | Architecture review | CWE-400 |
| **Cache Miss Storm** | Cold cache causes overload | Load testing | N/A |
| **Regex Catastrophe** | ReDoS vulnerable regex | Static analysis | CWE-1333 |
| **Excessive Logging** | Log in hot path | Profiling | CWE-779 |
| **Busy Wait** | Spin loop instead of sleep | Static analysis | CWE-1088 |
| **Premature Optimization** | Complex code, no benefit | Code review | N/A |
| **Missing Pagination** | Load all records | Code review | CWE-770 |
| **Synchronous Blocking** | Sync call in async context | Code review | N/A |

---

## 2. ROOT CAUSE TAXONOMY

### 2.1 Memory Management Errors

```
MEMORY_ERRORS/
├── Allocation/
│   ├── Null allocation (malloc returns NULL)
│   ├── Zero-size allocation
│   ├── Integer overflow in size calculation
│   └── Excessive allocation (OOM)
├── Access/
│   ├── Null pointer dereference
│   ├── Dangling pointer (use after free)
│   ├── Wild pointer (uninitialized)
│   ├── Buffer overflow (read/write)
│   └── Out-of-bounds array access
├── Deallocation/
│   ├── Double free
│   ├── Free of stack memory
│   ├── Free of invalid pointer
│   ├── Memory leak (never freed)
│   └── Use after free
└── Type Safety/
    ├── Type confusion
    ├── Invalid cast
    └── Alignment violation
```

### 2.2 Concurrency Errors

```
CONCURRENCY_ERRORS/
├── Race Conditions/
│   ├── Data race (unsynchronized access)
│   ├── TOCTOU (time-of-check time-of-use)
│   ├── Check-then-act without atomicity
│   └── Read-modify-write without atomicity
├── Deadlocks/
│   ├── Lock order violation
│   ├── Self-deadlock (recursive lock)
│   ├── Resource cycle deadlock
│   └── Distributed deadlock
├── Livelocks/
│   ├── Retry storm
│   ├── Mutual yielding
│   └── Priority inversion
├── Starvation/
│   ├── Thread starvation
│   ├── Lock starvation
│   └── Resource starvation
└── Atomicity Violations/
    ├── Compound operation not atomic
    ├── Partial update visible
    └── Lost update
```

### 2.3 Resource Management Errors

```
RESOURCE_ERRORS/
├── Leaks/
│   ├── Memory leak
│   ├── File handle leak
│   ├── Socket leak
│   ├── Database connection leak
│   ├── Thread leak
│   └── Lock leak (not released)
├── Exhaustion/
│   ├── Out of memory
│   ├── Out of file descriptors
│   ├── Out of disk space
│   ├── Out of threads
│   └── Connection pool exhaustion
├── Improper Cleanup/
│   ├── Missing finally/defer
│   ├── Exception skips cleanup
│   ├── Early return skips cleanup
│   └── Cleanup in wrong order
└── Initialization/
    ├── Uninitialized variable
    ├── Partial initialization
    ├── Double initialization
    └── Missing null check after allocation
```

### 2.4 Logic Errors

```
LOGIC_ERRORS/
├── Control Flow/
│   ├── Off-by-one error
│   ├── Infinite loop
│   ├── Unreachable code
│   ├── Missing break in switch
│   ├── Wrong operator (= vs ==)
│   └── Inverted condition
├── Boundary/
│   ├── Integer overflow/underflow
│   ├── Floating point precision
│   ├── Truncation
│   ├── Sign error (signed/unsigned)
│   └── Range check missing
├── State/
│   ├── Invalid state transition
│   ├── Missing state validation
│   ├── State corruption
│   └── Stale state
└── Algorithm/
    ├── Wrong algorithm choice
    ├── Incorrect implementation
    ├── Edge case not handled
    └── Complexity explosion
```

### 2.5 Input/Output Errors

```
IO_ERRORS/
├── Input Validation/
│   ├── Missing validation
│   ├── Insufficient validation
│   ├── Wrong validation logic
│   └── Bypass of validation
├── Injection/
│   ├── SQL injection
│   ├── Command injection
│   ├── XSS (script injection)
│   ├── LDAP injection
│   ├── XML/XXE injection
│   └── Path traversal
├── Encoding/
│   ├── Character encoding mismatch
│   ├── Missing escaping
│   ├── Double encoding
│   └── Null byte injection
└── Serialization/
    ├── Deserialization of untrusted data
    ├── Version mismatch
    ├── Schema evolution error
    └── Circular reference
```

### 2.6 Error Handling Errors

```
ERROR_HANDLING_ERRORS/
├── Missing Handling/
│   ├── Uncaught exception
│   ├── Ignored return code
│   ├── Empty catch block
│   └── Missing error check
├── Incorrect Handling/
│   ├── Wrong exception caught
│   ├── Swallowed exception
│   ├── Exception in exception handler
│   └── Inconsistent error codes
├── Information Leakage/
│   ├── Stack trace exposed
│   ├── Internal paths exposed
│   ├── Database errors exposed
│   └── Sensitive data in error
└── Recovery/
    ├── Partial rollback
    ├── Inconsistent state after error
    ├── Missing cleanup on error
    └── Retry without backoff
```

---

## 3. DETECTION PHASE TAXONOMY

| Phase | When | Methods | Effectiveness |
|-------|------|---------|---------------|
| **Design Review** | Before coding | Architecture review, threat modeling | Prevents structural issues |
| **Static Analysis** | At commit | AST analysis, pattern matching, data flow | 40-60% of bugs |
| **Compile Time** | Build | Type checking, warnings | Language-dependent |
| **Unit Testing** | Development | Test execution, mocking | Logic errors |
| **Integration Testing** | Pre-deploy | System tests, API tests | Interface errors |
| **Dynamic Analysis** | Runtime | ASAN, TSAN, Valgrind | Memory/concurrency |
| **Load Testing** | Pre-production | Performance tests, stress tests | Scalability issues |
| **Production Monitoring** | Live | APM, logging, metrics | Runtime issues |
| **Post-Mortem** | After incident | Root cause analysis | Learning |

---

## 4. LANGUAGE AFFINITY MATRIX

| Error Type | C/C++ | Java | Python | C# | JavaScript | Go | Rust |
|------------|-------|------|--------|----|-----------|----|------|
| Null Deref | HIGH | MEDIUM | LOW | MEDIUM | MEDIUM | LOW | NONE |
| Buffer Overflow | HIGH | NONE | NONE | NONE | NONE | NONE | NONE |
| Memory Leak | HIGH | LOW | LOW | LOW | LOW | LOW | LOW |
| Use After Free | HIGH | NONE | NONE | NONE | NONE | NONE | NONE |
| Data Race | HIGH | MEDIUM | HIGH | MEDIUM | HIGH | MEDIUM | LOW |
| Deadlock | MEDIUM | MEDIUM | MEDIUM | MEDIUM | LOW | MEDIUM | LOW |
| Integer Overflow | HIGH | LOW | LOW | LOW | LOW | LOW | LOW |
| Injection | MEDIUM | MEDIUM | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM |
| Resource Leak | HIGH | MEDIUM | MEDIUM | MEDIUM | MEDIUM | LOW | LOW |
| Type Confusion | HIGH | LOW | HIGH | LOW | HIGH | NONE | NONE |

**Legend:** HIGH = Zeer gevoelig, MEDIUM = Mogelijk, LOW = Zeldzaam, NONE = Taal voorkomt dit

---

## 5. EXTENDED CLASSIFICATION SYSTEMS

### 5.1 CWE (Common Weakness Enumeration)
**Scope:** Security-focused weaknesses
**Maintained by:** MITRE
**Categories relevant:**
- CWE-119: Buffer Errors
- CWE-189: Numeric Errors
- CWE-399: Resource Management Errors
- CWE-361: Concurrency Issues
- CWE-703: Improper Error Handling

### 5.2 OWASP Top 10
**Scope:** Web application security
**Categories:**
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration

### 5.3 CERT Coding Standards
**Scope:** Secure coding per language
**Standards:**
- CERT C Coding Standard
- CERT C++ Coding Standard
- CERT Java Coding Standard
- CERT Python Coding Standard

### 5.4 ISO/IEC 25010 (Quality Model)
**Scope:** Software quality characteristics
**Relevant:**
- Reliability → Maturity, Fault Tolerance, Recoverability
- Performance Efficiency → Time Behavior, Resource Utilization
- Security → Confidentiality, Integrity, Availability

### 5.5 CISQ (Consortium for IT Software Quality)
**Scope:** Automated measurement of software quality
**Categories:**
- Reliability: crashes, data corruption
- Performance Efficiency: resource usage
- Security: vulnerabilities
- Maintainability: code complexity

### 5.6 SonarQube Rules
**Scope:** Code quality and security
**Categories:**
- Bugs: Reliability issues
- Vulnerabilities: Security issues
- Code Smells: Maintainability issues
- Security Hotspots: Review needed

### 5.7 SEI CERT Oracle Coding Standard
**Scope:** Oracle/Java specific
**Categories:**
- Declarations and Initialization
- Expressions
- Integers
- Floating Point
- Characters and Strings
- Memory Management
- Input/Output
- Concurrency

### 5.8 NASA/JPL Coding Standards
**Scope:** Safety-critical systems
**Rules:**
- Restrict recursion
- Fixed loop bounds
- No dynamic memory after init
- Check return values
- Limited pointer use

### 5.9 MISRA (Motor Industry Software Reliability Association)
**Scope:** Automotive/embedded C/C++
**Categories:**
- Required rules (must follow)
- Advisory rules (should follow)
- Mandatory rules (no deviation)

### 5.10 Custom MarQed Categories (Proposed)

```
MARQED_TAXONOMY/
├── Severity/
│   ├── CRITICAL - System crash, data loss, security breach
│   ├── HIGH - Major functionality broken, performance severe
│   ├── MEDIUM - Feature degraded, minor data issues
│   └── LOW - Cosmetic, minor inconvenience
├── Detectability/
│   ├── STATIC - Can detect at code analysis
│   ├── DYNAMIC - Needs runtime analysis
│   ├── TESTING - Needs specific test cases
│   └── MONITORING - Only visible in production
├── Frequency/
│   ├── ALWAYS - Happens every time
│   ├── OFTEN - >50% of executions
│   ├── SOMETIMES - 10-50% of executions
│   ├── RARELY - <10% of executions
│   └── EDGE_CASE - Specific conditions only
├── Fix Complexity/
│   ├── TRIVIAL - One-line fix
│   ├── SIMPLE - Localized change
│   ├── MODERATE - Multiple files/components
│   ├── COMPLEX - Architectural change
│   └── REDESIGN - Fundamental redesign needed
└── Business Impact/
    ├── REVENUE - Direct revenue loss
    ├── REPUTATION - Brand damage
    ├── LEGAL - Compliance/legal issues
    ├── OPERATIONAL - Process disruption
    └── TECHNICAL - Tech debt increase
```

---

## 6. DETECTION RULES MAPPING

### 6.1 Static Analysis Rules (OpenGrep/Custom)

| Error Type | Pattern | Rule Complexity |
|------------|---------|-----------------|
| Null deref | `if (x) { ... } x.method()` outside if | MEDIUM |
| SQL Injection | `query + user_input` | LOW |
| N+1 Query | Loop containing DB call | MEDIUM |
| Resource Leak | Open without close in same scope | MEDIUM |
| Infinite Loop | `while(true)` without break | LOW |
| Missing Timeout | HTTP client without timeout config | LOW |
| Empty Catch | `catch { }` or `except: pass` | LOW |
| Hardcoded Secret | `password = "..."` | LOW |

### 6.2 AST Patterns (Per Language)

**Python:**
```python
# N+1 Query Detection
for item in items:           # Loop
    db.query(item.id)        # DB call inside loop

# Resource Leak
f = open("file.txt")         # Open
# ... no f.close() or context manager
```

**C#:**
```csharp
// Null Dereference Risk
if (obj != null) { ... }
obj.Method();  // Outside the if block

// Lock Order Violation
lock(lockA) {
    lock(lockB) { ... }  // In one place
}
lock(lockB) {
    lock(lockA) { ... }  // Different order elsewhere
}
```

**JavaScript:**
```javascript
// Missing await
async function getData() {
    fetch(url);  // Missing await = fire and forget
}

// Callback Hell (complexity)
fs.readFile(f1, (err, data) => {
    fs.readFile(f2, (err, data) => {
        fs.readFile(f3, (err, data) => {
            // Deeply nested
        });
    });
});
```

---

## 7. IMPLEMENTATION RECOMMENDATIONS

### 7.1 Priority Order for MarQed

| Priority | Category | Why |
|----------|----------|-----|
| P0 | Crashes (Null, Buffer) | Direct user impact |
| P0 | Security (Injection) | Compliance, breach risk |
| P1 | Data Loss (Race, Transaction) | Business critical |
| P1 | Resource Leaks | Production stability |
| P2 | Deadlocks | Hard to diagnose |
| P2 | Performance (N+1, Memory) | Scalability |
| P3 | Code Quality (Complexity) | Maintainability |

### 7.2 Integration Points

1. **CWE Scanner (Fase 31)** - Add new rules
2. **Knowledge Base (KB1-KB5)** - Add taxonomy context
3. **Betty Agent** - Quality patterns
4. **Diana Agent** - Security patterns
5. **Stability Analyzer (Fase 21)** - Resource leaks

### 7.3 New Scanner Modules Needed

| Module | Detects | Effort |
|--------|---------|--------|
| `DeadlockDetector` | Lock ordering, nested locks | 24h |
| `PerformancePatternDetector` | N+1, complexity, unbounded | 32h |
| `DataIntegrityDetector` | Race conditions, TOCTOU | 24h |
| `ResourceLifecycleDetector` | Leaks, missing cleanup | 16h |

---

## 8. NEXT STEPS

1. **Fase 24-KB:** Integreer taxonomie in Knowledge Base
2. **Fase 34 (Proposed):** Implement DeadlockDetector
3. **Fase 35 (Proposed):** Implement PerformancePatternDetector
4. **Scanner Rules:** Add patterns to OpenGrep configuration

---

## References

- [CWE List](https://cwe.mitre.org/data/definitions/699.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CERT Coding Standards](https://wiki.sei.cmu.edu/confluence/display/seccode)
- [ISO/IEC 25010](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010)
- [CISQ Standards](https://www.it-cisq.org/standards/)
- [NASA JPL C Coding Standard](https://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf)
- [MISRA C Guidelines](https://www.misra.org.uk/)
