# Fase 38: Memory Safety Scanner - Implementation Plan

## Overview

Implementatie van een Memory Safety Scanner die de 5 ontbrekende CWE Top 25 gaps dekt:

| Rank | CWE | Description | Priority |
|------|-----|-------------|----------|
| 1 | **CWE-787** | Out-of-bounds Write | CRITICAL |
| 4 | **CWE-416** | Use After Free | CRITICAL |
| 7 | **CWE-125** | Out-of-bounds Read | HIGH |
| 17 | **CWE-119** | Buffer Overflow | CRITICAL |
| 21 | **CWE-362** | Race Condition | HIGH |

**Doel: 100% CWE Top 25 dekking**

---

## Architecture

```
SecurityOrchestrator (parallel execution)
├── ... existing scanners ...
├── MemorySafetyDetector      → ScannerType.MEMORY_SAFETY
└── ConcurrencyErrorDetector  → ScannerType.CONCURRENCY_ERROR
```

### Scanner 1: MemorySafetyDetector (16 regels)

Detecteert memory safety issues in C, C++, en Rust (unsafe blocks).

### Scanner 2: ConcurrencyErrorDetector (8 regels)

Detecteert race conditions en thread safety issues in multi-threaded code.

---

## Files to Create

### Scanner Implementations

| File | Scanner | CWE's |
|------|---------|-------|
| `adapters/memory_safety_detector.py` | MemorySafetyDetector | CWE-787, 416, 125, 119, 122, 124, 126, 127, 415, 590 |
| `adapters/concurrency_error_detector.py` | ConcurrencyErrorDetector | CWE-362, 366, 367, 820, 821, 764, 765, 833 |

### Tests

| File | Tests |
|------|-------|
| `tests/unit/security_scanner/test_memory_safety_detector.py` | ~25 tests |
| `tests/unit/security_scanner/test_concurrency_error_detector.py` | ~15 tests |

### Files to Modify

| File | Changes |
|------|---------|
| `models/findings.py` | Add 2 ScannerType enums |
| `adapters/__init__.py` | Export new scanners |
| `orchestrator.py` | Register scanners + add to LANGUAGE_SCANNERS |

---

## Scanner 1: MemorySafetyDetector (16 regels)

### Rules Definition

```python
MEMORY_SAFETY_RULES = [
    # ==========================================================================
    # BUFFER OVERFLOW (CWE-119, CWE-787, CWE-125)
    # ==========================================================================

    # MS001: Unsafe string copy functions
    MemorySafetyRule(
        id="MS001",
        title="Unsafe string copy function (strcpy, strcat)",
        description="strcpy/strcat do not check buffer bounds, leading to buffer overflow.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-119", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "c": r'\b(strcpy|strcat|sprintf|vsprintf)\s*\(',
            "cpp": r'\b(strcpy|strcat|sprintf|vsprintf)\s*\(',
        },
        fix_suggestion="Use strncpy, strncat, snprintf, or C++ std::string instead.",
    ),

    # MS002: Unsafe gets() function
    MemorySafetyRule(
        id="MS002",
        title="Use of gets() function",
        description="gets() cannot limit input size, always causes buffer overflow vulnerability.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-119", "CWE-787", "CWE-242"],
        category="buffer_overflow",
        patterns={
            "c": r'\bgets\s*\(',
            "cpp": r'\bgets\s*\(',
        },
        fix_suggestion="Use fgets() with explicit buffer size limit.",
    ),

    # MS003: Unchecked array index
    MemorySafetyRule(
        id="MS003",
        title="Array access without bounds checking",
        description="Array indexed with variable without prior bounds check.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-125", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "c": r'\w+\s*\[\s*\w+\s*\](?!\s*=)',  # array[var] not in assignment context
            "cpp": r'\w+\s*\[\s*\w+\s*\](?!\s*=)',
        },
        context_keywords=["for", "while", "index", "idx", "i", "j"],
        fix_suggestion="Add bounds checking: if (index >= 0 && index < array_size)",
    ),

    # MS004: scanf without width specifier
    MemorySafetyRule(
        id="MS004",
        title="scanf/sscanf without width specifier",
        description="scanf %s without width limit can overflow buffer.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "c": r'scanf\s*\([^)]*%[^0-9]*s',
            "cpp": r'scanf\s*\([^)]*%[^0-9]*s',
        },
        fix_suggestion="Use width specifier: scanf(\"%99s\", buffer) for 100-byte buffer.",
    ),

    # MS005: memcpy/memmove without size validation
    MemorySafetyRule(
        id="MS005",
        title="memcpy/memmove with unchecked size",
        description="Memory copy with size from untrusted source can cause overflow.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-787", "CWE-805"],
        category="buffer_overflow",
        patterns={
            "c": r'\b(memcpy|memmove|bcopy)\s*\([^)]+\)',
            "cpp": r'\b(memcpy|memmove|bcopy)\s*\([^)]+\)',
        },
        context_keywords=["user", "input", "request", "recv", "read"],
        fix_suggestion="Validate size parameter against destination buffer size.",
    ),

    # ==========================================================================
    # USE AFTER FREE (CWE-416)
    # ==========================================================================

    # MS006: Use after free pattern
    MemorySafetyRule(
        id="MS006",
        title="Potential use after free",
        description="Memory accessed after being freed, leading to undefined behavior.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-416"],
        category="use_after_free",
        patterns={
            "c": r'free\s*\(\s*(\w+)\s*\)(?:[^;]*;[^}]*\1\s*[\[\.\->])',
            "cpp": r'delete\s+(\w+)\s*;(?:[^}]*\1\s*[\[\.\->])',
        },
        fix_suggestion="Set pointer to NULL after free: free(ptr); ptr = NULL;",
    ),

    # MS007: Double free
    MemorySafetyRule(
        id="MS007",
        title="Potential double free",
        description="Same pointer freed twice, causing heap corruption.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-415"],
        category="use_after_free",
        patterns={
            "c": r'free\s*\(\s*(\w+)\s*\)(?:[^}]*free\s*\(\s*\1\s*\))',
            "cpp": r'delete\s+(\w+)\s*;(?:[^}]*delete\s+\1\s*;)',
        },
        fix_suggestion="Track allocation state or set pointer to NULL after free.",
    ),

    # MS008: Return of stack address
    MemorySafetyRule(
        id="MS008",
        title="Return of local variable address",
        description="Returning address of stack variable leads to dangling pointer.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-562"],
        category="use_after_free",
        patterns={
            "c": r'return\s*&\s*\w+\s*;',  # return &localvar;
            "cpp": r'return\s*&\s*\w+\s*;',
        },
        fix_suggestion="Return by value, use static storage, or allocate on heap.",
    ),

    # ==========================================================================
    # INTEGER OVERFLOW LEADING TO BUFFER ISSUES (CWE-190 related)
    # ==========================================================================

    # MS009: Integer overflow in allocation
    MemorySafetyRule(
        id="MS009",
        title="Integer overflow in memory allocation size",
        description="Multiplication in malloc size can overflow, allocating small buffer.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-190", "CWE-122"],
        category="integer_overflow",
        patterns={
            "c": r'malloc\s*\(\s*\w+\s*\*\s*\w+\s*\)',
            "cpp": r'new\s+\w+\s*\[\s*\w+\s*\*\s*\w+\s*\]',
        },
        fix_suggestion="Check for overflow before allocation: if (a > SIZE_MAX / b) error();",
    ),

    # MS010: Signed/unsigned comparison
    MemorySafetyRule(
        id="MS010",
        title="Signed/unsigned comparison in bounds check",
        description="Comparing signed with unsigned can bypass bounds checks.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-195", "CWE-697"],
        category="integer_overflow",
        patterns={
            "c": r'if\s*\(\s*\w+\s*<\s*sizeof',
            "cpp": r'if\s*\(\s*\w+\s*<\s*sizeof',
        },
        fix_suggestion="Use size_t for sizes and ensure consistent signedness.",
    ),

    # ==========================================================================
    # FORMAT STRING (CWE-134)
    # ==========================================================================

    # MS011: Format string vulnerability
    MemorySafetyRule(
        id="MS011",
        title="Format string vulnerability",
        description="User-controlled format string can read/write arbitrary memory.",
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-134"],
        category="format_string",
        patterns={
            "c": r'printf\s*\(\s*\w+\s*\)',  # printf(uservar)
            "cpp": r'printf\s*\(\s*\w+\s*\)',
        },
        fix_suggestion="Always use format string literal: printf(\"%s\", user_input);",
    ),

    # ==========================================================================
    # UNSAFE RUST (unsafe blocks)
    # ==========================================================================

    # MS012: Unsafe Rust block
    MemorySafetyRule(
        id="MS012",
        title="Unsafe Rust block detected",
        description="Unsafe blocks bypass Rust's memory safety guarantees.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-119"],
        category="unsafe_rust",
        patterns={
            "rust": r'unsafe\s*\{',
        },
        fix_suggestion="Review unsafe block for memory safety. Consider safe alternatives.",
    ),

    # MS013: Raw pointer dereference in Rust
    MemorySafetyRule(
        id="MS013",
        title="Raw pointer dereference in Rust",
        description="Dereferencing raw pointers requires unsafe and can cause UB.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-119", "CWE-416"],
        category="unsafe_rust",
        patterns={
            "rust": r'\*\s*\w+\s+as\s+\*(?:const|mut)',
        },
        fix_suggestion="Use references (&T, &mut T) instead of raw pointers when possible.",
    ),

    # ==========================================================================
    # C++ SPECIFIC
    # ==========================================================================

    # MS014: Vector access without bounds check
    MemorySafetyRule(
        id="MS014",
        title="std::vector operator[] without bounds check",
        description="operator[] does not check bounds, use at() for safety.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-125", "CWE-787"],
        category="buffer_overflow",
        patterns={
            "cpp": r'\.\s*operator\s*\[\s*\]|(?:vector|array)<[^>]+>\s*\w+[^.]+\[\w+\]',
        },
        fix_suggestion="Use .at(index) for bounds-checked access, or validate index first.",
    ),

    # MS015: Manual memory management in C++
    MemorySafetyRule(
        id="MS015",
        title="Manual new/delete instead of smart pointers",
        description="Raw new/delete is error-prone; use smart pointers.",
        severity=Severity.LOW,
        cwe_ids=["CWE-401", "CWE-416"],
        category="memory_management",
        patterns={
            "cpp": r'\bnew\s+\w+(?:\s*\[|\s*\()',
        },
        fix_suggestion="Use std::unique_ptr, std::shared_ptr, or std::make_unique.",
    ),

    # MS016: Uninitialized pointer
    MemorySafetyRule(
        id="MS016",
        title="Potentially uninitialized pointer",
        description="Pointer declared without initialization may contain garbage.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-824", "CWE-457"],
        category="uninitialized",
        patterns={
            "c": r'^\s*\w+\s*\*\s*\w+\s*;',  # int *ptr;
            "cpp": r'^\s*\w+\s*\*\s*\w+\s*;',
        },
        fix_suggestion="Initialize pointers: int *ptr = NULL; or int *ptr = nullptr;",
    ),
]
```

---

## Scanner 2: ConcurrencyErrorDetector (8 regels)

### Rules Definition

```python
CONCURRENCY_RULES = [
    # ==========================================================================
    # RACE CONDITIONS (CWE-362)
    # ==========================================================================

    # CC001: Unprotected shared variable
    ConcurrencyRule(
        id="CC001",
        title="Shared variable without synchronization",
        description="Global/shared variable accessed without lock protection.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-366"],
        category="race_condition",
        patterns={
            "c": r'pthread_create.*\n(?:[^\n]*\n)*?[^\n]*\b(\w+)\b[^\n]*(?:global|shared|static)',
            "cpp": r'std::thread.*\n(?:[^\n]*\n)*?[^\n]*\b(\w+)\b',
            "java": r'new\s+Thread\s*\(',
            "python": r'threading\.Thread\s*\(',
        },
        context_keywords=["global", "shared", "static", "volatile"],
        fix_suggestion="Protect shared data with mutex/lock or use atomic operations.",
    ),

    # CC002: Check-then-act race (TOCTOU)
    ConcurrencyRule(
        id="CC002",
        title="Time-of-check to time-of-use (TOCTOU) race",
        description="File/resource checked then used without atomicity.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-367"],
        category="race_condition",
        patterns={
            "c": r'(?:access|stat|lstat)\s*\([^)]+\)(?:[^;]*;[^}]*(?:open|fopen|unlink|remove))',
            "python": r'os\.path\.exists\s*\([^)]+\)(?:[^:]*:[^}]*open\s*\()',
            "java": r'\.exists\s*\(\s*\)(?:[^;]*;[^}]*(?:new\s+File|read|write|delete))',
        },
        fix_suggestion="Use atomic operations or file locking mechanisms.",
    ),

    # CC003: Signal handler race
    ConcurrencyRule(
        id="CC003",
        title="Non-reentrant function in signal handler",
        description="Calling non-async-signal-safe functions in signal handler.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-362", "CWE-479"],
        category="race_condition",
        patterns={
            "c": r'signal\s*\([^)]+\)(?:[^}]*(?:printf|malloc|free|exit)\s*\()',
        },
        fix_suggestion="Only use async-signal-safe functions in signal handlers.",
    ),

    # ==========================================================================
    # DEADLOCK (CWE-833)
    # ==========================================================================

    # CC004: Potential deadlock - nested locks
    ConcurrencyRule(
        id="CC004",
        title="Nested lock acquisition (potential deadlock)",
        description="Acquiring multiple locks without consistent ordering.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-833", "CWE-764"],
        category="deadlock",
        patterns={
            "c": r'pthread_mutex_lock\s*\([^)]+\)(?:[^}]*pthread_mutex_lock\s*\()',
            "cpp": r'\.lock\s*\(\s*\)(?:[^}]*\.lock\s*\(\s*\))',
            "java": r'synchronized\s*\([^)]+\)\s*\{(?:[^}]*synchronized\s*\()',
            "python": r'\.acquire\s*\(\s*\)(?:[^:]*\.acquire\s*\(\s*\))',
        },
        fix_suggestion="Use consistent lock ordering or std::scoped_lock for multiple locks.",
    ),

    # CC005: Lock not released on all paths
    ConcurrencyRule(
        id="CC005",
        title="Lock not released on error path",
        description="Lock acquired but not released before return/throw.",
        severity=Severity.HIGH,
        cwe_ids=["CWE-764", "CWE-765"],
        category="deadlock",
        patterns={
            "c": r'pthread_mutex_lock\s*\([^)]+\)(?:[^}]*return[^}]*(?!pthread_mutex_unlock))',
            "cpp": r'\.lock\s*\(\s*\)(?:[^}]*(?:return|throw)[^}]*(?!\.unlock))',
        },
        fix_suggestion="Use RAII (std::lock_guard) or ensure unlock on all paths.",
    ),

    # ==========================================================================
    # THREAD SAFETY (CWE-820, CWE-821)
    # ==========================================================================

    # CC006: Thread-unsafe function usage
    ConcurrencyRule(
        id="CC006",
        title="Thread-unsafe function in multi-threaded context",
        description="Using non-thread-safe functions (strtok, localtime, etc.).",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820"],
        category="thread_safety",
        patterns={
            "c": r'\b(strtok|localtime|gmtime|asctime|ctime|rand|strerror)\s*\(',
            "cpp": r'\b(strtok|localtime|gmtime|asctime|ctime|rand|strerror)\s*\(',
        },
        fix_suggestion="Use thread-safe variants: strtok_r, localtime_r, rand_r, etc.",
    ),

    # CC007: Volatile misuse
    ConcurrencyRule(
        id="CC007",
        title="Volatile used for synchronization",
        description="Volatile does not provide atomicity or memory ordering.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820"],
        category="thread_safety",
        patterns={
            "c": r'volatile\s+\w+\s+\w+\s*=',
            "cpp": r'volatile\s+\w+\s+\w+\s*=',
            "java": r'volatile\s+\w+\s+\w+\s*=',
        },
        context_keywords=["thread", "concurrent", "shared", "flag"],
        fix_suggestion="Use std::atomic (C++), AtomicInteger (Java), or proper synchronization.",
    ),

    # CC008: Missing volatile for shared flag
    ConcurrencyRule(
        id="CC008",
        title="Shared flag without volatile/atomic",
        description="Flag variable shared between threads without memory visibility.",
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-820", "CWE-821"],
        category="thread_safety",
        patterns={
            "c": r'(?<!volatile\s)(?:int|bool)\s+\w*(?:flag|stop|done|running)\w*\s*=',
            "java": r'(?<!volatile\s)(?:boolean|int)\s+\w*(?:flag|stop|done|running)\w*\s*=',
        },
        fix_suggestion="Declare as volatile or use atomic types for inter-thread flags.",
    ),
]
```

---

## Supported Languages

| Language | Extensions | MemorySafety | Concurrency |
|----------|------------|--------------|-------------|
| C | .c, .h | ✅ Full | ✅ Full |
| C++ | .cpp, .hpp, .cc | ✅ Full | ✅ Full |
| Rust | .rs | ✅ Partial (unsafe) | ❌ |
| Java | .java | ❌ | ✅ Full |
| Python | .py | ❌ | ✅ Partial |
| Go | .go | ❌ | ✅ Partial |

---

## Implementation Steps

### Phase 1: Foundation
1. Add `ScannerType.MEMORY_SAFETY` and `ScannerType.CONCURRENCY_ERROR` to `findings.py`
2. Create base structure for both scanner files

### Phase 2: MemorySafetyDetector
1. Implement all 16 memory safety rules
2. Add C/C++/Rust pattern matching
3. Write unit tests (~25 tests)

### Phase 3: ConcurrencyErrorDetector
1. Implement all 8 concurrency rules
2. Add multi-language pattern matching
3. Write unit tests (~15 tests)

### Phase 4: Integration
1. Export scanners in `__init__.py`
2. Register in orchestrator
3. Add to `LANGUAGE_SCANNERS` for C, C++, Rust, Java, Python, Go
4. Run integration tests

---

## Test Commands

```bash
# Unit tests
cd backend
pytest tests/unit/security_scanner/test_memory_safety_detector.py -v
pytest tests/unit/security_scanner/test_concurrency_error_detector.py -v

# Integration test
pytest tests/integration/security_scanner/ -v -k "memory or concurrency"
```

---

## Success Criteria

- [ ] 24 new detection rules implemented (16 + 8)
- [ ] CWE-787, 416, 125, 119, 362 covered (100% CWE Top 25)
- [ ] C/C++ primary focus with Rust/Java/Python support
- [ ] >90% test coverage
- [ ] <20% false positive rate (memory safety is hard)
- [ ] SARIF compatible output

---

## Effort Estimate

| Component | Effort |
|-----------|--------|
| MemorySafetyDetector + tests | 10h |
| ConcurrencyErrorDetector + tests | 6h |
| Integration + orchestrator | 2h |
| **Total** | **~18h** |

---

## CWE Coverage After Fase 38

| Metric | Before | After |
|--------|--------|-------|
| CWE Top 25 | 20/25 (80%) | **25/25 (100%)** |
| Total CWEs | 225 | ~240 |
| Memory Safety | ❌ | ✅ |
| Concurrency | ❌ | ✅ |

---

## References

- [CWE-787: Out-of-bounds Write](https://cwe.mitre.org/data/definitions/787.html)
- [CWE-416: Use After Free](https://cwe.mitre.org/data/definitions/416.html)
- [CWE-125: Out-of-bounds Read](https://cwe.mitre.org/data/definitions/125.html)
- [CWE-119: Buffer Overflow](https://cwe.mitre.org/data/definitions/119.html)
- [CWE-362: Race Condition](https://cwe.mitre.org/data/definitions/362.html)
- [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c)
- [SEI CERT C++ Coding Standard](https://wiki.sei.cmu.edu/confluence/display/cplusplus)
