# Security Scanners: Advanced Detection

**Phase:** Week 157-160
**Priority:** MEDIUM
**Target:** Classic ASP, VBScript, Runtime behavior

---

## Overview

Advanced detection covers race conditions, array validation, and exceptional condition handling - issues that are harder to detect but can cause subtle security problems.

---

## CWE-362: Race Condition Detector

### Doel
Detecteer TOCTOU (time-of-check-time-of-use) en andere race conditions.

### Patterns te Detecteren

```vbscript
' VULNERABLE: TOCTOU race condition
Set fso = CreateObject("Scripting.FileSystemObject")
If fso.FileExists(filePath) Then
    ' Time gap here - file could be replaced/deleted
    Set file = fso.OpenTextFile(filePath)
End If

' VULNERABLE: Check-then-act on shared resource
If Application("counter") < maxLimit Then
    ' Another request could increment between check and use
    Application("counter") = Application("counter") + 1
End If

' SAFE: Atomic operations
Application.Lock
If Application("counter") < maxLimit Then
    Application("counter") = Application("counter") + 1
End If
Application.Unlock
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| RACE-001 | FileExists check before OpenTextFile | MEDIUM |
| RACE-002 | Application variable check without Lock | HIGH |
| RACE-003 | Session check-then-act patterns | MEDIUM |

### ASP-Specific Race Conditions

```python
RACE_CONDITION_PATTERNS = [
    # TOCTOU file operations
    (r'FileExists\s*\([^)]+\)', r'OpenTextFile|CreateTextFile'),
    # Application scope without locking
    (r'If Application\([^)]+\)', r'Application\([^)]+\)\s*='),
    # Session race conditions
    (r'If Session\([^)]+\)', r'Session\([^)]+\)\s*='),
]
```

---

## CWE-129: Array Index Validation Detector

### Doel
Detecteer array access zonder bounds checking.

### Patterns te Detecteren

```vbscript
' VULNERABLE: No bounds check
index = CInt(Request("index"))
value = myArray(index)  ' Could be out of bounds

' VULNERABLE: Split without validation
parts = Split(Request("data"), ",")
name = parts(0)  ' Assumes at least 1 element
email = parts(1)  ' Assumes at least 2 elements

' SAFE: Bounds checking
parts = Split(Request("data"), ",")
If UBound(parts) >= 1 Then
    name = parts(0)
    email = parts(1)
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| ARRAY-001 | `Split` result used without `UBound` check | MEDIUM |
| ARRAY-002 | Array index from user input | HIGH |
| ARRAY-003 | Loop to UBound without LBound | LOW |

---

## CWE-754: Exceptional Condition Detector

### Doel
Detecteer ontbrekende error handling voor uitzonderlijke condities.

### Patterns te Detecteren

```vbscript
' VULNERABLE: No error handling for database
Set conn = Server.CreateObject("ADODB.Connection")
conn.Open connectionString  ' Could fail
Set rs = conn.Execute(sql)  ' Could fail

' VULNERABLE: Ignoring errors silently
On Error Resume Next
conn.Execute sql
On Error Goto 0  ' Error ignored, no logging

' SAFE: Proper error handling
On Error Resume Next
conn.Open connectionString
If Err.Number <> 0 Then
    LogError "Database connection failed: " & Err.Description
    ShowUserFriendlyError
    Response.End
End If
On Error Goto 0
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| EXCEPT-001 | Database operations without error check | MEDIUM |
| EXCEPT-002 | `On Error Resume Next` zonder Err check | HIGH |
| EXCEPT-003 | Division without zero check | MEDIUM |
| EXCEPT-004 | File operations without existence check | LOW |

---

## CWE-400: Resource Allocation Enhancement

### Doel
Uitbreiding van bestaande resource leak detector met DoS prevention.

### Additional Patterns

```vbscript
' VULNERABLE: Unlimited resource allocation
Do While Not rs.EOF
    ' Potentially infinite loop loading data
    ReDim Preserve allData(UBound(allData) + 1)
    allData(UBound(allData)) = rs("data")
    rs.MoveNext
Loop

' SAFE: Resource limits
maxRecords = 1000
recordCount = 0
Do While Not rs.EOF And recordCount < maxRecords
    ' Process limited records
    recordCount = recordCount + 1
    rs.MoveNext
Loop
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| RES-001 | Loop without iteration limit | MEDIUM |
| RES-002 | ReDim Preserve in loop | HIGH |
| RES-003 | Unbounded string concatenation | MEDIUM |

---

## Implementation Architecture

```python
# backend/app/scanners/security/advanced.py

class RaceConditionDetector(BaseSecurityScanner):
    """CWE-362: Race Condition Detection"""

    def __init__(self):
        self.toctou_patterns = self._load_toctou_patterns()
        self.shared_resource_patterns = self._load_shared_patterns()

    async def scan(self, project_path: str) -> List[Finding]:
        findings = []

        # Check for TOCTOU patterns
        for file in self.asp_files:
            if self._has_toctou_vulnerability(file):
                findings.append(self._create_toctou_finding(file))

        # Check for shared resource race conditions
        for file in self.asp_files:
            if self._has_shared_resource_race(file):
                findings.append(self._create_race_finding(file))

        return findings


class ArrayIndexDetector(BaseSecurityScanner):
    """CWE-129: Improper Validation of Array Index"""

    ARRAY_ACCESS_PATTERN = r'\w+\s*\(\s*(?:CInt|CLng)?\s*\(?Request\s*\('


class ExceptionalConditionDetector(BaseSecurityScanner):
    """CWE-754: Improper Check for Unusual or Exceptional Conditions"""

    UNHANDLED_OPERATIONS = [
        'conn.Open',
        'conn.Execute',
        'fso.OpenTextFile',
        'xmlhttp.Open',
    ]
```

---

## Data Flow Analysis

### Inter-procedural Tracking

```python
class DataFlowAnalyzer:
    """Track data flow between procedures for advanced detection"""

    def trace_tainted_data(self, source: str, sink: str) -> List[Path]:
        """
        Trace paths from source (e.g., Request) to sink (e.g., Array access)
        """
        paths = []
        # Build call graph
        call_graph = self._build_call_graph()
        # Find all paths from source to sink
        for path in self._dfs_paths(source, sink, call_graph):
            if not self._has_sanitization(path):
                paths.append(path)
        return paths
```

---

## FysioOne Specific Patterns

### Session Race Conditions

```python
def check_fysioone_session_races(file_content: str) -> List[Finding]:
    """Check for FysioOne-specific session race conditions"""

    # Pattern: Reading OmgevingId and using it separately
    # Could be changed between reads in multi-tab scenario
    patterns = [
        (r'ses_omgevingId\s*=\s*Session\("OmgevingId"\)',
         r'WHERE.*OmgevingId\s*=\s*ses_omgevingId'),
    ]
```

---

## Effort Estimate

| Task | Days |
|------|------|
| RaceConditionDetector | 3 |
| ArrayIndexDetector | 2 |
| ExceptionalConditionDetector | 2 |
| DataFlowAnalyzer (basic) | 3 |
| FysioOne-specific patterns | 2 |
| Integration + Tests | 2 |
| **Total** | **14 days** |

---

## Integration with Brown Paper

```python
# Update Phase 1 to include advanced security scan
result.advanced_security = await self._run_advanced_security_scan(
    project_path,
    [RaceConditionDetector, ArrayIndexDetector, ExceptionalConditionDetector]
)
```

---

*Spec Version: 1.0*
*Target: Week 157-160*
