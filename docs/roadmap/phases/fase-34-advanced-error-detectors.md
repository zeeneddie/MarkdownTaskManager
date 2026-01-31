# Fase 34: Advanced Error Detectors (KW6-KW7 [w159-160])

**Goal:** Implementatie van geavanceerde detectoren voor deadlocks en performance problemen
**Status:** PLANNED
**Priority:** HIGH (productie-stabiliteit)
**Effort:** ~48 uur
**Week:** KW6-KW7 [w159-160] (Q1 2026)
**Dependencies:** Fase 31 (CWE Scanner) ✅, Fase 24-KB (Knowledge Base) ✅

---

## Executive Summary

Twee nieuwe scanner modules voor detectie van:
1. **DeadlockDetector** - Lock ordering violations, nested locks, resource cycles
2. **PerformancePatternDetector** - N+1 queries, algorithmic complexity, unbounded growth

---

## Problem Statement

Huidige CWE Scanner (Fase 31) detecteert:
- ✅ Injection vulnerabilities
- ✅ Authentication issues
- ✅ Data protection problems
- ❌ Deadlock patterns
- ❌ Performance anti-patterns

Deze errors veroorzaken **production outages** maar zijn moeilijk te vinden met standaard security scanners.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ADVANCED ERROR DETECTORS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DeadlockDetector                          │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │    │
│  │  │ LockOrder    │ │ NestedLock   │ │ ResourceCycle        │ │    │
│  │  │ Analyzer     │ │ Detector     │ │ Detector             │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                PerformancePatternDetector                    │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │    │
│  │  │ N+1 Query    │ │ Complexity   │ │ Unbounded Growth     │ │    │
│  │  │ Detector     │ │ Analyzer     │ │ Detector             │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Output: SecurityFinding (SARIF compatible)                         │
│  Integration: SecurityOrchestrator                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module 1: DeadlockDetector (24 uur)

### 1.1 Lock Order Analyzer

**Detecteert:** Inconsistente lock acquisition volgorde

```python
# PROBLEEM: Lock order violation
def thread_1():
    with lock_a:
        with lock_b:  # A -> B
            process()

def thread_2():
    with lock_b:
        with lock_a:  # B -> A (DEADLOCK RISK!)
            process()
```

**Analyse methode:**
1. Build lock acquisition graph per functie
2. Detect cycles in cross-function lock ordering
3. Report potential deadlock paths

**Languages:** Python, Java, C#, C++, Go

### 1.2 Nested Lock Detector

**Detecteert:** Recursive lock acquisition, self-deadlock

```java
// PROBLEEM: Nested lock same object
synchronized(this) {
    // ...
    synchronized(this) {  // Self-deadlock risk
        // ...
    }
}
```

**Patterns:**
- Same lock acquired twice in call chain
- ReentrantLock without proper reentrant handling
- Mutex lock in recursive function

### 1.3 Resource Cycle Detector

**Detecteert:** Circular resource dependencies

```
Thread 1: Holds A, Waits for B
Thread 2: Holds B, Waits for C
Thread 3: Holds C, Waits for A  → CYCLE!
```

**Analysis:**
- Build resource dependency graph
- Detect cycles using DFS
- Report all resources in cycle

### 1.4 Database Deadlock Patterns

**Detecteert:** SQL patterns die database deadlocks veroorzaken

```sql
-- PROBLEEM: Update in inconsistente volgorde
-- Transaction 1: UPDATE users SET ... WHERE id = 1; UPDATE orders SET ... WHERE id = 1;
-- Transaction 2: UPDATE orders SET ... WHERE id = 1; UPDATE users SET ... WHERE id = 1;
```

**CWE Mapping:** CWE-833 (Deadlock)

---

## Module 2: PerformancePatternDetector (24 uur)

### 2.1 N+1 Query Detector

**Detecteert:** Database queries in loops

```python
# PROBLEEM: N+1 Query
users = User.objects.all()  # 1 query
for user in users:
    orders = Order.objects.filter(user=user)  # N queries!
```

**Detection patterns:**
- Loop containing ORM query
- Loop containing raw SQL execute
- Nested data fetching without prefetch/join

**Languages:** Python (Django, SQLAlchemy), Java (JPA, Hibernate), C# (EF), JavaScript (Sequelize, Prisma)

**CWE Mapping:** CWE-1073 (Non-SQL Invocation)

### 2.2 Algorithmic Complexity Analyzer

**Detecteert:** Suboptimale algoritmes

```python
# PROBLEEM: O(n²) waar O(n) mogelijk is
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):  # Nested loop = O(n²)
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# BETER: O(n) met set
def find_duplicates_fast(items):
    seen = set()
    duplicates = []
    for item in items:
        if item in seen:
            duplicates.append(item)
        seen.add(item)
    return duplicates
```

**Detection patterns:**
- Nested loops over same collection
- Linear search where hash lookup possible
- String concatenation in loop (O(n²) in some languages)
- Repeated sorting of same data

**CWE Mapping:** CWE-407 (Algorithmic Complexity)

### 2.3 Unbounded Growth Detector

**Detecteert:** Collections die onbeperkt groeien

```python
# PROBLEEM: Unbounded cache
cache = {}

def get_data(key):
    if key not in cache:
        cache[key] = expensive_fetch(key)  # Grows forever!
    return cache[key]
```

**Patterns:**
- Dictionary/Map without eviction
- List append without size check
- Queue without consumer
- Log buffer without rotation

**CWE Mapping:** CWE-770 (Allocation without Limits)

### 2.4 Missing Pagination Detector

**Detecteert:** Queries zonder LIMIT

```python
# PROBLEEM: Load all records
all_users = User.objects.all()  # Kan miljoenen records zijn!

# BETER: Pagination
users_page = User.objects.all()[:100]
```

### 2.5 Regex Catastrophe Detector

**Detecteert:** ReDoS vulnerable regex patterns

```python
# PROBLEEM: Catastrophic backtracking
import re
pattern = r"(a+)+"  # Evil regex!
re.match(pattern, "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!")  # Hangs!
```

**Vulnerable patterns:**
- `(a+)+`
- `(a|a)+`
- `(a|aa)+`
- Nested quantifiers

**CWE Mapping:** CWE-1333 (Regex Complexity)

---

## Implementation Plan

### Phase 34.1: DeadlockDetector Foundation (KW6 [w159])

| Task | Description | Effort |
|------|-------------|--------|
| 34.1.1 | Create DeadlockDetector base class | 2h |
| 34.1.2 | Implement Lock AST parser (Python, Java, C#) | 6h |
| 34.1.3 | Build lock acquisition graph | 4h |
| 34.1.4 | Implement cycle detection algorithm | 4h |
| 34.1.5 | Unit tests | 4h |

### Phase 34.2: DeadlockDetector Advanced (KW6 [w159])

| Task | Description | Effort |
|------|-------------|--------|
| 34.2.1 | Nested lock detection | 3h |
| 34.2.2 | Database deadlock patterns | 3h |
| 34.2.3 | Cross-file analysis | 4h |
| 34.2.4 | Integration with SecurityOrchestrator | 2h |
| 34.2.5 | Integration tests | 4h |

### Phase 34.3: PerformancePatternDetector Foundation (KW7 [w160])

| Task | Description | Effort |
|------|-------------|--------|
| 34.3.1 | Create PerformancePatternDetector base | 2h |
| 34.3.2 | N+1 Query detector (ORM patterns) | 6h |
| 34.3.3 | Loop-query pattern matching | 4h |
| 34.3.4 | Unit tests | 4h |

### Phase 34.4: PerformancePatternDetector Advanced (KW7 [w160])

| Task | Description | Effort |
|------|-------------|--------|
| 34.4.1 | Algorithmic complexity analyzer | 6h |
| 34.4.2 | Unbounded growth detector | 4h |
| 34.4.3 | Regex catastrophe detector | 4h |
| 34.4.4 | Missing pagination detector | 2h |
| 34.4.5 | Integration with SecurityOrchestrator | 2h |
| 34.4.6 | Integration tests | 4h |

---

## File Structure

```
backend/app/services/security_scanner/adapters/
├── deadlock_detector.py
│   ├── DeadlockDetector
│   ├── LockOrderAnalyzer
│   ├── NestedLockDetector
│   └── ResourceCycleDetector
└── performance_pattern_detector.py
    ├── PerformancePatternDetector
    ├── NPlusOneQueryDetector
    ├── ComplexityAnalyzer
    ├── UnboundedGrowthDetector
    └── RegexCatastropheDetector

backend/tests/unit/security_scanner/
├── test_deadlock_detector.py
└── test_performance_pattern_detector.py
```

---

## Detection Rules

### Deadlock Rules

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| DL001 | Lock order violation | HIGH | CWE-833 |
| DL002 | Nested same lock | HIGH | CWE-833 |
| DL003 | Resource cycle | CRITICAL | CWE-833 |
| DL004 | Missing timeout on lock | MEDIUM | CWE-1088 |
| DL005 | Database transaction order | HIGH | CWE-833 |

### Performance Rules

| Rule ID | Pattern | Severity | CWE |
|---------|---------|----------|-----|
| PF001 | N+1 Query in loop | HIGH | CWE-1073 |
| PF002 | O(n²) algorithm | MEDIUM | CWE-407 |
| PF003 | Unbounded collection | HIGH | CWE-770 |
| PF004 | ReDoS vulnerable regex | HIGH | CWE-1333 |
| PF005 | Missing pagination | MEDIUM | CWE-770 |
| PF006 | String concat in loop | LOW | CWE-407 |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Deadlock patterns detected | >5 rule types |
| Performance patterns detected | >6 rule types |
| Languages supported | Python, Java, C#, JavaScript |
| False positive rate | <15% |
| Test coverage | >90% |

---

## References

- [CWE-833: Deadlock](https://cwe.mitre.org/data/definitions/833.html)
- [CWE-1073: Non-SQL Invocation](https://cwe.mitre.org/data/definitions/1073.html)
- [CWE-407: Algorithmic Complexity](https://cwe.mitre.org/data/definitions/407.html)
- [CWE-770: Allocation without Limits](https://cwe.mitre.org/data/definitions/770.html)
- [CWE-1333: Regex Complexity](https://cwe.mitre.org/data/definitions/1333.html)
