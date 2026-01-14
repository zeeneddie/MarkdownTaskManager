# Static Code Analysis Coverage - MarQed Platform

**Bron:** [IN-COM Blog - Hidden Dangers in Your Code](https://www.in-com.com/nl/blog/the-hidden-dangers-in-your-code-how-static-code-analysis-detects-critical-errors/)
**Datum:** 2026-01-13
**Doel:** Gap analysis tussen SCA best practices en MarQed scanner coverage

---

## Coverage Matrix

| Categorie | Subcategorie | MarQed Scanner | Status | Fase |
|-----------|--------------|----------------|--------|------|
| **Syntax Errors** | Missing delimiters | - | ⚪ N/A (interpreted) | - |
| | Mismatched brackets | BracketMatcher | 🔴 Missing | 33 |
| | Invalid operators | - | ⚪ Low priority | - |
| **Type Errors** | Type mismatches | TypeMismatchDetector | 🔴 Missing | 33 |
| | Implicit conversions | ImplicitConversionDetector | 🔴 Missing | 33 |
| | Variant abuse | VariantAbuseDetector | 🔴 Missing | 33 |
| **Logical Errors** | Unreachable code | UnreachableCodeDetector | 🔴 Missing | 33 |
| | Infinite loops | InfiniteLoopDetector | 🔴 Missing | 33 |
| | Dead code | DeadCodeDetector | 🟢 Exists | - |
| | Incorrect conditions | ConditionAnalyzer | 🟡 Partial | 33 |
| **Security** | SQL Injection | SQLInjectionDetector | 🔴 Planned | 31.1 |
| | XSS | XSSDetector | 🔴 Planned | 31.1 |
| | Buffer overflow | - | ⚪ N/A (ASP) | - |
| | Weak crypto | WeakCryptoDetector | 🔴 Planned | 31.3 |
| | Hardcoded secrets | HardcodedCredentialsDetector | 🟡 Partial | 31.3 |
| **Memory/Resources** | Memory leaks | - | ⚪ N/A (ASP) | - |
| | Resource leaks | ResourceLeakDetector | 🟢 Exists | - |
| | Null references | NullReferenceDetector | 🔴 Missing | 33 |

**Legend:** 🟢 Exists | 🟡 Partial | 🔴 Missing/Planned | ⚪ N/A

---

## Gap Analysis

### Huidige Coverage

| Status | Count | Percentage |
|--------|-------|------------|
| 🟢 Exists | 2 | 13% |
| 🟡 Partial | 2 | 13% |
| 🔴 Missing | 10 | 67% |
| ⚪ N/A | 4 | - |

### Prioriteit voor Classic ASP/VBScript

**HOOG - Direct relevant:**
1. Unreachable Code Detection
2. Infinite Loop Detection
3. Null Reference Detection
4. Type Mismatch Detection (VBScript Variant issues)

**MEDIUM - Nuttig:**
5. Bracket/Parenthesis Matching
6. Condition Analysis (always true/false)
7. Implicit Conversion Warnings

**LAAG - Minder relevant voor ASP:**
- Memory management (handled by runtime)
- Buffer overflows (N/A)

---

## Detailed Gap Specifications

### 1. Unreachable Code Detector

**Doel:** Detecteer code die nooit uitgevoerd kan worden

**Patterns te Detecteren:**
```vbscript
' ISSUE: Code after Response.End
Response.End
DoSomething()  ' <-- Unreachable

' ISSUE: Code after Exit Sub/Function
Exit Sub
CleanupCode()  ' <-- Unreachable

' ISSUE: Dead branch
If False Then
    NeverExecuted()  ' <-- Unreachable
End If

' ISSUE: Return path analysis
Function GetValue()
    If condition Then
        GetValue = 1
        Exit Function
    Else
        GetValue = 2
        Exit Function
    End If
    ' Everything below is unreachable
    LogSomething()
End Function
```

**Detection Rules:**
| Rule ID | Pattern | Severity |
|---------|---------|----------|
| UNREACH-001 | Code after Response.End | HIGH |
| UNREACH-002 | Code after Exit Sub/Function | HIGH |
| UNREACH-003 | Code in always-false branch | MEDIUM |
| UNREACH-004 | Code after unconditional Return | HIGH |

---

### 2. Infinite Loop Detector

**Doel:** Detecteer loops die mogelijk nooit eindigen

**Patterns te Detecteren:**
```vbscript
' ISSUE: No exit condition modification
Do While condition
    ' condition never changes
    ProcessItem()
Loop

' ISSUE: Counter not incremented
For i = 0 To count
    ' i is never incremented (manual loop)
    ProcessItem()
Next  ' This is fine, but manual loops...

' ISSUE: While without increment
i = 0
Do While i < 10
    ProcessItem()
    ' Missing: i = i + 1
Loop

' ISSUE: Recordset without MoveNext
Do While Not rs.EOF
    ProcessRecord(rs)
    ' Missing: rs.MoveNext
Loop
```

**Detection Rules:**
| Rule ID | Pattern | Severity |
|---------|---------|----------|
| INFLOOP-001 | Do While without condition change | CRITICAL |
| INFLOOP-002 | Recordset loop without MoveNext | CRITICAL |
| INFLOOP-003 | Counter loop without increment | HIGH |
| INFLOOP-004 | While True without Exit | MEDIUM |

**FysioOne Known Issues:**
- Grafiek bestanden met potentiële oneindige loops (eerder gedetecteerd)

---

### 3. Null Reference Detector

**Doel:** Detecteer gebruik van objecten zonder Nothing check

**Patterns te Detecteren:**
```vbscript
' ISSUE: No Nothing check before use
Set obj = GetObject()
obj.DoSomething()  ' Could fail if Nothing

' ISSUE: Recordset without EOF check
Set rs = conn.Execute(sql)
value = rs("field")  ' Fails if no records

' SAFE: Proper check
Set obj = GetObject()
If Not obj Is Nothing Then
    obj.DoSomething()
End If

' SAFE: Recordset with EOF
Set rs = conn.Execute(sql)
If Not rs.EOF Then
    value = rs("field")
End If
```

**Detection Rules:**
| Rule ID | Pattern | Severity |
|---------|---------|----------|
| NULL-001 | Object use without Nothing check | HIGH |
| NULL-002 | Recordset field access without EOF | HIGH |
| NULL-003 | Collection access without Count check | MEDIUM |
| NULL-004 | Dictionary access without Exists check | MEDIUM |

---

### 4. Type Mismatch Detector (VBScript)

**Doel:** Detecteer potentiële type conversie problemen

**Patterns te Detecteren:**
```vbscript
' ISSUE: String used as number without conversion
userInput = Request("amount")
total = total + userInput  ' Type mismatch if non-numeric

' ISSUE: Null propagation
value = rs("field")  ' Could be Null
result = value + 10  ' Error if Null

' ISSUE: Date format assumptions
dateStr = Request("date")
dateVal = CDate(dateStr)  ' Fails on invalid format

' SAFE: Explicit conversion with validation
userInput = Request("amount")
If IsNumeric(userInput) Then
    total = total + CDbl(userInput)
End If
```

**Detection Rules:**
| Rule ID | Pattern | Severity |
|---------|---------|----------|
| TYPE-001 | Request value used without IsNumeric | HIGH |
| TYPE-002 | Database field used without IsNull check | HIGH |
| TYPE-003 | CDate without date validation | MEDIUM |
| TYPE-004 | Implicit Variant arithmetic | LOW |

---

### 5. Condition Analyzer

**Doel:** Detecteer altijd-waar of altijd-onwaar condities

**Patterns te Detecteren:**
```vbscript
' ISSUE: Always true
If True Then  ' Obvious
If 1 = 1 Then  ' Less obvious
If x = x Then  ' Always true

' ISSUE: Always false
If False Then
If 1 = 2 Then

' ISSUE: Redundant conditions
If x > 5 And x > 3 Then  ' x > 3 is redundant
If x < 5 Or x < 10 Then  ' x < 10 always true when x < 5

' ISSUE: Contradictory conditions
If x > 5 And x < 3 Then  ' Never true

' ISSUE: Operator precedence (eerder gedetecteerd!)
If a Or b And c Then  ' Evaluates as: a Or (b And c)
```

**Detection Rules:**
| Rule ID | Pattern | Severity |
|---------|---------|----------|
| COND-001 | Tautology (always true) | MEDIUM |
| COND-002 | Contradiction (always false) | HIGH |
| COND-003 | Redundant sub-condition | LOW |
| COND-004 | Operator precedence ambiguity | HIGH |

---

## Implementation Roadmap Addition

### Fase 33: Static Analysis Enhancement (Week 165-170)

| Sub-fase | Scanner | Priority | Effort |
|----------|---------|----------|--------|
| 33.1 | UnreachableCodeDetector | P1 | 3 days |
| 33.2 | InfiniteLoopDetector | P0 | 4 days |
| 33.3 | NullReferenceDetector | P1 | 3 days |
| 33.4 | TypeMismatchDetector | P2 | 3 days |
| 33.5 | ConditionAnalyzer | P1 | 4 days |
| 33.6 | Integration + Tests | - | 3 days |

**Total Effort:** 20 dagen (~4 weken)

---

## Integration with Existing Scanners

### Complementary Analysis

```
Brown Paper Phase 1: Code Understanding
├── Existing Scanners
│   ├── ComplexityAnalyzer (SIG)
│   ├── DuplicationAnalyzer (SIG)
│   ├── CouplingAnalyzer (SIG)
│   ├── ResourceLeakDetector (CWE-400)
│   └── DeadCodeDetector
│
├── Fase 31: Security (CWE Top 25)
│   ├── SQLInjectionDetector
│   ├── XSSDetector
│   └── ... (26 scanners)
│
└── Fase 33: Static Analysis NEW
    ├── UnreachableCodeDetector
    ├── InfiniteLoopDetector
    ├── NullReferenceDetector
    ├── TypeMismatchDetector
    └── ConditionAnalyzer
```

### Combined Report Output

```json
{
  "static_analysis": {
    "logical_errors": {
      "unreachable_code": 12,
      "infinite_loops": 3,
      "dead_code": 156
    },
    "null_safety": {
      "unchecked_objects": 45,
      "unchecked_recordsets": 23
    },
    "type_safety": {
      "unvalidated_input": 89,
      "null_propagation": 34
    },
    "condition_issues": {
      "operator_precedence": 5,
      "tautologies": 2,
      "contradictions": 0
    }
  }
}
```

---

## Quality Gate Integration

```python
STATIC_ANALYSIS_GATE = {
    "infinite_loops_allowed": 0,        # CRITICAL - block deployment
    "unreachable_code_max": 10,         # HIGH
    "null_reference_max": 20,           # HIGH
    "type_mismatch_max": 50,            # MEDIUM
    "condition_issues_max": 10          # MEDIUM
}
```

---

## References

- [IN-COM Static Code Analysis](https://www.in-com.com/nl/blog/the-hidden-dangers-in-your-code-how-static-code-analysis-detects-critical-errors/)
- [CWE Top 25 Coverage](../plans/cwe-top25-coverage-analysis.md)
- [12 Coding Mistakes](coding-best-practices-checklist.md)
- [GEMMA Informatiebeveiliging](gemma-informatiebeveiliging-userstories.md)

---

*Document Version: 1.0*
*Created: 2026-01-13*
*MarQed AI Agent Platform*
