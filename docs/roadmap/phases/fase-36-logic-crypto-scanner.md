# Fase 36: Logic & Crypto Error Scanner (Week 176-182)

**Goal:** Detectie van cryptografische fouten, control flow logic errors, en boolean operator mistakes
**Status:** PLANNED
**Priority:** HIGH (security + correctness)
**Effort:** ~72 uur
**Dependencies:** Fase 31 (CWE Scanner), Fase 34-35 (Advanced Detectors)

---

## Executive Summary

Drie nieuwe scanner modules voor detectie van:
1. **CryptoErrorDetector** - Cryptografische implementatiefouten
2. **ControlFlowLogicDetector** - Loop/if/switch logic errors
3. **BooleanLogicDetector** - AND/OR/precedence/comparison fouten

**Research Basis:**
- `docs/crypto_vulnerabilities_research.md`
- `docs/control_flow_errors_reference.md`
- `docs/logical_operator_errors_reference.md`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOGIC & CRYPTO ERROR SCANNER                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    CryptoErrorDetector                          │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │     │
│  │  │ Hardcoded   │ │ Weak Algo   │ │ Timing      │ │ TLS/Cert  │ │     │
│  │  │ Keys        │ │ Detector    │ │ Attack      │ │ Validator │ │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                 ControlFlowLogicDetector                        │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │     │
│  │  │ Loop Error  │ │ If/Else     │ │ Switch/Case │ │ Exception │ │     │
│  │  │ Detector    │ │ Analyzer    │ │ Checker     │ │ Handler   │ │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                  BooleanLogicDetector                           │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │     │
│  │  │ Operator    │ │ Precedence  │ │ Comparison  │ │ Short-    │ │     │
│  │  │ Confusion   │ │ Analyzer    │ │ Checker     │ │ Circuit   │ │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  Output: SecurityFinding (SARIF compatible)                             │
│  Integration: SecurityOrchestrator                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module 1: CryptoErrorDetector (24 uur)

### 1.1 Hardcoded Secrets Detector

**CWE-321, CWE-798**

```python
# DETECT: Hardcoded keys/secrets
ENCRYPTION_KEY = b'my-super-secret-key-12345'  # CWE-321
API_KEY = "sk_live_abcd1234efgh5678"           # CWE-798
password = "admin123"                           # CWE-798
```

**Detection Patterns:**
| Pattern | Regex/AST | Severity |
|---------|-----------|----------|
| `key = "..."` (16+ chars) | Regex | HIGH |
| `password = "..."` | Regex | CRITICAL |
| `secret = "..."` | Regex | CRITICAL |
| `api_key = "..."` | Regex | HIGH |
| Base64 encoded strings (40+ chars) | Regex | MEDIUM |
| High entropy strings | Entropy calc | MEDIUM |

### 1.2 Weak Algorithm Detector

**CWE-327, CWE-328**

```python
# DETECT: Weak/broken algorithms
import hashlib
hashlib.md5(data)           # CWE-328: Broken hash
hashlib.sha1(data)          # CWE-328: Weak hash
from Crypto.Cipher import DES  # CWE-327: Broken cipher

# DETECT: ECB mode
cipher = AES.new(key, AES.MODE_ECB)  # CWE-327: ECB mode

# DETECT: Weak random
import random
random.randint(0, 100)  # CWE-330: Not cryptographically secure
```

**Blocklist:**
| Algorithm | Replacement | CWE |
|-----------|-------------|-----|
| MD5 | SHA-256, SHA-3 | CWE-328 |
| SHA1 | SHA-256, SHA-3 | CWE-328 |
| DES | AES-256 | CWE-327 |
| 3DES | AES-256 | CWE-327 |
| RC4 | AES-GCM | CWE-327 |
| ECB mode | GCM, CBC+HMAC | CWE-327 |
| `random` | `secrets` | CWE-330 |

### 1.3 Timing Attack Detector

**CWE-208**

```python
# DETECT: Non-constant-time comparison
if user_token == stored_token:  # Timing attack vulnerable!
    authenticate()

# CORRECT:
import hmac
if hmac.compare_digest(user_token, stored_token):
    authenticate()
```

**Patterns:**
- `==` comparison of secrets/tokens
- String comparison in auth context
- Loop-based byte comparison

### 1.4 Certificate Validation Detector

**CWE-295, CWE-296**

```python
# DETECT: Disabled certificate validation
requests.get(url, verify=False)  # CWE-295

# DETECT: Custom SSL context without verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # CWE-295
ssl_context.verify_mode = ssl.CERT_NONE  # CWE-295
```

---

## Module 2: ControlFlowLogicDetector (24 uur)

### 2.1 Loop Error Detector

**CWE-193, CWE-835**

```java
// DETECT: Off-by-one (<=length)
for (int i = 0; i <= arr.length; i++) {  // CWE-193
    arr[i] = 0;  // Buffer overflow at i=length
}

// DETECT: Infinite loop
while (true) {  // CWE-835 (if no break)
    process();
}

// DETECT: Empty loop body
for (int i = 0; i < n; i++);  // Semicolon = empty body
    doSomething();  // Not in loop!

// DETECT: Float loop counter
for (float f = 0.0f; f < 1.0f; f += 0.1f) {  // Precision issues
    process(f);
}
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| CF001 | `<= array.length` | CWE-193 |
| CF002 | `while(true)` without break | CWE-835 |
| CF003 | `for(...);` (semicolon after) | Logic |
| CF004 | Float loop counter | CERT FLP30-C |
| CF005 | Loop var modified in body | Logic |

### 2.2 If/Else Analyzer

**CWE-481, CWE-483**

```c
// DETECT: Assignment in condition
if (x = getValue()) {  // CWE-481: = instead of ==
    process();
}

// DETECT: Dangling else
if (a)
    if (b)
        doB();
else  // CWE-483: Belongs to inner if, not outer!
    doElse();

// DETECT: Missing braces (Apple goto fail pattern)
if (condition)
    statement1();
    statement2();  // NOT in if block!
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| CF010 | `if (x = ...)` | CWE-481 |
| CF011 | Dangling else | CWE-483 |
| CF012 | Single-line if without braces | Style/Risk |
| CF013 | Duplicate statement (goto fail) | Logic |

### 2.3 Switch/Case Checker

**CWE-484, CWE-478**

```java
// DETECT: Missing break (fall-through)
switch (value) {
    case 1:
        doOne();
        // CWE-484: Missing break!
    case 2:
        doTwo();
        break;
}

// DETECT: Missing default
switch (status) {  // CWE-478
    case ACTIVE: handle(); break;
    case INACTIVE: handle(); break;
    // No default case!
}

// DETECT: Enum not exhaustive
enum State { A, B, C }
switch (state) {
    case A: break;
    case B: break;
    // C not handled!
}
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| CF020 | Case without break | CWE-484 |
| CF021 | Switch without default | CWE-478 |
| CF022 | Enum case not exhaustive | Logic |
| CF023 | Duplicate case value | Logic |

### 2.4 Exception Handler Analyzer

**CWE-1069, CWE-459**

```java
// DETECT: Empty catch block
try {
    riskyOperation();
} catch (Exception e) {  // CWE-1069
    // Empty!
}

// DETECT: Catch and ignore
try {
    process();
} catch (Exception e) {
    // Only logging, no handling
    log.error(e);
}

// DETECT: Missing finally cleanup
FileInputStream fis = new FileInputStream(file);
try {
    process(fis);
} catch (Exception e) {
    throw e;
}
// CWE-459: fis never closed if exception!
```

---

## Module 3: BooleanLogicDetector (24 uur)

### 3.1 Operator Confusion Detector

**CWE-480**

```java
// DETECT: Bitwise instead of logical
if (a > 0 & b > 0) {  // CWE-480: & instead of &&
    process();
}

if (isAdmin | isEditor) {  // CWE-480: | instead of ||
    grantAccess();
}
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| BL001 | `&` in boolean context | CWE-480 |
| BL002 | `\|` in boolean context | CWE-480 |
| BL003 | `=` in condition | CWE-481 |

### 3.2 Precedence Analyzer

**CWE-783**

```c
// DETECT: Missing parentheses in bitwise
if (flags & MASK == VALUE) {  // CWE-783: & vs ==
    process();
}

// DETECT: AND/OR precedence
if (a || b && c) {  // May not be intended grouping
    process();
}

// DETECT: Macro without parentheses
#define SQUARE(x) x * x  // CWE-783
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| BL010 | `& ... ==` without parens | CWE-783 |
| BL011 | `\|\| ... &&` without parens | CWE-783 |
| BL012 | Macro args without parens | CWE-783 |
| BL013 | Ternary precedence ambiguity | CWE-783 |

### 3.3 Comparison Checker

**CWE-480, CWE-843, CWE-1077**

```javascript
// DETECT: == instead of === (JavaScript)
if (userInput == "admin") {  // CWE-843: Type coercion
    grantAccess();
}

// DETECT: Float equality
if (a == 0.3) {  // CWE-1077
    process();
}

// DETECT: Chained comparison (non-Python)
if (0 < x < 10) {  // CWE-480: Wrong in C/Java/JS
    process();
}
```

**Detection Rules:**
| Rule ID | Pattern | CWE |
|---------|---------|-----|
| BL020 | `==` in JS (should be `===`) | CWE-843 |
| BL021 | Float `==` comparison | CWE-1077 |
| BL022 | Chained comparison (non-Python) | CWE-480 |
| BL023 | String `==` in Java | Logic |

### 3.4 Short-Circuit Analyzer

**CWE-768**

```java
// DETECT: Null check AFTER dereference
if (user.isActive() && user != null) {  // CWE-476
    process();
}

// DETECT: Side effect in short-circuit
if (condition && counter++ > 0) {  // CWE-768
    // counter++ may not execute
}
```

### 3.5 Tautology/Contradiction Detector

**CWE-570, CWE-571**

```java
// DETECT: Always true
if (x >= 0 || x < 0) {  // CWE-571: Tautology
    process();
}

// DETECT: Always false
if (x > 5 && x < 3) {  // CWE-570: Contradiction
    process();  // Dead code
}

// DETECT: Redundant boolean
if (isValid == true) {  // Redundant
    process();
}
```

---

## Implementation Plan

### Phase 36.1: CryptoErrorDetector (Week 176-177)

| Task | Description | Effort |
|------|-------------|--------|
| 36.1.1 | Hardcoded secrets detector | 6h |
| 36.1.2 | Weak algorithm blocklist | 4h |
| 36.1.3 | Timing attack patterns | 4h |
| 36.1.4 | Certificate validation checker | 4h |
| 36.1.5 | Unit tests | 6h |

### Phase 36.2: ControlFlowLogicDetector (Week 178-179)

| Task | Description | Effort |
|------|-------------|--------|
| 36.2.1 | Loop error detector | 6h |
| 36.2.2 | If/else analyzer | 4h |
| 36.2.3 | Switch/case checker | 4h |
| 36.2.4 | Exception handler analyzer | 4h |
| 36.2.5 | Unit tests | 6h |

### Phase 36.3: BooleanLogicDetector (Week 180-181)

| Task | Description | Effort |
|------|-------------|--------|
| 36.3.1 | Operator confusion detector | 4h |
| 36.3.2 | Precedence analyzer | 4h |
| 36.3.3 | Comparison checker | 4h |
| 36.3.4 | Short-circuit analyzer | 4h |
| 36.3.5 | Tautology/contradiction detector | 4h |
| 36.3.6 | Unit tests | 4h |

### Phase 36.4: Integration (Week 182)

| Task | Description | Effort |
|------|-------------|--------|
| 36.4.1 | SecurityOrchestrator integration | 2h |
| 36.4.2 | SARIF output formatting | 2h |
| 36.4.3 | Integration tests | 4h |
| 36.4.4 | Documentation | 2h |

---

## File Structure

```
backend/app/services/security_scanner/adapters/
├── crypto_error_detector.py
│   ├── CryptoErrorDetector
│   ├── HardcodedSecretsDetector
│   ├── WeakAlgorithmDetector
│   ├── TimingAttackDetector
│   └── CertValidationDetector
├── control_flow_logic_detector.py
│   ├── ControlFlowLogicDetector
│   ├── LoopErrorDetector
│   ├── IfElseAnalyzer
│   ├── SwitchCaseChecker
│   └── ExceptionHandlerAnalyzer
└── boolean_logic_detector.py
    ├── BooleanLogicDetector
    ├── OperatorConfusionDetector
    ├── PrecedenceAnalyzer
    ├── ComparisonChecker
    ├── ShortCircuitAnalyzer
    └── TautologyDetector

backend/tests/unit/security_scanner/
├── test_crypto_error_detector.py
├── test_control_flow_logic_detector.py
└── test_boolean_logic_detector.py
```

---

## Detection Rules Summary

### Crypto Rules (12)

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| CR001 | Hardcoded encryption key | CRITICAL | CWE-321 |
| CR002 | Hardcoded password | CRITICAL | CWE-798 |
| CR003 | Hardcoded API key | HIGH | CWE-798 |
| CR004 | MD5 hash usage | HIGH | CWE-328 |
| CR005 | SHA1 hash usage | MEDIUM | CWE-328 |
| CR006 | DES/3DES/RC4 usage | HIGH | CWE-327 |
| CR007 | ECB mode usage | HIGH | CWE-327 |
| CR008 | Non-secure random | MEDIUM | CWE-330 |
| CR009 | Timing-vulnerable comparison | HIGH | CWE-208 |
| CR010 | Certificate validation disabled | CRITICAL | CWE-295 |
| CR011 | Hostname verification disabled | HIGH | CWE-295 |
| CR012 | Weak TLS version | MEDIUM | CWE-326 |

### Control Flow Rules (12)

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| CF001 | Off-by-one (<= length) | HIGH | CWE-193 |
| CF002 | Infinite loop (while true) | MEDIUM | CWE-835 |
| CF003 | Empty loop body | HIGH | Logic |
| CF004 | Float loop counter | MEDIUM | CERT |
| CF010 | Assignment in condition | HIGH | CWE-481 |
| CF011 | Dangling else | MEDIUM | CWE-483 |
| CF012 | Missing braces risk | LOW | Style |
| CF020 | Missing break in case | HIGH | CWE-484 |
| CF021 | Missing default case | MEDIUM | CWE-478 |
| CF022 | Enum not exhaustive | MEDIUM | Logic |
| CF030 | Empty catch block | HIGH | CWE-1069 |
| CF031 | Missing finally cleanup | MEDIUM | CWE-459 |

### Boolean Logic Rules (12)

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| BL001 | Bitwise & in boolean | HIGH | CWE-480 |
| BL002 | Bitwise \| in boolean | HIGH | CWE-480 |
| BL010 | Missing parens (& vs ==) | HIGH | CWE-783 |
| BL011 | AND/OR precedence ambiguity | MEDIUM | CWE-783 |
| BL012 | Macro without parens | HIGH | CWE-783 |
| BL020 | == instead of === (JS) | MEDIUM | CWE-843 |
| BL021 | Float equality | MEDIUM | CWE-1077 |
| BL022 | Chained comparison | HIGH | CWE-480 |
| BL030 | Null check after deref | CRITICAL | CWE-476 |
| BL031 | Side effect in short-circuit | MEDIUM | CWE-768 |
| BL040 | Tautology (always true) | MEDIUM | CWE-571 |
| BL041 | Contradiction (always false) | MEDIUM | CWE-570 |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Crypto rules | 12 patterns |
| Control flow rules | 12 patterns |
| Boolean logic rules | 12 patterns |
| Languages supported | Python, Java, C#, JavaScript, C/C++ |
| False positive rate | <15% |
| Test coverage | >90% |

---

## References

- [docs/crypto_vulnerabilities_research.md](../../crypto_vulnerabilities_research.md)
- [docs/control_flow_errors_reference.md](../../control_flow_errors_reference.md)
- [docs/logical_operator_errors_reference.md](../../logical_operator_errors_reference.md)
- [CWE-310: Cryptographic Issues](https://cwe.mitre.org/data/definitions/310.html)
- [CWE-691: Insufficient Control Flow Management](https://cwe.mitre.org/data/definitions/691.html)
- [CWE-1024: Comparison of Incompatible Types](https://cwe.mitre.org/data/definitions/1024.html)
