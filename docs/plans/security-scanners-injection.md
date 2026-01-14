# Security Scanners: Injection Vulnerabilities

**Phase:** Week 145-147
**Priority:** CRITICAL
**Target:** Classic ASP, VBScript, SQL

---

## Overview

Injection attacks zijn de #1 en #2 in de CWE Top 25. Voor Classic ASP zijn deze bijzonder relevant omdat:
- Veel dynamische SQL constructie met string concatenation
- `Response.Write` zonder encoding
- `Server.Execute` en `Server.Transfer` met user input

---

## CWE-89: SQL Injection Detector

### Doel
Detecteer dynamische SQL constructies die kwetsbaar zijn voor injection.

### Patterns te Detecteren

```vbscript
' VULNERABLE: String concatenation with user input
sql = "SELECT * FROM Users WHERE id = " & Request("id")
sql = "SELECT * FROM Users WHERE name = '" & Request("name") & "'"

' VULNERABLE: Execute with concatenated string
conn.Execute "DELETE FROM " & tableName & " WHERE id = " & id

' SAFE: Parameterized queries
cmd.Parameters.Append cmd.CreateParameter("@id", adInteger, adParamInput, , id)
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| SQL-INJ-001 | `Request\(.*\)` in SQL string | CRITICAL |
| SQL-INJ-002 | `& Request` in Execute | CRITICAL |
| SQL-INJ-003 | `Session\(` in SQL zonder sanitization | HIGH |
| SQL-INJ-004 | Dynamic table/column names | MEDIUM |

### False Positive Mitigation

- Check for preceding `CLng()`, `CInt()`, `CDbl()` casting
- Check for `Replace(x, "'", "''")` escaping
- Check for stored procedure calls

### Implementation

```python
class SQLInjectionDetector(BaseSecurityScanner):
    """CWE-89: SQL Injection Detection for Classic ASP"""

    DANGEROUS_SOURCES = [
        r'Request\s*\(\s*["\'].*["\']\s*\)',
        r'Request\.Form\s*\(',
        r'Request\.QueryString\s*\(',
        r'Request\.Cookies\s*\(',
    ]

    SQL_SINKS = [
        r'\.Execute\s*\(',
        r'\.Open\s*["\']SELECT',
        r'sql\s*=\s*["\']',
        r'strSQL\s*=',
    ]

    async def scan(self) -> List[ScanFinding]:
        findings = []
        for file in self.asp_files:
            content = file.read_text()
            for source in self.DANGEROUS_SOURCES:
                for sink in self.SQL_SINKS:
                    if self._flows_to(source, sink, content):
                        findings.append(self._create_finding(
                            cwe="CWE-89",
                            severity=Severity.CRITICAL,
                            ...
                        ))
        return findings
```

---

## CWE-79: Cross-Site Scripting (XSS) Detector

### Doel
Detecteer output van user input zonder HTML encoding.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Direct output of user input
Response.Write Request("name")
Response.Write "<input value='" & username & "'>"

' VULNERABLE: In ASP blocks
<%= Request("search") %>
<%= Session("username") %>

' SAFE: Encoded output
Response.Write Server.HTMLEncode(Request("name"))
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| XSS-001 | `Response.Write Request(` | CRITICAL |
| XSS-002 | `<%= Request(` | CRITICAL |
| XSS-003 | `Response.Write Session(` zonder encode | HIGH |
| XSS-004 | `Response.Write` met variabele zonder encode | MEDIUM |

### Implementation

```python
class XSSDetector(BaseSecurityScanner):
    """CWE-79: XSS Detection for Classic ASP"""

    UNSAFE_OUTPUTS = [
        r'Response\.Write\s+Request\s*\(',
        r'<%=\s*Request\s*\(',
        r'<%=\s*Session\s*\(',
    ]

    SAFE_WRAPPERS = [
        r'Server\.HTMLEncode\s*\(',
        r'HTMLEncode\s*\(',
        r'AntiXSS\.',
    ]
```

---

## CWE-78: OS Command Injection Detector

### Doel
Detecteer execution van system commands met user input.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Shell execution with user input
Set shell = Server.CreateObject("WScript.Shell")
shell.Run "cmd /c " & Request("cmd")

' VULNERABLE: Exec method
shell.Exec("ping " & ipAddress)

' SAFE: Whitelist validation
If InStr(allowedCommands, cmd) > 0 Then
    shell.Run cmd
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| CMD-INJ-001 | `WScript.Shell` + `Request(` | CRITICAL |
| CMD-INJ-002 | `.Run` met variabele | HIGH |
| CMD-INJ-003 | `.Exec` met string concatenation | CRITICAL |

---

## CWE-22: Path Traversal Detector

### Doel
Detecteer file access met user-controlled paths.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Direct file access
filePath = Server.MapPath(Request("file"))
Set fso = CreateObject("Scripting.FileSystemObject")
Set file = fso.OpenTextFile(Request("path"))

' VULNERABLE: Include with user input
Server.Execute Request("page") & ".asp"

' SAFE: Whitelist validation
allowedFiles = Array("home", "about", "contact")
If InArray(Request("page"), allowedFiles) Then
    Server.Execute Request("page") & ".asp"
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| PATH-001 | `Server.MapPath(Request(` | CRITICAL |
| PATH-002 | `FileSystemObject` + `Request(` | CRITICAL |
| PATH-003 | `Server.Execute Request(` | CRITICAL |
| PATH-004 | `Server.Transfer Request(` | HIGH |

---

## Test Cases

### FysioOne-Specific Tests

```vbscript
' Test 1: SQL Injection in Doorboeken.asp
' Expected: CRITICAL finding for dynamic SQL

' Test 2: XSS in form outputs
' Expected: HIGH finding for unencoded Session values

' Test 3: Path traversal in include files
' Expected: MEDIUM finding for dynamic includes
```

---

## Integration

### Scanner Registry

```python
# backend/app/scanners/security/__init__.py
from .sql_injection import SQLInjectionDetector
from .xss import XSSDetector
from .command_injection import OSCommandInjectionDetector
from .path_traversal import PathTraversalDetector

__all__ = [
    'SQLInjectionDetector',
    'XSSDetector',
    'OSCommandInjectionDetector',
    'PathTraversalDetector',
]
```

### Brown Paper Integration

```python
# In _phase1_code_understanding():
try:
    from app.scanners.security import (
        SQLInjectionDetector,
        XSSDetector,
        OSCommandInjectionDetector,
        PathTraversalDetector,
    )

    security_results = await self._run_security_scan(
        project_path,
        [SQLInjectionDetector, XSSDetector,
         OSCommandInjectionDetector, PathTraversalDetector]
    )
    result.security_scan = security_results
```

---

## Effort Estimate

| Task | Days |
|------|------|
| SQLInjectionDetector | 3 |
| XSSDetector | 3 |
| OSCommandInjectionDetector | 2 |
| PathTraversalDetector | 2 |
| Integration + Tests | 2 |
| **Total** | **12 days** |

---

*Spec Version: 1.0*
*Target: Week 145-147*
