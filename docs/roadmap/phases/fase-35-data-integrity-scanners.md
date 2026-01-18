# Fase 35: Data Integrity Scanners (Week 171-175)

**Goal:** Implementatie van scanners voor race conditions en resource lifecycle issues
**Status:** PLANNED
**Priority:** HIGH (data integriteit)
**Effort:** ~40 uur
**Dependencies:** Fase 31 (CWE Scanner), Fase 34 (Advanced Error Detectors)

---

## Executive Summary

Twee nieuwe scanner modules voor detectie van:
1. **DataIntegrityDetector** - Race conditions, TOCTOU, atomicity violations
2. **ResourceLifecycleDetector** - Resource leaks, missing cleanup, improper initialization

---

## Problem Statement

Data integrity en resource issues zijn **#1 oorzaak van production bugs**:
- Race conditions → Data corruption, inconsistent state
- Resource leaks → Memory exhaustion, connection pool exhaustion
- TOCTOU → Security vulnerabilities, data races

Huidige detectie:
- ✅ Fase 21: Resource leak detection (basic)
- ❌ Race condition detection
- ❌ TOCTOU detection
- ❌ Atomicity violation detection

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA INTEGRITY SCANNERS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   DataIntegrityDetector                      │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │    │
│  │  │ RaceCondition│ │ TOCTOU       │ │ Atomicity            │ │    │
│  │  │ Detector     │ │ Detector     │ │ Violation Detector   │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                ResourceLifecycleDetector                     │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │    │
│  │  │ Leak         │ │ Cleanup      │ │ Initialization       │ │    │
│  │  │ Detector     │ │ Analyzer     │ │ Checker              │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Output: SecurityFinding (SARIF compatible)                         │
│  Integration: SecurityOrchestrator + StabilityAnalyzer              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module 1: DataIntegrityDetector (24 uur)

### 1.1 Race Condition Detector

**Detecteert:** Unsynchronized access to shared state

```python
# PROBLEEM: Data race
counter = 0  # Shared state

def increment():
    global counter
    counter += 1  # Read-modify-write NOT atomic!

# Thread 1: reads 5, writes 6
# Thread 2: reads 5, writes 6  # Lost update!
```

**Patterns:**
| Pattern | Description | Risk |
|---------|-------------|------|
| Shared mutable global | Global var modified by threads | HIGH |
| Shared instance var | Instance var without sync | HIGH |
| Check-then-act | if(x) then modify(x) | MEDIUM |
| Read-modify-write | x = x + 1 without lock | HIGH |
| Lazy initialization | Singleton without sync | MEDIUM |

**Detection approach:**
1. Identify shared state (globals, instance vars)
2. Find concurrent access points (threads, async)
3. Check for synchronization primitives
4. Report unprotected access

**CWE Mapping:** CWE-362 (Race Condition)

### 1.2 TOCTOU Detector

**Detecteert:** Time-of-Check to Time-of-Use vulnerabilities

```python
# PROBLEEM: TOCTOU
import os

def safe_read(filename):
    if os.path.exists(filename):  # TIME OF CHECK
        # Attacker swaps file here!
        return open(filename).read()  # TIME OF USE

# BETER: EAFP (Easier to Ask Forgiveness)
def safe_read_fixed(filename):
    try:
        return open(filename).read()
    except FileNotFoundError:
        return None
```

**TOCTOU patterns:**
| Pattern | Check | Use | Risk |
|---------|-------|-----|------|
| File exists check | `os.path.exists()` | `open()` | HIGH |
| Permission check | `os.access()` | `open()` | HIGH |
| Directory check | `os.path.isdir()` | `os.listdir()` | MEDIUM |
| Lock file check | Check file exists | Create file | HIGH |

**CWE Mapping:** CWE-367 (TOCTOU Race Condition)

### 1.3 Atomicity Violation Detector

**Detecteert:** Compound operations die atomisch zouden moeten zijn

```java
// PROBLEEM: Non-atomic compound operation
public class BankAccount {
    private int balance;

    public void transfer(BankAccount other, int amount) {
        if (this.balance >= amount) {  // Check
            this.balance -= amount;     // Modify this
            other.balance += amount;    // Modify other
            // Crash here = inconsistent state!
        }
    }
}
```

**Atomicity patterns:**
| Pattern | Description | Fix |
|---------|-------------|-----|
| Check-then-modify | if(x) then x = y | Atomic CAS |
| Multi-object update | Modify A then B | Transaction |
| Put-if-absent | if not in map, add | putIfAbsent() |
| Increment | x = x + 1 | AtomicInteger |

**CWE Mapping:** CWE-362 (Race Condition)

### 1.4 Double-Checked Locking Detector

**Detecteert:** Broken double-checked locking pattern

```java
// PROBLEEM: Broken double-checked locking (pre-Java 5)
public class Singleton {
    private static Singleton instance;

    public static Singleton getInstance() {
        if (instance == null) {           // Check 1
            synchronized(Singleton.class) {
                if (instance == null) {   // Check 2
                    instance = new Singleton();  // Not atomic!
                }
            }
        }
        return instance;
    }
}
```

**Fix:** Use `volatile` (Java 5+) or static holder pattern

---

## Module 2: ResourceLifecycleDetector (16 uur)

### 2.1 Enhanced Leak Detector

**Uitbreiding op Fase 21 StabilityAnalyzer:**

```python
# PROBLEEM: Connection leak
def get_data():
    conn = database.connect()  # OPEN
    result = conn.execute("SELECT * FROM users")
    return result  # LEAK! conn never closed

# BETER: Context manager
def get_data_fixed():
    with database.connect() as conn:
        return conn.execute("SELECT * FROM users")
```

**Resource types:**
| Resource | Open Pattern | Close Pattern | Risk |
|----------|--------------|---------------|------|
| File | `open()` | `close()` / `with` | HIGH |
| DB Connection | `connect()` | `close()` / `with` | CRITICAL |
| HTTP Client | `requests.Session()` | `close()` | MEDIUM |
| Thread | `Thread.start()` | `join()` | HIGH |
| Lock | `acquire()` | `release()` | CRITICAL |
| Socket | `socket()` | `close()` | HIGH |

**CWE Mapping:** CWE-772 (Missing Release), CWE-401 (Memory Leak), CWE-775 (File Descriptor Leak)

### 2.2 Cleanup Analyzer

**Detecteert:** Missing cleanup in error paths

```python
# PROBLEEM: Cleanup skipped on exception
def process_file(path):
    f = open(path)
    temp = create_temp_file()

    try:
        process(f, temp)
    except Exception:
        raise  # temp file not cleaned up!
    finally:
        f.close()  # f is closed, but temp is leaked
```

**Patterns:**
| Pattern | Issue | Fix |
|---------|-------|-----|
| Missing finally | Cleanup only on success | Add finally |
| Early return | Cleanup after return skipped | Cleanup before return |
| Exception in cleanup | Cleanup raises, masks error | Try-except in cleanup |
| Nested resources | Inner cleanup skipped | Nested try-finally |

**CWE Mapping:** CWE-459 (Incomplete Cleanup)

### 2.3 Initialization Checker

**Detecteert:** Improper initialization issues

```python
# PROBLEEM: Use before initialization
class DataProcessor:
    def __init__(self):
        self.data = None  # Not initialized

    def process(self):
        return self.data.transform()  # NullPointerException!

    def load(self):
        self.data = load_data()
```

**Patterns:**
| Pattern | Issue | Risk |
|---------|-------|------|
| Null after construction | Field set to null in __init__ | HIGH |
| Conditional init | Field only set in some paths | MEDIUM |
| Late initialization | Field set after construction | MEDIUM |
| Double initialization | Field set twice | LOW |

**CWE Mapping:** CWE-665 (Improper Initialization), CWE-908 (Uninitialized Resource)

### 2.4 Resource Order Checker

**Detecteert:** Verkeerde volgorde van resource operaties

```python
# PROBLEEM: Wrong order - use after close
def bad_order():
    conn = connect()
    conn.close()
    conn.execute("SELECT 1")  # Use after close!

# PROBLEEM: Wrong cleanup order
def bad_cleanup():
    parent = acquire_parent()
    child = acquire_child(parent)
    parent.release()  # Parent released before child!
    child.release()
```

---

## Implementation Plan

### Phase 35.1: DataIntegrityDetector Foundation (Week 171-172)

| Task | Description | Effort |
|------|-------------|--------|
| 35.1.1 | Create DataIntegrityDetector base class | 2h |
| 35.1.2 | Implement shared state identifier | 4h |
| 35.1.3 | Build concurrent access analyzer | 6h |
| 35.1.4 | Race condition pattern matching | 4h |
| 35.1.5 | Unit tests | 4h |

### Phase 35.2: DataIntegrityDetector Advanced (Week 173)

| Task | Description | Effort |
|------|-------------|--------|
| 35.2.1 | TOCTOU detector | 4h |
| 35.2.2 | Atomicity violation detector | 4h |
| 35.2.3 | Double-checked locking detector | 2h |
| 35.2.4 | Integration tests | 2h |

### Phase 35.3: ResourceLifecycleDetector (Week 174-175)

| Task | Description | Effort |
|------|-------------|--------|
| 35.3.1 | Enhanced leak detector | 4h |
| 35.3.2 | Cleanup analyzer | 4h |
| 35.3.3 | Initialization checker | 3h |
| 35.3.4 | Resource order checker | 3h |
| 35.3.5 | Integration with StabilityAnalyzer | 2h |
| 35.3.6 | Integration tests | 4h |

---

## File Structure

```
backend/app/services/security_scanner/adapters/
├── data_integrity_detector.py
│   ├── DataIntegrityDetector
│   ├── RaceConditionDetector
│   ├── TOCTOUDetector
│   └── AtomicityViolationDetector
└── resource_lifecycle_detector.py
    ├── ResourceLifecycleDetector
    ├── EnhancedLeakDetector
    ├── CleanupAnalyzer
    └── InitializationChecker

backend/tests/unit/security_scanner/
├── test_data_integrity_detector.py
└── test_resource_lifecycle_detector.py
```

---

## Detection Rules

### Data Integrity Rules

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| DI001 | Shared mutable state without sync | HIGH | CWE-362 |
| DI002 | TOCTOU file operation | HIGH | CWE-367 |
| DI003 | Non-atomic compound operation | HIGH | CWE-362 |
| DI004 | Broken double-checked locking | MEDIUM | CWE-609 |
| DI005 | Check-then-act without atomicity | HIGH | CWE-362 |
| DI006 | Lazy init without sync | MEDIUM | CWE-609 |

### Resource Lifecycle Rules

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| RL001 | Resource opened never closed | HIGH | CWE-772 |
| RL002 | Cleanup skipped on exception | HIGH | CWE-459 |
| RL003 | Use before initialization | HIGH | CWE-908 |
| RL004 | Use after close | CRITICAL | CWE-416 |
| RL005 | Wrong resource cleanup order | MEDIUM | CWE-459 |
| RL006 | Missing finally block | MEDIUM | CWE-459 |

---

## Integration with Existing Components

### StabilityAnalyzer (Fase 21)
- Extend ResourceLeakDetector categories
- Share resource tracking infrastructure
- Unified reporting

### SecurityOrchestrator (Fase 31)
- Register as additional scanner
- SARIF output format
- Parallel execution

### Knowledge Base (Fase 24-KB)
- Link findings to KB examples
- Provide fix suggestions from post-mortems

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Data integrity patterns detected | >6 rule types |
| Resource lifecycle patterns detected | >6 rule types |
| Languages supported | Python, Java, C#, JavaScript |
| False positive rate | <20% |
| Test coverage | >90% |

---

## References

- [CWE-362: Race Condition](https://cwe.mitre.org/data/definitions/362.html)
- [CWE-367: TOCTOU](https://cwe.mitre.org/data/definitions/367.html)
- [CWE-772: Missing Release](https://cwe.mitre.org/data/definitions/772.html)
- [CWE-459: Incomplete Cleanup](https://cwe.mitre.org/data/definitions/459.html)
- [CWE-908: Uninitialized Resource](https://cwe.mitre.org/data/definitions/908.html)
